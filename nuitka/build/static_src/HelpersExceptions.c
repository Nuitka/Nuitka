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

void SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyObject *exception_type, char const *format, char const *value) {
    PyErr_Format(exception_type, format, value);
}

void SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyObject *exception_type, char const *format, char const *value1,
                                         char const *value2) {
    PyErr_Format(exception_type, format, value1, value2);
}

void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(char const *format, PyObject *mistyped) {
    SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, format, Py_TYPE(mistyped)->tp_name);
}

static char const *TYPE_NAME_DESC(PyObject *type) {
    if (type == Py_None) {
        return "None";
    } else {
        return Py_TYPE(type)->tp_name;
    }
}

void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_NICE(char const *format, PyObject *mistyped) {
    SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, format, TYPE_NAME_DESC(mistyped));
}

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