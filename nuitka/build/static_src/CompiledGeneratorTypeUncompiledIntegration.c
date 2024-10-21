//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** Uncompiled generator integration
 *
 * This is for use in compiled generator, coroutine, async types. The file in
 * included for compiled generator, and in part exports functions as necessary.
 *
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// spell-checker: ignore f_valuestack,f_stacktop,PYGEN,_Py_CODEUNIT,OPARG
// spell-checker: ignore localsplus,stacktop,f_funcobj,genexit
// spell-checker: ignore deopt,subscr,isinstance,getitem,noargs,aiter,anext
// spell-checker: ignore classderef,getattribute,precall,nondescriptor,pyfunc

#if PYTHON_VERSION >= 0x300
static PyObject *Nuitka_CallGeneratorThrowMethod(PyObject *throw_method,
                                                 struct Nuitka_ExceptionPreservationItem *exception_state);
#endif

#if PYTHON_VERSION >= 0x300
static PyBaseExceptionObject *Nuitka_BaseExceptionSingleArg_new(PyThreadState *tstate, PyTypeObject *type,
                                                                PyObject *arg) {
    PyBaseExceptionObject *result = (PyBaseExceptionObject *)type->tp_alloc(type, 0);

    result->dict = NULL;
    result->traceback = NULL;
    result->cause = NULL;
    result->context = NULL;
    result->suppress_context = 0;

    if (arg != NULL) {
        result->args = MAKE_TUPLE1(tstate, arg);
    } else {
        result->args = const_tuple_empty;
        Py_INCREF_IMMORTAL(result->args);
    }

    return result;
}

static PyObject *Nuitka_CreateStopIteration(PyThreadState *tstate, PyObject *value) {
    if (value == Py_None) {
        value = NULL;
    }

    PyStopIterationObject *result =
        (PyStopIterationObject *)Nuitka_BaseExceptionSingleArg_new(tstate, (PyTypeObject *)PyExc_StopIteration, value);

#if PYTHON_VERSION >= 0x3c0
    if (value == NULL) {
        // Immortal value.
        result->value = Py_None;
    } else {
        result->value = value;
        Py_INCREF(value);
    }
#else
    result->value = value;
    Py_XINCREF(value);
#endif

    return (PyObject *)result;
}

// This function takes no reference to value, and publishes a StopIteration
// exception with it.
static void Nuitka_SetStopIterationValue(PyThreadState *tstate, PyObject *value) {
    CHECK_OBJECT(value);

#if PYTHON_VERSION <= 0x352
    PyObject *stop_value = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, PyExc_StopIteration, value);

    if (unlikely(stop_value == NULL)) {
        return;
    }

    SET_CURRENT_EXCEPTION_TYPE0_VALUE1(tstate, PyExc_StopIteration, stop_value);
#elif PYTHON_VERSION < 0x3c0
    if (likely(!PyTuple_Check(value) && !PyExceptionInstance_Check(value))) {
        SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_StopIteration, value);
    } else {
        struct Nuitka_ExceptionPreservationItem exception_state = {Py_NewRef(PyExc_StopIteration),
                                                                   Nuitka_CreateStopIteration(tstate, value)};

        RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
    }
#else
    struct Nuitka_ExceptionPreservationItem exception_state = {Nuitka_CreateStopIteration(tstate, value)};

    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
#endif
}
#endif

static void SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(PyThreadState *tstate) {
#if PYTHON_VERSION < 0x3c0
    SET_CURRENT_EXCEPTION_TYPE0(tstate, PyExc_StopIteration);
#else
    struct Nuitka_ExceptionPreservationItem exception_state = {Nuitka_CreateStopIteration(tstate, NULL)};

    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
#endif
}

#if PYTHON_VERSION >= 0x360

#if PYTHON_VERSION >= 0x3c0
static PyObject *Nuitka_CreateStopAsyncIteration(PyThreadState *tstate) {
    return (PyObject *)Nuitka_BaseExceptionSingleArg_new(tstate, (PyTypeObject *)PyExc_StopAsyncIteration, NULL);
}
#endif

static void SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(PyThreadState *tstate) {
#if PYTHON_VERSION < 0x3c0
    SET_CURRENT_EXCEPTION_TYPE0(tstate, PyExc_StopAsyncIteration);
#else
    struct Nuitka_ExceptionPreservationItem exception_state = {Nuitka_CreateStopAsyncIteration(tstate)};

    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
#endif
}

#endif

#if PYTHON_VERSION >= 0x3c0
static PyObject *Nuitka_CreateGeneratorExit(PyThreadState *tstate) {
    return (PyObject *)Nuitka_BaseExceptionSingleArg_new(tstate, (PyTypeObject *)PyExc_GeneratorExit, NULL);
}
#endif

#if PYTHON_VERSION >= 0x300
static void SET_CURRENT_EXCEPTION_GENERATOR_EXIT(PyThreadState *tstate) {
#if PYTHON_VERSION < 0x3c0
    SET_CURRENT_EXCEPTION_TYPE0(tstate, PyExc_GeneratorExit);
#else
    struct Nuitka_ExceptionPreservationItem exception_state = {Nuitka_CreateGeneratorExit(tstate)};

    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
#endif
}
#endif

#if PYTHON_VERSION >= 0x300
static bool Nuitka_PyGen_FetchStopIterationValue(PyThreadState *tstate, PyObject **pvalue) {
#if PYTHON_VERSION < 0x3c0
    if (!HAS_ERROR_OCCURRED(tstate)) {
        *pvalue = Py_None;
        Py_INCREF_IMMORTAL(Py_None);

        return true;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, tstate->curexc_type, PyExc_StopIteration)) {
        PyObject *value = NULL;

        PyObject *exception_type, *exception_value;
        PyTracebackObject *exception_tb;

        FETCH_ERROR_OCCURRED(tstate, &exception_type, &exception_value, &exception_tb);

        if (exception_value) {
            // TODO: API call here should be eliminated.
            if (PyObject_TypeCheck(exception_value, (PyTypeObject *)exception_type)) {
                value = ((PyStopIterationObject *)exception_value)->value;
                Py_INCREF(value);
                Py_DECREF(exception_value);
            } else if (exception_type == PyExc_StopIteration && !PyTuple_Check(exception_value)) {
                value = exception_value;
            } else {
                NORMALIZE_EXCEPTION(tstate, &exception_type, &exception_value, &exception_tb);

                if (!PyObject_TypeCheck(exception_value, (PyTypeObject *)PyExc_StopIteration)) {
                    RESTORE_ERROR_OCCURRED(tstate, exception_type, exception_value, exception_tb);

                    return false;
                }

                value = ((PyStopIterationObject *)exception_value)->value;
                Py_INCREF(value);

                Py_DECREF(exception_value);
            }
        }

        Py_XDECREF(exception_type);
        Py_XDECREF(exception_tb);

        if (value == NULL) {
            value = Py_None;
            Py_INCREF(value);
        }

        *pvalue = value;

        return true;
    } else {
        return false;
    }
#else
    if (!HAS_ERROR_OCCURRED(tstate)) {
        *pvalue = Py_None;
        Py_INCREF_IMMORTAL(Py_None);

        return true;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, tstate->current_exception, PyExc_StopIteration)) {
        PyObject *value = NULL;

        PyObject *exc = tstate->current_exception;
        tstate->current_exception = NULL;

        value = Py_NewRef(((PyStopIterationObject *)exc)->value);
        Py_DECREF(exc);

        if (value == NULL) {
            value = Py_None;
        }

        *pvalue = value;

        return true;

    } else {
        return false;
    }
#endif
}
#endif

#if PYTHON_VERSION >= 0x370
static inline void Nuitka_PyGen_exc_state_clear(_PyErr_StackItem *exc_state) {
#if PYTHON_VERSION < 0x3b0
    PyObject *t = exc_state->exc_type;
#endif
    PyObject *v = exc_state->exc_value;
#if PYTHON_VERSION < 0x3b0
    PyObject *tb = exc_state->exc_traceback;
#endif

#if PYTHON_VERSION < 0x3b0
    exc_state->exc_type = NULL;
#endif
    exc_state->exc_value = NULL;
#if PYTHON_VERSION < 0x3b0
    exc_state->exc_traceback = NULL;
#endif

#if PYTHON_VERSION < 0x3b0
    Py_XDECREF(t);
#endif
    Py_XDECREF(v);
#if PYTHON_VERSION < 0x3b0
    Py_XDECREF(tb);
#endif
}
#endif

#if PYTHON_VERSION >= 0x300

#if PYTHON_VERSION < 0x3b0
static inline bool Nuitka_PyFrameHasCompleted(PyFrameObject *const frame) {
#if PYTHON_VERSION < 0x3a0
    return frame->f_stacktop == NULL;
#else
    return frame->f_state > FRAME_EXECUTING;
#endif
}
#endif

// This is for CPython iterator objects, the respective code is not exported as
// API, so we need to redo it. This is an re-implementation that closely follows
// what it does. It's unrelated to compiled generators, and used from coroutines
// and asyncgen to interact with them.
static PyObject *Nuitka_PyGen_Send(PyThreadState *tstate, PyGenObject *gen, PyObject *arg) {
#if PYTHON_VERSION >= 0x3a0
    PyObject *result;

    // TODO: Avoid API call for performance.
    PySendResult res = PyIter_Send((PyObject *)gen, arg, &result);

    switch (res) {
    case PYGEN_RETURN:
        if (result == NULL) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        } else {
            if (result != Py_None) {
                Nuitka_SetStopIterationValue(tstate, result);
            }

            Py_DECREF(result);
        }

        return NULL;
    case PYGEN_NEXT:
        return result;
    case PYGEN_ERROR:
        return NULL;
    default:
        NUITKA_CANNOT_GET_HERE("invalid PYGEN_ result");
    }
#else

    PyFrameObject *f = gen->gi_frame;

