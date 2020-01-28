//     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_COMPILED_CELL_H__
#define __NUITKA_COMPILED_CELL_H__

/* This is a clone of the normal PyCell structure. We should keep it binary
 * compatible, just in case somebody crazy insists on it.
 */

extern PyTypeObject Nuitka_Cell_Type;

static inline bool Nuitka_Cell_Check(PyObject *object) { return Py_TYPE(object) == &Nuitka_Cell_Type; }

struct Nuitka_CellObject {
    /* Python object folklore: */
    PyObject_HEAD;

    /* Content of the cell or NULL when empty */
    PyObject *ob_ref;
};

extern struct Nuitka_CellObject *Nuitka_Cell_New(void);

extern void Nuitka_Cells_New(struct Nuitka_CellObject **closure, int count);

NUITKA_MAY_BE_UNUSED static struct Nuitka_CellObject *PyCell_NEW0(PyObject *value) {
    CHECK_OBJECT(value);

    struct Nuitka_CellObject *result = Nuitka_Cell_New();
    assert(result != NULL);

    result->ob_ref = value;
    Py_INCREF(value);

    return result;
}

NUITKA_MAY_BE_UNUSED static struct Nuitka_CellObject *PyCell_NEW1(PyObject *value) {
    CHECK_OBJECT(value);

    struct Nuitka_CellObject *result = Nuitka_Cell_New();
    assert(result != NULL);

    result->ob_ref = value;

    return result;
}

NUITKA_MAY_BE_UNUSED static struct Nuitka_CellObject *PyCell_EMPTY(void) {
    struct Nuitka_CellObject *result = Nuitka_Cell_New();
    result->ob_ref = NULL;

    return result;
}

#endif
