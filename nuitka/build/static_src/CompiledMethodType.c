//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** Compiled methods.
 *
 * It strives to be full replacement for normal method objects, but
 * normally should be avoided to exist in Nuitka calls.
 *
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/freelists.h"
#include "nuitka/prelude.h"
#include <structmember.h>
#endif

static PyObject *Nuitka_Method_get__doc__(PyObject *self, void *data) {
    struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)self;
    PyObject *result = method->m_function->m_doc;

    if (result == NULL) {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static PyGetSetDef Nuitka_Method_tp_getset[] = {{(char *)"__doc__", Nuitka_Method_get__doc__, NULL, NULL}, {NULL}};

#define OFF(x) offsetof(struct Nuitka_MethodObject, x)

static PyMemberDef Nuitka_Method_members[] = {
    {(char *)"im_class", T_OBJECT, OFF(m_class), READONLY | RESTRICTED, (char *)"the class associated with a method"},
    {(char *)"im_func", T_OBJECT, OFF(m_function), READONLY | RESTRICTED,
     (char *)"the function (or other callable) implementing a method"},
    {(char *)"__func__", T_OBJECT, OFF(m_function), READONLY | RESTRICTED,
     (char *)"the function (or other callable) implementing a method"},
    {(char *)"im_self", T_OBJECT, OFF(m_object), READONLY | RESTRICTED,
     (char *)"the instance to which a method is bound; None for unbound method"},
    {(char *)"__self__", T_OBJECT, OFF(m_object), READONLY | RESTRICTED,
     (char *)"the instance to which a method is bound; None for unbound method"},
    {NULL}};

static PyObject *Nuitka_Method_reduce(struct Nuitka_MethodObject *method, PyObject *unused) {
    PyThreadState *tstate = PyThreadState_GET();

#if PYTHON_VERSION < 0x300
    // spell-checker: ignore instancemethod
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "can't pickle instancemethod objects");
    return NULL;
#else
    PyObject *result = MAKE_TUPLE_EMPTY(tstate, 2);
    PyTuple_SET_ITEM0(result, 0, LOOKUP_BUILTIN(const_str_plain_getattr));
    PyObject *arg_tuple = MAKE_TUPLE2(tstate, method->m_object, method->m_function->m_name);
    PyTuple_SET_ITEM(result, 1, arg_tuple);

    CHECK_OBJECT_DEEP(result);

    return result;
#endif
}

static PyObject *Nuitka_Method_reduce_ex(struct Nuitka_MethodObject *method, PyObject *args) {
    int proto;

    if (!PyArg_ParseTuple(args, "|i:__reduce_ex__", &proto)) {
        return NULL;
    }

    // Python API, spell-checker: ignore copyreg,newobj

#if PYTHON_VERSION < 0x300
    PyObject *copy_reg = PyImport_ImportModule("copy_reg");

    CHECK_OBJECT(copy_reg);
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *newobj_func = LOOKUP_ATTRIBUTE(tstate, copy_reg, const_str_plain___newobj__);
    Py_DECREF(copy_reg);
    if (unlikely(newobj_func == NULL)) {
        return NULL;
    }

    PyObject *result = MAKE_TUPLE_EMPTY(tstate, 5);
    PyTuple_SET_ITEM(result, 0, newobj_func);
    PyObject *type_tuple = MAKE_TUPLE1(tstate, (PyObject *)&Nuitka_Method_Type);
    PyTuple_SET_ITEM(result, 1, type_tuple);
    PyTuple_SET_ITEM_IMMORTAL(result, 2, Py_None);
    PyTuple_SET_ITEM_IMMORTAL(result, 3, Py_None);
    PyTuple_SET_ITEM_IMMORTAL(result, 4, Py_None);

    CHECK_OBJECT_DEEP(result);

    return result;
#else
    return Nuitka_Method_reduce(method, NULL);
#endif
}