#if PYTHON_VERSION >= 0x3b0
    if (gen->gi_frame_state == FRAME_EXECUTING) {
#elif PYTHON_VERSION >= 0x3a0
    if (f != NULL && _PyFrame_IsExecuting(f)) {
#else
    if (unlikely(gen->gi_running)) {
#endif
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "generator already executing");
        return NULL;
    }

#if PYTHON_VERSION < 0x3b0
    if (f == NULL || Nuitka_PyFrameHasCompleted(f)) {
#else
    if (gen->gi_frame_state >= FRAME_COMPLETED) {
#endif
        // Set exception if called from send()
        if (arg != NULL) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        }

        return NULL;
    }

#if PYTHON_VERSION < 0x3a0
    if (f->f_lasti == -1) {
        if (unlikely(arg && arg != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                            "can't send non-None value to a just-started generator");

            return NULL;
        }
    } else {
        // Put arg on top of the value stack
        PyObject *tmp = arg ? arg : Py_None;

        Py_INCREF(tmp);
        *(f->f_stacktop++) = tmp;
    }
#else
    // CPython assertions, check them
    assert(_PyFrame_IsRunnable(f));
    assert(f->f_lasti >= 0 || ((unsigned char *)PyBytes_AS_STRING(f->f_code->co_code))[0] == 129);

    PyObject *gen_result = arg ? arg : Py_None;
    Py_INCREF(gen_result);
    gen->gi_frame->f_valuestack[gen->gi_frame->f_stackdepth] = gen_result;
    gen->gi_frame->f_stackdepth++;
#endif

    // Generators always return to their most recent caller, not necessarily
    // their creator.
    tstate = PyThreadState_GET();
    Py_XINCREF(tstate->frame);

    f->f_back = tstate->frame;

#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 1;
#endif
#if PYTHON_VERSION >= 0x370
    gen->gi_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = &gen->gi_exc_state;
#endif

#if PYTHON_VERSION < 0x390
    PyObject *result = PyEval_EvalFrameEx(f, 0);
#else
    PyObject *result = _PyEval_EvalFrame(tstate, f, 0);
#endif

#if PYTHON_VERSION >= 0x370
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;
#endif
#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 0;
#endif

    // Don't keep the reference to f_back any longer than necessary.  It
    // may keep a chain of frames alive or it could create a reference
    // cycle.
    Py_CLEAR(f->f_back);

    // If the generator just returned (as opposed to yielding), signal that the
    // generator is exhausted.
#if PYTHON_VERSION < 0x3a0
    if (result && f->f_stacktop == NULL) {
        if (result == Py_None) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        } else {
            PyObject *e = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, (PyObject *)PyExc_StopIteration, result);

            if (likely(e != NULL)) {
                SET_CURRENT_EXCEPTION_TYPE0_VALUE1(tstate, PyExc_StopIteration, e);
            }
        }

        Py_CLEAR(result);
    }

    if (result == NULL || f->f_stacktop == NULL) {
#if PYTHON_VERSION < 0x370
        // Generator is finished, remove exception from frame before releasing
        // it.
        PyObject *type = f->f_exc_type;
        PyObject *value = f->f_exc_value;
        PyObject *traceback = f->f_exc_traceback;
        f->f_exc_type = NULL;
        f->f_exc_value = NULL;
        f->f_exc_traceback = NULL;
        Py_XDECREF(type);
        Py_XDECREF(value);
        Py_XDECREF(traceback);
#else
        Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);
#endif

        // Now release frame.
#if PYTHON_VERSION >= 0x300
        gen->gi_frame->f_gen = NULL;
#endif
        gen->gi_frame = NULL;
        Py_DECREF(f);
    }
#else
    if (result) {
        if (!_PyFrameHasCompleted(f)) {
            return result;
        }
        assert(result == Py_None || !PyAsyncGen_CheckExact(gen));

        if (result == Py_None && !PyAsyncGen_CheckExact(gen)) {
            Py_DECREF_IMMORTAL(result);
            result = NULL;
        }
    } else {
        if (PyErr_ExceptionMatches(PyExc_StopIteration)) {
            const char *msg = "generator raised StopIteration";
            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            } else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        } else if (PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
            const char *msg = "async generator raised StopAsyncIteration";
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        }

        result = NULL;
    }

    Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);

    gen->gi_frame->f_gen = NULL;
    gen->gi_frame = NULL;

    Py_DECREF(f);

#endif

    return result;
#endif
}

#endif

// Not done for Python2, indicate usability for compiled generators, but it
// seems that mostly coroutines need it anyway, so the benefit would be only for
// performance and not by a lot.
#if PYTHON_VERSION >= 0x300
#define NUITKA_UNCOMPILED_THROW_INTEGRATION 1
#endif

#if NUITKA_UNCOMPILED_THROW_INTEGRATION

static bool _Nuitka_Generator_check_throw(PyThreadState *tstate,
                                          struct Nuitka_ExceptionPreservationItem *exception_state);

#if PYTHON_VERSION < 0x3b0
#include <opcode.h>
// Clashes with our helper names.
#undef CALL_FUNCTION
#endif

static PyObject *Nuitka_PyGen_gen_close(PyThreadState *tstate, PyGenObject *gen, PyObject *args);
static int Nuitka_PyGen_gen_close_iter(PyThreadState *tstate, PyObject *yf);

// Restarting with 3.11, because the structures and internal API have
// changed so much, makes no sense to keep it in one code. For older
// versions, the else branch is there.
#if PYTHON_VERSION >= 0x3b0

