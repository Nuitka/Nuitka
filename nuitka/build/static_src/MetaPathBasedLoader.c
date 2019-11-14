//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
// This implements the loading of C compiled modules and shared library
// extension modules bundled for standalone mode.

// This is achieved mainly by registered a "sys.meta_path" loader, that then
// gets asked for module names, and responds if knows about one. It's fed by
// a table created at compile time.

// The nature and use of these 2 loaded module kinds is very different, but
// having them as distinct loaders would only require to duplicate the search
// and registering of stuff.

#include <osdefs.h>

#ifdef _WIN32
#undef SEP
#define SEP '\\'
#endif

#include "nuitka/prelude.h"
// Include definition of PyInterpreterState, hidden since Python 3.8
#if PYTHON_VERSION >= 380
#define Py_BUILD_CORE
#include "internal/pycore_pystate.h"
#undef Py_BUILD_CORE
#endif
#include "nuitka/unfreezing.h"

#ifdef _WIN32
#include <windows.h>
#endif

extern char *getDirname(char *path);

extern PyTypeObject Nuitka_Loader_Type;

struct Nuitka_LoaderObject {
    /* Python object folklore: */
    PyObject_HEAD;

    /* The loader entry, to know what was loaded exactly. */
    struct Nuitka_MetaPathBasedLoaderEntry *m_loader_entry;
};

#ifdef _NUITKA_EXE
static inline bool isVerbose(void) { return Py_VerboseFlag != 0; }
#elif _NUITKA_SYSFLAG_VERBOSE
static inline bool isVerbose(void) { return true; }
#else
static inline bool isVerbose(void) { return false; }
#endif

static struct Nuitka_MetaPathBasedLoaderEntry *loader_entries = NULL;

static bool hasFrozenModule(char const *name) {
    for (struct _frozen const *p = PyImport_FrozenModules;; p++) {
        if (p->name == NULL) {
            return false;
        }

        if (strcmp(p->name, name) == 0) {
            break;
        }
    }

    return true;
}

static char *copyModulenameAsPath(char *buffer, char const *module_name) {
    while (*module_name) {
        if (*module_name == '.') {
            *buffer++ = SEP;
            module_name++;
        } else {
            *buffer++ = *module_name++;
        }
    }

    *buffer = 0;

    return buffer;
}

#ifdef _WIN32
static void wcscat_char(wchar_t *target, char c) {
    target += wcslen(target);
    char buffer_c[2] = {c};
    size_t res = mbstowcs(target, buffer_c, 2);
    assert(res == 1);
}

static void wcscat_cstr(wchar_t *target, char const *source) {
    while (*source) {
        wcscat_char(target, *source);
        source++;
    }
}

static void concatModulenameAsPathW(wchar_t *buffer, char const *module_name) {
    while (*module_name) {
        char c = *module_name++;

        if (c == '.') {
            c = SEP;
        }

        wcscat_char(buffer, c);
    }
}
#endif

extern PyObject *const_str_plain___path__;
extern PyObject *const_str_plain___file__;
extern PyObject *const_str_plain___loader__;

