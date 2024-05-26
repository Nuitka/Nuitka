//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/**
 * This is responsible for deep copy and hashing of constants.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION >= 0x390
typedef struct {
    PyObject_HEAD PyObject *origin;
    PyObject *args;
    PyObject *parameters;
} GenericAliasObject;
#endif

typedef PyObject *(*copy_func)(PyThreadState *tstate, PyObject *);

static PyObject *DEEP_COPY_ITEM(PyThreadState *tstate, PyObject *value, PyTypeObject **type, copy_func *copy_function);

PyObject *DEEP_COPY_LIST(PyThreadState *tstate, PyObject *value) {
    assert(PyList_CheckExact(value));

    Py_ssize_t n = PyList_GET_SIZE(value);
    PyObject *result = MAKE_LIST_EMPTY(tstate, n);

    PyTypeObject *type = NULL;
    copy_func copy_function = NULL;

    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *item = PyList_GET_ITEM(value, i);
        if (i == 0) {
            PyList_SET_ITEM(result, i, DEEP_COPY_ITEM(tstate, item, &type, &copy_function));
        } else {
            PyObject *new_item;

            if (likely(type == Py_TYPE(item))) {
                if (copy_function) {
                    new_item = copy_function(tstate, item);
                } else {
                    new_item = item;
                    Py_INCREF(item);
                }
            } else {
                new_item = DEEP_COPY_ITEM(tstate, item, &type, &copy_function);
            }

            PyList_SET_ITEM(result, i, new_item);
        }
    }

    return result;
}

PyObject *DEEP_COPY_TUPLE(PyThreadState *tstate, PyObject *value) {
    assert(PyTuple_CheckExact(value));

    Py_ssize_t n = PyTuple_GET_SIZE(value);

    PyObject *result = MAKE_TUPLE_EMPTY_VAR(tstate, n);

    for (Py_ssize_t i = 0; i < n; i++) {
        PyTuple_SET_ITEM(result, i, DEEP_COPY(tstate, PyTuple_GET_ITEM(value, i)));
    }

    return result;
}

static PyObject *_DEEP_COPY_SET(PyObject *value) {
    // Sets cannot contain non-hashable types, so these all must be immutable,
    // but the set itself might be changed, so we need to copy it.
    return PySet_New(value);
}

PyObject *DEEP_COPY_SET(PyThreadState *tstate, PyObject *value) { return _DEEP_COPY_SET(value); }

#if PYTHON_VERSION >= 0x390
PyObject *DEEP_COPY_GENERICALIAS(PyThreadState *tstate, PyObject *value) {
    assert(Py_TYPE(value) == &Py_GenericAliasType);

    GenericAliasObject *generic_alias = (GenericAliasObject *)value;

    PyObject *args = DEEP_COPY(tstate, generic_alias->args);
    PyObject *origin = DEEP_COPY(tstate, generic_alias->origin);

    if (generic_alias->args == args && generic_alias->origin == origin) {
        Py_INCREF(value);
        return value;
    } else {
        return Py_GenericAlias(origin, args);
    }
}
#endif

static PyObject *_deep_copy_dispatch = NULL;
static PyObject *_deep_noop = NULL;

static PyObject *Nuitka_CapsuleNew(void *pointer) {
#if PYTHON_VERSION < 0x300
    return PyCObject_FromVoidPtr(pointer, NULL);
#else
    return PyCapsule_New(pointer, "", NULL);
#endif
}

#if PYTHON_VERSION >= 0x300
typedef struct {
    PyObject_HEAD void *pointer;
    const char *name;
    void *context;
    PyCapsule_Destructor destructor;
} Nuitka_PyCapsule;

#define Nuitka_CapsuleGetPointer(capsule) (((Nuitka_PyCapsule *)(capsule))->pointer)

#else
#define Nuitka_CapsuleGetPointer(capsule) (PyCObject_AsVoidPtr(capsule))
#endif

#if PYTHON_VERSION >= 0x3a0
PyTypeObject *Nuitka_PyUnion_Type;
#endif

