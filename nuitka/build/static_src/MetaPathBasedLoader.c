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
#include "nuitka/unfreezing.h"

#ifdef _WIN32
#include <windows.h>
#endif

extern PyTypeObject Nuitka_Loader_Type;

struct Nuitka_LoaderObject {
    /* Python object folklore: */
    PyObject_HEAD;

    /* The loader entry, to know what was loaded exactly. */
    struct Nuitka_MetaPathBasedLoaderEntry const *m_loader_entry;
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

static char *appendModulenameAsPath(char *buffer, char const *module_name, size_t buffer_size) {
    // Skip to the end
    while (*buffer != 0) {
        buffer++;
    }

    while (*module_name) {
        if (buffer_size < 1) {
            abort();
        }

        if (*module_name == '.') {
            *buffer++ = SEP;
            module_name++;
        } else {
            *buffer++ = *module_name++;
        }

        buffer_size -= 1;
    }

    *buffer = 0;

    return buffer;
}

#if defined(_WIN32) && defined(_NUITKA_STANDALONE)

static void appendModulenameAsPathW(wchar_t *buffer, char const *module_name, size_t buffer_size) {
    // Skip to the end
    while (*buffer != 0) {
        buffer++;
    }

    while (*module_name) {
        char c = *module_name++;

        if (c == '.') {
            c = SEP;
        }

        appendCharSafeW(buffer, c, buffer_size);
    }
}
#endif

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
    char buffer[MAXPATHLEN + 1] = {0};

    appendModulenameAsPath(buffer, name, sizeof(buffer));

    if (is_package) {
        appendCharSafe(buffer, SEP, sizeof(buffer));
        appendStringSafe(buffer, "__init__.py", sizeof(buffer));
    } else {
        appendStringSafe(buffer, ".py", sizeof(buffer));
    }

    PyObject *module_path_entry_base = Nuitka_String_FromString(buffer);

    PyObject *result = MAKE_RELATIVE_PATH(module_path_entry_base);

    Py_DECREF(module_path_entry_base);

    return result;
}

static PyObject *loadModuleFromCodeObject(PyObject *module, PyCodeObject *code_object, char const *name,
                                          bool is_package) {
    assert(code_object != NULL);

    // TODO: This should not actually trigger, but it does.
    // assert(PyDict_GetItemString(modules, name) == NULL);
    bool b_res = Nuitka_SetModuleString(name, module);
    assert(b_res != false);

    char buffer[MAXPATHLEN + 1] = {0};

    PyObject *module_path_entry = NULL;

    if (is_package) {
        appendModulenameAsPath(buffer, name, sizeof(buffer));
        PyObject *module_path_entry_base = Nuitka_String_FromString(buffer);

        module_path_entry = MAKE_RELATIVE_PATH(module_path_entry_base);
        Py_DECREF(module_path_entry_base);

        appendCharSafe(buffer, SEP, sizeof(buffer));
        appendStringSafe(buffer, "__init__.py", sizeof(buffer));
    } else {
        appendModulenameAsPath(buffer, name, sizeof(buffer));
        appendStringSafe(buffer, ".py", sizeof(buffer));
    }

    PyObject *module_path_name = Nuitka_String_FromString(buffer);

    PyObject *module_path = MAKE_RELATIVE_PATH(module_path_name);
    Py_DECREF(module_path_name);

    if (is_package) {
        /* Set __path__ properly, unlike frozen module importer does. */
        PyObject *path_list = PyList_New(1);
        if (unlikely(path_list == NULL))
            return NULL;

        int res = PyList_SetItem(path_list, 0, module_path_entry);
        if (unlikely(res != 0)) {
            return NULL;
        }
        Py_INCREF(module_path_entry);

        res = PyObject_SetAttr(module, const_str_plain___path__, path_list);
        if (unlikely(res != 0)) {
            return NULL;
        }

        Py_DECREF(path_list);

        PyObject *module_name = PyObject_GetAttr(module, const_str_plain___name__);
        CHECK_OBJECT(module_name);

        res = PyObject_SetAttr(module, const_str_plain___package__, module_name);

        if (unlikely(res != 0)) {
            return NULL;
        }
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
        if ((current->flags & NUITKA_TRANSLATED_FLAG) != 0) {
            current->name = UNTRANSLATE(current->name);
            current->flags -= NUITKA_TRANSLATED_FLAG;
        }

        if (strcmp(name, current->name) == 0) {
            return current;
        }

        current++;
    }

    return NULL;
}

#ifndef _NUITKA_STANDALONE
static struct Nuitka_MetaPathBasedLoaderEntry *findContainingPackageEntry(char const *name) {
    struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;

    // Consider the package name of the searched entry.
    char const *package_name_end = strrchr(name, '.');
    if (package_name_end == NULL) {
        return NULL;
    }

    size_t length = package_name_end - name;

