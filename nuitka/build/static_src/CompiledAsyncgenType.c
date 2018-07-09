//     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
#include "nuitka/prelude.h"

#include "nuitka/freelists.h"


static PyObject *Nuitka_Asyncgen_get_name( struct Nuitka_AsyncgenObject *asyncgen )
{
    Py_INCREF( asyncgen->m_name );
    return asyncgen->m_name;
}

static int Nuitka_Asyncgen_set_name( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
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

    PyObject *tmp = asyncgen->m_name;
    Py_INCREF( value );
    asyncgen->m_name = value;
    Py_DECREF( tmp );

    return 0;
}

static PyObject *Nuitka_Asyncgen_get_qualname( struct Nuitka_AsyncgenObject *asyncgen )
{
    Py_INCREF( asyncgen->m_qualname );
    return asyncgen->m_qualname;
}

static int Nuitka_Asyncgen_set_qualname( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
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

    PyObject *tmp = asyncgen->m_qualname;
    Py_INCREF( value );
    asyncgen->m_qualname = value;
    Py_DECREF( tmp );

    return 0;
}

static PyObject *Nuitka_Asyncgen_get_ag_await( struct Nuitka_AsyncgenObject *asyncgen )
{
    if ( asyncgen->m_yieldfrom )
    {
        Py_INCREF( asyncgen->m_yieldfrom );
        return asyncgen->m_yieldfrom;
    }
    else
    {
        Py_INCREF( Py_None );
        return Py_None;
    }
}

static PyObject *Nuitka_Asyncgen_get_code( struct Nuitka_AsyncgenObject *asyncgen )
{
    Py_INCREF( asyncgen->m_code_object );
    return (PyObject *)asyncgen->m_code_object;
}

static int Nuitka_Asyncgen_set_code( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "ag_code is not writable in Nuitka" );
    return -1;
}


static void Nuitka_Asyncgen_release_closure( struct Nuitka_AsyncgenObject *asyncgen )
{
    for( Py_ssize_t i = 0; i < asyncgen->m_closure_given; i++ )
    {
        CHECK_OBJECT( asyncgen->m_closure[ i ] );
        Py_DECREF( asyncgen->m_closure[ i ] );
    }

    asyncgen->m_closure_given = 0;
}

#ifdef _NUITKA_MAKECONTEXT_INTS
static void Nuitka_Asyncgen_entry_point( int address_1, int address_2 )
{
    // Restore the pointer from integers should it be necessary, depending on
    // the platform. This requires pointers to be no larger that to "int" value.
    int addresses[2] =
    {
        address_1,
        address_2
    };

    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)*(uintptr_t *)&addresses[0];
#else
static void Nuitka_Asyncgen_entry_point( struct Nuitka_AsyncgenObject *asyncgen )
{
#endif
    ((asyncgen_code)asyncgen->m_code)( asyncgen );

    swapFiber( &asyncgen->m_yielder_context, &asyncgen->m_caller_context );
}


static PyObject *_Nuitka_Asyncgen_send( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value, bool closing )
{
    if ( value == NULL ) value = Py_None;

    if ( asyncgen->m_status == status_Unused && value != NULL && value != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "can't send non-None value to a just-started async generator" );
        return NULL;
    }

    if ( asyncgen->m_status != status_Finished )
    {
        PyThreadState *thread_state = PyThreadState_GET();

        if ( asyncgen->m_running )
        {
            PyErr_Format( PyExc_ValueError, "async generator already executing" );
            return NULL;
        }

        if ( asyncgen->m_status == status_Unused )
        {
            // Prepare the asyncgen context to run.
            int res = prepareFiber( &asyncgen->m_yielder_context, (void *)Nuitka_Asyncgen_entry_point, (uintptr_t)asyncgen );

            if ( res != 0 )
            {
                PyErr_Format( PyExc_MemoryError, "async generator cannot be allocated" );
                return NULL;
            }

            asyncgen->m_status = status_Running;
        }

        asyncgen->m_yielded = value;

        // Put the generator back on the frame stack.
        PyFrameObject *return_frame = thread_state->frame;
#ifndef __NUITKA_NO_ASSERT__
        if ( return_frame )
        {
            assertFrameObject( (struct Nuitka_FrameObject *)return_frame );
        }
#endif

        if ( asyncgen->m_frame )
        {
            // It would be nice if our frame were still alive. Nobody had the
            // right to release it.
            assertFrameObject( asyncgen->m_frame );

            // It's not supposed to be on the top right now.
            assert( return_frame != &asyncgen->m_frame->m_frame );

            Py_XINCREF( return_frame );
            asyncgen->m_frame->m_frame.f_back = return_frame;

            thread_state->frame = &asyncgen->m_frame->m_frame;
        }

        // Continue the yielder function while preventing recursion.
        asyncgen->m_running = true;

        swapFiber( &asyncgen->m_caller_context, &asyncgen->m_yielder_context );

        asyncgen->m_running = false;

        thread_state = PyThreadState_GET();

        // Remove the asyncgen from the frame stack.
        if ( asyncgen->m_frame )
        {
            assert( thread_state->frame == &asyncgen->m_frame->m_frame );
            assertFrameObject( asyncgen->m_frame );

            Py_CLEAR( asyncgen->m_frame->m_frame.f_back );
        }

        thread_state->frame = return_frame;

        // Generator return does set this.
        if ( asyncgen->m_status == status_Finished )
        {
            Py_XDECREF( asyncgen->m_frame );
            asyncgen->m_frame = NULL;

            Nuitka_Asyncgen_release_closure( asyncgen );

            return NULL;
        }
        else if ( asyncgen->m_yielded == NULL )
        {
            assert( ERROR_OCCURRED() );

            asyncgen->m_status = status_Finished;

            Py_XDECREF( asyncgen->m_frame );
            asyncgen->m_frame = NULL;

            Nuitka_Asyncgen_release_closure( asyncgen );

            assert( ERROR_OCCURRED() );

            PyObject *error_occurred = GET_ERROR_OCCURRED();

            if ( error_occurred == PyExc_StopIteration || error_occurred == PyExc_StopAsyncIteration )
            {
                PyObject *saved_exception_type, *saved_exception_value;
                PyTracebackObject *saved_exception_tb;

                FETCH_ERROR_OCCURRED( &saved_exception_type, &saved_exception_value, &saved_exception_tb );
                NORMALIZE_EXCEPTION( &saved_exception_type, &saved_exception_value, &saved_exception_tb );

                if ( error_occurred == PyExc_StopIteration )
                {
                    PyErr_Format(
                        PyExc_RuntimeError,
                        "async generator raised StopIteration"
                    );
                }
                else
                {
                    PyErr_Format(
                        PyExc_RuntimeError,
                        "async generator raised StopAsyncIteration"
                    );
                }
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
            return asyncgen->m_yielded;
        }
    }
    else
    {
        PyErr_SetObject( PyExc_StopAsyncIteration, (PyObject *)NULL );

        return NULL;
    }
}

