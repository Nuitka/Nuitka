#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to make PyQt and PySide work well in standalone mode.

To run properly, these need the Qt plugins copied along, which have their
own dependencies.
"""

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Options import (
    getWindowsIconExecutablePath,
    getWindowsIconPaths,
    isStandaloneMode,
    requireNoDebugImmortalAssumptions,
    shallCreateAppBundle,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import (
    getActiveQtPlugin,
    getOtherGUIBindingNames,
    getQtBindingNames,
    getQtPluginNames,
    hasActiveGuiPluginForBinding,
)
from nuitka.PythonFlavors import isAnacondaPython
from nuitka.PythonVersions import python_version
from nuitka.utils.Distributions import getDistributionFromModuleName
from nuitka.utils.FileOperations import getFileList, getNormalizedPath, listDir
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Utils import getArchitecture, isMacOS, isWin32Windows


class NuitkaPluginQtBindingsPluginBase(NuitkaPluginBase):
    # Plenty of attributes, because it's storing many states.
    # pylint: disable=too-many-instance-attributes

    plugin_category = "package-support,qt-binding"

    # Automatically suppress detectors for any other toolkit
    plugin_gui_toolkit = True

    # For overload in the derived bindings plugin.
    binding_name = None

    warned_about = set()

    def __init__(self, include_qt_plugins, noinclude_qt_plugins, no_qt_translations):
        self.binding_package_name = ModuleName(self.binding_name)

        self.include_qt_plugins = include_qt_plugins
        self.noinclude_qt_plugins = noinclude_qt_plugins
        self.no_qt_translations = no_qt_translations

        # Qt plugin directories found.
        self.qt_plugins_dirs = None

        # Selected Qt plugins.
        self.qt_plugins = None

        active_qt_plugin_name = getActiveQtPlugin()

        if active_qt_plugin_name is not None:
            self.sysexit(
                "Error, conflicting plugin '%s', you can only have one enabled."
                % active_qt_plugin_name
            )

        self.web_engine_done_binaries = False
        self.web_engine_done_data = False

        self.plugin_families = None

    def onCompilationStartChecks(self):
        # Make sure, distribution location for this uses shortest name approach,
        # we do not need to use the value, just want to make sure it is resolved
        # properly and quickly.
        _distribution = getDistributionFromModuleName(
            self.binding_package_name, prefer_shorter_distribution_name=True
        )

        if self.locateModule(self.binding_package_name) is None:
            self.sysexit(
                "Error, failed to locate the '%s' installation." % self.binding_name
            )

        sensible_qt_plugins = self._getSensiblePlugins()

        self.include_qt_plugins = OrderedSet(
            sum([value.split(",") for value in self.include_qt_plugins], [])
        )

        # Useless, but nice for old option usage, where expanding it meant to repeat it.
        if "sensible" in self.include_qt_plugins:
            self.include_qt_plugins.remove("sensible")

        for include_qt_plugin in self.include_qt_plugins:
            if include_qt_plugin not in ("qml", "all") and not self.hasPluginFamily(
                include_qt_plugin
            ):
                self.sysexit(
                    "Error, there is no Qt plugin family '%s' (only %s)."
                    % (include_qt_plugin, self.getAvailablePluginFamilies())
                )

        self.qt_plugins = sensible_qt_plugins
        self.qt_plugins.update(self.include_qt_plugins)

        for noinclude_qt_plugin in self.noinclude_qt_plugins:
            self.qt_plugins.discard(noinclude_qt_plugin)

        # Allow to specify none.
        if self.qt_plugins == set(["none"]):
            self.qt_plugins = set()

        # Prevent the list of binding names from being incomplete, it's used for conflicts.
        assert self.binding_name in getQtBindingNames(), self.binding_name

        # Also lets have consistency in naming.
        assert self.plugin_name in getQtPluginNames()

        requireNoDebugImmortalAssumptions(
            logger=self,
            reason="%s bindings removing immortal states of objects"
            % self.binding_name,
        )

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--include-qt-plugins",
            action="append",
            dest="include_qt_plugins",
            default=[],
            help="""\
Which Qt plugins to include. These can be big with dependencies, so
by default only the "sensible" ones are included, but you can also put
"all" or list them individually. If you specify something that does
not exist, a list of all available will be given.""",
        )

        group.add_option(
            "--noinclude-qt-plugins",
            action="append",
            dest="noinclude_qt_plugins",
            default=[],
            help="""\
Which Qt plugins to not include. This removes things, so you can
ask to include "all" and selectively remove from there, or even
from the default sensible list.""",
        )

        group.add_option(
            "--noinclude-qt-translations",
            action="store_true",
            dest="no_qt_translations",
            default=False,
            help="""\
