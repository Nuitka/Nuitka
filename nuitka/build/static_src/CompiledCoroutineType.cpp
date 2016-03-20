//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

static PyObject *Nuitka_Coroutine_get_name( Nuitka_CoroutineObject *coroutine)
{
    return INCREASE_REFCOUNT( coroutine->m_name );
}

static int Nuitka_Coroutine_set_name( Nuitka_CoroutineObject *coroutine, PyObject *value )
{
    // Cannot be deleted, not be non-unicode value.
    if (unlikely( ( value == NULL ) || !PyUnicode_Check( value ) ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "__name__ must be set to a string object"
        );

        return -1;
    }

    PyObject *tmp = coroutine->m_name;
    Py_INCREF( value );
    coroutine->m_name = value;
    Py_DECREF( tmp );

    return 0;
}

static PyObject *Nuitka_Coroutine_get_qualname( Nuitka_CoroutineObject *coroutine )
{
    return INCREASE_REFCOUNT( coroutine->m_qualname );
}

static int Nuitka_Coroutine_set_qualname( Nuitka_CoroutineObject *coroutine, PyObject *value )
{
    // Cannot be deleted, not be non-unicode value.
    if (unlikely( ( value == NULL ) || !PyUnicode_Check( value ) ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "__qualname__ must be set to a string object"
        );

        return -1;
    }

    PyObject *tmp = coroutine->m_qualname;
    Py_INCREF( value );
    coroutine->m_qualname = value;
    Py_DECREF( tmp );

    return 0;
}

static PyObject *Nuitka_Coroutine_get_cr_await( Nuitka_CoroutineObject *coroutine )
{
    if ( coroutine->m_yieldfrom )
    {
        Py_INCREF( coroutine->m_yieldfrom );
        return coroutine->m_yieldfrom;
    }
    else
    {
        Py_INCREF( Py_None );
        return Py_None;
    }
}

static PyObject *Nuitka_Coroutine_get_code( Nuitka_CoroutineObject *coroutine )
{
    return INCREASE_REFCOUNT( (PyObject *)coroutine->m_code_object );
}

static int Nuitka_Coroutine_set_code( Nuitka_CoroutineObject *coroutine, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "cr_code is not writable in Nuitka" );
    return -1;
}

static PyObject *Nuitka_Coroutine_get_frame( Nuitka_CoroutineObject *coroutine )
{
    if ( coroutine->m_frame )
    {
        return INCREASE_REFCOUNT( (PyObject *)coroutine->m_frame );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_None );
    }
}

static int Nuitka_Coroutine_set_frame( Nuitka_CoroutineObject *coroutine, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "gi_frame is not writable in Nuitka" );
    return -1;
}


static void Nuitka_Coroutine_release_closure( Nuitka_CoroutineObject *coroutine )
{
    if ( coroutine->m_closure )
    {
        for( Py_ssize_t i = 0; i < coroutine->m_closure_given; i++ )
        {
            Py_DECREF( coroutine->m_closure[ i ] );
        }

        free( coroutine->m_closure );
        coroutine->m_closure = NULL;
    }
}


// For the coroutine object fiber entry point, we may need to follow what
// "makecontext" will support and that is only a list of integers, but we will need
// to push a pointer through it, and so it's two of them, which might be fully
// sufficient.