PyObject *Nuitka_Asyncgen_close( struct Nuitka_AsyncgenObject *asyncgen, PyObject *args )
{
    if ( asyncgen->m_status == status_Running )
    {
        asyncgen->m_exception_type = PyExc_GeneratorExit;
        Py_INCREF( PyExc_GeneratorExit );
        asyncgen->m_exception_value = NULL;
        asyncgen->m_exception_tb = NULL;

        PyObject *result = _Nuitka_Asyncgen_send( asyncgen, Py_None, true );

        if (unlikely( result ))
        {
            Py_DECREF( result );

            PyErr_Format( PyExc_RuntimeError, "async generator ignored GeneratorExit" );
            return NULL;
        }
        else
        {
            PyObject *error = GET_ERROR_OCCURRED();
            assert( error != NULL );

            if ( EXCEPTION_MATCH_GENERATOR( error ) )
            {
                CLEAR_ERROR_OCCURRED();

                Py_INCREF( Py_None );
                return Py_None;
            }

            return NULL;
        }
    }

    Py_INCREF( Py_None );
    return Py_None;
}

/* Shared from coroutines. */
extern bool Nuitka_gen_close_iter( PyObject *yieldfrom );

extern PyObject *const_str_plain_throw;

static PyObject *_Nuitka_Asyncgen_throw2( struct Nuitka_AsyncgenObject *asyncgen, bool close_on_genexit )
{
    if ( asyncgen->m_yieldfrom != NULL )
    {
        if ( close_on_genexit )
        {
            if ( PyErr_GivenExceptionMatches( asyncgen->m_exception_type, PyExc_GeneratorExit ) )
            {
                // Asynchronous generators need to close the yield_from.
                asyncgen->m_running = 1;
                bool res = Nuitka_gen_close_iter( asyncgen->m_yieldfrom );
                asyncgen->m_running = 0;

                if ( res == true )
                {
                    return _Nuitka_Asyncgen_send( asyncgen, Py_None, false );
                }

                goto throw_here;
            }
        }

        PyObject *meth = PyObject_GetAttr( asyncgen->m_yieldfrom, const_str_plain_throw );
        if (unlikely( meth == NULL ))
        {
            if ( !PyErr_ExceptionMatches( PyExc_AttributeError ) )
            {
                return NULL;
            }
            CLEAR_ERROR_OCCURRED();

            goto throw_here;
        }

        asyncgen->m_running = 1;
        PyObject *ret = PyObject_CallFunctionObjArgs( meth, asyncgen->m_exception_type, asyncgen->m_exception_value, asyncgen->m_exception_tb, NULL );
        asyncgen->m_running = 0;

        Py_DECREF( meth );

        if (unlikely( ret == NULL ))
        {
            PyObject *val;

            if ( _PyGen_FetchStopIterationValue( &val ) == 0 )
            {
                ret = _Nuitka_Asyncgen_send( asyncgen, val, false );
                Py_DECREF( val );
            }
            else
            {
                ret = _Nuitka_Asyncgen_send( asyncgen, Py_None, false );
            }
        }

        return ret;
    }

throw_here:

    if ( (PyObject *)asyncgen->m_exception_tb == Py_None )
    {
        asyncgen->m_exception_tb = NULL;
    }
    else if ( asyncgen->m_exception_tb != NULL && !PyTraceBack_Check( asyncgen->m_exception_tb ) )
    {
        asyncgen->m_exception_type = NULL;
        asyncgen->m_exception_value = NULL;
        asyncgen->m_exception_tb = NULL;

        PyErr_Format( PyExc_TypeError, "throw() third argument must be a traceback object" );
        return NULL;
    }

    if ( PyExceptionClass_Check( asyncgen->m_exception_type ))
    {
        Py_INCREF( asyncgen->m_exception_type );
        Py_XINCREF( asyncgen->m_exception_value );
        Py_XINCREF( asyncgen->m_exception_tb );

        NORMALIZE_EXCEPTION( &asyncgen->m_exception_type, &asyncgen->m_exception_value, &asyncgen->m_exception_tb );
    }
    else if ( PyExceptionInstance_Check( asyncgen->m_exception_type ) )
    {
        if ( asyncgen->m_exception_value && asyncgen->m_exception_value != Py_None )
        {
            asyncgen->m_exception_type = NULL;
            asyncgen->m_exception_value = NULL;
            asyncgen->m_exception_tb = NULL;

            PyErr_Format( PyExc_TypeError, "instance exception may not have a separate value" );
            return NULL;
        }

        asyncgen->m_exception_value = asyncgen->m_exception_type;
        Py_INCREF( asyncgen->m_exception_value );
        asyncgen->m_exception_type = PyExceptionInstance_Class( asyncgen->m_exception_type );
        Py_INCREF( asyncgen->m_exception_type );
        Py_XINCREF( asyncgen->m_exception_tb );
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "exceptions must be classes or instances deriving from BaseException, not %s",
            Py_TYPE( asyncgen->m_exception_type )->tp_name
        );

        asyncgen->m_exception_type = NULL;
        asyncgen->m_exception_value = NULL;
        asyncgen->m_exception_tb = NULL;

        return NULL;
    }

    if ( ( asyncgen->m_exception_tb != NULL ) && ( (PyObject *)asyncgen->m_exception_tb != Py_None ) && ( !PyTraceBack_Check( asyncgen->m_exception_tb ) ) )
    {
        PyErr_Format( PyExc_TypeError, "throw() third argument must be a traceback object" );
        return NULL;
    }

    if ( asyncgen->m_status != status_Finished )
    {
        PyObject *result = _Nuitka_Asyncgen_send( asyncgen, Py_None, false );

        return result;
    }
    else
    {
        PyErr_SetNone( PyExc_StopAsyncIteration );
        return NULL;
    }
}

static PyObject *_Nuitka_Asyncgen_throw( struct Nuitka_AsyncgenObject *asyncgen, bool close_for_exit, PyObject *exc_type, PyObject *exc_value, PyObject *exc_tb )
{
    asyncgen->m_exception_type = exc_type;
    asyncgen->m_exception_value = exc_value;
    asyncgen->m_exception_tb = (PyTracebackObject *)exc_tb;

    return _Nuitka_Asyncgen_throw2( asyncgen, close_for_exit );
}

static PyObject *Nuitka_Asyncgen_throw( struct Nuitka_AsyncgenObject *asyncgen, PyObject *args )
{
    assert( asyncgen->m_exception_type == NULL );
    assert( asyncgen->m_exception_value == NULL );
    assert( asyncgen->m_exception_tb == NULL );

    int res = PyArg_UnpackTuple( args, "throw", 1, 3, &asyncgen->m_exception_type, &asyncgen->m_exception_value, (PyObject **)&asyncgen->m_exception_tb );

    if (unlikely( res == 0 ))
    {
        asyncgen->m_exception_type = NULL;
        asyncgen->m_exception_value = NULL;
        asyncgen->m_exception_tb = NULL;

        return NULL;
    }

    return _Nuitka_Asyncgen_throw2( asyncgen, true );
}


