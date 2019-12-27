//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_EXCEPTIONS_H__
#define __NUITKA_EXCEPTIONS_H__

// Exception helpers for generated code and compiled code helpers.

// Did an error occur.
NUITKA_MAY_BE_UNUSED static inline bool ERROR_OCCURRED(void) {
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type != NULL;
}

// Get the error type occurred.
NUITKA_MAY_BE_UNUSED static inline PyObject *GET_ERROR_OCCURRED(void) {
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type;
}

// Clear error, which likely set.
NUITKA_MAY_BE_UNUSED static inline void CLEAR_ERROR_OCCURRED(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *old_type = tstate->curexc_type;
    PyObject *old_value = tstate->curexc_value;
    PyObject *old_tb = tstate->curexc_traceback;

    tstate->curexc_type = NULL;
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;

    Py_XDECREF(old_type);
    Py_XDECREF(old_value);
    Py_XDECREF(old_tb);
}

// Clear error, which is not likely set. This is about bugs from CPython,
// use CLEAR_ERROR_OCCURRED is not sure.
NUITKA_MAY_BE_UNUSED static inline void DROP_ERROR_OCCURRED(void) {
    PyThreadState *tstate = PyThreadState_GET();

    if (unlikely(tstate->curexc_type != NULL)) {
        PyObject *old_type = tstate->curexc_type;
        PyObject *old_value = tstate->curexc_value;
        PyObject *old_tb = tstate->curexc_traceback;

        tstate->curexc_type = NULL;
        tstate->curexc_value = NULL;
        tstate->curexc_traceback = NULL;

        Py_DECREF(old_type);
        Py_XDECREF(old_value);
        Py_XDECREF(old_tb);
    }
}

// Fetch the current error into object variables.
NUITKA_MAY_BE_UNUSED static void FETCH_ERROR_OCCURRED(PyObject **exception_type, PyObject **exception_value,
                                                      PyTracebackObject **exception_traceback) {
    PyThreadState *tstate = PyThreadState_GET();

    *exception_type = tstate->curexc_type;
    *exception_value = tstate->curexc_value;
    *exception_traceback = (PyTracebackObject *)tstate->curexc_traceback;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("FETCH_ERROR_OCCURRED:\n");
    PRINT_EXCEPTION(tstate->curexc_type, tstate->curexc_value, tstate->curexc_traceback);
#endif

    tstate->curexc_type = NULL;
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;
}

// Fetch the current error into object variables.
NUITKA_MAY_BE_UNUSED static void FETCH_ERROR_OCCURRED_UNTRACED(PyObject **exception_type, PyObject **exception_value,
                                                               PyTracebackObject **exception_traceback) {
    PyThreadState *tstate = PyThreadState_GET();

    *exception_type = tstate->curexc_type;
    *exception_value = tstate->curexc_value;
    *exception_traceback = (PyTracebackObject *)tstate->curexc_traceback;

    tstate->curexc_type = NULL;
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;
}

NUITKA_MAY_BE_UNUSED static void RESTORE_ERROR_OCCURRED(PyObject *exception_type, PyObject *exception_value,
                                                        PyTracebackObject *exception_traceback) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *old_exception_type = tstate->curexc_type;
    PyObject *old_exception_value = tstate->curexc_value;
    PyObject *old_exception_traceback = tstate->curexc_traceback;

    tstate->curexc_type = exception_type;
    tstate->curexc_value = exception_value;
    tstate->curexc_traceback = (PyObject *)exception_traceback;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("RESTORE_ERROR_OCCURRED:\n");
    PRINT_EXCEPTION(tstate->curexc_type, tstate->curexc_value, tstate->curexc_traceback);
#endif

    Py_XDECREF(old_exception_type);
    Py_XDECREF(old_exception_value);
    Py_XDECREF(old_exception_traceback);
}

NUITKA_MAY_BE_UNUSED static void RESTORE_ERROR_OCCURRED_UNTRACED(PyObject *exception_type, PyObject *exception_value,
                                                                 PyTracebackObject *exception_traceback) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *old_exception_type = tstate->curexc_type;
    PyObject *old_exception_value = tstate->curexc_value;
    PyObject *old_exception_traceback = tstate->curexc_traceback;

    tstate->curexc_type = exception_type;
    tstate->curexc_value = exception_value;
    tstate->curexc_traceback = (PyObject *)exception_traceback;

    Py_XDECREF(old_exception_type);
    Py_XDECREF(old_exception_value);
    Py_XDECREF(old_exception_traceback);
}

