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


static PyObject *Nuitka_Generator_tp_repr( struct Nuitka_GeneratorObject *generator )
{
#if PYTHON_VERSION < 300
    return PyString_FromFormat(
        "<compiled_generator object %s at %p>",
        Nuitka_String_AsString( generator->m_name ),
        generator
    );
#else
    return PyUnicode_FromFormat(
        "<compiled_generator object %s at %p>",
#if PYTHON_VERSION < 350
        Nuitka_String_AsString( generator->m_name ),
#else
        Nuitka_String_AsString( generator->m_qualname ),
#endif
        generator
    );
#endif
}

static long Nuitka_Generator_tp_traverse( struct Nuitka_GeneratorObject *generator, visitproc visit, void *arg )
{
    // Not needed.
    // Py_VISIT( (PyObject *)generator->m_frame );

    return 0;
}

static void Nuitka_Generator_release_closure( struct Nuitka_GeneratorObject *generator )
{
    for( Py_ssize_t i = 0; i < generator->m_closure_given; i++ )
    {
        CHECK_OBJECT( generator->m_closure[ i ] );
        Py_DECREF( generator->m_closure[ i ] );
    }

    generator->m_closure_given = 0;
}

#ifndef _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
// For the generator object fiber entry point, we may need to follow what
// "makecontext" will support and that is only a list of integers, but we will need
// to push a pointer through it, and so it's two of them, which might be fully
// sufficient.

#ifdef _NUITKA_MAKECONTEXT_INTS
static void Nuitka_Generator_entry_point( int address_1, int address_2 )
{
    // Restore the pointer from integers should it be necessary, depending on
    // the platform. This requires pointers to be no larger that to "int" value.
    int addresses[2] =
    {
        address_1,
        address_2
    };

    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)*(uintptr_t *)&addresses[0];
#else
static void Nuitka_Generator_entry_point( struct Nuitka_GeneratorObject *generator )
{
#endif
    ((generator_code)generator->m_code)( generator );

    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );
}
#endif


