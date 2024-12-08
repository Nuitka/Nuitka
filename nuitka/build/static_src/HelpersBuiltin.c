//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** For calling built-ins, calls it and uses keyword dictionary if necessary.
 *
 * This helper simplifies calling built-ins with optional arguments that can
 * be given as keyword arguments. We basically re-construct the minimal call
 * using keywords here. This obviously is for inefficient calls to the original
 * built-in and should be avoided.
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *CALL_BUILTIN_KW_ARGS(PyThreadState *tstate, PyObject *callable, PyObject **args, char const **arg_names,
                               int max_args, int kw_only_args) {
    int i = 0;

    while (i < max_args - kw_only_args) {
        if (args[i] == NULL) {
            break;
        }

        CHECK_OBJECT(args[i]);

        i++;
    }

    int usable_args = i;

    PyObject *kw_dict = NULL;

    while (i < max_args) {
        if (args[i] != NULL) {
            CHECK_OBJECT(args[i]);

            if (kw_dict == NULL) {
                kw_dict = MAKE_DICT_EMPTY(tstate);
            }

            NUITKA_MAY_BE_UNUSED int res = PyDict_SetItemString(kw_dict, arg_names[i], args[i]);
            assert(res == 0);
        }

        i++;
    }

    PyObject *args_tuple = MAKE_TUPLE_VAR(tstate, args, usable_args);

    PyObject *result = CALL_FUNCTION(tstate, callable, args_tuple, kw_dict);
    Py_XDECREF(kw_dict);
    Py_DECREF(args_tuple);

    return result;
}

/** The "compile" built-in.
 *
 */

NUITKA_DEFINE_BUILTIN(compile)

#if PYTHON_VERSION < 0x300
PyObject *COMPILE_CODE(PyThreadState *tstate, PyObject *source_code, PyObject *file_name, PyObject *mode,
                       PyObject *flags, PyObject *dont_inherit)
#else
PyObject *COMPILE_CODE(PyThreadState *tstate, PyObject *source_code, PyObject *file_name, PyObject *mode,
                       PyObject *flags, PyObject *dont_inherit, PyObject *optimize)
#endif
{
    // May be a source, but also could already be a compiled object, in which
    // case this should just return it.
    if (PyCode_Check(source_code)) {
        Py_INCREF(source_code);
        return source_code;
    }

    PyObject *pos_args = MAKE_TUPLE3(tstate, source_code, file_name, mode);

    PyObject *kw_values[] = {
        flags,
        dont_inherit,
#if PYTHON_VERSION >= 0x300
        optimize,
#endif
    };

    char const *kw_keys[] = {
        "flags",
        "dont_inherit",
#if PYTHON_VERSION >= 0x300
        "optimize",
#endif
    };

    PyObject *kw_args = MAKE_DICT_X_CSTR(kw_keys, kw_values, sizeof(kw_values) / sizeof(PyObject *));

    NUITKA_ASSIGN_BUILTIN(compile);

    PyObject *result = CALL_FUNCTION(tstate, NUITKA_ACCESS_BUILTIN(compile), pos_args, kw_args);

    Py_DECREF(pos_args);
    Py_XDECREF(kw_args);

    return result;
}

/**
 * Helper used to deal with exec statement
 */

#if PYTHON_VERSION < 0x300

bool EXEC_FILE_ARG_HANDLING(PyThreadState *tstate, PyObject **prog, PyObject **name) {
    CHECK_OBJECT(*prog);
    CHECK_OBJECT(*name);

    if (PyFile_Check(*prog)) {
        PyObject *old = *name;
        *name = PyFile_Name(*prog);
        Py_INCREF(*name);
        Py_DECREF(old);

        if (unlikely(*name == NULL)) {
            return false;
        }

        old = *prog;
        *prog = CALL_METHOD_NO_ARGS(tstate, *prog, const_str_plain_read);
        Py_DECREF(old);

        if (unlikely(*prog == NULL)) {
            return false;
        }
    }

    return true;
}
#endif

/**
 *  The "eval" implementation, used for "exec" too.
 */

