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

/** Providing access to the constants binary blob.
 *
 * There are multiple ways, the constants binary is accessed, and its
 * definition depends on how that is done.
 *
 * This deals with loading the resource from a DLL under Windows.
 *
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Loading of constants binary at run time from Windows resource is preferred method
// for that OS.
#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
unsigned char const *constant_bin = NULL;

void loadConstantsResource() {
#ifdef _NUITKA_EXE
    // Using NULL as this indicates running program.
    HMODULE handle = NULL;
#else
    HMODULE handle = getDllModuleHandle();
#endif

    constant_bin =
        (const unsigned char *)LockResource(LoadResource(handle, FindResource(handle, MAKEINTRESOURCE(3), RT_RCDATA)));

    assert(constant_bin);
}
#endif

typedef bool (*value_compare)(PyObject *a, PyObject *b);

struct ValueCache {
    PyObject **values;
    int used;
    int size;
    value_compare comparator;
};

#if PYTHON_VERSION < 300
#define INT_START_SIZE (512)
static struct ValueCache int_cache;
#endif

#define LONG_START_SIZE (512)
static struct ValueCache long_cache;

#define FLOAT_START_SIZE (512)
static struct ValueCache float_cache;

#if PYTHON_VERSION >= 300
#define BYTES_START_SIZE (512)
static struct ValueCache bytes_cache;
#endif

#if PYTHON_VERSION < 300
#define UNICODE_START_SIZE (512)
static struct ValueCache unicode_cache;
#endif

#define TUPLE_START_SIZE (64)
static struct ValueCache tuple_cache;

#define LIST_START_SIZE (64)
static struct ValueCache list_cache;

#define DICT_START_SIZE (64)
static struct ValueCache dict_cache;

#define SET_START_SIZE (64)
static struct ValueCache set_cache;

#define FROZENSET_START_SIZE (64)
static struct ValueCache frozenset_cache;

#if PYTHON_VERSION < 300
static bool compareIntValues(PyIntObject *a, PyIntObject *b) { return a->ob_ival == b->ob_ival; }
#endif

static bool compareLongValues(PyObject *a, PyObject *b) { return PyObject_RichCompareBool(a, b, Py_EQ) == 1; }

static bool compareFloatValues(PyFloatObject *a, PyFloatObject *b) {
    // Avoid the C math when comparing, for it makes too many values equal or unequal.
    return memcmp(&a->ob_fval, &b->ob_fval, sizeof(b->ob_fval)) == 0;
}

#if PYTHON_VERSION >= 300
static bool compareBytesValues(PyBytesObject *a, PyBytesObject *b) {
    if (Py_SIZE(a) != Py_SIZE(b)) {
        return false;
    }

    return memcmp(&a->ob_sval[0], &b->ob_sval[0], Py_SIZE(a)) == 0;
}
#else
static bool compareUnicodeValues(PyUnicodeObject *a, PyUnicodeObject *b) {
    if (Py_SIZE(a) != Py_SIZE(b)) {
        return false;
    }

    return memcmp(&a->str[0], &b->str[0], Py_SIZE(a) * sizeof(Py_UNICODE)) == 0;
}
#endif

static bool compareTupleValues(PyTupleObject *a, PyTupleObject *b) {
    if (Py_SIZE(a) != Py_SIZE(b)) {
        return false;
    }

    return memcmp(&a->ob_item[0], &b->ob_item[0], Py_SIZE(a) * sizeof(PyObject *)) == 0;
}

static bool compareListValues(PyListObject *a, PyTupleObject *b) {
    if (Py_SIZE(a) != Py_SIZE(b)) {
        return false;
    }

    return memcmp(&a->ob_item[0], &b->ob_item[0], Py_SIZE(a) * sizeof(PyObject *)) == 0;
}

static bool _compareSetItems(PyObject *a, PyObject *b) {
    Py_ssize_t pos1 = 0, pos2 = 0;
    PyObject *key1, *key2;

#if PYTHON_VERSION < 300
    // Same sized set, simply check if values are identical. Other reductions should
    // make it identical, or else this won't have the effect intended.
    while (_PySet_Next(a, &pos1, &key1)) {
        int res = _PySet_Next(b, &pos2, &key2);
        assert(res != 0);

        if (key1 != key2) {
            return false;
        }
    }
#else
    Py_hash_t unused;

    // Same sized dictionary, simply check if values are identical. Other reductions should
    // make it identical, or else this won't have the effect intended.
    while (_PySet_NextEntry(a, &pos1, &key1, &unused)) {
        int res = _PySet_NextEntry(b, &pos2, &key2, &unused);
        assert(res != 0);

        if (key1 != key2) {
            return false;
        }
    }

#endif

    return true;
}

static bool compareFrozensetValues(PyObject *a, PyObject *b) {
    if (Py_SIZE(a) != Py_SIZE(b)) {
        return false;
    }

    // Shortcut for frozensets, they are known to be hashable.
    if (HASH_VALUE_WITHOUT_ERROR(a) != HASH_VALUE_WITHOUT_ERROR(b)) {
        return false;
    }

    return _compareSetItems(a, b);
}

static bool compareSetValues(PyObject *a, PyObject *b) {
    if (Py_SIZE(a) != Py_SIZE(b)) {
        return false;
    }

    return _compareSetItems(a, b);
}

static bool compareDictValues(PyObject *a, PyObject *b) {
    if (Py_SIZE(a) != Py_SIZE(b)) {
        return false;
    }

    Py_ssize_t ppos1 = 0, ppos2 = 0;
    PyObject *key1, *value1;
    PyObject *key2, *value2;

    // Same sized dictionary, simply check if key and values are identical.
    // Other reductions should make it identical, or else this won't have the
    // effect intended.
    while (PyDict_Next(a, &ppos1, &key1, &value1)) {
        int res = PyDict_Next(b, &ppos2, &key2, &value2);
        assert(res != 0);

        if (key1 != key2) {
            return false;
        }
        if (value1 != value2) {
            return false;
        }
    }

    return true;
}

static void initCaches(void) {
    static bool init_done = false;
    if (init_done == true) {
        return;
    }

#if PYTHON_VERSION < 300
    int_cache.values = (PyObject **)malloc(sizeof(PyObject *) * INT_START_SIZE);
    int_cache.used = 0;
    int_cache.size = INT_START_SIZE;
    int_cache.comparator = (value_compare)compareIntValues;
#endif

    long_cache.values = (PyObject **)malloc(sizeof(PyObject *) * LONG_START_SIZE);
    long_cache.used = 0;
    long_cache.size = LONG_START_SIZE;
    long_cache.comparator = compareLongValues;

    float_cache.values = (PyObject **)malloc(sizeof(PyObject *) * FLOAT_START_SIZE);
    float_cache.used = 0;
    float_cache.size = FLOAT_START_SIZE;
    float_cache.comparator = (value_compare)compareFloatValues;

#if PYTHON_VERSION >= 300
    bytes_cache.values = (PyObject **)malloc(sizeof(PyObject *) * BYTES_START_SIZE);
    bytes_cache.used = 0;
    bytes_cache.size = BYTES_START_SIZE;
    bytes_cache.comparator = (value_compare)compareBytesValues;
#endif

#if PYTHON_VERSION < 300
    unicode_cache.values = (PyObject **)malloc(sizeof(PyObject *) * UNICODE_START_SIZE);
    unicode_cache.used = 0;
    unicode_cache.size = UNICODE_START_SIZE;
    unicode_cache.comparator = (value_compare)compareUnicodeValues;
#endif

    tuple_cache.values = (PyObject **)malloc(sizeof(PyObject *) * TUPLE_START_SIZE);
    tuple_cache.used = 0;
    tuple_cache.size = TUPLE_START_SIZE;
    tuple_cache.comparator = (value_compare)compareTupleValues;

    list_cache.values = (PyObject **)malloc(sizeof(PyObject *) * LIST_START_SIZE);
    list_cache.used = 0;
    list_cache.size = LIST_START_SIZE;
    list_cache.comparator = (value_compare)compareListValues;

    dict_cache.values = (PyObject **)malloc(sizeof(PyObject *) * DICT_START_SIZE);
    dict_cache.used = 0;
    dict_cache.size = DICT_START_SIZE;
    dict_cache.comparator = compareDictValues;

    set_cache.values = (PyObject **)malloc(sizeof(PyObject *) * SET_START_SIZE);
    set_cache.used = 0;
    set_cache.size = SET_START_SIZE;
    set_cache.comparator = compareSetValues;

    frozenset_cache.values = (PyObject **)malloc(sizeof(PyObject *) * FROZENSET_START_SIZE);
    frozenset_cache.used = 0;
    frozenset_cache.size = FROZENSET_START_SIZE;
    frozenset_cache.comparator = compareFrozensetValues;

    init_done = true;
}

static void insertToValueCache(struct ValueCache *cache, PyObject **value) {
    for (int i = 0; i < cache->used; i++) {
        if (cache->comparator(*value, cache->values[i])) {
            Py_DECREF(*value);

            *value = cache->values[i];
            return;
        }
    }

    if (cache->used == cache->size) {
        cache->size = cache->size * 2;
        cache->values = (PyObject **)realloc(cache->values, sizeof(PyObject *) * cache->size);
    }

    cache->values[cache->used++] = *value;
}

static int unpackValueInt(unsigned char const **data) {
    int size;

    memcpy(&size, *data, sizeof(size));
    *data += sizeof(size);

    return size;
}

static long unpackValueLong(unsigned char const **data) {
    long size;

    memcpy(&size, *data, sizeof(size));
    *data += sizeof(size);

    return size;
}

static long long unpackValueLongLong(unsigned char const **data) {
    long long size;

    memcpy(&size, *data, sizeof(size));
    *data += sizeof(size);

    return size;
}

static unsigned long long unpackValueUnsignedLongLong(unsigned char const **data) {
    unsigned long long size;

    memcpy(&size, *data, sizeof(size));
    *data += sizeof(size);

    return size;
}

static double unpackValueFloat(unsigned char const **data) {
    double size;

    memcpy(&size, *data, sizeof(size));
    *data += sizeof(size);

    return size;
}

static unsigned char const *_unpackValueCString(unsigned char const *data) {
    while (*(data++) != 0) {
    }

    return data;
}

static PyObject *_unpackAnonValue(unsigned char anon_index) {
    switch (anon_index) {
    case 0:
        return (PyObject *)Py_TYPE(Py_None);
    case 1:
        return (PyObject *)&PyEllipsis_Type;
    case 2:
        return (PyObject *)Py_TYPE(Py_NotImplemented);
    case 3:
        return (PyObject *)&PyFunction_Type;
    case 4:
        return (PyObject *)&PyGen_Type;
    case 5:
        return (PyObject *)&PyCFunction_Type;
    case 6:
        return (PyObject *)&PyCode_Type;

#if PYTHON_VERSION < 300
    case 7:
        return (PyObject *)&PyFile_Type;
    case 8:
        return (PyObject *)&PyClass_Type;
    case 9:
        return (PyObject *)&PyInstance_Type;
    case 10:
        return (PyObject *)&PyMethod_Type;
#endif
    default:
        PRINT_FORMAT("Missing anon value for %d\n", (int)anon_index);
        NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
    }
}

PyObject *_unpackSpecialValue(unsigned char special_index) {
    switch (special_index) {
    case 0:
        return PyObject_GetAttrString((PyObject *)builtin_module, "Ellipsis");
    case 1:
        return PyObject_GetAttrString((PyObject *)builtin_module, "NotImplemented");
    default:
        PRINT_FORMAT("Missing special value for %d\n", (int)special_index);
        NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
    }
}

static unsigned char const *_unpackBlobConstants(PyObject **output, unsigned char const *data, int count) {
    for (int _i = 0; _i < count; _i++) {
        // Make sure we discover failures to assign.
        *output = NULL;
        bool is_object;

        char c = *((char const *)data++);
        // unsigned char const *data_old = data;
        // printf("Type %c for %d of %d:\n", c, _i, count);

        switch (c) {
        case 'T': {
            // TODO: Use fixed sizes
            // uint32_t size = unpackSizeUint32(&data);
            int size = unpackValueInt(&data);

            PyObject *t = PyTuple_New(size);

            if (size > 0) {
                data = _unpackBlobConstants(&PyTuple_GET_ITEM(t, 0), data, size);
            }

            insertToValueCache(&tuple_cache, &t);

            *output = t;
            is_object = true;

            break;
        }
        case 'L': {
            // TODO: Use fixed sizes
            // uint32_t size = unpackSizeUint32(&data);
            int size = unpackValueInt(&data);

            PyObject *l = PyList_New(size);

            if (size > 0) {
                data = _unpackBlobConstants(&PyList_GET_ITEM(l, 0), data, size);
            }

            insertToValueCache(&list_cache, &l);

            *output = l;
            is_object = true;

            break;
        }
        case 'D': {
            // TODO: Use fixed sizes
            // uint32_t size = unpackSizeUint32(&data);
            int size = unpackValueInt(&data);

            PyObject *d = _PyDict_NewPresized(size);

            while (size-- > 0) {
                PyObject *items[2];
                // TODO: Special case string keys only dict.
                data = _unpackBlobConstants(&items[0], data, 2);

                PyDict_SetItem(d, items[0], items[1]);
            }

            insertToValueCache(&dict_cache, &d);

            *output = d;
            is_object = true;

            break;
        }
        case 'P':
        case 'S': {
            // TODO: Use fixed sizes
            // uint32_t size = unpackSizeUint32(&data);
            int size = unpackValueInt(&data);

            PyObject *s;

            if (c == 'S') {
                s = PySet_New(NULL);
            } else {
                if (size == 0) {
                    // Get at the frozenset singleton of CPython and use it too. Some things
                    // rely on it being a singleton across the board.
                    static PyObject *empty_frozenset = NULL;

                    if (empty_frozenset == NULL) {
                        empty_frozenset =
                            CALL_FUNCTION_WITH_SINGLE_ARG((PyObject *)&PyFrozenSet_Type, PyBytes_FromString(""));
                    }

                    s = empty_frozenset;
                } else {
                    s = PyFrozenSet_New(NULL);
                }
            }

            while (size-- > 0) {
                PyObject *value;

                data = _unpackBlobConstants(&value, data, 1);
                PySet_Add(s, value);
            }

            // sets are cached globally too.
            if (c == 'S') {
                insertToValueCache(&set_cache, &s);
            } else {
                insertToValueCache(&frozenset_cache, &s);
            }

            *output = s;
            is_object = true;

            break;
        }
#if PYTHON_VERSION < 300
        case 'i': {
            // TODO: Use fixed sizes for small values, e.g. byte sized.
            long value = unpackValueLong(&data);

            PyObject *i = PyInt_FromLong(value);

            insertToValueCache(&int_cache, &i);

            *output = i;
            is_object = true;

            break;
        }
#endif
        case 'l': {
            // TODO: Use fixed sizes for small values, e.g. byte sized.
            long value = unpackValueLong(&data);

            PyObject *l = PyLong_FromLong(value);

            insertToValueCache(&long_cache, &l);

            *output = l;
            is_object = true;

            break;
        }
        case 'q': {
            long long value = unpackValueLongLong(&data);

            PyObject *l = PyLong_FromLongLong(value);

            insertToValueCache(&long_cache, &l);

            *output = l;
            is_object = true;

            break;
        }
        case 'g': {
            PyObject *result = PyLong_FromLong(0);

            unsigned char sign = *data++;
            int size = unpackValueInt(&data);

            PyObject *shift = PyLong_FromLong(8 * sizeof(unsigned long long));

            for (int i = 0; i < size; i++) {
                result = PyNumber_InPlaceLshift(result, shift);

                unsigned long long value = unpackValueUnsignedLongLong(&data);
                PyObject *part = PyLong_FromUnsignedLongLong(value);
                result = PyNumber_InPlaceAdd(result, part);
                Py_DECREF(part);
            }

            Py_DECREF(shift);

            if (sign == '-') {
                // TODO: There is a negate function
                PyObject *neg = PyLong_FromLong(-1);
                result = PyNumber_InPlaceMultiply(result, neg);
                Py_DECREF(neg);
            }

            insertToValueCache(&long_cache, &result);

            *output = result;
            is_object = true;

            break;
        }
        case 'f': {
            double value = unpackValueFloat(&data);

            PyObject *f = PyFloat_FromDouble(value);

            // Floats are cached globally too.
            insertToValueCache(&float_cache, &f);

            *output = f;
            is_object = true;

            break;
        }
        case 'j': {
            double real = unpackValueFloat(&data);
            double imag = unpackValueFloat(&data);

            *output = PyComplex_FromDoubles(real, imag);
            is_object = true;

            break;
        }
#if PYTHON_VERSION < 300
        case 'a':
#endif
        case 'c': {
            // Python2 str, potentially attributes, or Python3 bytes, zero terminated.

            // TODO: Make this zero copy for non-interned with fake objects?
            PyObject *b = PyBytes_FromString((const char *)data);
            data += PyBytes_GET_SIZE(b) + 1;

#if PYTHON_VERSION < 300
            if (c == 'a') {
                PyString_InternInPlace(&b);
            }
#else
            insertToValueCache(&bytes_cache, &b);
#endif

            *output = b;
            is_object = true;

            break;
        }
        case 'd': {
            // Python2 str length 1 str, potentially attribute, or Python3 single byte

            PyObject *b = PyBytes_FromStringAndSize((const char *)data, 1);
            data += 1;

#if PYTHON_VERSION < 300
            PyString_InternInPlace(&b);
#else
            insertToValueCache(&bytes_cache, &b);
#endif

            *output = b;
            is_object = true;

            break;
        }
        case 'w': {
            // Python2 unicode, Python3 str length 1, potentially attribute in Python3

            PyObject *u = PyUnicode_FromStringAndSize((const char *)data, 1);
            data += 1;

#if PYTHON_VERSION >= 300
            PyUnicode_InternInPlace(&u);
#else
            insertToValueCache(&unicode_cache, &u);
#endif

            *output = u;
            is_object = true;

            break;
        }
        case 'b': {
            // Python2 str or Python3 bytes, length indicated.
            // Python2 str, potentially attributes, or Python3 bytes, zero terminated.

            // TODO: Use fixed sizes for small, e.g. character values, and length vs. 0
            // termination.
            int size = unpackValueInt(&data);

            // TODO: Make this zero copy for non-interned with fake objects?
            PyObject *b = PyBytes_FromStringAndSize((const char *)data, size);
            data += size;

#if PYTHON_VERSION >= 300
            insertToValueCache(&bytes_cache, &b);
#endif

            *output = b;
            is_object = true;

            break;
        }

        case 'B': {
            // TODO: Use fixed sizes for small, e.g. character values, and length vs. 0
            // termination.
            int size = unpackValueInt(&data);

            // TODO: Make this zero copy for non-interned with fake objects?
            PyObject *b = PyByteArray_FromStringAndSize((const char *)data, size);
            data += size;

            *output = b;
            is_object = true;

            break;
        }
#if PYTHON_VERSION >= 300
        case 'a': // Python3 attributes
#endif
        case 'u': { // Python2 unicode, Python3 str, zero terminated.
            size_t size = strlen((const char *)data);
#if PYTHON_VERSION < 300
            PyObject *u = PyUnicode_FromStringAndSize((const char *)data, size);
#else
            PyObject *u = PyUnicode_DecodeUTF8((const char *)data, size, "surrogatepass");
#endif
            data += size + 1;

#if PYTHON_VERSION >= 300
            if (c == 'a') {
                PyUnicode_InternInPlace(&u);
            }
#else
            insertToValueCache(&unicode_cache, &u);
#endif

            *output = u;
            is_object = true;

            break;
        }
        case 'v': {
            int size = unpackValueInt(&data);

#if PYTHON_VERSION < 300
            PyObject *u = PyUnicode_FromStringAndSize((const char *)data, size);
#else
            PyObject *u = PyUnicode_DecodeUTF8((const char *)data, size, "surrogatepass");
#endif
            data += size;

#if PYTHON_VERSION < 300
            insertToValueCache(&unicode_cache, &u);
#endif

            *output = u;
            is_object = true;

            break;
        }
        case 'n': {
            *output = Py_None;
            is_object = true;

            break;
        }
        case 't': {
            *output = Py_True;
            is_object = true;

            break;
        }
        case 'F': {
            *output = Py_False;
            is_object = true;

            break;
        }
        case ':': {
            // Slice object
            PyObject *items[3];
            data = _unpackBlobConstants(&items[0], data, 3);

            PyObject *s = MAKE_SLICEOBJ3(items[0], items[1], items[2]);

            *output = s;
            is_object = true;

            break;
        }
        case ';': {
            // (x)range objects
#if PYTHON_VERSION < 300
            int start = unpackValueInt(&data);
            int stop = unpackValueInt(&data);
            int step = unpackValueInt(&data);

            PyObject *s = MAKE_XRANGE(start, stop, step);
#else
            PyObject *items[3];
            data = _unpackBlobConstants(&items[0], data, 3);

            PyObject *s = BUILTIN_XRANGE3(items[0], items[1], items[2]);
#endif
            *output = s;
            is_object = true;

            break;
        }
        case 'M': {
            // Anonymous builtin by table index value.
            unsigned char anon_index = *data++;

            *output = _unpackAnonValue(anon_index);
            is_object = true;

            break;
        }
        case 'Q': {
            // Anonymous builtin by table index value.
            unsigned char special_index = *data++;

            *output = _unpackSpecialValue(special_index);
            is_object = true;

            break;
        }
        case 'O': {
            // Builtin by name. TODO: Define number table shared by C and Python
            // serialization to avoid using strings here.
            char const *builtin_name = (char const *)data;
            data = _unpackValueCString(data);

            *output = PyObject_GetAttrString((PyObject *)builtin_module, builtin_name);
            is_object = true;

            break;
        }
        case 'E': {
            // Builtin exception by name. TODO: Define number table shared by C and Python
            // serialization to avoid using strings here.
            char const *builtin_exception_name = (char const *)data;
            data = _unpackValueCString(data);

            *output = PyObject_GetAttrString((PyObject *)builtin_module, builtin_exception_name);
            is_object = true;

            break;
        }
        case 'Z': {
            unsigned char v = *data++;

            PyObject *z = NULL;

            switch (v) {
            case 0: {
                static PyObject *_const_float_0_0 = NULL;

                if (_const_float_0_0 == NULL) {
                    _const_float_0_0 = PyFloat_FromDouble(0.0);
                }
                z = _const_float_0_0;

                break;
            }
            case 1: {
                static PyObject *_const_float_plus_nan = NULL;

                if (_const_float_plus_nan == NULL) {
                    _const_float_plus_nan = PyFloat_FromDouble(Py_NAN);

                    // Older Python3 has variable signs for NaN from C, so be explicit about it.
                    PyFloat_AS_DOUBLE(_const_float_plus_nan) = copysign(PyFloat_AS_DOUBLE(_const_float_plus_nan), 1.0);
                }
                z = _const_float_plus_nan;

                break;
            }
            case 2: {
                static PyObject *_const_float_minus_nan = NULL;

                if (_const_float_minus_nan == NULL) {
                    _const_float_minus_nan = PyFloat_FromDouble(Py_NAN);

                    // Older Python3 has variable signs for NaN from C, so be explicit about it.
                    PyFloat_AS_DOUBLE(_const_float_minus_nan) =
                        copysign(PyFloat_AS_DOUBLE(_const_float_minus_nan), -1.0);
                }
                z = _const_float_minus_nan;

                break;
            }
            case 3: {
                static PyObject *_const_float_plus_inf = NULL;

                if (_const_float_plus_inf == NULL) {
                    _const_float_plus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

                    // Older Python3 has variable signs for NaN from C, so be explicit about it.
                    PyFloat_AS_DOUBLE(_const_float_plus_inf) = copysign(PyFloat_AS_DOUBLE(_const_float_plus_inf), 1.0);
                }
                z = _const_float_plus_inf;

                break;
            }
            case 4: {
                static PyObject *_const_float_minus_inf = NULL;

                if (_const_float_minus_inf == NULL) {
                    _const_float_minus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

                    // Older Python3 has variable signs for NaN from C, so be explicit about it.
                    PyFloat_AS_DOUBLE(_const_float_minus_inf) =
                        copysign(PyFloat_AS_DOUBLE(_const_float_minus_inf), -1.0);
                }
                z = _const_float_minus_inf;

                break;
            }
            default: {
                PRINT_FORMAT("Missing decoding for %d\n", (int)c);
                NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
            }
            }

            // Floats are cached globally too.
            insertToValueCache(&float_cache, &z);

            *output = z;
            is_object = true;

            break;
        }
        case 'X': {
            // Blob data pointer, user knowns size.
            int size = unpackValueInt(&data);

            *output = (PyObject *)data;
            is_object = false;

            data += size;

            break;
        }
        default:
            PRINT_FORMAT("Missing decoding for %d\n", (int)c);
            NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
        }

        CHECK_OBJECT(*output);

        // printf("Size for %c was %d\n", c, data - data_old);

        // Discourage in-place operations from modifying these. These
        // might be put into containers, therefore take 2 refs to be
        // accounting for the container too.
        if (is_object == true) {
            Py_INCREF(*output);
            Py_INCREF(*output);
        }

        // PRINT_ITEM(*output);
        // PRINT_NEW_LINE();

        output += 1;
    }

    return data;
}

static void unpackBlobConstants(PyObject **output, unsigned char const *data, int count) {
    _unpackBlobConstants(output, data, count);
}

void loadConstantsBlob(PyObject **output, char const *name, int count) {
    initCaches();

    unsigned char const *w = constant_bin;

    for (;;) {
        int match = strcmp(name, (char const *)w);
        w += strlen((char const *)w) + 1;
        int size = *((int *)w);
        w += sizeof(size);

        if (match == 0) {
            break;
        }

        // Skip other module data.
        w += size;
    }

    unpackBlobConstants(output, w, count);
}

#ifndef __NUITKA_NO_ASSERT__
void checkConstantsBlob(PyObject **output, char const *name, int count) {
    // TODO: Unpack and check for correct values in output only.
}
#endif