//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_COMPILED_TYPES_COMMON_H__
#define __NUITKA_COMPILED_TYPES_COMMON_H__

/* Shared helpers used across the compiled generator/coroutine/asyncgen/frame
 * implementation files. Those are all chained into one compilation unit, and
 * therefore the helpers are "static" to it.
 *
 * This file is included from that compilation unit, and from the individual
 * files on their own, to help IDEs to parse them.
 */
#ifdef __IDE_ONLY__
#include "nuitka/compiled_frame.h"
#include "nuitka/cpython_api_compat.h"

#include "internal/pycore_gc.h"
#include "nuitka/defines.h"
#include "nuitka/exceptions.h"
#endif

struct Nuitka_GeneratorObject;
struct Nuitka_CoroutineObject;
struct Nuitka_AsyncgenObject;
struct Nuitka_AsyncgenAsendObject;

// Need to integrate with garbage collector to undo finalization.
#if PYTHON_VERSION >= 0x300

#if PYTHON_VERSION < 0x380
#define _PyGC_CLEAR_FINALIZED(o) _PyGC_SET_FINALIZED(o, 0)
#elif PYTHON_VERSION < 0x3d0
#define _PyGCHead_SET_UNFINALIZED(g) ((g)->_gc_prev &= (~_PyGC_PREV_MASK_FINALIZED))
#define _PyGC_CLEAR_FINALIZED(o) _PyGCHead_SET_UNFINALIZED(_Py_AS_GC(o))
#endif
#endif

#if !defined(_PyGC_FINALIZED) && PYTHON_VERSION < 0x3d0
#define _PyGC_FINALIZED(o) _PyGCHead_FINALIZED(_Py_AS_GC(o))
#endif
#if !defined(_PyType_IS_GC) && PYTHON_VERSION < 0x3d0
#define _PyType_IS_GC(t) PyType_HasFeature((t), Py_TPFLAGS_HAVE_GC)
#endif

#if PYTHON_VERSION >= 0x300
static PyBaseExceptionObject *Nuitka_BaseExceptionSingleArg_new(PyThreadState *tstate, PyTypeObject *type,
                                                                PyObject *arg);
static bool Nuitka_CallFinalizerFromDealloc(PyObject *self);
static PyObject *Nuitka_CreateStopIteration(PyThreadState *tstate, PyObject *value);
static void Nuitka_SetStopIterationValue(PyThreadState *tstate, PyObject *value);
static bool Nuitka_PyGen_FetchStopIterationValue(PyThreadState *tstate, PyObject **pvalue);
static PyObject *Nuitka_PyGen_Send(PyThreadState *tstate, PyGenObject *gen, PyObject *arg);
static PyObject *Nuitka_CallGeneratorThrowMethod(PyObject *throw_method,
                                                 struct Nuitka_ExceptionPreservationItem *exception_state);
static PyObject *ERROR_GET_STOP_ITERATION_VALUE(PyThreadState *tstate);
static PyObject *_Nuitka_YieldFromPassExceptionTo(PyThreadState *tstate, PyObject *value,
                                                  struct Nuitka_ExceptionPreservationItem *exception_state);
static bool Nuitka_gen_close_iter(PyThreadState *tstate, PyObject *yield_from);
static PyObject *_Nuitka_Generator_throw2(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                          struct Nuitka_ExceptionPreservationItem *exception_state);
#endif

static void SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(PyThreadState *tstate);
static void _Nuitka_GeneratorPopFrame(PyThreadState *tstate, Nuitka_ThreadStateFrameType *return_frame);
static bool DROP_ERROR_OCCURRED_GENERATOR_EXIT_OR_STOP_ITERATION(PyThreadState *tstate);
static bool _Nuitka_Generator_make_throw_exception_state(PyThreadState *tstate,
                                                         struct Nuitka_ExceptionPreservationItem *exception_state,
                                                         PyObject *exception_type, PyObject *exception_value,
                                                         PyTracebackObject *exception_tb);
static bool _Nuitka_Generator_close(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator);

#if PYTHON_VERSION >= 0x350
static void RAISE_RUNTIME_ERROR_RAISED_STOP_ITERATION(PyThreadState *tstate, char const *message);
static PyObject *_Nuitka_YieldFromCore(PyThreadState *tstate, PyObject *yield_from, PyObject *send_value,
                                       PyObject **returned_value, bool mode);
static PyObject *_Nuitka_Coroutine_throw2(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine, bool closing,
                                          struct Nuitka_ExceptionPreservationItem *exception_state);
static bool _Nuitka_Coroutine_close(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine);
static void _initCompiledCoroutineTypes(void);
#endif

#if PYTHON_VERSION >= 0x360
static void SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(PyThreadState *tstate);
static bool _Nuitka_Asyncgen_close(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen);
static PyObject *_Nuitka_AsyncgenAsend_throw2(PyThreadState *tstate, struct Nuitka_AsyncgenAsendObject *asyncgen_asend,
                                              struct Nuitka_ExceptionPreservationItem *exception_state);
static bool Nuitka_AsyncgenAsend_Check(PyObject *object);
static void _initCompiledAsyncgenTypes(void);
#endif

#if PYTHON_VERSION >= 0x3c0
static PyObject *Nuitka_CreateStopAsyncIteration(PyThreadState *tstate);
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
