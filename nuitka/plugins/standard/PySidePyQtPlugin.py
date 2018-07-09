#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils import Execution
from nuitka.utils.FileOperations import (
    getFileList,
    getSubDirectories,
    removeDirectory
)


class NuitkaPluginPyQtPySidePlugins(NuitkaPluginBase):
    """ This is for plugins of PySide/PyQt4/PyQt5.

        When loads an image, it may use a plug-in, which in turn used DLLs,
        which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "qt-plugins"

    def __init__(self):
        self.qt_dirs = {}

    def getPyQtPluginDirs(self, qt_version):
        if qt_version in self.qt_dirs:
            return self.qt_dirs[qt_version]

        command = """\
from __future__ import print_function

import PyQt%(qt_version)d.QtCore
for v in PyQt%(qt_version)d.QtCore.QCoreApplication.libraryPaths():
    print(v)
import os
guess_path = os.path.join(os.path.dirname(PyQt%(qt_version)d.__file__), "plugins")
if os.path.exists(guess_path):
    print("GUESS:", guess_path)
""" % {
           "qt_version" : qt_version
        }

        output = Execution.check_output([sys.executable, "-c", command])

        # May not be good for everybody, but we cannot have bytes in paths, or
        # else working with them breaks down.
        if str is not bytes:
            output = output.decode("utf-8")

        result = []

        for line in output.replace('\r', "").split('\n'):
            if not line:
                continue

            # Take the guessed path only if necessary.
            if line.startswith("GUESS: "):
                if result:
                    continue

                line = line[len("GUESS: "):]

            result.append(os.path.normpath(line))

        self.qt_dirs[qt_version] = result

        return result

    @staticmethod
    def hasPluginFamily(plugin_dir, family):
        if os.path.isdir(os.path.join(plugin_dir, family)):
            return True

        # TODO: Special case xxml.

        return False

    def considerExtraDlls(self, dist_dir, module):
        full_name = module.getFullName()

        if full_name in ("PyQt4", "PyQt5"):
            qt_version = int(full_name[-1])

            plugin_dir, = self.getPyQtPluginDirs(qt_version)

            target_plugin_dir = os.path.join(
                dist_dir,
                full_name,
                "qt-plugins"
            )

            plugin_options = self.getPluginOptions()
            plugin_options = set(plugin_options)

            if not plugin_options:
                plugin_options.add("sensible")

            if "sensible" in plugin_options:
                # Most used ones with low dependencies.
                plugin_options.update(
                    tuple(
                        family
                        for family in (
                            "imageformats",
                            "iconengines",
                            "mediaservice",
                            "printsupport"
                        )
                        if self.hasPluginFamily(plugin_dir, family)
                    )
                )

                plugin_options.remove("sensible")

                # Make sure the above didn't detect nothing, which would be
                # indicating the check to be bad.
                assert plugin_options

                # Seems platforms is required on Windows.
                if os.name == "nt":
                    plugin_options.add("platforms")

            info(
                "Copying Qt plug-ins '%s' to '%s'." % (
                    ','.join(sorted(x for x in plugin_options if x != "xml")),
                    target_plugin_dir
                )
            )

            shutil.copytree(
                plugin_dir,
                target_plugin_dir
            )

            if "all" not in plugin_options:
                for plugin_candidate in getSubDirectories(target_plugin_dir):
                    if os.path.basename(plugin_candidate) not in plugin_options:
                        removeDirectory(plugin_candidate, ignore_errors = False)

                for plugin_candidate in plugin_options:
                    if plugin_candidate == "qml":
                        continue

                    if not os.path.isdir(os.path.join(target_plugin_dir, plugin_candidate)):
                        sys.exit("Error, no such Qt plugin family: %s" % plugin_candidate)

            result = [
                (
                    filename,
                    os.path.join(target_plugin_dir, os.path.relpath(filename, plugin_dir)),
                    full_name
                )
                for filename in
                getFileList(plugin_dir)
                if not filename.endswith(".qml")
                if os.path.exists(os.path.join(target_plugin_dir, os.path.relpath(filename, plugin_dir)))
            ]

            if "qml" in plugin_options or "all" in plugin_options:
                qml_plugin_dir = os.path.normpath(
                    os.path.join(
                        plugin_dir,
                        "..",
                        "qml"
                    )
                )

                qml_target_dir = os.path.normpath(
                    os.path.join(
                        target_plugin_dir,
                        "..",
                        "Qt",
                        "qml"
                    )
                )

                info(
                    "Copying Qt plug-ins 'xml' to '%s'." % (
                        qml_target_dir
                    )
                )

                shutil.copytree(
                    qml_plugin_dir,
                    qml_target_dir
                )

                # We try to filter here, not for DLLs.
                result += [
                    (
                        filename,
                        os.path.join(qml_target_dir, os.path.relpath(filename, qml_plugin_dir)),
                        full_name
                    )
                    for filename in
                    getFileList(qml_plugin_dir)
                    if not filename.endswith(
                        (
                            ".qml", ".qmlc", ".qmltypes",
                            ".js", ".jsc",
                            ".png", ".ttf",
                            ".metainfo"
                        )
                    )
                    if not os.path.isdir(filename)
                    if not os.path.basename(filename) == "qmldir"
                ]

            return result

        return ()

    def removeDllDependencies(self, dll_filename, dll_filenames):
        for values in self.qt_dirs.values():
            for value in values:
                if dll_filename.startswith(value):
                    for sub_dll_filename in dll_filenames:
                        for badword in (
                            "libKF5", "libkfontinst", "libkorganizer", "libplasma",
                            "libakregator", "libdolphin", "libnoteshared", "libknotes",
                            "libsystemsettings", "libkerfuffle", "libkaddressbook",
                            "libkworkspace", "libkmail", "libmilou", "libtaskmanager",
                            "libkonsole", "libgwenview", "libweather_ion"):
                            if os.path.basename(sub_dll_filename).startswith(badword):
                                yield sub_dll_filename


    @staticmethod
    def createPostModuleLoadCode(module):
        """ Create code to load after a module was successfully imported.

            For Qt we need to set the library path to the distribution folder
            we are running from. The code is immediately run after the code
            and therefore makes sure it's updated properly.
        """

        full_name = module.getFullName()

        if full_name in ("PyQt4.QtCore", "PyQt5.QtCore"):
            qt_version = int(full_name.split('.')[0][-1])

            code = """\
from PyQt%(qt_version)d.QtCore import QCoreApplication
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
                "qt_version" : qt_version
            }

            return code, """\
Setting Qt library path to distribution folder. Need to avoid loading target
system Qt plug-ins, which may be from another Qt version."""

        return None, None


class NuitkaPluginDetectorPyQtPySidePlugins(NuitkaPluginBase):
    plugin_name = "qt-plugins"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        if module.getFullName() in ("PyQt4.QtCore", "PyQt5.QtCore", "PySide"):
            self.warnUnusedPlugin("Inclusion of Qt plugins.")
