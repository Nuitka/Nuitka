//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
 * The plan should be to generate these as well. Currently also naming is
 * very inconsistent.
 */

#if PYTHON_VERSION < 0x300
#include <stddef.h>

#define PyStringObject_SIZE (offsetof(PyStringObject, ob_sval) + 1)

NUITKA_MAY_BE_UNUSED static bool STRING_RESIZE(PyObject **value, Py_ssize_t newsize) {
    PyStringObject *sv;

    _Py_DEC_REFTOTAL;
    _Py_ForgetReference(*value);

    *value = (PyObject *)PyObject_REALLOC((char *)*value, PyStringObject_SIZE + newsize);

    if (unlikely(*value == NULL)) {
        PyErr_NoMemory();

        return false;
    }
    Nuitka_Py_NewReference(*value);

    sv = (PyStringObject *)*value;
    Py_SIZE(sv) = newsize;

    sv->ob_sval[newsize] = '\0';
    sv->ob_shash = -1;

    return true;
}

NUITKA_MAY_BE_UNUSED static bool STRING_ADD_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(PyString_CheckExact(*operand1));
    assert(!PyString_CHECK_INTERNED(*operand1));
    assert(PyString_CheckExact(operand2));

    Py_ssize_t operand1_size = PyString_GET_SIZE(*operand1);
    Py_ssize_t operand2_size = PyString_GET_SIZE(operand2);

    Py_ssize_t new_size = operand1_size + operand2_size;

    if (unlikely(new_size < 0)) {
        PyErr_Format(PyExc_OverflowError, "strings are too large to concat");

        return false;
    }

    if (unlikely(STRING_RESIZE(operand1, new_size) == false)) {
        return false;
    }

    memcpy(PyString_AS_STRING(*operand1) + operand1_size, PyString_AS_STRING(operand2), operand2_size);

    return true;
}
#endif

#if PYTHON_VERSION >= 0x300
NUITKA_MAY_BE_UNUSED static bool BYTES_ADD_INCREMENTAL(PyObject **operand1, PyObject *operand2) {
    assert(PyBytes_CheckExact(*operand1));
    assert(PyBytes_CheckExact(operand2));

    // Buffer of operand2
    Py_buffer wb;
    wb.len = -1;

    int res = PyObject_GetBuffer(operand2, &wb, PyBUF_SIMPLE);

    // Has to work.
    assert(res == 0);

    Py_ssize_t oldsize = PyBytes_GET_SIZE(*operand1);

    if (oldsize > PY_SSIZE_T_MAX - wb.len) {
        PyErr_NoMemory();
        PyBuffer_Release(&wb);
        return false;
    }
    if (_PyBytes_Resize(operand1, oldsize + wb.len) < 0) {
        PyBuffer_Release(&wb);
        return false;
    }

    memcpy(PyBytes_AS_STRING(*operand1) + oldsize, wb.buf, wb.len);
    PyBuffer_Release(&wb);
    return true;
}
#endif

NUITKA_MAY_BE_UNUSED static bool UNICODE_ADD_INCREMENTAL(PyObject **operand1, PyObject *operand2) {
    Py_ssize_t operand2_size = PyUnicode_GET_SIZE(operand2);
    if (operand2_size == 0)
        return true;

#if PYTHON_VERSION < 0x300
    Py_ssize_t operand1_size = PyUnicode_GET_SIZE(*operand1);

    Py_ssize_t new_size = operand1_size + operand2_size;

    if (unlikely(new_size < 0)) {
        PyErr_Format(PyExc_OverflowError, "strings are too large to concat");

        return false;
    }

    if (unlikely(PyUnicode_Resize(operand1, new_size) != 0)) {
        return false;
    }

    memcpy(PyUnicode_AS_UNICODE(*operand1) + operand1_size, PyUnicode_AS_UNICODE(operand2),
           operand2_size * sizeof(Py_UNICODE));

    return true;
#else
    assert(!PyUnicode_CHECK_INTERNED(*operand1));

    return UNICODE_APPEND(operand1, operand2);
#endif
}
