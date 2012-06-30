//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
//
#ifndef __NUITKA_BUILTINS_H__
#define __NUITKA_BUILTINS_H__

extern PyModuleObject *module_builtin;

#include "nuitka/calling.hpp"

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_BUILTIN( PyObject *name )
{
    assertObject( name );
    assert( Nuitka_String_Check( name ) );

    PyDictEntry *entry = GET_PYDICT_ENTRY(
        module_builtin,
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
                    module_builtin,
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
                module_builtin,
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