    while (current->name != NULL) {
        if ((current->flags & NUITKA_TRANSLATED_FLAG) != 0) {
            current->name = UNTRANSLATE(current->name);
            current->flags -= NUITKA_TRANSLATED_FLAG;
        }

        if ((current->flags & NUITKA_PACKAGE_FLAG) != 0) {
            if (strlen(current->name) == length && strncmp(name, current->name, length) == 0) {
                return current;
            }
        }

        current++;
    }

    return NULL;
}

static PyObject *getFileList(PyObject *dirname) {
    static PyObject *listdir_func = NULL;

    if (listdir_func == NULL) {
        PyObject *os_module = PyImport_ImportModule("os");
        listdir_func = PyObject_GetAttrString(os_module, "listdir");
    }

    if (unlikely(listdir_func == NULL)) {
        return NULL;
    }

    return CALL_FUNCTION_WITH_SINGLE_ARG(listdir_func, dirname);
}

#if PYTHON_VERSION < 0x300
static PyObject *_getImportingSuffixesByPriority(int kind) {
    static PyObject *result = NULL;

    if (result == NULL) {
        result = PyList_New(0);

        PyObject *imp_module = PyImport_ImportModule("imp");
        PyObject *get_suffixes_func = PyObject_GetAttrString(imp_module, "get_suffixes");

        PyObject *suffix_list = CALL_FUNCTION_NO_ARGS(get_suffixes_func);

        for (int i = 0; i < PyList_GET_SIZE(suffix_list); i++) {
            PyObject *module_kind = PyTuple_GET_ITEM(PyList_GET_ITEM(suffix_list, i), 2);

            if (PyInt_AsLong(module_kind) == kind) {
                LIST_APPEND0(result, PyTuple_GET_ITEM(PyList_GET_ITEM(suffix_list, i), 0));
            }
        }

        Py_DECREF(suffix_list);
    }

    return result;
}
#endif

static PyObject *getExtensionModuleSuffixesByPriority() {
    static PyObject *result = NULL;

    if (result == NULL) {
#if PYTHON_VERSION < 0x300
        result = _getImportingSuffixesByPriority(3);
#else
        static PyObject *machinery_module = NULL;

        if (machinery_module == NULL) {
            machinery_module = PyImport_ImportModule("importlib.machinery");
        }

        result = PyObject_GetAttrString(machinery_module, "EXTENSION_SUFFIXES");
#endif
    }

    CHECK_OBJECT(result);
    return result;
}

static PyObject *installed_extension_modules = NULL;

static bool scanModuleInPackagePath(PyObject *module_name, char const *parent_module_name) {
    PyObject *sys_modules = PyImport_GetModuleDict();

    PyObject *parent_module = PyDict_GetItemString(sys_modules, parent_module_name);
    CHECK_OBJECT(parent_module);

    PyObject *parent_path = PyObject_GetAttr(parent_module, const_str_plain___path__);

    // Accept that it might be deleted.
    if (parent_path == NULL || !PyList_Check(parent_path)) {
        return false;
    }

    PyObject *candidates = PyList_New(0);

    // Search only relative to the parent name of course.
    char const *module_relname_str = Nuitka_String_AsString(module_name) + strlen(parent_module_name) + 1;

    Py_ssize_t parent_path_size = PyList_GET_SIZE(parent_path);

    for (Py_ssize_t i = 0; i < parent_path_size; i += 1) {
        PyObject *path_element = PyList_GET_ITEM(parent_path, i);

        PyObject *filenames_list = getFileList(path_element);

        if (filenames_list == NULL) {
            DROP_ERROR_OCCURRED();
            continue;
        }

        Py_ssize_t filenames_list_size = PyList_GET_SIZE(filenames_list);

        for (Py_ssize_t j = 0; j < filenames_list_size; j += 1) {
            PyObject *filename = PyList_GET_ITEM(filenames_list, j);

            if (Nuitka_String_CheckExact(filename)) {
                char const *filename_str = Nuitka_String_AsString(filename);

                if (strncmp(filename_str, module_relname_str, strlen(module_relname_str)) == 0 &&
                    filename_str[strlen(module_relname_str)] == '.') {
                    LIST_APPEND1(candidates, PyTuple_Pack(2, path_element, filename));
                }
            }
        }
    }

#if 0
    PRINT_STRING("CANDIDATES:");
    PRINT_STRING(Nuitka_String_AsString(module_name));
    PRINT_STRING(module_relname_str);
    PRINT_ITEM(candidates);
    PRINT_NEW_LINE();
#endif

    // Look up C-extension suffixes, these are used with highest priority.
    PyObject *suffix_list = getExtensionModuleSuffixesByPriority();

    bool result = false;

    for (Py_ssize_t i = 0; i < PyList_GET_SIZE(suffix_list); i += 1) {
        PyObject *suffix = PyList_GET_ITEM(suffix_list, i);

        char const *suffix_str = Nuitka_String_AsString(suffix);

        for (Py_ssize_t j = 0; j < PyList_GET_SIZE(candidates); j += 1) {
            PyObject *entry = PyList_GET_ITEM(candidates, j);

            PyObject *directory = PyTuple_GET_ITEM(entry, 0);
            PyObject *candidate = PyTuple_GET_ITEM(entry, 1);

            char const *candidate_str = Nuitka_String_AsString(candidate);

            if (strcmp(suffix_str, candidate_str + strlen(module_relname_str)) == 0) {
                PyObject *fullpath = JOIN_PATH2(directory, candidate);

                if (installed_extension_modules == NULL) {
                    installed_extension_modules = PyDict_New();
                }

// Force path to unicode, to have easier consumption, as we need a wchar_t or char *
// from it later, and we don't want to test there.
#if PYTHON_VERSION < 0x300 && defined(_WIN32)
                PyObject *tmp = PyUnicode_FromObject(fullpath);
                Py_DECREF(fullpath);
                fullpath = tmp;
#endif

                DICT_SET_ITEM(installed_extension_modules, module_name, fullpath);

                result = true;
                break;
            }
        }
    }

    Py_DECREF(candidates);

    return result;
}