static PyObject *Nuitka_Generator_send2( struct Nuitka_GeneratorObject *generator, PyObject *value )
{
    if ( generator->m_status != status_Finished )
    {
        PyThreadState *thread_state = PyThreadState_GET();

#if PYTHON_VERSION < 300
        PyObject *saved_exception_type = thread_state->exc_type;
        PyObject *saved_exception_value = NULL;
        PyTracebackObject *saved_exception_traceback = NULL;

        if ( saved_exception_type != Py_None && saved_exception_type != NULL )
        {
            Py_INCREF( saved_exception_type );
            saved_exception_value = thread_state->exc_value;
            Py_XINCREF( saved_exception_value );
            saved_exception_traceback = (PyTracebackObject *)thread_state->exc_traceback;
            Py_XINCREF( saved_exception_traceback );
        }
#endif

        if ( generator->m_running )
        {
            PyErr_Format( PyExc_ValueError, "generator already executing" );
            return NULL;
        }

        if ( generator->m_status == status_Unused )
        {
#ifndef _NUITKA_EXPERIMENTAL_GENERATOR_GOTO

            // Prepare the generator context to run.
            int res = prepareFiber( &generator->m_yielder_context, (void *)Nuitka_Generator_entry_point, (uintptr_t)generator );

            if ( res != 0 )
            {
                PyErr_Format( PyExc_MemoryError, "generator cannot be allocated" );
                return NULL;
            }
#endif

            generator->m_status = status_Running;
        }

        // Put the generator back on the frame stack.
        PyFrameObject *return_frame = thread_state->frame;
#ifndef __NUITKA_NO_ASSERT__
        if ( return_frame )
        {
            assertFrameObject( (struct Nuitka_FrameObject *)return_frame );
        }
#endif

        if ( generator->m_frame )
        {
            // It would be nice if our frame were still alive. Nobody had the
            // right to release it.
            assertFrameObject( generator->m_frame );

            // It's not supposed to be on the top right now.
            assert( return_frame != &generator->m_frame->m_frame );

            Py_XINCREF( return_frame );
            generator->m_frame->m_frame.f_back = return_frame;

            thread_state->frame = &generator->m_frame->m_frame;
        }

        // Continue the yielder function while preventing recursion.
        generator->m_running = true;

#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO

        PyObject *yielded = ((generator_code)generator->m_code)( generator, value );
#else
        generator->m_yielded = value;
        swapFiber( &generator->m_caller_context, &generator->m_yielder_context );
        PyObject *yielded = generator->m_yielded;
#endif

        generator->m_running = false;

        thread_state = PyThreadState_GET();

        // Remove the generator from the frame stack.
        if ( generator->m_frame )
        {
            assert( thread_state->frame == &generator->m_frame->m_frame );
            assertFrameObject( generator->m_frame );

            Py_CLEAR( generator->m_frame->m_frame.f_back );
        }

        thread_state->frame = return_frame;

        if ( yielded == NULL )
        {
            generator->m_status = status_Finished;

            Py_XDECREF( generator->m_frame );
            generator->m_frame = NULL;

            Nuitka_Generator_release_closure( generator );

#if PYTHON_VERSION < 300
            if ( saved_exception_type != NULL && saved_exception_type != Py_None )
            {
                Py_DECREF( saved_exception_type );
                Py_XDECREF( saved_exception_value );
                Py_XDECREF( saved_exception_traceback );
            }
#endif

#if PYTHON_VERSION >= 350
            if ( generator->m_code_object->co_flags & CO_FUTURE_GENERATOR_STOP &&
                 GET_ERROR_OCCURRED() == PyExc_StopIteration )
            {
                PyObject *saved_exception_type, *saved_exception_value;
                PyTracebackObject *saved_exception_tb;

                FETCH_ERROR_OCCURRED( &saved_exception_type, &saved_exception_value, &saved_exception_tb );
                NORMALIZE_EXCEPTION( &saved_exception_type, &saved_exception_value, &saved_exception_tb );

                PyErr_Format(
                    PyExc_RuntimeError,
                    "generator raised StopIteration"
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
#endif

            return NULL;
        }
        else
        {
#if PYTHON_VERSION < 300
            PyObject *old_type  = thread_state->exc_type;
            PyObject *old_value = thread_state->exc_value;
            PyTracebackObject *old_tb = (PyTracebackObject *)thread_state->exc_traceback;

            // Set sys attributes in the fastest possible way.
            PyObject *sys_dict = thread_state->interp->sysdict;
            CHECK_OBJECT( sys_dict );

            if ( saved_exception_type != NULL && saved_exception_type != Py_None )
            {
                thread_state->exc_type = saved_exception_type;
                thread_state->exc_value = saved_exception_value;
                thread_state->exc_traceback = (PyObject *)saved_exception_traceback;

                Py_XDECREF( old_type );
                Py_XDECREF( old_value );
                Py_XDECREF( old_tb );


                if ( old_type != saved_exception_type )
                {
                    PyDict_SetItem( sys_dict, const_str_plain_exc_type, saved_exception_type );
                }
                if ( saved_exception_value != old_value )
                {
                    PyDict_SetItem( sys_dict, const_str_plain_exc_value, saved_exception_value ? saved_exception_value : Py_None );
                }
                if ( saved_exception_traceback != old_tb )
                {
                    PyDict_SetItem( sys_dict, const_str_plain_exc_traceback, saved_exception_traceback ? (PyObject *)saved_exception_traceback : Py_None );
                }
            }
            else
            {
                thread_state->exc_type = Py_None;
                thread_state->exc_value = Py_None;
                thread_state->exc_traceback = (PyObject *)Py_None;

                Py_INCREF( Py_None );
                Py_INCREF( Py_None );
                Py_INCREF( Py_None );

                Py_XDECREF( old_type );
                Py_XDECREF( old_value );
                Py_XDECREF( old_tb );

                if ( old_type != Py_None )
                {
                    PyDict_SetItem( sys_dict, const_str_plain_exc_type, Py_None );
                }
                if ( old_value != Py_None )
                {
                    PyDict_SetItem( sys_dict, const_str_plain_exc_value, Py_None );
                }
                if ( old_tb != (PyTracebackObject *)Py_None )
                {
                    PyDict_SetItem( sys_dict, const_str_plain_exc_traceback, Py_None );
                }
            }
#endif

            return yielded;
        }
    }
    else
    {
        return NULL;
    }
}

static PyObject *Nuitka_Generator_send( struct Nuitka_GeneratorObject *generator, PyObject *value )
{
    if ( generator->m_status == status_Unused && value != NULL && value != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "can't send non-None value to a just-started generator" );
        return NULL;
    }

    PyObject *result = Nuitka_Generator_send2( generator, value );

    if ( result == NULL )
    {
        if ( GET_ERROR_OCCURRED() == NULL )
        {
            RESTORE_ERROR_OCCURRED( PyExc_StopIteration, NULL, NULL );
            Py_INCREF( PyExc_StopIteration );
        }
    }

    return result;
}

static PyObject *Nuitka_Generator_tp_iternext( struct Nuitka_GeneratorObject *generator )
{
    return Nuitka_Generator_send2( generator, Py_None );
}

/* Our own qiter interface, which is for quicker simple loop style iteration,
   that does not send anything in. */
PyObject *Nuitka_Generator_qiter( struct Nuitka_GeneratorObject *generator, bool *finished )
{
    PyObject *result = Nuitka_Generator_send2( generator, Py_None );

    if ( result == NULL )
    {
        if (unlikely( !CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED() ))
        {
            *finished = false;
            return NULL;
        }

        *finished = true;
        return NULL;
    }

    *finished = false;
    return result;
}



#if PYTHON_VERSION < 340
static
#endif
PyObject *Nuitka_Generator_close( struct Nuitka_GeneratorObject *generator, PyObject *args )
{
    if ( generator->m_status == status_Running )
    {
        Py_INCREF( PyExc_GeneratorExit );
        generator->m_exception_type = PyExc_GeneratorExit;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        PyObject *result = Nuitka_Generator_send2( generator, Py_None );

        if (unlikely( result ))
        {
            Py_DECREF( result );

            PyErr_Format( PyExc_RuntimeError, "generator ignored GeneratorExit" );
            return NULL;
        }
        else
        {
            PyObject *error = GET_ERROR_OCCURRED();

            // StopIteration as exception.
            if ( error == NULL )
            {
                Py_INCREF( Py_None );
                return Py_None;
            }

            // Maybe another acceptable exception for generator exit.
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

static PyObject *Nuitka_Generator_throw( struct Nuitka_GeneratorObject *generator, PyObject *args )
{
    assert( generator->m_exception_type == NULL );
    assert( generator->m_exception_value == NULL );
    assert( generator->m_exception_tb == NULL );

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

    if ( generator->m_status == status_Running )
    {
        PyObject *result = Nuitka_Generator_send2( generator, Py_None );

        if ( result == NULL )
        {
            if ( GET_ERROR_OCCURRED() == NULL )
            {
                RESTORE_ERROR_OCCURRED( PyExc_StopIteration, NULL, NULL );
                Py_INCREF( PyExc_StopIteration );
            }
        }

        return result;
    }
    else if ( generator->m_status == status_Finished )
    {
        RESTORE_ERROR_OCCURRED(
            generator->m_exception_type,
            generator->m_exception_value,
            generator->m_exception_tb
        );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        return NULL;
    }
    else
    {
        if ( generator->m_exception_tb == NULL )
        {
            // TODO: Our compiled objects really need a way to store common
            // stuff in a "shared" part across all instances, and outside of
            // run time, so we could reuse this.
            struct Nuitka_FrameObject *frame = MAKE_FUNCTION_FRAME(
                generator->m_code_object,
                generator->m_module,
                0
            );

            generator->m_exception_tb = MAKE_TRACEBACK(
                frame,
                generator->m_code_object->co_firstlineno
            );

            Py_DECREF( frame );
        }

        RESTORE_ERROR_OCCURRED(
            generator->m_exception_type,
            generator->m_exception_value,
            generator->m_exception_tb
        );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        generator->m_status = status_Finished;

        return NULL;
    }
}

#if PYTHON_VERSION >= 340
static void Nuitka_Generator_tp_del( struct Nuitka_GeneratorObject *generator )
{
    if ( generator->m_status != status_Running )
    {
        return;
    }

    PyObject *error_type, *error_value;
    PyTracebackObject *error_traceback;

    FETCH_ERROR_OCCURRED( &error_type, &error_value, &error_traceback );

    PyObject *close_result = Nuitka_Generator_close( generator, NULL );

    if (unlikely( close_result == NULL ))
    {
        PyErr_WriteUnraisable( (PyObject *)generator );
    }
    else
    {
        Py_DECREF( close_result );
    }

    /* Restore the saved exception if any. */
    RESTORE_ERROR_OCCURRED( error_type, error_value, error_traceback );
}

#endif

#define MAX_GENERATOR_FREE_LIST_COUNT 100
static struct Nuitka_GeneratorObject *free_list_generators = NULL;
static int free_list_generators_count = 0;

static void Nuitka_Generator_tp_dealloc( struct Nuitka_GeneratorObject *generator )
{
    // Revive temporarily.
    assert( Py_REFCNT( generator ) == 0 );
    Py_REFCNT( generator ) = 1;

    // Save the current exception, if any, we must preserve it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED( &save_exception_type, &save_exception_value, &save_exception_tb );

    if ( generator->m_status == status_Running )
    {
        PyObject *close_result = Nuitka_Generator_close( generator, NULL );

        if (unlikely( close_result == NULL ))
        {
            PyErr_WriteUnraisable( (PyObject *)generator );
        }
        else
        {
            Py_DECREF( close_result );
        }
    }

    Nuitka_Generator_release_closure( generator );

    Py_XDECREF( generator->m_frame );

    assert( Py_REFCNT( generator ) == 1 );
    Py_REFCNT( generator ) = 0;

#ifndef _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
    releaseFiber( &generator->m_yielder_context );
#endif

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack( generator );

    if ( generator->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)generator );
        assert( !ERROR_OCCURRED() );
    }

    Py_DECREF( generator->m_name );

#if PYTHON_VERSION >= 350
    Py_DECREF( generator->m_qualname );
#endif

    /* Put the object into freelist or release to GC */
    releaseToFreeList(
        free_list_generators,
        generator,
        MAX_GENERATOR_FREE_LIST_COUNT
    );

    RESTORE_ERROR_OCCURRED( save_exception_type, save_exception_value, save_exception_tb );
}

static PyObject *Nuitka_Generator_get_name( struct Nuitka_GeneratorObject *generator )
{
    PyObject *result = generator->m_name;
    Py_INCREF( result );
    return result;
}

#if PYTHON_VERSION >= 350
static int Nuitka_Generator_set_name( struct Nuitka_GeneratorObject *generator, PyObject *value )
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

    PyObject *tmp = generator->m_name;
    Py_INCREF( value );
    generator->m_name = value;
    Py_DECREF( tmp );

    return 0;
}

static PyObject *Nuitka_Generator_get_qualname( struct Nuitka_GeneratorObject *generator )
{
    PyObject *result = generator->m_qualname;
    Py_INCREF( result );
    return result;
}

static int Nuitka_Generator_set_qualname( struct Nuitka_GeneratorObject *generator, PyObject *value )
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

    PyObject *tmp = generator->m_qualname;
    Py_INCREF( value );
    generator->m_qualname = value;
    Py_DECREF( tmp );

    return 0;
}