#ifdef _NUITKA_MAKECONTEXT_INTS
static void Nuitka_Coroutine_entry_point( int address_1, int address_2 )
{
    // Restore the pointer from integers should it be necessary, depending on
    // the platform. This requires pointers to be no larger that to "int" value.
    int addresses[2] = {
        address_1,
        address_2
    };

    Nuitka_CoroutineObject *coroutine = (Nuitka_CoroutineObject *)*(uintptr_t *)&addresses[0];
#else
static void Nuitka_Coroutine_entry_point( Nuitka_CoroutineObject *coroutine )
{
#endif
    ((coroutine_code)coroutine->m_code)( coroutine );

    swapFiber( &coroutine->m_yielder_context, &coroutine->m_caller_context );
}


static PyObject *Nuitka_Coroutine_send( Nuitka_CoroutineObject *coroutine, PyObject *value )
{
    if ( coroutine->m_status == status_Unused && value != NULL && value != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "can't send non-None value to a just-started coroutine" );
        return NULL;
    }

    if ( coroutine->m_status != status_Finished )
    {
        PyThreadState *thread_state = PyThreadState_GET();

#if PYTHON_VERSION < 300
        PyObject *saved_exception_type = thread_state->exc_type;
        Py_XINCREF( saved_exception_type );
        PyObject *saved_exception_value = thread_state->exc_value;
        Py_XINCREF( saved_exception_value );
        PyTracebackObject *saved_exception_traceback = (PyTracebackObject *)thread_state->exc_traceback;
        Py_XINCREF( saved_exception_traceback );
#endif

        if ( coroutine->m_running )
        {
            PyErr_Format( PyExc_ValueError, "coroutine already executing" );
            return NULL;
        }

        if ( coroutine->m_status == status_Unused )
        {
            // Prepare the generator context to run.
            int res = prepareFiber( &coroutine->m_yielder_context, (void *)Nuitka_Coroutine_entry_point, (uintptr_t)coroutine );

            if ( res != 0 )
            {
                PyErr_Format( PyExc_MemoryError, "coroutine cannot be allocated" );
                return NULL;
            }

            coroutine->m_status = status_Running;
        }

        coroutine->m_yielded = value;

        // Put the generator back on the frame stack.
        PyFrameObject *return_frame = thread_state->frame;
#ifndef __NUITKA_NO_ASSERT__
        if ( return_frame )
        {
            assertFrameObject( return_frame );
        }
#endif

        if ( coroutine->m_frame )
        {
            // It would be nice if our frame were still alive. Nobody had the
            // right to release it.
            assertFrameObject( coroutine->m_frame );

            // It's not supposed to be on the top right now.
            assert( return_frame != coroutine->m_frame );

            Py_XINCREF( return_frame );
            coroutine->m_frame->f_back = return_frame;

            thread_state->frame = coroutine->m_frame;
        }

        // Continue the yielder function while preventing recursion.
        coroutine->m_running = true;

        swapFiber( &coroutine->m_caller_context, &coroutine->m_yielder_context );

        coroutine->m_running = false;

        thread_state = PyThreadState_GET();

        // Remove the generator from the frame stack.
        if ( coroutine->m_frame )
        {
            assert( thread_state->frame == coroutine->m_frame );
            assertFrameObject( coroutine->m_frame );

            Py_CLEAR( coroutine->m_frame->f_back );
        }

        thread_state->frame = return_frame;

        if ( coroutine->m_returned != NULL )
        {
            coroutine->m_status = status_Finished;

            Py_XDECREF( coroutine->m_frame );
            coroutine->m_frame = NULL;

            Nuitka_Coroutine_release_closure( coroutine );

            PyObject *result = coroutine->m_returned;

            if ( result == Py_None )
            {
                PyErr_SetObject( PyExc_StopIteration, Py_None );
                Py_DECREF( Py_None );
            }
            else
            {
                PyObject *exc_result  = PyObject_CallFunctionObjArgs( PyExc_StopIteration, result, NULL );
                Py_DECREF( result );

                if (likely( exc_result != NULL ))
                {
                    PyErr_SetObject( PyExc_StopIteration, exc_result );
                    Py_DECREF( exc_result );
                }
            }

            return NULL;
        }
        else if ( coroutine->m_yielded == NULL )
        {
            assert( ERROR_OCCURRED() );

            coroutine->m_status = status_Finished;

            Py_XDECREF( coroutine->m_frame );
            coroutine->m_frame = NULL;

            Nuitka_Coroutine_release_closure( coroutine );

            assert( ERROR_OCCURRED() );

            if ( GET_ERROR_OCCURRED() == PyExc_StopIteration )
            {
                PyObject *saved_exception_type, *saved_exception_value;
                PyTracebackObject *saved_exception_tb;

                FETCH_ERROR_OCCURRED( &saved_exception_type, &saved_exception_value, &saved_exception_tb );
                NORMALIZE_EXCEPTION( &saved_exception_type, &saved_exception_value, &saved_exception_tb );

                PyErr_Format(
                    PyExc_RuntimeError,
                    "coroutine raised StopIteration"
                );
                PyObject *exception_type, *exception_value;
                PyTracebackObject *exception_tb;

                FETCH_ERROR_OCCURRED( &exception_type, &exception_value, &exception_tb );

                RAISE_EXCEPTION_WITH_CAUSE(
                    &exception_type,
                    &exception_value,
                    &exception_tb,
                    saved_exception_value
                );

                CHECK_OBJECT( exception_value );
                CHECK_OBJECT( saved_exception_value );

                Py_INCREF( saved_exception_value );
                PyException_SetContext( exception_value, saved_exception_value );

                Py_DECREF( saved_exception_type );
                Py_XDECREF( saved_exception_tb );

                RESTORE_ERROR_OCCURRED( exception_type, exception_value, exception_tb );
            }

            return NULL;
        }
        else
        {
            return coroutine->m_yielded;
        }
    }
    else
    {
        PyErr_SetObject( PyExc_StopIteration, (PyObject *)NULL );

        return NULL;
    }
}

