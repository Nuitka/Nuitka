#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Import related codes.

That is import as expression, and star import.
"""

import os

from nuitka.HardImportRegistry import isHardModule, isHardModuleDynamic
from nuitka.ModuleRegistry import getModuleByName
from nuitka.nodes.LocalsScopes import GlobalsDictHandle
from nuitka.PythonVersions import python_version
from nuitka.utils.ModuleNames import ModuleName

from .CodeHelpers import (
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode
from .LineNumberCodes import emitLineNumberUpdateCode
from .LoaderCodes import getModuleEntryCodeName
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


def _getIncludedModule(module_name):
    """Get the module object of an included module.

    Args:
        module_name: ModuleName of the module to check.

    Returns:
        Module object, or None if the module is not included.
    """
    return getModuleByName(module_name)


def _getIncludedModuleEntryRef(module, context):
    """Get C code referencing the loader entry of an included module.

    Args:
        module: Module object of the included module.
        context: Code generation context to add the entry declaration to.

    Returns:
        C code naming the entry.
    """
    loader_entry_ref = getModuleEntryCodeName(module.getFullName())

    if not context.hasDeclaration(loader_entry_ref):
        context.addDeclaration(
            loader_entry_ref,
            "extern struct Nuitka_MetaPathBasedLoaderEntry %(loader_entry_ref)s;"
            % {"loader_entry_ref": loader_entry_ref},
        )

    return loader_entry_ref


def _getIncludedModuleImportCall(module, loader_entry_ref):
    """Get C code importing an included module through its loader entry.

    Args:
        module: Module object of the included module.
        loader_entry_ref: C code naming the entry of the module.

    Returns:
        C code calling the entry importer.
    """
    if module.isCompiledPythonModule():
        return "%(loader_entry_ref)s.m_import_module(tstate, NULL, NULL)" % {
            "loader_entry_ref": loader_entry_ref
        }
    else:
        return (
            "%(loader_entry_ref)s.m_import_module(tstate, &%(loader_entry_ref)s, NULL)"
            % {"loader_entry_ref": loader_entry_ref}
        )


def _emitFromlistModuleImports(expression, module_value_name, emit, context):
    # Emulate the fromlist handling of "__import__", which imports the real
    # submodules before the values are looked up on the imported module.
    for fromlist_module_name in expression.getFromlistModuleNames():
        res_name = context.getBoolResName()

        fromlist_module = _getIncludedModule(module_name=fromlist_module_name)

        if fromlist_module is not None:
            submodule_import_call = _getIncludedModuleImportCall(
                fromlist_module,
                _getIncludedModuleEntryRef(fromlist_module, context),
            )

            emit(
                """\
%(res_name)s = HAS_ATTR_BOOL(tstate, %(module_value_name)s, %(attribute_name)s);

