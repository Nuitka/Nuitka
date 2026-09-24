//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"

#include "nuitka/compiled_cell.h"
#include "nuitka/compiled_frame.h"
#include "nuitka/helper/boolean.h"
#include <structmember.h>
#endif

#if PYTHON_VERSION >= 0x3d0

typedef struct {
    PyObject_HEAD struct Nuitka_FrameObject *frame;
} Nuitka_FrameLocalsProxyObject;

static PyTypeObject Nuitka_FrameLocalsProxy_Type;

static void _Nuitka_FrameLocalsProxy_dealloc(PyObject *self);
static int _Nuitka_FrameLocalsProxy_traverse(PyObject *self, visitproc visit, void *arg);
static int _Nuitka_FrameLocalsProxy_clear(PyObject *self);
static Py_ssize_t _Nuitka_FrameLocalsProxy_length(PyObject *self);
static PyObject *_Nuitka_FrameLocalsProxy_subscript(PyObject *self, PyObject *key);
static int _Nuitka_FrameLocalsProxy_ass_subscript(PyObject *self, PyObject *key, PyObject *value);
static int _Nuitka_FrameLocalsProxy_contains(PyObject *self, PyObject *key);
static PyObject *_Nuitka_FrameLocalsProxy_iter(PyObject *self);
static PyObject *_Nuitka_FrameLocalsProxy_repr(PyObject *self);
static void *_Nuitka_FrameLocalsProxy_lookup(Nuitka_FrameLocalsProxyObject *proxy, PyObject *key, int *type_out);

// ---------- FrameLocalsProxy ----------

static void _Nuitka_FrameLocalsProxy_dealloc(PyObject *self) {
    Nuitka_GC_UnTrack(self);
    Py_XDECREF(((Nuitka_FrameLocalsProxyObject *)self)->frame);
    Py_TYPE(self)->tp_free(self);
}

static int _Nuitka_FrameLocalsProxy_traverse(PyObject *self, visitproc visit, void *arg) {
    Py_VISIT(((Nuitka_FrameLocalsProxyObject *)self)->frame);
    return 0;
}

static int _Nuitka_FrameLocalsProxy_clear(PyObject *self) {
    Py_CLEAR(((Nuitka_FrameLocalsProxyObject *)self)->frame);
    return 0;
}

// Build a plain dict snapshot of the locals (storage + f_extra_locals).
// No recursion: it walks the type description directly.
static PyObject *_Nuitka_FrameLocalsProxy_to_dict(Nuitka_FrameLocalsProxyObject *proxy) {
    struct Nuitka_FrameObject *frame = proxy->frame;
    PyCodeObject *co = Nuitka_GetFrameCodeObject(frame);
    PyObject *result = MAKE_DICT_EMPTY(PyThreadState_GET());
    if (result == NULL) {
        return NULL;
    }

    unsigned char const *p = (unsigned char const *)frame->m_type_description;
    if (p != NULL && frame->m_locals_ptr != NULL) {
        PyObject **var_names = Nuitka_GetCodeVarNames(co);
        size_t offset = 0;

        assert(p[co->co_nlocals] == 0);

        for (int i = 0; i < co->co_nlocals; i++) {
            int type = p[i];
            offset = Nuitka_FrameLocals_AlignUp(offset, Nuitka_FrameLocals_Align(type));
            void *slot = (char *)frame->m_locals_ptr + offset;
            PyObject *value = NULL;
            switch (type) {
            case NUITKA_TYPE_DESCRIPTION_OBJECT:
            case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR:
                value = *(PyObject **)slot;
                break;
            case NUITKA_TYPE_DESCRIPTION_CELL: {
                struct Nuitka_CellObject *cell = *(struct Nuitka_CellObject **)slot;
                if (cell != NULL) {
                    value = Nuitka_CellOrPyCell_GET((PyObject *)cell);
                }
                break;
            }
            case NUITKA_TYPE_DESCRIPTION_NILONG: {
                nuitka_ilong *nilong = (nuitka_ilong *)slot;
                if (Nuitka_FrameLocals_NilongActive(nilong)) {
                    ENFORCE_NILONG_OBJECT_VALUE(nilong);
                    value = nilong->python_value;
                }
                break;
            }
            case NUITKA_TYPE_DESCRIPTION_BOOL: {
                nuitka_bool val = *(nuitka_bool *)slot;
                if (val == NUITKA_BOOL_TRUE) {
                    value = Py_True;
                } else if (val == NUITKA_BOOL_FALSE) {
                    value = Py_False;
                }
                break;
            }
            }
            if (value != NULL) {
                PyObject *name = *var_names;
                if (!DICT_SET_ITEM(result, name, value)) {
                    Py_DECREF(result);
                    return NULL;
                }
            }
            var_names++;
            offset += Nuitka_FrameLocals_Size(type);
        }
    }

    if (frame->m_frame.f_extra_locals != NULL) {
        if (PyDict_Update(result, frame->m_frame.f_extra_locals) < 0) {
            Py_DECREF(result);
            return NULL;
        }
    }

    return result;
}

