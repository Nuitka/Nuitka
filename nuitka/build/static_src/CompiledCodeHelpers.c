//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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
    NUITKA_PRINT_TRACE("main(): Calling _initListBuiltinMethods().");
    _initListBuiltinMethods();
}

#if PYTHON_VERSION >= 0x350
#include "HelpersAllocator.c"
#endif

#include "HelpersBuiltin.c"
#include "HelpersBytes.c"
#include "HelpersClasses.c"
#include "HelpersDictionaries.c"
#include "HelpersExceptions.c"
#include "HelpersFiles.c"
#include "HelpersFloats.c"
#include "HelpersHeapStorage.c"
#include "HelpersImport.c"
#include "HelpersImportHard.c"
#include "HelpersLists.c"
#include "HelpersMappings.c"
#include "HelpersRaising.c"
#include "HelpersSequences.c"
#include "HelpersSlices.c"
#include "HelpersStrings.c"
#include "HelpersTuples.c"

#include "HelpersEnvironmentVariables.c"
#include "HelpersFilesystemPaths.c"
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

    PyObject *result = MAKE_LIST_EMPTY(tstate, size);

    long current = low;

    for (int i = 0; i < size; i++) {
        PyList_SET_ITEM(result, i, Nuitka_PyInt_FromLong(current));
        current += step;
    }

    return result;
}

static PyObject *_BUILTIN_RANGE_INT2(long low, long high) { return _BUILTIN_RANGE_INT3(low, high, 1); }

static PyObject *_BUILTIN_RANGE_INT(long boundary) {
    PyObject *result = MAKE_LIST_EMPTY(tstate, boundary > 0 ? boundary : 0);

    for (int i = 0; i < boundary; i++) {
        PyList_SET_ITEM(result, i, Nuitka_PyInt_FromLong(i));
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

PyObject *BUILTIN_RANGE(PyThreadState *tstate, PyObject *boundary) {
    PyObject *boundary_temp = TO_RANGE_ARG(boundary, "end");

    if (unlikely(boundary_temp == NULL)) {
        return NULL;
    }

    long start = PyInt_AsLong(boundary_temp);

    if (start == -1 && DROP_ERROR_OCCURRED(tstate)) {
        NUITKA_ASSIGN_BUILTIN(range);

        PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, NUITKA_ACCESS_BUILTIN(range), boundary_temp);

        Py_DECREF(boundary_temp);

        return result;
    }
    Py_DECREF(boundary_temp);

    return _BUILTIN_RANGE_INT(start);
}

PyObject *BUILTIN_RANGE2(PyThreadState *tstate, PyObject *low, PyObject *high) {
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

    if (unlikely(start == -1 && DROP_ERROR_OCCURRED(tstate))) {
        fallback = true;
    }

    long end = PyInt_AsLong(high_temp);

    if (unlikely(end == -1 && DROP_ERROR_OCCURRED(tstate))) {
        fallback = true;
    }

    if (fallback) {
        // Transfers references to tuple.
        PyObject *pos_args = MAKE_TUPLE2_0(tstate, low_temp, high_temp);
        NUITKA_ASSIGN_BUILTIN(range);

        PyObject *result = CALL_FUNCTION_WITH_POS_ARGS2(tstate, NUITKA_ACCESS_BUILTIN(range), pos_args);

        Py_DECREF(pos_args);

        return result;
    } else {
        Py_DECREF(low_temp);
        Py_DECREF(high_temp);

        return _BUILTIN_RANGE_INT2(start, end);
    }
}

PyObject *BUILTIN_RANGE3(PyThreadState *tstate, PyObject *low, PyObject *high, PyObject *step) {
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

    if (unlikely(start == -1 && DROP_ERROR_OCCURRED(tstate))) {
        fallback = true;
    }

    long end = PyInt_AsLong(high_temp);

    if (unlikely(end == -1 && DROP_ERROR_OCCURRED(tstate))) {
        fallback = true;
    }

    long step_long = PyInt_AsLong(step_temp);

    if (unlikely(step_long == -1 && DROP_ERROR_OCCURRED(tstate))) {
        fallback = true;
    }

    if (fallback) {
        PyObject *pos_args = MAKE_TUPLE3_0(tstate, low_temp, high_temp, step_temp);

        NUITKA_ASSIGN_BUILTIN(range);

        PyObject *result = CALL_FUNCTION_WITH_POS_ARGS3(tstate, NUITKA_ACCESS_BUILTIN(range), pos_args);

        Py_DECREF(pos_args);

        return result;
    } else {
        Py_DECREF(low_temp);
        Py_DECREF(high_temp);
        Py_DECREF(step_temp);

        if (unlikely(step_long == 0)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "range() step argument must not be zero");
            return NULL;
        }

        return _BUILTIN_RANGE_INT3(start, end, step_long);
    }
}

#endif

#if PYTHON_VERSION < 0x300

