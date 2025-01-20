//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_RAISING_H__
#define __NUITKA_HELPER_RAISING_H__

#if PYTHON_VERSION >= 0x300
NUITKA_MAY_BE_UNUSED static void CHAIN_EXCEPTION(PyThreadState *tstate, PyObject *exception_value) {
    // Implicit chain of exception already existing.

    // Normalize existing published exception first.
#if PYTHON_VERSION < 0x3b0
    {
        // TODO: Revert to using NORMALIZE_EXCEPTION
        struct Nuitka_ExceptionPreservationItem *exception_state =
            (struct Nuitka_ExceptionPreservationItem *)&EXC_TYPE(tstate);
        NORMALIZE_EXCEPTION_STATE(tstate, exception_state);
    }
#endif

    PyObject *old_exc_value = EXC_VALUE(tstate);

    if (old_exc_value != NULL && old_exc_value != Py_None && old_exc_value != exception_value) {
        PyObject *current = old_exc_value;
        while (true) {
            PyObject *context = Nuitka_Exception_GetContext(current);
            if (context == NULL) {
                break;
            }

            CHECK_OBJECT(context);

            if (context == exception_value) {
                Nuitka_Exception_DeleteContext(current);
                break;
            }

            current = context;
        }

        CHECK_OBJECT(old_exc_value);
        Nuitka_Exception_SetContext(exception_value, old_exc_value);

#if PYTHON_VERSION < 0x3b0
        CHECK_OBJECT(EXC_TRACEBACK(tstate));
        ATTACH_TRACEBACK_TO_EXCEPTION_VALUE(old_exc_value, (PyTracebackObject *)EXC_TRACEBACK(tstate));
#endif
    }
}
#endif

#if PYTHON_VERSION < 0x3c0
extern void RAISE_EXCEPTION_WITH_TYPE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state);
extern void RAISE_EXCEPTION_WITH_TYPE_AND_VALUE(PyThreadState *tstate,
                                                struct Nuitka_ExceptionPreservationItem *exception_state);
#else
extern void RAISE_EXCEPTION_WITH_VALUE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state);
#endif

#if PYTHON_VERSION < 0x300
extern void RAISE_EXCEPTION_WITH_TRACEBACK(PyThreadState *tstate,
                                           struct Nuitka_ExceptionPreservationItem *exception_state);
#else
extern void RAISE_EXCEPTION_WITH_CAUSE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                       PyObject *exception_cause);
#endif

extern bool RERAISE_EXCEPTION(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state);

extern void RAISE_CURRENT_EXCEPTION_NAME_ERROR(PyThreadState *tstate,
                                               struct Nuitka_ExceptionPreservationItem *exception_state,
                                               PyObject *variable_name);

#if PYTHON_VERSION < 0x300
extern void RAISE_CURRENT_EXCEPTION_GLOBAL_NAME_ERROR(PyThreadState *tstate,
                                                      struct Nuitka_ExceptionPreservationItem *exception_state,
                                                      PyObject *variable_name);
#endif

extern PyObject *NORMALIZE_EXCEPTION_VALUE_FOR_RAISE(PyThreadState *tstate, PyObject *exception_type);

#if PYTHON_VERSION >= 0x300
extern PyObject *MAKE_STOP_ITERATION_EMPTY(void);
extern PyObject *MAKE_BASE_EXCEPTION_DERIVED_EMPTY(PyObject *exception_type);
#endif

NUITKA_MAY_BE_UNUSED static inline void
SET_EXCEPTION_PRESERVATION_STATE_STOP_ITERATION_EMPTY(PyThreadState *tstate,
                                                      struct Nuitka_ExceptionPreservationItem *exception_state) {
#if PYTHON_VERSION < 0x3c0
    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0(tstate, exception_state, PyExc_StopIteration);
#else
    exception_state->exception_value = MAKE_STOP_ITERATION_EMPTY();
#endif
}

// Create an exception value object from type and value input.
extern PyObject *MAKE_EXCEPTION_WITH_VALUE(PyThreadState *tstate, PyObject *exception_type, PyObject *value);

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
