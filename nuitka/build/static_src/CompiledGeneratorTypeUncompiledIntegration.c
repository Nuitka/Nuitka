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

#ifdef PY_NOGIL
#define Py_BUILD_CORE
#include "internal/pycore_generator.h"
#undef Py_BUILD_CORE
#endif

// This function takes no reference to value, and publishes a StopIteration
// exception with it.
#if PYTHON_VERSION >= 0x300
static void Nuitka_SetStopIterationValue(PyObject *value) {
    CHECK_OBJECT(value);

#if PYTHON_VERSION <= 0x352
    PyObject *stop_value = CALL_FUNCTION_WITH_SINGLE_ARG(PyExc_StopIteration, value);

    if (unlikely(stop_value == NULL)) {
        return;
    }

    Py_INCREF(PyExc_StopIteration);
    RESTORE_ERROR_OCCURRED(PyExc_StopIteration, stop_value, NULL);
#else
    if (likely(!PyTuple_Check(value) && !PyExceptionInstance_Check(value))) {
        Py_INCREF(PyExc_StopIteration);
        Py_INCREF(value);

        RESTORE_ERROR_OCCURRED(PyExc_StopIteration, value, NULL);
    } else {
        PyObject *stop_value = CALL_FUNCTION_WITH_SINGLE_ARG(PyExc_StopIteration, value);

        if (unlikely(stop_value == NULL)) {
            return;
        }

        Py_INCREF(PyExc_StopIteration);

        RESTORE_ERROR_OCCURRED(PyExc_StopIteration, stop_value, NULL);
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
static PyObject *Nuitka_PyGen_Send(PyGenObject *gen, PyObject *arg) {
#if defined(PY_NOGIL)
    PyObject *res;

    if (gen->status == GEN_CREATED) {
        if (unlikely(arg != Py_None)) {
            char const *msg = "generator raised StopIteration";
            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            } else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }

            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
            return NULL;
        }
        arg = NULL;
    }

    res = PyEval2_EvalGen(gen, arg);

    if (likely(res != NULL)) {
        assert(gen->status == GEN_SUSPENDED);
        return res;
    }

    if (likely(gen->return_value == Py_None)) {
        gen->return_value = NULL;
        SET_CURRENT_EXCEPTION_TYPE0(PyAsyncGen_CheckExact(gen) ? PyExc_StopAsyncIteration : PyExc_StopIteration);
        return NULL;
    } else if (gen->return_value != NULL) {
        Nuitka_SetStopIterationValue(gen->return_value);
        return NULL;
    } else {
        return gen_wrap_exception(gen);
    }
#elif PYTHON_VERSION >= 0x3a0
    PyObject *result;

    PySendResult res = PyIter_Send((PyObject *)gen, arg, &result);

    switch (res) {
    case PYGEN_RETURN:
        if (result == NULL) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        } else {
            if (result != Py_None) {
                Nuitka_SetStopIterationValue(result);
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
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "generator already executing");
        return NULL;
    }

#if PYTHON_VERSION < 0x3b0
    if (f == NULL || Nuitka_PyFrameHasCompleted(f)) {
#else
    if (gen->gi_frame_state >= FRAME_COMPLETED) {
#endif
        // Set exception if called from send()
        if (arg != NULL) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        }

        return NULL;
    }

#if PYTHON_VERSION < 0x3a0
    if (f->f_lasti == -1) {
        if (unlikely(arg && arg != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "can't send non-None value to a just-started generator");

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
    PyThreadState *tstate = PyThreadState_GET();
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
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        } else {
            PyObject *e = PyObject_CallFunctionObjArgs(PyExc_StopIteration, result, NULL);

            if (e != NULL) {
                SET_CURRENT_EXCEPTION_TYPE0_VALUE1(PyExc_StopIteration, e);
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
#if PYTHON_VERSION >= 0x340
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
            Py_DECREF(result);
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

// TODO: Disabled for NOGIL until it becomes more ready.
// Not done for earlier versions yet, indicate usability for compiled
// generators, but it seems that mostly coroutines need it anyway, so the
// benefit would be only for performance and not by a lot.
#if PYTHON_VERSION >= 0x340 && !defined(PY_NOGIL)
#define NUITKA_UNCOMPILED_THROW_INTEGRATION 1
#endif

#if NUITKA_UNCOMPILED_THROW_INTEGRATION

static bool _Nuitka_Generator_check_throw2(PyObject **exception_type, PyObject **exception_value,
                                           PyTracebackObject **exception_tb);

#if PYTHON_VERSION < 0x3B0
#include <opcode.h>
// Clashes with our helper names.
#undef CALL_FUNCTION
#endif

static PyObject *Nuitka_PyGen_gen_close(PyGenObject *gen, PyObject *args);
static int Nuitka_PyGen_gen_close_iter(PyObject *yf);

// Restarting with 3.11, because the structures and internal API have
// changed so much, makes no sense to keep it in one code. For older
// versions, the else branch is there.
#if PYTHON_VERSION >= 0x3b0

// Private opcode mapping, that we need too.
static const uint8_t Nuitka_PyOpcode_Deopt[256] = {
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
};

PyObject *Nuitka_PyGen_yf(PyGenObject *gen) {
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
}

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
static PyFrameObject *_Nuitka_PyFrame_MakeAndSetFrameObject(_PyInterpreterFrame *frame) {
    assert(frame->frame_obj == NULL);

    PyObject *error_type, *error_value;
    PyTracebackObject *error_traceback;

    FETCH_ERROR_OCCURRED(&error_type, &error_value, &error_traceback);

    PyFrameObject *f = _Nuitka_PyFrame_New_NoTrack(frame->f_code);

    // Out of memory should be rare.
    assert(f != NULL);

    RESTORE_ERROR_OCCURRED(error_type, error_value, error_traceback);

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
static inline PyFrameObject *_Nuitka_PyFrame_GetFrameObject(_PyInterpreterFrame *frame) {
    assert(!_PyFrame_IsIncomplete(frame));

    PyFrameObject *res = frame->frame_obj;

    if (res != NULL) {
        return res;
    }

    return _Nuitka_PyFrame_MakeAndSetFrameObject(frame);
}

// Also not exported, taking over a frame object.

static void _Nuitka_take_ownership(PyFrameObject *f, _PyInterpreterFrame *frame) {
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
        PyFrameObject *back = _Nuitka_PyFrame_GetFrameObject(prev);

        if (unlikely(back == NULL)) {
            DROP_ERROR_OCCURRED();
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
static void _Nuitka_PyFrame_Clear(_PyInterpreterFrame *frame) {
    assert(frame->owner != FRAME_OWNED_BY_GENERATOR || _PyFrame_GetGenerator(frame)->gi_frame_state == FRAME_CLEARED);

    if (frame->frame_obj) {
        PyFrameObject *f = frame->frame_obj;
        frame->frame_obj = NULL;

        if (Py_REFCNT(f) > 1) {
            _Nuitka_take_ownership(f, frame);
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
    Py_DECREF(frame->f_func);
    Py_DECREF(frame->f_code);
}

static PySendResult Nuitka_PyGen_gen_send_ex2(PyGenObject *gen, PyObject *arg, PyObject **presult, int exc,
                                              int closing) {
    PyThreadState *tstate = _PyThreadState_GET();
    _PyInterpreterFrame *frame = (_PyInterpreterFrame *)gen->gi_iframe;
    PyObject *result;

    *presult = NULL;

    if (gen->gi_frame_state == FRAME_CREATED && arg != NULL && arg != Py_None) {
        const char *msg = "can't send non-None value to a just-started generator";
        if (PyCoro_CheckExact(gen)) {
            msg = "can't send non-None value to a just-started coroutine";
        } else if (PyAsyncGen_CheckExact(gen)) {
            msg = "can't send non-None value to a just-started async generator";
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, msg);
        return PYGEN_ERROR;
    }

    if (gen->gi_frame_state == FRAME_EXECUTING) {
        const char *msg = "generator already executing";

        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine already executing";
        } else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator already executing";
        }

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, msg);
        return PYGEN_ERROR;
    }

    if (gen->gi_frame_state >= FRAME_COMPLETED) {
        if (PyCoro_CheckExact(gen) && !closing) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "cannot reuse already awaited coroutine");
        } else if (arg && !exc) {
            *presult = Py_None;
            Py_INCREF(*presult);
            return PYGEN_RETURN;
        }
        return PYGEN_ERROR;
    }

    assert(gen->gi_frame_state < FRAME_EXECUTING);

    // Put arg on the frame's stack
    result = arg ? arg : Py_None;
    Py_INCREF(result);
    _PyFrame_StackPush(frame, result);

    frame->previous = tstate->cframe->current_frame;

    gen->gi_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = &gen->gi_exc_state;

    if (exc) {
        assert(_PyErr_Occurred(tstate));
        _PyErr_ChainStackItem(NULL);
    }

    gen->gi_frame_state = FRAME_EXECUTING;
    result = _PyEval_EvalFrame(tstate, frame, exc);
    if (gen->gi_frame_state == FRAME_EXECUTING) {
        gen->gi_frame_state = FRAME_COMPLETED;
    }
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;

    assert(tstate->cframe->current_frame == frame->previous);
    frame->previous = NULL;

    if (result != NULL) {
        if (gen->gi_frame_state == FRAME_SUSPENDED) {
            *presult = result;
            return PYGEN_NEXT;
        }

        assert(result == Py_None || !PyAsyncGen_CheckExact(gen));

        if (result == Py_None && !PyAsyncGen_CheckExact(gen) && !arg) {
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
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        }
    }

    _PyErr_ClearExcState(&gen->gi_exc_state);

    gen->gi_frame_state = FRAME_CLEARED;
    _Nuitka_PyFrame_Clear(frame);

    *presult = result;
    return result ? PYGEN_RETURN : PYGEN_ERROR;
}

static PyObject *Nuitka_PyGen_gen_send_ex(PyGenObject *gen, PyObject *arg, int exc, int closing) {
    PyObject *result;

    if (Nuitka_PyGen_gen_send_ex2(gen, arg, &result, exc, closing) == PYGEN_RETURN) {
        if (PyAsyncGen_CheckExact(gen)) {
            assert(result == Py_None);
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopAsyncIteration);
        } else if (result == Py_None) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        } else {
            _PyGen_SetStopIterationValue(result);
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
static PyObject *Nuitka_UncompiledGenerator_throw(PyGenObject *gen, int close_on_genexit, PyObject *exception_type,
                                                  PyObject *exception_value, PyTracebackObject *exception_tb) {
#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_UncompiledGenerator_throw: Enter ");
    PRINT_ITEM((PyObject *)gen);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_NEW_LINE();
#endif

    PyObject *yf = Nuitka_PyGen_yf(gen);

    if (yf != NULL) {
        _PyInterpreterFrame *frame = (_PyInterpreterFrame *)gen->gi_iframe;

        if (close_on_genexit && EXCEPTION_MATCH_BOOL_SINGLE(exception_type, PyExc_GeneratorExit)) {
            PyFrameState state = (PyFrameState)gen->gi_frame_state;
            gen->gi_frame_state = FRAME_EXECUTING;

            int err = Nuitka_PyGen_gen_close_iter(yf);

            gen->gi_frame_state = state;

            Py_DECREF(yf);

            if (err < 0) {
                // Releasing exception, we are done with it, raising instead the error just
                // occurred.
                Py_DECREF(exception_type);
                Py_XDECREF(exception_value);
                Py_XDECREF(exception_tb);

                return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
            }

            // Handing exception ownership to this code.
            goto throw_here;
        }

        PyObject *ret;

        if (PyGen_CheckExact(yf) || PyCoro_CheckExact(yf)) {
            PyThreadState *tstate = _PyThreadState_GET();
            _PyInterpreterFrame *prev = tstate->cframe->current_frame;
            frame->previous = prev;
            tstate->cframe->current_frame = frame;
            PyFrameState state = (PyFrameState)gen->gi_frame_state;
            gen->gi_frame_state = FRAME_EXECUTING;

            // Handing exception ownership to "Nuitka_UncompiledGenerator_throw".
            ret = Nuitka_UncompiledGenerator_throw((PyGenObject *)yf, close_on_genexit, exception_type, exception_value,
                                                   exception_tb);
            gen->gi_frame_state = state;
            tstate->cframe->current_frame = prev;
            frame->previous = NULL;
        } else {
#if 0
            // TODO: Add slow mode traces.
            PRINT_ITEM(yf);
            PRINT_NEW_LINE();
#endif

            PyObject *meth;

            // TODO: Use our faster (?) code here too.
            if (_PyObject_LookupAttr(yf, &_Py_ID(throw), &meth) < 0) {
                Py_DECREF(yf);

                goto failed_throw;
            }

            if (meth == NULL) {
                Py_DECREF(yf);
                goto throw_here;
            }

            PyFrameState state = (PyFrameState)gen->gi_frame_state;
            gen->gi_frame_state = FRAME_EXECUTING;

            // TODO: Faster call code should be used.
            ret = PyObject_CallFunctionObjArgs(meth, exception_type, exception_value, exception_tb, NULL);

            gen->gi_frame_state = state;

            // Releasing exception, we are done with it.
            Py_DECREF(exception_type);
            Py_XDECREF(exception_value);
            Py_XDECREF(exception_tb);

            Py_DECREF(meth);
        }
        Py_DECREF(yf);

        if (ret == NULL) {
            PyObject *val;
            assert(gen->gi_frame_state < FRAME_CLEARED);
            ret = _PyFrame_StackPop((_PyInterpreterFrame *)gen->gi_iframe);
            assert(ret == yf);
            Py_DECREF(ret);
            assert(_PyInterpreterFrame_LASTI(frame) >= 0);
            assert(_Py_OPCODE(frame->prev_instr[-1]) == SEND);
            int jump = _Py_OPARG(frame->prev_instr[-1]);
            frame->prev_instr += jump - 1;
            if (_PyGen_FetchStopIterationValue(&val) == 0) {
                ret = Nuitka_PyGen_gen_send_ex(gen, val, 0, 0);
                Py_DECREF(val);
            } else {
                ret = Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
            }
        }

        return ret;
    }

throw_here:
    if (exception_tb == (PyTracebackObject *)Py_None) {
        exception_tb = NULL;
        Py_DECREF(exception_tb);
    } else if (exception_tb != NULL && !PyTraceBack_Check(exception_tb)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "throw() third argument must be a traceback object");
        goto failed_throw;
    }

    PyThreadState *tstate = _PyThreadState_GET();

    if (PyExceptionClass_Check(exception_type)) {
        Nuitka_Err_NormalizeException(tstate, &exception_type, &exception_value, &exception_tb);
    } else if (PyExceptionInstance_Check(exception_type)) {
        if (exception_value && exception_value != Py_None) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "instance exception may not have a separate value");
            goto failed_throw;
        } else {
            // Normalize manually here via APIs
            Py_XDECREF(exception_value);
            exception_value = exception_type;
            exception_type = PyExceptionInstance_Class(exception_type);
            Py_INCREF(exception_type);

            if (exception_tb == NULL) {
                // Can remain NULL if no traceback is available.
                exception_tb = GET_EXCEPTION_TRACEBACK(exception_value);
                Py_XINCREF(exception_tb);
            }
        }
    } else {
        // Raisable
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(
            "exceptions must be classes or instances deriving from BaseException, not %s", exception_type);
        goto failed_throw;
    }

    RESTORE_ERROR_OCCURRED_TSTATE(tstate, exception_type, exception_value, exception_tb);

    return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 1);

failed_throw:
    Py_DECREF(exception_type);
    Py_XDECREF(exception_value);
    Py_XDECREF(exception_tb);

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

static PyObject *Nuitka_PyGen_gen_send_ex(PyGenObject *gen, PyObject *arg, int exc, int closing) {
    PyThreadState *tstate = PyThreadState_GET();
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
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, msg);

        return NULL;
    }

    if (f == NULL || Nuitka_PyFrameHasCompleted(f)) {
#if PYTHON_VERSION >= 0x350
        if (PyCoro_CheckExact(gen) && !closing) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "cannot reuse already awaited coroutine");
        } else