static PyObject *Nuitka_Generator_get_yieldfrom( struct Nuitka_GeneratorObject *generator )
{
    if ( generator->m_yieldfrom )
    {
        Py_INCREF( generator->m_yieldfrom );
        return generator->m_yieldfrom;
    }
    else
    {
        Py_INCREF( Py_None );
        return Py_None;
    }
}

#endif

static PyObject *Nuitka_Generator_get_code( struct Nuitka_GeneratorObject *generator )
{
    PyObject *result = (PyObject *)generator->m_code_object;
    Py_INCREF( result );
    return result;
}

static int Nuitka_Generator_set_code( struct Nuitka_GeneratorObject *generator, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "gi_code is not writable in Nuitka" );
    return -1;
}

static PyObject *Nuitka_Generator_get_frame( struct Nuitka_GeneratorObject *generator )
{
    PyObject *result;

    if ( generator->m_frame )
    {
        result = (PyObject *)generator->m_frame;
    }
    else
    {
        result = Py_None;
    }

    Py_INCREF( result );
    return result;
}

static int Nuitka_Generator_set_frame( struct Nuitka_GeneratorObject *generator, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "gi_frame is not writable in Nuitka" );
    return -1;
}

static PyGetSetDef Nuitka_Generator_getsetlist[] =
{
#if PYTHON_VERSION < 350
    { (char *)"__name__", (getter)Nuitka_Generator_get_name, NULL, NULL },
#else
    { (char *)"__name__", (getter)Nuitka_Generator_get_name, (setter)Nuitka_Generator_set_name, NULL },
    { (char *)"__qualname__", (getter)Nuitka_Generator_get_qualname, (setter)Nuitka_Generator_set_qualname, NULL },
    { (char *)"gi_yieldfrom", (getter)Nuitka_Generator_get_yieldfrom, NULL, NULL },
#endif
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
    /* The type of "gi_running" changed in Python3. */
#if PYTHON_VERSION < 330
    { (char *)"gi_running", T_INT, offsetof(struct Nuitka_GeneratorObject, m_running), READONLY },
#else
    { (char *)"gi_running", T_BOOL, offsetof(struct Nuitka_GeneratorObject, m_running), READONLY },
#endif
    { NULL }
};