PyObject *EVAL_CODE(PyThreadState *tstate, PyObject *code, PyObject *globals, PyObject *locals, PyObject *closure) {
    CHECK_OBJECT(code);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);

    if (PyDict_Check(globals) == 0) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "exec: arg 2 must be a dictionary or None");
        return NULL;
    }

    // TODO: Our re-formulation prevents this externally, doesn't it.
    if (locals == Py_None) {
        locals = globals;
    }

    if (PyMapping_Check(locals) == 0) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "exec: arg 3 must be a mapping or None");
        return NULL;
    }

    // Set the "__builtins__" value in globals, it is expected to be present.
    assert(builtin_module != NULL);

    if (PyDict_Check(globals)) {
        const int res = DICT_HAS_ITEM(tstate, globals, const_str_plain___builtins__);

        if (res == 0) {
            if (PyDict_SetItem(globals, const_str_plain___builtins__, (PyObject *)builtin_module) != 0) {
                // Not really allowed to happen, so far this was seen only with
                // C compilers getting the value of "res" wrong.
                assert(false);
                return NULL;
            }
        }
    }

    if (isFakeCodeObject((PyCodeObject *)code)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                        "compiled function code objects do not work with exec/eval");
        return NULL;
    }

#if PYTHON_VERSION < 0x300
    PyObject *result = PyEval_EvalCode((PyCodeObject *)code, globals, locals);
#elif PYTHON_VERSION < 0x3b0
    PyObject *result = PyEval_EvalCode(code, globals, locals);
#else
    PyObject *result = PyEval_EvalCodeEx(code, globals, locals, NULL, 0, NULL, 0, NULL, 0, NULL, closure);
#endif

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

/** The "open" built-in.
 *
 * Different for Python2 and Python3, the later has more arguments and
 * both accept keyword arguments.
 *
 **/

NUITKA_DEFINE_BUILTIN(open);

#if PYTHON_VERSION < 0x300
PyObject *BUILTIN_OPEN(PyThreadState *tstate, PyObject *file_name, PyObject *mode, PyObject *buffering) {
    NUITKA_ASSIGN_BUILTIN(open);

    PyObject *result;

    if (TRACE_FILE_OPEN(tstate, file_name, mode, buffering, &result)) {
        return result;
    }

    PyObject *args[] = {file_name, mode, buffering};

    char const *arg_names[] = {"name", "mode", "buffering"};

    return CALL_BUILTIN_KW_ARGS(tstate, NUITKA_ACCESS_BUILTIN(open), args, arg_names, 3, 0);
}
#else
PyObject *BUILTIN_OPEN(PyThreadState *tstate, PyObject *file_name, PyObject *mode, PyObject *buffering,
                       PyObject *encoding, PyObject *errors, PyObject *newline, PyObject *closefd, PyObject *opener) {
    NUITKA_ASSIGN_BUILTIN(open);

    PyObject *result;

    if (TRACE_FILE_OPEN(tstate, file_name, mode, buffering, encoding, errors, newline, closefd, opener, &result)) {
        return result;
    }

    PyObject *args[] = {file_name, mode, buffering, encoding, errors, newline, closefd, opener};

    char const *arg_names[] = {"file", "mode", "buffering", "encoding", "errors", "newline", "closefd", "opener"};

    return CALL_BUILTIN_KW_ARGS(tstate, NUITKA_ACCESS_BUILTIN(open), args, arg_names, 8, 0);
}

#endif

NUITKA_DEFINE_BUILTIN(input);

PyObject *BUILTIN_INPUT(PyThreadState *tstate, PyObject *prompt) {
    NUITKA_ASSIGN_BUILTIN(input);

#if NUITKA_STDERR_NOT_VISIBLE && (PYTHON_VERSION >= 0x300 || !defined(_WIN32))
    if (prompt != NULL) {
        PRINT_ITEM(prompt);
        prompt = NULL;
    }
#endif

    if (prompt == NULL) {
        return CALL_FUNCTION_NO_ARGS(tstate, NUITKA_ACCESS_BUILTIN(input));
    } else {
        return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, NUITKA_ACCESS_BUILTIN(input), prompt);
    }
}

/** The "staticmethod" built-in.
 *
 **/

NUITKA_DEFINE_BUILTIN(staticmethod)

PyObject *BUILTIN_STATICMETHOD(PyThreadState *tstate, PyObject *value) {
    NUITKA_ASSIGN_BUILTIN(staticmethod);

    return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, NUITKA_ACCESS_BUILTIN(staticmethod), value);
}

