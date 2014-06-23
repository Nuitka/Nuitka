//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_PRELUDE_H__
#define __NUITKA_PRELUDE_H__

#ifdef __NUITKA_NO_ASSERT__
#define NDEBUG
#endif

// Include the Python version numbers, and define our own take of what
// versions should be
#include "patchlevel.h"
#define PYTHON_VERSION (PY_MAJOR_VERSION*100+PY_MINOR_VERSION*10+PY_MICRO_VERSION)

// This is needed or else we can't create modules name "proc" or "func". For
// Python3, the name collision can't happen, so we can limit it to Python2.
#if PYTHON_VERSION < 300
#define initproc python_initproc
#define initfunc python_initfunc
#define initstate system_initstate
#endif

// Include the Python C/API header files
#include "Python.h"
#include "methodobject.h"
#include "frameobject.h"
#include "pydebug.h"
#include "marshal.h"

#if PYTHON_VERSION < 300
#undef initproc
#undef initfunc
#undef initstate
#endif

// Include the C header files most often used.
#include <stdio.h>

// An idea I first saw used with Cython, hint the compiler about branches that
// are more or less likely to be taken. And hint the compiler about things that
// we assume to be normally true. If other compilers can do similar, I would be
// grateful for howtos.

#ifdef __GNUC__
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

// A way to not give warnings about things that are declared, but might not be
// used like inline helper functions in headers or static per module variables
// from headers.

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

#ifdef __GNUC__
#define NUITKA_FORCE_INLINE __attribute__((always_inline))
#else
#define NUITKA_FORCE_INLINE
#endif

NUITKA_MAY_BE_UNUSED static PyObject *_eval_globals_tmp;
NUITKA_MAY_BE_UNUSED static PyObject *_eval_locals_tmp;


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
#define Nuitka_StringIntern PyString_InternInPlace
#else
#define Nuitka_String_AsString _PyUnicode_AsString
// Note: There seems to be no variant that does it without checks, so rolled our
// own.
#define Nuitka_String_AsString_Unchecked _PyUnicode_AS_STRING
#define Nuitka_String_Check PyUnicode_Check
#define Nuitka_StringObject PyUnicodeObject
#define Nuitka_StringIntern PyUnicode_InternInPlace
#endif


// With the idea to reduce the amount of exported symbols in the DLLs, make it
// clear that the module init function should of course be exported, but not for
// executable, where we call it ourselves.
#if defined( _NUITKA_EXE )

#if PYTHON_VERSION < 300
#define NUITKA_MODULE_INIT_FUNCTION void
#else
#define NUITKA_MODULE_INIT_FUNCTION PyObject *
#endif

#elif defined( __GNUC__ )

#if PYTHON_VERSION < 300
#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC __attribute__(( visibility( "default" )))
#else
#define NUITKA_MODULE_INIT_FUNCTION extern "C" __attribute__(( visibility( "default" ))) PyObject *
#endif

#else

#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC

#endif

// The name of the entry point for DLLs changed between Python versions, and
// this is.
#if PYTHON_VERSION < 300

#define MOD_INIT_NAME( name ) init##name
#define MOD_INIT_DECL( name ) NUITKA_MODULE_INIT_FUNCTION init##name( void )
#define MOD_RETURN_VALUE( value )

#else

#define MOD_INIT_NAME( name ) PyInit_##name
#define MOD_INIT_DECL( name ) NUITKA_MODULE_INIT_FUNCTION PyInit_##name( void )
#define MOD_RETURN_VALUE( value ) value

#endif

// These two express if a directly called function should be exported (C++
// level) or if it can be local to the file.
#define NUITKA_CROSS_MODULE
#define NUITKA_LOCAL_MODULE static

#include "nuitka/helpers.hpp"

#include "nuitka/compiled_function.hpp"

// Sentinel PyObject to be used for all our call iterator endings.
extern PyObject *_sentinel_value;

#include "nuitka/compiled_generator.hpp"

#include "nuitka/compiled_method.hpp"

#include "nuitka/compiled_frame.hpp"

#endif
