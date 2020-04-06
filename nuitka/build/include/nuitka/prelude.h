//     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

/* Include the CPython version numbers, and define our own take of what version
 * numbers should be.
 */
#include <patchlevel.h>

// TODO: Switch to using hex format version of standard Python or change our
// to use that too, to avoid overflows more generally. For now we to out at
// e.g. 369 for 3.6.10 or higher, but behavior changes are really rare at that
// point.
#if PY_MICRO_VERSION < 10
#define PYTHON_VERSION (PY_MAJOR_VERSION * 100 + PY_MINOR_VERSION * 10 + PY_MICRO_VERSION)
#else
#define PYTHON_VERSION (PY_MAJOR_VERSION * 100 + PY_MINOR_VERSION * 10 + 9)
#endif

/* This is needed or else we can't create modules name "proc" or "func". For
 * Python3, the name collision can't happen, so we can limit it to Python2.
 */
#if PYTHON_VERSION < 300
#define initproc python_initproc
#define initfunc python_initfunc
#define initstate system_initstate
#endif

/* Include the relevant Python C-API header files. */
#include "Python.h"
#include "frameobject.h"
#include "marshal.h"
#include "methodobject.h"
#include "pydebug.h"

/* See above. */
#if PYTHON_VERSION < 300
#undef initproc
#undef initfunc
#undef initstate
#endif

/* Type bool */
#ifndef __cplusplus
#include "stdbool.h"
#endif

/* Include the C header files most often used. */
#include <stdio.h>

/* Using "_alloca" extension due to MSVC restrictions for array variables
 * on the local stack.
 */
#ifdef _MSC_VER
#include <malloc.h>
#endif

/* An idea I first saw used with Cython, hint the compiler about branches
 * that are more or less likely to be taken. And hint the compiler about
 * things that we assume to be normally true. If other compilers can do
 * similar, I would be grateful for instructions.
 */

#ifdef __GNUC__
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

/* A way to not give warnings about things that are declared, but might not
 * be used like in-line helper functions in headers or static per module
 * variables from headers.
 */
#ifdef __GNUC__
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

/* A way to indicate that a specific function won't return, so the C compiler
 * can create better code.
 */
#ifdef __GNUC__
#define NUITKA_NO_RETURN __attribute__((__noreturn__))
#elif defined(_MSC_VER)
#define NUITKA_NO_RETURN __declspec(noreturn)
#else
#define NUITKA_NO_RETURN
#endif