static PyObject *Nuitka_Method_deepcopy(struct Nuitka_MethodObject *method, PyObject *memo) {
    assert(Nuitka_Method_Check((PyObject *)method));

    static PyObject *module_copy = NULL;
    static PyObject *deepcopy_function = NULL;

    if (module_copy == NULL) {
        module_copy = PyImport_ImportModule("copy");
        CHECK_OBJECT(module_copy);

        deepcopy_function = PyObject_GetAttrString(module_copy, "deepcopy");
        CHECK_OBJECT(deepcopy_function);
    }

    PyObject *object = PyObject_CallFunctionObjArgs(deepcopy_function, method->m_object, memo, NULL);

    if (unlikely(object == NULL)) {
        return NULL;
    }

    PyObject *result = Nuitka_Method_New(method->m_function, object, method->m_class);
    // Nuitka_Method_New took a reference to the object.
    Py_DECREF(object);
    return result;
}

static PyMethodDef Nuitka_Method_methods[] = {
    {"__reduce__", (PyCFunction)Nuitka_Method_reduce, METH_NOARGS, NULL},
    {"__reduce_ex__", (PyCFunction)Nuitka_Method_reduce_ex, METH_VARARGS, NULL},
    {"__deepcopy__", (PyCFunction)Nuitka_Method_deepcopy, METH_O, NULL},
    {NULL}};

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_SLOT)
static PyObject *Nuitka_Method_tp_vectorcall(struct Nuitka_MethodObject *method, PyObject *const *stack, size_t nargsf,
                                             PyObject *kwnames) {
    assert(Nuitka_Method_Check((PyObject *)method));
    assert(kwnames == NULL || PyTuple_CheckExact(kwnames));
    Py_ssize_t nkwargs = (kwnames == NULL) ? 0 : PyTuple_GET_SIZE(kwnames);
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);

    assert(nargs >= 0);
    assert((nargs == 0 && nkwargs == 0) || stack != NULL);

    Py_ssize_t totalargs = nargs + nkwargs;

    // Shortcut possible, no args.
    if (totalargs == 0) {
        return Nuitka_CallMethodFunctionNoArgs(PyThreadState_GET(), method->m_function, method->m_object);
    }

    PyObject *result;

    if (nargsf & PY_VECTORCALL_ARGUMENTS_OFFSET) {
        /* We are allowed to mutate the stack. TODO: Is this the normal case, so
           we can consider the else branch irrelevant? Also does it not make sense
           to check pos arg and kw counts and shortcut somewhat. */

        PyObject **new_args = (PyObject **)stack - 1;

        PyObject *tmp = new_args[0];
        new_args[0] = method->m_object;

        CHECK_OBJECTS(new_args, totalargs + 1);

        result = Nuitka_CallFunctionVectorcall(PyThreadState_GET(), method->m_function, new_args, nargs + 1,
                                               kwnames ? &PyTuple_GET_ITEM(kwnames, 0) : NULL, nkwargs);

        CHECK_OBJECTS(new_args, totalargs + 1);

        new_args[0] = tmp;
    } else {
        /* Definitely having args at this point. */
        assert(stack != NULL);

        NUITKA_DYNAMIC_ARRAY_DECL(new_args, PyObject *, totalargs + 1);
        new_args[0] = method->m_object;
        memcpy(&new_args[1], stack, totalargs * sizeof(PyObject *));

        CHECK_OBJECTS(new_args, totalargs + 1);

        result = Nuitka_CallFunctionVectorcall(PyThreadState_GET(), method->m_function, new_args, nargs + 1,
                                               kwnames ? &PyTuple_GET_ITEM(kwnames, 0) : NULL, nkwargs);

        CHECK_OBJECTS(new_args, totalargs + 1);
    }

    return result;
}
#endif

