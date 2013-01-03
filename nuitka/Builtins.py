#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Builtins module. Information about builtins of the currently running Python.

"""

from nuitka import Utils

def isExceptionName( builtin_name ):
    if builtin_name.endswith( "Error" ) or builtin_name.endswith( "Exception" ):
        return True
    elif builtin_name in ( "StopIteration", "GeneratorExit" ):
        return True
    else:
        return False

# Hide Python3 changes for builtin exception names
try:
    import exceptions

    builtin_exception_names = [
        str( name ) for name in dir( exceptions )
        if isExceptionName( name )
    ]

    builtin_exception_values = {}

    for key in builtin_exception_names:
        builtin_exception_values[ key ] = getattr( exceptions, key )

    del name, key # Remove names uses in branch, pylint: disable=W0631

except ImportError:
    exceptions = {}

    import sys

    for x in dir( sys.modules[ "builtins" ] ):
        name = str( x )

        if isExceptionName( name ):
            exceptions[ name ] = x

    builtin_exception_names = [
        key for key, value in exceptions.items()
    ]

    builtin_exception_values = {}

    for key, value in exceptions.items():
        builtin_exception_values[ key ] = value

    del name, key, value, x # Remove names uses in branch, pylint: disable=W0631

assert "ValueError" in builtin_exception_names
assert "StopIteration" in builtin_exception_names
assert "GeneratorExit" in builtin_exception_names
assert "AssertionError" in builtin_exception_names
assert "BaseException" in builtin_exception_names
assert "Exception" in builtin_exception_names

builtin_names = [
    str( x )
    for x in __builtins__.keys()
]

builtin_names.remove( "__doc__" )
builtin_names.remove( "__name__" )
builtin_names.remove( "__package__" )
# TODO: Python3 may have others to remove.

assert "__import__" in builtin_names
assert "int" in builtin_names

assert "__doc__" not in builtin_names
assert "sys" not in builtin_names

builtin_all_names = builtin_names + builtin_exception_names

# For PyLint to be happy.
assert exceptions

builtin_anon_names = {
    "NoneType"                   : type( None ),
    "builtin_function_or_method" : type( len ),
    "ellipsis"                   : type( Ellipsis ),
    "NotImplementedType"         : type( NotImplemented )
}

builtin_anon_codes = {
    "NoneType"                   : "Py_TYPE( Py_None )",
    "builtin_function_or_method" : "&PyCFunction_Type",
    "ellipsis"                   : "&PyEllipsis_Type",
    "NotImplementedType"         : "Py_TYPE( Py_NotImplemented )"
}

if Utils.python_version < 300:
    class Temp:
        pass

    builtin_anon_names[ "classobj" ] = type( Temp )
    builtin_anon_codes[ "classobj" ] = "&PyClass_Type"

    del Temp
