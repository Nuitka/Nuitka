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
#ifndef __NUITKA_EXCEPTIONS_H__
#define __NUITKA_EXCEPTIONS_H__

// Exception helpers for generated code and compiled code helpers.

// Did an error occur.
NUITKA_MAY_BE_UNUSED static inline bool ERROR_OCCURED( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type != NULL;
}

// Get the error occured.
NUITKA_MAY_BE_UNUSED static inline PyObject *GET_ERROR_OCCURED( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type;
}

NUITKA_MAY_BE_UNUSED static void PRINT_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyObject *exception_tb )
{
    if ( exception_type != NULL )
    {
        PRINT_ITEM( PyObject_Repr( exception_type ) );
    }
    else
    {
        PRINT_NULL();
    }

    if ( exception_value != NULL  )
    {
        PRINT_ITEM( PyObject_Repr( exception_value ) );
    }
    else
    {
        PRINT_NULL();
    }

    if ( exception_tb != NULL )
    {
        PRINT_ITEM( exception_tb );
    }
    else
    {
        PRINT_NULL();
    }

    PRINT_NEW_LINE();
}

// Fetch the current error into object variables.
NUITKA_MAY_BE_UNUSED static void FETCH_ERROR( PyObject **exception_type, PyObject **exception_value, PyObject **exception_traceback)
{
    PyThreadState *tstate = PyThreadState_GET();

   *exception_type = tstate->curexc_type;
   *exception_value = tstate->curexc_value;
   *exception_traceback = tstate->curexc_traceback;

#if _DEBUG_EXCEPTIONS
   PRINT_STRING("FETCH_ERROR:\n");
   PRINT_EXCEPTION( tstate->curexc_type,  tstate->curexc_value, tstate->curexc_traceback );
#endif

   tstate->curexc_type = NULL;
   tstate->curexc_value = NULL;
   tstate->curexc_traceback = NULL;
}

// Special helper that checks for StopIteration and if so clears it, only
// indicating if it was set.
NUITKA_MAY_BE_UNUSED static bool HAS_STOP_ITERATION_OCCURED( void )
{
    if ( PyErr_ExceptionMatches( PyExc_StopIteration ) )
    {
        PyErr_Clear();
        return true;
    }
    else
    {
        return false;
    }
}

#if PYTHON_VERSION < 300
NUITKA_MAY_BE_UNUSED static void dumpTraceback( PyTracebackObject *traceback )
{
    PRINT_STRING("Dumping traceback:\n");

    if ( traceback == NULL ) PRINT_STRING( "<NULL traceback?!>\n" );

    while( traceback )
    {
        printf( " line %d (frame object chain):\n", traceback->tb_lineno );

        PyFrameObject *frame = traceback->tb_frame;

        while ( frame )
        {
            printf( "  Frame at %s\n", PyString_AsString( PyObject_Str( (PyObject *)frame->f_code )));

            frame = frame->f_back;
        }

        assert( traceback->tb_next != traceback );
        traceback = traceback->tb_next;
    }

    PRINT_STRING("End of Dump.\n");
}
#endif

NUITKA_MAY_BE_UNUSED static inline PyTracebackObject *INCREASE_REFCOUNT( PyTracebackObject *traceback_object )
{
    Py_INCREF( traceback_object );
    return traceback_object;
}

NUITKA_MAY_BE_UNUSED static inline PyTracebackObject *INCREASE_REFCOUNT_X( PyTracebackObject *traceback_object )
{
    Py_XINCREF( traceback_object );
    return traceback_object;
}

// Create a traceback for a given frame. TODO: Probably we ought to have a quick
// cache for it, in case of repeated usage.
NUITKA_MAY_BE_UNUSED static PyTracebackObject *MAKE_TRACEBACK( PyFrameObject *frame )
{
    // assertFrameObject( frame );

    PyTracebackObject *result = PyObject_GC_New( PyTracebackObject, &PyTraceBack_Type );

    result->tb_next = NULL;
    result->tb_frame = frame;

    result->tb_lasti = 0;
    result->tb_lineno = frame->f_lineno;

    Nuitka_GC_Track( result );

    return result;
}