static PyObject *Nuitka_Method_tp_call(struct Nuitka_MethodObject *method, PyObject *args, PyObject *kw) {
    Py_ssize_t arg_count = PyTuple_GET_SIZE(args);

    if (method->m_object == NULL) {
        if (unlikely(arg_count < 1)) {
            PyErr_Format(
                PyExc_TypeError,
                "unbound compiled_method %s%s must be called with %s instance as first argument (got nothing instead)",
                GET_CALLABLE_NAME((PyObject *)method->m_function), GET_CALLABLE_DESC((PyObject *)method->m_function),
                GET_CLASS_NAME(method->m_class));
            return NULL;
        } else {
            PyObject *self = PyTuple_GET_ITEM(args, 0);
            CHECK_OBJECT(self);

            int result = PyObject_IsInstance(self, method->m_class);

            if (unlikely(result < 0)) {
                return NULL;
            } else if (unlikely(result == 0)) {
                PyThreadState *tstate = PyThreadState_GET();

                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }
        }

        return Py_TYPE(method->m_function)->tp_call((PyObject *)method->m_function, args, kw);
    } else {
        PyThreadState *tstate = PyThreadState_GET();

        if (kw == NULL) {
            if (arg_count == 0) {
                return Nuitka_CallMethodFunctionNoArgs(tstate, method->m_function, method->m_object);
            } else {
                return Nuitka_CallMethodFunctionPosArgs(tstate, method->m_function, method->m_object,
                                                        &PyTuple_GET_ITEM(args, 0), arg_count);
            }
        } else {
            return Nuitka_CallMethodFunctionPosArgsKwArgs(tstate, method->m_function, method->m_object,
                                                          &PyTuple_GET_ITEM(args, 0), arg_count, kw);
        }
    }
}

static PyObject *Nuitka_Method_tp_descr_get(struct Nuitka_MethodObject *method, PyObject *object,
                                            PyObject *class_object) {
    // Don't rebind already bound methods.
    if (method->m_object != NULL) {
        Py_INCREF(method);
        return (PyObject *)method;
    }

    if (method->m_class != NULL && class_object != NULL) {
        // Quick subclass test, bound methods remain the same if the class is a sub class
        int result = PyObject_IsSubclass(class_object, method->m_class);

        if (unlikely(result < 0)) {
            return NULL;
        } else if (result == 0) {
            Py_INCREF(method);
            return (PyObject *)method;
        }
    }

    return Nuitka_Method_New(method->m_function, object, class_object);
}

static PyObject *Nuitka_Method_tp_getattro(struct Nuitka_MethodObject *method, PyObject *name) {
    PyObject *descr = Nuitka_TypeLookup(&Nuitka_Method_Type, name);

    if (descr != NULL) {
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr)) && (Py_TYPE(descr)->tp_descr_get != NULL)) {
            return Py_TYPE(descr)->tp_descr_get(descr, (PyObject *)method, (PyObject *)Py_TYPE(method));
        } else {
            Py_INCREF(descr);
            return descr;
        }
    }

    // Delegate all other attributes to the underlying function.
    // TODO: Could be a bit more direct here, and know this is generic lookup.
    return PyObject_GetAttr((PyObject *)method->m_function, name);
}

static long Nuitka_Method_tp_traverse(struct Nuitka_MethodObject *method, visitproc visit, void *arg) {
    Py_VISIT(method->m_function);
    Py_VISIT(method->m_object);
    Py_VISIT(method->m_class);

    return 0;
}

// tp_repr slot, decide how a function shall be output
static PyObject *Nuitka_Method_tp_repr(struct Nuitka_MethodObject *method) {
    if (method->m_object == NULL) {
#if PYTHON_VERSION < 0x300
        return PyString_FromFormat("<unbound compiled_method %s.%s>", GET_CLASS_NAME(method->m_class),
                                   Nuitka_String_AsString(method->m_function->m_name));
#else
        return PyUnicode_FromFormat("<compiled_function %s at %p>", Nuitka_String_AsString(method->m_function->m_name),
                                    method->m_function);
#endif
    } else {
        // Note: CPython uses repr of the object, although a comment despises
        // it, we do it for compatibility.
        PyObject *object_repr = PyObject_Repr(method->m_object);

        if (object_repr == NULL) {
            return NULL;
        }
#if PYTHON_VERSION < 0x300
        else if (!PyString_Check(object_repr)) {
            Py_DECREF(object_repr);
            return NULL;
        }
#else
        else if (!PyUnicode_Check(object_repr)) {
            Py_DECREF(object_repr);
            return NULL;
        }
#endif

#if PYTHON_VERSION < 0x350
        PyObject *result =
            Nuitka_String_FromFormat("<bound compiled_method %s.%s of %s>", GET_CLASS_NAME(method->m_class),
                                     Nuitka_String_AsString_Unchecked(method->m_function->m_name),
                                     Nuitka_String_AsString_Unchecked(object_repr));
#else
        PyObject *result =
            PyUnicode_FromFormat("<bound compiled_method %U of %U>", method->m_function->m_qualname, object_repr);
#endif

        Py_DECREF(object_repr);

        return result;
    }
}

