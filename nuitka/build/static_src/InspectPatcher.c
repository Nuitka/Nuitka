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
/**
 * This is responsible for updating parts of CPython to better work with Nuitka
 * by replacing CPython implementations with enhanced versions.
 */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION >= 0x300
static PyObject *module_inspect;
#if PYTHON_VERSION >= 0x350
static PyObject *module_types;
#endif

static char *kw_list_object[] = {(char *)"object", NULL};

// spell-checker: ignore getgeneratorstate, getcoroutinestate

static PyObject *old_getgeneratorstate = NULL;

static PyObject *_inspect_getgeneratorstate_replacement(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *object;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:getgeneratorstate", kw_list_object, &object, NULL)) {
        return NULL;
    }

    if (Nuitka_Generator_Check(object)) {
        struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)object;

        if (generator->m_running) {
            return PyObject_GetAttrString(module_inspect, "GEN_RUNNING");
        } else if (generator->m_status == status_Finished) {
            return PyObject_GetAttrString(module_inspect, "GEN_CLOSED");
        } else if (generator->m_status == status_Unused) {
            return PyObject_GetAttrString(module_inspect, "GEN_CREATED");
        } else {
            return PyObject_GetAttrString(module_inspect, "GEN_SUSPENDED");
        }
    } else {
        return old_getgeneratorstate->ob_type->tp_call(old_getgeneratorstate, args, kwds);
    }
}

#if PYTHON_VERSION >= 0x350
static PyObject *old_getcoroutinestate = NULL;

static PyObject *_inspect_getcoroutinestate_replacement(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *object;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:getcoroutinestate", kw_list_object, &object, NULL)) {
        return NULL;
    }

    if (Nuitka_Coroutine_Check(object)) {
        struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)object;

        if (coroutine->m_running) {
            return PyObject_GetAttrString(module_inspect, "CORO_RUNNING");
        } else if (coroutine->m_status == status_Finished) {
            return PyObject_GetAttrString(module_inspect, "CORO_CLOSED");
        } else if (coroutine->m_status == status_Unused) {
            return PyObject_GetAttrString(module_inspect, "CORO_CREATED");
        } else {
            return PyObject_GetAttrString(module_inspect, "CORO_SUSPENDED");
        }
    } else {
        return old_getcoroutinestate->ob_type->tp_call(old_getcoroutinestate, args, kwds);
    }
}

static PyObject *old_types_coroutine = NULL;

static char *kw_list_coroutine[] = {(char *)"func", NULL};

static PyObject *_types_coroutine_replacement(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *func;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:coroutine", kw_list_coroutine, &func, NULL)) {
        return NULL;
    }

    if (Nuitka_Function_Check(func)) {
        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)func;

        if (function->m_code_object->co_flags & CO_GENERATOR) {
            function->m_code_object->co_flags |= 0x100;
        }
    }

    return old_types_coroutine->ob_type->tp_call(old_types_coroutine, args, kwds);
}

#endif

#endif

#if PYTHON_VERSION >= 0x300
static PyMethodDef _method_def_inspect_getgeneratorstate_replacement = {
    "getgeneratorstate", (PyCFunction)_inspect_getgeneratorstate_replacement, METH_VARARGS | METH_KEYWORDS, NULL};

#if PYTHON_VERSION >= 0x350
static PyMethodDef _method_def_inspect_getcoroutinestate_replacement = {
    "getcoroutinestate", (PyCFunction)_inspect_getcoroutinestate_replacement, METH_VARARGS | METH_KEYWORDS, NULL};

static PyMethodDef _method_def_types_coroutine_replacement = {"coroutine", (PyCFunction)_types_coroutine_replacement,
                                                              METH_VARARGS | METH_KEYWORDS, NULL};

#endif

