//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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

// spell-checker: ignore getgeneratorstate,getcoroutinestate

static PyObject *old_getgeneratorstate = NULL;

static PyObject *_inspect_getgeneratorstate_replacement(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *object;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:getgeneratorstate", kw_list_object, &object, NULL)) {
        return NULL;
    }

    CHECK_OBJECT(object);

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
static PyObject *types_coroutine_wrapped = NULL;

static char *kw_list_coroutine[] = {(char *)"func", NULL};

static PyObject *_types_coroutine_replacement(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *func;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:coroutine", kw_list_coroutine, &func, NULL)) {
        return NULL;
    }

    if (Nuitka_Function_Check(func)) {
        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)func;

        // Check if "func" is a coroutine function, then return it unchanged.
        if (function->m_code_object->co_flags & 0x180) {
            return Py_NewRef(func);
        }

        // Check if "func" is a generator function, then make it an iterable
        // coroutine and return it unchanged.
        if (function->m_code_object->co_flags & CO_GENERATOR) {
            function->m_code_object->co_flags |= 0x100;

            return Py_NewRef(func);
        }
    }

    // Use a replacement that also handles compiled coroutine and generator
    // objects, which the original "types.coroutine" will not recognize.
    if (types_coroutine_wrapped != NULL) {
        return CALL_FUNCTION_WITH_SINGLE_ARG(PyThreadState_GET(), types_coroutine_wrapped, func);
    }

    return old_types_coroutine->ob_type->tp_call(old_types_coroutine, args, kwds);
}

#endif

#endif

#if PYTHON_VERSION >= 0x300
static PyMethodDef _method_def_inspect_getgeneratorstate_replacement = {
    "getgeneratorstate", CAST_METHOD_KW(_inspect_getgeneratorstate_replacement), METH_VARARGS | METH_KEYWORDS, NULL};

#if PYTHON_VERSION >= 0x350
static PyMethodDef _method_def_inspect_getcoroutinestate_replacement = {
    "getcoroutinestate", CAST_METHOD_KW(_inspect_getcoroutinestate_replacement), METH_VARARGS | METH_KEYWORDS, NULL};

static PyMethodDef _method_def_types_coroutine_replacement = {"coroutine", CAST_METHOD_KW(_types_coroutine_replacement),
                                                              METH_VARARGS | METH_KEYWORDS, NULL};

#endif

#if PYTHON_VERSION >= 0x3c0

static char *kw_list_depth[] = {(char *)"depth", NULL};

static bool Nuitka_FrameIsCompiled(_PyInterpreterFrame *frame) {
    return ((frame->frame_obj != NULL) && Nuitka_Frame_Check((PyObject *)frame->frame_obj));
}

static bool Nuitka_FrameIsIncomplete(_PyInterpreterFrame *frame) {
    bool r = _PyFrame_IsIncomplete(frame);

    return r;
}

static PyObject *orig_sys_getframemodulename = NULL;

static PyObject *_sys_getframemodulename_replacement(PyObject *self, PyObject *args, PyObject *kwds) {
    PyObject *depth_arg = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:_getframemodulename", kw_list_depth, &depth_arg)) {
        return NULL;
    }

    PyObject *index_value = Nuitka_Number_IndexAsLong(depth_arg ? depth_arg : const_int_0);

    if (unlikely(index_value == NULL)) {
        return NULL;
    }

    Py_ssize_t depth_ssize = PyLong_AsSsize_t(index_value);

    Py_DECREF(index_value);

    PyThreadState *tstate = _PyThreadState_GET();

    _PyInterpreterFrame *frame = CURRENT_TSTATE_INTERPRETER_FRAME(tstate);
    while ((frame != NULL) && ((Nuitka_FrameIsIncomplete(frame)) || depth_ssize-- > 0)) {
        frame = frame->previous;
    }

    if ((frame != NULL) && (Nuitka_FrameIsCompiled(frame))) {
        PyObject *result = PyDict_GetItemWithError(frame->f_globals, const_str_plain___name__);

        if (result == NULL) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                return NULL;
            }

            Py_RETURN_NONE;
        }

        Py_INCREF(result);
        return result;
    }

    return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, orig_sys_getframemodulename, depth_arg ? depth_arg : const_int_0);
}

