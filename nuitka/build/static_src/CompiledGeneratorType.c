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
/** Compiled Generators.
 *
 * Unlike in CPython, we have one type for just generators, this doesn't do coroutines
 * nor asyncgen.
 *
 * It strives to be full replacement for normal generators, while providing also an
 * interface for quick iteration from compiled code.
 *
 */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// In a separate file, code to interact with uncompiled generators, that does
// all the quirks necessary to get those working.
#include "CompiledGeneratorTypeUncompiledIntegration.c"

// Debugging output tools
#if _DEBUG_GENERATOR
NUITKA_MAY_BE_UNUSED static void _PRINT_GENERATOR_STATUS(char const *descriptor, char const *context,
                                                         struct Nuitka_GeneratorObject *generator) {
    char const *status;

    switch (generator->m_status) {
    case status_Finished:
        status = "(finished)";
        break;
    case status_Running:
        status = "(running)";
        break;
    case status_Unused:
        status = "(unused)";
        break;
    default:
        status = "(ILLEGAL)";
        break;
    }

    PRINT_STRING(descriptor);
    PRINT_STRING(" : ");
    PRINT_STRING(context);
    PRINT_STRING(" ");
    PRINT_ITEM((PyObject *)generator);
    PRINT_STRING(" ");
    PRINT_STRING(status);
    PRINT_STRING(" ");
    PRINT_REFCOUNT((PyObject *)generator);
    PRINT_NEW_LINE();
}

#define PRINT_GENERATOR_STATUS(context, generator) _PRINT_GENERATOR_STATUS(__FUNCTION__, context, generator)

#endif

#if _DEBUG_GENERATOR || _DEBUG_COROUTINE || _DEBUG_ASYNCGEN

NUITKA_MAY_BE_UNUSED static void PRINT_COROUTINE_VALUE(char const *name, PyObject *value) {
    PRINT_STRING(name);
    PRINT_STRING("=");
    PRINT_ITEM(value);
    if (value) {
        PRINT_REFCOUNT(value);
    }
    PRINT_NEW_LINE();
}

NUITKA_MAY_BE_UNUSED static void PRINT_COROUTINE_STRING(char const *name, char const *value) {
    PRINT_STRING(name);
    PRINT_STRING("=");
    PRINT_STRING(value);
    PRINT_NEW_LINE();
}

#endif

static PyObject *Nuitka_Generator_tp_repr(struct Nuitka_GeneratorObject *generator) {
    return Nuitka_String_FromFormat("<compiled_generator object %s at %p>",
#if PYTHON_VERSION < 0x350
                                    Nuitka_String_AsString(generator->m_name),
#else
                                    Nuitka_String_AsString(generator->m_qualname),
#endif
                                    generator);
}

static long Nuitka_Generator_tp_traverse(struct Nuitka_GeneratorObject *generator, visitproc visit, void *arg) {
    CHECK_OBJECT(generator);

    // TODO: Identify the impact of not visiting owned objects like module.
#if PYTHON_VERSION >= 0x300
    Py_VISIT(generator->m_yieldfrom);
#endif

    for (Py_ssize_t i = 0; i < generator->m_closure_given; i++) {
        Py_VISIT(generator->m_closure[i]);
    }

    Py_VISIT(generator->m_frame);

    return 0;
}

static void Nuitka_Generator_release_closure(struct Nuitka_GeneratorObject *generator) {
    for (Py_ssize_t i = 0; i < generator->m_closure_given; i++) {
        CHECK_OBJECT(generator->m_closure[i]);
        Py_DECREF(generator->m_closure[i]);
    }

    generator->m_closure_given = 0;
}

#if PYTHON_VERSION >= 0x300

// Note: Shared with coroutines and asyncgen code.
static PyObject *ERROR_GET_STOP_ITERATION_VALUE(void) {
    assert(PyErr_ExceptionMatches(PyExc_StopIteration));

    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;
    FETCH_ERROR_OCCURRED(&exception_type, &exception_value, &exception_tb);

    Py_DECREF(exception_type);
    Py_XDECREF(exception_tb);

    PyObject *value = NULL;

    if (exception_value) {
        if (EXCEPTION_MATCH_BOOL_SINGLE(exception_value, PyExc_StopIteration)) {
            value = ((PyStopIterationObject *)exception_value)->value;
            Py_XINCREF(value);
            Py_DECREF(exception_value);
        } else {
            value = exception_value;
        }
    }

    if (value == NULL) {
        Py_INCREF(Py_None);
        value = Py_None;
    }

    return value;
}

static PyObject *_Nuitka_Generator_throw2(struct Nuitka_GeneratorObject *generator, PyObject *exception_type,
                                          PyObject *exception_value, PyTracebackObject *exception_tb);
#if PYTHON_VERSION >= 0x350
static PyObject *_Nuitka_Coroutine_throw2(struct Nuitka_CoroutineObject *coroutine, bool closing,
                                          PyObject *exception_type, PyObject *exception_value,
                                          PyTracebackObject *exception_tb);
#endif

static PyObject *_Nuitka_YieldFromPassExceptionTo(PyObject *value, PyObject *exception_type, PyObject *exception_value,
                                                  PyTracebackObject *exception_tb) {
    // The yielding generator is being closed, but we also are tasked to
    // immediately close the currently running sub-generator.
    if (EXCEPTION_MATCH_BOOL_SINGLE(exception_type, PyExc_GeneratorExit)) {
        PyObject *close_method = PyObject_GetAttr(value, const_str_plain_close);

        if (close_method) {
            PyObject *close_value = PyObject_Call(close_method, const_tuple_empty, NULL);
            Py_DECREF(close_method);

            if (unlikely(close_value == NULL)) {
                // Release exception, we are done with it, raising the one from close instead.
                Py_DECREF(exception_type);
                Py_XDECREF(exception_value);
                Py_XDECREF(exception_tb);

                return NULL;
            }

            Py_DECREF(close_value);
        } else {
            PyObject *error = GET_ERROR_OCCURRED();

            if (error != NULL && !EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_AttributeError)) {
                PyErr_WriteUnraisable((PyObject *)value);
            }
        }

        // Transfer exception ownership to pusblished.
        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

        return NULL;
    }

#if NUITKA_UNCOMPILED_THROW_INTEGRATION
    if (PyGen_CheckExact(value)
#if PYTHON_VERSION >= 0x350
        || PyCoro_CheckExact(value)
#endif
    ) {
        PyGenObject *gen = (PyGenObject *)value;

        // Handing exception ownership over.
        PyObject *result = Nuitka_UncompiledGenerator_throw(gen, 1, exception_type, exception_value, exception_tb);

        return result;
    }
#endif

    if (Nuitka_Generator_Check(value)) {
        struct Nuitka_GeneratorObject *gen = ((struct Nuitka_GeneratorObject *)value);

        return _Nuitka_Generator_throw2(gen, exception_type, exception_value, exception_tb);
    }

#if PYTHON_VERSION >= 0x350
    if (Nuitka_Coroutine_Check(value)) {
        struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineObject *)value);
        // Handing exception ownership over.
        return _Nuitka_Coroutine_throw2(coro, true, exception_type, exception_value, exception_tb);
    }

    if (Nuitka_CoroutineWrapper_Check(value)) {
        struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineWrapperObject *)value)->m_coroutine;
        // Handing exception ownership over.
        return _Nuitka_Coroutine_throw2(coro, true, exception_type, exception_value, exception_tb);
    }
