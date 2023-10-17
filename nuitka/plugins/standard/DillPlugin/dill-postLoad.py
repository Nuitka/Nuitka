#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
# Not supposed to be good code,
# pylint: disable=invalid-name,missing-module-docstring,protected-access,too-many-branches
# spell-checker: ignore kwdefaults,globalvars
# Nuitka will optimize this away, but VS code will warn about them otherwise.
from typing import TYPE_CHECKING

import dill._dill

if TYPE_CHECKING:
    compiled_method = type
    compiled_function = type
    compiled_function_tables = ()


# Compiled methods need to be created.
@dill.register(compiled_method)
def save_compiled_method(pickler, obj):
    if str is not bytes:
        pickler.save_reduce(compiled_method, (obj.__func__, obj.__self__), obj=obj)
    else:
        pickler.save_reduce(
            compiled_method, (obj.im_func, obj.im_self, obj.im_class), obj=obj
        )


def _create_compiled_function2(module_name, func_values, func_dict, func_defaults):
    if module_name not in compiled_function_tables:
        __import__(module_name)

    func = compiled_function_tables[module_name][1](*func_values)
    if func_dict:
        for key, value in func_dict.items():
            func[key] = value

    func.__defaults__ = func_defaults

    return func


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
    if not dill._dill._locate_function(obj):
        stack = dill._dill.stack

        # TODO: Dead code, we cannot really make functions change what globals
        # they use. pylint: disable=unused-variable
        if getattr(pickler, "_recurse", False):
            from dill.detect import globalvars

            globs = globalvars(obj, recurse=True, builtin=True)
            if id(obj) in stack:
                globs = obj.__globals__ if str is not bytes else obj.func_globals
        else:
            globs = obj.__globals__ if str is not bytes else obj.func_globals

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