static Py_ssize_t _Nuitka_FrameLocalsProxy_length(PyObject *self) {
    struct Nuitka_FrameObject *frame = ((Nuitka_FrameLocalsProxyObject *)self)->frame;
    Py_ssize_t size = 0;

    PyCodeObject *co = Nuitka_GetFrameCodeObject(frame);
    unsigned char const *p = (unsigned char const *)frame->m_type_description;
    if (p != NULL && frame->m_locals_ptr != NULL) {
        size_t offset = 0;

        assert(p[co->co_nlocals] == 0);

        for (int i = 0; i < co->co_nlocals; i++) {
            int type = p[i];
            offset = Nuitka_FrameLocals_AlignUp(offset, Nuitka_FrameLocals_Align(type));
            void *slot = (char *)frame->m_locals_ptr + offset;
            bool is_active = false;
            switch (type) {
            case NUITKA_TYPE_DESCRIPTION_OBJECT:
            case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR:
                is_active = (*(PyObject **)slot != NULL);
                break;
            case NUITKA_TYPE_DESCRIPTION_CELL: {
                struct Nuitka_CellObject *cell = *(struct Nuitka_CellObject **)slot;
                is_active = (cell != NULL && Nuitka_CellOrPyCell_GET((PyObject *)cell) != NULL);
                break;
            }
            case NUITKA_TYPE_DESCRIPTION_NILONG:
                is_active = Nuitka_FrameLocals_NilongActive((nuitka_ilong *)slot);
                break;
            case NUITKA_TYPE_DESCRIPTION_BOOL: {
                nuitka_bool value = *(nuitka_bool *)slot;
                is_active = (value == NUITKA_BOOL_TRUE || value == NUITKA_BOOL_FALSE);
                break;
            }
            }
            if (is_active) {
                size++;
            }
            offset += Nuitka_FrameLocals_Size(type);
        }
    }

    if (frame->m_frame.f_extra_locals != NULL) {
        size += DICT_SIZE(frame->m_frame.f_extra_locals);
    }

    return size;
}