PyObject *Nuitka_Coroutine_close( Nuitka_CoroutineObject *coroutine, PyObject *args )
{
    if ( coroutine->m_status == status_Running )
    {
        coroutine->m_exception_type = INCREASE_REFCOUNT( PyExc_GeneratorExit );
        coroutine->m_exception_value = NULL;
        coroutine->m_exception_tb = NULL;

        PyObject *result = Nuitka_Coroutine_send( coroutine, Py_None );

        if (unlikely( result ))
        {
            Py_DECREF( result );

            PyErr_Format( PyExc_RuntimeError, "coroutine ignored GeneratorExit" );
            return NULL;
        }
        else
        {
            PyObject *error = GET_ERROR_OCCURRED();
            assert( error != NULL );

            if ( EXCEPTION_MATCH_GENERATOR( error ) )
            {
                CLEAR_ERROR_OCCURRED();

                return INCREASE_REFCOUNT( Py_None );
            }

            return NULL;
        }
    }

    return INCREASE_REFCOUNT( Py_None );
}

static PyObject *Nuitka_Coroutine_throw( Nuitka_CoroutineObject *coroutine, PyObject *args )
{
    assert( coroutine->m_exception_type == NULL );
    assert( coroutine->m_exception_value == NULL );
    assert( coroutine->m_exception_tb == NULL );

    int res = PyArg_UnpackTuple( args, "throw", 1, 3, &coroutine->m_exception_type, &coroutine->m_exception_value, (PyObject **)&coroutine->m_exception_tb );

    if (unlikely( res == 0 ))
    {
        coroutine->m_exception_type = NULL;
        coroutine->m_exception_value = NULL;
        coroutine->m_exception_tb = NULL;

        return NULL;
    }

    if ( (PyObject *)coroutine->m_exception_tb == Py_None )
    {
        coroutine->m_exception_tb = NULL;
    }
    else if ( coroutine->m_exception_tb != NULL && !PyTraceBack_Check( coroutine->m_exception_tb ) )
    {
        coroutine->m_exception_type = NULL;
        coroutine->m_exception_value = NULL;
        coroutine->m_exception_tb = NULL;

        PyErr_Format( PyExc_TypeError, "throw() third argument must be a traceback object" );
        return NULL;
    }

    if ( PyExceptionClass_Check( coroutine->m_exception_type ))
    {
        Py_INCREF( coroutine->m_exception_type );
        Py_XINCREF( coroutine->m_exception_value );
        Py_XINCREF( coroutine->m_exception_tb );

        NORMALIZE_EXCEPTION( &coroutine->m_exception_type, &coroutine->m_exception_value, &coroutine->m_exception_tb );
    }
    else if ( PyExceptionInstance_Check( coroutine->m_exception_type ) )
    {
        if ( coroutine->m_exception_value && coroutine->m_exception_value != Py_None )
        {
            coroutine->m_exception_type = NULL;
            coroutine->m_exception_value = NULL;
            coroutine->m_exception_tb = NULL;

            PyErr_Format( PyExc_TypeError, "instance exception may not have a separate value" );
            return NULL;
        }
        coroutine->m_exception_value = coroutine->m_exception_type;
        Py_INCREF( coroutine->m_exception_value );
        coroutine->m_exception_type = PyExceptionInstance_Class( coroutine->m_exception_type );
        Py_INCREF( coroutine->m_exception_type );
        Py_XINCREF( coroutine->m_exception_tb );
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "exceptions must be classes or instances deriving from BaseException, not %s",
            Py_TYPE( coroutine->m_exception_type )->tp_name
        );

        coroutine->m_exception_type = NULL;
        coroutine->m_exception_value = NULL;
        coroutine->m_exception_tb = NULL;

        return NULL;
    }

    if ( ( coroutine->m_exception_tb != NULL ) && ( (PyObject *)coroutine->m_exception_tb != Py_None ) && ( !PyTraceBack_Check( coroutine->m_exception_tb ) ) )
    {
        PyErr_Format( PyExc_TypeError, "throw() third argument must be a traceback object" );
        return NULL;
    }

    if ( coroutine->m_status != status_Finished )
    {
        PyObject *result = Nuitka_Coroutine_send( coroutine, Py_None );

        return result;
    }
    else
    {
        RESTORE_ERROR_OCCURRED( coroutine->m_exception_type, coroutine->m_exception_value, coroutine->m_exception_tb );

        coroutine->m_exception_type = NULL;
        coroutine->m_exception_value = NULL;
        coroutine->m_exception_tb = NULL;

        return NULL;
    }
}