Include Qt translations with QtWebEngine if used. These can be a lot
of files that you may not want to be included.""",
        )

    def _getQmlTargetDir(self):
        """Where does the Qt bindings package expect the QML files."""
        return os.path.join(self.binding_name, "qml")

    def _isUsingMacOSFrameworks(self):
        """Is this a framework based build, or one that shared more commonality with Linux"""
        if isMacOS() and self.binding_name in ("PySide6", "PySide2"):
            return os.path.exists(
                os.path.join(
                    self._getQtInformation().data_path,
                    "lib/QtWebEngineCore.framework",
                )
            )
        else:
            return False

    def _getWebEngineResourcesTargetDir(self):
        """Where does the Qt bindings package expect the resources files."""
        if isWin32Windows():
            if self.binding_name in ("PySide2", "PyQt5"):
                return "resources"
            else:
                # While PyQt6/PySide6 complains about these, they are not working
                # return os.path.join(self.binding_name, "resources")
                return "."
        else:
            if self.binding_name in ("PySide2", "PySide6", "PyQt6"):
                return "."
            elif self.binding_name == "PyQt5":
                return "resources"
            else:
                assert False

    def _getTranslationsTargetDir(self):
        """Where does the Qt bindings package expect the translation files."""
        if isMacOS():
            # default name of PySide6, spell-checker: ignore qtwebengine_locales
            return os.path.join(self.binding_name, "Qt", "translations")
        elif isWin32Windows():
            if self.binding_name in ("PySide2", "PyQt5"):
                return "translations"
            elif self.binding_name == "PyQt6":
                # TODO: PyQt6 is complaining about not being in "translations", but ignores it there.
                return "."
            else:
                return os.path.join(self.binding_name, "translations")
        else:
            if self.binding_name in ("PySide2", "PySide6", "PyQt6"):
                return "."
            elif self.binding_name == "PyQt5":
                return "translations"
            else:
                assert False

    @staticmethod
    def _getWebEngineTargetDir():
        """Where to put the web process executable."""
        return "."

    def _getSensiblePlugins(self):
        # spell-checker: ignore imageformats,iconengines,mediaservice,printsupport
        # spell-checker: ignore platformthemes,egldeviceintegrations,xcbglintegrations
        return OrderedSet(
            tuple(
                family
                for family in (
                    "imageformats",
                    "iconengines",
                    "mediaservice",
                    "printsupport",
                    "platforms",
                    "platformthemes",
                    "styles",
                    # Wayland on Linux needs these
                    "wayland-shell-integration",
                    "wayland-decoration-client",
                    "wayland-graphics-integration-client",
                    "egldeviceintegrations",
                    # OpenGL rendering, maybe should be something separate.
                    "xcbglintegrations",
                    # SSL network needs those
                    "tls",
                )
                if self.hasPluginFamily(family)
            )
        )

    def getQtPluginsSelected(self):
        return self.qt_plugins

    def hasQtPluginSelected(self, plugin_name):
        selected = self.getQtPluginsSelected()

        return "all" in selected or plugin_name in selected

    def _applyBindingCondaLibraryPath(self, sub_path):
        return self._applyBindingName(
            "os.path.join(os.path.dirname(%(binding_name)s.__file__), '..', '..', '..', 'Library', "
            + sub_path
            + ")"
        )

    def _applyBindingName(self, template):
        return template % {
            "binding_name": self.binding_name,
            "qt_major_version": self.binding_name[-1],
        }

    def _getQtInformation(self):
        # This is generic, and therefore needs to apply this to a lot of strings.

        def getLocationQueryCode(path_name):
            if self.binding_name == "PyQt6":
                template = """\
%(binding_name)s.QtCore.QLibraryInfo.path(%(binding_name)s.QtCore.QLibraryInfo.LibraryPath.%(path_name)s)"""
            else:
                template = """\
%(binding_name)s.QtCore.QLibraryInfo.location(%(binding_name)s.QtCore.QLibraryInfo.%(path_name)s)"""

            return template % {
                "binding_name": self.binding_name,
                "path_name": path_name,
            }

        setup_codes = self._applyBindingName(
            r"""