struct Nuitka_FrameObject;

extern PyTracebackObject *MAKE_TRACEBACK(struct Nuitka_FrameObject *frame, int lineno);

// Add a frame to an existing exception trace-back.
NUITKA_MAY_BE_UNUSED static PyTracebackObject *ADD_TRACEBACK(PyTracebackObject *exception_tb,
                                                             struct Nuitka_FrameObject *frame, int lineno) {
    PyTracebackObject *traceback_new = MAKE_TRACEBACK(frame, lineno);
    traceback_new->tb_next = exception_tb;
    return traceback_new;
}

#if PYTHON_VERSION < 300
extern PyObject *const_str_plain_exc_type, *const_str_plain_exc_value, *const_str_plain_exc_traceback;
#endif

// Need some wrapper functions for accessing exception type, value, and traceback
// due to changes in Python 3.7

#if PYTHON_VERSION < 370
#define EXC_TYPE(x) (x->exc_type)
#define EXC_VALUE(x) (x->exc_value)
#define EXC_TRACEBACK(x) (x->exc_traceback)

#define EXC_TYPE_F(x) (x->m_frame->m_frame.f_exc_type)
#define EXC_VALUE_F(x) (x->m_frame->m_frame.f_exc_value)
#define EXC_TRACEBACK_F(x) (x->m_frame->m_frame.f_exc_traceback)

#else
#define EXC_TYPE(x) (x->exc_state.exc_type)
#define EXC_VALUE(x) (x->exc_state.exc_value)
#define EXC_TRACEBACK(x) (x->exc_state.exc_traceback)

#define EXC_TYPE_F(x) (x->m_exc_state.exc_type)
#define EXC_VALUE_F(x) (x->m_exc_state.exc_value)
#define EXC_TRACEBACK_F(x) (x->m_exc_state.exc_traceback)

#endif

// Helper that sets the current thread exception, releasing the current one, for
// use in this file only.
NUITKA_MAY_BE_UNUSED inline static void SET_CURRENT_EXCEPTION(PyObject *exception_type, PyObject *exception_value,
                                                              PyTracebackObject *exception_tb) {
    CHECK_OBJECT_X(exception_type);
    CHECK_OBJECT_X(exception_value);
    CHECK_OBJECT_X(exception_tb);

    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *old_type = EXC_TYPE(thread_state);
    PyObject *old_value = EXC_VALUE(thread_state);
    PyObject *old_tb = EXC_TRACEBACK(thread_state);

    CHECK_OBJECT_X(old_type);
    CHECK_OBJECT_X(old_value);
    CHECK_OBJECT_X(old_tb);

    EXC_TYPE(thread_state) = exception_type;
    EXC_VALUE(thread_state) = exception_value;
    EXC_TRACEBACK(thread_state) = (PyObject *)exception_tb;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION:\n");
    PRINT_EXCEPTION(exception_type, exception_value, (PyObject *)exception_tb);
#endif

    Py_XDECREF(old_type);
    Py_XDECREF(old_value);
    Py_XDECREF(old_tb);

#if PYTHON_VERSION < 300
    // Set sys attributes in the fastest possible way.
    PyObject *sys_dict = thread_state->interp->sysdict;
    CHECK_OBJECT(sys_dict);

    PyDict_SetItem(sys_dict, const_str_plain_exc_type, exception_type ? exception_type : Py_None);
    PyDict_SetItem(sys_dict, const_str_plain_exc_value, exception_value ? exception_value : Py_None);
    PyDict_SetItem(sys_dict, const_str_plain_exc_traceback, exception_tb ? (PyObject *)exception_tb : Py_None);

    if (exception_type)
        assert(Py_REFCNT(exception_type) >= 2);
    if (exception_value)
        assert(Py_REFCNT(exception_value) >= 2);
    if (exception_tb)
        assert(Py_REFCNT(exception_tb) >= 2);
#endif
}

#if PYTHON_VERSION < 300

