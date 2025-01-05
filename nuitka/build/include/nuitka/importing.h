//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_IMPORTING_H__
#define __NUITKA_IMPORTING_H__

/* These are for the built-in import.
 *
 * They call the real thing with varying amount of arguments. For keyword
 * calls using default values, the _KW helper is used.
 *
 */
extern PyObject *IMPORT_MODULE1(PyThreadState *tstate, PyObject *module_name);
extern PyObject *IMPORT_MODULE2(PyThreadState *tstate, PyObject *module_name, PyObject *globals);
extern PyObject *IMPORT_MODULE3(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals);
extern PyObject *IMPORT_MODULE4(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals,
                                PyObject *import_items);
extern PyObject *IMPORT_MODULE5(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals,
                                PyObject *import_items, PyObject *level);

extern PyObject *IMPORT_MODULE_KW(PyThreadState *tstate, PyObject *module_name, PyObject *globals, PyObject *locals,
                                  PyObject *import_items, PyObject *level);

extern bool IMPORT_MODULE_STAR(PyThreadState *tstate, PyObject *target, bool is_module, PyObject *module);

// Fixed import name to be imported and used by value name.
extern PyObject *IMPORT_MODULE_FIXED(PyThreadState *tstate, PyObject *module_name, PyObject *value_name);

// Import an embedded module directly.
extern PyObject *IMPORT_EMBEDDED_MODULE(PyThreadState *tstate, char const *name);

// Execute a module, the module object is prepared empty, but with __name__.
extern PyObject *EXECUTE_EMBEDDED_MODULE(PyThreadState *tstate, PyObject *module);

// Import a name from a module.
extern PyObject *IMPORT_NAME_FROM_MODULE(PyThreadState *tstate, PyObject *module, PyObject *import_name);

// import a name from a module, potentially making an import of it if necessary.
#if PYTHON_VERSION >= 0x350
extern PyObject *IMPORT_NAME_OR_MODULE(PyThreadState *tstate, PyObject *module, PyObject *globals,
                                       PyObject *import_name, PyObject *level);
#endif

#if PYTHON_VERSION >= 0x300
extern PyObject *getImportLibBootstrapModule(void);
#endif

// Replacement for "PyImport_GetModuleDict"
NUITKA_MAY_BE_UNUSED static PyObject *Nuitka_GetSysModules(void) {
#if PYTHON_VERSION < 0x390
    return PyThreadState_GET()->interp->modules;
#elif PYTHON_VERSION < 0x3c0
    return _PyInterpreterState_GET()->modules;
#else
    return _PyInterpreterState_GET()->imports.modules;
#endif
}

// Check if a module is in "sys.modules"
NUITKA_MAY_BE_UNUSED static bool Nuitka_HasModule(PyThreadState *tstate, PyObject *module_name) {
    return DICT_HAS_ITEM(tstate, Nuitka_GetSysModules(), module_name) == 1;
}

// Replacement for "PyImport_GetModule" working across all versions and less checks.
NUITKA_MAY_BE_UNUSED static PyObject *Nuitka_GetModule(PyThreadState *tstate, PyObject *module_name) {
    return DICT_GET_ITEM1(tstate, Nuitka_GetSysModules(), module_name);
}

// Replacement for PyImport_GetModule working across all versions and less checks.
NUITKA_MAY_BE_UNUSED static PyObject *Nuitka_GetModuleString(PyThreadState *tstate, char const *module_name) {
    PyObject *module_name_object = Nuitka_String_FromString(module_name);
    PyObject *result = Nuitka_GetModule(tstate, module_name_object);
    Py_DECREF(module_name_object);

    return result;
}

// Add a module to the modules dictionary from name object
NUITKA_MAY_BE_UNUSED static bool Nuitka_SetModule(PyObject *module_name, PyObject *module) {
    CHECK_OBJECT(module_name);
    CHECK_OBJECT(module);
    assert(PyModule_Check(module));

    return DICT_SET_ITEM(Nuitka_GetSysModules(), module_name, module);
}

// Add a module to the modules dictionary from name C string
NUITKA_MAY_BE_UNUSED static bool Nuitka_SetModuleString(char const *module_name, PyObject *module) {
    PyObject *module_name_object = Nuitka_String_FromString(module_name);
    bool result = Nuitka_SetModule(module_name_object, module);
    Py_DECREF(module_name_object);

    return result;
}

// Remove a module to the modules dictionary from name object
NUITKA_MAY_BE_UNUSED static bool Nuitka_DelModule(PyThreadState *tstate, PyObject *module_name) {
    CHECK_OBJECT(module_name);

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    bool result = DICT_REMOVE_ITEM(PyImport_GetModuleDict(), module_name);

    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    return result;
}

// Remove a module to the modules dictionary from name C string
NUITKA_MAY_BE_UNUSED static bool Nuitka_DelModuleString(PyThreadState *tstate, char const *module_name) {
    PyObject *module_name_object = Nuitka_String_FromString(module_name);
    bool result = Nuitka_DelModule(tstate, module_name_object);
    Py_DECREF(module_name_object);

    return result;
}

// Wrapper for PyModule_GetFilenameObject that has no error.
NUITKA_MAY_BE_UNUSED static PyObject *Nuitka_GetFilenameObject(PyThreadState *tstate, PyObject *module) {
#if PYTHON_VERSION < 0x300
    PyObject *filename = LOOKUP_ATTRIBUTE(tstate, module, const_str_plain___file__);
#else
    PyObject *filename = PyModule_GetFilenameObject(module);
#endif

    if (unlikely(filename == NULL)) {
        CLEAR_ERROR_OCCURRED(tstate);
        filename = PyUnicode_FromString("unknown location");
    }

    return filename;
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
