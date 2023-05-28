//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
        // Fallback for uninitialized classes to API usage
        return PyType_IsSubtype(a, b) != 0;
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
// points for generic attributes.
void Nuitka_PyType_Ready(PyTypeObject *type, PyTypeObject *base, bool generic_get_attr, bool generic_set_attr,
                         bool self_iter, bool await_self_iter, bool self_aiter) {
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

    if (self_aiter) {
        assert(type->tp_as_async->am_aiter == NULL);
        type->tp_as_async->am_aiter = PyObject_SelfIter;
    }
#else
    assert(!await_self_iter);
    assert(!self_aiter);
#endif

    int res = PyType_Ready(type);
    assert(res >= 0);
}