#endif

    PyObject *throw_method = PyObject_GetAttr(value, const_str_plain_throw);

    if (throw_method) {
        PyObject *result =
            PyObject_CallFunctionObjArgs(throw_method, exception_type, exception_value, exception_tb, NULL);
        Py_DECREF(throw_method);

        // Releasing exception we own.
        Py_DECREF(exception_type);
        Py_XDECREF(exception_value);
        Py_XDECREF(exception_tb);

        return result;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(GET_ERROR_OCCURRED(), PyExc_AttributeError)) {
        // Restoring the exception we own, to be released when handling it.
        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

        return NULL;
    } else {
        assert(ERROR_OCCURRED());

        // Releasing exception we own.
        Py_DECREF(exception_type);
        Py_XDECREF(exception_value);
        Py_XDECREF(exception_tb);

        return NULL;
    }
}

static PyObject *_Nuitka_YieldFromGeneratorCore(struct Nuitka_GeneratorObject *generator, PyObject *yieldfrom,
                                                PyObject *send_value) {
    // Send iteration value to the sub-generator, which may be a CPython
    // generator object, something with an iterator next, or a send method,
    // where the later is only required if values other than "None" need to
    // be passed in.
    CHECK_OBJECT(yieldfrom);
    assert(send_value != NULL || ERROR_OCCURRED());

    PyObject *retval;

#if 0
    PRINT_STRING("YIELD CORE:");
    PRINT_ITEM( value );
    PRINT_ITEM( send_value );

    PRINT_NEW_LINE();
#endif

    assert(send_value != NULL || ERROR_OCCURRED());

    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;
    FETCH_ERROR_OCCURRED(&exception_type, &exception_value, &exception_tb);

    // Exception, was thrown into us, need to send that to sub-generator.
    if (exception_type != NULL) {
        // Passing ownership of exception fetch to it.
        retval = _Nuitka_YieldFromPassExceptionTo(yieldfrom, exception_type, exception_value, exception_tb);

        if (unlikely(send_value == NULL)) {
            PyObject *error = GET_ERROR_OCCURRED();

            if (error != NULL && EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_StopIteration)) {
                generator->m_returned = ERROR_GET_STOP_ITERATION_VALUE();

                assert(!ERROR_OCCURRED());
                return NULL;
            }
        }
    } else if (PyGen_CheckExact(yieldfrom)) {
        retval = Nuitka_PyGen_Send((PyGenObject *)yieldfrom, Py_None);
    }
#if PYTHON_VERSION >= 0x350
    else if (PyCoro_CheckExact(yieldfrom)) {
        retval = Nuitka_PyGen_Send((PyGenObject *)yieldfrom, Py_None);
    }
#endif
    else if (send_value == Py_None && Py_TYPE(yieldfrom)->tp_iternext != NULL) {
        retval = Py_TYPE(yieldfrom)->tp_iternext(yieldfrom);
    } else {
        // Bug compatibility here, before 3.3 tuples were unrolled in calls, which is what
        // PyObject_CallMethod does.
#if PYTHON_VERSION >= 0x340
        retval = PyObject_CallMethodObjArgs(yieldfrom, const_str_plain_send, send_value, NULL);
#else
        retval = PyObject_CallMethod(yieldfrom, (char *)"send", (char *)"O", send_value);
#endif
    }

    // Check the sub-generator result
    if (retval == NULL) {
        PyObject *error = GET_ERROR_OCCURRED();

        if (error == NULL) {
            Py_INCREF(Py_None);
            generator->m_returned = Py_None;
        } else if (likely(EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_StopIteration))) {
            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            generator->m_returned = ERROR_GET_STOP_ITERATION_VALUE();
            assert(!ERROR_OCCURRED());
        }

        return NULL;
    } else {
        return retval;
    }
}

static PyObject *Nuitka_YieldFromGeneratorCore(struct Nuitka_GeneratorObject *generator, PyObject *send_value) {
    CHECK_OBJECT(generator);
    CHECK_OBJECT_X(send_value);

    PyObject *yieldfrom = generator->m_yieldfrom;
    CHECK_OBJECT(yieldfrom);

    // Need to make it unaccessible while using it.
    generator->m_yieldfrom = NULL;
    PyObject *yielded = _Nuitka_YieldFromGeneratorCore(generator, yieldfrom, send_value);

    if (yielded == NULL) {
        Py_DECREF(yieldfrom);

        if (generator->m_returned != NULL) {
            PyObject *yield_from_result = generator->m_returned;
            generator->m_returned = NULL;

            yielded = ((generator_code)generator->m_code)(generator, yield_from_result);
        } else {
            assert(ERROR_OCCURRED());
            yielded = ((generator_code)generator->m_code)(generator, NULL);
        }

    } else {
        generator->m_yieldfrom = yieldfrom;
    }

    return yielded;
}

static PyObject *Nuitka_YieldFromGeneratorNext(struct Nuitka_GeneratorObject *generator) {
    CHECK_OBJECT(generator);

    // Coroutines are already perfect for yielding from.
#if PYTHON_VERSION >= 0x350
    if (PyCoro_CheckExact(generator->m_yieldfrom) || Nuitka_Coroutine_Check(generator->m_yieldfrom)) {
        if (unlikely((generator->m_code_object->co_flags & CO_ITERABLE_COROUTINE) == 0)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError,
                                            "cannot 'yield from' a coroutine object in a non-coroutine generator");
        }
    } else
#endif
    {
        PyObject *new_iterator = MAKE_ITERATOR(generator->m_yieldfrom);
        if (new_iterator != NULL) {
            Py_DECREF(generator->m_yieldfrom);
            generator->m_yieldfrom = new_iterator;
        }
    }

    return Nuitka_YieldFromGeneratorCore(generator, Py_None);
}

static PyObject *Nuitka_YieldFromGeneratorInitial(struct Nuitka_GeneratorObject *generator, PyObject *send_value) {
    PyObject *result = Nuitka_YieldFromGeneratorCore(generator, send_value);

#if 0
    PRINT_STRING("RES:");
    PRINT_ITEM( result );
    PRINT_NEW_LINE();
#endif

    return result;
}

#endif

