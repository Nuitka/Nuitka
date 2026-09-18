//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_EXCEPTION_GROUPS_H__
#define __NUITKA_EXCEPTION_GROUPS_H__

// Exception group helpers for generated code and compiled code helpers.

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/cpython_api_compat.h"

#include "internal/pycore_pyerrors.h"
#include "nuitka/allocator.h"
#include "nuitka/calling.h"
#include "nuitka/defines.h"
#include "nuitka/exceptions.h"
#include "nuitka/helper/tuples.h"
extern PyObject *const_str_plain_derive;
extern PyObject *const_str_plain_split;
extern PyObject *const_str_plain___notes__;
#endif

#if PYTHON_VERSION >= 0x3b0

NUITKA_MAY_BE_UNUSED static void FORMAT_CLASS_CATCH_ERROR(PyThreadState *tstate) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                    "catching classes that do not inherit from BaseException is not allowed");
}

NUITKA_MAY_BE_UNUSED static int CHECK_EXCEPTION_TYPE_VALID(PyThreadState *tstate, PyObject *right) {
    if (PyTuple_Check(right)) {
        Py_ssize_t length = PyTuple_GET_SIZE(right);

        for (Py_ssize_t i = 0; i < length; i++) {
            PyObject *exc = PyTuple_GET_ITEM(right, i);

            if (!PyExceptionClass_Check(exc)) {
                FORMAT_CLASS_CATCH_ERROR(tstate);
                return -1;
            }
        }
    } else {
        if (!PyExceptionClass_Check(right)) {
            FORMAT_CLASS_CATCH_ERROR(tstate);
            return -1;
        }
    }
    return 0;
}

NUITKA_MAY_BE_UNUSED static int CHECK_EXCEPTION_STAR_VALID(PyThreadState *tstate, PyObject *right) {
    if (CHECK_EXCEPTION_TYPE_VALID(tstate, right) < 0) {
        return -1;
    }

    int is_subclass = 0;

    if (PyTuple_Check(right)) {
        Py_ssize_t length = PyTuple_GET_SIZE(right);

        for (Py_ssize_t i = 0; i < length; i++) {
            PyObject *exc = PyTuple_GET_ITEM(right, i);
            is_subclass = PyObject_IsSubclass(exc, PyExc_BaseExceptionGroup);

            if (is_subclass < 0) {
                return -1;
            }

            if (is_subclass) {
                break;
            }
        }
    } else {
        is_subclass = PyObject_IsSubclass(right, PyExc_BaseExceptionGroup);

        if (is_subclass < 0) {
            return -1;
        }
    }

    if (is_subclass) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                        "catching ExceptionGroup with except* is not allowed. Use except instead.");
        return -1;
    }

    return 0;
}

// This is copied directly from CPython
NUITKA_MAY_BE_UNUSED static inline PyObject *CREATE_EXCEPTION_GROUP(PyThreadState *tstate, PyObject *excs) {
    CHECK_OBJECT(excs);
    PyObject *args[2] = {const_str_empty, excs};

    return CALL_FUNCTION_WITH_ARGS2(tstate, PyExc_BaseExceptionGroup, args);
}

