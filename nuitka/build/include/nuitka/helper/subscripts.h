//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_SUBSCRIPTS_H__
#define __NUITKA_HELPER_SUBSCRIPTS_H__

extern PyObject *STRING_FROM_CHAR(unsigned char c);

#if PYTHON_VERSION >= 0x3b0
static void formatNotSubscriptableTypeError(PyObject *type) {
    SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "type '%s' is not subscriptable",
                                        ((PyTypeObject *)type)->tp_name);
}
#endif

#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_SUBSCRIPT_OPT)
static void formatNotSubscriptableError(PyObject *source) {
    SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(
#if PYTHON_VERSION < 0x270
        "'%s' object is unsubscriptable",
#elif PYTHON_VERSION <= 0x272
        "'%s' object is not subscriptable",
#elif PYTHON_VERSION < 0x300
        "'%s' object has no attribute '__getitem__'",
#else
        "'%s' object is not subscriptable",
#endif
        source);
}
#endif

#if PYTHON_VERSION < 0x370
#define HAS_SEQUENCE_ITEM_SLOT(type) (type->tp_as_sequence != NULL)
#else
#define HAS_SEQUENCE_ITEM_SLOT(type) (type->tp_as_sequence != NULL && type->tp_as_sequence->sq_item)
#endif

#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_SUBSCRIPT_OPT)
static PyObject *SEQUENCE_GET_ITEM_CONST(PyObject *sequence, Py_ssize_t int_subscript) {
    PySequenceMethods *tp_as_sequence = Py_TYPE(sequence)->tp_as_sequence;
    assert(tp_as_sequence != NULL);

#if PYTHON_VERSION < 0x370
    if (unlikely(tp_as_sequence->sq_item == NULL)) {
        PyErr_Format(PyExc_TypeError, "'%s' object does not support indexing", Py_TYPE(sequence)->tp_name);
        return NULL;
    }
#endif

    if (int_subscript < 0) {
        if (tp_as_sequence->sq_length) {
            Py_ssize_t length = (*tp_as_sequence->sq_length)(sequence);
            if (length < 0) {
                return NULL;
            }

            int_subscript += length;
        }
    }

    PyObject *res = tp_as_sequence->sq_item(sequence, int_subscript);
    return res;
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SUBSCRIPT_CONST(PyThreadState *tstate, PyObject *source,
                                                             PyObject *const_subscript, Py_ssize_t int_subscript) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(const_subscript);

#if _NUITKA_EXPERIMENTAL_DISABLE_SUBSCRIPT_OPT
    return PyObject_GetItem(source, const_subscript);
#else
    PyTypeObject *type = Py_TYPE(source);
    PyMappingMethods *tp_as_mapping = type->tp_as_mapping;

    PyObject *result;

    if (tp_as_mapping && tp_as_mapping->mp_subscript) {
        if (PyList_CheckExact(source)) {
            Py_ssize_t list_size = PyList_GET_SIZE(source);

            if (int_subscript < 0) {
                if (-int_subscript > list_size) {
                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_IndexError, "list index out of range");
                    return NULL;
                }

                int_subscript += list_size;
            } else {
                if (int_subscript >= list_size) {
                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_IndexError, "list index out of range");
                    return NULL;
                }
            }

            result = ((PyListObject *)source)->ob_item[int_subscript];

            Py_INCREF(result);
            return result;
        }
#if PYTHON_VERSION < 0x300
        else if (PyString_CheckExact(source)) {
            Py_ssize_t string_size = PyString_GET_SIZE(source);

            if (int_subscript < 0) {
                if (-int_subscript > string_size) {
                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_IndexError, "string index out of range");
                    return NULL;
                }

                int_subscript += string_size;
            } else {
                if (int_subscript >= string_size) {
                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_IndexError, "string index out of range");
                    return NULL;
                }
            }

            unsigned char c = ((PyStringObject *)source)->ob_sval[int_subscript];
            return STRING_FROM_CHAR(c);
        }
