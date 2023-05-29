//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* This helpers is used to work with mapping interfaces.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

Py_ssize_t Nuitka_PyMapping_Size(PyObject *mapping) {
    CHECK_OBJECT(mapping);

    PyMappingMethods *tp_as_mapping = Py_TYPE(mapping)->tp_as_mapping;

    if (tp_as_mapping != NULL && tp_as_mapping->mp_length) {
        Py_ssize_t result = tp_as_mapping->mp_length(mapping);
        assert(result >= 0);
        return result;
    }

    if (Py_TYPE(mapping)->tp_as_sequence && Py_TYPE(mapping)->tp_as_sequence->sq_length) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("%s is not a mapping", mapping);
        return -1;
    }

    SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("object of type '%s' has no len()", mapping);
    return -1;
}
