//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/**
 * This is responsible for collection of Nuitka Python PGO information. It writes
 * traces to files, for reuse in a future Python compilation of the same program.
 *
 * The file uses the "PGO File Format v2": entries are content deduplicated and
 * written as their own records before the records that reference them, so all
 * references are by ID and point backward.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static FILE *pgo_output = NULL;

// Content deduplicated string entries, IDs are their index. The strings are
// owned copies, since not all callers pass persistent strings.
struct PGO_StringEntry {
    char *value;
    uint32_t length;
    bool written;
};

static struct PGO_StringEntry *pgo_string_entries = NULL;
static uint32_t pgo_string_entries_size = 0;
static uint32_t pgo_string_entries_used = 0;

// Content deduplicated key entries, IDs are their index.
struct PGO_KeyEntry {
    uint32_t scope_kind;
    uint32_t string_id;
    // For repeatable class prepare probes, set once the key budget was used up.
    bool exhausted;
    bool written;
};

static struct PGO_KeyEntry *pgo_key_entries = NULL;
static uint32_t pgo_key_entries_size = 0;
static uint32_t pgo_key_entries_used = 0;

// Value entries, IDs are their index. The serialization is a stream of
// operations to replay when the definition is written to the file.
typedef enum {
    PGO_VALUE_OP_TAG = 1,
    PGO_VALUE_OP_UVARINT = 2,
    PGO_VALUE_OP_STRING_REF = 3,
    PGO_VALUE_OP_UINT64 = 5
} PGO_ValueOp;

// Budgets for value serialization, keeping the PGO file small and the capture
// fast. A single shared string may be up to PGO_VALUE_MAX_STRING_SIZE, a value
// encoding (which references shared strings by ID) up to
// PGO_VALUE_MAX_SERIALIZED_SIZE, and the distinct observations of one
// repeatable key up to PGO_KEY_MAX_SERIALIZED_SIZE combined.
#define PGO_VALUE_MAX_STRING_SIZE 1024
#define PGO_VALUE_MAX_SERIALIZED_SIZE 512
#define PGO_KEY_MAX_SERIALIZED_SIZE (20 * 1024)

struct PGO_ValueEntry {
    uint32_t ops_start;
    uint32_t ops_length;
    bool written;
};

static uint8_t *pgo_value_ops = NULL;
static uint32_t pgo_value_ops_size = 0;
static uint32_t pgo_value_ops_used = 0;

// Absolute limit for the current value serialization, and whether it was
// exceeded, in which case the value is recorded as not captured.
static uint32_t pgo_value_ops_limit = (uint32_t)-1;
static bool pgo_value_too_large = false;

static struct PGO_ValueEntry *pgo_value_entries = NULL;
static uint32_t pgo_value_entries_size = 0;
static uint32_t pgo_value_entries_used = 0;

// Observed values of repeatable class prepare probes, as they are written at
// the end, deduplicating equal observations by counting them.
struct PGO_ClassObservation {
    uint32_t key_id;
    uint32_t value_id;
    uint32_t count;
};

static struct PGO_ClassObservation *pgo_class_observations = NULL;
static uint32_t pgo_class_observations_size = 0;
static uint32_t pgo_class_observations_used = 0;

static void PGO_writeUvarint(uint64_t value) {
    assert(pgo_output != NULL);

    while (value >= 0x80) {
        fputc((int)((value & 0x7f) | 0x80), pgo_output);
        value >>= 7;
    }

    fputc((int)value, pgo_output);
}

static void PGO_writeProbeId(uint32_t probe_id) { PGO_writeUvarint(probe_id); }

static uint32_t PGO_getStringID(char const *value, uint32_t length, bool *is_new) {
    for (uint32_t i = 0; i < pgo_string_entries_used; i++) {
        if (pgo_string_entries[i].length == length && memcmp(pgo_string_entries[i].value, value, length) == 0) {
            *is_new = false;

            return i;
        }
    }

    if (pgo_string_entries_used == pgo_string_entries_size) {
        pgo_string_entries_size += 1024;
        pgo_string_entries = realloc(pgo_string_entries, pgo_string_entries_size * sizeof(struct PGO_StringEntry));
    }

    uint32_t result = pgo_string_entries_used;

    pgo_string_entries[result].value = (char *)malloc(length + 1);
    memcpy(pgo_string_entries[result].value, value, length);
    pgo_string_entries[result].value[length] = 0;
    pgo_string_entries[result].length = length;
    pgo_string_entries[result].written = false;
    pgo_string_entries_used += 1;

    *is_new = true;

    return result;
}