static int Nuitka_Asyncgen_init_hooks( struct Nuitka_AsyncgenObject *asyncgen )
{
    /* Just do this once per async generator object. */
    if ( asyncgen->m_hooks_init_done )
    {
        return 0;
    }
    asyncgen->m_hooks_init_done = 1;

    PyThreadState *tstate = PyThreadState_GET();

    /* Attach the finalizer if any. */
    PyObject *finalizer = tstate->async_gen_finalizer;
    if ( finalizer )
    {
        Py_INCREF( finalizer );
        asyncgen->m_finalizer = finalizer;
    }

    /* Call the "firstiter" hook for async generator. */
    PyObject *firstiter = tstate->async_gen_firstiter;
    if ( firstiter )
    {
        Py_INCREF( firstiter );

        PyObject *args[] =
        {
            (PyObject *)asyncgen
        };
        PyObject *res = CALL_FUNCTION_WITH_ARGS1( firstiter, args );

        Py_DECREF( firstiter );

        if (unlikely( res == NULL ))
        {
            return 1;
        }

        Py_DECREF( res );
    }

    return 0;
}

static PyObject *Nuitka_AsyncgenAsend_New( struct Nuitka_AsyncgenObject *asyncgen, PyObject *sendval );
static PyObject *Nuitka_AsyncgenAthrow_New( struct Nuitka_AsyncgenObject *asyncgen, PyObject *args );

static PyObject *Nuitka_Asyncgen_anext( struct Nuitka_AsyncgenObject *asyncgen )
{
    if ( Nuitka_Asyncgen_init_hooks( asyncgen ) )
    {
        return NULL;
    }

#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_Asyncgen_anext: Making Nuitka_AsyncgenAsend object.");
    PRINT_NEW_LINE();
#endif

    return Nuitka_AsyncgenAsend_New( asyncgen, NULL );
}


static PyObject *Nuitka_Asyncgen_asend( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
{
    if ( Nuitka_Asyncgen_init_hooks( asyncgen ) )
    {
        return NULL;
    }

    return Nuitka_AsyncgenAsend_New( asyncgen, value );
}

static PyObject *Nuitka_Asyncgen_aclose( struct Nuitka_AsyncgenObject *asyncgen, PyObject *arg )
{
    if ( Nuitka_Asyncgen_init_hooks( asyncgen ) )
    {
        return NULL;
    }

    return Nuitka_AsyncgenAthrow_New( asyncgen, NULL );
}

static PyObject *Nuitka_Asyncgen_athrow( struct Nuitka_AsyncgenObject *asyncgen, PyObject *args )
{
    if ( Nuitka_Asyncgen_init_hooks( asyncgen ) )
    {
        return NULL;
    }

    return Nuitka_AsyncgenAthrow_New( asyncgen, args );
}

#define MAX_ASYNCGEN_FREE_LIST_COUNT 100
static struct Nuitka_AsyncgenObject *free_list_asyncgens = NULL;
static int free_list_asyncgens_count = 0;

// TODO: This might have to be finalize actually.
static void Nuitka_Asyncgen_tp_dealloc( struct Nuitka_AsyncgenObject *asyncgen )
{
    // Revive temporarily.
    assert( Py_REFCNT( asyncgen ) == 0 );
    Py_REFCNT( asyncgen ) = 1;

    // Save the current exception, if any, we must preserve it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;

    PyObject *finalizer = asyncgen->m_finalizer;
    if ( finalizer && asyncgen->m_closed == false )
    {
        /* Save the current exception, if any. */
        FETCH_ERROR_OCCURRED( &save_exception_type, &save_exception_value, &save_exception_tb );

        // TODO: Call with args 1 function.
        PyObject *res = PyObject_CallFunctionObjArgs( finalizer, asyncgen, NULL );

        if (unlikely( res == NULL ))
        {
            PyErr_WriteUnraisable( (PyObject *)asyncgen );
        }
        else
        {
            Py_DECREF( res );
        }

        RESTORE_ERROR_OCCURRED( save_exception_type, save_exception_value, save_exception_tb );
        return;
    }

    FETCH_ERROR_OCCURRED( &save_exception_type, &save_exception_value, &save_exception_tb );

    PyObject *close_result = Nuitka_Asyncgen_close( asyncgen, NULL );

    if (unlikely( close_result == NULL ))
    {
        PyErr_WriteUnraisable( (PyObject *)asyncgen );
    }
    else
    {
        Py_DECREF( close_result );
    }

    Nuitka_Asyncgen_release_closure( asyncgen );

    Py_XDECREF( asyncgen->m_frame );

    assert( Py_REFCNT( asyncgen ) == 1 );
    Py_REFCNT( asyncgen ) = 0;

    releaseFiber( &asyncgen->m_yielder_context );

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack( asyncgen );

    Py_CLEAR( asyncgen->m_finalizer );

    if ( asyncgen->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)asyncgen );
        assert( !ERROR_OCCURRED() );
    }

    Py_DECREF( asyncgen->m_name );
    Py_DECREF( asyncgen->m_qualname );

    /* Put the object into freelist or release to GC */
    releaseToFreeList(
        free_list_asyncgens,
        asyncgen,
        MAX_ASYNCGEN_FREE_LIST_COUNT
    );

    RESTORE_ERROR_OCCURRED( save_exception_type, save_exception_value, save_exception_tb );
}

static PyObject *Nuitka_Asyncgen_tp_repr( struct Nuitka_AsyncgenObject *asyncgen )
{
    return PyUnicode_FromFormat(
        "<compiled_async_generator object %s at %p>",
        Nuitka_String_AsString( asyncgen->m_qualname ),
        asyncgen
    );
}

static int Nuitka_Asyncgen_tp_traverse( struct Nuitka_AsyncgenObject *asyncgen, visitproc visit, void *arg )
{
    Py_VISIT( asyncgen->m_finalizer );

    // TODO: Identify the impact of not visiting owned objects and/or if it
    // could be NULL instead. The "methodobject" visits its self and module. I
    // understand this is probably so that back references of this function to
    // its upper do not make it stay in the memory. A specific test if that
    // works might be needed.
    return 0;
}

#include <structmember.h>

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyMethodDef Nuitka_Asyncgen_methods[] =
{
    { "asend",  (PyCFunction)Nuitka_Asyncgen_asend,  METH_O, NULL },
    { "athrow", (PyCFunction)Nuitka_Asyncgen_athrow, METH_VARARGS, NULL },
    { "aclose", (PyCFunction)Nuitka_Asyncgen_aclose, METH_NOARGS, NULL },
    { NULL }
};


static PyAsyncMethods Nuitka_Asyncgen_as_async =
{
    0,                                          /* am_await */
    PyObject_SelfIter,                          /* am_aiter */
    (unaryfunc)Nuitka_Asyncgen_anext            /* am_anext */
};

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyGetSetDef Nuitka_Asyncgen_getsetlist[] =
{
    { (char *)"__name__",     (getter)Nuitka_Asyncgen_get_name,     (setter)Nuitka_Asyncgen_set_name,     NULL },
    { (char *)"__qualname__", (getter)Nuitka_Asyncgen_get_qualname, (setter)Nuitka_Asyncgen_set_qualname, NULL },
    { (char *)"ag_await",     (getter)Nuitka_Asyncgen_get_ag_await, (setter)NULL,                         NULL },
    { (char *)"ag_code",      (getter)Nuitka_Asyncgen_get_code,     (setter)Nuitka_Asyncgen_set_code,     NULL },

    { NULL }
};