import os
import %(binding_name)s.QtCore
"""
        )

        info = self.queryRuntimeInformationMultiple(
            info_name=self._applyBindingName("%(binding_name)s_info"),
            setup_codes=setup_codes,
            values=(
                (
                    "library_paths",
                    self._applyBindingName(
                        "%(binding_name)s.QtCore.QCoreApplication.libraryPaths()"
                    ),
                ),
                (
                    "guess_path1",
                    self._applyBindingName(
                        "os.path.join(os.path.dirname(%(binding_name)s.__file__), 'plugins')"
                    ),
                ),
                (
                    "guess_path2",
                    self._applyBindingCondaLibraryPath("'plugins'"),
                ),
                (
                    "guess_path3",
                    self._applyBindingCondaLibraryPath(
                        "'lib', 'qt%(qt_major_version)s', 'plugins'"
                    ),
                ),
                (
                    "version",
                    self._applyBindingName(
                        "%(binding_name)s.__version_info__"
                        if "PySide" in self.binding_name
                        else "%(binding_name)s.QtCore.PYQT_VERSION_STR"
                    ),
                ),
                (
                    "nuitka_patch_level",
                    self._applyBindingName(
                        "getattr(%(binding_name)s, '_nuitka_patch_level', 0)"
                    ),
                ),
                (
                    "translations_path",
                    getLocationQueryCode("TranslationsPath"),
                ),
                (
                    "translations_path_guess",
                    self._applyBindingCondaLibraryPath(
                        "'share', 'qt%(qt_major_version)s', 'translations'"
                    ),
                ),
                (
                    "library_executables_path",
                    getLocationQueryCode("LibraryExecutablesPath"),
                ),
                (
                    "library_executables_path_guess",
                    self._applyBindingCondaLibraryPath(
                        "'lib', 'qt%(qt_major_version)s'"
                    ),
                ),
                (
                    "data_path",
                    getLocationQueryCode("DataPath"),
                ),
                (
                    "qt_resources_path_guess",
                    self._applyBindingCondaLibraryPath(
                        "'share', 'qt%(qt_major_version)s', 'resources'"
                    ),
                ),
            ),
        )

        if info is None:
            self.sysexit(
                "Error, it seems '%s' is not installed or broken." % self.binding_name
            )

        return info

    def _getBindingVersion(self):
        """Get the version of the binding in tuple digit form, e.g. (6,0,3)"""
        return self._getQtInformation().version

    def _getNuitkaPatchLevel(self):
        """Does it include the Nuitka patch, i.e. is a self-built one with it applied."""
        return self._getQtInformation().nuitka_patch_level

    def _getTranslationsPath(self):
        """Get the path to the Qt translations."""
        translation_path = self._getQtInformation().translations_path

        if not os.path.exists(translation_path):
            translation_path = self._getQtInformation().translations_path_guess

        if not os.path.exists(translation_path):
            self.sysexit("Error, failed to detect QtWebEngine translation path")

        return translation_path

    def _getWebEngineResourcesPath(self):
        """Get the path to the Qt web engine resources."""
        if self._isUsingMacOSFrameworks():
            return os.path.join(
                self._getQtInformation().data_path,
                "lib/QtWebEngineCore.framework/Resources",
            )
        else:
            resources_path = os.path.join(
                self._getQtInformation().data_path, "resources"
            )

            if not os.path.exists(resources_path):
                resources_path = self._getQtInformation().qt_resources_path_guess

            if not os.path.exists(resources_path):
                self.sysexit("Error, failed to detect QtWebEngine resources path")

            return resources_path

    def _getWebEngineExecutablePath(self):
        """Get the path to QtWebEngine binary."""
        library_executables_path = self._getQtInformation().library_executables_path

        if not os.path.exists(library_executables_path):
            library_executables_path = (
                self._getQtInformation().library_executables_path_guess
            )

        if not os.path.exists(library_executables_path):
            self.sysexit("Error, failed to detect QtWebEngine library path")

        return getNormalizedPath(library_executables_path)

    def getQtPluginDirs(self):
        if self.qt_plugins_dirs is not None:
            return self.qt_plugins_dirs

        qt_info = self._getQtInformation()

        self.qt_plugins_dirs = qt_info.library_paths

        if not self.qt_plugins_dirs and os.path.exists(qt_info.guess_path1):
            self.qt_plugins_dirs.append(qt_info.guess_path1)
        if not self.qt_plugins_dirs and os.path.exists(qt_info.guess_path2):
            self.qt_plugins_dirs.append(qt_info.guess_path2)
        if not self.qt_plugins_dirs and os.path.exists(qt_info.guess_path3):
            self.qt_plugins_dirs.append(qt_info.guess_path3)

        # Avoid duplicates.
        self.qt_plugins_dirs = [
            getNormalizedPath(dirname) for dirname in self.qt_plugins_dirs
        ]
        self.qt_plugins_dirs = tuple(sorted(set(self.qt_plugins_dirs)))

        if not self.qt_plugins_dirs:
            self.warning("Couldn't detect Qt plugin directories.")

        return self.qt_plugins_dirs

    def _getQtBinDirs(self):
        for plugin_dir in self.getQtPluginDirs():
            if "PyQt" in self.binding_name:
                qt_bin_dir = getNormalizedPath(os.path.join(plugin_dir, "..", "bin"))

                if os.path.isdir(qt_bin_dir):
                    yield qt_bin_dir
            else:
                qt_bin_dir = getNormalizedPath(os.path.join(plugin_dir, ".."))

                yield qt_bin_dir

    def getAvailablePluginFamilies(self):
        if self.plugin_families is None:
            self.plugin_families = OrderedSet()

            for plugin_dir in self.getQtPluginDirs():
                for filename, filename_relative in listDir(plugin_dir):
                    if os.path.isdir(filename):
                        self.plugin_families.add(filename_relative)

        return self.plugin_families

    def hasPluginFamily(self, family):
        return family in self.getAvailablePluginFamilies()

    def _getQmlDirectory(self):
        for plugin_dir in self.getQtPluginDirs():
            qml_plugin_dir = getNormalizedPath(os.path.join(plugin_dir, "..", "qml"))

            if os.path.exists(qml_plugin_dir):
                return qml_plugin_dir

        self.sysexit("Error, no such Qt plugin family: qml")

    def _getQmlFileList(self, dlls):
        qml_plugin_dir = self._getQmlDirectory()

        # List all file types of the QML plugin folder that are data files and
        # not DLLs, spell-checker: ignore qmlc,qmltypes,metainfo,qmldir
        datafile_suffixes = (
            ".qml",
            ".qmlc",
            ".qmltypes",
            ".js",
            ".jsc",
            ".json",
            ".png",
            ".ttf",
            ".metainfo",
            ".mesh",
            ".frag",
            "qmldir",
            ".webp",
        )

        if dlls:
            ignore_suffixes = datafile_suffixes
            only_suffixes = ()
        else:
            ignore_suffixes = ()
            only_suffixes = datafile_suffixes

        return getFileList(
            qml_plugin_dir,
            ignore_suffixes=ignore_suffixes,
            only_suffixes=only_suffixes,
        )

    def _findQtPluginDLLs(self):
        for qt_plugins_dir in self.getQtPluginDirs():
            for filename in getFileList(qt_plugins_dir):
                filename_relative = os.path.relpath(filename, start=qt_plugins_dir)

                qt_plugin_name = filename_relative.split(os.path.sep, 1)[0]

                if not self.hasQtPluginSelected(qt_plugin_name):
                    continue

                yield self.makeDllEntryPoint(
                    source_path=filename,
                    dest_path=os.path.join(
                        self.getQtPluginTargetPath(),
                        filename_relative,
                    ),
                    module_name=self.binding_package_name,
                    package_name=self.binding_package_name,
                    reason="qt plugin",
                )

    def _getChildNamed(self, *child_names):
        for child_name in child_names:
            return ModuleName(self.binding_name).getChildNamed(child_name)

    def getImplicitImports(self, module):
        # Way too many indeed, pylint: disable=too-many-branches,too-many-statements

        full_name = module.getFullName()
        top_level_package_name, child_name = full_name.splitPackageName()

        if top_level_package_name != self.binding_name:
            return

        # These are alternatives depending on PyQt5 version
        if child_name == "QtCore" and "PyQt" in self.binding_name:
            if python_version < 0x300:
                yield "atexit"

            yield "sip"
            yield self._getChildNamed("sip")

        if child_name in (
            "QtGui",
            "QtAssistant",
            "QtDBus",
            "QtDeclarative",
            "QtSql",
            "QtDesigner",
            "QtHelp",
            "QtNetwork",
            "QtScript",
            "QtQml",
            "QtGui",
            "QtScriptTools",
            "QtSvg",
            "QtTest",
            "QtWebKit",
            "QtOpenGL",
            "QtXml",
            "QtXmlPatterns",
            "QtPrintSupport",
            "QtNfc",
            "QtWebKitWidgets",
            "QtBluetooth",
            "QtMultimediaWidgets",
            "QtQuick",
            "QtWebChannel",
            "QtWebSockets",
            "QtX11Extras",
            "_QOpenGLFunctions_2_0",
            "_QOpenGLFunctions_2_1",
            "_QOpenGLFunctions_4_1_Core",
        ):
            yield self._getChildNamed("QtCore")

        if child_name in (
            "QtDeclarative",
            "QtWebKit",
            "QtXmlPatterns",
            "QtQml",
            "QtPrintSupport",
            "QtWebKitWidgets",
            "QtMultimedia",
            "QtMultimediaWidgets",
            "QtQuick",
            "QtQuickWidgets",
            "QtWebSockets",
            "QtWebEngineWidgets",
        ):
            yield self._getChildNamed("QtNetwork")

        if child_name == "QtWebEngineWidgets":
            yield self._getChildNamed("QtWebEngineCore")
            yield self._getChildNamed("QtWebChannel")
            yield self._getChildNamed("QtPrintSupport")
        elif child_name == "QtScriptTools":
            yield self._getChildNamed("QtScript")
        elif child_name in (
            "QtWidgets",
            "QtDeclarative",
            "QtDesigner",
            "QtHelp",
            "QtScriptTools",
            "QtSvg",
            "QtTest",
            "QtWebKit",
            "QtPrintSupport",
            "QtWebKitWidgets",
            "QtMultimedia",
            "QtMultimediaWidgets",
            "QtOpenGL",
            "QtQuick",
            "QtQuickWidgets",
            "QtSql",
            "_QOpenGLFunctions_2_0",
            "_QOpenGLFunctions_2_1",
            "_QOpenGLFunctions_4_1_Core",
        ):
            yield self._getChildNamed("QtGui")

        if child_name in (
            "QtDesigner",
            "QtHelp",
            "QtTest",
            "QtPrintSupport",
            "QtSvg",
            "QtOpenGL",
            "QtWebKitWidgets",
            "QtMultimediaWidgets",
            "QtQuickWidgets",
            "QtSql",
        ):
            yield self._getChildNamed("QtWidgets")

        if child_name in ("QtPrintSupport",):
            yield self._getChildNamed("QtSvg")

        if child_name in ("QtWebKitWidgets",):
            yield self._getChildNamed("QtWebKit")
            yield self._getChildNamed("QtPrintSupport")

        if child_name in ("QtMultimediaWidgets",):
            yield self._getChildNamed("QtMultimedia")

        if child_name in ("QtQuick", "QtQuickWidgets"):
            yield self._getChildNamed("QtQml")
            yield self._getChildNamed("QtOpenGL")

        if child_name in ("QtQuickWidgets", "QtQml", "QtQuickControls2"):
            yield self._getChildNamed("QtQuick")

        if child_name == "Qt":
            yield self._getChildNamed("QtCore")
            yield self._getChildNamed("QtDBus")
            yield self._getChildNamed("QtGui")
            yield self._getChildNamed("QtNetwork")
            yield self._getChildNamed("QtNetworkAuth")
            yield self._getChildNamed("QtSensors")
            yield self._getChildNamed("QtSerialPort")
            yield self._getChildNamed("QtMultimedia")
            yield self._getChildNamed("QtQml")
            yield self._getChildNamed("QtWidgets")

        # TODO: Questionable if this still exists in newer PySide.
        if child_name == "QtUiTools":
            yield self._getChildNamed("QtGui")
            yield self._getChildNamed("QtXml")

        # TODO: Questionable if this still exists in newer PySide.
        if full_name == "phonon":
            yield self._getChildNamed("QtGui")

    def createPostModuleLoadCode(self, module):
        """Create code to load after a module was successfully imported.

        For Qt we need to set the library path to the distribution folder
        we are running from. The code is immediately run after the code
        and therefore makes sure it's updated properly.

        Also, for QApplication we try and load icons automatically.
        TODO: Currently only for Windows, but we could add icons from macOS too
        """

        full_name = module.getFullName()

        # We do this for PySide6 only.
        if (
            full_name == "%s" % self.binding_name
            and self.binding_name == "PySide6"
            and (getWindowsIconPaths() or getWindowsIconExecutablePath())
        ):
            # TODO: Ideally we would know the icons count and not be confused by
            # resources the user may have added themselves.

            # spell-checker: ignore Pixmap
            code = """\