#ifdef _WIN32
static PyObject *callIntoShlibModule(char const *full_name, const wchar_t *filename);
#else
static PyObject *callIntoShlibModule(char const *full_name, const char *filename);
#endif

static PyObject *callIntoInstalledShlibModule(PyObject *module_name, PyObject *extension_module_filename) {
#if _WIN32
    // We can rely on unicode object to be there in case of Windows, to have an easier time to
    // create the string needed.
    assert(PyUnicode_CheckExact(extension_module_filename));

#if PYTHON_VERSION < 0x300
    wchar_t const *extension_module_filename_str = PyUnicode_AS_UNICODE(extension_module_filename);
#else
    wchar_t const *extension_module_filename_str = PyUnicode_AsWideCharString(extension_module_filename, NULL);
#endif
#else
    char const *extension_module_filename_str = Nuitka_String_AsString(extension_module_filename);
#endif

    return callIntoShlibModule(Nuitka_String_AsString(module_name), extension_module_filename_str);
}

#endif

static char *_kwlist[] = {(char *)"fullname", (char *)"unused", NULL};

static PyObject *_path_unfreezer_find_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:find_module", (char **)_kwlist, &module_name, &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    char const *name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # considering responsibility (find_module)\n", name);
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

#ifndef _NUITKA_STANDALONE
    entry = findContainingPackageEntry(name);

    if (entry != NULL) {
        bool result = scanModuleInPackagePath(module_name, entry->name);

        if (result) {
            PyObject *metapath_based_loader = (PyObject *)&Nuitka_Loader_Type;

            Py_INCREF(metapath_based_loader);
            return metapath_based_loader;
        }
    }
