//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// spell-checker: ignore klass

#if PYTHON_VERSION < 0x300
PyObject *FIND_ATTRIBUTE_IN_CLASS(PyClassObject *klass, PyObject *attr_name) {
    CHECK_OBJECT(klass);
    CHECK_OBJECT(attr_name);

    assert(PyClass_Check(klass));
    assert(PyString_CheckExact(attr_name));

    PyObject *result = GET_STRING_DICT_VALUE((PyDictObject *)klass->cl_dict, (PyStringObject *)attr_name);

    if (result == NULL) {
        assert(PyTuple_Check(klass->cl_bases));

        Py_ssize_t base_count = PyTuple_GET_SIZE(klass->cl_bases);

        for (Py_ssize_t i = 0; i < base_count; i++) {
            result = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)PyTuple_GET_ITEM(klass->cl_bases, i), attr_name);

            if (result != NULL) {
                break;
            }
        }
    }

    return result;
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *LOOKUP_INSTANCE(PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    assert(PyInstance_Check(source));
    assert(PyString_CheckExact(attr_name));

    PyInstanceObject *source_instance = (PyInstanceObject *)source;

    // The special cases have their own variant on the code generation level
    // as we are called with constants only.
    assert(attr_name != const_str_plain___dict__);
    assert(attr_name != const_str_plain___class__);

    // Try the instance dict first.
    PyObject *result = GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

    if (result) {
        Py_INCREF(result);
        return result;
    }

    // Next see if a class has it
    result = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

    if (result != NULL) {
        descrgetfunc func = Py_TYPE(result)->tp_descr_get;

        if (func) {
            result = func(result, source, (PyObject *)source_instance->in_class);

            if (unlikely(result == NULL)) {
                return NULL;
            }

            CHECK_OBJECT(result);

            return result;
        } else {
            Py_INCREF(result);
            return result;
        }
    }

    // Finally allow a __getattr__ to handle it or else it's an error.
    if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
        PyErr_Format(PyExc_AttributeError, "%s instance has no attribute '%s'",
                     PyString_AS_STRING(source_instance->in_class->cl_name), PyString_AS_STRING(attr_name));

        return NULL;
    } else {
        PyObject *args[] = {source, attr_name};
        return CALL_FUNCTION_WITH_ARGS2(source_instance->in_class->cl_getattr, args);
    }
}
#endif

PyObject *LOOKUP_ATTRIBUTE(PyObject *source, PyObject *attr_name) {
    /* Note: There are 2 specializations of this function, that need to be
     * updated in line with this: LOOKUP_ATTRIBUTE_[DICT|CLASS]_SLOT
     */

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    return PyObject_GetAttr(source, attr_name);
#else
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && PyDescr_IsData(descr)) {
                    PyObject *result = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    return result;
                }
            }
        }

        PyObject *dict = NULL;

// TODO: This is what Python 3.11 requires us to add.
#if PYTHON_VERSION >= 0x3b0 && 0
        if ((type->tp_flags & Py_TPFLAGS_MANAGED_DICT) && *_PyObject_ValuesPointer(source)) {
            PyObject **dict_pointer;

            PyDictValues **values_ptr = _PyObject_ValuesPointer(source);

            // TODO: Seems we would benefit by knowing this on the outside.
            if (PyUnicode_CheckExact(attr_name)) {
                assert(*_PyObject_DictPointer(source) == NULL);
                PyObject *result = _PyObject_GetInstanceAttribute(source, *values_ptr, attr_name);
                if (result != NULL) {
                    return result;
                }
            } else {
                dict_pointer = _PyObject_DictPointer(source);
                assert(dict_pointer != NULL && *dict_pointer == NULL);

                *dict_pointer = dict = _PyObject_MakeDictFromInstanceAttributes(source, *values_ptr);
                if (unlikely(dict == NULL)) {
                    return NULL;
                }
                *values_ptr = NULL;
            }
        }
