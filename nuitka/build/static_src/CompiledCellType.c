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

#include "nuitka/prelude.h"

#include "nuitka/freelists.h"

#define MAX_CELL_FREE_LIST_COUNT 1000
static struct Nuitka_CellObject *free_list_cells = NULL;
static int free_list_cells_count = 0;

static void Nuitka_Cell_tp_dealloc(struct Nuitka_CellObject *cell) {
    Nuitka_GC_UnTrack(cell);
    Py_XDECREF(cell->ob_ref);

    releaseToFreeList(free_list_cells, cell, MAX_CELL_FREE_LIST_COUNT);
}

#if PYTHON_VERSION < 0x300
static int Nuitka_Cell_tp_compare(struct Nuitka_CellObject *cell_a, struct Nuitka_CellObject *cell_b) {
    /* Empty cells compare specifically different. */
    if (cell_a->ob_ref == NULL) {
        if (cell_b->ob_ref == NULL) {
            return 0;
        }

        return -1;
    }

    if (cell_b->ob_ref == NULL) {
        return 1;
    }

    return PyObject_Compare(cell_a->ob_ref, cell_b->ob_ref);
}
#else
static PyObject *Nuitka_Cell_tp_richcompare(PyObject *a, PyObject *b, int op) {
    PyObject *result;

    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

    if (unlikely(!Nuitka_Cell_Check(a) || !Nuitka_Cell_Check(b))) {
        result = Py_NotImplemented;
        Py_INCREF(result);

        return result;
    }

    /* Now just dereference, and compare from there by contents. */
    a = ((struct Nuitka_CellObject *)a)->ob_ref;
    b = ((struct Nuitka_CellObject *)b)->ob_ref;

    if (a != NULL && b != NULL) {
        return PyObject_RichCompare(a, b, op);
    }

    int res = (b == NULL) - (a == NULL);
    switch (op) {
    case Py_EQ:
        result = BOOL_FROM(res == 0);
        break;
    case Py_NE:
        result = BOOL_FROM(res != 0);
        break;
    case Py_LE:
        result = BOOL_FROM(res <= 0);
        break;
    case Py_GE:
        result = BOOL_FROM(res >= 0);
        break;
    case Py_LT:
        result = BOOL_FROM(res < 0);
        break;
    case Py_GT:
        result = BOOL_FROM(res > 0);
        break;
    default:
        PyErr_BadArgument();
        return NULL;
    }

    Py_INCREF(result);
    return result;
}

#endif

static PyObject *Nuitka_Cell_tp_repr(struct Nuitka_CellObject *cell) {
    if (cell->ob_ref == NULL) {
#if PYTHON_VERSION < 0x300
        return PyString_FromFormat(
#else
        return PyUnicode_FromFormat(
#endif
            "<compiled_cell at %p: empty>", cell);
    } else {
#if PYTHON_VERSION < 0x300
        return PyString_FromFormat(
#else
        return PyUnicode_FromFormat(
#endif
            "<compiled_cell at %p: %s object at %p>", cell, cell->ob_ref->ob_type->tp_name, cell->ob_ref);
    }
}

static int Nuitka_Cell_tp_traverse(struct Nuitka_CellObject *cell, visitproc visit, void *arg) {
    Py_VISIT(cell->ob_ref);

    return 0;
}

static int Nuitka_Cell_tp_clear(struct Nuitka_CellObject *cell) {
    Py_CLEAR(cell->ob_ref);

    return 0;
}

static PyObject *Nuitka_Cell_get_contents(struct Nuitka_CellObject *cell, void *closure) {
    if (cell->ob_ref == NULL) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "Cell is empty");
        return NULL;
    }

    Py_INCREF(cell->ob_ref);
    return cell->ob_ref;
}

#if PYTHON_VERSION >= 0x370
static int Nuitka_Cell_set_contents(struct Nuitka_CellObject *cell, PyObject *value) {
    PyObject *old = cell->ob_ref;

    if (old != NULL && value == NULL) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "cell_contents cannot be used to delete values Nuitka");
        return -1;
    }

    cell->ob_ref = value;
    Py_XINCREF(value);
    Py_XDECREF(old);

    return 0;
}
#endif

static PyGetSetDef Nuitka_Cell_getsetlist[] = {
#if PYTHON_VERSION < 0x370
    {(char *)"cell_contents", (getter)Nuitka_Cell_get_contents, NULL, NULL},
#else
    {(char *)"cell_contents", (getter)Nuitka_Cell_get_contents, (setter)Nuitka_Cell_set_contents, NULL},
#endif
    {NULL}};

PyTypeObject Nuitka_Cell_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_cell",
    sizeof(struct Nuitka_CellObject),
    0,
    (destructor)Nuitka_Cell_tp_dealloc, /* tp_dealloc */
    0,                                  /* tp_print */
    0,                                  /* tp_getattr */
    0,                                  /* tp_setattr */
#if PYTHON_VERSION < 0x300
    (cmpfunc)Nuitka_Cell_tp_compare, /* tp_compare */
#else
    0,                          /* tp_reserved */
#endif
    (reprfunc)Nuitka_Cell_tp_repr,           /* tp_repr */
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
    (traverseproc)Nuitka_Cell_tp_traverse,   /* tp_traverse */
    (inquiry)Nuitka_Cell_tp_clear,           /* tp_clear */
#if PYTHON_VERSION < 0x300
    0, /* tp_richcompare */
#else
    Nuitka_Cell_tp_richcompare, /* tp_richcompare */
#endif
    0,                      /* tp_weaklistoffset */
    0,                      /* tp_iter */
    0,                      /* tp_iternext */
    0,                      /* tp_methods */
    0,                      /* tp_members */
    Nuitka_Cell_getsetlist, /* tp_getset */
};

void _initCompiledCellType(void) { PyType_Ready(&Nuitka_Cell_Type); }

struct Nuitka_CellObject *Nuitka_Cell_Empty(void) {
    struct Nuitka_CellObject *result;

    allocateFromFreeListFixed(free_list_cells, struct Nuitka_CellObject, Nuitka_Cell_Type);

    result->ob_ref = NULL;

    Nuitka_GC_Track(result);

    return result;
}

struct Nuitka_CellObject *Nuitka_Cell_New0(PyObject *value) {
    CHECK_OBJECT(value);

    struct Nuitka_CellObject *result;

    allocateFromFreeListFixed(free_list_cells, struct Nuitka_CellObject, Nuitka_Cell_Type);

    result->ob_ref = value;
    Py_INCREF(value);

    Nuitka_GC_Track(result);

    return result;
}

struct Nuitka_CellObject *Nuitka_Cell_New1(PyObject *value) {
    CHECK_OBJECT(value);

    struct Nuitka_CellObject *result;

    allocateFromFreeListFixed(free_list_cells, struct Nuitka_CellObject, Nuitka_Cell_Type);

    result->ob_ref = value;

    Nuitka_GC_Track(result);

    return result;
}