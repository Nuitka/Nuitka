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
""" Standard plug-in to make dill module work for compiled stuff.

"""

from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version


class NuitkaPluginDillWorkarounds(NuitkaPluginBase):
    """ This is to make dill module work with compiled methods.

    """

    plugin_name = "dill-compat"

    @staticmethod
    def isAlwaysEnabled():
        return False

    @staticmethod
    def createPostModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "dill":
            code = r"""\
import dill._dill

# Compiled methods need to be created.
@dill.register(compiled_method)
def save_compiled_method(pickler, obj):
    if str is not bytes:
        pickler.save_reduce(compiled_method, (obj.__func__, obj.__self__), obj=obj)
    else:
        pickler.save_reduce(compiled_method, (obj.im_func, obj.im_self, obj.im_class), obj=obj)

# Compiled methods might have to be created or not.
@dill.register(compiled_function)
def save_compiled_function(pickler, obj):
    if not dill._dill._locate_function(obj):
        if getattr(pickler, '_recurse', False):
            from dill.detect import globalvars
            globs = globalvars(obj, recurse=True, builtin=True)
            if id(obj) in stack:
                globs = obj.__globals__ if str is not bytes else obj.func_globals
        else:
            globs = obj.__globals__ if str is not bytes else obj.func_globals

        _byref = getattr(pickler, '_byref', None)
        _recurse = getattr(pickler, '_recurse', None)
        _memo = (id(obj) in stack) and (_recurse is not None)
        stack = dill._dill.stack
        stack[id(obj)] = len(stack), obj
        if str is not bytes:
            _super = ('super' in getattr(obj.__code__,'co_names',())) and (_byref is not None)
            if _super: pickler._byref = True
            if _memo: pickler._recurse = False
            fkwdefaults = getattr(obj, '__kwdefaults__', None)

            # TODO: Make compiled functions constructable via name
            assert False
            pickler.save_reduce(_create_function, (obj.__code__,
                                globs, obj.__name__,
                                obj.__defaults__, obj.__closure__,
                                obj.__dict__, fkwdefaults), obj=obj)
        else:
            _super = ('super' in getattr(obj.func_code,'co_names',())) and (_byref is not None) and getattr(pickler, '_recurse', False)
            if _super: pickler._byref = True
            if _memo: pickler._recurse = False

            pickler.save_reduce(_create_function, (obj.func_code,
                                globs, obj.func_name,
                                obj.func_defaults, obj.func_closure,
                                obj.__dict__), obj=obj)
        if _super: pickler._byref = _byref
        if _memo: pickler._recurse = _recurse

        if OLDER and not _byref and (_super or (not _super and _memo) or (not _super and not _memo and _recurse)): pickler.clear_memo()
    else:
        dill._dill.StockPickler.save_global(pickler, obj)
"""
            return (
                code,
                """\
Monkey patching "dill" for compiled types.""",
            )

        return None, None