import sys
import %(binding_name)s.QtWidgets
orig_QApplication = %(binding_name)s.QtWidgets.QApplication

from %(binding_name)s.QtGui import QIcon, QPixmap, QImage

class OurQApplication(orig_QApplication):
    def __init__(self, *args, **kwargs):
        orig_QApplication.__init__(self, *args, **kwargs)
        main_filename = sys.argv[0]

        import ctypes
        ctypes.windll.shell32.ExtractIconExW.restype = ctypes.wintypes.HICON
        ctypes.windll.shell32.ExtractIconExW.argtypes = (ctypes.wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(ctypes.wintypes.HICON), ctypes.POINTER(ctypes.wintypes.HICON), ctypes.c_uint)
        icon_count = ctypes.windll.shell32.ExtractIconExW(main_filename, -1, None, None, 0)

        assert icon_count > 0

        small_icon = ctypes.wintypes.HICON()
        large_icon = ctypes.wintypes.HICON()

        icons = []
        for icon_index in range(icon_count):
            res = ctypes.windll.shell32.ExtractIconExW(main_filename, icon_index, ctypes.byref(small_icon), ctypes.byref(large_icon), 1)

            icons.append(small_icon.value)
            icons.append(large_icon.value)

        icon = QIcon()
        for icon_handle in icons:
            icon.addPixmap(QPixmap.fromImage(QImage.fromHICON(icon_handle)))

        self.setWindowIcon(icon)

%(binding_name)s.QtWidgets.QApplication = OurQApplication
""" % {
                "binding_name": self.binding_name
            }

            yield (code, "Loading Qt application icon from Windows resources.")

        # Only in standalone mode, this will be needed.
        if full_name == "%s.QtCore" % self.binding_name and isStandaloneMode():
            code = """\
from __future__ import absolute_import

from %(package_name)s import QCoreApplication
import os

qt_plugins_path = %(qt_plugins_path)s

if qt_plugins_path is not None:
    QCoreApplication.setLibraryPaths(
        [
            os.path.join(
                os.path.dirname(__file__),
                "..",
                %(qt_plugins_path)s
            )
        ]
    )

os.environ["QML2_IMPORT_PATH"] = os.path.join(
    os.path.dirname(__file__),
    "qml"
)
""" % {
                "package_name": full_name,
                "qt_plugins_path": repr(
                    None
                    if self.isDefaultQtPluginTargetPath()
                    else self.getQtPluginTargetPath()
                ),
            }

            yield (
                code,
                """\
