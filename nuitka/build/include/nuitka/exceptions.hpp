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

static bool ERROR_OCCURED( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type != NULL;
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_ERROR_OCCURED( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type;
}

NUITKA_MAY_BE_UNUSED static void FETCH_ERROR( PyObject **exception_type, PyObject **exception_value, PyObject **exception_traceback)
{
   PyThreadState *tstate = PyThreadState_GET();

   *exception_type = tstate->curexc_type;
   *exception_value = tstate->curexc_value;
   *exception_traceback = tstate->curexc_traceback;

   tstate->curexc_type = NULL;
   tstate->curexc_value = NULL;
   tstate->curexc_traceback = NULL;
}

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
    puts( "Dumping traceback:" );

    if ( traceback == NULL ) puts( "<NULL traceback?!>" );

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

    puts( "End of Dump." );
}
#endif

NUITKA_MAY_BE_UNUSED static PyTracebackObject *INCREASE_REFCOUNT( PyTracebackObject *traceback_object )
{
    Py_INCREF( traceback_object );
    return traceback_object;
}

NUITKA_MAY_BE_UNUSED static PyTracebackObject *INCREASE_REFCOUNT_X( PyTracebackObject *traceback_object )
{
    Py_XINCREF( traceback_object );
    return traceback_object;
}

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
inline void SET_CURRENT_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyTracebackObject *exception_tb )
{
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *old_type  = thread_state->exc_type;
    PyObject *old_value = thread_state->exc_value;
    PyObject *old_tb    = thread_state->exc_traceback;

    thread_state->exc_type = exception_type;
    thread_state->exc_value = exception_value;
    thread_state->exc_traceback = (PyObject *)exception_tb;

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

inline void PRESERVE_FRAME_EXCEPTION( PyFrameObject *frame_object )
{
    // Setting exception for frame if not already done.
    if ( frame_object->f_exc_type == NULL )
    {
        PyThreadState *thread_state = PyThreadState_GET();

        if ( thread_state->exc_type != NULL && thread_state->exc_type != Py_None )
        {
            frame_object->f_exc_type = INCREASE_REFCOUNT( thread_state->exc_type );
            frame_object->f_exc_value = INCREASE_REFCOUNT_X( thread_state->exc_value );
            frame_object->f_exc_traceback = INCREASE_REFCOUNT_X( thread_state->exc_traceback );
        }
        else
        {
            frame_object->f_exc_type = INCREASE_REFCOUNT( Py_None );
            frame_object->f_exc_value = NULL;
            frame_object->f_exc_traceback = NULL;
        }
    }
}

inline void RESTORE_FRAME_EXCEPTION( PyFrameObject *frame_object )
{
    if ( frame_object->f_exc_type )
    {
        SET_CURRENT_EXCEPTION( frame_object->f_exc_type, frame_object->f_exc_value, (PyTracebackObject *)frame_object->f_exc_traceback );

        frame_object->f_exc_type = NULL;
        frame_object->f_exc_value = NULL;
        frame_object->f_exc_traceback = NULL;
    }
}

inline void PUBLISH_EXCEPTION( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    SET_CURRENT_EXCEPTION( *exception_type, *exception_value, *exception_tb );

    *exception_type = NULL;
    *exception_value = NULL;
    *exception_tb = NULL;
}

inline void NORMALIZE_EXCEPTION( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    PyErr_NormalizeException( exception_type, exception_value, (PyObject **)exception_tb );
}

class PythonException
{
public:
    PythonException()
    {
    }
};


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

#endif