#endif

    if (isVerbose()) {
        PySys_WriteStderr("import %s # denied responsibility\n", name);
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static char const *_kwlist_get_data[] = {"filename", NULL};

static PyObject *_path_unfreezer_get_data(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *filename;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:get_data", (char **)_kwlist_get_data, &filename);

    if (unlikely(res == 0)) {
        return NULL;
    }

#if PYTHON_VERSION < 0x300
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

#if PYTHON_VERSION < 0x300
typedef void (*entrypoint_t)(void);
#else
typedef PyObject *(*entrypoint_t)(void);
#endif

#ifndef _WIN32
// Shared libraries loading.
#include <dlfcn.h>
#endif

#if PYTHON_VERSION >= 0x350
static PyObject *createModuleSpec(PyObject *module_name, bool is_package);
#endif

#ifdef _WIN32
static PyObject *callIntoShlibModule(char const *full_name, const wchar_t *filename) {
#else
static PyObject *callIntoShlibModule(char const *full_name, const char *filename) {
#endif
    // Determine the package name and basename of the module to load.
    char const *dot = strrchr(full_name, '.');
    char const *name;
    char const *package;

    if (dot == NULL) {
        package = NULL;
        name = full_name;
    } else {
        // The extension modules do expect it to be full name in context.
        package = (char *)full_name;
        name = dot + 1;
    }

    char entry_function_name[1024];
    snprintf(entry_function_name, sizeof(entry_function_name),
#if PYTHON_VERSION < 0x300
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

        char error_message[1024];
        int size;

        unsigned int error_code = GetLastError();

        size = FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL, error_code, 0,
                             (LPTSTR)error_message, sizeof(error_message), NULL);

        // Report either way even if failed to get error message.
        if (size == 0) {
            PyOS_snprintf(buffer, sizeof(buffer), "LoadLibraryExW '%S' failed with error code %d", filename,
                          error_code);
        } else {
            // Strip trailing newline.
            if (size >= 2 && error_message[size - 2] == '\r' && error_message[size - 1] == '\n') {
                size -= 2;
                error_message[size] = '\0';
            }
            PyOS_snprintf(buffer, sizeof(buffer), "LoadLibraryExW '%S' failed: %s", filename, error_message);
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ImportError, buffer);
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)GetProcAddress(hDLL, entry_function_name);
#else
    // This code would work for all versions, we are avoiding access to interpreter
    // structure internals of 3.8 or higher.
    static PyObject *dlopenflags_object = NULL;
    if (dlopenflags_object == NULL) {
        dlopenflags_object = CALL_FUNCTION_NO_ARGS(PySys_GetObject((char *)"getdlopenflags"));
    }
    int dlopenflags = PyInt_AsLong(dlopenflags_object);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # dlopen(\"%s\", %x);\n", full_name, filename, dlopenflags);
    }

    void *handle = dlopen(filename, dlopenflags);

    if (unlikely(handle == NULL)) {
        const char *error = dlerror();

        if (unlikely(error == NULL)) {
            error = "unknown dlopen() error";
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ImportError, error);
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)dlsym(handle, entry_function_name);
#endif
    assert(entrypoint);

#if PYTHON_VERSION < 0x370
    char *old_context = _Py_PackageContext;
#else
    char const *old_context = _Py_PackageContext;
#endif

    _Py_PackageContext = (char *)package;

    // Finally call into the DLL.
#if PYTHON_VERSION < 0x300
    (*entrypoint)();
#else
    PyObject *module = (*entrypoint)();
#endif

    _Py_PackageContext = old_context;

#if PYTHON_VERSION < 0x300
    PyObject *module = Nuitka_GetModuleString(full_name);
#endif

    if (unlikely(module == NULL)) {
        if (!ERROR_OCCURRED()) {
            PyErr_Format(PyExc_SystemError, "dynamic module '%s' not initialized properly", full_name);
        }

        return NULL;
    }

#if PYTHON_VERSION >= 0x300
#if PYTHON_VERSION >= 0x350
    PyModuleDef *def;

    if (Py_TYPE(module) == &PyModuleDef_Type) {
        def = (PyModuleDef *)module;

        PyObject *full_name_obj = Nuitka_String_FromString(full_name);

        PyObject *spec = createModuleSpec(full_name_obj, false);

        module = PyModule_FromDefAndSpec(def, spec);
        Py_DECREF(spec);

        if (unlikely(module == NULL)) {
            PyErr_Format(PyExc_SystemError, "dynamic module '%s' not initialized properly from def", full_name);

            return NULL;
        }

        Nuitka_SetModule(full_name_obj, module);
        Py_DECREF(full_name_obj);

        int res = PyModule_ExecDef(module, def);

        if (unlikely(res == -1)) {
            return NULL;
        }

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
#if PYTHON_VERSION < 0x300
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
#if PYTHON_VERSION >= 0x370
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

static void loadTriggeredModule(char const *name, char const *trigger_name) {
    char trigger_module_name[2048];

    copyStringSafe(trigger_module_name, name, sizeof(trigger_module_name));
    appendStringSafe(trigger_module_name, trigger_name, sizeof(trigger_module_name));

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(trigger_module_name);

    if (entry != NULL) {
        if (isVerbose()) {
            PySys_WriteStderr("Loading %s\n", trigger_module_name);
        }

        IMPORT_EMBEDDED_MODULE(trigger_module_name);

        if (unlikely(ERROR_OCCURRED())) {
            if ((entry->flags & NUITKA_ABORT_MODULE_FLAG) != 0) {
                printf("Critical error loading %s.\n", trigger_module_name);
                abort();
            } else {
                PyObject *trigger_module_name_str = Nuitka_String_FromString(trigger_module_name);
                PyErr_WriteUnraisable(trigger_module_name_str);
                Py_DECREF(trigger_module_name_str);
            }
        }
    }
}

#if PYTHON_VERSION >= 0x340
static void _fixupSpecAttribute(PyObject *module) {
    PyObject *spec_value = LOOKUP_ATTRIBUTE(module, const_str_plain___spec__);

    if (spec_value && spec_value != Py_None) {
        if (HAS_ATTR_BOOL(spec_value, const_str_plain__initializing)) {
            SET_ATTRIBUTE(spec_value, const_str_plain__initializing, Py_False);
        }
    }
}
#endif

// Pointers to bytecode data.
static char **_bytecode_data = NULL;

static PyObject *loadModule(PyObject *module, PyObject *module_name,
                            struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
#ifdef _NUITKA_STANDALONE
    if ((entry->flags & NUITKA_SHLIB_FLAG) != 0) {
        // Append the the entry name from full path module name with dots,
        // and translate these into directory separators.
#ifdef _WIN32
        wchar_t filename[MAXPATHLEN + 1] = {0};

        appendWStringSafeW(filename, getBinaryDirectoryWideChars(), sizeof(filename) / sizeof(wchar_t));
        appendCharSafeW(filename, SEP, sizeof(filename) / sizeof(wchar_t));
        appendModulenameAsPathW(filename, entry->name, sizeof(filename) / sizeof(wchar_t));
        appendStringSafeW(filename, ".pyd", sizeof(filename) / sizeof(wchar_t));
#else
        char filename[MAXPATHLEN + 1] = {0};

        appendStringSafe(filename, getBinaryDirectoryHostEncoded(), sizeof(filename));
        appendCharSafe(filename, SEP, sizeof(filename));
        appendModulenameAsPath(filename, entry->name, sizeof(filename));
        appendStringSafe(filename, ".so", sizeof(filename));

#endif
        // Not used unfortunately. TODO: Check if we can make it so.
        Py_DECREF(module);

        callIntoShlibModule(entry->name, filename);
    } else
#endif
        if ((entry->flags & NUITKA_BYTECODE_FLAG) != 0) {
        // TODO: Do node use marshal, but our own stuff, once we
        // can do code objects too.

        PyCodeObject *code_object =
            (PyCodeObject *)PyMarshal_ReadObjectFromString(_bytecode_data[entry->bytecode_index], entry->bytecode_size);

        // TODO: Probably a bit harsh reaction.
        if (unlikely(code_object == NULL)) {
            PyErr_Print();
            abort();
        }

        return loadModuleFromCodeObject(module, code_object, entry->name, (entry->flags & NUITKA_PACKAGE_FLAG) != 0);
    } else {
        assert((entry->flags & NUITKA_SHLIB_FLAG) == 0);
        assert(entry->python_initfunc);

        bool res = Nuitka_SetModule(module_name, module);
        assert(res != false);

        // Run the compiled module code, we get the module returned.
        PyObject *result = entry->python_initfunc(module, entry);
        CHECK_OBJECT_X(result);

#if PYTHON_VERSION >= 0x340
        if (result != NULL) {
            _fixupSpecAttribute(result);
        }
#endif
    }

    if (unlikely(ERROR_OCCURRED())) {
        return NULL;
    }

    if (isVerbose()) {
        PySys_WriteStderr("Loaded %s\n", entry->name);
    }

    return Nuitka_GetModule(module_name);
}

static PyObject *_EXECUTE_EMBEDDED_MODULE(PyObject *module, PyObject *module_name, char const *name) {
    CHECK_OBJECT(module);
    CHECK_OBJECT(module_name);

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(name);
    bool frozen_import = entry == NULL && hasFrozenModule(name);

    if (entry != NULL || frozen_import) {
        // Execute the "preLoad" code produced for the module potentially. This
        // is from plug-ins typically, that want to modify things for the the
        // module before loading, to e.g. set a plug-in path, or do some monkey
        // patching in order to make things compatible.
        loadTriggeredModule(name, "-preLoad");
    }

    PyObject *result = NULL;

    if (entry != NULL) {
        result = loadModule(module, module_name, entry);

        if (unlikely(result == NULL)) {
            return NULL;
        }
    }

    if (frozen_import) {
        int res = PyImport_ImportFrozenModule((char *)name);

        if (unlikely(res == -1)) {
            return NULL;
        }

        if (res == 1) {
            result = Nuitka_GetModule(module_name);
        }
    }

    if (result != NULL) {
        // Execute the "postLoad" code produced for the module potentially. This
        // is from plug-ins typically, that want to modify the module immediately
        // after loading, to e.g. set a plug-in path, or do some monkey patching
        // in order to make things compatible.
        loadTriggeredModule(name, "-postLoad");

        return result;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

// Note: This may become an entry point for hard coded imports of compiled
// stuff.
PyObject *IMPORT_EMBEDDED_MODULE(char const *name) {
    PyObject *module_name = Nuitka_String_FromString(name);

    // Check if it's already loaded, and don't do it again otherwise.
    PyObject *module = Nuitka_GetModule(module_name);

    if (module != NULL) {
        Py_DECREF(module_name);
        return module;
    }

#if PYTHON_VERSION < 0x300
    module = PyModule_New(name);
#else
    module = PyModule_NewObject(module_name);
#endif

    PyObject *result = _EXECUTE_EMBEDDED_MODULE(module, module_name, name);

    Py_DECREF(module_name);

#if PYTHON_VERSION < 0x350
    if (unlikely(result == NULL)) {
        PyObject *save_exception_type, *save_exception_value;
        PyTracebackObject *save_exception_tb;
        FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

        PyObject_DelItem(PyImport_GetModuleDict(), module_name);

        RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
    }
#endif

    return result;
}

PyObject *EXECUTE_EMBEDDED_MODULE(PyObject *module) {
    PyObject *module_name = LOOKUP_ATTRIBUTE(module, const_str_plain___name__);
    assert(module_name);

    char const *name = Nuitka_String_AsString(module_name);

    return _EXECUTE_EMBEDDED_MODULE(module, module_name, name);
}

static PyObject *_path_unfreezer_load_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:load_module", (char **)_kwlist, &module_name, &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    assert(module_name);
    assert(Nuitka_String_Check(module_name));

    char const *name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("Loading %s\n", name);
    }

#ifndef _NUITKA_STANDALONE
    if (installed_extension_modules != NULL) {
        PyObject *extension_module_filename = DICT_GET_ITEM0(installed_extension_modules, module_name);

        if (extension_module_filename != NULL) {
            return callIntoInstalledShlibModule(module_name, extension_module_filename);
        }
    }
#endif

    return IMPORT_EMBEDDED_MODULE(name);
}

static char const *_kwlist_is_package[] = {"fullname", NULL};

static PyObject *_path_unfreezer_is_package(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:is_package", (char **)_kwlist_is_package, &module_name);

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

static char const *_kwlist_iter_modules[] = {"package", NULL};

static PyObject *_path_unfreezer_iter_modules(struct Nuitka_LoaderObject *self, PyObject *args, PyObject *kwds) {
    PyObject *prefix;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:iter_modules", (char **)_kwlist_iter_modules, &prefix);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *result = PyList_New(0);

    struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;
    assert(current);

    char const *s = self->m_loader_entry->name;

    while (current->name != NULL) {
        if ((current->flags & NUITKA_TRANSLATED_FLAG) != 0) {
            current->name = UNTRANSLATE(current->name);
            current->flags -= NUITKA_TRANSLATED_FLAG;
        }

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

        PyObject *name = Nuitka_String_FromString(current->name + strlen(s) + 1);

        if (CHECK_IF_TRUE(prefix)) {
            PyObject *old = name;
            name = PyUnicode_Concat(prefix, name);
            Py_DECREF(old);
        }

        PyTuple_SET_ITEM(r, 0, name);
        PyTuple_SET_ITEM0(r, 1, BOOL_FROM((current->flags & NUITKA_PACKAGE_FLAG) != 0));

        LIST_APPEND1(result, r);

        current++;
    }

    return result;
}

#if PYTHON_VERSION >= 0x300
// Used in module template too, therefore exported.
PyObject *getImportLibBootstrapModule() {
    static PyObject *importlib = NULL;
    if (importlib == NULL) {
        importlib = PyImport_ImportModule("importlib._bootstrap");
    }

    return importlib;
}
#endif

#if PYTHON_VERSION >= 0x340
static PyObject *_path_unfreezer_repr_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:module_repr", (char **)_kwlist, &module, &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    return PyUnicode_FromFormat("<module '%s' from %R>", PyModule_GetName(module), PyModule_GetFilenameObject(module));
}

static PyObject *getModuleSpecClass(PyObject *importlib_module) {
    static PyObject *module_spec_class = NULL;

    if (module_spec_class == NULL) {
        module_spec_class = PyObject_GetAttrString(importlib_module, "ModuleSpec");
    }

    return module_spec_class;
}

static PyObject *createModuleSpec(PyObject *module_name, bool is_package) {
    CHECK_OBJECT(module_name);
    assert(Nuitka_String_Check(module_name));

    PyObject *importlib_module = getImportLibBootstrapModule();

    if (unlikely(importlib_module == NULL)) {
        return NULL;
    }

    PyObject *module_spec_class = getModuleSpecClass(importlib_module);

    if (unlikely(module_spec_class == NULL)) {
        return NULL;
    }

    PyObject *args = PyTuple_New(2);
    PyTuple_SET_ITEM0(args, 0, module_name);
    PyTuple_SET_ITEM0(args, 1, (PyObject *)&Nuitka_Loader_Type);

    PyObject *kwargs = PyDict_New();
    PyDict_SetItemString(kwargs, "is_package", is_package ? Py_True : Py_False);

    PyObject *result = CALL_FUNCTION(module_spec_class, args, kwargs);

    Py_DECREF(args);
    Py_DECREF(kwargs);

    return result;
}

#ifndef _NUITKA_STANDALONE
// We might have to load stuff from installed modules in our package namespaces.
static PyObject *createModuleSpecViaPathFinder(PyObject *module_name, char const *parent_module_name) {
    if (scanModuleInPackagePath(module_name, parent_module_name)) {
        return createModuleSpec(module_name, false);
    } else {
        // Without error this means we didn't make it.
        return NULL;
    }
}
#endif

static char const *_kwlist_find_spec[] = {"fullname", "is_package", "path", NULL};

static PyObject *_path_unfreezer_find_spec(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused1; // We ignore "is_package"
    PyObject *unused2; // We ignore "path"

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:find_spec", (char **)_kwlist_find_spec, &module_name,
                                          &unused1, &unused2);

    if (unlikely(res == 0)) {
        return NULL;
    }

    char const *full_name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # considering responsibility (find_spec)\n", full_name);
    }

    struct Nuitka_MetaPathBasedLoaderEntry const *entry = findEntry(full_name);

#ifndef _NUITKA_STANDALONE
    // We need to deal with things located in compiled packages, that were not included,
    // e.g. extension modules, but also other files, that were asked to not be included
    // or added later.
    if (entry == NULL) {
        entry = findContainingPackageEntry(full_name);

        if (entry != NULL) {
            PyObject *result = createModuleSpecViaPathFinder(module_name, entry->name);

            if (result != NULL) {
                if (isVerbose()) {
                    PySys_WriteStderr("import %s # claimed responsibility (contained in compiled package %s)\n",
                                      full_name, entry->name);
                }

                return result;
            }

            if (ERROR_OCCURRED()) {
                return NULL;
            }

            entry = NULL;
        }
    }
#endif

    if (entry == NULL) {
        if (isVerbose()) {
            PySys_WriteStderr("import %s # denied responsibility\n", full_name);
        }

        Py_INCREF(Py_None);
        return Py_None;
    }

    if (isVerbose()) {
        PySys_WriteStderr("import %s # claimed responsibility (%s)\n", Nuitka_String_AsString(module_name),
                          (entry->flags & NUITKA_BYTECODE_FLAG) != 0 ? "bytecode" : "compiled");
    }

    return createModuleSpec(module_name, (entry->flags & NUITKA_PACKAGE_FLAG) != 0);
}

#if PYTHON_VERSION >= 0x350
static char const *_kwlist_create_module[] = {"spec", NULL};

static PyObject *_path_unfreezer_create_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *spec;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:create_module", (char **)_kwlist_create_module, &spec);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *module_name = PyObject_GetAttr(spec, const_str_plain_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # created module\n", Nuitka_String_AsString(module_name));
    }
    // TODO: Should we clean it up here?
    return PyModule_NewObject(module_name);
}

