//     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

extern PyObject *const_str_plain_name;
extern PyObject *const_str_plain_globals;
extern PyObject *const_str_plain_locals;
extern PyObject *const_str_plain_fromlist;
extern PyObject *const_str_plain_level;

PyObject *IMPORT_MODULE_KW(PyObject *module_name, PyObject *globals, PyObject *locals, PyObject *import_items,
                           PyObject *level) {
    if (module_name)
        CHECK_OBJECT(module_name);
    if (globals)
        CHECK_OBJECT(globals);
    if (locals)
        CHECK_OBJECT(locals);
    if (import_items)
        CHECK_OBJECT(import_items);
    if (level)
        CHECK_OBJECT(level);

    PyObject *kw_args = PyDict_New();
    if (module_name) {
        CHECK_OBJECT(module_name);
        PyDict_SetItem(kw_args, const_str_plain_name, module_name);
    }
    if (globals) {
        CHECK_OBJECT(globals);
        PyDict_SetItem(kw_args, const_str_plain_globals, globals);
    }
    if (locals) {
        CHECK_OBJECT(locals);
        PyDict_SetItem(kw_args, const_str_plain_locals, locals);
    }
    if (import_items) {
        CHECK_OBJECT(import_items);
        PyDict_SetItem(kw_args, const_str_plain_fromlist, import_items);
    }
    if (level) {
        CHECK_OBJECT(level);
        PyDict_SetItem(kw_args, const_str_plain_level, level);
    }
    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_KEYARGS(NUITKA_ACCESS_BUILTIN(__import__), kw_args);

    Py_DECREF(kw_args);

    return import_result;
}

PyObject *IMPORT_MODULE1(PyObject *module_name) {
    CHECK_OBJECT(module_name);

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_SINGLE_ARG(NUITKA_ACCESS_BUILTIN(__import__), module_name);

    return import_result;
}

PyObject *IMPORT_MODULE2(PyObject *module_name, PyObject *globals) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);

    PyObject *pos_args[] = {module_name, globals};

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS2(NUITKA_ACCESS_BUILTIN(__import__), pos_args);

    return import_result;
}

PyObject *IMPORT_MODULE3(PyObject *module_name, PyObject *globals, PyObject *locals) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);

    PyObject *pos_args[] = {module_name, globals, locals};

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS3(NUITKA_ACCESS_BUILTIN(__import__), pos_args);

    return import_result;
}

PyObject *IMPORT_MODULE4(PyObject *module_name, PyObject *globals, PyObject *locals, PyObject *import_items) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);
    CHECK_OBJECT(import_items);

    PyObject *pos_args[] = {module_name, globals, locals, import_items};

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS4(NUITKA_ACCESS_BUILTIN(__import__), pos_args);

    return import_result;
}

PyObject *IMPORT_MODULE5(PyObject *module_name, PyObject *globals, PyObject *locals, PyObject *import_items,
                         PyObject *level) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(globals);
    CHECK_OBJECT(locals);
    CHECK_OBJECT(import_items);
    CHECK_OBJECT(level);

    PyObject *pos_args[] = {module_name, globals, locals, import_items, level};

    NUITKA_ASSIGN_BUILTIN(__import__);

    PyObject *import_result = CALL_FUNCTION_WITH_ARGS5(NUITKA_ACCESS_BUILTIN(__import__), pos_args);

    return import_result;
}

extern PyObject *const_str_plain___all__;