static uint32_t PGO_getStringIDForCString(char const *value, bool *is_new) {
    return PGO_getStringID(value, (uint32_t)strlen(value), is_new);
}

static void PGO_writeStringReference(uint32_t string_id) { PGO_writeUvarint(string_id); }

static uint32_t PGO_getKeyID(uint32_t scope_kind, uint32_t string_id, bool *is_new) {
    for (uint32_t i = 0; i < pgo_key_entries_used; i++) {
        if (pgo_key_entries[i].scope_kind == scope_kind && pgo_key_entries[i].string_id == string_id) {
            *is_new = false;

            return i;
        }
    }

    if (pgo_key_entries_used == pgo_key_entries_size) {
        pgo_key_entries_size += 1024;
        pgo_key_entries = realloc(pgo_key_entries, pgo_key_entries_size * sizeof(struct PGO_KeyEntry));
    }

    uint32_t result = pgo_key_entries_used;
    pgo_key_entries[result].scope_kind = scope_kind;
    pgo_key_entries[result].string_id = string_id;
    pgo_key_entries[result].exhausted = false;
    pgo_key_entries[result].written = false;
    pgo_key_entries_used += 1;

    *is_new = true;

    return result;
}

static uint32_t PGO_getKeyIDForCString(uint32_t scope_kind, char const *value, bool *is_new) {
    bool new_string;
    uint32_t string_id = PGO_getStringIDForCString(value, &new_string);

    return PGO_getKeyID(scope_kind, string_id, is_new);
}

// Write a key reference, the definition is written before use.
static void PGO_writeKeyReferenceByID(uint32_t key_id) { PGO_writeUvarint(key_id); }

static void PGO_valueOpsAppendRaw(uint8_t const *data, uint32_t length) {
    if (pgo_value_ops_used + length > pgo_value_ops_limit) {
        // The value will be recorded as not captured, so stop growing it.
        pgo_value_too_large = true;

        return;
    }

    if (pgo_value_ops_used + length > pgo_value_ops_size) {
        while (pgo_value_ops_used + length > pgo_value_ops_size) {
            pgo_value_ops_size = pgo_value_ops_size == 0 ? 1024 : pgo_value_ops_size * 2;
        }

        pgo_value_ops = realloc(pgo_value_ops, pgo_value_ops_size);
    }

    memcpy(pgo_value_ops + pgo_value_ops_used, data, length);
    pgo_value_ops_used += length;
}

static void PGO_valueOpsAppendByte(uint8_t value) { PGO_valueOpsAppendRaw(&value, 1); }

static void PGO_valueOpsAppendUvarint(uint64_t value) {
    PGO_valueOpsAppendByte(PGO_VALUE_OP_UVARINT);

    uint8_t buffer[10];
    uint32_t length = 0;

    while (value >= 0x80) {
        buffer[length++] = (uint8_t)((value & 0x7f) | 0x80);
        value >>= 7;
    }

    buffer[length++] = (uint8_t)value;

    PGO_valueOpsAppendRaw(buffer, length);
}

static void PGO_valueOpsAppendUint32(uint32_t value) { PGO_valueOpsAppendRaw((uint8_t *)&value, 4); }

static void PGO_valueOpsAppendDouble(double value) {
    PGO_valueOpsAppendByte(PGO_VALUE_OP_UINT64);

    uint64_t bits;
    memcpy(&bits, &value, 8);

    // Store big endian, so the file write is a plain copy.
    uint8_t buffer[8];

    for (uint32_t i = 0; i < 8; i++) {
        buffer[i] = (uint8_t)(bits >> (56 - 8 * i));
    }

    PGO_valueOpsAppendRaw(buffer, 8);
}

static bool PGO_serializeValue(PyThreadState *tstate, PyObject *value, uint32_t depth);

static void PGO_serializeTooLargeValue(uint8_t type_tag, uint64_t size) {
    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_TOO_LARGE);
    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(type_tag);
    PGO_valueOpsAppendUvarint(size);
}

static void PGO_serializeTooLargeEncodingValue(void) {
    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_TOO_LARGE_ENCODING);
}

static void PGO_serializeTooManyValue(void) {
    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_TOO_MANY);
}