/** The "classmethod" built-in.
 *
 **/

NUITKA_DEFINE_BUILTIN(classmethod)

PyObject *BUILTIN_CLASSMETHOD(PyThreadState *tstate, PyObject *value) {
    NUITKA_ASSIGN_BUILTIN(classmethod);

    return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, NUITKA_ACCESS_BUILTIN(classmethod), value);
}

#if PYTHON_VERSION >= 0x300

/** The "bytes" built-in.
 *
 * Only for Python3. There is not BYTES_BUILTIN1 yet, this only delegates to
 * the actual built-in which is wasteful. TODO: Have dedicated implementation
 * for this.
 *
 **/

NUITKA_DEFINE_BUILTIN(bytes);

PyObject *BUILTIN_BYTES1(PyThreadState *tstate, PyObject *value) {
    NUITKA_ASSIGN_BUILTIN(bytes);

    return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, NUITKA_ACCESS_BUILTIN(bytes), value);
}

PyObject *BUILTIN_BYTES3(PyThreadState *tstate, PyObject *value, PyObject *encoding, PyObject *errors) {
    NUITKA_ASSIGN_BUILTIN(bytes);

    PyObject *args[] = {value, encoding, errors};

    char const *arg_names[] = {"value", "encoding", "errors"};

    return CALL_BUILTIN_KW_ARGS(tstate, NUITKA_ACCESS_BUILTIN(bytes), args, arg_names, 3, 0);
}
#endif

/** The "bin" built-in.
 *
 **/

