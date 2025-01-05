#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# Plugin dill-compat has this as post load code for the "dill" package.
# Not supposed to be good code,
# pylint: disable=invalid-name,missing-module-docstring,protected-access
# pylint: disable=too-many-branches,too-many-statements,used-before-assignment
from types import CodeType

# spell-checker: ignore kwdefaults,globalvars
# Nuitka will optimize this away, but VS code will warn about them otherwise.
from typing import TYPE_CHECKING

import dill._dill

if str is bytes:
    import __builtin__ as builtins  # Python2 code, pylint: disable=import-error
else:
    import builtins

if TYPE_CHECKING:
    compiled_function_tables = {}


class ForCompiledTypeLookups:
    def for_compiled_type(self):
        pass


compiled_function = type(ForCompiledTypeLookups.for_compiled_type)
compiled_method = type(ForCompiledTypeLookups().for_compiled_type)
assert "__compiled__" in globals()

dill_version = tuple(int(d) for d in dill.__version__.split("."))


# Compiled methods need to be created.
@dill.register(compiled_method)
def save_compiled_method(pickler, obj):
    if str is not bytes:
        pickler.save_reduce(compiled_method, (obj.__func__, obj.__self__), obj=obj)
    else:
        pickler.save_reduce(
            compiled_method, (obj.im_func, obj.im_self, obj.im_class), obj=obj
        )


if str is bytes:

    def _create_compiled_function2(module_name, func_values, func_dict, func_defaults):
        if module_name not in compiled_function_tables:
            __import__(module_name)

        # This gets the "_create_compiled_function" of the module and calls it.
        func = compiled_function_tables[module_name][1](*func_values)
        if func_dict:
            for key, value in func_dict.items():
                func[key] = value

        func.__defaults__ = func_defaults

        return func


if str is not bytes:

    def _create_compiled_function3(
        module_name, func_values, func_dict, func_defaults, func_kwdefaults
    ):
        if module_name not in compiled_function_tables:
            __import__(module_name)

        func = compiled_function_tables[module_name][1](*func_values)
        if func_dict:
            for key, value in func_dict.items():
                func[key] = value

        func.__defaults__ = func_defaults
        func.__kwdefaults__ = func_kwdefaults

        return func


# Compiled methods might have to be created as well. This is very closely following
# the code of "dill._dill.save_function" that is intended to do things for the
# uncompiled function.
@dill.register(compiled_function)
def save_compiled_function(pickler, obj):
    # Complex beast, pylint: disable=too-many-locals

    if dill_version >= (0, 3):
        if not dill._dill._locate_function(obj, pickler):
            if type(obj.__code__) is not CodeType:
                # Some PyPy builtin functions have no module name, and thus are not
                # able to be located
                module_name = getattr(obj, "__module__", None)
                if module_name is None:
                    module_name = builtins.__name__

                _module = dill._dill._import_module(module_name, safe=True)

            _recurse = getattr(pickler, "_recurse", None)
            _postproc = getattr(pickler, "_postproc", None)
            _main_modified = getattr(pickler, "_main_modified", None)
            _original_main = getattr(pickler, "_original_main", builtins)

            postproc_list = []
            if _recurse:
                # recurse to get all globals referred to by obj
                from dill.detect import globalvars

                globs_copy = globalvars(obj, recurse=True, builtin=True)

                # Add the name of the module to the globs dictionary to prevent
                # the duplication of the dictionary. Pickle the unpopulated
                # globals dictionary and set the remaining items after the function
                # is created to correctly handle recursion.
                globs = {"__name__": obj.__module__}
            else:
                globs_copy = obj.__globals__

                # If the globals is the __dict__ from the module being saved as a
                # session, substitute it by the dictionary being actually saved.
                if _main_modified and globs_copy is _original_main.__dict__:
                    globs_copy = getattr(pickler, "_main", _original_main).__dict__
                    globs = globs_copy
                # If the globals is a module __dict__, do not save it in the pickle.
                elif (
                    globs_copy is not None
                    and obj.__module__ is not None
                    and getattr(
                        dill._dill._import_module(obj.__module__, True),
                        "__dict__",
                        None,
                    )
                    is globs_copy
                ):
                    globs = globs_copy
                else:
                    globs = {"__name__": obj.__module__}

            if globs_copy is not None and globs is not globs_copy:
                # In the case that the globals are copied, we need to ensure that
                # the globals dictionary is updated when all objects in the
                # dictionary are already created.
                glob_ids = {id(g) for g in globs_copy.values()}
                for stack_element in _postproc:
                    if stack_element in glob_ids:
                        _postproc[stack_element].append(
                            (dill._dill._setitems, (globs, globs_copy))
                        )
                        break
                else:
                    postproc_list.append((dill._dill._setitems, (globs, globs_copy)))

            state_dict = {}
            for fattrname in ("__doc__", "__kwdefaults__", "__annotations__"):
                fattr = getattr(obj, fattrname, None)
                if fattr is not None:
                    state_dict[fattrname] = fattr
            if obj.__qualname__ != obj.__name__:
                state_dict["__qualname__"] = obj.__qualname__
            if "__name__" not in globs or obj.__module__ != globs["__name__"]:
                state_dict["__module__"] = obj.__module__

            pickler.save_reduce(
                _create_compiled_function3,
                (
                    obj.__module__,
                    # This gets the "_reduce_compiled_function" of the module and calls it.
                    compiled_function_tables[obj.__module__][0](obj),
                    obj.__dict__,
                    obj.__defaults__,
                    obj.__kwdefaults__,
                ),
            )
        else:
            name = getattr(obj, "__qualname__", getattr(obj, "__name__", None))
            dill._dill.StockPickler.save_global(pickler, obj, name=name)
    else:
        if not dill._dill._locate_function(obj):
            stack = dill._dill.stack

            _byref = getattr(pickler, "_byref", None)
            _recurse = getattr(pickler, "_recurse", None)
            _memo = (id(obj) in stack) and (_recurse is not None)
            stack[id(obj)] = len(stack), obj

            if str is not bytes:
                # Python3
                _super = ("super" in getattr(obj.__code__, "co_names", ())) and (
                    _byref is not None
                )
                if _super:
                    pickler._byref = True
                if _memo:
                    pickler._recurse = False

                pickler.save_reduce(
                    _create_compiled_function3,
                    (
                        obj.__module__,
                        compiled_function_tables[obj.__module__][0](obj),
                        obj.__dict__,
                        obj.__defaults__,
                        obj.__kwdefaults__,
                    ),
                )
            else:
                # Python2
                _super = (
                    ("super" in getattr(obj.__code__, "co_names", ()))
                    and (_byref is not None)
                    and getattr(pickler, "_recurse", False)
                )
                if _super:
                    pickler._byref = True
                if _memo:
                    pickler._recurse = False

                pickler.save_reduce(
                    _create_compiled_function2,
                    (
                        obj.__module__,
                        compiled_function_tables[obj.__module__][0](obj),
                        obj.__dict__,
                        obj.__defaults__,
                    ),
                )

            if _super:
                pickler._byref = _byref
            if _memo:
                pickler._recurse = _recurse
        else:
            dill._dill.StockPickler.save_global(pickler, obj)


if __compiled__.standalone:  # pylint: disable=undefined-variable
    builtins.compiled_method = compiled_method
    builtins.compiled_function = compiled_function

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