static Nuitka_ThreadStateFrameType *_Nuitka_GeneratorPushFrame(PyThreadState *thread_state,
                                                               Nuitka_ThreadStateFrameType *generator_frame) {
    PRINT_TOP_FRAME("Generator push entry gives top frame:");
    PRINT_INTERPRETER_FRAME("Pushing:", generator_frame);

    // First take of running frame from the stack, owning a reference.
#if PYTHON_VERSION < 0x3b0
    PyFrameObject *return_frame = thread_state->frame;
#ifndef __NUITKA_NO_ASSERT__
    if (return_frame) {
        assertFrameObject((struct Nuitka_FrameObject *)return_frame);
    }
#endif
#else
    _PyInterpreterFrame *return_frame = thread_state->cframe->current_frame;
#endif

    if (generator_frame != NULL) {

        // It's not supposed to be on the top right now.
#if PYTHON_VERSION < 0x3b0
        // It would be nice if our frame were still alive. Nobody had the
        // right to release it.
        assertFrameObject((struct Nuitka_FrameObject *)generator_frame);

        // Link frames
        assert(return_frame != generator_frame);
        Py_XINCREF(return_frame);
        generator_frame->f_back = return_frame;

        // Make generator frame active
        thread_state->frame = generator_frame;
#else
        // It would be nice if our frame were still alive. Nobody had the
        // right to release it.
        assertFrameObject((struct Nuitka_FrameObject *)(generator_frame->frame_obj));

        // Link frames
        if (return_frame) {
            // Connect frames if possible.
            PyFrameObject *back_frame = return_frame->frame_obj;

            generator_frame->frame_obj->f_back = back_frame;
            Py_INCREF(back_frame);
        }
        generator_frame->previous = return_frame;

        // Make generator frame active
        thread_state->cframe->current_frame = generator_frame;
#endif
    }

    PRINT_TOP_FRAME("Generator push exit gives top frame:");

    return return_frame;
}

static Nuitka_ThreadStateFrameType *_Nuitka_GeneratorPushFrameObject(PyThreadState *thread_state,
                                                                     struct Nuitka_FrameObject *generator_frame) {
#if PYTHON_VERSION < 0x3b0
    Nuitka_ThreadStateFrameType *thread_frame = &generator_frame->m_frame;
#else
    Nuitka_ThreadStateFrameType *thread_frame = NULL;
    if (generator_frame != NULL) {
        thread_frame = &generator_frame->m_interpreter_frame;
    }
#endif

    return _Nuitka_GeneratorPushFrame(thread_state, thread_frame);
}

static void _Nuitka_GeneratorPopFrame(PyThreadState *thread_state, Nuitka_ThreadStateFrameType *return_frame) {
#if PYTHON_VERSION < 0x3b0
    thread_state->frame = return_frame;
#else
    thread_state->cframe->current_frame = return_frame;

    if (return_frame != NULL) {
        return_frame->previous = NULL;
    }
#endif

    PRINT_TOP_FRAME("Generator pop exit gives top frame:");
}

static PyObject *_Nuitka_Generator_send(struct Nuitka_GeneratorObject *generator, PyObject *value,
                                        PyObject *exception_type, PyObject *exception_value,
                                        PyTracebackObject *exception_tb) {
    CHECK_OBJECT(generator);
    assert(Nuitka_Generator_Check((PyObject *)generator));
    CHECK_OBJECT_X(exception_type);
    CHECK_OBJECT_X(exception_value);
    CHECK_OBJECT_X(exception_tb);
    CHECK_OBJECT_X(value);

#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Enter", generator);
    PRINT_COROUTINE_VALUE("value", value);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    if (value != NULL) {
        assert(exception_type == NULL);
        assert(exception_value == NULL);
        assert(exception_tb == NULL);
    }

    if (generator->m_status != status_Finished) {
        if (generator->m_running) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "generator already executing");
            return NULL;
        }

        PyThreadState *thread_state = PyThreadState_GET();

#if PYTHON_VERSION < 0x300
        PyObject *saved_exception_type = thread_state->exc_type;
        PyObject *saved_exception_value = NULL;
        PyTracebackObject *saved_exception_traceback = NULL;

        if (saved_exception_type != Py_None && saved_exception_type != NULL) {
            saved_exception_value = thread_state->exc_value;
            Py_INCREF(saved_exception_type);
            Py_XINCREF(saved_exception_value);
            saved_exception_traceback = (PyTracebackObject *)thread_state->exc_traceback;
            Py_XINCREF(saved_exception_traceback);
        }
#endif

        // Put the generator back on the frame stack.
        Nuitka_ThreadStateFrameType *return_frame = _Nuitka_GeneratorPushFrameObject(thread_state, generator->m_frame);

        if (generator->m_status == status_Unused) {
            generator->m_status = status_Running;
        }

        // Continue the yielder function while preventing recursion.
        generator->m_running = true;

        // Check for thrown exception, publish it to the generator code.
        if (unlikely(exception_type)) {
            assert(value == NULL);

            // Transfer exception ownership to published.
            RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);
        }

        if (generator->m_frame) {
            Nuitka_Frame_MarkAsExecuting(generator->m_frame);
        }

#if _DEBUG_GENERATOR
        PRINT_GENERATOR_STATUS("Switching to coroutine", generator);
        PRINT_COROUTINE_VALUE("value", value);
        PRINT_CURRENT_EXCEPTION();
        PRINT_NEW_LINE();
        // dumpFrameStack();
#endif

        PyObject *yielded;

#if PYTHON_VERSION >= 0x300
        if (generator->m_yieldfrom == NULL) {
            yielded = ((generator_code)generator->m_code)(generator, value);
        } else {
            yielded = Nuitka_YieldFromGeneratorInitial(generator, value);
        }
#else
        yielded = ((generator_code)generator->m_code)(generator, value);
#endif

#if PYTHON_VERSION >= 0x300
        // If the generator returns with m_yieldfrom set, it wants us to yield
        // from that value from now on.
        while (yielded == NULL && generator->m_yieldfrom != NULL) {
            yielded = Nuitka_YieldFromGeneratorNext(generator);
        }
#endif
        if (generator->m_frame) {
            Nuitka_Frame_MarkAsNotExecuting(generator->m_frame);
        }

        generator->m_running = false;

        thread_state = PyThreadState_GET();

        // Remove the generator from the frame stack.
        if (generator->m_frame) {
            // assert(thread_state->frame == &generator->m_frame->m_frame);
            assertFrameObject(generator->m_frame);

            Py_CLEAR(generator->m_frame->m_frame.f_back);
        }

        // Return back to the frame that called us.
        _Nuitka_GeneratorPopFrame(thread_state, return_frame);

#if _DEBUG_GENERATOR
        PRINT_GENERATOR_STATUS("Returned from generator", generator);
        // dumpFrameStack();
#endif

        if (yielded == NULL) {
#if _DEBUG_GENERATOR
            PRINT_GENERATOR_STATUS("finishing from yield", generator);
            PRINT_STRING("-> finishing generator sets status_Finished\n");
            PRINT_COROUTINE_VALUE("return_value", generator->m_returned);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
            generator->m_status = status_Finished;

            if (generator->m_frame != NULL) {
#if PYTHON_VERSION >= 0x340
                Nuitka_SetFrameGenerator(generator->m_frame, NULL);
#endif
                Py_DECREF(generator->m_frame);
                generator->m_frame = NULL;
            }

            Nuitka_Generator_release_closure(generator);

#if PYTHON_VERSION < 0x300
            if (saved_exception_type != NULL && saved_exception_type != Py_None) {
                Py_DECREF(saved_exception_type);
                Py_XDECREF(saved_exception_value);
                Py_XDECREF(saved_exception_traceback);
            }
#endif

#if PYTHON_VERSION >= 0x350
            if (
#if PYTHON_VERSION < 0x370
                generator->m_code_object->co_flags & CO_FUTURE_GENERATOR_STOP &&
#endif
                GET_ERROR_OCCURRED() == PyExc_StopIteration) {
                PyObject *saved_exception_type, *saved_exception_value;
                PyTracebackObject *saved_exception_tb;

                FETCH_ERROR_OCCURRED(&saved_exception_type, &saved_exception_value, &saved_exception_tb);
                NORMALIZE_EXCEPTION(&saved_exception_type, &saved_exception_value, &saved_exception_tb);

                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "generator raised StopIteration");

                FETCH_ERROR_OCCURRED(&exception_type, &exception_value, &exception_tb);

                RAISE_EXCEPTION_WITH_CAUSE(&exception_type, &exception_value, &exception_tb, saved_exception_value);

                CHECK_OBJECT(exception_value);
                CHECK_OBJECT(saved_exception_value);

                Py_INCREF(saved_exception_value);
                PyException_SetContext(exception_value, saved_exception_value);

                Py_DECREF(saved_exception_type);
                Py_XDECREF(saved_exception_tb);

                RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

                return NULL;
            }
