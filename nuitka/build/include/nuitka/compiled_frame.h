//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
extern struct Nuitka_FrameObject *MAKE_MODULE_FRAME(PyCodeObject *code, PyObject *module);
extern struct Nuitka_FrameObject *MAKE_FUNCTION_FRAME(PyCodeObject *code, PyObject *module, Py_ssize_t locals_size);

// Create a code object for the given filename and function name

#if PYTHON_VERSION < 0x300
#define MAKE_CODEOBJECT(filename, line, flags, function_name, argnames, freevars, arg_count, kw_only_count,            \
                        pos_only_count)                                                                                \
    makeCodeObject(filename, line, flags, function_name, argnames, freevars, arg_count)
extern PyCodeObject *makeCodeObject(PyObject *filename, int line, int flags, PyObject *function_name,
                                    PyObject *argnames, PyObject *freevars, int arg_count);
#elif PYTHON_VERSION < 0x380
#define MAKE_CODEOBJECT(filename, line, flags, function_name, argnames, freevars, arg_count, kw_only_count,            \
                        pos_only_count)                                                                                \
    makeCodeObject(filename, line, flags, function_name, argnames, freevars, arg_count, kw_only_count)
extern PyCodeObject *makeCodeObject(PyObject *filename, int line, int flags, PyObject *function_name,
                                    PyObject *argnames, PyObject *freevars, int arg_count, int kw_only_count);
#else
#define MAKE_CODEOBJECT(filename, line, flags, function_name, argnames, freevars, arg_count, kw_only_count,            \
                        pos_only_count)                                                                                \
    makeCodeObject(filename, line, flags, function_name, argnames, freevars, arg_count, kw_only_count, pos_only_count)
extern PyCodeObject *makeCodeObject(PyObject *filename, int line, int flags, PyObject *function_name,
                                    PyObject *argnames, PyObject *freevars, int arg_count, int kw_only_count,
                                    int pos_only_count);
#endif

extern PyTypeObject Nuitka_Frame_Type;

static inline bool Nuitka_Frame_Check(PyObject *object) { return Py_TYPE(object) == &Nuitka_Frame_Type; }

struct Nuitka_FrameObject {
    PyFrameObject m_frame;

    // Our own extra stuff, attached variables.
    char const *m_type_description;
    char m_locals_storage[1];
};

inline static void assertCodeObject(PyCodeObject *code_object) { CHECK_OBJECT(code_object); }

NUITKA_MAY_BE_UNUSED static inline bool isFrameUnusable(struct Nuitka_FrameObject *frame_object) {
    CHECK_OBJECT_X(frame_object);

    bool result =
        // Never used.
        frame_object == NULL ||
        // Still in use
        Py_REFCNT(frame_object) > 1 ||
#if PYTHON_VERSION < 0x340
        // Last used by another thread (TODO: Could just set it when re-using)
        frame_object->m_frame.f_tstate != PyThreadState_GET() ||
#endif
        // Not currently linked.
        frame_object->m_frame.f_back != NULL;

#if _DEBUG_REFRAME
    if (result && frame_object != NULL) {
        PRINT_STRING("NOT REUSING FRAME:");
        PRINT_ITEM((PyObject *)frame_object);
        PRINT_REFCOUNT((PyObject *)frame_object);
        if (frame_object->f_back) {
            PRINT_ITEM((PyObject *)frame_object->f_back);
        }
        PRINT_NEW_LINE();
    }
#endif

    return result;
}

#if _DEBUG_REFCOUNTS
extern int count_active_frame_cache_instances;
extern int count_allocated_frame_cache_instances;
extern int count_released_frame_cache_instances;
extern int count_hit_frame_cache_instances;
#endif

extern void dumpFrameStack(void);

inline static void assertFrameObject(struct Nuitka_FrameObject *frame_object) {
    CHECK_OBJECT(frame_object);
    assertCodeObject(frame_object->m_frame.f_code);
}

