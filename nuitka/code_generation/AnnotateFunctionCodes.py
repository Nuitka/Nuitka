#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for annotate functions.

Annotate functions (marked with flag "annotate") are backed by real Python
bytecode instead of compiled C code.  This allows `annotationlib` to re-wrap
them with `_StringifierDict` globals for FORWARDREF resolution.
"""

import marshal

from nuitka.options.Options import isExperimental

from .ErrorCodes import getAssertionCode
from .PythonSourceCodeGeneration import (
    generateFunctionSourceFromBody,
    getFunctionMakerIdentifier,
)


def isBytecodeBackedFunction(function_body):
    """Decide if a function is backed by Python bytecode, not compiled C code.

    Currently this is true for functions marked with flag "annotate". We
    mean to add more plugin and user control though.

    Args:
        function_body: Function body node to check.

    Returns:
        True if bytecode backed
    """
    return (
        function_body.hasFlag("annotate")
        and not isExperimental("no-deferred-annotation")
        and not function_body.hasFlag("force_c")
    )


def generateAnnotateFunctionCreationCode(to_name, expression, emit, context):
    function_body = expression.subnode_function_ref.getFunctionBody()
    function_identifier = function_body.getCodeName()

    # Only need to generate the maker once.
    if not context.hasHelperCode(function_identifier):
        _generateAnnotateFunctionMaker(function_body, function_identifier, context)

    # Emit the call to the maker.
    function_maker_identifier = getFunctionMakerIdentifier(
        function_identifier=function_identifier
    )

    emit("%s = %s(tstate);" % (to_name, function_maker_identifier))

    getAssertionCode(check="%s != NULL" % to_name, emit=emit)

    context.addCleanupTempName(to_name)


def _generateAnnotateFunctionMaker(function_body, function_identifier, context):
    """Generate a C maker function that creates a PyFunctionObject from bytecode."""

    maker_identifier = getFunctionMakerIdentifier(function_identifier)

    source = generateFunctionSourceFromBody(function_body)

    compiled = compile(source, function_identifier, "exec")
    marshalled = marshal.dumps(compiled.co_consts[0])
    marshalled_size = len(marshalled)

    marshalled_ptr = context.getBlobConstantCode(
        marshalled,
        "annotate marshalled code for '%s'" % function_identifier,
    )

    module_code_name = context.getModuleCodeName()
    module_dict_name = "(PyObject *)moduledict_%s" % module_code_name
    qualname = function_body.getFunctionQualname()
    qualname_obj = context.getConstantCode(constant=qualname)

    maker_code = """\
static PyObject *%(maker)s(PyThreadState *tstate) {
    PyObject *result;
    PyObject *code = PyMarshal_ReadObjectFromString(
        %(marshalled)s,
        %(marshalled_size)d);
    if (unlikely(code == NULL)) {
        return NULL;
    }
    result = PyFunction_NewWithQualName(code, %(module_dict)s, %(qualname)s);
    Py_DECREF(code);
    return result;
}
""" % {
        "maker": maker_identifier,
        "marshalled": marshalled_ptr,
        "marshalled_size": marshalled_size,
        "module_dict": module_dict_name,
        "qualname": qualname_obj,
    }

    context.addHelperCode(function_identifier, maker_code)

    declaration_code = "static PyObject *%(maker)s(PyThreadState *tstate);" % {
        "maker": maker_identifier,
    }
    context.addDeclaration(function_identifier, declaration_code)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