PyTypeObject Nuitka_Generator_Type =
{
    PyVarObject_HEAD_INIT(NULL, 0)
    "compiled_generator",                            /* tp_name */
    sizeof(struct Nuitka_GeneratorObject),           /* tp_basicsize */
    sizeof(struct Nuitka_CellObject *),              /* tp_itemsize */
    (destructor)Nuitka_Generator_tp_dealloc,         /* tp_dealloc */
    0,                                               /* tp_print */
    0,                                               /* tp_getattr */
    0,                                               /* tp_setattr */
    0,                                               /* tp_compare */
    (reprfunc)Nuitka_Generator_tp_repr,              /* tp_repr */
    0,                                               /* tp_as_number */
    0,                                               /* tp_as_sequence */
    0,                                               /* tp_as_mapping */
    0,                                               /* tp_hash */
    0,                                               /* tp_call */
    0,                                               /* tp_str */
    PyObject_GenericGetAttr,                         /* tp_getattro */
    0,                                               /* tp_setattro */
    0,                                               /* tp_as_buffer */
#if PYTHON_VERSION < 340
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
#else
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE,
#endif
                                                     /* tp_flags */
    0,                                               /* tp_doc */
    (traverseproc)Nuitka_Generator_tp_traverse,      /* tp_traverse */
    0,                                               /* tp_clear */
    0,                                               /* tp_richcompare */
    offsetof(struct Nuitka_GeneratorObject, m_weakrefs),  /* tp_weaklistoffset */
    PyObject_SelfIter,                               /* tp_iter */
    (iternextfunc)Nuitka_Generator_tp_iternext,      /* tp_iternext */
    Nuitka_Generator_methods,                        /* tp_methods */
    Nuitka_Generator_members,                        /* tp_members */
    Nuitka_Generator_getsetlist,                     /* tp_getset */
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
    0                                                /* tp_version_tag */
#if PYTHON_VERSION >= 340
    ,(destructor)Nuitka_Generator_tp_del             /* tp_finalizer */
#endif
};

