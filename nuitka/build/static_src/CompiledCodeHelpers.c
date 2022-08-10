//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "HelpersBuiltinTypeMethods.c"

static void _initBuiltinTypeMethods(void) {
#if PYTHON_VERSION < 0x300
    NUITKA_PRINT_TRACE("main(): Calling _initStrBuiltinMethods().");
    _initStrBuiltinMethods();
#else
    NUITKA_PRINT_TRACE("main(): Calling _initBytesBuiltinMethods().");
    _initBytesBuiltinMethods();
#endif
    NUITKA_PRINT_TRACE("main(): Calling _initUnicodeBuiltinMethods().");
    _initUnicodeBuiltinMethods();
    NUITKA_PRINT_TRACE("main(): Calling _initDictBuiltinMethods().");
    _initDictBuiltinMethods();
}

#include "HelpersBuiltin.c"
#include "HelpersClasses.c"
#include "HelpersDictionaries.c"
#include "HelpersExceptions.c"
#include "HelpersFiles.c"
#include "HelpersHeapStorage.c"
#include "HelpersImport.c"
#include "HelpersImportHard.c"
#include "HelpersRaising.c"
#include "HelpersStrings.c"

#include "HelpersSafeStrings.c"

#if PYTHON_VERSION >= 0x3a0
#include "HelpersMatching.c"
#endif

#if PYTHON_VERSION < 0x300

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

static PyObject *_BUILTIN_RANGE_INT(long boundary) {
    PyObject *result = PyList_New(boundary > 0 ? boundary : 0);

    for (int i = 0; i < boundary; i++) {
        PyList_SET_ITEM(result, i, PyInt_FromLong(i));
    }

    return result;
}

static PyObject *TO_RANGE_ARG(PyObject *value, char const *name) {
    if (likely(PyInt_Check(value) || PyLong_Check(value))) {
        Py_INCREF(value);
        return value;
    }

    PyTypeObject *type = Py_TYPE(value);
    PyNumberMethods *tp_as_number = type->tp_as_number;

    // Everything that casts to int is allowed.
    if (
#if PYTHON_VERSION >= 0x270
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

#if PYTHON_VERSION < 0x300

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

        PyObject *result = CALL_FUNCTION_WITH_POSARGS2(NUITKA_ACCESS_BUILTIN(range), pos_args);

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

        PyObject *result = CALL_FUNCTION_WITH_POSARGS3(NUITKA_ACCESS_BUILTIN(range), pos_args);

        Py_DECREF(pos_args);

        return result;
    } else {
        Py_DECREF(low_temp);
        Py_DECREF(high_temp);
        Py_DECREF(step_temp);

        if (unlikely(step_long == 0)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "range() step argument must not be zero");
            return NULL;
        }

        return _BUILTIN_RANGE_INT3(start, end, step_long);
    }
}

#endif

#if PYTHON_VERSION < 0x300

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
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_OverflowError, "xrange() result has too many items");

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
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "range() arg 3 must not be zero");

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
#if PYTHON_VERSION < 0x300
    if (unlikely(PyFloat_Check(high))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "integer argument expected, got float");

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
#if PYTHON_VERSION < 0x300
    if (unlikely(PyFloat_Check(low))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_low = PyInt_AsLong(low);

    if (unlikely(int_low == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(high))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "integer argument expected, got float");

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
#if PYTHON_VERSION < 0x300
    if (unlikely(PyFloat_Check(low))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_low = PyInt_AsLong(low);

    if (unlikely(int_low == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(high))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_high = PyInt_AsLong(high);

    if (unlikely(int_high == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(step))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_step = PyInt_AsLong(step);

    if (unlikely(int_step == -1 && ERROR_OCCURRED())) {
        return NULL;
    }

    if (unlikely(int_step == 0)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "range() arg 3 must not be zero");

        return NULL;
    }

    return MAKE_XRANGE(int_low, int_high, int_step);
#else
    return MAKE_XRANGE(low, high, step);
#endif
}

PyObject *BUILTIN_ALL(PyObject *value) {
    CHECK_OBJECT(value);

    PyObject *it = PyObject_GetIter(value);

    if (unlikely((it == NULL))) {
        return NULL;
    }

    iternextfunc iternext = Py_TYPE(it)->tp_iternext;
    for (;;) {
        PyObject *item = iternext(it);

        if (unlikely((item == NULL)))
            break;
        int cmp = PyObject_IsTrue(item);
        Py_DECREF(item);
        if (unlikely(cmp < 0)) {
            Py_DECREF(it);
            return NULL;
        }
        if (cmp == 0) {
            Py_DECREF(it);
            Py_INCREF(Py_False);
            return Py_False;
        }
    }

    Py_DECREF(it);
    if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED())) {
        return NULL;
    }

    Py_INCREF(Py_True);
    return Py_True;
}

