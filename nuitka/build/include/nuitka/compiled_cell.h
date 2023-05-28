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
#ifndef __NUITKA_COMPILED_CELL_H__
#define __NUITKA_COMPILED_CELL_H__

/* This is a clone of the normal PyCell structure. We should keep it binary
 * compatible, just in case somebody crazy insists on it.
 */

extern PyTypeObject Nuitka_Cell_Type;

static inline bool Nuitka_Cell_Check(PyObject *object) { return Py_TYPE(object) == &Nuitka_Cell_Type; }

struct Nuitka_CellObject {
    /* Python object folklore: */
    PyObject_HEAD

        /* Content of the cell or NULL when empty */
        PyObject *ob_ref;
};

// Create cell with out value, and with or without reference given.
extern struct Nuitka_CellObject *Nuitka_Cell_Empty(void);
extern struct Nuitka_CellObject *Nuitka_Cell_New0(PyObject *value);
extern struct Nuitka_CellObject *Nuitka_Cell_New1(PyObject *value);

// Check stuff while accessing a compile cell in debug mode.
#ifdef __NUITKA_NO_ASSERT__
#define Nuitka_Cell_GET(cell) (((struct Nuitka_CellObject *)(cell))->ob_ref)
#else
#define Nuitka_Cell_GET(cell)                                                                                          \
    (CHECK_OBJECT(cell), assert(Nuitka_Cell_Check((PyObject *)cell)), (((struct Nuitka_CellObject *)(cell))->ob_ref))
#endif
#endif