// Private opcode mapping, that we need too
const uint8_t Nuitka_PyOpcode_Deopt[256] = {
#if PYTHON_VERSION >= 0x3d0
    [BEFORE_ASYNC_WITH] = BEFORE_ASYNC_WITH,
    [BEFORE_WITH] = BEFORE_WITH,
    [BINARY_OP] = BINARY_OP,
    [BINARY_OP_ADD_FLOAT] = BINARY_OP,
    [BINARY_OP_ADD_INT] = BINARY_OP,
    [BINARY_OP_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_INPLACE_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_MULTIPLY_FLOAT] = BINARY_OP,
    [BINARY_OP_MULTIPLY_INT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_FLOAT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_INT] = BINARY_OP,
    [BINARY_SLICE] = BINARY_SLICE,
    [BINARY_SUBSCR] = BINARY_SUBSCR,
    [BINARY_SUBSCR_DICT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_GETITEM] = BINARY_SUBSCR,
    [BINARY_SUBSCR_LIST_INT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_STR_INT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_TUPLE_INT] = BINARY_SUBSCR,
    [BUILD_CONST_KEY_MAP] = BUILD_CONST_KEY_MAP,
    [BUILD_LIST] = BUILD_LIST,
    [BUILD_MAP] = BUILD_MAP,
    [BUILD_SET] = BUILD_SET,
    [BUILD_SLICE] = BUILD_SLICE,
    [BUILD_STRING] = BUILD_STRING,
    [BUILD_TUPLE] = BUILD_TUPLE,
    [CACHE] = CACHE,
    [CALL] = CALL,
    [CALL_ALLOC_AND_ENTER_INIT] = CALL,
    [CALL_BOUND_METHOD_EXACT_ARGS] = CALL,
    [CALL_BOUND_METHOD_GENERAL] = CALL,
    [CALL_BUILTIN_CLASS] = CALL,
    [CALL_BUILTIN_FAST] = CALL,
    [CALL_BUILTIN_FAST_WITH_KEYWORDS] = CALL,
    [CALL_BUILTIN_O] = CALL,
    [CALL_FUNCTION_EX] = CALL_FUNCTION_EX,
    [CALL_INTRINSIC_1] = CALL_INTRINSIC_1,
    [CALL_INTRINSIC_2] = CALL_INTRINSIC_2,
    [CALL_ISINSTANCE] = CALL,
    [CALL_KW] = CALL_KW,
    [CALL_LEN] = CALL,
    [CALL_LIST_APPEND] = CALL,
    [CALL_METHOD_DESCRIPTOR_FAST] = CALL,
    [CALL_METHOD_DESCRIPTOR_FAST_WITH_KEYWORDS] = CALL,
    [CALL_METHOD_DESCRIPTOR_NOARGS] = CALL,
    [CALL_METHOD_DESCRIPTOR_O] = CALL,
    [CALL_NON_PY_GENERAL] = CALL,
    [CALL_PY_EXACT_ARGS] = CALL,
    [CALL_PY_GENERAL] = CALL,
    [CALL_STR_1] = CALL,
    [CALL_TUPLE_1] = CALL,
    [CALL_TYPE_1] = CALL,
    [CHECK_EG_MATCH] = CHECK_EG_MATCH,
    [CHECK_EXC_MATCH] = CHECK_EXC_MATCH,
    [CLEANUP_THROW] = CLEANUP_THROW,
    [COMPARE_OP] = COMPARE_OP,
    [COMPARE_OP_FLOAT] = COMPARE_OP,
    [COMPARE_OP_INT] = COMPARE_OP,
    [COMPARE_OP_STR] = COMPARE_OP,
    [CONTAINS_OP] = CONTAINS_OP,
    [CONTAINS_OP_DICT] = CONTAINS_OP,
    [CONTAINS_OP_SET] = CONTAINS_OP,
    [CONVERT_VALUE] = CONVERT_VALUE,
    [COPY] = COPY,
    [COPY_FREE_VARS] = COPY_FREE_VARS,
    [DELETE_ATTR] = DELETE_ATTR,
    [DELETE_DEREF] = DELETE_DEREF,
    [DELETE_FAST] = DELETE_FAST,
    [DELETE_GLOBAL] = DELETE_GLOBAL,
    [DELETE_NAME] = DELETE_NAME,
    [DELETE_SUBSCR] = DELETE_SUBSCR,
    [DICT_MERGE] = DICT_MERGE,
    [DICT_UPDATE] = DICT_UPDATE,
    [END_ASYNC_FOR] = END_ASYNC_FOR,
    [END_FOR] = END_FOR,
    [END_SEND] = END_SEND,
    [ENTER_EXECUTOR] = ENTER_EXECUTOR,
    [EXIT_INIT_CHECK] = EXIT_INIT_CHECK,
    [EXTENDED_ARG] = EXTENDED_ARG,
    [FORMAT_SIMPLE] = FORMAT_SIMPLE,
    [FORMAT_WITH_SPEC] = FORMAT_WITH_SPEC,
    [FOR_ITER] = FOR_ITER,
    [FOR_ITER_GEN] = FOR_ITER,
    [FOR_ITER_LIST] = FOR_ITER,
    [FOR_ITER_RANGE] = FOR_ITER,
    [FOR_ITER_TUPLE] = FOR_ITER,
    [GET_AITER] = GET_AITER,
    [GET_ANEXT] = GET_ANEXT,
    [GET_AWAITABLE] = GET_AWAITABLE,
    [GET_ITER] = GET_ITER,
    [GET_LEN] = GET_LEN,
    [GET_YIELD_FROM_ITER] = GET_YIELD_FROM_ITER,
    [IMPORT_FROM] = IMPORT_FROM,
    [IMPORT_NAME] = IMPORT_NAME,
    [INSTRUMENTED_CALL] = INSTRUMENTED_CALL,
    [INSTRUMENTED_CALL_FUNCTION_EX] = INSTRUMENTED_CALL_FUNCTION_EX,
    [INSTRUMENTED_CALL_KW] = INSTRUMENTED_CALL_KW,
    [INSTRUMENTED_END_FOR] = INSTRUMENTED_END_FOR,
    [INSTRUMENTED_END_SEND] = INSTRUMENTED_END_SEND,
    [INSTRUMENTED_FOR_ITER] = INSTRUMENTED_FOR_ITER,
    [INSTRUMENTED_INSTRUCTION] = INSTRUMENTED_INSTRUCTION,
    [INSTRUMENTED_JUMP_BACKWARD] = INSTRUMENTED_JUMP_BACKWARD,
    [INSTRUMENTED_JUMP_FORWARD] = INSTRUMENTED_JUMP_FORWARD,
    [INSTRUMENTED_LINE] = INSTRUMENTED_LINE,
    [INSTRUMENTED_LOAD_SUPER_ATTR] = INSTRUMENTED_LOAD_SUPER_ATTR,
    [INSTRUMENTED_POP_JUMP_IF_FALSE] = INSTRUMENTED_POP_JUMP_IF_FALSE,
    [INSTRUMENTED_POP_JUMP_IF_NONE] = INSTRUMENTED_POP_JUMP_IF_NONE,
    [INSTRUMENTED_POP_JUMP_IF_NOT_NONE] = INSTRUMENTED_POP_JUMP_IF_NOT_NONE,
    [INSTRUMENTED_POP_JUMP_IF_TRUE] = INSTRUMENTED_POP_JUMP_IF_TRUE,
    [INSTRUMENTED_RESUME] = INSTRUMENTED_RESUME,
    [INSTRUMENTED_RETURN_CONST] = INSTRUMENTED_RETURN_CONST,
    [INSTRUMENTED_RETURN_VALUE] = INSTRUMENTED_RETURN_VALUE,
    [INSTRUMENTED_YIELD_VALUE] = INSTRUMENTED_YIELD_VALUE,
    [INTERPRETER_EXIT] = INTERPRETER_EXIT,
    [IS_OP] = IS_OP,
    [JUMP_BACKWARD] = JUMP_BACKWARD,
    [JUMP_BACKWARD_NO_INTERRUPT] = JUMP_BACKWARD_NO_INTERRUPT,
    [JUMP_FORWARD] = JUMP_FORWARD,
    [LIST_APPEND] = LIST_APPEND,
    [LIST_EXTEND] = LIST_EXTEND,
    [LOAD_ASSERTION_ERROR] = LOAD_ASSERTION_ERROR,
    [LOAD_ATTR] = LOAD_ATTR,
    [LOAD_ATTR_CLASS] = LOAD_ATTR,
    [LOAD_ATTR_GETATTRIBUTE_OVERRIDDEN] = LOAD_ATTR,
    [LOAD_ATTR_INSTANCE_VALUE] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_LAZY_DICT] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_NO_DICT] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_WITH_VALUES] = LOAD_ATTR,
    [LOAD_ATTR_MODULE] = LOAD_ATTR,
    [LOAD_ATTR_NONDESCRIPTOR_NO_DICT] = LOAD_ATTR,
    [LOAD_ATTR_NONDESCRIPTOR_WITH_VALUES] = LOAD_ATTR,
    [LOAD_ATTR_PROPERTY] = LOAD_ATTR,
    [LOAD_ATTR_SLOT] = LOAD_ATTR,
    [LOAD_ATTR_WITH_HINT] = LOAD_ATTR,
    [LOAD_BUILD_CLASS] = LOAD_BUILD_CLASS,
    [LOAD_CONST] = LOAD_CONST,
    [LOAD_DEREF] = LOAD_DEREF,
    [LOAD_FAST] = LOAD_FAST,
    [LOAD_FAST_AND_CLEAR] = LOAD_FAST_AND_CLEAR,
    [LOAD_FAST_CHECK] = LOAD_FAST_CHECK,
    [LOAD_FAST_LOAD_FAST] = LOAD_FAST_LOAD_FAST,
    [LOAD_FROM_DICT_OR_DEREF] = LOAD_FROM_DICT_OR_DEREF,
    [LOAD_FROM_DICT_OR_GLOBALS] = LOAD_FROM_DICT_OR_GLOBALS,
    [LOAD_GLOBAL] = LOAD_GLOBAL,
    [LOAD_GLOBAL_BUILTIN] = LOAD_GLOBAL,
    [LOAD_GLOBAL_MODULE] = LOAD_GLOBAL,
    [LOAD_LOCALS] = LOAD_LOCALS,
    [LOAD_NAME] = LOAD_NAME,
    [LOAD_SUPER_ATTR] = LOAD_SUPER_ATTR,
    [LOAD_SUPER_ATTR_ATTR] = LOAD_SUPER_ATTR,
    [LOAD_SUPER_ATTR_METHOD] = LOAD_SUPER_ATTR,
    [MAKE_CELL] = MAKE_CELL,
    [MAKE_FUNCTION] = MAKE_FUNCTION,
    [MAP_ADD] = MAP_ADD,
    [MATCH_CLASS] = MATCH_CLASS,
    [MATCH_KEYS] = MATCH_KEYS,
    [MATCH_MAPPING] = MATCH_MAPPING,
    [MATCH_SEQUENCE] = MATCH_SEQUENCE,
    [NOP] = NOP,
    [POP_EXCEPT] = POP_EXCEPT,
    [POP_JUMP_IF_FALSE] = POP_JUMP_IF_FALSE,
    [POP_JUMP_IF_NONE] = POP_JUMP_IF_NONE,
    [POP_JUMP_IF_NOT_NONE] = POP_JUMP_IF_NOT_NONE,
    [POP_JUMP_IF_TRUE] = POP_JUMP_IF_TRUE,
    [POP_TOP] = POP_TOP,
    [PUSH_EXC_INFO] = PUSH_EXC_INFO,
    [PUSH_NULL] = PUSH_NULL,
    [RAISE_VARARGS] = RAISE_VARARGS,
    [RERAISE] = RERAISE,
    [RESERVED] = RESERVED,
    [RESUME] = RESUME,
    [RESUME_CHECK] = RESUME,
    [RETURN_CONST] = RETURN_CONST,
    [RETURN_GENERATOR] = RETURN_GENERATOR,
    [RETURN_VALUE] = RETURN_VALUE,
    [SEND] = SEND,
    [SEND_GEN] = SEND,
    [SETUP_ANNOTATIONS] = SETUP_ANNOTATIONS,
    [SET_ADD] = SET_ADD,
    [SET_FUNCTION_ATTRIBUTE] = SET_FUNCTION_ATTRIBUTE,
    [SET_UPDATE] = SET_UPDATE,
    [STORE_ATTR] = STORE_ATTR,
    [STORE_ATTR_INSTANCE_VALUE] = STORE_ATTR,
    [STORE_ATTR_SLOT] = STORE_ATTR,
    [STORE_ATTR_WITH_HINT] = STORE_ATTR,
    [STORE_DEREF] = STORE_DEREF,
    [STORE_FAST] = STORE_FAST,
    [STORE_FAST_LOAD_FAST] = STORE_FAST_LOAD_FAST,
    [STORE_FAST_STORE_FAST] = STORE_FAST_STORE_FAST,
    [STORE_GLOBAL] = STORE_GLOBAL,
    [STORE_NAME] = STORE_NAME,
    [STORE_SLICE] = STORE_SLICE,
    [STORE_SUBSCR] = STORE_SUBSCR,
    [STORE_SUBSCR_DICT] = STORE_SUBSCR,
    [STORE_SUBSCR_LIST_INT] = STORE_SUBSCR,
    [SWAP] = SWAP,
    [TO_BOOL] = TO_BOOL,
    [TO_BOOL_ALWAYS_TRUE] = TO_BOOL,
    [TO_BOOL_BOOL] = TO_BOOL,
    [TO_BOOL_INT] = TO_BOOL,
    [TO_BOOL_LIST] = TO_BOOL,
    [TO_BOOL_NONE] = TO_BOOL,
    [TO_BOOL_STR] = TO_BOOL,
    [UNARY_INVERT] = UNARY_INVERT,
    [UNARY_NEGATIVE] = UNARY_NEGATIVE,
    [UNARY_NOT] = UNARY_NOT,
    [UNPACK_EX] = UNPACK_EX,
    [UNPACK_SEQUENCE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_LIST] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TUPLE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TWO_TUPLE] = UNPACK_SEQUENCE,
    [WITH_EXCEPT_START] = WITH_EXCEPT_START,
    [YIELD_VALUE] = YIELD_VALUE,