// A value that the writer could not represent at all, e.g. because even the
// reduce fallback failed. Recorded so that a missing key reliably means the
// probe never fired.
static void PGO_serializeUnsupportedValue(void) {
    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_UNSUPPORTED);
}

// Add a string object (unicode on Python3, str or unicode on Python2) to the
// string space and return its ID.
static bool PGO_getStringIDFromTextObject(PyObject *value, uint32_t *string_id) {
    PyObject *encoded;

#if PYTHON_VERSION >= 0x300
    encoded = PyUnicode_AsUTF8String(value);

    if (encoded == NULL) {
        return false;
    }
#else
    if (PyUnicode_Check(value)) {
        encoded = PyUnicode_AsUTF8String(value);

        if (encoded == NULL) {
            return false;
        }
    } else {
        encoded = value;
        Py_INCREF(encoded);
    }
#endif

    char *data;
    Py_ssize_t data_length;
    int res = PyBytes_AsStringAndSize(encoded, &data, &data_length);
    assert(res == 0);

    bool is_new;
    *string_id = PGO_getStringID(data, (uint32_t)data_length, &is_new);

    Py_DECREF(encoded);

    return true;
}

// A Python int that does not fit into a C "long long" is written as its
// decimal string, so the value is preserved exactly, and a py2 "long" and a
// py3 big "int" produce the same output.
static bool PGO_serializeBigInt(PyThreadState *tstate, PyObject *value) {
    PyObject *decimal = PyObject_Str(value);

    if (decimal == NULL) {
        DROP_ERROR_OCCURRED(tstate);

        return false;
    }

    uint32_t string_id;

    if (!PGO_getStringIDFromTextObject(decimal, &string_id)) {
        Py_DECREF(decimal);
        DROP_ERROR_OCCURRED(tstate);

        return false;
    }

    Py_DECREF(decimal);

    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_BIG_INT);
    PGO_valueOpsAppendByte(PGO_VALUE_OP_STRING_REF);
    PGO_valueOpsAppendUint32(string_id);

    return true;
}

// Types, functions and modules are referenced by their module and qualified
// name, so the reader can resolve them.
static bool PGO_serializeGlobal(PyThreadState *tstate, PyObject *value) {
    PyObject *module = PyObject_GetAttrString(value, "__module__");

    if (module == NULL) {
        DROP_ERROR_OCCURRED(tstate);

        return false;
    }

#if PYTHON_VERSION >= 0x300
    PyObject *qualname = PyObject_GetAttrString(value, "__qualname__");
#else
    PyObject *qualname = PyObject_GetAttrString(value, "__name__");
#endif

    if (qualname == NULL) {
        Py_DECREF(module);
        DROP_ERROR_OCCURRED(tstate);

        return false;
    }

    uint32_t module_id;
    uint32_t qualname_id;
    bool result =
        PGO_getStringIDFromTextObject(module, &module_id) && PGO_getStringIDFromTextObject(qualname, &qualname_id);

    Py_DECREF(module);
    Py_DECREF(qualname);

    if (!result) {
        DROP_ERROR_OCCURRED(tstate);

        return false;
    }

    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_GLOBAL);
    PGO_valueOpsAppendByte(PGO_VALUE_OP_STRING_REF);
    PGO_valueOpsAppendUint32(module_id);
    PGO_valueOpsAppendByte(PGO_VALUE_OP_STRING_REF);
    PGO_valueOpsAppendUint32(qualname_id);

    return true;
}

