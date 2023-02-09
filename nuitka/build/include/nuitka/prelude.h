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
#ifndef __NUITKA_PRELUDE_H__
#define __NUITKA_PRELUDE_H__

#ifdef __NUITKA_NO_ASSERT__
#undef NDEBUG
#define NDEBUG
#endif

#if defined(_WIN32)
// Note: Keep this separate line, must be included before other Windows headers.
#include <windows.h>
#endif

/* Include the CPython version numbers, and define our own take of what version
 * numbers should be.
 */
#include "patchlevel.h"

/* Use a hex version of our own to compare for versions. We do not care about pre-releases */
#if PY_MICRO_VERSION < 16
#define PYTHON_VERSION (PY_MAJOR_VERSION * 256 + PY_MINOR_VERSION * 16 + PY_MICRO_VERSION)
#else
#define PYTHON_VERSION (PY_MAJOR_VERSION * 256 + PY_MINOR_VERSION * 16 + 15)
#endif

/* This is needed or else we can't create modules name "proc" or "func". For
 * Python3, the name collision can't happen, so we can limit it to Python2.
 */
#define initproc python_initproc
#define initfunc python_initfunc
#define initstate python_initstate

/* Include the relevant Python C-API header files. */
#include "Python.h"
#include "frameobject.h"
#include "marshal.h"
#include "methodobject.h"
#include "osdefs.h"
#include "structseq.h"

#if PYTHON_VERSION < 0x3a0
#include "pydebug.h"
#endif

// We are not following the 3.10 change to an inline function. At least
// not immediately.
#if PYTHON_VERSION >= 0x3a0
#undef Py_REFCNT
#define Py_REFCNT(ob) (_PyObject_CAST(ob)->ob_refcnt)
#endif

// We are using this new macro on old code too.
#ifndef Py_SET_REFCNT
#define Py_SET_REFCNT(ob, refcnt) Py_REFCNT(ob) = refcnt
#endif

#if defined(_WIN32)
// Windows is too difficult for API redefines.
#define MIN_PYCORE_PYTHON_VERSION 0x380
#else
#define MIN_PYCORE_PYTHON_VERSION 0x371
#endif

#if PYTHON_VERSION >= MIN_PYCORE_PYTHON_VERSION
#define NUITKA_USE_PYCORE_THREADSTATE
#endif

#ifdef NUITKA_USE_PYCORE_THREADSTATE
#undef Py_BUILD_CORE
#define Py_BUILD_CORE
#undef _PyGC_FINALIZED

#if PYTHON_VERSION < 0x380
#undef Py_ATOMIC_H
#include "pyatomic.h"
#undef Py_INTERNAL_PYSTATE_H
#include "internal/pystate.h"
#undef Py_STATE_H
#include "pystate.h"

extern _PyRuntimeState _PyRuntime;
#else
#include "internal/pycore_pystate.h"
#endif

#if PYTHON_VERSION >= 0x390
#include <internal/pycore_ceval.h>
#include <internal/pycore_interp.h>
#include <internal/pycore_runtime.h>
#endif

#if PYTHON_VERSION >= 0x380
#include <internal/pycore_pyerrors.h>
#endif

#if PYTHON_VERSION >= 0x3a0
#include <internal/pycore_long.h>
#include <internal/pycore_unionobject.h>
#endif

#if PYTHON_VERSION >= 0x3b0
#include <internal/pycore_frame.h>
#endif

// TODO: Might be useful too, allows access to Python configuration.
// #include <internal/pycore_initconfig.h>

#ifndef PY_NOGIL
#undef PyThreadState_GET
#define _PyThreadState_Current _PyRuntime.gilstate.tstate_current
#define PyThreadState_GET() ((PyThreadState *)_Py_atomic_load_relaxed(&_PyThreadState_Current))
#endif

#if PYTHON_VERSION >= 0x380
#undef _PyObject_LookupSpecial
#include <internal/pycore_object.h>
#else
#include <objimpl.h>
#endif

#undef Py_BUILD_CORE

#endif

/* See above. */
#if PYTHON_VERSION < 0x300
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

#include "hedley.h"

/* Use annotations for branch prediction. They still make sense as the L1
 * cache space is saved.
 */

#define likely(x) HEDLEY_LIKELY(x)
#define unlikely(x) HEDLEY_UNLIKELY(x)

/* A way to indicate that a specific function won't return, so the C compiler
 * can create better code.
 */

#define NUITKA_NO_RETURN HEDLEY_NO_RETURN

/* A way to not give warnings about things that are declared, but might not
 * be used like in-line helper functions in headers or static per module
 * variables from headers.
 */
#ifdef __GNUC__
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

