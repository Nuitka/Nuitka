#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Builtins module. Information about builtins of the currently running Python.

"""

# Hide Python3 changes for builtin exception names
try:
    import exceptions

    builtin_exception_names = [
        str( x ) for x in dir( exceptions )
        if x.endswith( "Error" ) or x in ( "StopIteration", "GeneratorExit" )
    ]

    builtin_exception_values = {}

    for key in builtin_exception_names:
        builtin_exception_values[ key ] = getattr( exceptions, key )

except ImportError:
    exceptions = {}

    import sys

    for x in dir( sys.modules[ "builtins" ] ):
        name = str( x )

        if name.endswith( "Error" ) or name in ( "StopIteration", "GeneratorExit" ):
            exceptions[ name ] = x

    builtin_exception_names = [
        key for key, value in exceptions.items()
    ]

    builtin_exception_values = {}

    for key, value in exceptions.items():
        builtin_exception_values[ key ] = value

assert "ValueError" in builtin_exception_names
assert "StopIteration" in builtin_exception_names
assert "GeneratorExit" in builtin_exception_names
assert "AssertionError" in builtin_exception_names

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
