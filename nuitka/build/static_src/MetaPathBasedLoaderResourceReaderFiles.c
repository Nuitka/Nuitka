//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This implements the resource reader of C compiled modules and
// shared library extension modules bundled for standalone mode with
// newer Python.

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#include "nuitka/unfreezing.h"

static PyObject *getModuleDirectory(PyThreadState *tstate, struct Nuitka_MetaPathBasedLoaderEntry const *entry,
                                    PyObject *module_name);
static void Nuitka_LoaderEntryDisplayName(struct Nuitka_MetaPathBasedLoaderEntry const *entry, char *buffer,
                                          size_t buffer_size);
#endif

struct Nuitka_ResourceReaderFilesObject {
    PyObject_HEAD

        // The loader entry, to know this is for one package exactly.
        struct Nuitka_MetaPathBasedLoaderEntry const *m_loader_entry;

    // The runtime name of the module, if known.
    PyObject *m_module_name;

    // The path relative to the entry, if e.g. joinpath is used
    PyObject *m_path;
};

static PyTypeObject Nuitka_ResourceReaderFiles_Type;

static PyObject *Nuitka_ResourceReaderFiles_New(PyThreadState *tstate,
                                                struct Nuitka_MetaPathBasedLoaderEntry const *entry,
                                                PyObject *module_name, PyObject *path);

static PyObject *_Nuitka_ResourceReaderFiles_JoinChild(PyThreadState *tstate, PyObject *base, PyObject *child) {
    PyObject *child_fspath = OS_FSPATH(tstate, child);
    if (unlikely(child_fspath == NULL)) {
        return NULL;
    }

    if (unlikely(!PyUnicode_Check(child_fspath))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(
            "argument should be a str or an os.PathLike object where __fspath__ returns a str, not '%s'", child_fspath);
        Py_DECREF(child_fspath);
        return NULL;
    }

    if (unlikely(!PyUnicode_CheckExact(child_fspath))) {
        PyObject *exact_str = Nuitka_PyUnicode_FromObject(child_fspath);
        Py_DECREF(child_fspath);
        CHECK_OBJECT(exact_str);
        child_fspath = exact_str;
    }

    if (base == const_str_empty) {
        return child_fspath;
    }

    PyObject *paths[2] = {base, child_fspath};
    PyObject *result = OS_PATH_JOIN(tstate, paths, 2);
    Py_DECREF(child_fspath);
    return result;
}

static PyObject *_Nuitka_ResourceReaderFiles_GetPath(PyThreadState *tstate,
                                                     struct Nuitka_ResourceReaderFilesObject const *files) {
    if (files->m_path == const_str_empty) {
        return getModuleDirectory(tstate, files->m_loader_entry, files->m_module_name);
    }

    PyObject *is_abs = OS_PATH_ISABS(tstate, files->m_path);
    if (unlikely(is_abs == NULL)) {
        return NULL;
    }

    PyObject *result;
    if (is_abs == Py_True) {
        result = Py_NewRef(files->m_path);
    } else {
        PyObject *module_dir = getModuleDirectory(tstate, files->m_loader_entry, files->m_module_name);
        if (unlikely(module_dir == NULL)) {
            Py_DECREF(is_abs);
            return NULL;
        }

        PyObject *paths[2] = {module_dir, files->m_path};
        result = OS_PATH_JOIN(tstate, paths, 2);
        Py_DECREF(module_dir);
    }

    Py_DECREF(is_abs);

    return result;
}

