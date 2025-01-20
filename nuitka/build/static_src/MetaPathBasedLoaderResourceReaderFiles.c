//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This implements the resource reader for of C compiled modules and
// shared library extension modules bundled for standalone mode with
// newer Python.

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#include "nuitka/unfreezing.h"
#endif

struct Nuitka_ResourceReaderFilesObject {
    /* Python object folklore: */
    PyObject_HEAD

        // The loader entry, to know this is for one package exactly.
        struct Nuitka_MetaPathBasedLoaderEntry const *m_loader_entry;

    // The path relative to the entry, if e.g. joinpath is used
    PyObject *m_path;
};

static PyObject *Nuitka_ResourceReaderFiles_New(PyThreadState *tstate,
                                                struct Nuitka_MetaPathBasedLoaderEntry const *entry, PyObject *path);

static PyObject *_Nuitka_ResourceReaderFiles_GetPath(PyThreadState *tstate,
                                                     struct Nuitka_ResourceReaderFilesObject const *files) {
    // Allow for absolute paths, TODO: Too lazy to have OS_PATH_JOIN at this
    // time also not clearly how early JOIN2 is used, i.e. do we have importing
    // available for it.

    PyObject *is_abs = OS_PATH_ISABS(tstate, files->m_path);
    PyObject *result;
    if (is_abs == Py_True) {
#if 0
        PRINT_STRING("Getting path from absolute: ");
        PRINT_ITEM(files->m_path);
        PRINT_NEW_LINE();
#endif

        result = files->m_path;
        Py_INCREF(result);
    } else {
        result = getModuleDirectory(tstate, files->m_loader_entry);

#if 0
        PRINT_STRING("Getting path from relative: ");
        PRINT_ITEM(result);
        PRINT_STRING(" ");
        PRINT_ITEM(files->m_path);
        PRINT_NEW_LINE();
#endif

        if (files->m_path != const_str_empty) {
            PyObject *old = result;
            result = JOIN_PATH2(result, files->m_path);
            Py_DECREF(old);
        }
    }

    Py_DECREF(is_abs);

    return result;
}

static void Nuitka_ResourceReaderFiles_tp_dealloc(struct Nuitka_ResourceReaderFilesObject *files) {
    Nuitka_GC_UnTrack(files);

    Py_DECREF(files->m_path);

    PyObject_GC_Del(files);
}

static PyObject *Nuitka_ResourceReaderFiles_tp_repr(struct Nuitka_ResourceReaderFilesObject *files) {
    return PyUnicode_FromFormat("<nuitka_resource_reader_files for package '%s' file %R>", files->m_loader_entry->name,
                                files->m_path);
}

static PyObject *Nuitka_ResourceReaderFiles_tp_str(struct Nuitka_ResourceReaderFilesObject *files) {
    PyThreadState *tstate = PyThreadState_GET();
    return _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
}

// Obligatory, even if we have nothing to own
static int Nuitka_ResourceReaderFiles_tp_traverse(struct Nuitka_ResourceReaderFilesObject *files, visitproc visit,
                                                  void *arg) {
    return 0;
}

// Methods that need to be implemented.
//
//
//    def iterdir(self):
//        """
//        Yield Traversable objects from self
//        """
//
static PyObject *Nuitka_ResourceReaderFiles_iterdir(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                    PyObject *kwds) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *file_path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    PyObject *file_names = OS_LISTDIR(tstate, file_path);
    Py_DECREF(file_path);

    // TODO: Actually we ought to behave like a generator and delay this error,
    // but we currently spare us the effort and raise this immediately.
    if (unlikely(file_names == NULL)) {
        return NULL;
    }

    PyObject *files_objects = MAKE_LIST_EMPTY(tstate, 0);

    Py_ssize_t n = PyList_GET_SIZE(file_names);
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *file_name = PyList_GET_ITEM(file_names, i);
        CHECK_OBJECT(file_name);

        PyObject *joined = JOIN_PATH2(files->m_path, file_name);
        CHECK_OBJECT(joined);

        PyObject *files_object = Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, joined);
        {
            NUITKA_MAY_BE_UNUSED bool res = LIST_APPEND1(files_objects, files_object);
            assert(res);
        }

        CHECK_OBJECT(files_object);
        Py_DECREF(joined);
    }

    PyObject *result = MAKE_ITERATOR_INFALLIBLE(files_objects);
    Py_DECREF(files_objects);

    return result;
}

//    def read_bytes(self):
//        """
//        Read contents of self as bytes
//        """
//        with self.open('rb') as strm:
//            return strm.read()
//

static PyObject *Nuitka_ResourceReaderFiles_read_bytes(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                       PyObject *kwds) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    if (unlikely(file_name == NULL)) {
        return NULL;
    }

    return GET_FILE_BYTES(tstate, file_name);
}

