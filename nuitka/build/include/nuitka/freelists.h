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

#ifndef __NUITKA_FREELISTS_H__
#define __NUITKA_FREELISTS_H__

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
        _Py_NewReference((PyObject *)result);                                                                          \
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
        _Py_NewReference((PyObject *)result);                                                                          \
    } else {                                                                                                           \
        result = (object_type *)PyObject_GC_New(object_type, &type_type);                                              \
    }                                                                                                                  \
    CHECK_OBJECT(result);

#define releaseToFreeList(free_list, object, max_free_list_count)                                                      \
    if (free_list != NULL) {                                                                                           \
        if (free_list##_count > max_free_list_count) {                                                                 \
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

#endif