static char const *_kwlist_exec_module[] = {"module", NULL};

static PyObject *_path_unfreezer_exec_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:exec_module", (char **)_kwlist_exec_module, &module);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *module_name = PyObject_GetAttr(module, const_str_plain___name__);
    CHECK_OBJECT(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # execute module\n", Nuitka_String_AsString(module_name));
    }

    // During spec creation, we have populated the dictionary with a filename to load from
    // for extension modules that were found installed in the system and below our package.
#ifndef _NUITKA_STANDALONE
    if (installed_extension_modules != NULL) {
        PyObject *extension_module_filename = DICT_GET_ITEM0(installed_extension_modules, module_name);

        if (extension_module_filename != NULL) {
            return callIntoInstalledShlibModule(module_name, extension_module_filename);
        }
    }
#endif

    return EXECUTE_EMBEDDED_MODULE(module);
}

#endif

#endif

#if _NUITKA_EXPERIMENTAL_METADATA

struct Nuitka_DistributionObject {
    /* Python object folklore: */
    PyObject_HEAD;

    /* The loader entry, to know this is about exactly. */
    struct Nuitka_MetaPathBasedLoaderEntry const *m_loader_entry;
};

static void Nuitka_Distribution_tp_dealloc(struct Nuitka_DistributionObject *distribution) {
    Nuitka_GC_UnTrack(distribution);

    PyObject_GC_Del(distribution);
}

