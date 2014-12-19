//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "nuitka/prelude.hpp"

static PyObject *Nuitka_Generator_tp_repr( Nuitka_GeneratorObject *generator )
{
#if PYTHON_VERSION < 300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
        "<compiled generator object %s at %p>",
        Nuitka_String_AsString( generator->m_name ),
        generator
    );
}

static long Nuitka_Generator_tp_traverse( PyObject *function, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting owned objects and/or if it
    // could be NULL instead. The methodobject visits its self and module. I
    // understand this is probably so that back references of this function to
    // its upper do not make it stay in the memory. A specific test if that
    // works might be needed.
    return 0;
}


static PyObject *Nuitka_Generator_send( Nuitka_GeneratorObject *generator, PyObject *value )
{
    if ( generator->m_status == status_Unused && value != NULL && value != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "can't send non-None value to a just-started generator" );
        return NULL;
    }

    if ( generator->m_status != status_Finished )
    {
        PyThreadState *thread_state = PyThreadState_GET();

#if PYTHON_VERSION < 300
        PyObject *saved_exception_type = INCREASE_REFCOUNT_X( thread_state->exc_type );
        PyObject *saved_exception_value = INCREASE_REFCOUNT_X( thread_state->exc_value );
        PyTracebackObject *saved_exception_traceback = INCREASE_REFCOUNT_X( (PyTracebackObject *)thread_state->exc_traceback );
#endif

        if ( generator->m_running )
        {
            PyErr_Format( PyExc_ValueError, "generator already executing" );
            return NULL;
        }

        if ( generator->m_status == status_Unused )
        {
            // Prepare the generator context to run.
            int res = prepareFiber( &generator->m_yielder_context, generator->m_code, (uintptr_t)generator );

            if ( res != 0 )
            {
                PyErr_Format( PyExc_MemoryError, "generator cannot be allocated" );
                return NULL;
            }

            generator->m_status = status_Running;
        }

        generator->m_yielded = value;

        // Put the generator back on the frame stack.
        PyFrameObject *return_frame = thread_state->frame;
#ifndef __NUITKA_NO_ASSERT__
        if ( return_frame )
        {
            assertFrameObject( return_frame );
        }
#endif

        if ( generator->m_frame )
        {
            // It would be nice if our frame were still alive. Nobody had the
            // right to release it.
            assertFrameObject( generator->m_frame );

            // It's not supposed to be on the top right now.
            assert( return_frame != generator->m_frame );

            Py_XINCREF( return_frame );
            generator->m_frame->f_back = return_frame;

            thread_state->frame = generator->m_frame;
        }

        // Continue the yielder function while preventing recursion.
        generator->m_running = true;

        swapFiber( &generator->m_caller_context, &generator->m_yielder_context );

        generator->m_running = false;

        thread_state = PyThreadState_GET();

        // Remove the generator from the frame stack.
        if ( generator->m_frame )
        {
            assert( thread_state->frame == generator->m_frame );
            assertFrameObject( generator->m_frame );

            Py_CLEAR( generator->m_frame->f_back );
        }

        thread_state->frame = return_frame;

        if ( generator->m_yielded == NULL )
        {
            assert( ERROR_OCCURED() );

            generator->m_status = status_Finished;

            Py_XDECREF( generator->m_frame );
            generator->m_frame = NULL;

            if ( generator->m_context )
            {
                // Surpressing exception in cleanup, to restore later before
                // return.
                generator->m_cleanup( generator->m_context );
                generator->m_context = NULL;
            }

            assert( ERROR_OCCURED() );

#if PYTHON_VERSION < 300
            Py_XDECREF( saved_exception_type );
            Py_XDECREF( saved_exception_value );
            Py_XDECREF( saved_exception_traceback );
#endif
            return NULL;
        }
        else
        {
#if PYTHON_VERSION < 300
            SET_CURRENT_EXCEPTION( saved_exception_type, saved_exception_value, saved_exception_traceback );
#endif

            return generator->m_yielded;
        }
    }
    else
    {
        PyErr_SetObject( PyExc_StopIteration, (PyObject *)NULL );

        return NULL;
    }
}

static PyObject *Nuitka_Generator_tp_iternext( Nuitka_GeneratorObject *generator )
{
    return Nuitka_Generator_send( generator, Py_None );
}

