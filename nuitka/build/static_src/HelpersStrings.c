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
/* This helpers is used to quickly create a string object from C char.

   Currently this is used for string subscript code, but may also be used
   for the "char" C type in the future.
*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *STRING_FROM_CHAR(unsigned char c) {
    // TODO: A switch statement might be faster, because no object needs to be
    // created at all, this here is how CPython does it.
    char s[1];
    s[0] = (char)c;

    return Nuitka_String_FromStringAndSize(s, 1);
}

/* The "chr" built-in.

   This could also use a table for the interned single char strings, to be
   faster on Python2. For Python3 no such table is reasonable.
*/

PyObject *BUILTIN_CHR(PyObject *value) {
    long x = PyInt_AsLong(value);

    if (unlikely(x == -1 && ERROR_OCCURRED())) {
#if PYTHON_VERSION < 0x300 && defined(_NUITKA_FULL_COMPAT)
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "an integer is required");
#else
        PyErr_Format(PyExc_TypeError, "an integer is required (got type %s)", Py_TYPE(value)->tp_name);
#endif
        return NULL;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(x < 0 || x >= 256)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "chr() arg not in range(256)");
        return NULL;
    }

    // TODO: A switch statement might be faster, because no object needs to be
    // created at all, this is how CPython does it.
    char s[1];
    s[0] = (char)x;

    return PyString_FromStringAndSize(s, 1);
#else
    PyObject *result = PyUnicode_FromOrdinal(x);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    assert(PyUnicode_Check(result));

    return result;
#endif
}

/* The "ord" built-in.

*/

PyObject *BUILTIN_ORD(PyObject *value) {
    long result;

    if (likely(PyBytes_Check(value))) {
        Py_ssize_t size = PyBytes_GET_SIZE(value);

        if (likely(size == 1)) {
            result = (long)(((unsigned char *)PyBytes_AS_STRING(value))[0]);
        } else {
            PyErr_Format(PyExc_TypeError, "ord() expected a character, but string of length %zd found", size);
            return NULL;
        }
    } else if (PyByteArray_Check(value)) {
        Py_ssize_t size = PyByteArray_GET_SIZE(value);

        if (likely(size == 1)) {
            result = (long)(((unsigned char *)PyByteArray_AS_STRING(value))[0]);
        } else {
            PyErr_Format(PyExc_TypeError,
                         "ord() expected a character, but byte array of length "
                         "%zd found",
                         size);
            return NULL;
        }
    } else if (PyUnicode_Check(value)) {
#if PYTHON_VERSION >= 0x300
        if (unlikely(PyUnicode_READY(value) == -1)) {
            return NULL;
        }

        Py_ssize_t size = PyUnicode_GET_LENGTH(value);
#else
        Py_ssize_t size = PyUnicode_GET_SIZE(value);
#endif

        if (likely(size == 1)) {
#if PYTHON_VERSION >= 0x300
            result = (long)(PyUnicode_READ_CHAR(value, 0));
#else
            result = (long)(*PyUnicode_AS_UNICODE(value));
#endif
        } else {
            PyErr_Format(PyExc_TypeError,
                         "ord() expected a character, but unicode string of "
                         "length %zd found",
                         size);
            return NULL;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "ord() expected string of length 1, but %s found", Py_TYPE(value)->tp_name);
        return NULL;
    }

    return PyInt_FromLong(result);
}

#if PYTHON_VERSION >= 0x300

#define _PyUnicode_UTF8_LENGTH(op) (((PyCompactUnicodeObject *)(op))->utf8_length)
#define PyUnicode_UTF8_LENGTH(op)                                                                                      \
    (assert(_PyUnicode_CHECK(op)), assert(PyUnicode_IS_READY(op)),                                                     \
     PyUnicode_IS_COMPACT_ASCII(op) ? ((PyASCIIObject *)(op))->length : _PyUnicode_UTF8_LENGTH(op))
