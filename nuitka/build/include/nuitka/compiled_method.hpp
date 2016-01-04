//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

#ifndef __NUITKA_COMPILED_METHOD_H__
#define __NUITKA_COMPILED_METHOD_H__

// Compiled function and compile generator types may be referenced.
#include "compiled_function.hpp"
#include "compiled_generator.hpp"

// The backbone of the integration into CPython. Try to behave as well as normal
// method objects, or even better.

// The Nuitka_MethodObject is the storage associated with a compiled method
// instance of which there can be many for each code.

typedef struct {
    PyObject_HEAD

    Nuitka_FunctionObject *m_function;

    PyObject *m_weakrefs;

    PyObject *m_object;
    PyObject *m_class;
} Nuitka_MethodObject;

extern PyTypeObject Nuitka_Method_Type;

// Make a method out of a function.
extern PyObject *Nuitka_Method_New( Nuitka_FunctionObject *function, PyObject *object, PyObject *klass );

static inline bool Nuitka_Method_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Method_Type;
}

#endif