static PyObject *_Nuitka_ResourceReaderFiles_GetBasename(PyThreadState *tstate,
                                                         struct Nuitka_ResourceReaderFilesObject const *files) {
    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(path == NULL)) {
        return NULL;
    }

    PyObject *basename = OS_PATH_BASENAME(tstate, path);
    Py_DECREF(path);
    if (unlikely(basename == NULL)) {
        return NULL;
    }

    if (unlikely(!PyUnicode_Check(basename))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("basename() returned non-string (type %s)", basename);
        Py_DECREF(basename);
        return NULL;
    }

    if (unlikely(!PyUnicode_CheckExact(basename))) {
        PyObject *exact_basename = Nuitka_PyUnicode_FromObject(basename);
        Py_DECREF(basename);
        CHECK_OBJECT(exact_basename);
        return exact_basename;
    }

#if PYTHON_VERSION < 0x3c0
    if (unlikely(PyUnicode_READY(basename) == -1)) {
        Py_DECREF(basename);
        return NULL;
    }
#endif

    return basename;
}

static void Nuitka_ResourceReaderFiles_tp_dealloc(PyObject *self) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    Nuitka_GC_UnTrack(self);

    Py_XDECREF(files->m_module_name);
    Py_DECREF(files->m_path);

    PyObject_GC_Del(files);
}

static PyObject *Nuitka_ResourceReaderFiles_tp_repr(PyObject *self) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    char display_name[NUITKA_LOADER_NAME_MAX_LEN];
    Nuitka_LoaderEntryDisplayName(files->m_loader_entry, display_name, sizeof(display_name));

    return PyUnicode_FromFormat("<nuitka_resource_reader_files for package '%s' file %R>", display_name, files->m_path);
}

static PyObject *Nuitka_ResourceReaderFiles_tp_str(PyObject *self) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    PyThreadState *tstate = PyThreadState_GET();
    return _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
}

static int Nuitka_ResourceReaderFiles_tp_traverse(PyObject *self, visitproc visit, void *arg) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    if (files->m_module_name != NULL && !Nuitka_String_CheckExact(files->m_module_name)) {
        Py_VISIT(files->m_module_name);
    }
    if (!Nuitka_String_CheckExact(files->m_path)) {
        Py_VISIT(files->m_path);
    }

    return 0;
}

static PyObject *Nuitka_ResourceReaderFiles_iterdir(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *file_path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(file_path == NULL)) {
        return NULL;
    }

    PyObject *file_names = OS_LISTDIR(tstate, file_path);
    Py_DECREF(file_path);

    // TODO: Actually we ought to behave like a generator and delay this error,
    // but we currently spare us the effort and raise this immediately.
    if (unlikely(file_names == NULL)) {
        return NULL;
    }

    PyObject *files_objects = MAKE_LIST_EMPTY(tstate, 0);
    CHECK_OBJECT(files_objects);

    Py_ssize_t n = PyList_GET_SIZE(file_names);
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *file_name = PyList_GET_ITEM(file_names, i);
        CHECK_OBJECT(file_name);

        PyObject *joined = _Nuitka_ResourceReaderFiles_JoinChild(tstate, files->m_path, file_name);
        if (unlikely(joined == NULL)) {
            Py_DECREF(files_objects);
            Py_DECREF(file_names);
            return NULL;
        }

        PyObject *files_object =
            Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, files->m_module_name, joined);
        Py_DECREF(joined);
        CHECK_OBJECT(files_object);

        {
            NUITKA_MAY_BE_UNUSED bool res = LIST_APPEND1(files_objects, files_object);
            assert(res);
        }
    }

    Py_DECREF(file_names);

    PyObject *result = MAKE_ITERATOR_INFALLIBLE(files_objects);
    Py_DECREF(files_objects);

    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_read_bytes(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    if (unlikely(file_name == NULL)) {
        return NULL;
    }

    PyObject *result = GET_FILE_BYTES(tstate, file_name);
    Py_DECREF(file_name);
    return result;
}

#if PYTHON_VERSION >= 0x3d0
static char const *_kw_list_encoding_errors[] = {"encoding", "errors", NULL};
#else
static char const *_kw_list_encoding[] = {"encoding", NULL};
#endif

