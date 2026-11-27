#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for annotate functions.

Annotate functions (marked with flag 'annotate') are backed by real Python
bytecode instead of compiled C code. This allows 'annotationlib' to re-wrap
them with '_StringifierDict' globals for FORWARDREF resolution.
"""

import marshal

from .CodeHelpers import withObjectCodeTemporaryAssignment
from .ErrorCodes import getAssertionCode
from .PythonSourceCodeGeneration import (
    PythonSourceGenerationError,
    generateFunctionSourceFromBody,
    getAnnotateClosureVariables,
    getAnnotateSourceVariableName,
    getFunctionCodeObjectFromSource,
    getFunctionMakerIdentifier,
)
from .templates.CodeTemplatesFunction import (
    template_annotate_function_closure_setup,
    template_make_function,
)
from .VariableCodes import getClosureCopyCode


def isBytecodeBackedFunction(function_body):
    """Decide if a function is backed by Python bytecode, not compiled C code.

    This is true for function bodies created by the source backed machinery,
    e.g. 'annotate' functions.
    """
    return function_body.hasFlag("python_source") and not function_body.hasFlag(
        "force_c"
    )


def generateAnnotateFunctionCreationCode(to_name, expression, emit, context):
    function_body = expression.subnode_function_ref.getFunctionBody()
    function_identifier = function_body.getCodeName()

    if not context.hasHelperCode(function_identifier):
        _generateAnnotateFunctionMaker(function_body, function_identifier, context)

    closure_variables = expression.getClosureVariableVersions()

    if closure_variables:
        closure_variables = sorted(
            closure_variables,
            key=lambda item: getAnnotateSourceVariableName(item[0]),
        )

    closure_name, closure_copy = getClosureCopyCode(
        closure_variables=closure_variables,
        context=context,
    )

    function_maker_identifier = getFunctionMakerIdentifier(
        function_identifier=function_identifier
    )

    args = ["tstate"]

    if closure_name:
        args.append(closure_name)

    with withObjectCodeTemporaryAssignment(
        to_name, "annotate_function_result", expression, emit, context
    ) as result_name:
        emit(
            template_make_function
            % {
                "to_name": result_name,
                "function_maker_identifier": function_maker_identifier,
                "args": ", ".join(str(arg) for arg in args),
                "closure_copy": "\n".join(closure_copy),
            }
        )

        getAssertionCode(check="%s != NULL" % result_name, emit=emit)
        context.addCleanupTempName(result_name)


def _getClosureSetupCode(closure_variables):
    if not closure_variables:
        return "", ""

    return (
        ", struct Nuitka_CellObject **closure",
        template_annotate_function_closure_setup
        % {
            "closure_count": len(closure_variables),
        },
    )


def _getCodeObjectCreationCode(context, marshalled, function_identifier, first_lineno):
    """Get the C code to create the annotate code object, and to release it.

    A definition that can be executed repeatedly, e.g. a nested function on
    every call, unmarshals the immutable code object once and shares it
    between every function created from it, as CPython does, and must then
    not release it, while one that is executed once creates and releases it.

    Returns:
        Tuple of the C code providing the 'code' variable, and the C code
        releasing it, which is empty when it is cached.
    """
    marshalled_code = context.getBlobConstantCode(
        marshalled,
        "annotate marshalled code for '%s'" % function_identifier,
    )

    if context.mayRecurse():
        # Racing threads can at worst each unmarshal it, and keep one.
        code_object_setup = """\
    static PyObject *code_cache = NULL;
    PyObject *code = code_cache;
    if (code == NULL) {
        code = PyMarshal_ReadObjectFromString(
            %(marshalled)s,
            %(marshalled_size)d);
        assert(code != NULL);
        USE_CODE_OBJECT_WITH_LINE(code, module_filename_obj, %(first_lineno)d);
        code_cache = code;
    }
""" % {
            "marshalled": marshalled_code,
            "marshalled_size": len(marshalled),
            "first_lineno": first_lineno,
        }
        code_object_release = ""
    else:
        code_object_setup = """\
    PyObject *code = PyMarshal_ReadObjectFromString(
        %(marshalled)s,
        %(marshalled_size)d);
    assert(code != NULL);
    USE_CODE_OBJECT_WITH_LINE(code, module_filename_obj, %(first_lineno)d);
""" % {
            "marshalled": marshalled_code,
            "marshalled_size": len(marshalled),
            "first_lineno": first_lineno,
        }
        code_object_release = "    Py_DECREF(code);\n"

    return code_object_setup, code_object_release


def _getAnnotateCodeAndClosureVariables(function_body, function_identifier):
    source = generateFunctionSourceFromBody(function_body)

    compiled = compile(source, "", "exec")

    annotate_code = getFunctionCodeObjectFromSource(
        function_body=function_body, compiled=compiled
    )

    closure_variables = getAnnotateClosureVariables(function_body)

    if annotate_code.co_freevars != tuple(
        getAnnotateSourceVariableName(variable) for variable in closure_variables
    ):
        raise PythonSourceGenerationError(
            "Closure variables of annotate function '%s' do not match its free variables"
            % function_identifier
        )

    return annotate_code, closure_variables


def checkAnnotateFunction(function_body):
    """Check that an annotate function can be created from generated source.

    Raises:
        PythonSourceGenerationError: If the function has to use compiled C code instead.
    """
    _getAnnotateCodeAndClosureVariables(
        function_body=function_body,
        function_identifier=function_body.getCodeName(),
    )


def _generateAnnotateFunctionMaker(function_body, function_identifier, context):
    maker_identifier = getFunctionMakerIdentifier(function_identifier)

    annotate_code, closure_variables = _getAnnotateCodeAndClosureVariables(
        function_body=function_body, function_identifier=function_identifier
    )

    marshalled = marshal.dumps(annotate_code)

    closure_parameter, closure_setup = _getClosureSetupCode(closure_variables)

    code_object_setup, code_object_release = _getCodeObjectCreationCode(
        context=context,
        marshalled=marshalled,
        function_identifier=function_identifier,
        first_lineno=function_body.getCodeObject().getLineNumber(),
    )

    maker_code = """\
static PyObject *%(maker)s(PyThreadState *tstate%(closure_parameter)s) {
    PyObject *result;
%(code_object_setup)s
    result = PyFunction_NewWithQualName(code, %(module_dict)s, %(qualname)s);
    assert(result != NULL);
%(code_object_release)s
%(closure_setup)s
    return result;
}
""" % {
        "maker": maker_identifier,
        "module_dict": "(PyObject *)%s" % context.getModuleDictCodeName(),
        "qualname": context.getConstantCode(
            constant=function_body.getFunctionQualname()
        ),
        "closure_parameter": closure_parameter,
        "closure_setup": closure_setup,
        "code_object_setup": code_object_setup,
        "code_object_release": code_object_release,
    }

    context.addHelperCode(function_identifier, maker_code)

    declaration_code = (
        "static PyObject *%(maker)s(PyThreadState *tstate%(closure_parameter)s);"
        % {
            "maker": maker_identifier,
            "closure_parameter": closure_parameter,
        }
    )
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
