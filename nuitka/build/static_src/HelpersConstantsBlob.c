//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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
static PyObject *Nuitka_LongFromCLong(long ival);

// Most often used modes per OS, more exist and could be used of course.
#if defined(_WIN32)
#define _NUITKA_CONSTANTS_FROM_COFF_OBJ 1
#elif defined(__APPLE__)
#define _NUITKA_CONSTANTS_FROM_MACOS_SECTION 1
#else
#define _NUITKA_CONSTANTS_FROM_CODE 1
#endif

#endif

#if _NUITKA_EXPERIMENTAL_WRITEABLE_CONSTANTS
#define CONSTANT_BIN_CONSTANT
#else
#define CONSTANT_BIN_CONSTANT const
#endif

#if defined(_NUITKA_CONSTANTS_FROM_LINKER) || defined(_NUITKA_CONSTANTS_FROM_COFF_OBJ) ||                              \
    defined(_NUITKA_CONSTANTS_FROM_CODE) || defined(_NUITKA_CONSTANTS_FROM_INCBIN) ||                                  \
    defined(_NUITKA_CONSTANTS_FROM_C23_EMBED) || defined(_NUITKA_CONSTANTS_FROM_MACOS_SECTION)
NUITKA_DECLARE_CONSTANT_BLOB(constant_bin, constant_bin, CONSTANT_BIN_CONSTANT);
#endif

#include "nuitka/constants_blob_spec.h"

// Symbol to be assigned locally.
unsigned char const *constant_bin = NULL;

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

