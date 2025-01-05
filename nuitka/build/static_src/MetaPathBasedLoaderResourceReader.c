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

// Just for the IDE to know, this file is not included otherwise.
#if PYTHON_VERSION >= 0x370

struct Nuitka_ResourceReaderObject {
    /* Python object folklore: */
    PyObject_HEAD

        /* The loader entry, to know this is about exactly. */
        struct Nuitka_MetaPathBasedLoaderEntry const *m_loader_entry;
};

static void Nuitka_ResourceReader_tp_dealloc(struct Nuitka_ResourceReaderObject *reader) {
    Nuitka_GC_UnTrack(reader);

    PyObject_GC_Del(reader);
}

static PyObject *Nuitka_ResourceReader_tp_repr(struct Nuitka_ResourceReaderObject *reader) {
    return PyUnicode_FromFormat("<nuitka_resource_reader for '%s'>", reader->m_loader_entry->name);
}

// Obligatory, even if we have nothing to own
static int Nuitka_ResourceReader_tp_traverse(struct Nuitka_ResourceReaderObject *reader, visitproc visit, void *arg) {
    return 0;
}

static PyObject *_Nuitka_ResourceReader_resource_path(PyThreadState *tstate, struct Nuitka_ResourceReaderObject *reader,
                                                      PyObject *resource) {
    PyObject *dir_name = getModuleDirectory(tstate, reader->m_loader_entry);

    if (unlikely(dir_name == NULL)) {
        return NULL;
    }

    PyObject *result = JOIN_PATH2(dir_name, resource);
    Py_DECREF(dir_name);

    return result;
}

static PyObject *Nuitka_ResourceReader_resource_path(struct Nuitka_ResourceReaderObject *reader, PyObject *args,
                                                     PyObject *kwds) {
    PyObject *resource;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:resource_path", (char **)_kw_list_get_data, &resource);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    return _Nuitka_ResourceReader_resource_path(tstate, reader, resource);
}

static PyObject *Nuitka_ResourceReader_open_resource(struct Nuitka_ResourceReaderObject *reader, PyObject *args,
                                                     PyObject *kwds) {
    PyObject *resource;

    int res = PyArg_ParseTupleAndKeywords(args, kwds, "O:open_resource", (char **)_kw_list_get_data, &resource);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *filename = _Nuitka_ResourceReader_resource_path(tstate, reader, resource);

    return BUILTIN_OPEN_BINARY_READ_SIMPLE(tstate, filename);
}

#include "MetaPathBasedLoaderResourceReaderFiles.c"

static PyObject *Nuitka_ResourceReader_files(struct Nuitka_ResourceReaderObject *reader, PyObject *args,
                                             PyObject *kwds) {

    PyThreadState *tstate = PyThreadState_GET();
    return Nuitka_ResourceReaderFiles_New(tstate, reader->m_loader_entry, const_str_empty);
}

static PyMethodDef Nuitka_ResourceReader_methods[] = {
    {"resource_path", (PyCFunction)Nuitka_ResourceReader_resource_path, METH_VARARGS | METH_KEYWORDS, NULL},
    {"open_resource", (PyCFunction)Nuitka_ResourceReader_open_resource, METH_VARARGS | METH_KEYWORDS, NULL},
    {"files", (PyCFunction)Nuitka_ResourceReader_files, METH_NOARGS, NULL},
    {NULL}};

static PyTypeObject Nuitka_ResourceReader_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "nuitka_resource_reader",
    sizeof(struct Nuitka_ResourceReaderObject),      // tp_basicsize
    0,                                               // tp_itemsize
    (destructor)Nuitka_ResourceReader_tp_dealloc,    // tp_dealloc
    0,                                               // tp_print
    0,                                               // tp_getattr
    0,                                               // tp_setattr
    0,                                               // tp_reserved
    (reprfunc)Nuitka_ResourceReader_tp_repr,         // tp_repr
    0,                                               // tp_as_number
    0,                                               // tp_as_sequence
    0,                                               // tp_as_mapping
    0,                                               // tp_hash
    0,                                               // tp_call
    0,                                               // tp_str
    0,                                               // tp_getattro (PyObject_GenericGetAttr)
    0,                                               // tp_setattro
    0,                                               // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,         // tp_flags
    0,                                               // tp_doc
    (traverseproc)Nuitka_ResourceReader_tp_traverse, // tp_traverse
    0,                                               // tp_clear
    0,                                               // tp_richcompare
    0,                                               // tp_weaklistoffset
    0,                                               // tp_iter
    0,                                               // tp_iternext
    Nuitka_ResourceReader_methods,                   // tp_methods
    0,                                               // tp_members
    0,                                               // tp_getset
};

static PyObject *Nuitka_ResourceReader_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry) {
    struct Nuitka_ResourceReaderObject *result;

    result = (struct Nuitka_ResourceReaderObject *)Nuitka_GC_New(&Nuitka_ResourceReader_Type);
    Nuitka_GC_Track(result);

    result->m_loader_entry = entry;

    return (PyObject *)result;
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
