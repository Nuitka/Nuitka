#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""NSIS backend for Windows installer creation.

This generates an NSIS script from the backend neutral installer manifest
and invokes the 'makensis' tool on it. The tool is looked up from an
explicit path, then 'PATH', and as a last resort from a cached download of
the official upstream release. NSIS is not redistributed or mirrored by
Nuitka, the download is cached locally for the user only.
"""

import os

from nuitka.options.Options import (
    assumeYesForDownloads,
    getProductVersionTuple,
)
from nuitka.Tracing import installer_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import (
    check_output,
    executeToolChecked,
    getExecutablePath,
)
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    getExternalUsePath,
    getFileContents,
    getNormalizedPathJoin,
    makePath,
    putTextFileContents,
)
from nuitka.utils.Utils import getArchitecture

# The NSIS version to download from upstream if not otherwise found. Most of
# NSIS is zlib/libpng licensed, but bundled compression modules have separate
# licenses, therefore it must only ever be fetched from upstream and cached
# for the user, and never be redistributed by Nuitka.
_nsis_version = "3.11"
_nsis_detected_version = None

_nsis_download_url = (
    "https://downloads.sourceforge.net/project/nsis/NSIS%%203/%(version)s/nsis-%(version)s.zip"
    % {"version": _nsis_version}
)

_desktop_shortcut_section = """\
Section "Desktop Shortcut" section_desktop_shortcut
  @SHELL_VAR_SETUP@

  SetOutPath "$INSTDIR"

  CreateShortcut "$DESKTOP\\@PRODUCT_NAME@.lnk" "$INSTDIR\\@MAIN_BINARY@"
SectionEnd
"""

_start_menu_shortcut_section = """\
Section "Start Menu Shortcut" section_start_menu_shortcut
  @SHELL_VAR_SETUP@

  SetOutPath "$INSTDIR"

  CreateShortcut "$SMPROGRAMS\\@PRODUCT_NAME@.lnk" "$INSTDIR\\@MAIN_BINARY@"
SectionEnd
"""


def getNsisVersion():
    """*str*, the detected NSIS version, or the download version."""
    if _nsis_detected_version is not None:
        return _nsis_detected_version

    return _nsis_version


def getRequiredMetadataFields():
    """Manifest fields the NSIS template requires, mapped to their options."""

    return {
        "product_name": "--product-name",
        "product_version": "--product-version",
        "company_name": "--company-name",
    }


def _escapeNsisString(value):
    """Escape a value for use inside a double quoted NSIS string."""
    return value.replace("$", "$$").replace('"', '$\\"')


def _escapeNsisStringKeepingVariables(value):
    """Escape a value but keep NSIS variable usages like '$PROGRAMFILES64'."""
    return value.replace('"', '$\\"')


def getNsisBinaryPath(installer_tool_path):
    """Locate the 'makensis' binary to use.

    Notes:
        Lookup order is the explicitly given path, then 'PATH', then a
        cached download of the official upstream NSIS release into the
        standard Nuitka tool cache.
    """
    # Singleton, pylint: disable=global-statement
    global _nsis_detected_version

    if installer_tool_path is not None:
        tool_path = getExecutablePath("makensis.exe", installer_tool_path)

        if tool_path is None:
            return installer_logger.sysexit(
                "Error, NSIS binary '%s' as given with '--windows-nsis-path' does not exist."
                % installer_tool_path
            )
    else:
        tool_path = getExecutablePath("makensis")

        if tool_path is None:
            tool_path = getCachedDownload(
                name="nsis",
                url=_nsis_download_url,
                is_arch_specific=None,
                specificity=_nsis_version,
                binary=r"nsis-%s\makensis.exe" % _nsis_version,
                unzip=True,
                flatten=False,
                message="""\