#define _PyUnicode_WSTR(op) (((PyASCIIObject *)(op))->wstr)
#define _PyUnicode_WSTR_LENGTH(op) (((PyCompactUnicodeObject *)(op))->wstr_length)
#define _PyUnicode_LENGTH(op) (((PyASCIIObject *)(op))->length)
#define _PyUnicode_STATE(op) (((PyASCIIObject *)(op))->state)
#define _PyUnicode_HASH(op) (((PyASCIIObject *)(op))->hash)
#define _PyUnicode_KIND(op) (((PyASCIIObject *)(op))->state.kind)
#define _PyUnicode_DATA_ANY(op) (((PyUnicodeObject *)(op))->data.any)

#undef PyUnicode_READY
#define PyUnicode_READY(op) ((PyUnicode_IS_READY(op) ? 0 : _PyUnicode_Ready(op)))

#define _PyUnicode_SHARE_UTF8(op) (assert(!PyUnicode_IS_COMPACT_ASCII(op)), (_PyUnicode_UTF8(op) == PyUnicode_DATA(op)))
#define _PyUnicode_SHARE_WSTR(op) ((_PyUnicode_WSTR(unicode) == PyUnicode_DATA(op)))

#define _PyUnicode_HAS_UTF8_MEMORY(op)                                                                                 \
    ((!PyUnicode_IS_COMPACT_ASCII(op) && _PyUnicode_UTF8(op) && _PyUnicode_UTF8(op) != PyUnicode_DATA(op)))

#define _PyUnicode_HAS_WSTR_MEMORY(op)                                                                                 \
    ((_PyUnicode_WSTR(op) && (!PyUnicode_IS_READY(op) || _PyUnicode_WSTR(op) != PyUnicode_DATA(op))))

#define _PyUnicode_CONVERT_BYTES(from_type, to_type, begin, end, to)                                                   \
    do {                                                                                                               \
        to_type *_to = (to_type *)(to);                                                                                \
        const from_type *_iter = (from_type *)(begin);                                                                 \
        const from_type *_end = (from_type *)(end);                                                                    \
        Py_ssize_t n = (_end) - (_iter);                                                                               \
        const from_type *_unrolled_end = _iter + _Py_SIZE_ROUND_DOWN(n, 4);                                            \
        while (_iter < (_unrolled_end)) {                                                                              \
            _to[0] = (to_type)_iter[0];                                                                                \
            _to[1] = (to_type)_iter[1];                                                                                \
            _to[2] = (to_type)_iter[2];                                                                                \
            _to[3] = (to_type)_iter[3];                                                                                \
            _iter += 4;                                                                                                \
            _to += 4;                                                                                                  \
        }                                                                                                              \
        while (_iter < (_end))                                                                                         \
            *_to++ = (to_type)*_iter++;                                                                                \
    } while (0)

extern int ucs1lib_find_max_char(const Py_UCS1 *begin, const Py_UCS1 *end);