//    def read_text(self, encoding=None, errors=None):
//        """
//        Read contents of self as text, errors is new in Python3.13
//        """
//        with self.open(encoding=encoding) as strm:
//            return strm.read()

#if PYTHON_VERSION >= 0x3d0
static char const *_kw_list_encoding_errors[] = {"encoding", "errors", NULL};
#else
static char const *_kw_list_encoding[] = {"encoding", NULL};
#endif

static PyObject *Nuitka_ResourceReaderFiles_read_text(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                      PyObject *kwds) {

    PyObject *encoding = NULL;

    PyObject *errors = NULL;

    // The errors argument is only available for 3.13 only
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

    PyObject *result = CALL_FUNCTION_NO_ARGS(PyThreadState_GET(), read_method);
    Py_DECREF(read_method);
    return result;
}

static PyObject *Nuitka_ResourceReaderFiles_exists(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                   PyObject *kwds) {

    PyThreadState *tstate = PyThreadState_GET();
    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    PyObject *result = OS_PATH_FILE_EXISTS(tstate, file_name);
    Py_DECREF(file_name);
    return result;
}

//    @abc.abstractmethod
//    def is_dir(self) -> bool:
//        """
//        Return True if self is a dir
//        """
//

static PyObject *Nuitka_ResourceReaderFiles_is_dir(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                   PyObject *kwds) {

    PyThreadState *tstate = PyThreadState_GET();
    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    PyObject *result = OS_PATH_FILE_ISDIR(tstate, file_name);
    Py_DECREF(file_name);
    return result;
}

//    @abc.abstractmethod
//    def is_file(self) -> bool:
//        """
//        Return True if self is a file
//        """
static PyObject *Nuitka_ResourceReaderFiles_is_file(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                    PyObject *kwds) {

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    PyObject *result = OS_PATH_FILE_ISFILE(tstate, file_name);
    Py_DECREF(file_name);
    return result;
}

static char const *_kw_list_joinpath[] = {"child", NULL};

//    @abc.abstractmethod
//    def joinpath(self, child):
//        """
//        Return Traversable child in self
//        """
//

// Functions out there, some accept "child", and accept varargs, lets be compatible with both.

static PyObject *Nuitka_ResourceReaderFiles_joinpath(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                     PyObject *kwds) {

    PyObject *joined = files->m_path;

    if (kwds != NULL) {
        PyObject *child;

        int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:joinpath", (char **)_kw_list_joinpath, &child);

        if (unlikely(res == 0)) {
            return NULL;
        }

        joined = JOIN_PATH2(joined, child);

        if (unlikely(joined == NULL)) {
            return NULL;
        }
    } else {
        Py_INCREF(joined);

        Py_ssize_t n = PyTuple_GET_SIZE(args);
        for (Py_ssize_t i = 0; i < n; ++i) {
            PyObject *child = PyTuple_GET_ITEM(args, i);

            PyObject *old = joined;
            if (old == const_str_empty) {
                joined = child;
                Py_INCREF(child);
            } else {
                joined = JOIN_PATH2(joined, child);
            }

            Py_DECREF(old);

            if (unlikely(joined == NULL)) {
                return NULL;
            }
        }
    }

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *result = Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, joined);

    Py_DECREF(joined);

    return result;
}

//    def def as_posix(self):
//        """
//        Return Traversable child in self
//        """
//

static PyObject *Nuitka_ResourceReaderFiles_as_posix(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                     PyObject *kwds) {
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

#ifdef _WIN32

#if PYTHON_VERSION < 0x300
    PyObject *result;

    if (PyString_Check(path)) {
        result = STR_REPLACE3(tstate, path, const_str_backslash, const_str_slash);
    } else {
        result = UNICODE_REPLACE3(tstate, path, const_str_backslash, const_str_slash);
    }
#else
    PyObject *result = UNICODE_REPLACE3(tstate, path, const_str_backslash, const_str_slash);
#endif

    Py_DECREF(path);

    return result;
#else
    return path;
#endif
}

PyObject *Nuitka_ResourceReaderFiles_nb_truediv(struct Nuitka_ResourceReaderFilesObject *files, PyObject *arg) {
    PyObject *joined;

    if (files->m_path == const_str_empty) {
        joined = arg;
        Py_INCREF(arg);
    } else {
        joined = JOIN_PATH2(files->m_path, arg);
    }

    if (unlikely(joined == NULL)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *result = Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, joined);

    return result;
}

//    @abc.abstractmethod
//    def open(self, mode='r', *args, **kwargs):
//        """
//        mode may be 'r' or 'rb' to open as text or binary. Return a handle
//        suitable for reading (same as pathlib.Path.open).
//
//        When opening as text, accepts encoding parameters such as those
//        accepted by io.TextIOWrapper.
//        """
//

