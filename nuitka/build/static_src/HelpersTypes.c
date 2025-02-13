//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Our replacement for "PyType_IsSubtype"
bool Nuitka_Type_IsSubtype(PyTypeObject *a, PyTypeObject *b) {
    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

#if PYTHON_VERSION < 0x300
    if (!(a->tp_flags & Py_TPFLAGS_HAVE_CLASS)) {
        return b == a || b == &PyBaseObject_Type;
    }
#endif

    PyObject *mro = a->tp_mro;
    CHECK_OBJECT_X(mro);

    if (likely(mro != NULL)) {
        assert(PyTuple_Check(mro));

        Py_ssize_t n = PyTuple_GET_SIZE(mro);

        for (Py_ssize_t i = 0; i < n; i++) {
            if (PyTuple_GET_ITEM(mro, i) == (PyObject *)b) {
                return true;
            }
        }

        return false;
    } else {
        // Fallback for uninitialized classes to base class scan
        do {
            if (a == b) {
                return true;
            }
            a = a->tp_base;
        } while (a != NULL);

        return (b == &PyBaseObject_Type);
    }
}

// TODO: We cannot really do this, until Nuitka_TypeLookup (_PyType_Lookup) is
// not also a call to an API, we just become wasteful here. What will make sense
// is to make specialized variants for not sub class checks, like
// PyExc_GeneratorExit and PyExc_StopIteration by caching the descriptor
// "checker" for them and then calling the "func" behind them more or less
// directly. These could be created during startup and be very fast to use.

#if 0
int Nuitka_Object_IsSubclass(PyThreadState *tstate, PyObject *derived, PyObject *cls)
{
    // TODO: Checking for a type is nothing the core does, could have a second variant
    if (PyType_CheckExact(cls)) {
        // Only a quick test for an exact match, but then give up.
        if (derived == cls) {
            return 1;
        }

        // Too hard for us.
        return PyObject_IsSubclass(derived, cls);
    }

    // TODO: Checking for a tuple is nothing the core does, could have a second variant
    if (PyTuple_Check(cls)) {
        if (Py_EnterRecursiveCall(" in __subclasscheck__")) {
            return -1;
        }

        Py_ssize_t n = PyTuple_GET_SIZE(cls);
        int r = 0;

        for (Py_ssize_t i = 0; i < n; ++i) {
            PyObject *item = PyTuple_GET_ITEM(cls, i);

            r = Nuitka_Object_IsSubclass(tstate, derived, item);

            if (r != 0) {
                break;
            }
        }

        Py_LeaveRecursiveCall();

        return r;
    }

    // TODO: For many of our uses, we know it.
    PyObject *checker = Nuitka_TypeLookup((PyTypeObject *)cls, const_str_plain___subclasscheck__);

    if (checker != NULL) {
        descrgetfunc f = Py_TYPE(checker)->tp_descr_get;

        if (f == NULL) {
            Py_INCREF(checker);
        } else {
            checker = f(checker, cls, (PyObject *)(Py_TYPE(cls)));
        }
    }

    if (checker != NULL) {
        int ok = -1;

        if (Py_EnterRecursiveCall(" in __subclasscheck__")) {
            Py_DECREF(checker);
            return ok;
        }

        PyObject *res = CALL_FUNCTION_WITH_SINGLE_ARG(checker, derived);

        Py_LeaveRecursiveCall();

        Py_DECREF(checker);

        if (res != NULL) {
            ok = CHECK_IF_TRUE(res);
            Py_DECREF(res);
        }
        return ok;
    } else if (HAS_ERROR_OCCURRED(tstate)) {
        return -1;
    }

    // Too hard for us.
    return PyObject_IsSubclass(derived, cls);
}
#endif

getattrofunc PyObject_GenericGetAttr_resolved;
setattrofunc PyObject_GenericSetAttr_resolved;

// Our wrapper for "PyType_Ready" that takes care of trying to avoid DLL entry
// points for generic attributes. spell-checker: ignore aiter
void Nuitka_PyType_Ready(PyTypeObject *type, PyTypeObject *base, bool generic_get_attr, bool generic_set_attr,
                         bool self_iter, bool await_self_iter, bool await_self_aiter) {
    assert(type->tp_base == NULL);

    PyObject_GenericGetAttr_resolved = PyBaseObject_Type.tp_getattro;
    PyObject_GenericSetAttr_resolved = PyBaseObject_Type.tp_setattro;

    type->tp_base = base;

    if (generic_get_attr) {
        assert(type->tp_getattro == NULL);
        type->tp_getattro = PyObject_GenericGetAttr_resolved;
    }

    if (generic_set_attr) {
        assert(type->tp_setattro == NULL);
        type->tp_setattro = PyObject_GenericSetAttr_resolved;
    }

    if (self_iter) {
        assert(type->tp_iter == NULL);
        type->tp_iter = PyObject_SelfIter;
    }

#if PYTHON_VERSION >= 0x350
    if (await_self_iter) {
        assert(type->tp_as_async->am_await == NULL);
        type->tp_as_async->am_await = PyObject_SelfIter;
    }

    if (await_self_aiter) {
        assert(type->tp_as_async->am_aiter == NULL);
        type->tp_as_async->am_aiter = PyObject_SelfIter;
    }
#else
    assert(!await_self_iter);
    assert(!await_self_aiter);
#endif

#if PYTHON_VERSION >= 0x3a0
    type->tp_flags |= Py_TPFLAGS_IMMUTABLETYPE;
#endif

    NUITKA_MAY_BE_UNUSED int res = PyType_Ready(type);
    assert(res >= 0);
}