static void _NuitkaUnicode_FastCopyCharacters(PyObject *to, Py_ssize_t to_start, PyObject *from, Py_ssize_t from_start,
                                              Py_ssize_t how_many) {
    assert(from_start + how_many <= PyUnicode_GET_LENGTH(from));
    assert(to_start + how_many <= PyUnicode_GET_LENGTH(to));

    assert(how_many > 0);

    unsigned int from_kind = PyUnicode_KIND(from);
    void *from_data = PyUnicode_DATA(from);

    unsigned int to_kind = PyUnicode_KIND(to);
    void *to_data = PyUnicode_DATA(to);

    if (from_kind == to_kind) {
        memcpy((char *)to_data + to_kind * to_start, (char *)from_data + from_kind * from_start, to_kind * how_many);
    } else if (from_kind == PyUnicode_1BYTE_KIND && to_kind == PyUnicode_2BYTE_KIND) {
        _PyUnicode_CONVERT_BYTES(Py_UCS1, Py_UCS2, PyUnicode_1BYTE_DATA(from) + from_start,
                                 PyUnicode_1BYTE_DATA(from) + from_start + how_many,
                                 PyUnicode_2BYTE_DATA(to) + to_start);
    } else if (from_kind == PyUnicode_1BYTE_KIND && to_kind == PyUnicode_4BYTE_KIND) {
        _PyUnicode_CONVERT_BYTES(Py_UCS1, Py_UCS4, PyUnicode_1BYTE_DATA(from) + from_start,
                                 PyUnicode_1BYTE_DATA(from) + from_start + how_many,
                                 PyUnicode_4BYTE_DATA(to) + to_start);
    } else if (from_kind == PyUnicode_2BYTE_KIND && to_kind == PyUnicode_4BYTE_KIND) {
        _PyUnicode_CONVERT_BYTES(Py_UCS2, Py_UCS4, PyUnicode_2BYTE_DATA(from) + from_start,
                                 PyUnicode_2BYTE_DATA(from) + from_start + how_many,
                                 PyUnicode_4BYTE_DATA(to) + to_start);
    } else {
        assert(PyUnicode_MAX_CHAR_VALUE(from) > PyUnicode_MAX_CHAR_VALUE(to));

        if (from_kind == PyUnicode_2BYTE_KIND && to_kind == PyUnicode_1BYTE_KIND) {
            _PyUnicode_CONVERT_BYTES(Py_UCS2, Py_UCS1, PyUnicode_2BYTE_DATA(from) + from_start,
                                     PyUnicode_2BYTE_DATA(from) + from_start + how_many,
                                     PyUnicode_1BYTE_DATA(to) + to_start);
        } else if (from_kind == PyUnicode_4BYTE_KIND && to_kind == PyUnicode_1BYTE_KIND) {
            _PyUnicode_CONVERT_BYTES(Py_UCS4, Py_UCS1, PyUnicode_4BYTE_DATA(from) + from_start,
                                     PyUnicode_4BYTE_DATA(from) + from_start + how_many,
                                     PyUnicode_1BYTE_DATA(to) + to_start);
        } else if (from_kind == PyUnicode_4BYTE_KIND && to_kind == PyUnicode_2BYTE_KIND) {
            _PyUnicode_CONVERT_BYTES(Py_UCS4, Py_UCS2, PyUnicode_4BYTE_DATA(from) + from_start,
                                     PyUnicode_4BYTE_DATA(from) + from_start + how_many,
                                     PyUnicode_2BYTE_DATA(to) + to_start);
        } else {
            assert(false);
        }
    }
}

static int _NuitkaUnicode_modifiable(PyObject *unicode) {
    if (Py_REFCNT(unicode) != 1)
        return 0;
    if (_PyUnicode_HASH(unicode) != -1)
        return 0;
    // TODO: That ought to be impossible with refcnf 1.
    if (PyUnicode_CHECK_INTERNED(unicode))
        return 0;
    return 1;
}

static PyObject *_NuitkaUnicode_New(Py_ssize_t length) {
    assert(length != 0);

    if (length > ((PY_SSIZE_T_MAX / (Py_ssize_t)sizeof(Py_UNICODE)) - 1)) {
        return PyErr_NoMemory();
    }

    PyUnicodeObject *unicode = PyObject_New(PyUnicodeObject, &PyUnicode_Type);

    if (unlikely(unicode == NULL)) {
        return NULL;
    }
    Py_ssize_t new_size = sizeof(Py_UNICODE) * ((size_t)length + 1);

    _PyUnicode_WSTR_LENGTH(unicode) = length;
    _PyUnicode_HASH(unicode) = -1;
    _PyUnicode_STATE(unicode).interned = 0;
    _PyUnicode_STATE(unicode).kind = 0;
    _PyUnicode_STATE(unicode).compact = 0;
    _PyUnicode_STATE(unicode).ready = 0;
    _PyUnicode_STATE(unicode).ascii = 0;
    _PyUnicode_DATA_ANY(unicode) = NULL;
    _PyUnicode_LENGTH(unicode) = 0;
    _PyUnicode_UTF8(unicode) = NULL;
    _PyUnicode_UTF8_LENGTH(unicode) = 0;

    _PyUnicode_WSTR(unicode) = (Py_UNICODE *)PyObject_MALLOC(new_size);
    if (!_PyUnicode_WSTR(unicode)) {
        Py_DECREF(unicode);
        PyErr_NoMemory();
        return NULL;
    }

    _PyUnicode_WSTR(unicode)[0] = 0;
    _PyUnicode_WSTR(unicode)[length] = 0;

    return (PyObject *)unicode;
}

