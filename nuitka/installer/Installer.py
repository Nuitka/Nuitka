#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Installer creation dispatch.

Provides the single entry point 'createInstaller' called from the end of
compilation in 'MainControl'. It dispatches to the appropriate platform
implementation, so macOS DMG creation and Windows installer creation share
one call site.
"""

from nuitka.options.Options import (
    getLinuxInstallerAppImagetoolPath,
    getWindowsInstallerInstallDir,
    getWindowsInstallerLicenseFile,
    getWindowsInstallerMode,
    getWindowsInstallerNsisPath,
    getWindowsInstallerOutputFilename,
    getWindowsInstallerShortcuts,
    isStandaloneMode,
    isWindowsInstallerAllowUserChangeInstallDir,
    shallCreateDmgFile,
    shallCreateLinuxInstaller,
    shallCreateWindowsInstaller,
)
from nuitka.OutputDirectories import getStandaloneDirectoryPath
from nuitka.utils.FileOperations import changeFilenameExtension

from .backends.AppImageBackend import getAppImageToolVersion
from .backends.NsisBackend import getNsisVersion
from .LinuxInstaller import (
    computeLinuxInstallerOutputFilename,
    createLinuxInstaller,
)
from .MacOSDmg import createMacOSDmg, getCreateDmgPath
from .WindowsInstaller import (
    computeWindowsInstallerOutputFilename,
    createWindowsInstaller,
)

_installer_created = False


def wasInstallerCreated():
    """*bool*, whether an installer artifact was successfully produced."""
    return _installer_created


def getInstallerOutputFilename():
    """Return the absolute output filename for the installer, or *None*.

    Covers Windows installer, macOS DMG, and Linux AppImage creation.
    """
    if shallCreateWindowsInstaller():
        return computeWindowsInstallerOutputFilename()

    if shallCreateLinuxInstaller():
        return computeLinuxInstallerOutputFilename()

    if shallCreateDmgFile():
        if getCreateDmgPath() is not None:
            return changeFilenameExtension(
                getStandaloneDirectoryPath(bundle=False, real=True), ".dmg"
            )

    return None


def getInstallerBackendName():
    """*str* or *None*, the name of the installer backend in use."""
    if shallCreateWindowsInstaller():
        return "nsis"
    if shallCreateLinuxInstaller():
        return "appimage"
    if shallCreateDmgFile():
        return "create-dmg"
    return None


def getInstallerToolVersion():
    """*str* or *None*, the version of the installer tool in use."""
    if shallCreateWindowsInstaller():
        return getNsisVersion()
    if shallCreateLinuxInstaller():
        return getAppImageToolVersion()
    return None


def createInstallerDispatch():
    """Create installer artifacts after successful compilation.

    Notes:
        Called once from 'MainControl' after compilation succeeded and
        'onFinalResult' has been dispatched. Dispatches to DMG creation on
        macOS, Windows installer creation through NSIS, or Linux AppImage
        creation. The regular compilation output is kept intact even when
        installer creation fails, so problems remain diagnosable.
    """
    # Singleton, pylint: disable=global-statement
    global _installer_created

    if shallCreateDmgFile():
        createMacOSDmg()
        _installer_created = True

    if shallCreateWindowsInstaller():
        assert isStandaloneMode()

        createWindowsInstaller(
            installer_tool_path=getWindowsInstallerNsisPath(),
            output_filename=getWindowsInstallerOutputFilename(),
            install_dir_spec=getWindowsInstallerInstallDir(),
            shortcuts=getWindowsInstallerShortcuts() or (),
            license_filename=getWindowsInstallerLicenseFile(),
            allow_user_install_dir_change=isWindowsInstallerAllowUserChangeInstallDir(),
            install_mode=getWindowsInstallerMode(),
        )

        _installer_created = True

    if shallCreateLinuxInstaller():
        assert isStandaloneMode()

        createLinuxInstaller(
            installer_tool_path=getLinuxInstallerAppImagetoolPath(),
        )

        _installer_created = True


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
