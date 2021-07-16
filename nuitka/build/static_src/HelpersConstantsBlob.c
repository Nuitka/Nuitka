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

#include <stdint.h>

#if defined(_NUITKA_CONSTANTS_FROM_LINKER)
// Symbol as provided by the linker, different for C++ and C11 mode.
#ifdef __cplusplus
extern "C" const unsigned char constant_bin_data[];
#else
extern const unsigned char constant_bin_data[0];
#endif

// Symbol to be assigned locally.
unsigned char const *constant_bin = &constant_bin_data[0];

#else
// Symbol to be assigned locally.
unsigned char const *constant_bin = NULL;
#endif

#if defined(_NUITKA_CONSTANTS_FROM_INCBIN)
extern unsigned const char *getConstantsBlobData();
#endif

// No Python runtime yet, need to do this manually.
static uint32_t calcCRC32(unsigned char const *message, uint32_t size) {
    uint32_t crc = 0xFFFFFFFF;

    for (uint32_t i = 0; i < size; i++) {
        unsigned int c = message[i];
        crc = crc ^ c;

        for (int j = 7; j >= 0; j--) {
            uint32_t mask = ((crc & 1) != 0) ? 0xFFFFFFFF : 0;
            crc = (crc >> 1) ^ (0xEDB88320 & mask);
        }
    }

    return ~crc;
}

#if PYTHON_VERSION < 0x300
static PyObject *int_cache = NULL;
#endif

static PyObject *long_cache = NULL;

static PyObject *float_cache = NULL;

#if PYTHON_VERSION >= 0x300
static PyObject *bytes_cache = NULL;
#endif

#if PYTHON_VERSION < 0x300
static PyObject *unicode_cache = NULL;
#endif

static PyObject *tuple_cache = NULL;

static PyObject *list_cache = NULL;

static PyObject *dict_cache = NULL;

static PyObject *set_cache = NULL;

static PyObject *frozenset_cache = NULL;

// Use our own non-random hash for some of the things to be fast. This is inspired
// from the original Python2 hash func, but we are mostly using it on pointer values
static Py_hash_t Nuitka_FastHashBytes(const void *value, Py_ssize_t size) {
    if (unlikely(size == 0)) {
        return 0;
    }

    unsigned char *w = (unsigned char *)value;
    long x = *w << 7;

    while (--size >= 0) {
        x = (1000003 * x) ^ *w++;
    }

    x ^= size;

    // The value -1 is reserved for errors.
    if (x == -1) {
        x = -2;
    }

    return x;
}

static Py_hash_t our_list_hash(PyListObject *list) {
    return Nuitka_FastHashBytes(&list->ob_item[0], Py_SIZE(list) * sizeof(PyObject *));
}

static PyObject *our_list_richcompare(PyListObject *list1, PyListObject *list2, int op) {
    assert(op == Py_EQ);

    PyObject *result;

    if (list1 == list2) {
        result = Py_True;
    } else if (Py_SIZE(list1) != Py_SIZE(list2)) {
        result = Py_False;
    } else if (memcmp(&list1->ob_item[0], &list2->ob_item[0], Py_SIZE(list1) * sizeof(PyObject *)) == 0) {
        result = Py_True;
    } else {
        result = Py_False;
    }

    Py_INCREF(result);
    return result;
}

static Py_hash_t our_tuple_hash(PyTupleObject *tuple) {
    return Nuitka_FastHashBytes(&tuple->ob_item[0], Py_SIZE(tuple) * sizeof(PyObject *));
}

static PyObject *our_tuple_richcompare(PyTupleObject *tuple1, PyTupleObject *tuple2, int op) {
    assert(op == Py_EQ);

    PyObject *result;

    if (tuple1 == tuple2) {
        result = Py_True;
    } else if (Py_SIZE(tuple1) != Py_SIZE(tuple2)) {
        result = Py_False;
    } else if (memcmp(&tuple1->ob_item[0], &tuple2->ob_item[0], Py_SIZE(tuple1) * sizeof(PyObject *)) == 0) {
        result = Py_True;
    } else {
        result = Py_False;
    }

    Py_INCREF(result);
    return result;
}