#endif

        if (dict == NULL) {
            Py_ssize_t dict_offset = type->tp_dictoffset;

            if (dict_offset != 0) {

                // Negative dictionary offsets have special meaning.
                if (dict_offset < 0) {
                    Py_ssize_t tsize;
                    size_t size;

                    tsize = ((PyVarObject *)source)->ob_size;
                    if (tsize < 0) {
                        tsize = -tsize;
                    }
                    size = _PyObject_VAR_SIZE(type, tsize);

                    dict_offset += (long)size;
                }

                PyObject **dict_pointer = (PyObject **)((char *)source + dict_offset);
                dict = *dict_pointer;
            }
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            // TODO: If this is an exact dict, we don't have to hold a reference, is it?
            Py_INCREF(dict);

            PyObject *result = DICT_GET_ITEM1(dict, attr_name);

            Py_DECREF(dict);

            if (result != NULL) {
                Py_XDECREF(descr);

                CHECK_OBJECT(result);
                return result;
            }
        }

        if (func != NULL) {
            PyObject *result = func(descr, source, (PyObject *)type);
            Py_DECREF(descr);

            CHECK_OBJECT_X(result);
            return result;
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);
            return descr;
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                     PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type->tp_getattro == PyInstance_Type.tp_getattro && Nuitka_String_CheckExact(attr_name)) {
        PyObject *result = LOOKUP_INSTANCE(source, attr_name);
        return result;
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *result = (*type->tp_getattro)(source, attr_name);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        CHECK_OBJECT(result);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *result = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));
        return result;
    } else {
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                     Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
#endif
}

PyObject *LOOKUP_ATTRIBUTE_DICT_SLOT(PyObject *source) {
    CHECK_OBJECT(source);

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    return PyObject_GetAttr(source, const_str_plain___dict__);
#else
    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, const_str_plain___dict__);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && PyDescr_IsData(descr)) {
                    PyObject *result = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    return result;
                }
            }
        }

        Py_ssize_t dict_offset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dict_offset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dict_offset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0)
                    tsize = -tsize;
                size = _PyObject_VAR_SIZE(type, tsize);

                dict_offset += (long)size;
            }

            PyObject **dict_pointer = (PyObject **)((char *)source + dict_offset);
            dict = *dict_pointer;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *result = DICT_GET_ITEM1(dict, const_str_plain___dict__);

            if (result != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                CHECK_OBJECT(result);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            PyObject *result = func(descr, source, (PyObject *)type);
            Py_DECREF(descr);

            CHECK_OBJECT_X(result);
            return result;
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);
            return descr;
        }

        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '__dict__'", type->tp_name);
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type->tp_getattro == PyInstance_Type.tp_getattro) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;
        PyObject *result = source_instance->in_dict;

        Py_INCREF(result);
        return result;
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *result = (*type->tp_getattro)(source, const_str_plain___dict__);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        CHECK_OBJECT(result);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *result = (*type->tp_getattr)(source, (char *)"__dict__");
        return result;
    } else {
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '__dict__'", type->tp_name);

        return NULL;
    }
#endif
}

PyObject *LOOKUP_ATTRIBUTE_CLASS_SLOT(PyObject *source) {
    CHECK_OBJECT(source);

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    return PyObject_GetAttr(source, const_str_plain___class__);
#else
    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, const_str_plain___class__);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && PyDescr_IsData(descr)) {
                    PyObject *result = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    return result;
                }
            }
        }

        Py_ssize_t dict_offset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dict_offset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dict_offset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dict_offset += (long)size;
            }

            PyObject **dict_pointer = (PyObject **)((char *)source + dict_offset);
            dict = *dict_pointer;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *result = DICT_GET_ITEM1(dict, const_str_plain___class__);

            if (result != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                CHECK_OBJECT(result);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            PyObject *result = func(descr, source, (PyObject *)type);
            Py_DECREF(descr);

            CHECK_OBJECT_X(result);
            return result;
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);
            return descr;
        }

        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '__class__'", type->tp_name);
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type->tp_getattro == PyInstance_Type.tp_getattro) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;
        PyObject *result = (PyObject *)source_instance->in_class;

        Py_INCREF(result);
        return result;
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *result = (*type->tp_getattro)(source, const_str_plain___class__);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        CHECK_OBJECT(result);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *result = (*type->tp_getattr)(source, (char *)"__class__");
        return result;
    } else {
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '__class__'", type->tp_name);

        return NULL;
    }
#endif
}

int BUILTIN_HASATTR_BOOL(PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

#if PYTHON_VERSION < 0x300
    if (PyUnicode_Check(attr_name)) {
        attr_name = _PyUnicode_AsDefaultEncodedString(attr_name, NULL);

        if (unlikely(attr_name == NULL)) {
            return -1;
        }
    }

    if (unlikely(!PyString_Check(attr_name))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "hasattr(): attribute name must be string");

        return -1;
    }
