//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

        /* The loader entry, to know this is for one package exactly. */
        struct Nuitka_MetaPathBasedLoaderEntry const *m_loader_entry;

    /* The path relative to the entry, if e.g. joinpath is used. */
    PyObject *m_path;
    struct Nuitka_MetaPathBasedLoaderEntry const *m_iterating_entry;
};

static PyObject *Nuitka_ResourceReaderFiles_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry, PyObject *path);

static PyObject *_Nuitka_ResourceReaderFiles_GetPath(struct Nuitka_ResourceReaderFilesObject const *files) {
    return JOIN_PATH2(getModuleDirectory(files->m_loader_entry), files->m_path);
}

static void Nuitka_ResourceReaderFiles_tp_dealloc(struct Nuitka_ResourceReaderFilesObject *files) {
    Nuitka_GC_UnTrack(files);

    Py_DECREF(files->m_path);

    PyObject_GC_Del(files);
}

static PyObject *Nuitka_ResourceReaderFiles_tp_repr(struct Nuitka_ResourceReaderFilesObject *files) {
    return PyUnicode_FromFormat("<nuitka_resource_reader_files for '%s'>", files->m_loader_entry->name);
}

static PyObject *Nuitka_ResourceReaderFiles_tp_str(struct Nuitka_ResourceReaderFilesObject *files) {
    return _Nuitka_ResourceReaderFiles_GetPath(files);
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
//        Yield Traversable objects in self
//        """
//
static PyObject *Nuitka_ResourceReaderFiles_iterdir(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                    PyObject *kwds) {

    if (files->m_path == const_str_empty) {

        struct Nuitka_ResourceReaderFilesObject *result =
            (struct Nuitka_ResourceReaderFilesObject *)Nuitka_ResourceReaderFiles_New(files->m_loader_entry,
                                                                                      const_str_empty);
        result->m_iterating_entry = loader_entries;

        return (PyObject *)result;
    } else {
        PyErr_SetNone(PyExc_NotImplementedError);
        return NULL;
    }
}

// iterator next implementation
static PyObject *Nuitka_ResourceReaderFiles_tp_iternext(struct Nuitka_ResourceReaderFilesObject *files) {
    if (files->m_iterating_entry == NULL) {
        return NULL;
    }

    struct Nuitka_MetaPathBasedLoaderEntry const *current = files->m_iterating_entry;

    if (files->m_path == const_str_empty) {
        while (current != NULL) {
            char const *current_package_name = strrchr(current->name, '.');

            if (current_package_name != NULL) {
                if (strncmp(files->m_loader_entry->name, current_package_name, current_package_name - current->name) ==
                    0) {
                }
            }

            current += 1;
        }

        return NULL;
    } else {
        PyErr_SetNone(PyExc_NotImplementedError);
        return NULL;
    }
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
    PyObject *filename = _Nuitka_ResourceReaderFiles_GetPath(files);

    if (unlikely(filename == NULL)) {
        return NULL;
    }

    return GET_FILE_BYTES(filename);
}

//    def read_text(self, encoding=None):
//        """
//        Read contents of self as text
//        """
//        with self.open(encoding=encoding) as strm:
//            return strm.read()

static char const *_kw_list_encoding[] = {"encoding", NULL};

static PyObject *Nuitka_ResourceReaderFiles_read_text(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                      PyObject *kwds) {

    PyObject *encoding = NULL;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "|O:read_text", (char **)_kw_list_encoding, &encoding);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *filename = _Nuitka_ResourceReaderFiles_GetPath(files);

    if (unlikely(filename == NULL)) {
        return NULL;
    }

    PyObject *file_object = BUILTIN_OPEN_SIMPLE(filename, "r", true, encoding);

    Py_DECREF(filename);

    if (unlikely(file_object == NULL)) {
        return NULL;
    }

    PyObject *read_method = LOOKUP_ATTRIBUTE(file_object, const_str_plain_read);
    Py_DECREF(file_object);

    if (unlikely(read_method == NULL)) {
        return NULL;
    }

    PyObject *result = CALL_FUNCTION_NO_ARGS(read_method);
    Py_DECREF(read_method);
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

    PyObject *filename = _Nuitka_ResourceReaderFiles_GetPath(files);
    PyObject *result = OS_PATH_FILE_ISDIR(filename);
    Py_DECREF(filename);
    return result;
}
//    @abc.abstractmethod
//    def is_file(self) -> bool:
//        """
//        Return True if self is a file
//        """

static PyObject *Nuitka_ResourceReaderFiles_is_file(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                    PyObject *kwds) {

    PyObject *filename = _Nuitka_ResourceReaderFiles_GetPath(files);
    PyObject *result = OS_PATH_FILE_ISFILE(filename);
    Py_DECREF(filename);
    return result;
}

static char const *_kw_list_joinpath[] = {"child", NULL};

//    @abc.abstractmethod
//    def joinpath(self, child):
//        """
//        Return Traversable child in self
//        """
//

