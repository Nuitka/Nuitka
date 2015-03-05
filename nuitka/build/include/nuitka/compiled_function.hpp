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
#ifndef __NUITKA_COMPILED_FUNCTION_H__
#define __NUITKA_COMPILED_FUNCTION_H__

#include "Python.h"
#include "frameobject.h"

// Compiled function type.

// The backbone of the integration into CPython. Try to behave as well as normal
// functions and builtin functions, or even better.

// Cleanup function to be called when the function object is released.
typedef void (*releaser)( void * );

struct Nuitka_FunctionObject;

// Standard Python entry point, accepting argument tuple and keyword dict.
typedef PyObject *(*function_arg_parser)( Nuitka_FunctionObject *, PyObject **, Py_ssize_t, PyObject * );
// Quick call variant, only plain arguments are present and not formed as a
// tuple, allowing shortcuts.
typedef PyObject *(*direct_arg_parser)( Nuitka_FunctionObject *, PyObject **, int );

// The Nuitka_FunctionObject is the storage associated with a compiled function
// instance of which there can be many for each code.
struct Nuitka_FunctionObject {
    PyObject_HEAD

    PyObject *m_name;

    PyObject *m_module;
    PyObject *m_doc;

    PyCodeObject *m_code_object;

    function_arg_parser m_code;
    direct_arg_parser m_direct_arg_parser;

    PyObject *m_dict;
    PyObject *m_weakrefs;

    // List of defaults, for use in __defaults__ and parameter parsing.
    PyObject *m_defaults;
    Py_ssize_t m_defaults_given;

    // Closure taken objects, for use in __closure__ and for accessing it.
    PyCellObject **m_closure;
    Py_ssize_t m_closure_given;

#if PYTHON_VERSION >= 300
    // List of keyword only defaults, for use in __kwdefaults__ and parameter
    // parsing.
    PyObject *m_kwdefaults;

    // Annotations to the function arguments and return value.
    PyObject *m_annotations;
#endif

#if PYTHON_VERSION >= 330
    PyObject *m_qualname;
#endif

    long m_counter;
};

extern PyTypeObject Nuitka_Function_Type;


// Make a function without context.
#if PYTHON_VERSION < 300
extern PyObject *Nuitka_Function_New( function_arg_parser code, direct_arg_parser, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc );
#elif PYTHON_VERSION < 330
extern PyObject *Nuitka_Function_New( function_arg_parser code, direct_arg_parser, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc );
#else
extern PyObject *Nuitka_Function_New( function_arg_parser code, direct_arg_parser, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc );
#endif

// Make a function with context.
#if PYTHON_VERSION < 300
extern PyObject *Nuitka_Function_New( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given );
#elif PYTHON_VERSION < 330
extern PyObject *Nuitka_Function_New( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given );
#else
extern PyObject *Nuitka_Function_New( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given );
#endif

static inline bool Nuitka_Function_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Function_Type;
}

static inline PyObject *Nuitka_Function_GetName( PyObject *object )
{
    return ((Nuitka_FunctionObject *)object)->m_name;
}

extern void ERROR_MULTIPLE_VALUES( Nuitka_FunctionObject *function,
                                   Py_ssize_t index );

extern void ERROR_TOO_MANY_ARGUMENTS( struct Nuitka_FunctionObject *function,
                                      Py_ssize_t given
#if PYTHON_VERSION < 270
                                    , Py_ssize_t kw_size
#endif
#if PYTHON_VERSION >= 330
                                    , Py_ssize_t kw_only
#endif
);

#if PYTHON_VERSION < 330
extern void ERROR_TOO_FEW_ARGUMENTS( Nuitka_FunctionObject *function,
#if PYTHON_VERSION < 270
                                     Py_ssize_t kw_size,
#endif
                                     Py_ssize_t given );
#else
extern void ERROR_TOO_FEW_ARGUMENTS( Nuitka_FunctionObject *function,
                                     PyObject **values);
#endif

extern void ERROR_NO_ARGUMENTS_ALLOWED( struct Nuitka_FunctionObject *function,
#if PYTHON_VERSION >= 330
                                        PyObject *kw,
#endif
                                        Py_ssize_t given );

#if PYTHON_VERSION >= 330
extern void ERROR_TOO_FEW_KWONLY( struct Nuitka_FunctionObject *function,
                                  PyObject **kw_vars );
#endif

#endif