#if PYTHON_VERSION < 340
static
#endif
PyObject *Nuitka_Generator_close( Nuitka_GeneratorObject *generator, PyObject *args )
{
    if ( generator->m_status == status_Running )
    {
        generator->m_exception_type = INCREASE_REFCOUNT( PyExc_GeneratorExit );
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        PyObject *result = Nuitka_Generator_send( generator, Py_None );

        if (unlikely( result ))
        {
            Py_DECREF( result );

            PyErr_Format( PyExc_RuntimeError, "generator ignored GeneratorExit" );
            return NULL;
        }
        else if ( PyErr_ExceptionMatches( PyExc_StopIteration ) || PyErr_ExceptionMatches( PyExc_GeneratorExit ) )
        {
            PyErr_Clear();
            return INCREASE_REFCOUNT( Py_None );
        }
        else
        {
            assert( ERROR_OCCURED() );

            return NULL;
        }
    }

    return INCREASE_REFCOUNT( Py_None );
}

#if PYTHON_VERSION >= 340
static void Nuitka_Generator_tp_del( Nuitka_GeneratorObject *generator )
{
    if ( generator->m_status != status_Running )
    {
        return;
    }

    // Revive temporarily.
    assert( Py_REFCNT( generator ) == 0 );
    Py_REFCNT( generator ) = 1;

    PyObject *error_type, *error_value, *error_traceback;
    PyErr_Fetch( &error_type, &error_value, &error_traceback );

    PyObject *result = Nuitka_Generator_close( generator, NULL );

    if (unlikely( result == NULL ))
    {
        PyErr_WriteUnraisable( (PyObject *)generator );
    }
    else
    {
        Py_DECREF( result );
    }

    /* Restore the saved exception. */
    PyErr_Restore( error_type, error_value, error_traceback );

    assert( Py_REFCNT( generator ) > 0 );
    Py_REFCNT( generator ) -= 1;

    Py_ssize_t refcnt = Py_REFCNT( generator );

    if (unlikely( refcnt != 0 ))
    {
        _Py_NewReference( (PyObject *)generator );
        Py_REFCNT( generator ) = refcnt;

        _Py_DEC_REFTOTAL;
    }
}
#endif

static void Nuitka_Generator_tp_dealloc( Nuitka_GeneratorObject *generator )
{
    assert( Py_REFCNT( generator ) == 0 );
    Py_REFCNT( generator ) = 1;

    // Save the current exception, if any, we must preserve it.
    PyObject *save_exception_type, *save_exception_value, *save_exception_tb;
    PyErr_Fetch(&save_exception_type, &save_exception_value, &save_exception_tb);

    PyObject *close_result = Nuitka_Generator_close( generator, NULL );

    if (unlikely( close_result == NULL ))
    {
        PyErr_WriteUnraisable( (PyObject *)generator );
    }
    else
    {
        Py_DECREF( close_result );
    }

    if ( generator->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)generator );
    }

    if ( generator->m_context )
    {
        generator->m_cleanup( generator->m_context );
    }

    Py_DECREF( generator->m_name );

    Py_XDECREF( generator->m_frame );

    assert( Py_REFCNT( generator ) == 1 );
    Py_REFCNT( generator ) = 0;

    releaseFiber( &generator->m_yielder_context );

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack( generator );

    PyObject_GC_Del( generator );
    PyErr_Restore( save_exception_type, save_exception_value, save_exception_tb );
}

