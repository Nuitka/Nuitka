//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This implements the loading of C compiled modules and shared library
// extension modules bundled for standalone mode.

// This is achieved mainly by registered a "sys.meta_path" loader, that then
// gets asked for module names, and responds if knows about one. It's fed by
// a table created at compile time.

// The nature and use of these 2 loaded module kinds is very different, but
// having them as distinct loaders would only require to duplicate the search
// and registering of stuff.

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#include "nuitka/unfreezing.h"

#ifdef _WIN32
#undef SEP
#define SEP '\\'
#define SEP_L L'\\'
#else
#define SEP_L SEP
#endif

#ifdef _WIN32
#include <windows.h>
#endif

extern PyTypeObject Nuitka_Loader_Type;

struct Nuitka_LoaderObject {
    /* Python object folklore: */
    PyObject_HEAD

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
    for (struct _frozen const *p = PyImport_FrozenModules; p != NULL; p++) {
        if (p->name == NULL) {
            return false;
        }

        if (strcmp(p->name, name) == 0) {
            break;
        }
    }

    return true;
}

static char *appendModuleNameAsPath(char *buffer, char const *module_name, size_t buffer_size) {
    // Skip to the end
    while (*buffer != 0) {
        buffer++;
        buffer_size -= 1;
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

static void appendModuleNameAsPathW(wchar_t *buffer, PyObject *module_name, size_t buffer_size) {
    Py_ssize_t size;
    wchar_t const *module_name_wstr = Nuitka_UnicodeAsWideString(module_name, &size);

    while (size > 0) {
        wchar_t c = *module_name_wstr++;
        size -= 1;

        if (c == L'.') {
            c = SEP_L;
        }

        appendWCharSafeW(buffer, c, buffer_size);
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

    Py_ssize_t consts_count = PyTuple_GET_SIZE(code_object->co_consts);

    for (Py_ssize_t i = 0; i < consts_count; i++) {
        PyObject *constant = PyTuple_GET_ITEM(code_object->co_consts, i);

        if (PyCode_Check(constant)) {
            patchCodeObjectPaths((PyCodeObject *)constant, module_path);
        }
    }
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_RELATIVE_PATH_FROM_NAME(char const *name, bool is_package, bool dir_only) {
    char buffer[MAXPATHLEN + 1] = {0};

    appendModuleNameAsPath(buffer, name, sizeof(buffer));

    if (dir_only == false) {
        if (is_package) {
            appendCharSafe(buffer, SEP, sizeof(buffer));
            appendStringSafe(buffer, "__init__.py", sizeof(buffer));
        } else {
            appendStringSafe(buffer, ".py", sizeof(buffer));
        }
    } else {
        if (is_package == false) {
            char *sep = strrchr(buffer, SEP);
            if (sep) {
                *sep = 0;
            } else {
                buffer[0] = '.';
                buffer[1] = 0;
            }
        }
    }

    PyObject *module_path_entry_base = Nuitka_String_FromString(buffer);

    PyObject *result = MAKE_RELATIVE_PATH(module_path_entry_base);

    Py_DECREF(module_path_entry_base);

    return result;
}

static PyObject *_makeDunderPathObject(PyThreadState *tstate, PyObject *module_path_entry) {
    CHECK_OBJECT(module_path_entry);

    PyObject *path_list = MAKE_LIST_EMPTY(tstate, 1);
    if (unlikely(path_list == NULL)) {
        return NULL;
    }

    PyList_SET_ITEM0(path_list, 0, module_path_entry);

    CHECK_OBJECT(path_list);
    return path_list;
}

static PyObject *loadModuleFromCodeObject(PyThreadState *tstate, PyObject *module, PyCodeObject *code_object,
                                          char const *name, bool is_package) {
    assert(code_object != NULL);

    {
        NUITKA_MAY_BE_UNUSED bool b_res = Nuitka_SetModuleString(name, module);
        assert(b_res != false);
    }

    char buffer[MAXPATHLEN + 1] = {0};

    PyObject *module_path_entry = NULL;

    if (is_package) {
        appendModuleNameAsPath(buffer, name, sizeof(buffer));
        PyObject *module_path_entry_base = Nuitka_String_FromString(buffer);

        module_path_entry = MAKE_RELATIVE_PATH(module_path_entry_base);
        Py_DECREF(module_path_entry_base);

        appendCharSafe(buffer, SEP, sizeof(buffer));
        appendStringSafe(buffer, "__init__.py", sizeof(buffer));
    } else {
        appendModuleNameAsPath(buffer, name, sizeof(buffer));
        appendStringSafe(buffer, ".py", sizeof(buffer));
    }

    PyObject *module_path_name = Nuitka_String_FromString(buffer);

    PyObject *module_path = MAKE_RELATIVE_PATH(module_path_name);
    Py_DECREF(module_path_name);

    if (is_package) {
        /* Set __path__ properly, unlike frozen module importer does. */
        PyObject *path_list = _makeDunderPathObject(tstate, module_path_entry);

        int res = PyObject_SetAttr(module, const_str_plain___path__, path_list);
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

    PGO_onModuleEntered(name);
    module = PyImport_ExecCodeModuleEx((char *)name, (PyObject *)code_object, Nuitka_String_AsString(module_path));
    PGO_onModuleExit(name, module == NULL);

    Py_DECREF(module_path);

    return module;
}

static struct Nuitka_MetaPathBasedLoaderEntry *findEntry(char const *name) {
    struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;
    assert(current);

    while (current->name != NULL) {
        if ((current->flags & NUITKA_TRANSLATED_FLAG) != 0) {
            current->name = UN_TRANSLATE(current->name);
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
            current->name = UN_TRANSLATE(current->name);
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

static PyObject *_getFileList(PyThreadState *tstate, PyObject *dirname) {
    static PyObject *listdir_func = NULL;

    // TODO: Use OS_LISTDIR instead.

    if (listdir_func == NULL) {
        listdir_func = PyObject_GetAttrString(IMPORT_HARD_OS(), "listdir");
    }

    if (unlikely(listdir_func == NULL)) {
        return NULL;
    }

    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, listdir_func, dirname);

    return result;
}

#if PYTHON_VERSION < 0x300
static PyObject *_getImportingSuffixesByPriority(PyThreadState *tstate, int kind) {
    static PyObject *result = NULL;

    if (result == NULL) {
        result = MAKE_LIST_EMPTY(tstate, 0);

        PyObject *imp_module = PyImport_ImportModule("imp");
        PyObject *get_suffixes_func = PyObject_GetAttrString(imp_module, "get_suffixes");

        PyObject *suffix_list = CALL_FUNCTION_NO_ARGS(tstate, get_suffixes_func);

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

static PyObject *getExtensionModuleSuffixesByPriority(PyThreadState *tstate) {
    static PyObject *result = NULL;

    if (result == NULL) {
#if PYTHON_VERSION < 0x300
        result = _getImportingSuffixesByPriority(tstate, 3);
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

static bool scanModuleInPackagePath(PyThreadState *tstate, PyObject *module_name, char const *parent_module_name) {
    PyObject *sys_modules = Nuitka_GetSysModules();

    PyObject *parent_module = PyDict_GetItemString(sys_modules, parent_module_name);
    CHECK_OBJECT(parent_module);

    PyObject *parent_path = PyObject_GetAttr(parent_module, const_str_plain___path__);

    // Accept that it might be deleted.
    if (parent_path == NULL || !PyList_Check(parent_path)) {
        return false;
    }

    PyObject *candidates = MAKE_LIST_EMPTY(tstate, 0);

    // Search only relative to the parent name of course.
    char const *module_relative_name_str = Nuitka_String_AsString(module_name) + strlen(parent_module_name) + 1;

    Py_ssize_t parent_path_size = PyList_GET_SIZE(parent_path);

    for (Py_ssize_t i = 0; i < parent_path_size; i += 1) {
        PyObject *path_element = PyList_GET_ITEM(parent_path, i);

        PyObject *filenames_list = _getFileList(tstate, path_element);

        if (filenames_list == NULL) {
            CLEAR_ERROR_OCCURRED(tstate);
            continue;
        }

        Py_ssize_t filenames_list_size = PyList_GET_SIZE(filenames_list);

        for (Py_ssize_t j = 0; j < filenames_list_size; j += 1) {
            PyObject *filename = PyList_GET_ITEM(filenames_list, j);

            if (Nuitka_String_CheckExact(filename)) {
                char const *filename_str = Nuitka_String_AsString(filename);

                if (strncmp(filename_str, module_relative_name_str, strlen(module_relative_name_str)) == 0 &&
                    filename_str[strlen(module_relative_name_str)] == '.') {
                    LIST_APPEND1(candidates, MAKE_TUPLE2(tstate, path_element, filename));
                }
            }
        }
    }

#if 0
    PRINT_STRING("CANDIDATES:");
    PRINT_STRING(Nuitka_String_AsString(module_name));
    PRINT_STRING(module_relative_name_str);
    PRINT_ITEM(candidates);
    PRINT_NEW_LINE();
#endif

    // Look up C-extension suffixes, these are used with highest priority.
    PyObject *suffix_list = getExtensionModuleSuffixesByPriority(tstate);

    bool result = false;

    for (Py_ssize_t i = 0; i < PyList_GET_SIZE(suffix_list); i += 1) {
        PyObject *suffix = PyList_GET_ITEM(suffix_list, i);

        char const *suffix_str = Nuitka_String_AsString(suffix);

        for (Py_ssize_t j = 0; j < PyList_GET_SIZE(candidates); j += 1) {
            PyObject *entry = PyList_GET_ITEM(candidates, j);

            PyObject *directory = PyTuple_GET_ITEM(entry, 0);
            PyObject *candidate = PyTuple_GET_ITEM(entry, 1);

            char const *candidate_str = Nuitka_String_AsString(candidate);

            if (strcmp(suffix_str, candidate_str + strlen(module_relative_name_str)) == 0) {
                PyObject *fullpath = JOIN_PATH2(directory, candidate);

                if (installed_extension_modules == NULL) {
                    installed_extension_modules = MAKE_DICT_EMPTY(tstate);
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

static PyObject *callIntoExtensionModule(PyThreadState *tstate, char const *full_name, const filename_char_t *filename,
                                         bool is_package);

static PyObject *callIntoInstalledExtensionModule(PyThreadState *tstate, PyObject *module_name,
                                                  PyObject *extension_module_filename) {
#if _WIN32
    // We can rely on unicode object to be there in case of Windows, to have an easier time to
    // create the string needed.
    assert(PyUnicode_CheckExact(extension_module_filename));

    wchar_t const *extension_module_filename_str = Nuitka_UnicodeAsWideString(extension_module_filename, NULL);
#else
    char const *extension_module_filename_str = Nuitka_String_AsString(extension_module_filename);
#endif

    // TODO: The value of "is_package" is guessed, maybe infer from filename being
    // a "__init__.so" and the like.
    return callIntoExtensionModule(tstate, Nuitka_String_AsString(module_name), extension_module_filename_str, false);
}

#endif

static char const *getEntryModeString(struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
    char const *mode = "compiled";

    if ((entry->flags & NUITKA_EXTENSION_MODULE_FLAG) != 0) {
        mode = "extension";
    } else if ((entry->flags & NUITKA_BYTECODE_FLAG) != 0) {
        mode = "bytecode";
    }

    return mode;
}

static char *_kw_list_find_module[] = {(char *)"fullname", (char *)"unused", NULL};

static PyObject *_nuitka_loader_find_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:find_module", (char **)_kw_list_find_module, &module_name,
                                          &unused);

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
            PySys_WriteStderr("import %s # claimed responsibility (%s)\n", name, getEntryModeString(entry));
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
        PyThreadState *tstate = PyThreadState_GET();

        bool result = scanModuleInPackagePath(tstate, module_name, entry->name);

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

    Py_INCREF_IMMORTAL(Py_None);
    return Py_None;
}

static char const *_kw_list_get_data[] = {"filename", NULL};

static PyObject *_nuitka_loader_get_data(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *filename;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:get_data", (char **)_kw_list_get_data, &filename);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    return GET_FILE_BYTES(tstate, filename);
}

static void setModuleFileValue(PyThreadState *tstate, PyObject *module, filename_char_t const *filename) {
    CHECK_OBJECT(module);
    assert(filename != NULL);

    assert(PyModule_Check(module));

    PyObject *dict = PyModule_GetDict(module);

    // TODO: We should have DICT_SET_ITEM0/1 for these things.
    PyObject *new_file_value = Nuitka_String_FromFilename(filename);
    DICT_SET_ITEM(dict, const_str_plain___file__, new_file_value);
    Py_DECREF(new_file_value);
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
static PyObject *createModuleSpec(PyThreadState *tstate, PyObject *module_name, PyObject *origin, bool is_package);
#endif

static void _fillExtensionModuleDllEntryFunctionName(PyThreadState *tstate, char *buffer, size_t buffer_size,
                                                     char const *name) {

#if PYTHON_VERSION >= 0x350
    PyObject *name_bytes_obj = PyBytes_FromString(name);
    PyObject *name_obj = BYTES_DECODE2(tstate, name_bytes_obj, Nuitka_String_FromString("utf8"));
    Py_DECREF(name_bytes_obj);

    PyObject *name_ascii = UNICODE_ENCODE2(tstate, name_obj, const_str_plain_ascii);

    if (name_ascii == NULL) {
        DROP_ERROR_OCCURRED(tstate);

        PyObject *name_punycode = UNICODE_ENCODE2(tstate, name_obj, const_str_plain_punycode);

        CHECK_OBJECT(name_punycode);

        snprintf(buffer, buffer_size, "PyInitU_%s", PyBytes_AsString(name_punycode));

        Py_DECREF(name_punycode);
    } else {
        Py_DECREF(name_ascii);

        snprintf(buffer, buffer_size, "PyInit_%s", name);
    }
    Py_DECREF(name_obj);
#else

    snprintf(buffer, buffer_size,
#if PYTHON_VERSION < 0x300
             "init%s",
#else
             "PyInit_%s",
#endif
             name);
#endif
}

#ifdef _NUITKA_STANDALONE
// Append the the entry name from full path module name with dots,
// and translate these into directory separators.
static void _makeModuleCFilenameValue(filename_char_t *filename, size_t filename_size, char const *module_name_cstr,
                                      PyObject *module_name, bool is_package) {
#ifdef _WIN32
    appendWStringSafeW(filename, getBinaryDirectoryWideChars(true), filename_size);
    appendWCharSafeW(filename, SEP_L, filename_size);
    appendModuleNameAsPathW(filename, module_name, filename_size);
    if (is_package) {
        appendWCharSafeW(filename, SEP_L, filename_size);
        appendStringSafeW(filename, "__init__", filename_size);
    }
    appendStringSafeW(filename, ".pyd", filename_size);
#else
    appendStringSafe(filename, getBinaryDirectoryHostEncoded(true), filename_size);
    appendCharSafe(filename, SEP, filename_size);
    appendModuleNameAsPath(filename, module_name_cstr, filename_size);
    if (is_package) {
        appendCharSafe(filename, SEP, filename_size);
        appendStringSafe(filename, "__init__", filename_size);
    }
    appendStringSafe(filename, ".so", filename_size);
#endif
}
#endif

#if PYTHON_VERSION >= 0x3c0 && defined(_NUITKA_USE_UNEXPOSED_API)
extern _Thread_local const char *pkgcontext;
#endif

static const char *NuitkaImport_SwapPackageContext(const char *new_context) {
// TODO: The locking APIs for 3.13 give errors here that are not explained
// yet.
#if PYTHON_VERSION >= 0x3c0
    // spell-checker: ignore pkgcontext
    const char *old_context = _PyRuntime.imports.pkgcontext;
    _PyRuntime.imports.pkgcontext = new_context;
#if PYTHON_VERSION >= 0x3c0 && defined(_NUITKA_USE_UNEXPOSED_API)
    pkgcontext = new_context;
#endif
    return old_context;
#elif PYTHON_VERSION >= 0x370
    char const *old_context = _Py_PackageContext;
    _Py_PackageContext = (char *)new_context;
    return old_context;
#else
    char *old_context = _Py_PackageContext;
    _Py_PackageContext = (char *)new_context;
    return (char const *)old_context;
#endif
}

static PyObject *callIntoExtensionModule(PyThreadState *tstate, char const *full_name, const filename_char_t *filename,
                                         bool is_package) {
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
    _fillExtensionModuleDllEntryFunctionName(tstate, entry_function_name, sizeof(entry_function_name), name);

#ifdef _WIN32
    if (isVerbose()) {
        PySys_WriteStderr("import %s # LoadLibraryExW(\"%S\");\n", full_name, filename);
    }

#ifndef _NUITKA_EXPERIMENTAL_DEBUG_STANDALONE
    // Disable all but critical errors, prevents dialogs from showing.
    // spell-checker: ignore SEM_FAILCRITICALERRORS
    unsigned int old_mode = SetErrorMode(SEM_FAILCRITICALERRORS);
#endif

    HINSTANCE hDLL;
#if PYTHON_VERSION >= 0x380
    Py_BEGIN_ALLOW_THREADS;
    hDLL = LoadLibraryExW(filename, NULL, LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR);
    Py_END_ALLOW_THREADS;
#else
    hDLL = LoadLibraryExW(filename, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
#endif

#ifndef _NUITKA_EXPERIMENTAL_DEBUG_STANDALONE
    SetErrorMode(old_mode);
#endif

    if (unlikely(hDLL == NULL)) {
        char buffer[1024];

        char error_message[1024];
        int size;

        unsigned int error_code = GetLastError();

        size = FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL, error_code, 0,
                             (LPTSTR)error_message, sizeof(error_message), NULL);

        // Report either way even if failed to get error message.
        if (size == 0) {
            int ret = PyOS_snprintf(buffer, sizeof(buffer), "LoadLibraryExW '%S' failed with error code %d", filename,
                                    error_code);

            assert(ret >= 0);
        } else {
            // Strip trailing newline.
            if (size >= 2 && error_message[size - 2] == '\r' && error_message[size - 1] == '\n') {
                size -= 2;
                error_message[size] = '\0';
            }
            int ret = PyOS_snprintf(buffer, sizeof(buffer), "LoadLibraryExW '%S' failed: %s", filename, error_message);
            assert(ret >= 0);
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ImportError, buffer);
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)GetProcAddress(hDLL, entry_function_name);
#else
    // This code would work for all versions, we are avoiding access to interpreter
    // structure internals of 3.8 or higher.
    // spell-checker: ignore getdlopenflags,dlopenflags

#ifdef __wasi__
    const char *error = "dynamic libraries are not implemented in wasi";
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ImportError, error);
    return NULL;

    entrypoint_t entrypoint = NULL;
#else
    static PyObject *dlopenflags_object = NULL;
    if (dlopenflags_object == NULL) {
        dlopenflags_object = CALL_FUNCTION_NO_ARGS(tstate, Nuitka_SysGetObject("getdlopenflags"));
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

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ImportError, error);
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)dlsym(handle, entry_function_name);
#endif // __wasi__
#endif
    assert(entrypoint);

    char const *old_context = NuitkaImport_SwapPackageContext(package);

#if PYTHON_VERSION >= 0x3c0 && !defined(_NUITKA_USE_UNEXPOSED_API)
    char const *base_name = strrchr(full_name, '.');
    PyObject *base_name_obj = NULL;
    PyObject *prefix_name_obj = NULL;
    PyObject *preserved_basename_module = NULL;

    if (base_name != NULL) {
        base_name_obj = Nuitka_String_FromString(base_name + 1);
        preserved_basename_module = Nuitka_GetModule(tstate, base_name_obj);
        Py_XINCREF(preserved_basename_module);

        prefix_name_obj = Nuitka_String_FromStringAndSize(full_name, base_name - full_name + 1);
    }
#endif

    // Finally call into the DLL.
    PGO_onModuleEntered(full_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # calling entrypoint\n", full_name);
    }

    Nuitka_DelModuleString(tstate, full_name);

#if PYTHON_VERSION < 0x300
    (*entrypoint)();
#else
    PyObject *module = (*entrypoint)();
#endif

    if (isVerbose()) {
        PySys_WriteStderr("import %s # return from entrypoint\n", full_name);
    }

#if 0
    PRINT_STRING("FRESH");
    PRINT_ITEM(module);
    PRINT_NEW_LINE();
#endif

    NuitkaImport_SwapPackageContext(old_context);

#if PYTHON_VERSION < 0x300
    PyObject *module = Nuitka_GetModuleString(tstate, full_name);
#endif

    PGO_onModuleExit(name, module == NULL);

    if (unlikely(module == NULL)) {
        if (unlikely(!HAS_ERROR_OCCURRED(tstate))) {
            PyErr_Format(PyExc_SystemError, "dynamic module '%s' not initialized properly", full_name);
        }

        return NULL;
    }

#if PYTHON_VERSION >= 0x300
#if PYTHON_VERSION >= 0x350
    PyModuleDef *def;

    if (Py_TYPE(module) == &PyModuleDef_Type) {
        if (isVerbose()) {
            PySys_WriteStderr("import %s # entrypoint returned module def\n", full_name);
        }

        def = (PyModuleDef *)module;

        PyObject *full_name_obj = Nuitka_String_FromString(full_name);

        PyObject *origin = Nuitka_String_FromFilename(filename);

        PyObject *spec_value = createModuleSpec(tstate, full_name_obj, origin, is_package);
        CHECK_OBJECT(spec_value);

        module = PyModule_FromDefAndSpec(def, spec_value);

        if (unlikely(module == NULL)) {
            Py_DECREF(spec_value);

            PyErr_Format(PyExc_SystemError, "dynamic module '%s' not initialized properly from def", full_name);

            return NULL;
        }

        SET_ATTRIBUTE(tstate, module, const_str_plain___spec__, spec_value);

        setModuleFileValue(tstate, module, filename);

        /* Set __path__ properly, unlike frozen module importer does. */
        PyObject *path_list = _makeDunderPathObject(tstate, origin);

        int res = PyObject_SetAttr(module, const_str_plain___path__, path_list);
        if (unlikely(res != 0)) {
            return NULL;
        }

        Py_DECREF(path_list);

        SET_ATTRIBUTE(tstate, spec_value, const_str_plain__initializing, Py_True);

        Nuitka_SetModule(full_name_obj, module);
        Py_DECREF(full_name_obj);

        res = PyModule_ExecDef(module, def);
        SET_ATTRIBUTE(tstate, spec_value, const_str_plain__initializing, Py_False);

        Py_DECREF(spec_value);
        CHECK_OBJECT(spec_value);

        if (unlikely(res == -1)) {
            return NULL;
        }

        if (isVerbose()) {
            PySys_WriteStderr("import %s # executed module def\n", full_name);
        }

        CHECK_OBJECT(module);

        return module;
    } else {
        def = PyModule_GetDef(module);

        def->m_base.m_init = entrypoint;

        // Set "__spec__" and "__file__" after load.
        setModuleFileValue(tstate, module, filename);
        PyObject *full_name_obj = Nuitka_String_FromString(full_name);
        PyObject *spec_value =
            createModuleSpec(tstate, full_name_obj, LOOKUP_ATTRIBUTE(tstate, module, const_str_plain___file__), false);

        SET_ATTRIBUTE(tstate, module, const_str_plain___spec__, spec_value);

        // Fixup "__package__" after load. It seems some modules ignore _Py_PackageContext value.
        // so we patch it up here if it's None, but a package was specified.
        if (package != NULL) {
            PyObject *package_name = LOOKUP_ATTRIBUTE(tstate, module, const_str_plain___package__);

            if (package_name == Py_None) {
                char package2[1024];
                copyStringSafeN(package2, full_name, dot - full_name, sizeof(package2));

                PyObject *package_name_obj = Nuitka_String_FromString(package2);
                SET_ATTRIBUTE(tstate, module, const_str_plain___package__, package_name_obj);
                Py_DECREF(package_name_obj);
            }

            Py_DECREF(package_name);
        }
    }

    if (likely(def != NULL)) {
        def->m_base.m_init = entrypoint;
    }

#if PYTHON_VERSION >= 0x3d0
    Nuitka_SetModuleString(full_name, module);
#endif
#else
    PyModuleDef *def = PyModule_GetDef(module);

    if (unlikely(def == NULL)) {
        PyErr_Format(PyExc_SystemError, "initialization of %s did not return an extension module", filename);

        return NULL;
    }

    def->m_base.m_init = entrypoint;
#endif

#endif

    // Set filename attribute if not already set, in some branches we don't
    // do it, esp. not for older Python.
    setModuleFileValue(tstate, module, filename);

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
    PyObject *filename_obj = Nuitka_String_FromFilename(filename);

    CHECK_OBJECT(filename_obj);

// See above, we need to correct modules imported if we don't successfully swap
// the package context.
#if PYTHON_VERSION >= 0x3c0 && !defined(_NUITKA_USE_UNEXPOSED_API)
    if (preserved_basename_module != NULL) {
        Nuitka_SetModule(base_name_obj, preserved_basename_module);
        Py_DECREF(preserved_basename_module);
    }

    if (base_name_obj != NULL) {
        PyObject *need_correction = MAKE_LIST_EMPTY(tstate, 0);

        {
            PyObject *modules_dict = Nuitka_GetSysModules();

            Py_ssize_t pos = 0;
            PyObject *key, *value;

            PyObject *base_name_prefix = BINARY_OPERATION_ADD_OBJECT_UNICODE_UNICODE(base_name_obj, const_str_dot);

            while (Nuitka_DictNext(modules_dict, &pos, &key, &value)) {
                // TODO: Should have nuitka_bool return values for these as well maybe.
                PyObject *starts_with_result = UNICODE_STARTSWITH2(tstate, key, base_name_prefix);

                if (CHECK_IF_TRUE(starts_with_result) == 1) {
                    LIST_APPEND0(need_correction, key);
                }

                Py_DECREF(starts_with_result);
            }
        }

        Py_ssize_t n = PyList_GET_SIZE(need_correction);

        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *module_to_correct_name = PyList_GET_ITEM(need_correction, i);

            PyObject *correct_module_name =
                BINARY_OPERATION_ADD_OBJECT_UNICODE_UNICODE(prefix_name_obj, module_to_correct_name);

            PyObject *module_to_correct = Nuitka_GetModule(tstate, module_to_correct_name);
            Nuitka_SetModule(correct_module_name, module_to_correct);

            Nuitka_DelModule(tstate, module_to_correct_name);
        }

        Py_DECREF(base_name_obj);
        Py_DECREF(prefix_name_obj);
    }
#endif

#if PYTHON_VERSION < 0x3d0
    int res = _PyImport_FixupExtensionObject(module, full_name_obj, filename_obj
#if PYTHON_VERSION >= 0x370
                                             ,
                                             Nuitka_GetSysModules()
#endif
    );
#endif

    Py_DECREF(full_name_obj);
    Py_DECREF(filename_obj);

#if PYTHON_VERSION < 0x3d0
    if (unlikely(res == -1)) {
        return NULL;
    }
#endif
#endif

    return module;
}

static void loadTriggeredModule(PyThreadState *tstate, char const *name, char const *trigger_name) {
    char trigger_module_name[2048];

    copyStringSafe(trigger_module_name, name, sizeof(trigger_module_name));
    appendStringSafe(trigger_module_name, trigger_name, sizeof(trigger_module_name));

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(trigger_module_name);

    if (entry != NULL) {
        if (isVerbose()) {
            PySys_WriteStderr("Loading %s\n", trigger_module_name);
        }

        IMPORT_EMBEDDED_MODULE(tstate, trigger_module_name);

        if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
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

#if PYTHON_VERSION >= 0x300
static void _fixupSpecAttribute(PyThreadState *tstate, PyObject *module) {
    PyObject *spec_value = LOOKUP_ATTRIBUTE(tstate, module, const_str_plain___spec__);

    if (spec_value && spec_value != Py_None) {
        if (HAS_ATTR_BOOL(tstate, spec_value, const_str_plain__initializing)) {
            SET_ATTRIBUTE(tstate, spec_value, const_str_plain__initializing, Py_False);
        }
    }
}
#endif

// Pointers to bytecode data.
static char **_bytecode_data = NULL;

static PyObject *loadModule(PyThreadState *tstate, PyObject *module, PyObject *module_name,
                            struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
#ifdef _NUITKA_STANDALONE
    if ((entry->flags & NUITKA_EXTENSION_MODULE_FLAG) != 0) {
        bool is_package = (entry->flags & NUITKA_PACKAGE_FLAG) != 0;

        filename_char_t filename[MAXPATHLEN + 1] = {0};
        _makeModuleCFilenameValue(filename, sizeof(filename) / sizeof(filename_char_t), entry->name, module_name,
                                  is_package);

        callIntoExtensionModule(tstate, entry->name, filename, is_package);
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

        return loadModuleFromCodeObject(tstate, module, code_object, entry->name,
                                        (entry->flags & NUITKA_PACKAGE_FLAG) != 0);
    } else {
        assert((entry->flags & NUITKA_EXTENSION_MODULE_FLAG) == 0);
        assert(entry->python_init_func);

        {
            NUITKA_MAY_BE_UNUSED bool res = Nuitka_SetModule(module_name, module);
            assert(res != false);
        }

        // Run the compiled module code, we get the module returned.
#if PYTHON_VERSION < 0x300
        NUITKA_MAY_BE_UNUSED
#endif
        PyObject *result = entry->python_init_func(tstate, module, entry);
        CHECK_OBJECT_X(result);

#if PYTHON_VERSION >= 0x300
        if (likely(result != NULL)) {
            _fixupSpecAttribute(tstate, result);
        }
#endif
    }

    if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (isVerbose()) {
        PySys_WriteStderr("Loaded %s\n", entry->name);
    }

    return Nuitka_GetModule(tstate, module_name);
}

static PyObject *_EXECUTE_EMBEDDED_MODULE(PyThreadState *tstate, PyObject *module, PyObject *module_name,
                                          char const *name) {
    CHECK_OBJECT(module);
    CHECK_OBJECT(module_name);

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(name);
    bool frozen_import = entry == NULL && hasFrozenModule(name);

    if (entry != NULL || frozen_import) {
        // Execute the "preLoad" code produced for the module potentially. This
        // is from plugins typically, that want to modify things for the the
        // module before loading, to e.g. set a plug-in path, or do some monkey
        // patching in order to make things compatible.
        loadTriggeredModule(tstate, name, "-preLoad");
    }

    PyObject *result = NULL;

    if (entry != NULL) {
#ifdef _NUITKA_EXPERIMENTAL_FORCE_GC_COLLECT_ON_IMPORT
        PyGC_Collect();
#endif

        result = loadModule(tstate, module, module_name, entry);

#ifdef _NUITKA_EXPERIMENTAL_FORCE_GC_COLLECT_ON_IMPORT
        PyGC_Collect();
#endif

        if (unlikely(result == NULL)) {
            return NULL;
        }
    }

    if (frozen_import) {
        PGO_onModuleEntered(name);
        int res = PyImport_ImportFrozenModule((char *)name);
        PGO_onModuleExit(name, res == -1);

        if (unlikely(res == -1)) {
            return NULL;
        }

        if (res == 1) {
            result = Nuitka_GetModule(tstate, module_name);
        }
    }

    if (result != NULL) {
        // Execute the "postLoad" code produced for the module potentially. This
        // is from plugins typically, that want to modify the module immediately
        // after loading, to e.g. set a plug-in path, or do some monkey patching
        // in order to make things compatible.
        loadTriggeredModule(tstate, name, "-postLoad");

        return result;
    }

    Py_INCREF_IMMORTAL(Py_None);
    return Py_None;
}

// Note: This may become an entry point for hard coded imports of compiled
// stuff.
PyObject *IMPORT_EMBEDDED_MODULE(PyThreadState *tstate, char const *name) {
    PyObject *module_name = Nuitka_String_FromString(name);

    // Check if it's already loaded, and don't do it again otherwise.
    PyObject *module = Nuitka_GetModule(tstate, module_name);

    if (module != NULL) {
        Py_DECREF(module_name);
        return module;
    }

#if PYTHON_VERSION < 0x300
    module = PyModule_New(name);
#else
    module = PyModule_NewObject(module_name);
#endif

    PyObject *result = _EXECUTE_EMBEDDED_MODULE(tstate, module, module_name, name);

#if PYTHON_VERSION < 0x350
    if (unlikely(result == NULL)) {
        Nuitka_DelModule(tstate, module_name);
    }
#endif

    Py_DECREF(module_name);

    return result;
}

PyObject *EXECUTE_EMBEDDED_MODULE(PyThreadState *tstate, PyObject *module) {
    PyObject *module_name = LOOKUP_ATTRIBUTE(tstate, module, const_str_plain___name__);
    assert(module_name);

    char const *name = Nuitka_String_AsString(module_name);

    return _EXECUTE_EMBEDDED_MODULE(tstate, module, module_name, name);
}

static PyObject *_nuitka_loader_load_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|O:load_module", (char **)_kw_list_find_module, &module_name,
                                          &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    assert(module_name);
    assert(Nuitka_String_Check(module_name));

    char const *name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("Loading %s\n", name);
    }

    PyThreadState *tstate = PyThreadState_GET();

#ifndef _NUITKA_STANDALONE
    if (installed_extension_modules != NULL) {
        PyObject *extension_module_filename = DICT_GET_ITEM0(tstate, installed_extension_modules, module_name);

        if (extension_module_filename != NULL) {
            // TODO: Should we not set __file__ for the module here, but there is no object.
            return callIntoInstalledExtensionModule(tstate, module_name, extension_module_filename);
        }
    }
#endif

    return IMPORT_EMBEDDED_MODULE(tstate, name);
}

static char const *_kw_list_is_package[] = {"fullname", NULL};

static PyObject *_nuitka_loader_is_package(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:is_package", (char **)_kw_list_is_package, &module_name);

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

    Py_INCREF_IMMORTAL(result);
    return result;
}

static char const *_kw_list_iter_modules[] = {"package", NULL};

static PyObject *_nuitka_loader_iter_modules(struct Nuitka_LoaderObject *self, PyObject *args, PyObject *kwds) {
    PyObject *prefix;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:iter_modules", (char **)_kw_list_iter_modules, &prefix);

    if (unlikely(res == 0)) {
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyThreadState *tstate = PyThreadState_GET();

    PyObject *result = MAKE_LIST_EMPTY(tstate, 0);

    struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;
    assert(current);

    char const *s;

    if (self->m_loader_entry) {
        s = self->m_loader_entry->name;
    } else {
        s = "";
    }

    while (current->name != NULL) {
        if ((current->flags & NUITKA_TRANSLATED_FLAG) != 0) {
            current->name = UN_TRANSLATE(current->name);
            current->flags -= NUITKA_TRANSLATED_FLAG;
        }

        int c = strncmp(s, current->name, strlen(s));

        if (c != 0) {
            current++;
            continue;
        }

        if (strcmp(current->name, "__main__") == 0) {
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

        PyObject *name;
        if (self->m_loader_entry) {
            name = Nuitka_String_FromString(current->name + strlen(s) + 1);
        } else {
            name = Nuitka_String_FromString(current->name);
        }

        if (CHECK_IF_TRUE(prefix)) {
            PyObject *old = name;
            name = PyUnicode_Concat(prefix, name);
            Py_DECREF(old);
        }

        PyObject *r = MAKE_TUPLE_EMPTY(tstate, 2);
        PyTuple_SET_ITEM(r, 0, name);
        PyTuple_SET_ITEM_IMMORTAL(r, 1, BOOL_FROM((current->flags & NUITKA_PACKAGE_FLAG) != 0));

        LIST_APPEND1(result, r);

        current++;
    }

    return result;
}

static PyObject *getModuleDirectory(PyThreadState *tstate, struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
#if defined(_NUITKA_FREEZER_HAS_FILE_PATH)
#if defined(_WIN32)
    wchar_t buffer[1024];
    buffer[0] = 0;

    appendWStringSafeW(buffer, entry->file_path, sizeof(buffer));
    stripFilenameW(buffer);
    PyObject *dir_name = NuitkaUnicode_FromWideChar(buffer, -1);
#else
    char buffer[1024];
    copyStringSafe(buffer, entry->file_path, sizeof(buffer));

    PyObject *dir_name = Nuitka_String_FromString(dirname(buffer));
#endif
#else
    PyObject *module_name;
    if ((entry->flags & NUITKA_PACKAGE_FLAG) != 0) {
        module_name = Nuitka_String_FromString(entry->name);
    } else {
        char buffer[1024];
        copyStringSafe(buffer, entry->name, sizeof(buffer));

        char *dot = strrchr(buffer, '.');
        if (dot != NULL) {
            *dot = 0;
        }

        module_name = Nuitka_String_FromString(buffer);
    }

#if PYTHON_VERSION < 0x300
    PyObject *module_path = STR_REPLACE3(tstate, module_name, const_str_dot, getPathSeparatorStringObject());
#else
    PyObject *module_path = UNICODE_REPLACE3(tstate, module_name, const_str_dot, getPathSeparatorStringObject());
#endif
    Py_DECREF(module_name);

    if (unlikely(module_path == NULL)) {
        return NULL;
    }

    PyObject *dir_name = MAKE_RELATIVE_PATH(module_path);
    Py_DECREF(module_path);
#endif

    return dir_name;
}

#if PYTHON_VERSION >= 0x300
// Used in module template too, therefore exported.
PyObject *getImportLibBootstrapModule(void) {
    static PyObject *importlib = NULL;
    if (importlib == NULL) {
        importlib = PyImport_ImportModule("importlib._bootstrap");
    }

    return importlib;
}
#endif

static PyObject *getModuleFileValue(PyThreadState *tstate, struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
    PyObject *dir_name = getModuleDirectory(tstate, entry);

    char filename_buffer[1024];

    if ((entry->flags & NUITKA_PACKAGE_FLAG) != 0) {
        copyStringSafe(filename_buffer, "__init__", sizeof(filename_buffer));
    } else {
        char const *basename = strrchr(entry->name, '.');

        if (basename == NULL) {
            basename = entry->name;
        } else {
            basename += 1;
        }

        copyStringSafe(filename_buffer, basename, sizeof(filename_buffer));
    }

    if ((entry->flags & NUITKA_EXTENSION_MODULE_FLAG) != 0) {
#if defined(_WIN32)
        appendStringSafe(filename_buffer, ".pyd", sizeof(filename_buffer));
#else
        appendStringSafe(filename_buffer, ".so", sizeof(filename_buffer));
#endif
    } else {
        appendStringSafe(filename_buffer, ".py", sizeof(filename_buffer));
    }

    PyObject *module_filename = Nuitka_String_FromString(filename_buffer);

    PyObject *result = JOIN_PATH2(dir_name, module_filename);

    Py_DECREF(module_filename);

    return result;
}

#if PYTHON_VERSION >= 0x300

static PyObject *_nuitka_loader_repr_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module;
    PyObject *unused;

    int res =
        PyArg_ParseTupleAndKeywords(args, kwds, "O|O:module_repr", (char **)_kw_list_find_module, &module, &unused);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    return PyUnicode_FromFormat("<module '%s' from %R>", PyModule_GetName(module),
                                Nuitka_GetFilenameObject(tstate, module));
}

static PyObject *getModuleSpecClass(PyObject *importlib_module) {
    static PyObject *module_spec_class = NULL;

    if (module_spec_class == NULL) {
        module_spec_class = PyObject_GetAttrString(importlib_module, "ModuleSpec");
    }

    return module_spec_class;
}

static PyObject *createModuleSpec(PyThreadState *tstate, PyObject *module_name, PyObject *origin, bool is_package) {
    CHECK_OBJECT(module_name);
    assert(Nuitka_String_Check(module_name));
    CHECK_OBJECT_X(origin);

    PyObject *importlib_module = getImportLibBootstrapModule();

    if (unlikely(importlib_module == NULL)) {
        return NULL;
    }

    PyObject *module_spec_class = getModuleSpecClass(importlib_module);

    if (unlikely(module_spec_class == NULL)) {
        return NULL;
    }

    PyObject *args = MAKE_TUPLE2(tstate, module_name, (PyObject *)&Nuitka_Loader_Type);

    PyObject *kw_values[] = {is_package ? Py_True : Py_False, origin};

    char const *kw_keys[] = {"is_package", "origin"};

    PyObject *kw_args = MAKE_DICT_X_CSTR(kw_keys, kw_values, sizeof(kw_values) / sizeof(PyObject *));

    PyObject *result = CALL_FUNCTION(tstate, module_spec_class, args, kw_args);

    Py_DECREF(args);
    Py_DECREF(kw_args);

    return result;
}

#ifndef _NUITKA_STANDALONE
// We might have to load stuff from installed modules in our package namespaces.
static PyObject *createModuleSpecViaPathFinder(PyThreadState *tstate, PyObject *module_name,
                                               char const *parent_module_name) {
    if (scanModuleInPackagePath(tstate, module_name, parent_module_name)) {
        return createModuleSpec(tstate, module_name, NULL, false);
    } else {
        // Without error this means we didn't make it.
        return NULL;
    }
}
#endif

static char const *_kw_list_find_spec[] = {"fullname", "is_package", "path", NULL};

static PyObject *_nuitka_loader_find_spec(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;
    PyObject *unused1; // We ignore "is_package"
    PyObject *unused2; // We ignore "path"

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:find_spec", (char **)_kw_list_find_spec, &module_name,
                                          &unused1, &unused2);

    if (unlikely(res == 0)) {
        return NULL;
    }

    char const *full_name = Nuitka_String_AsString(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # considering responsibility (find_spec)\n", full_name);
    }

    struct Nuitka_MetaPathBasedLoaderEntry const *entry = findEntry(full_name);

    PyThreadState *tstate = PyThreadState_GET();

#ifndef _NUITKA_STANDALONE
    // We need to deal with things located in compiled packages, that were not included,
    // e.g. extension modules, but also other files, that were asked to not be included
    // or added later.
    if (entry == NULL) {
        entry = findContainingPackageEntry(full_name);

        if (entry != NULL) {
            PyObject *result = createModuleSpecViaPathFinder(tstate, module_name, entry->name);

            if (result != NULL) {
                if (isVerbose()) {
                    PySys_WriteStderr("import %s # claimed responsibility (%s, contained in compiled package %s)\n",
                                      full_name, getEntryModeString(entry), entry->name);
                }

                return result;
            }

            if (HAS_ERROR_OCCURRED(tstate)) {
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

        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }

    if (isVerbose()) {
        PySys_WriteStderr("import %s # claimed responsibility (%s)\n", Nuitka_String_AsString(module_name),
                          getEntryModeString(entry));
    }

    return createModuleSpec(tstate, module_name, getModuleFileValue(tstate, entry),
                            (entry->flags & NUITKA_PACKAGE_FLAG) != 0);
}

#if PYTHON_VERSION >= 0x350
static char const *_kw_list_create_module[] = {"spec", NULL};

static PyObject *_nuitka_loader_create_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *spec;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:create_module", (char **)_kw_list_create_module, &spec);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *module_name = PyObject_GetAttr(spec, const_str_plain_name);

    if (unlikely(module_name == NULL)) {
        return NULL;
    }

    if (isVerbose()) {
        PySys_WriteStderr("import %s # created module\n", Nuitka_String_AsString(module_name));
    }

    PyObject *result = PyModule_NewObject(module_name);

    Py_DECREF(module_name);

    return result;
}

static char const *_kw_list_exec_module[] = {"module", NULL};

static PyObject *_nuitka_loader_exec_module(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:exec_module", (char **)_kw_list_exec_module, &module);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *module_name = PyObject_GetAttr(module, const_str_plain___name__);
    CHECK_OBJECT(module_name);

    if (isVerbose()) {
        PySys_WriteStderr("import %s # execute module\n", Nuitka_String_AsString(module_name));
    }

    PyThreadState *tstate = PyThreadState_GET();

    // During spec creation, we have populated the dictionary with a filename to load from
    // for extension modules that were found installed in the system and below our package.
#ifndef _NUITKA_STANDALONE
    if (installed_extension_modules != NULL) {
        PyObject *extension_module_filename = DICT_GET_ITEM0(tstate, installed_extension_modules, module_name);

        if (extension_module_filename != NULL) {
            // Set filename attribute
            bool b_res = SET_ATTRIBUTE(tstate, module, const_str_plain___file__, extension_module_filename);

            if (unlikely(b_res == false)) {
                // Might be refuted, which wouldn't be harmful.
                CLEAR_ERROR_OCCURRED(tstate);
            }

            return callIntoInstalledExtensionModule(tstate, module_name, extension_module_filename);
        }
    }
#endif

    return EXECUTE_EMBEDDED_MODULE(tstate, module);
}

#if PYTHON_VERSION >= 0x370

// The resource reader class is implemented in a separate file.
#include "MetaPathBasedLoaderResourceReader.c"

static PyObject *_nuitka_loader_get_resource_reader(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *module_name;

    int res =
        PyArg_ParseTupleAndKeywords(args, kwds, "O:get_resource_reader", (char **)_kw_list_exec_module, &module_name);

    if (unlikely(res == 0)) {
        return NULL;
    }

    char const *name = Nuitka_String_AsString(module_name);

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(name);

    if (entry) {
        if (isVerbose()) {
            PySys_WriteStderr("import %s # get_resource_reader (%s)\n", name, getEntryModeString(entry));
        }

        return Nuitka_ResourceReader_New(entry);
    }

    PyErr_Format(PyExc_RuntimeError, "Requested resource reader for unhandled module %s", module_name);
    return NULL;
}

#endif

#endif

#endif

static char const *_kw_list_find_distributions[] = {"context", NULL};

static PyObject *_nuitka_loader_find_distributions(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *context;

    int res =
        PyArg_ParseTupleAndKeywords(args, kwds, "O:find_distributions", (char **)_kw_list_find_distributions, &context);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *name = PyObject_GetAttr(context, const_str_plain_name);

    if (unlikely(name == NULL)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *temp = MAKE_LIST_EMPTY(tstate, 0);

    Py_ssize_t pos = 0;
    PyObject *distribution_name;

    while (Nuitka_DistributionNext(&pos, &distribution_name)) {
        bool include = false;
        if (name == Py_None) {
            include = true;
        } else {
            nuitka_bool cmp_res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(name, distribution_name);

            if (unlikely(cmp_res == NUITKA_BOOL_EXCEPTION)) {
                Py_DECREF(name);
                return NULL;
            }

            include = cmp_res == NUITKA_BOOL_TRUE;
        }

        if (include) {
            // Create a distribution object from our data.
            PyObject *distribution = Nuitka_Distribution_New(tstate, distribution_name);

            if (distribution == NULL) {
                Py_DECREF(temp);
                return NULL;
            }

            LIST_APPEND1(temp, distribution);
        }
    }

    // We are expected to return an iterator.
    PyObject *result = MAKE_ITERATOR_INFALLIBLE(temp);

    Py_DECREF(temp);
    return result;
}

static char const *_kw_list_sys_path_hook[] = {"path", NULL};

static PyObject *_nuitka_loader_sys_path_hook(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *path;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:sys_path_hook", (char **)_kw_list_sys_path_hook, &path);

    if (unlikely(res == 0)) {
        return NULL;
    }

#if 0
    PRINT_STRING("CONSIDER PATH:");
    PRINT_ITEM(path);
    PRINT_NEW_LINE();
#endif

    struct Nuitka_MetaPathBasedLoaderEntry *entry = loader_entries;
    assert(entry);

    PyThreadState *tstate = PyThreadState_GET();

    while (entry->name != NULL) {
        if ((entry->flags & NUITKA_TRANSLATED_FLAG) != 0) {
            entry->name = UN_TRANSLATE(entry->name);
            entry->flags -= NUITKA_TRANSLATED_FLAG;
        }

        if ((entry->flags & NUITKA_PACKAGE_FLAG) != 0) {
            PyObject *module_directory = getModuleDirectory(tstate, entry);

#if 0
            PRINT_STRING(entry->name);
            PRINT_STRING(" ");
            PRINT_ITEM(module_directory);
            PRINT_NEW_LINE();
#endif

            nuitka_bool cmp_res = compareFilePaths(tstate, module_directory, path);

            if (unlikely(cmp_res == NUITKA_BOOL_EXCEPTION)) {
                return NULL;
            }

            // Create the loader for the module.
            if (cmp_res == NUITKA_BOOL_TRUE) {
                return Nuitka_Loader_New(entry);
            }
        }

        entry++;
    }

    SET_CURRENT_EXCEPTION_TYPE0(tstate, PyExc_ImportError);
    return NULL;
}

static PyMethodDef Nuitka_Loader_methods[] = {
    {"iter_modules", (PyCFunction)_nuitka_loader_iter_modules, METH_VARARGS | METH_KEYWORDS, NULL},
    {"get_data", (PyCFunction)_nuitka_loader_get_data, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"find_module", (PyCFunction)_nuitka_loader_find_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"load_module", (PyCFunction)_nuitka_loader_load_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"is_package", (PyCFunction)_nuitka_loader_is_package, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#if PYTHON_VERSION >= 0x300
    {"module_repr", (PyCFunction)_nuitka_loader_repr_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"find_spec", (PyCFunction)_nuitka_loader_find_spec, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#endif
#if PYTHON_VERSION >= 0x350
    {"create_module", (PyCFunction)_nuitka_loader_create_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
    {"exec_module", (PyCFunction)_nuitka_loader_exec_module, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},
#endif
#if PYTHON_VERSION >= 0x370
    {"get_resource_reader", (PyCFunction)_nuitka_loader_get_resource_reader, METH_STATIC | METH_VARARGS | METH_KEYWORDS,
     NULL},
#endif

    {"find_distributions", (PyCFunction)_nuitka_loader_find_distributions, METH_STATIC | METH_VARARGS | METH_KEYWORDS,
     NULL},

    {"sys_path_hook", (PyCFunction)_nuitka_loader_sys_path_hook, METH_STATIC | METH_VARARGS | METH_KEYWORDS, NULL},

    {NULL, NULL} // terminator
};

static PyObject *Nuitka_Loader_tp_repr(struct Nuitka_LoaderObject *loader) {
    if (loader->m_loader_entry == NULL) {
        // TODO: Indicate in module mode, which one it is for.
        return Nuitka_String_FromString("<nuitka_module_loader>");
    } else {
        return Nuitka_String_FromFormat("<nuitka_module_loader for '%s'>", loader->m_loader_entry->name);
    }
}

#include "nuitka/freelists.h"

// TODO: A free list is not the right thing for those, they are probably living forever, but it's
// no big harm too, but make it small, maybe be allowing a toggle that makes a specific macro not
// use the free list mechanism at all.

// Freelist setup
#define MAX_LOADER_FREE_LIST_COUNT 10
static struct Nuitka_LoaderObject *free_list_loaders = NULL;
static int free_list_loaders_count = 0;

static void Nuitka_Loader_tp_dealloc(struct Nuitka_LoaderObject *loader) {
    Nuitka_GC_UnTrack(loader);

    releaseToFreeList(free_list_loaders, loader, MAX_LOADER_FREE_LIST_COUNT);
}

static int Nuitka_Loader_tp_traverse(struct Nuitka_LoaderObject *loader, visitproc visit, void *arg) { return 0; }

static PyObject *Nuitka_Loader_get_name(struct Nuitka_LoaderObject *loader, void *closure) {
    PyObject *result = Nuitka_String_FromString(loader->m_loader_entry->name);

    return result;
}
static PyObject *Nuitka_Loader_get_path(struct Nuitka_LoaderObject *loader, void *closure) {
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *result = getModuleFileValue(tstate, loader->m_loader_entry);

    return result;
}

static PyObject *Nuitka_Loader_get__module__(struct Nuitka_LoaderObject *loader, void *closure) {
    PyObject *result = const_str_plain___nuitka__;

    Py_INCREF_IMMORTAL(result);
    return result;
}

static PyGetSetDef Nuitka_Loader_tp_getset[] = {{(char *)"__module__", (getter)Nuitka_Loader_get__module__, NULL, NULL},
                                                {(char *)"name", (getter)Nuitka_Loader_get_name, NULL, NULL},
                                                {(char *)"path", (getter)Nuitka_Loader_get_path, NULL, NULL},
                                                {NULL}};

PyTypeObject Nuitka_Loader_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "nuitka_module_loader",
    sizeof(struct Nuitka_LoaderObject),      // tp_basicsize
    0,                                       // tp_itemsize
    (destructor)Nuitka_Loader_tp_dealloc,    // tp_dealloc
    0,                                       // tp_print
    0,                                       // tp_getattr
    0,                                       // tp_setattr
    0,                                       // tp_reserved
    (reprfunc)Nuitka_Loader_tp_repr,         // tp_repr
    0,                                       // tp_as_number
    0,                                       // tp_as_sequence
    0,                                       // tp_as_mapping
    0,                                       // tp_hash
    0,                                       // tp_call
    0,                                       // tp_str
    0,                                       // tp_getattro (PyObject_GenericGetAttr)
    0,                                       // tp_setattro
    0,                                       // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, // tp_flags
    0,                                       // tp_doc
    (traverseproc)Nuitka_Loader_tp_traverse, // tp_traverse
    0,                                       // tp_clear
    0,                                       // tp_richcompare
    0,                                       // tp_weaklistoffset
    0,                                       // tp_iter
    0,                                       // tp_iternext
    Nuitka_Loader_methods,                   // tp_methods
    0,                                       // tp_members
    Nuitka_Loader_tp_getset,                 // tp_getset
};

/* Used by modules to register child loaders for packages. */
PyObject *Nuitka_Loader_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
    struct Nuitka_LoaderObject *result;

    allocateFromFreeListFixed(free_list_loaders, struct Nuitka_LoaderObject, Nuitka_Loader_Type);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;

    return (PyObject *)result;
}

#ifdef _NUITKA_MODULE
void updateMetaPathBasedLoaderModuleRoot(char const *module_root_name) {
    assert(module_root_name != NULL);
    char const *last_dot = strrchr(module_root_name, '.');

    if (last_dot != NULL) {
        struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;
        assert(current);

        while (current->name != NULL) {
            if ((current->flags & NUITKA_TRANSLATED_FLAG) != 0) {
                current->name = UN_TRANSLATE(current->name);
                current->flags -= NUITKA_TRANSLATED_FLAG;
            }

            char name[2048];

            if (strcmp(last_dot + 1, current->name) == 0) {
                copyStringSafeN(name, module_root_name, last_dot - module_root_name + 1, sizeof(name));
                appendStringSafe(name, current->name, sizeof(name));

                current->name = strdup(name);
            } else if (strncmp(last_dot + 1, current->name, strlen(last_dot + 1)) == 0 &&
                       current->name[strlen(last_dot + 1)] == '.') {
                copyStringSafeN(name, module_root_name, last_dot - module_root_name + 1, sizeof(name));
                appendStringSafe(name, current->name, sizeof(name));

                current->name = strdup(name);
            }

            current++;
        }
    }
}
#endif

void registerMetaPathBasedLoader(struct Nuitka_MetaPathBasedLoaderEntry *_loader_entries,
                                 unsigned char **bytecode_data) {
    // Do it only once.
    if (loader_entries) {
        assert(_loader_entries == loader_entries);

        return;
    }

    _bytecode_data = (char **)bytecode_data;

    if (isVerbose()) {
        PySys_WriteStderr("Setup nuitka compiled module/bytecode/extension importer.\n");
    }

    loader_entries = _loader_entries;

#if defined(_NUITKA_MODULE) && PYTHON_VERSION < 0x3c0
    if (_Py_PackageContext != NULL) {
        updateMetaPathBasedLoaderModuleRoot(_Py_PackageContext);
    }
#endif

    Nuitka_PyType_Ready(&Nuitka_Loader_Type, NULL, true, false, false, false, false);

#ifdef _NUITKA_EXE
    {
        NUITKA_MAY_BE_UNUSED int res =
            PyDict_SetItemString((PyObject *)dict_builtin, "__nuitka_loader_type", (PyObject *)&Nuitka_Loader_Type);
        assert(res == 0);
    }
#endif

#if PYTHON_VERSION >= 0x370
    Nuitka_PyType_Ready(&Nuitka_ResourceReader_Type, NULL, true, false, false, false, false);
#endif

    // Register it as a meta path loader.
    PyObject *global_loader = Nuitka_Loader_New(NULL);

    LIST_INSERT_CONST(Nuitka_SysGetObject("meta_path"),
#if PYTHON_VERSION < 0x300
                      0,
#else
                      2,
#endif

                      global_loader);

    // Our "sys.path_hooks" entry uses "os.path" to compare filenames, so we need
    // to load it without.
    PyThreadState *tstate = PyThreadState_GET();
    IMPORT_HARD_OS_PATH(tstate);

    // Register it as a sys.path_hook
    LIST_INSERT_CONST(Nuitka_SysGetObject("path_hooks"), 0, PyObject_GetAttrString(global_loader, "sys_path_hook"));
}

#if defined(_NUITKA_STANDALONE)
// This is called for the technical module imported early on during interpreter
// into, to still get compatible "__file__" attributes.
void setEarlyFrozenModulesFileAttribute(PyThreadState *tstate) {
    PyObject *sys_modules = Nuitka_GetSysModules();
    Py_ssize_t pos = 0;
    PyObject *key, *value;

    PyObject *builtin_module_names = Nuitka_SysGetObject("builtin_module_names");

    while (Nuitka_DictNext(sys_modules, &pos, &key, &value)) {
        if (key != NULL && value != NULL && PyModule_Check(value)) {
            bool is_package = HAS_ATTR_BOOL(tstate, value, const_str_plain___path__);

            if (is_package || HAS_ATTR_BOOL(tstate, value, const_str_plain___file__) ||
                PySequence_Contains(builtin_module_names, key) == 0) {
                PyObject *file_value = MAKE_RELATIVE_PATH_FROM_NAME(Nuitka_String_AsString(key), is_package, false);
                PyObject_SetAttr(value, const_str_plain___file__, file_value);
                Py_DECREF(file_value);
                CHECK_OBJECT(file_value);
            }
        }
    }

    assert(!HAS_ERROR_OCCURRED(tstate));
}

#endif

// The importlib distribution class is implemented in a separate file.
#include "MetaPathBasedLoaderImportlibMetadataDistribution.c"

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
