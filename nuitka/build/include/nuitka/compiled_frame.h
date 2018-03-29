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
#ifndef __NUITKA_COMPILED_FRAME_H__
#define __NUITKA_COMPILED_FRAME_H__

// Create a frame object for the given code object, frame or module.
extern struct Nuitka_FrameObject *MAKE_MODULE_FRAME( PyCodeObject *code, PyObject *module );
extern struct Nuitka_FrameObject *MAKE_FUNCTION_FRAME( PyCodeObject *code, PyObject *module, Py_ssize_t locals_size );

// Create a code object for the given filename and function name
#if PYTHON_VERSION < 300
extern PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name, int line, PyObject *argnames, int arg_count, int flags );
#else
extern PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name, int line, PyObject *argnames, int arg_count, int kw_only_count, int flags );
#endif

extern PyTypeObject Nuitka_Frame_Type;

static inline bool Nuitka_Frame_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Frame_Type;
}

struct Nuitka_FrameObject
{
    PyFrameObject m_frame;

    char const *m_type_description;
    char m_locals_storage[1];
};

#define MAKE_OR_REUSE_FRAME( cache_identifier, code_identifier, module_identifier, locals_size )    \
    if ( isFrameUnusable( cache_identifier ) )                                                      \
    {                                                                                               \
        Py_XDECREF( cache_identifier );                                                             \
        cache_identifier = MAKE_FUNCTION_FRAME( code_identifier, module_identifier, locals_size );  \
    }                                                                                               \
    assert( ((struct Nuitka_FrameObject *)cache_identifier)->m_type_description == NULL );                                           \

inline static void assertCodeObject( PyCodeObject *code_object )
{
    CHECK_OBJECT( (PyObject *)code_object );
}

NUITKA_MAY_BE_UNUSED static bool isFrameUnusable( struct Nuitka_FrameObject *frame_object )
{
    if ( frame_object ) CHECK_OBJECT( (PyObject *)frame_object );

    bool result =
        // Never used.
        frame_object == NULL ||
        // Still in use
        Py_REFCNT( frame_object ) > 1 ||
#if PYTHON_VERSION < 340
        // Last used by another thread (TODO: Could just set it when re-using)
        frame_object->m_frame.f_tstate != PyThreadState_GET() ||
#endif
        // Not currently linked.
        frame_object->m_frame.f_back != NULL;

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


inline static void assertFrameObject( struct Nuitka_FrameObject *frame_object )
{
    CHECK_OBJECT( (PyObject *)frame_object );
    assertCodeObject( frame_object->m_frame.f_code );
}

// Mark frame as currently executed. Starting with Python 3.4 that means it
// can or cannot be cleared, or should lead to a generator close. For Python2
// this is a no-op. Using a define to spare the compile from inlining an empty
// function.
#if PYTHON_VERSION >= 340
static inline void Nuitka_Frame_MarkAsExecuting( struct Nuitka_FrameObject *frame )
{
    frame->m_frame.f_executing = 1;
}
#else
#define Nuitka_Frame_MarkAsExecuting( frame ) ;
#endif

#if PYTHON_VERSION >= 340
static inline void Nuitka_Frame_MarkAsNotExecuting( struct Nuitka_FrameObject *frame )
{
    frame->m_frame.f_executing = 0;
}
#else
#define Nuitka_Frame_MarkAsNotExecuting( frame ) ;
#endif

// Put frame at the top of the frame stack and mark as executing.
NUITKA_MAY_BE_UNUSED inline static void pushFrameStack( struct Nuitka_FrameObject *frame_object )
{
    // Make sure it's healthy.
    assertFrameObject( frame_object );

    // We don't allow frame objects where this is not true.
    assert( frame_object->m_frame.f_back == NULL );

    // Look at current frame, "old" is the one previously active.
    PyThreadState *tstate = PyThreadState_GET();
    PyFrameObject *old = tstate->frame;

#if _DEBUG_FRAME
    if ( old )
    {
        assertCodeObject( old->f_code );

        printf( "Upstacking to frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)old ) ), PyString_AsString( PyObject_Repr( (PyObject *)old->f_code ) ) );
    }
#endif

    // No recursion with identical frames allowed, assert against it.
    assert( old != &frame_object->m_frame );

    // Push the new frame as the currently active one.
    tstate->frame = (PyFrameObject *)frame_object;

    // Transfer ownership of old frame.
    if ( old != NULL )
    {
        assertFrameObject( (struct Nuitka_FrameObject *)old );

        frame_object->m_frame.f_back = old;
    }

    Nuitka_Frame_MarkAsExecuting( frame_object );
    Py_INCREF( frame_object );

#if _DEBUG_FRAME
    printf( "Now at top frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)tstate->frame ) ), PyString_AsString( PyObject_Repr( (PyObject *)tstate->frame->f_code ) ) );
#endif
}

NUITKA_MAY_BE_UNUSED inline static void popFrameStack( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    PyFrameObject *old = tstate->frame;

#if _DEBUG_FRAME
    printf( "Taking off frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)old ) ), PyString_AsString( PyObject_Repr( (PyObject *)old->f_code ) ) );
#endif

    // Put previous frame on top.
    tstate->frame = old->f_back;
    old->f_back = NULL;

    Nuitka_Frame_MarkAsNotExecuting( (struct Nuitka_FrameObject *)old );
    Py_DECREF( old );

#if _DEBUG_FRAME
    if ( tstate->frame )
    {
        printf( "Now at top frame %s %s\n", PyString_AsString( PyObject_Str( (PyObject *)tstate->frame ) ), PyString_AsString( PyObject_Repr( (PyObject *)tstate->frame->f_code ) ) );
    }
    else
    {
        printf( "Now at top no frame\n");
    }
#endif
}

// Attach locals to a frame object.
extern void Nuitka_Frame_AttachLocals( struct Nuitka_FrameObject *frame, char const *type_description, ... );
extern void Nuitka_Frame_ReleaseLocals( struct Nuitka_FrameObject *frame );

// Codes used for type_description.
#define NUITKA_TYPE_DESCRIPTION_NULL 'N'
#define NUITKA_TYPE_DESCRIPTION_CELL 'c'
#define NUITKA_TYPE_DESCRIPTION_OBJECT 'o'
#define NUITKA_TYPE_DESCRIPTION_OBJECT_PTR 'O'
#define NUITKA_TYPE_DESCRIPTION_BOOL 'b'


#endif
