//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperAttributeLookup.c.j2 instead! */
#pragma once

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *LOOKUP_ATTRIBUTE(PyThreadState *tstate, PyObject *source, PyObject *attr_name) {
#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    return PyObject_GetAttr(source, attr_name);
#else
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            // Hold a refcount, Nuitka_TypeLookup does not give any.
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
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

            PyObject *result = DICT_GET_ITEM1(tstate, dict, attr_name);

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
        PyObject *result = LOOKUP_INSTANCE(tstate, source, attr_name);
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

PyObject *LOOKUP_ATTRIBUTE_DICT_SLOT(PyThreadState *tstate, PyObject *source) {
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
            // Hold a refcount, Nuitka_TypeLookup does not give any.
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
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

            PyObject *result = DICT_GET_ITEM1(tstate, dict, const_str_plain___dict__);

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

PyObject *LOOKUP_ATTRIBUTE_CLASS_SLOT(PyThreadState *tstate, PyObject *source) {
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
            // Hold a refcount, Nuitka_TypeLookup does not give any.
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
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

            PyObject *result = DICT_GET_ITEM1(tstate, dict, const_str_plain___class__);

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

bool HAS_ATTR_BOOL(PyThreadState *tstate, PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    return PyObject_HasAttr(source, attr_name);
#else
    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                CLEAR_ERROR_OCCURRED(tstate);
                return false;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            // Hold a refcount, Nuitka_TypeLookup does not give any.
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *result = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    if (result) {
                        CHECK_OBJECT(result);
                        Py_DECREF(result);
                        return true;
                    }

                    DROP_ERROR_OCCURRED(tstate);
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

            PyObject *result = DICT_GET_ITEM1(tstate, dict, attr_name);
            DROP_ERROR_OCCURRED(tstate);

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

            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate) == false) {
                return false;
            }
            return true;
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
        PyObject *result = LOOKUP_INSTANCE(tstate, source, attr_name);

        if (result == NULL) {
            CLEAR_ERROR_OCCURRED(tstate);
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
            DROP_ERROR_OCCURRED(tstate);

            return false;
        }

        CHECK_OBJECT(result);
        Py_DECREF(result);
        return true;
    } else if (type->tp_getattr != NULL) {
        PyObject *result = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (result == NULL) {
            CLEAR_ERROR_OCCURRED(tstate);

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

int HAS_ATTR_BOOL2(PyThreadState *tstate, PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

#if _NUITKA_EXPERIMENTAL_DISABLE_ATTR_OPT
    PyObject *result = PyObject_GetAttr(source, attr_name);

    if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate) == false) {
        return -1;
    }

    if (result == NULL) {
        return 0;
    }

    int result_bool = CHECK_IF_TRUE(result);
    Py_DECREF(result);

    return result_bool;
#else
    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
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

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *result = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    if (result) {
                        CHECK_OBJECT(result);
                        Py_DECREF(result);
                        return 1;
                    }

                    DROP_ERROR_OCCURRED(tstate);
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

            PyObject *result = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate) == false) {
                return -1;
            }

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

            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate) == false) {
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
        PyObject *result = LOOKUP_INSTANCE(tstate, source, attr_name);

        if (result == NULL) {
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
            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate) == false) {
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
            if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate) == false) {
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