static PyObject *Nuitka_ResourceReaderFiles_read_text(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    PyObject *encoding = NULL;

    PyObject *errors = NULL;

    // The "errors" argument was added in Python 3.13.
#if PYTHON_VERSION >= 0x3d0
    int res =
        PyArg_ParseTupleAndKeywords(args, kwds, "|OO:read_text", (char **)_kw_list_encoding_errors, &encoding, &errors);
#else
    int res = PyArg_ParseTupleAndKeywords(args, kwds, "|O:read_text", (char **)_kw_list_encoding, &encoding);
#endif

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    if (unlikely(file_name == NULL)) {
        return NULL;
    }

    PyObject *file_object =
        BUILTIN_OPEN(tstate, file_name, const_str_plain_r, Py_True, encoding, errors, NULL, NULL, NULL);

    Py_DECREF(file_name);

    if (unlikely(file_object == NULL)) {
        return NULL;
    }

    PyObject *read_method = LOOKUP_ATTRIBUTE(tstate, file_object, const_str_plain_read);
    Py_DECREF(file_object);

    if (unlikely(read_method == NULL)) {
        return NULL;
    }

    PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, read_method);
    Py_DECREF(read_method);
    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_exists(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    PyThreadState *tstate = PyThreadState_GET();
    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(file_name == NULL)) {
        return NULL;
    }

    PyObject *result = OS_PATH_FILE_EXISTS(tstate, file_name);
    Py_DECREF(file_name);
    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_is_dir(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    PyThreadState *tstate = PyThreadState_GET();
    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(file_name == NULL)) {
        return NULL;
    }

    PyObject *result = OS_PATH_FILE_ISDIR(tstate, file_name);
    Py_DECREF(file_name);
    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_is_file(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    PyThreadState *tstate = PyThreadState_GET();
    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(file_name == NULL)) {
        return NULL;
    }

    PyObject *result = OS_PATH_FILE_ISFILE(tstate, file_name);
    Py_DECREF(file_name);
    return result;
}

static char const *_kw_list_joinpath[] = {"child", NULL};

// Functions out there, some accept "child", and accept varargs, lets be compatible with both.

static PyObject *Nuitka_ResourceReaderFiles_joinpath(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *joined;

    if (kwds != NULL) {
        PyObject *child;

        int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:joinpath", (char **)_kw_list_joinpath, &child);

        if (unlikely(res == 0)) {
            return NULL;
        }

        joined = _Nuitka_ResourceReaderFiles_JoinChild(tstate, files->m_path, child);

        if (unlikely(joined == NULL)) {
            return NULL;
        }
    } else {
        joined = Py_NewRef(files->m_path);

        Py_ssize_t n = PyTuple_GET_SIZE(args);
        for (Py_ssize_t i = 0; i < n; ++i) {
            PyObject *child = PyTuple_GET_ITEM(args, i);

            PyObject *old = joined;
            joined = _Nuitka_ResourceReaderFiles_JoinChild(tstate, old, child);
            Py_DECREF(old);

            if (unlikely(joined == NULL)) {
                return NULL;
            }
        }
    }

    PyObject *result = Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, files->m_module_name, joined);

    Py_DECREF(joined);

    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_as_posix(PyObject *files_obj, PyObject *args) {
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(path == NULL)) {
        return NULL;
    }

#ifdef _WIN32
    if (unlikely(!PyUnicode_CheckExact(path))) {
        PyObject *exact_path = Nuitka_PyUnicode_FromObject(path);
        Py_DECREF(path);
        CHECK_OBJECT(exact_path);
        path = exact_path;
    }

    PyObject *result = UNICODE_REPLACE3(tstate, path, const_str_backslash, const_str_slash);
    Py_DECREF(path);

    return result;
#else
    return path;
#endif
}