#elif PYTHON_VERSION >= 0x3c0
    [BEFORE_ASYNC_WITH] = BEFORE_ASYNC_WITH,
    [BEFORE_WITH] = BEFORE_WITH,
    [BINARY_OP] = BINARY_OP,
    [BINARY_OP_ADD_FLOAT] = BINARY_OP,
    [BINARY_OP_ADD_INT] = BINARY_OP,
    [BINARY_OP_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_INPLACE_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_MULTIPLY_FLOAT] = BINARY_OP,
    [BINARY_OP_MULTIPLY_INT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_FLOAT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_INT] = BINARY_OP,
    [BINARY_SLICE] = BINARY_SLICE,
    [BINARY_SUBSCR] = BINARY_SUBSCR,
    [BINARY_SUBSCR_DICT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_GETITEM] = BINARY_SUBSCR,
    [BINARY_SUBSCR_LIST_INT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_TUPLE_INT] = BINARY_SUBSCR,
    [BUILD_CONST_KEY_MAP] = BUILD_CONST_KEY_MAP,
    [BUILD_LIST] = BUILD_LIST,
    [BUILD_MAP] = BUILD_MAP,
    [BUILD_SET] = BUILD_SET,
    [BUILD_SLICE] = BUILD_SLICE,
    [BUILD_STRING] = BUILD_STRING,
    [BUILD_TUPLE] = BUILD_TUPLE,
    [CACHE] = CACHE,
    [CALL] = CALL,
    [CALL_BOUND_METHOD_EXACT_ARGS] = CALL,
    [CALL_BUILTIN_CLASS] = CALL,
    [CALL_BUILTIN_FAST_WITH_KEYWORDS] = CALL,
    [CALL_FUNCTION_EX] = CALL_FUNCTION_EX,
    [CALL_INTRINSIC_1] = CALL_INTRINSIC_1,
    [CALL_INTRINSIC_2] = CALL_INTRINSIC_2,
    [CALL_METHOD_DESCRIPTOR_FAST_WITH_KEYWORDS] = CALL,
    [CALL_NO_KW_BUILTIN_FAST] = CALL,
    [CALL_NO_KW_BUILTIN_O] = CALL,
    [CALL_NO_KW_ISINSTANCE] = CALL,
    [CALL_NO_KW_LEN] = CALL,
    [CALL_NO_KW_LIST_APPEND] = CALL,
    [CALL_NO_KW_METHOD_DESCRIPTOR_FAST] = CALL,
    [CALL_NO_KW_METHOD_DESCRIPTOR_NOARGS] = CALL,
    [CALL_NO_KW_METHOD_DESCRIPTOR_O] = CALL,
    [CALL_NO_KW_STR_1] = CALL,
    [CALL_NO_KW_TUPLE_1] = CALL,
    [CALL_NO_KW_TYPE_1] = CALL,
    [CALL_PY_EXACT_ARGS] = CALL,
    [CALL_PY_WITH_DEFAULTS] = CALL,
    [CHECK_EG_MATCH] = CHECK_EG_MATCH,
    [CHECK_EXC_MATCH] = CHECK_EXC_MATCH,
    [CLEANUP_THROW] = CLEANUP_THROW,
    [COMPARE_OP] = COMPARE_OP,
    [COMPARE_OP_FLOAT] = COMPARE_OP,
    [COMPARE_OP_INT] = COMPARE_OP,
    [COMPARE_OP_STR] = COMPARE_OP,
    [CONTAINS_OP] = CONTAINS_OP,
    [COPY] = COPY,
    [COPY_FREE_VARS] = COPY_FREE_VARS,
    [DELETE_ATTR] = DELETE_ATTR,
    [DELETE_DEREF] = DELETE_DEREF,
    [DELETE_FAST] = DELETE_FAST,
    [DELETE_GLOBAL] = DELETE_GLOBAL,
    [DELETE_NAME] = DELETE_NAME,
    [DELETE_SUBSCR] = DELETE_SUBSCR,
    [DICT_MERGE] = DICT_MERGE,
    [DICT_UPDATE] = DICT_UPDATE,
    [END_ASYNC_FOR] = END_ASYNC_FOR,
    [END_FOR] = END_FOR,
    [END_SEND] = END_SEND,
    [EXTENDED_ARG] = EXTENDED_ARG,
    [FORMAT_VALUE] = FORMAT_VALUE,
    [FOR_ITER] = FOR_ITER,
    [FOR_ITER_GEN] = FOR_ITER,
    [FOR_ITER_LIST] = FOR_ITER,
    [FOR_ITER_RANGE] = FOR_ITER,
    [FOR_ITER_TUPLE] = FOR_ITER,
    [GET_AITER] = GET_AITER,
    [GET_ANEXT] = GET_ANEXT,
    [GET_AWAITABLE] = GET_AWAITABLE,
    [GET_ITER] = GET_ITER,
    [GET_LEN] = GET_LEN,
    [GET_YIELD_FROM_ITER] = GET_YIELD_FROM_ITER,
    [IMPORT_FROM] = IMPORT_FROM,
    [IMPORT_NAME] = IMPORT_NAME,
    [INSTRUMENTED_CALL] = INSTRUMENTED_CALL,
    [INSTRUMENTED_CALL_FUNCTION_EX] = INSTRUMENTED_CALL_FUNCTION_EX,
    [INSTRUMENTED_END_FOR] = INSTRUMENTED_END_FOR,
    [INSTRUMENTED_END_SEND] = INSTRUMENTED_END_SEND,
    [INSTRUMENTED_FOR_ITER] = INSTRUMENTED_FOR_ITER,
    [INSTRUMENTED_INSTRUCTION] = INSTRUMENTED_INSTRUCTION,
    [INSTRUMENTED_JUMP_BACKWARD] = INSTRUMENTED_JUMP_BACKWARD,
    [INSTRUMENTED_JUMP_FORWARD] = INSTRUMENTED_JUMP_FORWARD,
    [INSTRUMENTED_LINE] = INSTRUMENTED_LINE,
    [INSTRUMENTED_LOAD_SUPER_ATTR] = INSTRUMENTED_LOAD_SUPER_ATTR,
    [INSTRUMENTED_POP_JUMP_IF_FALSE] = INSTRUMENTED_POP_JUMP_IF_FALSE,
    [INSTRUMENTED_POP_JUMP_IF_NONE] = INSTRUMENTED_POP_JUMP_IF_NONE,
    [INSTRUMENTED_POP_JUMP_IF_NOT_NONE] = INSTRUMENTED_POP_JUMP_IF_NOT_NONE,
    [INSTRUMENTED_POP_JUMP_IF_TRUE] = INSTRUMENTED_POP_JUMP_IF_TRUE,
    [INSTRUMENTED_RESUME] = INSTRUMENTED_RESUME,
    [INSTRUMENTED_RETURN_CONST] = INSTRUMENTED_RETURN_CONST,
    [INSTRUMENTED_RETURN_VALUE] = INSTRUMENTED_RETURN_VALUE,
    [INSTRUMENTED_YIELD_VALUE] = INSTRUMENTED_YIELD_VALUE,
    [INTERPRETER_EXIT] = INTERPRETER_EXIT,
    [IS_OP] = IS_OP,
    [JUMP_BACKWARD] = JUMP_BACKWARD,
    [JUMP_BACKWARD_NO_INTERRUPT] = JUMP_BACKWARD_NO_INTERRUPT,
    [JUMP_FORWARD] = JUMP_FORWARD,
    [KW_NAMES] = KW_NAMES,
    [LIST_APPEND] = LIST_APPEND,
    [LIST_EXTEND] = LIST_EXTEND,
    [LOAD_ASSERTION_ERROR] = LOAD_ASSERTION_ERROR,
    [LOAD_ATTR] = LOAD_ATTR,
    [LOAD_ATTR_CLASS] = LOAD_ATTR,
    [LOAD_ATTR_GETATTRIBUTE_OVERRIDDEN] = LOAD_ATTR,
    [LOAD_ATTR_INSTANCE_VALUE] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_LAZY_DICT] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_NO_DICT] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_WITH_VALUES] = LOAD_ATTR,
    [LOAD_ATTR_MODULE] = LOAD_ATTR,
    [LOAD_ATTR_PROPERTY] = LOAD_ATTR,
    [LOAD_ATTR_SLOT] = LOAD_ATTR,
    [LOAD_ATTR_WITH_HINT] = LOAD_ATTR,
    [LOAD_BUILD_CLASS] = LOAD_BUILD_CLASS,
    [LOAD_CLOSURE] = LOAD_CLOSURE,
    [LOAD_CONST] = LOAD_CONST,
    [LOAD_CONST__LOAD_FAST] = LOAD_CONST,
    [LOAD_DEREF] = LOAD_DEREF,
    [LOAD_FAST] = LOAD_FAST,
    [LOAD_FAST_AND_CLEAR] = LOAD_FAST_AND_CLEAR,
    [LOAD_FAST_CHECK] = LOAD_FAST_CHECK,
    [LOAD_FAST__LOAD_CONST] = LOAD_FAST,
    [LOAD_FAST__LOAD_FAST] = LOAD_FAST,
    [LOAD_FROM_DICT_OR_DEREF] = LOAD_FROM_DICT_OR_DEREF,
    [LOAD_FROM_DICT_OR_GLOBALS] = LOAD_FROM_DICT_OR_GLOBALS,
    [LOAD_GLOBAL] = LOAD_GLOBAL,
    [LOAD_GLOBAL_BUILTIN] = LOAD_GLOBAL,
    [LOAD_GLOBAL_MODULE] = LOAD_GLOBAL,
    [LOAD_LOCALS] = LOAD_LOCALS,
    [LOAD_NAME] = LOAD_NAME,
    [LOAD_SUPER_ATTR] = LOAD_SUPER_ATTR,
    [LOAD_SUPER_ATTR_ATTR] = LOAD_SUPER_ATTR,
    [LOAD_SUPER_ATTR_METHOD] = LOAD_SUPER_ATTR,
    [MAKE_CELL] = MAKE_CELL,
    [MAKE_FUNCTION] = MAKE_FUNCTION,
    [MAP_ADD] = MAP_ADD,
    [MATCH_CLASS] = MATCH_CLASS,
    [MATCH_KEYS] = MATCH_KEYS,
    [MATCH_MAPPING] = MATCH_MAPPING,
    [MATCH_SEQUENCE] = MATCH_SEQUENCE,
    [NOP] = NOP,
    [POP_EXCEPT] = POP_EXCEPT,
    [POP_JUMP_IF_FALSE] = POP_JUMP_IF_FALSE,
    [POP_JUMP_IF_NONE] = POP_JUMP_IF_NONE,
    [POP_JUMP_IF_NOT_NONE] = POP_JUMP_IF_NOT_NONE,
    [POP_JUMP_IF_TRUE] = POP_JUMP_IF_TRUE,
    [POP_TOP] = POP_TOP,
    [PUSH_EXC_INFO] = PUSH_EXC_INFO,
    [PUSH_NULL] = PUSH_NULL,
    [RAISE_VARARGS] = RAISE_VARARGS,
    [RERAISE] = RERAISE,
    [RESERVED] = RESERVED,
    [RESUME] = RESUME,
    [RETURN_CONST] = RETURN_CONST,
    [RETURN_GENERATOR] = RETURN_GENERATOR,
    [RETURN_VALUE] = RETURN_VALUE,
    [SEND] = SEND,
    [SEND_GEN] = SEND,
    [SETUP_ANNOTATIONS] = SETUP_ANNOTATIONS,
    [SET_ADD] = SET_ADD,
    [SET_UPDATE] = SET_UPDATE,
    [STORE_ATTR] = STORE_ATTR,
    [STORE_ATTR_INSTANCE_VALUE] = STORE_ATTR,
    [STORE_ATTR_SLOT] = STORE_ATTR,
    [STORE_ATTR_WITH_HINT] = STORE_ATTR,
    [STORE_DEREF] = STORE_DEREF,
    [STORE_FAST] = STORE_FAST,
    [STORE_FAST__LOAD_FAST] = STORE_FAST,
    [STORE_FAST__STORE_FAST] = STORE_FAST,
    [STORE_GLOBAL] = STORE_GLOBAL,
    [STORE_NAME] = STORE_NAME,
    [STORE_SLICE] = STORE_SLICE,
    [STORE_SUBSCR] = STORE_SUBSCR,
    [STORE_SUBSCR_DICT] = STORE_SUBSCR,
    [STORE_SUBSCR_LIST_INT] = STORE_SUBSCR,
    [SWAP] = SWAP,
    [UNARY_INVERT] = UNARY_INVERT,
    [UNARY_NEGATIVE] = UNARY_NEGATIVE,
    [UNARY_NOT] = UNARY_NOT,
    [UNPACK_EX] = UNPACK_EX,
    [UNPACK_SEQUENCE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_LIST] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TUPLE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TWO_TUPLE] = UNPACK_SEQUENCE,
    [WITH_EXCEPT_START] = WITH_EXCEPT_START,
    [YIELD_VALUE] = YIELD_VALUE,