static PyObject *_makeDeepCopyFunctionCapsule(copy_func func) { return Nuitka_CapsuleNew((void *)func); }

static void _initDeepCopy(void) {
    _deep_copy_dispatch = PyDict_New();
    _deep_noop = Py_None;

    CHECK_OBJECT(_deep_noop);

    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyDict_Type, _makeDeepCopyFunctionCapsule(DEEP_COPY_DICT));
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyList_Type, _makeDeepCopyFunctionCapsule(DEEP_COPY_LIST));
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyTuple_Type, _makeDeepCopyFunctionCapsule(DEEP_COPY_TUPLE));
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PySet_Type, _makeDeepCopyFunctionCapsule(DEEP_COPY_SET));
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyByteArray_Type, _makeDeepCopyFunctionCapsule(BYTEARRAY_COPY));

#if PYTHON_VERSION >= 0x390
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&Py_GenericAliasType,
                   _makeDeepCopyFunctionCapsule(DEEP_COPY_GENERICALIAS));
#endif

#if PYTHON_VERSION >= 0x3a0
    {
        PyThreadState *tstate = PyThreadState_GET();

        PyObject *args[2] = {(PyObject *)&PyFloat_Type, (PyObject *)&PyTuple_Type};
        PyObject *args_tuple = MAKE_TUPLE(tstate, args, 2);
        PyObject *union_value = MAKE_UNION_TYPE(args_tuple);

        Nuitka_PyUnion_Type = Py_TYPE(union_value);

        PyDict_SetItem(_deep_copy_dispatch, (PyObject *)Nuitka_PyUnion_Type, _deep_noop);

        Py_DECREF(union_value);
        Py_DECREF(args_tuple);
    }

#endif

#if PYTHON_VERSION < 0x300
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyString_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyInt_Type, _deep_noop);
#else
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyBytes_Type, _deep_noop);
#endif
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyUnicode_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyLong_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)Py_TYPE(Py_None), _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyBool_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyFloat_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyRange_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyType_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PySlice_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyComplex_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyCFunction_Type, _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)Py_TYPE(Py_Ellipsis), _deep_noop);
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)Py_TYPE(Py_NotImplemented), _deep_noop);

    // Sets can be changed, but not a frozenset.
    PyDict_SetItem(_deep_copy_dispatch, (PyObject *)&PyFrozenSet_Type, _deep_noop);
}

static PyObject *DEEP_COPY_ITEM(PyThreadState *tstate, PyObject *value, PyTypeObject **type, copy_func *copy_function) {
    *type = Py_TYPE(value);

    PyObject *dispatcher = DICT_GET_ITEM0(tstate, _deep_copy_dispatch, (PyObject *)*type);

    if (unlikely(dispatcher == NULL)) {
        NUITKA_CANNOT_GET_HERE("DEEP_COPY encountered unknown type");
    }

    if (dispatcher == Py_None) {
        *copy_function = NULL;

        Py_INCREF(value);
        return value;
    } else {
        *copy_function = (copy_func)(Nuitka_CapsuleGetPointer(dispatcher));
        return (*copy_function)(tstate, value);
    }
}