// This is copied directly from CPython
NUITKA_MAY_BE_UNUSED static inline int EXCEPTION_GROUP_MATCH_BOOL(PyThreadState *tstate, PyObject *exc_value,
                                                                  PyObject *match_type, PyObject **match,
                                                                  PyObject **rest) {
    CHECK_OBJECT(match_type);

    // The match type is checked for every clause, even if there is nothing
    // left to match, just like CPython does for each executed clause.
    if (CHECK_EXCEPTION_STAR_VALID(tstate, match_type) < 0) {
        return -1;
    }

    if (Py_IsNone(exc_value)) {
        Py_INCREF_IMMORTAL(Py_None);
        *match = Py_None;

        Py_INCREF_IMMORTAL(Py_None);
        *rest = Py_None;

        return 0;
    }
    assert(PyExceptionInstance_Check(exc_value));

    int is_match = EXCEPTION_MATCH_BOOL(tstate, exc_value, match_type);
    if (unlikely(is_match < 0)) {
        return -1;
    }

    if (is_match) {
        /* Full match of exc itself */
        bool is_eg = _PyBaseExceptionGroup_Check(exc_value);

        if (is_eg) {
            *match = Py_NewRef(exc_value);
        } else {
            /* naked exception, we need to wrap it */
            PyObject *excs = MAKE_TUPLE1(tstate, exc_value);
            CHECK_OBJECT(excs);

            PyObject *wrapped = CREATE_EXCEPTION_GROUP(tstate, excs);
            Py_DECREF(excs);

            if (unlikely(wrapped == NULL)) {
                return -1;
            }
            // TODO: Starting with CPython 3.12.9 and 3.13.2, the implicit
            // exception group also gets the traceback of the current frame
            // attached. We cannot do that here, as the frame is not available
            // in this helper, so for now this matches the Python 3.11 behavior
            // of the implicit group having no traceback. Implementing this
            // requires passing the frame in and doing the equivalent of:
            //
            //     PyFrameObject *f = _PyFrame_GetFrameObject(frame);
            //     if (f == NULL) {
            //         Py_DECREF(wrapped);
            //         return -1;
            //     }
            //     PyObject *tb = _PyTraceBack_FromFrame(NULL, f);
            //     if (tb == NULL) {
            //         Py_DECREF(wrapped);
            //         return -1;
            //     }
            //     PyException_SetTraceback(wrapped, tb);
            //     Py_DECREF(tb);
            //
            *match = wrapped;
        }
        Py_INCREF_IMMORTAL(Py_None);
        *rest = Py_None;
        return 0;
    }

    /* exc_value does not match match_type.
     * Check for partial match if it's an exception group.
     */
    if (_PyBaseExceptionGroup_Check(exc_value)) {
        PyObject *pair = CALL_METHOD_WITH_SINGLE_ARG(tstate, exc_value, const_str_plain_split, match_type);
        if (pair == NULL) {
            return -1;
        }

        if (!PyTuple_CheckExact(pair)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_TypeError, "%s.split must return a tuple, not %s",
                                                Py_TYPE(exc_value)->tp_name, Py_TYPE(pair)->tp_name);
            Py_DECREF(pair);
            return -1;
        }

        // allow tuples of length > 2 for backwards compatibility
        if (PyTuple_GET_SIZE(pair) < 2) {
            PyErr_Format(PyExc_TypeError, "%s.split must return a 2-tuple, got tuple of size %zd",
                         Py_TYPE(exc_value)->tp_name, PyTuple_GET_SIZE(pair));
            Py_DECREF(pair);
            return -1;
        }

        *match = Py_NewRef(PyTuple_GET_ITEM(pair, 0));
        *rest = Py_NewRef(PyTuple_GET_ITEM(pair, 1));
        Py_DECREF(pair);
        return 0;
    }

    /* no match */
    Py_INCREF_IMMORTAL(Py_None);
    *match = Py_None;
    *rest = Py_NewRef(exc_value);

    return 0;
}

NUITKA_MAY_BE_UNUSED static inline PyObject *EXCEPTION_GROUP_MATCH(PyThreadState *tstate, PyObject *exc_value,
                                                                   PyObject *match_type) {
    CHECK_OBJECT(exc_value);
    CHECK_OBJECT(match_type);
    PyObject *match;
    PyObject *rest;
    if (EXCEPTION_GROUP_MATCH_BOOL(tstate, exc_value, match_type, &match, &rest) < 0) {
        return NULL;
    }

    CHECK_OBJECT(match);
    CHECK_OBJECT(rest);
    return MAKE_TUPLE2_0(tstate, match, rest);
}

// The following mirrors what CPython does, it is used to combine the
// exceptions raised by the "except*" clauses with the unhandled part of the
// original exception group, and to raise the result.

// Collect the object ids of all leaf exceptions contained in "exc".
static int _collectExceptionGroupLeafIds(PyObject *exc, PyObject *leaf_ids) {
    CHECK_OBJECT(exc);
    CHECK_OBJECT(leaf_ids);

    if (!_PyBaseExceptionGroup_Check(exc)) {
        PyObject *exc_id = PyLong_FromVoidPtr(exc);

        if (exc_id == NULL) {
            return -1;
        }

        int res = PySet_Add(leaf_ids, exc_id);
        Py_DECREF(exc_id);

        return res;
    }

    PyBaseExceptionGroupObject *eg = (PyBaseExceptionGroupObject *)exc;
    Py_ssize_t num_excs = PyTuple_GET_SIZE(eg->excs);

    for (Py_ssize_t i = 0; i < num_excs; i++) {
        PyObject *element = PyTuple_GET_ITEM(eg->excs, i);

        if (unlikely(_collectExceptionGroupLeafIds(element, leaf_ids) < 0)) {
            return -1;
        }
    }

    return 0;
}