#else
    [ASYNC_GEN_WRAP] = ASYNC_GEN_WRAP,
    [BEFORE_ASYNC_WITH] = BEFORE_ASYNC_WITH,
    [BEFORE_WITH] = BEFORE_WITH,
    [BINARY_OP] = BINARY_OP,
    [BINARY_OP_ADAPTIVE] = BINARY_OP,
    [BINARY_OP_ADD_FLOAT] = BINARY_OP,
    [BINARY_OP_ADD_INT] = BINARY_OP,
    [BINARY_OP_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_INPLACE_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_MULTIPLY_FLOAT] = BINARY_OP,
    [BINARY_OP_MULTIPLY_INT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_FLOAT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_INT] = BINARY_OP,
    [BINARY_SUBSCR] = BINARY_SUBSCR,
    [BINARY_SUBSCR_ADAPTIVE] = BINARY_SUBSCR,
    [BINARY_SUBSCR_DICT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_GETITEM] = BINARY_SUBSCR,
    [BINARY_SUBSCR_LIST_INT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_TUPLE_INT] = BINARY_SUBSCR,
    [BUILD_CONST_KEY_MAP] = BUILD_CONST_KEY_MAP,
    [BUILD_LIST] = BUILD_LIST,
    [BUILD_MAP] = BUILD_MAP,
    [BUILD_SET] = BUILD_SET,
    [BUILD_SLICE] = BUILD_SLICE,
    [BUILD_STRING] = BUILD_STRING,
    [BUILD_TUPLE] = BUILD_TUPLE,
    [CACHE] = CACHE,
    [CALL] = CALL,
    [CALL_ADAPTIVE] = CALL,
    [CALL_FUNCTION_EX] = CALL_FUNCTION_EX,
    [CALL_PY_EXACT_ARGS] = CALL,
    [CALL_PY_WITH_DEFAULTS] = CALL,
    [CHECK_EG_MATCH] = CHECK_EG_MATCH,
    [CHECK_EXC_MATCH] = CHECK_EXC_MATCH,
    [COMPARE_OP] = COMPARE_OP,
    [COMPARE_OP_ADAPTIVE] = COMPARE_OP,
    [COMPARE_OP_FLOAT_JUMP] = COMPARE_OP,
    [COMPARE_OP_INT_JUMP] = COMPARE_OP,
    [COMPARE_OP_STR_JUMP] = COMPARE_OP,
    [CONTAINS_OP] = CONTAINS_OP,
    [COPY] = COPY,
    [COPY_FREE_VARS] = COPY_FREE_VARS,
    [DELETE_ATTR] = DELETE_ATTR,
    [DELETE_DEREF] = DELETE_DEREF,
    [DELETE_FAST] = DELETE_FAST,
    [DELETE_GLOBAL] = DELETE_GLOBAL,
    [DELETE_NAME] = DELETE_NAME,
    [DELETE_SUBSCR] = DELETE_SUBSCR,
    [DICT_MERGE] = DICT_MERGE,
    [DICT_UPDATE] = DICT_UPDATE,
    [END_ASYNC_FOR] = END_ASYNC_FOR,
    [EXTENDED_ARG] = EXTENDED_ARG,
    [EXTENDED_ARG_QUICK] = EXTENDED_ARG,
    [FORMAT_VALUE] = FORMAT_VALUE,
    [FOR_ITER] = FOR_ITER,
    [GET_AITER] = GET_AITER,
    [GET_ANEXT] = GET_ANEXT,
    [GET_AWAITABLE] = GET_AWAITABLE,
    [GET_ITER] = GET_ITER,
    [GET_LEN] = GET_LEN,
    [GET_YIELD_FROM_ITER] = GET_YIELD_FROM_ITER,
    [IMPORT_FROM] = IMPORT_FROM,
    [IMPORT_NAME] = IMPORT_NAME,
    [IMPORT_STAR] = IMPORT_STAR,
    [IS_OP] = IS_OP,
    [JUMP_BACKWARD] = JUMP_BACKWARD,
    [JUMP_BACKWARD_NO_INTERRUPT] = JUMP_BACKWARD_NO_INTERRUPT,
    [JUMP_BACKWARD_QUICK] = JUMP_BACKWARD,
    [JUMP_FORWARD] = JUMP_FORWARD,
    [JUMP_IF_FALSE_OR_POP] = JUMP_IF_FALSE_OR_POP,
    [JUMP_IF_TRUE_OR_POP] = JUMP_IF_TRUE_OR_POP,
    [KW_NAMES] = KW_NAMES,
    [LIST_APPEND] = LIST_APPEND,
    [LIST_EXTEND] = LIST_EXTEND,
    [LIST_TO_TUPLE] = LIST_TO_TUPLE,
    [LOAD_ASSERTION_ERROR] = LOAD_ASSERTION_ERROR,
    [LOAD_ATTR] = LOAD_ATTR,
    [LOAD_ATTR_ADAPTIVE] = LOAD_ATTR,
    [LOAD_ATTR_INSTANCE_VALUE] = LOAD_ATTR,
    [LOAD_ATTR_MODULE] = LOAD_ATTR,
    [LOAD_ATTR_SLOT] = LOAD_ATTR,
    [LOAD_ATTR_WITH_HINT] = LOAD_ATTR,
    [LOAD_BUILD_CLASS] = LOAD_BUILD_CLASS,
    [LOAD_CLASSDEREF] = LOAD_CLASSDEREF,
    [LOAD_CLOSURE] = LOAD_CLOSURE,
    [LOAD_CONST] = LOAD_CONST,
    [LOAD_CONST__LOAD_FAST] = LOAD_CONST,
    [LOAD_DEREF] = LOAD_DEREF,
    [LOAD_FAST] = LOAD_FAST,
    [LOAD_FAST__LOAD_CONST] = LOAD_FAST,
    [LOAD_FAST__LOAD_FAST] = LOAD_FAST,
    [LOAD_GLOBAL] = LOAD_GLOBAL,
    [LOAD_GLOBAL_ADAPTIVE] = LOAD_GLOBAL,
    [LOAD_GLOBAL_BUILTIN] = LOAD_GLOBAL,
    [LOAD_GLOBAL_MODULE] = LOAD_GLOBAL,
    [LOAD_METHOD] = LOAD_METHOD,
    [LOAD_METHOD_ADAPTIVE] = LOAD_METHOD,
    [LOAD_METHOD_CLASS] = LOAD_METHOD,
    [LOAD_METHOD_MODULE] = LOAD_METHOD,
    [LOAD_METHOD_NO_DICT] = LOAD_METHOD,
    [LOAD_METHOD_WITH_DICT] = LOAD_METHOD,
    [LOAD_METHOD_WITH_VALUES] = LOAD_METHOD,
    [LOAD_NAME] = LOAD_NAME,
    [MAKE_CELL] = MAKE_CELL,
    [MAKE_FUNCTION] = MAKE_FUNCTION,
    [MAP_ADD] = MAP_ADD,
    [MATCH_CLASS] = MATCH_CLASS,
    [MATCH_KEYS] = MATCH_KEYS,
    [MATCH_MAPPING] = MATCH_MAPPING,
    [MATCH_SEQUENCE] = MATCH_SEQUENCE,
    [NOP] = NOP,
    [POP_EXCEPT] = POP_EXCEPT,
    [POP_JUMP_BACKWARD_IF_FALSE] = POP_JUMP_BACKWARD_IF_FALSE,
    [POP_JUMP_BACKWARD_IF_NONE] = POP_JUMP_BACKWARD_IF_NONE,
    [POP_JUMP_BACKWARD_IF_NOT_NONE] = POP_JUMP_BACKWARD_IF_NOT_NONE,
    [POP_JUMP_BACKWARD_IF_TRUE] = POP_JUMP_BACKWARD_IF_TRUE,
    [POP_JUMP_FORWARD_IF_FALSE] = POP_JUMP_FORWARD_IF_FALSE,
    [POP_JUMP_FORWARD_IF_NONE] = POP_JUMP_FORWARD_IF_NONE,
    [POP_JUMP_FORWARD_IF_NOT_NONE] = POP_JUMP_FORWARD_IF_NOT_NONE,
    [POP_JUMP_FORWARD_IF_TRUE] = POP_JUMP_FORWARD_IF_TRUE,
    [POP_TOP] = POP_TOP,
    [PRECALL] = PRECALL,
    [PRECALL_ADAPTIVE] = PRECALL,
    [PRECALL_BOUND_METHOD] = PRECALL,
    [PRECALL_BUILTIN_CLASS] = PRECALL,
    [PRECALL_BUILTIN_FAST_WITH_KEYWORDS] = PRECALL,
    [PRECALL_METHOD_DESCRIPTOR_FAST_WITH_KEYWORDS] = PRECALL,
    [PRECALL_NO_KW_BUILTIN_FAST] = PRECALL,
    [PRECALL_NO_KW_BUILTIN_O] = PRECALL,
    [PRECALL_NO_KW_ISINSTANCE] = PRECALL,
    [PRECALL_NO_KW_LEN] = PRECALL,
    [PRECALL_NO_KW_LIST_APPEND] = PRECALL,
    [PRECALL_NO_KW_METHOD_DESCRIPTOR_FAST] = PRECALL,
    [PRECALL_NO_KW_METHOD_DESCRIPTOR_NOARGS] = PRECALL,
    [PRECALL_NO_KW_METHOD_DESCRIPTOR_O] = PRECALL,
    [PRECALL_NO_KW_STR_1] = PRECALL,
    [PRECALL_NO_KW_TUPLE_1] = PRECALL,
    [PRECALL_NO_KW_TYPE_1] = PRECALL,
    [PRECALL_PYFUNC] = PRECALL,
    [PREP_RERAISE_STAR] = PREP_RERAISE_STAR,
    [PRINT_EXPR] = PRINT_EXPR,
    [PUSH_EXC_INFO] = PUSH_EXC_INFO,
    [PUSH_NULL] = PUSH_NULL,
    [RAISE_VARARGS] = RAISE_VARARGS,
    [RERAISE] = RERAISE,
    [RESUME] = RESUME,
    [RESUME_QUICK] = RESUME,
    [RETURN_GENERATOR] = RETURN_GENERATOR,
    [RETURN_VALUE] = RETURN_VALUE,
    [SEND] = SEND,
    [SETUP_ANNOTATIONS] = SETUP_ANNOTATIONS,
    [SET_ADD] = SET_ADD,
    [SET_UPDATE] = SET_UPDATE,
    [STORE_ATTR] = STORE_ATTR,
    [STORE_ATTR_ADAPTIVE] = STORE_ATTR,
    [STORE_ATTR_INSTANCE_VALUE] = STORE_ATTR,
    [STORE_ATTR_SLOT] = STORE_ATTR,
    [STORE_ATTR_WITH_HINT] = STORE_ATTR,
    [STORE_DEREF] = STORE_DEREF,
    [STORE_FAST] = STORE_FAST,
    [STORE_FAST__LOAD_FAST] = STORE_FAST,
    [STORE_FAST__STORE_FAST] = STORE_FAST,
    [STORE_GLOBAL] = STORE_GLOBAL,
    [STORE_NAME] = STORE_NAME,
    [STORE_SUBSCR] = STORE_SUBSCR,
    [STORE_SUBSCR_ADAPTIVE] = STORE_SUBSCR,
    [STORE_SUBSCR_DICT] = STORE_SUBSCR,
    [STORE_SUBSCR_LIST_INT] = STORE_SUBSCR,
    [SWAP] = SWAP,
    [UNARY_INVERT] = UNARY_INVERT,
    [UNARY_NEGATIVE] = UNARY_NEGATIVE,
    [UNARY_NOT] = UNARY_NOT,
    [UNARY_POSITIVE] = UNARY_POSITIVE,
    [UNPACK_EX] = UNPACK_EX,
    [UNPACK_SEQUENCE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_ADAPTIVE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_LIST] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TUPLE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TWO_TUPLE] = UNPACK_SEQUENCE,
    [WITH_EXCEPT_START] = WITH_EXCEPT_START,
    [YIELD_VALUE] = YIELD_VALUE,