// Preserve the current exception as the frame to restore.
NUITKA_MAY_BE_UNUSED static inline void PRESERVE_FRAME_EXCEPTION(struct Nuitka_FrameObject *frame_object) {
    PyFrameObject *frame = (PyFrameObject *)frame_object;

    // Setting exception for frame if not already done.
    if (frame->f_exc_type == NULL) {
        PyThreadState *thread_state = PyThreadState_GET();

        if (thread_state->exc_type != NULL && thread_state->exc_type != Py_None) {
#if _DEBUG_EXCEPTIONS
            PRINT_STRING("PRESERVE_FRAME_EXCEPTION: preserve thread exception\n");
#endif
            frame->f_exc_type = thread_state->exc_type;
            Py_INCREF(frame->f_exc_type);
            frame->f_exc_value = thread_state->exc_value;
            Py_XINCREF(frame->f_exc_value);
            frame->f_exc_traceback = thread_state->exc_traceback;
            Py_XINCREF(frame->f_exc_traceback);
        } else {
#if _DEBUG_EXCEPTIONS
            PRINT_STRING("PRESERVE_FRAME_EXCEPTION: no exception to preserve\n");
#endif
            frame->f_exc_type = Py_None;
            Py_INCREF(frame->f_exc_type);
            frame->f_exc_value = NULL;
            frame->f_exc_traceback = NULL;
        }
    }
#if _DEBUG_EXCEPTIONS
    else {
        PRINT_STRING("PRESERVE_FRAME_EXCEPTION: already preserving\n");
    }

    PRINT_ITEM((PyObject *)frame_object);
    PRINT_NEW_LINE();
    PRINT_EXCEPTION(frame->f_exc_type, frame->f_exc_value, frame->f_exc_traceback);
#endif
}

// Restore a previously preserved exception to the frame.
NUITKA_MAY_BE_UNUSED static inline void RESTORE_FRAME_EXCEPTION(struct Nuitka_FrameObject *frame_object) {
    PyFrameObject *frame = (PyFrameObject *)frame_object;

    if (frame->f_exc_type) {
#if _DEBUG_EXCEPTIONS
        PRINT_STRING("RESTORE_FRAME_EXCEPTION: restoring preserved\n");
        PRINT_ITEM((PyObject *)frame_object);
        PRINT_NEW_LINE();
#endif

        SET_CURRENT_EXCEPTION(frame->f_exc_type, frame->f_exc_value, (PyTracebackObject *)frame->f_exc_traceback);

        frame->f_exc_type = NULL;
        frame->f_exc_value = NULL;
        frame->f_exc_traceback = NULL;
    }
#if _DEBUG_EXCEPTIONS
    else {
        PRINT_STRING("RESTORE_FRAME_EXCEPTION: nothing to restore\n");
        PRINT_ITEM((PyObject *)frame_object);
        PRINT_NEW_LINE();
    }
#endif
}

#endif

// Publish an exception, erasing the values of the variables.
NUITKA_MAY_BE_UNUSED static inline void PUBLISH_EXCEPTION(PyObject **exception_type, PyObject **exception_value,
                                                          PyTracebackObject **exception_tb) {
#if _DEBUG_EXCEPTIONS
    PRINT_STRING("PUBLISH_EXCEPTION:\n");
#endif
    SET_CURRENT_EXCEPTION(*exception_type, *exception_value, *exception_tb);

    *exception_type = NULL;
    *exception_value = NULL;
    *exception_tb = NULL;
}

// Normalize an exception.
NUITKA_MAY_BE_UNUSED static inline void NORMALIZE_EXCEPTION(PyObject **exception_type, PyObject **exception_value,
                                                            PyTracebackObject **exception_tb) {
#if _DEBUG_EXCEPTIONS
    PRINT_STRING("NORMALIZE_EXCEPTION:\n");
    PRINT_EXCEPTION(*exception_type, *exception_value, (PyObject *)*exception_tb);
#endif

    if (*exception_type != Py_None && *exception_type != NULL) {
        PyErr_NormalizeException(exception_type, exception_value, (PyObject **)exception_tb);
    }

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("normalized:\n");
    PRINT_EXCEPTION(*exception_type, *exception_value, (PyObject *)*exception_tb);
#endif
}

NUITKA_MAY_BE_UNUSED static bool EXCEPTION_MATCH_GENERATOR(PyObject *exception_value) {
    CHECK_OBJECT(exception_value);

    // We need to check the class.
    if (PyExceptionInstance_Check(exception_value)) {
        exception_value = PyExceptionInstance_Class(exception_value);
    }

    // Lets be optimistic. If it matches, we would be wasting our time.
    if (exception_value == PyExc_GeneratorExit || exception_value == PyExc_StopIteration) {
        return true;
    }

    if (PyExceptionClass_Check(exception_value)) {
        // Save the current exception, if any, we must preserve it.
        PyObject *save_exception_type, *save_exception_value;
        PyTracebackObject *save_exception_tb;
        FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

        int res = PyObject_IsSubclass(exception_value, PyExc_GeneratorExit);

        // This function must not fail, so print the error here */
        if (unlikely(res == -1)) {
            PyErr_WriteUnraisable(exception_value);
        }

        if (res == 1)
            return true;

        res = PyObject_IsSubclass(exception_value, PyExc_StopIteration);

        // This function must not fail, so print the error here */
        if (unlikely(res == -1)) {
            PyErr_WriteUnraisable(exception_value);
        }

        RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);

        return res == 1;
    }

    return false;
}

