//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_PRINTING_H__
#define __NUITKA_PRINTING_H__

// Helper functions for print. Need to play nice with Python softspace
// behavior.

extern bool PRINT_NEW_LINE(void);
extern bool PRINT_ITEM(PyObject *object);
extern bool PRINT_STRING(char const *str);
extern bool PRINT_FORMAT(char const *fmt, ...);
extern bool PRINT_ITEM_TO(PyObject *file, PyObject *object);
extern bool PRINT_NEW_LINE_TO(PyObject *file);

extern PyObject *GET_STDOUT(void);
extern PyObject *GET_STDERR(void);

// -----------------------------------------------------------------------
// Helper functions to debug the run time operation of the compiled binary
// manually or in debug modes.

// Print the reference count of the object.
extern void PRINT_REFCOUNT(PyObject *object);

// Print the full traceback stack.
// TODO: Could be ported, the "printf" stuff would need to be split. On Python3
// the normal C print output gets lost.
#if PYTHON_VERSION < 0x300
extern void PRINT_TRACEBACK(PyTracebackObject *traceback);
#endif

// Print the exception state, including NULL values.
#if PYTHON_VERSION < 0x3b0
#define PRINT_EXCEPTION(exception_type, exception_value, exception_tb)                                                 \
    _PRINT_EXCEPTION(exception_type, exception_value, exception_tb)
extern void _PRINT_EXCEPTION(PyObject *exception_type, PyObject *exception_value, PyTracebackObject *exception_tb);
#else
#define PRINT_EXCEPTION(exception_type, exception_value, exception_tb) _PRINT_EXCEPTION(exception_value)
extern void _PRINT_EXCEPTION(PyObject *exception_value);
#endif

// Print the current exception state, including NULL values.
extern void PRINT_CURRENT_EXCEPTION(void);

// Print the current exception state, including NULL values.
extern void PRINT_PUBLISHED_EXCEPTION(void);

// Print the representation of the object, or "<NULL>" if it's not set.
extern bool PRINT_REPR(PyObject *object);

// Print the word <NULL>, as an alternative to pointers.
extern bool PRINT_NULL(void);

// Print the type of an object.
extern bool PRINT_TYPE(PyObject *object);

#endif