PyObject *BUILTIN_LEN(PyObject *value) {
    CHECK_OBJECT(value);

    Py_ssize_t res = PyObject_Size(value);

    if (unlikely(res < 0 && ERROR_OCCURRED())) {
        return NULL;
    }

    return PyInt_FromSsize_t(res);
}

PyObject *BUILTIN_ANY(PyObject *value) {
    CHECK_OBJECT(value);

    PyObject *it = PyObject_GetIter(value);

    if (unlikely((it == NULL))) {
        return NULL;
    }

    iternextfunc iternext = Py_TYPE(it)->tp_iternext;
    for (;;) {
        PyObject *item = iternext(it);

        if (unlikely((item == NULL)))
            break;
        int cmp = PyObject_IsTrue(item);
        Py_DECREF(item);
        if (unlikely(cmp < 0)) {
            Py_DECREF(it);
            return NULL;
        }
        if (cmp > 0) {
            Py_DECREF(it);
            Py_INCREF(Py_True);
            return Py_True;
        }
    }

    Py_DECREF(it);
    if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED())) {
        return NULL;
    }

    Py_INCREF(Py_False);
    return Py_False;
}

PyObject *BUILTIN_ABS(PyObject *o) {
    CHECK_OBJECT(o);

    PyNumberMethods *m = o->ob_type->tp_as_number;
    if (likely(m && m->nb_absolute)) {
        return m->nb_absolute(o);
    }

    return PyErr_Format(PyExc_TypeError, "bad operand type for abs(): '%s'", Py_TYPE(o)->tp_name);
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

#if PYTHON_VERSION >= 0x300
NUITKA_DEFINE_BUILTIN(print);
#endif

bool PRINT_NEW_LINE_TO(PyObject *file) {
#if PYTHON_VERSION < 0x300
    if (file == NULL || file == Py_None) {
        file = GET_STDOUT();

        if (unlikely(file == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "lost sys.stdout");
            return false;
        }
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
#if PYTHON_VERSION < 0x300
    if (file == NULL || file == Py_None) {
        file = GET_STDOUT();

        if (unlikely(file == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "lost sys.stdout");
            return false;
        }
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

    PyObject *print_kw = PyDict_New();
    PyDict_SetItem(print_kw, const_str_plain_end, const_str_empty);

    if (file == NULL) {
        PyDict_SetItem(print_kw, const_str_plain_file, GET_STDOUT());
    } else {
        PyDict_SetItem(print_kw, const_str_plain_file, file);
    }

    PyObject *print_args = PyTuple_New(1);
    PyTuple_SET_ITEM(print_args, 0, object);
    Py_INCREF(object);

    PyObject *result = CALL_FUNCTION(NUITKA_ACCESS_BUILTIN(print), print_args, print_kw);

    Py_DECREF(print_args);
    Py_DECREF(print_kw);

    Py_XDECREF(result);

    RESTORE_ERROR_OCCURRED_UNTRACED(exception_type, exception_value, exception_tb);

    return result != NULL;
#endif
}

void PRINT_REFCOUNT(PyObject *object) {
    if (object) {
        char buffer[1024];
        snprintf(buffer, sizeof(buffer) - 1, " refcnt %" PY_FORMAT_SIZE_T "d ", Py_REFCNT(object));

        PRINT_STRING(buffer);
    } else {
        PRINT_STRING("<null>");
    }
}

bool PRINT_STRING(char const *str) {
    if (str) {
        PyObject *tmp = PyUnicode_FromString(str);
        bool res = PRINT_ITEM(tmp);
        Py_DECREF(tmp);
        return res;
    } else {
        return PRINT_STRING("<nullstr>");
    }
}

bool PRINT_FORMAT(char const *fmt, ...) {
    va_list args;
    va_start(args, fmt);

    // Only used for debug purposes, lets be unsafe here.
    char buffer[4096];

    vsprintf(buffer, fmt, args);
    return PRINT_STRING(buffer);
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

bool PRINT_TYPE(PyObject *object) { return PRINT_ITEM((PyObject *)Py_TYPE(object)); }

void _PRINT_EXCEPTION(PyObject *exception_type, PyObject *exception_value, PyObject *exception_tb) {
    PRINT_REPR(exception_type);
    if (exception_type) {
        PRINT_REFCOUNT(exception_type);
    }
    PRINT_STRING("|");
    PRINT_REPR(exception_value);
    if (exception_value) {
        PRINT_REFCOUNT(exception_value);
    }
#if PYTHON_VERSION >= 0x300
    if (exception_value != NULL && PyExceptionInstance_Check(exception_value)) {
        PRINT_STRING(" <- context ");
        PyObject *context = PyException_GetContext(exception_value);
        PRINT_REPR(context);
        Py_XDECREF(context);
    }
#endif
    PRINT_STRING("|");
    PRINT_REPR(exception_tb);

    PRINT_NEW_LINE();
}

void PRINT_CURRENT_EXCEPTION(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PRINT_STRING("current_exc=");
    PRINT_EXCEPTION(tstate->curexc_type, tstate->curexc_value, tstate->curexc_traceback);
}

void PRINT_PUBLISHED_EXCEPTION(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PRINT_STRING("thread_exc=");
    PRINT_EXCEPTION(EXC_TYPE(tstate), EXC_VALUE(tstate), EXC_TRACEBACK(tstate));
}

// TODO: Could be ported, the "printf" stuff would need to be split. On Python3
// the normal C print output gets lost.
#if PYTHON_VERSION < 0x300
void PRINT_TRACEBACK(PyTracebackObject *traceback) {
    PRINT_STRING("Dumping traceback:\n");

    if (traceback == NULL)
        PRINT_STRING("<NULL traceback?!>\n");

    while (traceback != NULL) {
        printf(" line %d (frame object chain):\n", traceback->tb_lineno);

        PyFrameObject *frame = traceback->tb_frame;

        while (frame != NULL) {
            printf("  Frame at %s\n", PyString_AsString(PyObject_Str((PyObject *)frame->f_code)));

            frame = frame->f_back;
        }

        assert(traceback->tb_next != traceback);
        traceback = traceback->tb_next;
    }

    PRINT_STRING("End of Dump.\n");
}
#endif

PyObject *GET_STDOUT(void) {
    PyObject *result = Nuitka_SysGetObject("stdout");

    if (unlikely(result == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "lost sys.stdout");
        return NULL;
    }

    return result;
}

PyObject *GET_STDERR(void) {
    PyObject *result = Nuitka_SysGetObject("stderr");

    if (unlikely(result == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "lost sys.stderr");
        return NULL;
    }

    return result;
}

bool PRINT_NEW_LINE(void) { return PRINT_NEW_LINE_TO(NULL); }

bool PRINT_ITEM(PyObject *object) {
    if (object == NULL) {
        return PRINT_NULL();
    } else {
        return PRINT_ITEM_TO(NULL, object);
    }
}

#if PYTHON_VERSION < 0x300

static void set_slot(PyObject **slot, PyObject *value) {
    PyObject *temp = *slot;
    Py_XINCREF(value);
    *slot = value;
    Py_XDECREF(temp);
}

static void set_attr_slots(PyClassObject *klass) {
    set_slot(&klass->cl_getattr, FIND_ATTRIBUTE_IN_CLASS(klass, const_str_plain___getattr__));
    set_slot(&klass->cl_setattr, FIND_ATTRIBUTE_IN_CLASS(klass, const_str_plain___setattr__));
    set_slot(&klass->cl_delattr, FIND_ATTRIBUTE_IN_CLASS(klass, const_str_plain___delattr__));
}

static bool set_dict(PyClassObject *klass, PyObject *value) {
    if (value == NULL || !PyDict_Check(value)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__dict__ must be a dictionary object");
        return false;
    } else {
        set_slot(&klass->cl_dict, value);
        set_attr_slots(klass);

        return true;
    }
}

static bool set_bases(PyClassObject *klass, PyObject *value) {
    if (value == NULL || !PyTuple_Check(value)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__bases__ must be a tuple object");
        return false;
    } else {
        Py_ssize_t n = PyTuple_GET_SIZE(value);

        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *base = PyTuple_GET_ITEM(value, i);

            if (unlikely(!PyClass_Check(base))) {
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__bases__ items must be classes");
                return false;
            }

            if (unlikely(PyClass_IsSubclass(base, (PyObject *)klass))) {
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "a __bases__ item causes an inheritance cycle");
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
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__name__ must be a string object");
        return false;
    }

    if (strlen(PyString_AS_STRING(value)) != (size_t)PyString_GET_SIZE(value)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__name__ must not contain null bytes");
        return false;
    }

    set_slot(&klass->cl_name, value);
    return true;
}

static int nuitka_class_setattr(PyClassObject *klass, PyObject *attr_name, PyObject *value) {
    char const *sattr_name = PyString_AsString(attr_name);

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
    char const *sattr_name = PyString_AsString(attr_name);

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

    descrgetfunc tp_descr_get = NuitkaType_HasFeatureClass(type) ? type->tp_descr_get : NULL;

    if (tp_descr_get == NULL) {
        Py_INCREF(value);
        return value;
    } else {
        return tp_descr_get(value, (PyObject *)NULL, (PyObject *)klass);
    }
}

#endif

void enhancePythonTypes(void) {
#if PYTHON_VERSION < 0x300
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
#if PYTHON_VERSION < 0x300
            return PyInt_FromLong(int_result);
#else
            return PyLong_FromLong(int_result);
#endif
        } else if (item == NULL) {
            return NULL;
        }

        CHECK_OBJECT(item);

// For Python2 int objects:
#if PYTHON_VERSION < 0x300
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
#if PYTHON_VERSION >= 0x270
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
#if PYTHON_VERSION < 0x300
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

    PyObject *result = CALL_FUNCTION_WITH_POSARGS2(NUITKA_ACCESS_BUILTIN(sum), pos_args);

    Py_DECREF(pos_args);

    return result;
}

PyDictObject *dict_builtin = NULL;
PyModuleObject *builtin_module = NULL;

static PyTypeObject Nuitka_BuiltinModule_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_module", // tp_name
    sizeof(PyModuleObject),                           // tp_size
};

int Nuitka_BuiltinModule_SetAttr(PyModuleObject *module, PyObject *name, PyObject *value) {
    CHECK_OBJECT(module);
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

#if PYTHON_VERSION >= 0x300
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

#if defined(__FreeBSD__) || defined(__OpenBSD__)
#include <sys/sysctl.h>
#endif

static PyObject *getPathSeparatorStringObject(void) {
    static char const sep[2] = {SEP, 0};

    static PyObject *sep_str = NULL;

    if (sep_str == NULL) {
        sep_str = Nuitka_String_FromString(sep);
    }

    CHECK_OBJECT(sep_str);

    return sep_str;
}

PyObject *JOIN_PATH2(PyObject *dirname, PyObject *filename) {
    CHECK_OBJECT(dirname);
    CHECK_OBJECT(filename);

    // Avoid string APIs, so str, unicode doesn't matter for input.
    PyObject *result = PyNumber_Add(dirname, getPathSeparatorStringObject());
    CHECK_OBJECT(result);

    result = PyNumber_InPlaceAdd(result, filename);
    CHECK_OBJECT(result);

    return result;
}

#if defined(_WIN32)
// Replacement for RemoveFileSpecW, slightly smaller, avoids a link library.
NUITKA_MAY_BE_UNUSED static void stripFilenameW(wchar_t *path) {
    wchar_t *last_slash = NULL;

    while (*path != 0) {
        if (*path == L'\\') {
            last_slash = path;
        }

        path++;
    }

    if (last_slash != NULL) {
        *last_slash = 0;
    }
}
#endif

#if defined(_NUITKA_EXE)

#ifdef _WIN32
static void resolveFileSymbolicLink(wchar_t *resolved_filename, wchar_t const *filename, DWORD resolved_filename_size) {
#if defined(_NUITKA_EXPERIMENTAL_SYMLINKS)
    // Resolve any symbolic links in the filename.
    // Copies the resolved path over the top of the parameter.

    // Open the file in the most non-exclusive way possible
    HANDLE file_handle = CreateFileW(filename, 0, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                                     OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

    if (unlikely(file_handle == INVALID_HANDLE_VALUE)) {
        abort();
    }

    // Resolve the path, get the result with a drive letter
    DWORD len = GetFinalPathNameByHandleW(file_handle, resolved_filename, resolved_filename_size,
                                          FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);

    CloseHandle(file_handle);

    if (unlikely(len >= resolved_filename_size)) {
        abort();
    }
#else
    copyStringSafeW(resolved_filename, filename, resolved_filename_size);
#endif
}

#else

static void resolveFileSymbolicLink(char *resolved_filename, char const *filename, size_t resolved_filename_size) {
#if defined(_NUITKA_EXPERIMENTAL_SYMLINKS)
    assert(resolved_filename_size < PATH_MAX);
    assert(false);

    // At least on macOS, realpath cannot allocate a buffer, so the above test is what is needed
    // and then this will be safe, on Linux we could use NULL argument and have a malloc of the
    // resulting value.
    char *result = realpath(filename, resolved_filename);

    if (unlikely(result == NULL)) {
        abort();
    }
#else
    copyStringSafe(resolved_filename, filename, resolved_filename_size);
#endif
}
#endif

#ifndef _WIN32
char const *getBinaryDirectoryHostEncoded(void) {
    static char binary_directory[MAXPATHLEN + 1];
    static bool init_done = false;

    if (init_done) {
        return binary_directory;
    }

    char binary_filename[MAXPATHLEN + 1];

#if defined(__APPLE__)
    uint32_t bufsize = sizeof(binary_filename);
    int res = _NSGetExecutablePath(binary_filename, &bufsize);

    if (unlikely(res != 0)) {
        abort();
    }

    // Resolve any symlinks we were invoked via
    resolveFileSymbolicLink(binary_directory, binary_filename, sizeof(binary_directory));

    // On macOS, the "dirname" call creates a separate internal string, we can
    // safely copy back.
    copyStringSafe(binary_directory, dirname(binary_directory), sizeof(binary_directory));

#elif defined(__FreeBSD__) || defined(__OpenBSD__)
    /* Not all of FreeBSD has /proc file system, so use the appropriate
     * "sysctl" instead.
     */
    int mib[4];
    mib[0] = CTL_KERN;
    mib[1] = KERN_PROC;
    mib[2] = KERN_PROC_PATHNAME;
    mib[3] = -1;
    size_t cb = sizeof(binary_filename);
    int res = sysctl(mib, 4, binary_filename, &cb, NULL, 0);

    if (unlikely(res != 0)) {
        abort();
    }

    // Resolve any symlinks we were invoked via
    resolveFileSymbolicLink(binary_directory, binary_filename, sizeof(binary_directory));

    /* We want the directory name, the above gives the full executable name. */
    copyStringSafe(binary_directory, dirname(binary_directory), sizeof(binary_directory));
#else
    /* The remaining platforms, mostly Linux or compatible. */

    /* The "readlink" call does not terminate result, so fill zeros there, then
     * it is a proper C string right away. */
    memset(binary_filename, 0, sizeof(binary_filename));
    ssize_t res = readlink("/proc/self/exe", binary_filename, sizeof(binary_filename) - 1);

    if (unlikely(res == -1)) {
        abort();
    }

    // Resolve any symlinks we were invoked via
    resolveFileSymbolicLink(binary_directory, binary_filename, sizeof(binary_directory));

    copyStringSafe(binary_directory, dirname(binary_directory), sizeof(binary_directory));
#endif
    init_done = true;
    return binary_directory;
}
#endif

wchar_t const *getBinaryDirectoryWideChars(void) {
    static wchar_t binary_directory[MAXPATHLEN + 1];
    static bool init_done = false;

    if (init_done == false) {
        binary_directory[0] = 0;

#if defined(_WIN32)
        wchar_t binary_filename[MAXPATHLEN + 1];
        DWORD res = GetModuleFileNameW(NULL, binary_filename, sizeof(binary_filename));
        assert(res != 0);

        // Resolve any symlinks we were invoked via
        resolveFileSymbolicLink(binary_directory, binary_filename, sizeof(binary_directory));

        stripFilenameW(binary_directory);

        // Query length of result first.
        DWORD length = GetShortPathNameW(binary_directory, NULL, 0);
        assert(length != 0);

        wchar_t *short_binary_directory = (wchar_t *)malloc((length + 1) * sizeof(wchar_t));
        res = GetShortPathNameW(binary_directory, short_binary_directory, length);
        assert(res != 0);

        if (unlikely(res > length)) {
            abort();
        }

        binary_directory[0] = 0;
        appendWStringSafeW(binary_directory, short_binary_directory, sizeof(binary_directory) / sizeof(wchar_t));

        free(short_binary_directory);
#else
        appendStringSafeW(binary_directory, getBinaryDirectoryHostEncoded(),
                          sizeof(binary_directory) / sizeof(wchar_t));
#endif

        init_done = true;
    }
    return (wchar_t const *)binary_directory;
}

#if defined(_WIN32) && PYTHON_VERSION < 0x300
char const *getBinaryDirectoryHostEncoded(void) {
    static char *binary_directory = NULL;

    if (binary_directory != NULL) {
        return binary_directory;
    }
    wchar_t const *w = getBinaryDirectoryWideChars();

    DWORD bufsize = WideCharToMultiByte(CP_ACP, 0, w, -1, NULL, 0, NULL, NULL);
    assert(bufsize != 0);

    binary_directory = (char *)malloc(bufsize + 1);
    assert(binary_directory);

    DWORD res2 = WideCharToMultiByte(CP_ACP, 0, w, -1, binary_directory, bufsize, NULL, NULL);
    assert(res2 != 0);

    if (unlikely(res2 > bufsize)) {
        abort();
    }

    return (char const *)binary_directory;
}
#endif

static PyObject *getBinaryDirectoryObject(void) {
    static PyObject *binary_directory = NULL;

    if (binary_directory != NULL) {
        CHECK_OBJECT(binary_directory);

        return binary_directory;
    }

// On Python3, this must be a unicode object, it cannot be on Python2,
// there e.g. code objects expect Python2 strings.
#if PYTHON_VERSION >= 0x300
#ifdef _WIN32
    wchar_t const *bin_directory = getBinaryDirectoryWideChars();
    binary_directory = NuitkaUnicode_FromWideChar(bin_directory, -1);
#else
    binary_directory = PyUnicode_DecodeFSDefault(getBinaryDirectoryHostEncoded());
#endif
#else
    binary_directory = PyString_FromString(getBinaryDirectoryHostEncoded());
#endif

    if (unlikely(binary_directory == NULL)) {
        PyErr_Print();
        abort();
    }

    // Make sure it's usable for caching.
    Py_INCREF(binary_directory);

    return binary_directory;
}

#ifdef _NUITKA_STANDALONE
// Helper function to create path.
PyObject *getStandaloneSysExecutablePath(PyObject *basename) {
    PyObject *dir_name = getBinaryDirectoryObject();
    PyObject *sys_executable = JOIN_PATH2(dir_name, basename);

    return sys_executable;
}
#endif

#else

#if defined(_WIN32)
/* Small helper function to get current DLL handle. */
static HMODULE getDllModuleHandle(void) {
    static HMODULE hm = NULL;

    if (hm == NULL) {
        int res =
            GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                               (LPCSTR)&getDllModuleHandle, &hm);
        assert(res != 0);
    }

    assert(hm != NULL);
    return hm;
}
#endif

#if defined(_WIN32)
// Replacement for RemoveFileSpecA, slightly smaller.
static void stripFilenameA(char *path) {
    char *last_slash = NULL;

    while (*path != 0) {
        if (*path == '\\') {
            last_slash = path;
        }

        path++;
    }

    if (last_slash != NULL) {
        *last_slash = 0;
    }
}
#endif

static char const *getDllDirectory(void) {
#if defined(_WIN32)
    static char path[MAXPATHLEN + 1];
    path[0] = '\0';

#if PYTHON_VERSION >= 0x300
    WCHAR path2[MAXPATHLEN + 1];
    path2[0] = 0;

    int res = GetModuleFileNameW(getDllModuleHandle(), path2, MAXPATHLEN + 1);
    assert(res != 0);

    int res2 = WideCharToMultiByte(CP_UTF8, 0, path2, -1, path, MAXPATHLEN + 1, NULL, NULL);
    assert(res2 != 0);
#else
    int res = GetModuleFileNameA(getDllModuleHandle(), path, MAXPATHLEN + 1);
    assert(res != 0);
#endif

    stripFilenameA(path);

    return path;

#else
    Dl_info where;
    int res = dladdr((void *)getDllDirectory, &where);
    assert(res != 0);

    return dirname((char *)where.dli_fname);
#endif
}
#endif

static void _initDeepCopy(void);

void _initBuiltinModule(void) {
    NUITKA_PRINT_TRACE("main(): Calling _initBuiltinTypeMethods().");
    _initBuiltinTypeMethods();
    NUITKA_PRINT_TRACE("main(): Calling _initDeepCopy().");
    _initDeepCopy();

#if _NUITKA_MODULE
    if (builtin_module != NULL) {
        return;
    }
#else
    assert(builtin_module == NULL);
#endif

#if PYTHON_VERSION < 0x300
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

    // init Nuitka_BuiltinModule_Type, PyType_Ready won't copy all member from
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
#include "HelpersCalling2.c"

PyObject *MAKE_RELATIVE_PATH(PyObject *relative) {
    CHECK_OBJECT(relative);

    static PyObject *our_path_object = NULL;

    if (our_path_object == NULL) {
#if defined(_NUITKA_EXE)
        our_path_object = getBinaryDirectoryObject();
#else
        our_path_object = Nuitka_String_FromString(getDllDirectory());
#endif
    }

    return JOIN_PATH2(our_path_object, relative);
}

#ifdef _NUITKA_EXE

NUITKA_DEFINE_BUILTIN(type)
NUITKA_DEFINE_BUILTIN(len)
NUITKA_DEFINE_BUILTIN(repr)
NUITKA_DEFINE_BUILTIN(int)
NUITKA_DEFINE_BUILTIN(iter)
#if PYTHON_VERSION < 0x300
NUITKA_DEFINE_BUILTIN(long)
#else
NUITKA_DEFINE_BUILTIN(range);
#endif

void _initBuiltinOriginalValues(void) {
    NUITKA_ASSIGN_BUILTIN(type);
    NUITKA_ASSIGN_BUILTIN(len);
    NUITKA_ASSIGN_BUILTIN(range);
    NUITKA_ASSIGN_BUILTIN(repr);
    NUITKA_ASSIGN_BUILTIN(int);
    NUITKA_ASSIGN_BUILTIN(iter);
#if PYTHON_VERSION < 0x300
    NUITKA_ASSIGN_BUILTIN(long);
#endif

    CHECK_OBJECT(_python_original_builtin_value_range);
}

#endif

// Used for threading.
#if PYTHON_VERSION >= 0x300 && !defined(NUITKA_USE_PYCORE_THREADSTATE)
volatile int _Py_Ticker = _Py_CheckInterval;
#endif

#if PYTHON_VERSION >= 0x270
iternextfunc default_iternext;

void _initSlotIterNext(void) {
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

#if PYTHON_VERSION >= 0x3a0
PyObject *MAKE_UNION_TYPE(PyObject *args) {
    assert(PyTuple_CheckExact(args));
    assert(PyTuple_GET_SIZE(args) > 1);

    CHECK_OBJECT_DEEP(args);

    PyObject *result = NULL;

    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(args); i++) {
        PyObject *value = PyTuple_GET_ITEM(args, i);

        if (result == NULL) {
            assert(i == 0);
            result = value;
        } else {
            result = PyNumber_InPlaceBitor(result, value);
        }
    }

    return result;
}
#endif

#include "HelpersDeepcopy.c"

#include "HelpersAttributes.c"
#include "HelpersLists.c"

#include "HelpersOperationBinaryAdd.c"
#include "HelpersOperationBinaryBitand.c"
#include "HelpersOperationBinaryBitor.c"
#include "HelpersOperationBinaryBitxor.c"
#include "HelpersOperationBinaryDivmod.c"
#include "HelpersOperationBinaryFloordiv.c"
#include "HelpersOperationBinaryLshift.c"
#include "HelpersOperationBinaryMod.c"
#include "HelpersOperationBinaryMult.c"
#include "HelpersOperationBinaryPow.c"
#include "HelpersOperationBinaryRshift.c"
#include "HelpersOperationBinarySub.c"
#include "HelpersOperationBinaryTruediv.c"
#if PYTHON_VERSION < 0x300
#include "HelpersOperationBinaryOlddiv.c"
#endif
#if PYTHON_VERSION >= 0x350
#include "HelpersOperationBinaryMatmult.c"
#endif

#include "HelpersOperationInplaceAdd.c"
#include "HelpersOperationInplaceBitand.c"
#include "HelpersOperationInplaceBitor.c"
#include "HelpersOperationInplaceBitxor.c"
#include "HelpersOperationInplaceFloordiv.c"
#include "HelpersOperationInplaceLshift.c"
#include "HelpersOperationInplaceMod.c"
#include "HelpersOperationInplaceMult.c"
#include "HelpersOperationInplacePow.c"
#include "HelpersOperationInplaceRshift.c"
#include "HelpersOperationInplaceSub.c"
#include "HelpersOperationInplaceTruediv.c"
#if PYTHON_VERSION < 0x300
#include "HelpersOperationInplaceOlddiv.c"
#endif
#if PYTHON_VERSION >= 0x350
#include "HelpersOperationInplaceMatmult.c"
#endif

#include "HelpersComparisonEq.c"
#include "HelpersComparisonGe.c"
#include "HelpersComparisonGt.c"
#include "HelpersComparisonLe.c"
#include "HelpersComparisonLt.c"
#include "HelpersComparisonNe.c"

#include "HelpersConstantsBlob.c"

#if _NUITKA_PROFILE
#include "HelpersProfiling.c"
#endif

#if _NUITKA_PGO_PYTHON
#include "HelpersPythonPgo.c"
#endif

#include "MetaPathBasedLoader.c"
