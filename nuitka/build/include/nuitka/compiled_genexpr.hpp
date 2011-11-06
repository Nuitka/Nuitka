//
//     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
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
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
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
#ifndef __NUITKA_COMPILED_GENEXPR_H__
#define __NUITKA_COMPILED_GENEXPR_H__

#include "Python.h"
#include "methodobject.h"
#include "frameobject.h"

// Compiled generator expression type.

// Another cornerstone of the integration into CPython. Try to behave as well as normal
// generator expression objects do or even better.

// TODO: Could optimize it through a compile time determination and then provide as a
// command line define.
const int MAX_ITERATOR_COUNT = 20;

// The Nuitka_GenexprObject is the storage associated with a compiled generator object
// instance of which there can be many for each code.
typedef struct {
    PyObject_HEAD

    PyObject *m_name;

    void *m_context;
    releaser m_cleanup;

    PyObject *m_weakrefs;

    int m_running;
    void *m_code;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

    // Store the iterator provided at creation time here.
    PyObject *iterators[ MAX_ITERATOR_COUNT ];

    PyFrameObject *m_frame;
    PyCodeObject *m_code_object;

    int iterator_level;
} Nuitka_GenexprObject;

typedef PyObject * (*producer)( Nuitka_GenexprObject * );

extern PyTypeObject Nuitka_Genexpr_Type;

extern PyObject *Nuitka_Genexpr_New( producer code, PyObject *name, PyCodeObject *code_object, PyObject *iterated, int iterator_count, void *context, releaser cleanup );

#endif