static Py_hash_t our_set_hash(PyObject *set) {
    Py_hash_t result = 0;
    PyObject *key;
    Py_ssize_t pos = 0;

#if PYTHON_VERSION < 0x300
    // Same sized set, simply check if values are identical. Other reductions should
    // make it identical, or else this won't have the effect intended.
    while (_PySet_Next(set, &pos, &key)) {
        result *= 1000003;
        result ^= Nuitka_FastHashBytes(key, sizeof(PyObject *));
    }
#else
    Py_hash_t unused;

    while (_PySet_NextEntry(set, &pos, &key, &unused)) {
        result *= 1000003;
        result ^= Nuitka_FastHashBytes(key, sizeof(PyObject *));
    }
#endif

    return result;
}

static PyObject *our_set_richcompare(PyObject *set1, PyObject *set2, int op) {
    assert(op == Py_EQ);

    Py_ssize_t pos1 = 0, pos2 = 0;
    PyObject *key1, *key2;

#if PYTHON_VERSION < 0x300
    // Same sized set, simply check if values are identical. Other reductions should
    // make it identical, or else this won't have the effect intended.
    while (_PySet_Next(set1, &pos1, &key1)) {
        int res = _PySet_Next(set2, &pos2, &key2);
        assert(res != 0);

        if (key1 != key2) {
            PyObject *result = Py_False;
            Py_INCREF(result);
            return result;
        }
    }
#else
    Py_hash_t unused;

    // Same sized dictionary, simply check if values are identical. Other reductions should
    // make it identical, or else this won't have the effect intended.
    while (_PySet_NextEntry(set1, &pos1, &key1, &unused)) {
        int res = _PySet_NextEntry(set2, &pos2, &key2, &unused);
        assert(res != 0);

        if (key1 != key2) {
            PyObject *result = Py_False;
            Py_INCREF(result);
            return result;
        }
    }

#endif

    PyObject *result = Py_True;
    Py_INCREF(result);
    return result;
}

static PyObject *our_float_richcompare(PyFloatObject *a, PyFloatObject *b, int op) {
    assert(op == Py_EQ);

    PyObject *result;

    // Avoid the C math when comparing, for it makes too many values equal or unequal.
    if (memcmp(&a->ob_fval, &b->ob_fval, sizeof(b->ob_fval)) == 0) {
        result = Py_True;
    } else {
        result = Py_False;
    }

    Py_INCREF(result);
    return result;
}

static Py_hash_t our_dict_hash(PyObject *dict) {
    Py_hash_t result = 0;

    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while (PyDict_Next(dict, &ppos, &key, &value)) {
        result *= 1000003;
        result ^= Nuitka_FastHashBytes(key, sizeof(PyObject *));
        result *= 1000003;
        result ^= Nuitka_FastHashBytes(value, sizeof(PyObject *));
    }

    return result;
}

static PyObject *our_dict_richcompare(PyObject *a, PyObject *b, int op) {
    PyObject *result;

    if (Py_SIZE(a) != Py_SIZE(b)) {
        result = Py_False;
    } else {
        result = Py_True;

        Py_ssize_t ppos1 = 0, ppos2 = 0;
        PyObject *key1, *value1;
        PyObject *key2, *value2;

        // Same sized dictionary, simply check if key and values are identical.
        // Other reductions should make it identical, or else this won't have the
        // effect intended.
        while (PyDict_Next(a, &ppos1, &key1, &value1)) {
            int res = PyDict_Next(b, &ppos2, &key2, &value2);
            assert(res != 0);

            if (key1 != key2 || value1 != value2) {
                result = Py_False;
                break;
            }
        }
    }

    Py_INCREF(result);
    return result;
}

#if PYTHON_VERSION >= 0x300
// For creation of small long singleton long values as required by Python3.
PyObject *Nuitka_Long_SmallValues[NUITKA_STATIC_SMALLINT_VALUE_MAX - NUITKA_STATIC_SMALLINT_VALUE_MIN + 1];
#endif