static PyMemberDef Nuitka_Asyncgen_members[] =
{
    { (char *)"ag_frame",   T_OBJECT, offsetof(struct Nuitka_AsyncgenObject, m_frame),   READONLY },
    { (char *)"ag_running", T_BOOL,   offsetof(struct Nuitka_AsyncgenObject, m_running), READONLY },
    { NULL }
};

PyTypeObject Nuitka_Asyncgen_Type =
{
    PyVarObject_HEAD_INIT(NULL, 0)
    "compiled_async_generator",                          /* tp_name */
    sizeof(struct Nuitka_AsyncgenObject),                /* tp_basicsize */
    sizeof(struct Nuitka_CellObject *),                  /* tp_itemsize */
    (destructor)Nuitka_Asyncgen_tp_dealloc,              /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    &Nuitka_Asyncgen_as_async,                           /* tp_as_async */
    (reprfunc)Nuitka_Asyncgen_tp_repr,                   /* tp_repr */
    0,                                                   /* tp_as_number */
    0,                                                   /* tp_as_sequence */
    0,                                                   /* tp_as_mapping */
    0,                                                   /* tp_hash */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    PyObject_GenericGetAttr,                             /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_HAVE_FINALIZE,                        /* tp_flags */
    0,                                                   /* tp_doc */
    (traverseproc)Nuitka_Asyncgen_tp_traverse,           /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    offsetof(struct Nuitka_AsyncgenObject, m_weakrefs),  /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    Nuitka_Asyncgen_methods,                             /* tp_methods */
    Nuitka_Asyncgen_members,                             /* tp_members */
    Nuitka_Asyncgen_getsetlist,                          /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    0,                                                   /* tp_init */
    0,                                                   /* tp_alloc */
    0,                                                   /* tp_new */
    0,                                                   /* tp_free */
};

PyObject *Nuitka_Asyncgen_New( asyncgen_code code, PyObject *name, PyObject *qualname, PyCodeObject *code_object, Py_ssize_t closure_given )
{
    struct Nuitka_AsyncgenObject *result;

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(
        free_list_asyncgens,
        struct Nuitka_AsyncgenObject,
        Nuitka_Asyncgen_Type,
        closure_given
    );

    result->m_code = (void *)code;

    CHECK_OBJECT( name );
    result->m_name = name;
    Py_INCREF( name );

    CHECK_OBJECT( qualname );

    result->m_qualname = qualname;
    Py_INCREF( qualname );

    // TODO: Makes no sense with asyncgens maybe?
    result->m_yieldfrom = NULL;

    // The m_closure is set from the outside.
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = false;
    result->m_awaiting = false;

    result->m_exception_type = NULL;
    result->m_exception_value = NULL;
    result->m_exception_tb = NULL;

    result->m_yielded = NULL;

    result->m_frame = NULL;
    result->m_code_object = code_object;

    result->m_finalizer = NULL;
    result->m_hooks_init_done = false;
    result->m_closed = false;

    initFiber( &result->m_yielder_context );

    Nuitka_GC_Track( result );
    return (PyObject *)result;
}

struct Nuitka_AsyncgenWrappedValueObject {
    PyObject_HEAD
    PyObject *m_value;
};

static struct Nuitka_AsyncgenWrappedValueObject *free_list_asyncgen_value_wrappers = NULL;
static int free_list_asyncgen_value_wrappers_count = 0;

static void asyncgen_value_wrapper_tp_dealloc( struct Nuitka_AsyncgenWrappedValueObject *asyncgen_value_wrapper )
{
    Nuitka_GC_UnTrack( (PyObject *)asyncgen_value_wrapper );

    Py_DECREF( asyncgen_value_wrapper->m_value );

    releaseToFreeList(
        free_list_asyncgen_value_wrappers,
        asyncgen_value_wrapper,
        MAX_ASYNCGEN_FREE_LIST_COUNT
    );
}


static int asyncgen_value_wrapper_tp_traverse( struct Nuitka_AsyncgenWrappedValueObject *asyncgen_value_wrapper, visitproc visit, void *arg )
{
    Py_VISIT( asyncgen_value_wrapper->m_value );

    return 0;
}


static PyTypeObject Nuitka_AsyncgenValueWrapper_Type =
{
    PyVarObject_HEAD_INIT(NULL, 0)
    "compiled_async_generator_wrapped_value",         /* tp_name */
    sizeof(struct Nuitka_AsyncgenWrappedValueObject), /* tp_basicsize */
    0,                                                /* tp_itemsize */
    (destructor)asyncgen_value_wrapper_tp_dealloc,    /* tp_dealloc */
    0,                                                /* tp_print */
    0,                                                /* tp_getattr */
    0,                                                /* tp_setattr */
    0,                                                /* tp_as_async */
    0,                                                /* tp_repr */
    0,                                                /* tp_as_number */
    0,                                                /* tp_as_sequence */
    0,                                                /* tp_as_mapping */
    0,                                                /* tp_hash */
    0,                                                /* tp_call */
    0,                                                /* tp_str */
    PyObject_GenericGetAttr,                          /* tp_getattro */
    0,                                                /* tp_setattro */
    0,                                                /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,          /* tp_flags */
    0,                                                /* tp_doc */
    (traverseproc)asyncgen_value_wrapper_tp_traverse, /* tp_traverse */
    0,                                                /* tp_clear */
    0,                                                /* tp_richcompare */
    0,                                                /* tp_weaklistoffset */
    0,                                                /* tp_iter */
    0,                                                /* tp_iternext */
    0,                                                /* tp_methods */
    0,                                                /* tp_members */
    0,                                                /* tp_getset */
    0,                                                /* tp_base */
    0,                                                /* tp_dict */
    0,                                                /* tp_descr_get */
    0,                                                /* tp_descr_set */
    0,                                                /* tp_dictoffset */
    0,                                                /* tp_init */
    0,                                                /* tp_alloc */
    0,                                                /* tp_new */
};


PyObject *Nuitka_AsyncGenValueWrapperNew( PyObject *value )
{
    CHECK_OBJECT( value );
    struct Nuitka_AsyncgenWrappedValueObject *result;

    allocateFromFreeListFixed(
        free_list_asyncgen_value_wrappers,
        struct Nuitka_AsyncgenWrappedValueObject,
        Nuitka_AsyncgenValueWrapper_Type
    );

    result->m_value = value;

    Py_INCREF( value );

    Nuitka_GC_Track( result );

    return (PyObject *)result;
}

#define Nuitka_AsyncgenWrappedValue_CheckExact(o) (Py_TYPE(o) == &Nuitka_AsyncgenValueWrapper_Type)