static char const *_kw_list_open[] = {"mode", "buffering", "encoding", "errors", "newline", NULL};

static PyObject *Nuitka_ResourceReaderFiles_open(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                 PyObject *kwds) {

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

    return BUILTIN_OPEN(tstate, file_name, mode, buffering, encoding, errors, newline, NULL, NULL);
}

static PyObject *Nuitka_ResourceReaderFiles_as_file(struct Nuitka_ResourceReaderFilesObject *files) {
    CHECK_OBJECT(files);

    Py_INCREF(files);
    return (PyObject *)files;
}

static PyObject *Nuitka_ResourceReaderFiles_enter(struct Nuitka_ResourceReaderFilesObject *files) {
    CHECK_OBJECT(files);

    Py_INCREF(files);
    return (PyObject *)files;
}

static PyObject *Nuitka_ResourceReaderFiles_exit(struct Nuitka_ResourceReaderFilesObject *files) {
    CHECK_OBJECT(files);

    Py_INCREF_IMMORTAL(Py_None);
    return Py_None;
}

static PyObject *Nuitka_ResourceReaderFiles_fspath(struct Nuitka_ResourceReaderFilesObject *files) {
    PyThreadState *tstate = PyThreadState_GET();

    return _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
}

static PyObject *Nuitka_ResourceReaderFiles_absolute(struct Nuitka_ResourceReaderFilesObject *files) {
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    PyObject *abspath = OS_PATH_ABSPATH(tstate, path);

    if (unlikely(abspath == NULL)) {
        return NULL;
    }

    return Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, abspath);
}

static PyObject *Nuitka_ResourceReaderFiles_get_parent(PyObject *self, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;
    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    PyObject *abspath = OS_PATH_ABSPATH(tstate, path);

    if (unlikely(abspath == NULL)) {
        return NULL;
    }

    PyObject *dirname = OS_PATH_DIRNAME(tstate, abspath);

    if (unlikely(dirname == NULL)) {
        return NULL;
    }

    return Nuitka_ResourceReaderFiles_New(tstate, files->m_loader_entry, dirname);
}

