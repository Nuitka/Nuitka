//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** For making imports work.
 *
 * These make the actual built-in importing mechanic work with Nuitka. We
 * provide code to import modules and names from modules, also the mechanic
 * for star imports to look at "__all__".
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

NUITKA_DEFINE_BUILTIN(__import__);

PyObject *IMPORT_MODULE_KW(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals,
                           PyObject *import_items, PyObject *level) {
    CHECK_OBJECT_X(module_name);
    CHECK_OBJECT_X(globals);
    CHECK_OBJECT_X(locals);
    CHECK_OBJECT_X(import_items);
    CHECK_OBJECT_X(level);

    PyObject *kw_pairs[5 * 2] = {const_str_plain_name,   module_name, const_str_plain_globals,  globals,
                                 const_str_plain_locals, locals,      const_str_plain_fromlist, import_items,
                                 const_str_plain_level,  level};
    PyObject *kw_args = MAKE_DICT_X(kw_pairs, 5);

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_KW_ARGS(tstate, NUITKA_ACCESS_BUILTIN(__import__), kw_args);

    Py_DECREF(kw_args);

    return import_result;
}

PyObject *IMPORT_MODULE1(PyThreadState *tstate, PyObject *module_name) {
    CHECK_OBJECT(module_name);

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, NUITKA_ACCESS_BUILTIN(__import__), module_name);

    return import_result;
}

PyObject *IMPORT_MODULE2(PyThreadState *tstate, PyObject *module_name, PyObject *globals) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);

    PyObject *pos_args[] = {module_name, globals};

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS2(tstate, NUITKA_ACCESS_BUILTIN(__import__), pos_args);

    return import_result;
}

PyObject *IMPORT_MODULE3(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);

    PyObject *pos_args[] = {module_name, globals, locals};

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS3(tstate, NUITKA_ACCESS_BUILTIN(__import__), pos_args);

    return import_result;
}

PyObject *IMPORT_MODULE4(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals,
                         PyObject *import_items) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);
    CHECK_OBJECT(import_items);

    PyObject *pos_args[] = {module_name, globals, locals, import_items};

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS4(tstate, NUITKA_ACCESS_BUILTIN(__import__), pos_args);

    return import_result;
}

PyObject *IMPORT_MODULE5(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals,
                         PyObject *import_items, PyObject *level) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);
    CHECK_OBJECT(import_items);
    CHECK_OBJECT(level);

    PyObject *pos_args[] = {module_name, globals, locals, import_items, level};

    NUITKA_ASSIGN_BUILTIN(__import__);
    PyObject *import_function = NUITKA_ACCESS_BUILTIN(__import__);

// TODO: This should be reserved for the import statements, but not for
// the import built-in, we have to make a difference there with 3.10 to
// be compatible.
#if PYTHON_VERSION >= 0x3a0 && 0
    // Fast path for default "__import__" avoids function call.
    if (import_function == tstate->interp->import_func) {
        int level_int = _PyLong_AsInt(level);

        if (level_int == -1 && HAS_ERROR_OCCURRED(tstate)) {
            return NULL;
        }

        return PyImport_ImportModuleLevelObject(module_name, globals, locals, import_items, level_int);
    }
#endif

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS5(tstate, import_function, pos_args);

    return import_result;
}