// spell-checker: ignore getframemodulename
static PyMethodDef _method_def_sys_getframemodulename_replacement = {
    "_getframemodulename", CAST_METHOD_KW(_sys_getframemodulename_replacement), METH_VARARGS | METH_KEYWORDS, NULL};

// The "_typing" types derive the module of their user from the current frame
// function object, which compiled frames do not have, so we fill it in from
// the compiled frame ourselves.
#define MAX_TYPING_TYPES 4

static PyTypeObject *typing_types[MAX_TYPING_TYPES];
static newfunc typing_types_original_new[MAX_TYPING_TYPES];
static int typing_types_count = 0;

static PyObject *getCompiledCallerModuleName(PyThreadState *tstate) {
    _PyInterpreterFrame *frame = CURRENT_TSTATE_INTERPRETER_FRAME(tstate);

    while ((frame != NULL) && Nuitka_FrameIsIncomplete(frame)) {
        frame = frame->previous;
    }

    if ((frame != NULL) && Nuitka_FrameIsCompiled(frame)) {
        PyObject *result = PyDict_GetItemWithError(frame->f_globals, const_str_plain___name__);

        Py_XINCREF(result);

        return result;
    }

    return NULL;
}

static PyObject *Nuitka_typing_type_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    newfunc original_new = NULL;

    for (int i = 0; i < typing_types_count; i++) {
        if (typing_types[i] == type) {
            original_new = typing_types_original_new[i];
            break;
        }
    }

    assert(original_new != NULL);

    PyObject *result = original_new(type, args, kwds);

    if (result != NULL) {
        PyThreadState *tstate = PyThreadState_GET();

        PyObject *module_name = getCompiledCallerModuleName(tstate);

        if (module_name != NULL) {
            if (SET_ATTRIBUTE(tstate, result, const_str_plain___module__, module_name) == false) {
                CLEAR_ERROR_OCCURRED(tstate);
            }

            Py_DECREF(module_name);
        } else {
            CLEAR_ERROR_OCCURRED(tstate);
        }
    }

    return result;
}

static void patchTypingType(char const *attribute_name) {
    PyObject *typing_module = IMPORT_HARD_TYPING();

    PyObject *typing_type = PyObject_GetAttrString(typing_module, attribute_name);

    CHECK_OBJECT(typing_type);
    assert(PyType_Check(typing_type));
    assert(typing_types_count < MAX_TYPING_TYPES);

    PyTypeObject *type_object = (PyTypeObject *)typing_type;

    assert(type_object->tp_new != NULL);
    assert(type_object->tp_new != (newfunc)Nuitka_typing_type_new);

    typing_types[typing_types_count] = type_object;
    typing_types_original_new[typing_types_count] = type_object->tp_new;
    typing_types_count += 1;

    type_object->tp_new = (newfunc)Nuitka_typing_type_new;

    Py_DECREF(typing_type);
}

static void patchTypingModule(void) {
    patchTypingType("TypeVar");
    patchTypingType("ParamSpec");
    patchTypingType("TypeVarTuple");
}

#endif