static void initCaches(void) {
    static bool init_done = false;
    if (init_done == true) {
        return;
    }

#if PYTHON_VERSION < 0x300
    int_cache = PyDict_New();
#endif

    long_cache = PyDict_New();

    float_cache = PyDict_New();

#if PYTHON_VERSION >= 0x300
    bytes_cache = PyDict_New();
#endif

#if PYTHON_VERSION < 0x300
    unicode_cache = PyDict_New();
#endif

    tuple_cache = PyDict_New();

    list_cache = PyDict_New();

    dict_cache = PyDict_New();

    set_cache = PyDict_New();

    frozenset_cache = PyDict_New();

    for (long i = NUITKA_STATIC_SMALLINT_VALUE_MIN; i <= NUITKA_STATIC_SMALLINT_VALUE_MAX; i++) {
#if PYTHON_VERSION >= 0x300
        PyObject *value = PyLong_FromLong(i);
        Py_INCREF(value);

        Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(i)] = value;
#endif
    }

    init_done = true;
}

static void insertToDictCache(PyObject *dict, PyObject **value) {
    PyObject *item = PyDict_GetItem(dict, *value);

    if (item != NULL) {
        *value = item;
    } else {
        PyDict_SetItem(dict, *value, *value);
    }
}

static void insertToDictCacheForcedHash(PyObject *dict, PyObject **value, hashfunc tp_hash,
                                        richcmpfunc tp_richcompare) {
    hashfunc old_hash = Py_TYPE(*value)->tp_hash;
    richcmpfunc old_richcmp = Py_TYPE(*value)->tp_richcompare;

    // Hash is optional, e.g. for floats we can spare us doing our own hash,
    // but we do equality
    if (tp_hash != NULL) {
        Py_TYPE(*value)->tp_hash = tp_hash;
    }
    Py_TYPE(*value)->tp_richcompare = tp_richcompare;

    insertToDictCache(dict, value);

    Py_TYPE(*value)->tp_hash = old_hash;
    Py_TYPE(*value)->tp_richcompare = old_richcmp;
}

static uint16_t unpackValueUint16(unsigned char const **data) {
    uint16_t value;

    memcpy(&value, *data, sizeof(value));

    assert(sizeof(value) == 2);

    *data += sizeof(value);

    return value;
}