PyObject *DEEP_COPY(PyThreadState *tstate, PyObject *value) {
#if 1
    PyObject *dispatcher = DICT_GET_ITEM0(tstate, _deep_copy_dispatch, (PyObject *)Py_TYPE(value));

    if (unlikely(dispatcher == NULL)) {
        NUITKA_CANNOT_GET_HERE("DEEP_COPY encountered unknown type");
    }

    if (dispatcher == Py_None) {
        Py_INCREF(value);
        return value;
    } else {
        copy_func copy_function = (copy_func)(Nuitka_CapsuleGetPointer(dispatcher));
        return copy_function(tstate, value);
    }

#else

    if (PyDict_CheckExact(value)) {
        return DEEP_COPY_DICT(value);
    } else if (PyList_CheckExact(value)) {
        return DEEP_COPY_LIST(value);
    } else if (PyTuple_CheckExact(value)) {
        return DEEP_COPY_TUPLE(value);
    } else if (PySet_CheckExact(value)) {
        return DEEP_COPY_SET(value);
    } else if (PyFrozenSet_CheckExact(value)) {
        // Sets cannot contain non-hashable types, so they must be immutable and
        // the frozenset itself is immutable.
        return value;
    } else if (
#if PYTHON_VERSION < 0x300
        PyString_Check(value) ||
#endif
        PyUnicode_Check(value) ||
#if PYTHON_VERSION < 0x300
        PyInt_CheckExact(value) ||
#endif
        PyLong_CheckExact(value) || value == Py_None || PyBool_Check(value) || PyFloat_CheckExact(value) ||
        PyBytes_CheckExact(value) || PyRange_Check(value) || PyType_Check(value) || PySlice_Check(value) ||
        PyComplex_CheckExact(value) || PyCFunction_Check(value) || value == Py_Ellipsis || value == Py_NotImplemented) {
        Py_INCREF(value);
        return value;
    } else if (PyByteArray_CheckExact(value)) {
        // TODO: Could make an exception for zero size.
        return PyByteArray_FromObject(value);
#if PYTHON_VERSION >= 0x390
    } else if (Py_TYPE(value) == &Py_GenericAliasType) {
        GenericAliasObject *generic_alias = (GenericAliasObject *)value;

        PyObject *args = DEEP_COPY(generic_alias->args);
        PyObject *origin = DEEP_COPY(generic_alias->origin);

        if (generic_alias->args == args && generic_alias->origin == origin) {
            Py_INCREF(value);
            return value;
        } else {
            return Py_GenericAlias(origin, args);
        }
#endif
    } else {
        NUITKA_CANNOT_GET_HERE("DEEP_COPY encountered unknown type");
    }
#endif
}

#ifndef __NUITKA_NO_ASSERT__

static Py_hash_t DEEP_HASH_INIT(PyThreadState *tstate, PyObject *value) {
    // To avoid warnings about reduced sizes, we put an intermediate value
    // that is size_t.
    size_t value2 = (size_t)value;
    Py_hash_t result = (Py_hash_t)(value2);

    if (Py_TYPE(value) != &PyType_Type) {
        result ^= DEEP_HASH(tstate, (PyObject *)Py_TYPE(value));
    }

    return result;
}

static void DEEP_HASH_BLOB(Py_hash_t *hash, char const *s, Py_ssize_t size) {
    while (size > 0) {
        *hash = (1000003 * (*hash)) ^ (Py_hash_t)(*s++);
        size--;
    }
}

static void DEEP_HASH_CSTR(Py_hash_t *hash, char const *s) { DEEP_HASH_BLOB(hash, s, strlen(s)); }

