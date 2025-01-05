#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to make multiprocessing and joblib work well.

On Windows, the multiprocessing modules forks new processes which then have
to start from scratch. This won't work if there is no "sys.executable" to
point to a "Python.exe" and won't use compiled code by default.

The issue applies to accelerated and standalone mode alike.

spell-checker: ignore joblib,anyio
"""

from nuitka import Options
from nuitka.ModuleRegistry import (
    getModuleInclusionInfoByName,
    getRootTopModule,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.tree.SourceHandling import readSourceCodeFromFilename
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
    plugin_desc = "Required by Python's 'multiprocessing' module."
    plugin_category = "package-support"

    @classmethod
    def isRelevant(cls):
        return not Options.shallMakeModule()

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def createPreModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name in ("multiprocessing", "anyio"):
            yield (
                """\
import sys, os
argv0 = sys.argv[0]
if sys.platform == "win32" and not os.path.exists(argv0) and not argv0.endswith(".exe"):
    argv0 += ".exe"

sys.executable = %s
sys._base_executable = sys.executable
"""
                % ("__nuitka_binary_exe" if Options.isStandaloneMode() else "argv0"),
                """\
Monkey patching "%s" load environment."""
                % full_name,
            )

    @staticmethod
    def createPostModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "multiprocessing":
            yield (
                """\
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
""",
                """\
Monkey patching "multiprocessing" for compiled methods.""",
            )

    @staticmethod
    def createFakeModuleDependency(module):
        full_name = module.getFullName()

        if full_name != "multiprocessing":
            return

        # First, build the module node and then read again from the
        # source code.
        root_module = getRootTopModule()

        module_name = ModuleName("__parents_main__")

        source_code = readSourceCodeFromFilename(module_name, root_module.getFilename())

        # For the call stack, this may look bad or different to what CPython
        # does, but such is life. The forking module was split up into multiple
        # modules in Python3 so this is doubled. TODO: Move the version check
        # into the code and let Nuitka compile time optimize it, which will also
        # make sure joblib support is there for Python2 as well.
        if python_version >= 0x300:
            source_code += """
def __nuitka_freeze_support():
    import sys

    # Not needed, and can crash from minor __file__ differences, depending on invocation
    import multiprocessing.spawn
    multiprocessing.spawn._fixup_main_from_path = lambda mod_name : None

    # This is a variant of freeze_support that will work for multiprocessing and
    # joblib equally well.
    kwds = {}
    args = []
    for arg in sys.argv[2:]:
        try:
            name, value = arg.split('=')
        except ValueError:
            name = "pipe_handle"
            value = arg

        if value == 'None':
            kwds[name] = None
        else:
            kwds[name] = int(value)

    # Otherwise main module names will not work.
    sys.modules["__main__"] = sys.modules["__parents_main__"]

    multiprocessing.spawn.spawn_main(*args, **kwds)
__nuitka_freeze_support()
"""
        else:
            source_code += """
__import__("sys").modules["__main__"] = __import__("sys").modules[__name__]
__import__("multiprocessing.forking").forking.freeze_support()"""

        yield (
            module_name,
            source_code,
            root_module.getCompileTimeFilename(),
            "Auto enable multiprocessing freeze support",
        )

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        # Enforce recursion in to multiprocessing for accelerated mode, which
        # would normally avoid this.
        if module_name.hasNamespace("multiprocessing"):
            return True, "Multiprocessing plugin needs this to monkey patch it."

    def decideCompilation(self, module_name):
        if module_name.hasNamespace("multiprocessing"):
            return "bytecode"

        # TODO: Make this demoted too.
        # or module_name in( "multiprocessing-preLoad", "multiprocessing-postLoad"):

    @staticmethod
    def getPreprocessorSymbols():
        if getModuleInclusionInfoByName("__parents_main__"):
            return {"_NUITKA_PLUGIN_MULTIPROCESSING_ENABLED": "1"}


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
