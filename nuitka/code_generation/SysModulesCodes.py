#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for "sys.modules" operations."""

from nuitka.ModuleRegistry import getModuleByName

from .CodeHelpers import (
    generateChildExpressionCode,
    generateChildExpressionsCode,
    generateExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode
from .LineNumberCodes import emitLineNumberUpdateCode
from .LoaderCodes import getModuleEntryCodeName


def _getSysModulesEntryRef(module_name, context):
    """Get C code for the loader entry of a statically known module.

    Args:
        module_name: ModuleName of the target, or None.
        context: Code generation context.

    Returns:
        C code for the entry pointer, or "NULL" if there is no included entry.
    """
    if module_name is None:
        return "NULL"

    module = getModuleByName(module_name)

    if module is None:
        return "NULL"

    entry_ref = getModuleEntryCodeName(module.getFullName())

    if not context.hasDeclaration(entry_ref):
        context.addDeclaration(
            entry_ref,
            "extern struct Nuitka_MetaPathBasedLoaderEntry %s;" % entry_ref,
        )

    return "&%s" % entry_ref


def _getSysModulesReservedValueCode(module_name):  # pylint: disable=unused-argument
    # The module name is reserved for future use.
    return "0"


def generateImportlibReloadCallCode(to_name, expression, emit, context):
    module_name = generateChildExpressionCode(
        expression=expression.subnode_module, emit=emit, context=context
    )

    emitLineNumberUpdateCode(expression, emit, context)

    with withObjectCodeTemporaryAssignment(
        to_name, "reloaded_module", expression, emit, context
    ) as value_name:
        emit("%s = Nuitka_ReloadModule(tstate, %s);" % (value_name, module_name))

        getErrorExitCode(
            check_name=value_name,
            release_names=(module_name,),
            needs_check=True,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateSysModulesRefCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "sys_modules_value", expression, emit, context
    ) as value_name:
        emit('%s = Nuitka_SysGetObject("modules");' % value_name)


def generateSysModulesLookupCode(to_name, expression, emit, context):
    sys_modules_name, subscript_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    entry_ref = _getSysModulesEntryRef(
        module_name=expression.getModuleName(), context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "sys_modules_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = Nuitka_LookupSysModulesValue(tstate, %s, %s, %s);"
            % (value_name, sys_modules_name, entry_ref, subscript_name)
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(sys_modules_name, subscript_name),
            needs_check=True,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def _generateSysModulesCallCode(to_name, expression, emit, context, get_call):
    entry_ref = _getSysModulesEntryRef(
        module_name=expression.getModuleName(), context=context
    )

    value_names = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    dict_name = value_names[0]
    key_name = value_names[1]
    default_name = value_names[2] if len(value_names) > 2 else None

    with withObjectCodeTemporaryAssignment(
        to_name, "sys_modules_value", expression, emit, context
    ) as value_name:
        if get_call:
            emit(
                "%s = Nuitka_GetSysModulesValue(tstate, %s, %s, %s, %s);"
                % (
                    value_name,
                    dict_name,
                    entry_ref,
                    key_name,
                    default_name if default_name is not None else "NULL",
                )
            )
        else:
            emit(
                "%s = Nuitka_PopSysModulesValue(tstate, %s, %s, %s, %s, %s);"
                % (
                    value_name,
                    dict_name,
                    entry_ref,
                    key_name,
                    default_name if default_name is not None else "NULL",
                    _getSysModulesReservedValueCode(expression.getModuleName()),
                )
            )

        getErrorExitCode(
            check_name=value_name,
            release_names=(dict_name, key_name)
            + ((default_name,) if default_name is not None else ()),
            # "pop" can raise KeyError even when the key is known hashable.
            # For "get" only an unknown hashable key can cause an exception.
            needs_check=(not get_call) or (not expression.known_hashable_key),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateSysModulesGetCode(to_name, expression, emit, context):
    _generateSysModulesCallCode(
        to_name=to_name,
        expression=expression,
        emit=emit,
        context=context,
        get_call=True,
    )


def generateSysModulesPopCode(to_name, expression, emit, context):
    _generateSysModulesCallCode(
        to_name=to_name,
        expression=expression,
        emit=emit,
        context=context,
        get_call=False,
    )


def generateSysModulesAssignmentCode(statement, emit, context):
    value_name, sys_modules_name, subscript_name = generateExpressionsCode(
        expressions=(
            statement.subnode_source,
            statement.subnode_subscribed,
            statement.subnode_subscript,
        ),
        names=("sys_modules_value", "sys_modules_dict", "sys_modules_key"),
        emit=emit,
        context=context,
    )

    entry_ref = _getSysModulesEntryRef(
        module_name=statement.getModuleName(), context=context
    )

    res_name = context.getBoolResName()

    emit(
        "%s = Nuitka_SetSysModulesValue(tstate, %s, %s, %s, %s, %s);"
        % (
            res_name,
            sys_modules_name,
            entry_ref,
            subscript_name,
            value_name,
            _getSysModulesReservedValueCode(statement.getModuleName()),
        )
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(value_name, sys_modules_name, subscript_name),
        emit=emit,
        context=context,
    )


def generateSysModulesDelCode(statement, emit, context):
    sys_modules_name, subscript_name = generateExpressionsCode(
        expressions=(statement.subnode_subscribed, statement.subnode_subscript),
        names=("sys_modules_dict", "sys_modules_key"),
        emit=emit,
        context=context,
    )

    entry_ref = _getSysModulesEntryRef(
        module_name=statement.getModuleName(), context=context
    )

    res_name = context.getBoolResName()

    emit(
        "%s = Nuitka_DelSysModulesValue(tstate, %s, %s, %s, %s);"
        % (
            res_name,
            sys_modules_name,
            entry_ref,
            subscript_name,
            _getSysModulesReservedValueCode(statement.getModuleName()),
        )
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(sys_modules_name, subscript_name),
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