// Generic fallback for values not covered by the direct tags, using
// "__reduce_ex__" like pickle does, with a "G" reference for the callable.
static bool PGO_serializeReduced(PyThreadState *tstate, PyObject *value, uint32_t depth) {
    PyObject *reduced = PyObject_CallMethod(value, "__reduce_ex__", "(i)", 2);

    if (reduced == NULL) {
        DROP_ERROR_OCCURRED(tstate);

        reduced = PyObject_CallMethod(value, "__reduce__", NULL);
    }

    if (reduced == NULL) {
        DROP_ERROR_OCCURRED(tstate);

        return false;
    }

    if (!PyTuple_CheckExact(reduced) || PyTuple_GET_SIZE(reduced) < 2 || PyTuple_GET_SIZE(reduced) > 5) {
        Py_DECREF(reduced);

        return false;
    }

    PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
    PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_REDUCED);

    // The type of the value first, so at least that is known if the
    // reconstruction of the value fails.
    if (!PGO_serializeValue(tstate, (PyObject *)Py_TYPE(value), depth + 1)) {
        Py_DECREF(reduced);

        return false;
    }

    for (uint32_t i = 0; i < 5; i++) {
        PyObject *part;

        if (i < (uint32_t)PyTuple_GET_SIZE(reduced)) {
            part = PyTuple_GET_ITEM(reduced, i);
        } else {
            part = Py_None;
        }

        if (part == Py_None) {
            PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
            PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_NONE);
        } else if (i >= 3) {
            // The list and dict items are iterators, consume them into a list.
            PyObject *items = PySequence_List(part);

            if (items == NULL) {
                DROP_ERROR_OCCURRED(tstate);
                Py_DECREF(reduced);

                return false;
            }

            bool result = PGO_serializeValue(tstate, items, depth + 1);

            Py_DECREF(items);

            if (!result) {
                Py_DECREF(reduced);

                return false;
            }
        } else if (!PGO_serializeValue(tstate, part, depth + 1)) {
            Py_DECREF(reduced);

            return false;
        }

        if (pgo_value_too_large) {
            break;
        }
    }

    Py_DECREF(reduced);

    return true;
}

// Serialize the items of a container inline, they become part of its
// definition rather than being separate values.
static bool PGO_serializeContainerItems(PyThreadState *tstate, PyObject *value, uint32_t depth) {
    PyObject *iterator = PyObject_GetIter(value);

    if (iterator == NULL) {
        return false;
    }

    PyObject *item;

    while ((item = PyIter_Next(iterator)) != NULL) {
        if (pgo_value_too_large) {
            Py_DECREF(item);

            break;
        }

        bool result = PGO_serializeValue(tstate, item, depth);

        Py_DECREF(item);

        if (!result) {
            Py_DECREF(iterator);

            return false;
        }
    }

    Py_DECREF(iterator);

    return !HAS_ERROR_OCCURRED(tstate);
}

static bool PGO_serializeValue(PyThreadState *tstate, PyObject *value, uint32_t depth) {
    CHECK_OBJECT(value);

    if (depth > 100) {
        return false;
    }

    if (value == Py_None) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_NONE);

        return true;
    }

    if (value == Py_True) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_TRUE);

        return true;
    }

    if (value == Py_False) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_FALSE);

        return true;
    }

    if (value == Py_Ellipsis) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_ELLIPSIS);

        return true;
    }

    if (PyLong_CheckExact(value)) {
#if PYTHON_VERSION < 0x300
        long long integer_value = PyLong_AsLongLong(value);

        if (integer_value == -1 && HAS_ERROR_OCCURRED(tstate)) {
            DROP_ERROR_OCCURRED(tstate);

            return PGO_serializeBigInt(tstate, value);
        }
#else
        int overflow = 0;
        long long integer_value = PyLong_AsLongLongAndOverflow(value, &overflow);

        if (integer_value == -1 && HAS_ERROR_OCCURRED(tstate)) {
            DROP_ERROR_OCCURRED(tstate);

            return false;
        }

        if (overflow != 0) {
            return PGO_serializeBigInt(tstate, value);
        }
#endif

        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);

        if (integer_value >= 0) {
            PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_INT_POSITIVE);
            PGO_valueOpsAppendUvarint((uint64_t)integer_value);
        } else {
            PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_INT_NEGATIVE);
            PGO_valueOpsAppendUvarint((uint64_t)(-(integer_value + 1)) + 1);
        }

        return true;
    }

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(value)) {
        long integer_value = PyInt_AS_LONG(value);

        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);

        if (integer_value >= 0) {
            PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_INT_POSITIVE);
            PGO_valueOpsAppendUvarint((uint64_t)integer_value);
        } else {
            PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_INT_NEGATIVE);
            PGO_valueOpsAppendUvarint((uint64_t)(-(integer_value + 1)) + 1);
        }

        return true;
    }