static void Nuitka_Coroutine_tp_del( Nuitka_CoroutineObject *coroutine )
{
    if ( coroutine->m_status != status_Running )
    {
        return;
    }

    PyObject *error_type, *error_value;
    PyTracebackObject *error_traceback;

    FETCH_ERROR_OCCURRED( &error_type, &error_value, &error_traceback );

    PyObject *close_result = Nuitka_Coroutine_close( coroutine, NULL );

    if (unlikely( close_result == NULL ))
    {
        PyErr_WriteUnraisable( (PyObject *)coroutine );
    }
    else
    {
        Py_DECREF( close_result );
    }

    /* Restore the saved exception if any. */
    RESTORE_ERROR_OCCURRED( error_type, error_value, error_traceback );
}

static void Nuitka_Coroutine_tp_dealloc( Nuitka_CoroutineObject *coroutine )
{
    // Revive temporarily.
    assert( Py_REFCNT( coroutine ) == 0 );
    Py_REFCNT( coroutine ) = 1;

    // Save the current exception, if any, we must preserve it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED( &save_exception_type, &save_exception_value, &save_exception_tb );

    PyObject *close_result = Nuitka_Coroutine_close( coroutine, NULL );

    if (unlikely( close_result == NULL ))
    {
        PyErr_WriteUnraisable( (PyObject *)coroutine );
    }
    else
    {
        Py_DECREF( close_result );
    }

    Nuitka_Coroutine_release_closure( coroutine );

    Py_XDECREF( coroutine->m_frame );

    assert( Py_REFCNT( coroutine ) == 1 );
    Py_REFCNT( coroutine ) = 0;

    releaseFiber( &coroutine->m_yielder_context );

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack( coroutine );

    if ( coroutine->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)coroutine );
        assert( !ERROR_OCCURRED() );
    }

    Py_DECREF( coroutine->m_name );
    Py_DECREF( coroutine->m_qualname );

    PyObject_GC_Del( coroutine );
    RESTORE_ERROR_OCCURRED( save_exception_type, save_exception_value, save_exception_tb );
}


static PyObject *Nuitka_Coroutine_tp_repr( Nuitka_CoroutineObject *coroutine )
{
    return PyUnicode_FromFormat(
        "<compiled_coroutine object %s at %p>",
        Nuitka_String_AsString( coroutine->m_qualname ),
        coroutine
    );
}

static long Nuitka_Coroutine_tp_traverse( PyObject *coroutine, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting owned objects and/or if it
    // could be NULL instead. The "methodobject" visits its self and module. I
    // understand this is probably so that back references of this function to
    // its upper do not make it stay in the memory. A specific test if that
    // works might be needed.
    return 0;
}
static PyObject *Nuitka_Coroutine_await( Nuitka_CoroutineObject *coroutine )
{
#if _DEBUG_COROUTINE
    puts("Nuitka_Coroutine_await enter");
#endif

    Nuitka_CoroutineWrapperObject *result = PyObject_GC_New( Nuitka_CoroutineWrapperObject, &Nuitka_CoroutineWrapper_Type);

    if (unlikely(result == NULL))
    {
        return NULL;
    }

    result->m_coroutine = coroutine;
    Py_INCREF( result->m_coroutine );

    Nuitka_GC_Track( result );

    return (PyObject *)result;
}