/* This is used to indicate code control flows we know cannot happen. */
#ifndef __NUITKA_NO_ASSERT__
#define NUITKA_CANNOT_GET_HERE(NAME)                                                                                   \
    PRINT_FORMAT("%s : %s\n", __FUNCTION__, #NAME);                                                                    \
    assert(false);                                                                                                     \
    abort();
#else
#define NUITKA_CANNOT_GET_HERE(NAME) abort();
#endif

#ifdef _MSC_VER
/* Using "_alloca" extension due to MSVC restrictions for array variables
 * on the local stack.
 */
#include <malloc.h>
#define NUITKA_DYNAMIC_ARRAY_DECL(VARIABLE_NAME, ELEMENT_TYPE, COUNT)                                                  \
    ELEMENT_TYPE *VARIABLE_NAME = (ELEMENT_TYPE *)_alloca(sizeof(ELEMENT_TYPE) * (COUNT));
#else
#define NUITKA_DYNAMIC_ARRAY_DECL(VARIABLE_NAME, ELEMENT_TYPE, COUNT) ELEMENT_TYPE VARIABLE_NAME[COUNT];
#endif

// Stringizing, to make strings out of defines use XSTRINGIZED(SOME_DEFINE) needs
// to level of defines to work.
#define _STRINGIZED(ARG) #ARG
#define STRINGIZED(ARG) _STRINGIZED(ARG)

/* Python3 removed PyInt instead of renaming PyLong, and PyObject_Str instead
 * of renaming PyObject_Unicode. Define this to be easily portable.
 */
#if PYTHON_VERSION >= 0x300
#define PyInt_FromLong PyLong_FromLong
#define PyInt_AsLong PyLong_AsLong
#define PyInt_FromSsize_t PyLong_FromSsize_t

#define PyNumber_Int PyNumber_Long

#define PyObject_Unicode PyObject_Str

#endif

/* String handling that uses the proper version of strings for Python3 or not,
 * which makes it easier to write portable code.
 */
#if PYTHON_VERSION < 0x300
#define Nuitka_String_AsString PyString_AsString
#define Nuitka_String_AsString_Unchecked PyString_AS_STRING
#define Nuitka_String_Check PyString_Check
#define Nuitka_String_CheckExact PyString_CheckExact
#define Nuitka_StringObject PyStringObject
#define Nuitka_String_FromString PyString_FromString
#define Nuitka_String_FromStringAndSize PyString_FromStringAndSize
#define Nuitka_String_FromFormat PyString_FromFormat
#define PyUnicode_CHECK_INTERNED (0)
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
#define Nuitka_String_FromString PyUnicode_FromString
#define Nuitka_String_FromStringAndSize PyUnicode_FromStringAndSize
#define Nuitka_String_FromFormat PyUnicode_FromFormat
#endif

#if PYTHON_VERSION < 0x300
#define PyUnicode_GET_LENGTH(x) (PyUnicode_GET_SIZE(x))
#endif

// Wrap the type lookup for debug mode, to identify errors, and potentially
// to make our own enhancement later on. For now only verify it is not being
// called with an error set, which 3.9 asserts against in core code.
#ifdef __NUITKA_NO_ASSERT__
#define Nuitka_TypeLookup(x, y) _PyType_Lookup(x, y)
#else
NUITKA_MAY_BE_UNUSED static inline bool ERROR_OCCURRED(void);
NUITKA_MAY_BE_UNUSED static PyObject *Nuitka_TypeLookup(PyTypeObject *type, PyObject *name) {
    return _PyType_Lookup(type, name);
}

#endif

/* With the idea to reduce the amount of exported symbols in the DLLs, make it
 * clear that the module "init" function should of course be exported, but not
 * for executable, where we call it ourselves from the main code.
 */

#if PYTHON_VERSION < 0x300
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
#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x340

#undef PyMem_MALLOC
#define PyMem_MALLOC(n) ((size_t)(n) > (size_t)PY_SSIZE_T_MAX ? NULL : malloc(((n) != 0) ? (n) : 1))

#undef PyMem_REALLOC
#define PyMem_REALLOC(p, n) ((size_t)(n) > (size_t)PY_SSIZE_T_MAX ? NULL : realloc((p), ((n) != 0) ? (n) : 1))

#endif

#if PYTHON_VERSION < 0x300
typedef long Py_hash_t;
#endif

/* These two express if a directly called function should be exported (C level)
 * or if it can be local to the file.
 */
#define NUITKA_CROSS_MODULE
#define NUITKA_LOCAL_MODULE static

/* Due to ABI issues, it seems that on Windows the symbols used by
 * "_PyObject_GC_TRACK" were not exported before 3.8 and we need to use a
 * function that does it instead.
 *
 * TODO: Make it work for Win32 Python <= 3.7 too.
 * TODO: The Python 3.7.0 on Linux doesn't work this way either, was a bad
 * CPython release apparently.
 */
#if (defined(_WIN32) || defined(__MSYS__)) && PYTHON_VERSION < 0x380
#define Nuitka_GC_Track PyObject_GC_Track
#define Nuitka_GC_UnTrack PyObject_GC_UnTrack
#elif PYTHON_VERSION == 0x370
#define Nuitka_GC_Track PyObject_GC_Track
#define Nuitka_GC_UnTrack PyObject_GC_UnTrack
#else
#define Nuitka_GC_Track _PyObject_GC_TRACK
#define Nuitka_GC_UnTrack _PyObject_GC_UNTRACK
#endif

#if _NUITKA_EXPERIMENTAL_FAST_THREAD_GET && PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x370
// We are careful, access without locking under the assumption that we hold
// the GIL over uses of this or the same thread continues to execute code of
// ours.
#undef PyThreadState_GET
extern PyThreadState *_PyThreadState_Current;
#define PyThreadState_GET() (_PyThreadState_Current)
#endif

#ifndef _NUITKA_FULL_COMPAT
// Remove useless recursion control guards, we have no need for them or we
// are achieving deeper recursion anyway.
#undef Py_EnterRecursiveCall
#define Py_EnterRecursiveCall(arg) (0)
#undef Py_LeaveRecursiveCall
#define Py_LeaveRecursiveCall()
#endif

#if PYTHON_VERSION < 0x300
#define RICHCOMPARE(t) (PyType_HasFeature((t), Py_TPFLAGS_HAVE_RICHCOMPARE) ? (t)->tp_richcompare : NULL)
#else
#define RICHCOMPARE(t) ((t)->tp_richcompare)
#endif

// For older Python we need to define this ourselves.
#ifndef Py_ABS
#define Py_ABS(x) ((x) < 0 ? -(x) : (x))
#endif

#ifndef Py_MIN
#define Py_MIN(x, y) (((x) > (y)) ? (y) : (x))
#endif

#ifndef Py_MAX
#define Py_MAX(x, y) (((x) > (y)) ? (x) : (y))
#endif

#ifndef Py_SET_SIZE
#define Py_SET_SIZE(op, size) ((PyVarObject *)(op))->ob_size = size
#endif

#ifndef PyFloat_SET_DOUBLE
#define PyFloat_SET_DOUBLE(op, value) ((PyFloatObject *)(op))->ob_fval = value
#endif

// For older Python, we don't have a feature "CLASS" anymore, that's implied now.
#if PYTHON_VERSION < 0x300
#define NuitkaType_HasFeatureClass(descr) (PyType_HasFeature(Py_TYPE(descr), Py_TPFLAGS_HAVE_CLASS))
#else
#define NuitkaType_HasFeatureClass(descr) (1)
#endif

// Our replacement for "PyType_IsSubtype"
extern bool Nuitka_Type_IsSubtype(PyTypeObject *a, PyTypeObject *b);

#include "nuitka/allocator.h"
#include "nuitka/exceptions.h"

// The digit types
#if PYTHON_VERSION < 0x300
#include <longintrepr.h>

#if PYTHON_VERSION < 0x270
// Not present in Python2.6 yet
typedef signed int sdigit;
#endif
#endif

// A long value that represents a signed digit on the helper interface.
typedef long nuitka_digit;

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

#if PYTHON_VERSION >= 0x350
#include "nuitka/compiled_coroutine.h"
#endif

#if PYTHON_VERSION >= 0x360
#include "nuitka/compiled_asyncgen.h"
#endif

#include "nuitka/filesystem_paths.h"
#include "nuitka/safe_string_ops.h"

#if _NUITKA_EXPERIMENTAL_WRITEABLE_CONSTANTS
#include "nuitka_data_decoder.h"
#else
#define DECODE(x) assert(x)
#define UNTRANSLATE(x) (x)
#endif

#if _NUITKA_EXPERIMENTAL_FILE_TRACING
#include "nuitka_file_tracer.h"
#else
#if PYTHON_VERSION < 0x300
#define TRACE_FILE_OPEN(x, y, z, r) (false)
#else
#define TRACE_FILE_OPEN(x, y, z, a, b, c, d, e, r) (false)
#endif
#define TRACE_FILE_READ(x, y) (false)

#define TRACE_FILE_EXISTS(x, y) (false)
#define TRACE_FILE_ISFILE(x, y) (false)
#define TRACE_FILE_ISDIR(x, y) (false)

#define TRACE_FILE_LISTDIR(x, y) (false)

#endif

#if _NUITKA_EXPERIMENTAL_INIT_PROGRAM
#include "nuitka_init_program.h"
#else
#define NUITKA_INIT_PROGRAM_EARLY(argc, argv)
#define NUITKA_INIT_PROGRAM_LATE(module_name)
#endif

// Only Python3.9+ has a more precise check, while making the old one slow.
#ifndef PyCFunction_CheckExact
#define PyCFunction_CheckExact PyCFunction_Check
#endif

#endif