Nuitka will use NSIS from the official upstream download to create the \
Windows installer, it will be cached for future use.""",
                reject="Error, NSIS is required to create a Windows installer with the 'nsis' backend.",
                assume_yes_for_downloads=assumeYesForDownloads(),
                download_ok=True,
            )

        if tool_path is None:
            return None

    if _nsis_detected_version is None:
        version_output = check_output([tool_path, "/VERSION"])

        if str is not bytes:
            version_output = version_output.decode("utf8")

        _nsis_detected_version = version_output.strip()

    return tool_path


def _getInstallDirDefaults(product_name):
    """Default install directories for the three supported install modes."""

    per_user_dir = "$LOCALAPPDATA\\Programs\\%s" % product_name
    per_machine_dir = "%s\\%s" % (
        "$PROGRAMFILES" if getArchitecture() == "x86" else "$PROGRAMFILES64",
        product_name,
    )

    return per_user_dir, per_machine_dir


def _makeInstallDirCfg(
    install_dir_spec,
    install_mode,
    company_name,
    product_name,
    per_user_dir,
    per_machine_dir,
):
    """Generate the InstallDir and InstallDirRegKey lines for the script."""

    install_reg_key = _escapeNsisString(
        "Software\\%s\\%s" % (company_name, product_name)
    )

    if install_dir_spec is not None:
        install_dir = _escapeNsisStringKeepingVariables(install_dir_spec)
    elif install_mode == "machine":
        install_dir = per_machine_dir
    else:
        install_dir = per_user_dir

    if install_mode == "multiuser":
        # MultiUser provides its own install-directory and registry
        # remembering via MULTIUSER_PAGE_INSTALLMODE, no separate
        # InstallDir or InstallDirRegKey needed.
        return ""

    install_root_key = "HKLM" if install_mode == "machine" else "HKCU"

    return 'InstallDir "%s"\nInstallDirRegKey %s "%s" "InstallDir"' % (
        install_dir,
        install_root_key,
        install_reg_key,
    )


def _makeMultiUserHeader(install_mode, product_name, install_reg_key):
    """Generate the MultiUser !define / !include header block."""

    if install_mode == "multiuser":
        return (
            "!define MULTIUSER_EXECUTIONLEVEL Highest\n"
            "!define MULTIUSER_MUI\n"
            "!define MULTIUSER_INSTALLMODE_COMMANDLINE\n"
            '!define MULTIUSER_INSTALLMODE_INSTDIR "%s"\n'
            '!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY "%s"\n'
            '!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUENAME "InstallDir"\n'
            '!include "MultiUser.nsh"\n'
        ) % (product_name, install_reg_key)
    elif install_mode == "machine":
        return (
            "!define MULTIUSER_EXECUTIONLEVEL Highest\n"
            "!define MULTIUSER_INSTALLMODE_ALLUSERS\n"
            '!include "MultiUser.nsh"\n'
        )
    else:
        return (
            "!define MULTIUSER_EXECUTIONLEVEL Standard\n"
            "!define MULTIUSER_INSTALLMODE_CURRENTUSER\n"
            '!include "MultiUser.nsh"\n'
        )


def _makeMultiUserPage(install_mode):
    """Generate the MultiUser page insertion for the page order."""

    if install_mode == "multiuser":
        return "!insertmacro MULTIUSER_PAGE_INSTALLMODE"

    return ""


def _makeRequestExecutionLevel(install_mode):
    """Generate the RequestExecutionLevel directive."""

    if install_mode == "machine":
        return "RequestExecutionLevel admin"

    return ""


def _makeShellVarSetup(install_mode):
    """Generate the SetShellVarContext line(s) for the current install mode."""

    if install_mode == "multiuser":
        return """\
${if} $MultiUser.InstallMode == "AllUsers"
    SetShellVarContext all
${else}
    SetShellVarContext current
