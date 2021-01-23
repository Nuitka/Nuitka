//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_THREADING_H__
#define __NUITKA_THREADING_H__

#if PYTHON_VERSION < 0x300
// We share this with CPython bytecode main loop.
PyAPI_DATA(volatile int) _Py_Ticker;
#else
extern volatile int _Py_Ticker;
#define _Py_CheckInterval 20
#endif

NUITKA_MAY_BE_UNUSED static inline bool CONSIDER_THREADING(void) {
    // Decrease ticker
    if (--_Py_Ticker < 0) {
        _Py_Ticker = _Py_CheckInterval;

        int res = Py_MakePendingCalls();

        if (unlikely(res < 0 && ERROR_OCCURRED())) {
            return false;
        }

        PyThreadState *tstate = PyThreadState_GET();
        assert(tstate);

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

            Py_INCREF(async_exc);

            RESTORE_ERROR_OCCURRED(async_exc, NULL, NULL);

            return false;
        }
    }

    return true;
}

#endif
