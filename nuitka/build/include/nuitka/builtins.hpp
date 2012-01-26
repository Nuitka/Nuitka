//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit patches or make the software available to licensors of
//     this software in either form, you automatically them grant them a
//     license for your part of the code under "Apache License 2.0" unless you
//     choose to remove this notice.
//
//     Kay Hayen uses the right to license his code under only GPL version 3,
//     to discourage a fork of Nuitka before it is "finished". He will later
//     make a new "Nuitka" release fully under "Apache License 2.0".
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//
#ifndef __NUITKA_BUILTINS_H__
#define __NUITKA_BUILTINS_H__

extern PyModuleObject *_module_builtin;

#include "nuitka/calling.hpp"

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_BUILTIN( PyObject *name )
{
    assertObject( name );
    assert( Nuitka_String_Check( name ) );

    PyDictEntry *entry = GET_PYDICT_ENTRY(
        _module_builtin,
        (Nuitka_StringObject *)name
    );

    PyObject *result = entry->me_value;

    assertObject( result );

    return result;
}

class PythonBuiltin
{
    public:
        explicit PythonBuiltin( PyObject **name )
        {
            this->name = (Nuitka_StringObject **)name;
            this->value = NULL;
        }

        PyObject *asObject()
        {
            if ( this->value == NULL )
            {
                PyDictEntry *entry = GET_PYDICT_ENTRY(
                    _module_builtin,
                    *this->name
                );

                this->value = entry->me_value;
            }

            assertObject( this->value );

            return this->value;
        }

        void refresh( void )
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY(
                _module_builtin,
                *this->name
            );

            this->value = entry->me_value;
        }

        PyObject *call()
        {
            return CALL_FUNCTION_NO_ARGS(
                this->asObject()
            );
        }


        PyObject *call1( PyObject *arg )
        {
            return CALL_FUNCTION_WITH_POSARGS(
                this->asObject(),
                PyObjectTemporary( MAKE_TUPLE1( arg ) ).asObject()
            );
        }

        PyObject *call_args( PyObject *args )
        {
            return CALL_FUNCTION_WITH_POSARGS(
                this->asObject(),
                PyObjectTemporary( args ).asObject()
            );
        }

        PyObject *call_kw( PyObject *kw )
        {
            return CALL_FUNCTION_WITH_KEYARGS(
                this->asObject(),
                kw
            );
        }

        PyObject *call_args_kw( PyObject *args, PyObject *kw )
        {
            return CALL_FUNCTION(
                this->asObject(),
                args,
                kw
            );
        }


    private:

        PythonBuiltin( PythonBuiltin const &  ) = delete;

        Nuitka_StringObject **name;
        PyObject *value;
};

#endif
