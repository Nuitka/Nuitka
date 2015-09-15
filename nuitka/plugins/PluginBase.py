#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""

Plugins: Welcome to Nuitka! This is your shortest way to become part of it.

This is to provide the base class for all plug-ins. Some of which are part of
proper Nuitka, and some of which are waiting to be created and submitted for
inclusion by you.

The base class will serve as documentation. And it will point to examples of
it being used.

"""

# This is heavily WIP.
import re
import shutil
import subprocess
import sys
from logging import info, warning

from nuitka import Options
from nuitka.ModuleRegistry import addUsedModule
from nuitka.SourceCodeReferences import fromFilename
from nuitka.utils import Utils

pre_modules = {}
post_modules = {}

warned_unused_plugins = set()

class NuitkaPluginBase:
    """ Nuitka base class for all plug-ins.

        Derive from "UserPlugin" please.

        The idea is it will allow to make differences for warnings, and traces
        of what is being done. For instance, the code that makes sure PyQt finds
        all his stuff, may want to do reports, but likely, you do not case about
        that enough to be visible by default.

    """

    # You must provide this as a string which then can be used to enable the
    # plug-in.
    plugin_name = None

    def considerImplicitImports(self, module, signal_change):
        """ Consider module imports.

            You will most likely want to look at "module.getFullName()" to get
            the fully qualified module or package name.

            You do not want to overload this method, but rather the things it
            calls, as the "signal_change" part of this API is not to be cared
            about. Most prominently "getImplicitImports()".
        """

        for full_name in self.getImplicitImports(module.getFullName()):
            module_name = full_name.split('.')[-1]
            module_package = '.'.join(full_name.split('.')[:-1]) or None

            module_filename = self.locateModule(
                importing      = module,
                source_ref     = module.getSourceReference(),
                module_name    = module_name,
                module_package = module_package,
            )

            if module_filename is None:
                sys.exit(
                    "Error, implicit module '%s' expected by '%s' not found." % (
                        full_name,
                        module.getFullName()
                    )
                )
            elif Utils.isDir(module_filename):
                module_kind = "py"
            elif module_filename.endswith(".py"):
                module_kind = "py"
            elif module_filename.endswith(".so") or \
                 module_filename.endswith(".pyd"):
                module_kind = "shlib"
            else:
                assert False, module_filename

            # TODO: This should get back to plug-ins, they should be allowed to
            # preempt or override the decision.
            decision, reason = self.decideRecursion(
                module_filename = module_filename,
                module_name     = module_name,
                module_package  = module_package,
                module_kind     = module_kind
            )

            if decision:
                self.recurseTo(
                    module_package  = module_package,
                    module_filename = module_filename,
                    module_kind     = module_kind,
                    reason          = reason,
                    signal_change   = signal_change
                )

    def getImplicitImports(self, full_name):
        # Virtual method, pylint: disable=R0201,W0613
        return ()

    # Provide fall-back for failed imports here.
    module_aliases = {}

    def considerFailedImportReferrals(self, module_name):
        return self.module_aliases.get(module_name, None)

    def onModuleSourceCode(self, module_name, source_code):
        # Virtual method, pylint: disable=R0201,W0613
        return source_code

    @staticmethod
    def _createTriggerLoadedModule(module, trigger_name, code):
        from nuitka.tree.Building import createModuleTree
        from nuitka.nodes.ModuleNodes import PythonModule

        trigger_module = PythonModule(
            name         = module.getName() + trigger_name,
            package_name = module.getPackage(),
            source_ref   = fromFilename(module.getCompileTimeFilename() + trigger_name)
        )

        createModuleTree(
            module      = trigger_module,
            source_ref  = module.getSourceReference(),
            source_code = code,
            is_main     = False
        )

        return trigger_module

    @staticmethod
    def createPreModuleLoadCode(module):
        # Virtual method, pylint: disable=W0613
        return None, None

    @staticmethod
    def createPostModuleLoadCode(module):
        # Virtual method, pylint: disable=W0613
        return None, None

    def onModuleDiscovered(self, module):
        pre_code, reason = self.createPreModuleLoadCode(module)

        full_name = module.getFullName()

        if pre_code:
            if full_name is pre_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            info(
                "Injecting plug-in based pre load code for module '%s':" % \
                    full_name
            )
            for line in reason.split('\n'):
                info("    " + line)

            pre_modules[full_name] = self._createTriggerLoadedModule(
                module       = module,
                trigger_name = "-preLoad",
                code         = pre_code
            )

        post_code, reason = self.createPostModuleLoadCode(module)

        if post_code:
            if full_name is post_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            info(
                "Injecting plug-in based post load code for module '%s':" % \
                    full_name
            )
            for line in reason.split('\n'):
                info("    " + line)

            post_modules[full_name] = self._createTriggerLoadedModule(
                module       = module,
                trigger_name = "-postLoad",
                code         = post_code
            )

    def onModuleEncounter(self, module_filename, module_name, module_package,
                          module_kind):
        pass

    @staticmethod
    def locateModule(importing, module_name, module_package, source_ref):
        from nuitka.importing import Importing

        _module_package, module_filename, _finding = Importing.findModule(
            importing      = importing,
            source_ref     = source_ref,
            module_name    = module_name,
            parent_package = module_package,
            level          = -1,
            warn           = True
        )

        return module_filename

    @staticmethod
    def decideRecursion(module_filename, module_name, module_package,
                        module_kind):
        from nuitka.importing import Recursion

        decision, reason = Recursion.decideRecursion(
            module_filename = module_filename,
            module_name     = module_name,
            module_package  = module_package,
            module_kind     = module_kind
        )

        return decision, reason

    @staticmethod
    def recurseTo(module_package, module_filename, module_kind, reason,
                  signal_change):
        from nuitka.importing import Recursion

        imported_module, added_flag = Recursion.recurseTo(
            module_package  = module_package,
            module_filename = module_filename,
            module_relpath  = Utils.relpath(module_filename),
            module_kind     = module_kind,
            reason          = reason
        )

        addUsedModule(imported_module)

        if added_flag:
            signal_change(
                "new_code",
                imported_module.getSourceReference(),
                "Recursed to module."
            )


    def considerExtraDlls(self, dist_dir, module):
        # Virtual method, pylint: disable=R0201,W0613
        return []

    def suppressBuiltinImportWarning(self, module_name, source_ref):
        # Virtual method, pylint: disable=R0201,W0613
        return False

    def suppressUnknownImportWarning(self, importing, module_name, source_ref):
        # Virtual method, pylint: disable=R0201,W0613
        return False

    def warnUnusedPlugin(self, message):
        if self.plugin_name not in warned_unused_plugins:
            warned_unused_plugins.add(self.plugin_name)

            warning(
                "Use --plugin-enable=%s for: %s" % (
                    self.plugin_name,
                    message
                )
            )


class NuitkaPluginPopularImplicitImports(NuitkaPluginBase):
    """ This is for implicit imports.

        When C extension modules import other modules, we cannot see this
        and need to be told that. This encodes the knowledge we have for
        various modules. Feel free to add to this and submit patches to
        make it more complete.
    """
    def getImplicitImports(self, full_name):
        elements = full_name.split('.')

        if elements[0] in ("PyQt4", "PyQt5"):
            if Utils.python_version < 300:
                yield "atexit"

            yield "sip"

            child = elements[1] if len(elements) > 1 else None

            if child == "QtGui":
                yield elements[0] + ".QtCore"

            if child == "QtWidgets":
                yield elements[0] + ".QtGui"
        elif full_name == "lxml.etree":
            yield "gzip"
            yield "lxml._elementpath"
        elif full_name == "gtk._gtk":
            yield "pangocairo"
            yield "pango"
            yield "cairo"
            yield "gio"
            yield "atk"
        elif full_name == "reportlab.rl_config":
            yield "reportlab.rl_settings"
        elif full_name == "ctypes":
            yield "_ctypes"
        elif full_name == "gi._gi":
            yield "gi._error"

    module_aliases = {
        "requests.packages.urllib3" : "urllib3",
        "requests.packages.chardet" : "chardet"
    }

    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "numexpr.cpuinfo":

            # We cannot intercept "is" tests, but need it to be "isinstance",
            # so we patch it on the file. TODO: This is only temporary, in
            # the future, we may use optimization that understands the right
            # hand size of the "is" argument well enough to allow for our
            # type too.
            return source_code.replace(
                "type(attr) is types.MethodType",
                "isinstance(attr, types.MethodType)"
            )


        # Do nothing by default.
        return source_code

    def suppressBuiltinImportWarning(self, module_name, source_ref):
        if module_name == "setuptools":
            return True

        return False


class NuitkaPluginPylintEclipseAnnotations(NuitkaPluginBase):
    plugin_name = "pylint-warnings"

    def __init__(self):
        self.line_annotations = {}

    def onModuleSourceCode(self, module_name, source_code):
        self.line_annotations[module_name] = {}

        for count, line in enumerate(source_code.split('\n')):
            match = re.search(r"#.*pylint:\s*disable=\s*([\w,]+)", line)

            if match:
                comment_only = line[:line.find('#')-1].strip() == ""

                if comment_only:
                    # TODO: Parse block wide annotations too.
                    pass
                else:
                    self.line_annotations[module_name][count+1] = set(
                        match.strip()
                        for match in
                        match.group(1).split(',')
                    )

        # Do nothing to it.
        return source_code

    def suppressUnknownImportWarning(self, importing, module_name, source_ref):
        annotations = self.line_annotations[importing.getFullName()].get(source_ref.getLineNumber(), ())

        if "F0401" in annotations:
            return True

        return False


class NuitkaPluginDetectorPylintEclipseAnnotations(NuitkaPluginBase):
    plugin_name = "pylint-warnings"

    def onModuleSourceCode(self, module_name, source_code):
        if re.search(r"#\s*pylint:\s*disable=\s*(\w+)", source_code):
            self.warnUnusedPlugin("Understand PyLint/PyDev annotations for warnings.")

        # Do nothing to it.
        return source_code



class NuitkaPluginMultiprocessingWorkaorunds(NuitkaPluginBase):
    """ This is to make multiprocess work with Nuitka and use compiled code.

        When running in accelerated mode, it's not good to fork a new Python
        instance to run other code, as that won't be accelerated. And when
        run in standalone mode, there may not even be a Python, but it's the
        same principle.

        So by default, this module is on and works around the behaviour of the
        "multiprocess.forking" expectations.
    """
    plugin_name = "multiprocessing"

    def __init__(self):
        self.multiprocessing_added = False


    @staticmethod
    def createPreModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "multiprocessing.forking":
            code = """\
