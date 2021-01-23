#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Standard plug-in to make PyQt and PySide work well in standalone mode.

To run properly, these need the Qt plug-ins copied along, which have their
own dependencies.
"""

import os
import shutil
import sys

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils import Execution
from nuitka.utils.FileOperations import (
    copyTree,
    getFileList,
    getSubDirectories,
    makePath,
    removeDirectory,
)
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Utils import isWin32Windows


class NuitkaPluginPyQtPySidePlugins(NuitkaPluginBase):
    """This is for plugins of PyQt4/PyQt5 and PySide once it is supported.

    When loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "qt-plugins"
    plugin_desc = "Required by the PyQt and PySide packages"

    def __init__(self, qt_plugins):
        self.qt_plugins = qt_plugins

        self.qt_dirs = {}
        self.webengine_done = False

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--include-qt-plugins",
            action="store",
            dest="qt_plugins",
            default="sensible",
            help="""\
Which Qt plugins to include. These can be big with dependencies, so
by default only the sensible ones are included, but you can also put
"all" or list them individually. If you specify something that does
not exist, a list of all available will be given.""",
        )

    @staticmethod
    def createPreModuleLoadCode(module):
        """Method called when a module is being imported.

        Notes:
            If full name equals "PyQt?" we insert code to include the dist
            folder in the 'PATH' environment variable (on Windows only).

        Args:
            module: the module object
        Returns:
            Code to insert and descriptive text (tuple), or (None, None).
        """
        if not isWin32Windows():  # we are only relevant on Windows
            return None, None

        if module.getFullName() not in ("PyQt4", "PyQt5"):
            return None, None  # not for us

        code = """import os
path = os.environ.get("PATH", "")
if not path.startswith(__nuitka_binary_dir):
    os.environ["PATH"] = __nuitka_binary_dir + ";" + path
"""
        return (
            code,
            "Adding binary folder to runtime 'PATH' environment variable for proper loading.",
        )

    def getPyQtPluginDirs(self, qt_version):
        if qt_version in self.qt_dirs:
            return self.qt_dirs[qt_version]

        command = """\
from __future__ import print_function
from __future__ import absolute_import

import PyQt%(qt_version)d.QtCore
for v in PyQt%(qt_version)d.QtCore.QCoreApplication.libraryPaths():
    print(v)
import os
# Standard CPython has installations like this.
guess_path = os.path.join(os.path.dirname(PyQt%(qt_version)d.__file__), "plugins")
if os.path.exists(guess_path):
    print("GUESS:", guess_path)
# Anaconda has this, but it seems not automatic.
guess_path = os.path.join(os.path.dirname(PyQt%(qt_version)d.__file__), "..", "..", "..", "Library", "plugins")
if os.path.exists(guess_path):
    print("GUESS:", guess_path)
""" % {
            "qt_version": qt_version
        }

        output = Execution.check_output([sys.executable, "-c", command])

        # May not be good for everybody, but we cannot have bytes in paths, or
        # else working with them breaks down.
        if str is not bytes:
            output = output.decode("utf-8")

        result = []

        for line in output.replace("\r", "").split("\n"):
            if not line:
                continue

            # Take the guessed path only if necessary.
            if line.startswith("GUESS: "):
                if result:
                    continue

                line = line[len("GUESS: ") :]

            result.append(os.path.normpath(line))

        # Avoid duplicates.
        result = tuple(sorted(set(result)))

        self.qt_dirs[qt_version] = result

        return result

    @staticmethod
    def hasPluginFamily(plugin_dirs, family):
        for plugin_dir in plugin_dirs:
            if os.path.isdir(os.path.join(plugin_dir, family)):
                return True

        # TODO: Special case xxml.

        return False

    @staticmethod
    def _getQtBinDirs(plugin_dirs):
        for plugin_dir in plugin_dirs:
            qt_bin_dir = os.path.normpath(os.path.join(plugin_dir, "..", "bin"))

            if os.path.isdir(qt_bin_dir):
                yield qt_bin_dir

    def considerExtraDlls(self, dist_dir, module):
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements
        full_name = module.getFullName()
        plugin_dirs = None

        if full_name.getTopLevelPackageName() in ("PyQt4", "PyQt5"):
            qt_version = int(full_name.getTopLevelPackageName()[-1])
            plugin_dirs = self.getPyQtPluginDirs(qt_version)

        if full_name in ("PyQt4", "PyQt5"):
            if not plugin_dirs:
                self.sysexit(
                    "Error, failed to detect %s plugin directories." % full_name
                )

            target_plugin_dir = os.path.join(dist_dir, full_name, "qt-plugins")

            plugin_options = set(self.qt_plugins.split(","))

            if "sensible" in plugin_options:
                # Most used ones with low dependencies.
                plugin_options.update(
                    tuple(
                        family
                        for family in (
                            "imageformats",
                            "iconengines",
                            "mediaservice",
                            "printsupport",
                            "platforms",
                        )
                        if self.hasPluginFamily(plugin_dirs, family)
                    )
                )

                plugin_options.remove("sensible")

                # Make sure the above didn't detect nothing, which would be
                # indicating the check to be bad.
                assert plugin_options

            self.info(
                "Copying Qt plug-ins '%s' to '%s'."
                % (
                    ",".join(sorted(x for x in plugin_options if x != "xml")),
                    target_plugin_dir,
                )
            )

            for plugin_dir in plugin_dirs:
                copyTree(plugin_dir, target_plugin_dir)

            if "all" not in plugin_options:
                for plugin_candidate in getSubDirectories(target_plugin_dir):
                    if os.path.basename(plugin_candidate) not in plugin_options:
                        removeDirectory(plugin_candidate, ignore_errors=False)

                for plugin_candidate in plugin_options:
                    if plugin_candidate == "qml":
                        continue

                    if not os.path.isdir(
                        os.path.join(target_plugin_dir, plugin_candidate)
                    ):
                        self.sysexit(
                            "Error, no such Qt plugin family: %s" % plugin_candidate
                        )

            result = [
                (
                    filename,
                    os.path.join(
                        target_plugin_dir, os.path.relpath(filename, plugin_dir)
                    ),
                    full_name,
                )
                for plugin_dir in plugin_dirs
                for filename in getFileList(plugin_dir)
                if not filename.endswith(".qml")
                if os.path.exists(
                    os.path.join(
                        target_plugin_dir, os.path.relpath(filename, plugin_dir)
                    )
                )
            ]

            if isWin32Windows():
                # Those 2 vars will be used later, just saving some resources
                # by caching the files list
                qt_bin_files = sum(
                    (
                        getFileList(qt_bin_dir)
                        for qt_bin_dir in self._getQtBinDirs(plugin_dirs)
                    ),
                    [],
                )

                self.info("Copying OpenSSL DLLs to %r." % dist_dir)

                for filename in qt_bin_files:
                    basename = os.path.basename(filename).lower()
                    if basename in ("libeay32.dll", "ssleay32.dll"):
                        shutil.copy(filename, os.path.join(dist_dir, basename))

            if "qml" in plugin_options or "all" in plugin_options:
                for plugin_dir in plugin_dirs:
                    qml_plugin_dir = os.path.normpath(
                        os.path.join(plugin_dir, "..", "qml")
                    )

                    if os.path.exists(qml_plugin_dir):
                        break
                else:
                    self.sysexit("Error, no such Qt plugin family: qml")

                qml_target_dir = os.path.normpath(
                    os.path.join(target_plugin_dir, "..", "Qt", "qml")
                )

                self.info("Copying Qt plug-ins 'xml' to '%s'." % (qml_target_dir))

                copyTree(qml_plugin_dir, qml_target_dir)

                # We try to filter here, not for DLLs.
                result += [
                    (
                        filename,
                        os.path.join(
                            qml_target_dir, os.path.relpath(filename, qml_plugin_dir)
                        ),
                        full_name,
                    )
                    for filename in getFileList(qml_plugin_dir)
                    if not filename.endswith(
                        (
                            ".qml",
                            ".qmlc",
                            ".qmltypes",
                            ".js",
                            ".jsc",
                            ".png",
                            ".ttf",
                            ".metainfo",
                        )
                    )
                    if not os.path.isdir(filename)
                    if not os.path.basename(filename) == "qmldir"
                ]

                # Also copy required OpenGL DLLs on Windows
                if isWin32Windows():
                    opengl_dlls = ("libegl.dll", "libglesv2.dll", "opengl32sw.dll")

                    self.info("Copying OpenGL DLLs to %r." % dist_dir)

                    for filename in qt_bin_files:
                        basename = os.path.basename(filename).lower()

                        if basename in opengl_dlls or basename.startswith(
                            "d3dcompiler_"
                        ):
                            shutil.copy(filename, os.path.join(dist_dir, basename))

            return result

        elif full_name == "PyQt5.QtNetwork":
            if not isWin32Windows():
                dll_path = locateDLL("crypto")

                if dll_path is None:
                    dist_dll_path = os.path.join(dist_dir, os.path.basename(dll_path))
                    shutil.copy(dll_path, dist_dll_path)

                dll_path = locateDLL("ssl")
                if dll_path is not None:
                    dist_dll_path = os.path.join(dist_dir, os.path.basename(dll_path))

                    shutil.copy(dll_path, dist_dll_path)

        elif (
            full_name
            in (
                "PyQt4.QtWebEngine",
                "PyQt5.QtWebEngine",
                "PyQt4.QtWebEngineCore",
                "PyQt5.QtWebEngineCore",
                "PyQt4.QtWebEngineWidgets",
                "PyQt5.QtWebEngineWidgets",
            )
            and not self.webengine_done
        ):
            self.webengine_done = True  # prevent multiple copies
            self.info("Copying QtWebEngine components")

            plugin_parent = os.path.dirname(plugin_dirs[0])

            if isWin32Windows():
                bin_dir = os.path.join(plugin_parent, "bin")
            else:  # TODO verify this for non-Windows!
                bin_dir = os.path.join(plugin_parent, "libexec")
            target_bin_dir = os.path.join(dist_dir)
            for f in os.listdir(bin_dir):
                if f.startswith("QtWebEngineProcess"):
                    shutil.copy(os.path.join(bin_dir, f), target_bin_dir)

            resources_dir = os.path.join(plugin_parent, "resources")
            target_resources_dir = os.path.join(dist_dir)
            for f in os.listdir(resources_dir):
                shutil.copy(os.path.join(resources_dir, f), target_resources_dir)

            translations_dir = os.path.join(plugin_parent, "translations")
            pos = len(translations_dir) + 1
            target_translations_dir = os.path.join(
                dist_dir, full_name.getTopLevelPackageName(), "Qt", "translations"
            )
            for f in getFileList(translations_dir):
                tar_f = os.path.join(target_translations_dir, f[pos:])
                makePath(os.path.dirname(tar_f))
                shutil.copyfile(f, tar_f)

        return ()

    def removeDllDependencies(self, dll_filename, dll_filenames):
        for values in self.qt_dirs.values():
            for value in values:
                if dll_filename.startswith(value):
                    for sub_dll_filename in dll_filenames:
                        for badword in (
                            "libKF5",
                            "libkfontinst",
                            "libkorganizer",
                            "libplasma",
                            "libakregator",
                            "libdolphin",
                            "libnoteshared",
                            "libknotes",
                            "libsystemsettings",
                            "libkerfuffle",
                            "libkaddressbook",
                            "libkworkspace",
                            "libkmail",
                            "libmilou",
                            "libtaskmanager",
                            "libkonsole",
                            "libgwenview",
                            "libweather_ion",
                        ):
                            if os.path.basename(sub_dll_filename).startswith(badword):
                                yield sub_dll_filename

    @staticmethod
    def createPostModuleLoadCode(module):
        """Create code to load after a module was successfully imported.

        For Qt we need to set the library path to the distribution folder
        we are running from. The code is immediately run after the code
        and therefore makes sure it's updated properly.
        """

        full_name = module.getFullName()

        if full_name in ("PyQt4.QtCore", "PyQt5.QtCore"):
            code = """\
from __future__ import absolute_import

from %(package_name)s import QCoreApplication
import os

QCoreApplication.setLibraryPaths(
    [
        os.path.join(
           os.path.dirname(__file__),
           "qt-plugins"
        )
    ]
)
""" % {
                "package_name": full_name
            }

            return (
                code,
                """\
Setting Qt library path to distribution folder. Need to avoid loading target
system Qt plug-ins, which may be from another Qt version.""",
            )

        return None, None


class NuitkaPluginDetectorPyQtPySidePlugins(NuitkaPluginBase):
    detector_for = NuitkaPluginPyQtPySidePlugins

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        if module.getFullName() in ("PyQt4.QtCore", "PyQt5.QtCore", "PySide"):
            self.warnUnusedPlugin("Inclusion of Qt plugins.")