/* Replace inspect functions with ones that handle compiles types too. */
void patchInspectModule(void) {
    static bool is_done = false;
    if (is_done)
        return;

#if PYTHON_VERSION >= 0x300
#if defined(_NUITKA_EXE) && !defined(_NUITKA_STANDALONE)
    // May need to import the "site" module, because otherwise the patching can
    // fail with it being unable to load it (yet)
    if (Py_NoSiteFlag == 0) {
        PyObject *site_module = IMPORT_MODULE5(const_str_plain_site, Py_None, Py_None, const_tuple_empty, const_int_0);

        if (site_module == NULL) {
            // Ignore "ImportError", having a "site" module is not a must.
            CLEAR_ERROR_OCCURRED();
        }
    }
#endif

    // TODO: Change this into an import hook that is executed after it is imported.
    module_inspect = IMPORT_MODULE5(const_str_plain_inspect, Py_None, Py_None, const_tuple_empty, const_int_0);

    if (module_inspect == NULL) {
        PyErr_PrintEx(0);
        Py_Exit(1);
    }
    CHECK_OBJECT(module_inspect);

    // Patch "inspect.getgeneratorstate" unless it is already patched.
    old_getgeneratorstate = PyObject_GetAttrString(module_inspect, "getgeneratorstate");
    CHECK_OBJECT(old_getgeneratorstate);

    if (PyFunction_Check(old_getgeneratorstate)) {
        PyObject *inspect_getgeneratorstate_replacement =
            PyCFunction_New(&_method_def_inspect_getgeneratorstate_replacement, NULL);
        CHECK_OBJECT(inspect_getgeneratorstate_replacement);

        PyObject_SetAttrString(module_inspect, "getgeneratorstate", inspect_getgeneratorstate_replacement);
    }

#if PYTHON_VERSION >= 0x350
    // Patch "inspect.getcoroutinestate" unless it is already patched.
    old_getcoroutinestate = PyObject_GetAttrString(module_inspect, "getcoroutinestate");
    CHECK_OBJECT(old_getcoroutinestate);

    if (PyFunction_Check(old_getcoroutinestate)) {
        PyObject *inspect_getcoroutinestate_replacement =
            PyCFunction_New(&_method_def_inspect_getcoroutinestate_replacement, NULL);
        CHECK_OBJECT(inspect_getcoroutinestate_replacement);

        PyObject_SetAttrString(module_inspect, "getcoroutinestate", inspect_getcoroutinestate_replacement);
    }

    module_types = IMPORT_MODULE5(const_str_plain_types, Py_None, Py_None, const_tuple_empty, const_int_0);

    if (module_types == NULL) {
        PyErr_PrintEx(0);
        Py_Exit(1);
    }
    CHECK_OBJECT(module_types);

    // Patch "types.coroutine" unless it is already patched.
    old_types_coroutine = PyObject_GetAttrString(module_types, "coroutine");
    CHECK_OBJECT(old_types_coroutine);

    if (PyFunction_Check(old_types_coroutine)) {
        PyObject *types_coroutine_replacement = PyCFunction_New(&_method_def_types_coroutine_replacement, NULL);
        CHECK_OBJECT(types_coroutine_replacement);

        PyObject_SetAttrString(module_types, "coroutine", types_coroutine_replacement);
    }

    static char const *wrapper_enhancement_code = "\n\
import types\n\
_old_GeneratorWrapper = types._GeneratorWrapper\n\
class GeneratorWrapperEnhanced(_old_GeneratorWrapper):\n\
    def __init__(self, gen):\n\
        _old_GeneratorWrapper.__init__(self, gen)\n\
\n\
        if hasattr(gen, 'gi_code'):\n\
            if gen.gi_code.co_flags & 0x0020:\n\
                self._GeneratorWrapper__isgen = True\n\
\n\
types._GeneratorWrapper = GeneratorWrapperEnhanced\
";

    PyObject *wrapper_enhancement_code_object = Py_CompileString(wrapper_enhancement_code, "<exec>", Py_file_input);
    CHECK_OBJECT(wrapper_enhancement_code_object);

    {
        PyObject *module = PyImport_ExecCodeModule("nuitka_types_patch", wrapper_enhancement_code_object);
        CHECK_OBJECT(module);

        bool bool_res = Nuitka_DelModuleString("nuitka_types_patch");
        assert(bool_res != false);

        Py_DECREF(module);
    }

#endif

#endif

    is_done = true;
}
#endif

static richcmpfunc original_PyType_tp_richcompare = NULL;

