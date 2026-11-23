//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

bool SEQUENCE_SET_ITEM(PyObject *sequence, Py_ssize_t index, PyObject *value) {
    CHECK_OBJECT(sequence);
    CHECK_OBJECT(value);

    PySequenceMethods *tp_as_sequence = Py_TYPE(sequence)->tp_as_sequence;

    if (tp_as_sequence != NULL && tp_as_sequence->sq_ass_item) {
        if (index < 0) {
            if (tp_as_sequence->sq_length) {
                Py_ssize_t length = (*tp_as_sequence->sq_length)(sequence);

                if (length < 0) {
                    return false;
                }

                index += length;
            }
        }

        int res = tp_as_sequence->sq_ass_item(sequence, index, value);

        if (unlikely(res == -1)) {
            return false;
        }

        return true;
    } else {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object does not support item assignment", sequence);
        return false;
    }
}

Py_ssize_t Nuitka_PyObject_Size(PyObject *sequence) {
    CHECK_OBJECT(sequence);

    PySequenceMethods *tp_as_sequence = Py_TYPE(sequence)->tp_as_sequence;

    if (tp_as_sequence && tp_as_sequence->sq_length) {
        return tp_as_sequence->sq_length(sequence);
    }

    return Nuitka_PyMapping_Size(sequence);
}

#if PYTHON_VERSION >= 0x270 && PYTHON_VERSION < 0x300
// Python 2.7's "PyInt_AsSsize_t" falls back to "__int__" for numbers that are
// neither "int" nor "long", with platform specific handling in CPython.
static Py_ssize_t _CONVERT_NUMBER_TO_SSIZE_T(PyThreadState *tstate, PyObject *value) {
    CHECK_OBJECT(value);

    if (PyInt_Check(value)) {
        return (Py_ssize_t)PyInt_AS_LONG(value);
    }

    if (PyLong_Check(value)) {
        return Nuitka_PyLong_AsSsize_t(tstate, value);
    }

    PyNumberMethods *number_methods = Py_TYPE(value)->tp_as_number;
    PyObject *int_value;

#if SIZEOF_SIZE_T == SIZEOF_LONG
    if (number_methods == NULL || number_methods->nb_int == NULL) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "an integer is required");
        return -1;
    }

    int_value = (*number_methods->nb_int)(value);
#else
    if (number_methods != NULL && number_methods->nb_long != NULL) {
        int_value = (*number_methods->nb_long)(value);
    } else if (number_methods != NULL && number_methods->nb_int != NULL) {
        int_value = (*number_methods->nb_int)(value);
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "an integer is required");
        return -1;
    }
#endif

    if (int_value == NULL) {
        return -1;
    }

    Py_ssize_t result;

    if (PyInt_Check(int_value)) {
        result = (Py_ssize_t)PyInt_AS_LONG(int_value);
    } else if (PyLong_Check(int_value)) {
        result = Nuitka_PyLong_AsSsize_t(tstate, int_value);
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__int__ method should return an integer");
        result = -1;
    }

    Py_DECREF(int_value);

    return result;
}
#endif

static bool checkAndClearLengthHintError(PyThreadState *tstate) {
#if PYTHON_VERSION < 0x300
    return CHECK_AND_CLEAR_TYPE_ERROR_OCCURRED(tstate) || CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate);
#else
    return CHECK_AND_CLEAR_TYPE_ERROR_OCCURRED(tstate);
#endif
}

// CPython's length hint API, matching "PyObject_LengthHint" from Python 3.4
// onwards and "_PyObject_LengthHint" before that, but implemented as Nuitka
// helper code instead of a call into the Python DLL.
Py_ssize_t Nuitka_PyObject_LengthHint(PyObject *sequence, Py_ssize_t default_value) {
    CHECK_OBJECT(sequence);

    PyThreadState *tstate = PyThreadState_GET();

    Py_ssize_t result = Nuitka_PyObject_Size(sequence);

    if (result >= 0) {
        return result;
    }

    if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
        if (!checkAndClearLengthHintError(tstate)) {
            return -1;
        }
    }
#if PYTHON_VERSION >= 0x300
    else {
        // CPython 3 does not try "__length_hint__" when "PyObject_Length" fails
        // without setting an exception.
        return -1;
    }
#endif

    PyObject *hint_method;

#if PYTHON_VERSION < 0x270
    // Python 2.6 looks up "__length_hint__" like any other attribute.
    hint_method = LOOKUP_ATTRIBUTE(tstate, sequence, const_str_plain___length_hint__);

    if (hint_method == NULL) {
        if (checkAndClearLengthHintError(tstate)) {
            return default_value;
        }

        return -1;
    }
#else
#if PYTHON_VERSION < 0x300
    // Python 2.7 does not use "__length_hint__" of old-style instances.
    if (PyInstance_Check(sequence)) {
        return default_value;
    }