Setting Qt library path to distribution folder. We need to avoid loading target
system Qt plugins, which may be from another Qt version.""",
            )

    def isQtWebEngineModule(self, full_name):
        return full_name in (
            self.binding_name + ".QtWebEngine",
            self.binding_name + ".QtWebEngineCore",
        )

    def createPreModuleLoadCode(self, module):
        """Method called when a module is being imported.

        Notes:
            If full name equals to the binding we insert code to include the dist
            folder in the 'PATH' environment variable (on Windows only).

        Args:
            module: the module object
        Returns:
            Code to insert and descriptive text (tuple), or (None, None).
        """

        # This is only relevant on standalone mode for Windows
        if not isStandaloneMode():
            return

        full_name = module.getFullName()

        if full_name == self.binding_name and isWin32Windows():
            code = """\
import os
path = os.getenv("PATH", "")
if not path.startswith(__nuitka_binary_dir):
    os.environ["PATH"] = __nuitka_binary_dir + ";" + path
"""
            yield (
                code,
                "Adding binary folder to runtime 'PATH' environment variable for proper Qt loading.",
            )

        # We need to set these variables, to force the layout
        # spell-checker: ignore QTWEBENGINEPROCESS_PATH,QTWEBENGINE_DISABLE_SANDBOX,
        # spell-checker: ignore QTWEBENGINE_RESOURCES_PATH

        if self.isQtWebEngineModule(full_name):
            code = r"""
import os
os.environ["QTWEBENGINE_LOCALES_PATH"] = os.path.join(
    __nuitka_binary_dir,
    %(web_engine_locales_path)r,
    "qtwebengine_locales"
)
""" % {
                "web_engine_locales_path": self._getTranslationsTargetDir()
            }

            yield (
                code,
                "Setting WebEngine translations path'.",
            )

            if isWin32Windows():
                # TODO: Need to do it for DLL mode for sure, but we should do it
                # for all platforms.
                code = r"""
os.environ["QTWEBENGINEPROCESS_PATH"] = os.path.normpath(
    os.path.join(
        __nuitka_binary_dir,
        %(web_engine_process_path)r
    )
)
os.environ["QTWEBENGINE_RESOURCES_PATH"] = os.path.normpath(
    os.path.join(
        __nuitka_binary_dir,
        %(web_engine_resources_path)r
    )
)

                """ % {
                    "web_engine_process_path": "QtWebEngineProcess.exe",
                    "web_engine_resources_path": self._getWebEngineResourcesTargetDir(),
                }

                yield (
                    code,
                    "Setting Qt WebEngine binary path'.",
                )

            if self._isUsingMacOSFrameworks():
                code = r"""
os.environ["QTWEBENGINEPROCESS_PATH"] = os.path.join(
    __nuitka_binary_dir,
    %(web_engine_process_path)r
)
os.environ["QTWEBENGINE_LOCALES_PATH"] = os.path.join(
    __nuitka_binary_dir,
    "qtwebengine_locales"
)
os.environ["QTWEBENGINE_DISABLE_SANDBOX"]="1"
""" % {
                    "web_engine_process_path": """\
%s/Qt/lib/QtWebEngineCore.framework/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess"""
                    % self.binding_name
                }

                yield (
                    code,
                    "Setting Qt WebEngine binary path'.",
                )

    def _handleWebEngineDataFiles(self):
        # Do it only once
        if self.web_engine_done_data:
            return

        yield self.makeIncludedGeneratedDataFile(
            data="""\