#endif

            // Create StopIteration if necessary, i.e. return value that is not "None" was
            // given. TODO: Push this further down the user line, we might be able to avoid
            // it for some uses, e.g. quick iteration entirely.
#if PYTHON_VERSION >= 0x300
            if (generator->m_returned) {
                if (generator->m_returned != Py_None) {
                    Nuitka_SetStopIterationValue(generator->m_returned);
                }

                Py_DECREF(generator->m_returned);
                generator->m_returned = NULL;

#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Return value to exception set", generator);
                PRINT_CURRENT_EXCEPTION();
                PRINT_NEW_LINE();
#endif
            }
#endif

            return NULL;
        } else {
#if _NUITKA_MAINTAIN_SYS_EXC_VARS
            PyObject *old_type = thread_state->exc_type;
            PyObject *old_value = thread_state->exc_value;
            PyTracebackObject *old_tb = (PyTracebackObject *)thread_state->exc_traceback;

            // Set sys attributes in the fastest possible way.
            PyObject *sys_dict = thread_state->interp->sysdict;
            CHECK_OBJECT(sys_dict);

            if (saved_exception_type != NULL && saved_exception_type != Py_None) {
                thread_state->exc_type = saved_exception_type;
                thread_state->exc_value = saved_exception_value;
                thread_state->exc_traceback = (PyObject *)saved_exception_traceback;

                Py_XDECREF(old_type);
                Py_XDECREF(old_value);
                Py_XDECREF(old_tb);

                if (old_type != saved_exception_type) {
                    PyDict_SetItem(sys_dict, const_str_plain_exc_type, saved_exception_type);
                }
                if (saved_exception_value != old_value) {
                    PyDict_SetItem(sys_dict, const_str_plain_exc_value,
                                   saved_exception_value ? saved_exception_value : Py_None);
                }
                if (saved_exception_traceback != old_tb) {
                    PyDict_SetItem(sys_dict, const_str_plain_exc_traceback,
                                   saved_exception_traceback ? (PyObject *)saved_exception_traceback : Py_None);
                }
            } else {
                thread_state->exc_type = Py_None;
                thread_state->exc_value = Py_None;
                thread_state->exc_traceback = (PyObject *)Py_None;

                Py_INCREF(Py_None);
                Py_INCREF(Py_None);
                Py_INCREF(Py_None);

                Py_XDECREF(old_type);
                Py_XDECREF(old_value);
                Py_XDECREF(old_tb);

                if (old_type != Py_None) {
                    PyDict_SetItem(sys_dict, const_str_plain_exc_type, Py_None);
                }
                if (old_value != Py_None) {
                    PyDict_SetItem(sys_dict, const_str_plain_exc_value, Py_None);
                }
                if (old_tb != (PyTracebackObject *)Py_None) {
                    PyDict_SetItem(sys_dict, const_str_plain_exc_traceback, Py_None);
                }
            }
#endif

            return yielded;
        }
    } else {
        return NULL;
    }
}

static PyObject *Nuitka_Generator_send(struct Nuitka_GeneratorObject *generator, PyObject *value) {
    if (generator->m_status == status_Unused && value != NULL && value != Py_None) {
        // Buggy CPython 3.10 refuses to allow later usage.
#if PYTHON_VERSION >= 0x3a0 && PYTHON_VERSION < 0x3a2
        generator->m_status = status_Finished;
#endif

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "can't send non-None value to a just-started generator");
        return NULL;
    }

    PyObject *result = _Nuitka_Generator_send(generator, value, NULL, NULL, NULL);

    if (result == NULL) {
        if (GET_ERROR_OCCURRED() == NULL) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        }
    }

    return result;
}

static PyObject *Nuitka_Generator_tp_iternext(struct Nuitka_GeneratorObject *generator) {
    return _Nuitka_Generator_send(generator, Py_None, NULL, NULL, NULL);
}

/* Our own qiter interface, which is for quicker simple loop style iteration,
   that does not send anything in. */
PyObject *Nuitka_Generator_qiter(struct Nuitka_GeneratorObject *generator, bool *finished) {
    PyObject *result = _Nuitka_Generator_send(generator, Py_None, NULL, NULL, NULL);

    if (result == NULL) {
        if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED())) {
            *finished = false;
            return NULL;
        }

        *finished = true;
        return NULL;
    }

    *finished = false;
    return result;
}

// Note: Used by compiled frames.
static bool _Nuitka_Generator_close(struct Nuitka_GeneratorObject *generator) {
#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Enter", generator);
#endif
    CHECK_OBJECT(generator);

    if (generator->m_status == status_Running) {
        Py_INCREF(PyExc_GeneratorExit);

        PyObject *result = _Nuitka_Generator_send(generator, NULL, PyExc_GeneratorExit, NULL, NULL);

        if (unlikely(result)) {
            Py_DECREF(result);

            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "generator ignored GeneratorExit");
            return false;
        } else {
            PyObject *error = GET_ERROR_OCCURRED();

            // StopIteration as exception.
            if (error == NULL) {
                return true;
            }

            // Maybe another acceptable exception for generator exit.
            if (EXCEPTION_MATCH_GENERATOR(error)) {
                CLEAR_ERROR_OCCURRED();

                return true;
            }

            return false;
        }
    }

    return true;
}

static PyObject *Nuitka_Generator_close(struct Nuitka_GeneratorObject *generator) {
    bool r = _Nuitka_Generator_close(generator);

    if (unlikely(r == false)) {
        return NULL;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

// Shared code for checking a thrown exception, coroutines, asyncgen, uncompiled ones do this too.
static bool _Nuitka_Generator_check_throw2(PyObject **exception_type, PyObject **exception_value,
                                           PyTracebackObject **exception_tb) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT_X(*exception_value);
    CHECK_OBJECT_X(*exception_tb);

    if (*exception_tb == (PyTracebackObject *)Py_None) {
        Py_DECREF(*exception_tb);
        *exception_tb = NULL;
    } else if (*exception_tb != NULL && !PyTraceBack_Check(*exception_tb)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "throw() third argument must be a traceback object");
        goto failed_throw;
    }

    if (PyExceptionClass_Check(*exception_type)) {
        // TODO: Must not normalize here.
        NORMALIZE_EXCEPTION(exception_type, exception_value, exception_tb);
    } else if (PyExceptionInstance_Check(*exception_type)) {
        if (*exception_value != NULL && *exception_value != Py_None) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "instance exception may not have a separate value");
            goto failed_throw;
        }

        // Release old None value and replace it with the object, then set the exception type
        // from the class.
        Py_XDECREF(*exception_value);
        *exception_value = *exception_type;

        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);
    } else {
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "exceptions must be classes, or instances, not %s",
                     Py_TYPE(*exception_type)->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "exceptions must be classes or instances deriving from BaseException, not %s",
                     Py_TYPE(*exception_type)->tp_name);