static PyObject *_NuitkaUnicode_resize_copy(PyObject *unicode, Py_ssize_t length) {
    if (_PyUnicode_KIND(unicode) != PyUnicode_WCHAR_KIND) {
        PyObject *copy = PyUnicode_New(length, PyUnicode_MAX_CHAR_VALUE(unicode));
        if (unlikely(copy == NULL)) {
            return NULL;
        }

        Py_ssize_t copy_length = Py_MIN(length, PyUnicode_GET_LENGTH(unicode));
        _NuitkaUnicode_FastCopyCharacters(copy, 0, unicode, 0, copy_length);

        return copy;
    } else {
        PyObject *w = _NuitkaUnicode_New(length);
        if (unlikely(w == NULL)) {
            return NULL;
        }
        Py_ssize_t copy_length = _PyUnicode_WSTR_LENGTH(unicode);
        copy_length = Py_MIN(copy_length, length);
        memcpy(_PyUnicode_WSTR(w), _PyUnicode_WSTR(unicode), copy_length * sizeof(wchar_t));
        return w;
    }
}

// We use older form code, make some backward compatible defines available.
#if PYTHON_VERSION >= 0x390

#ifdef Py_REF_DEBUG
#define _Py_DEC_REFTOTAL _Py_RefTotal--;
#else
#define _Py_DEC_REFTOTAL
#endif

#ifdef Py_TRACE_REFS
#define _Py_ForgetReference(unicode) _Py_ForgetReference(unicode)
#else
#define _Py_ForgetReference(unicode)
#endif

#endif

static PyObject *_NuitkaUnicode_resize_compact(PyObject *unicode, Py_ssize_t length) {
    assert(PyUnicode_IS_COMPACT(unicode));

    Py_ssize_t char_size = PyUnicode_KIND(unicode);
    Py_ssize_t struct_size;

    if (PyUnicode_IS_ASCII(unicode)) {
        struct_size = sizeof(PyASCIIObject);
    } else {
        struct_size = sizeof(PyCompactUnicodeObject);
    }

    int share_wstr = _PyUnicode_SHARE_WSTR(unicode);

    if (length > ((PY_SSIZE_T_MAX - struct_size) / char_size - 1)) {
        PyErr_NoMemory();
        return NULL;
    }
    Py_ssize_t new_size = (struct_size + (length + 1) * char_size);

    if (_PyUnicode_HAS_UTF8_MEMORY(unicode)) {
        PyObject_DEL(_PyUnicode_UTF8(unicode));
        _PyUnicode_UTF8(unicode) = NULL;
        _PyUnicode_UTF8_LENGTH(unicode) = 0;
    }
    _Py_DEC_REFTOTAL;
    _Py_ForgetReference(unicode);

    PyObject *new_unicode = (PyObject *)PyObject_REALLOC(unicode, new_size);
    if (unlikely(new_unicode == NULL)) {
        _Py_NewReference(unicode);
        PyErr_NoMemory();
        return NULL;
    }
    unicode = new_unicode;
    _Py_NewReference(unicode);

    _PyUnicode_LENGTH(unicode) = length;
    if (share_wstr) {
        _PyUnicode_WSTR(unicode) = (wchar_t *)PyUnicode_DATA(unicode);
        if (!PyUnicode_IS_ASCII(unicode)) {
            _PyUnicode_WSTR_LENGTH(unicode) = length;
        }
    } else if (_PyUnicode_HAS_WSTR_MEMORY(unicode)) {
        PyObject_DEL(_PyUnicode_WSTR(unicode));
        _PyUnicode_WSTR(unicode) = NULL;
        if (!PyUnicode_IS_ASCII(unicode)) {
            _PyUnicode_WSTR_LENGTH(unicode) = 0;
        }
    }

    PyUnicode_WRITE(PyUnicode_KIND(unicode), PyUnicode_DATA(unicode), length, 0);

    return unicode;
}