PyObject *BUILTIN_BIN(PyObject *value) {
    // Note: I don't really know why "oct" and "hex" don't use this as well.
    PyObject *result = PyNumber_ToBase(value, 2);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

/** The "oct" built-in.
 *
 **/

PyObject *BUILTIN_OCT(PyThreadState *tstate, PyObject *value) {
#if PYTHON_VERSION >= 0x300
    PyObject *result = PyNumber_ToBase(value, 8);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
#else
    if (unlikely(value == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "oct() argument can't be converted to oct");
        return NULL;
    }

    PyNumberMethods *nb = Py_TYPE(value)->tp_as_number;

    if (unlikely(nb == NULL || nb->nb_oct == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "oct() argument can't be converted to oct");
        return NULL;
    }

    PyObject *result = (*nb->nb_oct)(value);

    if (result) {
        if (unlikely(!PyString_Check(result))) {
            PyErr_Format(PyExc_TypeError, "__oct__ returned non-string (type %s)", Py_TYPE(result)->tp_name);

            Py_DECREF(result);
            return NULL;
        }
    }

    return result;
#endif
}

/** The "hex" built-in.
 *
 **/

PyObject *BUILTIN_HEX(PyThreadState *tstate, PyObject *value) {
#if PYTHON_VERSION >= 0x300
    PyObject *result = PyNumber_ToBase(value, 16);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
#else
    if (unlikely(value == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "hex() argument can't be converted to hex");
        return NULL;
    }

    PyNumberMethods *nb = Py_TYPE(value)->tp_as_number;

    if (unlikely(nb == NULL || nb->nb_hex == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "hex() argument can't be converted to hex");
        return NULL;
    }

    PyObject *result = (*nb->nb_hex)(value);

    if (likely(result)) {
        if (unlikely(!PyString_Check(result))) {
            PyErr_Format(PyExc_TypeError, "__hex__ returned non-string (type %s)", Py_TYPE(result)->tp_name);

            Py_DECREF(result);
            return NULL;
        }
    }

    return result;
#endif
}

/** The "hash" built-in.
 *
 **/

static void SET_HASH_NOT_IMPLEMENTED_ERROR(PyThreadState *tstate, PyObject *value) {
    // TODO: Use our own formatting code.
    // spell-checker: ignore unhashable

    PyErr_Format(PyExc_TypeError, "unhashable type: '%s'", Py_TYPE(value)->tp_name);
}

#if PYTHON_VERSION < 0x300
// Helper to make hash from pointer value, compatible with CPython.
static long Nuitka_HashFromPointer(void *p) {
    size_t y = (size_t)p;
    y = (y >> 4) | (y << (8 * SIZEOF_VOID_P - 4));
    long x = (long)y;
    if (unlikely(x == -1)) {
        x = -2;
    }
    return x;
}
#endif

PyObject *BUILTIN_HASH(PyThreadState *tstate, PyObject *value) {
    PyTypeObject *type = Py_TYPE(value);

    if (likely(type->tp_hash != NULL)) {
        Py_hash_t hash = (*type->tp_hash)(value);

        if (unlikely(hash == -1)) {
            return NULL;
        }

#if PYTHON_VERSION < 0x300
        return Nuitka_PyInt_FromLong(hash);
#else
        // TODO: Have a dedicated helper of ours for this as well.
        return PyLong_FromSsize_t(hash);
#endif
    }

#if PYTHON_VERSION < 0x300
    if (likely(type->tp_compare == NULL && TP_RICHCOMPARE(type) == NULL)) {
        Py_hash_t hash = Nuitka_HashFromPointer(value);
        return Nuitka_PyInt_FromLong(hash);
    }
#endif

    SET_HASH_NOT_IMPLEMENTED_ERROR(tstate, value);
    return NULL;
}

Py_hash_t HASH_VALUE_WITH_ERROR(PyThreadState *tstate, PyObject *value) {
    PyTypeObject *type = Py_TYPE(value);

    if (likely(type->tp_hash != NULL)) {
        Py_hash_t hash = (*type->tp_hash)(value);
        return hash;
    }

#if PYTHON_VERSION < 0x300
    if (likely(type->tp_compare == NULL && TP_RICHCOMPARE(type) == NULL)) {
        return Nuitka_HashFromPointer(value);
    }
#endif

    SET_HASH_NOT_IMPLEMENTED_ERROR(tstate, value);
    return -1;
}

Py_hash_t HASH_VALUE_WITHOUT_ERROR(PyThreadState *tstate, PyObject *value) {
    PyTypeObject *type = Py_TYPE(value);

    if (likely(type->tp_hash != NULL)) {
        Py_hash_t hash = (*type->tp_hash)(value);

        if (unlikely(hash == -1)) {
            CLEAR_ERROR_OCCURRED(tstate);
        }

        return hash;
    }

#if PYTHON_VERSION < 0x300
    if (likely(type->tp_compare == NULL && TP_RICHCOMPARE(type) == NULL)) {
        return Nuitka_HashFromPointer(value);
    }
#endif

    return -1;
}

/** The "bytearray" built-in.
 *
 * These should be more in-lined maybe, as a lot of checks are not necessary
 * and the error checking for the 3 arguments variant may even not be enough,
 * as it could be keyword arguments.
 *
 **/

PyObject *BUILTIN_BYTEARRAY1(PyObject *value) {
    PyObject *result = PyByteArray_FromObject(value);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

NUITKA_DEFINE_BUILTIN(bytearray)

PyObject *BUILTIN_BYTEARRAY3(PyThreadState *tstate, PyObject *string, PyObject *encoding, PyObject *errors) {
    CHECK_OBJECT(string);
    CHECK_OBJECT(encoding);

    NUITKA_ASSIGN_BUILTIN(bytearray);

    if (errors == NULL) {
        PyObject *args[] = {string, encoding};

        PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, NUITKA_ACCESS_BUILTIN(bytearray), args);

        return result;
    } else {
        PyObject *args[] = {string, encoding, errors};

        PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, NUITKA_ACCESS_BUILTIN(bytearray), args);

        return result;
    }
}

/** The "iter" built-in.
 *
 * This comes in two flavors, with one or two arguments. The second one
 * creates a "calliterobject" that is private to CPython. We define it here
 * for ourselves. The one argument version is in headers for in-lining of
 * the code. spell-checker: ignore calliterobject
 *
 **/

// From CPython:
typedef struct {
    /* Python object folklore: */
    PyObject_HEAD

        PyObject *it_callable;
    PyObject *it_sentinel;
} calliterobject;

PyObject *BUILTIN_ITER2(PyObject *callable, PyObject *sentinel) {
    calliterobject *result = (calliterobject *)Nuitka_GC_New(&PyCallIter_Type);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    // Note: References were taken at call site already.
    result->it_callable = callable;
    Py_INCREF(callable);
    result->it_sentinel = sentinel;
    Py_INCREF(sentinel);

    Nuitka_GC_Track(result);

    return (PyObject *)result;
}

