//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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

#if _NUITKA_EXPERIMENTAL_WRITEABLE_CONSTANTS
#define CONST_CONSTANT
#else
#define CONST_CONSTANT const
#endif

#if defined(_NUITKA_CONSTANTS_FROM_LINKER)
// Symbol as provided by the linker, different for C++ and C11 mode.
#ifdef __cplusplus
extern "C" CONST_CONSTANT unsigned char constant_bin_data[];
#else
extern CONST_CONSTANT unsigned char constant_bin_data[0];
#endif

unsigned char const *constant_bin = &constant_bin_data[0];

#elif defined(_NUITKA_CONSTANTS_FROM_CODE)
extern CONST_CONSTANT unsigned char constant_bin_data[];

unsigned char const *constant_bin = &constant_bin_data[0];
#else
// Symbol to be assigned locally.
unsigned char const *constant_bin = NULL;
#endif

#if defined(_NUITKA_CONSTANTS_FROM_INCBIN)
extern unsigned const char *getConstantsBlobData(void);
#endif

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

    Py_INCREF_IMMORTAL(result);
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

    Py_INCREF_IMMORTAL(result);
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
        result ^= Nuitka_FastHashBytes(&key, sizeof(PyObject *));
    }
#else
    Py_hash_t unused;

    while (_PySet_NextEntry(set, &pos, &key, &unused)) {
        result *= 1000003;
        result ^= Nuitka_FastHashBytes(&key, sizeof(PyObject *));
    }
#endif

    return result;
}

static PyObject *our_set_richcompare(PyObject *set1, PyObject *set2, int op) {
    assert(op == Py_EQ);

    PyObject *result;

    Py_ssize_t pos1 = 0, pos2 = 0;
    PyObject *key1, *key2;

    if (Py_SIZE(set1) != Py_SIZE(set2)) {
        result = Py_False;
    } else {
        result = Py_True;

#if PYTHON_VERSION < 0x300
        // Same sized set, simply check if values are identical. Other reductions should
        // make it identical, or else this won't have the effect intended.
        while (_PySet_Next(set1, &pos1, &key1)) {
            {
                NUITKA_MAY_BE_UNUSED int res = _PySet_Next(set2, &pos2, &key2);
                assert(res != 0);
            }

            if (key1 != key2) {
                result = Py_False;
                break;
            }
        }
#else
        Py_hash_t unused1, unused2;

        // Same sized dictionary, simply check if values are identical. Other reductions should
        // make it identical, or else this won't have the effect intended.
        while (_PySet_NextEntry(set1, &pos1, &key1, &unused1)) {
            {
                NUITKA_MAY_BE_UNUSED int res = _PySet_NextEntry(set2, &pos2, &key2, &unused2);
                assert(res != 0);
            }

            if (key1 != key2) {
                result = Py_False;
                break;
            }
        }
#endif
    }

    Py_INCREF_IMMORTAL(result);
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

    Py_INCREF_IMMORTAL(result);
    return result;
}

static Py_hash_t our_dict_hash(PyObject *dict) {
    Py_hash_t result = 0;

    Py_ssize_t pos = 0;
    PyObject *key, *value;

    while (Nuitka_DictNext(dict, &pos, &key, &value)) {
        result *= 1000003;
        result ^= Nuitka_FastHashBytes(&key, sizeof(PyObject *));
        result *= 1000003;
        result ^= Nuitka_FastHashBytes(&value, sizeof(PyObject *));
    }

    return result;
}