static PyObject *Nuitka_Generator_throw( Nuitka_GeneratorObject *generator, PyObject *args )
{
    assert(generator->m_exception_type == NULL);
    assert(generator->m_exception_value == NULL);
    assert(generator->m_exception_tb == NULL);

    int res = PyArg_UnpackTuple( args, "throw", 1, 3, &generator->m_exception_type, &generator->m_exception_value, (PyObject **)&generator->m_exception_tb );

    if (unlikely( res == 0 ))
    {
        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        return NULL;
    }

    if ( (PyObject *)generator->m_exception_tb == Py_None )
    {
        generator->m_exception_tb = NULL;
    }
    else if ( generator->m_exception_tb != NULL && !PyTraceBack_Check( generator->m_exception_tb ) )
    {
        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        PyErr_Format( PyExc_TypeError, "throw() third argument must be a traceback object" );
        return NULL;
    }

    if ( PyExceptionClass_Check( generator->m_exception_type ))
    {
        Py_INCREF( generator->m_exception_type );
        Py_XINCREF( generator->m_exception_value );
        Py_XINCREF( generator->m_exception_tb );

        NORMALIZE_EXCEPTION( &generator->m_exception_type, &generator->m_exception_value, &generator->m_exception_tb );
    }
    else if ( PyExceptionInstance_Check( generator->m_exception_type ) )
    {
        if ( generator->m_exception_value && generator->m_exception_value != Py_None )
        {
            generator->m_exception_type = NULL;
            generator->m_exception_value = NULL;
            generator->m_exception_tb = NULL;

            PyErr_Format( PyExc_TypeError, "instance exception may not have a separate value" );
            return NULL;
        }
        generator->m_exception_value = generator->m_exception_type;
        Py_INCREF( generator->m_exception_value );
        generator->m_exception_type = PyExceptionInstance_Class( generator->m_exception_type );
        Py_INCREF( generator->m_exception_type );
        Py_XINCREF( generator->m_exception_tb );
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
#if PYTHON_VERSION < 300
            "exceptions must be classes, or instances, not %s",
#else
            "exceptions must be classes or instances deriving from BaseException, not %s",
#endif
            Py_TYPE( generator->m_exception_type )->tp_name
        );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        return NULL;
    }

    if ( ( generator->m_exception_tb != NULL ) && ( (PyObject *)generator->m_exception_tb != Py_None ) && ( !PyTraceBack_Check( generator->m_exception_tb ) ) )
    {
        PyErr_Format( PyExc_TypeError, "throw() third argument must be a traceback object" );
        return NULL;
    }

    if ( generator->m_status != status_Finished )
    {
        PyObject *result = Nuitka_Generator_send( generator, Py_None );

        return result;
    }
    else
    {
        PyErr_Restore( generator->m_exception_type, generator->m_exception_value, (PyObject *)generator->m_exception_tb );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        return NULL;
    }
}

static PyObject *Nuitka_Generator_get_name( Nuitka_GeneratorObject *generator )
{
    return INCREASE_REFCOUNT( generator->m_name );
}

static PyObject *Nuitka_Generator_get_code( Nuitka_GeneratorObject *object )
{
    return INCREASE_REFCOUNT( (PyObject *)object->m_code_object );
}

static int Nuitka_Generator_set_code( Nuitka_GeneratorObject *object, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "gi_code is not writable in Nuitka" );
    return -1;
}

static PyObject *Nuitka_Generator_get_frame( Nuitka_GeneratorObject *object )
{
    if ( object->m_frame )
    {
        return INCREASE_REFCOUNT( (PyObject *)object->m_frame );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_None );
    }
}

static int Nuitka_Generator_set_frame( Nuitka_GeneratorObject *object, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "gi_frame is not writable in Nuitka" );
    return -1;
}

static PyGetSetDef Nuitka_Generator_getsetlist[] =
{
    { (char *)"__name__", (getter)Nuitka_Generator_get_name, NULL, NULL },
    { (char *)"gi_code",  (getter)Nuitka_Generator_get_code, (setter)Nuitka_Generator_set_code, NULL },
    { (char *)"gi_frame", (getter)Nuitka_Generator_get_frame, (setter)Nuitka_Generator_set_frame, NULL },

    { NULL }
};

static PyMethodDef Nuitka_Generator_methods[] =
{
    { "send",  (PyCFunction)Nuitka_Generator_send,  METH_O, NULL },
    { "throw", (PyCFunction)Nuitka_Generator_throw, METH_VARARGS, NULL },
    { "close", (PyCFunction)Nuitka_Generator_close, METH_NOARGS, NULL },
    { NULL }
};

#include <structmember.h>

static PyMemberDef Nuitka_Generator_members[] =
{
    { (char *)"gi_running", T_INT, offsetof( Nuitka_GeneratorObject, m_running ), READONLY },
    { NULL }
};