static PyObject *Nuitka_Distribution_tp_repr(struct Nuitka_DistributionObject *loader) {
#if PYTHON_VERSION < 0x300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
        "<nuitka_distribution for '%s'>", loader->m_loader_entry->name);
}

static PyObject *_nuitka_distribution_metainfo(struct Nuitka_DistributionObject *distribution) {
    CHECK_OBJECT(distribution);

    PyObject *result = Nuitka_String_FromString("");

    return result;
}

static PyMethodDef Nuitka_Distribution_methods[] = {
    {"metainfo", (PyCFunction)_nuitka_distribution_metainfo, METH_NOARGS, NULL},

    {NULL, NULL}};

static PyObject *Nuitka_Distribution_get_version(struct Nuitka_DistributionObject *distribution) {
    CHECK_OBJECT(distribution);

    // TODO: Don't lie, but this will allow some things to proceed.
    return Nuitka_String_FromString("0.0.0");
}

static PyGetSetDef Nuitka_Distribution_getsetlist[] = {
    {(char *)"version", (getter)Nuitka_Distribution_get_version, (setter)NULL, NULL}, {NULL}};

static PyTypeObject Nuitka_Distribution_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "nuitka_distribution",
    sizeof(struct Nuitka_DistributionObject),   /* tp_basicsize */
    0,                                          /* tp_itemsize */
    (destructor)Nuitka_Distribution_tp_dealloc, /* tp_dealloc */
    0,                                          /* tp_print */
    0,                                          /* tp_getattr */
    0,                                          /* tp_setattr */
    0,                                          /* tp_reserved */
    (reprfunc)Nuitka_Distribution_tp_repr,      /* tp_repr */
    0,                                          /* tp_as_number */
    0,                                          /* tp_as_sequence */
    0,                                          /* tp_as_mapping */
    0,                                          /* tp_hash */
    0,                                          /* tp_call */
    0,                                          /* tp_str */
    PyObject_GenericGetAttr,                    /* tp_getattro */
    0,                                          /* tp_setattro */
    0,                                          /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,    /* tp_flags */
    0,                                          /* tp_doc */
    0,                                          /* tp_traverse */
    0,                                          /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    Nuitka_Distribution_methods,                /* tp_methods */
    0,                                          /* tp_members */
    Nuitka_Distribution_getsetlist,             /* tp_getset */
};