static PyObject *our_dict_richcompare(PyObject *a, PyObject *b, int op) {
    PyObject *result;

    if (Py_SIZE(a) != Py_SIZE(b)) {
        result = Py_False;
    } else {
        result = Py_True;

        Py_ssize_t pos1 = 0, pos2 = 0;
        PyObject *key1, *value1;
        PyObject *key2, *value2;

        // Same sized dictionary, simply check if key and values are identical.
        // Other reductions should make it identical, or else this won't have the
        // effect intended.
        while (Nuitka_DictNext(a, &pos1, &key1, &value1)) {
            {
                NUITKA_MAY_BE_UNUSED int res = Nuitka_DictNext(b, &pos2, &key2, &value2);
                assert(res != 0);
            }

            if (key1 != key2 || value1 != value2) {
                result = Py_False;
                break;
            }
        }
    }

    Py_INCREF_IMMORTAL(result);
    return result;
}

// For creation of small long singleton long values as required by Python3.
#if PYTHON_VERSION < 0x3b0
#if PYTHON_VERSION >= 0x390
PyObject **Nuitka_Long_SmallValues;
#elif PYTHON_VERSION >= 0x300
PyObject *Nuitka_Long_SmallValues[NUITKA_STATIC_SMALLINT_VALUE_MAX - NUITKA_STATIC_SMALLINT_VALUE_MIN + 1];
#endif
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

#if PYTHON_VERSION < 0x3b0
#if PYTHON_VERSION >= 0x390
    // On Python3.9+ these are exposed in the interpreter.
    Nuitka_Long_SmallValues = (PyObject **)_PyInterpreterState_GET()->small_ints;
#elif PYTHON_VERSION >= 0x300
    for (long i = NUITKA_STATIC_SMALLINT_VALUE_MIN; i < NUITKA_STATIC_SMALLINT_VALUE_MAX; i++) {
        // Have to use the original API here since out "Nuitka_PyLong_FromLong"
        // would insist on using "Nuitka_Long_SmallValues" to produce it.
        PyObject *value = PyLong_FromLong(i);
        Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(i)] = value;
    }
#endif
#endif

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

// Decoding Variable-length quantity values
static uint64_t _unpackVariableLength(unsigned char const **data) {
    uint64_t result = 0;
    uint64_t factor = 1;

    while (1) {
        unsigned char value = **data;
        *data += 1;

        result += (value & 127) * factor;

        if (value < 128) {
            break;
        }

        factor <<= 7;
    }

    return result;
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
    case 7:
        return (PyObject *)&PyModule_Type;

#if PYTHON_VERSION < 0x300
    case 8:
        return (PyObject *)&PyFile_Type;
    case 9:
        return (PyObject *)&PyClass_Type;
    case 10:
        return (PyObject *)&PyInstance_Type;
    case 11:
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
    case 2:
        return Py_SysVersionInfo;
    default:
        PRINT_FORMAT("Missing special value for %d\n", (int)special_index);
        NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
    }
}

static unsigned char const *_unpackBlobConstants(PyThreadState *tstate, PyObject **output, unsigned char const *data,
                                                 int count);

