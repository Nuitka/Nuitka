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

static PyObject *CALL_BUILTIN_KW_ARGS(PyObject *callable, PyObject **args, char const **arg_names, int max_args) {
    int i = 0;

    while (i < max_args) {
        if (args[i] == NULL)
            break;

        CHECK_OBJECT(args[i]);

        i++;
    }

    int usable_args = i;

    PyObject *kw_dict = NULL;

    while (i < max_args) {
        if (args[i] != NULL) {
            CHECK_OBJECT(args[i]);

            if (kw_dict == NULL) {
                kw_dict = PyDict_New();
            }

            int res = PyDict_SetItemString(kw_dict, arg_names[i], args[i]);
            assert(res == 0);
        }

        i++;
    }

    PyObject *args_tuple = PyTuple_New(usable_args);
    for (i = 0; i < usable_args; i++) {
        PyTuple_SET_ITEM(args_tuple, i, args[i]);

        Py_INCREF(args[i]);
    }

    PyObject *result = CALL_FUNCTION(callable, args_tuple, kw_dict);
    Py_XDECREF(kw_dict);
    Py_DECREF(args_tuple);

    return result;
}

/** The "compile" built-in.
 *
 */

NUITKA_DEFINE_BUILTIN(compile)

#if PYTHON_VERSION < 0x300
PyObject *COMPILE_CODE(PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags,
                       PyObject *dont_inherit)
#else
PyObject *COMPILE_CODE(PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags,
                       PyObject *dont_inherit, PyObject *optimize)
#endif
{
    // May be a source, but also could already be a compiled object, in which
    // case this should just return it.
    if (PyCode_Check(source_code)) {
        Py_INCREF(source_code);
        return source_code;
    }

    PyObject *pos_args = PyTuple_New(3);
    PyTuple_SET_ITEM(pos_args, 0, source_code);
    Py_INCREF(source_code);
    PyTuple_SET_ITEM(pos_args, 1, file_name);
    Py_INCREF(file_name);
    PyTuple_SET_ITEM(pos_args, 2, mode);
    Py_INCREF(mode);

    PyObject *kw_args = NULL;

    if (flags != NULL) {
        if (kw_args == NULL)
            kw_args = PyDict_New();
        PyDict_SetItemString(kw_args, "flags", flags);
    }

    if (dont_inherit != NULL) {
        if (kw_args == NULL)
            kw_args = PyDict_New();
        PyDict_SetItemString(kw_args, "dont_inherit", dont_inherit);
    }

#if PYTHON_VERSION >= 0x300
    if (optimize != NULL) {
        if (kw_args == NULL)
            kw_args = PyDict_New();
        PyDict_SetItemString(kw_args, "optimize", optimize);
    }
#endif

    NUITKA_ASSIGN_BUILTIN(compile);

    PyObject *result = CALL_FUNCTION(NUITKA_ACCESS_BUILTIN(compile), pos_args, kw_args);

    Py_DECREF(pos_args);
    Py_XDECREF(kw_args);

    return result;
}

/**
 * Helper used to deal with exec statement
 */

#if PYTHON_VERSION < 0x300

bool EXEC_FILE_ARG_HANDLING(PyObject **prog, PyObject **name) {
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
        *prog = CALL_METHOD_NO_ARGS(*prog, const_str_plain_read);
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

PyObject *EVAL_CODE(PyObject *code, PyObject *globals, PyObject *locals) {
    CHECK_OBJECT(code);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);

    if (PyDict_Check(globals) == 0) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "exec: arg 2 must be a dictionary or None");
        return NULL;
    }

    // TODO: Our re-formulation prevents this externally, doesn't it.
    if (locals == Py_None) {
        locals = globals;
    }

    if (PyMapping_Check(locals) == 0) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "exec: arg 3 must be a mapping or None");
        return NULL;
    }

    // Set the __builtins__ in globals, it is expected to be present.
    if (PyDict_Check(globals) && DICT_HAS_ITEM(globals, const_str_plain___builtins__) == 0) {
        if (PyDict_SetItem(globals, const_str_plain___builtins__, (PyObject *)builtin_module) != 0) {
            return NULL;
        }
    }