// Look up a variable name in the locals storage.  Returns the slot pointer
// and the type indicator for a matching name, which may be unbound, or NULL
// if no frame variable has that name.  A NULL return with an exception set
// signals a failed name comparison.
static void *_Nuitka_FrameLocalsProxy_lookup(Nuitka_FrameLocalsProxyObject *proxy, PyObject *key, int *type_out) {
    struct Nuitka_FrameObject *frame = proxy->frame;
    PyCodeObject *co = Nuitka_GetFrameCodeObject(frame);

    unsigned char const *p = (unsigned char const *)frame->m_type_description;
    if (p == NULL || frame->m_locals_ptr == NULL) {
        return NULL;
    }
    PyObject **var_names = Nuitka_GetCodeVarNames(co);
    size_t offset = 0;

    assert(p[co->co_nlocals] == 0);

    for (int i = 0; i < co->co_nlocals; i++) {
        int type = p[i];
        offset = Nuitka_FrameLocals_AlignUp(offset, Nuitka_FrameLocals_Align(type));

        if (type == NUITKA_TYPE_DESCRIPTION_NULL) {
            // No storage exists for this frame variable.
            var_names++;
            offset += Nuitka_FrameLocals_Size(type);
            continue;
        }

        if (*var_names != key) {
            nuitka_bool equal = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(*var_names, key);
            if (unlikely(equal == NUITKA_BOOL_EXCEPTION)) {
                return NULL;
            }
            if (equal == NUITKA_BOOL_FALSE) {
                var_names++;
                offset += Nuitka_FrameLocals_Size(type);
                continue;
            }
        }

        *type_out = type;
        return (char *)frame->m_locals_ptr + offset;
    }

    return NULL;
}

static bool _Nuitka_FrameLocalsProxy_slot_is_active(int type, void *slot) {
    switch (type) {
    case NUITKA_TYPE_DESCRIPTION_OBJECT:
    case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR:
        return *(PyObject **)slot != NULL;
    case NUITKA_TYPE_DESCRIPTION_CELL: {
        struct Nuitka_CellObject *cell = *(struct Nuitka_CellObject **)slot;
        return cell != NULL && Nuitka_CellOrPyCell_GET((PyObject *)cell) != NULL;
    }
    case NUITKA_TYPE_DESCRIPTION_NILONG:
        return Nuitka_FrameLocals_NilongActive((nuitka_ilong *)slot);
    case NUITKA_TYPE_DESCRIPTION_BOOL: {
        nuitka_bool value = *(nuitka_bool *)slot;
        return value == NUITKA_BOOL_TRUE || value == NUITKA_BOOL_FALSE;
    }
    }

    return false;
}

static PyObject *_Nuitka_FrameLocalsProxy_subscript(PyObject *self, PyObject *key) {
    Nuitka_FrameLocalsProxyObject *proxy = (Nuitka_FrameLocalsProxyObject *)self;
    struct Nuitka_FrameObject *frame = proxy->frame;
    PyThreadState *tstate = PyThreadState_GET();
    int type;

    void *slot = _Nuitka_FrameLocalsProxy_lookup(proxy, key, &type);
    if (slot == NULL && HAS_ERROR_OCCURRED(tstate)) {
        return NULL;
    }
    if (slot != NULL && _Nuitka_FrameLocalsProxy_slot_is_active(type, slot)) {
        switch (type) {
        case NUITKA_TYPE_DESCRIPTION_OBJECT:
        case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
            PyObject *value = *(PyObject **)slot;
            CHECK_OBJECT(value);
            Py_INCREF(value);
            return value;
        }
        case NUITKA_TYPE_DESCRIPTION_CELL: {
            struct Nuitka_CellObject *cell = *(struct Nuitka_CellObject **)slot;
            PyObject *value = Nuitka_CellOrPyCell_GET((PyObject *)cell);
            CHECK_OBJECT(value);
            Py_INCREF(value);
            return value;
        }
        case NUITKA_TYPE_DESCRIPTION_NILONG: {
            nuitka_ilong *nilong = (nuitka_ilong *)slot;
            ENFORCE_NILONG_OBJECT_VALUE(nilong);
            PyObject *value = nilong->python_value;
            CHECK_OBJECT(value);
            Py_INCREF(value);
            return value;
        }
        case NUITKA_TYPE_DESCRIPTION_BOOL: {
            nuitka_bool val = *(nuitka_bool *)slot;
            PyObject *result = (val == NUITKA_BOOL_TRUE) ? Py_True : Py_False;
            Py_INCREF(result);
            return result;
        }
        }
    }

    if (frame->m_frame.f_extra_locals != NULL) {
        PyObject *value = DICT_GET_ITEM_WITH_HASH_ERROR1(tstate, frame->m_frame.f_extra_locals, key);
        if (value != NULL) {
            return value;
        }
        if (HAS_ERROR_OCCURRED(tstate)) {
            return NULL;
        }
    }

    PyObject *message = Nuitka_String_FromFormat("local variable '%R' is not defined", key);
    if (unlikely(message == NULL)) {
        return NULL;
    }
    SET_CURRENT_EXCEPTION_TYPE0_VALUE1(tstate, PyExc_KeyError, message);
    return NULL;
}