PyTypeObject Nuitka_Generator_Type =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_generator",                            // tp_name
    sizeof(Nuitka_GeneratorObject),                  // tp_basicsize
    0,                                               // tp_itemsize
    (destructor)Nuitka_Generator_tp_dealloc,         // tp_dealloc
    0,                                               // tp_print
    0,                                               // tp_getattr
    0,                                               // tp_setattr
    0,                                               // tp_compare
    (reprfunc)Nuitka_Generator_tp_repr,              // tp_repr
    0,                                               // tp_as_number
    0,                                               // tp_as_sequence
    0,                                               // tp_as_mapping
    0,                                               // tp_hash
    0,                                               // tp_call
    0,                                               // tp_str
    PyObject_GenericGetAttr,                         // tp_getattro
    0,                                               // tp_setattro
    0,                                               // tp_as_buffer
#if PYTHON_VERSION < 340
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
#else
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE,
#endif
                                                     // tp_flags
    0,                                               // tp_doc
    (traverseproc)Nuitka_Generator_tp_traverse,      // tp_traverse
    0,                                               // tp_clear
    0,                                               // tp_richcompare
    offsetof( Nuitka_GeneratorObject, m_weakrefs ),  // tp_weaklistoffset
    PyObject_SelfIter,                               // tp_iter
    (iternextfunc)Nuitka_Generator_tp_iternext,      // tp_iternext
    Nuitka_Generator_methods,                        // tp_methods
    Nuitka_Generator_members,                        // tp_members
    Nuitka_Generator_getsetlist,                     // tp_getset
    0,                                               // tp_base
    0,                                               // tp_dict
    0,                                               // tp_descr_get
    0,                                               // tp_descr_set
    0,                                               // tp_dictoffset
    0,                                               // tp_init
    0,                                               // tp_alloc
    0,                                               // tp_new
    0,                                               // tp_free
    0,                                               // tp_is_gc
    0,                                               // tp_bases
    0,                                               // tp_mro
    0,                                               // tp_cache
    0,                                               // tp_subclasses
    0,                                               // tp_weaklist
#if PYTHON_VERSION < 340
    0                                                // tp_del
#else
    (destructor)Nuitka_Generator_tp_del
#endif
};

PyObject *Nuitka_Generator_New( yielder_func code, PyObject *name, PyCodeObject *code_object, void *context, releaser cleanup )
{
    Nuitka_GeneratorObject *result = PyObject_GC_New( Nuitka_GeneratorObject, &Nuitka_Generator_Type );

    if (unlikely( result == NULL ))
    {
        PyErr_Format(
            PyExc_RuntimeError,
            "cannot create genexpr %s",
            Nuitka_String_AsString( name )
        );

        return NULL;
    }

    result->m_code = (void *)code;

    result->m_name = INCREASE_REFCOUNT( name );

    result->m_context = context;
    result->m_cleanup = cleanup;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = false;

    result->m_exception_type = NULL;
    result->m_exception_value = NULL;
    result->m_exception_tb = NULL;

    result->m_yielded = NULL;

    result->m_frame = NULL;
    result->m_code_object = code_object;

    initFiber( &result->m_yielder_context );

    Nuitka_GC_Track( result );
    return (PyObject *)result;
}

PyObject *Nuitka_Generator_New( yielder_func code, PyObject *name, PyCodeObject *code_object )
{
    return Nuitka_Generator_New( code, name, code_object, NULL, NULL );
}

#if PYTHON_VERSION >= 330