PyObject *Nuitka_Distribution_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
    struct Nuitka_DistributionObject *result;

    result = (struct Nuitka_DistributionObject *)PyObject_GC_New(struct Nuitka_DistributionObject,
                                                                 &Nuitka_Distribution_Type);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;

    return (PyObject *)result;
}

static char const *_kwlist_find_distributions[] = {"context", NULL};

static PyObject *_path_unfreezer_find_distributions(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *context;

    int res =
        PyArg_ParseTupleAndKeywords(args, kwds, "O:find_distributions", (char **)_kwlist_find_distributions, &context);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *name = PyObject_GetAttr(context, const_str_plain_name);

    if (unlikely(name == 0)) {
        return NULL;
    }

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(Nuitka_String_AsString(name));

    Py_DECREF(name);

    PyObject *temp;

    if (entry) {
        temp = PyTuple_New(1);

        // Create a distribution object for the entry
        PyObject *distribution = Nuitka_Distribution_New(entry);
        PyTuple_SET_ITEM(temp, 0, distribution);

    } else {
        temp = const_tuple_empty;
        Py_INCREF(const_tuple_empty);
    }

    // We are expected to return an iterator.
    PyObject *result = MAKE_ITERATOR(temp);

    Py_DECREF(temp);
    return result;
}