static int _Nuitka_FrameLocalsProxy_ass_subscript(PyObject *self, PyObject *key, PyObject *value) {
    Nuitka_FrameLocalsProxyObject *proxy = (Nuitka_FrameLocalsProxyObject *)self;
    struct Nuitka_FrameObject *frame = proxy->frame;
    PyThreadState *tstate = PyThreadState_GET();
    int type;
    void *slot;

#if PYTHON_VERSION < 0x3d1
    // Python 3.13.0 did not allow removing anything from the proxy at all.
    if (value == NULL) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "cannot remove variables from FrameLocalsProxy");
        return -1;
    }
#endif

    slot = _Nuitka_FrameLocalsProxy_lookup(proxy, key, &type);
    if (slot == NULL && HAS_ERROR_OCCURRED(tstate)) {
        return -1;
    }
    if (slot != NULL) {
#if PYTHON_VERSION >= 0x3d1
        if (value == NULL) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError,
                                            "cannot remove local variables from FrameLocalsProxy");
            return -1;
        }
#endif

        switch (type) {
        case NUITKA_TYPE_DESCRIPTION_OBJECT:
        case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
            PyObject *old = *(PyObject **)slot;
            *(PyObject **)slot = value;
            Py_INCREF(value);
            Py_XDECREF(old);
            return 0;
        }
        case NUITKA_TYPE_DESCRIPTION_CELL: {
            struct Nuitka_CellObject *cell = *(struct Nuitka_CellObject **)slot;

            if (cell == NULL) {
                cell = Nuitka_Cell_New0(value);
                *(struct Nuitka_CellObject **)slot = cell;
                return 0;
            }

            PyObject *old = Nuitka_CellOrPyCell_GET((PyObject *)cell);
            Nuitka_CellOrPyCell_SET((PyObject *)cell, value);
            Py_INCREF(value);
            Py_XDECREF(old);
            return 0;
        }
        case NUITKA_TYPE_DESCRIPTION_NILONG: {
            nuitka_ilong *nilong = (nuitka_ilong *)slot;
            RELEASE_NILONG_VALUE(nilong);
            SET_NILONG_OBJECT_VALUE(nilong, value);
            Py_INCREF(value);
            return 0;
        }
        case NUITKA_TYPE_DESCRIPTION_BOOL: {
            if (!PyBool_Check(value)) {
                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                                "type-incompatible write to dual-typed local");
                return -1;
            }
            *(nuitka_bool *)slot = (value == Py_True) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            return 0;
        }
        }
    }

    if (value == NULL) {
        if (frame->m_frame.f_extra_locals == NULL) {
            SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);
            return -1;
        }
        return DICT_REMOVE_ITEM(frame->m_frame.f_extra_locals, key) ? 0 : -1;
    }
    if (frame->m_frame.f_extra_locals == NULL) {
        frame->m_frame.f_extra_locals = MAKE_DICT_EMPTY(tstate);
        if (frame->m_frame.f_extra_locals == NULL) {
            return -1;
        }
    }
    return DICT_SET_ITEM(frame->m_frame.f_extra_locals, key, value) ? 0 : -1;
}

