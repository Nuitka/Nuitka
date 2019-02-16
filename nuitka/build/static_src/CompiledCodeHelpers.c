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
/* Implementations of compiled code helpers.

 * The definition of a compiled code helper is that it's being used in
 * generated C code and provides part of the operations implementation.
 *
 * Currently we also have standalone mode related code here, patches to CPython
 * runtime that we do, and e.g. the built-in module. TODO: Move these to their
 * own files for clarity.
 */

#include "nuitka/prelude.h"

#include "HelpersBuiltin.c"
#include "HelpersClasses.c"
#include "HelpersHeapStorage.c"
#include "HelpersImport.c"
#include "HelpersPathTools.c"
#include "HelpersStrings.c"

#if PYTHON_VERSION < 300

static Py_ssize_t ESTIMATE_RANGE(long low, long high, long step) {
    if (low >= high) {
        return 0;
    } else {
        return (high - low - 1) / step + 1;
    }
}

static PyObject *_BUILTIN_RANGE_INT3(long low, long high, long step) {
    assert(step != 0);

    Py_ssize_t size;

    if (step > 0) {
        size = ESTIMATE_RANGE(low, high, step);
    } else {
        size = ESTIMATE_RANGE(high, low, -step);
    }

    PyObject *result = PyList_New(size);

    long current = low;

    for (int i = 0; i < size; i++) {
        PyList_SET_ITEM(result, i, PyInt_FromLong(current));
        current += step;
    }

    return result;
}

static PyObject *_BUILTIN_RANGE_INT2(long low, long high) { return _BUILTIN_RANGE_INT3(low, high, 1); }

static PyObject *_BUILTIN_RANGE_INT(long boundary) { return _BUILTIN_RANGE_INT2(0, boundary); }

static PyObject *TO_RANGE_ARG(PyObject *value, char const *name) {
    if (likely(PyInt_Check(value) || PyLong_Check(value))) {
        Py_INCREF(value);
        return value;
    }

    PyTypeObject *type = Py_TYPE(value);
    PyNumberMethods *tp_as_number = type->tp_as_number;

    // Everything that casts to int is allowed.
    if (
#if PYTHON_VERSION >= 270
        PyFloat_Check(value) ||
#endif
        tp_as_number == NULL || tp_as_number->nb_int == NULL) {
        PyErr_Format(PyExc_TypeError, "range() integer %s argument expected, got %s.", name, type->tp_name);
        return NULL;
    }

    PyObject *result = tp_as_number->nb_int(value);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}
#endif

#if PYTHON_VERSION < 300

NUITKA_DEFINE_BUILTIN(range);

PyObject *BUILTIN_RANGE(PyObject *boundary) {
    PyObject *boundary_temp = TO_RANGE_ARG(boundary, "end");

    if (unlikely(boundary_temp == NULL)) {
        return NULL;
    }

    long start = PyInt_AsLong(boundary_temp);

    if (start == -1 && ERROR_OCCURRED()) {
        CLEAR_ERROR_OCCURRED();

        NUITKA_ASSIGN_BUILTIN(range);

        PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(NUITKA_ACCESS_BUILTIN(range), boundary_temp);

        Py_DECREF(boundary_temp);

        return result;
    }
    Py_DECREF(boundary_temp);

    return _BUILTIN_RANGE_INT(start);
}

PyObject *BUILTIN_RANGE2(PyObject *low, PyObject *high) {
    PyObject *low_temp = TO_RANGE_ARG(low, "start");

    if (unlikely(low_temp == NULL)) {
        return NULL;
    }

    PyObject *high_temp = TO_RANGE_ARG(high, "end");

    if (unlikely(high_temp == NULL)) {
        Py_DECREF(low_temp);
        return NULL;
    }

    bool fallback = false;

    long start = PyInt_AsLong(low_temp);

    if (unlikely(start == -1 && ERROR_OCCURRED())) {
        CLEAR_ERROR_OCCURRED();
        fallback = true;
    }

    long end = PyInt_AsLong(high_temp);

    if (unlikely(end == -1 && ERROR_OCCURRED())) {
        CLEAR_ERROR_OCCURRED();
        fallback = true;
    }

    if (fallback) {
        PyObject *pos_args = PyTuple_New(2);
        PyTuple_SET_ITEM(pos_args, 0, low_temp);
        PyTuple_SET_ITEM(pos_args, 1, high_temp);

        NUITKA_ASSIGN_BUILTIN(range);

        PyObject *result = CALL_FUNCTION_WITH_POSARGS(NUITKA_ACCESS_BUILTIN(range), pos_args);

        Py_DECREF(pos_args);

        return result;
    } else {
        Py_DECREF(low_temp);
        Py_DECREF(high_temp);

        return _BUILTIN_RANGE_INT2(start, end);
    }
}

PyObject *BUILTIN_RANGE3(PyObject *low, PyObject *high, PyObject *step) {
    PyObject *low_temp = TO_RANGE_ARG(low, "start");

    if (unlikely(low_temp == NULL)) {
        return NULL;
    }

    PyObject *high_temp = TO_RANGE_ARG(high, "end");

    if (unlikely(high_temp == NULL)) {
        Py_DECREF(low_temp);
        return NULL;
    }

    PyObject *step_temp = TO_RANGE_ARG(step, "step");

    if (unlikely(high_temp == NULL)) {
        Py_DECREF(low_temp);
        Py_DECREF(high_temp);
        return NULL;
    }

    bool fallback = false;

    long start = PyInt_AsLong(low_temp);

    if (unlikely(start == -1 && ERROR_OCCURRED())) {
        CLEAR_ERROR_OCCURRED();
        fallback = true;
    }

    long end = PyInt_AsLong(high_temp);

    if (unlikely(end == -1 && ERROR_OCCURRED())) {
        CLEAR_ERROR_OCCURRED();
        fallback = true;
    }

    long step_long = PyInt_AsLong(step_temp);

    if (unlikely(step_long == -1 && ERROR_OCCURRED())) {
        CLEAR_ERROR_OCCURRED();
        fallback = true;
    }

    if (fallback) {
        PyObject *pos_args = PyTuple_New(3);
        PyTuple_SET_ITEM(pos_args, 0, low_temp);
        PyTuple_SET_ITEM(pos_args, 1, high_temp);
        PyTuple_SET_ITEM(pos_args, 2, step_temp);

        NUITKA_ASSIGN_BUILTIN(range);

        PyObject *result = CALL_FUNCTION_WITH_POSARGS(NUITKA_ACCESS_BUILTIN(range), pos_args);

        Py_DECREF(pos_args);

        return result;
    } else {
        Py_DECREF(low_temp);
        Py_DECREF(high_temp);
        Py_DECREF(step_temp);

        if (unlikely(step_long == 0)) {
            PyErr_Format(PyExc_ValueError, "range() step argument must not be zero");
            return NULL;
        }

        return _BUILTIN_RANGE_INT3(start, end, step_long);
    }
}

#endif

#if PYTHON_VERSION < 300

/* Same as CPython2: */
static unsigned long getLengthOfRange(long lo, long hi, long step) {
    assert(step != 0);

    if (step > 0 && lo < hi) {
        return 1UL + (hi - 1UL - lo) / step;
    } else if (step < 0 && lo > hi) {
        return 1UL + (lo - 1UL - hi) / (0UL - step);
    } else {
        return 0UL;
    }
}