bool IMPORT_MODULE_STAR(PyObject *target, bool is_module, PyObject *module) {
    // Check parameters.
    CHECK_OBJECT(module);
    CHECK_OBJECT(target);

    PyObject *iter;
    bool all_case;

    PyObject *all = PyObject_GetAttr(module, const_str_plain___all__);
    if (all != NULL) {
        iter = MAKE_ITERATOR(all);
        Py_DECREF(all);

        if (unlikely(iter == NULL)) {
            return false;
        }

        all_case = true;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(GET_ERROR_OCCURRED(), PyExc_AttributeError)) {
        CLEAR_ERROR_OCCURRED();

        iter = MAKE_ITERATOR(PyModule_GetDict(module));
        CHECK_OBJECT(iter);

        all_case = false;
    } else {
        return false;
    }

    for (;;) {
        PyObject *item = ITERATOR_NEXT(iter);
        if (item == NULL)
            break;

#if PYTHON_VERSION < 300
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
            if (Nuitka_String_AsString_Unchecked(item)[0] == '_') {
                continue;
            }
        }

        PyObject *value = LOOKUP_ATTRIBUTE(module, item);

        // Might not exist, because of e.g. wrong "__all__" value.
        if (unlikely(value == NULL)) {
            Py_DECREF(item);
            break;
        }

        // TODO: Check if the reference is handled correctly
        if (is_module) {
            SET_ATTRIBUTE(target, item, value);
        } else {
            SET_SUBSCRIPT(target, item, value);
        }

        Py_DECREF(value);
        Py_DECREF(item);
    }

    Py_DECREF(iter);

    return !ERROR_OCCURRED();
}

PyObject *IMPORT_NAME(PyObject *module, PyObject *import_name) {
    CHECK_OBJECT(module);
    CHECK_OBJECT(import_name);

    PyObject *result = PyObject_GetAttr(module, import_name);

    if (unlikely(result == NULL)) {
        if (EXCEPTION_MATCH_BOOL_SINGLE(GET_ERROR_OCCURRED(), PyExc_AttributeError)) {
#if PYTHON_VERSION >= 370
            PyObject *filename = PyModule_GetFilenameObject(module);
            if (filename == NULL) {
                filename = PyUnicode_FromString("unknown location");
            }

            PyObject *name = LOOKUP_ATTRIBUTE(module, const_str_plain___name__);
            if (name == NULL) {
                name = PyUnicode_FromString("<unknown module name>");
            }

            PyErr_Format(PyExc_ImportError, "cannot import name %R from %R (%S)", import_name, name, filename);

            Py_DECREF(filename);
            Py_DECREF(name);
#elif PYTHON_VERSION >= 340 || !defined(_NUITKA_FULL_COMPAT)
            PyErr_Format(PyExc_ImportError, "cannot import name '%s'", Nuitka_String_AsString(import_name));
#else
            PyErr_Format(PyExc_ImportError, "cannot import name %s", Nuitka_String_AsString(import_name));
#endif
        }

        return NULL;
    }

    return result;
}

#if PYTHON_VERSION >= 350
extern PyObject *const_str_empty;

PyObject *IMPORT_NAME_OR_MODULE(PyObject *module, PyObject *globals, PyObject *import_name, PyObject *level) {
    CHECK_OBJECT(module);
    CHECK_OBJECT(import_name);

    PyObject *result = PyObject_GetAttr(module, import_name);

    if (unlikely(result == NULL)) {
        if (EXCEPTION_MATCH_BOOL_SINGLE(GET_ERROR_OCCURRED(), PyExc_AttributeError)) {
            CLEAR_ERROR_OCCURRED();

            if (PyLong_AsLong(level) != 0) {
                PyObject *fromlist = PyTuple_New(1);
                PyTuple_SET_ITEM0(fromlist, 0, import_name);

                result = IMPORT_MODULE5(const_str_empty, globals, globals, fromlist, level);

                Py_DECREF(fromlist);
            } else {
                PyObject *name = PyUnicode_FromFormat("%s.%S", PyModule_GetName(module), import_name);

                result = IMPORT_MODULE5(name, globals, globals, const_tuple_empty, level);

                Py_DECREF(name);
            }

            if (result != NULL) {
                // Look up in "sys.modules", because we will have returned the
                // package of it from IMPORT_MODULE5.
                PyObject *name = PyUnicode_FromFormat("%s.%S", PyModule_GetName(result), import_name);
                Py_DECREF(result);

                result = PyDict_GetItem(PyImport_GetModuleDict(), name);
                Py_DECREF(name);
            }

            if (result == NULL) {
                CLEAR_ERROR_OCCURRED();

                result = IMPORT_NAME(module, import_name);
            }
        }
    }

    CHECK_OBJECT(import_name);

    return result;
}
#endif