#endif
};

#if PYTHON_VERSION >= 0x3d0
static inline bool _Nuitka_is_resume(_Py_CODEUNIT *instr) {
    uint8_t code = FT_ATOMIC_LOAD_UINT8_RELAXED(instr->op.code);
    return (code == RESUME || code == RESUME_CHECK || code == INSTRUMENTED_RESUME);
}
#endif

PyObject *Nuitka_PyGen_yf(PyGenObject *gen) {
#if PYTHON_VERSION >= 0x3d0
    if (gen->gi_frame_state == FRAME_SUSPENDED_YIELD_FROM) {
        _PyInterpreterFrame *frame = (_PyInterpreterFrame *)gen->gi_iframe;
        assert(_Nuitka_is_resume(frame->instr_ptr));
        assert((frame->instr_ptr->op.arg & RESUME_OPARG_LOCATION_MASK) >= RESUME_AFTER_YIELD_FROM);
        return Py_NewRef(_PyFrame_StackPeek(frame));
    }
    return NULL;
#else
    PyObject *yf = NULL;

    if (gen->gi_frame_state < FRAME_CLEARED) {
        _PyInterpreterFrame *frame = (_PyInterpreterFrame *)gen->gi_iframe;

        if (gen->gi_frame_state == FRAME_CREATED) {
            return NULL;
        }

        _Py_CODEUNIT next = frame->prev_instr[1];

        if (Nuitka_PyOpcode_Deopt[_Py_OPCODE(next)] != RESUME || _Py_OPARG(next) < 2) {
            return NULL;
        }

        yf = _PyFrame_StackPeek(frame);

        Py_INCREF(yf);
    }

    return yf;
#endif
}

#if PYTHON_VERSION < 0x3c0
// Because it is not exported, we need to duplicate this.
static PyFrameObject *_Nuitka_PyFrame_New_NoTrack(PyCodeObject *code) {
    int slots = code->co_nlocalsplus + code->co_stacksize;

    PyFrameObject *f = PyObject_GC_NewVar(PyFrameObject, &PyFrame_Type, slots);

    if (f == NULL) {
        return NULL;
    }

    f->f_back = NULL;
    f->f_trace = NULL;
    f->f_trace_lines = 1;
    f->f_trace_opcodes = 0;
    f->f_fast_as_locals = 0;
    f->f_lineno = 0;

    return f;
}

// Also not exported.
static PyFrameObject *_Nuitka_PyFrame_MakeAndSetFrameObject(PyThreadState *tstate, _PyInterpreterFrame *frame) {
    assert(frame->frame_obj == NULL);

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    PyFrameObject *f = _Nuitka_PyFrame_New_NoTrack(frame->f_code);

    // Out of memory should be rare.
    assert(f != NULL);

    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    // Apparently there are situations where there is a race with what code creates the
    // frame, and this time it's not us.
    if (frame->frame_obj) {
        f->f_frame = (_PyInterpreterFrame *)f->_f_frame_data;
        f->f_frame->owner = FRAME_CLEARED;
        f->f_frame->frame_obj = f;
        Py_DECREF(f);

        return frame->frame_obj;
    }

    assert(frame->owner != FRAME_OWNED_BY_FRAME_OBJECT);
    assert(frame->owner != FRAME_CLEARED);

    f->f_frame = frame;
    frame->frame_obj = f;

    return f;
}

// The header variant uses un-exported code, replicate it with using our own variation.
static inline PyFrameObject *_Nuitka_PyFrame_GetFrameObject(PyThreadState *tstate, _PyInterpreterFrame *frame) {
    assert(!_PyFrame_IsIncomplete(frame));

    PyFrameObject *res = frame->frame_obj;

    if (res != NULL) {
        return res;
    }

    return _Nuitka_PyFrame_MakeAndSetFrameObject(tstate, frame);
}

// Also not exported, taking over a frame object.
static void _Nuitka_take_ownership(PyThreadState *tstate, PyFrameObject *f, _PyInterpreterFrame *frame) {
    assert(frame->owner != FRAME_OWNED_BY_FRAME_OBJECT);
    assert(frame->owner != FRAME_CLEARED);

    Py_ssize_t size = ((char *)&frame->localsplus[frame->stacktop]) - (char *)frame;
    memcpy((_PyInterpreterFrame *)f->_f_frame_data, frame, size);

    frame = (_PyInterpreterFrame *)f->_f_frame_data;
    f->f_frame = frame;
    frame->owner = FRAME_OWNED_BY_FRAME_OBJECT;

    assert(f->f_back == NULL);

    _PyInterpreterFrame *prev = frame->previous;
    while (prev && _PyFrame_IsIncomplete(prev)) {
        prev = prev->previous;
    }

    // Link the back frame, which may have to be created.
    if (prev) {
        // Link PyFrameObject "f_back" and remove link through "_PyInterpreterFrame".previous
        // TODO: Nuitka doesn't do that for compiled frames ever, is that really needed?
        PyFrameObject *back = _Nuitka_PyFrame_GetFrameObject(tstate, prev);

        if (unlikely(back == NULL)) {
            DROP_ERROR_OCCURRED(tstate);
        } else {
            f->f_back = (PyFrameObject *)Py_NewRef(back);
        }

        frame->previous = NULL;
    }

    if (!_PyObject_GC_IS_TRACKED((PyObject *)f)) {
        Nuitka_GC_Track((PyObject *)f);
    }
}

// Cleanup up the frame is also not exported.
static void _Nuitka_PyFrame_Clear(PyThreadState *tstate, _PyInterpreterFrame *frame) {
    assert(frame->owner != FRAME_OWNED_BY_GENERATOR || _PyFrame_GetGenerator(frame)->gi_frame_state == FRAME_CLEARED);

    if (frame->frame_obj) {
        PyFrameObject *f = frame->frame_obj;
        frame->frame_obj = NULL;

        if (Py_REFCNT(f) > 1) {
            _Nuitka_take_ownership(tstate, f, frame);
            Py_DECREF(f);

            return;
        }

        Py_DECREF(f);
    }

    assert(frame->stacktop >= 0);
    for (int i = 0; i < frame->stacktop; i++) {
        Py_XDECREF(frame->localsplus[i]);
    }

    Py_XDECREF(frame->frame_obj);
    Py_XDECREF(frame->f_locals);
#if PYTHON_VERSION < 0x3c0
    Py_DECREF(frame->f_func);
#else
    Py_DECREF(frame->f_funcobj);
#endif

#if PYTHON_VERSION < 0x3d0
    Py_XDECREF(frame->f_code);
#else
    Py_XDECREF(frame->f_executable);
#endif
}
#endif

// Needs to be similar to "gen_send_ex2" implementation in CPython. This is the low
// end of an uncompiled generator receiving a value.
static PySendResult Nuitka_PyGen_gen_send_ex2(PyThreadState *tstate, PyGenObject *gen, PyObject *arg,
                                              PyObject **result_ptr, int exc, int closing) {
    _PyInterpreterFrame *frame = (_PyInterpreterFrame *)gen->gi_iframe;
    PyObject *result;

    *result_ptr = NULL;

    if (gen->gi_frame_state == FRAME_CREATED && arg != NULL && arg != Py_None) {
        const char *msg = "can't send non-None value to a just-started generator";
        if (PyCoro_CheckExact(gen)) {
            msg = "can't send non-None value to a just-started coroutine";
        } else if (PyAsyncGen_CheckExact(gen)) {
            msg = "can't send non-None value to a just-started async generator";
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, msg);
        return PYGEN_ERROR;
    }

    if (gen->gi_frame_state == FRAME_EXECUTING) {
        const char *msg = "generator already executing";

        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine already executing";
        } else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator already executing";
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, msg);
        return PYGEN_ERROR;
    }

    if (gen->gi_frame_state >= FRAME_COMPLETED) {
        if (PyCoro_CheckExact(gen) && !closing) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cannot reuse already awaited coroutine");
        } else if (arg && !exc) {
            *result_ptr = Py_None;
            Py_INCREF_IMMORTAL(*result_ptr);
            return PYGEN_RETURN;
        }
        return PYGEN_ERROR;
    }

    assert(gen->gi_frame_state < FRAME_EXECUTING);

    // Put arg on the frame's stack
    result = arg ? arg : Py_None;
    Py_INCREF(result);
    _PyFrame_StackPush(frame, result);

#if PYTHON_VERSION < 0x3c0
    frame->previous = CURRENT_TSTATE_INTERPRETER_FRAME(tstate);
#endif

    _PyErr_StackItem *prev_exc_info = tstate->exc_info;
    gen->gi_exc_state.previous_item = prev_exc_info;

    tstate->exc_info = &gen->gi_exc_state;

    if (exc) {
        assert(_PyErr_Occurred(tstate));
#if PYTHON_VERSION >= 0x3d0
        {
            _PyErr_StackItem *exc_info = tstate->exc_info;

            if (exc_info->exc_value != NULL && exc_info->exc_value != Py_None) {
                PyObject *current_exception = tstate->current_exception;

                PyErr_SetObject((PyObject *)Py_TYPE(current_exception), current_exception);
                Py_DECREF(current_exception);
            }
        }
#else
        _PyErr_ChainStackItem(NULL);
#endif
    }

    gen->gi_frame_state = FRAME_EXECUTING;
    result = _PyEval_EvalFrame(tstate, frame, exc);
#if PYTHON_VERSION < 0x3c0
    if (gen->gi_frame_state == FRAME_EXECUTING) {
        gen->gi_frame_state = FRAME_COMPLETED;
    }
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;

    assert(CURRENT_TSTATE_INTERPRETER_FRAME(tstate) == frame->previous);
    frame->previous = NULL;
