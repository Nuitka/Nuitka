//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_ITERATORS_H__
#define __NUITKA_HELPER_ITERATORS_H__

#if PYTHON_VERSION >= 0x270
// Initialize value for "tp_iternext" to compare with, needed by HAS_ITERNEXT
// which emulates "PyCheck_Iter" but is bug free.
extern iternextfunc default_iternext;
extern void _initSlotIterNext(void);
#endif

// This is like "PyIter_Check" but without bugs due to shared library pointers.
NUITKA_MAY_BE_UNUSED static inline bool HAS_ITERNEXT(PyObject *value) {
#if PYTHON_VERSION < 0x300
    if (!PyType_HasFeature(Py_TYPE(value), Py_TPFLAGS_HAVE_ITER)) {
        return false;
    }
#endif

    iternextfunc tp_iternext = Py_TYPE(value)->tp_iternext;

    if (tp_iternext == NULL) {
        return false;
    }

#if PYTHON_VERSION >= 0x270
    return tp_iternext != default_iternext;
#else
    return true;
#endif
}

// Taken from CPython implementation, so we can access and create it, needs to match
// their definition exactly. spell-checker: ignore seqiterobject
typedef struct {
    PyObject_HEAD
#if PYTHON_VERSION < 0x300
        long it_index;
#else
        Py_ssize_t it_index;
#endif
    PyObject *it_seq;
} seqiterobject;

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_ITERATOR_INFALLIBLE(PyObject *iterated) {
    CHECK_OBJECT(iterated);

#if PYTHON_VERSION < 0x300
    getiterfunc tp_iter = NULL;
    if (PyType_HasFeature(Py_TYPE(iterated), Py_TPFLAGS_HAVE_ITER)) {
        tp_iter = Py_TYPE(iterated)->tp_iter;
    }
#else
    getiterfunc tp_iter = Py_TYPE(iterated)->tp_iter;
#endif
    if (tp_iter) {
        PyObject *result = (*tp_iter)(iterated);
        CHECK_OBJECT(result);
        assert(HAS_ITERNEXT(result));

        return result;
    } else {
        assert(PySequence_Check(iterated));

        seqiterobject *result = (seqiterobject *)Nuitka_GC_New(&PySeqIter_Type);
        assert(result);

        result->it_index = 0;
        Py_INCREF(iterated);
        result->it_seq = iterated;

        Nuitka_GC_Track(result);

        return (PyObject *)result;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_ITERATOR(PyThreadState *tstate, PyObject *iterated) {
    CHECK_OBJECT(iterated);

#if _NUITKA_EXPERIMENTAL_DISABLE_ITERATOR_OPT
    return PyObject_GetIter(iterated);
#else

#if PYTHON_VERSION < 0x300
    getiterfunc tp_iter = NULL;
    if (PyType_HasFeature(Py_TYPE(iterated), Py_TPFLAGS_HAVE_ITER)) {
        tp_iter = Py_TYPE(iterated)->tp_iter;
    }
#else
    getiterfunc tp_iter = Py_TYPE(iterated)->tp_iter;
#endif

    if (tp_iter) {
        PyObject *result = (*tp_iter)(iterated);

        if (unlikely(result == NULL)) {
            return NULL;
        } else if (unlikely(!HAS_ITERNEXT(result))) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("iter() returned non-iterator of type '%s'", result);

            Py_DECREF(result);

            return NULL;
        } else {
            return result;
        }
    } else if (PySequence_Check(iterated)) {
        seqiterobject *result = (seqiterobject *)Nuitka_GC_New(&PySeqIter_Type);
        assert(result);

        result->it_index = 0;
        Py_INCREF(iterated);
        result->it_seq = iterated;

        Nuitka_GC_Track(result);

        return (PyObject *)result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not iterable", iterated);

        return NULL;
    }
#endif
}

#if PYTHON_VERSION >= 0x370

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_UNPACK_ITERATOR(PyObject *iterated) {
    CHECK_OBJECT(iterated);

    getiterfunc tp_iter = Py_TYPE(iterated)->tp_iter;

    if (tp_iter) {
        PyObject *result = (*tp_iter)(iterated);

        if (unlikely(result == NULL)) {
            return NULL;
        } else if (unlikely(!HAS_ITERNEXT(result))) {
            PyErr_Format(PyExc_TypeError, "iter() returned non-iterator of type '%s'", Py_TYPE(result)->tp_name);

            Py_DECREF(result);

            return NULL;
        } else {
            return result;
        }
    } else if (PySequence_Check(iterated)) {
        seqiterobject *result = (seqiterobject *)Nuitka_GC_New(&PySeqIter_Type);
        assert(result);

        result->it_index = 0;
        Py_INCREF(iterated);
        result->it_seq = iterated;

        Nuitka_GC_Track(result);

        return (PyObject *)result;
    } else {
        PyErr_Format(PyExc_TypeError, "cannot unpack non-iterable %s object", Py_TYPE(iterated)->tp_name);

        return NULL;
    }
}

#endif

NUITKA_MAY_BE_UNUSED static PyObject *ITERATOR_NEXT_ITERATOR(PyObject *iterator) {
    CHECK_OBJECT(iterator);
    iternextfunc iternext = Py_TYPE(iterator)->tp_iternext;
    assert(iternext != NULL);

#if _NUITKA_EXPERIMENTAL_DISABLE_ITERATOR_OPT
    return PyIter_Next(iterator);
#else
    PyObject *result = (*iternext)(iterator);
    CHECK_OBJECT_X(result);
    return result;
#endif
}

NUITKA_MAY_BE_UNUSED static PyObject *ITERATOR_NEXT(PyObject *iterator) {
    CHECK_OBJECT(iterator);

#if _NUITKA_EXPERIMENTAL_DISABLE_ITERATOR_OPT
    return PyIter_Next(iterator);
#else
    iternextfunc iternext = Py_TYPE(iterator)->tp_iternext;

    if (unlikely(iternext == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(
#if PYTHON_VERSION < 0x300 && defined(_NUITKA_FULL_COMPAT)
            "%s object is not an iterator",
#else
            "'%s' object is not an iterator",
#endif
            iterator);

        return NULL;
    }

    PyObject *result = (*iternext)(iterator);

    CHECK_OBJECT_X(result);

    return result;
#endif
}

NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_NEXT2(PyThreadState *tstate, PyObject *iterator,
                                                    PyObject *default_value) {
    CHECK_OBJECT(iterator);
    CHECK_OBJECT(default_value);

    PyObject *result = (*Py_TYPE(iterator)->tp_iternext)(iterator);

    if (unlikely(result == NULL)) {
        bool stop_iteration_error = CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate);

        if (unlikely(stop_iteration_error == false)) {
            return NULL;
        }

        Py_INCREF(default_value);
        return default_value;
    }

    CHECK_OBJECT(result);
    return result;
}

// For cases, where no exception raising is needed, because we know it at compile time.
NUITKA_MAY_BE_UNUSED static PyObject *UNPACK_NEXT_INFALLIBLE(PyObject *iterator) {
    CHECK_OBJECT(iterator);
    assert(HAS_ITERNEXT(iterator));

    PyObject *result = (*Py_TYPE(iterator)->tp_iternext)(iterator);
    CHECK_OBJECT(result);
    return result;
}

#if PYTHON_VERSION < 0x350
NUITKA_MAY_BE_UNUSED static PyObject *UNPACK_NEXT(PyThreadState *tstate,
                                                  struct Nuitka_ExceptionPreservationItem *exception_state,
                                                  PyObject *iterator, int seq_size_so_far)
#else
NUITKA_MAY_BE_UNUSED static PyObject *UNPACK_NEXT(PyThreadState *tstate,
                                                  struct Nuitka_ExceptionPreservationItem *exception_state,
                                                  PyObject *iterator, int seq_size_so_far, int expected)
#endif
{
    CHECK_OBJECT(iterator);
    assert(HAS_ITERNEXT(iterator));

    PyObject *result = (*Py_TYPE(iterator)->tp_iternext)(iterator);

    if (unlikely(result == NULL)) {
        bool had_stop_iteration = true;

        PyObject *error = GET_ERROR_OCCURRED(tstate);

        if (error != NULL) {
            if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_StopIteration)) {
                CLEAR_ERROR_OCCURRED(tstate);
            } else {
                had_stop_iteration = false;
            }
        }

        if (had_stop_iteration) {
#if PYTHON_VERSION < 0x350
            if (seq_size_so_far == 1) {
                SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, exception_state, PyExc_ValueError,
                                                                "need more than 1 value to unpack");
            } else {
                SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_FORMAT1(
                    tstate, exception_state, PyExc_ValueError, "need more than %d values to unpack", seq_size_so_far);
            }
#else
            SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_FORMAT2(tstate, exception_state, PyExc_ValueError,
                                                                "not enough values to unpack (expected %d, got %d)",
                                                                expected, seq_size_so_far);
#endif
        } else {
            assert(HAS_ERROR_OCCURRED(tstate));
            FETCH_ERROR_OCCURRED_STATE(tstate, exception_state);
        }

        return NULL;
    }

    CHECK_OBJECT(result);

    return result;
}

