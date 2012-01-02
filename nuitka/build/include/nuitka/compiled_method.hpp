//
//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at a later time to
//     the PSF. With this version of Nuitka, using it for a Closed Source and
//     distributing the binary only is not allowed.
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//

#ifndef __NUITKA_COMPILED_METHOD_H__
#define __NUITKA_COMPILED_METHOD_H__

// Compiled function and compile generator types may be referenced.
#include "compiled_function.hpp"
#include "compiled_generator.hpp"

// The backbone of the integration into CPython. Try to behave as well as normal method
// objects, or even better.

// The Nuitka_MethodObject is the storage associated with a compiled method instance
// of which there can be many for each code.

typedef struct {
    PyObject_HEAD

    Nuitka_FunctionObject *m_function;

    PyObject *m_dict;
    PyObject *m_weakrefs;

    PyObject *m_object;
    PyObject *m_class;
    PyObject *m_module;
} Nuitka_MethodObject;

extern PyTypeObject Nuitka_Method_Type;

// Make a method out of a function.
extern PyObject *Nuitka_Method_New( Nuitka_FunctionObject *function, PyObject *object, PyObject *klass );

static inline bool Nuitka_Method_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Method_Type;
}

#endif