#else
    if (unlikely(!PyUnicode_Check(attr_name))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "hasattr(): attribute name must be string");

        return -1;
    }
#endif

    // TODO: This should use what LOOKUP_ATTRIBUTE does and know that the result value is going to
    // be unused, having an easier time generally, e.g. not having to create the error in the first
    // place.
    PyObject *value = PyObject_GetAttr(source, attr_name);

    if (value == NULL) {
        if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED() == false) {
            return -1;
        }
        return 0;
    }

    Py_DECREF(value);

    return 1;
}

bool HAS_ATTR_BOOL(PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    return PyObject_HasAttr(source, attr_name);
#else
    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                DROP_ERROR_OCCURRED();

                return false;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && PyDescr_IsData(descr)) {
                    PyObject *result = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    if (result) {
                        CHECK_OBJECT(result);

                        Py_DECREF(result);
                        return true;
                    }

                    DROP_ERROR_OCCURRED();
                    return false;
                }
            }
        }

        Py_ssize_t dict_offset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dict_offset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dict_offset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dict_offset += (long)size;
            }

            PyObject **dict_pointer = (PyObject **)((char *)source + dict_offset);
            dict = *dict_pointer;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            // TODO: If this is an exact dict, we don't have to hold a reference, is it?
            Py_INCREF(dict);

            PyObject *result = DICT_GET_ITEM1(dict, attr_name);
            DROP_ERROR_OCCURRED();

            Py_DECREF(dict);

            if (result != NULL) {
                Py_XDECREF(descr);

                CHECK_OBJECT(result);

                Py_DECREF(result);
                return true;
            }
        }

        if (func != NULL) {
            PyObject *result = func(descr, source, (PyObject *)type);
            Py_DECREF(descr);

            if (result != NULL) {
                CHECK_OBJECT(result);

                Py_DECREF(result);
                return true;
            }

            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED() == false) {
                return -1;
            }
            return 0;
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            Py_DECREF(descr);
            return true;
        }

        return false;
    }
#if PYTHON_VERSION < 0x300
    else if (type->tp_getattro == PyInstance_Type.tp_getattro && Nuitka_String_CheckExact(attr_name)) {
        PyObject *result = LOOKUP_INSTANCE(source, attr_name);

        if (result == NULL) {
            DROP_ERROR_OCCURRED();

            return false;
        }

        CHECK_OBJECT(result);

        Py_DECREF(result);
        return true;
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *result = (*type->tp_getattro)(source, attr_name);

        if (result == NULL) {
            DROP_ERROR_OCCURRED();

            return false;
        }

        CHECK_OBJECT(result);
        Py_DECREF(result);
        return true;
    } else if (type->tp_getattr != NULL) {
        PyObject *result = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (result == NULL) {
            DROP_ERROR_OCCURRED();

            return false;
        }

        CHECK_OBJECT(result);
        Py_DECREF(result);
        return true;
    } else {
        return false;
    }
#endif
}

int HAS_ATTR_BOOL2(PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    PyObject *result = PyObject_GetAttr(source, attr_name);

    if (result == NULL) {
        return -1;
    }

    return CHECK_IF_TRUE(result) = 1 : 0;
#else
    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return -1;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            // Hold a refcount, Nuitka_TypeLookup does not give any.
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && PyDescr_IsData(descr)) {
                    PyObject *result = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    if (result) {
                        CHECK_OBJECT(result);

                        Py_DECREF(result);
                        return 1;
                    }

                    DROP_ERROR_OCCURRED();
                    return 0;
                }
            }
        }

        Py_ssize_t dict_offset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dict_offset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dict_offset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dict_offset += (long)size;
            }

            PyObject **dict_pointer = (PyObject **)((char *)source + dict_offset);
            dict = *dict_pointer;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            // TODO: If this is an exact dict, we don't have to hold a reference, is it?
            Py_INCREF(dict);

            PyObject *result = DICT_GET_ITEM1(dict, attr_name);

            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED() == false) {
                return -1;
            }

            DROP_ERROR_OCCURRED();

            Py_DECREF(dict);

            if (result != NULL) {
                Py_XDECREF(descr);

                CHECK_OBJECT(result);

                Py_DECREF(result);
                return 1;
            }
        }

        if (func != NULL) {
            PyObject *result = func(descr, source, (PyObject *)type);
            Py_DECREF(descr);

            if (result != NULL) {
                CHECK_OBJECT(result);

                Py_DECREF(result);
                return 1;
            }

            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED() == false) {
                return -1;
            }
            return 0;
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            Py_DECREF(descr);
            return 1;
        }

        return 0;
    }
