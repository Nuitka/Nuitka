//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_CHECKERS_H__
#define __NUITKA_CHECKERS_H__

#ifdef __IDE_ONLY__
#include "Python.h"
#endif
// Helper to check that an object is valid and has positive reference count.
#define CHECK_OBJECT(value) (assert((value) != NULL), assert(Py_REFCNT(value) > 0))
#define CHECK_OBJECT_X(value) (assert((value) == NULL || Py_REFCNT(value) > 0))

// Helper to check an array of objects with CHECK_OBJECT
#ifndef __NUITKA_NO_ASSERT__
#define CHECK_OBJECTS(values, count)                                                                                   \
    {                                                                                                                  \
        for (int i = 0; i < count; i++) {                                                                              \
            CHECK_OBJECT((values)[i]);                                                                                 \
        }                                                                                                              \
    }
#else
#define CHECK_OBJECTS(values, count)
#endif

extern void CHECK_OBJECT_DEEP(PyObject *value);
extern void CHECK_OBJECT_DEEP_NAMED(char const *name, PyObject *value);
extern void CHECK_OBJECTS_DEEP(PyObject *const *values, Py_ssize_t size);

// Our replacement for "PyType_IsSubtype"
extern bool Nuitka_Type_IsSubtype(PyTypeObject *a, PyTypeObject *b);
static inline int Nuitka_PyObject_TypeCheck(PyObject *obj, PyTypeObject *type) {
    return Py_TYPE(obj) == type || Nuitka_Type_IsSubtype(Py_TYPE(obj), type);
}

// Our replacement for "PyObject_IsInstance"
extern int Nuitka_Object_IsInstance(PyThreadState *tstate, PyObject *instance, PyObject *cls);

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
