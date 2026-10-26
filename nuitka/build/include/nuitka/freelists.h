//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_FREELISTS_H__
#define __NUITKA_FREELISTS_H__

#ifndef __cplusplus
#include <stdbool.h>
#endif

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#ifdef Py_GIL_DISABLED
#define NUITKA_FREELIST_DECLARE_LOCK(free_list) NUITKA_MAY_BE_UNUSED static uint8_t free_list##_lock = 0;

#define NUITKA_FREELIST_LOCK(free_list)                                                                                \
    do {                                                                                                               \
        uint8_t _expected = 0;                                                                                         \
        while (!_Py_atomic_compare_exchange_uint8(&free_list##_lock, &_expected, 1)) {                                 \
            _expected = 0;                                                                                             \
            while (_Py_atomic_load_uint8_relaxed(&free_list##_lock) != 0) {                                            \
                /* spin without bouncing the lock cache line */                                                        \
            }                                                                                                          \
        }                                                                                                              \
    } while (0)

#define NUITKA_FREELIST_UNLOCK(free_list) _Py_atomic_store_uint8(&free_list##_lock, 0)
#else
#define NUITKA_FREELIST_DECLARE_LOCK(free_list)
#define NUITKA_FREELIST_LOCK(free_list)
#define NUITKA_FREELIST_UNLOCK(free_list)
#endif

#ifdef _NUITKA_EXPERIMENTAL_DISABLE_FREELIST_ALL
static const bool use_freelists = false;
#else
static const bool use_freelists = true;
#endif

#define allocateFromFreeList(free_list, object_type, type_type, size)                                                  \
    if (use_freelists == true) {                                                                                       \
        NUITKA_FREELIST_LOCK(free_list);                                                                               \
        if (free_list != NULL) {                                                                                       \
            result = free_list;                                                                                        \
            free_list = *((object_type **)free_list);                                                                  \
            free_list##_count -= 1;                                                                                    \
            assert(free_list##_count >= 0);                                                                            \
            NUITKA_FREELIST_UNLOCK(free_list);                                                                         \
                                                                                                                       \
            if (Py_SIZE(result) < size) {                                                                              \
                result = PyObject_GC_Resize(object_type, result, size);                                                \
                assert(result != NULL);                                                                                \
            }                                                                                                          \
                                                                                                                       \
            Nuitka_Py_NewReference((PyObject *)result);                                                                \
        } else {                                                                                                       \
            NUITKA_FREELIST_UNLOCK(free_list);                                                                         \
            result = (object_type *)Nuitka_GC_NewVar(&type_type, size);                                                \
        }                                                                                                              \
    } else {                                                                                                           \
        result = (object_type *)Nuitka_GC_NewVar(&type_type, size);                                                    \
    }                                                                                                                  \
    CHECK_OBJECT(result);

#define allocateFromFreeListFixed(free_list, object_type, type_type)                                                   \
    if (use_freelists == true) {                                                                                       \
        NUITKA_FREELIST_LOCK(free_list);                                                                               \
        if (free_list != NULL) {                                                                                       \
            result = free_list;                                                                                        \
            free_list = *((object_type **)free_list);                                                                  \
            free_list##_count -= 1;                                                                                    \
            assert(free_list##_count >= 0);                                                                            \
            NUITKA_FREELIST_UNLOCK(free_list);                                                                         \
                                                                                                                       \
            Nuitka_Py_NewReference((PyObject *)result);                                                                \
        } else {                                                                                                       \
            NUITKA_FREELIST_UNLOCK(free_list);                                                                         \
            result = (object_type *)Nuitka_GC_New(&type_type);                                                         \
        }                                                                                                              \
    } else {                                                                                                           \
        result = (object_type *)Nuitka_GC_New(&type_type);                                                             \
    }                                                                                                                  \
    CHECK_OBJECT(result);

#define releaseToFreeList(free_list, object, max_free_list_count)                                                      \
    if (use_freelists == false) {                                                                                      \
        PyObject_GC_Del(object);                                                                                       \
    } else {                                                                                                           \
        NUITKA_FREELIST_LOCK(free_list);                                                                               \
        if (free_list##_count >= max_free_list_count) {                                                                \
            NUITKA_FREELIST_UNLOCK(free_list);                                                                         \
            PyObject_GC_Del(object);                                                                                   \
        } else {                                                                                                       \
            *((void **)object) = (void *)free_list;                                                                    \
            free_list = object;                                                                                        \
                                                                                                                       \
            free_list##_count += 1;                                                                                    \
            NUITKA_FREELIST_UNLOCK(free_list);                                                                         \
        }                                                                                                              \
    }

#if PYTHON_VERSION >= 0x3d0

#if PYTHON_VERSION >= 0x3e0

// CPython 3.14 changed the layout before post-QSBR interpreter fields in
// 3.14.4 and again in 3.14.5.
static inline struct _Py_freelists *Nuitka_Py_freelists_GET(PyThreadState *tstate) {
#ifdef Py_GIL_DISABLED
    return &((_PyThreadStateImpl *)tstate)->freelists;
#else
#if _NUITKA_MODULE_MODE && PYTHON_VERSION < 0x3f0
    return (struct _Py_freelists *)Nuitka_PyInterpreterState_AdjustPostQsbrPointer(
        &tstate->interp->object_state.freelists);
#else
    return &tstate->interp->object_state.freelists;
#endif
#endif
}

// Like _PyFreeList_Pop but doesn't set the reference, may also be totally
// unnecessary to have.
static inline PyObject *Nuitka_PyFreeList_Pop(struct _Py_freelist *freelist) {
    return _PyFreeList_PopNoStats(freelist);
}

#else

NUITKA_MAY_BE_UNUSED static inline struct _Py_object_freelists *_Nuitka_object_freelists_GET(PyThreadState *tstate) {

#ifdef Py_GIL_DISABLED
    return &((_PyThreadStateImpl *)tstate)->freelists;
#else
    return &tstate->interp->object_state.freelists;
#endif
}
#endif

#endif

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