${endif}"""
    elif install_mode == "machine":
        return "SetShellVarContext all"

    return "SetShellVarContext current"


def _makeNsisScript(
    product_name,
    product_version,
    company_name,
    file_description,
    legal_copyright,
    icon_path,
    license_filename,
    allow_user_install_dir_change,
    shortcuts,
    install_dir_spec,
    install_mode,
    output_filename,
    payload_dir,
    payload_filename,
    main_binary_name,
    external_files,
):
    """Create the NSIS script source from the installer manifest."""
    # Plenty of decisions to make here,
    # pylint: disable=too-many-arguments,too-many-branches,too-many-locals

    template_filename = getNormalizedPathJoin(
        os.path.dirname(os.path.abspath(__file__)), "NsisTemplate.nsi"
    )

    script_source = getFileContents(filename=template_filename, encoding="utf8")

    escaped_product_name = _escapeNsisString(product_name)
    escaped_company_name = _escapeNsisString(company_name)

    per_user_dir, per_machine_dir = _getInstallDirDefaults(escaped_product_name)

    install_reg_key = _escapeNsisString(
        "Software\\%s\\%s" % (company_name, product_name)
    )

    multi_user_header = _makeMultiUserHeader(
        install_mode, escaped_product_name, install_reg_key
    )

    # Optional icon for the installer.
    if icon_path is not None:
        mui_icon_define = '!define MUI_ICON "%s"' % _escapeNsisString(
            os.path.abspath(icon_path)
        )
    else:
        mui_icon_define = ""

    # Optional license page.
    if license_filename is not None:
        if not os.path.isfile(license_filename):
            return installer_logger.sysexit(
                "Error, license file '%s' as given with '--windows-installer-license-file' does not exist."
                % license_filename
            )

        license_page = '!insertmacro MUI_PAGE_LICENSE "%s"' % _escapeNsisString(
            os.path.abspath(license_filename)
        )
    else:
        license_page = ""

    # End user install directory override is the default, but can be
    # disabled by the deployment maker.  MultiUser mode has its own
    # directory page embedded in the MULTIUSER_PAGE_INSTALLMODE macro.
    if install_mode == "multiuser":
        directory_page = ""
    elif allow_user_install_dir_change:
        directory_page = "!insertmacro MUI_PAGE_DIRECTORY"
    else:
        directory_page = ""

    # Optional shortcut sections, these are selectable by the end user
    # through the components page if present.
    shortcut_sections = []

    if "desktop" in shortcuts:
        shortcut_sections.append(_desktop_shortcut_section)
    if "start-menu" in shortcuts:
        shortcut_sections.append(_start_menu_shortcut_section)

    if shortcut_sections:
        components_page = "!insertmacro MUI_PAGE_COMPONENTS"
    else:
        components_page = ""

    if install_dir_spec is not None:
        install_dir = _escapeNsisStringKeepingVariables(install_dir_spec)
    elif install_mode == "machine":
        install_dir = per_machine_dir
    else:
        install_dir = per_user_dir

    product_version_4 = "%d.%d.%d.%d" % getProductVersionTuple()

    # Payload commands, either the whole dist folder contents, or the single
    # onefile program binary.
    if payload_dir is not None:
        payload_commands = 'File /r "%s\\*"' % _escapeNsisString(
            os.path.abspath(payload_dir)
        )
    else:
        payload_commands = 'File "%s"' % _escapeNsisString(
            os.path.abspath(payload_filename)
        )

    for external_file in external_files:
        payload_commands += '\n  File "%s"' % _escapeNsisString(
            os.path.abspath(external_file)
        )

    replacements = {
        "@MULTIUSER_HEADER@": multi_user_header,
        "@PRODUCT_NAME@": escaped_product_name,
        "@PRODUCT_VERSION@": _escapeNsisString(product_version),
        "@PRODUCT_VERSION_4@": product_version_4,
        "@COMPANY_NAME@": escaped_company_name,
        "@FILE_DESCRIPTION@": _escapeNsisString(
            file_description or "%s Installer" % product_name
        ),
        "@LEGAL_COPYRIGHT@": _escapeNsisString(legal_copyright or ""),
        "@OUTPUT_FILENAME@": _escapeNsisString(os.path.abspath(output_filename)),
        "@REQUEST_EXECUTION_LEVEL@": _makeRequestExecutionLevel(install_mode),
        "@INSTALLDIR_CFG@": _makeInstallDirCfg(
            install_dir_spec,
            install_mode,
            company_name,
            product_name,
            per_user_dir,
            per_machine_dir,
        ),
        "@MULTIUSER_PAGE@": _makeMultiUserPage(install_mode),
        "@SHELL_VAR_SETUP@": _makeShellVarSetup(install_mode),
        "@PAYLOAD_COMMANDS@": payload_commands,
        "@MAIN_BINARY@": _escapeNsisString(main_binary_name),
        "@INSTALL_DIR@": install_dir,
        "@INSTALL_REG_KEY@": install_reg_key,
        "@UNINSTALL_REG_KEY@": _escapeNsisString(
            "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%s" % product_name
        ),
        "@MUI_ICON_DEFINE@": mui_icon_define,
        "@LICENSE_PAGE@": license_page,
        "@COMPONENTS_PAGE@": components_page,
        "@DIRECTORY_PAGE@": directory_page,
        "@SHORTCUT_SECTIONS@": "\n".join(shortcut_sections),
    }

    # Shortcut sections contain tokens themselves, so replace repeatedly
    # until all tokens are resolved.
    script_source = script_source.replace(
        "@SHORTCUT_SECTIONS@", replacements["@SHORTCUT_SECTIONS@"]
    )

    for token, value in replacements.items():
        script_source = script_source.replace(token, value)

    return script_source


def createNsisInstaller(
    product_name,
    product_version,
    company_name,
    file_description,
    legal_copyright,
    icon_path,
    license_filename,
    allow_user_install_dir_change,
    shortcuts,
    install_dir_spec,
    install_mode,
    output_filename,
    payload_dir,
    payload_filename,
    main_binary_name,
    external_files,
    installer_tool_path,
):
    """Create the Windows installer executable with NSIS.

    Returns:
        Filename of the created installer, or None if only the script
        generation was requested.
    """
    # pylint: disable=too-many-arguments,too-many-locals

    script_source = _makeNsisScript(
        product_name=product_name,
        product_version=product_version,
        company_name=company_name,
        file_description=file_description,
        legal_copyright=legal_copyright,
        icon_path=icon_path,
        license_filename=license_filename,
        allow_user_install_dir_change=allow_user_install_dir_change,
        shortcuts=shortcuts,
        install_dir_spec=install_dir_spec,
        install_mode=install_mode,
        output_filename=output_filename,
        payload_dir=payload_dir,
        payload_filename=payload_filename,
        main_binary_name=main_binary_name,
        external_files=external_files,
    )

    if payload_dir is not None:
        installer_base_path = payload_dir
    else:
        installer_base_path = payload_filename

    installer_build_dir = changeFilenameExtension(
        getExternalUsePath(installer_base_path), ".installer-build"
    )

    makePath(installer_build_dir)

    script_filename = getNormalizedPathJoin(installer_build_dir, "installer.nsi")

    putTextFileContents(
        filename=script_filename, contents=script_source, encoding="utf8"
    )

    installer_logger.info("Created NSIS script '%s'." % script_filename)

    nsis_binary = getNsisBinaryPath(installer_tool_path=installer_tool_path)

    installer_logger.info("Creating Windows installer '%s'..." % output_filename)

    executeToolChecked(
        logger=installer_logger,
        command=[nsis_binary, "/V2", script_filename],
        absence_message="""\
Error, cannot find NSIS 'makensis' tool necessary to create the Windows \
installer, use '--windows-nsis-path' to provide it.""",
        stderr_filter=None,
    )

    if not os.path.exists(output_filename):
        return installer_logger.sysexit(
            "Error, NSIS did not create the expected installer '%s'." % output_filename
        )

    installer_logger.info("Created Windows installer '%s'." % output_filename)

    return output_filename


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
