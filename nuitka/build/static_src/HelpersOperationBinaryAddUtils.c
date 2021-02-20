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
/* These slots are still manually coded and are used by the generated code.
 *
 * The plan should be to generate these as well, so e.g. we can have a slot
 * SLOT_nb_add_LONG_INT that is optimal too.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static PyObject *LIST_CONCAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    Py_ssize_t size = Py_SIZE(operand1) + Py_SIZE(operand2);

    PyListObject *result = (PyListObject *)PyList_New(size);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    PyObject **src = ((PyListObject *)operand1)->ob_item;
    PyObject **dest = result->ob_item;

    for (Py_ssize_t i = 0; i < Py_SIZE(operand1); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    src = ((PyListObject *)operand2)->ob_item;
    dest = result->ob_item + Py_SIZE(operand1);
    for (Py_ssize_t i = 0; i < Py_SIZE(operand2); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    return (PyObject *)result;
}
