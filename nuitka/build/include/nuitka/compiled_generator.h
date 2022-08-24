//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_COMPILED_GENERATOR_H__
#define __NUITKA_COMPILED_GENERATOR_H__

#include "Python.h"
#include "frameobject.h"
#include "methodobject.h"

// Compiled generator function type.

// Another cornerstone of the integration into CPython. Try to behave as well as
// normal generator objects do or even better.

// Status of the generator object.
#ifdef __cplusplus
enum Generator_Status {
    status_Unused,  // Not used so far
    status_Running, // Running, used but didn't stop yet
    status_Finished // Stopped, no more values to come
};
#else
typedef int Generator_Status;
static const int status_Unused = 0;
static const int status_Running = 1;
static const int status_Finished = 2;
#endif

// We use this even before Python3.10
#if PYTHON_VERSION < 0x3a0
typedef enum {
    PYGEN_RETURN = 0,
    PYGEN_ERROR = -1,
    PYGEN_NEXT = 1,
} PySendResult;
#endif

// The Nuitka_GeneratorObject is the storage associated with a compiled
// generator object instance of which there can be many for each code.
struct Nuitka_GeneratorObject {
    /* Python object folklore: */
    PyObject_VAR_HEAD

        PyObject *m_name;

    // TODO: Only to make traceback for non-started throw
    PyObject *m_module;

#if PYTHON_VERSION >= 0x350
    PyObject *m_qualname;
#endif
#if PYTHON_VERSION >= 0x300
    // The value currently yielded from.
    PyObject *m_yieldfrom;
#endif

    // Weak references are supported for generator objects in CPython.
    PyObject *m_weakrefs;

    int m_running;

    void *m_code;

    struct Nuitka_FrameObject *m_frame;
    PyCodeObject *m_code_object;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

#if PYTHON_VERSION >= 0x370
    struct Nuitka_ExceptionStackItem m_exc_state;
#endif

    // The label index to resume after yield.
    int m_yield_return_index;

    // Returned value if yielded value is NULL, is
    // NULL if not a return
#if PYTHON_VERSION >= 0x300
    PyObject *m_returned;
#endif

    // A kind of uuid for the generator object, used in comparisons.
    long m_counter;

    /* The heap of generator objects at run time. */
    void *m_heap_storage;

    /* Closure variables given, if any, we reference cells here. The last
     * part is dynamically allocated, the array size differs per generator
     * and includes the heap storage.
     */
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Generator_Type;

typedef PyObject *(*generator_code)(struct Nuitka_GeneratorObject *, PyObject *);

extern PyObject *Nuitka_Generator_New(generator_code code, PyObject *module, PyObject *name,
#if PYTHON_VERSION >= 0x350
                                      PyObject *qualname,
#endif
                                      PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                      Py_ssize_t closure_given, Py_ssize_t heap_storage_size);

extern PyObject *Nuitka_Generator_NewEmpty(PyObject *module, PyObject *name,
#if PYTHON_VERSION >= 0x350
                                           PyObject *qualname,
#endif
                                           PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                           Py_ssize_t closure_given);

extern PyObject *Nuitka_Generator_qiter(struct Nuitka_GeneratorObject *generator, bool *finished);

static inline bool Nuitka_Generator_Check(PyObject *object) { return Py_TYPE(object) == &Nuitka_Generator_Type; }

static inline PyObject *Nuitka_Generator_GetName(PyObject *object) {
    return ((struct Nuitka_GeneratorObject *)object)->m_name;
}

static inline void SAVE_GENERATOR_EXCEPTION(struct Nuitka_GeneratorObject *generator) {
    /* Before Python3.7: When yielding from an exception handler in Python3,
     * the exception preserved to the frame is restored, while the current one
     * is put as there.
     *
     * Python3.7: The exception is preserved in the generator object itself
     * which has a new "m_exc_state" structure just for that.
     */

    PyThreadState *thread_state = PyThreadState_GET();

#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_type = EXC_TYPE(thread_state);
#endif
    PyObject *saved_exception_value = EXC_VALUE(thread_state);
#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_traceback = EXC_TRACEBACK(thread_state);
#endif

#if PYTHON_VERSION < 0x370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;
#else
#if PYTHON_VERSION < 0x3b0
    EXC_TYPE(thread_state) = generator->m_exc_state.exception_type;
#endif
    EXC_VALUE(thread_state) = generator->m_exc_state.exception_value;
#if PYTHON_VERSION < 0x3b0
    EXC_TRACEBACK(thread_state) = (PyObject *)generator->m_exc_state.exception_tb;
#endif
#endif

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("YIELD exit:\n");
    PRINT_PUBLISHED_EXCEPTION();
#endif

#if PYTHON_VERSION < 0x370
    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
#if PYTHON_VERSION < 0x3b0
    generator->m_exc_state.exception_type = saved_exception_type;
#endif
    generator->m_exc_state.exception_value = saved_exception_value;
#if PYTHON_VERSION < 0x3b0
    generator->m_exc_state.exception_tb = (PyTracebackObject *)saved_exception_traceback;
#endif
#endif
}

static inline void RESTORE_GENERATOR_EXCEPTION(struct Nuitka_GeneratorObject *generator) {
    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.
    PyThreadState *thread_state = PyThreadState_GET();

#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_type = EXC_TYPE(thread_state);
#endif
    PyObject *saved_exception_value = EXC_VALUE(thread_state);
#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_traceback = EXC_TRACEBACK(thread_state);
#endif

#if PYTHON_VERSION < 0x370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
#if PYTHON_VERSION < 0x3b0
    EXC_TYPE(thread_state) = generator->m_exc_state.exception_type;
#endif
    EXC_VALUE(thread_state) = generator->m_exc_state.exception_value;
#if PYTHON_VERSION < 0x3b0
    EXC_TRACEBACK(thread_state) = (PyObject *)generator->m_exc_state.exception_tb;
#endif

#if PYTHON_VERSION < 0x3b0
    generator->m_exc_state.exception_type = saved_exception_type;
#endif
    generator->m_exc_state.exception_value = saved_exception_value;
#if PYTHON_VERSION < 0x3b0
    generator->m_exc_state.exception_tb = (PyTracebackObject *)saved_exception_traceback;
#endif
#endif
}

// Functions to preserver and restore from heap area temporary values during
// yield/yield from/await exits of generator functions.
extern void Nuitka_PreserveHeap(void *dest, ...);
extern void Nuitka_RestoreHeap(void *source, ...);

#endif