/* Same as CPython2: */
static unsigned long getLengthOfRange(PyThreadState *tstate, long lo, long hi, long step) {
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
PyObject *MAKE_XRANGE(PyThreadState *tstate, long start, long stop, long step) {
    /* TODO: It would be sweet to calculate that on user side already. */
    unsigned long n = getLengthOfRange(tstate, start, stop, step);

    if (n > (unsigned long)LONG_MAX || (long)n > PY_SSIZE_T_MAX) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_OverflowError, "xrange() result has too many items");

        return NULL;
    }

    // spell-checker: ignore rangeobject

    struct _rangeobject2 *result = (struct _rangeobject2 *)PyObject_New(struct _rangeobject2, &PyRange_Type);
    assert(result != NULL);

    result->start = start;
    result->len = (long)n;
    result->step = step;

    return (PyObject *)result;
}

#else

/* Same as CPython3: */
static PyObject *getLengthOfRange(PyThreadState *tstate, PyObject *start, PyObject *stop, PyObject *step) {
    nuitka_bool nbool_res = RICH_COMPARE_GT_NBOOL_OBJECT_LONG(step, const_int_0);

    if (unlikely(nbool_res == NUITKA_BOOL_EXCEPTION)) {
        return NULL;
    }

    PyObject *lo, *hi;

    // Make sure we use step as a positive number.
    if (nbool_res == NUITKA_BOOL_TRUE) {
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

        nbool_res = RICH_COMPARE_EQ_NBOOL_OBJECT_LONG(step, const_int_0);

        if (unlikely(nbool_res == NUITKA_BOOL_EXCEPTION)) {
            Py_DECREF(step);
            return NULL;
        }

        if (unlikely(nbool_res == NUITKA_BOOL_TRUE)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "range() arg 3 must not be zero");
            Py_DECREF(step);

            return NULL;
        }
    }

    // Negative difference, we got zero length.
    nbool_res = RICH_COMPARE_GE_NBOOL_OBJECT_OBJECT(lo, hi);

    // No distance means we do not have any length to go.
    if (nbool_res != NUITKA_BOOL_FALSE) {
        Py_DECREF(step);

        if (unlikely(nbool_res == NUITKA_BOOL_EXCEPTION)) {
            return NULL;
        }

        Py_INCREF(const_int_0);
        return const_int_0;
    }

    // TODO: Use binary operations here, for now we only eliminated rich comparison API
    PyObject *tmp1 = PyNumber_Subtract(hi, lo);

    if (unlikely(tmp1 == NULL)) {
        Py_DECREF(step);

        return NULL;
    }

    PyObject *diff = PyNumber_Subtract(tmp1, const_int_pos_1);
    Py_DECREF(tmp1);

    if (unlikely(diff == NULL)) {
        Py_DECREF(step);

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

static PyObject *MAKE_XRANGE(PyThreadState *tstate, PyObject *start, PyObject *stop, PyObject *step) {
    start = Nuitka_Number_IndexAsLong(start);
    if (unlikely(start == NULL)) {
        return NULL;
    }
    stop = Nuitka_Number_IndexAsLong(stop);
    if (unlikely(stop == NULL)) {
        return NULL;
    }
    step = Nuitka_Number_IndexAsLong(step);
    if (unlikely(step == NULL)) {
        return NULL;
    }

    PyObject *length = getLengthOfRange(tstate, start, stop, step);
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
PyObject *BUILTIN_XRANGE1(PyThreadState *tstate, PyObject *high) {
#if PYTHON_VERSION < 0x300
    if (unlikely(PyFloat_Check(high))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_high = PyInt_AsLong(high);

    if (unlikely(int_high == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    return MAKE_XRANGE(tstate, 0, int_high, 1);
#else
    PyObject *stop = Nuitka_Number_IndexAsLong(high);

    if (unlikely(stop == NULL)) {
        return NULL;
    }

    PyObject *length = getLengthOfRange(tstate, const_int_0, stop, const_int_pos_1);
    if (unlikely(length == NULL)) {
        Py_DECREF(stop);

        return NULL;
    }

    struct _rangeobject3 *result = (struct _rangeobject3 *)PyObject_New(struct _rangeobject3, &PyRange_Type);
    assert(result != NULL);

    result->start = const_int_0;
    Py_INCREF(const_int_0);
    result->stop = stop;
    result->step = const_int_pos_1;
    Py_INCREF(const_int_pos_1);

    result->length = length;

    return (PyObject *)result;
#endif
}

/* Built-in xrange (Python2) or xrange (Python3) with two arguments. */
PyObject *BUILTIN_XRANGE2(PyThreadState *tstate, PyObject *low, PyObject *high) {
#if PYTHON_VERSION < 0x300
    if (unlikely(PyFloat_Check(low))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_low = PyInt_AsLong(low);

    if (unlikely(int_low == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(high))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_high = PyInt_AsLong(high);

    if (unlikely(int_high == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    return MAKE_XRANGE(tstate, int_low, int_high, 1);
#else
    return MAKE_XRANGE(tstate, low, high, const_int_pos_1);
#endif
}

/* Built-in xrange (Python2) or xrange (Python3) with three arguments. */
PyObject *BUILTIN_XRANGE3(PyThreadState *tstate, PyObject *low, PyObject *high, PyObject *step) {
#if PYTHON_VERSION < 0x300
    if (unlikely(PyFloat_Check(low))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_low = PyInt_AsLong(low);

    if (unlikely(int_low == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(high))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_high = PyInt_AsLong(high);

    if (unlikely(int_high == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (unlikely(PyFloat_Check(step))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");

        return NULL;
    }

    long int_step = PyInt_AsLong(step);

    if (unlikely(int_step == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (unlikely(int_step == 0)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "range() arg 3 must not be zero");

        return NULL;
    }

    return MAKE_XRANGE(tstate, int_low, int_high, int_step);
#else
    return MAKE_XRANGE(tstate, low, high, step);
#endif
}

PyObject *BUILTIN_ALL(PyThreadState *tstate, PyObject *value) {
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
            Py_INCREF_IMMORTAL(Py_False);
            return Py_False;
        }
    }

    Py_DECREF(it);

    if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate))) {
        return NULL;
    }

    Py_INCREF_IMMORTAL(Py_True);
    return Py_True;
}

PyObject *BUILTIN_LEN(PyThreadState *tstate, PyObject *value) {
    CHECK_OBJECT(value);

    Py_ssize_t res = Nuitka_PyObject_Size(value);

    if (unlikely(res < 0 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    return PyInt_FromSsize_t(res);
}

PyObject *BUILTIN_ANY(PyThreadState *tstate, PyObject *value) {
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
            Py_INCREF_IMMORTAL(Py_True);
            return Py_True;
        }
    }

    Py_DECREF(it);
    if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate))) {
        return NULL;
    }

    Py_INCREF_IMMORTAL(Py_False);
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

PyObject *BUILTIN_FORMAT(PyThreadState *tstate, PyObject *value, PyObject *format_spec) {
    CHECK_OBJECT(value);
    CHECK_OBJECT(format_spec);

    NUITKA_ASSIGN_BUILTIN(format);

    PyObject *args[2] = {value, format_spec};

    return CALL_FUNCTION_WITH_ARGS2(tstate, NUITKA_ACCESS_BUILTIN(format), args);
}

// Helper functions for print. Need to play nice with Python softspace
// behavior. spell-checker: ignore softspace

#if PYTHON_VERSION >= 0x300
NUITKA_DEFINE_BUILTIN(print);
#endif

bool PRINT_NEW_LINE_TO(PyObject *file) {
    PyThreadState *tstate = PyThreadState_GET();

#if PYTHON_VERSION < 0x300
    if (file == NULL || file == Py_None) {
        file = GET_STDOUT();

        if (unlikely(file == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "lost sys.stdout");
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

    struct Nuitka_ExceptionPreservationItem saved_exception_state;

    FETCH_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

    PyObject *result;

    if (likely(file == NULL)) {
        result = CALL_FUNCTION_NO_ARGS(tstate, NUITKA_ACCESS_BUILTIN(print));
    } else {
        PyObject *kw_pairs[2] = {const_str_plain_file, GET_STDOUT()};
        PyObject *kw_args = MAKE_DICT(kw_pairs, 1);

        // TODO: This should use something that does not build a dictionary at all, and not
        // uses a tuple.
        result = CALL_FUNCTION_WITH_KW_ARGS(tstate, NUITKA_ACCESS_BUILTIN(print), kw_args);

        Py_DECREF(kw_args);
    }

    Py_XDECREF(result);

    RESTORE_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

    return result != NULL;
#endif
}

bool PRINT_ITEM_TO(PyObject *file, PyObject *object) {
    PyThreadState *tstate = PyThreadState_GET();

// The print built-in function cannot replace "softspace" behavior of CPython
// print statement, so this code is really necessary.
#if PYTHON_VERSION < 0x300
    if (file == NULL || file == Py_None) {
        file = GET_STDOUT();

        if (unlikely(file == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "lost sys.stdout");
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

    struct Nuitka_ExceptionPreservationItem saved_exception_state;

    FETCH_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

    // TODO: Have a helper that creates a dictionary for PyObject **
    PyObject *print_kw = MAKE_DICT_EMPTY(tstate);
    DICT_SET_ITEM(print_kw, const_str_plain_end, const_str_empty);

    if (file == NULL) {
        DICT_SET_ITEM(print_kw, const_str_plain_file, GET_STDOUT());
    } else {
        DICT_SET_ITEM(print_kw, const_str_plain_file, file);
    }

    PyObject *print_args = MAKE_TUPLE1(tstate, object);

    PyObject *result = CALL_FUNCTION(tstate, NUITKA_ACCESS_BUILTIN(print), print_args, print_kw);

    Py_DECREF(print_args);
    Py_DECREF(print_kw);

    Py_XDECREF(result);

    RESTORE_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

    return result != NULL;
#endif
}

void PRINT_REFCOUNT(PyObject *object) {
    if (object) {
#if PYTHON_VERSION >= 0x3c0
        if (_Py_IsImmortal(object)) {
            PRINT_STRING(" refcnt IMMORTAL");
            return;
        }
#endif
        char buffer[1024];
        snprintf(buffer, sizeof(buffer) - 1, " refcnt %" PY_FORMAT_SIZE_T "d ", Py_REFCNT(object));

        PRINT_STRING(buffer);
    } else {
        PRINT_STRING(" <null>");
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

bool PRINT_STRING_W(wchar_t const *str) {
    if (str) {
        PyObject *tmp = NuitkaUnicode_FromWideChar(str, -1);
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
    va_end(args);

    return PRINT_STRING(buffer);
}

bool PRINT_REPR(PyObject *object) {
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state;

    FETCH_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

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

    RESTORE_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

    return res;
}

bool PRINT_NULL(void) { return PRINT_STRING("<NULL>"); }

bool PRINT_TYPE(PyObject *object) { return PRINT_ITEM((PyObject *)Py_TYPE(object)); }

void _PRINT_EXCEPTION3(PyObject *exception_type, PyObject *exception_value, PyTracebackObject *exception_tb) {
    PRINT_REPR(exception_type);
    if (exception_type != NULL) {
        PRINT_REFCOUNT(exception_type);
    }
    PRINT_STRING("|");
    PRINT_REPR(exception_value);
    if (exception_value != NULL) {
        PRINT_REFCOUNT(exception_value);
    }
#if PYTHON_VERSION >= 0x300
    if (exception_value != NULL && PyExceptionInstance_Check(exception_value)) {
        PRINT_STRING(" <- context ");
        PyObject *context = Nuitka_Exception_GetContext(exception_value);
        PRINT_REPR(context);
    }
#endif
    PRINT_STRING("|");
    PRINT_REPR((PyObject *)exception_tb);
    if (exception_tb != NULL) {
        PRINT_REFCOUNT((PyObject *)exception_tb);
    }

    PRINT_NEW_LINE();
}

#if PYTHON_VERSION >= 0x3b0
void _PRINT_EXCEPTION1(PyObject *exception_value) {
    PyObject *exception_type = exception_value ? PyExceptionInstance_Class(exception_value) : NULL;
    PyTracebackObject *exception_tb = (exception_value && PyExceptionInstance_Check(exception_value))
                                          ? GET_EXCEPTION_TRACEBACK(exception_value)
                                          : NULL;

    _PRINT_EXCEPTION3(exception_type, exception_value, exception_tb);
}
#endif

void PRINT_CURRENT_EXCEPTION(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PRINT_STRING("current_exc=");
#if PYTHON_VERSION < 0x3c0
    PRINT_EXCEPTION(tstate->curexc_type, tstate->curexc_value, (PyTracebackObject *)tstate->curexc_traceback);
#else
    _PRINT_EXCEPTION1(tstate->current_exception);
#endif
}

void PRINT_PUBLISHED_EXCEPTION(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PRINT_STRING("thread_exc=");
#if PYTHON_VERSION < 0x3b0
    PRINT_EXCEPTION(EXC_TYPE(tstate), EXC_VALUE(tstate), EXC_TRACEBACK(tstate));
#else
    PyObject *exc_value = EXC_VALUE(tstate);
    PyTracebackObject *exc_tb = (exc_value != NULL && exc_value != Py_None) ? GET_EXCEPTION_TRACEBACK(exc_value) : NULL;
    PRINT_EXCEPTION(EXC_TYPE(tstate), exc_value, exc_tb);
#endif
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
            printf("  Frame at %s\n", PyString_AsString(PyObject_Str((PyObject *)Nuitka_Frame_GetCodeObject(frame))));

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
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "lost sys.stdout");
        return NULL;
    }

    return result;
}

PyObject *GET_STDERR(void) {
    PyObject *result = Nuitka_SysGetObject("stderr");

    if (unlikely(result == NULL)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "lost sys.stderr");
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

bool PRINT_ITEM_LINE(PyObject *object) { return PRINT_ITEM(object) && PRINT_NEW_LINE(); }

#if PYTHON_VERSION < 0x300

static void set_slot(PyObject **slot, PyObject *value) {
    PyObject *temp = *slot;
    Py_XINCREF(value);
    *slot = value;
    Py_XDECREF(temp);
}

static void set_attr_slots(PyClassObject *class_object) {
    set_slot(&class_object->cl_getattr, FIND_ATTRIBUTE_IN_CLASS(class_object, const_str_plain___getattr__));
    set_slot(&class_object->cl_setattr, FIND_ATTRIBUTE_IN_CLASS(class_object, const_str_plain___setattr__));
    set_slot(&class_object->cl_delattr, FIND_ATTRIBUTE_IN_CLASS(class_object, const_str_plain___delattr__));
}

static bool set_dict(PyClassObject *class_object, PyObject *value) {
    if (value == NULL || !PyDict_Check(value)) {
        PyThreadState *tstate = PyThreadState_GET();
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__dict__ must be a dictionary object");
        return false;
    } else {
        set_slot(&class_object->cl_dict, value);
        set_attr_slots(class_object);

        return true;
    }
}

static bool set_bases(PyClassObject *class_object, PyObject *value) {
    if (value == NULL || !PyTuple_Check(value)) {

        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__bases__ must be a tuple object");
        return false;
    } else {
        Py_ssize_t n = PyTuple_GET_SIZE(value);

        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *base = PyTuple_GET_ITEM(value, i);

            if (unlikely(!PyClass_Check(base))) {
                PyThreadState *tstate = PyThreadState_GET();

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__bases__ items must be classes");
                return false;
            }

            if (unlikely(PyClass_IsSubclass(base, (PyObject *)class_object))) {
                PyThreadState *tstate = PyThreadState_GET();

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                                "a __bases__ item causes an inheritance cycle");
                return false;
            }
        }

        set_slot(&class_object->cl_bases, value);
        set_attr_slots(class_object);

        return true;
    }
}

static bool set_name(PyClassObject *class_object, PyObject *value) {
    if (value == NULL || !PyDict_Check(value)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__name__ must be a string object");
        return false;
    }

    if (strlen(PyString_AS_STRING(value)) != (size_t)PyString_GET_SIZE(value)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__name__ must not contain null bytes");
        return false;
    }

    set_slot(&class_object->cl_name, value);
    return true;
}

static int nuitka_class_setattr(PyClassObject *class_object, PyObject *attr_name, PyObject *value) {
    char const *sattr_name = PyString_AsString(attr_name);

    if (sattr_name[0] == '_' && sattr_name[1] == '_') {
        Py_ssize_t n = PyString_Size(attr_name);

        if (sattr_name[n - 2] == '_' && sattr_name[n - 1] == '_') {
            if (strcmp(sattr_name, "__dict__") == 0) {
                if (set_dict(class_object, value) == false) {
                    return -1;
                } else {
                    return 0;
                }
            } else if (strcmp(sattr_name, "__bases__") == 0) {
                if (set_bases(class_object, value) == false) {
                    return -1;
                } else {
                    return 0;
                }
            } else if (strcmp(sattr_name, "__name__") == 0) {
                if (set_name(class_object, value) == false) {
                    return -1;
                } else {
                    return 0;
                }
            } else if (strcmp(sattr_name, "__getattr__") == 0) {
                set_slot(&class_object->cl_getattr, value);
            } else if (strcmp(sattr_name, "__setattr__") == 0) {
                set_slot(&class_object->cl_setattr, value);
            } else if (strcmp(sattr_name, "__delattr__") == 0) {
                set_slot(&class_object->cl_delattr, value);
            }
        }
    }

    if (value == NULL) {
        int status = DICT_REMOVE_ITEM(class_object->cl_dict, attr_name);

        if (status < 0) {
            PyErr_Format(PyExc_AttributeError, "class %s has no attribute '%s'",
                         PyString_AS_STRING(class_object->cl_name), sattr_name);
        }

        return status;
    } else {
        return DICT_SET_ITEM(class_object->cl_dict, attr_name, value) ? 0 : -1;
    }
}

static PyObject *nuitka_class_getattr(PyClassObject *class_object, PyObject *attr_name) {
    char const *sattr_name = PyString_AsString(attr_name);

    if (sattr_name[0] == '_' && sattr_name[1] == '_') {
        if (strcmp(sattr_name, "__dict__") == 0) {
            Py_INCREF(class_object->cl_dict);
            return class_object->cl_dict;
        } else if (strcmp(sattr_name, "__bases__") == 0) {
            Py_INCREF(class_object->cl_bases);
            return class_object->cl_bases;
        } else if (strcmp(sattr_name, "__name__") == 0) {
            if (class_object->cl_name == NULL) {
                Py_INCREF_IMMORTAL(Py_None);
                return Py_None;
            } else {
                Py_INCREF(class_object->cl_name);
                return class_object->cl_name;
            }
        }
    }

    PyObject *value = FIND_ATTRIBUTE_IN_CLASS(class_object, attr_name);

    if (unlikely(value == NULL)) {
        PyErr_Format(PyExc_AttributeError, "class %s has no attribute '%s'", PyString_AS_STRING(class_object->cl_name),
                     sattr_name);
        return NULL;
    }

    PyTypeObject *type = Py_TYPE(value);

    descrgetfunc tp_descr_get = NuitkaType_HasFeatureClass(type) ? type->tp_descr_get : NULL;

    if (tp_descr_get == NULL) {
        Py_INCREF(value);
        return value;
    } else {
        return tp_descr_get(value, (PyObject *)NULL, (PyObject *)class_object);
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

static bool MAKE_QUICK_ITERATOR(PyThreadState *tstate, PyObject *sequence, struct Nuitka_QuickIterator *qiter) {
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

        qiter->iterator_data.iter = MAKE_ITERATOR(tstate, sequence);
        if (unlikely(qiter->iterator_data.iter == NULL)) {
            return false;
        }
    }

    return true;
}

static PyObject *QUICK_ITERATOR_NEXT(PyThreadState *tstate, struct Nuitka_QuickIterator *qiter, bool *finished) {
    PyObject *result;

    switch (qiter->iterator_mode) {
    case ITERATOR_GENERIC:
        result = ITERATOR_NEXT_ITERATOR(qiter->iterator_data.iter);

        if (result == NULL) {
            Py_DECREF(qiter->iterator_data.iter);

            if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate))) {
                *finished = false;
                return NULL;
            }

            *finished = true;
            return NULL;
        }

        *finished = false;
        return result;
    case ITERATOR_COMPILED_GENERATOR:
        result = Nuitka_Generator_qiter(tstate, qiter->iterator_data.generator, finished);

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

PyObject *BUILTIN_SUM1(PyThreadState *tstate, PyObject *sequence) {
    struct Nuitka_QuickIterator qiter;

    if (unlikely(MAKE_QUICK_ITERATOR(tstate, sequence, &qiter) == false)) {
        return NULL;
    }

    PyObject *result;

    long int_result = 0;

    PyObject *item;

    for (;;) {
        bool finished;

        item = QUICK_ITERATOR_NEXT(tstate, &qiter, &finished);

        if (finished) {
            return Nuitka_PyInt_FromLong(int_result);
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
            Py_DECREF_IMMORTAL(item);
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
    result = Nuitka_PyInt_FromLong(int_result);
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
        item = QUICK_ITERATOR_NEXT(tstate, &qiter, &finished);

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

PyObject *BUILTIN_SUM2(PyThreadState *tstate, PyObject *sequence, PyObject *start) {
    NUITKA_ASSIGN_BUILTIN(sum);

    CHECK_OBJECT(sequence);
    CHECK_OBJECT(start);

    PyObject *pos_args = MAKE_TUPLE2(tstate, sequence, start);

    PyObject *result = CALL_FUNCTION_WITH_POS_ARGS2(tstate, NUITKA_ACCESS_BUILTIN(sum), pos_args);

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

    if (found == false) {
        res = PyObject_RichCompareBool(name, const_str_plain_super, Py_EQ);

        if (unlikely(res == -1)) {
            return -1;
        }

        if (res == 1) {
            NUITKA_UPDATE_BUILTIN(super, value);
            found = true;
        }
    }

    return PyObject_GenericSetAttr((PyObject *)module, name, value);
}

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
    PyObject *result = dirname;

    if (dirname != const_str_empty) {
        result = PyNumber_InPlaceAdd(result, getPathSeparatorStringObject());
        CHECK_OBJECT(result);
    }

    result = PyNumber_InPlaceAdd(result, filename);
    CHECK_OBJECT(result);

    return result;
}

#if defined(_NUITKA_EXE)

wchar_t const *getBinaryDirectoryWideChars(bool resolve_symlinks) {
    static wchar_t binary_directory[MAXPATHLEN + 1];
    static bool init_done = false;

    if (init_done == false) {
        binary_directory[0] = 0;

#if defined(_WIN32)
        copyStringSafeW(binary_directory, getBinaryFilenameWideChars(resolve_symlinks),
                        sizeof(binary_directory) / sizeof(wchar_t));

        stripFilenameW(binary_directory);

#ifndef _NUITKA_EXPERIMENTAL_AVOID_SHORT_PATH
        // Query length of result first.
        DWORD length = GetShortPathNameW(binary_directory, NULL, 0);
        assert(length != 0);

        wchar_t *short_binary_directory = (wchar_t *)malloc((length + 1) * sizeof(wchar_t));
        DWORD res = GetShortPathNameW(binary_directory, short_binary_directory, length);
        assert(res != 0);

        if (unlikely(res > length)) {
            abort();
        }

        binary_directory[0] = 0;
        appendWStringSafeW(binary_directory, short_binary_directory, sizeof(binary_directory) / sizeof(wchar_t));

        free(short_binary_directory);
#endif
#else
        appendStringSafeW(binary_directory, getBinaryDirectoryHostEncoded(true),
                          sizeof(binary_directory) / sizeof(wchar_t));
#endif

        init_done = true;
    }
    return (wchar_t const *)binary_directory;
}

#if defined(_WIN32)
char const *getBinaryDirectoryHostEncoded(bool resolve_symlinks) {
    static char *binary_directory = NULL;
    static char *binary_directory_resolved = NULL;

    char *binary_directory_target;

    if (resolve_symlinks) {
        binary_directory_target = binary_directory_resolved;
    } else {
        binary_directory_target = binary_directory;
    }

    if (binary_directory_target != NULL) {
        return binary_directory_target;
    }
    wchar_t const *w = getBinaryDirectoryWideChars(resolve_symlinks);

    DWORD bufsize = WideCharToMultiByte(CP_ACP, 0, w, -1, NULL, 0, NULL, NULL);
    assert(bufsize != 0);

    binary_directory_target = (char *)malloc(bufsize + 1);
    assert(binary_directory_target);

    DWORD res2 = WideCharToMultiByte(CP_ACP, 0, w, -1, binary_directory_target, bufsize, NULL, NULL);
    assert(res2 != 0);

    if (unlikely(res2 > bufsize)) {
        abort();
    }

    return (char const *)binary_directory_target;
}

#else

char const *getBinaryDirectoryHostEncoded(bool resolve_symlinks) {
    const int buffer_size = MAXPATHLEN + 1;

    static char binary_directory[MAXPATHLEN + 1] = {0};
    static char binary_directory_resolved[MAXPATHLEN + 1] = {0};

    char *binary_directory_target;

    if (resolve_symlinks) {
        binary_directory_target = binary_directory_resolved;
    } else {
        binary_directory_target = binary_directory;
    }

    if (*binary_directory_target != 0) {
        return binary_directory_target;
    }

    // Get the filename first.
    copyStringSafe(binary_directory_target, getBinaryFilenameHostEncoded(resolve_symlinks), buffer_size);

    // We want the directory name, the above gives the full executable name.
    copyStringSafe(binary_directory_target, dirname(binary_directory_target), buffer_size);

    return binary_directory_target;
}

#endif

#ifdef _NUITKA_EXE
PyObject *getBinaryFilenameObject(bool resolve_symlinks) {
    static PyObject *binary_filename = NULL;
    static PyObject *binary_filename_resolved = NULL;

    PyObject **binary_object_target;

    if (resolve_symlinks) {
        binary_object_target = &binary_filename_resolved;
    } else {
        binary_object_target = &binary_filename;
    }

    if (*binary_object_target != NULL) {
        CHECK_OBJECT(*binary_object_target);

        return *binary_object_target;
    }

// On Python3, this must be a unicode object, it cannot be on Python2,
// there e.g. code objects expect Python2 strings.
#if PYTHON_VERSION >= 0x300
#ifdef _WIN32
    wchar_t const *exe_filename = getBinaryFilenameWideChars(resolve_symlinks);
    *binary_object_target = NuitkaUnicode_FromWideChar(exe_filename, -1);
#else
    *binary_object_target = PyUnicode_DecodeFSDefault(getBinaryFilenameHostEncoded(resolve_symlinks));
#endif
#else
    *binary_object_target = PyString_FromString(getBinaryFilenameHostEncoded(resolve_symlinks));
#endif

    if (unlikely(*binary_object_target == NULL)) {
        PyErr_Print();
        abort();
    }

    // Make sure it's usable for caching.
    Py_INCREF(*binary_object_target);

    return *binary_object_target;
}
#endif

PyObject *getBinaryDirectoryObject(bool resolve_symlinks) {
    static PyObject *binary_directory = NULL;
    static PyObject *binary_directory_resolved = NULL;

    PyObject **binary_object_target;

    if (resolve_symlinks) {
        binary_object_target = &binary_directory_resolved;
    } else {
        binary_object_target = &binary_directory;
    }

    if (*binary_object_target != NULL) {
        CHECK_OBJECT(*binary_object_target);

        return *binary_object_target;
    }

// On Python3, this must be a unicode object, it cannot be on Python2,
// there e.g. code objects expect Python2 strings.
#if PYTHON_VERSION >= 0x300
#ifdef _WIN32
    wchar_t const *bin_directory = getBinaryDirectoryWideChars(resolve_symlinks);
    *binary_object_target = NuitkaUnicode_FromWideChar(bin_directory, -1);
#else
    *binary_object_target = PyUnicode_DecodeFSDefault(getBinaryDirectoryHostEncoded(resolve_symlinks));
#endif
#else
    *binary_object_target = PyString_FromString(getBinaryDirectoryHostEncoded(resolve_symlinks));
#endif

    if (unlikely(*binary_object_target == NULL)) {
        PyErr_Print();
        abort();
    }

    // Make sure it's usable for caching.
    Py_INCREF(*binary_object_target);

    return *binary_object_target;
}

#ifdef _NUITKA_STANDALONE
// Helper function to create path.
PyObject *getStandaloneSysExecutablePath(PyObject *basename) {
    PyObject *dir_name = getBinaryDirectoryObject(false);
    PyObject *sys_executable = JOIN_PATH2(dir_name, basename);

    return sys_executable;
}
#endif

#else

#if defined(_WIN32)
// Small helper function to get current DLL handle, spell-checker: ignore lpcstr
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

filename_char_t const *getDllDirectory(void) {
#if defined(_WIN32)
    static WCHAR path[MAXPATHLEN + 1];
    path[0] = 0;

    int res = GetModuleFileNameW(getDllModuleHandle(), path, MAXPATHLEN);
    assert(res != 0);

    stripFilenameW(path);

    return path;
#else
    Dl_info where;

    {
        NUITKA_MAY_BE_UNUSED int res = dladdr((void *)getDllDirectory, &where);
        assert(res != 0);
    }

    return dirname((char *)where.dli_fname);
#endif
}
static PyObject *getDllDirectoryObject(void) {
    static PyObject *dll_directory = NULL;

    if (dll_directory == NULL) {
        filename_char_t const *dll_directory_filename = getDllDirectory();

        dll_directory = Nuitka_String_FromFilename(dll_directory_filename);

#if PYTHON_VERSION < 0x300
        // Avoid unnecessary unicode values.
        PyObject *decoded_dll_directory = PyObject_Str(dll_directory);

        if (decoded_dll_directory == NULL) {
            PyThreadState *tstate = PyThreadState_GET();
            DROP_ERROR_OCCURRED(tstate);
        } else {
            Py_DECREF(dll_directory);
            dll_directory = decoded_dll_directory;
        }
#endif
    }

    CHECK_OBJECT(dll_directory);

    return dll_directory;
}
#endif

#if defined(_NUITKA_MODULE)
static filename_char_t const *getDllFilename(void) {
#if defined(_WIN32)
    static WCHAR path[MAXPATHLEN + 1];
    path[0] = 0;

    int res = GetModuleFileNameW(getDllModuleHandle(), path, MAXPATHLEN);
    assert(res != 0);

    return path;
#else
    Dl_info where;

    {
        NUITKA_MAY_BE_UNUSED int res = dladdr((void *)getDllDirectory, &where);
        assert(res != 0);
    }

    return where.dli_fname;
#endif
}

PyObject *getDllFilenameObject(void) {
    static PyObject *dll_filename = NULL;

    if (dll_filename == NULL) {
        filename_char_t const *dll_filename_str = getDllFilename();

        dll_filename = Nuitka_String_FromFilename(dll_filename_str);

#if PYTHON_VERSION < 0x300
        // Avoid unnecessary unicode values.
        PyObject *decoded_dll_filename = PyObject_Str(dll_filename);

        if (decoded_dll_filename == NULL) {
            PyThreadState *tstate = PyThreadState_GET();
            DROP_ERROR_OCCURRED(tstate);
        } else {
            Py_DECREF(dll_filename);
            dll_filename = decoded_dll_filename;
        }
#endif
    }

    CHECK_OBJECT(dll_filename);

    return dll_filename;
}
#endif

PyObject *getContainingDirectoryObject(bool resolve_symlinks) {
#if defined(_NUITKA_EXE)
#if defined(_NUITKA_ONEFILE_MODE)
    environment_char_t const *onefile_directory = getEnvironmentVariable("NUITKA_ONEFILE_DIRECTORY");
    if (onefile_directory != NULL) {
        PyObject *result = Nuitka_String_FromFilename(onefile_directory);
        unsetEnvironmentVariable("NUITKA_ONEFILE_DIRECTORY");

        return result;
    }

    return getBinaryDirectoryObject(resolve_symlinks);
#else
    return getBinaryDirectoryObject(resolve_symlinks);
#endif
#else
    return getDllDirectoryObject();
#endif
}

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
    {
        NUITKA_MAY_BE_UNUSED int res =
            PyDict_SetItemString((PyObject *)dict_builtin, "__nuitka_binary_dir", getBinaryDirectoryObject(true));
        assert(res == 0);
        PyDict_SetItemString((PyObject *)dict_builtin, "__nuitka_binary_exe", getBinaryFilenameObject(true));
        assert(res == 0);
    }
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
    NUITKA_MAY_BE_UNUSED int res2 = PyType_Ready(&Nuitka_BuiltinModule_Type);
    assert(res2 >= 0);

    // Replace type of builtin module to take over.
    ((PyObject *)builtin_module)->ob_type = &Nuitka_BuiltinModule_Type;
    assert(PyModule_Check(builtin_module) == 1);
}

#include "HelpersCalling.c"

PyObject *MAKE_RELATIVE_PATH(PyObject *relative) {
    CHECK_OBJECT(relative);

    static PyObject *our_path_object = NULL;

    if (our_path_object == NULL) {
        our_path_object = getContainingDirectoryObject(true);
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
#if PYTHON_VERSION >= 0x300 && !defined(NUITKA_USE_PYCORE_THREAD_STATE)
volatile int _Py_Ticker = _Py_CheckInterval;
#endif

#if PYTHON_VERSION >= 0x270
iternextfunc default_iternext;

void _initSlotIterNext(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *pos_args = MAKE_TUPLE1(tstate, (PyObject *)&PyBaseObject_Type);

    // Note: Not using MAKE_DICT_EMPTY on purpose, this is called early on.
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

#include "HelpersAttributes.c"
#include "HelpersDeepcopy.c"
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
#include "HelpersTypes.c"
#if PYTHON_VERSION < 0x300
#include "HelpersOperationBinaryOlddiv.c"
#endif
#if PYTHON_VERSION >= 0x350
#include "HelpersOperationBinaryMatmult.c"
#endif

#include "HelpersOperationBinaryDualAdd.c"

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
#include "HelpersComparisonLe.c"
#include "HelpersComparisonLt.c"

#include "HelpersComparisonGe.c"
#include "HelpersComparisonGt.c"
#include "HelpersComparisonNe.c"

#include "HelpersComparisonDualEq.c"
#include "HelpersComparisonDualLe.c"
#include "HelpersComparisonDualLt.c"

#include "HelpersComparisonDualGe.c"
#include "HelpersComparisonDualGt.c"
#include "HelpersComparisonDualNe.c"

#include "HelpersChecksumTools.c"
#include "HelpersConstantsBlob.c"

#if _NUITKA_PROFILE
#include "HelpersProfiling.c"
#endif

#if _NUITKA_PGO_PYTHON
#include "HelpersPythonPgo.c"
#endif

#include "MetaPathBasedLoader.c"

#ifdef _NUITKA_EXPERIMENTAL_DUMP_C_TRACEBACKS
#include "HelpersDumpBacktraces.c"
#endif

#ifdef _NUITKA_INLINE_COPY_HACL
#include "Hacl_Hash_SHA2.c"
#endif

#include "HelpersJitSources.c"

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