#include <structmember.h>

static PyMethodDef Nuitka_Coroutine_methods[] =
{
    { "send",  (PyCFunction)Nuitka_Coroutine_send,  METH_O, NULL },
    { "throw", (PyCFunction)Nuitka_Coroutine_throw, METH_VARARGS, NULL },
    { "close", (PyCFunction)Nuitka_Coroutine_close, METH_NOARGS, NULL },
    { NULL }
};

static PyGetSetDef Nuitka_Coroutine_getsetlist[] =
{
    { (char *)"__name__",     (getter)Nuitka_Coroutine_get_name,     (setter)Nuitka_Coroutine_set_name,     NULL },
    { (char *)"__qualname__", (getter)Nuitka_Coroutine_get_qualname, (setter)Nuitka_Coroutine_set_qualname, NULL },
    { (char *)"cr_await",     (getter)Nuitka_Coroutine_get_cr_await, (setter)NULL,                          NULL },
    { (char *)"cr_code",      (getter)Nuitka_Coroutine_get_code,     (setter)Nuitka_Coroutine_set_code,     NULL },
    { (char *)"cr_frame",     (getter)Nuitka_Coroutine_get_frame,    (setter)Nuitka_Coroutine_set_frame,    NULL },

    { NULL }
};


static PyMemberDef Nuitka_Coroutine_members[] =
{
    { (char *)"cr_running", T_BOOL, offsetof( Nuitka_CoroutineObject, m_running ), READONLY },
    { NULL }
};


static PyAsyncMethods coro_as_async =
{
    (unaryfunc)Nuitka_Coroutine_await,  /* am_await */
    0,                                  /* am_aiter */
    0                                   /* am_anext */
};

PyTypeObject Nuitka_Coroutine_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_coroutine",                            /* tp_name */
    sizeof(Nuitka_CoroutineObject),                  /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)Nuitka_Coroutine_tp_dealloc,         /* tp_dealloc */
    0,                                               /* tp_print */
    0,                                               /* tp_getattr */
    0,                                               /* tp_setattr */
    &coro_as_async,                                  /* tp_as_async */
    (reprfunc)Nuitka_Coroutine_tp_repr,              /* tp_repr */
    0,                                               /* tp_as_number */
    0,                                               /* tp_as_sequence */
    0,                                               /* tp_as_mapping */
    0,                                               /* tp_hash */
    0,                                               /* tp_call */
    0,                                               /* tp_str */
    PyObject_GenericGetAttr,                         /* tp_getattro */
    0,                                               /* tp_setattro */
    0,                                               /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_HAVE_FINALIZE,                    /* tp_flags */
    0,                                               /* tp_doc */
    (traverseproc)Nuitka_Coroutine_tp_traverse,      /* tp_traverse */
    0,                                               /* tp_clear */
    0,                                               /* tp_richcompare */
    offsetof( Nuitka_CoroutineObject, m_weakrefs ),  /* tp_weaklistoffset */
    0,                                               /* tp_iter */
    0,                                               /* tp_iternext */
    Nuitka_Coroutine_methods,                        /* tp_methods */
    Nuitka_Coroutine_members,                        /* tp_members */
    Nuitka_Coroutine_getsetlist,                     /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    0,                                               /* tp_init */
    0,                                               /* tp_alloc */
    0,                                               /* tp_new */
    0,                                               /* tp_free */
    0,                                               /* tp_is_gc */
    0,                                               /* tp_bases */
    0,                                               /* tp_mro */
    0,                                               /* tp_cache */
    0,                                               /* tp_subclasses */
    0,                                               /* tp_weaklist */
    0,                                               /* tp_del */
    0,                                               /* tp_version_tag */
    (destructor)Nuitka_Coroutine_tp_del,             /* tp_finalize */
};

static void Nuitka_CoroutineWrapper_tp_dealloc( Nuitka_CoroutineWrapperObject *cw )
{
    Nuitka_GC_UnTrack( (PyObject *)cw );

    Py_DECREF( cw->m_coroutine );
    cw->m_coroutine = NULL;

    PyObject_GC_Del( cw );
}

static PyObject *Nuitka_CoroutineWrapper_tp_iternext( Nuitka_CoroutineWrapperObject *cw )
{
    return Nuitka_Coroutine_send( cw->m_coroutine, Py_None );
}