#if PYTHON_VERSION < 0x300
    PyObject *result = PyEval_EvalCode((PyCodeObject *)code, globals, locals);
#else
    PyObject *result = PyEval_EvalCode(code, globals, locals);
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
PyObject *BUILTIN_OPEN(PyObject *file_name, PyObject *mode, PyObject *buffering) {
    NUITKA_ASSIGN_BUILTIN(open);

    PyObject *args[] = {file_name, mode, buffering};

    char const *arg_names[] = {"name", "mode", "buffering"};

    return CALL_BUILTIN_KW_ARGS(NUITKA_ACCESS_BUILTIN(open), args, arg_names, 3);
}
#else
PyObject *BUILTIN_OPEN(PyObject *file_name, PyObject *mode, PyObject *buffering, PyObject *encoding, PyObject *errors,
                       PyObject *newline, PyObject *closefd, PyObject *opener) {
    NUITKA_ASSIGN_BUILTIN(open);

    PyObject *args[] = {file_name, mode, buffering, encoding, errors, newline, closefd, opener};

    char const *arg_names[] = {"file", "mode", "buffering", "encoding", "errors", "newline", "closefd", "opener"};

    return CALL_BUILTIN_KW_ARGS(NUITKA_ACCESS_BUILTIN(open), args, arg_names, 8);
}

#endif

/** The "staticmethod" built-in.
 *
 **/

NUITKA_DEFINE_BUILTIN(staticmethod)

PyObject *BUILTIN_STATICMETHOD(PyObject *value) {
    NUITKA_ASSIGN_BUILTIN(staticmethod);

    return CALL_FUNCTION_WITH_SINGLE_ARG(NUITKA_ACCESS_BUILTIN(staticmethod), value);
}

/** The "classmethod" built-in.
 *
 **/

NUITKA_DEFINE_BUILTIN(classmethod)