PyObject *Nuitka_ResourceReaderFiles_nb_truediv(PyObject *self, PyObject *arg) {
    if (unlikely(!Nuitka_PyObject_TypeCheck(self, &Nuitka_ResourceReaderFiles_Type))) {
        return Py_NewRef_IMMORTAL(Py_NotImplemented);
    }

    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *joined = _Nuitka_ResourceReaderFiles_JoinChild(tstate, files->m_path, arg);
    if (unlikely(joined == NULL)) {
        return NULL;
    }

    PyObject *result = Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, files->m_module_name, joined);
    Py_DECREF(joined);

    return result;
}

static char const *_kw_list_open[] = {"mode", "buffering", "encoding", "errors", "newline", NULL};

static PyObject *Nuitka_ResourceReaderFiles_open(PyObject *files_obj, PyObject *args, PyObject *kwds) {
    CHECK_OBJECT(files_obj);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    PyObject *mode = NULL;
    PyObject *buffering = NULL;
    PyObject *encoding = NULL;
    PyObject *errors = NULL;
    PyObject *newline = NULL;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "|OOOOO:open", (char **)_kw_list_open, &mode, &buffering,
                                          &encoding, &errors, &newline);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(file_name == NULL)) {
        return NULL;
    }

    PyObject *result = BUILTIN_OPEN(tstate, file_name, mode, buffering, encoding, errors, newline, NULL, NULL);
    Py_DECREF(file_name);
    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_as_file(PyObject *files_obj, PyObject *args) {
    CHECK_OBJECT(files_obj);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    Py_INCREF(files);
    return (PyObject *)files;
}

static PyObject *Nuitka_ResourceReaderFiles_enter(PyObject *files_obj, PyObject *args) {
    CHECK_OBJECT(files_obj);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    Py_INCREF(files);
    return (PyObject *)files;
}

static PyObject *Nuitka_ResourceReaderFiles_exit(PyObject *files_obj, PyObject *args) {
    CHECK_OBJECT(files_obj);

    Py_INCREF_IMMORTAL(Py_None);
    return Py_None;
}

static PyObject *Nuitka_ResourceReaderFiles_fspath(PyObject *files_obj, PyObject *args) {
    CHECK_OBJECT(files_obj);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    PyThreadState *tstate = PyThreadState_GET();

    return _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
}

static PyObject *Nuitka_ResourceReaderFiles_absolute(PyObject *files_obj, PyObject *args) {
    CHECK_OBJECT(files_obj);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)files_obj;

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(path == NULL)) {
        return NULL;
    }

    PyObject *abspath = OS_PATH_ABSPATH(tstate, path);
    Py_DECREF(path);

    if (unlikely(abspath == NULL)) {
        return NULL;
    }

    PyObject *result = Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, files->m_module_name, abspath);
    Py_DECREF(abspath);

    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_get_parent(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    if (unlikely(path == NULL)) {
        return NULL;
    }

    PyObject *abspath = OS_PATH_ABSPATH(tstate, path);
    Py_DECREF(path);

    if (unlikely(abspath == NULL)) {
        return NULL;
    }

    PyObject *dirname = OS_PATH_DIRNAME(tstate, abspath);
    Py_DECREF(abspath);

    if (unlikely(dirname == NULL)) {
        return NULL;
    }

    PyObject *result = Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, files->m_module_name, dirname);
    Py_DECREF(dirname);

    return result;
}

