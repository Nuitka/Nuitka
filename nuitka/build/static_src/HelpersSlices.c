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
/* Small helpers to work with slices their contents */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION >= 0x3a0
PyObject *Nuitka_Slice_New(PyObject *start, PyObject *stop, PyObject *step) {
    PyInterpreterState *interp = _PyInterpreterState_GET();

    PySliceObject *result_slice;

    if (interp->slice_cache != NULL) {
        result_slice = interp->slice_cache;
        interp->slice_cache = NULL;

        Nuitka_Py_NewReference((PyObject *)result_slice);
    } else {
        result_slice = (PySliceObject *)Nuitka_GC_New(&PySlice_Type);

        if (result_slice == NULL) {
            return NULL;
        }
    }

    if (step == NULL) {
        step = Py_None;
    }
    if (start == NULL) {
        start = Py_None;
    }
    if (stop == NULL) {
        stop = Py_None;
    }

    Py_INCREF(step);
    result_slice->step = step;
    Py_INCREF(start);
    result_slice->start = start;
    Py_INCREF(stop);
    result_slice->stop = stop;

    Nuitka_GC_Track(result_slice);

    return (PyObject *)result_slice;
}

#endif