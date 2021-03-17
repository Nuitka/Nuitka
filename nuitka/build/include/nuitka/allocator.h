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
#ifndef __NUITKA_ALLOCATOR_H__
#define __NUITKA_ALLOCATOR_H__

NUITKA_MAY_BE_UNUSED static void *Nuitka_GC_NewVar(PyTypeObject *tp, Py_ssize_t nitems) {
    assert(nitems >= 0);

    size_t size = _PyObject_VAR_SIZE(tp, nitems);
    PyVarObject *op = (PyVarObject *)_PyObject_GC_Malloc(size);
    assert(op != NULL);

    Py_TYPE(op) = tp;
    Py_SIZE(op) = size;
    Py_REFCNT(op) = 1;

    // TODO: Above assignments might replace this actually.
    op = PyObject_INIT_VAR(op, tp, nitems);

    return op;
}

#endif
