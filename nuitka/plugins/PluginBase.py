#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os

# This is heavily WIP.
import sys
from logging import info, warning

from nuitka import Options
from nuitka.ModuleRegistry import addUsedModule
from nuitka.SourceCodeReferences import fromFilename
from nuitka.utils.FileOperations import relpath

pre_modules = {}
post_modules = {}

warned_unused_plugins = set()


class NuitkaPluginBase(object):
    """ Nuitka base class for all plug-ins.

    Derive your plugin from "UserPlugin" please.

    Plugins allow to adapt Nuitka's behaviour in a number of ways as explained
    below at the individual methods.

    It is used to deal with special requirements some packages may have (e.g. PyQt
    and tkinter), data files to be included (e.g. certifi), inserting hidden
    code, coping with otherwise undetectable needs, or issuing messages in
    certain situations.

    A plugin in general must be enabled to be used by Nuitka. This happens by
    specifying "--enable-plugin" (standard plugins) or by "--user-plugin" (user
    plugins) in the Nuitka command line. However, some plugins are always enabled
    and invisible to the user.

    Nuitka comes with a number of "standard" plugins to be enabled as needed.
    What they are can be displayed using "nuitka --plugin-list file.py" (filename
    required but ignored).

    User plugins may be specified (and implicitely enabled) using their Python
    script pathname.
    """

    # Standard plugins must provide this as a unique string which Nuitka
    # then uses to identify them.
    #
    # User plugins are identified by their path and implicitely activated.
    # They however still need to specify some arbitrary non-blank string here,
    # which does not equal the name of an inactivated standard plugin.
    # For working with options, user plugins must set this variable to
    # the script's path (use __file__, __module__ or __name__).
    plugin_name = None

    def getPluginOptionBool(self, option_name, default_value):
        """ Check whether an option is switched on or off.

        Notes:
            Convenience method for checking single option items. If option_name is present
            in the options list, return "True". If '"no" + option_name' is present,
            return "False". Else return the default value.

        Args:
            option_name: option name
            default_value: value if neither option_name nor its negation present.
        Returns:
            True or False or default_value
        """
        plugin_options = self.getPluginOptions()

        if option_name in plugin_options and "no" + option_name in plugin_options:
            sys.exit("Error, conflicting options values given.")

        if option_name in plugin_options:
            return True

        if "no" + option_name in plugin_options:
            return False

        return default_value

    def getPluginOptions(self):
        """ Return all options for the plugin.

        Notes:
            This method will always return a list of strings.
            To specify options, code '=' immediately after the plugin name / script name.
            The following string (excluding next space) will be returned after applying split(",").
            You are free to specify anything. Use quotes to include spaces. See below for examples.

        Returns:
            list of strings

        Examples:
            For a plugin called "name"

            '...plugin=name' (no options string)
                []

            '...plugin=name=' (empty options string)
                ['']

            '...plugin=name=a,b,c' (normal options string)
                ['a', 'b', 'c']

            '...plugin=name=a=0,b=1,c=2' (normal options string)
                ['a=0', 'b=1', 'c=2']

            '...plugin=name="a=0, b=1, c=2"' (options string with spaces)
                ["[a=0", " b=1", " c=2]"]

        """
        return Options.getPluginOptions(self.plugin_name)

    def considerImplicitImports(self, module, signal_change):
        """ Provide additional modules to import implicitely when encountering the module.

        Notes:
            Better do not overload this method.
            The standard plugin 'ImplicitImports.py' already contains MANY of these.
            If you do have a new candidate, consider a PR to get it included there.

        Args:
            module: the module object
            signal_change: bool
        Returns:
            None
        """
        for full_name, required in self.getImplicitImports(module):
            module_name = full_name.split(".")[-1]
            module_package = ".".join(full_name.split(".")[:-1]) or None

            module_filename = self.locateModule(
                importing=module,
                module_name=module_name,
                module_package=module_package,
                warn=required,
            )

            if module_filename is None:
                if required:
                    sys.exit(
                        "Error, implicit module '%s' expected by '%s' not found."
                        % (full_name, module.getFullName())
                    )
                else:
                    continue
            elif os.path.isdir(module_filename):
                module_kind = "py"
            elif module_filename.endswith(".py"):
                module_kind = "py"
            elif module_filename.endswith(".so") or module_filename.endswith(".pyd"):
                module_kind = "shlib"
            else:
                assert False, module_filename

            # TODO: This should get back to plug-ins, they should be allowed to
            # preempt or override the decision.
            decision, reason = self.decideRecursion(
                module_filename=module_filename,
                module_name=module_name,
                module_package=module_package,
                module_kind=module_kind,
            )

            if decision:
                self.recurseTo(
                    module_package=module_package,
                    module_filename=module_filename,
                    module_kind=module_kind,
                    reason=reason,
                    signal_change=signal_change,
                )

    def isRequiredImplicitImport(self, module, full_name):
        """ Indicate whether an implicitely imported module should be accepted.

        Notes:
            You may negate importing a module specified as "implcit import",
            although this is an unexpected event.

        Args:
            module: the module object
            full_name: of the implicitly import module
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return True

    def getImplicitImports(self, module):
        """ Return the implicit imports for a given module (iterator).

        Args:
            module: the module object
        Yields:
            implicit imports for the module
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    # Provide fall-back for failed imports here.
    module_aliases = {}

    def considerFailedImportReferrals(self, module_name):
        """ Provide a dictionary of fallback imports for modules that failed to import.

        Args:
            module_name: name of module
        Returns:
            dict
        """
        return self.module_aliases.get(module_name, None)

    def onModuleSourceCode(self, module_name, source_code):
        """ Inspect or modify source code.

        Args:
            module_name: (str) name of module
            source_code: (str) its source code
        Returns:
            source_code (str)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return source_code

    def onFrozenModuleSourceCode(self, module_name, is_package, source_code):
        """ Inspect or modify frozen module source code.

        Args:
            module_name: (str) name of module
            is_package: (bool) True indicates a package
            source_code: (str) its source code
        Returns:
            source_code (str)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return source_code

    def onFrozenModuleBytecode(self, module_name, is_package, bytecode):
        """ Inspect or modify frozen module byte code.

        Args:
            module_name: (str) name of module
            is_package: (bool) True indicates a package
            bytecode: (bytes) byte code
        Returns:
            bytecode (bytes)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return bytecode

    @staticmethod
    def _createTriggerLoadedModule(module, trigger_name, code):
        """ Create a "trigger" for a module to be imported.

        Notes:
            The trigger will incorpaorate the code to be prepended / appended.
            Called by @onModuleDiscovered.

        Args:
            module: the module object (serves as dict key)
            trigger_name: string ("-preload"/"-postload")
            code: the code string
        Returns
            trigger_module
        """
        from nuitka.tree.Building import createModuleTree
        from nuitka.nodes.ModuleNodes import CompiledPythonModule
        from .Plugins import Plugins

        module_name = module.getName() + trigger_name
        source_ref = fromFilename(module.getCompileTimeFilename() + trigger_name)

        mode = Plugins.decideCompilation(module_name, source_ref)

        trigger_module = CompiledPythonModule(
            name=module_name,
            package_name=module.getPackage(),
            is_top=False,
            mode=mode,
            future_spec=None,
            source_ref=source_ref,
        )

        createModuleTree(
            module=trigger_module,
            source_ref=module.getSourceReference(),
            source_code=code,
            is_main=False,
        )

        return trigger_module

    @staticmethod
    def createPreModuleLoadCode(module):
        """ Create code to prepend to a module.

        Notes:
            Called by @onModuleDiscovered.

        Args:
            module: the module object
        Returns:
            tuple (code, documentary string)
        """
        # Virtual method, pylint: disable=unused-argument
        return None, None

    @staticmethod
    def createPostModuleLoadCode(module):
        """ Create code to append to a module.

        Notes:
            Called by @onModuleDiscovered.

        Args:
            module: the module object
        Returns:
            tuple (code, documentary string)
        """
        # Virtual method, pylint: disable=unused-argument
        return None, None

    def onModuleDiscovered(self, module):
        """ Called with a module to be loaded.

        Notes:
            We may specify code to be prepended and/or appended to this module.
            This code is stored in the appropriate dict.
            For every imported module and each of these two options, only one plugin may do this.
            We check this condition here.

        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName()

        pre_code, reason = self.createPreModuleLoadCode(module)

        if pre_code:
            # TODO: We could find a way to handle this.
            if full_name in pre_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            info("Injecting plug-in based pre load code for module '%s':" % full_name)
            for line in reason.split("\n"):
                info("    " + line)

            pre_modules[full_name] = self._createTriggerLoadedModule(
                module=module, trigger_name="-preLoad", code=pre_code
            )

        post_code, reason = self.createPostModuleLoadCode(module)

        if post_code:
            # TODO: We could find a way to handle this.
            if full_name is post_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            info("Injecting plug-in based post load code for module '%s':" % full_name)
            for line in reason.split("\n"):
                info("    " + line)

            post_modules[full_name] = self._createTriggerLoadedModule(
                module=module, trigger_name="-postLoad", code=post_code
            )

    def onModuleEncounter(
        self, module_filename, module_name, module_package, module_kind
    ):
        """ Help decide whether to include a module.

        Args:
            module_filename: filename
            module_name: module name
            module_package: package name
            module_kind: one of "py", "shlib" (shared library)
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    @staticmethod
    def locateModule(importing, module_name, module_package, warn):
        """ Provide a filename / -path for a to-be-imported module.

        Args:
            importing: module object
            module_name: (str) name of module
            module_package: (str) package name
            warn: (bool) True if required module
        Returns:
            filename for module
        """
        from nuitka.importing import Importing

        _module_package, module_filename, _finding = Importing.findModule(
            importing=importing,
            module_name=module_name,
            parent_package=module_package,
            level=-1,
            warn=warn,
        )

        return module_filename

    @staticmethod
    def decideRecursion(module_filename, module_name, module_package, module_kind):
        """ Decide whether Nuitka should recurse down to a given module.

        Args:
            module_filename: filename
            module_name: module name
            module_package: package name
            module_kind: one of "py" or "shlib" (shared library)
        Returns:
            (decision, reason) where decision is either a bool or None, and reason is a string message.
        """
        from nuitka.importing import Recursion

        decision, reason = Recursion.decideRecursion(
            module_filename=module_filename,
            module_name=module_name,
            module_package=module_package,
            module_kind=module_kind,
        )

        return decision, reason

    @staticmethod
    def recurseTo(module_package, module_filename, module_kind, reason, signal_change):
        from nuitka.importing import Recursion

        imported_module, added_flag = Recursion.recurseTo(
            module_package=module_package,
            module_filename=module_filename,
            module_relpath=relpath(module_filename),
            module_kind=module_kind,
            reason=reason,
        )

        addUsedModule(imported_module)

        if added_flag:
            signal_change(
                "new_code", imported_module.getSourceReference(), "Recursed to module."
            )

    def considerExtraDlls(self, dist_dir, module):
        """ Provide a tuple of names of binaries to be included.

        Args:
            dist_dir: the distribution folder
            module: the module object needing the binaries
        Returns:
            tuple
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def removeDllDependencies(self, dll_filename, dll_filenames):
        """ Yield any DLLs / shared libraries not to be included in distribution.

        Args:
            dll_filename: DLL name
            dll_filenames: list of DLLs
        Yields:
            yielded filenames to exclude
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def considerDataFiles(self, module):
        """ Yield data file names (source|func, target) for inclusion (iterator).

        Args:
            module: module object that may need extra data files
        Yields:
            Data file description pairs, either (source, dest) or (func, dest)
            where the func will be called to create the content dynamically.

        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def onStandaloneDistributionFinished(self, dist_dir):
        """ Called after successfully finishing a standalone compile.

        Note:
            It is up to the plugin to take subsequent action. Examples are:
            insert additional information (license, copyright, company or
            application description), create installation material, further
            folder clean-up, start downstream applications etc.

        Args:
            dist_dir: the created distribution folder

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def suppressBuiltinImportWarning(self, module, source_ref):
        """ Suppress import warnings for builtin modules.

        Args:
            module: the module object
            source_ref: ???
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    def suppressUnknownImportWarning(self, importing, module_name, source_ref):
        """ Suppress import warnings for unknown modules.

        Args:
            importing: the module object
            module_name: name of module
            source_ref: ???
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    def decideCompilation(self, module_name, source_ref):
        """ Decide whether to compile a module (or just use its bytecode).

        Notes:
            The first plugin not returning None makes the decision. Thereafter,
            no other plugins will be checked. If all plugins return None, the
            module will be compiled.

        Args:
            module_name: name of module
            source_ref: ???

        Returns:
            "compiled" or "bytecode" or None (default)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def warnUnusedPlugin(self, message):
        """ An inactive plugin may issue a warning if it believes this may be wrong.

        Returns:
            None
        """
        if self.plugin_name not in warned_unused_plugins:
            warned_unused_plugins.add(self.plugin_name)

            warning("Use '--plugin-enable=%s' for: %s" % (self.plugin_name, message))


class UserPluginBase(NuitkaPluginBase):
    """ Use this class to inherit from NuitkaPluginBase.

    Args:
        NuitkaPluginBase: the base class we inherit from
    """

    # You must provide this as a string which identifies your plugin.
    # Arbitrary for standard plugins, filename for user plugins.
    plugin_name = None