static int Nuitka_ResourceReaderFiles_set_parent(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_get_suffix(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;
    PyObject *basename = _Nuitka_ResourceReaderFiles_GetBasename(tstate, files);
    if (unlikely(basename == NULL)) {
        return NULL;
    }

    Py_ssize_t basename_len = PyUnicode_GET_LENGTH(basename);
    Py_ssize_t dot_index = Nuitka_Unicode_FindChar(basename, '.', 0, basename_len, -1);
    assert(dot_index >= -1);

    PyObject *result;
    if (dot_index > 0 && dot_index < basename_len - 1) {
        result = Nuitka_Unicode_Substring(basename, dot_index, basename_len);
    } else {
        result = Py_NewRef_IMMORTAL(const_str_empty);
    }

    Py_DECREF(basename);

    CHECK_OBJECT(result);
    return result;
}

// TODO: Share a single readonly setter function across these properties.
static int Nuitka_ResourceReaderFiles_set_suffix(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_get_stem(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *basename = _Nuitka_ResourceReaderFiles_GetBasename(tstate, files);
    if (unlikely(basename == NULL)) {
        return NULL;
    }

    Py_ssize_t basename_len = PyUnicode_GET_LENGTH(basename);
    Py_ssize_t dot_index = Nuitka_Unicode_FindChar(basename, '.', 0, basename_len, -1);
    assert(dot_index >= -1);

    PyObject *result;
    if (dot_index > 0 && dot_index < basename_len - 1) {
        result = Nuitka_Unicode_Substring(basename, 0, dot_index);
    } else {
        result = Py_NewRef(basename);
    }

    Py_DECREF(basename);

    CHECK_OBJECT(result);
    return result;
}

// TODO: Why don't we just share this method.
static int Nuitka_ResourceReaderFiles_set_stem(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_get_suffixes(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *basename = _Nuitka_ResourceReaderFiles_GetBasename(tstate, files);
    if (unlikely(basename == NULL)) {
        return NULL;
    }

    PyObject *endswith_dot = UNICODE_ENDSWITH2(tstate, basename, const_str_dot);
    if (unlikely(endswith_dot == NULL)) {
        Py_DECREF(basename);
        return NULL;
    }

    PyObject *result = MAKE_LIST_EMPTY(tstate, 0);
    CHECK_OBJECT(result);

    if (endswith_dot == Py_True) {
        Py_DECREF(endswith_dot);
        Py_DECREF(basename);
        return result;
    }
    Py_DECREF(endswith_dot);

    PyObject *current = UNICODE_LSTRIP2(tstate, basename, const_str_dot);
    Py_DECREF(basename);
    if (unlikely(current == NULL)) {
        Py_DECREF(result);
        return NULL;
    }

    PyObject *parts = UNICODE_SPLIT2(tstate, current, const_str_dot);
    Py_DECREF(current);
    if (unlikely(parts == NULL)) {
        Py_DECREF(result);
        return NULL;
    }

    for (Py_ssize_t i = 1; i < PyList_GET_SIZE(parts); i++) {
        current = const_str_dot;
        Py_INCREF_IMMORTAL(current);

        bool res = UNICODE_APPEND(tstate, &current, PyList_GET_ITEM(parts, i));
        if (unlikely(res == false)) {
            Py_DECREF(parts);
            Py_DECREF(result);
            return NULL;
        }

        {
            NUITKA_MAY_BE_UNUSED bool append_res = LIST_APPEND1(result, current);
            assert(append_res);
        }
    }

    Py_DECREF(parts);

    CHECK_OBJECT_DEEP(result);

    return result;
}

// TODO: Why don't we just share this method.
static int Nuitka_ResourceReaderFiles_set_suffixes(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyMethodDef Nuitka_ResourceReaderFiles_methods[] = {
    {"iterdir", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_iterdir), METH_NOARGS, NULL},
    {"read_bytes", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_read_bytes), METH_NOARGS, NULL},
    {"read_text", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_read_text), METH_VARARGS | METH_KEYWORDS, NULL},
    {"exists", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_exists), METH_NOARGS, NULL},
    {"is_dir", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_is_dir), METH_NOARGS, NULL},
    {"is_file", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_is_file), METH_NOARGS, NULL},
    {"joinpath", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_joinpath), METH_VARARGS | METH_KEYWORDS, NULL},
    {"open", CAST_METHOD_KW(Nuitka_ResourceReaderFiles_open), METH_VARARGS | METH_KEYWORDS, NULL},
    {"__enter__", (PyCFunction)Nuitka_ResourceReaderFiles_enter, METH_NOARGS, NULL},
    {"__exit__", (PyCFunction)Nuitka_ResourceReaderFiles_exit, METH_VARARGS, NULL},
    {"__fspath__", (PyCFunction)Nuitka_ResourceReaderFiles_fspath, METH_NOARGS, NULL},
    {"absolute", (PyCFunction)Nuitka_ResourceReaderFiles_absolute, METH_NOARGS, NULL},
    {"as_posix", (PyCFunction)Nuitka_ResourceReaderFiles_as_posix, METH_NOARGS, NULL},

    // Nuitka specific, for "importlib.resource.as_file" overload.
    {"as_file", (PyCFunction)Nuitka_ResourceReaderFiles_as_file, METH_NOARGS, NULL},

    {NULL}};