// TODO: This updates the wrong absolute path. We ought to change it to
// the "module_path_name" at the time of writing it, then we save a few
// bytes in the blob, and don't have to create that string here.
#ifdef _NUITKA_STANDALONE
static void patchCodeObjectPaths(PyCodeObject *code_object, PyObject *module_path) {
    code_object->co_filename = module_path;
    Py_INCREF(module_path);

    Py_ssize_t nconsts = PyTuple_GET_SIZE(code_object->co_consts);

    for (int i = 0; i < nconsts; i++) {
        PyObject *constant = PyTuple_GET_ITEM(code_object->co_consts, i);

        if (PyCode_Check(constant)) {
            patchCodeObjectPaths((PyCodeObject *)constant, module_path);
        }
    }
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_RELATIVE_PATH_FROM_NAME(char const *name, bool is_package) {
    char buffer[MAXPATHLEN + 1];

    copyModulenameAsPath(buffer, name);

    if (is_package) {
        char const sep_str[2] = {SEP, 0};
        strncat(buffer, sep_str, sizeof(buffer) - 1);
        strncat(buffer, "__init__.py", sizeof(buffer) - 1);
    } else {
        strncat(buffer, ".py", sizeof(buffer) - 1);
    }

#if PYTHON_VERSION < 300
    PyObject *module_path_entry_base = PyString_FromString(buffer);
#else
    PyObject *module_path_entry_base = PyUnicode_FromString(buffer);
#endif

    PyObject *result = MAKE_RELATIVE_PATH(module_path_entry_base);

    Py_DECREF(module_path_entry_base);

    return result;
}

static PyObject *loadModuleFromCodeObject(PyCodeObject *code_object, char const *name, bool is_package) {
    assert(code_object != NULL);

    PyObject *modules = PyImport_GetModuleDict();
    PyObject *module;

    assert(PyDict_GetItemString(modules, name) == NULL);

    module = PyModule_New(name);
    assert(module != NULL);

    int res = PyDict_SetItemString(modules, name, module);
    assert(res == 0);

    char buffer[MAXPATHLEN + 1];

    PyObject *module_path_entry = NULL;

    if (is_package) {
        copyModulenameAsPath(buffer, name);
#if PYTHON_VERSION < 300
        PyObject *module_path_entry_base = PyString_FromString(buffer);
#else
        PyObject *module_path_entry_base = PyUnicode_FromString(buffer);
#endif
        module_path_entry = MAKE_RELATIVE_PATH(module_path_entry_base);
        Py_DECREF(module_path_entry_base);

        char const sep_str[2] = {SEP, 0};
        strncat(buffer, sep_str, sizeof(buffer) - 1);
        strncat(buffer, "__init__.py", sizeof(buffer) - 1);
    } else {
        copyModulenameAsPath(buffer, name);
        strncat(buffer, ".py", sizeof(buffer) - 1);
    }

#if PYTHON_VERSION < 300
    PyObject *module_path_name = PyString_FromString(buffer);
#else
    PyObject *module_path_name = PyUnicode_FromString(buffer);
#endif

    PyObject *module_path = MAKE_RELATIVE_PATH(module_path_name);
    Py_DECREF(module_path_name);

    if (is_package) {
        /* Set __path__ properly, unlike frozen module importer does. */
        PyObject *path_list = PyList_New(1);
        if (unlikely(path_list == NULL))
            return NULL;

        res = PyList_SetItem(path_list, 0, module_path_entry);
        if (unlikely(res != 0))
            return NULL;
        Py_INCREF(module_path_entry);

        res = PyObject_SetAttr(module, const_str_plain___path__, path_list);
        if (unlikely(res != 0))
            return NULL;

        Py_DECREF(path_list);
    }

#ifdef _NUITKA_STANDALONE
    patchCodeObjectPaths(code_object, module_path);
#endif

    module = PyImport_ExecCodeModuleEx((char *)name, (PyObject *)code_object, Nuitka_String_AsString(module_path));

    Py_DECREF(module_path);

    return module;
}

static struct Nuitka_MetaPathBasedLoaderEntry *findEntry(char const *name) {
    struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;
    assert(current);

    while (current->name != NULL) {
        if (strcmp(name, current->name) == 0) {
            return current;
        }

        current++;
    }

    return NULL;
}

static char *_kwlist[] = {(char *)"fullname", (char *)"unused", NULL};

static PyObject *_path_unfreezer_find_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:find_module", _kwlist, &module_name, &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    char const *name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # considering responsibility\n", name);
    }

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(name);

    if (entry) {
        if (isVerbose()) {
            PySys_WriteStderr("import %s # claimed responsibility (compiled)\n", name);
        }

        PyObject *metapath_based_loader = (PyObject *)&Nuitka_Loader_Type;

        Py_INCREF(metapath_based_loader);
        return metapath_based_loader;
    }

    if (hasFrozenModule(name)) {
        if (isVerbose()) {
            PySys_WriteStderr("import %s # claimed responsibility (frozen)\n", name);
        }

        PyObject *metapath_based_loader = (PyObject *)&Nuitka_Loader_Type;

        Py_INCREF(metapath_based_loader);
        return metapath_based_loader;
    }

    if (isVerbose()) {
        PySys_WriteStderr("import %s # denied responsibility\n", name);
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static char *_kwlist_get_data[] = {(char *)"filename", NULL};

extern PyObject *const_str_plain_read, *const_str_plain_rb;

static PyObject *_path_unfreezer_get_data(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *filename;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:get_data", _kwlist_get_data, &filename);

    if (unlikely(res == 0)) {
        return NULL;
    }

#if PYTHON_VERSION < 300
    PyObject *data_file = BUILTIN_OPEN(filename, const_str_plain_rb, NULL);
#else
    PyObject *data_file = BUILTIN_OPEN(filename, const_str_plain_rb, NULL, NULL, NULL, NULL, NULL, NULL);
#endif
    if (unlikely(data_file == NULL)) {
        // TODO: Issue a runtime warning maybe.
        return NULL;
    }

    PyObject *read_method = PyObject_GetAttr(data_file, const_str_plain_read);
    Py_DECREF(data_file);

    if (unlikely(read_method == NULL)) {
        return NULL;
    }

    PyObject *result = CALL_FUNCTION_NO_ARGS(read_method);
    Py_DECREF(read_method);
    return result;
}

#ifdef _NUITKA_STANDALONE

#if PYTHON_VERSION < 300
typedef void (*entrypoint_t)(void);
#else
typedef PyObject *(*entrypoint_t)(void);
#endif

#ifndef _WIN32
// Shared libraries loading.
#include <dlfcn.h>
#endif

#if PYTHON_VERSION >= 350
static PyObject *createModuleSpec(PyObject *module_name);
#endif

#ifdef _WIN32
PyObject *callIntoShlibModule(const char *full_name, const wchar_t *filename) {
#else
PyObject *callIntoShlibModule(const char *full_name, const char *filename) {
#endif
    // Determine the package name and basename of the module to load.
    char const *dot = strrchr(full_name, '.');
    char const *name;
    char const *package;

    if (dot == NULL) {
        package = NULL;
        name = full_name;
    } else {
        package = (char *)full_name;
        name = dot + 1;
    }

    char entry_function_name[1024];
    snprintf(entry_function_name, sizeof(entry_function_name),
#if PYTHON_VERSION < 300
             "init%s",
#else
             "PyInit_%s",
#endif
             name);

#ifdef _WIN32
    if (isVerbose()) {
        PySys_WriteStderr("import %s # LoadLibraryExW(\"%S\");\n", full_name, filename);
    }

    unsigned int old_mode = SetErrorMode(SEM_FAILCRITICALERRORS);

    HINSTANCE hDLL = LoadLibraryExW(filename, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    SetErrorMode(old_mode);

    if (unlikely(hDLL == NULL)) {
        char buffer[1024];
        unsigned int error_code;

        char error_message[1024];
        int size;

        error_code = GetLastError();

        size = FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL, error_code, 0,
                             (LPTSTR)error_message, sizeof(error_message), NULL);

        // Report either way even if failed to get error message.
        if (size == 0) {
            PyOS_snprintf(buffer, sizeof(buffer), "LoadLibraryEx '%S' failed with error code %d", filename, error_code);
        } else {
            // Strip trailing newline.
            if (size >= 2 && error_message[size - 2] == '\r' && error_message[size - 1] == '\n') {
                size -= 2;
                error_message[size] = '\0';
            }
            PyOS_snprintf(buffer, sizeof(buffer), "LoadLibraryEx '%S' failed: %s", filename, error_message);
        }

        PyErr_SetString(PyExc_ImportError, buffer);
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)GetProcAddress(hDLL, entry_function_name);
#else
    int dlopenflags = PyThreadState_GET()->interp->dlopenflags;

    if (isVerbose()) {
        PySys_WriteStderr("import %s # dlopen(\"%s\", %x);\n", full_name, filename, dlopenflags);
    }

    void *handle = dlopen(filename, dlopenflags);

    if (unlikely(handle == NULL)) {
        const char *error = dlerror();

        if (unlikely(error == NULL)) {
            error = "unknown dlopen() error";
        }

        PyErr_SetString(PyExc_ImportError, error);
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)dlsym(handle, entry_function_name);

#endif
    assert(entrypoint);

#if PYTHON_VERSION < 370
    char *old_context = _Py_PackageContext;
#else
    char const *old_context = _Py_PackageContext;
#endif

    _Py_PackageContext = (char *)package;

    // Finally call into the DLL.
#if PYTHON_VERSION < 300
    (*entrypoint)();
#else
    PyObject *module = (*entrypoint)();
#endif

    _Py_PackageContext = old_context;

#if PYTHON_VERSION < 300
    PyObject *module = PyDict_GetItemString(PyImport_GetModuleDict(), full_name);
#endif

    if (unlikely(module == NULL)) {
        if (!ERROR_OCCURRED()) {
            PyErr_Format(PyExc_SystemError, "dynamic module '%s' not initialized properly", full_name);
        }

        return NULL;
    }

#if PYTHON_VERSION >= 300
#if PYTHON_VERSION >= 350
    PyModuleDef *def;

    if (Py_TYPE(module) == &PyModuleDef_Type) {
        def = (PyModuleDef *)module;

        PyObject *spec = createModuleSpec(PyUnicode_FromString(full_name));
        module = PyModule_FromDefAndSpec(def, spec);
        Py_DECREF(spec);

        if (unlikely(module == NULL)) {
            PyErr_Format(PyExc_SystemError, "dynamic module '%s' not initialized properly from def", full_name);

            return NULL;
        }

        assert(PyModule_Check(module));

        int res = PyModule_ExecDef(module, def);

        if (unlikely(res == -1)) {
            return NULL;
        }

        PyDict_SetItemString(PyImport_GetModuleDict(), full_name, module);

        return module;
    } else {
        def = PyModule_GetDef(module);
    }

    if (likely(def != NULL)) {
        def->m_base.m_init = entrypoint;
    }
#else
    PyModuleDef *def = PyModule_GetDef(module);

    if (unlikely(def == NULL)) {
        PyErr_Format(PyExc_SystemError, "initialization of %s did not return an extension module", filename);

        return NULL;
    }

    def->m_base.m_init = entrypoint;
#endif

#endif

    // Set filename attribute
#ifdef _WIN32
    int res = PyModule_AddObject(module, "__file__", PyUnicode_FromWideChar(filename, -1));
#else
    int res = PyModule_AddObject(module, "__file__", PyUnicode_FromString(filename));
#endif
    if (unlikely(res < 0)) {
        // Might be refuted, which wouldn't be harmful.
        CLEAR_ERROR_OCCURRED();
    }

    // Call the standard import fix-ups for extension modules. Their interface
    // changed over releases.
#if PYTHON_VERSION < 300
    PyObject *res2 = _PyImport_FixupExtension((char *)full_name, (char *)filename);

    if (unlikely(res2 == NULL)) {
        return NULL;
    }
#else
    PyObject *full_name_obj = PyUnicode_FromString(full_name);
    CHECK_OBJECT(full_name_obj);
#ifdef _WIN32
    PyObject *filename_obj = PyUnicode_FromWideChar(filename, -1);
#else
    PyObject *filename_obj = PyUnicode_FromString(filename);
#endif
    CHECK_OBJECT(filename_obj);

    res = _PyImport_FixupExtensionObject(module, full_name_obj, filename_obj
#if PYTHON_VERSION >= 370
                                         ,
                                         PyImport_GetModuleDict()
#endif

    );

    Py_DECREF(full_name_obj);
    Py_DECREF(filename_obj);

    if (unlikely(res == -1)) {
        return NULL;
    }
#endif

    return module;
}

#endif

static bool loadTriggeredModule(char const *name, char const *trigger_name) {
    char trigger_module_name[2048];

    copyStringSafe(trigger_module_name, name, sizeof(trigger_module_name));
    appendStringSafe(trigger_module_name, trigger_name, sizeof(trigger_module_name));

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(trigger_module_name);

    if (entry != NULL) {
        if (isVerbose()) {
            PySys_WriteStderr("Loading %s\n", trigger_module_name);
        }

        entry->python_initfunc(trigger_module_name);

        if (unlikely(ERROR_OCCURRED())) {
            return false;
        }
    }

    return true;
}

#if PYTHON_VERSION >= 340
extern PyObject *const_str_plain___spec__;
extern PyObject *const_str_plain__initializing;

static void _fixupSpecAttribute(PyObject *module) {
    PyObject *spec_value = LOOKUP_ATTRIBUTE(module, const_str_plain___spec__);

    if (spec_value && spec_value != Py_None) {
        if (PyObject_HasAttr(spec_value, const_str_plain__initializing)) {
            SET_ATTRIBUTE(spec_value, const_str_plain__initializing, Py_False);
        }
    }
}
#endif

static PyObject *Nuitka_Loader_New(struct Nuitka_MetaPathBasedLoaderEntry *entry);

static PyObject *loadModule(PyObject *module_name, struct Nuitka_MetaPathBasedLoaderEntry *entry) {
#ifdef _NUITKA_STANDALONE
    if ((entry->flags & NUITKA_SHLIB_FLAG) != 0) {
        // Append the the entry name from full path module name with dots,
        // and translate these into directory separators.
#ifdef _WIN32
        wchar_t filename[MAXPATHLEN + 1];

        wcscpy(filename, getBinaryDirectoryWideChars());
        wcscat_char(filename, SEP);
        concatModulenameAsPathW(filename, entry->name);
        wcscat_cstr(filename, ".pyd");
#else
        char filename[MAXPATHLEN + 1];

        strcpy(filename, getBinaryDirectoryHostEncoded());
        char const sep_str[2] = {SEP, 0};
        strcat(filename, sep_str);
        copyModulenameAsPath(filename + strlen(filename), entry->name);
        strcat(filename, ".so");

#endif
        callIntoShlibModule(entry->name, filename);
    } else
#endif
        if ((entry->flags & NUITKA_BYTECODE_FLAG) != 0) {
        PyCodeObject *code_object = (PyCodeObject *)PyMarshal_ReadObjectFromString(
            (char *)&constant_bin[entry->bytecode_start], entry->bytecode_size);

        // TODO: Probably a bit harsh reaction.
        if (unlikely(code_object == NULL)) {
            PyErr_Print();
            abort();
        }

        return loadModuleFromCodeObject(code_object, entry->name, (entry->flags & NUITKA_PACKAGE_FLAG) != 0);
    } else {
        assert((entry->flags & NUITKA_SHLIB_FLAG) == 0);
        assert(entry->python_initfunc);

        // Run the compiled module code, we get the module returned.
        PyObject *result = entry->python_initfunc(entry->name);

        PyObject *exception_type = NULL;
        PyObject *exception_value = NULL;
        PyTracebackObject *exception_tb = NULL;

        FETCH_ERROR_OCCURRED(&exception_type, &exception_value, &exception_tb);

#if PYTHON_VERSION >= 340
        if (result != NULL) {
            _fixupSpecAttribute(result);
        }
#endif

        // For use by "pkgutil.walk_modules" add the runtime path to the
        // "sys.path_importer_cache" dictionary.
        if (result != NULL && entry->flags & NUITKA_PACKAGE_FLAG) {
            PyObject *path_value = LOOKUP_ATTRIBUTE(result, const_str_plain___path__);

            if (path_value && PyList_CheckExact(path_value) && PyList_Size(path_value) > 0) {
                PyObject *path_element = PyList_GetItem(path_value, 0);
                CHECK_OBJECT(path_value);

                PyObject *path_importer_cache = PySys_GetObject((char *)"path_importer_cache");
                CHECK_OBJECT(path_importer_cache);

                PyObject *loader = Nuitka_Loader_New(entry);
                CHECK_OBJECT(loader);

                if (loader) {
                    int res = PyDict_SetItem(path_importer_cache, path_element, loader);
                    assert(res == 0);
                }
            }
        }

        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);
    }

    if (unlikely(ERROR_OCCURRED())) {
        return NULL;
    }

    if (isVerbose()) {
        PySys_WriteStderr("Loaded %s\n", entry->name);
    }

    return LOOKUP_SUBSCRIPT(PyImport_GetModuleDict(), module_name);
}

// Note: This may become an entry point for hard coded imports of compiled
// stuff.
PyObject *IMPORT_EMBEDDED_MODULE(PyObject *module_name, char const *name) {
    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(name);
    bool frozen_import = entry == NULL && hasFrozenModule(name);

    if (entry != NULL || frozen_import) {
        // Execute the "preLoad" code produced for the module potentially. This
        // is from plug-ins typically, that want to modify things for the the
        // module before loading, to e.g. set a plug-in path, or do some monkey
        // patching in order to make things compatible.
        if (loadTriggeredModule(name, "-preLoad") == false) {
            return NULL;
        }
    }

    PyObject *result = NULL;

    if (entry != NULL) {
        result = loadModule(module_name, entry);

        if (result == NULL) {
            return NULL;
        }
    }

    if (frozen_import) {
        int res = PyImport_ImportFrozenModule((char *)name);

        if (unlikely(res == -1)) {
            return NULL;
        }

        if (res == 1) {
            result = LOOKUP_SUBSCRIPT(PyImport_GetModuleDict(), module_name);
        }
    }

    if (result != NULL) {
        // Execute the "postLoad" code produced for the module potentially. This
        // is from plug-ins typically, that want to modify the module immediately
        // after loading, to e.g. set a plug-in path, or do some monkey patching
        // in order to make things compatible.
        if (loadTriggeredModule(name, "-postLoad") == false) {
            return NULL;
        }

        return result;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *_path_unfreezer_load_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:load_module", _kwlist, &module_name, &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    assert(module_name);
    assert(Nuitka_String_Check(module_name));

    char const *name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("Loading %s\n", name);
    }

    return IMPORT_EMBEDDED_MODULE(module_name, name);
}

static char *_kwlist_is_package[] = {(char *)"fullname", NULL};

static PyObject *_path_unfreezer_is_package(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:is_package", _kwlist_is_package, &module_name);

    if (unlikely(res == 0)) {
        return NULL;
    }

    assert(module_name);
    assert(Nuitka_String_Check(module_name));

    char const *name = Nuitka_String_AsString(module_name);

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(name);

    PyObject *result;

    if (entry) {
        result = BOOL_FROM((entry->flags & NUITKA_PACKAGE_FLAG) != 0);
    } else {
        // TODO: Maybe needs to be an exception.
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

#if PYTHON_VERSION >= 340
static PyObject *_path_unfreezer_repr_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:module_repr", _kwlist, &module, &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    return PyUnicode_FromFormat("<module '%s' from %R>", PyModule_GetName(module), PyModule_GetFilenameObject(module));
}

static PyObject *createModuleSpec(PyObject *module_name) {
    assert(module_name);
    assert(Nuitka_String_Check(module_name));

    char const *name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # considering responsibility\n", name);
    }

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(name);

    if (entry == NULL) {
        if (isVerbose()) {
            PySys_WriteStderr("import %s # denied responsibility\n", name);
        }

        Py_INCREF(Py_None);
        return Py_None;
    }

    static PyObject *importlib = NULL;
    if (importlib == NULL) {
        importlib = PyImport_ImportModule("importlib._bootstrap");
    }

    if (unlikely(importlib == NULL)) {
        return NULL;
    }

    static PyObject *module_spec_class = NULL;
    if (module_spec_class == NULL) {
        module_spec_class = PyObject_GetAttrString(importlib, "ModuleSpec");
    }

    if (unlikely(module_spec_class == NULL)) {
        return NULL;
    }

    if (isVerbose()) {
        PySys_WriteStderr("import %s # claimed responsibility (compiled)\n", name);
    }

    PyObject *result =
        PyObject_CallFunctionObjArgs(module_spec_class, module_name, (PyObject *)&Nuitka_Loader_Type, NULL);

    return result;
}

static char *_kwlist_find_spec[] = {(char *)"fullname", (char *)"is_package", (char *)"path", NULL};

static PyObject *_path_unfreezer_find_spec(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused1; // We ignore "is_package"
    PyObject *unused2; // We ignore "path"

    int res =
        PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:find_spec", _kwlist_find_spec, &module_name, &unused1, &unused2);

    if (unlikely(res == 0)) {
        return NULL;
    }

    return createModuleSpec(module_name);
}

#endif

static char *_kwlist_iter_modules[] = {(char *)"package", NULL};

extern PyObject *const_str_plain_name;

static PyObject *_path_unfreezer_iter_modules(struct Nuitka_LoaderObject *self, PyObject *args, PyObject *kwds) {
    PyObject *prefix;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:iter_modules", _kwlist_iter_modules, &prefix);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *result = PyList_New(0);

    struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;
    assert(current);

    char const *s = self->m_loader_entry->name;

    while (current->name != NULL) {
        int c = strncmp(s, current->name, strlen(s));

        if (c != 0) {
            current++;
            continue;
        }

        if (current->name[strlen(s)] == 0) {
            current++;
            continue;
        }

        char const *sub = strchr(current->name + strlen(s) + 1, '.');

        if (sub != NULL) {
            current++;
            continue;
        }

        PyObject *r = PyTuple_New(2);

#if PYTHON_VERSION < 300
        PyObject *name = PyString_FromString(current->name + strlen(s) + 1);
#else
        PyObject *name = PyUnicode_FromString(current->name + strlen(s) + 1);
#endif

        if (CHECK_IF_TRUE(prefix)) {
            PyObject *old = name;
            name = PyUnicode_Concat(prefix, name);
            Py_DECREF(old);
        }

        PyTuple_SET_ITEM(r, 0, name);
        PyTuple_SetItem(r, 1, BOOL_FROM((current->flags & NUITKA_PACKAGE_FLAG) != 0));

        PyList_Append(result, r);
        Py_DECREF(r);

        current++;
    }

    return result;
}

static PyMethodDef Nuitka_Loader_methods[] = {
    {"iter_modules", (PyCFunction)_path_unfreezer_iter_modules, METH_VARARGS | METH_KEYWORDS, NULL},
    {"get_data", (PyCFunction)_path_unfreezer_get_data, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"find_module", (PyCFunction)_path_unfreezer_find_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"load_module", (PyCFunction)_path_unfreezer_load_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"is_package", (PyCFunction)_path_unfreezer_is_package, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#if PYTHON_VERSION >= 340
    {"module_repr", (PyCFunction)_path_unfreezer_repr_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"find_spec", (PyCFunction)_path_unfreezer_find_spec, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#endif
    {NULL, NULL}
};

static PyObject *Nuitka_Loader_tp_repr(struct Nuitka_LoaderObject *loader) {
#if PYTHON_VERSION < 300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
        "<nuitka_module_loader for '%s'>", loader->m_loader_entry->name);
}

#include "nuitka/freelists.h"

// TODO: A freelist is not the right thing for those, they are probably living forever, but it's
// no big harm too, but make it small.

#define MAX_LOADER_FREE_LIST_COUNT 10
static struct Nuitka_LoaderObject *free_list_loaders = NULL;
static int free_list_loaders_count = 0;

static void Nuitka_Loader_tp_dealloc(struct Nuitka_LoaderObject *loader) {
    Nuitka_GC_UnTrack(loader);

    releaseToFreeList(free_list_loaders, loader, MAX_LOADER_FREE_LIST_COUNT);
}

static int Nuitka_Loader_tp_traverse(struct Nuitka_LoaderObject *loader) { return 0; }

PyTypeObject Nuitka_Loader_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "nuitka_module_loader",
    sizeof(struct Nuitka_LoaderObject),      /* tp_basicsize */
    0,                                       /* tp_itemsize */
    (destructor)Nuitka_Loader_tp_dealloc,    /* tp_dealloc */
    0,                                       /* tp_print */
    0,                                       /* tp_getattr */
    0,                                       /* tp_setattr */
    0,                                       /* tp_reserved */
    (reprfunc)Nuitka_Loader_tp_repr,         /* tp_repr */
    0,                                       /* tp_as_number */
    0,                                       /* tp_as_sequence */
    0,                                       /* tp_as_mapping */
    0,                                       /* tp_hash */
    0,                                       /* tp_call */
    0,                                       /* tp_str */
    PyObject_GenericGetAttr,                 /* tp_getattro */
    0,                                       /* tp_setattro */
    0,                                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, /* tp_flags */
    0,                                       /* tp_doc */
    (traverseproc)Nuitka_Loader_tp_traverse, /* tp_traverse */
    0,                                       /* tp_clear */
    0,                                       /* tp_richcompare */
    0,                                       /* tp_weaklistoffset */
    0,                                       /* tp_iter */
    0,                                       /* tp_iternext */
    Nuitka_Loader_methods,                   /* tp_methods */
    0,                                       /* tp_members */
    0,                                       /* tp_getset */
};

static PyObject *Nuitka_Loader_New(struct Nuitka_MetaPathBasedLoaderEntry *entry) {
    struct Nuitka_LoaderObject *result;

    allocateFromFreeListFixed(free_list_loaders, struct Nuitka_LoaderObject, Nuitka_Loader_Type);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;

    return (PyObject *)result;
}

void registerMetaPathBasedUnfreezer(struct Nuitka_MetaPathBasedLoaderEntry *_loader_entries) {
    // Do it only once.
    if (loader_entries) {
        assert(_loader_entries == loader_entries);

        return;
    }

    if (isVerbose()) {
        PySys_WriteStderr("Setup nuitka compiled module/bytecode/shlib importer.\n");
    }

#ifdef _NUITKA_MODULE
    if (_Py_PackageContext != NULL) {
        char const *last_dot = strrchr(_Py_PackageContext, '.');

        if (last_dot != NULL) {
            struct Nuitka_MetaPathBasedLoaderEntry *current = _loader_entries;
            assert(current);

            while (current->name != NULL) {
                char name[2048];

                if (strcmp(last_dot + 1, current->name) == 0) {
                    copyStringSafeN(name, _Py_PackageContext, last_dot - _Py_PackageContext + 1, sizeof(name));
                    appendStringSafe(name, current->name, sizeof(name));

                    current->name = strdup(name);
                } else if (strncmp(last_dot + 1, current->name, strlen(last_dot + 1)) == 0 &&
                           current->name[strlen(last_dot + 1)] == '.') {
                    copyStringSafeN(name, _Py_PackageContext, last_dot - _Py_PackageContext + 1, sizeof(name));
                    appendStringSafe(name, current->name, sizeof(name));

                    current->name = strdup(name);
                }

                current++;
            }
        }
    }
#endif

    loader_entries = _loader_entries;

    PyType_Ready(&Nuitka_Loader_Type);

    // Register it as a meta path loader.
    int res = PyList_Insert(PySys_GetObject((char *)"meta_path"),
#if PYTHON_VERSION < 300
                            0,
#else
                            2,
#endif

                            (PyObject *)&Nuitka_Loader_Type);
    assert(res == 0);
}

#if defined(_NUITKA_STANDALONE) || _NUITKA_FROZEN > 0

extern PyObject *const_str_plain___file__;

// This is called for each module imported early on.
void setEarlyFrozenModulesFileAttribute(void) {
    PyObject *sys_modules = PyImport_GetModuleDict();
    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while (PyDict_Next(sys_modules, &ppos, &key, &value)) {
        if (key != NULL && value != NULL && PyModule_Check(value)) {
            if (PyObject_HasAttr(value, const_str_plain___file__)) {
                bool is_package = PyObject_HasAttr(value, const_str_plain___path__) == 1;

                PyObject *file_value = MAKE_RELATIVE_PATH_FROM_NAME(Nuitka_String_AsString(key), is_package);
                PyObject_SetAttr(value, const_str_plain___file__, file_value);
                Py_DECREF(file_value);
            }
        }
    }

    assert(!ERROR_OCCURRED());
}

#endif