bool IMPORT_MODULE_STAR(PyThreadState *tstate, PyObject *target, bool is_module, PyObject *module) {
    // Check parameters.
    CHECK_OBJECT(module);
    CHECK_OBJECT(target);

    PyObject *iter;
    bool all_case;

    PyObject *all = PyObject_GetAttr(module, const_str_plain___all__);
    if (all != NULL) {
        iter = MAKE_ITERATOR(tstate, all);
        Py_DECREF(all);

        if (unlikely(iter == NULL)) {
            return false;
        }

        all_case = true;
    } else {
        assert(HAS_ERROR_OCCURRED(tstate));

        if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, GET_ERROR_OCCURRED(tstate), PyExc_AttributeError)) {
            CLEAR_ERROR_OCCURRED(tstate);

            iter = MAKE_ITERATOR(tstate, PyModule_GetDict(module));
            CHECK_OBJECT(iter);

            all_case = false;
        } else {
            return false;
        }
    }

    for (;;) {
        PyObject *item = ITERATOR_NEXT_ITERATOR(iter);
        if (item == NULL) {
            break;
        }

#if PYTHON_VERSION < 0x300
        if (unlikely(PyString_Check(item) == false && PyUnicode_Check(item) == false))
#else
        if (unlikely(PyUnicode_Check(item) == false))
#endif
        {
            PyErr_Format(PyExc_TypeError, "attribute name must be string, not '%s'", Py_TYPE(item)->tp_name);
            break;
        }

        // When we are not using the "__all__", we should skip private variables.
        if (all_case == false) {
            PyObject *startswith_value;
#if PYTHON_VERSION < 0x300
            if (PyString_Check(item)) {
                startswith_value = STR_STARTSWITH2(tstate, item, const_str_underscore);
            } else {
                startswith_value = UNICODE_STARTSWITH2(tstate, item, const_str_underscore);
            }
#else
            startswith_value = UNICODE_STARTSWITH2(tstate, item, const_str_underscore);
#endif

            CHECK_OBJECT(startswith_value);
            Py_DECREF(startswith_value);

            if (startswith_value == Py_True) {
                continue;
            }
        }

        PyObject *value = LOOKUP_ATTRIBUTE(tstate, module, item);

        // Might not exist, because of e.g. wrong "__all__" value.
        if (unlikely(value == NULL)) {
            Py_DECREF(item);
            break;
        }

        // TODO: Check if the reference is handled correctly
        if (is_module) {
            SET_ATTRIBUTE(tstate, target, item, value);
        } else {
            SET_SUBSCRIPT(tstate, target, item, value);
        }

        Py_DECREF(value);
        Py_DECREF(item);
    }

    Py_DECREF(iter);

    return !HAS_ERROR_OCCURRED(tstate);
}

PyObject *IMPORT_NAME_FROM_MODULE(PyThreadState *tstate, PyObject *module, PyObject *import_name) {
    CHECK_OBJECT(module);
    CHECK_OBJECT(import_name);

    PyObject *result = PyObject_GetAttr(module, import_name);

    if (unlikely(result == NULL)) {
        if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate)) {
#if PYTHON_VERSION >= 0x370
            PyObject *filename = Nuitka_GetFilenameObject(tstate, module);

            PyObject *name = LOOKUP_ATTRIBUTE(tstate, module, const_str_plain___name__);
            if (name == NULL) {
                name = PyUnicode_FromString("<unknown module name>");
            }

            PyErr_Format(PyExc_ImportError, "cannot import name %R from %R (%S)", import_name, name, filename);

            Py_DECREF(filename);
            Py_DECREF(name);

#elif PYTHON_VERSION >= 0x300 || !defined(_NUITKA_FULL_COMPAT)
            PyErr_Format(PyExc_ImportError, "cannot import name '%s'", Nuitka_String_AsString(import_name));
#else
            PyErr_Format(PyExc_ImportError, "cannot import name %s", Nuitka_String_AsString(import_name));
#endif
        }

        return NULL;
    }

    return result;
}

#if PYTHON_VERSION >= 0x350

