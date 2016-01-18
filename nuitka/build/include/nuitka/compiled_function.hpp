//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
// functions and built-in functions, or even better.

struct Nuitka_FunctionObject;

// The actual function code with arguments as an array.
typedef PyObject *(*function_impl_code)( Nuitka_FunctionObject const *, PyObject ** );

// The Nuitka_FunctionObject is the storage associated with a compiled function
// instance of which there can be many for each code.
struct Nuitka_FunctionObject {
    PyObject_HEAD

    PyObject *m_name;

    PyObject *m_module;
    PyObject *m_doc;

    PyCodeObject *m_code_object;
    Py_ssize_t m_args_overall_count;
    Py_ssize_t m_args_positional_count;
    Py_ssize_t m_args_keywords_count;
    bool m_args_simple;
    Py_ssize_t m_args_star_list_index;
    Py_ssize_t m_args_star_dict_index;

    // Same as code_object->co_varnames
    PyObject **m_varnames;

    function_impl_code m_c_code;

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
extern PyObject *Nuitka_Function_New( function_impl_code c_code, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc );
#elif PYTHON_VERSION < 330
extern PyObject *Nuitka_Function_New( function_impl_code c_code, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc );
#else
extern PyObject *Nuitka_Function_New( function_impl_code c_code, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc );
#endif

// Make a function with context.
#if PYTHON_VERSION < 300
extern PyObject *Nuitka_Function_New( function_impl_code c_code, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given );
#elif PYTHON_VERSION < 330
extern PyObject *Nuitka_Function_New( function_impl_code c_code, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given );
#else
extern PyObject *Nuitka_Function_New( function_impl_code c_code, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given );
#endif

static inline bool Nuitka_Function_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Function_Type;
}

static inline PyObject *Nuitka_Function_GetName( PyObject *object )
{
    return ((Nuitka_FunctionObject *)object)->m_name;
}

extern bool parseArgumentsPos( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject **args, Py_ssize_t args_size );
extern bool parseArgumentsMethodPos( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *object, PyObject **args, Py_ssize_t args_size );

extern PyObject *Nuitka_CallFunctionPosArgsKwArgs( Nuitka_FunctionObject const *function, PyObject **args, Py_ssize_t args_size, PyObject *kw );

extern PyObject *Nuitka_CallMethodFunctionNoArgs( Nuitka_FunctionObject const *function, PyObject *object );
extern PyObject *Nuitka_CallMethodFunctionPosArgsKwArgs( Nuitka_FunctionObject const *function, PyObject *object, PyObject **args, Py_ssize_t args_size, PyObject *kw );

#endif