[Paths]
Prefix = .
""",
            dest_path="qt6.conf" if "6" in self.binding_name else "qt.conf",
            reason="QtWebEngine needs Qt configuration file",
        )

        if self._isUsingMacOSFrameworks():
            yield self._handleWebEngineDataFilesMacOSFrameworks()
        else:
            yield self._handleWebEngineDataFilesGeneric()

        self.web_engine_done_data = True

    def _handleWebEngineDataFilesMacOSFrameworks(self):
        if not shallCreateAppBundle():
            self.sysexit(
                "Error, cannot include required Qt WebEngine binaries unless in an application bundle."
            )

        resources_dir = self._getWebEngineResourcesPath()

        for filename in getFileList(resources_dir):
            filename_relative = os.path.relpath(filename, resources_dir)

            yield self.makeIncludedDataFile(
                source_path=filename,
                dest_path=filename_relative,
                reason="Qt WebEngine resources",
            )

        used_frameworks = [
            "QtWebEngineCore",
            "QtCore",
            "QtQuick",
            "QtQml",
            "QtQmlModels",
            "QtNetwork",
            "QtGui",
            "QtWebChannel",
            "QtPositioning",
        ]
        if self.binding_name in ("PySide6", "PyQt6"):
            used_frameworks += ["QtOpenGL", "QtDBus"]

        # Newer PySide6 needs even more.
        if self.binding_name == "PySide6" and self._getBindingVersion() >= (6, 8, 0):
            used_frameworks.append("QtQmlMeta")
            used_frameworks.append("QtQmlWorkerScript")

        for used_framework in used_frameworks:
            yield self.makeIncludedAppBundleFramework(
                source_path=os.path.join(self._getQtInformation().data_path, "lib"),
                framework_name=used_framework,
                reason="Qt WebEngine dependency",
            )

    def makeIncludedAppBundleFramework(
        self, source_path, framework_name, reason, tags=""
    ):
        framework_basename = framework_name + ".framework"
        framework_path = os.path.join(source_path, framework_basename)

        for filename in getFileList(framework_path):
            filename_relative = os.path.relpath(filename, framework_path)

            yield self.makeIncludedDataFile(
                source_path=filename,
                dest_path=os.path.join(
                    self.binding_name,
                    "Qt",
                    "lib",
                    framework_basename,
                    filename_relative,
                ),
                reason=reason,
                tags=tags,
            )

    def _handleWebEngineDataFilesGeneric(self):
        resources_dir = self._getWebEngineResourcesPath()

        for filename in getFileList(resources_dir, ignore_suffixes=(".debug.bin",)):
            filename_relative = os.path.relpath(filename, resources_dir)

            yield self.makeIncludedDataFile(
                source_path=filename,
                dest_path=os.path.join(
                    self._getWebEngineResourcesTargetDir(), filename_relative
                ),
                reason="Qt resources",
            )

        if not self.no_qt_translations:
            translations_path = self._getTranslationsPath()
            dest_path = self._getTranslationsTargetDir()

            for filename in getFileList(translations_path):
                filename_relative = os.path.relpath(filename, translations_path)

                yield self.makeIncludedDataFile(
                    source_path=filename,
                    dest_path=os.path.join(dest_path, filename_relative),
                    reason="Qt translation",
                    tags="translation",
                )

    def considerDataFiles(self, module):
        full_name = module.getFullName()

        if full_name == self.binding_name and (
            "qml" in self.getQtPluginsSelected() or "all" in self.getQtPluginsSelected()
        ):
            qml_plugin_dir = self._getQmlDirectory()
            qml_target_dir = self._getQmlTargetDir()

            self.info("Including Qt plugins 'qml' below '%s'." % qml_target_dir)

            for filename in self._getQmlFileList(dlls=False):
                filename_relative = os.path.relpath(filename, qml_plugin_dir)

                yield self.makeIncludedDataFile(
                    source_path=filename,
                    dest_path=os.path.join(
                        qml_target_dir,
                        filename_relative,
                    ),
                    reason="Qt QML datafile",
                    tags="qml",
                )
        elif self.isQtWebEngineModule(full_name):
            yield self._handleWebEngineDataFiles()

    def _getExtraBinariesWebEngineGeneric(self, full_name):
        if self.web_engine_done_binaries:
            return

        self.info("Including QtWebEngine executable.")

        qt_web_engine_dir = self._getWebEngineExecutablePath()

        if not os.path.isdir(qt_web_engine_dir):
            assert False, qt_web_engine_dir

        for filename, filename_relative in listDir(qt_web_engine_dir):
            if filename_relative.startswith("QtWebEngineProcess"):
                yield self.makeExeEntryPoint(
                    source_path=filename,
                    dest_path=getNormalizedPath(
                        os.path.join(self._getWebEngineTargetDir(), filename_relative)
                    ),
                    module_name=full_name,
                    package_name=full_name,
                    reason="needed by '%s'" % full_name.asString(),
                )

                break
        else:
            self.sysexit(
                "Error, cannot locate 'QtWebEngineProcess' executable at '%s'."
                % qt_web_engine_dir
            )

        self.web_engine_done_binaries = True  # prevent multiple copies

    def getQtPluginTargetPath(self):
        if self.binding_name == "PyQt6":
            return os.path.join(self.binding_name, "Qt6", "plugins")
        else:
            return os.path.join(self.binding_name, "qt-plugins")

    def isDefaultQtPluginTargetPath(self):
        # So far we use the default only with PyQt6, since our post load code to
        # change it crashes on macOS, probably being called too soon.
        return self.binding_name == "PyQt6"

    def getExtraDlls(self, module):
        # pylint: disable=too-many-branches
        full_name = module.getFullName()

        if full_name == self.binding_name:
            if not self.getQtPluginDirs():
                self.sysexit(
                    "Error, failed to detect '%s' plugin directories."
                    % self.binding_name
                )

            self.info(
                "Including Qt plugins '%s' below '%s'."
                % (
                    ",".join(
                        sorted(x for x in self.getQtPluginsSelected() if x != "xml")
                    ),
                    self.getQtPluginTargetPath(),
                )
            )

            # TODO: Yielding a generator should become OK too.
            for r in self._findQtPluginDLLs():
                yield r

            if isWin32Windows():
                # Those 2 vars will be used later, just saving some resources
                # by caching the files list
                qt_bin_files = sum(
                    (getFileList(qt_bin_dir) for qt_bin_dir in self._getQtBinDirs()),
                    [],
                )

                count = 0
                for filename in qt_bin_files:
                    basename = os.path.basename(filename).lower()
                    # spell-checker: ignore libeay32,ssleay32

                    if basename in ("libeay32.dll", "ssleay32.dll"):
                        yield self.makeDllEntryPoint(
                            source_path=filename,
                            dest_path=basename,
                            module_name=full_name,
                            package_name=full_name,
                            reason="needed by '%s'" % full_name.asString(),
                        )

                        count += 1

                self.reportFileCount(full_name, count, section="OpenSSL")

            if (
                "qml" in self.getQtPluginsSelected()
                or "all" in self.getQtPluginsSelected()
            ):
                qml_plugin_dir = self._getQmlDirectory()
                qml_target_dir = self._getQmlTargetDir()

                for filename in self._getQmlFileList(dlls=True):
                    filename_relative = os.path.relpath(filename, qml_plugin_dir)

                    yield self.makeDllEntryPoint(
                        source_path=filename,
                        dest_path=os.path.join(
                            qml_target_dir,
                            filename_relative,
                        ),
                        module_name=full_name,
                        package_name=full_name,
                        reason="Qt QML plugin DLL",
                    )

                # Also copy required OpenGL DLLs on Windows,
                # spell-checker: ignore libegl,libglesv2,opengl32sw,d3dcompiler_
                if isWin32Windows():
                    gl_dlls = ("libegl.dll", "libglesv2.dll", "opengl32sw.dll")

                    count = 0
                    for filename in qt_bin_files:
                        basename = os.path.basename(filename).lower()

                        if basename in gl_dlls or basename.startswith("d3dcompiler_"):
                            yield self.makeDllEntryPoint(
                                source_path=filename,
                                dest_path=basename,
                                module_name=full_name,
                                package_name=full_name,
                                reason="needed by OpenGL for '%s'"
                                % full_name.asString(),
                            )

                    self.reportFileCount(full_name, count, section="OpenGL")
        elif full_name == self.binding_name + ".QtNetwork":
            yield self._getExtraBinariesQtNetwork(full_name=full_name)
        elif self.isQtWebEngineModule(full_name):
            if not self._isUsingMacOSFrameworks():
                yield self._getExtraBinariesWebEngineGeneric(full_name=full_name)

    def _getExtraBinariesQtNetwork(self, full_name):
        if isWin32Windows():
            if self.binding_name == "PyQt5":
                arch_name = getArchitecture()

                if arch_name == "x86":
                    arch_suffix = ""
                elif arch_name == "x86_64":
                    arch_suffix = "-x64"
                else:
                    self.sysexit(
                        "Error, unknown architecture encountered, need to add support for %s."
                        % arch_name
                    )

                # Manually loaded DLLs by Qt5.
                # spell-checker: ignore libcrypto
                for dll_basename in ("libssl-1_1", "libcrypto-1_1"):
                    dll_filename = dll_basename + arch_suffix + ".dll"

                    for plugin_dir in self._getQtBinDirs():
                        candidate = os.path.join(plugin_dir, dll_filename)

                        if os.path.exists(candidate):
                            yield self.makeDllEntryPoint(
                                source_path=candidate,
                                dest_path=dll_filename,
                                module_name=full_name,
                                package_name=full_name,
                                reason="needed by '%s'" % full_name.asString(),
                            )

                            break

        else:
            dll_path = self.locateDLL("crypto")
            if dll_path is not None:
                yield self.makeDllEntryPoint(
                    source_path=dll_path,
                    dest_path=os.path.basename(dll_path),
                    module_name=full_name,
                    package_name=full_name,
                    reason="needed by '%s'" % full_name.asString(),
                )

            dll_path = self.locateDLL("ssl")
            if dll_path is not None:
                yield self.makeDllEntryPoint(
                    source_path=dll_path,
                    dest_path=os.path.basename(dll_path),
                    module_name=full_name,
                    package_name=full_name,
                    reason="needed by '%s'" % full_name.asString(),
                )

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        top_package_name = module_name.getTopLevelPackageName()

        if isStandaloneMode():
            if (
                top_package_name in getQtBindingNames()
                and top_package_name != self.binding_name
            ):
                if top_package_name not in self.warned_about:
                    self.info(
                        """\