#endif

static PyMethodDef Nuitka_Loader_methods[] = {
    {"iter_modules", (PyCFunction)_path_unfreezer_iter_modules, METH_VARARGS | METH_KEYWORDS, NULL},
    {"get_data", (PyCFunction)_path_unfreezer_get_data, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"find_module", (PyCFunction)_path_unfreezer_find_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"load_module", (PyCFunction)_path_unfreezer_load_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"is_package", (PyCFunction)_path_unfreezer_is_package, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#if PYTHON_VERSION >= 0x340
    {"module_repr", (PyCFunction)_path_unfreezer_repr_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"find_spec", (PyCFunction)_path_unfreezer_find_spec, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#endif
#if PYTHON_VERSION >= 0x350
    {"create_module", (PyCFunction)_path_unfreezer_create_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"exec_module", (PyCFunction)_path_unfreezer_exec_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#endif
#if _NUITKA_EXPERIMENTAL_METADATA
    {"find_distributions", (PyCFunction)_path_unfreezer_find_distributions, METH_STATIC | METH_VARARGS | METH_KEYWORDS,
     NULL},
#endif

    {NULL, NULL}
};

static PyObject *Nuitka_Loader_tp_repr(struct Nuitka_LoaderObject *loader) {
#if PYTHON_VERSION < 0x300
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

static int Nuitka_Loader_tp_traverse(struct Nuitka_LoaderObject *loader, visitproc visit, void *arg) { return 0; }

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

/* Used by modules to register child loaders for packages. */
PyObject *Nuitka_Loader_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
    struct Nuitka_LoaderObject *result;

    allocateFromFreeListFixed(free_list_loaders, struct Nuitka_LoaderObject, Nuitka_Loader_Type);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;

    return (PyObject *)result;
}

void registerMetaPathBasedUnfreezer(struct Nuitka_MetaPathBasedLoaderEntry *_loader_entries,
                                    unsigned char **bytecode_data) {
    // Do it only once.
    if (loader_entries) {
        assert(_loader_entries == loader_entries);

        return;
    }

    _bytecode_data = (char **)bytecode_data;

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
                if ((current->flags & NUITKA_TRANSLATED_FLAG) != 0) {
                    current->name = UNTRANSLATE(current->name);
                    current->flags -= NUITKA_TRANSLATED_FLAG;
                }

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

#if _NUITKA_EXPERIMENTAL_METADATA
    PyType_Ready(&Nuitka_Distribution_Type);
#endif

    // Register it as a meta path loader.
    int res = PyList_Insert(PySys_GetObject((char *)"meta_path"),
#if PYTHON_VERSION < 0x300
                            0,
#else
                            2,
#endif

                            (PyObject *)&Nuitka_Loader_Type);
    assert(res == 0);
}

#if defined(_NUITKA_STANDALONE)
// This is called for the technical module imported early on during interpreter
// into, to still get compatible "__file__" attributes.
void setEarlyFrozenModulesFileAttribute(void) {
#if PYTHON_VERSION >= 0x300
    // Make sure the importlib fully bootstraps before doing this.
    PyObject *importlib_module = getImportLibBootstrapModule();
    CHECK_OBJECT(importlib_module);
#endif

    PyObject *sys_modules = PyImport_GetModuleDict();
    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while (PyDict_Next(sys_modules, &ppos, &key, &value)) {
        if (key != NULL && value != NULL && PyModule_Check(value)) {
            if (HAS_ATTR_BOOL(value, const_str_plain___file__)) {
                bool is_package = HAS_ATTR_BOOL(value, const_str_plain___path__);

                PyObject *file_value = MAKE_RELATIVE_PATH_FROM_NAME(Nuitka_String_AsString(key), is_package);
                PyObject_SetAttr(value, const_str_plain___file__, file_value);
                Py_DECREF(file_value);
            }
        }
    }

    assert(!ERROR_OCCURRED());
}

#endif
