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
#ifndef __NUITKA_PRELUDE_H__
#define __NUITKA_PRELUDE_H__

#ifdef __NUITKA_NO_ASSERT__
#define NDEBUG
#endif

// Include the Python C/API header files
#include "Python.h"
#include "methodobject.h"
#include "frameobject.h"

// Include the C header files most often used.
#include <stdio.h>

// An idea I first saw used with Cython, hint the compiler about branches that are more or
// less likely to be taken. And hint the compiler about things that we assume to be
// normally true. If other compilers can do similar, I would be grateful for howtos.

#ifdef __GNUC__
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

// A way to not give warnings about things that are declared, but might not be used like
// inline helper functions in headers or static per module variables from headers.

#ifdef __GNUC__
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

#ifdef __GNUC__
#define NUITKA_NO_RETURN __attribute__((__noreturn__))
#else
#define NUITKA_NO_RETURN
#endif

NUITKA_MAY_BE_UNUSED static PyObject *_eval_globals_tmp;
NUITKA_MAY_BE_UNUSED static PyObject *_eval_locals_tmp;

#define PYTHON_VERSION (PY_MAJOR_VERSION*100+PY_MINOR_VERSION*10+PY_MICRO_VERSION)

#if PYTHON_VERSION >= 300
// Python3 removed PyInt instead of renaming PyLong.
#define PyInt_FromString PyLong_FromString
#define PyInt_FromLong PyLong_FromLong
#define PyInt_AsLong PyLong_AsLong
#define PyInt_FromSsize_t PyLong_FromSsize_t

#define PyNumber_Int PyNumber_Long

#define PyObject_Unicode PyObject_Str

#endif

#if PYTHON_VERSION < 300
#define Nuitka_String_AsString PyString_AsString
#define Nuitka_String_AsString_Unchecked PyString_AS_STRING
#define Nuitka_String_Check PyString_Check
#define Nuitka_StringObject PyStringObject
#else
#define Nuitka_String_AsString _PyUnicode_AsString
// TODO: Clarify is there is something without checks.
#define Nuitka_String_AsString_Unchecked Nuitka_String_AsString
#define Nuitka_String_Check PyUnicode_Check
#define Nuitka_StringObject PyUnicodeObject
#endif


#if PYTHON_VERSION < 300

// With the idea to reduce the amount of exported symbols, make it clear that the module
// init function should of course be exported.
#ifdef __GNUC__
#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC __attribute__((visibility( "default" )))
#else
#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC
#endif

#define MOD_INIT( name ) NUITKA_MODULE_INIT_FUNCTION init##name( void )
#define MOD_RETURN_VALUE( value )

#else

#define MOD_INIT( name ) PyMODINIT_FUNC PyInit_##name( void )
#define MOD_RETURN_VALUE( value ) value
#endif

#include "nuitka/helpers.hpp"

#include "nuitka/compiled_function.hpp"

// Sentinel PyObject to be used for all our call iterator endings.
extern PyObject *_sentinel_value;

#include "nuitka/compiled_generator.hpp"
#include "nuitka/compiled_genexpr.hpp"

#include "nuitka/compiled_method.hpp"

#endif