static PyObject *resolveParentModuleName(PyThreadState *tstate, PyObject *module, PyObject *name, int level) {
    PyObject *globals = PyModule_GetDict(module);

    CHECK_OBJECT(globals);

    if (unlikely(!PyDict_Check(globals))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "globals must be a dict");
        return NULL;
    }

    PyObject *package = DICT_GET_ITEM0(tstate, globals, const_str_plain___package__);

    if (unlikely(package == NULL && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (package == Py_None) {
        package = NULL;
    }

    PyObject *spec = DICT_GET_ITEM0(tstate, globals, const_str_plain___spec__);

    if (unlikely(spec == NULL && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (package != NULL) {
        if (!PyUnicode_Check(package)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "package must be a string");
            return NULL;
        }

        // Compare with spec.
        if (spec != NULL && spec != Py_None) {
            PyObject *parent = PyObject_GetAttr(spec, const_str_plain_parent);

            if (unlikely(parent == NULL)) {
                return NULL;
            }

            nuitka_bool nbool_equal = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(package, parent);

            Py_DECREF(parent);

            if (unlikely(nbool_equal == NUITKA_BOOL_EXCEPTION)) {
                return NULL;
            }

            if (unlikely(nbool_equal == NUITKA_BOOL_FALSE)) {
                if (PyErr_WarnEx(PyExc_ImportWarning, "__package__ != __spec__.parent", 1) < 0) {
                    return NULL;
                }
            }
        }

        Py_INCREF(package);
    } else if (spec != NULL && spec != Py_None) {
        package = PyObject_GetAttr(spec, const_str_plain_parent);

        if (unlikely(package == NULL)) {
            return NULL;
        }

        if (unlikely(!PyUnicode_Check(package))) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__spec__.parent must be a string");
            return NULL;
        }
    } else {
        if (PyErr_WarnEx(PyExc_ImportWarning,
                         "can't resolve package from __spec__ or __package__, "
                         "falling back on __name__ and __path__",
                         1) < 0) {
            return NULL;
        }

        package = DICT_GET_ITEM0(tstate, globals, const_str_plain___name__);

        if (unlikely(package == NULL && !HAS_ERROR_OCCURRED(tstate))) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_KeyError, "'__name__' not in globals");
            return NULL;
        }

        if (!PyUnicode_Check(package)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__name__ must be a string");
            return NULL;
        }

        // Detect package from __path__ presence.
        if (DICT_HAS_ITEM(tstate, globals, const_str_plain___path__) == 1) {
            Py_ssize_t dot = PyUnicode_FindChar(package, '.', 0, PyUnicode_GET_LENGTH(package), -1);

            if (unlikely(dot == -2)) {
                return NULL;
            }

            if (unlikely(dot == -1)) {
                // NULL without error means it just didn't work.
                return NULL;
            }

            PyObject *substr = PyUnicode_Substring(package, 0, dot);
            if (unlikely(substr == NULL)) {
                return NULL;
            }

            package = substr;
        } else {
            Py_INCREF(package);
        }
    }

    Py_ssize_t last_dot = PyUnicode_GET_LENGTH(package);

    if (unlikely(last_dot == 0)) {
        Py_DECREF(package);

        // NULL without error means it just didn't work.
        return NULL;
    }

    for (int level_up = 1; level_up < level; level_up += 1) {
        last_dot = PyUnicode_FindChar(package, '.', 0, last_dot, -1);
        if (last_dot == -2) {
            Py_DECREF(package);
            return NULL;
        } else if (last_dot == -1) {
            Py_DECREF(package);
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError,
                                            "attempted relative import beyond top-level package");
            return NULL;
        }
    }

    PyObject *base = PyUnicode_Substring(package, 0, last_dot);

    Py_DECREF(package);

    if (unlikely(base == NULL || PyUnicode_GET_LENGTH(name) == 0)) {
        return base;
    }

    PyObject *abs_name = PyUnicode_FromFormat("%U.%U", base, name);
    Py_DECREF(base);

    return abs_name;
}

PyObject *IMPORT_NAME_OR_MODULE(PyThreadState *tstate, PyObject *module, PyObject *globals, PyObject *import_name,
                                PyObject *level) {
    CHECK_OBJECT(module);
    CHECK_OBJECT(import_name);

    PyObject *result = PyObject_GetAttr(module, import_name);

    if (unlikely(result == NULL)) {
        if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, GET_ERROR_OCCURRED(tstate), PyExc_AttributeError)) {
            CLEAR_ERROR_OCCURRED(tstate);

            long level_int = PyLong_AsLong(level);

            if (unlikely(level_int == -1 && HAS_ERROR_OCCURRED(tstate))) {
                return NULL;
            }

            if (unlikely(level_int < 0)) {
                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "level must be >= 0");
                return NULL;
            }

            if (level_int > 0) {
                PyObject *fromlist = MAKE_TUPLE1(tstate, import_name);

                result = IMPORT_MODULE5(tstate, const_str_empty, globals, globals, fromlist, level);

                Py_DECREF(fromlist);

                // Look up in "sys.modules", because we will have returned the
                // package of it from IMPORT_MODULE5.
                PyObject *name = PyUnicode_FromFormat("%s.%S", PyModule_GetName(result), import_name);

                if (result != NULL) {
                    Py_DECREF(result);

                    result = Nuitka_GetModule(tstate, name);
                }

                Py_DECREF(name);
            } else {
                PyObject *name = resolveParentModuleName(tstate, module, import_name, level_int);

                if (name == NULL) {
                    if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                        return NULL;
                    }
                } else {
                    result = IMPORT_MODULE5(tstate, name, globals, globals, const_tuple_empty, level);

                    if (result != NULL) {
                        Py_DECREF(result);

                        // Look up in "sys.modules", because we will have returned the
                        result = Nuitka_GetModule(tstate, name);
                        Py_DECREF(name);
                    }
                }
            }

            if (result == NULL) {
                CLEAR_ERROR_OCCURRED(tstate);

                result = IMPORT_NAME_FROM_MODULE(tstate, module, import_name);
            }
        }
    }

    CHECK_OBJECT(import_name);

    return result;
}
#endif

PyObject *IMPORT_MODULE_FIXED(PyThreadState *tstate, PyObject *module_name, PyObject *value_name) {
    PyObject *import_result = IMPORT_MODULE1(tstate, module_name);

    if (unlikely(import_result == NULL)) {
        return import_result;
    }

    PyObject *result = Nuitka_GetModule(tstate, value_name);

    Py_DECREF(import_result);

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