// TODO: We could change all generators to use that kind of enum, if
// it's properly supported.
typedef enum
{
    AWAITABLE_STATE_INIT   = 0,  /* Has not yet been iterated. */
    AWAITABLE_STATE_ITER   = 1,  /* Being iterated currently. */
    AWAITABLE_STATE_CLOSED = 2,  /* Closed, no more. */
} AwaitableState;

struct Nuitka_AsyncgenAsendObject
{
    PyObject_HEAD

    struct Nuitka_AsyncgenObject *m_gen;
    PyObject *m_sendval;

    AwaitableState m_state;
};

/**
 * These can be created by byte code loop, and we don't now its internals,
 * yet we have to unwrap ourselves too. These could break in future updates,
 * and ideally we would have checks to cover those.
 */
typedef struct {
    PyObject_HEAD
    PyObject *agw_val;
} _PyAsyncGenWrappedValue;

#define _PyAsyncGenWrappedValue_CheckExact(o) (Py_TYPE(o) == &_PyAsyncGenWrappedValue_Type)

static PyObject *Nuitka_Asyncgen_unwrap_value( struct Nuitka_AsyncgenObject *asyncgen, PyObject *result )
{
    if ( result == NULL )
    {
        if ( !ERROR_OCCURRED() )
        {
            PyErr_SetNone( PyExc_StopAsyncIteration );
            asyncgen->m_closed = true;
        }
        else if ( PyErr_ExceptionMatches( PyExc_StopAsyncIteration ) ||
                  PyErr_ExceptionMatches( PyExc_GeneratorExit ) )
        {
            asyncgen->m_closed = true;
        }

        return NULL;
    }

    if ( _PyAsyncGenWrappedValue_CheckExact( result ) )
    {
        /* async yield */
        _PyGen_SetStopIterationValue( ((_PyAsyncGenWrappedValue*)result)->agw_val );

        Py_DECREF( result );

        return NULL;
    }
    else if ( Nuitka_AsyncgenWrappedValue_CheckExact( result ) )
    {
        /* async yield */
        _PyGen_SetStopIterationValue( ((struct Nuitka_AsyncgenWrappedValueObject *)result)->m_value );

        Py_DECREF( result );

        return NULL;
    }

    return result;
}

static struct Nuitka_AsyncgenAsendObject *free_list_asyncgen_asends = NULL;
static int free_list_asyncgen_asends_count = 0;


static void Nuitka_AsyncgenAsend_tp_dealloc( struct Nuitka_AsyncgenAsendObject *asyncgen_asend )
{
    Nuitka_GC_UnTrack( asyncgen_asend );

    Py_DECREF( asyncgen_asend->m_gen );
    Py_XDECREF( asyncgen_asend->m_sendval );

    releaseToFreeList(
        free_list_asyncgen_asends,
        asyncgen_asend,
        MAX_ASYNCGEN_FREE_LIST_COUNT
    );
}

static int Nuitka_AsyncgenAsend_tp_traverse( struct Nuitka_AsyncgenAsendObject *asyncgen_asend, visitproc visit, void *arg )
{
    Py_VISIT( asyncgen_asend->m_gen );
    Py_VISIT( asyncgen_asend->m_sendval );

    return 0;
}

static PyObject *Nuitka_AsyncgenAsend_send( struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *arg )
{
#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_send: Enter with state" );
    printf("State on entry is asyncgen_send->m_state = %d\n", asyncgen_asend->m_state );
    fflush(stdout);
    PRINT_NEW_LINE();
#endif

    PyObject *result;

    if ( asyncgen_asend->m_state == AWAITABLE_STATE_CLOSED )
    {
        PyErr_SetNone( PyExc_StopIteration );
        return NULL;
    }

    if ( asyncgen_asend->m_state == AWAITABLE_STATE_INIT )
    {
        if ( arg == NULL || arg == Py_None )
        {
            arg = asyncgen_asend->m_sendval;
        }

        asyncgen_asend->m_state = AWAITABLE_STATE_ITER;
    }

    result = _Nuitka_Asyncgen_send( asyncgen_asend->m_gen, arg, false );
    result = Nuitka_Asyncgen_unwrap_value( asyncgen_asend->m_gen, result );

    if ( result == NULL )
    {
        asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;
    }

    return result;
}


static PyObject *Nuitka_AsyncgenAsend_tp_iternext( struct Nuitka_AsyncgenAsendObject *asyncgen_asend )
{
#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_tp_iternext: refer to Nuitka_AsyncgenAsend_send");
    PRINT_NEW_LINE();
#endif


    return Nuitka_AsyncgenAsend_send( asyncgen_asend, NULL );
}


static PyObject *Nuitka_AsyncgenAsend_throw( struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *args )
{
    PyObject *result;

    if ( asyncgen_asend->m_state == AWAITABLE_STATE_CLOSED )
    {
        PyErr_SetNone( PyExc_StopIteration );
        return NULL;
    }

    result = Nuitka_Asyncgen_throw( asyncgen_asend->m_gen, args );
    result = Nuitka_Asyncgen_unwrap_value( asyncgen_asend->m_gen, result );

    if ( asyncgen_asend == NULL )
    {
        asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;
    }

    return result;
}


static PyObject *Nuitka_AsyncgenAsend_close( struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *args )
{
    asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;

    Py_INCREF( Py_None );
    return Py_None;
}


static PyMethodDef Nuitka_AsyncgenAsend_methods[] =
{
    { "send",  (PyCFunction)Nuitka_AsyncgenAsend_send,  METH_O, NULL},
    { "throw", (PyCFunction)Nuitka_AsyncgenAsend_throw, METH_VARARGS, NULL},
    { "close", (PyCFunction)Nuitka_AsyncgenAsend_close, METH_NOARGS, NULL},
    { NULL }
};


static PyAsyncMethods Nuitka_AsyncgenAsend_as_async =
{
    PyObject_SelfIter,                          /* am_await */
    0,                                          /* am_aiter */
    0                                           /* am_anext */
};


static PyTypeObject Nuitka_AsyncgenAsend_Type =
{
    PyVarObject_HEAD_INIT(NULL, 0)
    "compiled_async_generator_asend",                   /* tp_name */
    sizeof(struct Nuitka_AsyncgenAsendObject),          /* tp_basicsize */
    0,                                                  /* tp_itemsize */
    (destructor)Nuitka_AsyncgenAsend_tp_dealloc,        /* tp_dealloc */
    0,                                                  /* tp_print */
    0,                                                  /* tp_getattr */
    0,                                                  /* tp_setattr */
    &Nuitka_AsyncgenAsend_as_async,                     /* tp_as_async */
    0,                                                  /* tp_repr */
    0,                                                  /* tp_as_number */
    0,                                                  /* tp_as_sequence */
    0,                                                  /* tp_as_mapping */
    0,                                                  /* tp_hash */
    0,                                                  /* tp_call */
    0,                                                  /* tp_str */
    PyObject_GenericGetAttr,                            /* tp_getattro */
    0,                                                  /* tp_setattro */
    0,                                                  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,            /* tp_flags */
    0,                                                  /* tp_doc */
    (traverseproc)Nuitka_AsyncgenAsend_tp_traverse,     /* tp_traverse */
    0,                                                  /* tp_clear */
    0,                                                  /* tp_richcompare */
    0,                                                  /* tp_weaklistoffset */
    PyObject_SelfIter,                                  /* tp_iter */
    (iternextfunc)Nuitka_AsyncgenAsend_tp_iternext,     /* tp_iternext */
    Nuitka_AsyncgenAsend_methods,                       /* tp_methods */
    0,                                                  /* tp_members */
    0,                                                  /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    0,                                                  /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    0,                                                  /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    0,                                                  /* tp_new */
};


