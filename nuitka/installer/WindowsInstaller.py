#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Windows installer creation for standalone and onefile deployments.

This module collects the options, validates payload, invokes the NSIS
backend, and fires the ``onInstallerOutput`` hook.
"""

import os

from nuitka.freezer.IncludedDataFiles import getIncludedDataFiles
from nuitka.options.Options import (
    getCompanyName,
    getFileDescription,
    getInstallerOutputFilename,
    getLegalCopyright,
    getOutputFilename,
    getOutputPath,
    getProductName,
    getProductVersion,
    getWindowsIconPaths,
    isOnefileMode,
    shallCreateWindowsInstaller,
)
from nuitka.OutputDirectories import (
    getResultFullpath,
    getStandaloneDirectoryPath,
)
from nuitka.plugins.Hooks import onInstallerOutput
from nuitka.Tracing import installer_logger
from nuitka.utils.FileOperations import changeFilenameExtension, relpath

from .backends.NsisBackend import createNsisInstaller


def computeWindowsInstallerOutputFilename():
    """Return the absolute output path for the Windows installer.

    Returns *None* if installer creation was not requested.
    """
    if not shallCreateWindowsInstaller():
        return None

    output_filename = getInstallerOutputFilename()

    if output_filename is None:
        output_filename = getOutputFilename()

    if output_filename is None:
        if isOnefileMode():
            base = getResultFullpath(onefile=True, real=True)
        else:
            base = getStandaloneDirectoryPath(bundle=True, real=True)

        output_filename = changeFilenameExtension(base, "-setup.exe")

    return getOutputPath(path=output_filename)


def _checkPayload(payload_dir, payload_filename, main_binary_name):
    if payload_dir is not None:
        if not os.path.isdir(payload_dir):
            return installer_logger.sysexit(
                "Error, installer payload directory '%s' does not exist." % payload_dir
            )

        main_binary_path = os.path.join(payload_dir, main_binary_name)

        if not os.path.isfile(main_binary_path):
            return installer_logger.sysexit(
                "Error, installer payload main program '%s' does not exist."
                % main_binary_path
            )
    else:
        if not os.path.isfile(payload_filename):
            return installer_logger.sysexit(
                "Error, installer payload program '%s' does not exist."
                % payload_filename
            )


def createWindowsInstaller(
    installer_tool_path,
    output_filename,
    install_dir_spec,
    shortcuts,
    license_filename,
    allow_user_install_dir_change,
    install_mode,
):
    """Create a Windows installer artifact from the compiled result.

    Returns:
        Filename of the created artifact, or None if none was created.
    """
    if isOnefileMode():
        payload_dir = None
        payload_filename = getResultFullpath(onefile=True, real=True)
        main_binary_name = os.path.basename(payload_filename)
    else:
        payload_dir = getStandaloneDirectoryPath(bundle=True, real=True)
        payload_filename = None
        main_binary_name = relpath(
            path=getResultFullpath(onefile=False, real=True), start=payload_dir
        )

    icon_paths = getWindowsIconPaths()

    if output_filename is not None:
        output_filename = getOutputPath(path=output_filename)

    _checkPayload(payload_dir, payload_filename, main_binary_name)

    external_files = [
        included_datafile.dest_path
        for included_datafile in getIncludedDataFiles()
        if included_datafile.isExternal()
    ]

    artifact_filename = createNsisInstaller(
        product_name=getProductName(),
        product_version=getProductVersion(),
        company_name=getCompanyName(),
        file_description=getFileDescription(),
        legal_copyright=getLegalCopyright(),
        icon_path=icon_paths[0] if icon_paths else None,
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
        installer_tool_path=installer_tool_path,
    )

    onInstallerOutput(filename=artifact_filename)

    return artifact_filename


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