static PyObject *Nuitka_ResourceReaderFiles_joinpath(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                     PyObject *kwds) {

    PyObject *child;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:joinpath", (char **)_kw_list_joinpath, &child);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *joined = JOIN_PATH2(files->m_path, child);

    if (unlikely(joined == NULL)) {
        return NULL;
    }

    return Nuitka_ResourceReaderFiles_New(files->m_loader_entry, joined);
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

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "|OOOO:open", (char **)_kw_list_open, &mode, &buffering,
                                          &encoding, &errors, &newline);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyObject *file_name = _Nuitka_ResourceReaderFiles_GetPath(files);

    return BUILTIN_OPEN(file_name, mode, buffering, encoding, errors, newline, NULL, NULL);
}

//    @abc.abstractproperty
//    def name(self) -> str:
//        """
//        The base name of this object without any parent references.
//        """

static PyObject *Nuitka_ResourceReaderFiles_get_name(struct Nuitka_ResourceReaderFilesObject *files) {
    PyObject *filename = _Nuitka_ResourceReaderFiles_GetPath(files);
    return filename;
}

static int Nuitka_ResourceReaderFiles_set_name(struct Nuitka_FunctionObject *object, PyObject *value) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_AttributeError, "readonly attribute");

    return -1;
}

static PyMethodDef Nuitka_ResourceReaderFiles_methods[] = {
    {"iterdir", (PyCFunction)Nuitka_ResourceReaderFiles_iterdir, METH_NOARGS, NULL},
    {"read_bytes", (PyCFunction)Nuitka_ResourceReaderFiles_read_bytes, METH_NOARGS, NULL},
    {"read_text", (PyCFunction)Nuitka_ResourceReaderFiles_read_text, METH_VARARGS | METH_KEYWORDS, NULL},
    {"is_dir", (PyCFunction)Nuitka_ResourceReaderFiles_is_dir, METH_NOARGS, NULL},
    {"is_file", (PyCFunction)Nuitka_ResourceReaderFiles_is_file, METH_NOARGS, NULL},
    {"joinpath", (PyCFunction)Nuitka_ResourceReaderFiles_joinpath, METH_VARARGS | METH_KEYWORDS, NULL},
    {"__truediv__", (PyCFunction)Nuitka_ResourceReaderFiles_joinpath, METH_VARARGS | METH_KEYWORDS, NULL},
    {"open", (PyCFunction)Nuitka_ResourceReaderFiles_open, METH_VARARGS | METH_KEYWORDS, NULL},
    {NULL}};

static PyGetSetDef Nuitka_ResourceReaderFiles_getset[] = {
    {(char *)"name", (getter)Nuitka_ResourceReaderFiles_get_name, (setter)Nuitka_ResourceReaderFiles_set_name, NULL},
    {NULL}};

static PyTypeObject Nuitka_ResourceReaderFiles_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "nuitka_resource_reader_files",
    sizeof(struct Nuitka_ResourceReaderFilesObject),      /* tp_basicsize */
    0,                                                    /* tp_itemsize */
    (destructor)Nuitka_ResourceReaderFiles_tp_dealloc,    /* tp_dealloc */
    0,                                                    /* tp_print */
    0,                                                    /* tp_getattr */
    0,                                                    /* tp_setattr */
    0,                                                    /* tp_reserved */
    (reprfunc)Nuitka_ResourceReaderFiles_tp_repr,         /* tp_repr */
    0,                                                    /* tp_as_number */
    0,                                                    /* tp_as_sequence */
    0,                                                    /* tp_as_mapping */
    0,                                                    /* tp_hash */
    0,                                                    /* tp_call */
    (reprfunc)Nuitka_ResourceReaderFiles_tp_str,          /* tp_str */
    PyObject_GenericGetAttr,                              /* tp_getattro */
    0,                                                    /* tp_setattro */
    0,                                                    /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,              /* tp_flags */
    0,                                                    /* tp_doc */
    (traverseproc)Nuitka_ResourceReaderFiles_tp_traverse, /* tp_traverse */
    0,                                                    /* tp_clear */
    0,                                                    /* tp_richcompare */
    0,                                                    /* tp_weaklistoffset */
    PyObject_SelfIter,                                    /* tp_iter */
    (iternextfunc)Nuitka_ResourceReaderFiles_tp_iternext, /* tp_iternext */
    Nuitka_ResourceReaderFiles_methods,                   /* tp_methods */
    0,                                                    /* tp_members */
    Nuitka_ResourceReaderFiles_getset,                    /* tp_getset */
};

static PyObject *Nuitka_ResourceReaderFiles_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry, PyObject *path) {
    struct Nuitka_ResourceReaderFilesObject *result;

    static bool init_done = false;
    if (init_done == false) {
        PyType_Ready(&Nuitka_ResourceReaderFiles_Type);
        init_done = true;
    }

    result = (struct Nuitka_ResourceReaderFilesObject *)PyObject_GC_New(struct Nuitka_ResourceReaderFilesObject,
                                                                        &Nuitka_ResourceReaderFiles_Type);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;
    result->m_path = path;
    Py_INCREF(path);
    result->m_iterating_entry = NULL;

    return (PyObject *)result;
}