static PyObject *our_list_tp_richcompare(PyListObject *list1, PyListObject *list2, int op) {
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

static PyObject *our_tuple_tp_richcompare(PyTupleObject *tuple1, PyTupleObject *tuple2, int op) {
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

static PyObject *our_set_tp_richcompare(PyObject *set1, PyObject *set2, int op) {
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

static PyObject *our_float_tp_richcompare(PyFloatObject *a, PyFloatObject *b, int op) {
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

static PyObject *our_dict_tp_richcompare(PyObject *a, PyObject *b, int op) {
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

static void _finalizeUnpackedConstantObject(void **output, PyObject *value) {
    *(PyObject **)*output = value;
    CHECK_OBJECT(value);

#if PYTHON_VERSION < 0x3c0
    Py_INCREF(value);
    Py_INCREF(value);
#else
#if defined(__GNUC__) && __GNUC__ >= 11
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Warray-bounds"
#endif
    Py_SET_REFCNT_IMMORTAL(value);
#if defined(__GNUC__) && __GNUC__ >= 11
#pragma GCC diagnostic pop
#endif
#endif
    *output = (void *)((PyObject **)*output + 1);
}

static void insertToDictCacheForcedHash(PyObject *dict, PyObject **value, hashfunc tp_hash,
                                        richcmpfunc tp_richcompare) {
    hashfunc old_hash = Py_TYPE(*value)->tp_hash;
    richcmpfunc old_richcmpfunc = Py_TYPE(*value)->tp_richcompare;

    // Hash is optional, e.g. for floats we can spare us doing our own hash,
    // but we do equality
    if (tp_hash != NULL) {
        Py_TYPE(*value)->tp_hash = tp_hash;
    }
    Py_TYPE(*value)->tp_richcompare = tp_richcompare;

    insertToDictCache(dict, value);

    Py_TYPE(*value)->tp_hash = old_hash;
    Py_TYPE(*value)->tp_richcompare = old_richcmpfunc;
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

#if PYTHON_VERSION >= 0x3a0
    case 10:
        return (PyObject *)Nuitka_PyUnion_Type;
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

static PyObject *_Nuitka_Unicode_ImmortalFromStringAndSize(PyThreadState *tstate, const char *data, Py_ssize_t size,
                                                           bool is_ascii) {
#if PYTHON_VERSION < 0x300
    PyObject *u = PyUnicode_FromStringAndSize((const char *)data, size);
#else
    // spell-checker: ignore surrogatepass
    PyObject *u = PyUnicode_DecodeUTF8((const char *)data, size, "surrogatepass");
#endif

#if PYTHON_VERSION >= 0x3d0 || (PYTHON_VERSION >= 0x3c7 && _NUITKA_EXE_MODE)
    _PyUnicode_InternImmortal(tstate->interp, &u);
#elif PYTHON_VERSION >= 0x3c0
    if (is_ascii) {
        PyUnicode_InternInPlace(&u);
    }

#if PYTHON_VERSION >= 0x3c7
    _PyUnicode_STATE(u).interned = SSTATE_INTERNED_IMMORTAL_STATIC;

#if _NUITKA_EXE_MODE
    _PyUnicode_STATE(u).statically_allocated = 1;
#else
    if (Py_Version >= 0x30c0700) {
        _PyUnicode_STATE(u).statically_allocated = 1;
    }
#endif
#endif

#elif PYTHON_VERSION >= 0x300
    if (is_ascii) {
        PyUnicode_InternInPlace(&u);
    }
#else
    insertToDictCache(unicode_cache, &u);
#endif

    // Make sure our strings are consistent.
    // TODO: Check with an assertion making build of Python 3.13.0 if this is really true,
    // for 3.14 it ought to not be done.
#if PYTHON_VERSION >= 0x3c0 && PYTHON_VERSION < 0x3e0 && !defined(__NUITKA_NO_ASSERT__)
    // Note: Setting to immortal happens last, but we want to check now.
    Py_SET_REFCNT_IMMORTAL(u);

    assert(Nuitka_PyUnicode_CheckConsistency(u, 1));
#endif

    return u;
}

static unsigned char const *_unpackBlobConstants(PyThreadState *tstate, void **output, unsigned char const *data,
                                                 int count);

static unsigned char const *_unpackBlobConstantsAt(PyThreadState *tstate, void *output, unsigned char const *data,
                                                   int count);

static unsigned char const *_unpackBlobConstant(PyThreadState *tstate, void **output, unsigned char const *data);

static unsigned char const *_unpackBlobConstantObjectPrevious(PyThreadState *tstate, void **output,
                                                              unsigned char const *data) {
    PyObject *prev = ((PyObject **)*output)[-1];
    _finalizeUnpackedConstantObject(output, prev);
    return data;
}

static unsigned char const *_unpackBlobConstantObjectTuple(PyThreadState *tstate, void **output,
                                                           unsigned char const *data) {
    int size = (int)_unpackVariableLength(&data);

    PyObject *t;

    if (size > 0) {
        t = MAKE_TUPLE_EMPTY(tstate, size);
        CHECK_OBJECT(t);

        data = _unpackBlobConstantsAt(tstate, &PyTuple_GET_ITEM(t, 0), data, size);

        CHECK_OBJECTS(&PyTuple_GET_ITEM(t, 0), size);
    } else {
        t = PyTuple_New(0);
    }

    insertToDictCacheForcedHash(tuple_cache, &t, (hashfunc)our_tuple_hash, (richcmpfunc)our_tuple_tp_richcompare);

    _finalizeUnpackedConstantObject(output, t);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectList(PyThreadState *tstate, void **output,
                                                          unsigned char const *data) {
    int size = (int)_unpackVariableLength(&data);

    PyObject *l = MAKE_LIST_EMPTY(tstate, size);
    CHECK_OBJECT(l);

    if (size > 0) {
        data = _unpackBlobConstantsAt(tstate, &PyList_GET_ITEM(l, 0), data, size);

        CHECK_OBJECTS(&PyList_GET_ITEM(l, 0), size);
    }

    insertToDictCacheForcedHash(list_cache, &l, (hashfunc)our_list_hash, (richcmpfunc)our_list_tp_richcompare);

    _finalizeUnpackedConstantObject(output, l);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectDict(PyThreadState *tstate, void **output,
                                                          unsigned char const *data) {
    int size = (int)_unpackVariableLength(&data);

    PyObject *d = _PyDict_NewPresized(size);
    CHECK_OBJECT(d);

    if (size > 0) {
        NUITKA_DYNAMIC_ARRAY_DECL(keys, PyObject *, size);
        NUITKA_DYNAMIC_ARRAY_DECL(values, PyObject *, size);

        data = _unpackBlobConstantsAt(tstate, keys, data, size);
        data = _unpackBlobConstantsAt(tstate, values, data, size);

        CHECK_OBJECTS(&keys[0], size);
        CHECK_OBJECTS(&values[0], size);

        for (int i = 0; i < size; i++) {
            NUITKA_MAY_BE_UNUSED int res = PyDict_SetItem(d, keys[i], values[i]);
            assert(res == 0);
        }
    }

    insertToDictCacheForcedHash(dict_cache, &d, (hashfunc)our_dict_hash, (richcmpfunc)our_dict_tp_richcompare);

    _finalizeUnpackedConstantObject(output, d);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectSetOrFrozenset(PyThreadState *tstate, void **output,
                                                                    unsigned char const *data, unsigned char c) {
    int size = (int)_unpackVariableLength(&data);

    PyObject *s;

    if (c == NUITKA_CONSTANT_BLOB_TAG_SET) {
        s = PySet_New(NULL);
    } else {
        if (size == 0) {
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

    CHECK_OBJECT(s);

    if (size > 0) {
        NUITKA_DYNAMIC_ARRAY_DECL(values, PyObject *, size);

        data = _unpackBlobConstantsAt(tstate, values, data, size);

        CHECK_OBJECTS(&values[0], size);

        for (int i = 0; i < size; i++) {
            NUITKA_MAY_BE_UNUSED int res = PySet_Add(s, values[i]);
            assert(res == 0);
        }
    }

    if (c == NUITKA_CONSTANT_BLOB_TAG_SET) {
        insertToDictCacheForcedHash(set_cache, &s, (hashfunc)our_set_hash, (richcmpfunc)our_set_tp_richcompare);
    } else {
        insertToDictCacheForcedHash(frozenset_cache, &s, (hashfunc)our_set_hash, (richcmpfunc)our_set_tp_richcompare);
    }

    _finalizeUnpackedConstantObject(output, s);

    return data;
}

#if PYTHON_VERSION < 0x300
static unsigned char const *_unpackBlobConstantObjectIntNegativeOrPositive(PyThreadState *tstate, void **output,
                                                                           unsigned char const *data, unsigned char c) {
    long value = (long)_unpackVariableLength(&data);
    if (c == NUITKA_CONSTANT_BLOB_TAG_INT_NEGATIVE) {
        value = -value;
    }

    PyObject *i = PyInt_FromLong(value);

    insertToDictCache(int_cache, &i);

    _finalizeUnpackedConstantObject(output, i);

    return data;
}
#endif

static unsigned char const *_unpackBlobConstantObjectLongPositiveOrNegativeSmall(PyThreadState *tstate, void **output,
                                                                                 unsigned char const *data,
                                                                                 unsigned char c) {
    uint64_t value = _unpackVariableLength(&data);

    PyObject *l =
        Nuitka_LongFromCLong((c == NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_SMALL) ? ((long)value) : (-(long)value));
    assert(l != NULL);

#if PYTHON_VERSION >= 0x300
    long check_value = (c == NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_SMALL) ? (long)value : -(long)value;
    if (check_value < NUITKA_STATIC_SMALLINT_VALUE_MIN || check_value >= NUITKA_STATIC_SMALLINT_VALUE_MAX)
#endif
    {
        insertToDictCache(long_cache, &l);
    }

    _finalizeUnpackedConstantObject(output, l);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectLongPositiveOrNegativeLarge(PyThreadState *tstate, void **output,
                                                                                 unsigned char const *data,
                                                                                 unsigned char c) {
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

    if (c == NUITKA_CONSTANT_BLOB_TAG_LONG_NEGATIVE_LARGE) {
        Nuitka_LongSetSignNegative(result);
    }

    insertToDictCache(long_cache, &result);

    _finalizeUnpackedConstantObject(output, result);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectFloat(PyThreadState *tstate, void **output,
                                                           unsigned char const *data) {
    double value = unpackValueFloat(&data);

    PyObject *f = PyFloat_FromDouble(value);

    insertToDictCacheForcedHash(float_cache, &f, NULL, (richcmpfunc)our_float_tp_richcompare);

    _finalizeUnpackedConstantObject(output, f);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectComplex(PyThreadState *tstate, void **output,
                                                             unsigned char const *data) {
    double real = unpackValueFloat(&data);
    double imag = unpackValueFloat(&data);

    _finalizeUnpackedConstantObject(output, PyComplex_FromDoubles(real, imag));

    return data;
}

static unsigned char const *_unpackBlobConstantObjectComplexSpecial(PyThreadState *tstate, void **output,
                                                                    unsigned char const *data) {
    PyObject *parts[2];

    data = _unpackBlobConstantsAt(tstate, parts, data, 2);

    _finalizeUnpackedConstantObject(output, BUILTIN_COMPLEX2(tstate, parts[0], parts[1]));

    return data;
}

#if PYTHON_VERSION < 0x300
static unsigned char const *_unpackBlobConstantObjectAttributeNameOrBytesZeroTerminated(PyThreadState *tstate,
                                                                                        void **output,
                                                                                        unsigned char const *data,
                                                                                        unsigned char c) {
    size_t size = strlen((const char *)data);

    PyObject *s = PyString_FromStringAndSize((const char *)data, size);
    CHECK_OBJECT(s);

    data += size + 1;

    if (c == NUITKA_CONSTANT_BLOB_TAG_ATTRIBUTE_NAME) {
        PyString_InternInPlace(&s);
    }

    _finalizeUnpackedConstantObject(output, s);

    return data;
}
#endif

#if PYTHON_VERSION >= 0x300
static unsigned char const *_unpackBlobConstantObjectBytesZeroTerminated(PyThreadState *tstate, void **output,
                                                                         unsigned char const *data) {
    size_t size = strlen((const char *)data);

    PyObject *b = Nuitka_Bytes_FromStringAndSize((const char *)data, size);
    CHECK_OBJECT(b);

    data += size + 1;

    if (size > 1) {
        insertToDictCache(bytes_cache, &b);
    }

    _finalizeUnpackedConstantObject(output, b);

    return data;
}
#endif

static unsigned char const *_unpackBlobConstantObjectBytesSingle(PyThreadState *tstate, void **output,
                                                                 unsigned char const *data) {
#if PYTHON_VERSION < 0x300
    PyObject *s = PyString_FromStringAndSize((const char *)data, 1);
    data += 1;
    _finalizeUnpackedConstantObject(output, s);
#else
    PyObject *b = Nuitka_Bytes_FromStringAndSize((const char *)data, 1);
    data += 1;
    _finalizeUnpackedConstantObject(output, b);
#endif

    return data;
}

static unsigned char const *_unpackBlobConstantObjectTextSingle(PyThreadState *tstate, void **output,
                                                                unsigned char const *data) {
    PyObject *u = _Nuitka_Unicode_ImmortalFromStringAndSize(tstate, (const char *)data, 1, true);
    data += 1;

    _finalizeUnpackedConstantObject(output, u);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectBytesLengthPrefixed(PyThreadState *tstate, void **output,
                                                                         unsigned char const *data) {
    int size = (int)_unpackVariableLength(&data);
    assert(size > 1);

    PyObject *b = Nuitka_Bytes_FromStringAndSize((const char *)data, size);
    CHECK_OBJECT(b);

    data += size;

#if PYTHON_VERSION >= 0x300
    insertToDictCache(bytes_cache, &b);
#endif

    _finalizeUnpackedConstantObject(output, b);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectBytearray(PyThreadState *tstate, void **output,
                                                               unsigned char const *data) {
    int size = (int)_unpackVariableLength(&data);

    PyObject *b = PyByteArray_FromStringAndSize((const char *)data, size);
    data += size;

    _finalizeUnpackedConstantObject(output, b);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectAttributeNameOrTextUtf8ZeroTerminated(PyThreadState *tstate,
                                                                                           void **output,
                                                                                           unsigned char const *data,
                                                                                           unsigned char c) {
    size_t size = strlen((const char *)data);
    assert(size != 0);

    PyObject *u = _Nuitka_Unicode_ImmortalFromStringAndSize(tstate, (const char *)data, size,
                                                            c == NUITKA_CONSTANT_BLOB_TAG_ATTRIBUTE_NAME);
    data += size + 1;

    _finalizeUnpackedConstantObject(output, u);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectTextUtf8LengthPrefixed(PyThreadState *tstate, void **output,
                                                                            unsigned char const *data) {
    int size = (int)_unpackVariableLength(&data);
    assert(size != 0);

    PyObject *u = _Nuitka_Unicode_ImmortalFromStringAndSize(tstate, (const char *)data, size, false);
    data += size;

    _finalizeUnpackedConstantObject(output, u);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectNone(PyThreadState *tstate, void **output,
                                                          unsigned char const *data) {
    _finalizeUnpackedConstantObject(output, Py_None);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectTextEmpty(PyThreadState *tstate, void **output,
                                                               unsigned char const *data) {
    _finalizeUnpackedConstantObject(output,
                                    _Nuitka_Unicode_ImmortalFromStringAndSize(tstate, (const char *)data, 0, true));

    return data;
}

static unsigned char const *_unpackBlobConstantObjectTrue(PyThreadState *tstate, void **output,
                                                          unsigned char const *data) {
    _finalizeUnpackedConstantObject(output, Py_True);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectFalse(PyThreadState *tstate, void **output,
                                                           unsigned char const *data) {
    _finalizeUnpackedConstantObject(output, Py_False);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectSlice(PyThreadState *tstate, void **output,
                                                           unsigned char const *data) {
    PyObject *items[3];
    data = _unpackBlobConstantsAt(tstate, items, data, 3);

    PyObject *s = MAKE_SLICE_OBJECT3(tstate, items[0], items[1], items[2]);

    _finalizeUnpackedConstantObject(output, s);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectRange(PyThreadState *tstate, void **output,
                                                           unsigned char const *data) {
    PyObject *items[3];
    data = _unpackBlobConstantsAt(tstate, items, data, 3);
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
    _finalizeUnpackedConstantObject(output, s);

    return data;
}

static unsigned char const *_unpackBlobConstantObjectBuiltinAnon(PyThreadState *tstate, void **output,
                                                                 unsigned char const *data) {
    unsigned char anon_index = *data++;

    _finalizeUnpackedConstantObject(output, _unpackAnonValue(anon_index));

    return data;
}

static unsigned char const *_unpackBlobConstantObjectBuiltinSpecial(PyThreadState *tstate, void **output,
                                                                    unsigned char const *data) {
    unsigned char special_index = *data++;

    _finalizeUnpackedConstantObject(output, _unpackSpecialValue(special_index));

    return data;
}

static unsigned char const *_unpackBlobConstantObjectBuiltinNamed(PyThreadState *tstate, void **output,
                                                                  unsigned char const *data) {
    char const *builtin_name = (char const *)data;
    data = _unpackValueCString(data);

    _finalizeUnpackedConstantObject(output, PyObject_GetAttrString((PyObject *)builtin_module, builtin_name));

    return data;
}

static unsigned char const *_unpackBlobConstantObjectBuiltinException(PyThreadState *tstate, void **output,
                                                                      unsigned char const *data) {
    char const *builtin_exception_name = (char const *)data;
    data = _unpackValueCString(data);

    _finalizeUnpackedConstantObject(output, PyObject_GetAttrString((PyObject *)builtin_module, builtin_exception_name));

    return data;
}

static unsigned char const *_unpackBlobConstantObjectFloatSpecial(PyThreadState *tstate, void **output,
                                                                  unsigned char const *data) {
    unsigned char v = *data++;

    PyObject *z = NULL;

    switch (v) {
    case NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_ZERO: {
        static PyObject *_const_float_0_0 = NULL;

        if (_const_float_0_0 == NULL) {
            _const_float_0_0 = PyFloat_FromDouble(0.0);
        }
        z = _const_float_0_0;

        break;
    }
    case NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_ZERO: {
        static PyObject *_const_float_minus_0_0 = NULL;

        if (_const_float_minus_0_0 == NULL) {
            _const_float_minus_0_0 = PyFloat_FromDouble(0.0);

            PyFloat_SET_DOUBLE(_const_float_minus_0_0, copysign(PyFloat_AS_DOUBLE(_const_float_minus_0_0), -1.0));
        }
        z = _const_float_minus_0_0;

        break;
    }

    case NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_NAN: {
        static PyObject *_const_float_plus_nan = NULL;

        if (_const_float_plus_nan == NULL) {
            _const_float_plus_nan = PyFloat_FromDouble(Py_NAN);

            PyFloat_SET_DOUBLE(_const_float_plus_nan, copysign(PyFloat_AS_DOUBLE(_const_float_plus_nan), 1.0));
        }
        z = _const_float_plus_nan;

        break;
    }
    case NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_NAN: {
        static PyObject *_const_float_minus_nan = NULL;

        if (_const_float_minus_nan == NULL) {
            _const_float_minus_nan = PyFloat_FromDouble(Py_NAN);

            PyFloat_SET_DOUBLE(_const_float_minus_nan, copysign(PyFloat_AS_DOUBLE(_const_float_minus_nan), -1.0));
        }
        z = _const_float_minus_nan;

        break;
    }
    case NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_INF: {
        static PyObject *_const_float_plus_inf = NULL;

        if (_const_float_plus_inf == NULL) {
            _const_float_plus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

            PyFloat_SET_DOUBLE(_const_float_plus_inf, copysign(PyFloat_AS_DOUBLE(_const_float_plus_inf), 1.0));
        }
        z = _const_float_plus_inf;

        break;
    }
    case NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_INF: {
        static PyObject *_const_float_minus_inf = NULL;

        if (_const_float_minus_inf == NULL) {
            _const_float_minus_inf = PyFloat_FromDouble(Py_HUGE_VAL);

            PyFloat_SET_DOUBLE(_const_float_minus_inf, copysign(PyFloat_AS_DOUBLE(_const_float_minus_inf), -1.0));
        }
        z = _const_float_minus_inf;

        break;
    }
    default: {
#ifndef __NUITKA_NO_ASSERT__
        PRINT_FORMAT("Missing decoding for %d\n", (int)v);
#endif
        NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
    }
    }

    insertToDictCacheForcedHash(float_cache, &z, NULL, (richcmpfunc)our_float_tp_richcompare);

    _finalizeUnpackedConstantObject(output, z);

    return data;
}

#if PYTHON_VERSION >= 0x390
static unsigned char const *_unpackBlobConstantObjectGenericAlias(PyThreadState *tstate, void **output,
                                                                  unsigned char const *data) {
    PyObject *items[2];
    data = _unpackBlobConstantsAt(tstate, items, data, 2);

    PyObject *g = Py_GenericAlias(items[0], items[1]);

    _finalizeUnpackedConstantObject(output, g);
    return data;
}
#endif

#if PYTHON_VERSION >= 0x3a0
static unsigned char const *_unpackBlobConstantObjectUnionType(PyThreadState *tstate, void **output,
                                                               unsigned char const *data) {
    PyObject *args;
    data = _unpackBlobConstantsAt(tstate, &args, data, 1);

    PyObject *union_type = MAKE_UNION_TYPE(args);

    _finalizeUnpackedConstantObject(output, union_type);
    return data;
}
#endif

static unsigned char const *_unpackBlobConstantObjectCodeObject(PyThreadState *tstate, void **output,
                                                                unsigned char const *data) {
    uint64_t flags = _unpackVariableLength(&data);

    int co_flags = 0;

    PyObject *function_name;
    void *_slot = (void *)&function_name;
    data = _unpackBlobConstant(tstate, &_slot, data);

    int line_number = (int)_unpackVariableLength(&data) + 1;

    PyObject *arg_names;
    _slot = (void *)&arg_names;
    data = _unpackBlobConstant(tstate, &_slot, data);

    int arg_count = (int)_unpackVariableLength(&data);

#if PYTHON_VERSION >= 0x3b0
    PyObject *function_qualname;

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_QUALNAME) {
        _slot = (void *)&function_qualname;
        data = _unpackBlobConstant(tstate, &_slot, data);
    } else {
        function_qualname = function_name;
    }
#endif

    PyObject *free_vars = NULL;

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FREE_VARS) {
        _slot = (void *)&free_vars;
        data = _unpackBlobConstant(tstate, &_slot, data);
    }

#if PYTHON_VERSION >= 0x300
    int kw_only_count = 0;
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_KW_ONLY) {
        kw_only_count = (int)_unpackVariableLength(&data) + 1;
    }
    assert(kw_only_count >= 0);
#endif

#if PYTHON_VERSION >= 0x380
    int pos_only_count = 0;
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_POS_ONLY) {
        pos_only_count = (int)_unpackVariableLength(&data) + 1;
    }
    assert(pos_only_count >= 0);
#endif

    switch (flags & NUITKA_CONSTANT_BLOB_CODE_KIND_MASK) {
#if PYTHON_VERSION >= 0x360
    case NUITKA_CONSTANT_BLOB_CODE_KIND_ASYNCGEN:
        co_flags += CO_ASYNC_GENERATOR;
        break;
#endif
#if PYTHON_VERSION >= 0x350
    case NUITKA_CONSTANT_BLOB_CODE_KIND_COROUTINE:
        co_flags += CO_COROUTINE;
        break;
#endif
    case NUITKA_CONSTANT_BLOB_CODE_KIND_GENERATOR:
        co_flags += CO_GENERATOR;
        break;
    default:
        break;
    }

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_OPTIMIZED) {
        co_flags += CO_OPTIMIZED;
    }

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_NEWLOCALS) {
        co_flags += CO_NEWLOCALS;
    }

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_VARARGS) {
        co_flags += CO_VARARGS;
    }

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_VARKEYWORDS) {
        co_flags += CO_VARKEYWORDS;
    }

#if PYTHON_VERSION >= 0x370
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_ANNOTATIONS) {
        co_flags += CO_FUTURE_ANNOTATIONS;
    }
#endif

#if PYTHON_VERSION < 0x300
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_DIVISION) {
        co_flags += CO_FUTURE_DIVISION;
    }
#endif

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_UNICODE_LITERALS) {
        co_flags += CO_FUTURE_UNICODE_LITERALS;
    }

#if PYTHON_VERSION < 0x300
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_PRINT_FUNCTION) {
        co_flags += CO_FUTURE_PRINT_FUNCTION;
    }
#endif

#if PYTHON_VERSION < 0x300
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_ABSOLUTE_IMPORT) {
        co_flags += CO_FUTURE_ABSOLUTE_IMPORT;
    }
#endif

#if PYTHON_VERSION >= 0x350 && PYTHON_VERSION < 0x370
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_GENERATOR_STOP) {
        co_flags += CO_FUTURE_GENERATOR_STOP;
    }
#endif

#if PYTHON_VERSION >= 0x300
    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_BARRY_AS_BDFL) {
        co_flags += CO_FUTURE_BARRY_AS_BDFL;
    }
#endif

    if (flags & NUITKA_CONSTANT_BLOB_CODE_FLAG_NOFREE) {
        co_flags += CO_NOFREE;
    }

    _finalizeUnpackedConstantObject(output, (PyObject *)MAKE_CODE_OBJECT(Py_None, line_number, co_flags, function_name,
                                                                         function_qualname, arg_names, free_vars,
                                                                         arg_count, kw_only_count, pos_only_count));

    return data;
}

static unsigned char const *_unpackBlobConstant(PyThreadState *tstate, void **output, unsigned char const *data) {

    // Make sure we discover failures to assign.
    *(PyObject **)*output = NULL;
    unsigned char c = *data++;
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
    unsigned char const *data_old = data;
    printf("Type %u:\n", (unsigned int)c);
#endif
    switch (c) {

    case NUITKA_CONSTANT_BLOB_TAG_PREVIOUS: {
        data = _unpackBlobConstantObjectPrevious(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_TUPLE: {
        data = _unpackBlobConstantObjectTuple(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_LIST: {
        data = _unpackBlobConstantObjectList(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_DICT: {
        data = _unpackBlobConstantObjectDict(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_FROZENSET:
    case NUITKA_CONSTANT_BLOB_TAG_SET: {
        data = _unpackBlobConstantObjectSetOrFrozenset(tstate, output, data, c);
        break;
    }
#if PYTHON_VERSION < 0x300
    case NUITKA_CONSTANT_BLOB_TAG_INT_NEGATIVE:
    case NUITKA_CONSTANT_BLOB_TAG_INT_POSITIVE: {
        data = _unpackBlobConstantObjectIntNegativeOrPositive(tstate, output, data, c);
        break;
    }
#endif
    case NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_SMALL:
    case NUITKA_CONSTANT_BLOB_TAG_LONG_NEGATIVE_SMALL: {
        data = _unpackBlobConstantObjectLongPositiveOrNegativeSmall(tstate, output, data, c);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_LONG_NEGATIVE_LARGE:
    case NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_LARGE: {
        data = _unpackBlobConstantObjectLongPositiveOrNegativeLarge(tstate, output, data, c);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_FLOAT: {
        data = _unpackBlobConstantObjectFloat(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_COMPLEX: {
        data = _unpackBlobConstantObjectComplex(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_COMPLEX_SPECIAL: {
        data = _unpackBlobConstantObjectComplexSpecial(tstate, output, data);
        break;
    }
#if PYTHON_VERSION < 0x300
    case NUITKA_CONSTANT_BLOB_TAG_ATTRIBUTE_NAME:
    case NUITKA_CONSTANT_BLOB_TAG_BYTES_ZERO_TERMINATED: {
        data = _unpackBlobConstantObjectAttributeNameOrBytesZeroTerminated(tstate, output, data, c);
        break;
    }
#else
    case NUITKA_CONSTANT_BLOB_TAG_BYTES_ZERO_TERMINATED: {
        data = _unpackBlobConstantObjectBytesZeroTerminated(tstate, output, data);
        break;
    }
#endif
    case NUITKA_CONSTANT_BLOB_TAG_BYTES_SINGLE: {
        data = _unpackBlobConstantObjectBytesSingle(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_TEXT_SINGLE: {
        data = _unpackBlobConstantObjectTextSingle(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_BYTES_LENGTH_PREFIXED: {
        data = _unpackBlobConstantObjectBytesLengthPrefixed(tstate, output, data);
        break;
    }

    case NUITKA_CONSTANT_BLOB_TAG_BYTEARRAY: {
        data = _unpackBlobConstantObjectBytearray(tstate, output, data);
        break;
    }
#if PYTHON_VERSION >= 0x300
    case NUITKA_CONSTANT_BLOB_TAG_ATTRIBUTE_NAME: // Python3 attributes
#endif
    case NUITKA_CONSTANT_BLOB_TAG_TEXT_UTF8_ZERO_TERMINATED: {
        data = _unpackBlobConstantObjectAttributeNameOrTextUtf8ZeroTerminated(tstate, output, data, c);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_TEXT_UTF8_LENGTH_PREFIXED: {
        data = _unpackBlobConstantObjectTextUtf8LengthPrefixed(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_NONE: {
        data = _unpackBlobConstantObjectNone(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_TEXT_EMPTY: {
        data = _unpackBlobConstantObjectTextEmpty(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_TRUE: {
        data = _unpackBlobConstantObjectTrue(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_FALSE: {
        data = _unpackBlobConstantObjectFalse(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_SLICE: {
        data = _unpackBlobConstantObjectSlice(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_RANGE: {
        data = _unpackBlobConstantObjectRange(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_BUILTIN_ANON: {
        data = _unpackBlobConstantObjectBuiltinAnon(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_BUILTIN_SPECIAL: {
        data = _unpackBlobConstantObjectBuiltinSpecial(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_BUILTIN_NAMED: {
        data = _unpackBlobConstantObjectBuiltinNamed(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_BUILTIN_EXCEPTION: {
        data = _unpackBlobConstantObjectBuiltinException(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_FLOAT_SPECIAL: {
        data = _unpackBlobConstantObjectFloatSpecial(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_BLOB_DATA: {
        uint64_t size = _unpackVariableLength(&data);

        *(unsigned char const **)*output = data;
        data += size;
        *output = (void *)((unsigned char const **)*output + 1);
        break;
    }
#if PYTHON_VERSION >= 0x390
    case NUITKA_CONSTANT_BLOB_TAG_GENERIC_ALIAS: {
        data = _unpackBlobConstantObjectGenericAlias(tstate, output, data);
        break;
    }
#endif
#if PYTHON_VERSION >= 0x3a0
    case NUITKA_CONSTANT_BLOB_TAG_UNION_TYPE: {
        data = _unpackBlobConstantObjectUnionType(tstate, output, data);
        break;
    }
#endif
    case NUITKA_CONSTANT_BLOB_TAG_CODE_OBJECT: {
        data = _unpackBlobConstantObjectCodeObject(tstate, output, data);
        break;
    }
    case NUITKA_CONSTANT_BLOB_TAG_END: {
#ifndef __NUITKA_NO_ASSERT__
        PRINT_STRING("Missing blob values\n");
#endif
        NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
    }
    default:
#ifndef __NUITKA_NO_ASSERT__
        PRINT_FORMAT("Missing decoding for %d\n", (int)c);
#endif
        NUITKA_CANNOT_GET_HERE("Corrupt constants blob");
    }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
    printf("Size for %u was %d\n", (unsigned int)c, (int)(data - data_old));
#endif

    return data;
}

static unsigned char const *_unpackBlobConstants(PyThreadState *tstate, void **output, unsigned char const *data,
                                                 int count) {
    for (int _i = 0; _i < count; _i++) {
        data = _unpackBlobConstant(tstate, output, data);
    }

    return data;
}

static unsigned char const *_unpackBlobConstantsAt(PyThreadState *tstate, void *output, unsigned char const *data,
                                                   int count) {
    return _unpackBlobConstants(tstate, &output, data, count);
}

static void unpackBlobConstants(PyThreadState *tstate, void *output, unsigned char const *data) {
    int count = (int)unpackValueUint16(&data);

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
    printf("unpackBlobConstants count %d\n", count);
#endif
    _unpackBlobConstants(tstate, &output, data, count);
}

void loadConstantsBlobData(PyThreadState *tstate, void *output, unsigned char const *data) {
    initCaches();
    unpackBlobConstants(tstate, output, data);
}

void loadConstantsBlob(PyThreadState *tstate, void *output, char const *name) {
    static bool init_done = false;

    if (init_done == false) {
        NUITKA_PRINT_TIMING("loadConstantsBlob(): One time init.");

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CONSTANTS
        printf("loadConstantsBlob '%s' one time init\n", name);
#endif

#if defined(_NUITKA_CONSTANTS_FROM_INCBIN) || defined(_NUITKA_CONSTANTS_FROM_LINKER) ||                                \
    defined(_NUITKA_CONSTANTS_FROM_COFF_OBJ) || defined(_NUITKA_CONSTANTS_FROM_CODE) ||                                \
    defined(_NUITKA_CONSTANTS_FROM_C23_EMBED) || defined(_NUITKA_CONSTANTS_FROM_MACOS_SECTION)
        constant_bin = getconstant_binData();
#endif
        NUITKA_PRINT_TIMING("loadConstantsBlob(): Found blob, decoding now.");
        DECODE(constant_bin);

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