static int _Nuitka_FrameLocalsProxy_contains(PyObject *self, PyObject *key) {
    Nuitka_FrameLocalsProxyObject *proxy = (Nuitka_FrameLocalsProxyObject *)self;
    PyThreadState *tstate = PyThreadState_GET();
    int type;
    void *slot = _Nuitka_FrameLocalsProxy_lookup(proxy, key, &type);
    if (slot != NULL) {
        return _Nuitka_FrameLocalsProxy_slot_is_active(type, slot) ? 1 : 0;
    }
    if (HAS_ERROR_OCCURRED(tstate)) {
        return -1;
    }
    if (proxy->frame->m_frame.f_extra_locals != NULL) {
        return DICT_HAS_ITEM(tstate, proxy->frame->m_frame.f_extra_locals, key);
    }
    return 0;
}

static PyObject *_Nuitka_FrameLocalsProxy_iter(PyObject *self) {
    PyObject *snapshot_dict = _Nuitka_FrameLocalsProxy_to_dict((Nuitka_FrameLocalsProxyObject *)self);
    if (snapshot_dict == NULL) {
        return NULL;
    }
    PyObject *result = MAKE_ITERATOR(PyThreadState_GET(), snapshot_dict);
    Py_DECREF(snapshot_dict);
    return result;
}

static PyObject *_Nuitka_FrameLocalsProxy_repr(PyObject *self) {
    int i = Py_ReprEnter(self);
    if (i != 0) {
        return i > 0 ? Nuitka_String_FromString("{...}") : NULL;
    }
    PyObject *snapshot_dict = _Nuitka_FrameLocalsProxy_to_dict((Nuitka_FrameLocalsProxyObject *)self);
    if (snapshot_dict == NULL) {
        Py_ReprLeave(self);
        return NULL;
    }
    PyObject *result = PyObject_Repr(snapshot_dict);
    Py_DECREF(snapshot_dict);
    Py_ReprLeave(self);
    return result;
}

// Build a snapshot dict and delegate the non-mutating view methods to it.
static PyObject *_Nuitka_FrameLocalsProxy_copy(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return _Nuitka_FrameLocalsProxy_to_dict((Nuitka_FrameLocalsProxyObject *)self);
}

static PyObject *_Nuitka_FrameLocalsProxy_keys(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    PyObject *snapshot_dict = _Nuitka_FrameLocalsProxy_to_dict((Nuitka_FrameLocalsProxyObject *)self);
    if (snapshot_dict == NULL) {
        return NULL;
    }
    PyObject *result = PyDict_Keys(snapshot_dict);
    Py_DECREF(snapshot_dict);
    return result;
}

static PyObject *_Nuitka_FrameLocalsProxy_values(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    PyObject *snapshot_dict = _Nuitka_FrameLocalsProxy_to_dict((Nuitka_FrameLocalsProxyObject *)self);
    if (snapshot_dict == NULL) {
        return NULL;
    }
    PyObject *result = PyDict_Values(snapshot_dict);
    Py_DECREF(snapshot_dict);
    return result;
}

static PyObject *_Nuitka_FrameLocalsProxy_items(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    PyObject *snapshot_dict = _Nuitka_FrameLocalsProxy_to_dict((Nuitka_FrameLocalsProxyObject *)self);
    if (snapshot_dict == NULL) {
        return NULL;
    }
    PyObject *result = PyDict_Items(snapshot_dict);
    Py_DECREF(snapshot_dict);
    return result;
}