#else
    assert(tstate->exc_info == prev_exc_info);
    assert(gen->gi_exc_state.previous_item == NULL);
    assert(gen->gi_frame_state != FRAME_EXECUTING);
    assert(frame->previous == NULL);
#endif
    if (result != NULL) {
        if (gen->gi_frame_state == FRAME_SUSPENDED) {
            *result_ptr = result;
            return PYGEN_NEXT;
        }

        assert(result == Py_None || !PyAsyncGen_CheckExact(gen));

        if (result == Py_None && !PyAsyncGen_CheckExact(gen) && !arg) {
            // TODO: Have Py_CLEAR_IMMORTAL maybe

            Py_CLEAR(result);
        }
    } else {
#if PYTHON_VERSION < 0x3c0
        if (PyErr_ExceptionMatches(PyExc_StopIteration)) {
            const char *msg = "generator raised StopIteration";
            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            } else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        } else if (PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
            const char *msg = "async generator raised StopAsyncIteration";
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        }
#else
        assert(!PyErr_ExceptionMatches(PyExc_StopIteration));
        assert(!PyAsyncGen_CheckExact(gen) || !PyErr_ExceptionMatches(PyExc_StopAsyncIteration));

#endif
    }

    _PyErr_ClearExcState(&gen->gi_exc_state);

    gen->gi_frame_state = FRAME_CLEARED;

#if PYTHON_VERSION < 0x3c0
    _Nuitka_PyFrame_Clear(tstate, frame);
#endif

    *result_ptr = result;
    return result ? PYGEN_RETURN : PYGEN_ERROR;
}

static PyObject *Nuitka_PyGen_gen_send_ex(PyThreadState *tstate, PyGenObject *gen, PyObject *arg, int exc,
                                          int closing) {
    PyObject *result;

    if (Nuitka_PyGen_gen_send_ex2(tstate, gen, arg, &result, exc, closing) == PYGEN_RETURN) {
        if (PyAsyncGen_CheckExact(gen)) {
            assert(result == Py_None);
            SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
        } else if (result == Py_None) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        } else {
            Nuitka_SetStopIterationValue(tstate, result);
        }

        Py_DECREF(result);
        return NULL;
    }

    return result;
}

// This function is called when throwing to an uncompiled generator. Coroutines and generators
// do this in their yielding from.
// Note:
//   Exception arguments are passed for ownership and must be released before returning. The
//   value of exception_type will not be NULL, but the actual exception will not necessarily
//   be normalized.
static PyObject *Nuitka_UncompiledGenerator_throw(PyThreadState *tstate, PyGenObject *gen, int close_on_genexit,
                                                  struct Nuitka_ExceptionPreservationItem *exception_state) {
#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_UncompiledGenerator_throw: Enter ");
    PRINT_ITEM((PyObject *)gen);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_NEW_LINE();
#endif

    PyObject *yf = Nuitka_PyGen_yf(gen);

    if (yf != NULL) {
        _PyInterpreterFrame *frame = (_PyInterpreterFrame *)gen->gi_iframe;

        if (close_on_genexit && EXCEPTION_STATE_MATCH_BOOL_SINGLE(tstate, exception_state, PyExc_GeneratorExit)) {
            PyFrameState state = (PyFrameState)gen->gi_frame_state;
            gen->gi_frame_state = FRAME_EXECUTING;

            int err = Nuitka_PyGen_gen_close_iter(tstate, yf);

            gen->gi_frame_state = state;

            Py_DECREF(yf);

            if (err < 0) {
                // Releasing exception, we are done with it, raising instead the error just
                // occurred.
                RELEASE_ERROR_OCCURRED_STATE(exception_state);

                return Nuitka_PyGen_gen_send_ex(tstate, gen, Py_None, 1, 0);
            }

            // Handing exception ownership to this code.
            goto throw_here;
        }

        PyObject *ret;

        if (PyGen_CheckExact(yf) || PyCoro_CheckExact(yf)) {
            _PyInterpreterFrame *prev = CURRENT_TSTATE_INTERPRETER_FRAME(tstate);
            frame->previous = prev;
            CURRENT_TSTATE_INTERPRETER_FRAME(tstate) = frame;
            PyFrameState state = (PyFrameState)gen->gi_frame_state;
            gen->gi_frame_state = FRAME_EXECUTING;

            // Handing exception ownership to "Nuitka_UncompiledGenerator_throw".
            ret = Nuitka_UncompiledGenerator_throw(tstate, (PyGenObject *)yf, close_on_genexit, exception_state);
            gen->gi_frame_state = state;
            CURRENT_TSTATE_INTERPRETER_FRAME(tstate) = prev;
            frame->previous = NULL;
        } else {
#if 0
            // TODO: Add slow mode traces.
            PRINT_ITEM(yf);
            PRINT_NEW_LINE();
#endif

            PyObject *meth = LOOKUP_ATTRIBUTE(tstate, yf, const_str_plain_throw);

            if (unlikely(meth == NULL)) {
                Py_DECREF(yf);

                goto failed_throw;
            }

            if (meth == NULL) {
                Py_DECREF(yf);
                goto throw_here;
            }

            PyFrameState state = (PyFrameState)gen->gi_frame_state;
            gen->gi_frame_state = FRAME_EXECUTING;

            ret = Nuitka_CallGeneratorThrowMethod(meth, exception_state);

            gen->gi_frame_state = state;

            // Releasing exception, we are done with it.
            RELEASE_ERROR_OCCURRED_STATE(exception_state);

            Py_DECREF(meth);
        }
        Py_DECREF(yf);

        if (ret == NULL) {
#if PYTHON_VERSION < 0x3c0
            PyObject *val;
            assert(gen->gi_frame_state < FRAME_CLEARED);
            ret = _PyFrame_StackPop((_PyInterpreterFrame *)gen->gi_iframe);
            assert(ret == yf);
            Py_DECREF(ret);
            assert(_PyInterpreterFrame_LASTI(frame) >= 0);
            assert(_Py_OPCODE(frame->prev_instr[-1]) == SEND);
            int jump = _Py_OPARG(frame->prev_instr[-1]);
            frame->prev_instr += jump - 1;
            if (Nuitka_PyGen_FetchStopIterationValue(tstate, &val)) {
                ret = Nuitka_PyGen_gen_send_ex(tstate, gen, val, 0, 0);
                Py_DECREF(val);
            } else
#endif
            {
                ret = Nuitka_PyGen_gen_send_ex(tstate, gen, Py_None, 1, 0);
            }
        }

        return ret;
    }

throw_here:
    tstate = _PyThreadState_GET();

    if (unlikely(_Nuitka_Generator_check_throw(tstate, exception_state) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw already.
        return NULL;
    }

    RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

    return Nuitka_PyGen_gen_send_ex(tstate, gen, Py_None, 1, 1);

failed_throw:
    RELEASE_ERROR_OCCURRED_STATE(exception_state);

    return NULL;
}

#else

// For Python3.10 or earlier:

static PyObject *Nuitka_PyGen_yf(PyGenObject *gen) {
    PyFrameObject *f = gen->gi_frame;

#if PYTHON_VERSION < 0x3a0
    if (f && f->f_stacktop) {
#else
    if (f) {
#endif
        PyObject *bytecode = f->f_code->co_code;
        unsigned char *code = (unsigned char *)PyBytes_AS_STRING(bytecode);

        if (f->f_lasti < 0) {
            return NULL;
        }

#if PYTHON_VERSION < 0x360
        if (code[f->f_lasti + 1] != YIELD_FROM)
#elif PYTHON_VERSION < 0x3a0
        if (code[f->f_lasti + sizeof(_Py_CODEUNIT)] != YIELD_FROM)
#else
    if (code[(f->f_lasti + 1) * sizeof(_Py_CODEUNIT)] != YIELD_FROM)
#endif
        {
            return NULL;
        }

#if PYTHON_VERSION < 0x3a0
        PyObject *yf = f->f_stacktop[-1];
#else
        assert(f->f_stackdepth > 0);
        PyObject *yf = f->f_valuestack[f->f_stackdepth - 1];
#endif
        Py_INCREF(yf);
        return yf;
    } else {
        return NULL;
    }
}

static PyObject *Nuitka_PyGen_gen_send_ex(PyThreadState *tstate, PyGenObject *gen, PyObject *arg, int exc,
                                          int closing) {
    PyFrameObject *f = gen->gi_frame;
    PyObject *result;

#if PYTHON_VERSION >= 0x3a0
    if (f != NULL && unlikely(_PyFrame_IsExecuting(f))) {
#else
    if (unlikely(gen->gi_running)) {
#endif
        char const *msg = "generator already executing";

#if PYTHON_VERSION >= 0x350
        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine already executing";
        }
#if PYTHON_VERSION >= 0x360
        else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator already executing";
        }
#endif
#endif
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, msg);

        return NULL;
    }

    if (f == NULL || Nuitka_PyFrameHasCompleted(f)) {
#if PYTHON_VERSION >= 0x350
        if (PyCoro_CheckExact(gen) && !closing) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cannot reuse already awaited coroutine");
        } else
#endif
            if (arg && !exc) {
#if PYTHON_VERSION >= 0x360
            if (PyAsyncGen_CheckExact(gen)) {
                SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
            } else
#endif
            {
                SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
            }
        }
        return NULL;
    }

#if PYTHON_VERSION < 0x3a0
    if (f->f_lasti == -1) {
        if (unlikely(arg != NULL && arg != Py_None)) {
            char const *msg = "can't send non-None value to a just-started generator";

#if PYTHON_VERSION >= 0x350
            if (PyCoro_CheckExact(gen)) {
                msg = "can't send non-None value to a just-started coroutine";
            }
#if PYTHON_VERSION >= 0x360
            else if (PyAsyncGen_CheckExact(gen)) {
                msg = "can't send non-None value to a just-started async generator";
            }
#endif
#endif

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, msg);
            return NULL;
        }
    } else {
        // Put arg on the frame's stack
        result = arg ? arg : Py_None;
        Py_INCREF(result);
        *(f->f_stacktop++) = result;
    }
#else
    // CPython assertions, check them
    assert(_PyFrame_IsRunnable(f));
    assert(f->f_lasti >= 0 || ((unsigned char *)PyBytes_AS_STRING(f->f_code->co_code))[0] == GEN_START);

    result = arg ? arg : Py_None;
    Py_INCREF(result);
    gen->gi_frame->f_valuestack[gen->gi_frame->f_stackdepth] = result;
    gen->gi_frame->f_stackdepth++;
#endif

    Py_XINCREF(tstate->frame);
    f->f_back = tstate->frame;