// Add a frame to an existing exception traceback.
NUITKA_MAY_BE_UNUSED static PyTracebackObject *ADD_TRACEBACK( PyFrameObject *frame, PyTracebackObject *exception_tb )
{
    Py_INCREF( frame );

    if ( exception_tb->tb_frame != frame || exception_tb->tb_lineno != frame->f_lineno )
    {
        PyTracebackObject *traceback_new = (PyTracebackObject *)MAKE_TRACEBACK( frame );

        traceback_new->tb_next = exception_tb;

        return traceback_new;
    }
    else
    {
        return exception_tb;
    }

}

#if PYTHON_VERSION < 300
extern PyObject *const_str_plain_exc_type, *const_str_plain_exc_value, *const_str_plain_exc_traceback;
#endif

// Helper that sets the current thread exception, releasing the current one, for
// use in this file only.
NUITKA_MAY_BE_UNUSED inline void SET_CURRENT_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyTracebackObject *exception_tb )
{
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *old_type  = thread_state->exc_type;
    PyObject *old_value = thread_state->exc_value;
    PyObject *old_tb    = thread_state->exc_traceback;

    thread_state->exc_type = exception_type;
    thread_state->exc_value = exception_value;
    thread_state->exc_traceback = (PyObject *)exception_tb;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION:\n");
    PRINT_EXCEPTION( exception_type, exception_value, (PyObject *)exception_tb );
#endif


    Py_XDECREF( old_type );
    Py_XDECREF( old_value );
    Py_XDECREF( old_tb );

#if PYTHON_VERSION < 300
    // Set sys attributes in the fastest possible way.
    PyObject *sys_dict = thread_state->interp->sysdict;
    assertObject( sys_dict );

    PyDict_SetItem( sys_dict, const_str_plain_exc_type, exception_type ? exception_type : Py_None );
    PyDict_SetItem( sys_dict, const_str_plain_exc_value, exception_value ? exception_value : Py_None );
    PyDict_SetItem( sys_dict, const_str_plain_exc_traceback, exception_tb ? (PyObject *)exception_tb : Py_None );

    if ( exception_type )
        assert( Py_REFCNT( exception_type ) >= 2 );
    if ( exception_value )
        assert( Py_REFCNT( exception_value ) >= 2 );
    if ( exception_tb )
        assert( Py_REFCNT( exception_tb ) >= 2 );
#endif
}

// Preserve the current exception as the frame to restore.
NUITKA_MAY_BE_UNUSED static inline void PRESERVE_FRAME_EXCEPTION( PyFrameObject *frame_object )
{
    // Setting exception for frame if not already done.
    if ( frame_object->f_exc_type == NULL )
    {
        PyThreadState *thread_state = PyThreadState_GET();

        if ( thread_state->exc_type != NULL && thread_state->exc_type != Py_None )
        {
#if _DEBUG_EXCEPTIONS
            PRINT_STRING("PRESERVE_FRAME_EXCEPTION: preserve thread exception\n");
#endif
            frame_object->f_exc_type = INCREASE_REFCOUNT( thread_state->exc_type );
            frame_object->f_exc_value = INCREASE_REFCOUNT_X( thread_state->exc_value );
            frame_object->f_exc_traceback = INCREASE_REFCOUNT_X( thread_state->exc_traceback );
        }
        else
        {
#if _DEBUG_EXCEPTIONS
            PRINT_STRING("PRESERVE_FRAME_EXCEPTION: no exception to preserve\n");
#endif
            frame_object->f_exc_type = INCREASE_REFCOUNT( Py_None );
            frame_object->f_exc_value = NULL;
            frame_object->f_exc_traceback = NULL;
        }
    }
#if _DEBUG_EXCEPTIONS
    else
    {
        PRINT_STRING("PRESERVE_FRAME_EXCEPTION: already preserving\n");
    }

    PRINT_ITEM( (PyObject *)frame_object );
    PRINT_NEW_LINE();
    PRINT_EXCEPTION( frame_object->f_exc_type,  frame_object->f_exc_value, frame_object->f_exc_traceback );
#endif

}

