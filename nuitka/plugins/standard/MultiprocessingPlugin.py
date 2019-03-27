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
""" Standard plug-in to make multiprocessing work well on Windows.

On Windows, the multiprocessing modules forks new processes which then have
to start from scratch. This won't work if there is no "sys.executable" to
point to a "Python.exe" and won't use compiled code by default.

The issue applies to accelerated and standalone mode alike.
"""

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils import Utils


class NuitkaPluginMultiprocessingWorkarounds(NuitkaPluginBase):
    """ This is to make multiprocessing work with Nuitka and use compiled code.

        When running in accelerated mode, it's not good to fork a new Python
        instance to run other code, as that won't be accelerated. And when
        run in standalone mode, there may not even be a Python, but it's the
        same principle.

        So by default, this module is on and works around the behavior of the
        "multiprocessing.forking/multiprocessing.spawn" expectations.
    """

    plugin_name = "multiprocessing"

    def __init__(self):
        self.multiprocessing_added = False

    @staticmethod
    def createPreModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "multiprocessing":
            code = """\
import sys
sys.frozen = 1
sys.executable = sys.argv[0]
"""
            return (
                code,
                """\
Monkey patching "multiprocessing" load environment.""",
            )

        return None, None

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

        return None, None

    @staticmethod
    def _addSlaveMainModule(root_module):
        from nuitka.tree.Building import (
            CompiledPythonModule,
            readSourceCodeFromFilename,
            createModuleTree,
        )
        from nuitka.ModuleRegistry import addRootModule
        from nuitka.plugins.Plugins import Plugins
        from sys import hexversion

        # First, build the module node and then read again from the
        # source code.
        module_name = "__parents_main__"
        source_ref = root_module.getSourceReference()

        mode = Plugins.decideCompilation(module_name, source_ref)

        slave_main_module = CompiledPythonModule(
            name=module_name,
            package_name=None,
            is_top=False,
            mode=mode,
            future_spec=None,
            source_ref=root_module.getSourceReference(),
        )

        source_code = readSourceCodeFromFilename(
            "__parents_main__", root_module.getFilename()
        )

        # For the call stack, this may look bad or different to what
        # CPython does. Using the "__import__" built-in to not spoil
        # or use the module namespace. The forking module was split up
        # into multiple modules in Python 3.4.0.a2
        if hexversion >= 0x030400A2:
            source_code += """
__import__("sys").modules["__main__"] = __import__("sys").modules[__name__]
__import__("multiprocessing.spawn").spawn.freeze_support()"""
        else:
            source_code += """
__import__("sys").modules["__main__"] = __import__("sys").modules[__name__]
__import__("multiprocessing.forking").forking.freeze_support()"""

        createModuleTree(
            module=slave_main_module,
            source_ref=root_module.getSourceReference(),
            source_code=source_code,
            is_main=False,
        )

        # This is an alternative entry point of course.
        addRootModule(slave_main_module)

    def onModuleEncounter(
        self, module_filename, module_name, module_package, module_kind
    ):
        if (
            module_name == "multiprocessing"
            and module_package is None
            and not self.multiprocessing_added
        ):
            self.multiprocessing_added = True

            from nuitka.ModuleRegistry import getRootModules

            for root_module in getRootModules():
                if root_module.isMainModule():
                    self._addSlaveMainModule(root_module)
                    break
            else:
                assert False

        if module_package == "multiprocessing" and module_name in (
            "forking",
            "spawn",
            "reduction",
        ):
            return True, "Multiprocessing plugin needs this to monkey patch it."


class NuitkaPluginDetectorMultiprocessingWorkarounds(NuitkaPluginBase):
    plugin_name = "multiprocessing"

    @staticmethod
    def isRelevant():
        return Utils.getOS() == "Windows" and not Options.shallMakeModule()

    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "__main__":
            if "multiprocessing" in source_code and "freeze_support" in source_code:
                self.warnUnusedPlugin(
                    "Multiprocessing workarounds for compiled code on Windows."
                )

        return source_code