// Hash function that actually verifies things done to the bit level. Can be
// used to detect corruption.
Py_hash_t DEEP_HASH(PyThreadState *tstate, PyObject *value) {
    assert(value != NULL);

    if (PyType_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        DEEP_HASH_CSTR(&result, ((PyTypeObject *)value)->tp_name);
        return result;
    } else if (PyDict_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        Py_ssize_t pos = 0;
        PyObject *key, *dict_value;

        while (Nuitka_DictNext(value, &pos, &key, &dict_value)) {
            if (key != NULL && value != NULL) {
                result ^= DEEP_HASH(tstate, key);
                result ^= DEEP_HASH(tstate, dict_value);
            }
        }

        return result;
    } else if (PyTuple_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        Py_ssize_t n = PyTuple_GET_SIZE(value);

        for (Py_ssize_t i = 0; i < n; i++) {
            result ^= DEEP_HASH(tstate, PyTuple_GET_ITEM(value, i));
        }

        return result;
    } else if (PyList_CheckExact(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        Py_ssize_t n = PyList_GET_SIZE(value);

        for (Py_ssize_t i = 0; i < n; i++) {
            result ^= DEEP_HASH(tstate, PyList_GET_ITEM(value, i));
        }

        return result;
    } else if (PySet_Check(value) || PyFrozenSet_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        PyObject *iterator = PyObject_GetIter(value);
        CHECK_OBJECT(iterator);

        while (true) {
            PyObject *item = PyIter_Next(iterator);
            if (!item)
                break;

            CHECK_OBJECT(item);

            result ^= DEEP_HASH(tstate, item);

            Py_DECREF(item);
        }

        Py_DECREF(iterator);

        return result;
    } else if (PyLong_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        struct Nuitka_ExceptionPreservationItem saved_exception_state;

        FETCH_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

        // Use string to hash the long value, which relies on that to not
        // use the object address.
        PyObject *str = PyObject_Str(value);
        result ^= DEEP_HASH(tstate, str);
        Py_DECREF(str);

        RESTORE_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

        return result;
    } else if (PyUnicode_Check(value)) {
        Py_hash_t result = DEEP_HASH(tstate, (PyObject *)Py_TYPE(value));

        struct Nuitka_ExceptionPreservationItem saved_exception_state;

        FETCH_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

#if PYTHON_VERSION >= 0x300
        char const *s = (char const *)PyUnicode_DATA(value);
        Py_ssize_t size = PyUnicode_GET_LENGTH(value) * PyUnicode_KIND(value);

        DEEP_HASH_BLOB(&result, s, size);
#else
        PyObject *str = PyUnicode_AsUTF8String(value);

        if (str) {
            result ^= DEEP_HASH(tstate, str);
        }

        Py_DECREF(str);
#endif
        RESTORE_ERROR_OCCURRED_STATE_UNTRACED(tstate, &saved_exception_state);

        return result;
    }
#if PYTHON_VERSION < 0x300
    else if (PyString_Check(value)) {
        Py_hash_t result = DEEP_HASH(tstate, (PyObject *)Py_TYPE(value));

        Py_ssize_t size;
        char *s;

        int res = PyString_AsStringAndSize(value, &s, &size);
        assert(res != -1);

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    }
#else
    else if (PyBytes_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        Py_ssize_t size;
        char *s;

        int res = PyBytes_AsStringAndSize(value, &s, &size);
        assert(res != -1);

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    }
#endif
    else if (PyByteArray_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        Py_ssize_t size = PyByteArray_Size(value);
        assert(size >= 0);

        char *s = PyByteArray_AsString(value);

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    } else if (value == Py_None || value == Py_Ellipsis || value == Py_NotImplemented) {
        return DEEP_HASH_INIT(tstate, value);
    } else if (PyComplex_Check(value)) {
        Py_complex c = PyComplex_AsCComplex(value);

        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        Py_ssize_t size = sizeof(c);
        char *s = (char *)&c;

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    } else if (PyFloat_Check(value)) {
        double f = PyFloat_AsDouble(value);

        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        Py_ssize_t size = sizeof(f);
        char *s = (char *)&f;

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    } else if (
#if PYTHON_VERSION < 0x300
        PyInt_Check(value) ||
#endif
        PyBool_Check(value) || PyRange_Check(value) || PySlice_Check(value) || PyCFunction_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

#if 0
        printf("Too simple deep hash: %s\n", Py_TYPE(value)->tp_name);
#endif

        return result;
#if PYTHON_VERSION >= 0x390
    } else if (Py_TYPE(value) == &Py_GenericAliasType) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        GenericAliasObject *generic_alias = (GenericAliasObject *)value;

        result ^= DEEP_HASH(tstate, generic_alias->args);
        result ^= DEEP_HASH(tstate, generic_alias->origin);

        return result;
#endif
#if PYTHON_VERSION >= 0x3a0
    } else if (Py_TYPE(value) == Nuitka_PyUnion_Type) {
        Py_hash_t result = DEEP_HASH_INIT(tstate, value);

        result ^= DEEP_HASH(tstate, LOOKUP_ATTRIBUTE(tstate, value, const_str_plain___args__));

        return result;
#endif
    } else {
        NUITKA_CANNOT_GET_HERE("Unknown type hashed");

        return -1;
    }
}
#endif