static int _NuitkaUnicode_resize_inplace(PyObject *unicode, Py_ssize_t length) {
    assert(!PyUnicode_IS_COMPACT(unicode));
    assert(Py_REFCNT(unicode) == 1);

    if (PyUnicode_IS_READY(unicode)) {
        void *data = _PyUnicode_DATA_ANY(unicode);
        Py_ssize_t char_size = PyUnicode_KIND(unicode);
        int share_wstr = _PyUnicode_SHARE_WSTR(unicode);
        int share_utf8 = _PyUnicode_SHARE_UTF8(unicode);

        if (length > (PY_SSIZE_T_MAX / char_size - 1)) {
            PyErr_NoMemory();
            return -1;
        }
        Py_ssize_t new_size = (length + 1) * char_size;

        if (!share_utf8 && _PyUnicode_HAS_UTF8_MEMORY(unicode)) {
            PyObject_DEL(_PyUnicode_UTF8(unicode));
            _PyUnicode_UTF8(unicode) = NULL;
            _PyUnicode_UTF8_LENGTH(unicode) = 0;
        }

        data = (PyObject *)PyObject_REALLOC(data, new_size);
        if (data == NULL) {
            PyErr_NoMemory();
            return -1;
        }
        _PyUnicode_DATA_ANY(unicode) = data;
        if (share_wstr) {
            _PyUnicode_WSTR(unicode) = (wchar_t *)data;
            _PyUnicode_WSTR_LENGTH(unicode) = length;
        }
        if (share_utf8) {
            _PyUnicode_UTF8(unicode) = (char *)data;
            _PyUnicode_UTF8_LENGTH(unicode) = length;
        }
        _PyUnicode_LENGTH(unicode) = length;
        PyUnicode_WRITE(PyUnicode_KIND(unicode), data, length, 0);

        if (share_wstr || _PyUnicode_WSTR(unicode) == NULL) {
            return 0;
        }
    }
    assert(_PyUnicode_WSTR(unicode) != NULL);

    if (length > PY_SSIZE_T_MAX / (Py_ssize_t)sizeof(wchar_t) - 1) {
        PyErr_NoMemory();
        return -1;
    }
    Py_ssize_t new_size = sizeof(wchar_t) * (length + 1);
    wchar_t *wstr = _PyUnicode_WSTR(unicode);
    wstr = (wchar_t *)PyObject_REALLOC(wstr, new_size);

    if (!wstr) {
        PyErr_NoMemory();
        return -1;
    }
    _PyUnicode_WSTR(unicode) = wstr;
    _PyUnicode_WSTR(unicode)[length] = 0;
    _PyUnicode_WSTR_LENGTH(unicode) = length;

    return 0;
}

static int _NuitkaUnicode_resize(PyObject **p_unicode, Py_ssize_t length) {
    PyObject *unicode = *p_unicode;
    Py_ssize_t old_length;

    if (_PyUnicode_KIND(unicode) == PyUnicode_WCHAR_KIND) {
        old_length = PyUnicode_WSTR_LENGTH(unicode);
    } else {
        old_length = PyUnicode_GET_LENGTH(unicode);
    }

    if (old_length == length) {
        return 0;
    }

    if (length == 0) {
        Py_DECREF(*p_unicode);
        *p_unicode = const_str_empty;
        return 0;
    }

    if (!_NuitkaUnicode_modifiable(unicode)) {
        PyObject *copy = _NuitkaUnicode_resize_copy(unicode, length);
        if (copy == NULL)
            return -1;
        Py_DECREF(*p_unicode);
        *p_unicode = copy;
        return 0;
    }

    if (PyUnicode_IS_COMPACT(unicode)) {
        PyObject *new_unicode = _NuitkaUnicode_resize_compact(unicode, length);
        if (new_unicode == NULL)
            return -1;
        *p_unicode = new_unicode;
        return 0;
    }

    return _NuitkaUnicode_resize_inplace(unicode, length);
}

