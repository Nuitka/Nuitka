//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
/** For setting exceptions.
 *
 * These are non-inline variants for exception raises, done so to avoid the code bloat.
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

void FORMAT_NAME_ERROR(PyObject **exception_type, PyObject **exception_value, PyObject *variable_name) {
    *exception_type = PyExc_NameError;
    Py_INCREF(*exception_type);

    *exception_value =
        Nuitka_String_FromFormat("name '%s' is not defined", Nuitka_String_AsString_Unchecked(variable_name));
    CHECK_OBJECT(*exception_value);
}

#if PYTHON_VERSION < 0x340
void FORMAT_GLOBAL_NAME_ERROR(PyObject **exception_type, PyObject **exception_value, PyObject *variable_name) {
    *exception_type = PyExc_NameError;
    Py_INCREF(*exception_type);

    *exception_value =
        Nuitka_String_FromFormat("global name '%s' is not defined", Nuitka_String_AsString_Unchecked(variable_name));
    CHECK_OBJECT(*exception_value);
}
#endif

void FORMAT_UNBOUND_LOCAL_ERROR(PyObject **exception_type, PyObject **exception_value, PyObject *variable_name) {
    *exception_type = PyExc_UnboundLocalError;
    Py_INCREF(*exception_type);

    *exception_value = Nuitka_String_FromFormat("local variable '%s' referenced before assignment",
                                                Nuitka_String_AsString_Unchecked(variable_name));
    CHECK_OBJECT(*exception_value);
}

void FORMAT_UNBOUND_CLOSURE_ERROR(PyObject **exception_type, PyObject **exception_value, PyObject *variable_name) {
    *exception_type = PyExc_NameError;
    Py_INCREF(*exception_type);

    *exception_value = Nuitka_String_FromFormat("free variable '%s' referenced before assignment in enclosing scope",
                                                Nuitka_String_AsString_Unchecked(variable_name));
    CHECK_OBJECT(*exception_value);
}