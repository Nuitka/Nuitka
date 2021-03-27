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
from abc import abstractmethod

from nuitka import Options
from nuitka.containers.oset import OrderedSet
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
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


class NuitkaPluginQtBindingsPluginBase(NuitkaPluginBase):
    # For overload in the derived bindings plugin.
    binding_name = None

    def __init__(self, qt_plugins):
        self.webengine_done = False
        self.qt_plugins_dirs = None

        self.qt_plugins = OrderedSet(x.strip().lower() for x in qt_plugins.split(","))

        # Allow to specify none.
        if self.qt_plugins == set(["none"]):
            self.qt_plugins = set()

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

    @abstractmethod
    def _getQmlTargetDir(self, target_plugin_dir):
        """ Where does the bindings package expect the QML files. """

    def getQtPluginsSelected(self):
        # Resolve "sensible on first use"
        if "sensible" in self.qt_plugins:
            # Most used ones with low dependencies.
            self.qt_plugins.update(
                tuple(
                    family
                    for family in (
                        "imageformats",
                        "iconengines",
                        "mediaservice",
                        "printsupport",
                        "platforms",
                    )
                    if self.hasPluginFamily(family)
                )
            )

            self.qt_plugins.remove("sensible")

            # Make sure the above didn't detect nothing, which would be
            # indicating the check to be bad.
            assert self.qt_plugins

        return self.qt_plugins

    def getQtPluginDirs(self):
        if self.qt_plugins_dirs is not None:
            return self.qt_plugins_dirs

        command = """\
from __future__ import print_function
from __future__ import absolute_import

import %(binding_name)s.QtCore
for v in %(binding_name)s.QtCore.QCoreApplication.libraryPaths():
    print(v)
import os
# Standard CPython has installations like this.
guess_path = os.path.join(os.path.dirname(%(binding_name)s.__file__), "plugins")
if os.path.exists(guess_path):
    print("GUESS:", guess_path)
# Anaconda has this, but it seems not automatic.
guess_path = os.path.join(os.path.dirname(%(binding_name)s.__file__), "..", "..", "..", "Library", "plugins")
if os.path.exists(guess_path):
    print("GUESS:", guess_path)
""" % {
            "binding_name": self.binding_name
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

        self.qt_plugins_dirs = result

        return result

    def _getQtBinDirs(self):
        for plugin_dir in self.getQtPluginDirs():
            qt_bin_dir = os.path.normpath(os.path.join(plugin_dir, "..", "bin"))

            if os.path.isdir(qt_bin_dir):
                yield qt_bin_dir

    def hasPluginFamily(self, family):
        for plugin_dir in self.getQtPluginDirs():
            if os.path.isdir(os.path.join(plugin_dir, family)):
                return True

        # TODO: Special case "xml".
        return False

    def copyQmlFiles(self, full_name, target_plugin_dir):
        for plugin_dir in self.getQtPluginDirs():
            qml_plugin_dir = os.path.normpath(os.path.join(plugin_dir, "..", "qml"))

            if os.path.exists(qml_plugin_dir):
                break
        else:
            self.sysexit("Error, no such Qt plugin family: qml")

        qml_target_dir = os.path.normpath(self._getQmlTargetDir(target_plugin_dir))

        self.info("Copying Qt plug-ins 'qml' to '%s'." % (qml_target_dir))

        copyTree(qml_plugin_dir, qml_target_dir)

        # We try to filter here, not for DLLs.
        return [
            (
                filename,
                os.path.join(qml_target_dir, os.path.relpath(filename, qml_plugin_dir)),
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

    def findDLLs(self, full_name, target_plugin_dir):
        # TODO: Change this to modern DLL entry points.
        return [
            (
                filename,
                os.path.join(target_plugin_dir, os.path.relpath(filename, plugin_dir)),
                full_name,
            )
            for plugin_dir in self.getQtPluginDirs()
            for filename in getFileList(plugin_dir)
            if not filename.endswith(".qml")
            if not filename.endswith(".mesh")
            if os.path.exists(
                os.path.join(target_plugin_dir, os.path.relpath(filename, plugin_dir))
            )
        ]

    def createPostModuleLoadCode(self, module):
        """Create code to load after a module was successfully imported.

        For Qt we need to set the library path to the distribution folder
        we are running from. The code is immediately run after the code
        and therefore makes sure it's updated properly.
        """

        # Only in standalone mode, this will be needed.
        if not Options.isStandaloneMode():
            return

        full_name = module.getFullName()

        if full_name == "%s.QtCore" % self.binding_name:
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
Setting Qt library path to distribution folder. We need to avoid loading target
system Qt plug-ins, which may be from another Qt version.""",
            )

    @staticmethod
    def createPreModuleLoadCode(module):
        """Method called when a module is being imported.

        Notes:
            If full name equals to the binding we insert code to include the dist
            folder in the 'PATH' environment variable (on Windows only).

        Args:
            module: the module object
        Returns:
            Code to insert and descriptive text (tuple), or (None, None).
        """
        if (
            not isWin32Windows() or not Options.isStandaloneMode()
        ):  # we are only relevant on standalone mode for Windows
            return None

        if module.getFullName() != "PyQt5":
            return None

        code = """import os
path = os.environ.get("PATH", "")
if not path.startswith(__nuitka_binary_dir):
    os.environ["PATH"] = __nuitka_binary_dir + ";" + path
"""
        return (
            code,
            "Adding binary folder to runtime 'PATH' environment variable for proper loading.",
        )

    def considerExtraDlls(self, dist_dir, module):
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements
        full_name = module.getFullName()

        if full_name == self.binding_name:
            if not self.getQtPluginDirs():
                self.sysexit(
                    "Error, failed to detect %r plugin directories." % self.binding_name
                )

            target_plugin_dir = os.path.join(dist_dir, full_name.asPath(), "qt-plugins")

            self.info(
                "Copying Qt plug-ins '%s' to '%s'."
                % (
                    ",".join(
                        sorted(x for x in self.getQtPluginsSelected() if x != "xml")
                    ),
                    target_plugin_dir,
                )
            )

            # TODO: Change this to filtering copyTree while it's doing it.
            for plugin_dir in self.getQtPluginDirs():
                copyTree(plugin_dir, target_plugin_dir)

            if "all" not in self.getQtPluginsSelected():
                for plugin_candidate in getSubDirectories(target_plugin_dir):
                    if (
                        os.path.basename(plugin_candidate)
                        not in self.getQtPluginsSelected()
                    ):
                        removeDirectory(plugin_candidate, ignore_errors=False)

                for plugin_candidate in self.getQtPluginsSelected():
                    if plugin_candidate == "qml":
                        continue

                    if not os.path.isdir(
                        os.path.join(target_plugin_dir, plugin_candidate)
                    ):
                        self.sysexit(
                            "Error, no such Qt plugin family: %s" % plugin_candidate
                        )

            result = self.findDLLs(
                full_name=full_name,
                target_plugin_dir=target_plugin_dir,
            )

            if isWin32Windows():
                # Those 2 vars will be used later, just saving some resources
                # by caching the files list
                qt_bin_files = sum(
                    (getFileList(qt_bin_dir) for qt_bin_dir in self._getQtBinDirs()),
                    [],
                )

                self.info("Copying OpenSSL DLLs to %r." % dist_dir)

                for filename in qt_bin_files:
                    basename = os.path.basename(filename).lower()
                    if basename in ("libeay32.dll", "ssleay32.dll"):
                        shutil.copy(filename, os.path.join(dist_dir, basename))

            if (
                "qml" in self.getQtPluginsSelected()
                or "all" in self.getQtPluginsSelected()
            ):
                result += self.copyQmlFiles(
                    full_name=full_name,
                    target_plugin_dir=target_plugin_dir,
                )

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
        elif full_name == self.binding_name + ".QtNetwork":
            if not isWin32Windows():
                dll_path = locateDLL("crypto")

                if dll_path is not None:
                    dist_dll_path = os.path.join(dist_dir, os.path.basename(dll_path))
                    shutil.copy(dll_path, dist_dll_path)

                dll_path = locateDLL("ssl")
                if dll_path is not None:
                    dist_dll_path = os.path.join(dist_dir, os.path.basename(dll_path))

                    shutil.copy(dll_path, dist_dll_path)
        elif (
            full_name
            in (
                self.binding_name + ".QtWebEngine",
                self.binding_name + ".QtWebEngineCore",
                self.binding_name + ".QtWebEngineWidgets",
            )
            and not self.webengine_done
        ):
            self.webengine_done = True  # prevent multiple copies
            self.info("Copying QtWebEngine components")

            plugin_parent = os.path.dirname(self.getQtPluginDirs()[0])

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
                dist_dir,
                full_name.getTopLevelPackageName().asPath(),
                "Qt",
                "translations",
            )
            for f in getFileList(translations_dir):
                tar_f = os.path.join(target_translations_dir, f[pos:])
                makePath(os.path.dirname(tar_f))
                shutil.copyfile(f, tar_f)

        return ()

    def removeDllDependencies(self, dll_filename, dll_filenames):
        for value in self.getQtPluginDirs():
            # TODO: That is not a proper check if a file is below that.
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


class NuitkaPluginPyQt5QtPluginsPlugin(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PyQt5 and PySide once it is supported.

    When loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "qt-plugins"
    plugin_desc = "Required by the PyQt and PySide packages"

    binding_name = "PyQt5"

    def __init__(self, qt_plugins):
        NuitkaPluginQtBindingsPluginBase.__init__(self, qt_plugins)

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    def _getQmlTargetDir(self, target_plugin_dir):
        return os.path.join(target_plugin_dir, "..", "Qt", "qml")


class NuitkaPluginDetectorPyQt5QtPluginsPlugin(NuitkaPluginBase):
    detector_for = NuitkaPluginPyQt5QtPluginsPlugin

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        full_name = module.getFullName()

        if full_name == NuitkaPluginPyQt5QtPluginsPlugin.binding_name + ".QtCore":
            self.warnUnusedPlugin("Inclusion of Qt plugins.")
        elif full_name == "PyQt4.QtCore":
            self.warning(
                "Support for PyQt4 has been dropped. Please contact Nuitka commercial if you need it."
            )


class NuitkaPluginPySide2Plugins(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PySide2 once it is supported.

    When Qt loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyside2"
    plugin_desc = "Required by the PySide2 package."

    binding_name = "PySide2"

    def __init__(self, qt_plugins):
        if python_version < 0x360:
            self.sysexit("Error, PySide2 is not supported with Nuitka on CPython <3.6.")

        NuitkaPluginQtBindingsPluginBase.__init__(self, qt_plugins)

    def _getQmlTargetDir(self, target_plugin_dir):
        return os.path.join(target_plugin_dir, "..", "qml")

    def getImplicitImports(self, module):
        full_name = module.getFullName()

        if full_name == "PySide2.QtQuick":
            yield "PySide2.QtQuick.Controls"

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        # Enforce recursion in to multiprocessing for accelerated mode, which
        # would normally avoid this.
        if module_name == self.binding_name:
            return True, "Need monkey patch PySide2 for abstract methods."

    def createPostModuleLoadCode(self, module):
        """Create code to load after a module was successfully imported.

        For Qt we need to set the library path to the distribution folder
        we are running from. The code is immediately run after the code
        and therefore makes sure it's updated properly.
        """

        result = NuitkaPluginQtBindingsPluginBase.createPostModuleLoadCode(self, module)
        if result:
            return result

        if module.getFullName() == self.binding_name:
            code = r"""\
# Make them unique and count them.
wrapper_count = 0
import functools
import inspect

def nuitka_wrap(cls):
    global wrapper_count

    for attr in cls.__dict__:
        if attr.startswith("__") and attr.endswith("__"):
            continue

        value = getattr(cls, attr)

        if type(value).__name__ == "compiled_function":
            # Only work on overloaded attributes.
            for base in cls.__bases__:
                base_value = getattr(base, attr, None)

                if base_value:
                    module = inspect.getmodule(base_value)

                    # PySide C stuff does this, and we only need to cover that.
                    if module is None:
                        break
            else:
                continue

            wrapper_count += 1
            wrapper_name = "_wrapped_function_%s_%d" % (attr, wrapper_count)

            signature = inspect.signature(value)

            # Remove annotations junk that cannot be executed.
            signature = signature.replace(
                return_annotation = inspect.Signature.empty,
                parameters=[
                    parameter.replace(default=inspect.Signature.empty,annotation=inspect.Signature.empty)
                    for parameter in
                    signature.parameters.values()
                ]
            )

            v = r'''
def %(wrapper_name)s%(signature)s:
    return %(wrapper_name)s.func(%(parameters)s)
            ''' % {
                    "signature": signature,
                    "parameters": ",".join(signature.parameters),
                    "wrapper_name": wrapper_name
                }

            # TODO: Nuitka does not currently statically optimize this, might change!
            exec(
                v,
                globals(),
            )

            wrapper = globals()[wrapper_name]
            wrapper.func = value
            wrapper.__defaults__ = value.__defaults__

            setattr(cls, attr, wrapper)

    return cls

@classmethod
def my_init_subclass(cls, *args):
    return nuitka_wrap(cls)

import PySide2.QtCore
PySide2.QtCore.QAbstractItemModel.__init_subclass__ = my_init_subclass
PySide2.QtCore.QObject.__init_subclass__ = my_init_subclass
"""
            return (
                code,
                """\
Money patching classes derived from PySide2 base classes to pass PySide2 checks.""",
            )


class NuitkaPluginDetectorPySide2Plugins(NuitkaPluginBase):
    detector_for = NuitkaPluginPySide2Plugins

    def onModuleDiscovered(self, module):
        if module.getFullName() == NuitkaPluginPySide2Plugins.binding_name + ".QtCore":
            self.warnUnusedPlugin("Making callbacks work and include Qt plugins.")