static unsigned char const *_unpackBlobConstant(PyThreadState *tstate, PyObject **output, unsigned char const *data) {

    // Make sure we discover failures to assign.
    *output = NULL;
    bool is_object;

    char c = *((char const *)data++);
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
    unsigned char const *data_old = data;
    printf("Type %c for %d of %d:\n", c, _i, count);
#endif
    switch (c) {

    case 'p': {
        *output = *(output - 1);
        is_object = true;

        break;
    }
    case 'T': {
        int size = (int)_unpackVariableLength(&data);

        PyObject *t = PyTuple_New(size);

        if (size > 0) {
            data = _unpackBlobConstants(tstate, &PyTuple_GET_ITEM(t, 0), data, size);
        }

        insertToDictCacheForcedHash(tuple_cache, &t, (hashfunc)our_tuple_hash, (richcmpfunc)our_tuple_richcompare);

        *output = t;
        is_object = true;

        break;
    }
    case 'L': {
        int size = (int)_unpackVariableLength(&data);

        PyObject *l = PyList_New(size);

        if (size > 0) {
            data = _unpackBlobConstants(tstate, &PyList_GET_ITEM(l, 0), data, size);
        }

        insertToDictCacheForcedHash(list_cache, &l, (hashfunc)our_list_hash, (richcmpfunc)our_list_richcompare);

        *output = l;
        is_object = true;

        break;
    }
    case 'D': {
        int size = (int)_unpackVariableLength(&data);

        PyObject *d = _PyDict_NewPresized(size);

        if (size > 0) {
            NUITKA_DYNAMIC_ARRAY_DECL(keys, PyObject *, size);
            NUITKA_DYNAMIC_ARRAY_DECL(values, PyObject *, size);

            data = _unpackBlobConstants(tstate, &keys[0], data, size);
            data = _unpackBlobConstants(tstate, &values[0], data, size);

            for (int i = 0; i < size; i++) {
                PyDict_SetItem(d, keys[i], values[i]);
            }
        }

        insertToDictCacheForcedHash(dict_cache, &d, (hashfunc)our_dict_hash, (richcmpfunc)our_dict_richcompare);

        *output = d;
        is_object = true;

        break;
    }
    case 'P':
    case 'S': {
        int size = (int)_unpackVariableLength(&data);

        PyObject *s;

        if (c == 'S') {
            s = PySet_New(NULL);
        } else {
            if (size == 0) {
                // Get at the frozenset singleton of CPython and use it too. Some things
                // rely on it being a singleton across the board.
                static PyObject *empty_frozenset = NULL;

                if (empty_frozenset == NULL) {
                    empty_frozenset = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, (PyObject *)&PyFrozenSet_Type,
                                                                    Nuitka_Bytes_FromStringAndSize("", 0));
                }

                s = empty_frozenset;
            } else {
                s = PyFrozenSet_New(NULL);
            }
        }

        if (size > 0) {
            NUITKA_DYNAMIC_ARRAY_DECL(values, PyObject *, size);

            data = _unpackBlobConstants(tstate, &values[0], data, size);

            for (int i = 0; i < size; i++) {
                PySet_Add(s, values[i]);
            }
        }

        // sets are cached globally too.
        if (c == 'S') {
            insertToDictCacheForcedHash(set_cache, &s, (hashfunc)our_set_hash, (richcmpfunc)our_set_richcompare);
        } else {
            insertToDictCacheForcedHash(frozenset_cache, &s, (hashfunc)our_set_hash, (richcmpfunc)our_set_richcompare);
        }

        *output = s;
        is_object = true;

        break;
    }
#if PYTHON_VERSION < 0x300
    case 'I':
    case 'i': {
        long value = (long)_unpackVariableLength(&data);
        if (c == 'I') {
            value = -value;
        }

        PyObject *i = PyInt_FromLong(value);

        insertToDictCache(int_cache, &i);

        *output = i;
        is_object = true;

        break;
    }
#endif
    case 'l':
    case 'q': {
        // Positive/negative integer value with abs value < 2**31
        uint64_t value = _unpackVariableLength(&data);

        PyObject *l = Nuitka_LongFromCLong((c == 'l') ? ((long)value) : (-(long)value));
        assert(l != NULL);

        // Avoid the long cache, won't do anything useful for small ints
#if PYTHON_VERSION >= 0x300
        if (value < NUITKA_STATIC_SMALLINT_VALUE_MIN || value >= NUITKA_STATIC_SMALLINT_VALUE_MAX)
#endif
        {
            insertToDictCache(long_cache, &l);
        }

        *output = l;
        is_object = true;

        break;
    }
    case 'G':
    case 'g': {
        PyObject *result = Nuitka_PyLong_FromLong(0);

        int size = (int)_unpackVariableLength(&data);

        PyObject *shift = Nuitka_PyLong_FromLong(31);

        for (int i = 0; i < size; i++) {
            result = PyNumber_InPlaceLshift(result, shift);

            uint64_t value = _unpackVariableLength(&data);
            PyObject *part = Nuitka_LongFromCLong((long)value);
            assert(part != NULL);
            result = PyNumber_InPlaceAdd(result, part);
            Py_DECREF(part);
        }

        Py_DECREF(shift);

        if (c == 'G') {
            Nuitka_LongSetSignNegative(result);
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
        data = _unpackBlobConstants(tstate, &parts[0], data, 2);

        *output = BUILTIN_COMPLEX2(tstate, parts[0], parts[1]);
        is_object = true;

        break;
    }
#if PYTHON_VERSION < 0x300
    case 'a':
    case 'c': {
        // Python2 str, potentially attribute, zero terminated.
        size_t size = strlen((const char *)data);

        PyObject *s = PyString_FromStringAndSize((const char *)data, size);
        CHECK_OBJECT(s);

        data += size + 1;

        if (c == 'a') {
            PyString_InternInPlace(&s);
        }

        *output = s;
        is_object = true;

        break;
    }
#else
    case 'c': {
        // Python3 bytes, zero terminated.
        size_t size = strlen((const char *)data);

        PyObject *b = Nuitka_Bytes_FromStringAndSize((const char *)data, size);
        CHECK_OBJECT(b);

        data += size + 1;

        // Empty bytes value is here as well.
        if (size > 1) {
            insertToDictCache(bytes_cache, &b);
        }

        *output = b;
        is_object = true;

        break;
    }
#endif
    case 'd': {
        // Python2 str length 1 str, potentially attribute, or Python3 single byte

#if PYTHON_VERSION < 0x300
        PyObject *s = PyString_FromStringAndSize((const char *)data, 1);
        data += 1;
        *output = s;
#else
        PyObject *b = Nuitka_Bytes_FromStringAndSize((const char *)data, 1);
        data += 1;
        *output = b;
#endif

        is_object = true;

        break;
    }
    case 'w': {
        // Python2 unicode, Python3 str length 1, potentially attribute in Python3

        PyObject *u = PyUnicode_FromStringAndSize((const char *)data, 1);
        data += 1;

#if PYTHON_VERSION >= 0x3c7
        _PyUnicode_InternImmortal(tstate->interp, &u);
#elif PYTHON_VERSION >= 0x300
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
        int size = (int)_unpackVariableLength(&data);
        assert(size > 1);

        PyObject *b = Nuitka_Bytes_FromStringAndSize((const char *)data, size);
        CHECK_OBJECT(b);

        data += size;

#if PYTHON_VERSION >= 0x300
        insertToDictCache(bytes_cache, &b);
#endif

        *output = b;
        is_object = true;

        break;
    }

    case 'B': {
        int size = (int)_unpackVariableLength(&data);

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

#if PYTHON_VERSION >= 0x3c7
        _PyUnicode_InternImmortal(tstate->interp, &u);
#elif PYTHON_VERSION >= 0x300
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
        int size = (int)_unpackVariableLength(&data);

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
        data = _unpackBlobConstants(tstate, &items[0], data, 3);

        PyObject *s = MAKE_SLICE_OBJECT3(tstate, items[0], items[1], items[2]);

        *output = s;
        is_object = true;

        break;
    }
    case ';': {
        // (x)range objects
        PyObject *items[3];
        data = _unpackBlobConstants(tstate, &items[0], data, 3);
#if PYTHON_VERSION < 0x300
        assert(PyInt_CheckExact(items[0]));
        assert(PyInt_CheckExact(items[1]));
        assert(PyInt_CheckExact(items[2]));

        long start = PyInt_AS_LONG(items[0]);
        long stop = PyInt_AS_LONG(items[1]);
        long step = PyInt_AS_LONG(items[2]);

        PyObject *s = MAKE_XRANGE(tstate, start, stop, step);
#else
        PyObject *s = BUILTIN_XRANGE3(tstate, items[0], items[1], items[2]);
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
                PyFloat_SET_DOUBLE(_const_float_minus_0_0, copysign(PyFloat_AS_DOUBLE(_const_float_minus_0_0), -1.0));
            }
            z = _const_float_minus_0_0;

            break;
        }

        case 2: {
            static PyObject *_const_float_plus_nan = NULL;

            if (_const_float_plus_nan == NULL) {
                _const_float_plus_nan = PyFloat_FromDouble(Py_NAN);

                // Older Python3 has variable signs for NaN from C, so be explicit about it.
                PyFloat_SET_DOUBLE(_const_float_plus_nan, copysign(PyFloat_AS_DOUBLE(_const_float_plus_nan), 1.0));
            }
            z = _const_float_plus_nan;

            break;
        }
        case 3: {
            static PyObject *_const_float_minus_nan = NULL;

            if (_const_float_minus_nan == NULL) {
                _const_float_minus_nan = PyFloat_FromDouble(Py_NAN);

                // Older Python3 has variable signs for NaN from C, so be explicit about it.
                PyFloat_SET_DOUBLE(_const_float_minus_nan, copysign(PyFloat_AS_DOUBLE(_const_float_minus_nan), -1.0));
            }
            z = _const_float_minus_nan;

            break;
        }
        case 4: {
            static PyObject *_const_float_plus_inf = NULL;

            if (_const_float_plus_inf == NULL) {
                _const_float_plus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

                // Older Python3 has variable signs from C, so be explicit about it.
                PyFloat_SET_DOUBLE(_const_float_plus_inf, copysign(PyFloat_AS_DOUBLE(_const_float_plus_inf), 1.0));
            }
            z = _const_float_plus_inf;

            break;
        }
        case 5: {
            static PyObject *_const_float_minus_inf = NULL;

            if (_const_float_minus_inf == NULL) {
                _const_float_minus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

                // Older Python3 has variable signs from C, so be explicit about it.
                PyFloat_SET_DOUBLE(_const_float_minus_inf, copysign(PyFloat_AS_DOUBLE(_const_float_minus_inf), -1.0));
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
        uint64_t size = _unpackVariableLength(&data);

        *output = (PyObject *)data;
        is_object = false;

        data += size;

        break;
    }
#if PYTHON_VERSION >= 0x390
    case 'A': {
        // GenericAlias object
        PyObject *items[2];
        data = _unpackBlobConstants(tstate, &items[0], data, 2);

        PyObject *g = Py_GenericAlias(items[0], items[1]);

        // TODO: Maybe deduplicate.
        *output = g;

        is_object = true;
        break;
    }
#endif
#if PYTHON_VERSION >= 0x3a0
    case 'H': {
        // UnionType object
        PyObject *args;
        data = _unpackBlobConstants(tstate, &args, data, 1);

        PyObject *union_type = MAKE_UNION_TYPE(args);

        // TODO: Maybe deduplicate.
        *output = union_type;

        is_object = true;
        break;
    }
#endif
    case 'C': {
        // Code object, without the filename, we let the module do that, depending on
        // the source mode.
        int line = unpackValueInt(&data);
        int flags = unpackValueInt(&data);

        PyObject *function_name;
        data = _unpackBlobConstant(tstate, &function_name, data);
        // TODO: Version specific if we have this
#if PYTHON_VERSION >= 0x3b0
        PyObject *function_qualname;
        data = _unpackBlobConstant(tstate, &function_qualname, data);
#endif
        PyObject *arg_names;
        data = _unpackBlobConstant(tstate, &arg_names, data);
        PyObject *free_vars;
        data = _unpackBlobConstant(tstate, &free_vars, data);
        int arg_count = unpackValueInt(&data);

#if PYTHON_VERSION >= 0x300
        int kw_only_count = unpackValueInt(&data);
#if PYTHON_VERSION >= 0x380
        int pos_only_count = unpackValueInt(&data);
#endif
#endif
        // Filename will be supplied later during usage.
        *output = (PyObject *)MAKE_CODE_OBJECT(Py_None, line, flags, function_name, function_qualname, arg_names,
                                               free_vars, arg_count, kw_only_count, pos_only_count);

        is_object = true;
        break;
    }
    case '.': {
        PRINT_STRING("Missing blob values\n");
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

#if PYTHON_VERSION < 0x3c0
        Py_INCREF(*output);
        Py_INCREF(*output);
#else
        Py_SET_REFCNT_IMMORTAL(*output);
#endif
    }

    return data;
}

static unsigned char const *_unpackBlobConstants(PyThreadState *tstate, PyObject **output, unsigned char const *data,
                                                 int count) {
    for (int _i = 0; _i < count; _i++) {
        data = _unpackBlobConstant(tstate, output, data);

        output += 1;
    }

    return data;
}

static void unpackBlobConstants(PyThreadState *tstate, PyObject **output, unsigned char const *data) {
    int count = (int)unpackValueUint16(&data);

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
    printf("unpackBlobConstants count %d\n", count);
#endif
    _unpackBlobConstants(tstate, output, data, count);
}

#if _NUITKA_CONSTANTS_FROM_MACOS_SECTION

#include <mach-o/getsect.h>
#include <mach-o/ldsyms.h>

#ifndef _NUITKA_EXE
static int findMacOSDllImageId(void) {
    Dl_info where;
    int res = dladdr((void *)findMacOSDllImageId, &where);
    assert(res != 0);

    char const *dll_filename = where.dli_fname;

    unsigned long image_count = _dyld_image_count();

    for (int i = 0; i < image_count; i++) {
        // Ignore entries without a header.
        struct mach_header const *header = _dyld_get_image_header(i);
        if (header == NULL) {
            continue;
        }

        if (strcmp(dll_filename, _dyld_get_image_name(i)) == 0) {
            return i;
        }
    }

    return -1;
}
#endif

unsigned char *findMacOSBinarySection(void) {
#ifdef _NUITKA_EXE
    const struct mach_header *header = &_mh_execute_header;
#else
    int image_id = findMacOSDllImageId();
    assert(image_id != -1);

    const struct mach_header *header = _dyld_get_image_header(image_id);
#endif

    unsigned long *size;
    return getsectiondata(header, "constants", "constants", &size);
}

#endif

void loadConstantsBlob(PyThreadState *tstate, PyObject **output, char const *name) {
    static bool init_done = false;

    if (init_done == false) {
        NUITKA_PRINT_TIMING("loadConstantsBlob(): One time init.");

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        printf("loadConstantsBlob '%s' one time init\n", name);
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
#elif _NUITKA_CONSTANTS_FROM_MACOS_SECTION
        constant_bin = findMacOSBinarySection();

        assert(constant_bin);
#endif
        NUITKA_PRINT_TIMING("loadConstantsBlob(): Found blob, decoding now.");
        DECODE(constant_bin);

        NUITKA_PRINT_TIMING("loadConstantsBlob(): CRC32 that blob for correctness.");
        uint32_t hash = unpackValueUint32(&constant_bin);
        uint32_t size = unpackValueUint32(&constant_bin);

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        printf("loadConstantsBlob '%u' hash value\n", hash);
        printf("loadConstantsBlob '%u' size value\n", size);
#endif
        if (calcCRC32(constant_bin, size) != hash) {
            puts("Error, corrupted constants object");
            abort();
        }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        printf("Checked CRC32 to match hash %u size %u\n", hash, size);
#endif

        NUITKA_PRINT_TIMING("loadConstantsBlob(): One time init complete.");

        init_done = true;
    }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
    printf("Loading blob named '%s'\n", name);
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
        printf("offset of blob size %d\n", w - constant_bin);
#endif

        uint32_t size = unpackValueUint32(&w);

        if (match == 0) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
            printf("Loading blob named '%s' with size %d\n", name, size);
#endif
            break;
        }

        // Skip other module data.
        w += size;
    }

    unpackBlobConstants(tstate, output, w);
}

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