#endif

    // Python 2.7 and 3.x look up "__length_hint__" on the type only.
    hint_method = LOOKUP_SPECIAL_NO_ERROR(sequence, const_str_plain___length_hint__);

    if (hint_method == NULL) {
        if (HAS_ERROR_OCCURRED(tstate)) {
            return -1;
        }

        return default_value;
    }
#endif

    PyObject *hint_value = CALL_FUNCTION_NO_ARGS(tstate, hint_method);
    Py_DECREF(hint_method);

    if (unlikely(hint_value == NULL)) {
        if (checkAndClearLengthHintError(tstate)) {
            return default_value;
        }

        return -1;
    }

#if PYTHON_VERSION < 0x270
    if (!PyLong_Check(hint_value)) {
        Py_DECREF(hint_value);
        return default_value;
    }

    result = Nuitka_PyLong_AsSsize_t(tstate, hint_value);
    Py_DECREF(hint_value);

    return result;
#elif PYTHON_VERSION < 0x300
    if (PyInt_Check(hint_value)) {
        result = (Py_ssize_t)PyInt_AS_LONG(hint_value);
    } else if (PyLong_Check(hint_value)) {
        result = Nuitka_PyLong_AsSsize_t(tstate, hint_value);
    } else {
        PyNumberMethods *number_methods = Py_TYPE(hint_value)->tp_as_number;

        if (number_methods != NULL && (number_methods->nb_int != NULL || number_methods->nb_float != NULL)) {
            result = _CONVERT_NUMBER_TO_SSIZE_T(tstate, hint_value);
        } else {
            result = default_value;
        }
    }

    Py_DECREF(hint_value);

    return result;
#else
    if (hint_value == Py_NotImplemented) {
        Py_DECREF(hint_value);
        return default_value;
    }

    if (unlikely(!PyLong_Check(hint_value))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__length_hint__ must be an integer, not %.100s", hint_value);
        Py_DECREF(hint_value);

        return -1;
    }

    result = Nuitka_PyLong_AsSsize_t(tstate, hint_value);
    Py_DECREF(hint_value);

    if (unlikely(result < 0)) {
        if (HAS_ERROR_OCCURRED(tstate)) {
            return -1;
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "__length_hint__() should return >= 0");

        return -1;
    }

    return result;
#endif
}

PyObject *Nuitka_Number_Index(PyObject *item) {
    CHECK_OBJECT(item);

#if PYTHON_VERSION < 0x300
    if (PyInt_Check(item) || PyLong_Check(item))
#else
    if (PyLong_Check(item))
#endif
    {
        Py_INCREF(item);
        return item;
    }

    if (unlikely(!Nuitka_Index_Check(item))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object cannot be interpreted as an integer", item);
        return NULL;
    }

    PyObject *result = Py_TYPE(item)->tp_as_number->nb_index(item);

#if PYTHON_VERSION < 0x300
    if (result == NULL || PyInt_CheckExact(result) || PyLong_CheckExact(result)) {
        return result;
    }
#else
    if (result == NULL || PyLong_CheckExact(result)) {
        return result;
    }
#endif

#if PYTHON_VERSION < 0x300
    if (!PyInt_Check(result) && !PyLong_Check(result))
#else
    if (!PyLong_Check(result))
#endif
    {
#if PYTHON_VERSION < 0x300
        char const *message = "__index__ returned non-(int,long) (type %s)";
#else
        char const *message = "__index__ returned non-int (type %s)";
#endif
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(message, result);

        Py_DECREF(result);
        return NULL;
    }

    return result;
}

// Our "PyNumber_AsSsize_t" replacement. It clips on overflow if "exc" is
// "NULL", otherwise it raises "exc" with the original item type in the message.
Py_ssize_t Nuitka_Number_AsSsize_t(PyObject *item, PyObject *exc) {
    CHECK_OBJECT(item);

    PyObject *index = Nuitka_Number_Index(item);

    if (unlikely(index == NULL)) {
        return -1;
    }

    Py_ssize_t result;

#if PYTHON_VERSION < 0x300
    if (PyInt_Check(index)) {
        result = (Py_ssize_t)PyInt_AS_LONG(index);
    } else
#endif
    {
        int overflow;
        result = Nuitka_PyLong_AsSsize_tAndOverflow(index, &overflow);

        if (unlikely(overflow != 0)) {
            Py_DECREF(index);

            if (exc == NULL) {
                return overflow < 0 ? PY_SSIZE_T_MIN : PY_SSIZE_T_MAX;
            }

            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(exc, "cannot fit '%s' into an index-sized integer",
                                                Py_TYPE(item)->tp_name);

            return -1;
        }
    }

    Py_DECREF(index);

    return result;
}

#if PYTHON_VERSION >= 0x3a0
PyObject *Nuitka_Number_IndexAsLong(PyObject *item) {
    PyObject *result = Nuitka_Number_Index(item);

    if (result == NULL || PyLong_CheckExact(result)) {
        return result;
    }

    PyObject *converted_long = _PyLong_Copy((PyLongObject *)result);
    Py_DECREF(result);

    return converted_long;
}
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