/* Replace inspect functions with ones that handle compiles types too. */
void patchInspectModule(PyThreadState *tstate) {
    static bool is_done = false;
    if (is_done) {
        return;
    }

    CHECK_OBJECT(dict_builtin);

#if PYTHON_VERSION >= 0x300
#if _NUITKA_EXE_MODE && !_NUITKA_STANDALONE_MODE
    // May need to import the "site" module, because otherwise the patching can
    // fail with it being unable to load it (yet)
    if (Py_NoSiteFlag == 0) {
        PyObject *site_module =
            IMPORT_MODULE5(tstate, const_str_plain_site, Py_None, Py_None, const_tuple_empty, const_int_0);

        if (site_module == NULL) {
            // Ignore "ImportError", having a "site" module is not a must.
            CLEAR_ERROR_OCCURRED(tstate);
        }
    }
#endif

    // TODO: Change this into an import hook that is executed after it is imported.
    module_inspect = IMPORT_MODULE5(tstate, const_str_plain_inspect, Py_None, Py_None, const_tuple_empty, const_int_0);

    if (module_inspect == NULL) {
        PyErr_PrintEx(0);
        Py_Exit(1);
    }
    CHECK_OBJECT(module_inspect);

    // Patch "inspect.getgeneratorstate" unless it is already patched.
    old_getgeneratorstate = PyObject_GetAttrString(module_inspect, "getgeneratorstate");
    CHECK_OBJECT(old_getgeneratorstate);

    PyObject *inspect_getgeneratorstate_replacement =
        PyCFunction_New(&_method_def_inspect_getgeneratorstate_replacement, NULL);
    CHECK_OBJECT(inspect_getgeneratorstate_replacement);

    PyObject_SetAttrString(module_inspect, "getgeneratorstate", inspect_getgeneratorstate_replacement);

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

    module_types = IMPORT_MODULE5(tstate, const_str_plain_types, Py_None, Py_None, const_tuple_empty, const_int_0);

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
types._GeneratorWrapper = GeneratorWrapperEnhanced\n\
\n\
def _coroutine_wrapped(func):\n\
    import functools\n\
    import _collections_abc\n\
\n\
    @functools.wraps(func)\n\
    def wrapped(*args, **kwargs):\n\
        coro = func(*args, **kwargs)\n\
        if isinstance(coro, types.CoroutineType):\n\
            return coro\n\
        if isinstance(coro, types.GeneratorType):\n\
            if coro.gi_code.co_flags & 0x100:\n\
                return coro\n\
            return types._GeneratorWrapper(coro)\n\
        if (isinstance(coro, _collections_abc.Generator) and\n\
            not isinstance(coro, _collections_abc.Coroutine)):\n\
            return types._GeneratorWrapper(coro)\n\
        return coro\n\
\n\
    return wrapped\n\
\n\
def _types_coroutine(func):\n\
    if not callable(func):\n\
        raise TypeError('types.coroutine() expects a callable')\n\
\n\
    if type(func) is types.FunctionType:\n\
        co_flags = func.__code__.co_flags\n\
        if co_flags & 0x180:\n\
            return func\n\
        if co_flags & 0x20:\n\
            return _old_types_coroutine(func)\n\
\n\
    return _coroutine_wrapped(func)\n"
#if PYTHON_VERSION >= 0x3b0
                                                  "\
import inspect\n\
_old_get_code_position = inspect._get_code_position\n\
def _get_code_position(code, instruction_index):\n\
    try:\n\
        return _old_get_code_position(code, instruction_index)\n\
    except StopIteration:\n\
        return None, None, None, None\n\
inspect._get_code_position=_get_code_position\n\
"
#endif
        ;

    PyObject *wrapper_enhancement_code_object = Py_CompileString(wrapper_enhancement_code, "<exec>", Py_file_input);
    CHECK_OBJECT(wrapper_enhancement_code_object);

    {
        NUITKA_MAY_BE_UNUSED PyObject *module =
            PyImport_ExecCodeModule("nuitka_types_patch", wrapper_enhancement_code_object);
        CHECK_OBJECT(module);

#if PYTHON_VERSION >= 0x350
        types_coroutine_wrapped = PyObject_GetAttrString(module, "_types_coroutine");
        CHECK_OBJECT(types_coroutine_wrapped);

        NUITKA_MAY_BE_UNUSED int res = PyObject_SetAttrString(module, "_old_types_coroutine", old_types_coroutine);
        assert(res == 0);
#endif

        NUITKA_MAY_BE_UNUSED bool bool_res = Nuitka_DelModuleString(tstate, "nuitka_types_patch");
        assert(bool_res != false);
    }

#endif

#endif

#if PYTHON_VERSION >= 0x3c0
    orig_sys_getframemodulename = Nuitka_SysGetObject("_getframemodulename");

    PyObject *sys_getframemodulename_replacement =
        PyCFunction_New(&_method_def_sys_getframemodulename_replacement, NULL);
    CHECK_OBJECT(sys_getframemodulename_replacement);

    Nuitka_SysSetObject("_getframemodulename", sys_getframemodulename_replacement);

    patchTypingModule();
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

// Freelist setup
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
    if (lineno == 0) {
        lineno = frame->m_frame.f_lineno;
    }
    assert(lineno != 0);

    PyTracebackObject *result;

    allocateFromFreeListFixed(free_list_tracebacks, PyTracebackObject, PyTraceBack_Type);

    result->tb_next = NULL;
    result->tb_frame = (PyFrameObject *)frame;
    Py_INCREF(frame);

    result->tb_lasti = -1;
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