#if PYTHON_VERSION >= 0x3c0

typedef struct {
    PyObject_HEAD PyObject *name;
    PyObject *type_params;
    PyObject *compute_value;
    PyObject *value;
    PyObject *module;
} typealiasobject;

static PyTypeObject *getTypeAliasType(void) {
    static PyTypeObject *type_alias_type = NULL;

    if (type_alias_type == NULL) {

        PyObject *typing_module = PyImport_ImportModule("_typing");
        CHECK_OBJECT(typing_module);

        type_alias_type = (PyTypeObject *)PyObject_GetAttrString(typing_module, "TypeAliasType");
        CHECK_OBJECT(type_alias_type);
    }

    return type_alias_type;
}

PyObject *MAKE_TYPE_ALIAS(PyObject *name, PyObject *type_params, PyObject *value, PyObject *module_name) {
    // TODO: For Python 3.13 we can use the intrinsic.

    typealiasobject *ta = Nuitka_GC_New(getTypeAliasType());

    // TODO: Lets follow Python new inline function in the future, this is 3.12
    // only code, so we can use it here.
    ta->name = Py_NewRef(name);
    ta->type_params = Py_IsNone(type_params) ? NULL : Py_XNewRef(type_params);
    ta->compute_value = NULL;
    ta->value = Py_XNewRef(value);
    ta->module = Py_NewRef(module_name);

    Nuitka_GC_Track(ta);

    return (PyObject *)ta;
}

typedef struct {
    PyObject_HEAD PyObject *name;
    PyObject *bound;
    PyObject *evaluate_bound;
    PyObject *constraints;
    PyObject *evaluate_constraints;
    bool covariant;
    bool contravariant;
    bool infer_variance;
} typevarobject;

static typevarobject *_Nuitka_typevar_alloc(PyThreadState *tstate, PyObject *name, PyObject *bound,
                                            PyObject *evaluate_bound, PyObject *constraints,
                                            PyObject *evaluate_constraints, bool covariant, bool contravariant,
                                            bool infer_variance, PyObject *module) {
    PyTypeObject *tp = tstate->interp->cached_objects.typevar_type;
    typevarobject *result = Nuitka_GC_New(tp);

    result->name = Py_NewRef(name);

    result->bound = Py_XNewRef(bound);
    result->evaluate_bound = Py_XNewRef(evaluate_bound);
    result->constraints = Py_XNewRef(constraints);
    result->evaluate_constraints = Py_XNewRef(evaluate_constraints);

    result->covariant = covariant;
    result->contravariant = contravariant;
    result->infer_variance = infer_variance;

    Nuitka_GC_Track(result);

    // TODO: Not seen yet.
    if (unlikely(module != NULL)) {
        if (PyObject_SetAttrString((PyObject *)result, "__module__", module) < 0) {
            Py_DECREF(result);
            return NULL;
        }
    }

    return result;
}

PyObject *MAKE_TYPE_VAR(PyThreadState *tstate, PyObject *name) {
    // TODO: For Python 3.13 this would work.
    // return _PyIntrinsics_UnaryFunctions[INTRINSIC_TYPEVAR].func(tstate, name);

    return (PyObject *)_Nuitka_typevar_alloc(tstate, name, NULL, NULL, NULL, NULL, false, false, true, NULL);
}

static PyTypeObject *_getTypeGenericAliasType(void) {
    static PyTypeObject *type_generic_alias_type = NULL;

    if (type_generic_alias_type == NULL) {

        PyObject *typing_module = PyImport_ImportModule("_typing");
        CHECK_OBJECT(typing_module);

        type_generic_alias_type = (PyTypeObject *)PyObject_GetAttrString(typing_module, "_GenericAlias");
        CHECK_OBJECT(type_generic_alias_type);
    }

    return type_generic_alias_type;
}

static PyObject *_Nuitka_unpack_typevartuples(PyObject *params) {
    assert(PyTuple_Check(params));

    // TODO: Not implemented yet.

    return Py_NewRef(params);
}

PyObject *MAKE_TYPE_GENERIC(PyThreadState *tstate, PyObject *params) {
    CHECK_OBJECT(params);
    PyObject *unpacked_params = _Nuitka_unpack_typevartuples(params);
    CHECK_OBJECT(unpacked_params);

    PyObject *args[2] = {(PyObject *)tstate->interp->cached_objects.generic_type, unpacked_params};

    PyObject *called = (PyObject *)_getTypeGenericAliasType();

    PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, called, args);
    Py_DECREF(unpacked_params);
    return result;
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