// Restore a previously preserved exception to the frame.
NUITKA_MAY_BE_UNUSED static inline void RESTORE_FRAME_EXCEPTION( PyFrameObject *frame_object )
{
    if ( frame_object->f_exc_type )
    {
#if _DEBUG_EXCEPTIONS
        PRINT_STRING("RESTORE_FRAME_EXCEPTION: restoring preserved\n");
        PRINT_ITEM( (PyObject *)frame_object );
        PRINT_NEW_LINE();
#endif

        SET_CURRENT_EXCEPTION( frame_object->f_exc_type, frame_object->f_exc_value, (PyTracebackObject *)frame_object->f_exc_traceback );

        frame_object->f_exc_type = NULL;
        frame_object->f_exc_value = NULL;
        frame_object->f_exc_traceback = NULL;
    }
#if _DEBUG_EXCEPTIONS
    else
    {
        PRINT_STRING("RESTORE_FRAME_EXCEPTION: nothing to restore\n");
        PRINT_ITEM( (PyObject *)frame_object );
        PRINT_NEW_LINE();
    }
#endif
}

// Publish an exception, erasing the values of the variables.
NUITKA_MAY_BE_UNUSED static inline void PUBLISH_EXCEPTION( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
#if _DEBUG_EXCEPTIONS
    PRINT_STRING("PUBLISH_EXCEPTION:\n");
#endif
    SET_CURRENT_EXCEPTION( *exception_type, *exception_value, *exception_tb );

    *exception_type = NULL;
    *exception_value = NULL;
    *exception_tb = NULL;
}

// Normalize an exception.
NUITKA_MAY_BE_UNUSED static inline void NORMALIZE_EXCEPTION( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
#if _DEBUG_EXCEPTIONS
    PRINT_STRING("NORMALIZE_EXCEPTION:\n");
    PRINT_EXCEPTION( *exception_type,  *exception_value, (PyObject *)*exception_tb );
#endif

    if ( *exception_type != Py_None && *exception_type != NULL )
    {
        PyErr_NormalizeException( exception_type, exception_value, (PyObject **)exception_tb );
    }

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("normalized:\n");
    PRINT_EXCEPTION( *exception_type,  *exception_value, (PyObject *)*exception_tb );
#endif
}

NUITKA_MAY_BE_UNUSED static inline int EXCEPTION_MATCH_BOOL( PyObject *exception_value, PyObject *exception_checked )
{
#if PYTHON_VERSION >= 300
    if ( PyTuple_Check( exception_checked ))
    {
        Py_ssize_t length = PyTuple_Size( exception_checked );

        for ( Py_ssize_t i = 0; i < length; i += 1 )
        {
            PyObject *element = PyTuple_GET_ITEM( exception_checked, i );

            if (unlikely( !PyExceptionClass_Check( element ) ))
            {
                PyErr_Format( PyExc_TypeError, "catching classes that do not inherit from BaseException is not allowed" );
                return -1;
            }
        }
    }
    else if (unlikely( !PyExceptionClass_Check( exception_checked ) ))
    {
        PyErr_Format( PyExc_TypeError, "catching classes that do not inherit from BaseException is not allowed" );
        return -1;
    }
#endif

    return PyErr_GivenExceptionMatches( exception_value, exception_checked );
}

#if PYTHON_VERSION >= 300
// Attach the exception context if necessary.
NUITKA_MAY_BE_UNUSED static inline void ADD_EXCEPTION_CONTEXT( PyObject **exception_type, PyObject **exception_value )
{
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *context = tstate->exc_value;

    if ( context != NULL )
    {
        NORMALIZE_EXCEPTION( exception_type, exception_value, NULL );

        Py_INCREF( context );
        PyException_SetContext( *exception_value, context );
    }
}
#endif

#endif
