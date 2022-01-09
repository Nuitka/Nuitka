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
from nuitka.ModuleRegistry import getRootTopModule
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.tree.SourceReading import readSourceCodeFromFilename
from nuitka.utils.ModuleNames import ModuleName


class NuitkaPluginMultiprocessingWorkarounds(NuitkaPluginBase):
    """This is to make multiprocessing work with Nuitka and use compiled code.

    When running in accelerated mode, it's not good to fork a new Python
    instance to run other code, as that won't be accelerated. And when
    run in standalone mode, there may not even be a Python, but it's the
    same principle.

    So by default, this module is on and works around the behavior of the
    "multiprocessing.forking/multiprocessing.spawn/multiprocessing.manager"
    expectations.
    """

    plugin_name = "multiprocessing"
    plugin_desc = "Required by Python's multiprocessing module"

    @classmethod
    def isRelevant(cls):
        return not Options.shallMakeModule()

    @staticmethod
    def getPreprocessorSymbols():
        return {"_NUITKA_PLUGIN_MULTIPROCESSING_ENABLED": "1"}

    @staticmethod
    def createPreModuleLoadCode(module):
        full_name = module.getFullName()

        # TODO: Replace the setting of "sys.frozen" with a change to the source code of the
        # modules we want to affect from this plugin, it's a huge impact on compatibility
        # with other things potentially. We should do it, once the anti-bloat engine is
        # re-usable or supports conditional replacements based on plugin activity and is
        # always on.
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
        from nuitka.tree.Building import buildModule

        # First, build the module node and then read again from the
        # source code.
        root_module = getRootTopModule()

        module_name = ModuleName("__parents_main__")

        source_code = readSourceCodeFromFilename(module_name, root_module.getFilename())

        # For the call stack, this may look bad or different to what
        # CPython does. Using the "__import__" built-in to not spoil
        # or use the module namespace. The forking module was split up
        # into multiple modules in Python 3.4.
        if python_version >= 0x340:
            source_code += """
__import__("sys").modules["__main__"] = __import__("sys").modules[__name__]
# Not needed, and can crash from minor __file__ differences, depending on invocation
__import__("multiprocessing.spawn").spawn._fixup_main_from_path = lambda mod_name : None
__import__("multiprocessing.spawn").spawn.freeze_support()"""
        else:
            source_code += """
__import__("sys").modules["__main__"] = __import__("sys").modules[__name__]
__import__("multiprocessing.forking").forking.freeze_support()"""

        multiprocessing_main_module, _added = buildModule(
            module_filename=root_module.getCompileTimeFilename(),
            module_name=module_name,
            source_code=source_code,
            is_top=False,
            is_main=False,
            is_shlib=False,
            is_fake=module_name,
            hide_syntax_error=False,
        )

        if multiprocessing_main_module.getCompilationMode() == "bytecode":
            multiprocessing_main_module.setSourceCode(source_code)

        yield multiprocessing_main_module

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        # Enforce recursion in to multiprocessing for accelerated mode, which
        # would normally avoid this.
        if module_name.hasNamespace("multiprocessing"):
            return True, "Multiprocessing plugin needs this to monkey patch it."

    def decideCompilation(self, module_name):
        if module_name.hasNamespace("multiprocessing"):
            return "bytecode"

        # TODO: Make this demotable too.
        # or module_name in( "multiprocessing-preLoad", "multiprocessing-postLoad"):

    def onFrozenModuleSourceCode(self, module_name, is_package, source_code):
        if module_name == "multiprocessing.resource_tracker":
            source_code = source_code.replace(
                "args += ['-c', cmd % r]",
                "args += ['--multiprocessing-resource-tracker', str(r)]",
            )

        return source_code


class NuitkaPluginDetectorMultiprocessingWorkarounds(NuitkaPluginBase):
    detector_for = NuitkaPluginMultiprocessingWorkarounds

    @classmethod
    def isRelevant(cls):
        return not Options.shallMakeModule()

    def checkModuleSourceCode(self, module_name, source_code):
        if module_name == "__main__":
            if "multiprocessing" in source_code:
                self.warnUnusedPlugin("Multiprocessing workarounds for compiled code.")