Unwanted import of '%(unwanted)s' that conflicts with '%(binding_name)s' \
encountered, preventing its inclusion. As a result an "ImportError" might \
be given at run time. Uninstall the module it for fully compatible \
behavior with the uncompiled code."""
                        % {
                            "unwanted": top_package_name,
                            "binding_name": self.binding_name,
                        }
                    )

                    self.warned_about.add(top_package_name)

                return (
                    False,
                    "Not included due to potentially conflicting Qt versions with selected Qt binding '%s'."
                    % self.binding_name,
                )

            if (
                top_package_name in getOtherGUIBindingNames()
                and not hasActiveGuiPluginForBinding(top_package_name)
            ):
                return (
                    False,
                    "Not included due to its plugin not being active, but a Qt plugin is.",
                )

            if module_name == self.binding_name:
                return (True, "Included to allow post load workaround code.")

    def onModuleCompleteSet(self, module_set):
        self.onModuleCompleteSetGUI(
            module_set=module_set, plugin_binding_name=self.binding_name
        )

    def onModuleSourceCode(self, module_name, source_filename, source_code):
        """Third party packages that make binding selections."""
        # spell-checker: ignore pyqtgraph
        if module_name.hasNamespace("pyqtgraph"):
            # TODO: Add a mechanism to force all variable references of a name to something
            # during tree building, that would cover all uses in a nicer way.
            source_code = source_code.replace(
                "{QT_LIB.lower()}", self.binding_name.lower()
            )
            source_code = source_code.replace(
                "QT_LIB.lower()", repr(self.binding_name.lower())
            )

        return source_code

    def onDataFileTags(self, included_datafile):
        if included_datafile.dest_path.endswith(
            ".qml"
        ) and not self.hasQtPluginSelected("qml"):
            self.warning(
                """Including QML file %s, but not having Qt qml plugins is unlikely \
to work. Consider using '--include-qt-plugins=qml' to include the \
necessary files to use it."""
                % included_datafile.dest_path
            )


class NuitkaPluginPyQt5QtPluginsPlugin(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PyQt5.

    When loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyqt5"
    plugin_desc = "Required by the PyQt5 package."

    binding_name = "PyQt5"

    def __init__(self, include_qt_plugins, noinclude_qt_plugins, no_qt_translations):
        NuitkaPluginQtBindingsPluginBase.__init__(
            self,
            include_qt_plugins=include_qt_plugins,
            noinclude_qt_plugins=noinclude_qt_plugins,
            no_qt_translations=no_qt_translations,
        )

        # TODO: make this into yaml instead, so we do not pollute this constructor.
        self.warning(
            """\
For the obsolete PyQt5 the Nuitka support is incomplete. Threading, callbacks \
to compiled functions, etc. may not be working.""",
            mnemonic="pyqt5",
        )

    def _getQtInformation(self):
        result = NuitkaPluginQtBindingsPluginBase._getQtInformation(self)

        if isAnacondaPython():
            if "CONDA_PREFIX" in os.environ:
                conda_prefix = os.environ["CONDA_PREFIX"]
            elif "CONDA_PYTHON_EXE" in os.environ:
                conda_prefix = os.path.dirname(os.environ["CONDA_PYTHON_EXE"])

            if conda_prefix is not None:
                values = result._asdict()

                def updateStaticPath(value):
                    path_parts = value.split("/")

                    # That is how it is built for Anaconda.
                    if "_h_env" in path_parts:
                        return getNormalizedPath(
                            os.path.join(
                                conda_prefix,
                                *path_parts[path_parts.index("_h_env") + 1 :]
                            )
                        )
                    else:
                        return value

                for key in "translations_path", "library_executables_path", "data_path":
                    values[key] = updateStaticPath(values[key])

                # Update the "namedtuple".
                result = result.__class__(**values)

        return result

    @classmethod
    def isRelevant(cls):
        return isStandaloneMode()


class NuitkaPluginDetectorPyQt5QtPluginsPlugin(NuitkaPluginBase):
    detector_for = NuitkaPluginPyQt5QtPluginsPlugin

    @classmethod
    def isRelevant(cls):
        return isStandaloneMode()

    def onModuleDiscovered(self, module):
        full_name = module.getFullName()

        if full_name == NuitkaPluginPyQt5QtPluginsPlugin.binding_name + ".QtCore":
            self.warnUnusedPlugin("Inclusion of Qt plugins.")
        elif full_name == "PyQt4.QtCore":
            self.warning(
                "Support for PyQt4 has been dropped. Please contact Nuitka commercial if you need it."
            )


class NuitkaPluginPySide2Plugins(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PySide2.

    When Qt loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyside2"
    plugin_desc = "Required by the PySide2 package."

    binding_name = "PySide2"

    def __init__(self, include_qt_plugins, noinclude_qt_plugins, no_qt_translations):
        if self._getNuitkaPatchLevel() < 1:
            self.warning(
                """\