static PyObject *Nuitka_AsyncgenAsend_New( struct Nuitka_AsyncgenObject *asyncgen, PyObject *sendval )
{
    struct Nuitka_AsyncgenAsendObject *result;

    allocateFromFreeListFixed(
        free_list_asyncgen_asends,
        struct Nuitka_AsyncgenAsendObject,
        Nuitka_AsyncgenAsend_Type
    )

    Py_INCREF( asyncgen );
    result->m_gen = asyncgen;

    // TODO: We could make the user do that, so NULL is handled faster.
    Py_XINCREF( sendval );
    result->m_sendval = sendval;

    result->m_state = AWAITABLE_STATE_INIT;

    Nuitka_GC_Track( result );
    return (PyObject*)result;
}

struct Nuitka_AsyncgenAthrowObject
{
    PyObject_HEAD

    // The asyncgen we are working for.
    struct Nuitka_AsyncgenObject *m_gen;
    // Arguments, NULL in case of close, otherwise throw arguments.
    PyObject *m_args;

    AwaitableState m_state;
};

static struct Nuitka_AsyncgenAthrowObject *free_list_asyncgen_athrows = NULL;
static int free_list_asyncgen_athrows_count = 0;


static void Nuitka_AsyncgenAthrow_dealloc( struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow )
{
    Nuitka_GC_UnTrack( asyncgen_athrow );

    Py_DECREF( asyncgen_athrow->m_gen );
    Py_XDECREF( asyncgen_athrow->m_args );

    releaseToFreeList(
        free_list_asyncgen_athrows,
        asyncgen_athrow,
        MAX_ASYNCGEN_FREE_LIST_COUNT
    );
}


static int Nuitka_AsyncgenAthrow_traverse( struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, visitproc visit, void *arg )
{
    Py_VISIT( asyncgen_athrow->m_gen );
    Py_VISIT( asyncgen_athrow->m_args );

    return 0;
}


static PyObject *Nuitka_AsyncgenAthrow_send( struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *arg )
{
    struct Nuitka_AsyncgenObject *asyncgen = asyncgen_athrow->m_gen;

    // If finished, just report StopIteration.
    if ( asyncgen->m_status == status_Finished ||
         asyncgen_athrow->m_state == AWAITABLE_STATE_CLOSED )
    {
        PyErr_SetNone( PyExc_StopIteration );
        return NULL;
    }

    PyObject *retval;

    if ( asyncgen_athrow->m_state == AWAITABLE_STATE_INIT )
    {
        // Can also close only once.
        if ( asyncgen->m_closed )
        {
            PyErr_SetNone( PyExc_StopIteration );
            return NULL;
        }

        // Starting accepts only "None" as input value.
        if ( arg != Py_None )
        {
            PyErr_Format(
                PyExc_RuntimeError,
                "can't send non-None value to a just-started coroutine"
            );

            return NULL;
        }

        asyncgen_athrow->m_state = AWAITABLE_STATE_ITER;

        if ( asyncgen_athrow->m_args == NULL )
        {
            asyncgen->m_closed = true;

            retval = _Nuitka_Asyncgen_throw(
                asyncgen,
                0,  /* Do not close generator when PyExc_GeneratorExit is passed */
                PyExc_GeneratorExit,
                NULL,
                NULL
            );

            if ( retval )
            {
                if ( _PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval) )
                {
                    Py_DECREF( retval );

                    PyErr_Format(
                        PyExc_RuntimeError,
                        "async generator ignored GeneratorExit"
                    );

                    return NULL;
                }
            }
        }
        else
        {
            PyObject *typ;
            PyObject *tb = NULL;
            PyObject *val = NULL;

            if (unlikely( !PyArg_UnpackTuple( asyncgen_athrow->m_args, "athrow", 1, 3, &typ, &val, &tb)))
            {
                return NULL;
            }

            retval = _Nuitka_Asyncgen_throw(
                asyncgen,
                0,  /* Do not close generator when PyExc_GeneratorExit is passed */
                typ,
                val,
                tb
            );

            retval = Nuitka_Asyncgen_unwrap_value( asyncgen, retval );
        }

        if ( retval == NULL )
        {
            goto check_error;
        }

        return retval;
    }

    assert( asyncgen_athrow->m_state == AWAITABLE_STATE_ITER );

    retval = _Nuitka_Asyncgen_send( asyncgen, arg, false );

    if ( asyncgen_athrow->m_args )
    {
        return Nuitka_Asyncgen_unwrap_value( asyncgen, retval );
    }
    else
    {
        /* We are here to close if no args. */
        if ( retval )
        {
            if ( _PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval) )
            {
                Py_DECREF( retval );

                PyErr_Format(
                    PyExc_RuntimeError,
                    "async generator ignored GeneratorExit"
                );

                return NULL;
            }

            return retval;
        }
    }

check_error:

    if ( PyErr_ExceptionMatches( PyExc_StopAsyncIteration ) )
    {
        asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

        if ( asyncgen_athrow->m_args == NULL )
        {
            CLEAR_ERROR_OCCURRED();
            PyErr_SetNone( PyExc_StopIteration );
        }
    }
    else if ( PyErr_ExceptionMatches( PyExc_GeneratorExit ) )
    {
        asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

        CLEAR_ERROR_OCCURRED();
        PyErr_SetNone( PyExc_StopIteration );
    }

    return NULL;
}



static PyObject *Nuitka_AsyncgenAthrow_throw( struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *args )
{
    PyObject *retval;

    if ( asyncgen_athrow->m_state == AWAITABLE_STATE_INIT )
    {
        PyErr_Format(
            PyExc_RuntimeError,
            "can't send non-None value to a just-started coroutine"
        );

        return NULL;
    }

    if ( asyncgen_athrow->m_state == AWAITABLE_STATE_CLOSED )
    {
        PyErr_SetNone( PyExc_StopIteration );
        return NULL;
    }

    retval = Nuitka_Asyncgen_throw( asyncgen_athrow->m_gen, args );

    if ( asyncgen_athrow->m_args )
    {
        return Nuitka_Asyncgen_unwrap_value( asyncgen_athrow->m_gen, retval );
    }
    else
    {
        if ( retval )
        {
            if ( _PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval) )
            {
                Py_DECREF( retval );

                PyErr_Format(
                    PyExc_RuntimeError,
                    "async generator ignored GeneratorExit"
                );

                return NULL;
            }
        }

        return retval;
    }
}

static PyObject *Nuitka_AsyncgenAthrow_iternext( struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow )
{
    return Nuitka_AsyncgenAthrow_send( asyncgen_athrow, Py_None );
}