#if PYTHON_VERSION < 0x300
static int Nuitka_Method_tp_compare(struct Nuitka_MethodObject *a, struct Nuitka_MethodObject *b) {
    if (a->m_function->m_counter < b->m_function->m_counter) {
        return -1;
    } else if (a->m_function->m_counter > b->m_function->m_counter) {
        return 1;
    } else if (a->m_object == b->m_object) {
        return 0;
    } else if (a->m_object == NULL) {
        return -1;
    } else if (b->m_object == NULL) {
        return 1;
    } else {
        return PyObject_Compare(a->m_object, b->m_object);
    }
}
#endif

static PyObject *Nuitka_Method_tp_richcompare(struct Nuitka_MethodObject *a, struct Nuitka_MethodObject *b, int op) {
    if (op != Py_EQ && op != Py_NE) {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    if (Nuitka_Method_Check((PyObject *)a) == false || Nuitka_Method_Check((PyObject *)b) == false) {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    bool b_res = a->m_function->m_counter == b->m_function->m_counter;

    // If the underlying function objects are the same, check the objects, which
    // may be NULL in case of unbound methods, which would be the same again.
    if (b_res) {
#if PYTHON_VERSION < 0x380
        if (a->m_object == NULL) {
            b_res = b->m_object == NULL;
        } else if (b->m_object == NULL) {
            b_res = false;
        } else {
            nuitka_bool nbool_res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(a->m_object, b->m_object);

            if (unlikely(nbool_res == NUITKA_BOOL_EXCEPTION)) {
                return NULL;
            }

            b_res = nbool_res == NUITKA_BOOL_TRUE;
        }
#else
        b_res = a->m_object == b->m_object;
#endif
    }

    PyObject *result;

    if (op == Py_EQ) {
        result = BOOL_FROM(b_res);
    } else {
        result = BOOL_FROM(!b_res);
    }

    Py_INCREF_IMMORTAL(result);
    return result;
}

static long Nuitka_Method_tp_hash(struct Nuitka_MethodObject *method) {
    // Just give the hash of the method function, that ought to be good enough.
    return method->m_function->m_counter;
}

// Freelist setup
#define MAX_METHOD_FREE_LIST_COUNT 100
static struct Nuitka_MethodObject *free_list_methods = NULL;
static int free_list_methods_count = 0;

static void Nuitka_Method_tp_dealloc(struct Nuitka_MethodObject *method) {
#ifndef __NUITKA_NO_ASSERT__
    // Save the current exception, if any, we must to not corrupt it.
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state1;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state1);
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state1);
#endif

    Nuitka_GC_UnTrack(method);

    if (method->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)method);
    }

    Py_XDECREF(method->m_object);
    Py_XDECREF(method->m_class);

    Py_DECREF((PyObject *)method->m_function);

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_methods, method, MAX_METHOD_FREE_LIST_COUNT);

#ifndef __NUITKA_NO_ASSERT__
    struct Nuitka_ExceptionPreservationItem saved_exception_state2;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state2);
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state2);

    ASSERT_SAME_EXCEPTION_STATE(&saved_exception_state1, &saved_exception_state2);
#endif
}

static PyObject *Nuitka_Method_tp_new(PyTypeObject *type, PyObject *args, PyObject *kw) {
    PyObject *func;
    PyObject *self;
    PyObject *class_object = NULL;

    if (!_PyArg_NoKeywords("compiled_method", kw)) {
        return NULL;
    }

    if (!PyArg_UnpackTuple(args, "compiled_method", 2, 3, &func, &self, &class_object)) {
        return NULL;
    }

    CHECK_OBJECT(func);

    if (!PyCallable_Check(func)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "first argument must be callable");
        return NULL;
    }

    if (self == Py_None) {
        self = NULL;
    }

    if (self == NULL && class_object == NULL) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "unbound methods must have non-NULL im_class");
        return NULL;
    }

    if (Nuitka_Method_Check(func)) {
        return Nuitka_Method_New(((struct Nuitka_MethodObject *)func)->m_function, self, class_object);
    }

    if (Nuitka_Function_Check(func) == false) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_NICE("Cannot create compiled_ method from type '%s'", func);
        return NULL;
    }

    return Nuitka_Method_New((struct Nuitka_FunctionObject *)func, self, class_object);
}