static int Nuitka_CoroutineWrapper_tp_traverse( Nuitka_CoroutineWrapperObject *cw, visitproc visit, void *arg )
{
    Py_VISIT( (PyObject *)cw->m_coroutine );
    return 0;
}

static PyObject *Nuitka_CoroutineWrapper_send( Nuitka_CoroutineWrapperObject *cw, PyObject *arg )
{
    return Nuitka_Coroutine_send( cw->m_coroutine, arg );
}

static PyObject *Nuitka_CoroutineWrapper_throw( Nuitka_CoroutineWrapperObject *cw, PyObject *args )
{
    return Nuitka_Coroutine_throw( cw->m_coroutine, args );
}

static PyObject *Nuitka_CoroutineWrapper_close( Nuitka_CoroutineWrapperObject *cw, PyObject *args )
{
    return Nuitka_Coroutine_close( cw->m_coroutine, args );
}

static PyMethodDef Nuitka_CoroutineWrapper_methods[] =
{
    { "send",  (PyCFunction)Nuitka_CoroutineWrapper_send,  METH_O, NULL },
    { "throw", (PyCFunction)Nuitka_CoroutineWrapper_throw, METH_VARARGS, NULL },
    { "close", (PyCFunction)Nuitka_CoroutineWrapper_close, METH_NOARGS, NULL },
    { NULL }
};

PyTypeObject Nuitka_CoroutineWrapper_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_coroutine_wrapper",
    sizeof(Nuitka_CoroutineWrapperObject),             /* tp_basicsize */
    0,                                                 /* tp_itemsize */
    (destructor)Nuitka_CoroutineWrapper_tp_dealloc,    /* tp_dealloc */
    0,                                                 /* tp_print */
    0,                                                 /* tp_getattr */
    0,                                                 /* tp_setattr */
    0,                                                 /* tp_as_async */
    0,                                                 /* tp_repr */
    0,                                                 /* tp_as_number */
    0,                                                 /* tp_as_sequence */
    0,                                                 /* tp_as_mapping */
    0,                                                 /* tp_hash */
    0,                                                 /* tp_call */
    0,                                                 /* tp_str */
    PyObject_GenericGetAttr,                           /* tp_getattro */
    0,                                                 /* tp_setattro */
    0,                                                 /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,           /* tp_flags */
    0,                                                 /* tp_doc */
    (traverseproc)Nuitka_CoroutineWrapper_tp_traverse, /* tp_traverse */
    0,                                                 /* tp_clear */
    0,                                                 /* tp_richcompare */
    0,                                                 /* tp_weaklistoffset */
    PyObject_SelfIter,                                 /* tp_iter */
    (iternextfunc)Nuitka_CoroutineWrapper_tp_iternext, /* tp_iternext */
    Nuitka_CoroutineWrapper_methods,                   /* tp_methods */
    0,                                                 /* tp_members */
    0,                                                 /* tp_getset */
    0,                                                 /* tp_base */
    0,                                                 /* tp_dict */
    0,                                                 /* tp_descr_get */
    0,                                                 /* tp_descr_set */
    0,                                                 /* tp_dictoffset */
    0,                                                 /* tp_init */
    0,                                                 /* tp_alloc */
    0,                                                 /* tp_new */
    PyObject_Del,                                      /* tp_free */
};

PyObject *Nuitka_Coroutine_New( coroutine_code code, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyCellObject **closure, Py_ssize_t closure_given )
{
    Nuitka_CoroutineObject *result = PyObject_GC_New( Nuitka_CoroutineObject, &Nuitka_Coroutine_Type );
    assert( result != NULL );

    result->m_code = (void *)code;

    CHECK_OBJECT( name );
    result->m_name = name;
    Py_INCREF( name );

    CHECK_OBJECT( qualname );

    result->m_qualname = qualname;
    Py_INCREF( qualname );

    // TODO: Makes no sense with coroutines maybe?
    result->m_yieldfrom = NULL;

    // We take ownership of those and received the reference count from the
    // caller.
    result->m_closure = closure;
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = false;

    result->m_exception_type = NULL;
    result->m_exception_value = NULL;
    result->m_exception_tb = NULL;

    result->m_yielded = NULL;
    result->m_returned = NULL;

    result->m_frame = NULL;
    result->m_code_object = code_object;

    initFiber( &result->m_yielder_context );

    Nuitka_GC_Track( result );
    return (PyObject *)result;
}

