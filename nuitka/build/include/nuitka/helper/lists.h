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
#ifndef __NUITKA_HELPER_LISTS_H__
#define __NUITKA_HELPER_LISTS_H__

// Like PyList_SET_ITEM but takes a reference to the item.
#define PyList_SET_ITEM0(tuple, index, value)                                                                          \
    {                                                                                                                  \
        PyObject *tmp = value;                                                                                         \
        Py_INCREF(tmp);                                                                                                \
        PyList_SET_ITEM(tuple, index, tmp);                                                                            \
    }

#ifndef _PyList_ITEMS
#define _PyList_ITEMS(op) (((PyListObject *)(op))->ob_item)
#endif

#if PYTHON_VERSION >= 0x3a0
#define NUITKA_LIST_HAS_FREELIST 1
extern PyObject *MAKE_LIST_EMPTY(Py_ssize_t size);
#else
#define NUITKA_LIST_HAS_FREELIST 0

#define MAKE_LIST_EMPTY(size) PyList_New(size)
#endif

extern bool LIST_EXTEND(PyObject *list, PyObject *other);
extern bool LIST_EXTEND_FOR_UNPACK(PyObject *list, PyObject *other);

// Like PyList_Append, but we get to specify the transfer of refcount ownership.
extern bool LIST_APPEND1(PyObject *target, PyObject *item);
extern bool LIST_APPEND0(PyObject *target, PyObject *item);

// Like list.clear
extern void LIST_CLEAR(PyObject *target);

// Like list.reverse
extern void LIST_REVERSE(PyObject *list);

// Like list.copy
extern PyObject *LIST_COPY(PyObject *list);

// Like list.count
extern PyObject *LIST_COUNT(PyObject *list, PyObject *item);

// Like list.index
extern PyObject *LIST_INDEX2(PyObject *list, PyObject *item);
extern PyObject *LIST_INDEX3(PyObject *list, PyObject *item, PyObject *start);
extern PyObject *LIST_INDEX4(PyObject *list, PyObject *item, PyObject *start, PyObject *stop);

// Like list.index
extern bool LIST_INSERT(PyObject *list, PyObject *index, PyObject *item);
// Like PyList_Insert
extern void LIST_INSERT_CONST(PyObject *list, Py_ssize_t index, PyObject *item);

extern PyObject *MAKE_LIST(PyObject *iterable);

extern bool LIST_EXTEND_FROM_LIST(PyObject *list, PyObject *other);

#endif