#endif

    if (PyFloat_CheckExact(value)) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_FLOAT);
        PGO_valueOpsAppendDouble(PyFloat_AS_DOUBLE(value));

        return true;
    }

    if (PyComplex_CheckExact(value)) {
        Py_complex complex_value = PyComplex_AsCComplex(value);

        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_COMPLEX);
        PGO_valueOpsAppendDouble(complex_value.real);
        PGO_valueOpsAppendDouble(complex_value.imag);

        return true;
    }

    if (PyUnicode_CheckExact(value)) {
        PyObject *encoded = PyUnicode_AsUTF8String(value);

        if (encoded == NULL) {
            DROP_ERROR_OCCURRED(tstate);

            return false;
        }

        char *data;
        Py_ssize_t data_length;
        int res = PyBytes_AsStringAndSize(encoded, &data, &data_length);
        assert(res == 0);

#if PYTHON_VERSION < 0x300
        uint8_t const type_tag = NUITKA_PGO_VALUE_TAG_UNICODE;
#else
        uint8_t const type_tag = NUITKA_PGO_VALUE_TAG_STR;
#endif

        if ((uint64_t)data_length > PGO_VALUE_MAX_STRING_SIZE) {
            PGO_serializeTooLargeValue(type_tag, (uint64_t)data_length);

            Py_DECREF(encoded);

            return true;
        }

        bool new_string;
        uint32_t string_id = PGO_getStringID(data, (uint32_t)data_length, &new_string);

        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(type_tag);
        PGO_valueOpsAppendByte(PGO_VALUE_OP_STRING_REF);
        PGO_valueOpsAppendUint32(string_id);

        Py_DECREF(encoded);

        return true;
    }

#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(value)) {
        uint64_t data_length = (uint64_t)PyString_GET_SIZE(value);

        if (data_length > PGO_VALUE_MAX_STRING_SIZE) {
            PGO_serializeTooLargeValue(NUITKA_PGO_VALUE_TAG_STR, data_length);

            return true;
        }

        bool new_string;
        uint32_t string_id = PGO_getStringID(PyString_AS_STRING(value), (uint32_t)data_length, &new_string);

        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_STR);
        PGO_valueOpsAppendByte(PGO_VALUE_OP_STRING_REF);
        PGO_valueOpsAppendUint32(string_id);

        return true;
    }
#else
    if (PyBytes_CheckExact(value)) {
        char *data;
        Py_ssize_t data_length;
        int res = PyBytes_AsStringAndSize(value, &data, &data_length);
        assert(res == 0);

        if ((uint64_t)data_length > PGO_VALUE_MAX_STRING_SIZE) {
            PGO_serializeTooLargeValue(NUITKA_PGO_VALUE_TAG_BYTES, (uint64_t)data_length);

            return true;
        }

        bool new_string;
        uint32_t string_id = PGO_getStringID(data, (uint32_t)data_length, &new_string);

        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_BYTES);
        PGO_valueOpsAppendByte(PGO_VALUE_OP_STRING_REF);
        PGO_valueOpsAppendUint32(string_id);

        return true;
    }
#endif

    if (PyByteArray_CheckExact(value)) {
        uint64_t data_length = (uint64_t)PyByteArray_GET_SIZE(value);

        if (data_length > PGO_VALUE_MAX_STRING_SIZE) {
            PGO_serializeTooLargeValue(NUITKA_PGO_VALUE_TAG_BYTEARRAY, data_length);

            return true;
        }

        bool new_string;
        uint32_t string_id = PGO_getStringID(PyByteArray_AS_STRING(value), (uint32_t)data_length, &new_string);

        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_BYTEARRAY);
        PGO_valueOpsAppendByte(PGO_VALUE_OP_STRING_REF);
        PGO_valueOpsAppendUint32(string_id);

        return true;
    }

    if (PyList_CheckExact(value)) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_LIST);
        PGO_valueOpsAppendUvarint((uint64_t)PyList_GET_SIZE(value));

        return PGO_serializeContainerItems(tstate, value, depth + 1);
    }

    if (PyTuple_CheckExact(value)) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_TUPLE);
        PGO_valueOpsAppendUvarint((uint64_t)PyTuple_GET_SIZE(value));

        return PGO_serializeContainerItems(tstate, value, depth + 1);
    }

    if (PyDict_CheckExact(value)) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(NUITKA_PGO_VALUE_TAG_DICT);
        PGO_valueOpsAppendUvarint((uint64_t)DICT_SIZE(value));

        Py_ssize_t position = 0;
        PyObject *key;
        PyObject *item;

        while (PyDict_Next(value, &position, &key, &item)) {
            if (pgo_value_too_large) {
                break;
            }

            if (!PGO_serializeValue(tstate, key, depth + 1) || !PGO_serializeValue(tstate, item, depth + 1)) {
                return false;
            }
        }

        return true;
    }

    if (PySet_CheckExact(value) || PyFrozenSet_CheckExact(value)) {
        PGO_valueOpsAppendByte(PGO_VALUE_OP_TAG);
        PGO_valueOpsAppendByte(PyFrozenSet_CheckExact(value) ? NUITKA_PGO_VALUE_TAG_FROZENSET
                                                             : NUITKA_PGO_VALUE_TAG_SET);
        PGO_valueOpsAppendUvarint((uint64_t)PySet_Size(value));

        return PGO_serializeContainerItems(tstate, value, depth + 1);
    }

    if (PyType_Check(value) || PyFunction_Check(value) || PyCFunction_Check(value)) {
        return PGO_serializeGlobal(tstate, value);
    }

    // Generic fallback for everything else, using "__reduce_ex__".
    return PGO_serializeReduced(tstate, value, depth);
}