NUITKA_MAY_BE_UNUSED static bool EXCEPTION_MATCH_BOOL_SINGLE(PyObject *exception_value, PyObject *exception_checked) {
    CHECK_OBJECT(exception_value);
    CHECK_OBJECT(exception_checked);

    // We need to check the class.
    if (PyExceptionInstance_Check(exception_value)) {
        exception_value = PyExceptionInstance_Class(exception_value);
    }

    // Lets be optimistic. If it matches, we would be wasting our time.
    if (exception_value == exception_checked) {
        return true;
    }

    if (PyExceptionClass_Check(exception_value)) {
        // Save the current exception, if any, we must preserve it.
        PyObject *save_exception_type, *save_exception_value;
        PyTracebackObject *save_exception_tb;
        FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

        int res = PyObject_IsSubclass(exception_value, exception_checked);

        // This function must not fail, so print the error here */
        if (unlikely(res == -1)) {
            PyErr_WriteUnraisable(exception_value);
        }

        RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);

        return res == 1;
    }

    return false;
}

// This is for the actual comparison operation that is being done in the
// node tree, no other code should use it. TODO: Then it's probably not
// properly located here, and it could still in-line the code of
// "PyErr_GivenExceptionMatches" to save on Python3 doing two tuple checks
// and iterations.
NUITKA_MAY_BE_UNUSED static inline int EXCEPTION_MATCH_BOOL(PyObject *exception_value, PyObject *exception_checked) {
    CHECK_OBJECT(exception_value);
    CHECK_OBJECT(exception_checked);

#if PYTHON_VERSION >= 300
    /* Note: Exact matching tuples seems to needed, despite using GET_ITEM later
       on, this probably cannot be overloaded that deep. */
    if (PyTuple_Check(exception_checked)) {
        Py_ssize_t length = PyTuple_Size(exception_checked);

        for (Py_ssize_t i = 0; i < length; i += 1) {
            PyObject *element = PyTuple_GET_ITEM(exception_checked, i);

            if (unlikely(!PyExceptionClass_Check(element))) {
                PyErr_Format(PyExc_TypeError, "catching classes that do not inherit from BaseException is not allowed");
                return -1;
            }
        }
    } else if (unlikely(!PyExceptionClass_Check(exception_checked))) {
        PyErr_Format(PyExc_TypeError, "catching classes that do not inherit from BaseException is not allowed");
        return -1;
    }
#endif

    return PyErr_GivenExceptionMatches(exception_value, exception_checked);
}

#if PYTHON_VERSION >= 300
// Attach the exception context if necessary.
NUITKA_MAY_BE_UNUSED static inline void ADD_EXCEPTION_CONTEXT(PyObject **exception_type, PyObject **exception_value) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *context = EXC_VALUE(tstate);

    if (context != NULL) {
        NORMALIZE_EXCEPTION(exception_type, exception_value, NULL);

        Py_INCREF(context);
        PyException_SetContext(*exception_value, context);
    }
}
#endif

/* Special helper that checks for StopIteration and if so clears it, only
 indicating if it was set.

   Equivalent to if(PyErr_ExceptionMatches(PyExc_StopIteration) PyErr_Clear();

   If error is raised by built-in function next() and an iterator’s __next__()
   method to signal that there are no further items produced by the iterator then
   it resets the TSTATE to NULL and returns True else return False

*/
NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(void) {
    PyObject *error = GET_ERROR_OCCURRED();

    if (error == NULL) {
        return true;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_StopIteration)) {
        CLEAR_ERROR_OCCURRED();
        return true;
    } else {
        return false;
    }
}

// Special helper that checks for KeyError and if so clears it, only
// indicating if it was set.
NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(void) {
    PyObject *error = GET_ERROR_OCCURRED();

    if (error == NULL) {
        return true;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_KeyError)) {
        CLEAR_ERROR_OCCURRED();
        return true;
    } else {
        return false;
    }
}

#endif