import sys
sys.frozen = 1
sys.executable = sys.argv[0]
"""
            return code, """\
Monkey patching "multiprocess" load environment."""


        return None, None

    def onModuleEncounter(self, module_filename, module_name, module_package,
                          module_kind):
        if module_name == "multiprocessing" and \
           module_package is None \
           and not self.multiprocessing_added:
            self.multiprocessing_added = True

            from nuitka.ModuleRegistry import getRootModules, addRootModule
            from nuitka.tree.Building import PythonModule, readSourceCodeFromFilename, createModuleTree

            for root_module in getRootModules():
                if root_module.isMainModule():
                    # First, build the module node and then read again from the
                    # source code.

                    slave_main_module = PythonModule(
                        name         = "__parents_main__",
                        package_name = None,
                        source_ref   = root_module.getSourceReference()
                    )

                    createModuleTree(
                        module      = slave_main_module,
                        source_ref  = root_module.getSourceReference(),
                        # source_code = 'from multiprocessing.forking import main; main()',
                        source_code = readSourceCodeFromFilename(slave_main_module, root_module.getFilename()),
                        is_main     = False
                    )

                    # This is an alternative entry point of course.
                    addRootModule(slave_main_module)

                    break
            else:
                assert False



class NuitkaPluginPyQtPySidePlugins(NuitkaPluginBase):
    """ This is for plugins of PySide/PyQt4/PyQt5.

        When loads an image, it may use a plug-in, which in turn used DLLs,
        which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "qt-plugins"

    @staticmethod
    def getPyQtPluginDirs(qt_version):
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
        output = subprocess.check_output([sys.executable, "-c", command])

        # May not be good for everybody, but we cannot have bytes in paths, or
        # else working with them breaks down.
        if Utils.python_version >= 300:
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

            result.append(Utils.normpath(line))

        return result

    def considerExtraDlls(self, dist_dir, module):
        full_name = module.getFullName()

        if full_name in ("PyQt4", "PyQt5"):
            qt_version = int(full_name[-1])

            plugin_dir, = self.getPyQtPluginDirs(qt_version)

            target_plugin_dir = Utils.joinpath(
                dist_dir,
                full_name,
                "qt-plugins"
            )

            shutil.copytree(
                plugin_dir,
                target_plugin_dir
            )

            info("Copying all Qt plug-ins to '%s'." % target_plugin_dir)

            return [
                (filename, full_name)
                for filename in
                Utils.getFileList(target_plugin_dir)
            ]

        return ()

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
Setting Qt library path to distribution folder. Need to avoid
loading target system Qt plug-ins, which may be from another
Qt version."""

        return None, None


class NuitkaPluginDetectorPyQtPySidePlugins(NuitkaPluginBase):
    plugin_name = "qt-plugins"

    def onModuleDiscovered(self, module):
        if module.getFullName() in ("PyQt4.QtCore", "PyQt5.QtCore", "PySide"):
            if Options.isStandaloneMode():
                self.warnUnusedPlugin("Inclusion of Qt plugins.")



class UserPluginBase(NuitkaPluginBase):
    """ For user plug-ins.

       Check the base class methods for what you can do.
    """

    # You must provide this as a string which then can be used to enable the
    # plug-in.
    plugin_name = None


active_plugin_list = [
    NuitkaPluginPopularImplicitImports(),
]

# List of optional plug-in classes. Until we have the meta class to do it, just
# add your class here. The second one is a detector, which is supposed to give
# a missing plug-in message, should it find the condition to make it useful.
optional_plugin_classes = (
    (NuitkaPluginPyQtPySidePlugins, NuitkaPluginDetectorPyQtPySidePlugins),
    (NuitkaPluginMultiprocessingWorkaorunds, None),
    (NuitkaPluginPylintEclipseAnnotations, NuitkaPluginDetectorPylintEclipseAnnotations),
)

plugin_name2plugin_classes = dict(
    (plugin[0].plugin_name, plugin)
    for plugin in
    optional_plugin_classes
)

for plugin_name in Options.getPluginsEnabled() + Options.getPluginsDisabled():
    if plugin_name not in plugin_name2plugin_classes:
        sys.exit("Error, unknown plug-in '%s' referenced." % plugin_name)

    if plugin_name in Options.getPluginsEnabled() and \
       plugin_name in Options.getPluginsDisabled():
        sys.exit("Error, conflicting enable/disable of plug-in '%s'." % plugin_name)

for plugin_name, (plugin_class, plugin_detector) in plugin_name2plugin_classes.items():
    if plugin_name in Options.getPluginsEnabled():
        active_plugin_list.append(
            plugin_class(
                **Options.getPluginOptions(plugin_name)
            )
        )
    elif plugin_name not in Options.getPluginsDisabled():
        if plugin_detector is not None and Options.shallDetectMissingPlugins():
            active_plugin_list.append(
                plugin_detector()
            )


class Plugins:
    @staticmethod
    def considerImplicitImports(module, signal_change):
        for plugin in active_plugin_list:
            plugin.considerImplicitImports(module, signal_change)

        # Post load code may have been created, if so indicate it's used.
        full_name = module.getFullName()

        if full_name in post_modules:
            addUsedModule(post_modules[full_name])

        if full_name in pre_modules:
            addUsedModule(pre_modules[full_name])

    @staticmethod
    def considerExtraDlls(dist_dir, module):
        result = []

        for plugin in active_plugin_list:
            for extra_dll in plugin.considerExtraDlls(dist_dir, module):
                assert Utils.isFile(extra_dll[0])

                result.append(extra_dll)

        return result

    @staticmethod
    def onModuleDiscovered(module):
        for plugin in active_plugin_list:
            plugin.onModuleDiscovered(module)

    @staticmethod
    def onModuleSourceCode(module_name, source_code):
        for plugin in active_plugin_list:
            source_code = plugin.onModuleSourceCode(module_name, source_code)

        return source_code

    @staticmethod
    def onModuleEncounter(module_filename, module_name, module_package,
                          module_kind):
        for plugin in active_plugin_list:
            plugin.onModuleEncounter(
                module_filename,
                module_name,
                module_package,
                module_kind
            )

    @staticmethod
    def considerFailedImportReferrals(module_name):
        for plugin in active_plugin_list:
            new_module_name = plugin.considerFailedImportReferrals(module_name)

            if new_module_name is not None:
                return new_module_name

        return None

    @staticmethod
    def suppressBuiltinImportWarning(module_name, source_ref):
        for plugin in active_plugin_list:
            if plugin.suppressBuiltinImportWarning(module_name, source_ref):
                return True

        return False

    @staticmethod
    def suppressUnknownImportWarning(importing, module_name, source_ref):
        for plugin in active_plugin_list:
            if plugin.suppressUnknownImportWarning(importing, module_name, source_ref):
                return True

        return False