void _initCompiledGeneratorType( void )
{
    PyType_Ready( &Nuitka_Generator_Type );
}

#if PYTHON_VERSION < 350
PyObject *Nuitka_Generator_New( generator_code code, PyObject *module, PyObject *name, PyCodeObject *code_object, Py_ssize_t closure_given )
#else
PyObject *Nuitka_Generator_New( generator_code code, PyObject *module, PyObject *name, PyObject *qualname, PyCodeObject *code_object, Py_ssize_t closure_given )
#endif
{
    struct Nuitka_GeneratorObject *result;

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(
        free_list_generators,
        struct Nuitka_GeneratorObject,
        Nuitka_Generator_Type,
        closure_given
    );

    assert( result != NULL );
    CHECK_OBJECT( result );

    assert( Py_SIZE( result ) >= closure_given );

    result->m_code = (void *)code;

    CHECK_OBJECT( module );
    result->m_module = module;

    CHECK_OBJECT( name );
    result->m_name = name;
    Py_INCREF( name );

#if PYTHON_VERSION >= 350
    CHECK_OBJECT( qualname );

    result->m_qualname = qualname;
    Py_INCREF( qualname );

    result->m_yieldfrom = NULL;
#endif

    /* Note: The closure is set externally. */
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = false;

    result->m_exception_type = NULL;
    result->m_exception_value = NULL;
    result->m_exception_tb = NULL;

#ifndef _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
    result->m_yielded = NULL;
#else
    result->m_yield_return_index = 0;
#endif

    result->m_frame = NULL;
    result->m_code_object = code_object;

#ifndef _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
    initFiber( &result->m_yielder_context );
#endif

    Nuitka_GC_Track( result );
    return (PyObject *)result;
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

    assert( frame == NULL || PyFrame_Check( frame ));

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

        Py_INCREF( tmp );
        *(frame->f_stacktop++) = tmp;
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
// TODO: Check how this should be changed for 3.7 where the generator owns
// things.

#if PYTHON_VERSION < 370
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
#endif

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

    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;
    FETCH_ERROR_OCCURRED( &exception_type, &exception_value, &exception_tb );

    Py_DECREF( exception_type );
    Py_XDECREF( exception_tb );

    PyObject *value = NULL;

    if ( exception_value )
    {
        if ( EXCEPTION_MATCH_BOOL_SINGLE( exception_value, PyExc_StopIteration ) )
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
        Py_INCREF( Py_None );
        value = Py_None;
    }

    return value;
}

