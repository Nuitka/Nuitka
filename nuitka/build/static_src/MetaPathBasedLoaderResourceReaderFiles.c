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

// Just for the IDE to know, this file is not included otherwise.
#if PYTHON_VERSION >= 0x390

struct Nuitka_ResourceReaderFilesObject {
    /* Python object folklore: */
    PyObject_HEAD

        /* The loader entry, to know this is about exactly. */
        struct Nuitka_MetaPathBasedLoaderEntry const *m_loader_entry;
    struct Nuitka_MetaPathBasedLoaderEntry const *m_iterating_entry;
};

static PyObject *Nuitka_ResourceReaderFiles_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry);

static void Nuitka_ResourceReaderFiles_tp_dealloc(struct Nuitka_ResourceReaderFilesObject *files) {
    Nuitka_GC_UnTrack(files);

    PyObject_GC_Del(files);
}

static PyObject *Nuitka_ResourceReaderFiles_tp_repr(struct Nuitka_ResourceReaderFilesObject *files) {
    return PyUnicode_FromFormat("<nuitka_resource_reader_files for '%s'>", files->m_loader_entry->name);
}

// Obligatory, even if we have nothing to own
static int Nuitka_ResourceReaderFiles_tp_traverse(struct Nuitka_ResourceReaderFilesObject *files, visitproc visit,
                                                  void *arg) {
    return 0;
}

// Methods that need to be implemented.
//
//    @abc.abstractmethod
//    def is_dir(self) -> bool:
//        """
//        Return True if self is a dir
//        """
//
//    @abc.abstractmethod
//    def is_file(self) -> bool:
//        """
//        Return True if self is a file
//        """
//
//    @abc.abstractmethod
//    def joinpath(self, child):
//        """
//        Return Traversable child in self
//        """
//
//    def __truediv__(self, child):
//        """
//        Return Traversable child in self
//        """
//        return self.joinpath(child)
//
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
//    @abc.abstractproperty
//    def name(self) -> str:
//        """
//        The base name of this object without any parent references.
//        """

//    def iterdir(self):
//        """
//        Yield Traversable objects in self
//        """
//
static PyObject *Nuitka_ResourceReaderFiles_iterdir(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                    PyObject *kwds) {

    struct Nuitka_ResourceReaderFilesObject *result =
        (struct Nuitka_ResourceReaderFilesObject *)Nuitka_ResourceReaderFiles_New(files->m_loader_entry);
    result->m_iterating_entry = loader_entries;

    return (PyObject *)result;
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

    PyErr_SetNone(PyExc_NotImplementedError);
    return NULL;
}

//    def read_text(self, encoding=None):
//        """
//        Read contents of self as text
//        """
//        with self.open(encoding=encoding) as strm:
//            return strm.read()
static PyObject *Nuitka_ResourceReaderFiles_read_text(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                      PyObject *kwds) {

    PyErr_SetNone(PyExc_NotImplementedError);
    return NULL;
}

static PyObject *Nuitka_ResourceReaderFiles_is_dir(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                   PyObject *kwds) {

    PyErr_SetNone(PyExc_NotImplementedError);
    return NULL;
}
static PyObject *Nuitka_ResourceReaderFiles_is_file(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                    PyObject *kwds) {

    PyErr_SetNone(PyExc_NotImplementedError);
    return NULL;
}
static PyObject *Nuitka_ResourceReaderFiles_joinpath(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                     PyObject *kwds) {

    PyErr_SetNone(PyExc_NotImplementedError);
    return NULL;
}
static PyObject *Nuitka_ResourceReaderFiles_open(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                 PyObject *kwds) {

    PyErr_SetNone(PyExc_NotImplementedError);
    return NULL;
}

static PyObject *Nuitka_ResourceReaderFiles_name(struct Nuitka_ResourceReaderFilesObject *files, PyObject *args,
                                                 PyObject *kwds) {

    PyErr_SetNone(PyExc_NotImplementedError);
    return NULL;
}

static PyObject *Nuitka_ResourceReaderFiles_tp_iternext(struct Nuitka_ResourceReaderFilesObject *files) {
    if (files->m_iterating_entry == NULL) {
        return NULL;
    }

    struct Nuitka_MetaPathBasedLoaderEntry const *current = files->m_iterating_entry;

    while (current != NULL) {
        char const *current_package_name = strrchr(current->name, '.');

        if (current_package_name != NULL) {
            if (strncmp(files->m_loader_entry->name, current_package_name, current_package_name - current->name) == 0) {
            }
        }

        current += 1;
    }

    return NULL;
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
    {"name", (PyCFunction)Nuitka_ResourceReaderFiles_name, METH_NOARGS, NULL},
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
    0,                                                    /* tp_str */
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
    0,                                                    /* tp_getset */
};

static PyObject *Nuitka_ResourceReaderFiles_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
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
    result->m_iterating_entry;

    return (PyObject *)result;
}

#endif