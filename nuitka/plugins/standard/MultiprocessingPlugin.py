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
""" Standard plug-in to make multiprocessing work well on Windows.

On Windows, the multiprocessing modules forks new processes which then have
to start from scratch. This won't work if there is no "sys.executable" to
point to a "Python.exe" and won't use compiled code by default.

The issue applies to accelerated and standalone mode alike.
"""

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils import Utils
from nuitka.utils.ModuleNames import ModuleName


class NuitkaPluginMultiprocessingWorkarounds(NuitkaPluginBase):
    """This is to make multiprocessing work with Nuitka and use compiled code.

    When running in accelerated mode, it's not good to fork a new Python
    instance to run other code, as that won't be accelerated. And when
    run in standalone mode, there may not even be a Python, but it's the
    same principle.

    So by default, this module is on and works around the behavior of the
    "multiprocessing.forking/multiprocessing.spawn" expectations.
    """

    plugin_name = "multiprocessing"
    plugin_desc = "Required by Python's multiprocessing module on Windows"

    @classmethod
    def isRelevant(cls):
        return Utils.getOS() == "Windows" and not Options.shallMakeModule()

    @staticmethod
    def getPreprocessorSymbols():
        return {"_NUITKA_PLUGIN_MULTIPROCESSING_ENABLED": "1"}

    @staticmethod
    def createPreModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "multiprocessing":
            code = """\
import sys, os
sys.frozen = 1
if sys.platform == "win32" and not os.path.exists(sys.argv[0]) and not sys.argv[0].endswith(".exe"):
    sys.executable = sys.argv[0] + ".exe"
else:
    sys.executable = sys.argv[0]
"""
            return (
                code,
                """\
Monkey patching "multiprocessing" load environment.""",
            )

    @staticmethod
    def createPostModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "multiprocessing":
            code = """\
try:
    from multiprocessing.forking import ForkingPickler
except ImportError:
    from multiprocessing.reduction import ForkingPickler

class C:
   def f():
       pass

def _reduce_compiled_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.__name__)
    else:
        return getattr, (m.im_self, m.im_func.__name__)

ForkingPickler.register(type(C().f), _reduce_compiled_method)
if str is bytes:
    ForkingPickler.register(type(C.f), _reduce_compiled_method)
"""

            return (
                code,
                """\
Monkey patching "multiprocessing" for compiled methods.""",
            )

    def onModuleInitialSet(self):
        from nuitka.importing.ImportCache import addImportedModule
        from nuitka.ModuleRegistry import getRootTopModule
        from nuitka.plugins.Plugins import Plugins
        from nuitka.tree.Building import (
            CompiledPythonModule,
            createModuleTree,
            readSourceCodeFromFilename,
        )

        # First, build the module node and then read again from the
        # source code.
        root_module = getRootTopModule()

        module_name = ModuleName("__parents_main__")
        source_ref = root_module.getSourceReference()

        mode = Plugins.decideCompilation(module_name, source_ref)

        multiprocessing_main_module = CompiledPythonModule(
            module_name=module_name,
            is_top=False,
            mode=mode,
            future_spec=None,
            source_ref=root_module.getSourceReference(),
        )

        source_code = readSourceCodeFromFilename(module_name, root_module.getFilename())

        # For the call stack, this may look bad or different to what
        # CPython does. Using the "__import__" built-in to not spoil
        # or use the module namespace. The forking module was split up
        # into multiple modules in Python 3.4.
        if python_version >= 0x340:
            source_code += """
__import__("sys").modules["__main__"] = __import__("sys").modules[__name__]
__import__("multiprocessing.spawn").spawn.freeze_support()"""
        else:
            source_code += """
__import__("sys").modules["__main__"] = __import__("sys").modules[__name__]
__import__("multiprocessing.forking").forking.freeze_support()"""

        createModuleTree(
            module=multiprocessing_main_module,
            source_ref=root_module.getSourceReference(),
            source_code=source_code,
            is_main=False,
        )

        addImportedModule(imported_module=multiprocessing_main_module)

        yield multiprocessing_main_module

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        # Enforce recursion in to multiprocessing for accelerated mode, which
        # would normally avoid this.
        if module_name.hasNamespace("multiprocessing"):
            return True, "Multiprocessing plugin needs this to monkey patch it."

    def decideCompilation(self, module_name, source_ref):
        if module_name.hasNamespace("multiprocessing"):
            return "bytecode"

        # TODO: Make this demotable too.
        # or module_name in( "multiprocessing-preLoad", "multiprocessing-postLoad"):


class NuitkaPluginDetectorMultiprocessingWorkarounds(NuitkaPluginBase):
    detector_for = NuitkaPluginMultiprocessingWorkarounds

    @classmethod
    def isRelevant(cls):
        return Utils.getOS() == "Windows" and not Options.shallMakeModule()

    def checkModuleSourceCode(self, module_name, source_code):
        if module_name == "__main__":
            if "multiprocessing" in source_code:
                self.warnUnusedPlugin(
                    "Multiprocessing workarounds for compiled code on Windows."
                )
