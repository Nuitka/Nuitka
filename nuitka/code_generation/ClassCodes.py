#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for class creation, metaclass selection, and 'super'."""

from nuitka.PythonVersions import python_version

from .AttributeCodes import getAttributeLookupCode
from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .LocalsDictCodes import assignDictOrMappingItem
from .PgoCodes import checkPGOValueShape
from .PythonAPICodes import (
    CArg,
    generateCAPIObjectCode,
    getCAPIObjectCode,
    makeArgDescFromExpression,
)
from .VariableCodes import getLocalVariableDeclaration


def generateSelectMetaclassCode(to_name, expression, emit, context):
    assert python_version >= 0x300

    generateCAPIObjectCode(
        to_name=to_name,
        capi="SELECT_METACLASS",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateClassDictFromClassCode(to_name, expression, emit, context):
    class_declaration = getLocalVariableDeclaration(context, expression.variable, None)

    with withObjectCodeTemporaryAssignment(
        to_name, "class_dict_value", expression, emit, context
    ) as value_name:
        class_name = class_declaration.getCType().emitValueAccessCode(
            value_name=class_declaration, emit=emit, context=context
        )

        emit("""\
%(to_name)s = (PyObject *)(((PyTypeObject *)%(class_name)s)->tp_dict);
CHECK_OBJECT(%(to_name)s);
Py_INCREF(%(to_name)s);""" % {"to_name": value_name, "class_name": class_name})

        context.addCleanupTempName(value_name)


def generateBuiltinSuper1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_SUPER2",
        tstate=True,
        arg_desc=(CArg(context.getModuleDictCodeName()),)
        + makeArgDescFromExpression(expression)
        + (CArg("NULL"),),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinSuperCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi=(
            "BUILTIN_SUPER2"
            if expression.isExpressionBuiltinSuper2()
            else "BUILTIN_SUPER0"
        ),
        tstate=True,
        arg_desc=(CArg(context.getModuleDictCodeName()),)
        + makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateTypeOperationPrepareCode(to_name, expression, emit, context):
    type_name, args_name, kwargs_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    prepare_func_name = context.allocateTempName("prepare_func")

    getAttributeLookupCode(
        to_name=prepare_func_name,
        source_name=type_name,
        attribute_name="__prepare__",
        needs_check=False,
        emit=emit,
        context=context,
    )

    getCAPIObjectCode(
        to_name=to_name,
        capi="CALL_FUNCTION",
        arg_names=(
            "tstate",
            prepare_func_name,
            "const_tuple_empty" if args_name is None else args_name,
            "NULL" if kwargs_name is None else kwargs_name,
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        ref_count=1,
        release_names=(prepare_func_name, type_name, args_name, kwargs_name),
        emit=emit,
        context=context,
    )


def generateCallMetaclassCode(to_name, expression, emit, context):
    (
        metaclass_name,
        name_name,
        bases_name,
        dict_name,
        class_decl_dict_name,
    ) = generateChildExpressionsCode(expression=expression, emit=emit, context=context)

    class_var_name = getLocalVariableDeclaration(
        context, expression.class_variable, None
    )

    if python_version >= 0x360 and expression.class_variable.isSharedTechnically():
        # In Python 3.6+, type.__new__ requires "__classcell__" to be populated in the class dictionary
        # if there are methods capturing it. The class namespace can be a custom mapping from the
        # "__prepare__" of the metaclass though, and then it has to be set via the mapping interface,
        # just like the class body does it.
        assignDictOrMappingItem(
            target_name=dict_name,
            key_name=context.getConstantCode(constant="__classcell__"),
            value_name="(PyObject *)%s" % class_var_name,
            is_dict_shape=expression.subnode_dict_arg.hasShapeDictionaryExact(),
            may_raise=True,
            emit=emit,
            context=context,
        )

    args_name = context.allocateTempName("metaclass_args")
    emit(
        "%s = MAKE_TUPLE3(tstate, %s, %s, %s);"
        % (args_name, name_name, bases_name, dict_name)
    )
    context.addCleanupTempName(args_name)

    getCAPIObjectCode(
        to_name=to_name,
        capi="CALL_FUNCTION",
        arg_names=(
            "tstate",
            metaclass_name,
            args_name,
            "NULL" if class_decl_dict_name is None else class_decl_dict_name,
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        ref_count=1,
        release_names=(
            metaclass_name,
            name_name,
            bases_name,
            dict_name,
            args_name,
            class_decl_dict_name,
        ),
        emit=emit,
        context=context,
    )


def _shallUseClassPrepareResultOnce(expression, context):
    """Is the class only created once per program run?

    This is the case when the class creation is not inside a loop and its
    entry point is the module, i.e. only module level code is executed exactly
    once per run.
    """
    return (
        expression.getContainingLoopNode() is None
        and context.getOwner().getEntryPoint().isCompiledPythonModule()
    )


def generateCallClassPrepareCode(to_name, expression, emit, context):
    assert expression.pgo_policy in (
        None,
        "ignore",
        "assertion",
        "exception",
    ), expression.pgo_policy

    # When the start value is trusted and the call is not executed, the
    # recorded value is used as the class namespace, with plain dicts being
    # data, so the "__prepare__" call is assumed to have no relevant side
    # effects. Custom mappings keep the call.
    if expression.pgo_policy == "ignore":
        assert expression.expected_value is not None

        to_name.getCType().emitAssignmentCodeFromConstant(
            to_name=to_name,
            constant=expression.expected_value,
            may_escape=True,
            emit=emit,
            context=context,
        )
    else:
        generateExpressionCode(
            to_name=to_name,
            expression=expression.subnode_called,
            emit=emit,
            context=context,
        )

        if _shallUseClassPrepareResultOnce(expression=expression, context=context):
            probe_function = "PGO_onProbeClassPrepareResultOnce"
        else:
            probe_function = "PGO_onProbeClassPrepareResult"

        emit('%s(tstate, "%s", %s);' % (probe_function, expression.code_name, to_name))

        if expression.pgo_policy in ("assertion", "exception"):
            assert expression.expected_value is not None

            checkPGOValueShape(
                type_shape_to_check=expression.getTypeShape(),
                value_name=to_name,
                description="'__prepare__' result",
                may_raise=expression.mayRaiseExceptionOperation(),
                emit=emit,
                context=context,
            )


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
