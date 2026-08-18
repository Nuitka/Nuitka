#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Low level constant code generation.

This deals with constants, there creation, there access, and some checks about
them. Even mutable constants should not change during the course of the
program.

There are shared constants, which are created for multiple modules to use, you
can think of them as globals. And there are module local constants, which are
for a single module only.

"""

import os
import sys

from nuitka.__past__ import unicode
from nuitka.build.DataComposerInterface import getConstantBlobSymbolName
from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.ModuleRegistry import getRootTopModule, hasDoneModule
from nuitka.options.Options import (
    isStandaloneMode,
    shallMakeModule,
    shallUseDirectConstantBlobs,
)
from nuitka.PythonVersions import python_version
from nuitka.Serialization import GlobalConstantAccessor
from nuitka.utils.CStrings import encodePythonStringToC
from nuitka.utils.Distributions import (
    getDistribution,
    getDistributionTopLevelPackageNames,
)
from nuitka.Version import getNuitkaVersionTuple

from .CodeHelpers import withObjectCodeTemporaryAssignment
from .ErrorCodes import getAssertionCode, getReleaseCode
from .GlobalConstants import getConstantDefaultPopulation
from .Namify import namifyConstant
from .SpecialConstantData import hasSpecialDetails
from .templates.CodeTemplatesConstants import template_constants_reading
from .templates.CodeTemplatesModules import template_header_guard


def generateConstantReferenceCode(to_name, expression, emit, context):
    """Assign the constant behind the expression to to_name."""

    to_name.getCType().emitAssignmentCodeFromConstant(
        to_name=to_name,
        constant=expression.getCompileTimeConstant(),
        # Derive this from context.
        may_escape=True,
        emit=emit,
        context=context,
    )


def generateConstantGenericAliasCode(to_name, expression, emit, context):
    # TODO: Have these as prepared constants as well, if args are not mutable.

    origin_name = context.allocateTempName("generic_alias_origin")
    args_name = context.allocateTempName("generic_alias_args")

    origin_name.getCType().emitAssignmentCodeFromConstant(
        to_name=origin_name,
        constant=expression.getCompileTimeConstant().__origin__,
        may_escape=True,
        emit=emit,
        context=context,
    )

    args_name.getCType().emitAssignmentCodeFromConstant(
        to_name=args_name,
        constant=expression.getCompileTimeConstant().__args__,
        may_escape=True,
        emit=emit,
        context=context,
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "builtin_value", expression, emit, context
    ) as value_name:
        emit("%s = Py_GenericAlias(%s, %s);" % (value_name, origin_name, args_name))

        getAssertionCode(check="%s != NULL" % value_name, emit=emit)

        getReleaseCode(origin_name, emit, context)
        getReleaseCode(args_name, emit, context)

        context.addCleanupTempName(value_name)


def getConstantsDefinitionCode():
    """Create the code code "__constants.c" and "__constants.h" files.

    This needs to create code to make all global constants (used in more
    than one module) and create them.

    """
    # Somewhat detail rich, pylint: disable=too-many-locals

    constant_accessor = GlobalConstantAccessor(
        data_filename="__constants.const", top_level_name="global_constants"
    )

    lines = []

    for constant_value in getConstantDefaultPopulation():
        identifier = constant_accessor.getConstantCode(constant_value)

        assert "[" in identifier, (identifier, constant_value)

        lines.append("// %s" % repr(constant_value))
        lines.append(
            "#define const_%s %s" % (namifyConstant(constant_value), identifier)
        )

    sys_executable = None

    if not shallMakeModule():
        if isStandaloneMode():
            # The directory is added back at run time.
            sys_executable = constant_accessor.getConstantCode(
                os.path.basename(sys.executable)
            )
        else:
            sys_executable = constant_accessor.getConstantCode(sys.executable)

    sys_prefix = None
    sys_base_prefix = None
    sys_exec_prefix = None
    sys_base_exec_prefix = None

    # TODO: This part is needed for main program only, so do it there?
    if not shallMakeModule() and not isStandaloneMode():
        sys_prefix = constant_accessor.getConstantCode(sys.prefix)
        sys_exec_prefix = constant_accessor.getConstantCode(sys.exec_prefix)

        if python_version >= 0x300:
            sys_base_prefix = constant_accessor.getConstantCode(sys.base_prefix)
            sys_base_exec_prefix = constant_accessor.getConstantCode(
                sys.base_exec_prefix
            )

    runtime_metadata_values = tuple(
        (
            distribution_name,
            (
                metadata_value.module_name,
                metadata_value.metadata,
                metadata_value.entry_points_data,
            ),
        )
        for distribution_name, metadata_value in getDistributionMetadataValues()
    )

    metadata_values_code = constant_accessor.getConstantCode(runtime_metadata_values)

    lines.insert(
        0,
        "extern PyObject *global_constants[%d];"
        % constant_accessor.getConstantsCount(),
    )

    header = template_header_guard % {
        "header_guard_name": "__NUITKA_GLOBAL_CONSTANTS_H__",
        "header_body": "\n".join(lines),
    }

    major, minor, micro, is_final, _rc_number = getNuitkaVersionTuple()

    body = template_constants_reading % {
        "module_name_cstr": encodePythonStringToC(
            getRootTopModule().getFullName().asString().encode("utf8")
        ),
        "global_constants_count": constant_accessor.getConstantsCount(),
        "global_constants_blob_symbol_name": getConstantBlobSymbolName(
            "__constants.const"
        ),
        "use_direct_constant_blobs": 1 if shallUseDirectConstantBlobs() else 0,
        "sys_executable": sys_executable,
        "sys_prefix": sys_prefix,
        "sys_base_prefix": sys_base_prefix,
        "sys_exec_prefix": sys_exec_prefix,
        "sys_base_exec_prefix": sys_base_exec_prefix,
        "nuitka_version_major": major,
        "nuitka_version_minor": minor,
        "nuitka_version_micro": micro,
        "nuitka_version_level": "release" if is_final else "candidate",
        "metadata_values": metadata_values_code,
    }

    return header, body


def getModuleConstantsDeclAndChecks(context):
    constants_count = context.getConstantsCount()
    constant_infos = context.getConstantInfos()

    module_constants_decl = "\n".join(
        "%s %s;" % (c_type, name) for name, c_type in constant_infos
    )

    check_lines = []
    verify_lines = []

    for i, (name, c_type) in enumerate(constant_infos):
        if hasSpecialDetails(name):
            details = context.getConstantDetails(name)
            check_lines.append(
                """\
