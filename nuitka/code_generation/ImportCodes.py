#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Import related codes.

That is import as expression, and star import.
"""

import os

from nuitka.HardImportRegistry import isHardModule, isHardModuleDynamic
from nuitka.nodes.LocalsScopes import GlobalsDictHandle
from nuitka.PythonVersions import python_version
from nuitka.utils.Jinja2 import renderTemplateFromString
from nuitka.utils.ModuleNames import ModuleName

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
    (
        module_name,
        globals_name,
        locals_name,
        import_list_name,
        level_name,
    ) = generateChildExpressionsCode(expression=expression, emit=emit, context=context)

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        _getBuiltinImportCode(
            expression=expression,
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
            "%s = %s_KW(tstate, %s);"
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
            "%s = %s%d(tstate, %s);"
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
    expression,
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
    emitLineNumberUpdateCode(expression, emit, context)

    # Spell the resulting helper names out, so this can be found,
    # IMPORT_MODULE_KW, IMPORT_MODULE1, IMPORT_MODULE2, IMPORT_MODULE3, IMPORT_MODULE5
    _getCountedArgumentsHelperCallCode(
        helper_prefix="IMPORT_MODULE",
        to_name=to_name,
        args=(module_name, globals_name, locals_name, import_list_name, level_name),
        min_args=1,
        needs_check=needs_check,
        emit=emit,
        context=context,
    )


def generateImportModuleFixedCode(to_name, expression, emit, context):
    needs_check = expression.mayRaiseException(BaseException)

    if needs_check:
        emitLineNumberUpdateCode(expression, emit, context)

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        emit(
            """%s = IMPORT_MODULE_FIXED(tstate, %s, %s);"""
            % (
                value_name,
                context.getConstantCode(expression.getModuleName().asString()),
                context.getConstantCode(expression.getValueName().asString()),
            )
        )

        getErrorExitCode(
            check_name=value_name, needs_check=needs_check, emit=emit, context=context
        )

        context.addCleanupTempName(value_name)


def getImportModuleHardCodeName(module_name):
    """Encoding hard module name for code name."""

    module_name = ModuleName(module_name)

    return "IMPORT_HARD_%s" % module_name.asPath().replace(os.path.sep, "__").upper()


def generateImportModuleHardCode(to_name, expression, emit, context):
    imported_module_name = expression.getModuleName()
    module_value_name = expression.getValueName()

    needs_check = expression.mayRaiseException(BaseException)

    if needs_check:
        emitLineNumberUpdateCode(expression, emit, context)

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        import_gives_ref, module_getter_code = getImportHardModuleGetterCode(
            module_name=imported_module_name, context=context
        )

        if imported_module_name == module_value_name:
            emit("""%s = %s;""" % (value_name, module_getter_code))
        else:
            import_gives_ref, module_getter_code2 = getImportHardModuleGetterCode(
                module_name=module_value_name, context=context
            )

            emit(
                renderTemplateFromString(
                    r"""
{% if import_gives_ref %}
{
    PyObject *hard_module = {{module_getter_code1}};
    Py_DECREF(hard_module);
}
{% else %}
{{module_getter_code1}};
{% endif %}
{{value_name}} = {{module_getter_code2}};
""",
                    value_name=value_name,
                    module_getter_code1=module_getter_code,
                    module_getter_code2=module_getter_code2,
                    import_gives_ref=import_gives_ref,
                )
            )

        getErrorExitCode(
            check_name=value_name, needs_check=needs_check, emit=emit, context=context
        )

        if import_gives_ref:
            context.addCleanupTempName(value_name)


def generateConstantSysVersionInfoCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        emit("""%s = Nuitka_SysGetObject("%s");""" % (value_name, "version_info"))

    getErrorExitCode(
        check_name=value_name, needs_check=False, emit=emit, context=context
    )


def getImportHardModuleGetterCode(module_name, context):
    if isHardModuleDynamic(module_name):
        module_name_code = context.getConstantCode(module_name.asString())

        module_getter_code = "IMPORT_MODULE_FIXED(tstate, %s, %s)" % (
            module_name_code,
            module_name_code,
        )
        gives_ref = True
    else:
        module_getter_code = "%s()" % getImportModuleHardCodeName(module_name)
        gives_ref = False

    return gives_ref, module_getter_code


def getImportModuleNameHardCode(
    to_name, module_name, import_name, needs_check, emit, context
):
    module_name = ModuleName(module_name)

    if module_name == "sys":
        emit("""%s = Nuitka_SysGetObject("%s");""" % (to_name, import_name))
        needs_release = False
    elif isHardModule(module_name):
        if needs_check:
            emitLineNumberUpdateCode(expression=None, emit=emit, context=context)

        import_gives_ref, module_getter_code = getImportHardModuleGetterCode(
            module_name=module_name, context=context
        )

        emit(
            renderTemplateFromString(
                r"""
{
    PyObject *hard_module = {{module_getter_code}};
{% if needs_check %}
    if (likely(hard_module != NULL)) {
        {{to_name}} = LOOKUP_ATTRIBUTE(tstate, hard_module, {{import_name}});

{% if import_gives_ref %}
        Py_DECREF(hard_module);
{% endif %}

    } else {
        {{to_name}} = NULL;
    }
{% else %}
    {{to_name}} = LOOKUP_ATTRIBUTE(tstate, hard_module, {{import_name}});
{% if import_gives_ref %}
    Py_DECREF(hard_module);
{% endif %}
{% endif %}
}
""",
                to_name=to_name,
                module_name=str(module_name),
                module_getter_code=module_getter_code,
                import_name=context.getConstantCode(import_name),
                needs_check=needs_check,
                import_gives_ref=import_gives_ref,
            )
        )

        needs_release = True
    else:
        assert False, module_name

    getErrorExitCode(
        check_name=to_name, needs_check=needs_check, emit=emit, context=context
    )

    if needs_release:
        context.addCleanupTempName(to_name)


def generateImportModuleNameHardCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        context.setCurrentSourceCodeReference(expression.getCompatibleSourceReference())

        getImportModuleNameHardCode(
            to_name=value_name,
            module_name=expression.getModuleName(),
            import_name=expression.getImportName(),
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )


def generateImportlibImportCallCode(to_name, expression, emit, context):
    needs_check = expression.mayRaiseException(BaseException)

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_module", expression, emit, context
    ) as value_name:
        import_name, package_name = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

        emitLineNumberUpdateCode(expression, emit, context)

        # TODO: The import name wouldn't have to be an object really, could do with a
        # C string only.

        emit(
            renderTemplateFromString(
                r"""
{
    PyObject *hard_module = {{import_hard_importlib}}();
    PyObject *import_module_func = LOOKUP_ATTRIBUTE(tstate, hard_module, {{context.getConstantCode("import_module")}});
{% if package_name == None %}
    {{to_name}} = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, import_module_func, {{import_name}});
{% else %}
    PyObject *args[2] = { {{import_name}}, {{package_name}} };
    {{to_name}} = CALL_FUNCTION_WITH_ARGS2(tstate, import_module_func, args);
{% endif %}
    Py_DECREF(import_module_func);
}
""",
                context=context,
                to_name=value_name,
                import_name=import_name,
                package_name=package_name,
                import_hard_importlib=getImportModuleHardCodeName("importlib"),
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(import_name, package_name),
            needs_check=needs_check,
            emit=emit,
            context=context,
        )


def generateImportStarCode(statement, emit, context):
    module_name = context.allocateTempName("star_imported")

    generateExpressionCode(
        to_name=module_name,
        expression=statement.subnode_module,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        res_name = context.getBoolResName()

        target_scope = statement.getTargetDictScope()

        if type(target_scope) is GlobalsDictHandle:
            emit(
                "%s = IMPORT_MODULE_STAR(tstate, %s, true, %s);"
                % (res_name, getModuleAccessCode(context=context), module_name)
            )
        else:
            locals_declaration = context.addLocalsDictName(target_scope.getCodeName())

            emit(
                "%(res_name)s = IMPORT_MODULE_STAR(tstate, %(locals_dict)s, false, %(module_name)s);"
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


def generateImportNameCode(to_name, expression, emit, context):
    from_arg_name = context.allocateTempName("import_name_from")

    generateExpressionCode(
        to_name=from_arg_name,
        expression=expression.subnode_module,
        emit=emit,
        context=context,
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        if python_version >= 0x350:
            emit(
                """\
if (PyModule_Check(%(from_arg_name)s)) {
    %(to_name)s = IMPORT_NAME_OR_MODULE(
        tstate,
        %(from_arg_name)s,
        (PyObject *)moduledict_%(module_identifier)s,
        %(import_name)s,
        %(import_level)s
    );
} else {
    %(to_name)s = IMPORT_NAME_FROM_MODULE(tstate, %(from_arg_name)s, %(import_name)s);
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
                    "module_identifier": context.getModuleCodeName(),
                }
            )
        else:
            emit(
                "%s = IMPORT_NAME_FROM_MODULE(tstate, %s, %s);"
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