// Note: Not recursion safe, cannot do this everywhere.
void CHECK_OBJECT_DEEP(PyObject *value) {
    CHECK_OBJECT(value);

    if (PyTuple_Check(value)) {
        for (Py_ssize_t i = 0, size = PyTuple_GET_SIZE(value); i < size; i++) {
            PyObject *element = PyTuple_GET_ITEM(value, i);

            CHECK_OBJECT_DEEP(element);
        }
    } else if (PyList_CheckExact(value)) {
        for (Py_ssize_t i = 0, size = PyList_GET_SIZE(value); i < size; i++) {
            PyObject *element = PyList_GET_ITEM(value, i);

            CHECK_OBJECT_DEEP(element);
        }
    } else if (PyDict_Check(value)) {
        Py_ssize_t pos = 0;
        PyObject *dict_key, *dict_value;

        while (Nuitka_DictNext(value, &pos, &dict_key, &dict_value)) {
            CHECK_OBJECT_DEEP(dict_key);
            CHECK_OBJECT_DEEP(dict_value);
        }
    }
}

void CHECK_OBJECTS_DEEP(PyObject *const *values, Py_ssize_t size) {
    for (Py_ssize_t i = 0; i < size; i++) {
        CHECK_OBJECT_DEEP(values[i]);
    }
}

static PyObject *_DEEP_COPY_LIST_GUIDED(PyThreadState *tstate, PyObject *value, char const **guide);
static PyObject *_DEEP_COPY_TUPLE_GUIDED(PyThreadState *tstate, PyObject *value, char const **guide);

static PyObject *_DEEP_COPY_ELEMENT_GUIDED(PyThreadState *tstate, PyObject *value, char const **guide) {
    char code = **guide;
    *guide += 1;

    switch (code) {
    case 'i':
        Py_INCREF(value);
        return value;
    case 'L':
        return _DEEP_COPY_LIST_GUIDED(tstate, value, guide);
    case 'l':
        return LIST_COPY(tstate, value);
    case 'T':
        return _DEEP_COPY_TUPLE_GUIDED(tstate, value, guide);
    case 't':
        return TUPLE_COPY(tstate, value);
    case 'D':
        return DEEP_COPY_DICT(tstate, value);
    case 'd':
        return DICT_COPY(tstate, value);
    case 'S':
        return DEEP_COPY_SET(tstate, value);
    case 'B':
        return BYTEARRAY_COPY(tstate, value);
    case '?':
        return DEEP_COPY(tstate, value);
    default:
        NUITKA_CANNOT_GET_HERE("Illegal type guide");
        abort();
    }
}

static PyObject *_DEEP_COPY_LIST_GUIDED(PyThreadState *tstate, PyObject *value, char const **guide) {
    assert(PyList_CheckExact(value));

    Py_ssize_t size = PyList_GET_SIZE(value);

    PyObject *result = MAKE_LIST_EMPTY(tstate, size);

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = _DEEP_COPY_ELEMENT_GUIDED(tstate, PyList_GET_ITEM(value, i), guide);

        PyList_SET_ITEM(result, i, item);
    }

    return result;
}

static PyObject *_DEEP_COPY_TUPLE_GUIDED(PyThreadState *tstate, PyObject *value, char const **guide) {
    assert(PyTuple_CheckExact(value));

    Py_ssize_t size = PyTuple_GET_SIZE(value);

    // We cannot have size 0, so this is safe.
    assert(size > 0);
    PyObject *result = MAKE_TUPLE_EMPTY(tstate, size);

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = _DEEP_COPY_ELEMENT_GUIDED(tstate, PyTuple_GET_ITEM(value, i), guide);

        PyTuple_SET_ITEM(result, i, item);
    }

    return result;
}

PyObject *DEEP_COPY_LIST_GUIDED(PyThreadState *tstate, PyObject *value, char const *guide) {
    PyObject *result = _DEEP_COPY_LIST_GUIDED(tstate, value, &guide);
    assert(*guide == 0);
    return result;
}

PyObject *DEEP_COPY_TUPLE_GUIDED(PyThreadState *tstate, PyObject *value, char const *guide) {
    PyObject *result = _DEEP_COPY_TUPLE_GUIDED(tstate, value, &guide);
    assert(*guide == 0);
    return result;
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
