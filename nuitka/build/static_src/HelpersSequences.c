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
/* This helpers is used to work with sequence interfaces.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

bool SEQUENCE_SET_ITEM(PyObject *sequence, Py_ssize_t index, PyObject *value) {
    CHECK_OBJECT(sequence);
    CHECK_OBJECT(value);

    PySequenceMethods *tp_as_sequence = Py_TYPE(sequence)->tp_as_sequence;

    if (tp_as_sequence != NULL && tp_as_sequence->sq_ass_item) {
        if (index < 0) {
            if (tp_as_sequence->sq_length) {
                Py_ssize_t length = (*tp_as_sequence->sq_length)(sequence);

                if (length < 0) {
                    return false;
                }

                index += length;
            }
        }

        int res = tp_as_sequence->sq_ass_item(sequence, index, value);

        if (unlikely(res == -1)) {
            return false;
        }

        return true;
    } else {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object does not support item assignment", sequence);
        return false;
    }
}

Py_ssize_t Nuitka_PyObject_Size(PyObject *sequence) {
    CHECK_OBJECT(sequence);

    PySequenceMethods *tp_as_sequence = Py_TYPE(sequence)->tp_as_sequence;

    if (tp_as_sequence && tp_as_sequence->sq_length) {
        return tp_as_sequence->sq_length(sequence);
    }

    return PyMapping_Size(sequence);
}