// Mark frame as currently executed. Starting with Python 3.4 that means it
// can or cannot be cleared, or should lead to a generator close. For Python2
// this is a no-op. Using a define to spare the compile from inlining an empty
// function.
#if PYTHON_VERSION >= 0x340
static inline void Nuitka_Frame_MarkAsExecuting(struct Nuitka_FrameObject *frame) { frame->m_frame.f_executing = 1; }
#else
#define Nuitka_Frame_MarkAsExecuting(frame) ;
#endif

#if PYTHON_VERSION >= 0x340
static inline void Nuitka_Frame_MarkAsNotExecuting(struct Nuitka_FrameObject *frame) { frame->m_frame.f_executing = 0; }
#else
#define Nuitka_Frame_MarkAsNotExecuting(frame) ;
#endif

// Put frame at the top of the frame stack and mark as executing.
NUITKA_MAY_BE_UNUSED inline static void pushFrameStack(struct Nuitka_FrameObject *frame_object) {
    // Make sure it's healthy.
    assertFrameObject(frame_object);

    // We don't allow frame objects where this is not true.
    assert(frame_object->m_frame.f_back == NULL);

    // Look at current frame, "old" is the one previously active.
    PyThreadState *tstate = PyThreadState_GET();
    PyFrameObject *old = tstate->frame;

#if _DEBUG_FRAME
    if (old) {
        assertCodeObject(old->f_code);

        printf("Upstacking to frame %s %s\n", Nuitka_String_AsString(PyObject_Str((PyObject *)old)),
               Nuitka_String_AsString(PyObject_Repr((PyObject *)old->f_code)));
    }
#endif

    // No recursion with identical frames allowed, assert against it.
    assert(old != &frame_object->m_frame);

    // Push the new frame as the currently active one.
    tstate->frame = (PyFrameObject *)frame_object;

    // Transfer ownership of old frame.
    if (old != NULL) {
        assertFrameObject((struct Nuitka_FrameObject *)old);

        frame_object->m_frame.f_back = old;
    }

    Nuitka_Frame_MarkAsExecuting(frame_object);
    Py_INCREF(frame_object);

#if _DEBUG_FRAME
    printf("Now at top frame %s %s\n", Nuitka_String_AsString(PyObject_Str((PyObject *)tstate->frame)),
           Nuitka_String_AsString(PyObject_Repr((PyObject *)tstate->frame->f_code)));
#endif
}

NUITKA_MAY_BE_UNUSED inline static void popFrameStack(void) {
    PyThreadState *tstate = PyThreadState_GET();

    PyFrameObject *old = tstate->frame;

#if _DEBUG_FRAME
    printf("Taking off frame %s %s\n", Nuitka_String_AsString(PyObject_Str((PyObject *)old)),
           Nuitka_String_AsString(PyObject_Repr((PyObject *)old->f_code)));
#endif

    // Put previous frame on top.
    tstate->frame = old->f_back;
    old->f_back = NULL;

    Nuitka_Frame_MarkAsNotExecuting((struct Nuitka_FrameObject *)old);
    Py_DECREF(old);

#if _DEBUG_FRAME
    if (tstate->frame) {
        printf("Now at top frame %s %s\n", Nuitka_String_AsString(PyObject_Str((PyObject *)tstate->frame)),
               Nuitka_String_AsString(PyObject_Repr((PyObject *)tstate->frame->f_code)));
    } else {
        printf("Now at top no frame\n");
    }
#endif
}

// Attach locals to a frame object. TODO: Upper case, this is for generated code only.
extern void Nuitka_Frame_AttachLocals(struct Nuitka_FrameObject *frame, char const *type_description, ...);

// Codes used for type_description.
#define NUITKA_TYPE_DESCRIPTION_NULL 'N'
#define NUITKA_TYPE_DESCRIPTION_CELL 'c'
#define NUITKA_TYPE_DESCRIPTION_OBJECT 'o'
#define NUITKA_TYPE_DESCRIPTION_OBJECT_PTR 'O'
#define NUITKA_TYPE_DESCRIPTION_BOOL 'b'

#if _DEBUG_REFCOUNTS
extern int count_active_Nuitka_Frame_Type;
extern int count_allocated_Nuitka_Frame_Type;
extern int count_released_Nuitka_Frame_Type;
#endif

#endif