#if PYTHON_VERSION < 0x300
    else if (type->tp_getattro == PyInstance_Type.tp_getattro && Nuitka_String_CheckExact(attr_name)) {
        PyObject *result = LOOKUP_INSTANCE(source, attr_name);

        if (result == NULL) {
            DROP_ERROR_OCCURRED();

            return -1;
        }

        CHECK_OBJECT(result);

        Py_DECREF(result);
        return true;
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *result = (*type->tp_getattro)(source, attr_name);

        if (result == NULL) {
            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED() == false) {
                return -1;
            }

            return 0;
        }

        CHECK_OBJECT(result);
        Py_DECREF(result);
        return true;
    } else if (type->tp_getattr != NULL) {
        PyObject *result = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (result == NULL) {
            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED() == false) {
                return -1;
            }

            return 0;
        }

        CHECK_OBJECT(result);
        Py_DECREF(result);

        return 1;
    } else {
        return 0;
    }
#endif
}

#if PYTHON_VERSION < 0x300
extern PyObject *CALL_FUNCTION_WITH_ARGS3(PyObject *called, PyObject *const *args);

static bool SET_INSTANCE(PyObject *target, PyObject *attr_name, PyObject *value) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(attr_name);
    CHECK_OBJECT(value);

    assert(PyInstance_Check(target));
    assert(PyString_Check(attr_name));

    PyInstanceObject *target_instance = (PyInstanceObject *)target;

    // The special cases should get their own SET_ATTRIBUTE_xxxx_SLOT variants
    // on the code generation level as SET_ATTRIBUTE is called with constants
    // only.
    assert(attr_name != const_str_plain___dict__);
    assert(attr_name != const_str_plain___class__);

    if (target_instance->in_class->cl_setattr != NULL) {
        PyObject *args[] = {target, attr_name, value};
        PyObject *result = CALL_FUNCTION_WITH_ARGS3(target_instance->in_class->cl_setattr, args);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(result);

        return true;
    } else {
        int status = PyDict_SetItem(target_instance->in_dict, attr_name, value);

        if (unlikely(status != 0)) {
            return false;
        }

        return true;
    }
}
#endif

#if (PYTHON_VERSION < 0x300 || defined(_NUITKA_USE_UNEXPOSED_API)) && !defined(_NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT)

// Classes in Python3 might share keys.
#define CACHED_KEYS(type) (((PyHeapTypeObject *)type)->ht_cached_keys)

static bool SET_ATTRIBUTE_GENERIC(PyTypeObject *type, PyObject *target, PyObject *attr_name, PyObject *value) {
    // Unfortunately this is required, although of cause rarely necessary.
    if (unlikely(type->tp_dict == NULL)) {
        if (unlikely(PyType_Ready(type) < 0)) {
            return false;
        }
    }

    PyObject *descr = Nuitka_TypeLookup(type, attr_name);

    if (descr != NULL) {
        Py_INCREF(descr);

        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            descrsetfunc func = Py_TYPE(descr)->tp_descr_set;

            if (func != NULL && PyDescr_IsData(descr)) {
                int res = func(descr, target, value);
                Py_DECREF(descr);

                return res == 0;
            }
        }
    }

    Py_ssize_t dict_offset = type->tp_dictoffset;
    PyObject *dict = NULL;

    if (dict_offset != 0) {
        // Negative dictionary offsets have special meaning.
        if (dict_offset < 0) {
            Py_ssize_t tsize;
            size_t size;

            tsize = ((PyVarObject *)target)->ob_size;
            if (tsize < 0) {
                tsize = -tsize;
            }
            size = _PyObject_VAR_SIZE(type, tsize);

            dict_offset += (long)size;
        }

        PyObject **dict_pointer = (PyObject **)((char *)target + dict_offset);

#if PYTHON_VERSION >= 0x300
        if ((type->tp_flags & Py_TPFLAGS_HEAPTYPE) && (CACHED_KEYS(type) != NULL)) {
            int res = _PyObjectDict_SetItem(type, dict_pointer, attr_name, value);

            // TODO: Not possible for set, is it?
            if (res < 0 && PyErr_ExceptionMatches(PyExc_KeyError)) {
                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(PyExc_AttributeError, attr_name);
                return false;
            }

            return res >= 0;
        } else
#endif
        {
            dict = *dict_pointer;

            if (dict == NULL) {
                dict = MAKE_DICT_EMPTY();
                *dict_pointer = dict;
            }
        }
    }

    if (dict != NULL) {
        CHECK_OBJECT(dict);

        // TODO: If this is an exact dict, we don't have to hold a reference, is it?
        Py_INCREF(dict);

        int res = PyDict_SetItem(dict, attr_name, value);

        Py_DECREF(dict);
        Py_XDECREF(descr);

        return res == 0;
    }

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                 PyString_AS_STRING(attr_name));
#else
    PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
    return false;
}