static PyObject *_Nuitka_FrameLocalsProxy_get(PyObject *self, PyObject *args) {
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *key;
    PyObject *default_value = Py_None;
    if (!PyArg_UnpackTuple(args, "get", 1, 2, &key, &default_value)) {
        return NULL;
    }

    PyObject *result = _Nuitka_FrameLocalsProxy_subscript(self, key);
    if (result != NULL) {
        return result;
    }

    if (!CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {
        return NULL;
    }
    Py_INCREF(default_value);
    return default_value;
}

#if PYTHON_VERSION >= 0x3d1
static PyObject *_Nuitka_FrameLocalsProxy_pop(PyObject *self, PyObject *args) {
    Nuitka_FrameLocalsProxyObject *proxy = (Nuitka_FrameLocalsProxyObject *)self;
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *key;
    PyObject *default_value = NULL;
    if (!PyArg_UnpackTuple(args, "pop", 1, 2, &key, &default_value)) {
        return NULL;
    }

    int type;
    void *slot = _Nuitka_FrameLocalsProxy_lookup(proxy, key, &type);
    if (slot == NULL && HAS_ERROR_OCCURRED(tstate)) {
        return NULL;
    }
    if (slot != NULL) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError,
                                        "cannot remove local variables from FrameLocalsProxy");
        return NULL;
    }

    if (proxy->frame->m_frame.f_extra_locals != NULL) {
        if (default_value != NULL) {
            return DICT_POP3(tstate, proxy->frame->m_frame.f_extra_locals, key, default_value);
        } else {
            return DICT_POP2(tstate, proxy->frame->m_frame.f_extra_locals, key);
        }
    }

    if (default_value != NULL) {
        Py_INCREF(default_value);
        return default_value;
    }
    SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);
    return NULL;
}
#endif

static PyObject *_Nuitka_FrameLocalsProxy_update(PyObject *self, PyObject *other) {
    PyThreadState *tstate = PyThreadState_GET();

    if (!PyDict_Check(other) && !Nuitka_PyObject_TypeCheck(other, &Nuitka_FrameLocalsProxy_Type)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                        "update() argument must be dict or another FrameLocalsProxy");
        return NULL;
    }

    PyObject *items = PyMapping_Items(other);
    if (items == NULL) {
        return NULL;
    }

    for (Py_ssize_t i = 0; i < PyList_GET_SIZE(items); i++) {
        PyObject *pair = PyList_GET_ITEM(items, i);
        PyObject *key = PyTuple_GET_ITEM(pair, 0);
        PyObject *value = PyTuple_GET_ITEM(pair, 1);

        if (_Nuitka_FrameLocalsProxy_ass_subscript(self, key, value) < 0) {
            Py_DECREF(items);
            return NULL;
        }
    }

    Py_DECREF(items);

    Py_RETURN_NONE;
}