static uint32_t PGO_registerValue(uint32_t ops_start) {
    uint32_t ops_length = pgo_value_ops_used - ops_start;

    // Content deduplication, canonical IDs in the operations make this work.
    for (uint32_t i = 0; i < pgo_value_entries_used; i++) {
        if (pgo_value_entries[i].ops_length == ops_length &&
            memcmp(pgo_value_ops + pgo_value_entries[i].ops_start, pgo_value_ops + ops_start, ops_length) == 0) {
            pgo_value_ops_used = ops_start;

            return i;
        }
    }

    if (pgo_value_entries_used == pgo_value_entries_size) {
        pgo_value_entries_size += 1024;
        pgo_value_entries = realloc(pgo_value_entries, pgo_value_entries_size * sizeof(struct PGO_ValueEntry));
    }

    uint32_t result_id = pgo_value_entries_used;

    pgo_value_entries[result_id].ops_start = ops_start;
    pgo_value_entries[result_id].ops_length = ops_length;
    pgo_value_entries[result_id].written = false;
    pgo_value_entries_used += 1;

    return result_id;
}

static uint32_t PGO_getTooManyValueID(void) {
    uint32_t ops_start = pgo_value_ops_used;

    PGO_serializeTooManyValue();

    return PGO_registerValue(ops_start);
}

static uint32_t PGO_getUnsupportedValueID(void) {
    uint32_t ops_start = pgo_value_ops_used;

    PGO_serializeUnsupportedValue();

    return PGO_registerValue(ops_start);
}

static bool PGO_getValueID(PyThreadState *tstate, PyObject *value, uint32_t *value_id, uint32_t depth) {
    uint32_t ops_start = pgo_value_ops_used;

    pgo_value_ops_limit = ops_start + PGO_VALUE_MAX_SERIALIZED_SIZE;
    pgo_value_too_large = false;

    bool result = PGO_serializeValue(tstate, value, depth);

    pgo_value_ops_limit = (uint32_t)-1;

    if (!result) {
        pgo_value_ops_used = ops_start;

        return false;
    }

    if (pgo_value_too_large) {
        pgo_value_ops_used = ops_start;

        PGO_serializeTooLargeEncodingValue();
    }

    *value_id = PGO_registerValue(ops_start);

    return true;
}

static void PGO_writeValueReference(uint32_t value_id) { PGO_writeUvarint(value_id); }

static void PGO_writeStringDefinition(uint32_t string_id) {
    pgo_string_entries[string_id].written = true;

    PGO_writeProbeId(NUITKA_PGO_PROBE_STRING_DEFINITION);
    PGO_writeUvarint(string_id);
    PGO_writeUvarint(pgo_string_entries[string_id].length);
    fwrite(pgo_string_entries[string_id].value, pgo_string_entries[string_id].length, 1, pgo_output);
}

static void PGO_writeKeyDefinition(uint32_t key_id) {
    pgo_key_entries[key_id].written = true;

    PGO_writeProbeId(NUITKA_PGO_PROBE_KEY_DEFINITION);
    PGO_writeUvarint(key_id);
    PGO_writeUvarint(pgo_key_entries[key_id].scope_kind);
    PGO_writeUvarint(pgo_key_entries[key_id].string_id);
}