/** The "type" built-in.
 *
 * This comes in two flavors, one being the detection of a values type,
 * and 3 argument variant creates a new type.
 *
 **/

PyObject *BUILTIN_TYPE1(PyObject *arg) {
    CHECK_OBJECT(arg);

    PyObject *result = (PyObject *)Py_TYPE(arg);
    CHECK_OBJECT(result);

    Py_INCREF(result);
    return result;
}

PyObject *BUILTIN_TYPE3(PyThreadState *tstate, PyObject *module_name, PyObject *name, PyObject *bases, PyObject *dict) {
    PyObject *pos_args = MAKE_TUPLE3(tstate, name, bases, dict);

    PyObject *result = PyType_Type.tp_new(&PyType_Type, pos_args, NULL);

    if (unlikely(result == NULL)) {
        Py_DECREF(pos_args);
        return NULL;
    }

    PyTypeObject *type = Py_TYPE(result);

    if (likely(Nuitka_Type_IsSubtype(type, &PyType_Type))) {
        if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
            int res = type->tp_init(result, pos_args, NULL);

            if (unlikely(res < 0)) {
                Py_DECREF(pos_args);
                Py_DECREF(result);
                return NULL;
            }
        }
    }

    Py_DECREF(pos_args);

    if (HAS_ATTR_BOOL(tstate, result, const_str_plain___module__) == false) {
        bool b_res = SET_ATTRIBUTE(tstate, result, const_str_plain___module__, module_name);

        if (b_res == false) {
            Py_DECREF(result);
            return NULL;
        }
    }

    return result;
}

/** The "super" built-in.
 *
 *
 **/

NUITKA_DEFINE_BUILTIN(super);

PyObject *BUILTIN_SUPER2(PyThreadState *tstate, PyDictObject *module_dict, PyObject *type, PyObject *object) {
    CHECK_OBJECT(type);
    CHECK_OBJECT_X(object);

    PyObject *super_value = GET_STRING_DICT_VALUE(module_dict, (Nuitka_StringObject *)const_str_plain_super);

    if (super_value == NULL) {
        NUITKA_ASSIGN_BUILTIN(super);

        super_value = NUITKA_ACCESS_BUILTIN(super);
    }

    if (object != NULL) {
        PyObject *args[] = {type, object};

        return CALL_FUNCTION_WITH_ARGS2(tstate, super_value, args);
    } else {
        return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, super_value, type);
    }
}

PyObject *BUILTIN_SUPER0(PyThreadState *tstate, PyDictObject *module_dict, PyObject *type, PyObject *object) {
    if (object == Py_None) {
        object = NULL;
    }

    return BUILTIN_SUPER2(tstate, module_dict, type, object);
}

/** The "callable" built-in.
 *
 **/

PyObject *BUILTIN_CALLABLE(PyObject *value) {
    int res = PyCallable_Check(value);
    PyObject *result = BOOL_FROM(res != 0);
    Py_INCREF_IMMORTAL(result);
    return result;
}

/* The "getattr" built-in with default value.
 *
 * We might want to split it off for a variant without default value.
 *
 **/

PyObject *BUILTIN_GETATTR(PyThreadState *tstate, PyObject *object, PyObject *attribute, PyObject *default_value) {
    CHECK_OBJECT(object);
    CHECK_OBJECT(attribute);
    CHECK_OBJECT_X(default_value);

#if PYTHON_VERSION < 0x300
    if (PyUnicode_Check(attribute)) {
        attribute = _PyUnicode_AsDefaultEncodedString(attribute, NULL);

        if (unlikely(attribute == NULL)) {
            return NULL;
        }
    }

    if (unlikely(!PyString_Check(attribute))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "getattr(): attribute name must be string");
        return NULL;
    }
#else
    if (!PyUnicode_Check(attribute)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "getattr(): attribute name must be string");
        return NULL;
    }
