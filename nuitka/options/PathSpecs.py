#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Path specifications and templating."""

import os

from nuitka.Tracing import onefile_logger, options_logger
from nuitka.utils.FileOperations import getUserInputNormalizedPath, isLegalPath

from .OptionParsing import run_time_variable_names


def _convertOldStylePathSpecQuotes(value):
    quote = None

    result = ""
    for c in value:
        if c == "%":
            if quote is None:
                quote = "{"
                result += quote
            elif quote == "{":
                result += "}"
                quote = None
        else:
            result += c

    return result


def checkPathSpec(value, arg_name, allow_disable):
    # There are never enough checks here and sysexit is returned,
    # pylint: disable=too-many-branches,too-many-return-statements
    from .Options import (
        getCompanyName,
        getFileVersionTuple,
        getProductName,
        getProductVersionTuple,
    )

    old = value
    value = _convertOldStylePathSpecQuotes(value)
    if old != value:
        options_logger.warning(
            "Adapted '%s' option value from legacy quoting style to '%s' -> '%s'"
            % (arg_name, old, value)
        )

    # This changes the '/' to '\\' on Windows at least.
    value = getUserInputNormalizedPath(value)

    if "\n" in value or "\r" in value:
        return options_logger.sysexit(
            "Using a new line in value '%s=%r' value is not allowed."
            % (arg_name, value)
        )

    if "{NONE}" in value:
        if not allow_disable:
            return options_logger.sysexit(
                "Using value '{NONE}' in '%s=%s' value is not allowed."
                % (arg_name, value)
            )

        if value != "{NONE}":
            return options_logger.sysexit(
                "Using value '{NONE}' in '%s=%s' value does not allow anything else used too."
                % (arg_name, value)
            )

    if "{NULL}" in value:
        if not allow_disable:
            return options_logger.sysexit(
                "Using value '{NULL}' in '%s=%s' value is not allowed."
                % (arg_name, value)
            )

        if value != "{NULL}":
            return options_logger.sysexit(
                "Using value '{NULL}' in '%s=%s' value does not allow anything else used too."
                % (arg_name, value)
            )

    if "{COMPANY}" in value and not getCompanyName():
        return options_logger.sysexit(
            "Using value '{COMPANY}' in '%s=%s' value without '--company-name' being specified."
            % (arg_name, value)
        )

    if "{PRODUCT}" in value and not getProductName():
        return options_logger.sysexit(
            "Using value '{PRODUCT}' in '%s=%s' value without '--product-name' being specified."
            % (arg_name, value)
        )

    if "{VERSION}" in value and not (getFileVersionTuple() or getProductVersionTuple()):
        return options_logger.sysexit(
            "Using value '{VERSION}' in '%s=%s' value without '--product-version' or '--file-version' being specified."
            % (arg_name, value)
        )

    if "{FILE_VERSION}" in value and not getFileVersionTuple():
        return options_logger.sysexit(
            "Using value '{FILE_VERSION}' in '%s=%s' value without '--file-version' being specified."
            % (arg_name, value)
        )

    if "{PRODUCT_VERSION}" in value and not getProductVersionTuple():
        return options_logger.sysexit(
            "Using value '{PRODUCT_VERSION}' in '%s=%s' value without '--product-version' being specified."
            % (arg_name, value)
        )

    if value.count("{") != value.count("}"):
        return options_logger.sysexit("""Unmatched '{}' is wrong for '%s=%s' and may \
definitely not do what you want it to do.""" % (arg_name, value))

    # Catch nested or illegal variable names.
    var_name = None
    for c in value:
        if c in "{":
            if var_name is not None:
                return options_logger.sysexit(
                    """Nested '{' is wrong for '%s=%s'.""" % (arg_name, value)
                )
            var_name = ""
        elif c == "}":
            if var_name is None:
                return options_logger.sysexit(
                    """Stray '}' is wrong for '%s=%s'.""" % (arg_name, value)
                )

            if var_name not in run_time_variable_names:
                return onefile_logger.sysexit(
                    "Found unknown variable name '{%s}' in for '%s=%s'."
                    "" % (var_name, arg_name, value)
                )

            var_name = None
        else:
            if var_name is not None:
                var_name += c

    for candidate in (
        "{PROGRAM}",
        "{PROGRAM_BASE}",
        "{PROGRAM_DIR}",
        "{CACHE_DIR}",
        "{HOME}",
        "{TEMP}",
    ):
        if candidate in value[1:]:
            return options_logger.sysexit("""\
Absolute run time paths of '%s' can only be at the start of \
'%s=%s', using it in the middle of it is not allowed.""" % (candidate, arg_name, value))

        if candidate == value:
            return options_logger.sysexit("""Cannot use folder '%s', may only be the \
start of '%s=%s', using that alone is not allowed.""" % (candidate, arg_name, value))

        if value.startswith(candidate) and candidate != "{PROGRAM_BASE}":
            if value[len(candidate)] != os.path.sep:
                return options_logger.sysexit(
                    """Cannot use general system folder %s, without a path \
separator '%s=%s', just appending to these is not allowed, needs to be \
below them.""" % (candidate, arg_name, value)
                )

    is_legal, reason = isLegalPath(value)
    if not is_legal:
        return options_logger.sysexit(
            """Cannot use illegal paths '%s=%s', due to %s."""
            % (arg_name, value, reason)
        )

    return value


def expandPathSpec(value):
    """Expand templated variables like {VERSION} into their actual string values.

    Notes:
        This evaluates the compile time available variables. Values like
        {PID} are not available and evaluated at run time by the binary.
    """
    from .Options import (
        getCompanyName,
        getFileVersion,
        getProductName,
        getProductVersion,
    )

    if "{VERSION}" in value:

        product_version = getProductVersion()
        file_version = getFileVersion()

        if file_version is not None and product_version is not None:
            effective_version = "%s-%s" % (
                product_version,
                file_version,
            )
        else:
            effective_version = file_version or product_version

        value = value.replace("{VERSION}", effective_version or "")

    if "{FILE_VERSION}" in value:
        version = getFileVersion() or ""
        value = value.replace("{FILE_VERSION}", version)

    if "{PRODUCT_VERSION}" in value:
        version = getProductVersion() or ""
        value = value.replace("{PRODUCT_VERSION}", version)

    if "{COMPANY}" in value:
        company = getCompanyName() or ""
        value = value.replace("{COMPANY}", company)

    if "{PRODUCT}" in value:
        product = getProductName() or ""
        value = value.replace("{PRODUCT}", product)

    return value


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