static void RAISE_GENERATOR_EXCEPTION( struct Nuitka_GeneratorObject *generator )
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

static PyObject *_YIELD_FROM( struct Nuitka_GeneratorObject *generator, PyObject *value )
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
        else if ( PyGen_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
#if PYTHON_VERSION >= 350
        else if ( PyCoro_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
#endif
        else if ( send_value == Py_None && Py_TYPE( value )->tp_iternext != NULL )
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

#if PYTHON_VERSION >= 350
            generator->m_yieldfrom = value;
#endif
            // Return to the calling context.
            swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

#if PYTHON_VERSION >= 350
            generator->m_yieldfrom = NULL;
#endif

            send_value = generator->m_yielded;

            CHECK_OBJECT( send_value );
        }
    }
}

PyObject *GENERATOR_YIELD_FROM( struct Nuitka_GeneratorObject *generator, PyObject *target )
{
    PyObject *value;

#if PYTHON_VERSION >= 350
    if ( PyCoro_CheckExact( target ) || Nuitka_Coroutine_Check( target ))
    {
        if (unlikely( (generator->m_code_object->co_flags & CO_ITERABLE_COROUTINE) == 0 ))
        {
            PyErr_SetString(
                PyExc_TypeError,
                "cannot 'yield from' a coroutine object in a non-coroutine generator"
            );
            return NULL;
        }

        return _YIELD_FROM( generator, target );
    }
    else
#endif
    {
        value = MAKE_ITERATOR( target );

        if (unlikely( value == NULL ))
        {
            return NULL;
        }

        PyObject *result = _YIELD_FROM( generator, value );

        Py_DECREF( value );

        return result;
    }
}

