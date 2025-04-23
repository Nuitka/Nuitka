#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# pylint: disable=missing-module-docstring,protected-access,used-before-assignment

# spell-checker: ignore kwdefaults,globalvars

# Nuitka will optimize this away, but VS code will warn about them otherwise.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    compiled_function_tables = {}

try:
    import cloudpickle
except ImportError:
    pass
else:

    def _create_compiled_function(module_name, func_values):
        if module_name not in compiled_function_tables:
            __import__(module_name)

        # This gets the "_create_compiled_function" of the module and calls it.
        return compiled_function_tables[module_name][1](*func_values)

    orig_dynamic_function_reduce = (
        cloudpickle.cloudpickle.Pickler._dynamic_function_reduce
    )

    def _dynamic_function_reduce(self, func):
        if type(func).__name__ != "compiled_function":
            return orig_dynamic_function_reduce(self, func)

        try:
            module_name = func.__module__
        except AttributeError:
            return orig_dynamic_function_reduce(self, func)
        else:
            if module_name not in compiled_function_tables:
                return orig_dynamic_function_reduce(self, func)

            return (
                _create_compiled_function,
                (
                    module_name,
                    # This gets the "_reduce_compiled_function" of the module and calls it.
                    compiled_function_tables[module_name][0](func),
                ),
            )

    cloudpickle.cloudpickle.Pickler._dynamic_function_reduce = _dynamic_function_reduce

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