static void PGO_writeValueDefinition(uint32_t value_id) {
    pgo_value_entries[value_id].written = true;

    PGO_writeProbeId(NUITKA_PGO_PROBE_VALUE_DEFINITION);
    PGO_writeUvarint(value_id);

    uint32_t offset = pgo_value_entries[value_id].ops_start;
    uint32_t end = offset + pgo_value_entries[value_id].ops_length;

    while (offset < end) {
        uint8_t op = pgo_value_ops[offset++];

        if (op == PGO_VALUE_OP_TAG) {
            fputc(pgo_value_ops[offset++], pgo_output);
        } else if (op == PGO_VALUE_OP_UVARINT) {
            uint64_t value = 0;
            uint32_t shift = 0;

            for (;;) {
                uint8_t byte = pgo_value_ops[offset++];

                value |= (uint64_t)(byte & 0x7f) << shift;

                if ((byte & 0x80) == 0) {
                    break;
                }

                shift += 7;
            }

            PGO_writeUvarint(value);
        } else if (op == PGO_VALUE_OP_STRING_REF) {
            uint32_t string_id;
            memcpy(&string_id, pgo_value_ops + offset, 4);
            offset += 4;

            PGO_writeStringReference(string_id);
        } else {
            assert(op == PGO_VALUE_OP_UINT64);

            fwrite(pgo_value_ops + offset, 8, 1, pgo_output);
            offset += 8;
        }
    }
}

// Write definitions of all entries that were not written yet, so that records
// can reference them by ID alone. Strings come first, then keys, then values,
// which guarantees definitions only reference earlier definitions.
static void PGO_writeDefinitions(void) {
    for (uint32_t i = 0; i < pgo_string_entries_used; i++) {
        if (!pgo_string_entries[i].written) {
            PGO_writeStringDefinition(i);
        }
    }

    for (uint32_t i = 0; i < pgo_key_entries_used; i++) {
        if (!pgo_key_entries[i].written) {
            PGO_writeKeyDefinition(i);
        }
    }

    for (uint32_t i = 0; i < pgo_value_entries_used; i++) {
        if (!pgo_value_entries[i].written) {
            PGO_writeValueDefinition(i);
        }
    }
}

static uint32_t PGO_getClassKeyID(char const *code_name) {
    bool new_string;
    uint32_t string_id = PGO_getStringIDForCString(code_name, &new_string);

    bool new_key;
    uint32_t key_id = PGO_getKeyID(NUITKA_PGO_SCOPE_CLASS, string_id, &new_key);

    return key_id;
}

void PGO_Initialize(void) {
    // We expect an environment variable to guide us to where the PGO information
    // shall be written to.
    char const *output_filename = getenv("NUITKA_PGO_OUTPUT");

    if (unlikely(output_filename == NULL)) {
        NUITKA_CANNOT_GET_HERE("NUITKA_PGO_OUTPUT needs to be set");
    }

    pgo_output = fopen(output_filename, "wb");

    if (unlikely(pgo_output == NULL)) {
        fprintf(stderr, "Error, failed to open '%s' for writing.\n", output_filename);
        exit(27);
    }

    fputs("KAY.PGO", pgo_output);

    // The format version of this file.
    PGO_writeUvarint(2);

    pgo_string_entries_size = 1024;
    pgo_string_entries = malloc(pgo_string_entries_size * sizeof(struct PGO_StringEntry));

    pgo_key_entries_size = 1024;
    pgo_key_entries = malloc(pgo_key_entries_size * sizeof(struct PGO_KeyEntry));

    pgo_value_entries_size = 1024;
    pgo_value_entries = malloc(pgo_value_entries_size * sizeof(struct PGO_ValueEntry));
}

void PGO_Finalize(void) {
    assert(pgo_output != NULL);

    PGO_writeDefinitions();

    for (uint32_t i = 0; i < pgo_class_observations_used; i++) {
        PGO_writeProbeId(NUITKA_PGO_PROBE_CLASS_PREPARE_RESULT);
        PGO_writeKeyReferenceByID(pgo_class_observations[i].key_id);
        PGO_writeValueReference(pgo_class_observations[i].value_id);
        PGO_writeUvarint(pgo_class_observations[i].count);
    }

    PGO_writeProbeId(NUITKA_PGO_PROBE_END);

    // Table sizes of the entries that were written before.
    uint32_t string_count = 0;
    uint32_t key_count = 0;
    uint32_t value_count = 0;

    for (uint32_t i = 0; i < pgo_string_entries_used; i++) {
        if (pgo_string_entries[i].written) {
            string_count += 1;
        }
    }

    for (uint32_t i = 0; i < pgo_key_entries_used; i++) {
        if (pgo_key_entries[i].written) {
            key_count += 1;
        }
    }

    for (uint32_t i = 0; i < pgo_value_entries_used; i++) {
        if (pgo_value_entries[i].written) {
            value_count += 1;
        }
    }

    PGO_writeUvarint(string_count);
    PGO_writeUvarint(key_count);
    PGO_writeUvarint(value_count);

    fputs("YAK.PGO", pgo_output);

    fclose(pgo_output);
    pgo_output = NULL;

    for (uint32_t i = 0; i < pgo_string_entries_used; i++) {
        free(pgo_string_entries[i].value);
    }

    free(pgo_string_entries);
    pgo_string_entries = NULL;

    free(pgo_key_entries);
    pgo_key_entries = NULL;

    free(pgo_value_ops);
    pgo_value_ops = NULL;

    free(pgo_value_entries);
    pgo_value_entries = NULL;

    free(pgo_class_observations);
    pgo_class_observations = NULL;
}