/* Create a "xrange" object from C long values. Used for constant ranges. */
PyObject *MAKE_XRANGE(long start, long stop, long step) {
    /* TODO: It would be sweet to calculate that on user side already. */
    unsigned long n = getLengthOfRange(start, stop, step);

    if (n > (unsigned long)LONG_MAX || (long)n > PY_SSIZE_T_MAX) {
        PyErr_SetString(PyExc_OverflowError, "xrange() result has too many items");

        return NULL;
    }

    struct _rangeobject2 *result = (struct _rangeobject2 *)PyObject_New(struct _rangeobject2, &PyRange_Type);
    assert(result != NULL);

    result->start = start;
    result->len = (long)n;
    result->step = step;

    return (PyObject *)result;
}

#else

/* Same as CPython3: */
static PyObject *getLengthOfRange(PyObject *start, PyObject *stop, PyObject *step) {
    int res = PyObject_RichCompareBool(step, const_int_0, Py_GT);

    if (unlikely(res == -1)) {
        return NULL;
    }

    PyObject *lo, *hi;

    // Make sure we use step as a positive number.
    if (res == 1) {
        lo = start;
        hi = stop;

        Py_INCREF(step);
    } else {
        lo = stop;
        hi = start;

        step = PyNumber_Negative(step);

        if (unlikely(step == NULL)) {
            return NULL;
        }

        res = PyObject_RichCompareBool(step, const_int_0, Py_EQ);

        if (unlikely(res == -1)) {
            return NULL;
        }

        if (res == 1) {
            PyErr_Format(PyExc_ValueError, "range() arg 3 must not be zero");

            return NULL;
        }
    }

    // Negative difference, we got zero length.
    res = PyObject_RichCompareBool(lo, hi, Py_GE);

    if (res != 0) {
        Py_XDECREF(step);

        if (res < 0) {
            return NULL;
        }

        Py_INCREF(const_int_0);
        return const_int_0;
    }

    PyObject *tmp1 = PyNumber_Subtract(hi, lo);

    if (unlikely(tmp1 == NULL)) {
        Py_DECREF(step);
        return NULL;
    }

    PyObject *diff = PyNumber_Subtract(tmp1, const_int_pos_1);
    Py_DECREF(tmp1);

    if (unlikely(diff == NULL)) {
        Py_DECREF(step);
        Py_DECREF(tmp1);

        return NULL;
    }

    tmp1 = PyNumber_FloorDivide(diff, step);
    Py_DECREF(diff);
    Py_DECREF(step);

    if (unlikely(tmp1 == NULL)) {
        return NULL;
    }

    PyObject *result = PyNumber_Add(tmp1, const_int_pos_1);
    Py_DECREF(tmp1);

    return result;
}

static PyObject *MAKE_XRANGE(PyObject *start, PyObject *stop, PyObject *step) {
    start = PyNumber_Index(start);
    if (unlikely(start == NULL)) {
        return NULL;
    }
    stop = PyNumber_Index(stop);
    if (unlikely(stop == NULL)) {
        return NULL;
    }
    step = PyNumber_Index(step);
    if (unlikely(step == NULL)) {
        return NULL;
    }

    PyObject *length = getLengthOfRange(start, stop, step);
    if (unlikely(length == NULL)) {
        return NULL;
    }

    struct _rangeobject3 *result = (struct _rangeobject3 *)PyObject_New(struct _rangeobject3, &PyRange_Type);
    assert(result != NULL);

    result->start = start;
    result->stop = stop;
    result->step = step;
    result->length = length;

    return (PyObject *)result;
}
#endif