if (%(res_name)s == false && HAS_ERROR_OCCURRED(tstate) == false) {
    PyObject *fromlist_module = %(submodule_import_call)s;

    if (unlikely(fromlist_module == NULL)) {
        %(res_name)s = false;
    } else {
        Py_DECREF(fromlist_module);
        %(res_name)s = true;
    }
}
"""
                % {
                    "res_name": res_name,
                    "module_value_name": module_value_name,
                    "attribute_name": context.getConstantCode(
                        fromlist_module_name.getBasename().asString()
                    ),
                    "submodule_import_call": submodule_import_call,
                }
            )
        else:
            emit(
                """%s = IMPORT_FIXED_MODULE_FROMLIST_ELEMENT(tstate, %s, %s, %s);"""
                % (
                    res_name,
                    module_value_name,
                    context.getConstantCode(
                        fromlist_module_name.getBasename().asString()
                    ),
                    context.getConstantCode(fromlist_module_name.asString()),
                )
            )

        getErrorExitBoolCode(
            condition="%s == false" % res_name, emit=emit, context=context
        )


def generateImportModuleFixedCode(to_name, expression, emit, context):
    needs_check = expression.mayRaiseException(BaseException)

    if needs_check:
        emitLineNumberUpdateCode(expression, emit, context)

    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        module_name = expression.getModuleName()
        module_value_name = expression.getValueName()
        found_module_name = expression.getFoundModuleName()

        target_module = _getIncludedModule(module_name=found_module_name)

        if target_module is not None:
            target_import_call = _getIncludedModuleImportCall(
                target_module,
                _getIncludedModuleEntryRef(target_module, context),
            )
        else:
            target_import_call = None

        if module_value_name == found_module_name:
            value_import_call = target_import_call
        else:
            value_module = _getIncludedModule(module_name=module_value_name)

            if value_module is not None:
                value_import_call = _getIncludedModuleImportCall(
                    value_module,
                    _getIncludedModuleEntryRef(value_module, context),
                )
            else:
                value_import_call = None

        if target_import_call is not None and value_import_call is not None:
            if module_value_name == found_module_name:
                emit("""%s = %s;""" % (value_name, target_import_call))
            elif needs_check:
                emit(
                    """\
{
    PyObject *imported_module = %(target_import_call)s;

    if (unlikely(imported_module == NULL)) {
        %(value_name)s = NULL;
    } else {
        Py_DECREF(imported_module);
        %(value_name)s = %(value_import_call)s;
    }
}
"""
                    % {
                        "value_name": value_name,
                        "target_import_call": target_import_call,
                        "value_import_call": value_import_call,
                    }
                )
            else:
                emit(
                    """\
{
    PyObject *imported_module = %(target_import_call)s;

    CHECK_OBJECT(imported_module);
    Py_DECREF(imported_module);
    %(value_name)s = %(value_import_call)s;
}
"""
                    % {
                        "value_name": value_name,
                        "target_import_call": target_import_call,
                        "value_import_call": value_import_call,
                    }
                )
        else:
            emit(
                """%s = IMPORT_MODULE_FIXED(tstate, %s, %s);"""
                % (
                    value_name,
                    context.getConstantCode(module_name.asString()),
                    context.getConstantCode(module_value_name.asString()),
                )
            )

        getErrorExitCode(
            check_name=value_name, needs_check=needs_check, emit=emit, context=context
        )

        context.addCleanupTempName(value_name)

        _emitFromlistModuleImports(
            expression=expression,
            module_value_name=value_name,
            emit=emit,
            context=context,
        )


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
        if imported_module_name == module_value_name:
            import_gives_ref, module_getter_code = getImportHardModuleGetterCode(
                module_name=imported_module_name,
                context=context,
                needs_check=needs_check,
            )

            emit("""%s = %s;""" % (value_name, module_getter_code))
        elif not isHardModule(module_value_name):
            # The imported module can be hard-imported while the value bound by
            # "import package.submodule" is still only the top level package.
            # In that case, use a normal fixed import to obtain that binding.
            emit(
                """%s = IMPORT_MODULE_FIXED(tstate, %s, %s);"""
                % (
                    value_name,
                    context.getConstantCode(imported_module_name.asString()),
                    context.getConstantCode(module_value_name.asString()),
                )
            )

            import_gives_ref = True
        else:
            import_gives_ref1, module_getter_code1 = getImportHardModuleGetterCode(
                module_name=imported_module_name,
                context=context,
                needs_check=needs_check,
            )
            import_gives_ref, module_getter_code2 = getImportHardModuleGetterCode(
                module_name=module_value_name,
                context=context,
                needs_check=needs_check,
            )

            if import_gives_ref1:
                if needs_check:
                    emit(
                        """\
{
    PyObject *fixed_module = %(module_getter_code1)s;

    if (unlikely(fixed_module == NULL)) {
        %(value_name)s = NULL;
    } else {
        Py_DECREF(fixed_module);
        %(value_name)s = %(module_getter_code2)s;
    }
}
"""
                        % {
                            "value_name": value_name,
                            "module_getter_code1": module_getter_code1,
                            "module_getter_code2": module_getter_code2,
                        }
                    )
                else:
                    emit(
                        """\
{
    PyObject *fixed_module = %(module_getter_code1)s;

    CHECK_OBJECT(fixed_module);
    Py_DECREF(fixed_module);
    %(value_name)s = %(module_getter_code2)s;
}
"""
                        % {
                            "value_name": value_name,
                            "module_getter_code1": module_getter_code1,
                            "module_getter_code2": module_getter_code2,
                        }
                    )
            else:
                emit(
                    """\