/* This is used to indicate code control flows we know cannot happen. */
#define NUITKA_CANNOT_GET_HERE(NAME)                                                                                   \
    assert(false && #NAME);                                                                                            \
    abort();

#ifdef __GNUC__
#define NUITKA_FORCE_INLINE __attribute__((always_inline))
#else
#define NUITKA_FORCE_INLINE
#endif

/* Python3 removed PyInt instead of renaming PyLong, and PyObject_Str instead
 * of renaming PyObject_Unicode. Define this to be easily portable.
 */
#if PYTHON_VERSION >= 300
#define PyInt_FromLong PyLong_FromLong
#define PyInt_AsLong PyLong_AsLong
#define PyInt_FromSsize_t PyLong_FromSsize_t

#define PyNumber_Int PyNumber_Long

#define PyObject_Unicode PyObject_Str

#endif

/* String handling that uses the proper version of strings for Python3 or not,
 * which makes it easier to write portable code.
 */
#if PYTHON_VERSION < 300
#define Nuitka_String_AsString PyString_AsString
#define Nuitka_String_AsString_Unchecked PyString_AS_STRING
#define Nuitka_String_Check PyString_Check
#define Nuitka_String_CheckExact PyString_CheckExact
#define Nuitka_StringObject PyStringObject
#define Nuitka_StringIntern PyString_InternInPlace
#define Nuitka_String_FromString PyString_FromString
#define Nuitka_String_FromStringAndSize PyString_FromStringAndSize
#else
#define Nuitka_String_AsString _PyUnicode_AsString

/* Note: This is from unicodeobject.c */
#define _PyUnicode_UTF8(op) (((PyCompactUnicodeObject *)(op))->utf8)
#define PyUnicode_UTF8(op)                                                                                             \
    (assert(PyUnicode_IS_READY(op)),                                                                                   \
     PyUnicode_IS_COMPACT_ASCII(op) ? ((char *)((PyASCIIObject *)(op) + 1)) : _PyUnicode_UTF8(op))
#define Nuitka_String_AsString_Unchecked PyUnicode_UTF8

#define Nuitka_String_Check PyUnicode_Check
#define Nuitka_String_CheckExact PyUnicode_CheckExact
#define Nuitka_StringObject PyUnicodeObject
#define Nuitka_StringIntern PyUnicode_InternInPlace
#define Nuitka_String_FromString PyUnicode_FromString
#define Nuitka_String_FromStringAndSize PyUnicode_FromStringAndSize
#endif

#if PYTHON_VERSION < 300
#define PyUnicode_GET_LENGTH(x) (PyUnicode_GET_SIZE(x))
#endif

/* With the idea to reduce the amount of exported symbols in the DLLs, make it
 * clear that the module "init" function should of course be exported, but not
 * for executable, where we call it ourselves from the main code.
 */

#if PYTHON_VERSION < 300
#define NUITKA_MODULE_ENTRY_FUNCTION void
#else
#define NUITKA_MODULE_ENTRY_FUNCTION PyObject *
#endif

/* Avoid gcc warnings about using an integer as a bool. This is a cherry-pick.
 *
 * This might apply to more versions. I am seeing this on 3.3.2, and it was
 * fixed for Python 2.x only later. We could include more versions. This is
 * only a problem with debug mode and therefore not too important maybe.
 */
#if PYTHON_VERSION >= 300 && PYTHON_VERSION < 340

#undef PyMem_MALLOC
#define PyMem_MALLOC(n) ((size_t)(n) > (size_t)PY_SSIZE_T_MAX ? NULL : malloc(((n) != 0) ? (n) : 1))

#undef PyMem_REALLOC
#define PyMem_REALLOC(p, n) ((size_t)(n) > (size_t)PY_SSIZE_T_MAX ? NULL : realloc((p), ((n) != 0) ? (n) : 1))

#endif

#if PYTHON_VERSION < 300
typedef long Py_hash_t;
#endif

/* These two express if a directly called function should be exported (C level)
 * or if it can be local to the file.
 */
#define NUITKA_CROSS_MODULE
#define NUITKA_LOCAL_MODULE static

/* Due to ABI issues, it seems that on Windows the symbols used by
 * "_PyObject_GC_TRACK" are not exported and we need to use a function that does
 * it instead.
 *
 * TODO: Make it work for 3.7 too.
 */
#if defined(_WIN32) || defined(__MSYS__) || PYTHON_VERSION >= 370
#define Nuitka_GC_Track PyObject_GC_Track
#define Nuitka_GC_UnTrack PyObject_GC_UnTrack
#else
#define Nuitka_GC_Track _PyObject_GC_TRACK
#define Nuitka_GC_UnTrack _PyObject_GC_UNTRACK
#endif

#if _NUITKA_EXPERIMENTAL_FAST_THREAD_GET && PYTHON_VERSION >= 300
// We are careful, access without locking under the assumption that we hold
// the GIL over uses of this or the same thread continues to execute code of
// ours.
#undef PyThreadState_GET
extern PyThreadState *_PyThreadState_Current;
#define PyThreadState_GET() (_PyThreadState_Current)
#endif

#include "nuitka/helpers.h"

#include "nuitka/compiled_frame.h"

#include "nuitka/compiled_cell.h"

#include "nuitka/compiled_function.h"

/* Sentinel PyObject to be used for all our call iterator endings. */
extern PyObject *_sentinel_value;

/* Value to use for __compiled__ value of all modules. */
extern PyObject *Nuitka_dunder_compiled_value;

#include "nuitka/compiled_generator.h"

#include "nuitka/compiled_method.h"

#if PYTHON_VERSION >= 350
#include "nuitka/compiled_coroutine.h"
#endif

#if PYTHON_VERSION >= 360
#include "nuitka/compiled_asyncgen.h"
#endif

/* Safe to use function to copy a string, will abort program for overflow. */
extern void copyStringSafe(char *buffer, char const *source, size_t buffer_size);
extern void copyStringSafeN(char *buffer, char const *source, size_t n, size_t buffer_size);
/* Safe to use function to append a string, will abort program for overflow. */
extern void appendStringSafe(char *buffer, char const *source, size_t buffer_size);

#endif