static uint32_t unpackValueUint32(unsigned char const **data) {
    uint32_t value;

    memcpy(&value, *data, sizeof(value));

    assert(sizeof(value) == 4);

    *data += sizeof(value);

    return value;
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

#if PYTHON_VERSION < 0x300
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
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        unsigned char const *data_old = data;
        PRINT_FORMAT("Type %c for %d of %d:\n", c, _i, count);
#endif
        switch (c) {
        case 'T': {
            // TODO: Use fixed sizes
            // uint32_t size = unpackSizeUint32(&data);
            int size = unpackValueInt(&data);

            PyObject *t = PyTuple_New(size);

            if (size > 0) {
                data = _unpackBlobConstants(&PyTuple_GET_ITEM(t, 0), data, size);
            }

            insertToDictCacheForcedHash(tuple_cache, &t, (hashfunc)our_tuple_hash, (richcmpfunc)our_tuple_richcompare);

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

            insertToDictCacheForcedHash(list_cache, &l, (hashfunc)our_list_hash, (richcmpfunc)our_list_richcompare);

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

            insertToDictCacheForcedHash(dict_cache, &d, (hashfunc)our_dict_hash, (richcmpfunc)our_dict_richcompare);

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
                insertToDictCacheForcedHash(set_cache, &s, (hashfunc)our_set_hash, (richcmpfunc)our_set_richcompare);
            } else {
                insertToDictCacheForcedHash(frozenset_cache, &s, (hashfunc)our_set_hash,
                                            (richcmpfunc)our_set_richcompare);
            }

            *output = s;
            is_object = true;

            break;
        }
#if PYTHON_VERSION < 0x300
        case 'i': {
            // TODO: Use fixed sizes for small values, e.g. byte sized.
            long value = unpackValueLong(&data);

            PyObject *i = PyInt_FromLong(value);

            insertToDictCache(int_cache, &i);

            *output = i;
            is_object = true;

            break;
        }
#endif
        case 'l': {
            // TODO: Use fixed sizes for small values, e.g. byte sized.
            long value = unpackValueLong(&data);

            PyObject *l = PyLong_FromLong(value);

            insertToDictCache(long_cache, &l);

            *output = l;
            is_object = true;

            break;
        }
        case 'q': {
            long long value = unpackValueLongLong(&data);

            PyObject *l = PyLong_FromLongLong(value);

            insertToDictCache(long_cache, &l);

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

            insertToDictCache(long_cache, &result);

            *output = result;
            is_object = true;

            break;
        }
        case 'f': {
            double value = unpackValueFloat(&data);

            PyObject *f = PyFloat_FromDouble(value);

            // Floats are cached globally too.
            insertToDictCacheForcedHash(float_cache, &f, NULL, (richcmpfunc)our_float_richcompare);

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
        case 'J': {
            PyObject *parts[2];

            // Complex via float is done for ones that are 0, nan, float.
            data = _unpackBlobConstants(&parts[0], data, 2);

            *output = BUILTIN_COMPLEX2(parts[0], parts[1]);
            is_object = true;

            break;
        }
#if PYTHON_VERSION < 0x300
        case 'a':
#endif
        case 'c': {
            // Python2 str, potentially attributes, or Python3 bytes, zero terminated.

            size_t size = strlen((const char *)data);

            // TODO: Make this zero copy for non-interned with fake objects?
            PyObject *b = PyBytes_FromStringAndSize((const char *)data, size);
            data += size + 1;

#if PYTHON_VERSION < 0x300
            if (c == 'a') {
                PyString_InternInPlace(&b);
            }
#else
            insertToDictCache(bytes_cache, &b);
#endif

            *output = b;
            is_object = true;

            break;
        }
        case 'd': {
            // Python2 str length 1 str, potentially attribute, or Python3 single byte

            PyObject *b = PyBytes_FromStringAndSize((const char *)data, 1);
            data += 1;

#if PYTHON_VERSION < 0x300
            PyString_InternInPlace(&b);
#else
            insertToDictCache(bytes_cache, &b);
#endif

            *output = b;
            is_object = true;

            break;
        }
        case 'w': {
            // Python2 unicode, Python3 str length 1, potentially attribute in Python3

            PyObject *u = PyUnicode_FromStringAndSize((const char *)data, 1);
            data += 1;

#if PYTHON_VERSION >= 0x300
            PyUnicode_InternInPlace(&u);
#else
            insertToDictCache(unicode_cache, &u);
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

#if PYTHON_VERSION >= 0x300
            insertToDictCache(bytes_cache, &b);
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
#if PYTHON_VERSION >= 0x300
        case 'a': // Python3 attributes
#endif
        case 'u': { // Python2 unicode, Python3 str, zero terminated.
            size_t size = strlen((const char *)data);
#if PYTHON_VERSION < 0x300
            PyObject *u = PyUnicode_FromStringAndSize((const char *)data, size);
#else
            PyObject *u = PyUnicode_DecodeUTF8((const char *)data, size, "surrogatepass");
#endif
            data += size + 1;

#if PYTHON_VERSION >= 0x300
            if (c == 'a') {
                PyUnicode_InternInPlace(&u);
            }
#else
            insertToDictCache(unicode_cache, &u);
#endif

            *output = u;
            is_object = true;

            break;
        }
        case 'v': {
            int size = unpackValueInt(&data);

#if PYTHON_VERSION < 0x300
            PyObject *u = PyUnicode_FromStringAndSize((const char *)data, size);
#else
            PyObject *u = PyUnicode_DecodeUTF8((const char *)data, size, "surrogatepass");
#endif
            data += size;

#if PYTHON_VERSION < 0x300
            insertToDictCache(unicode_cache, &u);
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
#if PYTHON_VERSION < 0x300
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
                static PyObject *_const_float_minus_0_0 = NULL;

                if (_const_float_minus_0_0 == NULL) {
                    _const_float_minus_0_0 = PyFloat_FromDouble(0.0);

                    // Older Python3 has variable signs from C, so be explicit about it.
                    PyFloat_AS_DOUBLE(_const_float_minus_0_0) =
                        copysign(PyFloat_AS_DOUBLE(_const_float_minus_0_0), -1.0);
                }
                z = _const_float_minus_0_0;

                break;
            }

            case 2: {
                static PyObject *_const_float_plus_nan = NULL;

                if (_const_float_plus_nan == NULL) {
                    _const_float_plus_nan = PyFloat_FromDouble(Py_NAN);

                    // Older Python3 has variable signs for NaN from C, so be explicit about it.
                    PyFloat_AS_DOUBLE(_const_float_plus_nan) = copysign(PyFloat_AS_DOUBLE(_const_float_plus_nan), 1.0);
                }
                z = _const_float_plus_nan;

                break;
            }
            case 3: {
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
            case 4: {
                static PyObject *_const_float_plus_inf = NULL;

                if (_const_float_plus_inf == NULL) {
                    _const_float_plus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

                    // Older Python3 has variable signs from C, so be explicit about it.
                    PyFloat_AS_DOUBLE(_const_float_plus_inf) = copysign(PyFloat_AS_DOUBLE(_const_float_plus_inf), 1.0);
                }
                z = _const_float_plus_inf;

                break;
            }
            case 5: {
                static PyObject *_const_float_minus_inf = NULL;

                if (_const_float_minus_inf == NULL) {
                    _const_float_minus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

                    // Older Python3 has variable signs from C, so be explicit about it.
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
            insertToDictCacheForcedHash(float_cache, &z, NULL, (richcmpfunc)our_float_richcompare);

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
#if PYTHON_VERSION >= 0x390
        case 'G': {
            // Slice object
            PyObject *items[2];
            data = _unpackBlobConstants(&items[0], data, 2);

            PyObject *g = Py_GenericAlias(items[0], items[1]);

            // TODO: Maybe deduplicate.
            *output = g;

            is_object = true;
            break;
        }
#endif
        case '.': {
            PRINT_FORMAT("Missing values %d\n", count - _i);
            NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
        }
        default:
            PRINT_FORMAT("Missing decoding for %d\n", (int)c);
            NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
        }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        printf("Size for %c was %d\n", c, data - data_old);
#endif

        // Discourage in-place operations from modifying these. These
        // might be put into containers, therefore take 2 refs to be
        // accounting for the container too.
        if (is_object == true) {
            CHECK_OBJECT(*output);

            Py_INCREF(*output);
            Py_INCREF(*output);
        }

        // PRINT_ITEM(*output);
        // PRINT_NEW_LINE();

        output += 1;
    }

    return data;
}

static void unpackBlobConstants(PyObject **output, unsigned char const *data) {
    int count = (int)unpackValueUint16(&data);

    _unpackBlobConstants(output, data, count);
}

void loadConstantsBlob(PyObject **output, char const *name) {
    static bool init_done = false;

    if (init_done == false) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        PRINT_STRING("loadConstantsBlob one time init\n");
#endif

#if defined(_NUITKA_CONSTANTS_FROM_INCBIN)
        constant_bin = getConstantsBlobData();
#elif defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
#ifdef _NUITKA_EXE
        // Using NULL as this indicates running program.
        HMODULE handle = NULL;
#else
        HMODULE handle = getDllModuleHandle();
#endif

        constant_bin = (const unsigned char *)LockResource(
            LoadResource(handle, FindResource(handle, MAKEINTRESOURCE(3), RT_RCDATA)));

        assert(constant_bin);
#endif
        DECODE(constant_bin);

        uint32_t hash = unpackValueUint32(&constant_bin);
        uint32_t size = unpackValueUint32(&constant_bin);

        if (calcCRC32(constant_bin, size) != hash) {
            puts("Error, corrupted constants object");
            abort();
        }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        PRINT_FORMAT("Checked CRC32 to match hash %u size %u\n", hash, size);
#endif

        init_done = true;
    }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
    PRINT_FORMAT("Loading blob named '%s' with %d values\n", name, count);
#endif
    // Python 3.9 or higher cannot create dictionary before calling init so avoid it.
    if (strcmp(name, ".bytecode") != 0) {
        initCaches();
    }

    unsigned char const *w = constant_bin;

    for (;;) {
        int match = strcmp(name, (char const *)w);
        w += strlen((char const *)w) + 1;

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        PRINT_FORMAT("offset of blob size %d\n", w - constant_bin);
#endif

        uint32_t size = unpackValueUint32(&w);

        if (match == 0) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
            PRINT_FORMAT("Loading blob named '%s' with %d values and size %d\n", name, count, size);
#endif
            break;
        }

        // Skip other module data.
        w += size;
    }

    unpackBlobConstants(output, w);
}

#ifndef __NUITKA_NO_ASSERT__
void checkConstantsBlob(PyObject **output, char const *name) {
    // TODO: Unpack and check for correct values in output only.
}
#endif