#else
        else if (PyUnicode_CheckExact(source)) {
            if (int_subscript < 0) {
                int_subscript += PyUnicode_GET_LENGTH(source);
            }

            result = type->tp_as_sequence->sq_item(source, int_subscript);
        }
#endif
        else {
            result = tp_as_mapping->mp_subscript(source, const_subscript);
        }
    } else if (HAS_SEQUENCE_ITEM_SLOT(type)) {
        result = SEQUENCE_GET_ITEM_CONST(source, int_subscript);
    } else {
#if PYTHON_VERSION >= 0x370
        if (PyType_Check(source)) {
#if PYTHON_VERSION >= 0x390
            if (source == (PyObject *)&PyType_Type) {
                PyObject *subscript = PyLong_FromSsize_t(int_subscript);
                result = Py_GenericAlias(source, subscript);
                Py_DECREF(subscript);

                return result;
            }
#endif

            PyObject *meth = LOOKUP_ATTRIBUTE(tstate, source, const_str_plain___class_getitem__);

            if (meth) {
                PyObject *subscript = PyLong_FromSsize_t(int_subscript);
                result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, meth, subscript);
                Py_DECREF(meth);
                Py_DECREF(subscript);

                return result;
            }

            // Different error against types for Python3.11+
#if PYTHON_VERSION >= 0x3b0
            formatNotSubscriptableTypeError(source);
            return NULL;
#endif
        }
#endif

        formatNotSubscriptableError(source);
        return NULL;
    }

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
#endif
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SUBSCRIPT(PyThreadState *tstate, PyObject *source, PyObject *subscript) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(subscript);

#if _NUITKA_EXPERIMENTAL_DISABLE_SUBSCRIPT_OPT
    return PyObject_GetItem(source, subscript);
#else
    PyTypeObject *type = Py_TYPE(source);
    PyMappingMethods *tp_as_mapping = type->tp_as_mapping;

    if (tp_as_mapping != NULL && tp_as_mapping->mp_subscript != NULL) {
        return tp_as_mapping->mp_subscript(source, subscript);
    } else if (HAS_SEQUENCE_ITEM_SLOT(type)) {
        if (Nuitka_Index_Check(subscript)) {
            Py_ssize_t index = PyNumber_AsSsize_t(subscript, NULL);

            if (index == -1 && HAS_ERROR_OCCURRED(tstate)) {
                return NULL;
            }

            return SEQUENCE_GET_ITEM_CONST(source, index);
        } else if (type->tp_as_sequence->sq_item) {
            PyErr_Format(PyExc_TypeError, "sequence index must be integer, not '%s'", Py_TYPE(subscript)->tp_name);
            return NULL;
#if PYTHON_VERSION < 0x370
        } else {
            formatNotSubscriptableError(source);
            return NULL;
#endif
        }
    }

#if PYTHON_VERSION >= 0x370
    if (PyType_Check(source)) {
#if PYTHON_VERSION >= 0x390
        if (source == (PyObject *)&PyType_Type) {
            return Py_GenericAlias(source, subscript);
        }
#endif

        PyObject *meth = LOOKUP_ATTRIBUTE(tstate, source, const_str_plain___class_getitem__);

        if (meth) {
            PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, meth, subscript);
            Py_DECREF(meth);
            return result;
        }

        // Different error against types for Python3.11+
#if PYTHON_VERSION >= 0x3b0
        formatNotSubscriptableTypeError(source);
        return NULL;
#endif
    }
#endif

    formatNotSubscriptableError(source);
    return NULL;
#endif
}

bool MATCH_MAPPING_KEY(PyThreadState *tstate, PyObject *map, PyObject *key);