static int Nuitka_ResourceReaderFiles_set_parent(PyObject *self, PyObject *value, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_get_suffix(PyObject *self, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;
    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    PyObject *basename = OS_PATH_BASENAME(tstate, path);
    Py_DECREF(path);

    PyObject *dot_index = UNICODE_RFIND2(tstate, basename, const_str_dot);

    PyObject *result;
    if (dot_index == Py_None) {
        result = const_str_empty;
        Py_INCREF_IMMORTAL(result);
    } else {
        result = PyUnicode_Substring(basename, PyLong_AsLong(dot_index), PyUnicode_GetLength(basename));
    }

    Py_DECREF(basename);
    Py_DECREF(dot_index);

    return result;
}

// TODO: Why don't we just share this method.
static int Nuitka_ResourceReaderFiles_set_suffix(PyObject *self, PyObject *value, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_get_stem(PyObject *self, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;
    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    PyObject *basename = OS_PATH_BASENAME(tstate, path);
    Py_DECREF(path);

    PyObject *dot_index = UNICODE_RFIND2(tstate, basename, const_str_dot);
    CHECK_OBJECT(dot_index);

    PyObject *result;

    if (dot_index == Py_None) {
        result = const_str_empty;
        Py_INCREF_IMMORTAL(result);
    } else {
        int dot_index_long = PyLong_AsLong(dot_index);

        if (dot_index_long > 0 && dot_index_long < PyUnicode_GetLength(basename) - 1) {
            result = PyUnicode_Substring(basename, 0, PyLong_AsLong(dot_index));
        } else {
            Py_INCREF(basename);
            result = basename;
        }
    }

    Py_DECREF(basename);
    Py_DECREF(dot_index);

    CHECK_OBJECT(result);

    return result;
}

// TODO: Why don't we just share this method.
static int Nuitka_ResourceReaderFiles_set_stem(PyObject *self, PyObject *value, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_get_suffixes(PyObject *self, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;
    PyObject *path = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);

    PyObject *basename = OS_PATH_BASENAME(tstate, path);
    Py_DECREF(path);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 0);

    if (UNICODE_ENDSWITH2(tstate, basename, const_str_dot) == Py_True) {
        return result;
    }

    PyObject *current = UNICODE_LSTRIP2(tstate, basename, const_str_dot);

    PyObject *parts = UNICODE_SPLIT2(tstate, current, const_str_dot);
    Py_DECREF(current);

    for (Py_ssize_t i = 1; i < PyList_GET_SIZE(parts); i++) {
        current = const_str_dot;
        Py_INCREF_IMMORTAL(current);

        UNICODE_APPEND(tstate, &current, PyList_GET_ITEM(parts, i));

        LIST_APPEND0(result, current);
    }

    CHECK_OBJECT_DEEP(result);

    return result;
}

// TODO: Why don't we just share this method.
static int Nuitka_ResourceReaderFiles_set_suffixes(PyObject *self, PyObject *value, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyMethodDef Nuitka_ResourceReaderFiles_methods[] = {
    {"iterdir", (PyCFunction)Nuitka_ResourceReaderFiles_iterdir, METH_NOARGS, NULL},
    {"read_bytes", (PyCFunction)Nuitka_ResourceReaderFiles_read_bytes, METH_NOARGS, NULL},
    {"read_text", (PyCFunction)Nuitka_ResourceReaderFiles_read_text, METH_VARARGS | METH_KEYWORDS, NULL},
    {"exists", (PyCFunction)Nuitka_ResourceReaderFiles_exists, METH_NOARGS, NULL},
    {"is_dir", (PyCFunction)Nuitka_ResourceReaderFiles_is_dir, METH_NOARGS, NULL},
    {"is_file", (PyCFunction)Nuitka_ResourceReaderFiles_is_file, METH_NOARGS, NULL},
    {"joinpath", (PyCFunction)Nuitka_ResourceReaderFiles_joinpath, METH_VARARGS | METH_KEYWORDS, NULL},
    {"open", (PyCFunction)Nuitka_ResourceReaderFiles_open, METH_VARARGS | METH_KEYWORDS, NULL},
    {"__enter__", (PyCFunction)Nuitka_ResourceReaderFiles_enter, METH_NOARGS, NULL},
    {"__exit__", (PyCFunction)Nuitka_ResourceReaderFiles_exit, METH_VARARGS, NULL},
    {"__fspath__", (PyCFunction)Nuitka_ResourceReaderFiles_fspath, METH_NOARGS, NULL},
    {"absolute", (PyCFunction)Nuitka_ResourceReaderFiles_absolute, METH_NOARGS, NULL},
    {"as_posix", (PyCFunction)Nuitka_ResourceReaderFiles_as_posix, METH_NOARGS, NULL},

    // Nuitka specific, for "importlib.resource.as_file" overload.
    {"as_file", (PyCFunction)Nuitka_ResourceReaderFiles_as_file, METH_NOARGS, NULL},

    {NULL}};

//    @abc.abstractproperty
//    def name(self) -> str:
//        """
//        The base name of this object without any parent references.
//        """

static PyObject *Nuitka_ResourceReaderFiles_get_name(PyObject *self, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ResourceReaderFilesObject *files = (struct Nuitka_ResourceReaderFilesObject *)self;
    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(tstate, files);
    PyObject *result = OS_PATH_BASENAME(tstate, file_name);
    Py_DECREF(file_name);

    return result;
}

static int Nuitka_ResourceReaderFiles_set_name(PyObject *self, PyObject *value, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_ResourceReaderFiles_tp_richcompare(struct Nuitka_ResourceReaderFilesObject *files_a,
                                                           PyObject *other, int op_id) {
    PyObject *a = PyObject_Str((PyObject *)files_a);
    CHECK_OBJECT(a);

    PyObject *b = PyObject_Str(other);
    if (unlikely(b == NULL)) {
        Py_DECREF(a);
        return NULL;
    }

    PyObject *result = PyObject_RichCompare(a, b, op_id);

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
        }

        Py_DECREF(as_file);
        Py_DECREF(our_as_file);
    } else {
        CLEAR_ERROR_OCCURRED(tstate);
    }
}
#endif

static PyObject *Nuitka_ResourceReaderFiles_New(PyThreadState *tstate,
                                                struct Nuitka_MetaPathBasedLoaderEntry const *entry, PyObject *path) {
    struct Nuitka_ResourceReaderFilesObject *result;

    static bool init_done = false;
    if (init_done == false) {
        // We do not really want to write a lot of NULLs just to do this, and
        // for as long as we do not have C11 everywhere, that is how we have
        // to do it.
        Nuitka_ResourceReaderFiles_Type.tp_as_number->nb_true_divide =
            (binaryfunc)Nuitka_ResourceReaderFiles_nb_truediv;

        Nuitka_PyType_Ready(&Nuitka_ResourceReaderFiles_Type, NULL, true, false, true, false, false);

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

    result = (struct Nuitka_ResourceReaderFilesObject *)Nuitka_GC_New(&Nuitka_ResourceReaderFiles_Type);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;
    result->m_path = path;
    Py_INCREF(path);

    return (PyObject *)result;
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
