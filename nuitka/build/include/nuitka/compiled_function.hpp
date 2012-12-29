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
#ifndef __NUITKA_COMPILED_FUNCTION_H__
#define __NUITKA_COMPILED_FUNCTION_H__

#include "Python.h"
#include "frameobject.h"

// Compiled function type.

// The backbone of the integration into CPython. Try to behave as well as normal functions
// and builtin functions, or even better.

// Cleanup function to be called when the function object is released.
typedef void (*releaser)( void * );

struct Nuitka_FunctionObject;

// Method argument parsing function.
typedef PyObject *(*method_arg_parser)( Nuitka_FunctionObject *, PyObject *, PyObject *, PyObject *);
typedef PyObject *(*function_arg_parser)( Nuitka_FunctionObject *, PyObject *, PyObject * );

typedef PyObject *(*argless_code)(PyObject *);

// The Nuitka_FunctionObject is the storage associated with a compiled function instance
// of which there can be many for each code.
struct Nuitka_FunctionObject {
    PyObject_HEAD

    PyObject *m_name;

    void *m_context;
    releaser m_cleanup;

    PyObject *m_module;
    PyObject *m_doc;

    PyCodeObject *m_code_object;

    void *m_code;
    bool m_has_args;

    method_arg_parser m_method_arg_parser;

    PyObject *m_dict;
    PyObject *m_weakrefs;

    // List of defaults, for use in func_defaults and parameter parsing.
    PyObject *m_defaults;

#if PYTHON_VERSION >= 300
    // List of keyword only defaults, for use in __kwdefaults__ and parameter parsing.
    PyObject *m_kwdefaults;
#endif

    long m_counter;
};

extern PyTypeObject Nuitka_Function_Type;


// Make a function without context.
#if PYTHON_VERSION < 300
extern PyObject *Nuitka_Function_New( function_arg_parser code, method_arg_parser, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc );
#else
extern PyObject *Nuitka_Function_New( function_arg_parser code, method_arg_parser, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *module, PyObject *doc );
#endif

// Make a function with context.
#if PYTHON_VERSION < 300
extern PyObject *Nuitka_Function_New( function_arg_parser code, method_arg_parser, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc, void *context, releaser cleanup );
#else
extern PyObject *Nuitka_Function_New( function_arg_parser code, method_arg_parser, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *module, PyObject *doc, void *context, releaser cleanup );
#endif

// Make a function that is only a yielder, no args.
extern PyObject *Nuitka_Function_New( argless_code code, PyObject *name, PyObject *module, PyObject *doc, void * );

static inline bool Nuitka_Function_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Function_Type;
}

static inline PyObject *Nuitka_Function_GetName( PyObject *object )
{
    return ((Nuitka_FunctionObject *)object)->m_name;
}

#endif