#endif

bool SET_ATTRIBUTE(PyObject *target, PyObject *attr_name, PyObject *value) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(attr_name);
    CHECK_OBJECT(value);

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    int res = PyObject_SetAttr(target, attr_name, value);
    return res == 0;
#else
    PyTypeObject *type = Py_TYPE(target);

#if PYTHON_VERSION < 0x300 || defined(_NUITKA_USE_UNEXPOSED_API)
    if (hasTypeGenericSetAttr(type)) {
        return SET_ATTRIBUTE_GENERIC(type, target, attr_name, value);
    }
#endif
#if PYTHON_VERSION < 0x300
    if (type->tp_setattro == PyInstance_Type.tp_setattro) {
        return SET_INSTANCE(target, attr_name, value);
    }
#endif
    if (type->tp_setattro != NULL) {
        int status = (*type->tp_setattro)(target, attr_name, value);

        if (unlikely(status == -1)) {
            return false;
        }

        return true;
    }

    if (type->tp_setattr != NULL) {
        int status = (*type->tp_setattr)(target, (char *)Nuitka_String_AsString_Unchecked(attr_name), value);

        if (unlikely(status == -1)) {
            return false;
        }

        return true;
    }

    if (type->tp_getattr == NULL && type->tp_getattro == NULL) {
        PyErr_Format(PyExc_TypeError, "'%s' object has no attributes (assign to %s)", type->tp_name,
                     Nuitka_String_AsString_Unchecked(attr_name));

        return false;
    } else {
        PyErr_Format(PyExc_TypeError, "'%s' object has only read-only attributes (assign to %s)", type->tp_name,
                     Nuitka_String_AsString_Unchecked(attr_name));

        return false;
    }
#endif
}

bool SET_ATTRIBUTE_DICT_SLOT(PyObject *target, PyObject *value) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(value);

#if PYTHON_VERSION < 0x300
    if (likely(PyInstance_Check(target))) {
        PyInstanceObject *target_instance = (PyInstanceObject *)target;

        /* Note seems this doesn't have to be an exact dictionary. */
        if (unlikely(!PyDict_Check(value))) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__dict__ must be set to a dictionary");
            return false;
        }

        PyObject *old = target_instance->in_dict;

        Py_INCREF(value);
        target_instance->in_dict = value;

        Py_DECREF(old);
    } else
#endif
    {
        PyTypeObject *type = Py_TYPE(target);

        if (type->tp_setattro != NULL) {
            int status = (*type->tp_setattro)(target, const_str_plain___dict__, value);

            if (unlikely(status == -1)) {
                return false;
            }
        } else if (type->tp_setattr != NULL) {
            int status = (*type->tp_setattr)(target, (char *)"__dict__", value);

            if (unlikely(status == -1)) {
                return false;
            }
        } else if (type->tp_getattr == NULL && type->tp_getattro == NULL) {
            PyErr_Format(PyExc_TypeError, "'%s' object has no attributes (assign to __dict__)", type->tp_name);

            return false;
        } else {
            PyErr_Format(PyExc_TypeError, "'%s' object has only read-only attributes (assign to __dict__)",
                         type->tp_name);

            return false;
        }
    }

    return true;
}

bool SET_ATTRIBUTE_CLASS_SLOT(PyObject *target, PyObject *value) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(value);

#if PYTHON_VERSION < 0x300
    if (likely(PyInstance_Check(target))) {
        PyInstanceObject *target_instance = (PyInstanceObject *)target;

        if (unlikely(!PyClass_Check(value))) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__class__ must be set to a class");
            return false;
        }

        PyObject *old = (PyObject *)(target_instance->in_class);
        Py_INCREF(value);
        target_instance->in_class = (PyClassObject *)value;
        Py_DECREF(old);
    } else
