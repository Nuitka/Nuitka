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


## Nuitka base class for all plug-ins. Derive from "UserPlugin" please.
#
# This concept allows to adapt Nuitka's behaviour in a number of ways as
# explained below at the individual methods.
#
# It is used to deal with special requirements some packages may have (e.g.
# PyQt and tkinter), data files to be included (e.g. certifi), inserting
# hidden code, coping with otherwise undetectable needs, or issuing messages
# in certain situations.
#
# A plugin in general must be activated to be used by Nuitka. This happens
# by specifying "--enable-plugin" (standard plugins) or "--user-plugin"
# (user plugins) in the Nuitka command line.
# However, some plugins are always activated and invisible to the user.
#
# Nuitka comes with a number of "standard" plugins that can be activated when needed.
# What they are can be displayed using "nuitka --plugin-list file.py"
# (filename required but ignored).
#
# User plugins may be specified (and implicitely activated) using their
# Python script pathname.
class NuitkaPluginBase(object):

    # Standard plugins must provide this as a unique string which Nuitka
    # then uses to identify them.
    #
    # User plugins are identified by their path and implicitely activated.
    # They however still need to specify some arbitrary non-blank string here,
    # which does not equal the name of an inactivated standard plugin.
    # For working with options, user plugins must set this variable to
    # the script's path (use __file__, __module__ or __name__).
    plugin_name = None

    ## Check whether an option is switched on or off.
    # @param option_name option name (str), can be prefixed with "no" to check
    # if option is negated.
    # @param default_value value if option_name not present
    # @returns option name, resp. the default_value
    def getPluginOptionBool(self, option_name, default_value):
        plugin_options = self.getPluginOptions()

        if option_name in plugin_options and "no" + option_name in plugin_options:
            sys.exit("Error, conflicting options values given.")

        if option_name in plugin_options:
            return True

        if "no" + option_name in plugin_options:
            return False

        return default_value

    ## Return all options specified for the plugin.
    # Relevant for standard plugins only. This method will always return a list
    # of strings.
    # To specify options, append a '=' to the plugin_name. Everything what follows
    # up to and excluding the next space will be taken to form a 'raw' value.
    # The result of raw.split(',') will be returned by this method.
    # Apart from this procedure you are free to specify anything, e.g.
    # filenames, etc. To include spaces use enclosing double apostrophies.
    # Here are some examples for a plugin named "name":
    #
    # --enable-plugin=name=a,b,c ----> ['a', 'b', 'c']
    #
    # --enable-plugin=name=a=0,b=1,c=2 ----> ['a=0', 'b=1', 'c=2']
    #
    # --enable-plugin=name ----> []
    #
    # --enable-plugin=name= ----> ['']
    #
    # --enable-plugin="name={'a':0, 'b':1, 'c':2}"  ----> ["{'a':0", " 'b':1", " 'c':2}"]
    # (note the spaces preceding 'b' and 'c').
    #
    # @returns list of strings
    def getPluginOptions(self):
        return Options.getPluginOptions(self.plugin_name)

    ## You will most likely want to look at "module.getFullName()" to get
    # the fully qualified module or package name.
    #
    # You do not want to overload this method, but rather the things it
    # calls, as the "signal_change" part of this API is not to be cared
    # about. Most prominently "getImplicitImports()".
    # @param module the module
    # @param signal_change to be ignored
    # @returns None
    def considerImplicitImports(self, module, signal_change):
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

    ## By default, if given as an implicit import, require it.
    # @param module the module object
    # @param full_name
    # @returns bool
    def isRequiredImplicitImport(self, module, full_name):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return True

    ## By default, if given as an implicit import, require it.
    # Standard plugin 'ImplicitImports.py' already contains MANY
    # of these. If you have a new candidate, consider a PR to
    # get it included there.
    # @param module the module
    # @returns yielded tuple
    def getImplicitImports(self, module):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    # Provide fall-back for failed imports here.
    module_aliases = {}

    ## Provide a dictionary of fallback imports for modules that failed
    # to import.
    # @param module_name name of module
    # @returns dict
    def considerFailedImportReferrals(self, module_name):
        return self.module_aliases.get(module_name, None)

    ## Called with a module name and its source code.
    # Expects the potentially modified source returned.
    # @param module_name (str) name of module
    # @param source_code (str) source code
    # @returns source_code (str)
    def onModuleSourceCode(self, module_name, source_code):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return source_code

    ## Called with a frozen module name and its source code.
    # Expects the potentially modified source returned.
    # @param module_name (str) name of module
    # @param is_package (bool) indicate a package
    # @param source_code (str) source code
    # @returns source_code (str)
    def onFrozenModuleSourceCode(self, module_name, is_package, source_code):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return source_code

    ## Called with a frozen module name and its byte code.
    # Expects the potentially modified source returned.
    # @param module_name (str) name of module
    # @param is_package (bool) indicate a package
    # @param bytecode (bytes) byte code
    # @returns source_code (bytes)
    def onFrozenModuleBytecode(self, module_name, is_package, bytecode):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return bytecode

    @staticmethod
    ## Compute a "trigger" module for processing a to-be-imported module together
    # with any prepended / appended code.
    # Called by onModuleDiscovered, which stores the result appropriately.
    # @param module the module object (serves as dict key)
    # @param trigger_name string ("-preload"/"-postload")
    # @param code the code string
    # @returns trigger_module
    def _createTriggerLoadedModule(module, trigger_name, code):
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
    ## Create code to prepend to a module.
    # Called by onModuleDiscovered().
    # @param module the module object
    # @returns tuple (code, documentary string)
    def createPreModuleLoadCode(module):
        # Virtual method, pylint: disable=unused-argument
        return None, None

    @staticmethod
    ## Create code to append to a module.
    # Called by onModuleDiscovered().
    # @param module the module object
    # @returns tuple (code, documentary string)
    def createPostModuleLoadCode(module):
        # Virtual method, pylint: disable=unused-argument
        return None, None

    ## Called with a module to be loaded. We may specify code to be prepended
    # and/or appended to this module by storing the code in the appropriate
    # list. For every imported module and each of these two options, only one
    # plugin may do this - a condition we are checking here.
    # @param module the module object
    # @returns None
    def onModuleDiscovered(self, module):
        pre_code, reason = self.createPreModuleLoadCode(module)

        full_name = module.getFullName()

        if pre_code:
            if full_name is pre_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            info("Injecting plug-in based pre load code for module '%s':" % full_name)
            for line in reason.split("\n"):
                info("    " + line)

            pre_modules[full_name] = self._createTriggerLoadedModule(
                module=module, trigger_name="-preLoad", code=pre_code
            )

        post_code, reason = self.createPostModuleLoadCode(module)

        if post_code:
            if full_name is post_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            info("Injecting plug-in based post load code for module '%s':" % full_name)
            for line in reason.split("\n"):
                info("    " + line)

            post_modules[full_name] = self._createTriggerLoadedModule(
                module=module, trigger_name="-postLoad", code=post_code
            )

    ## Help decide whether to include an item.
    # @param module_filename filename
    # @param module_name module name
    # @param module_package package name
    # @param module_kind one of "py", "shlib" (shared library)
    # @returns bool
    def onModuleEncounter(
        self, module_filename, module_name, module_package, module_kind
    ):
        pass

    @staticmethod
    ## Provide a filename / -path for a to-be-imported module.
    # @param importing module object
    # @param module_name (str) name of module
    # @param module_package (str) package name
    # @param warn (bool) True if required module
    # @ returns filename for module
    def locateModule(importing, module_name, module_package, warn):
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
    ## Decide whether Nuitka should recurse down to a given module.
    # @param module_filename filename
    # @param module_name module name
    # @param module_package package name
    # @param module_kind one of "py" or "shlib"
    # @returns (decision, reason) where decision is either a bool or None, and
    # reason is a string message.
    def decideRecursion(module_filename, module_name, module_package, module_kind):
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

    ## Provide a tuple of names of binaries to be included.
    # @param dist_dir the distribution folder
    # @param module the module object needing the binaries
    # @returns tuple
    def considerExtraDlls(self, dist_dir, module):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    ## Yield any DLLs / shared libraries not to be included in distribution.
    # @param dll_filename DLL name
    # @param dll_filenames list of DLLs
    # @returns yielded filename to be excluded
    def removeDllDependencies(self, dll_filename, dll_filenames):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    ## Iterator to yield a tuple of file names (source, target) for inclusion.
    # @param module module object needing extra data files
    # @returns tuple
    def considerDataFiles(self, module):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    ## Use to suppress import warnings for builtin modules.
    # @param module the module object
    # @param source_ref
    # @returns bool
    def suppressBuiltinImportWarning(self, module, source_ref):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    ## Use to suppress import warnings for unknown modules.
    # @param importing ?
    # @param module_name name of module
    # @param source_ref
    # @returns bool
    def suppressUnknownImportWarning(self, importing, module_name, source_ref):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    ## Decide whether to compile a module (or just use its bytecode)
    # @param module_name name of module
    # @param source_ref
    # @returns None
    def decideCompilation(self, module_name, source_ref):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    ## An inactive plugin may issue a warning if it believes it might be required.
    # @returns None
    def warnUnusedPlugin(self, message):
        if self.plugin_name not in warned_unused_plugins:
            warned_unused_plugins.add(self.plugin_name)

            warning("Use '--plugin-enable=%s' for: %s" % (self.plugin_name, message))


## Use this class to inherit from NuitkaPluginBase.
class UserPluginBase(NuitkaPluginBase):
    # You must provide this as a string which then can be used to enable the
    # plug-in.
    plugin_name = None
