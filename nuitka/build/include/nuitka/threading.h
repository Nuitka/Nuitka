//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_THREADING_H__
#define __NUITKA_THREADING_H__

#if PYTHON_VERSION < 0x300
// We share this with CPython bytecode main loop.
PyAPI_DATA(volatile int) _Py_Ticker;
#else
extern volatile int _Py_Ticker;
#define _Py_CheckInterval 20
#endif

#ifdef NUITKA_USE_PYCORE_THREAD_STATE

#if PYTHON_VERSION < 0x380

// Signals pending got their own indicator only in 3.8, covered by calls to do before.
#define HAS_WORK_TO_DO(ceval, ceval2) (ceval2->pending.calls_to_do._value)
#elif PYTHON_VERSION < 0x3d0
#define HAS_WORK_TO_DO(ceval, ceval2) (ceval->signals_pending._value || ceval2->pending.calls_to_do._value)
#else
#define HAS_WORK_TO_DO(ceval, ceval2) _Py_eval_breaker_bit_is_set(tstate, _PY_SIGNALS_PENDING_BIT | _PY_CALLS_TO_DO_BIT)
#endif

#ifndef Py_GIL_DISABLED
NUITKA_MAY_BE_UNUSED static inline bool CONSIDER_THREADING(PyThreadState *tstate) {
#if PYTHON_VERSION < 0x390
    _PyRuntimeState *const runtime = &_PyRuntime;
#elif PYTHON_VERSION < 0x3d0
    _PyRuntimeState *const runtime = tstate->interp->runtime;
#endif

#if PYTHON_VERSION < 0x3d0
    // This was split in 2 parts in 3.9 or higher.
    struct _ceval_runtime_state *ceval = &runtime->ceval;
#if PYTHON_VERSION >= 0x390
    struct _ceval_state *ceval2 = &tstate->interp->ceval;
#else
    struct _ceval_runtime_state *ceval2 = ceval;
#endif
#endif
    // Pending signals or calls to do
    if (HAS_WORK_TO_DO(ceval, ceval2)) {
        int res = Py_MakePendingCalls();

        if (unlikely(res < 0 && HAS_ERROR_OCCURRED(tstate))) {
            return false;
        }
    }

#if PYTHON_VERSION >= 0x3d0
    /* GIL drop request */
    if (_Py_eval_breaker_bit_is_set(tstate, _PY_GIL_DROP_REQUEST_BIT)) {
#else
    /* GIL drop request */
    if (ceval2->gil_drop_request._value) {
#endif
        /* Give another thread a chance */
        PyEval_SaveThread();
        PyEval_AcquireThread(tstate);
    }

    if (unlikely(tstate->async_exc != NULL)) {
        PyObject *async_exc = tstate->async_exc;
        tstate->async_exc = NULL;

        SET_CURRENT_EXCEPTION_TYPE0(tstate, async_exc);

        return false;
    }

    return true;
}
#else
NUITKA_MAY_BE_UNUSED static inline bool CONSIDER_THREADING(PyThreadState *tstate) {
    if (unlikely(tstate->async_exc != NULL)) {
        PyObject *async_exc = tstate->async_exc;
        tstate->async_exc = NULL;

        SET_CURRENT_EXCEPTION_TYPE0(tstate, async_exc);

        return false;
    }

    return true;
}

#endif

#else

NUITKA_MAY_BE_UNUSED static inline bool CONSIDER_THREADING(PyThreadState *tstate) {
    // Decrease ticker
    if (--_Py_Ticker < 0) {
        _Py_Ticker = _Py_CheckInterval;

        int res = Py_MakePendingCalls();

        if (unlikely(res < 0 && HAS_ERROR_OCCURRED(tstate))) {
            return false;
        }

        if (PyEval_ThreadsInitialized()) {
            // Release and acquire the GIL, it's very inefficient, because we
            // don't even know if it makes sense to do it. A controlling thread
            // should be used to determine if it's needed at all.
            PyEval_SaveThread();
            PyEval_AcquireThread(tstate);
        }

        if (unlikely(tstate->async_exc != NULL)) {
            PyObject *async_exc = tstate->async_exc;
            tstate->async_exc = NULL;

            SET_CURRENT_EXCEPTION_TYPE0(tstate, async_exc);

            return false;
        }
    }

    return true;
}

#endif

#endif

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