extern PyObject *PyGen_Send( PyGenObject *gen, PyObject *arg );
extern PyObject *const_str_plain_send;

static int gen_is_coroutine(PyObject *o)
{
    if ( PyGen_CheckExact(o) )
    {
        PyCodeObject *code = (PyCodeObject *)((PyGenObject*)o)->gi_code;

        if ( code->co_flags & CO_ITERABLE_COROUTINE )
        {
            return 1;
        }
    }

    return 0;
}

static PyObject *PyCoro_GetAwaitableIter( PyObject *value )
{
    unaryfunc getter = NULL;

    if ( PyCoro_CheckExact( value ) || gen_is_coroutine( value ) )
    {
        Py_INCREF( value );
        return value;
    }

    if ( Py_TYPE( value )->tp_as_async != NULL )
    {
        getter = Py_TYPE( value )->tp_as_async->am_await;
    }

    if ( getter != NULL )
    {
        PyObject *result = (*getter)( value );

        if ( result != NULL )
        {
            if (unlikely( PyCoro_CheckExact( result ) || gen_is_coroutine( result ) || Nuitka_Coroutine_Check( result ) ))
            {
                Py_DECREF( result );

                PyErr_Format(
                    PyExc_TypeError,
                    "__await__() returned a coroutine"
                );

                return NULL;
            }

            if (unlikely( !HAS_ITERNEXT( result ) ))
            {
                PyErr_Format(
                    PyExc_TypeError,
                     "__await__() returned non-iterator of type '%s'",
                     Py_TYPE( result )->tp_name
                );

                Py_DECREF( result );

                return NULL;
            }
        }

        return result;
    }

    PyErr_Format(
        PyExc_TypeError,
        "object %s can't be used in 'await' expression",
        Py_TYPE( value )->tp_name
    );

    return NULL;
}

static void RAISE_GENERATOR_EXCEPTION( Nuitka_CoroutineObject *generator )
{
    CHECK_OBJECT( generator->m_exception_type );

    RESTORE_ERROR_OCCURRED(
        generator->m_exception_type,
        generator->m_exception_value,
        generator->m_exception_tb
    );

    generator->m_exception_type = NULL;
    generator->m_exception_value = NULL;
    generator->m_exception_tb = NULL;
}

extern PyObject *ERROR_GET_STOP_ITERATION_VALUE();

extern PyObject *const_str_plain_send, *const_str_plain_throw, *const_str_plain_close;

static PyObject *yieldFromCoroutine( Nuitka_CoroutineObject *generator, PyObject *value )
{
    CHECK_OBJECT( value );

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
            if ( EXCEPTION_MATCH_BOOL_SINGLE( generator->m_exception_type, PyExc_GeneratorExit ) )
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
                else
                {
                    PyObject *error = GET_ERROR_OCCURRED();

                    if ( error != NULL && !EXCEPTION_MATCH_BOOL_SINGLE( error, PyExc_AttributeError ) )
                    {
                        PyErr_WriteUnraisable( (PyObject *)value );
                    }
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
                    if ( EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_StopIteration ) )
                    {
                        return ERROR_GET_STOP_ITERATION_VALUE();
                    }

                    return NULL;
                }

                generator->m_exception_type = NULL;
                generator->m_exception_value = NULL;
                generator->m_exception_tb = NULL;
            }
            else if ( EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_AttributeError ) )
            {
                CLEAR_ERROR_OCCURRED();

                RAISE_GENERATOR_EXCEPTION( generator );

                return NULL;
            }
            else
            {
                assert( ERROR_OCCURRED() );

                Py_CLEAR( generator->m_exception_type );
                Py_CLEAR( generator->m_exception_value );
                Py_CLEAR( generator->m_exception_tb );

                return NULL;
            }

        }
        else if ( PyGen_CheckExact( value ) || PyCoro_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
        else if ( send_value == Py_None && Py_TYPE( value )->tp_iternext != NULL )
        {
            retval = Py_TYPE( value )->tp_iternext( value );
        }
        else
        {
            retval = PyObject_CallMethodObjArgs( value, const_str_plain_send, send_value, NULL );
        }

        // Check the sub-generator result
        if ( retval == NULL )
        {
            PyObject *error = GET_ERROR_OCCURRED();
            if ( error == NULL )
            {
                Py_INCREF( Py_None );
                return Py_None;
            }

            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            if (likely( EXCEPTION_MATCH_BOOL_SINGLE( error, PyExc_StopIteration ) ))
            {
                return ERROR_GET_STOP_ITERATION_VALUE();
            }

            return NULL;
        }
        else
        {
            generator->m_yielded = retval;

            generator->m_yieldfrom = value;

            // Return to the calling context.
            swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

            generator->m_yieldfrom = NULL;

            send_value = generator->m_yielded;

            CHECK_OBJECT( send_value );
        }
    }
}