static PyObject *Nuitka_ResourceReaderFiles_get_name(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;

    PyThreadState *tstate = PyThreadState_GET();

    return _Nuitka_ResourceReaderFiles_GetBasename(tstate, files);
}

static int Nuitka_ResourceReaderFiles_set_name(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_tp_richcompare(PyObject *self, PyObject *other, int op_id) {
    PyObject *a = Nuitka_ResourceReaderFiles_tp_str(self);
    if (unlikely(a == NULL)) {
        return NULL;
    }

    PyObject *b = BUILTIN_UNICODE1(other);
    if (unlikely(b == NULL)) {
        Py_DECREF(a);
        return NULL;
    }

    PyObject *result;
    if (likely(PyUnicode_CheckExact(a) && PyUnicode_CheckExact(b))) {
        result = RICH_COMPARE_OBJECT_UNICODE_UNICODE(a, b, op_id);
    } else {
        result = RICH_COMPARE_OBJECT_OBJECT_OBJECT(a, b, op_id);
    }

    Py_DECREF(a);
    Py_DECREF(b);

    return result;
}

static PyGetSetDef Nuitka_ResourceReaderFiles_tp_getset[] = {
    {(char *)"name", Nuitka_ResourceReaderFiles_get_name, Nuitka_ResourceReaderFiles_set_name, NULL},
    {(char *)"parent", Nuitka_ResourceReaderFiles_get_parent, Nuitka_ResourceReaderFiles_set_parent, NULL},
    {(char *)"suffix", Nuitka_ResourceReaderFiles_get_suffix, Nuitka_ResourceReaderFiles_set_suffix, NULL},
    {(char *)"stem", Nuitka_ResourceReaderFiles_get_stem, Nuitka_ResourceReaderFiles_set_stem, NULL},
    {(char *)"suffixes", Nuitka_ResourceReaderFiles_get_suffixes, Nuitka_ResourceReaderFiles_set_suffixes, NULL},
    {NULL}};

// Initialized during readying the type for nb_truediv
static PyNumberMethods Nuitka_resource_reader_as_number = {0};

static PyTypeObject Nuitka_ResourceReaderFiles_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "nuitka_resource_reader_files",
    sizeof(struct Nuitka_ResourceReaderFilesObject),        // tp_basicsize
    0,                                                      // tp_itemsize
    (destructor)Nuitka_ResourceReaderFiles_tp_dealloc,      // tp_dealloc
    0,                                                      // tp_print
    0,                                                      // tp_getattr
    0,                                                      // tp_setattr
    0,                                                      // tp_reserved
    (reprfunc)Nuitka_ResourceReaderFiles_tp_repr,           // tp_repr
    &Nuitka_resource_reader_as_number,                      // tp_as_number
    0,                                                      // tp_as_sequence
    0,                                                      // tp_as_mapping
    0,                                                      // tp_hash
    0,                                                      // tp_call
    (reprfunc)Nuitka_ResourceReaderFiles_tp_str,            // tp_str
    0,                                                      // tp_getattro (PyObject_GenericGetAttr)
    0,                                                      // tp_setattro
    0,                                                      // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                // tp_flags
    0,                                                      // tp_doc
    (traverseproc)Nuitka_ResourceReaderFiles_tp_traverse,   // tp_traverse
    0,                                                      // tp_clear
    (richcmpfunc)Nuitka_ResourceReaderFiles_tp_richcompare, // tp_richcompare
    0,                                                      // tp_weaklistoffset
    0,                                                      // tp_iter (PyObject_SelfIter)
    0,                                                      // tp_iternext
    Nuitka_ResourceReaderFiles_methods,                     // tp_methods
    0,                                                      // tp_members
    Nuitka_ResourceReaderFiles_tp_getset,                   // tp_getset
};