#endif

    PyObject *result = PyObject_GetAttr(object, attribute);

    if (result == NULL) {
        if (default_value != NULL) {
            if (HAS_ERROR_OCCURRED(tstate)) {
                if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, GET_ERROR_OCCURRED(tstate), PyExc_AttributeError)) {
                    CLEAR_ERROR_OCCURRED(tstate);
                }
            }

            Py_INCREF(default_value);
            return default_value;
        } else {
            assert(HAS_ERROR_OCCURRED(tstate));

            return NULL;
        }
    } else {
        return result;
    }
}

/** The "setattr" built-in.
 *
 **/

PyObject *BUILTIN_SETATTR(PyObject *object, PyObject *attribute, PyObject *value) {
    int res = PyObject_SetAttr(object, attribute, value);

    if (unlikely(res < 0)) {
        return NULL;
    }

    // No reference returned.
    return Py_None;
}

PyObject *BUILTIN_INT2(PyThreadState *tstate, PyObject *value, PyObject *base) {
#if PYTHON_VERSION < 0x300
    long base_int = PyInt_AsLong(base);
#else
    Py_ssize_t base_int = PyNumber_AsSsize_t(base, NULL);
#endif

    if (unlikely(base_int == -1)) {
        PyObject *error = GET_ERROR_OCCURRED(tstate);

        if (likely(error != NULL)) {
            assert(HAS_ERROR_OCCURRED(tstate));

#if PYTHON_VERSION >= 0x300
            if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_OverflowError)) {
                PyErr_Format(PyExc_ValueError,
#if PYTHON_VERSION < 0x324
                             "int() arg 2 must be >= 2 and <= 36"
#elif PYTHON_VERSION < 0x364
                             "int() base must be >= 2 and <= 36"
#else
                             "int() base must be >= 2 and <= 36, or 0"
#endif
                );
            }
#endif
            return NULL;
        }
    }

#if PYTHON_VERSION >= 0x300
    if (unlikely((base_int != 0 && base_int < 2) || base_int > 36)) {
        PyErr_Format(PyExc_ValueError,
#if PYTHON_VERSION < 0x324
                     "int() arg 2 must be >= 2 and <= 36"
#elif PYTHON_VERSION < 0x364
                     "int() base must be >= 2 and <= 36"
#else
                     "int() base must be >= 2 and <= 36, or 0"
#endif
        );

        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x300
    if (unlikely(!Nuitka_String_Check(value) && !PyUnicode_Check(value))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "int() can't convert non-string with explicit base");
        return NULL;
    }

    char *value_str = Nuitka_String_AsString(value);
    if (unlikely(value_str == NULL)) {
        return NULL;
    }

    PyObject *result = PyInt_FromString(value_str, NULL, base_int);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
#else
    if (PyUnicode_Check(value)) {
        return PyLong_FromUnicodeObject(value, (int)base_int);
    } else if (PyBytes_Check(value) || PyByteArray_Check(value)) {
        // Check for "NUL" as PyLong_FromString has no length parameter,
        Py_ssize_t size = Py_SIZE(value);
        char const *value_str;

        if (PyByteArray_Check(value)) {
            value_str = PyByteArray_AS_STRING(value);
        } else {
            value_str = PyBytes_AS_STRING(value);
        }

        PyObject *result = NULL;

        if (size != 0 && strlen(value_str) == (size_t)size) {
            result = PyLong_FromString((char *)value_str, NULL, (int)base_int);
        }

        if (unlikely(result == NULL)) {
            PyErr_Format(PyExc_ValueError, "invalid literal for int() with base %d: %R", base_int, value);

            return NULL;
        }

        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "int() can't convert non-string with explicit base");
        return NULL;
    }
#endif
}

#if PYTHON_VERSION < 0x300
// Note: Python3 uses TO_INT2 function.
PyObject *BUILTIN_LONG2(PyThreadState *tstate, PyObject *value, PyObject *base) {
    long base_int = PyInt_AsLong(base);

    if (unlikely(base_int == -1)) {
        if (likely(HAS_ERROR_OCCURRED(tstate))) {
            return NULL;
        }
    }

    if (unlikely(!Nuitka_String_Check(value) && !PyUnicode_Check(value))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "long() can't convert non-string with explicit base");
        return NULL;
    }

    char *value_str = Nuitka_String_AsString(value);
    if (unlikely(value_str == NULL)) {
        return NULL;
    }

    PyObject *result = PyLong_FromString(value_str, NULL, base_int);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}
#endif

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