static PyObject *Nuitka_AsyncgenAthrow_close( struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *args )
{
    asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

    Py_INCREF( Py_None );
    return Py_None;
}


static PyMethodDef Nuitka_AsyncgenAthrow_methods[] =
{
    { "send",  (PyCFunction)Nuitka_AsyncgenAthrow_send,  METH_O, NULL },
    { "throw", (PyCFunction)Nuitka_AsyncgenAthrow_throw, METH_VARARGS, NULL },
    { "close", (PyCFunction)Nuitka_AsyncgenAthrow_close, METH_NOARGS, NULL },
    { NULL }
};


static PyAsyncMethods Nuitka_AsyncgenAthrow_as_async =
{
    PyObject_SelfIter,                          /* am_await */
    0,                                          /* am_aiter */
    0                                           /* am_anext */
};


static PyTypeObject Nuitka_AsyncgenAthrow_Type =
{
    PyVarObject_HEAD_INIT(NULL, 0)
    "compiled_async_generator_athrow",               /* tp_name */
    sizeof(struct Nuitka_AsyncgenAthrowObject),      /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)Nuitka_AsyncgenAthrow_dealloc,       /* tp_dealloc */
    0,                                               /* tp_print */
    0,                                               /* tp_getattr */
    0,                                               /* tp_setattr */
    &Nuitka_AsyncgenAthrow_as_async,                 /* tp_as_async */
    0,                                               /* tp_repr */
    0,                                               /* tp_as_number */
    0,                                               /* tp_as_sequence */
    0,                                               /* tp_as_mapping */
    0,                                               /* tp_hash */
    0,                                               /* tp_call */
    0,                                               /* tp_str */
    PyObject_GenericGetAttr,                         /* tp_getattro */
    0,                                               /* tp_setattro */
    0,                                               /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,         /* tp_flags */
    0,                                               /* tp_doc */
    (traverseproc)Nuitka_AsyncgenAthrow_traverse,    /* tp_traverse */
    0,                                               /* tp_clear */
    0,                                               /* tp_richcompare */
    0,                                               /* tp_weaklistoffset */
    PyObject_SelfIter,                               /* tp_iter */
    (iternextfunc)Nuitka_AsyncgenAthrow_iternext,    /* tp_iternext */
    Nuitka_AsyncgenAthrow_methods,                   /* tp_methods */
    0,                                               /* tp_members */
    0,                                               /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    0,                                               /* tp_init */
    0,                                               /* tp_alloc */
    0,                                               /* tp_new */
};

static PyObject *Nuitka_AsyncgenAthrow_New( struct Nuitka_AsyncgenObject *asyncgen, PyObject *args )
{
    struct Nuitka_AsyncgenAthrowObject *result;

    allocateFromFreeListFixed(
        free_list_asyncgen_athrows,
        struct Nuitka_AsyncgenAthrowObject,
        Nuitka_AsyncgenAthrow_Type
    )

    Py_INCREF( asyncgen );
    result->m_gen = asyncgen;

    Py_XINCREF( args );
    result->m_args = args;

    result->m_state = AWAITABLE_STATE_INIT;

    Nuitka_GC_Track( result );
    return (PyObject*)result;
}

static void RAISE_ASYNCGEN_EXCEPTION( struct Nuitka_AsyncgenObject *asyncgen )
{
    CHECK_OBJECT( asyncgen->m_exception_type );

    RESTORE_ERROR_OCCURRED(
        asyncgen->m_exception_type,
        asyncgen->m_exception_value,
        asyncgen->m_exception_tb
    );

    asyncgen->m_exception_type = NULL;
    asyncgen->m_exception_value = NULL;
    asyncgen->m_exception_tb = NULL;

    assert( ERROR_OCCURRED() );
}

extern PyObject *ERROR_GET_STOP_ITERATION_VALUE();
extern PyObject *PyGen_Send( PyGenObject *gen, PyObject *arg );
extern PyObject *const_str_plain_send, *const_str_plain_throw, *const_str_plain_close;

static PyObject *yieldFromAsyncgen( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
{
    // This is the value, propagated back and forth the sub-generator and the
    // yield from consumer.
    PyObject *send_value = Py_None;

    while( 1 )
    {
        CHECK_OBJECT( value );

        // Send iteration value to the sub-generator, which may be a CPython
        // generator object, something with an iterator next, or a send method,
        // where the later is only required if values other than "None" need to
        // be passed in.
        PyObject *retval;

        // Exception, was thrown into us, need to send that to sub-generator.
        if ( asyncgen->m_exception_type )
        {
            // The yielding generator is being closed, but we also are tasked to
            // immediately close the currently running sub-generator.
            if ( EXCEPTION_MATCH_BOOL_SINGLE( asyncgen->m_exception_type, PyExc_GeneratorExit ) )
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

                RAISE_ASYNCGEN_EXCEPTION( asyncgen );

                return NULL;
            }

            PyObject *throw_method = PyObject_GetAttr( value, const_str_plain_throw );

            if ( throw_method )
            {
                retval = PyObject_CallFunctionObjArgs( throw_method, asyncgen->m_exception_type, asyncgen->m_exception_value, asyncgen->m_exception_tb, NULL );
                Py_DECREF( throw_method );

                if (unlikely( send_value == NULL ))
                {
                    if ( EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_StopIteration ) )
                    {
                        return ERROR_GET_STOP_ITERATION_VALUE();
                    }

                    return NULL;
                }

                asyncgen->m_exception_type = NULL;
                asyncgen->m_exception_value = NULL;
                asyncgen->m_exception_tb = NULL;
            }
            else if ( EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_AttributeError ) )
            {
                CLEAR_ERROR_OCCURRED();

                RAISE_ASYNCGEN_EXCEPTION( asyncgen );

                return NULL;
            }
            else
            {
                assert( ERROR_OCCURRED() );

                Py_CLEAR( asyncgen->m_exception_type );
                Py_CLEAR( asyncgen->m_exception_value );
                Py_CLEAR( asyncgen->m_exception_tb );

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

            // No exception we take it as stop iteration.
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
            asyncgen->m_yielded = retval;

            asyncgen->m_yieldfrom = value;

            // Return to the calling context.
            swapFiber( &asyncgen->m_yielder_context, &asyncgen->m_caller_context );

            asyncgen->m_yieldfrom = NULL;

            send_value = asyncgen->m_yielded;

            if ( ERROR_OCCURRED() )
            {
                assert( asyncgen->m_exception_type != NULL );
                CLEAR_ERROR_OCCURRED();
            }
        }
    }
}


