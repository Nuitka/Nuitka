#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Import related codes.

That is import as expression, and star import.
"""

from nuitka.nodes.LocalsScopes import GlobalsDictHandle
from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode
from .LineNumberCodes import emitLineNumberUpdateCode
from .ModuleCodes import getModuleAccessCode


def generateBuiltinImportCode(to_name, expression, emit, context):
    # We know that 5 expressions are created, pylint: disable=W0632
    module_name, globals_name, locals_name, import_list_name, level_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:

        _getBuiltinImportCode(
            to_name=value_name,
            module_name=module_name,
            globals_name=globals_name,
            locals_name=locals_name,
            import_list_name=import_list_name,
            level_name=level_name,
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )


# TODO: Maybe use this for other cases too, not just import.
def _getCountedArgumentsHelperCallCode(
    helper_prefix, to_name, args, min_args, needs_check, emit, context
):
    orig_args = args
    args = list(args)
    while args[-1] is None:
        del args[-1]

    if None in args:
        emit(
            "%s = %s_KW( %s );"
            % (
                to_name,
                helper_prefix,
                ", ".join("NULL" if arg is None else str(arg) for arg in orig_args),
            )
        )
    else:
        # Check that no following arguments are not None.
        assert len(args) >= min_args

        emit(
            "%s = %s%d( %s );"
            % (to_name, helper_prefix, len(args), ", ".join(str(arg) for arg in args))
        )

    getErrorExitCode(
        check_name=to_name,
        release_names=args,
        needs_check=needs_check,
        emit=emit,
        context=context,
    )

    context.addCleanupTempName(to_name)


def _getBuiltinImportCode(
    to_name,
    module_name,
    globals_name,
    locals_name,
    import_list_name,
    level_name,
    needs_check,
    emit,
    context,
):

    emitLineNumberUpdateCode(emit, context)

    _getCountedArgumentsHelperCallCode(
        helper_prefix="IMPORT_MODULE",
        to_name=to_name,
        args=(module_name, globals_name, locals_name, import_list_name, level_name),
        min_args=1,
        needs_check=needs_check,
        emit=emit,
        context=context,
    )


def generateImportModuleHardCode(to_name, expression, emit, context):
    module_name = expression.getModuleName()
    needs_check = expression.mayRaiseException(BaseException)

    emitLineNumberUpdateCode(emit, context)

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:

        emit("""%s = PyImport_ImportModule("%s");""" % (value_name, module_name))

        getErrorExitCode(
            check_name=value_name, needs_check=needs_check, emit=emit, context=context
        )


def generateImportModuleNameHardCode(to_name, expression, emit, context):
    module_name = expression.getModuleName()
    import_name = expression.getImportName()
    needs_check = expression.mayRaiseException(BaseException)

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:

        if module_name == "sys":
            emit(
                """%s = PySys_GetObject( (char *)"%s" );""" % (value_name, import_name)
            )
        elif module_name in ("os", "__future__", "importlib._bootstrap"):
            emitLineNumberUpdateCode(emit, context)

            emit(
                """\
{
    PyObject *module = PyImport_ImportModule("%(module_name)s");
    if (likely( module != NULL ))
    {
        %(to_name)s = PyObject_GetAttr( module, %(import_name)s );
    }
    else
    {
        %(to_name)s = NULL;
    }
}
"""
                % {
                    "to_name": value_name,
                    "module_name": module_name,
                    "import_name": context.getConstantCode(import_name),
                }
            )
        else:
            assert False, module_name

        getErrorExitCode(
            check_name=value_name, needs_check=needs_check, emit=emit, context=context
        )


def generateImportStarCode(statement, emit, context):
    module_name = context.allocateTempName("star_imported")

    generateExpressionCode(
        to_name=module_name,
        expression=statement.getSourceModule(),
        emit=emit,
        context=context,
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    res_name = context.getBoolResName()

    target_scope = statement.getTargetDictScope()

    if type(target_scope) is GlobalsDictHandle:
        emit(
            "%s = IMPORT_MODULE_STAR( %s, true, %s );"
            % (res_name, getModuleAccessCode(context=context), module_name)
        )
    else:
        locals_declaration = context.addLocalsDictName(target_scope.getCodeName())

        emit(
            """
%(res_name)s = IMPORT_MODULE_STAR( %(locals_dict)s, false, %(module_name)s );
"""
            % {
                "res_name": res_name,
                "locals_dict": locals_declaration,
                "module_name": module_name,
            }
        )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_name=module_name,
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateImportNameCode(to_name, expression, emit, context):
    from_arg_name = context.allocateTempName("import_name_from")

    generateExpressionCode(
        to_name=from_arg_name,
        expression=expression.getModule(),
        emit=emit,
        context=context,
    )

    level = expression.getImportLevel()

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:

        if level and python_version >= 350:
            emit(
                """\
if ( PyModule_Check( %(from_arg_name)s ) )
{
   %(to_name)s = IMPORT_NAME_OR_MODULE(
        %(from_arg_name)s,
        (PyObject *)MODULE_DICT(%(from_arg_name)s),
        %(import_name)s,
        %(import_level)s
    );
}
else
{
   %(to_name)s = IMPORT_NAME( %(from_arg_name)s, %(import_name)s );
}
"""
                % {
                    "to_name": value_name,
                    "from_arg_name": from_arg_name,
                    "import_name": context.getConstantCode(
                        constant=expression.getImportName()
                    ),
                    "import_level": context.getConstantCode(
                        constant=expression.getImportLevel()
                    ),
                }
            )
        else:
            emit(
                "%s = IMPORT_NAME( %s, %s );"
                % (
                    value_name,
                    from_arg_name,
                    context.getConstantCode(constant=expression.getImportName()),
                )
            )

        getErrorExitCode(
            check_name=value_name,
            release_name=from_arg_name,
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)