/* Built-in xrange (Python2) or xrange (Python3) with one argument. */
PyObject *BUILTIN_XRANGE1(PyObject *high) {
#if PYTHON_VERSION < 300
    if (unlikely(PyFloat_Check(high))) {
        PyErr_SetString(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_high = PyInt_AsLong(high);

    if (unlikely(int_high == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    return MAKE_XRANGE(0, int_high, 1);
#else
    PyObject *stop = PyNumber_Index(high);

    if (unlikely(stop == NULL)) {
        return NULL;
    }

    struct _rangeobject3 *result = (struct _rangeobject3 *)PyObject_New(struct _rangeobject3, &PyRange_Type);
    assert(result != NULL);

    result->start = const_int_0;
    Py_INCREF(const_int_0);
    result->stop = stop;
    result->step = const_int_pos_1;
    Py_INCREF(const_int_pos_1);

    result->length = stop;
    Py_INCREF(stop);

    return (PyObject *)result;
#endif
}

/* Built-in xrange (Python2) or xrange (Python3) with two arguments. */
PyObject *BUILTIN_XRANGE2(PyObject *low, PyObject *high) {
#if PYTHON_VERSION < 300
    if (unlikely(PyFloat_Check(low))) {
        PyErr_SetString(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_low = PyInt_AsLong(low);

    if (unlikely(int_low == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(high))) {
        PyErr_SetString(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_high = PyInt_AsLong(high);

    if (unlikely(int_high == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    return MAKE_XRANGE(int_low, int_high, 1);
#else
    return MAKE_XRANGE(low, high, const_int_pos_1);
#endif
}

/* Built-in xrange (Python2) or xrange (Python3) with three arguments. */
PyObject *BUILTIN_XRANGE3(PyObject *low, PyObject *high, PyObject *step) {
#if PYTHON_VERSION < 300
    if (unlikely(PyFloat_Check(low))) {
        PyErr_SetString(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_low = PyInt_AsLong(low);

    if (unlikely(int_low == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(high))) {
        PyErr_SetString(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_high = PyInt_AsLong(high);

    if (unlikely(int_high == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(step))) {
        PyErr_SetString(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_step = PyInt_AsLong(step);

    if (unlikely(int_step == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(int_step == 0)) {
        PyErr_Format(PyExc_ValueError, "range() arg 3 must not be zero");

        return NULL;
    }

    return MAKE_XRANGE(int_low, int_high, int_step);
#else
    return MAKE_XRANGE(low, high, step);
#endif
}

PyObject *BUILTIN_LEN(PyObject *value) {
    CHECK_OBJECT(value);

    Py_ssize_t res = PyObject_Size(value);

    if (unlikely(res < 0 && ERROR_OCCURRED())) {
        return NULL;
    }

    return PyInt_FromSsize_t(res);
}

NUITKA_DEFINE_BUILTIN(format);

PyObject *BUILTIN_FORMAT(PyObject *value, PyObject *format_spec) {
    CHECK_OBJECT(value);
    CHECK_OBJECT(format_spec);

    NUITKA_ASSIGN_BUILTIN(format);

    PyObject *args[2] = {value, format_spec};

    return CALL_FUNCTION_WITH_ARGS2(NUITKA_ACCESS_BUILTIN(format), args);
}

// Helper functions for print. Need to play nice with Python softspace
// behaviour.

#if PYTHON_VERSION >= 300
extern PyObject *const_str_plain_end;
extern PyObject *const_str_plain_file;
extern PyObject *const_str_empty;

NUITKA_DEFINE_BUILTIN(print);
#endif

bool PRINT_NEW_LINE_TO(PyObject *file) {
#if PYTHON_VERSION < 300
    if (file == NULL || file == Py_None) {
        file = GET_STDOUT();
    }

    // need to hold a reference to the file or else __getattr__ may release
    // "file" in the mean time.
    Py_INCREF(file);

    if (unlikely(PyFile_WriteString("\n", file) == -1)) {
        Py_DECREF(file);
        return false;
    }

    PyFile_SoftSpace(file, 0);
    CHECK_OBJECT(file);

    Py_DECREF(file);
    return true;
#else
    NUITKA_ASSIGN_BUILTIN(print);

    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;

    FETCH_ERROR_OCCURRED_UNTRACED(&exception_type, &exception_value, &exception_tb);

    PyObject *result;

    if (likely(file == NULL)) {
        result = CALL_FUNCTION_NO_ARGS(NUITKA_ACCESS_BUILTIN(print));
    } else {
        PyObject *kw_args = PyDict_New();
        PyDict_SetItem(kw_args, const_str_plain_file, GET_STDOUT());

        result = CALL_FUNCTION_WITH_KEYARGS(NUITKA_ACCESS_BUILTIN(print), kw_args);

        Py_DECREF(kw_args);
    }

    Py_XDECREF(result);

    RESTORE_ERROR_OCCURRED_UNTRACED(exception_type, exception_value, exception_tb);

    return result != NULL;
#endif
}

bool PRINT_ITEM_TO(PyObject *file, PyObject *object) {
// The print built-in function cannot replace "softspace" behavior of CPython
// print statement, so this code is really necessary.
#if PYTHON_VERSION < 300
    if (file == NULL || file == Py_None) {
        file = GET_STDOUT();
    }

    CHECK_OBJECT(file);
    CHECK_OBJECT(object);

    // need to hold a reference to the file or else "__getattr__" code may
    // release "file" in the mean time.
    Py_INCREF(file);

    // Check for soft space indicator
    if (PyFile_SoftSpace(file, 0)) {
        if (unlikely(PyFile_WriteString(" ", file) == -1)) {
            Py_DECREF(file);
            return false;
        }
    }

    if (unlikely(PyFile_WriteObject(object, file, Py_PRINT_RAW) == -1)) {
        Py_DECREF(file);
        return false;
    }

    if (PyString_Check(object)) {
        char *buffer;
        Py_ssize_t length;

#ifndef __NUITKA_NO_ASSERT__
        int status =
#endif
            PyString_AsStringAndSize(object, &buffer, &length);
        assert(status != -1);

        if (length == 0 || !isspace(Py_CHARMASK(buffer[length - 1])) || buffer[length - 1] == ' ') {
            PyFile_SoftSpace(file, 1);
        }
    } else if (PyUnicode_Check(object)) {
        Py_UNICODE *buffer = PyUnicode_AS_UNICODE(object);
        Py_ssize_t length = PyUnicode_GET_SIZE(object);

        if (length == 0 || !Py_UNICODE_ISSPACE(buffer[length - 1]) || buffer[length - 1] == ' ') {
            PyFile_SoftSpace(file, 1);
        }
    } else {
        PyFile_SoftSpace(file, 1);
    }

    CHECK_OBJECT(file);
    Py_DECREF(file);

    return true;
#else
    NUITKA_ASSIGN_BUILTIN(print);

    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;

    FETCH_ERROR_OCCURRED_UNTRACED(&exception_type, &exception_value, &exception_tb);

    PyObject *result;

    if (likely(file == NULL)) {
        result = CALL_FUNCTION_WITH_SINGLE_ARG(NUITKA_ACCESS_BUILTIN(print), object);
    } else {
        PyObject *print_kw = PyDict_New();
        PyDict_SetItem(print_kw, const_str_plain_end, const_str_empty);
        PyDict_SetItem(print_kw, const_str_plain_file, GET_STDOUT());

        PyObject *print_args = PyTuple_New(1);
        PyTuple_SET_ITEM(print_args, 0, object);
        Py_INCREF(object);

        result = CALL_FUNCTION(NUITKA_ACCESS_BUILTIN(print), print_args, print_kw);

        Py_DECREF(print_args);
        Py_DECREF(print_kw);
    }

    Py_XDECREF(result);

    RESTORE_ERROR_OCCURRED_UNTRACED(exception_type, exception_value, exception_tb);

    return result != NULL;
#endif
}

void PRINT_REFCOUNT(PyObject *object) {
    char buffer[1024];
    snprintf(buffer, sizeof(buffer) - 1, " refcnt %" PY_FORMAT_SIZE_T "d ", Py_REFCNT(object));

    PRINT_STRING(buffer);
}

bool PRINT_STRING(char const *str) {
    PyObject *tmp = PyUnicode_FromString(str);
    bool res = PRINT_ITEM(tmp);
    Py_DECREF(tmp);

    return res;
}

bool PRINT_REPR(PyObject *object) {
    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;

    FETCH_ERROR_OCCURRED_UNTRACED(&exception_type, &exception_value, &exception_tb);

    bool res;

    if (object != NULL) {
        CHECK_OBJECT(object);

        // Cannot have error set for this function, it asserts against that
        // in debug builds.
        PyObject *repr = PyObject_Repr(object);

        res = PRINT_ITEM(repr);
        Py_DECREF(repr);
    } else {
        res = PRINT_NULL();
    }

    RESTORE_ERROR_OCCURRED_UNTRACED(exception_type, exception_value, exception_tb);

    return res;
}

bool PRINT_NULL(void) { return PRINT_STRING("<NULL>"); }

void PRINT_EXCEPTION(PyObject *exception_type, PyObject *exception_value, PyObject *exception_tb) {
    PRINT_REPR(exception_type);
    PRINT_STRING("|");
    PRINT_REPR(exception_value);
#if PYTHON_VERSION >= 300
    if (exception_value != NULL) {
        PRINT_STRING(" <- ");
        PRINT_REPR(PyException_GetContext(exception_value));
    }
#endif
    PRINT_STRING("|");
    PRINT_REPR(exception_tb);

    PRINT_NEW_LINE();
}

void PRINT_CURRENT_EXCEPTION(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PRINT_EXCEPTION(tstate->curexc_type, tstate->curexc_value, tstate->curexc_traceback);
}

void PRINT_PUBLISHED_EXCEPTION(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PRINT_EXCEPTION(EXC_TYPE(tstate), EXC_VALUE(tstate), EXC_TRACEBACK(tstate));
}

// TODO: Could be ported, the "printf" stuff would need to be split. On Python3
// the normal C print output gets lost.
#if PYTHON_VERSION < 300
void PRINT_TRACEBACK(PyTracebackObject *traceback) {
    PRINT_STRING("Dumping traceback:\n");

    if (traceback == NULL)
        PRINT_STRING("<NULL traceback?!>\n");

    while (traceback) {
        printf(" line %d (frame object chain):\n", traceback->tb_lineno);

        PyFrameObject *frame = traceback->tb_frame;

        while (frame) {
            printf("  Frame at %s\n", PyString_AsString(PyObject_Str((PyObject *)frame->f_code)));

            frame = frame->f_back;
        }

        assert(traceback->tb_next != traceback);
        traceback = traceback->tb_next;
    }

    PRINT_STRING("End of Dump.\n");
}
#endif

PyObject *GET_STDOUT() {
    PyObject *result = PySys_GetObject((char *)"stdout");

    if (unlikely(result == NULL)) {
        PyErr_Format(PyExc_RuntimeError, "lost sys.stdout");
        return NULL;
    }

    return result;
}

PyObject *GET_STDERR() {
    PyObject *result = PySys_GetObject((char *)"stderr");

    if (unlikely(result == NULL)) {
        PyErr_Format(PyExc_RuntimeError, "lost sys.stderr");
        return NULL;
    }

    return result;
}

bool PRINT_NEW_LINE(void) {
    PyObject *target = GET_STDOUT();

    return target != NULL && PRINT_NEW_LINE_TO(target);
}

bool PRINT_ITEM(PyObject *object) {
    if (object == NULL) {
        return PRINT_NULL();
    } else {
        PyObject *target = GET_STDOUT();

        return target != NULL && PRINT_ITEM_TO(target, object);
    }
}

#if PYTHON_VERSION < 300
PyObject *UNSTREAM_UNICODE(unsigned char const *buffer, Py_ssize_t size) {
    PyObject *result = PyUnicode_FromStringAndSize((char const *)buffer, size);

    assert(!ERROR_OCCURRED());
    CHECK_OBJECT(result);

    return result;
}
#endif

PyObject *UNSTREAM_STRING(unsigned char const *buffer, Py_ssize_t size, bool intern) {
#if PYTHON_VERSION < 300
    PyObject *result = PyString_FromStringAndSize((char const *)buffer, size);
#else
    PyObject *result = PyUnicode_FromStringAndSize((char const *)buffer, size);
#endif

    assert(!ERROR_OCCURRED());
    CHECK_OBJECT(result);
    assert(Nuitka_String_Check(result));

#if PYTHON_VERSION < 300
    assert(PyString_Size(result) == size);
#endif

    if (intern) {
        Nuitka_StringIntern(&result);

        CHECK_OBJECT(result);
        assert(Nuitka_String_Check(result));

#if PYTHON_VERSION < 300
        assert(PyString_Size(result) == size);
#else
        assert(PyUnicode_GET_SIZE(result) == size);
#endif
    }

    return result;
}

#if PYTHON_VERSION >= 300
PyObject *UNSTREAM_STRING_ASCII(unsigned char const *buffer, Py_ssize_t size, bool intern) {
    PyObject *result = PyUnicode_FromKindAndData(PyUnicode_1BYTE_KIND, (char const *)buffer, size);

    assert(!ERROR_OCCURRED());
    CHECK_OBJECT(result);
    assert(Nuitka_String_Check(result));

    if (intern) {
        Nuitka_StringIntern(&result);

        CHECK_OBJECT(result);
        assert(Nuitka_String_Check(result));

        assert(PyUnicode_GET_SIZE(result) == size);
    }

    return result;
}
#endif

PyObject *UNSTREAM_CHAR(unsigned char value, bool intern) {
#if PYTHON_VERSION < 300
    PyObject *result = PyString_FromStringAndSize((char const *)&value, 1);
#else
    PyObject *result = PyUnicode_FromStringAndSize((char const *)&value, 1);
#endif

    assert(!ERROR_OCCURRED());
    CHECK_OBJECT(result);
    assert(Nuitka_String_Check(result));

#if PYTHON_VERSION < 300
    assert(PyString_Size(result) == 1);
#else
    assert(PyUnicode_GET_SIZE(result) == 1);
#endif

    if (intern) {
        Nuitka_StringIntern(&result);

        CHECK_OBJECT(result);
        assert(Nuitka_String_Check(result));

#if PYTHON_VERSION < 300
        assert(PyString_Size(result) == 1);
#else
        assert(PyUnicode_GET_SIZE(result) == 1);
#endif
    }

    return result;
}

PyObject *UNSTREAM_FLOAT(unsigned char const *buffer) {
    double x = _PyFloat_Unpack8(buffer, 1);
    assert(x != -1.0 || !PyErr_Occurred());

    PyObject *result = PyFloat_FromDouble(x);
    assert(result != NULL);

    return result;
}

#if PYTHON_VERSION >= 300
PyObject *UNSTREAM_BYTES(unsigned char const *buffer, Py_ssize_t size) {
    PyObject *result = PyBytes_FromStringAndSize((char const *)buffer, size);
    assert(!ERROR_OCCURRED());
    CHECK_OBJECT(result);

    assert(PyBytes_GET_SIZE(result) == size);
    return result;
}
#endif

PyObject *UNSTREAM_BYTEARRAY(unsigned char const *buffer, Py_ssize_t size) {
    PyObject *result = PyByteArray_FromStringAndSize((char const *)buffer, size);
    assert(!ERROR_OCCURRED());
    CHECK_OBJECT(result);

    assert(PyByteArray_GET_SIZE(result) == size);
    return result;
}

#if PYTHON_VERSION < 300

static void set_slot(PyObject **slot, PyObject *value) {
    PyObject *temp = *slot;
    Py_XINCREF(value);
    *slot = value;
    Py_XDECREF(temp);
}

extern PyObject *const_str_plain___getattr__;
extern PyObject *const_str_plain___setattr__;
extern PyObject *const_str_plain___delattr__;

static void set_attr_slots(PyClassObject *klass) {
    set_slot(&klass->cl_getattr, FIND_ATTRIBUTE_IN_CLASS(klass, const_str_plain___getattr__));
    set_slot(&klass->cl_setattr, FIND_ATTRIBUTE_IN_CLASS(klass, const_str_plain___setattr__));
    set_slot(&klass->cl_delattr, FIND_ATTRIBUTE_IN_CLASS(klass, const_str_plain___delattr__));
}

static bool set_dict(PyClassObject *klass, PyObject *value) {
    if (value == NULL || !PyDict_Check(value)) {
        PyErr_SetString(PyExc_TypeError, (char *)"__dict__ must be a dictionary object");
        return false;
    } else {
        set_slot(&klass->cl_dict, value);
        set_attr_slots(klass);

        return true;
    }
}

static bool set_bases(PyClassObject *klass, PyObject *value) {
    if (value == NULL || !PyTuple_Check(value)) {
        PyErr_SetString(PyExc_TypeError, (char *)"__bases__ must be a tuple object");
        return false;
    } else {
        Py_ssize_t n = PyTuple_Size(value);

        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *base = PyTuple_GET_ITEM(value, i);

            if (unlikely(!PyClass_Check(base))) {
                PyErr_SetString(PyExc_TypeError, (char *)"__bases__ items must be classes");
                return false;
            }

            if (unlikely(PyClass_IsSubclass(base, (PyObject *)klass))) {
                PyErr_SetString(PyExc_TypeError, (char *)"a __bases__ item causes an inheritance cycle");
                return false;
            }
        }

        set_slot(&klass->cl_bases, value);
        set_attr_slots(klass);

        return true;
    }
}

static bool set_name(PyClassObject *klass, PyObject *value) {
    if (value == NULL || !PyDict_Check(value)) {
        PyErr_SetString(PyExc_TypeError, (char *)"__name__ must be a string object");
        return false;
    }

    if (strlen(PyString_AS_STRING(value)) != (size_t)PyString_GET_SIZE(value)) {
        PyErr_SetString(PyExc_TypeError, (char *)"__name__ must not contain null bytes");
        return false;
    }

    set_slot(&klass->cl_name, value);
    return true;
}

static int nuitka_class_setattr(PyClassObject *klass, PyObject *attr_name, PyObject *value) {
    char *sattr_name = PyString_AsString(attr_name);

    if (sattr_name[0] == '_' && sattr_name[1] == '_') {
        Py_ssize_t n = PyString_Size(attr_name);

        if (sattr_name[n - 2] == '_' && sattr_name[n - 1] == '_') {
            if (strcmp(sattr_name, "__dict__") == 0) {
                if (set_dict(klass, value) == false) {
                    return -1;
                } else {
                    return 0;
                }
            } else if (strcmp(sattr_name, "__bases__") == 0) {
                if (set_bases(klass, value) == false) {
                    return -1;
                } else {
                    return 0;
                }
            } else if (strcmp(sattr_name, "__name__") == 0) {
                if (set_name(klass, value) == false) {
                    return -1;
                } else {
                    return 0;
                }
            } else if (strcmp(sattr_name, "__getattr__") == 0) {
                set_slot(&klass->cl_getattr, value);
            } else if (strcmp(sattr_name, "__setattr__") == 0) {
                set_slot(&klass->cl_setattr, value);
            } else if (strcmp(sattr_name, "__delattr__") == 0) {
                set_slot(&klass->cl_delattr, value);
            }
        }
    }

    if (value == NULL) {
        int status = PyDict_DelItem(klass->cl_dict, attr_name);

        if (status < 0) {
            PyErr_Format(PyExc_AttributeError, "class %s has no attribute '%s'", PyString_AS_STRING(klass->cl_name),
                         sattr_name);
        }

        return status;
    } else {
        return PyDict_SetItem(klass->cl_dict, attr_name, value);
    }
}

static PyObject *nuitka_class_getattr(PyClassObject *klass, PyObject *attr_name) {
    char *sattr_name = PyString_AsString(attr_name);

    if (sattr_name[0] == '_' && sattr_name[1] == '_') {
        if (strcmp(sattr_name, "__dict__") == 0) {
            Py_INCREF(klass->cl_dict);
            return klass->cl_dict;
        } else if (strcmp(sattr_name, "__bases__") == 0) {
            Py_INCREF(klass->cl_bases);
            return klass->cl_bases;
        } else if (strcmp(sattr_name, "__name__") == 0) {
            if (klass->cl_name == NULL) {
                Py_INCREF(Py_None);
                return Py_None;
            } else {
                Py_INCREF(klass->cl_name);
                return klass->cl_name;
            }
        }
    }

    PyObject *value = FIND_ATTRIBUTE_IN_CLASS(klass, attr_name);

    if (unlikely(value == NULL)) {
        PyErr_Format(PyExc_AttributeError, "class %s has no attribute '%s'", PyString_AS_STRING(klass->cl_name),
                     sattr_name);
        return NULL;
    }

    PyTypeObject *type = Py_TYPE(value);

    descrgetfunc tp_descr_get = PyType_HasFeature(type, Py_TPFLAGS_HAVE_CLASS) ? type->tp_descr_get : NULL;

    if (tp_descr_get == NULL) {
        Py_INCREF(value);
        return value;
    } else {
        return tp_descr_get(value, (PyObject *)NULL, (PyObject *)klass);
    }
}

#endif

void enhancePythonTypes(void) {
#if PYTHON_VERSION < 300
    // Our own variant won't call PyEval_GetRestricted, saving quite some cycles
    // not doing that.
    PyClass_Type.tp_setattro = (setattrofunc)nuitka_class_setattr;
    PyClass_Type.tp_getattro = (getattrofunc)nuitka_class_getattr;
#endif
}

#ifdef __APPLE__
#ifdef __cplusplus
extern "C"
#endif
    wchar_t *
    _Py_DecodeUTF8_surrogateescape(const char *s, Py_ssize_t size);
#endif

#ifdef __FreeBSD__
#include <floatingpoint.h>
#endif

#include <locale.h>

#if PYTHON_VERSION >= 300
argv_type_t convertCommandLineParameters(int argc, char **argv) {
#if _WIN32
    int new_argc;

    argv_type_t result = CommandLineToArgvW(GetCommandLineW(), &new_argc);
    assert(new_argc == argc);
    return result;
#else
    // Originally taken from CPython3: There seems to be no sane way to use
    static wchar_t **argv_copy;
    argv_copy = (wchar_t **)PyMem_Malloc(sizeof(wchar_t *) * argc);

    // Temporarily disable locale for conversions to not use it.
    char *oldloc = strdup(setlocale(LC_ALL, NULL));
    setlocale(LC_ALL, "");

    for (int i = 0; i < argc; i++) {
#ifdef __APPLE__
        argv_copy[i] = _Py_DecodeUTF8_surrogateescape(argv[i], strlen(argv[i]));
#elif PYTHON_VERSION < 350
        argv_copy[i] = _Py_char2wchar(argv[i], NULL);
#else
        argv_copy[i] = Py_DecodeLocale(argv[i], NULL);
#endif

        assert(argv_copy[i]);
    }

    setlocale(LC_ALL, oldloc);
    free(oldloc);

    return argv_copy;
#endif
}
#endif

bool setCommandLineParameters(int argc, argv_type_t argv, bool initial) {
    bool is_multiprocessing_fork = false;

    if (initial) {
        /* We might need to skip what multiprocessing has told us. */
        for (int i = 1; i < argc; i++) {
#if PYTHON_VERSION < 300
            if ((strcmp(argv[i], "--multiprocessing-fork")) == 0 && (i + 1 < argc))
#else
            wchar_t constant_buffer[100];
            mbstowcs(constant_buffer, "--multiprocessing-fork", 100);
            if ((wcscmp(argv[i], constant_buffer)) == 0 && (i + 1 < argc))
#endif
            {
                is_multiprocessing_fork = true;
                break;
            }
        }
    }

    if (initial) {
        Py_SetProgramName(argv[0]);
    } else {
        PySys_SetArgv(argc, argv);
    }

    return is_multiprocessing_fork;
}

PyObject *original_isinstance = NULL;

// Note: Installed and used by "InspectPatcher" as "instance" too.
int Nuitka_IsInstance(PyObject *inst, PyObject *cls) {
    CHECK_OBJECT(original_isinstance);
    CHECK_OBJECT(inst);
    CHECK_OBJECT(cls);

    // Quick paths
    if (Py_TYPE(inst) == (PyTypeObject *)cls) {
        return true;
    }

    // Our paths for the types we need to hook.
    if (cls == (PyObject *)&PyFunction_Type && Nuitka_Function_Check(inst)) {
        return true;
    }

    if (cls == (PyObject *)&PyGen_Type && Nuitka_Generator_Check(inst)) {
        return true;
    }

    if (cls == (PyObject *)&PyMethod_Type && Nuitka_Method_Check(inst)) {
        return true;
    }

    if (cls == (PyObject *)&PyFrame_Type && Nuitka_Frame_Check(inst)) {
        return true;
    }

#if PYTHON_VERSION >= 350
    if (cls == (PyObject *)&PyCoro_Type && Nuitka_Coroutine_Check(inst)) {
        return true;
    }
#endif

#if PYTHON_VERSION >= 360
    if (cls == (PyObject *)&PyAsyncGen_Type && Nuitka_Asyncgen_Check(inst)) {
        return true;
    }
#endif

    // May need to be recursive for tuple arguments.
    if (PyTuple_Check(cls)) {
        for (Py_ssize_t i = 0, size = PyTuple_GET_SIZE(cls); i < size; i++) {
            PyObject *element = PyTuple_GET_ITEM(cls, i);

            if (unlikely(Py_EnterRecursiveCall((char *)" in __instancecheck__"))) {
                return -1;
            }

            int res = Nuitka_IsInstance(inst, element);

            Py_LeaveRecursiveCall();

            if (res != 0) {
                return res;
            }
        }

        return 0;
    } else {
        PyObject *args[] = {inst, cls};
        PyObject *result = CALL_FUNCTION_WITH_ARGS2(original_isinstance, args);

        if (result == NULL) {
            return -1;
        }

        int res = CHECK_IF_TRUE(result);
        Py_DECREF(result);

        if (res == 0) {
            if (cls == (PyObject *)&PyFunction_Type) {
                args[1] = (PyObject *)&Nuitka_Function_Type;
            } else if (cls == (PyObject *)&PyMethod_Type) {
                args[1] = (PyObject *)&Nuitka_Method_Type;
            } else if (cls == (PyObject *)&PyFrame_Type) {
                args[1] = (PyObject *)&Nuitka_Frame_Type;
            }
#if PYTHON_VERSION >= 350
            else if (cls == (PyObject *)&PyCoro_Type) {
                args[1] = (PyObject *)&Nuitka_Coroutine_Type;
            }
#endif
#if PYTHON_VERSION >= 360
            else if (cls == (PyObject *)&PyAsyncGen_Type) {
                args[1] = (PyObject *)&Nuitka_Asyncgen_Type;
            }
#endif
            else {
                return 0;
            }

            result = CALL_FUNCTION_WITH_ARGS2(original_isinstance, args);

            if (result == NULL) {
                return -1;
            }

            res = CHECK_IF_TRUE(result);
            Py_DECREF(result);
        }

        return res;
    }
}

#define ITERATOR_GENERIC 0
#define ITERATOR_COMPILED_GENERATOR 1
#define ITERATOR_TUPLE 2
#define ITERATOR_LIST 3

struct Nuitka_QuickIterator {
    int iterator_mode;

    union {
        // ITERATOR_GENERIC
        PyObject *iter;

        // ITERATOR_COMPILED_GENERATOR
        struct Nuitka_GeneratorObject *generator;

        // ITERATOR_TUPLE
        struct {
            PyTupleObject *tuple;
            Py_ssize_t tuple_index;
        } tuple_data;

        // ITERATOR_LIST
        struct {
            PyListObject *list;
            Py_ssize_t list_index;
        } list_data;
    } iterator_data;
};

static bool MAKE_QUICK_ITERATOR(PyObject *sequence, struct Nuitka_QuickIterator *qiter) {
    if (Nuitka_Generator_Check(sequence)) {
        qiter->iterator_mode = ITERATOR_COMPILED_GENERATOR;
        qiter->iterator_data.generator = (struct Nuitka_GeneratorObject *)sequence;
    } else if (PyTuple_CheckExact(sequence)) {
        qiter->iterator_mode = ITERATOR_TUPLE;
        qiter->iterator_data.tuple_data.tuple = (PyTupleObject *)sequence;
        qiter->iterator_data.tuple_data.tuple_index = 0;
    } else if (PyList_CheckExact(sequence)) {
        qiter->iterator_mode = ITERATOR_LIST;
        qiter->iterator_data.list_data.list = (PyListObject *)sequence;
        qiter->iterator_data.list_data.list_index = 0;
    } else {
        qiter->iterator_mode = ITERATOR_GENERIC;

        qiter->iterator_data.iter = MAKE_ITERATOR(sequence);
        if (unlikely(qiter->iterator_data.iter == NULL)) {
            return false;
        }
    }

    return true;
}

static PyObject *QUICK_ITERATOR_NEXT(struct Nuitka_QuickIterator *qiter, bool *finished) {
    PyObject *result;

    switch (qiter->iterator_mode) {
    case ITERATOR_GENERIC:
        result = ITERATOR_NEXT(qiter->iterator_data.iter);

        if (result == NULL) {
            Py_DECREF(qiter->iterator_data.iter);

            if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED())) {
                *finished = false;
                return NULL;
            }

            *finished = true;
            return NULL;
        }

        *finished = false;
        return result;
    case ITERATOR_COMPILED_GENERATOR:
        result = Nuitka_Generator_qiter(qiter->iterator_data.generator, finished);

        return result;
    case ITERATOR_TUPLE:
        if (qiter->iterator_data.tuple_data.tuple_index < PyTuple_GET_SIZE(qiter->iterator_data.tuple_data.tuple)) {
            result =
                PyTuple_GET_ITEM(qiter->iterator_data.tuple_data.tuple, qiter->iterator_data.tuple_data.tuple_index);
            qiter->iterator_data.tuple_data.tuple_index += 1;

            *finished = false;

            Py_INCREF(result);
            return result;
        } else {
            *finished = true;
            return NULL;
        }
    case ITERATOR_LIST:
        if (qiter->iterator_data.list_data.list_index < PyList_GET_SIZE(qiter->iterator_data.list_data.list)) {
            result = PyList_GET_ITEM(qiter->iterator_data.list_data.list, qiter->iterator_data.list_data.list_index);
            qiter->iterator_data.list_data.list_index += 1;

            *finished = false;

            Py_INCREF(result);
            return result;
        } else {
            *finished = true;
            return NULL;
        }
    }

    assert(false);
    return NULL;
}

PyObject *BUILTIN_SUM1(PyObject *sequence) {
    struct Nuitka_QuickIterator qiter;

    if (unlikely(MAKE_QUICK_ITERATOR(sequence, &qiter) == false)) {
        return NULL;
    }

    PyObject *result;

    long int_result = 0;

    PyObject *item;

    for (;;) {
        bool finished;

        item = QUICK_ITERATOR_NEXT(&qiter, &finished);

        if (finished) {
#if PYTHON_VERSION < 300
            return PyInt_FromLong(int_result);
#else
            return PyLong_FromLong(int_result);
#endif
        } else if (item == NULL) {
            return NULL;
        }

        CHECK_OBJECT(item);

        // For Python2 int objects:
#if PYTHON_VERSION < 300
        if (PyInt_CheckExact(item)) {
            long b = PyInt_AS_LONG(item);
            long x = int_result + b;

            if ((x ^ int_result) >= 0 || (x ^ b) >= 0) {
                int_result = x;
                Py_DECREF(item);

                continue;
            }
        }
#endif

        // For Python2 long, Python3 int objects
#if PYTHON_VERSION >= 270
        if (PyLong_CheckExact(item)) {
            int overflow;
            long b = PyLong_AsLongAndOverflow(item, &overflow);

            if (overflow) {
                break;
            }

            long x = int_result + b;

            if ((x ^ int_result) >= 0 || (x ^ b) >= 0) {
                int_result = x;
                Py_DECREF(item);

                continue;
            }
        }
#endif

        if (item == Py_False) {
            Py_DECREF(item);
            continue;
        }

        if (item == Py_True) {
            long b = 1;
            long x = int_result + b;

            if ((x ^ int_result) >= 0 || (x ^ b) >= 0) {
                int_result = x;
                Py_DECREF(item);

                continue;
            }
        }

        /* Either overflowed or not one of the supported int alike types. */
        break;
    }

    /* Switch over to objects, and redo last step. */
#if PYTHON_VERSION < 300
    result = PyInt_FromLong(int_result);
#else
    result = PyLong_FromLong(int_result);
#endif
    CHECK_OBJECT(result);

    PyObject *temp = PyNumber_Add(result, item);
    Py_DECREF(result);
    Py_DECREF(item);
    result = temp;

    if (unlikely(result == NULL)) {
        return NULL;
    }

    for (;;) {
        CHECK_OBJECT(result);

        bool finished;
        item = QUICK_ITERATOR_NEXT(&qiter, &finished);

        if (finished) {
            break;
        } else if (item == NULL) {
            Py_DECREF(result);
            return NULL;
        }

        CHECK_OBJECT(item);

        PyObject *temp2 = PyNumber_Add(result, item);

        Py_DECREF(item);
        Py_DECREF(result);

        if (unlikely(temp2 == NULL)) {
            return NULL;
        }

        result = temp2;
    }

    CHECK_OBJECT(result);

    return result;
}

NUITKA_DEFINE_BUILTIN(sum);

PyObject *BUILTIN_SUM2(PyObject *sequence, PyObject *start) {
    NUITKA_ASSIGN_BUILTIN(sum);

    CHECK_OBJECT(sequence);
    CHECK_OBJECT(start);

    PyObject *pos_args = PyTuple_New(2);
    PyTuple_SET_ITEM(pos_args, 0, sequence);
    Py_INCREF(sequence);
    PyTuple_SET_ITEM(pos_args, 1, start);
    Py_INCREF(start);

    PyObject *result = CALL_FUNCTION_WITH_POSARGS(NUITKA_ACCESS_BUILTIN(sum), pos_args);

    Py_DECREF(pos_args);
    return result;
}

PyDictObject *dict_builtin = NULL;
PyModuleObject *builtin_module = NULL;

static PyTypeObject Nuitka_BuiltinModule_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_module", // tp_name
    sizeof(PyModuleObject),                           // tp_size
};

extern PyObject *const_str_plain_open;

int Nuitka_BuiltinModule_SetAttr(PyModuleObject *module, PyObject *name, PyObject *value) {
    CHECK_OBJECT((PyObject *)module);
    CHECK_OBJECT(name);

    // This is used for "del" as well.
    assert(value == NULL || Py_REFCNT(value) > 0);

    // only checks the builtins that we can refresh at this time, if we have
    // many value to check maybe need create a dict first.
    bool found = false;

    int res = PyObject_RichCompareBool(name, const_str_plain_open, Py_EQ);

    if (unlikely(res == -1)) {
        return -1;
    }
    if (res == 1) {
        NUITKA_UPDATE_BUILTIN(open, value);
        found = true;
    }

    if (found == false) {
        res = PyObject_RichCompareBool(name, const_str_plain___import__, Py_EQ);

        if (unlikely(res == -1)) {
            return -1;
        }

        if (res == 1) {
            NUITKA_UPDATE_BUILTIN(__import__, value);
            found = true;
        }
    }

#if PYTHON_VERSION >= 300
    if (found == false) {
        res = PyObject_RichCompareBool(name, const_str_plain_print, Py_EQ);

        if (unlikely(res == -1)) {
            return -1;
        }

        if (res == 1) {
            NUITKA_UPDATE_BUILTIN(print, value);
            found = true;
        }
    }
#endif

    return PyObject_GenericSetAttr((PyObject *)module, name, value);
}

#include <osdefs.h>

#if defined(_WIN32)
#include <Shlwapi.h>
#elif defined(__APPLE__)
#include <dlfcn.h>
#include <libgen.h>
#include <mach-o/dyld.h>
#else
#include <dlfcn.h>
#include <libgen.h>
#endif

#if defined(__FreeBSD__)
#include <sys/sysctl.h>
#endif

#if defined(_NUITKA_EXE)

char *getBinaryDirectoryUTF8Encoded() {
    static char binary_directory[MAXPATHLEN + 1];
    static bool init_done = false;

    if (init_done) {
        return binary_directory;
    }

#if defined(_WIN32)

#if PYTHON_VERSION >= 300
    WCHAR binary_directory2[MAXPATHLEN + 1];
    binary_directory2[0] = 0;

    DWORD res = GetModuleFileNameW(NULL, binary_directory2, MAXPATHLEN);
    assert(res != 0);

    int res2 = WideCharToMultiByte(CP_UTF8, 0, binary_directory2, -1, binary_directory, MAXPATHLEN, NULL, NULL);
    assert(res2 != 0);
#else
    DWORD res = GetModuleFileName(NULL, binary_directory, MAXPATHLEN);
    assert(res != 0);
#endif
    PathRemoveFileSpec(binary_directory);
#elif defined(__APPLE__)
    uint32_t bufsize = MAXPATHLEN;
    int res = _NSGetExecutablePath(binary_directory, &bufsize);

    if (unlikely(res != 0)) {
        abort();
    }

    // On macOS, the "dirname" call creates a separate internal string, we can
    // safely copy back.
    strncpy(binary_directory, dirname(binary_directory), MAXPATHLEN);

#elif defined(__FreeBSD__)
    /* Not all of FreeBSD has /proc file system, so use the appropriate
     * "sysctl" instead.
     */
    int mib[4];
    mib[0] = CTL_KERN;
    mib[1] = KERN_PROC;
    mib[2] = KERN_PROC_PATHNAME;
    mib[3] = -1;
    size_t cb = sizeof(binary_directory);
    sysctl(mib, 4, binary_directory, &cb, NULL, 0);

    /* We want the directory name, the above gives the full executable name. */
    strcpy(binary_directory, dirname(binary_directory));
#else
    /* The remaining platforms, mostly Linux or compatible. */

    /* The "readlink" call does not terminate result, so fill zeros there, then
     * it is a proper C string right away. */
    memset(binary_directory, 0, MAXPATHLEN + 1);
    ssize_t res = readlink("/proc/self/exe", binary_directory, MAXPATHLEN);

    if (unlikely(res == -1)) {
        abort();
    }

    strncpy(binary_directory, dirname(binary_directory), MAXPATHLEN);
#endif
    init_done = true;
    return binary_directory;
}

char *getBinaryDirectoryHostEncoded() {
#if defined(_WIN32)
    static char binary_directory[MAXPATHLEN + 1];
    static bool init_done = false;

    if (init_done) {
        return binary_directory;
    }

#if PYTHON_VERSION >= 300
    WCHAR binary_directory2[MAXPATHLEN + 1];
    binary_directory2[0] = 0;

    DWORD res = GetModuleFileNameW(NULL, binary_directory2, MAXPATHLEN);
    assert(res != 0);

    int res2 = WideCharToMultiByte(CP_ACP, 0, binary_directory2, -1, binary_directory, MAXPATHLEN, NULL, NULL);
    assert(res2 != 0);
#else
    DWORD res = GetModuleFileName(NULL, binary_directory, MAXPATHLEN);
    assert(res != 0);
#endif
    PathRemoveFileSpec(binary_directory);

    init_done = true;
    return binary_directory;
#else
    return getBinaryDirectoryUTF8Encoded();
#endif
}

static PyObject *getBinaryDirectoryObject() {
    static PyObject *binary_directory = NULL;

    if (binary_directory != NULL) {
        return binary_directory;
    }

#if PYTHON_VERSION >= 300
    binary_directory = PyUnicode_FromString(getBinaryDirectoryUTF8Encoded());
#else
    binary_directory = PyString_FromString(getBinaryDirectoryUTF8Encoded());
#endif

    if (unlikely(binary_directory == NULL)) {
        PyErr_Print();
        abort();
    }

    return binary_directory;
}

#else
static char *getDllDirectory() {
#if defined(_WIN32)
    static char path[MAXPATHLEN + 1];
    HMODULE hm = NULL;
    path[0] = '\0';

#if PYTHON_VERSION >= 300
    WCHAR path2[MAXPATHLEN + 1];
    path2[0] = 0;

    int res = GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                                 (LPCSTR)&getDllDirectory, &hm);
    assert(res != 0);

    res = GetModuleFileNameW(hm, path2, MAXPATHLEN + 1);
    assert(res != 0);

    int res2 = WideCharToMultiByte(CP_UTF8, 0, path2, -1, path, MAXPATHLEN + 1, NULL, NULL);
    assert(res2 != 0);
#else
    int res = GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                                 (LPCSTR)&getDllDirectory, &hm);
    assert(res != 0);

    res = GetModuleFileNameA(hm, path, MAXPATHLEN + 1);
    assert(res != 0);
#endif
    PathRemoveFileSpec(path);

    return path;

#else
    Dl_info where;
    int res = dladdr((void *)getDllDirectory, &where);
    assert(res != 0);

    return dirname((char *)where.dli_fname);
#endif
}
#endif

void _initBuiltinModule() {
#if _NUITKA_MODULE
    if (builtin_module)
        return;
#else
    assert(builtin_module == NULL);
#endif

#if PYTHON_VERSION < 300
    builtin_module = (PyModuleObject *)PyImport_ImportModule("__builtin__");
#else
    builtin_module = (PyModuleObject *)PyImport_ImportModule("builtins");
#endif
    assert(builtin_module);
    dict_builtin = (PyDictObject *)builtin_module->md_dict;
    assert(PyDict_Check(dict_builtin));

#ifdef _NUITKA_STANDALONE
    int res = PyDict_SetItemString((PyObject *)dict_builtin, "__nuitka_binary_dir", getBinaryDirectoryObject());

    assert(res == 0);
#endif

    // init Nuitka_BuiltinModule_Type, PyType_Ready wont copy all member from
    // base type, so we need copy all members from PyModule_Type manual for
    // safety.  PyType_Ready will change tp_flags, we need define it again. Set
    // tp_setattro to Nuitka_BuiltinModule_SetAttr and we can detect value
    // change. Set tp_base to PyModule_Type and PyModule_Check will pass.
    Nuitka_BuiltinModule_Type.tp_dealloc = PyModule_Type.tp_dealloc;
    Nuitka_BuiltinModule_Type.tp_repr = PyModule_Type.tp_repr;
    Nuitka_BuiltinModule_Type.tp_setattro = (setattrofunc)Nuitka_BuiltinModule_SetAttr;
    Nuitka_BuiltinModule_Type.tp_getattro = PyModule_Type.tp_getattro;
    Nuitka_BuiltinModule_Type.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_BASETYPE;
    Nuitka_BuiltinModule_Type.tp_doc = PyModule_Type.tp_doc;
    Nuitka_BuiltinModule_Type.tp_traverse = PyModule_Type.tp_traverse;
    Nuitka_BuiltinModule_Type.tp_members = PyModule_Type.tp_members;
    Nuitka_BuiltinModule_Type.tp_base = &PyModule_Type;
    Nuitka_BuiltinModule_Type.tp_dictoffset = PyModule_Type.tp_dictoffset;
    Nuitka_BuiltinModule_Type.tp_init = PyModule_Type.tp_init;
    Nuitka_BuiltinModule_Type.tp_alloc = PyModule_Type.tp_alloc;
    Nuitka_BuiltinModule_Type.tp_new = PyModule_Type.tp_new;
    Nuitka_BuiltinModule_Type.tp_free = PyModule_Type.tp_free;
    int ret = PyType_Ready(&Nuitka_BuiltinModule_Type);
    assert(ret == 0);

    // Replace type of builtin module to take over.
    ((PyObject *)builtin_module)->ob_type = &Nuitka_BuiltinModule_Type;
    assert(PyModule_Check(builtin_module) == 1);
}

#include "HelpersCalling.c"

PyObject *MAKE_RELATIVE_PATH(PyObject *relative) {
    static PyObject *our_path_object = NULL;

    if (our_path_object == NULL) {
#if defined(_NUITKA_EXE)
        our_path_object = getBinaryDirectoryObject();
#else
#if PYTHON_VERSION >= 300
        our_path_object = PyUnicode_FromString(getDllDirectory());
#else
        our_path_object = PyString_FromString(getDllDirectory());
#endif

#endif
    }

    char sep[2] = {SEP, 0};

#if PYTHON_VERSION < 300
    PyObject *result = PyNumber_Add(our_path_object, PyString_FromString(sep));
#else
    PyObject *result = PyNumber_Add(our_path_object, PyUnicode_FromString(sep));
#endif

    assert(result);

#if PYTHON_VERSION < 300
    result = PyNumber_InPlaceAdd(result, relative);
#else
    result = PyNumber_InPlaceAdd(result, relative);
#endif

    assert(result);

    return result;
}

#ifdef _NUITKA_EXE

NUITKA_DEFINE_BUILTIN(type)
NUITKA_DEFINE_BUILTIN(len)
NUITKA_DEFINE_BUILTIN(repr)
NUITKA_DEFINE_BUILTIN(int)
NUITKA_DEFINE_BUILTIN(iter)
#if PYTHON_VERSION < 300
NUITKA_DEFINE_BUILTIN(long)
#else
NUITKA_DEFINE_BUILTIN(range);
#endif

void _initBuiltinOriginalValues() {
    NUITKA_ASSIGN_BUILTIN(type);
    NUITKA_ASSIGN_BUILTIN(len);
    NUITKA_ASSIGN_BUILTIN(range);
    NUITKA_ASSIGN_BUILTIN(repr);
    NUITKA_ASSIGN_BUILTIN(int);
    NUITKA_ASSIGN_BUILTIN(iter);
#if PYTHON_VERSION < 300
    NUITKA_ASSIGN_BUILTIN(long);
#endif

    CHECK_OBJECT(_python_original_builtin_value_range);
}

#endif

// Used for threading.
#if PYTHON_VERSION >= 300
volatile int _Py_Ticker = _Py_CheckInterval;
#endif

// Reverse operation mapping.
static int const swapped_op[] = {Py_GT, Py_GE, Py_EQ, Py_NE, Py_LT, Py_LE};

#if PYTHON_VERSION >= 270
iternextfunc default_iternext;

extern PyObject *const_str_plain___iter__;

void _initSlotIternext() {
    PyObject *pos_args = PyTuple_New(1);
    PyTuple_SET_ITEM(pos_args, 0, (PyObject *)&PyBaseObject_Type);
    Py_INCREF(&PyBaseObject_Type);

    PyObject *kw_args = PyDict_New();
    PyDict_SetItem(kw_args, const_str_plain___iter__, Py_True);

    PyObject *c =
        PyObject_CallFunctionObjArgs((PyObject *)&PyType_Type, const_str_plain___iter__, pos_args, kw_args, NULL);
    Py_DECREF(pos_args);
    Py_DECREF(kw_args);

    PyObject *r = PyObject_CallFunctionObjArgs(c, NULL);
    Py_DECREF(c);

    CHECK_OBJECT(r);
    assert(Py_TYPE(r)->tp_iternext);

    default_iternext = Py_TYPE(r)->tp_iternext;

    Py_DECREF(r);
}
#endif

#include "HelpersComparison.c"

#include "HelpersDeepcopy.c"

#include "HelpersAttributes.c"

#include "HelpersOperationBinaryAdd.c"
#include "HelpersOperationBinaryInplaceAdd.c"

#if _NUITKA_PROFILE
#include "HelpersProfiling.c"
#endif
