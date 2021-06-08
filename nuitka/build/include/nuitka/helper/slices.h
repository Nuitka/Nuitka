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
#ifndef __NUITKA_HELPER_SLICES_H__
#define __NUITKA_HELPER_SLICES_H__

// Note: Cannot these cannot fail, PySlice_New does not return errors.
NUITKA_MAY_BE_UNUSED static PyObject *MAKE_SLICEOBJ3(PyObject *start, PyObject *stop, PyObject *step) {
    CHECK_OBJECT(start);
    CHECK_OBJECT(stop);
    CHECK_OBJECT(step);

    return PySlice_New(start, stop, step);
}
NUITKA_MAY_BE_UNUSED static PyObject *MAKE_SLICEOBJ2(PyObject *start, PyObject *stop) {
    CHECK_OBJECT(start);
    CHECK_OBJECT(stop);

    return PySlice_New(start, stop, Py_None);
}
NUITKA_MAY_BE_UNUSED static PyObject *MAKE_SLICEOBJ1(PyObject *stop) {
    CHECK_OBJECT(stop);

    return PySlice_New(Py_None, stop, Py_None);
}

#if PYTHON_VERSION < 0x300
// Note: It appears that Python3 has no index slicing operations anymore, but
// uses slice objects all the time. That's fine and make sure we adhere to it by
// guarding the presence of the helpers.

static inline bool IS_INDEXABLE(PyObject *value) {
    return value == Py_None ||
#if PYTHON_VERSION < 0x300
           PyInt_Check(value) ||
#endif
           PyLong_Check(value) || PyIndex_Check(value);
}

static Py_ssize_t CONVERT_TO_INDEX(PyObject *value) {
    CHECK_OBJECT(value);

    if (PyInt_Check(value)) {
        return PyInt_AS_LONG(value);
    } else if (PyIndex_Check(value)) {
        return PyNumber_AsSsize_t(value, NULL);
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError,
                                        "slice indices must be integers or None or have an __index__ method");
        return -1;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SLICE(PyObject *source, PyObject *lower, PyObject *upper) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(lower);
    CHECK_OBJECT(upper);

    PySequenceMethods *tp_as_sequence = Py_TYPE(source)->tp_as_sequence;

    if (tp_as_sequence && tp_as_sequence->sq_slice && IS_INDEXABLE(lower) && IS_INDEXABLE(upper)) {
        Py_ssize_t ilow = 0;

        if (lower != Py_None) {
            ilow = CONVERT_TO_INDEX(lower);

            if (ilow == -1 && ERROR_OCCURRED()) {
                return NULL;
            }
        }

        Py_ssize_t ihigh = PY_SSIZE_T_MAX;

        if (upper != Py_None) {
            ihigh = CONVERT_TO_INDEX(upper);

            if (ihigh == -1 && ERROR_OCCURRED()) {
                return NULL;
            }
        }

        PyObject *result = PySequence_GetSlice(source, ilow, ihigh);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    } else {
        PyObject *slice = PySlice_New(lower, upper, NULL);

        if (unlikely(slice == NULL)) {
            return NULL;
        }

        PyObject *result = PyObject_GetItem(source, slice);
        Py_DECREF(slice);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_INDEX_SLICE(PyObject *source, Py_ssize_t lower, Py_ssize_t upper) {
    CHECK_OBJECT(source);

    PyObject *result = PySequence_GetSlice(source, lower, upper);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static bool SET_SLICE(PyObject *target, PyObject *lower, PyObject *upper, PyObject *value) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(lower);
    CHECK_OBJECT(upper);
    CHECK_OBJECT(value);

    PySequenceMethods *tp_as_sequence = Py_TYPE(target)->tp_as_sequence;

    if (tp_as_sequence && tp_as_sequence->sq_ass_slice && IS_INDEXABLE(lower) && IS_INDEXABLE(upper)) {
        Py_ssize_t lower_int = 0;

        if (lower != Py_None) {
            lower_int = CONVERT_TO_INDEX(lower);

            if (lower_int == -1 && ERROR_OCCURRED()) {
                return false;
            }
        }

        Py_ssize_t upper_int = PY_SSIZE_T_MAX;

        if (upper != Py_None) {
            upper_int = CONVERT_TO_INDEX(upper);

            if (upper_int == -1 && ERROR_OCCURRED()) {
                return false;
            }
        }

        int status = PySequence_SetSlice(target, lower_int, upper_int, value);

        if (unlikely(status == -1)) {
            return false;
        }
    } else {
        PyObject *slice = PySlice_New(lower, upper, NULL);

        if (unlikely(slice == NULL)) {
            return false;
        }

        int status = PyObject_SetItem(target, slice, value);
        Py_DECREF(slice);

        if (unlikely(status == -1)) {
            return false;
        }
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static bool SET_INDEX_SLICE(PyObject *target, Py_ssize_t lower, Py_ssize_t upper,
                                                 PyObject *value) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(value);

    PySequenceMethods *tp_as_sequence = Py_TYPE(target)->tp_as_sequence;

    if (tp_as_sequence && tp_as_sequence->sq_ass_slice) {
        int status = PySequence_SetSlice(target, lower, upper, value);

        if (unlikely(status == -1)) {
            return false;
        }
    } else {
        PyObject *slice = _PySlice_FromIndices(lower, upper);

        if (unlikely(slice == NULL)) {
            return false;
        }

        int status = PyObject_SetItem(target, slice, value);

        Py_DECREF(slice);

        if (unlikely(status == -1)) {
            return false;
        }
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static bool DEL_SLICE(PyObject *target, PyObject *lower, PyObject *upper) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(lower);
    CHECK_OBJECT(upper);

    PySequenceMethods *tp_as_sequence = Py_TYPE(target)->tp_as_sequence;

    if (tp_as_sequence && tp_as_sequence->sq_ass_slice && IS_INDEXABLE(lower) && IS_INDEXABLE(upper)) {
        Py_ssize_t lower_int = 0;

        if (lower != Py_None) {
            lower_int = CONVERT_TO_INDEX(lower);

            if (lower_int == -1 && ERROR_OCCURRED()) {
                return false;
            }
        }

        Py_ssize_t upper_int = PY_SSIZE_T_MAX;

        if (upper != Py_None) {
            upper_int = CONVERT_TO_INDEX(upper);

            if (upper_int == -1 && ERROR_OCCURRED()) {
                return false;
            }
        }

        int status = PySequence_DelSlice(target, lower_int, upper_int);

        if (unlikely(status == -1)) {
            return false;
        }
    } else {
        PyObject *slice = PySlice_New(lower, upper, NULL);

        if (unlikely(slice == NULL)) {
            return false;
        }

        int status = PyObject_DelItem(target, slice);
        Py_DECREF(slice);

        if (unlikely(status == -1)) {
            return false;
        }
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static bool DEL_INDEX_SLICE(PyObject *target, Py_ssize_t lower, Py_ssize_t upper) {
    CHECK_OBJECT(target);

    PySequenceMethods *tp_as_sequence = Py_TYPE(target)->tp_as_sequence;

    if (tp_as_sequence && tp_as_sequence->sq_ass_slice) {
        int status = PySequence_DelSlice(target, lower, upper);

        if (unlikely(status == -1)) {
            return false;
        }
    } else {
        PyObject *slice = _PySlice_FromIndices(lower, upper);

        if (unlikely(slice == NULL)) {
            return false;
        }

        int status = PyObject_DelItem(target, slice);

        Py_DECREF(slice);

        if (unlikely(status == -1)) {
            return false;
        }
    }

    return true;
}

#endif

#endif
