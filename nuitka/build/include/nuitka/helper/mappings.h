//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_MAPPINGS_H__
#define __NUITKA_MAPPINGS_H__

extern Py_ssize_t Nuitka_PyMapping_Size(PyObject *mapping);

NUITKA_MAY_BE_UNUSED static int MAPPING_HAS_ITEM(PyObject *mapping, PyObject *key) {
    PyObject *result = PyObject_GetItem(mapping, key);

    if (result == NULL) {
        bool had_key_error = CHECK_AND_CLEAR_KEY_ERROR_OCCURRED();

        if (had_key_error) {
            return 0;
        } else {
            return -1;
        }
    } else {
        Py_DECREF(result);
        return 1;
    }
}

#endif