#if PYTHON_VERSION >= 0x390
static void registerResourceReaderFiles(PyThreadState *tstate, PyObject *resources_module) {
    PyObject *as_file = LOOKUP_ATTRIBUTE(tstate, resources_module, const_str_plain_as_file);
    if (likely(as_file != NULL)) {
        PyObject *our_as_file =
            LOOKUP_ATTRIBUTE(tstate, (PyObject *)&Nuitka_ResourceReaderFiles_Type, const_str_plain_as_file);
        CHECK_OBJECT(our_as_file);

        PyObject *args[2] = {(PyObject *)&Nuitka_ResourceReaderFiles_Type, our_as_file};

        PyObject *register_result = CALL_METHOD_WITH_ARGS2(tstate, as_file, const_str_plain_register, args);
        if (unlikely(register_result == NULL)) {
            CLEAR_ERROR_OCCURRED(tstate);
        } else {
            Py_DECREF(register_result);
        }

        Py_DECREF(as_file);
        Py_DECREF(our_as_file);
    } else {
        CLEAR_ERROR_OCCURRED(tstate);
    }
}
#endif

static PyObject *Nuitka_ResourceReaderFiles_New(PyThreadState *tstate,
                                                struct Nuitka_MetaPathBasedLoaderEntry const *entry,
                                                PyObject *module_name, PyObject *path) {
    struct Nuitka_ResourceReaderFilesObject *result;

    static bool init_done = false;
    if (init_done == false) {
        // We do not really want to write a lot of NULLs just to do this, and
        // for as long as we do not have C11 everywhere, that is how we have
        // to do it.
        Nuitka_ResourceReaderFiles_Type.tp_as_number->nb_true_divide =
            (binaryfunc)Nuitka_ResourceReaderFiles_nb_truediv;

        Nuitka_PyType_Ready(&Nuitka_ResourceReaderFiles_Type, // type
                            NULL,                             // base
                            true,                             // generic_get_attr
                            false,                            // generic_set_attr
                            true,                             // self_iter
                            false,                            // await_self_iter
                            false                             // await_self_aiter
        );

#if PYTHON_VERSION >= 0x390
        // Also register our open, which can avoid a temporary file being created.
        PyObject *importlib_resources_module = IMPORT_HARD_IMPORTLIB__RESOURCES();
        registerResourceReaderFiles(tstate, importlib_resources_module);

        PyObject *importlib_resources_backport_module = IMPORT_HARD_IMPORTLIB_RESOURCES();
        if (importlib_resources_backport_module != NULL) {
            registerResourceReaderFiles(tstate, importlib_resources_backport_module);
        } else {
            DROP_ERROR_OCCURRED(tstate);
        }
#endif

        init_done = true;
    }

    CHECK_OBJECT(path);
    assert(PyUnicode_Check(path));

    result = (struct Nuitka_ResourceReaderFilesObject *)Nuitka_GC_New(&Nuitka_ResourceReaderFiles_Type);
    CHECK_OBJECT(result);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;
    result->m_module_name = module_name;
    Py_XINCREF(result->m_module_name);

    result->m_path = path;
    Py_INCREF(path);

    return (PyObject *)result;
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