#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 1;
#endif
#if PYTHON_VERSION >= 0x370
    gen->gi_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = &gen->gi_exc_state;
#endif
#if PYTHON_VERSION < 0x390
    result = PyEval_EvalFrameEx(f, exc);
#else
    result = _PyEval_EvalFrame(tstate, f, exc);
#endif
#if PYTHON_VERSION >= 0x370
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;
#endif
#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 0;
#endif

    Py_CLEAR(f->f_back);

#if PYTHON_VERSION < 0x3a0
    if (result && f->f_stacktop == NULL) {
        if (result == Py_None) {
#if PYTHON_VERSION >= 0x360
            if (PyAsyncGen_CheckExact(gen)) {
                SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
            } else
#endif
            {
                SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
            }
        } else {
            Nuitka_SetStopIterationValue(tstate, result);
        }

        // TODO: Add Py_CLEAR_IMMORTAL maybe
        Py_CLEAR(result);
    }
#if PYTHON_VERSION >= 0x350
    else if (result == NULL && PyErr_ExceptionMatches(PyExc_StopIteration)) {
#if PYTHON_VERSION < 0x370
        const int check_stop_iter_error_flags = CO_FUTURE_GENERATOR_STOP | CO_COROUTINE |
#if PYTHON_VERSION >= 0x360
                                                CO_ASYNC_GENERATOR |
#endif
                                                CO_ITERABLE_COROUTINE;

        if (unlikely(gen->gi_code != NULL && ((PyCodeObject *)gen->gi_code)->co_flags & check_stop_iter_error_flags))
#endif
        {
            char const *msg = "generator raised StopIteration";

            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            }
#if PYTHON_VERSION >= 0x360
            else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
#endif

#if PYTHON_VERSION >= 0x360
            _PyErr_FormatFromCause(
#else
            PyErr_Format(
#endif
                PyExc_RuntimeError, "%s", msg);
        }
    }
#endif
#if PYTHON_VERSION >= 0x360
    else if (result == NULL && PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
        char const *msg = "async generator raised StopAsyncIteration";
        _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
    }
#endif

    if (!result || f->f_stacktop == NULL) {
#if PYTHON_VERSION < 0x370
        PyObject *t, *v, *tb;
        t = f->f_exc_type;
        v = f->f_exc_value;
        tb = f->f_exc_traceback;
        f->f_exc_type = NULL;
        f->f_exc_value = NULL;
        f->f_exc_traceback = NULL;
        Py_XDECREF(t);
        Py_XDECREF(v);
        Py_XDECREF(tb);
#else
        Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);
#endif
        gen->gi_frame->f_gen = NULL;
        gen->gi_frame = NULL;
        Py_DECREF(f);
    }
#else
    if (result) {
        if (!_PyFrameHasCompleted(f)) {
            return result;
        }
        assert(result == Py_None || !PyAsyncGen_CheckExact(gen));
        if (result == Py_None && !PyAsyncGen_CheckExact(gen) && !arg) {
            // TODO: Add Py_CLEAR_IMMORTAL maybe
            Py_CLEAR(result);
        }
    } else {
        if (PyErr_ExceptionMatches(PyExc_StopIteration)) {
            const char *msg = "generator raised StopIteration";
            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            } else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        } else if (PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
            const char *msg = "async generator raised StopAsyncIteration";

            // TODO: Have our own variant of this.
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        }
    }

    Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);

    gen->gi_frame->f_gen = NULL;
    gen->gi_frame = NULL;

    Py_DECREF(f);
#endif
    return result;
}

// This function is called when throwing to an uncompiled generator. Coroutines and generators
// do this in their yielding from.
// Note:
//   Exception arguments are passed for ownership and must be released before returning. The
//   value of exception_type will not be NULL, but the actual exception will not necessarily
//   be normalized.
static PyObject *Nuitka_UncompiledGenerator_throw(PyThreadState *tstate, PyGenObject *gen, int close_on_genexit,
                                                  struct Nuitka_ExceptionPreservationItem *exception_state) {
#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_UncompiledGenerator_throw: Enter ");
    PRINT_ITEM((PyObject *)gen);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_NEW_LINE();
#endif

    PyObject *yf = Nuitka_PyGen_yf(gen);

    assert(HAS_EXCEPTION_STATE(exception_state));

    if (yf != NULL) {
        if (close_on_genexit &&
            EXCEPTION_MATCH_BOOL_SINGLE(tstate, exception_state->exception_type, PyExc_GeneratorExit)) {
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 1;
#else
            PyFrameState state = gen->gi_frame->f_state;
            gen->gi_frame->f_state = FRAME_EXECUTING;
#endif

            int err = Nuitka_PyGen_gen_close_iter(tstate, yf);
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif
            Py_DECREF(yf);

            if (err < 0) {
                // Releasing exception, we are done with it, raising instead the error just
                // occurred.
                RELEASE_ERROR_OCCURRED_STATE(exception_state);

                return Nuitka_PyGen_gen_send_ex(tstate, gen, Py_None, 1, 0);
            }

            // Handing exception ownership to this code.
            goto throw_here;
        }

        PyObject *ret;

        if (PyGen_CheckExact(yf)
#if PYTHON_VERSION >= 0x350
            || PyCoro_CheckExact(yf)
#endif
        ) {
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 1;
#else
            PyFrameState state = gen->gi_frame->f_state;
            gen->gi_frame->f_state = FRAME_EXECUTING;
#endif

            // Handing exception ownership to "Nuitka_UncompiledGenerator_throw".
            ret = Nuitka_UncompiledGenerator_throw(tstate, (PyGenObject *)yf, close_on_genexit, exception_state);

#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif
        } else {
#if 0
            // TODO: Add slow mode traces.
            PRINT_ITEM(yf);
            PRINT_NEW_LINE();
#endif

            // TODO: Use faster code here too.
            PyObject *meth = PyObject_GetAttr(yf, const_str_plain_throw);

            if (meth == NULL) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    Py_DECREF(yf);

                    // Releasing exception, we are done with it.
                    RELEASE_ERROR_OCCURRED_STATE(exception_state);

                    return NULL;
                }

                CLEAR_ERROR_OCCURRED(tstate);
                Py_DECREF(yf);

                // Handing exception ownership to this code.
                goto throw_here;
            }

#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 1;
#else
            PyFrameState state = gen->gi_frame->f_state;
            gen->gi_frame->f_state = FRAME_EXECUTING;
#endif
            // TODO: Faster call code should be used.
            ret = Nuitka_CallGeneratorThrowMethod(meth, exception_state);

#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif

            // Releasing exception, we are done with it.
            RELEASE_ERROR_OCCURRED_STATE(exception_state);

            Py_DECREF(meth);
        }

        Py_DECREF(yf);

        if (ret == NULL) {
#if PYTHON_VERSION < 0x3a0
            ret = *(--gen->gi_frame->f_stacktop);
#else
            assert(gen->gi_frame->f_stackdepth > 0);
            gen->gi_frame->f_stackdepth--;
            ret = gen->gi_frame->f_valuestack[gen->gi_frame->f_stackdepth];
#endif
            Py_DECREF(ret);

#if PYTHON_VERSION >= 0x360
            gen->gi_frame->f_lasti += sizeof(_Py_CODEUNIT);
#else
            gen->gi_frame->f_lasti += 1;
#endif

            if (Nuitka_PyGen_FetchStopIterationValue(tstate, &exception_state->exception_value)) {
                ret = Nuitka_PyGen_gen_send_ex(tstate, gen, exception_state->exception_value, 0, 0);

                Py_DECREF(exception_state->exception_value);
            } else {
                ret = Nuitka_PyGen_gen_send_ex(tstate, gen, Py_None, 1, 0);
            }
        }
        return ret;
    }

throw_here:
    // We continue to have exception ownership here.
    if (unlikely(_Nuitka_Generator_check_throw(tstate, exception_state) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw already.
        return NULL;
    }

    // Transfer exception ownership to published exception.
    RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

    return Nuitka_PyGen_gen_send_ex(tstate, gen, Py_None, 1, 1);
}

#endif

static int Nuitka_PyGen_gen_close_iter(PyThreadState *tstate, PyObject *yf) {
    PyObject *retval = NULL;

    if (PyGen_CheckExact(yf)
#if PYTHON_VERSION >= 0x350
        || PyCoro_CheckExact(yf)
#endif
    ) {
        assert(false);
        retval = Nuitka_PyGen_gen_close(tstate, (PyGenObject *)yf, NULL);

        if (retval == NULL) {
            return -1;
        }
    } else {
        PyObject *meth = PyObject_GetAttr(yf, const_str_plain_close);

        if (meth == NULL) {
            if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                PyErr_WriteUnraisable(yf);
            }

            CLEAR_ERROR_OCCURRED(tstate);
        } else {
            retval = CALL_FUNCTION_NO_ARGS(tstate, meth);

            Py_DECREF(meth);

            if (retval == NULL) {
                return -1;
            }
        }
    }

    Py_XDECREF(retval);
    return 0;
}

static PyObject *Nuitka_PyGen_gen_close(PyThreadState *tstate, PyGenObject *gen, PyObject *args) {
    PyObject *yf = Nuitka_PyGen_yf(gen);
    int err = 0;

    if (yf != NULL) {
#if PYTHON_VERSION >= 0x3b0
        PyFrameState state = (PyFrameState)gen->gi_frame_state;
        gen->gi_frame_state = FRAME_EXECUTING;
#elif PYTHON_VERSION >= 0x3a0
        PyFrameState state = gen->gi_frame->f_state;
        gen->gi_frame->f_state = FRAME_EXECUTING;
#else
        gen->gi_running = 1;
#endif
        err = Nuitka_PyGen_gen_close_iter(tstate, yf);

#if PYTHON_VERSION >= 0x3b0
        gen->gi_frame_state = state;
#elif PYTHON_VERSION >= 0x3a0
        gen->gi_frame->f_state = state;
#else
        gen->gi_running = 0;
#endif
        Py_DECREF(yf);
    }

    if (err == 0) {
        SET_CURRENT_EXCEPTION_GENERATOR_EXIT(tstate);
    }

    PyObject *retval = Nuitka_PyGen_gen_send_ex(tstate, gen, Py_None, 1, 1);

    if (retval != NULL) {
        char const *msg = "generator ignored GeneratorExit";

#if PYTHON_VERSION >= 0x350
        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine ignored GeneratorExit";
        }
#if PYTHON_VERSION >= 0x360
        else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator ignored GeneratorExit";
        }
#endif
#endif
        Py_DECREF(retval);

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, msg);
        return NULL;
    }

    if (PyErr_ExceptionMatches(PyExc_StopIteration) || PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
        CLEAR_ERROR_OCCURRED(tstate);

        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
    return NULL;
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
