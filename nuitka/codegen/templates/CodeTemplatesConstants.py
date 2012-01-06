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
""" Templates for the constants handling.

"""

template_constants_reading = """
#include "nuitka/prelude.hpp"

// Sentinel PyObject to be used for all our call iterator endings. It will become
// a PyCObject pointing to NULL. It's address is unique, and that's enough.
PyObject *_sentinel_value = NULL;

PyModuleObject *_module_builtin = NULL;

%(constant_declarations)s

static void __initConstants( void )
{
    UNSTREAM_INIT();

%(constant_inits)s
}

void _initConstants( void )
{
    if ( _sentinel_value == NULL )
    {
#if PYTHON_VERSION < 300
        _sentinel_value = PyCObject_FromVoidPtr( NULL, NULL );
#else
        // The NULL value is not allowed for a capsule, so use something else.
        _sentinel_value = PyCapsule_New( (void *)27, "sentinel", NULL );
#endif
        assert( _sentinel_value );

#if PYTHON_VERSION < 300
        _module_builtin = (PyModuleObject *)PyImport_ImportModule( "__builtin__" );
#else
        _module_builtin = (PyModuleObject *)PyImport_ImportModule( "builtins" );
#endif
        assert( _module_builtin );

        __initConstants();
    }
}
"""

template_constants_declaration = """\
// Call this to initialize all of the below
void _initConstants( void );

%(constant_declarations)s
"""

template_reverse_macro = """\
#define EVAL_ORDERED_%(count)d( %(args)s ) %(expanded)s"""

template_noreverse_macro = """\
#define EVAL_ORDERED_%(count)d( %(args)s ) %(args)s"""
