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

#if _DEBUG_FRAME
    printf( "Taking off frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)old ) ), PyString_AsString( PyObject_Repr( (PyObject *)old->f_code ) ) );
#endif

    tstate->frame = old->f_back;
    old->f_back = NULL;

    // We might be very top level, e.g. in a thread, and therefore do not insist on value.
    Py_XDECREF( tstate->frame );

#if _DEBUG_FRAME
    printf( "Now at top frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)tstate->frame ) ), PyString_AsString( PyObject_Repr( (PyObject *)tstate->frame->f_code ) ) );
#endif
}

inline static void pushFrameStack( PyFrameObject *frame_object )
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
        frame_object->f_back = INCREASE_REFCOUNT( old );
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

// Make a replacement for the current top frame, that we again own exclusively
// enough so that the line numbers are detached.
extern PyFrameObject *detachCurrentFrame();

class FrameGuard
{
public:
    explicit FrameGuard( PyFrameObject *frame_object )
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

    inline PyFrameObject *getFrame() const
    {
        return INCREASE_REFCOUNT( this->frame_object );
    }

    inline PyFrameObject *getFrame0() const
    {
        return this->frame_object;
    }

    // Use this to set the current line of the frame
    inline void setLineNumber( int lineno ) const
    {
        assertFrameObject( this->frame_object );
        assert( lineno >= 1 );

        // Make sure f_lineno is the actually used information.
        assert( this->frame_object->f_trace == Py_None );

        this->frame_object->f_lineno = lineno;
    }

    inline int getLineNumber() const
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

class FrameGuardWithExceptionPreservation
{
public:
    explicit FrameGuardWithExceptionPreservation( PyFrameObject *frame_object )
    {
        assertFrameObject( frame_object );

        // Remember it.
        this->frame_object = frame_object;

        // Push the new frame as the currently active one.
        pushFrameStack( frame_object );

        // Keep the frame object alive for this C++ objects live time.
        Py_INCREF( frame_object );

        this->preserving = false;

#if _DEBUG_REFRAME
        // dumpFrameStack();
#endif
    }

    ~FrameGuardWithExceptionPreservation()
    {
        // Our frame should be on top.
        assert( PyThreadState_GET()->frame == this->frame_object );

        // Put the previous frame on top instead.
        popFrameStack();

        assert( PyThreadState_GET()->frame != this->frame_object );

        // Should still be good.
        assertFrameObject( this->frame_object );

        if ( this->preserving )
        {
            _SET_CURRENT_EXCEPTION( this->frame_object->f_exc_type, this->frame_object->f_exc_value, (PyTracebackObject *)this->frame_object->f_exc_traceback );

            Py_XDECREF( this->frame_object->f_exc_type );
            Py_XDECREF( this->frame_object->f_exc_value );
            Py_XDECREF( this->frame_object->f_exc_traceback );

            this->frame_object->f_exc_type = NULL;
            this->frame_object->f_exc_value = NULL;
            this->frame_object->f_exc_traceback = NULL;
        }

        // Now release our frame object reference.
        Py_DECREF( this->frame_object );
    }

    inline PyFrameObject *getFrame() const
    {
        return INCREASE_REFCOUNT( this->frame_object );
    }

    inline PyFrameObject *getFrame0() const
    {
        return this->frame_object;
    }

    // Use this to set the current line of the frame
    inline void setLineNumber( int lineno ) const
    {
        assertFrameObject( this->frame_object );
        assert( lineno >= 1 );

        // Make sure f_lineno is the actually used information.
        assert( this->frame_object->f_trace == Py_None );

        this->frame_object->f_lineno = lineno;
    }

    inline int getLineNumber() const
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

    void preserveExistingException()
    {
        if ( this->preserving == false )
        {
            PyThreadState *thread_state = PyThreadState_GET();

            if ( thread_state->exc_type != NULL && thread_state->exc_type != Py_None )
            {
                this->frame_object->f_exc_type = INCREASE_REFCOUNT( thread_state->exc_type );
                this->frame_object->f_exc_value = INCREASE_REFCOUNT_X( thread_state->exc_value );
                this->frame_object->f_exc_traceback = INCREASE_REFCOUNT_X( thread_state->exc_traceback );
            }
            else
            {
                this->frame_object->f_exc_type = NULL;
                this->frame_object->f_exc_value = NULL;
                this->frame_object->f_exc_traceback = NULL;
            }

            this->preserving = true;
        }
    }

#if PYTHON_VERSION >= 300
    void restoreExistingException()
    {
        if ( this->preserving == true )
        {
            _SET_CURRENT_EXCEPTION( this->frame_object->f_exc_type, this->frame_object->f_exc_value, (PyTracebackObject *)this->frame_object->f_exc_traceback );

            Py_XDECREF( this->frame_object->f_exc_type );
            Py_XDECREF( this->frame_object->f_exc_value );
            Py_XDECREF( this->frame_object->f_exc_traceback );

            this->frame_object->f_exc_type = NULL;
            this->frame_object->f_exc_value = NULL;
            this->frame_object->f_exc_traceback = NULL;

            this->preserving = false;
        }
    }
#endif

private:

    bool preserving;
    PyFrameObject *frame_object;
};

class FrameGuardLight
{
public:
    explicit FrameGuardLight( PyFrameObject **frame_ptr )
    {
        assertFrameObject( *frame_ptr );

        // Remember it.
        this->frame_ptr = frame_ptr;

#if PYTHON_VERSION >= 300
        preserving = false;
#endif
    }

    ~FrameGuardLight()
    {
        // Should still be good.
        assertFrameObject( *this->frame_ptr );

#if PYTHON_VERSION >= 300
        if ( this->preserving )
        {
            PyFrameObject *frame_object = *this->frame_ptr;

            _SET_CURRENT_EXCEPTION( frame_object->f_exc_type, frame_object->f_exc_value, (PyTracebackObject *)frame_object->f_exc_traceback );

            Py_XDECREF( frame_object->f_exc_type );
            Py_XDECREF( frame_object->f_exc_value );
            Py_XDECREF( frame_object->f_exc_traceback );

            frame_object->f_exc_type = NULL;
            frame_object->f_exc_value = NULL;
            frame_object->f_exc_traceback = NULL;
        }
#endif
    }

    PyFrameObject *getFrame() const
    {
        return INCREASE_REFCOUNT( *this->frame_ptr );
    }

    PyFrameObject *getFrame0() const
    {
        return *this->frame_ptr;
    }

    inline int getLineNumber() const
    {
        return (*this->frame_ptr)->f_lineno;
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

    void preserveExistingException()
    {
#if PYTHON_VERSION >= 300
        if ( this->preserving == false )
        {
            PyThreadState *thread_state = PyThreadState_GET();

            PyFrameObject *frame_object = *this->frame_ptr;

            if ( thread_state->exc_type != NULL && thread_state->exc_type != Py_None )
            {
                frame_object->f_exc_type = INCREASE_REFCOUNT( thread_state->exc_type );
                frame_object->f_exc_value = INCREASE_REFCOUNT_X( thread_state->exc_value );
                frame_object->f_exc_traceback = INCREASE_REFCOUNT_X( thread_state->exc_traceback );
            }
            else
            {
                frame_object->f_exc_type = NULL;
                frame_object->f_exc_value = NULL;
                frame_object->f_exc_traceback = NULL;
            }

            this->preserving = true;
        }
#endif
    }

#if PYTHON_VERSION >= 300
    void restoreExistingException()
    {
        if ( this->preserving == true )
        {
            PyFrameObject *frame_object = *this->frame_ptr;

            _SET_CURRENT_EXCEPTION( frame_object->f_exc_type, frame_object->f_exc_value, (PyTracebackObject *)frame_object->f_exc_traceback );

            Py_XDECREF( frame_object->f_exc_type );
            Py_XDECREF( frame_object->f_exc_value );
            Py_XDECREF( frame_object->f_exc_traceback );

            frame_object->f_exc_type = NULL;
            frame_object->f_exc_value = NULL;
            frame_object->f_exc_traceback = NULL;

            this->preserving = false;
        }
    }
#endif

private:

    PyFrameObject **frame_ptr;

#if PYTHON_VERSION >= 300
    bool preserving;
#endif
};

class FrameGuardVeryLight
{
public:
    explicit FrameGuardVeryLight() {}

    inline int getLineNumber() const
    {
        PyFrameObject *frame_object = PyThreadState_GET()->frame;

        return frame_object->f_lineno;
    }

    inline void setLineNumber( int lineno ) const
    {
        PyFrameObject *frame_object = PyThreadState_GET()->frame;

        assertFrameObject( frame_object );
        assert( lineno >= 1 );

        // Make sure f_lineno is the actually used information.
        assert( frame_object->f_trace == Py_None );

        frame_object->f_lineno = lineno;
    }

    PyFrameObject *getFrame() const
    {
        return INCREASE_REFCOUNT( this->getFrame0() );
    }

    PyFrameObject *getFrame0() const
    {
        return PyThreadState_GET()->frame;
    }

    void preserveExistingException()
    {
    }

    void detachFrame( void )
    {
    }

#if PYTHON_VERSION >= 300
    void restoreExistingException()
    {
    }
#endif
};


#if PYTHON_VERSION >= 300
class ExceptionRestorerFrameGuard
{
public:
    explicit ExceptionRestorerFrameGuard( FrameGuardWithExceptionPreservation *frame_guard )
    {
        this->frame_guard = frame_guard;
    }

    ~ExceptionRestorerFrameGuard()
    {
        this->frame_guard->restoreExistingException();
    }

private:
    FrameGuardWithExceptionPreservation *frame_guard;
};

class ExceptionRestorerFrameGuardLight
{
public:
    explicit ExceptionRestorerFrameGuardLight( FrameGuardLight *frame_guard )
    {
        this->frame_guard = frame_guard;
    }

    ~ExceptionRestorerFrameGuardLight()
    {
        this->frame_guard->restoreExistingException();
    }

private:
    FrameGuardLight *frame_guard;
};

class ExceptionRestorerFrameGuardVeryLight
{
public:
    explicit ExceptionRestorerFrameGuardVeryLight( FrameGuardVeryLight *frame_guard )
    {
        this->frame_guard = frame_guard;
    }

    ~ExceptionRestorerFrameGuardVeryLight()
    {
        this->frame_guard->restoreExistingException();
    }

private:
    FrameGuardVeryLight *frame_guard;
};

#endif


#endif
