#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for 'sys.modules' operations."""

from nuitka.ModuleRegistry import getModuleByName

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionCode,
    generateExpressionsCode,
)
from .LineNumberCodes import emitLineNumberUpdateCode
from .LoaderCodes import getModuleEntryCodeName
from .PythonAPICodes import (
    CArg,
    generateCAPIObjectCode,
    generateCAPIObjectCode0,
    getCAPIErrorCode,
    getCAPIObjectCode,
)


def _getSysModulesEntryRef(module_name, context):
    """Return '&entry_...' C expression for an included 'module_name', or 'NULL'."""
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

    getCAPIObjectCode(
        to_name=to_name,
        capi="Nuitka_ReloadModule",
        arg_names=("tstate", module_name),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        ref_count=1,
        release_names=(module_name,),
        emit=emit,
        context=context,
    )


def generateSysModulesRefCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name=to_name,
        capi="Nuitka_SysGetObject",
        tstate=False,
        arg_desc=(CArg('"modules"'),),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateSysModulesLookupCode(to_name, expression, emit, context):
    entry_ref = _getSysModulesEntryRef(
        module_name=expression.getModuleName(), context=context
    )

    generateCAPIObjectCode(
        to_name=to_name,
        capi="Nuitka_LookupSysModulesValue",
        tstate=True,
        arg_desc=(
            ("expression_value", expression.subnode_expression),
            CArg(entry_ref),
            ("subscript_value", expression.subnode_subscript),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def _generateSysModulesCallCode(to_name, expression, emit, context, get_call):
    entry_ref = _getSysModulesEntryRef(
        module_name=expression.getModuleName(), context=context
    )

    arg_desc = (
        ("dict_arg_value", expression.subnode_dict_arg),
        CArg(entry_ref),
        ("key_value", expression.subnode_key),
        ("default_value", getattr(expression, "subnode_default", None)),
    )

    if get_call:
        capi = "Nuitka_GetSysModulesValue"
    else:
        capi = "Nuitka_PopSysModulesValue"
        arg_desc += (CArg(_getSysModulesReservedValueCode(expression.getModuleName())),)

    generateCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        tstate=True,
        arg_desc=arg_desc,
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


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

    getCAPIErrorCode(
        capi="Nuitka_SetSysModulesValue",
        arg_names=(
            "tstate",
            sys_modules_name,
            entry_ref,
            subscript_name,
            value_name,
            _getSysModulesReservedValueCode(statement.getModuleName()),
        ),
        may_raise=statement.mayRaiseExceptionOperation(),
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

    getCAPIErrorCode(
        capi="Nuitka_DelSysModulesValue",
        arg_names=(
            "tstate",
            sys_modules_name,
            entry_ref,
            subscript_name,
            _getSysModulesReservedValueCode(statement.getModuleName()),
        ),
        may_raise=statement.mayRaiseExceptionOperation(),
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