%(module_getter_code1)s;
%(value_name)s = %(module_getter_code2)s;
"""
                    % {
                        "value_name": value_name,
                        "module_getter_code1": module_getter_code1,
                        "module_getter_code2": module_getter_code2,
                    }
                )

        getErrorExitCode(
            check_name=value_name, needs_check=needs_check, emit=emit, context=context
        )

        if import_gives_ref:
            context.addCleanupTempName(value_name)

        _emitFromlistModuleImports(
            expression=expression,
            module_value_name=value_name,
            emit=emit,
            context=context,
        )


def generateConstantSysVersionInfoCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "imported_value", expression, emit, context
    ) as value_name:
        emit("""%s = Nuitka_SysGetObject("%s");""" % (value_name, "version_info"))

    getErrorExitCode(
        check_name=value_name, needs_check=False, emit=emit, context=context
    )


def getImportHardModuleGetterCode(module_name, context, needs_check):
    module = _getIncludedModule(module_name=module_name)

    if module is not None:
        loader_entry_ref = _getIncludedModuleEntryRef(module, context)

        if needs_check:
            module_getter_code = _getIncludedModuleImportCall(module, loader_entry_ref)
        else:
            # Guaranteed hard imports generate no result check and their
            # "IMPORT_HARD_*" helpers abort on failure, so the direct getter
            # must abort too instead of returning NULL unchecked.
            module_getter_code = (
                "Nuitka_ImportHardModuleEntry(tstate, &%(loader_entry_ref)s)"
                % {"loader_entry_ref": loader_entry_ref}
            )

        return True, module_getter_code

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
            module_name=module_name,
            context=context,
            needs_check=needs_check,
        )

        if import_gives_ref:
            release_code = "Py_DECREF(hard_module);"
        else:
            release_code = ""

        if needs_check:
            emit(
                """\
{
    PyObject *hard_module = %(module_getter_code)s;

    if (likely(hard_module != NULL)) {
        %(to_name)s = LOOKUP_ATTRIBUTE(tstate, hard_module, %(import_name)s);
        %(release_code)s
    } else {
        %(to_name)s = NULL;
    }
}
"""
                % {
                    "to_name": to_name,
                    "module_getter_code": module_getter_code,
                    "import_name": context.getConstantCode(import_name),
                    "release_code": release_code,
                }
            )
        else:
            emit(
                """\
{
    PyObject *hard_module = %(module_getter_code)s;

    %(to_name)s = LOOKUP_ATTRIBUTE(tstate, hard_module, %(import_name)s);
    %(release_code)s
}
"""
                % {
                    "to_name": to_name,
                    "module_getter_code": module_getter_code,
                    "import_name": context.getConstantCode(import_name),
                    "release_code": release_code,
                }
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

        import_gives_ref, module_getter_code = getImportHardModuleGetterCode(
            module_name=ModuleName("importlib"),
            context=context,
            needs_check=needs_check,
        )

        if import_gives_ref:
            release_hard_module_code = """\
    if (hard_module != NULL) {
        Py_DECREF(hard_module);
    }
"""
        else:
            release_hard_module_code = ""

        if package_name is None:
            call_code = """\
%(to_name)s = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, import_module_func, %(import_name)s);""" % {
                "to_name": value_name,
                "import_name": import_name,
            }
        else:
            call_code = """\
PyObject *args[2] = { %(import_name)s, %(package_name)s };
%(to_name)s = CALL_FUNCTION_WITH_ARGS2(tstate, import_module_func, args);""" % {
                "to_name": value_name,
                "import_name": import_name,
                "package_name": package_name,
            }

        emit(
            """\
{
    PyObject *hard_module = %(module_getter_code)s;
    PyObject *import_module_func;

    if (likely(hard_module != NULL)) {
        import_module_func = LOOKUP_ATTRIBUTE(tstate, hard_module, %(import_module_attr)s);
    } else {
        import_module_func = NULL;
    }
%(release_hard_module_code)s
    if (likely(import_module_func != NULL)) {
%(call_code)s
        Py_DECREF(import_module_func);
    } else {
        %(to_name)s = NULL;
    }
}
"""
            % {
                "module_getter_code": module_getter_code,
                "import_module_attr": context.getConstantCode("import_module"),
                "release_hard_module_code": release_hard_module_code,
                "call_code": call_code,
                "to_name": value_name,
            }
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