// Build a new exception group of the type of "orig" with "excs" and the
// metadata of "orig" copied over, or nothing if "excs" is empty.
static int _makeExceptionGroupSubset(PyThreadState *tstate, PyObject *orig, PyObject *excs, PyObject **result) {
    *result = NULL;

    Py_ssize_t num_excs = PySequence_Size(excs);
    if (num_excs < 0) {
        return -1;
    } else if (num_excs == 0) {
        return 0;
    }

    PyObject *eg = CALL_METHOD_WITH_SINGLE_ARG(tstate, orig, const_str_plain_derive, excs);

    if (eg == NULL) {
        return -1;
    }

    if (unlikely(!_PyBaseExceptionGroup_Check(eg))) {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(
            PyExc_TypeError, "derive must return an instance of BaseExceptionGroup, got %s", Py_TYPE(eg)->tp_name);
        Py_DECREF(eg);
        return -1;
    }

    PyObject *traceback = PyException_GetTraceback(orig);

    if (traceback != NULL) {
        int res = PyException_SetTraceback(eg, traceback);
        Py_DECREF(traceback);

        if (unlikely(res < 0)) {
            Py_DECREF(eg);
            return -1;
        }
    }

    PyException_SetContext(eg, PyException_GetContext(orig));
    PyException_SetCause(eg, PyException_GetCause(orig));

    PyObject *notes = LOOKUP_ATTRIBUTE(tstate, orig, const_str_plain___notes__);

    if (notes == NULL) {
        if (unlikely(!_CHECK_AND_CLEAR_EXCEPTION_OCCURRED(tstate, PyExc_AttributeError))) {
            Py_DECREF(eg);
            return -1;
        }
    } else if (PySequence_Check(notes)) {
        PyObject *notes_copy = PySequence_List(notes);
        Py_DECREF(notes);

        if (notes_copy == NULL) {
            Py_DECREF(eg);
            return -1;
        }

        if (unlikely(SET_ATTRIBUTE(tstate, eg, const_str_plain___notes__, notes_copy) == false)) {
            Py_DECREF(notes_copy);
            Py_DECREF(eg);
            return -1;
        }

        Py_DECREF(notes_copy);
    } else {
        Py_DECREF(notes);
    }

    *result = eg;
    return 0;
}

// Project "exc" onto the leaves whose object ids are in "leaf_ids", returning
// the result in "result", or nothing if no leaf was contained.
static int _projectExceptionGroup(PyThreadState *tstate, PyObject *exc, PyObject *leaf_ids, PyObject **result) {
    *result = NULL;

    if (!_PyBaseExceptionGroup_Check(exc)) {
        PyObject *exc_id = PyLong_FromVoidPtr(exc);

        if (exc_id == NULL) {
            return -1;
        }

        int res = PySet_Contains(leaf_ids, exc_id);
        Py_DECREF(exc_id);

        if (unlikely(res < 0)) {
            return -1;
        }

        if (res == 1) {
            *result = Py_NewRef(exc);
        }

        return 0;
    }

    PyBaseExceptionGroupObject *eg = (PyBaseExceptionGroupObject *)exc;
    Py_ssize_t num_excs = PyTuple_GET_SIZE(eg->excs);

    PyObject *match_list = PyList_New(0);

    if (match_list == NULL) {
        return -1;
    }

    for (Py_ssize_t i = 0; i < num_excs; i++) {
        PyObject *element = PyTuple_GET_ITEM(eg->excs, i);
        PyObject *sub_result = NULL;

        if (unlikely(_projectExceptionGroup(tstate, element, leaf_ids, &sub_result) < 0)) {
            Py_DECREF(match_list);
            return -1;
        }

        if (sub_result != NULL) {
            int res = PyList_Append(match_list, sub_result);
            Py_DECREF(sub_result);

            if (unlikely(res < 0)) {
                Py_DECREF(match_list);
                return -1;
            }
        }
    }

    if (PyList_GET_SIZE(match_list) == 0) {
        Py_DECREF(match_list);
        return 0;
    }

    int res = _makeExceptionGroupSubset(tstate, exc, match_list, result);
    Py_DECREF(match_list);

    return res;
}

// Project "eg" onto the leaves contained in the exception groups of "keep".
static PyObject *_makeExceptionGroupProjection(PyThreadState *tstate, PyObject *eg, PyObject *keep) {
    PyObject *leaf_ids = PySet_New(NULL);

    if (leaf_ids == NULL) {
        return NULL;
    }

    Py_ssize_t num_keep = PyList_GET_SIZE(keep);

    for (Py_ssize_t i = 0; i < num_keep; i++) {
        PyObject *element = PyList_GET_ITEM(keep, i);

        if (unlikely(_collectExceptionGroupLeafIds(element, leaf_ids) < 0)) {
            Py_DECREF(leaf_ids);
            return NULL;
        }
    }

    PyObject *result = NULL;
    int res = _projectExceptionGroup(tstate, eg, leaf_ids, &result);
    Py_DECREF(leaf_ids);

    if (unlikely(res < 0)) {
        return NULL;
    }

    if (result == NULL) {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }

    return result;
}

