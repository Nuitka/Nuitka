//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "__helpers.hpp"

extern PyModuleObject *builtin_module;
extern PyDictObject *dict_builtin;

#include "nuitka/calling.hpp"

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_BUILTIN( PyObject *name )
{
    CHECK_OBJECT( (PyObject *)dict_builtin );
    CHECK_OBJECT( name );
    assert( Nuitka_String_CheckExact( name ) );

    PyObject *result = GET_STRING_DICT_VALUE(
        dict_builtin,
        (Nuitka_StringObject *)name
    );

    CHECK_OBJECT( result );

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

    PyObject *asObject0()
    {
        if ( this->value == NULL )
        {
            this->value = LOOKUP_BUILTIN( (PyObject *)*this->name );
        }

        CHECK_OBJECT( this->value );

        return this->value;
    }

    void update( PyObject *new_value )
    {
        CHECK_OBJECT( new_value );

        this->value = new_value;
    }


private:

    PythonBuiltin( PythonBuiltin const &  ) { assert( false );  }

    Nuitka_StringObject **name;
    PyObject *value;
};

extern void _initBuiltinModule();

#ifdef _NUITKA_EXE
// Original builtin values, currently only used for assertions.
extern PyObject *_python_original_builtin_value_type;
extern PyObject *_python_original_builtin_value_len;
extern PyObject *_python_original_builtin_value_range;
extern PyObject *_python_original_builtin_value_repr;
extern PyObject *_python_original_builtin_value_int;
extern PyObject *_python_original_builtin_value_iter;
extern PyObject *_python_original_builtin_value_long;

extern void _initBuiltinOriginalValues();
#endif

#endif