void PGO_onModuleEntered(char const *module_name) {
    bool is_new;
    uint32_t key_id = PGO_getKeyIDForCString(NUITKA_PGO_SCOPE_MODULE, module_name, &is_new);

    PGO_writeDefinitions();

    PGO_writeProbeId(NUITKA_PGO_PROBE_MODULE_ENTER);
    PGO_writeKeyReferenceByID(key_id);
}

void PGO_onModuleExit(char const *module_name, bool had_error) {
    bool is_new;
    uint32_t key_id = PGO_getKeyIDForCString(NUITKA_PGO_SCOPE_MODULE, module_name, &is_new);

    PGO_writeDefinitions();

    PGO_writeProbeId(NUITKA_PGO_PROBE_MODULE_EXIT);
    PGO_writeKeyReferenceByID(key_id);

    PGO_writeUvarint(had_error ? 1 : 0);
}

void PGO_onProbeClassPrepareResult(PyThreadState *tstate, char const *code_name, PyObject *result) {
    uint32_t key_id = PGO_getClassKeyID(code_name);

    if (pgo_key_entries[key_id].exhausted) {
        return;
    }

    uint32_t value_id;

    if (!PGO_getValueID(tstate, result, &value_id, 0)) {
        value_id = PGO_getUnsupportedValueID();
    }

    for (uint32_t i = 0; i < pgo_class_observations_used; i++) {
        if (pgo_class_observations[i].key_id == key_id && pgo_class_observations[i].value_id == value_id) {
            pgo_class_observations[i].count += 1;

            return;
        }
    }

    uint32_t accumulated_size = pgo_value_entries[value_id].ops_length;

    for (uint32_t i = 0; i < pgo_class_observations_used; i++) {
        if (pgo_class_observations[i].key_id == key_id) {
            accumulated_size += pgo_value_entries[pgo_class_observations[i].value_id].ops_length;
        }
    }

    if (accumulated_size > PGO_KEY_MAX_SERIALIZED_SIZE) {
        pgo_key_entries[key_id].exhausted = true;

        value_id = PGO_getTooManyValueID();

        for (uint32_t i = 0; i < pgo_class_observations_used; i++) {
            if (pgo_class_observations[i].key_id == key_id && pgo_class_observations[i].value_id == value_id) {
                return;
            }
        }
    }

    if (pgo_class_observations_used == pgo_class_observations_size) {
        pgo_class_observations_size += 1024;
        pgo_class_observations =
            realloc(pgo_class_observations, pgo_class_observations_size * sizeof(struct PGO_ClassObservation));
    }

    pgo_class_observations[pgo_class_observations_used].key_id = key_id;
    pgo_class_observations[pgo_class_observations_used].value_id = value_id;
    pgo_class_observations[pgo_class_observations_used].count = 1;
    pgo_class_observations_used += 1;
}

void PGO_onProbeClassPrepareResultOnce(PyThreadState *tstate, char const *code_name, PyObject *result) {
    uint32_t value_id;

    if (!PGO_getValueID(tstate, result, &value_id, 0)) {
        value_id = PGO_getUnsupportedValueID();
    }

    uint32_t key_id = PGO_getClassKeyID(code_name);

    PGO_writeDefinitions();

    PGO_writeProbeId(NUITKA_PGO_PROBE_CLASS_PREPARE_RESULT_ONCE);
    PGO_writeKeyReferenceByID(key_id);
    PGO_writeValueReference(value_id);
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
