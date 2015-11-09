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
        from nuitka.nodes.ModuleNodes import CompiledPythonModule

        trigger_module = CompiledPythonModule(
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
    def locateModule(importing, module_name, module_package):
        from nuitka.importing import Importing

        _module_package, module_filename, _finding = Importing.findModule(
            importing      = importing,
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

from .standard.ConsiderPyLintAnnotationsPlugin import (  # isort:skip
    NuitkaPluginDetectorPylintEclipseAnnotations,
    NuitkaPluginPylintEclipseAnnotations
)
from .standard.MultiprocessingPlugin import (  # isort:skip
    NuitkaPluginDetectorMultiprocessingWorkaorunds,
    NuitkaPluginMultiprocessingWorkaorunds
)
from .standard.PySidePyQtPlugin import (  # isort:skip
    NuitkaPluginDetectorPyQtPySidePlugins,
    NuitkaPluginPyQtPySidePlugins
)

# The standard plug-ins have their list hard-coded here. User plug-ins will
# be scanned later, TODO.

# List of optional plug-in classes. Until we have the meta class to do it, just
# add your class here. The second one is a detector, which is supposed to give
# a missing plug-in message, should it find the condition to make it useful.
optional_plugin_classes = (
    (NuitkaPluginMultiprocessingWorkaorunds, NuitkaPluginDetectorMultiprocessingWorkaorunds),
    (NuitkaPluginPyQtPySidePlugins, NuitkaPluginDetectorPyQtPySidePlugins),
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
        if plugin_detector is not None \
           and Options.shallDetectMissingPlugins() and \
           plugin_detector.isRelevant():
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
        assert type(module_name) is str
        assert type(source_code) is str

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
    def suppressUnknownImportWarning(importing, module_name):
        if importing.isCompiledPythonModule():
            importing_module = importing
        else:
            importing_module = importing.getParentModule()

        source_ref = importing.getSourceReference()

        for plugin in active_plugin_list:
            if plugin.suppressUnknownImportWarning(importing_module, module_name, source_ref):
                return True

        return False