#endif
            if (arg && !exc) {
#if PYTHON_VERSION >= 0x360
            if (PyAsyncGen_CheckExact(gen)) {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopAsyncIteration);
            } else
#endif
            {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
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

            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, msg);
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
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopAsyncIteration);
            } else
#endif
            {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
            }
        } else {
            Nuitka_SetStopIterationValue(result);
        }

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
static PyObject *Nuitka_UncompiledGenerator_throw(PyGenObject *gen, int close_on_genexit, PyObject *exception_type,
                                                  PyObject *exception_value, PyTracebackObject *exception_tb) {
#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_UncompiledGenerator_throw: Enter ");
    PRINT_ITEM((PyObject *)gen);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_NEW_LINE();
#endif

    PyObject *yf = Nuitka_PyGen_yf(gen);

    if (yf != NULL) {
        if (close_on_genexit && EXCEPTION_MATCH_BOOL_SINGLE(exception_type, PyExc_GeneratorExit)) {
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 1;
#else
            PyFrameState state = gen->gi_frame->f_state;
            gen->gi_frame->f_state = FRAME_EXECUTING;
#endif

            int err = Nuitka_PyGen_gen_close_iter(yf);
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif
            Py_DECREF(yf);

            if (err < 0) {
                // Releasing exception, we are done with it, raising instead the error just
                // occurred.
                Py_DECREF(exception_type);
                Py_XDECREF(exception_value);
                Py_XDECREF(exception_tb);

                return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
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
            ret = Nuitka_UncompiledGenerator_throw((PyGenObject *)yf, close_on_genexit, exception_type, exception_value,
                                                   exception_tb);

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
                    Py_DECREF(exception_type);
                    Py_XDECREF(exception_value);
                    Py_XDECREF(exception_tb);

                    return NULL;
                }

                CLEAR_ERROR_OCCURRED();
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
            ret = PyObject_CallFunctionObjArgs(meth, exception_type, exception_value, exception_tb, NULL);
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif

            // Releasing exception, we are done with it.
            Py_DECREF(exception_type);
            Py_XDECREF(exception_value);
            Py_XDECREF(exception_tb);

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

            if (_PyGen_FetchStopIterationValue(&exception_value) == 0) {
                ret = Nuitka_PyGen_gen_send_ex(gen, exception_value, 0, 0);

                Py_DECREF(exception_value);
            } else {
                ret = Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
            }
        }
        return ret;
    }

throw_here:
    // We continue to have exception ownership here.
    if (unlikely(_Nuitka_Generator_check_throw2(&exception_type, &exception_value, &exception_tb) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw2 already.
        return NULL;
    }

    // Transfer exception ownership to published exception.
    RESTORE_ERROR_OCCURRED(exception_type, exception_value, (PyTracebackObject *)exception_tb);

    return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 1);
}

