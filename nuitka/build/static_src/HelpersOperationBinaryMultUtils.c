//     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* These slots are still manually coded and are used by the generated code.
 *
 * The plan should be to generate these as well, so e.g. we can have a slot
 * SLOT_nb_multiply_LONG_INT that is optimal too.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#include "longintrepr.h"

static Py_ssize_t CONVERT_LONG_TO_REPEAT_FACTOR(PyObject *value) {
    /* Inline PyLong_AsSsize_t here for our special purpose. */
    Py_ssize_t i = Py_SIZE(value);

    if (i == 0) {
        return 0;
    }

    PyLongObject *long_value = (PyLongObject *)value;

    if (i == 1) {
        return long_value->ob_digit[0];
    }

    Py_ssize_t result = 0;

    bool is_negative = i < 0;
    if (is_negative)
        i = -i;

    while (--i >= 0) {
        Py_ssize_t prev = result;
        result = (result << PyLong_SHIFT) | long_value->ob_digit[i];
        if ((result >> PyLong_SHIFT) != prev) {
            return (Py_ssize_t)-1;
        }
    }

    if (is_negative) {
        return 0;
    } else {
        return result;
    }
}

static Py_ssize_t CONVERT_TO_REPEAT_FACTOR(PyObject *value) {
#if PYTHON_VERSION < 300
    assert(PyInt_Check(value) || PyLong_Check(value));

    if (PyInt_Check(value)) {
        Py_ssize_t result = PyInt_AS_LONG(value);

        /* A -1 value could indicate error, so we avoid it. */
        if (result < 0) {
            return 0;
        } else {
            return result;
        }
    } else {
        return CONVERT_LONG_TO_REPEAT_FACTOR(value);
    }
#else
    /* For Python3 we know for a fact that it's a long, or else it's an
     * exception.
     */
    assert(PyLong_Check(value));

    return CONVERT_LONG_TO_REPEAT_FACTOR(value);
#endif
}

static PyObject *SEQUENCE_REPEAT(ssizeargfunc repeatfunc, PyObject *seq, PyObject *n) {
    if (unlikely(!PyIndex_Check(n))) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(n)->tp_name);

        return NULL;
    }

    PyObject *index_value = PyNumber_Index(n);

    if (unlikely(index_value == NULL)) {
        return NULL;
    }

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    Py_DECREF(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(n)->tp_name);
        return NULL;
    }

    PyObject *result = (*repeatfunc)(seq, count);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}