PyObject *BUILTIN_CLASSMETHOD(PyObject *value) {
    NUITKA_ASSIGN_BUILTIN(classmethod);

    return CALL_FUNCTION_WITH_SINGLE_ARG(NUITKA_ACCESS_BUILTIN(classmethod), value);
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

PyObject *BUILTIN_BYTES1(PyObject *value) {
    NUITKA_ASSIGN_BUILTIN(bytes);

    return CALL_FUNCTION_WITH_SINGLE_ARG(NUITKA_ACCESS_BUILTIN(bytes), value);
}

PyObject *BUILTIN_BYTES3(PyObject *value, PyObject *encoding, PyObject *errors) {
    NUITKA_ASSIGN_BUILTIN(bytes);

    PyObject *args[] = {value, encoding, errors};

    char const *arg_names[] = {"value", "encoding", "errors"};

    return CALL_BUILTIN_KW_ARGS(NUITKA_ACCESS_BUILTIN(bytes), args, arg_names, 3);
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

PyObject *BUILTIN_OCT(PyObject *value) {
#if PYTHON_VERSION >= 0x300
    PyObject *result = PyNumber_ToBase(value, 8);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
#else
    if (unlikely(value == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "oct() argument can't be converted to oct");
        return NULL;
    }

    PyNumberMethods *nb = Py_TYPE(value)->tp_as_number;

    if (unlikely(nb == NULL || nb->nb_oct == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "oct() argument can't be converted to oct");
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

PyObject *BUILTIN_HEX(PyObject *value) {
#if PYTHON_VERSION >= 0x300
    PyObject *result = PyNumber_ToBase(value, 16);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
#else
    if (unlikely(value == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "hex() argument can't be converted to hex");
        return NULL;
    }

    PyNumberMethods *nb = Py_TYPE(value)->tp_as_number;

    if (unlikely(nb == NULL || nb->nb_hex == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "hex() argument can't be converted to hex");
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

static void SET_HASH_NOT_IMPLEMENTED_ERROR(PyObject *value) {
    // TODO: Use our own formatting code.

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

PyObject *BUILTIN_HASH(PyObject *value) {
    PyTypeObject *type = Py_TYPE(value);

    if (likely(type->tp_hash != NULL)) {
        Py_hash_t hash = (*type->tp_hash)(value);

        if (unlikely(hash == -1)) {
            return NULL;
        }

#if PYTHON_VERSION < 0x300
        return PyInt_FromLong(hash);
#else
        return PyLong_FromSsize_t(hash);
#endif
    }

#if PYTHON_VERSION < 0x300
    if (likely(type->tp_compare == NULL && RICHCOMPARE(type) == NULL)) {
        Py_hash_t hash = Nuitka_HashFromPointer(value);
        return PyInt_FromLong(hash);
    }
#endif

    SET_HASH_NOT_IMPLEMENTED_ERROR(value);
    return NULL;
}

Py_hash_t HASH_VALUE_WITH_ERROR(PyObject *value) {
    PyTypeObject *type = Py_TYPE(value);

    if (likely(type->tp_hash != NULL)) {
        Py_hash_t hash = (*type->tp_hash)(value);
        return hash;
    }

#if PYTHON_VERSION < 0x300
    if (likely(type->tp_compare == NULL && RICHCOMPARE(type) == NULL)) {
        return Nuitka_HashFromPointer(value);
    }
#endif

    SET_HASH_NOT_IMPLEMENTED_ERROR(value);
    return -1;
}

Py_hash_t HASH_VALUE_WITHOUT_ERROR(PyObject *value) {
    PyTypeObject *type = Py_TYPE(value);

    if (likely(type->tp_hash != NULL)) {
        Py_hash_t hash = (*type->tp_hash)(value);

        if (unlikely(hash == -1)) {
            CLEAR_ERROR_OCCURRED();
        }

        return hash;
    }

#if PYTHON_VERSION < 0x300
    if (likely(type->tp_compare == NULL && RICHCOMPARE(type) == NULL)) {
        return Nuitka_HashFromPointer(value);
    }
#endif

    CLEAR_ERROR_OCCURRED();
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

PyObject *BUILTIN_BYTEARRAY3(PyObject *string, PyObject *encoding, PyObject *errors) {
    CHECK_OBJECT(string);
    CHECK_OBJECT(encoding);

    NUITKA_ASSIGN_BUILTIN(bytearray);

    if (errors == NULL) {
        PyObject *args[] = {string, encoding};

        PyObject *result = CALL_FUNCTION_WITH_ARGS2(NUITKA_ACCESS_BUILTIN(bytearray), args);

        return result;
    } else {
        PyObject *args[] = {string, encoding, errors};

        PyObject *result = CALL_FUNCTION_WITH_ARGS3(NUITKA_ACCESS_BUILTIN(bytearray), args);

        return result;
    }
}

/** The "iter" built-in.
 *
 * This comes in two flavors, with one or two arguments. The second one
 * creates a "calliterobject" that is private to CPython. We define it here
 * for ourselves. The one argument version is in headers for in-lining of
 * the code.
 *
 **/

// From CPython:
typedef struct {
    /* Python object folklore: */
    PyObject_HEAD;

    PyObject *it_callable;
    PyObject *it_sentinel;
} calliterobject;

PyObject *BUILTIN_ITER2(PyObject *callable, PyObject *sentinel) {
    calliterobject *result = PyObject_GC_New(calliterobject, &PyCallIter_Type);

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
    PyObject *result = (PyObject *)Py_TYPE(arg);

    Py_INCREF(result);
    return result;
}

PyObject *BUILTIN_TYPE3(PyObject *module_name, PyObject *name, PyObject *bases, PyObject *dict) {
    PyObject *pos_args = PyTuple_New(3);
    PyTuple_SET_ITEM(pos_args, 0, name);
    Py_INCREF(name);
    PyTuple_SET_ITEM(pos_args, 1, bases);
    Py_INCREF(bases);
    PyTuple_SET_ITEM(pos_args, 2, dict);
    Py_INCREF(dict);

    PyObject *result = PyType_Type.tp_new(&PyType_Type, pos_args, NULL);

    if (unlikely(result == NULL)) {
        Py_DECREF(pos_args);
        return NULL;
    }

    PyTypeObject *type = Py_TYPE(result);

    if (likely(PyType_IsSubtype(type, &PyType_Type))) {
        if (
#if PYTHON_VERSION < 0x300
            PyType_HasFeature(type, Py_TPFLAGS_HAVE_CLASS) &&
#endif
            type->tp_init != NULL) {
            int res = type->tp_init(result, pos_args, NULL);

            if (unlikely(res < 0)) {
                Py_DECREF(pos_args);
                Py_DECREF(result);
                return NULL;
            }
        }
    }

    Py_DECREF(pos_args);

    int res = PyObject_SetAttr(result, const_str_plain___module__, module_name);

    if (res < 0) {
        return NULL;
    }

    return result;
}

/** The "super" built-in.
 *
 * This uses a private structure "superobject" that we declare here too.
 *
 **/

typedef struct {
    /* Python object folklore: */
    PyObject_HEAD;

    PyTypeObject *type;
    PyObject *obj;
    PyTypeObject *obj_type;
} superobject;

PyObject *BUILTIN_SUPER2(PyObject *type, PyObject *object) {
    CHECK_OBJECT(type);
    CHECK_OBJECT_X(object);

    if (unlikely(PyType_Check(type) == false)) {
#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_NICE("super() argument 1 must be type, not %s", type);
#elif PYTHON_VERSION < 0x352
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_NICE("must be type, not %s", type);
#else
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_NICE("super() argument 1 must be type, not %s", type);
#endif
        return NULL;
    }

    if (object == Py_None) {
        object = NULL;
    }

    PyTypeObject *obj_type = NULL;

#if 0
    PRINT_STRING("SUPER:");
    PRINT_ITEM(type);
    PRINT_ITEM(object);
    PRINT_NEW_LINE();
#endif

    if (object != NULL) {

        if (PyType_Check(object) && PyType_IsSubtype((PyTypeObject *)object, (PyTypeObject *)type)) {
            obj_type = (PyTypeObject *)object;
        } else if (object != NULL && PyType_IsSubtype(Py_TYPE(object), (PyTypeObject *)type)) {
            obj_type = Py_TYPE(object);
        } else {
            PyObject *class_attr = PyObject_GetAttr(object, const_str_plain___class__);

            if (likely(class_attr != NULL && PyType_Check(class_attr) &&
                       (PyTypeObject *)class_attr != Py_TYPE(object) &&
                       PyType_IsSubtype((PyTypeObject *)class_attr, (PyTypeObject *)type))) {

                obj_type = (PyTypeObject *)class_attr;
                Py_DECREF(class_attr);
            } else {
                Py_XDECREF(class_attr);

                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError,
                                                "super(type, obj): obj must be an instance or subtype of type");

                return NULL;
            }
        }
    }

    superobject *result = PyObject_GC_New(superobject, &PySuper_Type);
    assert(result);

    result->type = (PyTypeObject *)type;
    Py_INCREF(type);
    result->obj = object;
    Py_XINCREF(object);

    result->obj_type = obj_type;
    Py_XINCREF(obj_type);

    Nuitka_GC_Track(result);

    CHECK_OBJECT(result);
    assert(Py_TYPE(result) == &PySuper_Type);

    return (PyObject *)result;
}

PyObject *BUILTIN_SUPER0(PyObject *type, PyObject *object) {
    CHECK_OBJECT(type);

    superobject *result = PyObject_GC_New(superobject, &PySuper_Type);
    assert(result);

    if (object == Py_None) {
        object = NULL;
    }

    if (unlikely(PyType_Check(type) == false)) {
        PyErr_Format(PyExc_RuntimeError, "super(): __class__ is not a type (%s)", Py_TYPE(type)->tp_name);

        return NULL;
    }

    result->type = (PyTypeObject *)type;
    Py_INCREF(type);
    if (object) {
        result->obj = object;
        Py_INCREF(object);

        if (PyType_Check(object) && PyType_IsSubtype((PyTypeObject *)object, (PyTypeObject *)type)) {
            result->obj_type = (PyTypeObject *)object;
            Py_INCREF(object);
        } else if (PyType_IsSubtype(Py_TYPE(object), (PyTypeObject *)type)) {
            result->obj_type = Py_TYPE(object);
            Py_INCREF(result->obj_type);
        } else {
            PyObject *class_attr = PyObject_GetAttr(object, const_str_plain___class__);

            if (likely(class_attr != NULL && PyType_Check(class_attr) &&
                       (PyTypeObject *)class_attr != Py_TYPE(object))) {
                result->obj_type = (PyTypeObject *)class_attr;
            } else {
                if (class_attr == NULL) {
                    CLEAR_ERROR_OCCURRED();
                } else {
                    Py_DECREF(class_attr);
                }

                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError,
                                                "super(type, obj): obj must be an instance or subtype of type");

                return NULL;
            }
        }
    } else {
        result->obj = NULL;
        result->obj_type = NULL;
    }

    Nuitka_GC_Track(result);

    CHECK_OBJECT(result);
    assert(Py_TYPE(result) == &PySuper_Type);

    return (PyObject *)result;
}

/** The "callable" built-in.
 *
 **/

PyObject *BUILTIN_CALLABLE(PyObject *value) {
    int res = PyCallable_Check(value);
    PyObject *result = BOOL_FROM(res != 0);
    Py_INCREF(result);
    return result;
}

/* The "getattr" built-in with default value.
 *
 * We might want to split it off for a variant without default value.
 *
 **/

PyObject *BUILTIN_GETATTR(PyObject *object, PyObject *attribute, PyObject *default_value) {
#if PYTHON_VERSION < 0x300
    if (PyUnicode_Check(attribute)) {
        attribute = _PyUnicode_AsDefaultEncodedString(attribute, NULL);

        if (unlikely(attribute == NULL)) {
            return NULL;
        }
    }

    if (unlikely(!PyString_Check(attribute))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "getattr(): attribute name must be string");
        return NULL;
    }
#else
    if (!PyUnicode_Check(attribute)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "getattr(): attribute name must be string");
        return NULL;
    }
#endif

    PyObject *result = PyObject_GetAttr(object, attribute);

    if (result == NULL) {
        if (default_value != NULL && EXCEPTION_MATCH_BOOL_SINGLE(GET_ERROR_OCCURRED(), PyExc_AttributeError)) {
            CLEAR_ERROR_OCCURRED();

            Py_INCREF(default_value);
            return default_value;
        } else {
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

PyObject *BUILTIN_INT2(PyObject *value, PyObject *base) {
#if PYTHON_VERSION < 0x340
    long base_int = PyInt_AsLong(base);
#else
    Py_ssize_t base_int = PyNumber_AsSsize_t(base, NULL);
#endif

    if (unlikely(base_int == -1)) {
        PyObject *error = GET_ERROR_OCCURRED();

        if (likely(error)) {
#if PYTHON_VERSION >= 0x300
            if (EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_OverflowError)) {
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
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "int() can't convert non-string with explicit base");
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
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "int() can't convert non-string with explicit base");
        return NULL;
    }
#endif
}

#if PYTHON_VERSION < 0x300
// Note: Python3 uses TO_INT2 function.
PyObject *BUILTIN_LONG2(PyObject *value, PyObject *base) {
    long base_int = PyInt_AsLong(base);

    if (unlikely(base_int == -1)) {
        if (likely(ERROR_OCCURRED())) {
            return NULL;
        }
    }

    if (unlikely(!Nuitka_String_Check(value) && !PyUnicode_Check(value))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "long() can't convert non-string with explicit base");
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
