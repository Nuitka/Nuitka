//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_FREELISTS_H__
#define __NUITKA_FREELISTS_H__

#ifndef __cplusplus
#include "stdbool.h"
#endif

#ifdef _NUITKA_EXPERIMENTAL_DISABLE_FREELIST_ALL
static const bool use_freelists = false;
#else
static const bool use_freelists = true;
#endif

#define allocateFromFreeList(free_list, object_type, type_type, size)                                                  \
    if (free_list != NULL) {                                                                                           \
        result = free_list;                                                                                            \
        free_list = *((object_type **)free_list);                                                                      \
        free_list##_count -= 1;                                                                                        \
        assert(free_list##_count >= 0);                                                                                \
                                                                                                                       \
        if (Py_SIZE(result) < size) {                                                                                  \
            result = PyObject_GC_Resize(object_type, result, size);                                                    \
            assert(result != NULL);                                                                                    \
        }                                                                                                              \
                                                                                                                       \
        Nuitka_Py_NewReference((PyObject *)result);                                                                    \
    } else {                                                                                                           \
        result = (object_type *)Nuitka_GC_NewVar(&type_type, size);                                                    \
    }                                                                                                                  \
    CHECK_OBJECT(result);

#define allocateFromFreeListFixed(free_list, object_type, type_type)                                                   \
    if (free_list != NULL) {                                                                                           \
        result = free_list;                                                                                            \
        free_list = *((object_type **)free_list);                                                                      \
        free_list##_count -= 1;                                                                                        \
        assert(free_list##_count >= 0);                                                                                \
                                                                                                                       \
        Nuitka_Py_NewReference((PyObject *)result);                                                                    \
    } else {                                                                                                           \
        result = (object_type *)Nuitka_GC_New(&type_type);                                                             \
    }                                                                                                                  \
    CHECK_OBJECT(result);

#define releaseToFreeList(free_list, object, max_free_list_count)                                                      \
    if (free_list != NULL || max_free_list_count == 0 || use_freelists == false) {                                     \
        if (free_list##_count >= max_free_list_count) {                                                                \
            PyObject_GC_Del(object);                                                                                   \
        } else {                                                                                                       \
            *((void **)object) = (void *)free_list;                                                                    \
            free_list = object;                                                                                        \
                                                                                                                       \
            free_list##_count += 1;                                                                                    \
        }                                                                                                              \
    } else {                                                                                                           \
        free_list = object;                                                                                            \
        *((void **)object) = NULL;                                                                                     \
                                                                                                                       \
        assert(free_list##_count == 0);                                                                                \
                                                                                                                       \
        free_list##_count += 1;                                                                                        \
    }

#if PYTHON_VERSION >= 0x3d0
NUITKA_MAY_BE_UNUSED static inline struct _Py_object_freelists *_Nuitka_object_freelists_GET(PyThreadState *tstate) {

#ifdef Py_GIL_DISABLED
    return &((_PyThreadStateImpl *)tstate)->freelists;
#else
    return &tstate->interp->object_state.freelists;
#endif
}
#endif

#endif

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