#endif

static int Nuitka_PyGen_gen_close_iter(PyObject *yf) {
    PyObject *retval = NULL;

    if (PyGen_CheckExact(yf)
#if PYTHON_VERSION >= 0x350
        || PyCoro_CheckExact(yf)
#endif
    ) {
        assert(false);
        retval = Nuitka_PyGen_gen_close((PyGenObject *)yf, NULL);

        if (retval == NULL) {
            return -1;
        }
    } else {
        PyObject *meth = PyObject_GetAttr(yf, const_str_plain_close);

        if (meth == NULL) {
            if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                PyErr_WriteUnraisable(yf);
            }

            CLEAR_ERROR_OCCURRED();
        } else {
            retval = CALL_FUNCTION_NO_ARGS(meth);

            Py_DECREF(meth);

            if (retval == NULL) {
                return -1;
            }
        }
    }

    Py_XDECREF(retval);
    return 0;
}

static PyObject *Nuitka_PyGen_gen_close(PyGenObject *gen, PyObject *args) {
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
        err = Nuitka_PyGen_gen_close_iter(yf);

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
        SET_CURRENT_EXCEPTION_TYPE0(PyExc_GeneratorExit);
    }

    PyObject *retval = Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 1);

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

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, msg);
        return NULL;
    }

    if (PyErr_ExceptionMatches(PyExc_StopIteration) || PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
        CLEAR_ERROR_OCCURRED();

        Py_INCREF(Py_None);
        return Py_None;
    }
    return NULL;
}

#endif