#endif

        goto failed_throw;
    }

    return true;

failed_throw:
    // Release exception, we are done with it now.
    Py_DECREF(*exception_type);
    Py_XDECREF(*exception_value);
    Py_XDECREF(*exception_tb);

    return false;
}

#if PYTHON_VERSION >= 0x300

static bool _Nuitka_Generator_close(struct Nuitka_GeneratorObject *generator);
#if PYTHON_VERSION >= 0x350
static bool _Nuitka_Coroutine_close(struct Nuitka_CoroutineObject *coroutine);
#if PYTHON_VERSION >= 0x360
static bool _Nuitka_Asyncgen_close(struct Nuitka_AsyncgenObject *asyncgen);
#endif
#endif

// Note: This is also used for coroutines and asyncgen
static bool Nuitka_gen_close_iter(PyObject *yieldfrom) {
#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_gen_close_iter: Enter\n");
#endif

    CHECK_OBJECT(yieldfrom);

    // TODO: Could specialize depending in yieldfrom type for performance. Many
    // times these will be our own ones, or known ones like uncompiled
    // generators.
    if (Nuitka_Generator_Check(yieldfrom)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Defer to _Nuitka_Generator_close\n");
#endif
        return _Nuitka_Generator_close((struct Nuitka_GeneratorObject *)yieldfrom);
    }

#if PYTHON_VERSION >= 0x350
    if (Nuitka_Coroutine_Check(yieldfrom)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Defer to _Nuitka_Coroutine_close\n");
#endif
        return _Nuitka_Coroutine_close((struct Nuitka_CoroutineObject *)yieldfrom);
    }
#endif

#if PYTHON_VERSION >= 0x360
    if (Nuitka_Asyncgen_Check(yieldfrom)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Defer to _Nuitka_Asyncgen_close\n");
#endif
        return _Nuitka_Asyncgen_close((struct Nuitka_AsyncgenObject *)yieldfrom);
    }
#endif

    PyObject *meth = PyObject_GetAttr(yieldfrom, const_str_plain_close);

    if (unlikely(meth == NULL)) {
        if (unlikely(!PyErr_ExceptionMatches(PyExc_AttributeError))) {
#if _DEBUG_GENERATOR
            PRINT_STRING("Nuitka_gen_close_iter: Strange error while looking up close method.\n");
#endif
            PyErr_WriteUnraisable(yieldfrom);
        }

        CLEAR_ERROR_OCCURRED();

#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Leave, has no close method.\n");
#endif
        return true;
    }

    PyObject *retval = CALL_FUNCTION_NO_ARGS(meth);
    Py_DECREF(meth);

    if (unlikely(retval == NULL)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Leave, exception from close.\n");
#endif
        return false;
    }

    CHECK_OBJECT(retval);
    Py_DECREF(retval);

#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_gen_close_iter: Leave, closed.\n");
#endif

    return true;
}
#endif

#if PYTHON_VERSION >= 0x360
static bool Nuitka_AsyncgenAsend_Check(PyObject *object);
struct Nuitka_AsyncgenAsendObject;
static PyObject *_Nuitka_AsyncgenAsend_throw2(struct Nuitka_AsyncgenAsendObject *asyncgen_asend,
                                              PyObject *exception_type, PyObject *exception_value,
                                              PyTracebackObject *exception_tb);
#endif

static PyObject *_Nuitka_Generator_throw2(struct Nuitka_GeneratorObject *generator, PyObject *exception_type,
                                          PyObject *exception_value, PyTracebackObject *exception_tb) {
#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Enter", generator);
    PRINT_COROUTINE_VALUE("yieldfrom", generator->m_yieldfrom);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_NEW_LINE();
#endif

    CHECK_OBJECT(generator);
    assert(Nuitka_Generator_Check((PyObject *)generator));
    CHECK_OBJECT(exception_type);
    CHECK_OBJECT_X(exception_value);
    CHECK_OBJECT_X(exception_tb);

#if PYTHON_VERSION >= 0x300
    if (generator->m_yieldfrom != NULL) {
        if (EXCEPTION_MATCH_BOOL_SINGLE(exception_type, PyExc_GeneratorExit)) {
            // Generators need to close the yield_from.
            generator->m_running = 1;
            bool res = Nuitka_gen_close_iter(generator->m_yieldfrom);
            generator->m_running = 0;

            if (res == false) {
                // Release exception, we are done with it now and pick up the new one.
                Py_DECREF(exception_type);
                Py_XDECREF(exception_value);
                Py_XDECREF(exception_tb);

                FETCH_ERROR_OCCURRED(&exception_type, &exception_value, &exception_tb);
            }

            // Transferred exception ownership to "_Nuitka_Generator_send".
            return _Nuitka_Generator_send(generator, NULL, exception_type, exception_value, exception_tb);
        }

        PyObject *ret;

#if _DEBUG_GENERATOR
        PRINT_GENERATOR_STATUS("Passing to yielded from", generator);
        PRINT_COROUTINE_VALUE("m_yieldfrom", generator->m_yieldfrom);
        PRINT_NEW_LINE();
#endif

        if (Nuitka_Generator_Check(generator->m_yieldfrom)) {
            struct Nuitka_GeneratorObject *gen = ((struct Nuitka_GeneratorObject *)generator->m_yieldfrom);
            // Transferred exception ownership to "_Nuitka_Generator_throw2".
            generator->m_running = 1;
            ret = _Nuitka_Generator_throw2(gen, exception_type, exception_value, exception_tb);
            generator->m_running = 0;
#if NUITKA_UNCOMPILED_THROW_INTEGRATION
        } else if (PyGen_CheckExact(generator->m_yieldfrom)) {
            PyGenObject *gen = (PyGenObject *)generator->m_yieldfrom;

            // Transferred exception ownership to "Nuitka_UncompiledGenerator_throw".
            generator->m_running = 1;
            ret = Nuitka_UncompiledGenerator_throw(gen, 1, exception_type, exception_value, exception_tb);
            generator->m_running = 0;
#endif
#if PYTHON_VERSION >= 0x350
        } else if (Nuitka_Coroutine_Check(generator->m_yieldfrom)) {
            struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineObject *)generator->m_yieldfrom);
            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            generator->m_running = 1;
            ret = _Nuitka_Coroutine_throw2(coro, true, exception_type, exception_value, exception_tb);
            generator->m_running = 0;
        } else if (Nuitka_CoroutineWrapper_Check(generator->m_yieldfrom)) {
            struct Nuitka_CoroutineObject *coro =
                ((struct Nuitka_CoroutineWrapperObject *)generator->m_yieldfrom)->m_coroutine;

            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            generator->m_running = 1;
            ret = _Nuitka_Coroutine_throw2(coro, true, exception_type, exception_value, exception_tb);
            generator->m_running = 0;
#if NUITKA_UNCOMPILED_THROW_INTEGRATION
        } else if (PyCoro_CheckExact(generator->m_yieldfrom)) {
            PyGenObject *gen = (PyGenObject *)generator->m_yieldfrom;

            // Transferred exception ownership to "Nuitka_UncompiledGenerator_throw".
            generator->m_running = 1;
            ret = Nuitka_UncompiledGenerator_throw(gen, 1, exception_type, exception_value, exception_tb);
            generator->m_running = 0;
#endif
#if PYTHON_VERSION >= 0x360
        } else if (Nuitka_AsyncgenAsend_Check(generator->m_yieldfrom)) {
            struct Nuitka_AsyncgenAsendObject *asyncgen_asend =
                ((struct Nuitka_AsyncgenAsendObject *)generator->m_yieldfrom);

            // Transferred exception ownership to "_Nuitka_AsyncgenAsend_throw2".
            generator->m_running = 1;
            ret = _Nuitka_AsyncgenAsend_throw2(asyncgen_asend, exception_type, exception_value, exception_tb);
            generator->m_running = 0;
#endif
#endif
        } else {
            PyObject *meth = PyObject_GetAttr(generator->m_yieldfrom, const_str_plain_throw);
            if (unlikely(meth == NULL)) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    // Release exception, we are done with it now.
                    Py_DECREF(exception_type);
                    Py_XDECREF(exception_value);
                    Py_XDECREF(exception_tb);

                    return NULL;
                }

                CLEAR_ERROR_OCCURRED();

                // Passing exception ownership to that code.
                goto throw_here;
            }

            CHECK_OBJECT(exception_type);

