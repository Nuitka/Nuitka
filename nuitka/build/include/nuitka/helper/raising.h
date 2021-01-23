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
#ifndef __NUITKA_HELPER_RAISING_H__
#define __NUITKA_HELPER_RAISING_H__

#if PYTHON_VERSION >= 0x300
NUITKA_MAY_BE_UNUSED static void CHAIN_EXCEPTION(PyObject *exception_value) {
    // Implicit chain of exception already existing.
    PyThreadState *thread_state = PyThreadState_GET();

    // Normalize existing exception first.
    NORMALIZE_EXCEPTION(&EXC_TYPE(thread_state), &EXC_VALUE(thread_state),
                        (PyTracebackObject **)&EXC_TRACEBACK(thread_state));

    PyObject *old_exc_value = EXC_VALUE(thread_state);

    if (old_exc_value != NULL && old_exc_value != Py_None && old_exc_value != exception_value) {
        PyObject *current = old_exc_value;
        while (true) {
            PyObject *context = PyException_GetContext(current);
            if (!context)
                break;

            CHECK_OBJECT(context);
            Py_DECREF(context);
            CHECK_OBJECT(context);

            if (context == exception_value) {
                PyException_SetContext(current, NULL);
                break;
            }

            current = context;
        }

        CHECK_OBJECT(old_exc_value);
        Py_INCREF(old_exc_value);
        PyException_SetContext(exception_value, old_exc_value);

        CHECK_OBJECT(EXC_TRACEBACK(thread_state));
        ATTACH_TRACEBACK_TO_EXCEPTION_VALUE(old_exc_value, (PyTracebackObject *)EXC_TRACEBACK(thread_state));
    }
}
#endif

extern void RAISE_EXCEPTION_WITH_TYPE(PyObject **exception_type, PyObject **exception_value,
                                      PyTracebackObject **exception_tb);

#if PYTHON_VERSION >= 0x300
extern void RAISE_EXCEPTION_WITH_CAUSE(PyObject **exception_type, PyObject **exception_value,
                                       PyTracebackObject **exception_tb, PyObject *exception_cause);
#endif

extern void RAISE_EXCEPTION_WITH_VALUE(PyObject **exception_type, PyObject **exception_value,
                                       PyTracebackObject **exception_tb);

extern void RAISE_EXCEPTION_IMPLICIT(PyObject **exception_type, PyObject **exception_value,
                                     PyTracebackObject **exception_tb);

extern void RAISE_EXCEPTION_WITH_TRACEBACK(PyObject **exception_type, PyObject **exception_value,
                                           PyTracebackObject **exception_tb);

extern bool RERAISE_EXCEPTION(PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb);

#endif