PyTypeObject Nuitka_Method_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_method",
    sizeof(struct Nuitka_MethodObject),
    0,
    (destructor)Nuitka_Method_tp_dealloc, // tp_dealloc
#if PYTHON_VERSION < 0x380 || defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_SLOT)
    0, // tp_print
#else
    offsetof(struct Nuitka_MethodObject, m_vectorcall), // tp_vectorcall_offset
#endif
    0, // tp_getattr
    0, // tp_setattr
#if PYTHON_VERSION < 0x300
    (cmpfunc)Nuitka_Method_tp_compare, // tp_compare
#else
    0,
#endif
    (reprfunc)Nuitka_Method_tp_repr,         // tp_repr
    0,                                       // tp_as_number
    0,                                       // tp_as_sequence
    0,                                       // tp_as_mapping
    (hashfunc)Nuitka_Method_tp_hash,         // tp_hash
    (ternaryfunc)Nuitka_Method_tp_call,      // tp_call
    0,                                       // tp_str
    (getattrofunc)Nuitka_Method_tp_getattro, // tp_getattro
    0,                                       // tp_setattro (PyObject_GenericSetAttr)
    0,                                       // tp_as_buffer
    Py_TPFLAGS_DEFAULT |                     // tp_flags
#if PYTHON_VERSION < 0x300
        Py_TPFLAGS_HAVE_WEAKREFS |
#endif
#if PYTHON_VERSION >= 0x380
        _Py_TPFLAGS_HAVE_VECTORCALL |
#endif
        Py_TPFLAGS_HAVE_GC,
    0,                                                // tp_doc
    (traverseproc)Nuitka_Method_tp_traverse,          // tp_traverse
    0,                                                // tp_clear
    (richcmpfunc)Nuitka_Method_tp_richcompare,        // tp_richcompare
    offsetof(struct Nuitka_MethodObject, m_weakrefs), // tp_weaklistoffset
    0,                                                // tp_iter
    0,                                                // tp_iternext
    Nuitka_Method_methods,                            // tp_methods
    Nuitka_Method_members,                            // tp_members
    Nuitka_Method_tp_getset,                          // tp_getset
    0,                                                // tp_base
    0,                                                // tp_dict
    (descrgetfunc)Nuitka_Method_tp_descr_get,         // tp_descr_get
    0,                                                // tp_descr_set
    0,                                                // tp_dictoffset
    0,                                                // tp_init
    0,                                                // tp_alloc
    Nuitka_Method_tp_new,                             // tp_new
    0,                                                // tp_free
    0,                                                // tp_is_gc
    0,                                                // tp_bases
    0,                                                // tp_mro
    0,                                                // tp_cache
    0,                                                // tp_subclasses
    0,                                                // tp_weaklist
    0,                                                // tp_del
    0                                                 // tp_version_tag
#if PYTHON_VERSION >= 0x300
    ,
    0 /* tp_finalizer */
#endif
};

void _initCompiledMethodType(void) {
    Nuitka_PyType_Ready(&Nuitka_Method_Type, &PyMethod_Type, false, true, false, false, false);
}

PyObject *Nuitka_Method_New(struct Nuitka_FunctionObject *function, PyObject *object, PyObject *class_object) {
    struct Nuitka_MethodObject *result;

    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    allocateFromFreeListFixed(free_list_methods, struct Nuitka_MethodObject, Nuitka_Method_Type);

    if (unlikely(result == NULL)) {
        PyErr_Format(PyExc_RuntimeError, "cannot create method %s", Nuitka_String_AsString(function->m_name));

        return NULL;
    }

    Py_INCREF(function);
    result->m_function = function;

    result->m_object = object;
    Py_XINCREF(object);
    result->m_class = class_object;
    Py_XINCREF(class_object);

    result->m_weakrefs = NULL;

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_SLOT)
    result->m_vectorcall = (vectorcallfunc)Nuitka_Method_tp_vectorcall;
#endif

    Nuitka_GC_Track(result);
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