#if 0
            // TODO: Add slow mode traces.
            PRINT_ITEM(coroutine->m_yieldfrom);
            PRINT_NEW_LINE();
#endif
            generator->m_running = 1;
            ret = PyObject_CallFunctionObjArgs(meth, exception_type, exception_value, exception_tb, NULL);
            generator->m_running = 0;

            Py_DECREF(meth);

            // Release exception, we are done with it now.
            Py_DECREF(exception_type);
            Py_XDECREF(exception_value);
            Py_XDECREF(exception_tb);
        }

        if (unlikely(ret == NULL)) {
            // Return value or exception, not to continue with yielding from.
            if (generator->m_yieldfrom != NULL) {
                CHECK_OBJECT(generator->m_yieldfrom);
#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Null return, yield from removal:", generator);
                PRINT_COROUTINE_VALUE("yieldfrom", generator->m_yieldfrom);
#endif
                Py_DECREF(generator->m_yieldfrom);
                generator->m_yieldfrom = NULL;
            }

            PyObject *val;
            if (_PyGen_FetchStopIterationValue(&val) == 0) {
                CHECK_OBJECT(val);

#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Sending return value into ourselves", generator);
                PRINT_COROUTINE_VALUE("value", val);
                PRINT_NEW_LINE();
#endif

                ret = _Nuitka_Generator_send(generator, val, NULL, NULL, NULL);
            } else {
#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Sending exception value into ourselves", generator);
                PRINT_CURRENT_EXCEPTION();
                PRINT_NEW_LINE();
#endif
                ret = _Nuitka_Generator_send(generator, NULL, NULL, NULL, NULL);
            }

#if _DEBUG_GENERATOR
            PRINT_GENERATOR_STATUS("Leave with value/exception from sending into ourselves:", generator);
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        } else {
#if _DEBUG_GENERATOR
            PRINT_GENERATOR_STATUS("Leave with return value:", generator);
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        }

        return ret;
    }

throw_here:
#endif

    // We continue to have exception ownership here.

    if (unlikely(_Nuitka_Generator_check_throw2(&exception_type, &exception_value, &exception_tb) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw2 already.
        return NULL;
    }

    if (generator->m_status == status_Running) {
        // Passing exception ownership to _Nuitka_Generator_send
        PyObject *result = _Nuitka_Generator_send(generator, NULL, exception_type, exception_value, exception_tb);

        if (result == NULL) {
            if (GET_ERROR_OCCURRED() == NULL) {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
            }
        }

        return result;
    } else if (generator->m_status == status_Finished) {
        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

        return NULL;
    } else {
        if (exception_tb == NULL) {
            // TODO: Our compiled objects really need a way to store common
            // stuff in a "shared" part across all instances, and outside of
            // run time, so we could reuse this.
            struct Nuitka_FrameObject *frame = MAKE_FUNCTION_FRAME(generator->m_code_object, generator->m_module, 0);
            exception_tb = MAKE_TRACEBACK(frame, generator->m_code_object->co_firstlineno);
            Py_DECREF(frame);
        }

        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

        generator->m_status = status_Finished;

        return NULL;
    }
}

static PyObject *Nuitka_Generator_throw(struct Nuitka_GeneratorObject *generator, PyObject *args) {
    PyObject *exception_type;
    PyObject *exception_value = NULL;
    PyTracebackObject *exception_tb = NULL;

    // This takes no references, that is for us to do.
    int res = PyArg_UnpackTuple(args, "throw", 1, 3, &exception_type, &exception_value, &exception_tb);

    if (unlikely(res == 0)) {
        return NULL;
    }

    // Handing ownership of exception over, we need not release it ourselves
    Py_INCREF(exception_type);
    Py_XINCREF(exception_value);
    Py_XINCREF(exception_tb);

    PyObject *result = _Nuitka_Generator_throw2(generator, exception_type, exception_value, exception_tb);

    if (result == NULL) {
        if (GET_ERROR_OCCURRED() == NULL) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        }
    }

#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Leave", generator);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_COROUTINE_VALUE("return value", result);
    PRINT_CURRENT_EXCEPTION();
#endif

    return result;
}

#if PYTHON_VERSION >= 0x340
static void Nuitka_Generator_tp_finalizer(struct Nuitka_GeneratorObject *generator) {
    if (generator->m_status != status_Running) {
        return;
    }

    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

    bool close_result = _Nuitka_Generator_close(generator);

    if (unlikely(close_result == false)) {
        PyErr_WriteUnraisable((PyObject *)generator);
    }

    /* Restore the saved exception if any. */
    RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
}
#endif

#define MAX_GENERATOR_FREE_LIST_COUNT 100
static struct Nuitka_GeneratorObject *free_list_generators = NULL;
static int free_list_generators_count = 0;

static void Nuitka_Generator_tp_dealloc(struct Nuitka_GeneratorObject *generator) {
    // Revive temporarily.
    assert(Py_REFCNT(generator) == 0);
    Py_SET_REFCNT(generator, 1);

    // Save the current exception, if any, we must preserve it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

    if (generator->m_status == status_Running) {
        bool close_result = _Nuitka_Generator_close(generator);
        CHECK_OBJECT(generator);

        if (unlikely(close_result == false)) {
            PyErr_WriteUnraisable((PyObject *)generator);
        }
    }

    Nuitka_Generator_release_closure(generator);

    // Allow for above code to resurrect the generator.
    Py_SET_REFCNT(generator, Py_REFCNT(generator) - 1);
    if (Py_REFCNT(generator) >= 1) {
        return;
    }

    if (generator->m_frame != NULL) {
#if PYTHON_VERSION >= 0x340
        Nuitka_SetFrameGenerator(generator->m_frame, NULL);
#endif
        Py_DECREF(generator->m_frame);
        generator->m_frame = NULL;
    }

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack(generator);

    if (generator->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)generator);
        assert(!ERROR_OCCURRED());
    }

    Py_DECREF(generator->m_name);