PyObject *AWAIT_COROUTINE( Nuitka_CoroutineObject *coroutine, PyObject *awaitable )
{
#if _DEBUG_COROUTINE
    PRINT_STRING("AWAIT entry:");

    PRINT_ITEM( awaitable );
    PRINT_NEW_LINE();
#endif

    PyObject *awaitable_iter = PyCoro_GetAwaitableIter( awaitable );

    if (unlikely( awaitable_iter == NULL ))
    {
        return NULL;
    }

    PyObject *retval = yieldFromCoroutine( coroutine, awaitable_iter );

    Py_DECREF( awaitable_iter );

#if _DEBUG_COROUTINE
    PRINT_STRING("AWAIT exit");

    PRINT_ITEM( retval );
    PRINT_NEW_LINE();
#endif

    return retval;
}

PyObject *MAKE_ASYNC_ITERATOR( Nuitka_CoroutineObject *coroutine, PyObject *value )
{
#if _DEBUG_COROUTINE
    PRINT_STRING("AITER entry:");

    PRINT_ITEM( value );
    PRINT_NEW_LINE();
#endif

    unaryfunc getter = NULL;

    if ( Py_TYPE( value )->tp_as_async )
    {
        getter = Py_TYPE( value )->tp_as_async->am_aiter;
    }

    if (unlikely( getter == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "'async for' requires an object with __aiter__ method, got %s",
            Py_TYPE( value )->tp_name
        );

        return NULL;
    }

    PyObject *iter = (*getter)( value );

    if (unlikely( iter == NULL ))
    {
        return NULL;
    }

    PyObject *awaitable_iter = PyCoro_GetAwaitableIter( iter );

    if (unlikely( awaitable_iter == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "'async for' received an invalid object from __aiter__: %s",
            Py_TYPE( iter )->tp_name
        );

        Py_DECREF( iter );

        return NULL;
    }

    Py_DECREF( iter );

    PyObject *retval = yieldFromCoroutine( coroutine, awaitable_iter );

    Py_DECREF( awaitable_iter );

#if _DEBUG_COROUTINE
    PRINT_STRING("AITER exit");
    PRINT_ITEM( retval );
    PRINT_NEW_LINE();
#endif

    return retval;
}

PyObject *ASYNC_ITERATOR_NEXT( Nuitka_CoroutineObject *coroutine, PyObject *value )
{
#if _DEBUG_COROUTINE
    PRINT_STRING("ANEXT entry:");

    PRINT_ITEM( value );
    PRINT_NEW_LINE();
#endif

    unaryfunc getter = NULL;

    if ( Py_TYPE( value )->tp_as_async )
    {
        getter = Py_TYPE( value )->tp_as_async->am_anext;
    }

    if (unlikely( getter == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "'async for' requires an iterator with __anext__ method, got %s",
            Py_TYPE( value )->tp_name
        );

        return NULL;
    }

    PyObject *next_value = (*getter)( value );

    if (unlikely( next_value == NULL ))
    {
        return NULL;
    }

    PyObject *awaitable_iter = PyCoro_GetAwaitableIter( next_value );

    if (unlikely( awaitable_iter == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "'async for' received an invalid object from __anext__: %s",
            Py_TYPE( next_value )->tp_name
        );

        Py_DECREF( next_value );

        return NULL;
    }

    Py_DECREF( next_value );

    PyObject *retval = yieldFromCoroutine( coroutine, awaitable_iter );

    Py_DECREF( awaitable_iter );

#if _DEBUG_COROUTINE
PRINT_STRING("ANEXT exit");
PRINT_ITEM( retval );
PRINT_NEW_LINE();
#endif

    return retval;
}