static PyObject *_Nuitka_FrameLocalsProxy_setdefault(PyObject *self, PyObject *args) {
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *key;
    PyObject *default_value = Py_None;
    if (!PyArg_UnpackTuple(args, "setdefault", 1, 2, &key, &default_value)) {
        return NULL;
    }

    PyObject *result = _Nuitka_FrameLocalsProxy_subscript(self, key);
    if (result != NULL) {
        return result;
    }

    if (!CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {
        return NULL;
    }

    if (_Nuitka_FrameLocalsProxy_ass_subscript(self, key, default_value) < 0) {
        return NULL;
    }

    Py_INCREF(default_value);
    return default_value;
}

static PyObject *_Nuitka_FrameLocalsProxy_reversed(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    PyObject *keys = _Nuitka_FrameLocalsProxy_keys(self, NULL);
    if (keys == NULL) {
        return NULL;
    }

    PyObject *list_keys = PySequence_List(keys);
    Py_DECREF(keys);
    if (list_keys == NULL) {
        return NULL;
    }

    LIST_REVERSE(list_keys);
    return list_keys;
}

static PyObject *_Nuitka_FrameLocalsProxy_contains_object(PyObject *self, PyObject *key) {
    int result = _Nuitka_FrameLocalsProxy_contains(self, key);
    if (result < 0) {
        return NULL;
    }
    PyObject *result_object = BOOL_FROM(result != 0);
    Py_INCREF_IMMORTAL(result_object);
    return result_object;
}

static PyMethodDef Nuitka_FrameLocalsProxy_methods[] = {
    {"__getitem__", (PyCFunction)_Nuitka_FrameLocalsProxy_subscript, METH_O, NULL},
    {"__contains__", (PyCFunction)_Nuitka_FrameLocalsProxy_contains_object, METH_O, NULL},
    {"copy", (PyCFunction)_Nuitka_FrameLocalsProxy_copy, METH_NOARGS, NULL},
    {"keys", (PyCFunction)_Nuitka_FrameLocalsProxy_keys, METH_NOARGS, NULL},
    {"values", (PyCFunction)_Nuitka_FrameLocalsProxy_values, METH_NOARGS, NULL},
    {"items", (PyCFunction)_Nuitka_FrameLocalsProxy_items, METH_NOARGS, NULL},
    {"get", (PyCFunction)_Nuitka_FrameLocalsProxy_get, METH_VARARGS, NULL},
#if PYTHON_VERSION >= 0x3d1
    {"pop", (PyCFunction)_Nuitka_FrameLocalsProxy_pop, METH_VARARGS, NULL},
#endif
    {"setdefault", (PyCFunction)_Nuitka_FrameLocalsProxy_setdefault, METH_VARARGS, NULL},
    {"update", (PyCFunction)_Nuitka_FrameLocalsProxy_update, METH_O, NULL},
    {"__reversed__", (PyCFunction)_Nuitka_FrameLocalsProxy_reversed, METH_NOARGS, NULL},
    {NULL, NULL},
};

static PyObject *_Nuitka_FrameLocalsProxy_richcompare(PyObject *self, PyObject *other, int op) {
    if (op != Py_EQ && op != Py_NE) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    if (Nuitka_PyObject_TypeCheck(other, &Nuitka_FrameLocalsProxy_Type)) {
        bool result = ((Nuitka_FrameLocalsProxyObject *)self)->frame == ((Nuitka_FrameLocalsProxyObject *)other)->frame;
        PyObject *result_object = BOOL_FROM(op == Py_EQ ? result : !result);
        Py_INCREF_IMMORTAL(result_object);
        return result_object;
    } else if (PyDict_Check(other)) {
        PyObject *snapshot_dict = _Nuitka_FrameLocalsProxy_to_dict((Nuitka_FrameLocalsProxyObject *)self);
        if (snapshot_dict == NULL) {
            return NULL;
        }
        PyObject *result = PyObject_RichCompare(snapshot_dict, other, op);
        Py_DECREF(snapshot_dict);
        return result;
    }

    Py_RETURN_NOTIMPLEMENTED;
}

// Mapping protocol
static PyMappingMethods Nuitka_FrameLocalsProxy_as_mapping = {
    (lenfunc)_Nuitka_FrameLocalsProxy_length,              // mp_length
    (binaryfunc)_Nuitka_FrameLocalsProxy_subscript,        // mp_subscript
    (objobjargproc)_Nuitka_FrameLocalsProxy_ass_subscript, // mp_ass_subscript
};

static PySequenceMethods Nuitka_FrameLocalsProxy_as_sequence = {
    0,                                             // sq_length
    0,                                             // sq_concat
    0,                                             // sq_repeat
    0,                                             // sq_item
    0,                                             // was_sq_slice
    0,                                             // sq_ass_item
    0,                                             // was_sq_ass_slice
    (objobjproc)_Nuitka_FrameLocalsProxy_contains, // sq_contains
    0,                                             // sq_inplace_concat
    0,                                             // sq_inplace_repeat
};

static PyObject *_Nuitka_FrameLocalsProxy_new(PyTypeObject *type, PyObject *args, PyObject *kwds);

static PyTypeObject Nuitka_FrameLocalsProxy_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_FrameLocalsProxy",
    sizeof(Nuitka_FrameLocalsProxyObject),
    0,
    (destructor)_Nuitka_FrameLocalsProxy_dealloc,                 // tp_dealloc
    0,                                                            // tp_print
    0,                                                            // tp_getattr
    0,                                                            // tp_setattr
    0,                                                            // tp_compare
    (reprfunc)_Nuitka_FrameLocalsProxy_repr,                      // tp_repr
    0,                                                            // tp_as_number
    &Nuitka_FrameLocalsProxy_as_sequence,                         // tp_as_sequence
    &Nuitka_FrameLocalsProxy_as_mapping,                          // tp_as_mapping
    0,                                                            // tp_hash
    0,                                                            // tp_call
    0,                                                            // tp_str
    PyObject_GenericGetAttr,                                      // tp_getattro
    PyObject_GenericSetAttr,                                      // tp_setattro
    0,                                                            // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_MAPPING, // tp_flags
    0,                                                            // tp_doc
    (traverseproc)_Nuitka_FrameLocalsProxy_traverse,              // tp_traverse
    (inquiry)_Nuitka_FrameLocalsProxy_clear,                      // tp_clear
    _Nuitka_FrameLocalsProxy_richcompare,                         // tp_richcompare
    0,                                                            // tp_weaklistoffset
    _Nuitka_FrameLocalsProxy_iter,                                // tp_iter
    0,                                                            // tp_iternext
    Nuitka_FrameLocalsProxy_methods,                              // tp_methods
    0,                                                            // tp_members
    0,                                                            // tp_getset
    0,                                                            // tp_base
    0,                                                            // tp_dict
    0,                                                            // tp_descr_get
    0,                                                            // tp_descr_set
    0,                                                            // tp_dictoffset
    0,                                                            // tp_init
    PyType_GenericAlloc,                                          // tp_alloc
    (newfunc)_Nuitka_FrameLocalsProxy_new,                        // tp_new
    PyObject_GC_Del,                                              // tp_free
};