#if PYTHON_VERSION >= 0x350
    Py_DECREF(generator->m_qualname);
#endif

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_generators, generator, MAX_GENERATOR_FREE_LIST_COUNT);

    RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
}

static long Nuitka_Generator_tp_hash(struct Nuitka_GeneratorObject *generator) { return generator->m_counter; }

static PyObject *Nuitka_Generator_get_name(struct Nuitka_GeneratorObject *generator) {
    PyObject *result = generator->m_name;
    Py_INCREF(result);
    return result;
}

#if PYTHON_VERSION >= 0x350
static int Nuitka_Generator_set_name(struct Nuitka_GeneratorObject *generator, PyObject *value) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__name__ must be set to a string object");

        return -1;
    }

    PyObject *tmp = generator->m_name;
    Py_INCREF(value);
    generator->m_name = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Generator_get_qualname(struct Nuitka_GeneratorObject *generator) {
    PyObject *result = generator->m_qualname;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Generator_set_qualname(struct Nuitka_GeneratorObject *generator, PyObject *value) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__qualname__ must be set to a string object");

        return -1;
    }

    PyObject *tmp = generator->m_qualname;
    Py_INCREF(value);
    generator->m_qualname = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Generator_get_yieldfrom(struct Nuitka_GeneratorObject *generator) {
    if (generator->m_yieldfrom) {
        Py_INCREF(generator->m_yieldfrom);
        return generator->m_yieldfrom;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

#endif

static PyObject *Nuitka_Generator_get_code(struct Nuitka_GeneratorObject *generator) {
    PyObject *result = (PyObject *)generator->m_code_object;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Generator_set_code(struct Nuitka_GeneratorObject *generator, PyObject *value) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "gi_code is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Generator_get_frame(struct Nuitka_GeneratorObject *generator) {
    PyObject *result;

    if (generator->m_frame) {
        result = (PyObject *)generator->m_frame;
    } else {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Generator_set_frame(struct Nuitka_GeneratorObject *generator, PyObject *value) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "gi_frame is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Generator_get_running(struct Nuitka_GeneratorObject *generator) {
    PyObject *result;

/* The type of "gi_running" changed in Python3. */
#if PYTHON_VERSION < 0x300
    result = PyInt_FromLong(generator->m_running);
#else
    result = BOOL_FROM(generator->m_running != 0);
    Py_INCREF(result);
#endif
    return result;
}

static int Nuitka_Generator_set_running(struct Nuitka_GeneratorObject *generator, PyObject *value) {
#if PYTHON_VERSION < 0x300
    PyObject *exception_type = PyExc_TypeError;
#else
    PyObject *exception_type = PyExc_AttributeError;
#endif

#if !defined(_NUITKA_FULL_COMPAT) || PYTHON_VERSION >= 0x3a0
    SET_CURRENT_EXCEPTION_TYPE0_STR(exception_type, "attribute 'gi_running' of 'generator' objects is not writable");
#else
    SET_CURRENT_EXCEPTION_TYPE0_STR(exception_type, "readonly attribute");
#endif

    return -1;
}

static PyGetSetDef Nuitka_Generator_getsetlist[] = {
#if PYTHON_VERSION < 0x350
    {(char *)"__name__", (getter)Nuitka_Generator_get_name, NULL, NULL},
#else
    {(char *)"__name__", (getter)Nuitka_Generator_get_name, (setter)Nuitka_Generator_set_name, NULL},
    {(char *)"__qualname__", (getter)Nuitka_Generator_get_qualname, (setter)Nuitka_Generator_set_qualname, NULL},
    {(char *)"gi_yieldfrom", (getter)Nuitka_Generator_get_yieldfrom, NULL, NULL},
#endif
    {(char *)"gi_code", (getter)Nuitka_Generator_get_code, (setter)Nuitka_Generator_set_code, NULL},
    {(char *)"gi_frame", (getter)Nuitka_Generator_get_frame, (setter)Nuitka_Generator_set_frame, NULL},
    {(char *)"gi_running", (getter)Nuitka_Generator_get_running, (setter)Nuitka_Generator_set_running, NULL},

    {NULL}};

static PyMethodDef Nuitka_Generator_methods[] = {{"send", (PyCFunction)Nuitka_Generator_send, METH_O, NULL},
                                                 {"throw", (PyCFunction)Nuitka_Generator_throw, METH_VARARGS, NULL},
                                                 {"close", (PyCFunction)Nuitka_Generator_close, METH_NOARGS, NULL},
                                                 {NULL}};

// This is only used.
#if PYTHON_VERSION >= 0x3a0
static PyAsyncMethods Nuitka_Generator_as_async = {
    NULL, /* am_await */
    NULL, /* am_aiter */
    NULL, /* am_anext */
    NULL  // TODO: have this too, (sendfunc)_Nuitka_Generator_amsend /* am_anext */
};
#endif

#include <structmember.h>

PyTypeObject Nuitka_Generator_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_generator", /* tp_name */
    sizeof(struct Nuitka_GeneratorObject),               /* tp_basicsize */
    sizeof(struct Nuitka_CellObject *),                  /* tp_itemsize */
    (destructor)Nuitka_Generator_tp_dealloc,             /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
#if PYTHON_VERSION < 0x3a0
    0, /* tp_as_async */
#else
    &Nuitka_Generator_as_async, /* tp_as_async */
#endif
    (reprfunc)Nuitka_Generator_tp_repr, /* tp_repr */
    0,                                  /* tp_as_number */
    0,                                  /* tp_as_sequence */
    0,                                  /* tp_as_mapping */
    (hashfunc)Nuitka_Generator_tp_hash, /* tp_hash */
    0,                                  /* tp_call */
    0,                                  /* tp_str */
    PyObject_GenericGetAttr,            /* tp_getattro */
    0,                                  /* tp_setattro */
    0,                                  /* tp_as_buffer */
#if PYTHON_VERSION < 0x340
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
#else
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE,
#endif
    /* tp_flags */
    0,                                                   /* tp_doc */
    (traverseproc)Nuitka_Generator_tp_traverse,          /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    offsetof(struct Nuitka_GeneratorObject, m_weakrefs), /* tp_weaklistoffset */
    PyObject_SelfIter,                                   /* tp_iter */
    (iternextfunc)Nuitka_Generator_tp_iternext,          /* tp_iternext */
    Nuitka_Generator_methods,                            /* tp_methods */
    NULL,                                                /* tp_members */
    Nuitka_Generator_getsetlist,                         /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    0,                                                   /* tp_init */
    0,                                                   /* tp_alloc */
    0,                                                   /* tp_new */
    0,                                                   /* tp_free */
    0,                                                   /* tp_is_gc */
    0,                                                   /* tp_bases */
    0,                                                   /* tp_mro */
    0,                                                   /* tp_cache */
    0,                                                   /* tp_subclasses */
    0,                                                   /* tp_weaklist */
    0,                                                   /* tp_del */
    0                                                    /* tp_version_tag */
#if PYTHON_VERSION >= 0x340
    ,
    (destructor)Nuitka_Generator_tp_finalizer /* tp_finalize */
#endif
};

#if PYTHON_VERSION >= 0x350
static void _initCompiledCoroutineTypes();
#endif
#if PYTHON_VERSION >= 0x360
static void _initCompiledAsyncgenTypes();
#endif

void _initCompiledGeneratorType(void) {
    Nuitka_Generator_Type.tp_base = &PyGen_Type;

    PyType_Ready(&Nuitka_Generator_Type);

    // Be a paranoid subtype of uncompiled function, we want nothing shared.
    assert(Nuitka_Generator_Type.tp_doc != PyGen_Type.tp_doc || PyGen_Type.tp_doc == NULL);
    assert(Nuitka_Generator_Type.tp_traverse != PyGen_Type.tp_traverse);
    assert(Nuitka_Generator_Type.tp_clear != PyGen_Type.tp_clear || PyGen_Type.tp_clear == NULL);
    assert(Nuitka_Generator_Type.tp_richcompare != PyGen_Type.tp_richcompare || PyGen_Type.tp_richcompare == NULL);
    assert(Nuitka_Generator_Type.tp_iter != PyGen_Type.tp_iter || PyGen_Type.tp_iter == PyObject_SelfIter);
    assert(Nuitka_Generator_Type.tp_iternext != PyGen_Type.tp_iternext || PyGen_Type.tp_iternext == NULL);
#if PYTHON_VERSION >= 0x350
    assert(Nuitka_Generator_Type.tp_as_async != PyGen_Type.tp_as_async || PyGen_Type.tp_as_async == NULL);
#endif
    assert(Nuitka_Generator_Type.tp_methods != PyGen_Type.tp_methods);
    assert(Nuitka_Generator_Type.tp_members != PyGen_Type.tp_members);
    assert(Nuitka_Generator_Type.tp_getset != PyGen_Type.tp_getset);
    assert(Nuitka_Generator_Type.tp_base != PyGen_Type.tp_base);
    assert(Nuitka_Generator_Type.tp_dict != PyGen_Type.tp_dict);
    assert(Nuitka_Generator_Type.tp_descr_get != PyGen_Type.tp_descr_get || PyGen_Type.tp_descr_get == NULL);

    assert(Nuitka_Generator_Type.tp_descr_set != PyGen_Type.tp_descr_set || PyGen_Type.tp_descr_set == NULL);
    assert(Nuitka_Generator_Type.tp_dictoffset != PyGen_Type.tp_dictoffset || PyGen_Type.tp_dictoffset == 0);
    // TODO: These get changed and into the same thing, not sure what to compare against, project something
    // assert(Nuitka_Generator_Type.tp_init != PyGen_Type.tp_init || PyGen_Type.tp_init == NULL);
    // assert(Nuitka_Generator_Type.tp_alloc != PyGen_Type.tp_alloc || PyGen_Type.tp_alloc == NULL);
    // assert(Nuitka_Generator_Type.tp_new != PyGen_Type.tp_new || PyGen_Type.tp_new == NULL);
    // assert(Nuitka_Generator_Type.tp_free != PyGen_Type.tp_free || PyGen_Type.tp_free == NULL);
    assert(Nuitka_Generator_Type.tp_bases != PyGen_Type.tp_bases);
    assert(Nuitka_Generator_Type.tp_mro != PyGen_Type.tp_mro);
    assert(Nuitka_Generator_Type.tp_cache != PyGen_Type.tp_cache || PyGen_Type.tp_cache == NULL);
    assert(Nuitka_Generator_Type.tp_subclasses != PyGen_Type.tp_subclasses || PyGen_Type.tp_cache == NULL);
    assert(Nuitka_Generator_Type.tp_weaklist != PyGen_Type.tp_weaklist);
    assert(Nuitka_Generator_Type.tp_del != PyGen_Type.tp_del || PyGen_Type.tp_del == NULL);
#if PYTHON_VERSION >= 0x340
    assert(Nuitka_Generator_Type.tp_finalize != PyGen_Type.tp_finalize || PyGen_Type.tp_finalize == NULL);
#endif

#if PYTHON_VERSION >= 0x350
    // Also initialize coroutines if necessary
    _initCompiledCoroutineTypes();
#endif

#if PYTHON_VERSION >= 0x360
    // Also initialize asyncgen if necessary
    _initCompiledAsyncgenTypes();
#endif
}

PyObject *Nuitka_Generator_New(generator_code code, PyObject *module, PyObject *name,
#if PYTHON_VERSION >= 0x350
                               PyObject *qualname,
#endif
                               PyCodeObject *code_object, struct Nuitka_CellObject **closure, Py_ssize_t closure_given,
                               Py_ssize_t heap_storage_size) {
    struct Nuitka_GeneratorObject *result;

    // TODO: Change the var part of the type to 1 maybe
    Py_ssize_t full_size = closure_given + (heap_storage_size + sizeof(void *) - 1) / sizeof(void *);

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_generators, struct Nuitka_GeneratorObject, Nuitka_Generator_Type, full_size);

    // For quicker access of generator heap.
    result->m_heap_storage = &result->m_closure[closure_given];

    assert(result != NULL);
    CHECK_OBJECT(result);

    assert(Py_SIZE(result) >= closure_given);

    result->m_code = (void *)code;

    CHECK_OBJECT(module);
    result->m_module = module;

    CHECK_OBJECT(name);
    result->m_name = name;
    Py_INCREF(name);

#if PYTHON_VERSION >= 0x350
    // The "qualname" defaults to NULL for most compact C code.
    if (qualname == NULL) {
        qualname = name;
    }
    CHECK_OBJECT(qualname);

    result->m_qualname = qualname;
    Py_INCREF(qualname);
#endif

#if PYTHON_VERSION >= 0x300
    result->m_yieldfrom = NULL;
#endif

    memcpy(&result->m_closure[0], closure, closure_given * sizeof(struct Nuitka_CellObject *));
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = false;

    result->m_yield_return_index = 0;

#if PYTHON_VERSION >= 0x300
    result->m_returned = NULL;
#endif

    result->m_frame = NULL;
    result->m_code_object = code_object;

#if PYTHON_VERSION >= 0x370
    result->m_exc_state = Nuitka_ExceptionStackItem_Empty;
#endif

    static long Nuitka_Generator_counter = 0;
    result->m_counter = Nuitka_Generator_counter++;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

static PyObject *_EMPTY_GENERATOR_CONTEXT(struct Nuitka_GeneratorObject *generator, PyObject *yield_return_value) {
    return NULL;
}

PyObject *Nuitka_Generator_NewEmpty(PyObject *module, PyObject *name,
#if PYTHON_VERSION >= 0x350
                                    PyObject *qualname,
#endif
                                    PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                    Py_ssize_t closure_given) {
    return Nuitka_Generator_New(_EMPTY_GENERATOR_CONTEXT, module, name,
#if PYTHON_VERSION >= 0x350
                                qualname,
#endif
                                code_object, closure, closure_given, 0);
}

// Chain coroutine code to generator code, as it uses same functions, and then we can
// have some things static if both are in the same compilation unit. This also loads
// the asyncgen for 3.6 and higher.
#if PYTHON_VERSION >= 0x350
#include "CompiledCoroutineType.c"
#endif

// Chain frames to generator and asyncgen code, as they need to close them with access
// to best functions.
#include "CompiledFrameType.c"