PyObject *UNICODE_CONCAT(PyObject *left, PyObject *right) {
    if (left == const_str_empty) {
        Py_INCREF(right);
        return right;
    }
    if (right == const_str_empty) {
        Py_INCREF(left);
        return left;
    }

    if (PyUnicode_READY(left) == -1 || PyUnicode_READY(right) == -1) {
        return NULL;
    }

    Py_ssize_t left_len = PyUnicode_GET_LENGTH(left);
    Py_ssize_t right_len = PyUnicode_GET_LENGTH(right);
    if (left_len > PY_SSIZE_T_MAX - right_len) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_OverflowError, "strings are too large to concat");
        return NULL;
    }
    Py_ssize_t new_len = left_len + right_len;

    Py_UCS4 maxchar = PyUnicode_MAX_CHAR_VALUE(left);
    Py_UCS4 maxchar2 = PyUnicode_MAX_CHAR_VALUE(right);
    maxchar = Py_MAX(maxchar, maxchar2);

    PyObject *result = PyUnicode_New(new_len, maxchar);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    _NuitkaUnicode_FastCopyCharacters(result, 0, left, 0, left_len);
    _NuitkaUnicode_FastCopyCharacters(result, left_len, right, 0, right_len);

    return result;
}

bool UNICODE_APPEND(PyObject **p_left, PyObject *right) {
    assert(p_left);

    PyObject *left = *p_left;

    if (left == const_str_empty) {
        Py_DECREF(left);
        Py_INCREF(right);
        *p_left = right;
        return true;
    }

    if (right == const_str_empty)
        return true;

    if (PyUnicode_READY(left) == -1 || PyUnicode_READY(right) == -1) {
        return false;
    }

    Py_ssize_t left_len = PyUnicode_GET_LENGTH(left);
    Py_ssize_t right_len = PyUnicode_GET_LENGTH(right);

    if (left_len > PY_SSIZE_T_MAX - right_len) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_OverflowError, "strings are too large to concat");
        return false;
    }
    Py_ssize_t new_len = left_len + right_len;

    if (_NuitkaUnicode_modifiable(left) && PyUnicode_KIND(right) <= PyUnicode_KIND(left) &&
        !(PyUnicode_IS_ASCII(left) && !PyUnicode_IS_ASCII(right))) {
        if (unlikely(_NuitkaUnicode_resize(p_left, new_len) != 0)) {
            return false;
        }

        _NuitkaUnicode_FastCopyCharacters(*p_left, left_len, right, 0, right_len);
    } else {
        Py_UCS4 maxchar = PyUnicode_MAX_CHAR_VALUE(left);
        Py_UCS4 maxchar2 = PyUnicode_MAX_CHAR_VALUE(right);

        maxchar = Py_MAX(maxchar, maxchar2);

        PyObject *res = PyUnicode_New(new_len, maxchar);
        if (unlikely(res == NULL)) {
            return false;
        }

        _NuitkaUnicode_FastCopyCharacters(res, 0, left, 0, left_len);
        _NuitkaUnicode_FastCopyCharacters(res, left_len, right, 0, right_len);

        Py_DECREF(left);
        *p_left = res;
    }

    return true;
}
#endif

PyObject *UNICODE_JOIN(PyObject *str, PyObject *iterable) {
    CHECK_OBJECT(str);
    CHECK_OBJECT(iterable);
    assert(PyUnicode_CheckExact(str));

    return PyUnicode_Join(str, iterable);
}

PyObject *UNICODE_PARTITION(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    CHECK_OBJECT(sep);
    assert(PyUnicode_CheckExact(str));

    return PyUnicode_Partition(str, sep);
}

PyObject *UNICODE_RPARTITION(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    CHECK_OBJECT(sep);
    assert(PyUnicode_CheckExact(str));

    return PyUnicode_RPartition(str, sep);
}
#if PYTHON_VERSION < 0x300

PyObject *STR_JOIN(PyObject *str, PyObject *iterable) {
    CHECK_OBJECT(str);
    CHECK_OBJECT(iterable);
    assert(PyString_CheckExact(str));

    return _PyString_Join(str, iterable);
}

#endif

PyObject *NuitkaUnicode_FromWideChar(const wchar_t *str, Py_ssize_t size) {
#if PYTHON_VERSION < 0x300
    if (size == -1) {
        size = wcslen(str);
    }
#endif

    return PyUnicode_FromWideChar(str, size);
}