PyObject *ASYNCGEN_AWAIT( struct Nuitka_AsyncgenObject *asyncgen, PyObject *awaitable )
{
#if _DEBUG_ASYNCGEN
    PRINT_STRING("AWAIT entry:");

    PRINT_ITEM( awaitable );
    PRINT_NEW_LINE();
#endif

    PyObject *awaitable_iter = PyCoro_GetAwaitableIter( awaitable );

    if (unlikely( awaitable_iter == NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Coroutine_Check( awaitable ) )
    {
        struct Nuitka_CoroutineObject *awaited_coroutine = (struct Nuitka_CoroutineObject *)awaitable;

        if ( awaited_coroutine->m_awaiting )
        {
            Py_DECREF( awaitable_iter );

            PyErr_Format(
                PyExc_RuntimeError,
                "coroutine is being awaited already"
            );

            return NULL;
        }
    }

    asyncgen->m_awaiting = true;
    PyObject *retval = yieldFromAsyncgen( asyncgen, awaitable_iter );
    asyncgen->m_awaiting = false;

    Py_DECREF( awaitable_iter );

#if _DEBUG_ASYNCGEN
    PRINT_STRING("AWAIT exit");

    PRINT_ITEM( retval );
    PRINT_NEW_LINE();
#endif

    return retval;
}

PyObject *ASYNCGEN_AWAIT_IN_HANDLER( struct Nuitka_AsyncgenObject *asyncgen, PyObject *awaitable )
{
#if _DEBUG_ASYNCGEN
    PRINT_STRING("AWAIT entry:");

    PRINT_ITEM( awaitable );
    PRINT_NEW_LINE();
#endif

    PyObject *awaitable_iter = PyCoro_GetAwaitableIter( awaitable );

    if (unlikely( awaitable_iter == NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Coroutine_Check( awaitable ) )
    {
        struct Nuitka_CoroutineObject *awaited_coroutine = (struct Nuitka_CoroutineObject *)awaitable;

        if ( awaited_coroutine->m_awaiting )
        {
            Py_DECREF( awaitable_iter );

            PyErr_Format(
                PyExc_RuntimeError,
                "coroutine is being awaited already"
            );

            return NULL;
        }
    }

    /* When yielding from an exception handler in Python3, the exception
     * preserved to the frame is restore, while the current one is put there.
     */
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *saved_exception_type = EXC_TYPE(thread_state);
    PyObject *saved_exception_value = EXC_VALUE(thread_state);
    PyObject *saved_exception_traceback = EXC_TRACEBACK(thread_state);

    if ( saved_exception_type ) CHECK_OBJECT( saved_exception_type );
    if ( saved_exception_value ) CHECK_OBJECT( saved_exception_value );
    if ( saved_exception_traceback ) CHECK_OBJECT( saved_exception_traceback );

#if PYTHON_VERSION < 370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;
#else
    EXC_TYPE(thread_state) = asyncgen->m_exc_state.exc_type;
    EXC_VALUE(thread_state) = asyncgen->m_exc_state.exc_value;
    EXC_TRACEBACK(thread_state) = asyncgen->m_exc_state.exc_traceback;
#endif

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("YIELD exit:\n");
    PRINT_EXCEPTION( thread_state->exc_type, thread_state->exc_value, (PyObject *)thread_state->exc_traceback );
#endif

#if PYTHON_VERSION < 370
    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
    asyncgen->m_exc_state.exc_type = saved_exception_type;
    asyncgen->m_exc_state.exc_value = saved_exception_value;
    asyncgen->m_exc_state.exc_traceback = saved_exception_traceback;
#endif

    if ( saved_exception_type ) CHECK_OBJECT( saved_exception_type );
    if ( saved_exception_value ) CHECK_OBJECT( saved_exception_value );
    if ( saved_exception_traceback ) CHECK_OBJECT( saved_exception_traceback );

    asyncgen->m_awaiting = true;
    PyObject *retval = yieldFromAsyncgen( asyncgen, awaitable_iter );
    asyncgen->m_awaiting = false;

    Py_DECREF( awaitable_iter );

    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.
    thread_state = PyThreadState_GET();

    saved_exception_type = EXC_TYPE(thread_state);
    saved_exception_value = EXC_VALUE(thread_state);
    saved_exception_traceback = EXC_TRACEBACK(thread_state);

    if ( saved_exception_type ) CHECK_OBJECT( saved_exception_type );
    if ( saved_exception_value ) CHECK_OBJECT( saved_exception_value );
    if ( saved_exception_traceback ) CHECK_OBJECT( saved_exception_traceback );

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("YIELD return:\n");
    PRINT_EXCEPTION( thread_state->exc_type, thread_state->exc_value, (PyObject *)thread_state->exc_traceback );
#endif

#if PYTHON_VERSION < 370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
    EXC_TYPE(thread_state) = asyncgen->m_exc_state.exc_type;
    EXC_VALUE(thread_state) = asyncgen->m_exc_state.exc_value;
    EXC_TRACEBACK(thread_state) = asyncgen->m_exc_state.exc_traceback;

    asyncgen->m_exc_state.exc_type = saved_exception_type;
    asyncgen->m_exc_state.exc_value = saved_exception_value;
    asyncgen->m_exc_state.exc_traceback = saved_exception_traceback;
#endif

    if ( EXC_TYPE(thread_state) ) CHECK_OBJECT( EXC_TYPE(thread_state) );
    if ( EXC_VALUE(thread_state) ) CHECK_OBJECT( EXC_VALUE(thread_state) );
    if ( EXC_TRACEBACK(thread_state) ) CHECK_OBJECT( EXC_TRACEBACK(thread_state) );


#if _DEBUG_ASYNCGEN
    PRINT_STRING("AWAIT exit");

    PRINT_ITEM( retval );
    PRINT_NEW_LINE();
#endif

    return retval;
}

extern PyObject *Nuitka_AIterWrapper_New( PyObject *aiter );

PyObject *ASYNCGEN_ASYNC_MAKE_ITERATOR( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
{
#if _DEBUG_ASYNCGEN
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

    /* Starting with Python 3.5.2 it is acceptable to return an async iterator
     * directly, instead of an awaitable.
     */
    if ( Py_TYPE( iter )->tp_as_async != NULL &&
         Py_TYPE( iter )->tp_as_async->am_anext != NULL)
    {

        PyObject *wrapper = Nuitka_AIterWrapper_New( iter );
        Py_DECREF( iter );

        iter = wrapper;
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

    PyObject *retval = yieldFromAsyncgen( asyncgen, awaitable_iter );

    Py_DECREF( awaitable_iter );

#if _DEBUG_ASYNCGEN
    PRINT_STRING("AITER exit");
    PRINT_ITEM( retval );
    PRINT_NEW_LINE();
#endif

    return retval;
}

PyObject *ASYNCGEN_ASYNC_ITERATOR_NEXT( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
{
#if _DEBUG_ASYNCGEN
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

    PyObject *retval = yieldFromAsyncgen( asyncgen, awaitable_iter );

    Py_DECREF( awaitable_iter );

#if _DEBUG_ASYNCGEN
PRINT_STRING("ANEXT exit");
PRINT_ITEM( retval );
PRINT_NEW_LINE();
#endif

    return retval;
}

void _initCompiledAsyncgenTypes( void )
{
    PyType_Ready( &Nuitka_Asyncgen_Type );
    PyType_Ready( &Nuitka_AsyncgenAsend_Type );
    PyType_Ready( &Nuitka_AsyncgenAthrow_Type );
    PyType_Ready( &Nuitka_AsyncgenValueWrapper_Type );
}
