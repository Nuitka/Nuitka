//     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_FRAME_STACK_H__
#define __NUITKA_FRAME_STACK_H__

#define MAKE_OR_REUSE_FRAME( cache_identifier, code_identifier, module_identifier ) \
    if ( isFrameUnusable( cache_identifier ) )                                \
    {                                                                         \
        Py_XDECREF( cache_identifier );                                       \
        cache_identifier = MAKE_FRAME( code_identifier, module_identifier );  \
    }                                                                         \

inline static void assertCodeObject( PyCodeObject *code_object )
{
    CHECK_OBJECT( (PyObject *)code_object );
}

inline static void assertFrameObject( PyFrameObject *frame_object )
{
    CHECK_OBJECT( (PyObject *)frame_object );
    assertCodeObject( frame_object->f_code );
}

NUITKA_MAY_BE_UNUSED static PyFrameObject *INCREASE_REFCOUNT( PyFrameObject *frame_object )
{
    assertFrameObject( frame_object );

    Py_INCREF( frame_object );
    return frame_object;
}

NUITKA_MAY_BE_UNUSED static bool isFrameUnusable( PyFrameObject *frame_object )
{
    if ( frame_object ) CHECK_OBJECT( (PyObject *)frame_object );

    bool result =
        // Never used.
        frame_object == NULL ||
        // Still in use
        Py_REFCNT( frame_object ) > 1 ||
#if PYTHON_VERSION < 340
        // Last used by another thread (TODO: Could just set it when re-using)
        frame_object->f_tstate != PyThreadState_GET() ||
#endif
        // Was detached from (TODO: When detaching, can't we just have another
        // frame guard instead)
        frame_object->f_back != NULL;

#if _DEBUG_REFRAME
    if (result && frame_object)
    {
        PRINT_STRING("NOT REUSING FRAME:");
        PRINT_ITEM((PyObject *)frame_object);
        PRINT_REFCOUNT( (PyObject *)frame_object );
        if ( frame_object->f_back ) PRINT_ITEM( (PyObject *)frame_object->f_back );
        PRINT_NEW_LINE();
    }
#endif

    return result;
}

NUITKA_MAY_BE_UNUSED inline static void popFrameStack( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    PyFrameObject *old = tstate->frame;

#if _DEBUG_FRAME
    printf( "Taking off frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)old ) ), PyString_AsString( PyObject_Repr( (PyObject *)old->f_code ) ) );
#endif

    tstate->frame = old->f_back;
    old->f_back = NULL;

    // We might be very top level, e.g. in a thread, and therefore do not insist
    // on value.
    Py_XDECREF( tstate->frame );

#if _DEBUG_FRAME
    if (tstate->frame)
    {
        printf( "Now at top frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)tstate->frame ) ), PyString_AsString( PyObject_Repr( (PyObject *)tstate->frame->f_code ) ) );
    }
    else
    {
        printf( "Now at top no frame\n");
    }
#endif
}

NUITKA_MAY_BE_UNUSED inline static void pushFrameStack( PyFrameObject *frame_object )
{
    assertFrameObject( frame_object );

    PyThreadState *tstate = PyThreadState_GET();

    // Look at current frame.
    PyFrameObject *old = tstate->frame;

#if _DEBUG_FRAME
    if ( old )
    {
        assertCodeObject( old->f_code );

        printf( "Upstacking to frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)old ) ), PyString_AsString( PyObject_Repr( (PyObject *)old->f_code ) ) );
    }
#endif

    // No recursion allowed of course, assert against it.
    assert( old != frame_object );

    // Push the new frame as the currently active one.
    tstate->frame = frame_object;

    // We don't allow touching cached frame objects where this is not true.
    assert( frame_object->f_back == NULL );

    if ( old != NULL )
    {
        assertFrameObject( old );

        frame_object->f_back = old;
        Py_INCREF( frame_object->f_back );
    }

#if _DEBUG_FRAME
    printf( "Now at top frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)tstate->frame ) ), PyString_AsString( PyObject_Repr( (PyObject *)tstate->frame->f_code ) ) );
#endif
}

#if _DEBUG_REFRAME
static inline void dumpFrameStack( void )
{
    PyFrameObject *current = PyThreadState_GET()->frame;
    int total = 0;

    while( current )
    {
        total++;
        current = current->f_back;
    }

    current = PyThreadState_GET()->frame;

    puts( ">--------->" );

    while( current )
    {
        printf( "Frame stack %d: %s %s\n", total--, PyString_AsString( PyObject_Str( (PyObject *)current ) ), PyString_AsString( PyObject_Str( (PyObject *)current->f_code ) ) );

        current = current->f_back;
    }

    puts( ">---------<" );
}
#endif

// Make a replacement for the traceback frame, that we again own it exclusively
// enough so that the line numbers are detached.
extern void detachFrame( PyTracebackObject *traceback, PyObject *locals );

#endif
