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
""" Built-ins module. Information about built-ins of the running Python.

"""

import sys
from types import BuiltinFunctionType, FunctionType, GeneratorType

from nuitka.__past__ import builtins
from nuitka.containers.odict import OrderedDict
from nuitka.PythonVersions import python_version


def _getBuiltinExceptionNames():
    def isExceptionName(builtin_name):
        if builtin_name.endswith("Error") or builtin_name.endswith("Exception"):
            return True
        elif builtin_name in (
            "StopIteration",
            "GeneratorExit",
            "SystemExit",
            "NotImplemented",
            "KeyboardInterrupt",
            "StopAsyncIteration",
        ):
            return True
        else:
            return False

    exceptions = OrderedDict()

    # Hide Python3 changes for built-in exception names
    if python_version < 0x300:
        import exceptions as builtin_exceptions  # python2 code, pylint: disable=import-error

        for key in sorted(dir(builtin_exceptions)):
            name = str(key)

            if isExceptionName(name):
                exceptions[name] = getattr(builtin_exceptions, key)

        for key in sorted(dir(builtins)):
            name = str(key)

            if isExceptionName(name):
                exceptions[name] = getattr(builtins, key)
    else:

        for key in sorted(dir(builtins)):
            if isExceptionName(key):
                exceptions[key] = getattr(builtins, key)

    return list(exceptions.keys()), exceptions


builtin_exception_names, builtin_exception_values = _getBuiltinExceptionNames()
builtin_exception_values_list = tuple(builtin_exception_values.values())


# Just to make sure it's covering these cases correctly.
assert "TypeError" in builtin_exception_names
assert "ValueError" in builtin_exception_names
assert "StopIteration" in builtin_exception_names
assert "GeneratorExit" in builtin_exception_names
assert "AssertionError" in builtin_exception_names
assert "BaseException" in builtin_exception_names
assert "Exception" in builtin_exception_names
assert "NotImplemented" in builtin_exception_names

assert "StopAsyncIteration" in builtin_exception_names or python_version < 0x350


def _getBuiltinNames():
    names = [str(x) for x in dir(builtins)]
    names.sort()

    for builtin_exception_name in builtin_exception_names:
        if builtin_exception_name in names:
            names.remove(builtin_exception_name)

    names.remove("__doc__")
    names.remove("__name__")
    names.remove("__package__")

    if "__loader__" in names:
        names.remove("__loader__")

    if "__spec__" in names:
        names.remove("__spec__")

    warnings = []

    for builtin_name in names:
        if builtin_name.endswith("Warning"):
            warnings.append(builtin_name)

    for builtin_name in warnings:
        names.remove(builtin_name)

    return names, warnings


builtin_names, builtin_warnings = _getBuiltinNames()
builtin_named_values = dict((getattr(builtins, x), x) for x in builtin_names)
builtin_named_values_list = tuple(builtin_named_values)

assert type in builtin_named_values

assert "__import__" in builtin_names
assert "int" in builtin_names
assert "type" in builtin_names

assert "__doc__" not in builtin_names
assert "sys" not in builtin_names

builtin_all_names = builtin_names + builtin_exception_names + builtin_warnings


def getBuiltinTypeNames():
    result = []

    for builtin_name in builtin_names:
        if isinstance(getattr(builtins, builtin_name), type):
            result.append(builtin_name)

    return tuple(sorted(result))


builtin_type_names = getBuiltinTypeNames()


def _getAnonBuiltins():
    # We use the order when encoding in the constants blob. Therefore it is imported
    # to not reorder these values, the C side uses the absolute indexes.
    anon_names = OrderedDict()
    anon_codes = OrderedDict()

    # Strangely these are not in Python3 types module
    anon_names["NoneType"] = type(None)
    anon_codes["NoneType"] = "Py_TYPE(Py_None)"

    anon_names["ellipsis"] = type(Ellipsis)  # see above
    anon_codes["ellipsis"] = "&PyEllipsis_Type"

    anon_names["NotImplementedType"] = type(NotImplemented)
    anon_codes["NotImplementedType"] = "Py_TYPE(Py_NotImplemented)"

    anon_names["function"] = FunctionType
    anon_codes["function"] = "&PyFunction_Type"

    anon_names["generator"] = GeneratorType
    anon_codes["generator"] = "&PyGenerator_Type"

    anon_names["builtin_function_or_method"] = BuiltinFunctionType
    anon_codes["builtin_function_or_method"] = "&PyCFunction_Type"

    # Can't really have it until we have __nuitka__
    # "compiled_function"          : BuiltinFunctionType,
    # "compiled_generator"         : GeneratorType, # see above
    # anon_codes["compiled_function"] =  "&Nuitka_Function_Type"
    # anon_codes["compiled_generator"] =  "&Nuitka_Generator_Type"

    anon_names["code"] = type(_getAnonBuiltins.__code__)
    anon_codes["code"] = "&PyCode_Type"

    if python_version < 0x300:
        # There are only there for Python2,
        # pylint: disable=I0021,no-name-in-module
        from types import ClassType, InstanceType, MethodType

        with open(sys.executable) as any_file:
            anon_names["file"] = type(any_file)
        anon_codes["file"] = "&PyFile_Type"

        anon_names["classobj"] = ClassType
        anon_codes["classobj"] = "&PyClass_Type"

        anon_names["instance"] = InstanceType
        anon_codes["instance"] = "&PyInstance_Type"

        anon_names["instancemethod"] = MethodType
        anon_codes["instancemethod"] = "&PyMethod_Type"

    return anon_names, anon_codes


builtin_anon_names, builtin_anon_codes = _getAnonBuiltins()
builtin_anon_values = OrderedDict((b, a) for a, b in builtin_anon_names.items())

# For being able to check if it's not hashable, we need something not using
# a hash.
builtin_anon_value_list = tuple(builtin_anon_values)