mod_consts_hash[%(index)d] = 0;
DEEP_HASH_BLOB(&mod_consts_hash[%(index)d], mod_consts.%(name)s, %(size)d);"""
                % {"index": i, "name": name, "size": details["size"]}
            )
            verify_lines.append("""\
{
    Py_hash_t h = 0;
    DEEP_HASH_BLOB(&h, mod_consts.%(name)s, %(size)d);
    assert(mod_consts_hash[%(index)d] == h);
}""" % {"name": name, "index": i, "size": details["size"]})
        else:
            check_lines.append(
                """\
CHECK_OBJECT_DEEP_NAMED("mod_consts.%(name)s", mod_consts.%(name)s);
mod_consts_hash[%(index)d] = DEEP_HASH(tstate, mod_consts.%(name)s);"""
                % {"name": name, "index": i}
            )
            verify_lines.append(
                """\
CHECK_OBJECT_DEEP_NAMED("mod_consts.%(name)s", mod_consts.%(name)s);
assert(mod_consts_hash[%(index)d] == DEEP_HASH(tstate, mod_consts.%(name)s) && "mod_consts.%(name)s");"""
                % {"name": name, "index": i}
            )

    module_constants_check_hash = "\n".join(check_lines)
    module_constants_check_object = "\n".join(verify_lines)

    return (
        constants_count,
        module_constants_decl,
        module_constants_check_hash,
        module_constants_check_object,
    )


MetaDataDescription = makeNamedtupleClass(
    "MetaDataDescription",
    (
        "module_name",
        "metadata",
        "entry_points_data",
        "reasons",
    ),
)

_metadata_values = {}


def addDistributionMetadataValue(distribution_name, distribution, reason):
    assert type(distribution_name) in (str, unicode), distribution_name

    # Extract what we need to from the distribution object.
    if distribution_name not in _metadata_values:
        # The user doesn't have this handy.
        if distribution is None:
            distribution = getDistribution(distribution_name)

        metadata = str(
            distribution.read_text("METADATA")
            or distribution.read_text("PKG-INFO")
            or ""
        )

        entry_points_data = str(distribution.read_text("entry_points.txt") or "")

        module_name = getDistributionTopLevelPackageNames(distribution=distribution)[0]

        _metadata_values[distribution_name] = MetaDataDescription(
            module_name=module_name,
            metadata=metadata,
            entry_points_data=entry_points_data,
            reasons=[reason],
        )
    else:
        _metadata_values[distribution_name].reasons.append(reason)


def getDistributionMetadataValues():
    result = []

    for distribution_name, value in _metadata_values.items():
        if "user requested" not in value.reasons and not hasDoneModule(
            value.module_name
        ):
            continue

        result.append((distribution_name, value))

    return sorted(result)


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