#if PYTHON_VERSION >= 0x350
// Different error message for starred unpacks
NUITKA_MAY_BE_UNUSED static PyObject *UNPACK_NEXT_STARRED(PyThreadState *tstate,
                                                          struct Nuitka_ExceptionPreservationItem *exception_state,
                                                          PyObject *iterator, int seq_size_so_far, int expected) {
    CHECK_OBJECT(iterator);
    assert(HAS_ITERNEXT(iterator));

    PyObject *result = (*Py_TYPE(iterator)->tp_iternext)(iterator);

    if (unlikely(result == NULL)) {
        FETCH_ERROR_OCCURRED_STATE(tstate, exception_state);

        // TODO: Specialize more for StopIteration and maybe derived ones do not
        // count or do they?
        if (!HAS_EXCEPTION_STATE(exception_state) ||
            EXCEPTION_STATE_MATCH_BOOL_SINGLE(tstate, exception_state, PyExc_StopIteration)) {
            SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_FORMAT2(
                tstate, exception_state, PyExc_ValueError, "not enough values to unpack (expected at least %d, got %d)",
                expected, seq_size_so_far);
        }

        return NULL;
    }

    CHECK_OBJECT(result);

    return result;
}
#endif

NUITKA_MAY_BE_UNUSED static bool UNPACK_ITERATOR_CHECK(PyThreadState *tstate,
                                                       struct Nuitka_ExceptionPreservationItem *exception_state,
                                                       PyObject *iterator, int expected) {
    PyObject *attempt = (*(Py_TYPE(iterator)->tp_iternext))(iterator);

    if (likely(attempt == NULL)) {
        PyObject *error = GET_ERROR_OCCURRED(tstate);

        if (error != NULL) {
            if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_StopIteration)) {
                CLEAR_ERROR_OCCURRED(tstate);
            } else {
                FETCH_ERROR_OCCURRED_STATE(tstate, exception_state);
                return false;
            }
        }

        return true;
    } else {
        Py_DECREF(attempt);

#if PYTHON_VERSION < 0x300
        SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, exception_state, PyExc_ValueError,
                                                        "too many values to unpack");
#else
        SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_FORMAT1(tstate, exception_state, PyExc_ValueError,
                                                            "too many values to unpack (expected %d)", expected);
#endif
        return false;
    }
}

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
