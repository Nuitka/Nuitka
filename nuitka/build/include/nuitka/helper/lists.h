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

extern PyObject *MAKE_LIST(PyObject *iterable);

extern PyObject *LIST_COPY(PyObject *list);

extern bool LIST_EXTEND_FROM_LIST(PyObject *list, PyObject *other);

// Like PyList_SET_ITEM but takes a reference to the item.
#define PyList_SET_ITEM0(tuple, index, value)                                                                          \
    {                                                                                                                  \
        PyObject *tmp = value;                                                                                         \
        Py_INCREF(tmp);                                                                                                \
        PyList_SET_ITEM(tuple, index, tmp);                                                                            \
    }

#endif

extern bool LIST_EXTEND(PyObject *list, PyObject *other);
extern bool LIST_EXTEND_FOR_UNPACK(PyObject *list, PyObject *other);

// Like PyList_Append, but we get to specify the transfer of refcount ownership.
extern bool LIST_APPEND1(PyObject *target, PyObject *item);
extern bool LIST_APPEND0(PyObject *target, PyObject *item);