#endif
    {
        PyTypeObject *type = Py_TYPE(target);

        if (type->tp_setattro != NULL) {
            int status = (*type->tp_setattro)(target, const_str_plain___class__, value);

            if (unlikely(status == -1)) {
                return false;
            }
        } else if (type->tp_setattr != NULL) {
            int status = (*type->tp_setattr)(target, (char *)"__class__", value);

            if (unlikely(status == -1)) {
                return false;
            }
        } else if (type->tp_getattr == NULL && type->tp_getattro == NULL) {
            PyErr_Format(PyExc_TypeError, "'%s' object has no attributes (assign to __class__)", type->tp_name);

            return false;
        } else {
            PyErr_Format(PyExc_TypeError, "'%s' object has only read-only attributes (assign to __class__)",
                         type->tp_name);

            return false;
        }
    }

    return true;
}

PyObject *LOOKUP_SPECIAL(PyObject *source, PyObject *attr_name) {
#if PYTHON_VERSION < 0x300
    if (PyInstance_Check(source)) {
        return LOOKUP_INSTANCE(source, attr_name);
    }
#endif

    // TODO: There is heavy optimization in CPython to avoid it. Potentially
    // that's worth it to imitate that.

    PyObject *result = Nuitka_TypeLookup(Py_TYPE(source), attr_name);

    if (likely(result)) {
        descrgetfunc func = Py_TYPE(result)->tp_descr_get;

        if (func == NULL) {
            Py_INCREF(result);
            return result;
        } else {
            PyObject *func_result = func(result, source, (PyObject *)(Py_TYPE(source)));

            if (unlikely(func_result == NULL)) {
                return NULL;
            }

            CHECK_OBJECT(func_result);
            return func_result;
        }
    }

#if PYTHON_VERSION < 0x3B0
    SET_CURRENT_EXCEPTION_TYPE0_VALUE0(PyExc_AttributeError, attr_name);
#else
    // TODO: Maybe we should have dedicated variations with the 4 hard coded
    // attribute names, might save a bit of complexity to large programs not
    // having to pass constant values in what is a frequent construct.
    if (attr_name == const_str_plain___exit__) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(
            "'%s' object does not support the context manager protocol (missed __exit__ method)", source);
    } else if (attr_name == const_str_plain___aexit__) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(
            "'%s' object does not support the asynchronous context manager protocol (missed __aexit__ method)", source);
    } else if (attr_name == const_str_plain___aenter__) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object does not support the asynchronous context manager protocol",
                                             source);
    } else {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object does not support the context manager protocol", source);
    }
#endif
    return NULL;
}

PyObject *LOOKUP_MODULE_VALUE(PyDictObject *module_dict, PyObject *var_name) {
    PyObject *result = GET_STRING_DICT_VALUE(module_dict, (Nuitka_StringObject *)var_name);

    if (unlikely(result == NULL)) {
        result = GET_STRING_DICT_VALUE(dict_builtin, (Nuitka_StringObject *)var_name);
    }

    return result;
}

PyObject *GET_MODULE_VARIABLE_VALUE_FALLBACK(PyObject *variable_name) {
    PyObject *result = GET_STRING_DICT_VALUE(dict_builtin, (Nuitka_StringObject *)variable_name);

    if (unlikely(result == NULL)) {
        PyObject *exception_type;
        PyObject *exception_value;

        // TODO: Do this in one go, once FORMAT_NAME_ERROR becomes unused in code generation.
        FORMAT_NAME_ERROR(&exception_type, &exception_value, variable_name);

#if PYTHON_VERSION >= 0x300
        // TODO: FORMAT_NAME_ERROR for Python3 should already produce this normalized and chained.
        NORMALIZE_EXCEPTION(&exception_type, &exception_value, NULL);
        CHAIN_EXCEPTION(exception_value);
#endif

        RESTORE_ERROR_OCCURRED(exception_type, exception_value, NULL);
    }

    return result;
}

#if PYTHON_VERSION < 0x340
PyObject *GET_MODULE_VARIABLE_VALUE_FALLBACK_IN_FUNCTION(PyObject *variable_name) {
    PyObject *result = GET_STRING_DICT_VALUE(dict_builtin, (Nuitka_StringObject *)variable_name);

    if (unlikely(result == NULL)) {
        PyObject *exception_type;
        PyObject *exception_value;

        FORMAT_GLOBAL_NAME_ERROR(&exception_type, &exception_value, variable_name);
        RESTORE_ERROR_OCCURRED(exception_type, exception_value, NULL);
    }

    return result;
}
#endif