For the standard PySide2 incomplete workarounds are applied. For \
full support consider provided information.""",
                mnemonic="pyside2",
            )

            if python_version < 0x360:
                self.sysexit(
                    """\
The standard PySide2 is not supported before CPython <3.6. For full support: https://nuitka.net/pages/pyside2.html"""
                )

        NuitkaPluginQtBindingsPluginBase.__init__(
            self,
            include_qt_plugins=include_qt_plugins,
            noinclude_qt_plugins=noinclude_qt_plugins,
            no_qt_translations=no_qt_translations,
        )

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        if module_name == self.binding_name and self._getNuitkaPatchLevel() < 1:
            return True, "Need to monkey patch PySide2 for abstract methods."

        return NuitkaPluginQtBindingsPluginBase.onModuleEncounter(
            self,
            using_module_name=using_module_name,
            module_name=module_name,
            module_filename=module_filename,
            module_kind=module_kind,
        )

    def createPostModuleLoadCode(self, module):
        """Create code to load after a module was successfully imported.

        For Qt we need to set the library path to the distribution folder
        we are running from. The code is immediately run after the code
        and therefore makes sure it's updated properly.
        """

        for result in NuitkaPluginQtBindingsPluginBase.createPostModuleLoadCode(
            self, module
        ):
            yield result

        if (
            self._getNuitkaPatchLevel() < 1
            and module.getFullName() == self.binding_name
        ):
            code = r"""
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
PySide2.QtCore.QAbstractTableModel.__init_subclass__ = my_init_subclass
PySide2.QtCore.QObject.__init_subclass__ = my_init_subclass
"""
            yield (
                code,
                """\
Monkey patching classes derived from PySide2 base classes to pass PySide2 checks.""",
            )


class NuitkaPluginDetectorPySide2Plugins(NuitkaPluginBase):
    detector_for = NuitkaPluginPySide2Plugins

    def onModuleDiscovered(self, module):
        if (
            module.getFullName() == NuitkaPluginPySide2Plugins.binding_name + ".QtCore"
            and getActiveQtPlugin() is None
        ):
            self.warnUnusedPlugin("Making callbacks work and include Qt plugins.")


class NuitkaPluginPySide6Plugins(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PySide6.

    When Qt loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyside6"
    plugin_desc = "Required by the PySide6 package for standalone mode."

    binding_name = "PySide6"

    def onCompilationStartChecks(self):
        NuitkaPluginQtBindingsPluginBase.onCompilationStartChecks(self)

        if self._getBindingVersion() < (6, 5, 0):
            self.warning(
                """\
Make sure to use PySide 6.5.0 or higher, otherwise Qt slots won't work in all cases."""
            )

        if self._getBindingVersion() < (6, 1, 2):
            self.warning(
                """\
Make sure to use PySide 6.1.2 or higher, otherwise Qt callbacks to Python won't work."""
            )


class NuitkaPluginDetectorPySide6Plugins(NuitkaPluginBase):
    detector_for = NuitkaPluginPySide6Plugins

    def onModuleDiscovered(self, module):
        if module.getFullName() == NuitkaPluginPySide6Plugins.binding_name + ".QtCore":
            self.warnUnusedPlugin("Standalone mode support and Qt plugins.")


class NuitkaPluginPyQt6Plugins(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PyQt6.

    When Qt loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyqt6"
    plugin_desc = "Required by the PyQt6 package for standalone mode."

    binding_name = "PyQt6"

    def __init__(self, include_qt_plugins, noinclude_qt_plugins, no_qt_translations):
        NuitkaPluginQtBindingsPluginBase.__init__(
            self,
            include_qt_plugins=include_qt_plugins,
            noinclude_qt_plugins=noinclude_qt_plugins,
            no_qt_translations=no_qt_translations,
        )

        self.info(
            """\
Support for PyQt6 is not perfect, e.g. Qt threading does not work, so prefer PySide6 if you can."""
        )


class NuitkaPluginDetectorPyQt6Plugins(NuitkaPluginBase):
    detector_for = NuitkaPluginPyQt6Plugins

    def onModuleDiscovered(self, module):
        if module.getFullName() == NuitkaPluginPyQt6Plugins.binding_name + ".QtCore":
            self.warnUnusedPlugin("Standalone mode support and Qt plugins.")


class NuitkaPluginNoQt(NuitkaPluginBase):
    """This is a plugins for suppression of all Qt binding plugins."""

    plugin_name = "no-qt"
    plugin_desc = "Disable inclusion of all Qt bindings."
    plugin_category = "package-support"

    warned_about = set()

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        top_package_name = module_name.getTopLevelPackageName()

        if top_package_name in getQtBindingNames():
            if isStandaloneMode() and top_package_name not in self.warned_about:
                self.info(
                    """\
Unwanted import of '%(unwanted)s' that is forbidden encountered, preventing \
its use. As a result an "ImportError" might be given at run time. Uninstall \
it for full compatible behavior with the uncompiled code to debug it."""
                    % {
                        "unwanted": top_package_name,
                    }
                )

                self.warned_about.add(top_package_name)

            return (False, "Not included due to all Qt bindings disallowed.")

    def getEvaluationConditionControlTags(self):
        # spell-checker: ignore noqt
        return {"use_noqt": True}


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