// This is for CPython iterator objects, the respective code is not exported as
// API, so we need to redo it. This is an re-implementation that closely follows
// what it does. It's unrelated to compiled generators.
PyObject *PyGen_Send( PyGenObject *generator, PyObject *arg )
{
    if (unlikely( generator->gi_running ))
    {
        PyErr_SetString( PyExc_ValueError, "generator already executing" );
        return NULL;
    }

    PyFrameObject *frame = generator->gi_frame;

    if ( frame == NULL || frame->f_stacktop == NULL )
    {
        // Set exception if called from send()
        if ( arg != NULL )
        {
            PyErr_SetNone( PyExc_StopIteration );
        }

        return NULL;
    }

    if ( frame->f_lasti == -1 )
    {
        if (unlikely( arg && arg != Py_None ))
        {
            PyErr_SetString(
                PyExc_TypeError,
                "can't send non-None value to a just-started generator"
            );

            return NULL;
        }
    }
    else
    {
        // Put arg on top of the value stack
        PyObject *tmp = arg ? arg : Py_None;
        *(frame->f_stacktop++) = INCREASE_REFCOUNT( tmp );
    }

    // Generators always return to their most recent caller, not necessarily
    // their creator.
    PyThreadState *tstate = PyThreadState_GET();
    Py_XINCREF( tstate->frame );

    assert( frame->f_back == NULL );
    frame->f_back = tstate->frame;

    generator->gi_running = 1;
    PyObject *result = PyEval_EvalFrameEx( frame, 0 );
    generator->gi_running = 0;

    // Don't keep the reference to f_back any longer than necessary.  It
    // may keep a chain of frames alive or it could create a reference
    // cycle.
    assert( frame->f_back == tstate->frame );
    Py_CLEAR( frame->f_back );

    // If the generator just returned (as opposed to yielding), signal that the
    // generator is exhausted.
    if ( result && frame->f_stacktop == NULL )
    {
        if ( result == Py_None )
        {
            PyErr_SetNone( PyExc_StopIteration );
        }
        else {
            PyObject *e = PyObject_CallFunctionObjArgs(
                PyExc_StopIteration,
                result,
                NULL
            );

            if ( e != NULL )
            {
                PyErr_SetObject( PyExc_StopIteration, e );
                Py_DECREF( e );
            }
        }

        Py_CLEAR( result );
    }

    if ( result == NULL || frame->f_stacktop == NULL )
    {
        // Generator is finished, remove exception from frame before releasing
        // it.
        PyObject *type = frame->f_exc_type;
        PyObject *value = frame->f_exc_value;
        PyObject *traceback = frame->f_exc_traceback;
        frame->f_exc_type = NULL;
        frame->f_exc_value = NULL;
        frame->f_exc_traceback = NULL;
        Py_XDECREF( type );
        Py_XDECREF( value );
        Py_XDECREF( traceback );

        // Now release frame.
        generator->gi_frame = NULL;
        Py_DECREF( frame );
    }

    return result;
}

#if PYTHON_VERSION >= 300

PyObject *ERROR_GET_STOP_ITERATION_VALUE()
{
    assert( PyErr_ExceptionMatches( PyExc_StopIteration ) );

    PyObject *exception_type, *exception_value, *exception_tb;
    PyErr_Fetch( &exception_type, &exception_value, &exception_tb );

    Py_DECREF( exception_type );
    Py_XDECREF( exception_tb );

    PyObject *value = NULL;

    if ( exception_value )
    {
        if ( PyErr_GivenExceptionMatches( exception_value, PyExc_StopIteration ) )
        {
            value = ((PyStopIterationObject *)exception_value)->value;
            Py_XINCREF( value );
            Py_DECREF( exception_value );
        }
        else
        {
            value = exception_value;
        }
    }

    if ( value == NULL )
    {
        value = INCREASE_REFCOUNT( Py_None );
    }

    return value;
}

static void RAISE_GENERATOR_EXCEPTION( Nuitka_GeneratorObject *generator )
{
    assertObject( generator->m_exception_type );

//    Py_INCREF( generator->m_exception_type );
//    Py_XINCREF( generator->m_exception_value );
//    Py_XINCREF( generator->m_exception_tb );

    PyErr_Restore(
        generator->m_exception_type,
        generator->m_exception_value,
        (PyObject *)generator->m_exception_tb
    );

    generator->m_exception_type = NULL;
    generator->m_exception_value = NULL;
    generator->m_exception_tb = NULL;
}

extern PyObject *ERROR_GET_STOP_ITERATION_VALUE();
extern PyObject *PyGen_Send( PyGenObject *gen, PyObject *arg );

extern PyObject *const_str_plain_send, *const_str_plain_throw, *const_str_plain_close;

