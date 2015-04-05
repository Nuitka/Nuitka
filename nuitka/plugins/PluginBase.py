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

Plugins: Welcome to Nuitka! This is your way to become part of it.

This is to provide the base class for all plug-ins. Some of which are part of
proper Nuitka, and some of which are waiting to be created and submitted for
inclusion by you.

The base class will serve as documentation. And it will point to examples of
it being used.

"""

# This is heavily WIP.
import shutil
import subprocess
import sys

from nuitka.ModuleRegistry import addUsedModule
from nuitka.nodes.ModuleNodes import PythonModule
from nuitka.SourceCodeReferences import fromFilename
from nuitka.utils import Utils

post_modules = {}

class NuitkaPluginBase:
    """ Nuitka base class for all plug-ins.

        Derive from "UserPlugin" please.

        The idea is it will allow to make differences for warnings, and traces
        of what is being done. For instance, the code that makes sure PyQt finds
        all his stuff, may want to do reports, but likely, you do not case about
        that enough to be visible by default.

    """
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
                source_ref     = module.getSourceReference(),
                module_name    = module_name,
                module_package = module_package,
            )

            if module_filename is None:
                sys.exit(
                    "Error, implicit module '%s' expected by '%s' not found" % (
                        module_name,
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

            full_name = module.getFullName()
            if full_name in post_modules:
                addUsedModule(post_modules[full_name])

    def onModuleDiscovered(self, module):
        post_code = self.createPostModuleLoadCode(module)

        if post_code:
            from nuitka.tree.Building import createModuleTree

            post_module = PythonModule(
                name         = module.getName() + "-onLoad",
                package_name = module.getPackage(),
                source_ref   = fromFilename(module.getName() + "-onLoad")
            )

            createModuleTree(
                module      = post_module,
                source_ref  = module.getSourceReference(),
                source_code = post_code,
                is_main     = False
            )

            post_modules[module.getFullName()] = post_module

    @staticmethod
    def locateModule(module_name, module_package, source_ref):
        from nuitka.importing import Importing

        _module_package, module_filename, _finding = Importing.findModule(
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



class NuitkaPopularImplicitImports(NuitkaPluginBase):

    @staticmethod
    def getImplicitImports(full_name):
        elements = full_name.split('.')

        if elements[0] in ("PyQt4", "PyQt5"):
            if Utils.python_version < 300:
                yield "atexit"

            yield "sip"

            if elements[1] == "QtGui":
                yield elements[0] + ".QtCore"
        elif full_name == "lxml.etree":
            yield "gzip"
            yield "lxml._elementpath"
        elif full_name == "gtk._gtk":
            yield "pangocairo"
            yield "pango"
            yield "cairo"
            yield "gio"
            yield "atk"

    @staticmethod
    def getPyQtPluginDirs(qt_version):
        command = """\
import PyQt%(qt_version)d.QtCore
for v in PyQt%(qt_version)d.QtCore.QCoreApplication.libraryPaths():
    print(v)
""" % {
           "qt_version" : qt_version
        }
        output = subprocess.check_output([sys.executable, "-c", command])

        # May not be good for everybody, but we cannot have bytes in paths, or
        # else working with them breaks down.
        if Utils.python_version >= 300:
            output = output.decode("utf-8")

        result = []

        for line in output.split('\n'):
            if not line:
                continue

            result.append(Utils.normpath(line))

        return result

    def considerExtraDlls(self, dist_dir, module):
        full_name = module.getFullName()

        if full_name in ("PyQt4", "PyQt5"):
            if not Options.isExperimental():
               return

            qt_version = int(full_name[-1])

            plugin_dir, = self.getPyQtPluginDirs(qt_version)

            shutil.copytree(
                plugin_dir,
                Utils.joinpath(
                    dist_dir,
                    "qt-plugins"
                )
            )

            return [
                (filename, full_name)
                for filename in
                Utils.getFileList(plugin_dir)
            ]

        return ()

    @staticmethod
    def createPostModuleLoadCode(module):
        """ Create code to load after a module was successfully imported.

        """

        full_name = module.getFullName()

        if full_name in ("PyQt4.QtCore", "PyQt5.QtCore"):
            qt_version = int(full_name.split('.')[0][-1])
            return """\
from PyQt%(qt_version)d.QtCore import QCoreApplication
import os

QCoreApplication.setLibraryPaths(
    [
        os.path.join(os.path.dirname(__file__),
        "qt-plugins")
    ]
)
""" % {
                "qt_version" : qt_version
            }


class UserPluginBase(NuitkaPluginBase):
    pass


plugin_list = [
    NuitkaPopularImplicitImports(),
]

class Plugins:
    @staticmethod
    def considerImplicitImports(module, signal_change):
        for plugin in plugin_list:
            plugin.considerImplicitImports(module, signal_change)

    @staticmethod
    def considerExtraDlls(dist_dir, module):
        result = []

        for plugin in plugin_list:
            result.extend(plugin.considerExtraDlls(dist_dir, module))

        return result

    @staticmethod
    def onModuleDiscovered(module):
        for plugin in plugin_list:
            plugin.onModuleDiscovered(module)