// Decide if an exception is a re-raise of (a part of) the original exception
// group, i.e. all of its leaf exceptions are contained in it.
//
// TODO: CPython decides this by comparing the exception metadata, which is
// not maintained yet for exceptions we raise, so we use the contained leaf
// exceptions instead, which gets the same results for all but constructed
// cases, and should be replaced once that metadata is available.
static int _isDerivedException(PyObject *exc, PyObject *leaf_ids) {
    CHECK_OBJECT(exc);
    CHECK_OBJECT(leaf_ids);

    if (!_PyBaseExceptionGroup_Check(exc)) {
        PyObject *exc_id = PyLong_FromVoidPtr(exc);

        if (exc_id == NULL) {
            return -1;
        }

        int res = PySet_Contains(leaf_ids, exc_id);
        Py_DECREF(exc_id);

        return res;
    }

    PyBaseExceptionGroupObject *eg = (PyBaseExceptionGroupObject *)exc;
    Py_ssize_t num_excs = PyTuple_GET_SIZE(eg->excs);

    if (num_excs == 0) {
        return 0;
    }

    for (Py_ssize_t i = 0; i < num_excs; i++) {
        int res = _isDerivedException(PyTuple_GET_ITEM(eg->excs, i), leaf_ids);

        if (res != 1) {
            return res;
        }
    }

    return 1;
}

// Calculate the exception to be raised at the end of an "except*" construct.
// The "orig" is the original caught exception, and "excs" is the list of
// exceptions that were raised or re-raised in the clauses, potentially with
// None values. Returns the exception to raise, or None if nothing is to be
// raised.
NUITKA_MAY_BE_UNUSED static PyObject *EXCEPTION_GROUP_PREPARE_RERAISE(PyThreadState *tstate, PyObject *orig,
                                                                      PyObject *excs) {
    CHECK_OBJECT(orig);
    CHECK_OBJECT(excs);

    Py_ssize_t numexcs = PyList_GET_SIZE(excs);

    if (numexcs == 0) {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }

    if (!_PyBaseExceptionGroup_Check(orig)) {
        // A naked exception was caught and wrapped, and therefore only one
        // clause can have executed, so there is at most one exception to
        // raise, which may also be None, if it was handled.
        for (Py_ssize_t i = 0; i < numexcs; i++) {
            PyObject *element = PyList_GET_ITEM(excs, i);

            if (!Py_IsNone(element)) {
                return Py_NewRef(element);
            }
        }

        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }

    PyObject *raised_list = PyList_New(0);

    if (raised_list == NULL) {
        return NULL;
    }

    PyObject *reraised_list = PyList_New(0);

    if (reraised_list == NULL) {
        Py_DECREF(raised_list);
        return NULL;
    }

    PyObject *orig_leaf_ids = PySet_New(NULL);

    if (orig_leaf_ids == NULL) {
        Py_DECREF(raised_list);
        Py_DECREF(reraised_list);
        return NULL;
    }

    if (unlikely(_collectExceptionGroupLeafIds(orig, orig_leaf_ids) < 0)) {
        Py_DECREF(orig_leaf_ids);
        Py_DECREF(raised_list);
        Py_DECREF(reraised_list);
        return NULL;
    }

    PyObject *result = NULL;
    PyObject *reraised_eg = NULL;

    // Split into raised and reraised, by checking for being derived from the
    // original exception group.
    for (Py_ssize_t i = 0; i < numexcs; i++) {
        PyObject *element = PyList_GET_ITEM(excs, i);

        if (Py_IsNone(element)) {
            continue;
        }

        int is_reraise = _isDerivedException(element, orig_leaf_ids);

        if (unlikely(is_reraise < 0)) {
            Py_DECREF(orig_leaf_ids);
            goto done;
        }

        PyObject *append_list = is_reraise == 1 ? reraised_list : raised_list;

        if (unlikely(PyList_Append(append_list, element) < 0)) {
            Py_DECREF(orig_leaf_ids);
            goto done;
        }
    }

    Py_DECREF(orig_leaf_ids);

    reraised_eg = _makeExceptionGroupProjection(tstate, orig, reraised_list);

    if (reraised_eg == NULL) {
        goto done;
    }

    if (PyList_GET_SIZE(raised_list) == 0) {
        result = reraised_eg;
        reraised_eg = NULL;
    } else {
        if (!Py_IsNone(reraised_eg)) {
            if (unlikely(PyList_Append(raised_list, reraised_eg) < 0)) {
                goto done;
            }
        }

        if (PyList_GET_SIZE(raised_list) > 1) {
            result = CREATE_EXCEPTION_GROUP(tstate, raised_list);
        } else {
            result = Py_NewRef(PyList_GET_ITEM(raised_list, 0));
        }
    }

done:
    Py_XDECREF(reraised_eg);
    Py_DECREF(raised_list);
    Py_DECREF(reraised_list);

    return result;
}

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