// Note: This is copy if YIELD_FROM with changes only at the end. As it's not
// easy to split up, we are going to tolerate the copy.
static PyObject *_YIELD_FROM_IN_HANDLER( struct Nuitka_GeneratorObject *generator, PyObject *value )
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
                else if ( !EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_AttributeError ) )
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
        else if ( PyGen_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
#if PYTHON_VERSION >= 350
        else if ( PyCoro_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
#endif
        else if ( send_value == Py_None && Py_TYPE( value )->tp_iternext != NULL )
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
            if ( !ERROR_OCCURRED() )
            {
                Py_INCREF( Py_None );
                return Py_None;
            }

            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            if (likely( EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_StopIteration ) ))
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

            PyObject *saved_exception_type = EXC_TYPE(thread_state);
            PyObject *saved_exception_value = EXC_VALUE(thread_state);
            PyObject *saved_exception_traceback = EXC_TRACEBACK(thread_state);

#if PYTHON_VERSION < 370
            EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
            EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
            EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;

            thread_state->frame->f_exc_type = saved_exception_type;
            thread_state->frame->f_exc_value = saved_exception_value;
            thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
            EXC_TYPE(thread_state) = generator->m_exc_state.exc_type;
            EXC_VALUE(thread_state) = generator->m_exc_state.exc_value;
            EXC_TRACEBACK(thread_state) = generator->m_exc_state.exc_traceback;

            generator->m_exc_state.exc_type = saved_exception_type;
            generator->m_exc_state.exc_value = saved_exception_value;
            generator->m_exc_state.exc_traceback = saved_exception_traceback;
#endif

#if PYTHON_VERSION >= 350
            generator->m_yieldfrom = value;
#endif
            // Return to the calling context.
            swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

#if PYTHON_VERSION >= 350
            generator->m_yieldfrom = NULL;
#endif
            // When returning from yield, the exception of the frame is preserved, and
            // the one that enters should be there.
            thread_state = PyThreadState_GET();


            saved_exception_type = EXC_TYPE(thread_state);
            saved_exception_value = EXC_VALUE(thread_state);
            saved_exception_traceback = EXC_TRACEBACK(thread_state);

#if PYTHON_VERSION < 370
            EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
            EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
            EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;

            thread_state->frame->f_exc_type = saved_exception_type;
            thread_state->frame->f_exc_value = saved_exception_value;
            thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
            EXC_TYPE(thread_state) = generator->m_exc_state.exc_type;
            EXC_VALUE(thread_state) = generator->m_exc_state.exc_value;
            EXC_TRACEBACK(thread_state) = generator->m_exc_state.exc_traceback;

            generator->m_exc_state.exc_type = saved_exception_type;
            generator->m_exc_state.exc_value = saved_exception_value;
            generator->m_exc_state.exc_traceback = saved_exception_traceback;
#endif

            send_value = generator->m_yielded;

            CHECK_OBJECT( send_value );
        }
    }
}

PyObject *GENERATOR_YIELD_FROM_IN_HANDLER( struct Nuitka_GeneratorObject *generator, PyObject *target )
{
    PyObject *value;

#if PYTHON_VERSION >= 350
    if ( PyCoro_CheckExact( target ) || Nuitka_Coroutine_Check( target ))
    {
        if (unlikely( (generator->m_code_object->co_flags & CO_ITERABLE_COROUTINE) == 0 ))
        {
            PyErr_SetString(
                PyExc_TypeError,
                "cannot 'yield from' a coroutine object in a non-coroutine generator"
            );
            return NULL;
        }

        return _YIELD_FROM_IN_HANDLER( generator, target );
    }
    else
#endif
    {
        value = MAKE_ITERATOR( target );

        if (unlikely( value == NULL ))
        {
            return NULL;
        }

        PyObject *result = _YIELD_FROM_IN_HANDLER( generator, value );

        Py_DECREF( value );

        return result;
    }
}

#endif

#endif