static PyObject *Nuitka_type_tp_richcompare(PyObject *a, PyObject *b, int op) {
    if (likely(op == Py_EQ || op == Py_NE)) {
        if (a == (PyObject *)&Nuitka_Function_Type) {
            a = (PyObject *)&PyFunction_Type;
        } else if (a == (PyObject *)&Nuitka_Method_Type) {
            a = (PyObject *)&PyMethod_Type;
        } else if (a == (PyObject *)&Nuitka_Generator_Type) {
            a = (PyObject *)&PyGen_Type;
#if PYTHON_VERSION >= 0x350
        } else if (a == (PyObject *)&Nuitka_Coroutine_Type) {
            a = (PyObject *)&PyCoro_Type;
#endif
#if PYTHON_VERSION >= 0x360
        } else if (a == (PyObject *)&Nuitka_Asyncgen_Type) {
            a = (PyObject *)&PyAsyncGen_Type;
#endif
        }

        if (b == (PyObject *)&Nuitka_Function_Type) {
            b = (PyObject *)&PyFunction_Type;
        } else if (b == (PyObject *)&Nuitka_Method_Type) {
            b = (PyObject *)&PyMethod_Type;
        } else if (b == (PyObject *)&Nuitka_Generator_Type) {
            b = (PyObject *)&PyGen_Type;
#if PYTHON_VERSION >= 0x350
        } else if (b == (PyObject *)&Nuitka_Coroutine_Type) {
            b = (PyObject *)&PyCoro_Type;
#endif
#if PYTHON_VERSION >= 0x360
        } else if (b == (PyObject *)&Nuitka_Asyncgen_Type) {
            b = (PyObject *)&PyAsyncGen_Type;
#endif
        }
    }

    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

    assert(original_PyType_tp_richcompare);

    return original_PyType_tp_richcompare(a, b, op);
}

void patchTypeComparison(void) {
    if (original_PyType_tp_richcompare == NULL) {
        original_PyType_tp_richcompare = PyType_Type.tp_richcompare;
        PyType_Type.tp_richcompare = Nuitka_type_tp_richcompare;
    }
}

#include "nuitka/freelists.h"

#define MAX_TRACEBACK_FREE_LIST_COUNT 1000
static PyTracebackObject *free_list_tracebacks = NULL;
static int free_list_tracebacks_count = 0;

// Create a traceback for a given frame, using a free list hacked into the
// existing type.
PyTracebackObject *MAKE_TRACEBACK(struct Nuitka_FrameObject *frame, int lineno) {
#if 0
    PRINT_STRING("MAKE_TRACEBACK: Enter");
    PRINT_ITEM((PyObject *)frame);
    PRINT_NEW_LINE();

    dumpFrameStack();
#endif

    CHECK_OBJECT(frame);
    assert(lineno != 0);

    PyTracebackObject *result;

    allocateFromFreeListFixed(free_list_tracebacks, PyTracebackObject, PyTraceBack_Type);

    result->tb_next = NULL;
    result->tb_frame = (PyFrameObject *)frame;
    Py_INCREF(frame);

    result->tb_lasti = 0;
    result->tb_lineno = lineno;

    Nuitka_GC_Track(result);

    return result;
}

static void Nuitka_tb_dealloc(PyTracebackObject *tb) {
    // Need to use official method as it checks for recursion.
    Nuitka_GC_UnTrack(tb);

#if 0
#if PYTHON_VERSION >= 0x380
    Py_TRASHCAN_BEGIN(tb, Nuitka_tb_dealloc);
#else
    Py_TRASHCAN_SAFE_BEGIN(tb);
#endif
#endif

    Py_XDECREF(tb->tb_next);
    Py_XDECREF(tb->tb_frame);

    releaseToFreeList(free_list_tracebacks, tb, MAX_TRACEBACK_FREE_LIST_COUNT);

#if 0
#if PYTHON_VERSION >= 0x380
    Py_TRASHCAN_END;
#else
    Py_TRASHCAN_SAFE_END(tb);
#endif
#endif
}

void patchTracebackDealloc(void) { PyTraceBack_Type.tp_dealloc = (destructor)Nuitka_tb_dealloc; }
