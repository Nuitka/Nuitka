//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
#ifndef __NUITKA_FRAME_GUARDS_H__
#define __NUITKA_FRAME_GUARDS_H__

inline static void assertCodeObject( PyCodeObject *code_object )
{
    assertObject( (PyObject *)code_object );
}

inline static void assertFrameObject( PyFrameObject *frame_object )
{
    assertObject( (PyObject *)frame_object );
    assertCodeObject( frame_object->f_code );
}

NUITKA_MAY_BE_UNUSED static PyFrameObject *INCREASE_REFCOUNT( PyFrameObject *frame_object )
{
    assertFrameObject( frame_object );

    Py_INCREF( frame_object );
    return frame_object;
}

NUITKA_MAY_BE_UNUSED static PyFrameObject *INCREASE_REFCOUNT_X( PyFrameObject *frame_object )
{
    Py_XINCREF( frame_object );
    return frame_object;
}

NUITKA_MAY_BE_UNUSED static bool isFrameUnusable( PyFrameObject *frame_object )
{
    return
        // Never used.
        frame_object == NULL ||
        // Still in use
        Py_REFCNT( frame_object ) > 1 ||
        // Last used by another thread (TODO: Could just set it when re-using)
        frame_object->f_tstate != PyThreadState_GET() ||
        // Was detached from (TODO: When detaching, can't we just have another
        // frame guard instead)
        frame_object->f_back != NULL;
}

inline static void popFrameStack( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    PyFrameObject *old = tstate->frame;

#if _DEBUG_REFRAME
    printf( "Taking off frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)old ) ), PyString_AsString( PyObject_Repr( (PyObject *)old->f_code ) ) );
#endif

    tstate->frame = old->f_back;
    old->f_back = NULL;

    // We might be very top level, e.g. in a thread, and therefore do not insist on value.
    Py_XDECREF( tstate->frame );

#if _DEBUG_REFRAME
    printf( "Now at top frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)tstate->frame ) ), PyString_AsString( PyObject_Repr( (PyObject *)tstate->frame->f_code ) ) );
#endif
}

inline static void pushFrameStack( PyFrameObject *frame_object )
{
    assertFrameObject( frame_object );

    PyThreadState *tstate = PyThreadState_GET();

    // Look at current frame.
    PyFrameObject *old = tstate->frame;

#if _DEBUG_REFRAME
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
        frame_object->f_back = INCREASE_REFCOUNT( old );
    }

#if _DEBUG_REFRAME
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

// Make a replacement for the current top frame, that we again own exclusively enough so
// that the line numbers are detached.
extern PyFrameObject *detachCurrentFrame();

class FrameGuard
{
public:
    FrameGuard( PyFrameObject *frame_object )
    {
        assertFrameObject( frame_object );

        // Remember it.
        this->frame_object = frame_object;

        // Push the new frame as the currently active one.
        pushFrameStack( frame_object );

        // Keep the frame object alive for this C++ objects live time.
        Py_INCREF( frame_object );

#if _DEBUG_REFRAME
        // dumpFrameStack();
#endif
    }

    ~FrameGuard()
    {
        // Our frame should be on top.
        assert( PyThreadState_GET()->frame == this->frame_object );

        // Put the previous frame on top instead.
        popFrameStack();

        assert( PyThreadState_GET()->frame != this->frame_object );

        // Should still be good.
        assertFrameObject( this->frame_object );

        // Now release our frame object reference.
        Py_DECREF( this->frame_object );
    }

    PyFrameObject *getFrame() const
    {
        return INCREASE_REFCOUNT( this->frame_object );
    }

    PyFrameObject *getFrame0() const
    {
        return this->frame_object;
    }

    // Use this to set the current line of the frame
    void setLineNumber( int lineno ) const
    {
        assertFrameObject( this->frame_object );
        assert( lineno >= 1 );

        // Make sure f_lineno is the actually used information.
        assert( this->frame_object->f_trace == Py_None );

        this->frame_object->f_lineno = lineno;
    }

    int getLineNumber() const
    {
        assertFrameObject( this->frame_object );

        return this->frame_object->f_lineno;
    }

    void check() const
    {
        assertFrameObject( this->frame_object );

        // Make sure f_lineno is the actually used information.
        assert( this->frame_object->f_trace == Py_None );
    }

    // Replace the frame object by a newer one.
    void detachFrame( void )
    {
        // Our old frame should be on top.
        assert( PyThreadState_GET()->frame == this->frame_object );

        this->frame_object = detachCurrentFrame();

        // Our new frame should be on top.
        assert( PyThreadState_GET()->frame == this->frame_object );
    }

private:

    PyFrameObject *frame_object;

};

class FrameGuardLight
{
public:
    FrameGuardLight( PyFrameObject **frame_ptr )
    {
        assertFrameObject( *frame_ptr );

        // Remember it.
        this->frame_ptr = frame_ptr;
    }

    ~FrameGuardLight()
    {
        // Should still be good.
        assertFrameObject( *this->frame_ptr );
    }

    PyFrameObject *getFrame() const
    {
        return INCREASE_REFCOUNT( *this->frame_ptr );
    }

    PyFrameObject *getFrame0() const
    {
        return *this->frame_ptr;
    }

    // Use this to set the current line of the frame
    void setLineNumber( int lineno ) const
    {
        assertFrameObject( *this->frame_ptr );
        assert( lineno >= 1 );

        // Make sure f_lineno is the actually used information.
        assert( (*this->frame_ptr)->f_trace == Py_None );

        (*this->frame_ptr)->f_lineno = lineno;
    }

    // Replace the frame object by a newer one.
    void detachFrame( void )
    {
        // Our old frame should be on top.
        assert( PyThreadState_GET()->frame == *this->frame_ptr );

        *this->frame_ptr = detachCurrentFrame();

        // Our new frame should be on top.
        assert( PyThreadState_GET()->frame == *this->frame_ptr );
    }


private:

    PyFrameObject **frame_ptr;

};

class FrameGuardVeryLight
{
public:

    explicit FrameGuardVeryLight() {}

    void setLineNumber( int lineno ) const
    {
        PyFrameObject *frame_object = PyThreadState_GET()->frame;

        assertFrameObject( frame_object );
        assert( lineno >= 1 );

        // Make sure f_lineno is the actually used information.
        assert( frame_object->f_trace == Py_None );

        frame_object->f_lineno = lineno;
    }

};

#endif