PyObject *YIELD_FROM( Nuitka_GeneratorObject *generator, PyObject *value )
{
    // This is the value, propagated back and forth the sub-generator and the
    // yield from consumer.
    PyObject *send_value = Py_None;

    while( 1 )
    {
        // Send iteration value to the sub-generator, which may be a CPython
        // generator object, something with an iterator next, or a send method,
        // where the later is only required if values other than "None" need to
        // be passed in.
        PyObject *retval;

        // Exception, was thrown into us, need to send that to sub-generator.
        if ( generator->m_exception_type )
        {
            // The yielding generator is being closed, but we also are tasked to
            // immediately close the currently running sub-generator.
            if ( PyErr_GivenExceptionMatches( generator->m_exception_type, PyExc_GeneratorExit ) )
            {
                PyObject *close_method = PyObject_GetAttr( value, const_str_plain_close );

                if ( close_method )
                {
                    PyObject *close_value = PyObject_Call( close_method, const_tuple_empty, NULL );
                    Py_DECREF( close_method );

                    if (unlikely( close_value == NULL ))
                    {
                        return NULL;
                    }

                    Py_DECREF( close_value );
                }
                else if ( !PyErr_ExceptionMatches( PyExc_AttributeError ) )
                {
                    PyErr_WriteUnraisable( (PyObject *)value );
                }

                RAISE_GENERATOR_EXCEPTION( generator );
                return NULL;
            }

            PyObject *throw_method = PyObject_GetAttr( value, const_str_plain_throw );

            if ( throw_method )
            {
                retval = PyObject_CallFunctionObjArgs( throw_method, generator->m_exception_type, generator->m_exception_value, generator->m_exception_tb, NULL );
                Py_DECREF( throw_method );

                if (unlikely( send_value == NULL ))
                {
                    if ( PyErr_ExceptionMatches( PyExc_StopIteration ) )
                    {
                        return ERROR_GET_STOP_ITERATION_VALUE();
                    }

                    return NULL;
                }


                generator->m_exception_type = NULL;
                generator->m_exception_value = NULL;
                generator->m_exception_tb = NULL;
            }
            else if ( PyErr_ExceptionMatches( PyExc_AttributeError ) )
            {
                PyErr_Clear();

                RAISE_GENERATOR_EXCEPTION( generator );

                return NULL;
            }
            else
            {
                assert( ERROR_OCCURED() );

                Py_CLEAR( generator->m_exception_type );
                Py_CLEAR( generator->m_exception_value );
                Py_CLEAR( generator->m_exception_tb );

                return NULL;
            }

        }
        else if ( PyGen_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
        else if ( send_value == Py_None )
        {
            retval = Py_TYPE( value )->tp_iternext( value );
        }
        else
        {
            // Bug compatibility here, before 3.3 tuples were unrolled in calls, which is what
            // PyObject_CallMethod does.
#if PYTHON_VERSION >= 340
            retval = PyObject_CallMethodObjArgs( value, const_str_plain_send, send_value, NULL );
#else
            retval = PyObject_CallMethod( value, (char *)"send", (char *)"O", send_value );
#endif
        }

        // Check the sub-generator result
        if ( retval == NULL )
        {
            if ( !ERROR_OCCURED() )
            {
                return INCREASE_REFCOUNT( Py_None ) ;
            }

            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            if (likely( PyErr_ExceptionMatches( PyExc_StopIteration ) ))
            {
                return ERROR_GET_STOP_ITERATION_VALUE();
            }

            return NULL;
        }
        else
        {
            generator->m_yielded = retval;

            // Return to the calling context.
            swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

            send_value = generator->m_yielded;

            assertObject( send_value );
        }
    }
}

// Note: This is copy if YIELD_FROM with changes only at the end. As it's not
// easy to split up, we are going to tolerate the copy.
PyObject *YIELD_FROM_IN_HANDLER( Nuitka_GeneratorObject *generator, PyObject *value )
{
    // This is the value, propagated back and forth the sub-generator and the
    // yield from consumer.
    PyObject *send_value = Py_None;

    while( 1 )
    {
        // Send iteration value to the sub-generator, which may be a CPython
        // generator object, something with an iterator next, or a send method,
        // where the later is only required if values other than "None" need to
        // be passed in.
        PyObject *retval;

        // Exception, was thrown into us, need to send that to sub-generator.
        if ( generator->m_exception_type )
        {
            // The yielding generator is being closed, but we also are tasked to
            // immediately close the currently running sub-generator.
            if ( PyErr_GivenExceptionMatches( generator->m_exception_type, PyExc_GeneratorExit ) )
            {
                PyObject *close_method = PyObject_GetAttr( value, const_str_plain_close );

                if ( close_method )
                {
                    PyObject *close_value = PyObject_Call( close_method, const_tuple_empty, NULL );
                    Py_DECREF( close_method );

                    if (unlikely( close_value == NULL ))
                    {
                        return NULL;
                    }

                    Py_DECREF( close_value );
                }
                else if ( !PyErr_ExceptionMatches( PyExc_AttributeError ) )
                {
                    PyErr_WriteUnraisable( (PyObject *)value );
                }

                RAISE_GENERATOR_EXCEPTION( generator );
                return NULL;
            }

            PyObject *throw_method = PyObject_GetAttr( value, const_str_plain_throw );

            if ( throw_method )
            {
                retval = PyObject_CallFunctionObjArgs( throw_method, generator->m_exception_type, generator->m_exception_value, generator->m_exception_tb, NULL );
                Py_DECREF( throw_method );

                if (unlikely( send_value == NULL ))
                {
                    if ( PyErr_ExceptionMatches( PyExc_StopIteration ) )
                    {
                        return ERROR_GET_STOP_ITERATION_VALUE();
                    }

                    return NULL;
                }


                generator->m_exception_type = NULL;
                generator->m_exception_value = NULL;
                generator->m_exception_tb = NULL;
            }
            else if ( PyErr_ExceptionMatches( PyExc_AttributeError ) )
            {
                PyErr_Clear();

                RAISE_GENERATOR_EXCEPTION( generator );

                return NULL;
            }
            else
            {
                assert( ERROR_OCCURED() );

                Py_CLEAR( generator->m_exception_type );
                Py_CLEAR( generator->m_exception_value );
                Py_CLEAR( generator->m_exception_tb );

                return NULL;
            }

        }
        else if ( PyGen_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
        else if ( send_value == Py_None )
        {
            retval = Py_TYPE( value )->tp_iternext( value );
        }
        else
        {
            // Bug compatibility here, before 3.3 tuples were unrolled in calls, which is what
            // PyObject_CallMethod does.
#if PYTHON_VERSION >= 340
            retval = PyObject_CallMethodObjArgs( value, const_str_plain_send, send_value, NULL );
#else
            retval = PyObject_CallMethod( value, (char *)"send", (char *)"O", send_value );
#endif
        }

        // Check the sub-generator result
        if ( retval == NULL )
        {
            if ( !ERROR_OCCURED() )
            {
                return INCREASE_REFCOUNT( Py_None ) ;
            }

            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            if (likely( PyErr_ExceptionMatches( PyExc_StopIteration ) ))
            {
                return ERROR_GET_STOP_ITERATION_VALUE();
            }

            return NULL;
        }
        else
        {
            generator->m_yielded = retval;

            // When yielding from an exception handler in Python3, the exception
            // preserved to the frame is restore, while the current one is put there.
            PyThreadState *thread_state = PyThreadState_GET();

            PyObject *saved_exception_type = thread_state->exc_type;
            PyObject *saved_exception_value = thread_state->exc_value;
            PyObject *saved_exception_traceback = thread_state->exc_traceback;

            thread_state->exc_type = thread_state->frame->f_exc_type;
            thread_state->exc_value = thread_state->frame->f_exc_value;
            thread_state->exc_traceback = thread_state->frame->f_exc_traceback;

            thread_state->frame->f_exc_type = saved_exception_type;
            thread_state->frame->f_exc_value = saved_exception_value;
            thread_state->frame->f_exc_traceback = saved_exception_traceback;

            // Return to the calling context.
            swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

            // When returning from yield, the exception of the frame is preserved, and
            // the one that enters should be there.
            thread_state = PyThreadState_GET();

            saved_exception_type = thread_state->exc_type;
            saved_exception_value = thread_state->exc_value;
            saved_exception_traceback = thread_state->exc_traceback;

            thread_state->exc_type = thread_state->frame->f_exc_type;
            thread_state->exc_value = thread_state->frame->f_exc_value;
            thread_state->exc_traceback = thread_state->frame->f_exc_traceback;

            thread_state->frame->f_exc_type = saved_exception_type;
            thread_state->frame->f_exc_value = saved_exception_value;
            thread_state->frame->f_exc_traceback = saved_exception_traceback;

            send_value = generator->m_yielded;

            assertObject( send_value );
        }
    }
}

#endif

#endif