NUITKA_MAY_BE_UNUSED static bool SET_SUBSCRIPT_CONST(PyThreadState *tstate, PyObject *target, PyObject *subscript,
                                                     Py_ssize_t int_subscript, PyObject *value) {
    CHECK_OBJECT(value);
    CHECK_OBJECT(target);
    CHECK_OBJECT(subscript);

#if _NUITKA_EXPERIMENTAL_DISABLE_SUBSCRIPT_OPT
    int res = PyObject_SetItem(target, subscript, value);
    return res == 0;
#else
    PyMappingMethods *tp_as_mapping = Py_TYPE(target)->tp_as_mapping;

    if (tp_as_mapping != NULL && tp_as_mapping->mp_ass_subscript) {
        if (PyList_CheckExact(target)) {
            Py_ssize_t list_size = PyList_GET_SIZE(target);

            if (int_subscript < 0) {
                if (-int_subscript > list_size) {
                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_IndexError, "list assignment index out of range");

                    return false;
                }

                int_subscript += list_size;
            }

            PyListObject *target_list = (PyListObject *)target;

            PyObject *old_value = target_list->ob_item[int_subscript];
            Py_INCREF(value);
            target_list->ob_item[int_subscript] = value;
            Py_DECREF(old_value);

            return true;
        } else {
            int res = tp_as_mapping->mp_ass_subscript(target, subscript, value);

            if (unlikely(res == -1)) {
                return false;
            }

            return true;
        }
    } else if (Py_TYPE(target)->tp_as_sequence) {
        if (Nuitka_Index_Check(subscript)) {
            Py_ssize_t key_value = PyNumber_AsSsize_t(subscript, PyExc_IndexError);

            if (key_value == -1) {
                if (HAS_ERROR_OCCURRED(tstate)) {
                    return false;
                }
            }

            return SEQUENCE_SET_ITEM(target, key_value, value);
        } else if (Py_TYPE(target)->tp_as_sequence->sq_ass_item) {
            PyErr_Format(PyExc_TypeError, "sequence index must be integer, not '%s'", Py_TYPE(subscript)->tp_name);

            return false;
        } else {
            PyErr_Format(PyExc_TypeError, "'%s' object does not support item assignment", Py_TYPE(target)->tp_name);

            return false;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "'%s' object does not support item assignment", Py_TYPE(target)->tp_name);

        return false;
    }
#endif
}

NUITKA_MAY_BE_UNUSED static bool SET_SUBSCRIPT(PyThreadState *tstate, PyObject *target, PyObject *subscript,
                                               PyObject *value) {
    CHECK_OBJECT(value);
    CHECK_OBJECT(target);
    CHECK_OBJECT(subscript);

#if _NUITKA_EXPERIMENTAL_DISABLE_SUBSCRIPT_OPT
    int res = PyObject_SetItem(target, subscript, value);
    return res == 0;
#else
    PyMappingMethods *tp_as_mapping = Py_TYPE(target)->tp_as_mapping;

    if (tp_as_mapping != NULL && tp_as_mapping->mp_ass_subscript) {
        int res = tp_as_mapping->mp_ass_subscript(target, subscript, value);

        if (unlikely(res == -1)) {
            return false;
        }
    } else if (Py_TYPE(target)->tp_as_sequence) {
        if (Nuitka_Index_Check(subscript)) {
            Py_ssize_t key_value = PyNumber_AsSsize_t(subscript, PyExc_IndexError);

            if (key_value == -1) {
                if (HAS_ERROR_OCCURRED(tstate)) {
                    return false;
                }
            }

            return SEQUENCE_SET_ITEM(target, key_value, value);
        } else if (Py_TYPE(target)->tp_as_sequence->sq_ass_item) {
            PyErr_Format(PyExc_TypeError, "sequence index must be integer, not '%s'", Py_TYPE(subscript)->tp_name);

            return false;
        } else {
            PyErr_Format(PyExc_TypeError, "'%s' object does not support item assignment", Py_TYPE(target)->tp_name);

            return false;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "'%s' object does not support item assignment", Py_TYPE(target)->tp_name);

        return false;
    }

    return true;
#endif
}

NUITKA_MAY_BE_UNUSED static bool DEL_SUBSCRIPT(PyObject *target, PyObject *subscript) {
    CHECK_OBJECT(target);
    CHECK_OBJECT(subscript);

    int status = PyObject_DelItem(target, subscript);

    if (unlikely(status == -1)) {
        return false;
    }

    return true;
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