// Create a new FrameLocalsProxy for the given frame.
static PyObject *_Nuitka_FrameLocalsProxy_New(struct Nuitka_FrameObject *frame) {
    Nuitka_FrameLocalsProxyObject *proxy = Nuitka_GC_New(&Nuitka_FrameLocalsProxy_Type);
    if (proxy == NULL) {
        return NULL;
    }
    Py_INCREF(frame);
    proxy->frame = frame;
    Nuitka_GC_Track((PyObject *)proxy);
    return (PyObject *)proxy;
}

static PyObject *_Nuitka_FrameLocalsProxy_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    if (PyTuple_GET_SIZE(args) != 1) {
        PyErr_Format(PyExc_TypeError, "%s expected 1 argument, got %zd", type->tp_name, PyTuple_GET_SIZE(args));
        return NULL;
    }

    PyObject *frame = PyTuple_GET_ITEM(args, 0);

    // Exact check only, so no GC tracking of arbitrary objects is inspected.
    if (!Nuitka_Frame_CheckExact(frame)) {
        // The "%T" format exists since Python 3.12 and like CPython this uses
        // the qualified type name. The COMPLAINT helper would only do that on
        // 3.14+.
        PyErr_Format(PyExc_TypeError, "expect frame, not %T", frame);
        return NULL;
    }

    // Like CPython, this is checked after the type, so the type complaint wins.
    if (kwds != NULL && PyDict_GET_SIZE(kwds) != 0) {
        PyErr_Format(PyExc_TypeError, "%s takes no keyword arguments", type->tp_name);
        return NULL;
    }

    return _Nuitka_FrameLocalsProxy_New((struct Nuitka_FrameObject *)frame);
}

static void _initCompiledFrameLocalsProxyType(void) {
    Nuitka_PyType_Ready(&Nuitka_FrameLocalsProxy_Type, NULL, false, false, false, false, false);
}

#endif // PYTHON_VERSION >= 0x3d0

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
