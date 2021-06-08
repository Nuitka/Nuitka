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

#include "nuitka/prelude.h"

#include "nuitka/compiled_method.h"

#include "nuitka/freelists.h"

// Needed for offsetof
#include <stddef.h>

// tp_descr_get slot, bind a function to an object.
static PyObject *Nuitka_Function_descr_get(PyObject *function, PyObject *object, PyObject *klass) {
    assert(Nuitka_Function_Check(function));

#if PYTHON_VERSION >= 0x300
    if (object == NULL || object == Py_None) {
        Py_INCREF(function);
        return function;
    }
#endif

    return Nuitka_Method_New((struct Nuitka_FunctionObject *)function, object == Py_None ? NULL : object, klass);
}

// tp_repr slot, decide how compiled function shall be output to "repr" built-in
static PyObject *Nuitka_Function_tp_repr(struct Nuitka_FunctionObject *function) {
#if PYTHON_VERSION < 0x300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
        "<compiled_function %s at %p>",
#if PYTHON_VERSION < 0x300
        Nuitka_String_AsString(function->m_name),
#else
        Nuitka_String_AsString(function->m_qualname),
#endif
        function);
}

static PyObject *Nuitka_Function_tp_call(struct Nuitka_FunctionObject *function, PyObject *tuple_args, PyObject *kw) {
    CHECK_OBJECT(tuple_args);
    assert(PyTuple_CheckExact(tuple_args));

    if (kw == NULL) {
        PyObject **args = &PyTuple_GET_ITEM(tuple_args, 0);
        Py_ssize_t args_size = PyTuple_GET_SIZE(tuple_args);

        if (function->m_args_simple && args_size == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < args_size; i++) {
                Py_INCREF(args[i]);
            }

            return function->m_c_code(function, args);
        } else if (function->m_args_simple &&
                   args_size + function->m_defaults_given == function->m_args_positional_count) {
#ifdef _MSC_VER
            PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
            PyObject *python_pars[function->m_args_overall_count];
#endif
            memcpy(python_pars, args, args_size * sizeof(PyObject *));
            memcpy(python_pars + args_size, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_overall_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            return function->m_c_code(function, python_pars);
        } else {
#ifdef _MSC_VER
            PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
            PyObject *python_pars[function->m_args_overall_count];
#endif
            memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

            if (parseArgumentsPos(function, python_pars, args, args_size)) {
                return function->m_c_code(function, python_pars);
            } else {
                return NULL;
            }
        }
    } else {
        return Nuitka_CallFunctionPosArgsKwArgs(function, &PyTuple_GET_ITEM(tuple_args, 0),
                                                PyTuple_GET_SIZE(tuple_args), kw);
    }
}

static long Nuitka_Function_tp_traverse(struct Nuitka_FunctionObject *function, visitproc visit, void *arg) {
    // TODO: Identify the impact of not visiting other owned objects. It appears
    // to be mostly harmless, as these are strings.
    Py_VISIT(function->m_dict);

    for (Py_ssize_t i = 0; i < function->m_closure_given; i++) {
        Py_VISIT(function->m_closure[i]);
    }

    return 0;
}

static long Nuitka_Function_tp_hash(struct Nuitka_FunctionObject *function) { return function->m_counter; }

static PyObject *Nuitka_Function_get_name(struct Nuitka_FunctionObject *object) {
    PyObject *result = object->m_name;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_name(struct Nuitka_FunctionObject *object, PyObject *value) {
#if PYTHON_VERSION < 0x300
    if (unlikely(value == NULL || PyString_Check(value) == 0))
#else
    if (unlikely(value == NULL || PyUnicode_Check(value) == 0))
#endif
    {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__name__ must be set to a string object");
        return -1;
    }

    PyObject *old = object->m_name;
    Py_INCREF(value);
    object->m_name = value;
    Py_DECREF(old);

    return 0;
}

#if PYTHON_VERSION >= 0x300
static PyObject *Nuitka_Function_get_qualname(struct Nuitka_FunctionObject *object) {
    PyObject *result = object->m_qualname;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_qualname(struct Nuitka_FunctionObject *object, PyObject *value) {
    if (unlikely(value == NULL || PyUnicode_Check(value) == 0)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__qualname__ must be set to a string object");
        return -1;
    }

    PyObject *old = object->m_qualname;
    Py_INCREF(value);
    object->m_qualname = value;
    Py_DECREF(old);

    return 0;
}
#endif

static PyObject *Nuitka_Function_get_doc(struct Nuitka_FunctionObject *object) {
    PyObject *result = object->m_doc;

    if (result == NULL) {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_doc(struct Nuitka_FunctionObject *object, PyObject *value) {
    PyObject *old = object->m_doc;

    object->m_doc = value;
    Py_XINCREF(value);

    Py_XDECREF(old);

    return 0;
}

static PyObject *Nuitka_Function_get_dict(struct Nuitka_FunctionObject *object) {
    if (object->m_dict == NULL) {
        object->m_dict = PyDict_New();
    }

    Py_INCREF(object->m_dict);
    return object->m_dict;
}

static int Nuitka_Function_set_dict(struct Nuitka_FunctionObject *object, PyObject *value) {
    if (unlikely(value == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "function's dictionary may not be deleted");
        return -1;
    }

    if (likely(PyDict_Check(value))) {
        PyObject *old = object->m_dict;
        Py_INCREF(value);
        object->m_dict = value;
        Py_XDECREF(old);

        return 0;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "setting function's dictionary to a non-dict");
        return -1;
    }
}

static PyObject *Nuitka_Function_get_code(struct Nuitka_FunctionObject *object) {
    PyObject *result = (PyObject *)object->m_code_object;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_code(struct Nuitka_FunctionObject *object, PyObject *value) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "__code__ is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Function_get_closure(struct Nuitka_FunctionObject *object) {
    if (object->m_closure_given > 0) {
        PyObject *result = PyTuple_New(object->m_closure_given);

        for (Py_ssize_t i = 0; i < object->m_closure_given; i++) {
            PyTuple_SET_ITEM0(result, i, (PyObject *)object->m_closure[i]);
        }

        return result;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

static int Nuitka_Function_set_closure(struct Nuitka_FunctionObject *object, PyObject *value) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(
#if PYTHON_VERSION < 0x300
        PyExc_TypeError,
#else
        PyExc_AttributeError,
#endif
        "readonly attribute");

    return -1;
}

static PyObject *Nuitka_Function_get_defaults(struct Nuitka_FunctionObject *object) {
    PyObject *result = (PyObject *)object->m_defaults;
    Py_INCREF(result);
    return result;
}

static void onUpdatedDefaultsValue(struct Nuitka_FunctionObject *function) {
    if (function->m_defaults == Py_None) {
        function->m_defaults_given = 0;
    } else {
        function->m_defaults_given = PyTuple_GET_SIZE(function->m_defaults);
    }
}

static int Nuitka_Function_set_defaults(struct Nuitka_FunctionObject *object, PyObject *value) {
    if (value == NULL) {
        value = Py_None;
    }

    if (unlikely(value != Py_None && PyTuple_Check(value) == false)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__defaults__ must be set to a tuple object");
        return -1;
    }

// TODO: Do we actually need this ever, probably not, as we don't generate argument
// parsing per function anymore.
#ifndef _NUITKA_PLUGIN_DILL_ENABLED
    if (object->m_defaults == Py_None && value != Py_None) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "Nuitka doesn't support __defaults__ size changes");
        return -1;
    }

    if (object->m_defaults != Py_None &&
        (value == Py_None || PyTuple_GET_SIZE(object->m_defaults) != PyTuple_GET_SIZE(value))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "Nuitka doesn't support __defaults__ size changes");
        return -1;
    }
#endif

    PyObject *old = object->m_defaults;
    Py_INCREF(value);
    object->m_defaults = value;
    Py_DECREF(old);

    onUpdatedDefaultsValue(object);

    return 0;
}

#if PYTHON_VERSION >= 0x300
static PyObject *Nuitka_Function_get_kwdefaults(struct Nuitka_FunctionObject *object) {
    PyObject *result = object->m_kwdefaults;

    if (result == NULL) {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_kwdefaults(struct Nuitka_FunctionObject *object, PyObject *value) {
    if (value == NULL) {
        value = Py_None;
    }

    if (unlikely(value != Py_None && PyDict_Check(value) == false)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__kwdefaults__ must be set to a dict object");
        return -1;
    }

    if (value == Py_None) {
        value = NULL;
    }

    PyObject *old = object->m_kwdefaults;
    Py_XINCREF(value);
    object->m_kwdefaults = value;
    Py_XDECREF(old);

    return 0;
}

static PyObject *Nuitka_Function_get_annotations(struct Nuitka_FunctionObject *object) {
    if (object->m_annotations == NULL) {
        object->m_annotations = PyDict_New();
    }

    Py_INCREF(object->m_annotations);
    return object->m_annotations;
}

static int Nuitka_Function_set_annotations(struct Nuitka_FunctionObject *object, PyObject *value) {
    if (unlikely(value != NULL && PyDict_Check(value) == false)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "__annotations__ must be set to a dict object");
        return -1;
    }

    PyObject *old = object->m_annotations;
    Py_XINCREF(value);
    object->m_annotations = value;
    Py_XDECREF(old);

    return 0;
}

#endif

static int Nuitka_Function_set_globals(struct Nuitka_FunctionObject *function, PyObject *value) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_Function_get_globals(struct Nuitka_FunctionObject *function) {
    PyObject *result = PyModule_GetDict(function->m_module);
    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_module(struct Nuitka_FunctionObject *object, PyObject *value) {
    if (object->m_dict == NULL) {
        object->m_dict = PyDict_New();
    }

    if (value == NULL) {
        value = Py_None;
    }

    return PyDict_SetItem(object->m_dict, const_str_plain___module__, value);
}

static PyObject *Nuitka_Function_get_module(struct Nuitka_FunctionObject *object) {
    PyObject *result;

    // The __dict__ might overrule this.
    if (object->m_dict) {
        result = DICT_GET_ITEM1(object->m_dict, const_str_plain___module__);

        if (result != NULL) {
            return result;
        }
    }

    result = MODULE_NAME1(object->m_module);
    return result;
}

static PyGetSetDef Nuitka_Function_getset[] = {
#if PYTHON_VERSION >= 0x300
    {(char *)"__qualname__", (getter)Nuitka_Function_get_qualname, (setter)Nuitka_Function_set_qualname, NULL},
#endif
#if PYTHON_VERSION < 0x300
    {(char *)"func_name", (getter)Nuitka_Function_get_name, (setter)Nuitka_Function_set_name, NULL},
#endif
    {(char *)"__name__", (getter)Nuitka_Function_get_name, (setter)Nuitka_Function_set_name, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_doc", (getter)Nuitka_Function_get_doc, (setter)Nuitka_Function_set_doc, NULL},
#endif
    {(char *)"__doc__", (getter)Nuitka_Function_get_doc, (setter)Nuitka_Function_set_doc, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_dict", (getter)Nuitka_Function_get_dict, (setter)Nuitka_Function_set_dict, NULL},
#endif
    {(char *)"__dict__", (getter)Nuitka_Function_get_dict, (setter)Nuitka_Function_set_dict, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_code", (getter)Nuitka_Function_get_code, (setter)Nuitka_Function_set_code, NULL},
#endif
    {(char *)"__code__", (getter)Nuitka_Function_get_code, (setter)Nuitka_Function_set_code, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_defaults", (getter)Nuitka_Function_get_defaults, (setter)Nuitka_Function_set_defaults, NULL},
#endif
    {(char *)"__defaults__", (getter)Nuitka_Function_get_defaults, (setter)Nuitka_Function_set_defaults, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_globals", (getter)Nuitka_Function_get_globals, (setter)Nuitka_Function_set_globals, NULL},
#endif
    {(char *)"__closure__", (getter)Nuitka_Function_get_closure, (setter)Nuitka_Function_set_closure, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_closure", (getter)Nuitka_Function_get_closure, (setter)Nuitka_Function_set_closure, NULL},
#endif
    {(char *)"__globals__", (getter)Nuitka_Function_get_globals, (setter)Nuitka_Function_set_globals, NULL},
    {(char *)"__module__", (getter)Nuitka_Function_get_module, (setter)Nuitka_Function_set_module, NULL},
#if PYTHON_VERSION >= 0x300
    {(char *)"__kwdefaults__", (getter)Nuitka_Function_get_kwdefaults, (setter)Nuitka_Function_set_kwdefaults, NULL},
    {(char *)"__annotations__", (getter)Nuitka_Function_get_annotations, (setter)Nuitka_Function_set_annotations, NULL},

#endif
    {NULL}};

static PyObject *Nuitka_Function_reduce(struct Nuitka_FunctionObject *function) {
    PyObject *result;

#if PYTHON_VERSION < 0x300
    result = function->m_name;
#else
    result = function->m_qualname;
#endif

    Py_INCREF(result);
    return result;
}

#define MAX_FUNCTION_FREE_LIST_COUNT 100
static struct Nuitka_FunctionObject *free_list_functions = NULL;
static int free_list_functions_count = 0;

static void Nuitka_Function_tp_dealloc(struct Nuitka_FunctionObject *function) {
#ifndef __NUITKA_NO_ASSERT__
    // Save the current exception, if any, we must to not corrupt it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);
    RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
#endif

    Nuitka_GC_UnTrack(function);

    if (function->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)function);
    }

    Py_DECREF(function->m_name);
#if PYTHON_VERSION >= 0x300
    Py_DECREF(function->m_qualname);
#endif

    // These may actually re-surrect the object, not?
    Py_XDECREF(function->m_dict);
    Py_DECREF(function->m_defaults);

    Py_XDECREF(function->m_doc);

#if PYTHON_VERSION >= 0x300
    Py_XDECREF(function->m_kwdefaults);
    Py_XDECREF(function->m_annotations);
#endif

    for (Py_ssize_t i = 0; i < function->m_closure_given; i++) {
        assert(function->m_closure[i]);
        Py_DECREF(function->m_closure[i]);

        // Note: No need to set to NULL, each function creation makes
        // a full copy, doing the init.
    }

    /* Put the object into freelist or release to GC */
    releaseToFreeList(free_list_functions, function, MAX_FUNCTION_FREE_LIST_COUNT);

#ifndef __NUITKA_NO_ASSERT__
    PyThreadState *tstate = PyThreadState_GET();

    assert(tstate->curexc_type == save_exception_type);
    assert(tstate->curexc_value == save_exception_value);
    assert((PyTracebackObject *)tstate->curexc_traceback == save_exception_tb);
#endif
}

static PyMethodDef Nuitka_Function_methods[] = {{"__reduce__", (PyCFunction)Nuitka_Function_reduce, METH_NOARGS, NULL},
                                                {NULL}};

PyTypeObject Nuitka_Function_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_function", /* tp_name */
    sizeof(struct Nuitka_FunctionObject),               /* tp_basicsize */
    sizeof(struct Nuitka_CellObject *),                 /* tp_itemsize */
    (destructor)Nuitka_Function_tp_dealloc,             /* tp_dealloc */
#if PYTHON_VERSION < 0x380
    0, /* tp_print */
#else
    offsetof(struct Nuitka_FunctionObject, m_vectorcall), /* tp_vectorcall_offset */
#endif
    0,                                    /* tp_getattr */
    0,                                    /* tp_setattr */
    0,                                    /* tp_compare */
    (reprfunc)Nuitka_Function_tp_repr,    /* tp_repr */
    0,                                    /* tp_as_number */
    0,                                    /* tp_as_sequence */
    0,                                    /* tp_as_mapping */
    (hashfunc)Nuitka_Function_tp_hash,    /* tp_hash */
    (ternaryfunc)Nuitka_Function_tp_call, /* tp_call */
    0,                                    /* tp_str */
    PyObject_GenericGetAttr,              /* tp_getattro */
    0,                                    /* tp_setattro */
    0,                                    /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
#if PYTHON_VERSION < 0x300
        Py_TPFLAGS_HAVE_WEAKREFS |
#endif
#if PYTHON_VERSION >= 0x380
        _Py_TPFLAGS_HAVE_VECTORCALL | Py_TPFLAGS_METHOD_DESCRIPTOR |
#endif
        Py_TPFLAGS_HAVE_GC,                             /* tp_flags */
    0,                                                  /* tp_doc */
    (traverseproc)Nuitka_Function_tp_traverse,          /* tp_traverse */
    0,                                                  /* tp_clear */
    0,                                                  /* tp_richcompare */
    offsetof(struct Nuitka_FunctionObject, m_weakrefs), /* tp_weaklistoffset */
    0,                                                  /* tp_iter */
    0,                                                  /* tp_iternext */
    Nuitka_Function_methods,                            /* tp_methods */
    0,                                                  /* tp_members */
    Nuitka_Function_getset,                             /* tp_getset */
    0,                                                  /* tp_base */
    0,                                                  /* tp_dict */
    Nuitka_Function_descr_get,                          /* tp_descr_get */
    0,                                                  /* tp_descr_set */
    offsetof(struct Nuitka_FunctionObject, m_dict),     /* tp_dictoffset */
    0,                                                  /* tp_init */
    0,                                                  /* tp_alloc */
    0,                                                  /* tp_new */
    0,                                                  /* tp_free */
    0,                                                  /* tp_is_gc */
    0,                                                  /* tp_bases */
    0,                                                  /* tp_mro */
    0,                                                  /* tp_cache */
    0,                                                  /* tp_subclasses */
    0,                                                  /* tp_weaklist */
    0,                                                  /* tp_del */
    0                                                   /* tp_version_tag */
#if PYTHON_VERSION >= 0x340
    ,
    0 /* tp_finalizer */
#endif
};

void _initCompiledFunctionType(void) {

    PyType_Ready(&Nuitka_Function_Type);

#ifdef _NUITKA_PLUGIN_DILL_ENABLED
    // TODO: Move this to a __nuitka__ module maybe
    PyObject_SetAttrString((PyObject *)builtin_module, "compiled_function", (PyObject *)&Nuitka_Function_Type);
#endif
}

// Shared implementations for empty functions. When a function body is empty, but
// still needs to exist, e.g. overloaded functions, this is saving the effort to
// produce one.
static PyObject *_Nuitka_FunctionEmptyCodeNoneImpl(struct Nuitka_FunctionObject const *function,
                                                   PyObject **python_pars) {
    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = Py_None;

    Py_INCREF(result);
    return result;
}

static PyObject *_Nuitka_FunctionEmptyCodeTrueImpl(struct Nuitka_FunctionObject const *function,
                                                   PyObject **python_pars) {
    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = Py_True;

    Py_INCREF(result);
    return result;
}

static PyObject *_Nuitka_FunctionEmptyCodeFalseImpl(struct Nuitka_FunctionObject const *function,
                                                    PyObject **python_pars) {
    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = Py_False;

    Py_INCREF(result);
    return result;
}

static PyObject *_Nuitka_FunctionEmptyCodeGenericImpl(struct Nuitka_FunctionObject const *function,
                                                      PyObject **python_pars) {
    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = function->m_constant_return_value;

    Py_INCREF(result);
    return result;
}

void Nuitka_Function_EnableConstReturnTrue(struct Nuitka_FunctionObject *function) {
    function->m_constant_return_value = Py_True;
    function->m_c_code = _Nuitka_FunctionEmptyCodeTrueImpl;
}

void Nuitka_Function_EnableConstReturnFalse(struct Nuitka_FunctionObject *function) {
    function->m_constant_return_value = Py_False;
    function->m_c_code = _Nuitka_FunctionEmptyCodeFalseImpl;
}

void Nuitka_Function_EnableConstReturnGeneric(struct Nuitka_FunctionObject *function, PyObject *value) {
    function->m_constant_return_value = value;
    function->m_c_code = _Nuitka_FunctionEmptyCodeGenericImpl;
}

#if PYTHON_VERSION >= 0x380
static PyObject *Nuitka_Function_tp_vectorcall(struct Nuitka_FunctionObject *function, PyObject *const *stack,
                                               size_t nargsf, PyObject *kwnames);
#endif

// Make a function with closure.
#if PYTHON_VERSION < 0x300
struct Nuitka_FunctionObject *Nuitka_Function_New(function_impl_code c_code, PyObject *name, PyCodeObject *code_object,
                                                  PyObject *defaults, PyObject *module, PyObject *doc,
                                                  struct Nuitka_CellObject **closure, Py_ssize_t closure_given)
#else
struct Nuitka_FunctionObject *Nuitka_Function_New(function_impl_code c_code, PyObject *name, PyObject *qualname,
                                                  PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults,
                                                  PyObject *annotations, PyObject *module, PyObject *doc,
                                                  struct Nuitka_CellObject **closure, Py_ssize_t closure_given)
#endif
{
    struct Nuitka_FunctionObject *result;

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_functions, struct Nuitka_FunctionObject, Nuitka_Function_Type, closure_given);

    memcpy(&result->m_closure[0], closure, closure_given * sizeof(struct Nuitka_CellObject *));
    result->m_closure_given = closure_given;

    if (c_code != NULL) {
        result->m_c_code = c_code;
#ifndef __NUITKA_NO_ASSERT__
        result->m_constant_return_value = NULL;
#endif
    } else {
        result->m_c_code = _Nuitka_FunctionEmptyCodeNoneImpl;
        result->m_constant_return_value = Py_None;
    }

    Py_INCREF(name);
    result->m_name = name;

#if PYTHON_VERSION >= 0x300
    // The "qualname" defaults to NULL for most compact C code.
    if (qualname == NULL) {
        qualname = name;
    }
    CHECK_OBJECT(qualname);

    Py_INCREF(qualname);
    result->m_qualname = qualname;
#endif

    if (defaults == NULL) {
        Py_INCREF(Py_None);
        defaults = Py_None;
    }
    CHECK_OBJECT(defaults);
    assert(defaults == Py_None || (PyTuple_Check(defaults) && PyTuple_GET_SIZE(defaults) > 0));
    result->m_defaults = defaults;

    onUpdatedDefaultsValue(result);

#if PYTHON_VERSION >= 0x300
    assert(kwdefaults == NULL || (PyDict_Check(kwdefaults) && DICT_SIZE(kwdefaults) > 0));
    result->m_kwdefaults = kwdefaults;

    assert(annotations == NULL || (PyDict_Check(annotations) && DICT_SIZE(annotations) > 0));
    result->m_annotations = annotations;
#endif

    result->m_code_object = code_object;
    result->m_args_positional_count = code_object->co_argcount;
    result->m_args_keywords_count = result->m_args_positional_count;
#if PYTHON_VERSION >= 0x300
    result->m_args_keywords_count += code_object->co_kwonlyargcount;
#endif
#if PYTHON_VERSION >= 0x380
    result->m_args_pos_only_count = code_object->co_posonlyargcount;
#endif

    result->m_args_overall_count = result->m_args_keywords_count + ((code_object->co_flags & CO_VARARGS) ? 1 : 0) +
                                   ((code_object->co_flags & CO_VARKEYWORDS) ? 1 : 0);

    result->m_args_simple = (code_object->co_flags & (CO_VARARGS | CO_VARKEYWORDS)) == 0;
#if PYTHON_VERSION >= 0x300
    if (code_object->co_kwonlyargcount > 0) {
        result->m_args_simple = false;
    }
#endif

    if ((code_object->co_flags & CO_VARARGS) != 0) {
        result->m_args_star_list_index = result->m_args_keywords_count;
    } else {
        result->m_args_star_list_index = -1;
    }

    if ((code_object->co_flags & CO_VARKEYWORDS) != 0) {
        result->m_args_star_dict_index = result->m_args_keywords_count;

        if (code_object->co_flags & CO_VARARGS) {
            result->m_args_star_dict_index += 1;
        }
    } else {
        result->m_args_star_dict_index = -1;
    }

    result->m_varnames = &PyTuple_GET_ITEM(code_object->co_varnames, 0);

    result->m_module = module;

    Py_XINCREF(doc);
    result->m_doc = doc;

    result->m_dict = NULL;
    result->m_weakrefs = NULL;

    static long Nuitka_Function_counter = 0;
    result->m_counter = Nuitka_Function_counter++;

#if PYTHON_VERSION >= 0x380
    result->m_vectorcall = (vectorcallfunc)Nuitka_Function_tp_vectorcall;
#endif

    Nuitka_GC_Track(result);

    assert(Py_REFCNT(result) == 1);

    return result;
}

static void formatErrorNoArgumentAllowed(struct Nuitka_FunctionObject const *function,
#if PYTHON_VERSION >= 0x300
                                         PyObject *kw,
#endif
                                         Py_ssize_t given) {
    char const *function_name = Nuitka_String_AsString(function->m_name);

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "%s() takes no arguments (%zd given)", function_name, given);
#else
    if (kw == NULL) {
        PyErr_Format(PyExc_TypeError, "%s() takes 0 positional arguments but %zd was given", function_name, given);
    } else {
        PyObject *tmp_iter = PyObject_GetIter(kw);
        PyObject *tmp_arg_name = PyIter_Next(tmp_iter);
        Py_DECREF(tmp_iter);

        PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'", function_name,
                     Nuitka_String_AsString(tmp_arg_name));

        Py_DECREF(tmp_arg_name);
    }
#endif
}

static void formatErrorMultipleValuesGiven(struct Nuitka_FunctionObject const *function, Py_ssize_t index) {
#if PYTHON_VERSION < 0x390
    char const *function_name = Nuitka_String_AsString(function->m_name);
#else
    char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

    PyErr_Format(PyExc_TypeError,
#if PYTHON_VERSION < 0x300
                 "%s() got multiple values for keyword argument '%s'",
#else
                 "%s() got multiple values for argument '%s'",
#endif
                 function_name, Nuitka_String_AsString(function->m_varnames[index]));
}

#if PYTHON_VERSION < 0x300
static void formatErrorTooFewArguments(struct Nuitka_FunctionObject const *function,
#if PYTHON_VERSION < 0x270
                                       Py_ssize_t kw_size,
#endif
                                       Py_ssize_t given) {
    Py_ssize_t required_parameter_count = function->m_args_positional_count - function->m_defaults_given;

    char const *function_name = Nuitka_String_AsString(function->m_name);
    char const *violation =
        (function->m_defaults != Py_None || function->m_args_star_list_index != -1) ? "at least" : "exactly";
    char const *plural = required_parameter_count == 1 ? "" : "s";

#if PYTHON_VERSION < 0x270
    if (kw_size > 0) {
        PyErr_Format(PyExc_TypeError, "%s() takes %s %zd non-keyword argument%s (%zd given)", function_name, violation,
                     required_parameter_count, plural, given - function->m_defaults_given);
    } else {
        PyErr_Format(PyExc_TypeError, "%s() takes %s %zd argument%s (%zd given)", function_name, violation,
                     required_parameter_count, plural, given);
    }
#else
    PyErr_Format(PyExc_TypeError, "%s() takes %s %zd argument%s (%zd given)", function_name, violation,
                 required_parameter_count, plural, given);
#endif
}
#else
static void formatErrorTooFewArguments(struct Nuitka_FunctionObject const *function, PyObject **values) {
    char const *function_name = Nuitka_String_AsString(function->m_name);

    Py_ssize_t max_missing = 0;

    for (Py_ssize_t i = function->m_args_positional_count - 1 - function->m_defaults_given; i >= 0; --i) {
        if (values[i] == NULL) {
            max_missing += 1;
        }
    }

    PyObject *list_str = PyUnicode_FromString("");

    PyObject *comma_str = PyUnicode_FromString(", ");
    PyObject *and_str = PyUnicode_FromString(max_missing == 2 ? " and " : ", and ");

    Py_ssize_t missing = 0;
    for (Py_ssize_t i = function->m_args_positional_count - 1 - function->m_defaults_given; i >= 0; --i) {
        if (values[i] == NULL) {
            PyObject *current_str = function->m_varnames[i];

            PyObject *current = PyObject_Repr(current_str);

            if (missing == 0) {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(list_str, current);

                Py_DECREF(old);
            } else if (missing == 1) {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(and_str, list_str);

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(current, list_str);

                Py_DECREF(old);
            } else {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(comma_str, list_str);

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(current, list_str);

                Py_DECREF(old);
            }

            Py_DECREF(current);

            missing += 1;
        }
    }

    Py_DECREF(comma_str);
    Py_DECREF(and_str);

    PyErr_Format(PyExc_TypeError, "%s() missing %zd required positional argument%s: %s", function_name, max_missing,
                 max_missing > 1 ? "s" : "", Nuitka_String_AsString(list_str));

    Py_DECREF(list_str);
}
#endif

static void formatErrorTooManyArguments(struct Nuitka_FunctionObject const *function, Py_ssize_t given
#if PYTHON_VERSION < 0x270
                                        ,
                                        Py_ssize_t kw_size

#endif
#if PYTHON_VERSION >= 0x300
                                        ,
                                        Py_ssize_t kw_only
#endif
) {
    Py_ssize_t top_level_parameter_count = function->m_args_positional_count;

    char const *function_name = Nuitka_String_AsString(function->m_name);
#if PYTHON_VERSION < 0x300
    char const *violation = function->m_defaults != Py_None ? "at most" : "exactly";
#endif
    char const *plural = top_level_parameter_count == 1 ? "" : "s";

#if PYTHON_VERSION < 0x270
    PyErr_Format(PyExc_TypeError, "%s() takes %s %zd %sargument%s (%zd given)", function_name, violation,
                 top_level_parameter_count, kw_size > 0 ? "non-keyword " : "", plural, given);
#elif PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "%s() takes %s %zd argument%s (%zd given)", function_name, violation,
                 top_level_parameter_count, plural, given);
#else
    char keyword_only_part[100];

    if (kw_only > 0) {
        snprintf(keyword_only_part, sizeof(keyword_only_part) - 1,
                 " positional argument%s (and %" PY_FORMAT_SIZE_T "d keyword-only argument%s)", given != 1 ? "s" : "",
                 kw_only, kw_only != 1 ? "s" : "");
    } else {
        keyword_only_part[0] = 0;
    }

    if (function->m_defaults_given == 0) {
        PyErr_Format(PyExc_TypeError, "%s() takes %zd positional argument%s but %zd%s were given", function_name,
                     top_level_parameter_count, plural, given, keyword_only_part);
    } else {
        PyErr_Format(PyExc_TypeError, "%s() takes from %zd to %zd positional argument%s but %zd%s were given",
                     function_name, top_level_parameter_count - function->m_defaults_given, top_level_parameter_count,
                     plural, given, keyword_only_part);
    }
#endif
}

#if PYTHON_VERSION >= 0x300
static void formatErrorTooFewKwOnlyArguments(struct Nuitka_FunctionObject const *function, PyObject **kw_vars) {
    char const *function_name = Nuitka_String_AsString(function->m_name);

    Py_ssize_t kwonlyargcount = function->m_code_object->co_kwonlyargcount;

    Py_ssize_t max_missing = 0;

    for (Py_ssize_t i = kwonlyargcount - 1; i >= 0; --i) {
        if (kw_vars[i] == NULL) {
            max_missing += 1;
        }
    }

    PyObject *list_str = PyUnicode_FromString("");

    PyObject *comma_str = PyUnicode_FromString(", ");
    PyObject *and_str = PyUnicode_FromString(max_missing == 2 ? " and " : ", and ");

    Py_ssize_t missing = 0;
    for (Py_ssize_t i = kwonlyargcount - 1; i >= 0; --i) {
        if (kw_vars[i] == NULL) {
            PyObject *current_str = function->m_varnames[function->m_args_positional_count + i];

            PyObject *current = PyObject_Repr(current_str);

            if (missing == 0) {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(list_str, current);

                Py_DECREF(old);
            } else if (missing == 1) {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(and_str, list_str);

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(current, list_str);

                Py_DECREF(old);
            } else {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(comma_str, list_str);

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(current, list_str);

                Py_DECREF(old);
            }

            Py_DECREF(current);

            missing += 1;
        }
    }

    Py_DECREF(comma_str);
    Py_DECREF(and_str);

    PyErr_Format(PyExc_TypeError, "%s() missing %zd required keyword-only argument%s: %s", function_name, max_missing,
                 max_missing > 1 ? "s" : "", Nuitka_String_AsString(list_str));

    Py_DECREF(list_str);
}
#endif

static void formatErrorKeywordsMustBeString(struct Nuitka_FunctionObject const *function) {
#if PYTHON_VERSION < 0x390
    char const *function_name = Nuitka_String_AsString(function->m_name);
    PyErr_Format(PyExc_TypeError, "%s() keywords must be strings", function_name);
#else
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "keywords must be strings");
#endif
}

#if PYTHON_VERSION < 0x300
static Py_ssize_t handleKeywordArgs(struct Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw)
#else
static Py_ssize_t handleKeywordArgs(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                    Py_ssize_t *kw_only_found, PyObject *kw)
#endif
{
    Py_ssize_t keywords_count = function->m_args_keywords_count;

#if PYTHON_VERSION >= 0x300
    Py_ssize_t keyword_after_index = function->m_args_positional_count;
#endif

    assert(function->m_args_star_dict_index == -1);

    Py_ssize_t kw_found = 0;
    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while (PyDict_Next(kw, &ppos, &key, &value)) {
#if PYTHON_VERSION < 0x300
        if (unlikely(!PyString_Check(key) && !PyUnicode_Check(key)))
#else
        if (unlikely(!PyUnicode_Check(key)))
#endif
        {
            formatErrorKeywordsMustBeString(function);
            return -1;
        }

        NUITKA_MAY_BE_UNUSED bool found = false;

        Py_INCREF(key);
        Py_INCREF(value);

#if PYTHON_VERSION < 0x380
        Py_ssize_t kw_arg_start = 0;
#else
        Py_ssize_t kw_arg_start = function->m_args_pos_only_count;
#endif

        for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
            if (function->m_varnames[i] == key) {
                assert(python_pars[i] == NULL);
                python_pars[i] = value;

#if PYTHON_VERSION >= 0x300
                if (i >= keyword_after_index) {
                    *kw_only_found += 1;
                }
#endif

                found = true;
                break;
            }
        }

        if (found == false) {
            PyObject **varnames = function->m_varnames;

            for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
                if (RICH_COMPARE_EQ_CBOOL_OBJECT_OBJECT(varnames[i], key)) {
                    assert(python_pars[i] == NULL);
                    python_pars[i] = value;

#if PYTHON_VERSION >= 0x300
                    if (i >= keyword_after_index) {
                        *kw_only_found += 1;
                    }
#endif

                    found = true;
                    break;
                }
            }
        }

        if (unlikely(found == false)) {
            bool pos_only_error = false;

            for (Py_ssize_t i = 0; i < kw_arg_start; i++) {
                PyObject **varnames = function->m_varnames;

                if (RICH_COMPARE_EQ_CBOOL_OBJECT_OBJECT(varnames[i], key)) {
                    pos_only_error = true;
                    break;
                }
            }

            if (pos_only_error == true) {
                PyErr_Format(PyExc_TypeError,
                             "%s() got some positional-only arguments passed as keyword arguments: '%s'",
                             Nuitka_String_AsString(function->m_name),
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");

            } else {

                PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'",
                             Nuitka_String_AsString(function->m_name),
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");
            }

            Py_DECREF(key);
            Py_DECREF(value);

            return -1;
        }

        Py_DECREF(key);

        kw_found += 1;
    }

    return kw_found;
}

static bool MAKE_STAR_DICT_DICTIONARY_COPY(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                           PyObject *kw) {
    Py_ssize_t star_dict_index = function->m_args_star_dict_index;
    assert(star_dict_index != -1);

    if (kw == NULL) {
        python_pars[star_dict_index] = PyDict_New();
    } else if (((PyDictObject *)kw)->ma_used > 0) {
#if PYTHON_VERSION < 0x300
        python_pars[star_dict_index] = _PyDict_NewPresized(((PyDictObject *)kw)->ma_used);

        for (int i = 0; i <= ((PyDictObject *)kw)->ma_mask; i++) {
            PyDictEntry *entry = &((PyDictObject *)kw)->ma_table[i];

            if (entry->me_value != NULL) {

                if (unlikely(!PyString_Check(entry->me_key) && !PyUnicode_Check(entry->me_key))) {
                    formatErrorKeywordsMustBeString(function);
                    return false;
                }

                int res = PyDict_SetItem(python_pars[star_dict_index], entry->me_key, entry->me_value);

                if (unlikely(res != 0)) {
                    return false;
                }
            }
        }
#else
        if (_PyDict_HasSplitTable((PyDictObject *)kw)) {
            PyDictObject *mp = (PyDictObject *)kw;

            PyObject **newvalues = PyMem_NEW(PyObject *, mp->ma_keys->dk_size);
            assert(newvalues != NULL);

            PyDictObject *split_copy = PyObject_GC_New(PyDictObject, &PyDict_Type);
            assert(split_copy != NULL);

            split_copy->ma_values = newvalues;
            split_copy->ma_keys = mp->ma_keys;
            split_copy->ma_used = mp->ma_used;

            mp->ma_keys->dk_refcnt += 1;

            Nuitka_GC_Track(split_copy);

#if PYTHON_VERSION < 0x360
            Py_ssize_t size = mp->ma_keys->dk_size;
#else
            Py_ssize_t size = DK_USABLE_FRACTION(DK_SIZE(mp->ma_keys));
#endif
            for (Py_ssize_t i = 0; i < size; i++) {
#if PYTHON_VERSION < 0x360
                PyDictKeyEntry *entry = &split_copy->ma_keys->dk_entries[i];
#else
                PyDictKeyEntry *entry = &DK_ENTRIES(split_copy->ma_keys)[i];
#endif
                if ((entry->me_key != NULL) && unlikely(!PyUnicode_Check(entry->me_key))) {
                    formatErrorKeywordsMustBeString(function);
                    return false;
                }

                split_copy->ma_values[i] = mp->ma_values[i];
                Py_XINCREF(split_copy->ma_values[i]);
            }

            python_pars[star_dict_index] = (PyObject *)split_copy;
        } else {
            python_pars[star_dict_index] = PyDict_New();

            PyDictObject *mp = (PyDictObject *)kw;

#if PYTHON_VERSION < 0x360
            Py_ssize_t size = mp->ma_keys->dk_size;
#else
            Py_ssize_t size = mp->ma_keys->dk_nentries;
#endif
            for (Py_ssize_t i = 0; i < size; i++) {
#if PYTHON_VERSION < 0x360
                PyDictKeyEntry *entry = &mp->ma_keys->dk_entries[i];
#else
                PyDictKeyEntry *entry = &DK_ENTRIES(mp->ma_keys)[i];
#endif

                PyObject *value = entry->me_value;

                if (value != NULL) {
                    if (unlikely(!PyUnicode_Check(entry->me_key))) {
                        formatErrorKeywordsMustBeString(function);
                        return false;
                    }

                    int res = PyDict_SetItem(python_pars[star_dict_index], entry->me_key, value);

                    if (unlikely(res != 0)) {
                        return false;
                    }
                }
            }
        }
#endif
    } else {
        python_pars[star_dict_index] = PyDict_New();
    }

    return true;
}

#if PYTHON_VERSION < 0x300
static Py_ssize_t handleKeywordArgsWithStarDict(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                                PyObject *kw)
#else
static Py_ssize_t handleKeywordArgsWithStarDict(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                                Py_ssize_t *kw_only_found, PyObject *kw)
#endif
{
    assert(function->m_args_star_dict_index != -1);

    if (unlikely(MAKE_STAR_DICT_DICTIONARY_COPY(function, python_pars, kw) == false)) {
        return -1;
    }

    Py_ssize_t kw_found = 0;
    Py_ssize_t keywords_count = function->m_args_keywords_count;
#if PYTHON_VERSION >= 0x300
    Py_ssize_t keyword_after_index = function->m_args_positional_count;
#endif

    Py_ssize_t dict_star_index = function->m_args_star_dict_index;

    PyObject **varnames = function->m_varnames;

#if PYTHON_VERSION < 0x380
    Py_ssize_t kw_arg_start = 0;
#else
    Py_ssize_t kw_arg_start = function->m_args_pos_only_count;
#endif

    for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
        PyObject *arg_name = varnames[i];

        PyObject *kw_arg_value = DICT_GET_ITEM1(python_pars[dict_star_index], arg_name);

        if (kw_arg_value != NULL) {
            assert(python_pars[i] == NULL);

            python_pars[i] = kw_arg_value;

            PyDict_DelItem(python_pars[dict_star_index], arg_name);

            kw_found += 1;

#if PYTHON_VERSION >= 0x300
            if (i >= keyword_after_index) {
                *kw_only_found += 1;
            }
#endif
        }
    }

    return kw_found;
}

static void makeStarListTupleCopy(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                  PyObject *const *args, Py_ssize_t args_size) {
    assert(function->m_args_star_list_index != -1);
    Py_ssize_t list_star_index = function->m_args_star_list_index;

    // Copy left-over argument values to the star list parameter given.
    if (args_size > function->m_args_positional_count) {
        python_pars[list_star_index] = PyTuple_New(args_size - function->m_args_positional_count);

        for (Py_ssize_t i = 0; i < args_size - function->m_args_positional_count; i++) {
            PyObject *value = args[function->m_args_positional_count + i];

            PyTuple_SET_ITEM(python_pars[list_star_index], i, value);
            Py_INCREF(value);
        }
    } else {
        python_pars[list_star_index] = const_tuple_empty;
        Py_INCREF(const_tuple_empty);
    }
}

static void makeStarListTupleCopyMethod(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                        PyObject *const *args, Py_ssize_t args_size) {
    assert(function->m_args_star_list_index != -1);
    Py_ssize_t list_star_index = function->m_args_star_list_index;

    // Copy left-over argument values to the star list parameter given.
    if (args_size + 1 > function->m_args_positional_count) {
        python_pars[list_star_index] = PyTuple_New(args_size + 1 - function->m_args_positional_count);

        for (Py_ssize_t i = 0; i < args_size + 1 - function->m_args_positional_count; i++) {
            PyObject *value = args[function->m_args_positional_count + i - 1];

            PyTuple_SET_ITEM(python_pars[list_star_index], i, value);
            Py_INCREF(value);
        }
    } else {
        python_pars[list_star_index] = const_tuple_empty;
        Py_INCREF(const_tuple_empty);
    }
}

static bool _handleArgumentsPlainOnly(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                      PyObject *const *args, Py_ssize_t args_size) {
    Py_ssize_t arg_count = function->m_args_positional_count;

    // Check if too many arguments were given in case of non list star arg.
    // For Python3.3 it's done only later, when more knowledge has
    // been gained. TODO: Could be done this way for improved mode
    // on all versions.
#if PYTHON_VERSION < 0x300
    if (function->m_args_star_list_index == -1) {
        if (unlikely(args_size > arg_count)) {
#if PYTHON_VERSION < 0x270
            formatErrorTooManyArguments(function, args_size, 0);
#else
            formatErrorTooManyArguments(function, args_size);
#endif
            return false;
        }
    }
#endif

#if PYTHON_VERSION >= 0x300
    bool parameter_error = false;
#endif

    Py_ssize_t defaults_given = function->m_defaults_given;

    if (args_size + defaults_given < arg_count) {
#if PYTHON_VERSION < 0x270
        formatErrorTooFewArguments(function, 0, args_size);
        return false;
#elif PYTHON_VERSION < 0x300
        formatErrorTooFewArguments(function, args_size);
        return false;
#else
        parameter_error = true;
#endif
    }

    for (Py_ssize_t i = 0; i < args_size; i++) {
        if (i >= arg_count)
            break;

        assert(python_pars[i] == NULL);

        python_pars[i] = args[i];
        Py_INCREF(python_pars[i]);
    }

#if PYTHON_VERSION >= 0x300
    if (parameter_error == false) {
#endif
        PyObject *source = function->m_defaults;

        for (Py_ssize_t i = args_size; i < arg_count; i++) {
            assert(python_pars[i] == NULL);
            assert(i + defaults_given >= arg_count);

            python_pars[i] = PyTuple_GET_ITEM(source, defaults_given + i - arg_count);
            Py_INCREF(python_pars[i]);
        }
#if PYTHON_VERSION >= 0x300
    }
#endif

#if PYTHON_VERSION >= 0x300
    if (unlikely(parameter_error)) {
        formatErrorTooFewArguments(function, python_pars);
        return false;
    }

    if (function->m_args_star_list_index == -1) {
        // Check if too many arguments were given in case of non list star arg
        if (unlikely(args_size > arg_count)) {
            formatErrorTooManyArguments(function, args_size, 0);
            return false;
        }
    }
#endif

    if (function->m_args_star_list_index != -1) {
        makeStarListTupleCopy(function, python_pars, args, args_size);
    }

    return true;
}

static bool handleMethodArgumentsPlainOnly(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                           PyObject *object, PyObject **args, Py_ssize_t args_size) {
    Py_ssize_t arg_count = function->m_args_positional_count;

    // There may be no self, otherwise we can directly assign it.
    if (arg_count >= 1) {
        python_pars[0] = object;
        Py_INCREF(object);
    } else {
        // Without self, there can only be star list to get the object as its
        // first element. Or we complain about illegal arguments.
        if (function->m_args_star_list_index == 0) {
            python_pars[0] = PyTuple_New(args_size + 1);
            PyTuple_SET_ITEM(python_pars[0], 0, object);
            Py_INCREF(object);

            for (Py_ssize_t i = 0; i < args_size; i++) {
                PyTuple_SET_ITEM(python_pars[0], i + 1, args[i]);
                Py_INCREF(args[i]);
            }

            return true;
        }
    }

    // Check if too many arguments were given in case of non list star arg.
    // For Python3.3 it's done only later, when more knowledge has
    // been gained. TODO: Could be done this way for improved mode
    // on all versions.
#if PYTHON_VERSION < 0x300
    if (function->m_args_star_list_index == -1) {
        if (unlikely(args_size + 1 > arg_count)) {
#if PYTHON_VERSION < 0x270
            formatErrorTooManyArguments(function, args_size + 1, 0);
#else
            formatErrorTooManyArguments(function, args_size + 1);
#endif
            return false;
        }
    }
#endif

#if PYTHON_VERSION >= 0x300
    bool parameter_error = false;
#endif
    Py_ssize_t defaults_given = function->m_defaults_given;

    if (args_size + 1 + defaults_given < arg_count) {
#if PYTHON_VERSION < 0x270
        formatErrorTooFewArguments(function, 0, args_size + 1);
        return false;
#elif PYTHON_VERSION < 0x300
        formatErrorTooFewArguments(function, args_size + 1);
        return false;
#else
        parameter_error = true;
#endif
    }

    for (Py_ssize_t i = 0; i < args_size; i++) {
        if (i + 1 >= arg_count)
            break;

        assert(python_pars[i + 1] == NULL);

        python_pars[i + 1] = args[i];
        Py_INCREF(python_pars[i + 1]);
    }

#if PYTHON_VERSION >= 0x300
    if (parameter_error == false) {
#endif
        for (Py_ssize_t i = args_size + 1; i < arg_count; i++) {
            assert(python_pars[i] == NULL);
            assert(i + defaults_given >= arg_count);

            python_pars[i] = PyTuple_GET_ITEM(function->m_defaults, defaults_given + i - arg_count);
            Py_INCREF(python_pars[i]);
        }
#if PYTHON_VERSION >= 0x300
    }
#endif

#if PYTHON_VERSION >= 0x300
    if (unlikely(parameter_error)) {
        formatErrorTooFewArguments(function, python_pars);
        return false;
    }

    if (function->m_args_star_list_index == -1) {
        // Check if too many arguments were given in case of non list star arg
        if (unlikely(args_size + 1 > arg_count)) {
            formatErrorTooManyArguments(function, args_size + 1, 0);
            return false;
        }
    }
#endif

    if (function->m_args_star_list_index != -1) {
        makeStarListTupleCopyMethod(function, python_pars, args, args_size);
    }

    return true;
}

#if PYTHON_VERSION < 0x270
static bool _handleArgumentsPlain(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                  PyObject *const *args, Py_ssize_t args_size, Py_ssize_t kw_found, Py_ssize_t kw_size)
#elif PYTHON_VERSION < 0x300
static bool _handleArgumentsPlain(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                  PyObject *const *args, Py_ssize_t args_size, Py_ssize_t kw_found)
#else
static bool _handleArgumentsPlain(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                  PyObject *const *args, Py_ssize_t args_size, Py_ssize_t kw_found,
                                  Py_ssize_t kw_only_found)
#endif
{
    Py_ssize_t arg_count = function->m_args_positional_count;

    // Check if too many arguments were given in case of non list star arg.
    // For Python3.3 it's done only later, when more knowledge has
    // been gained. TODO: Could be done this way for improved mode
    // on all versions.
#if PYTHON_VERSION < 0x300
    if (function->m_args_star_list_index == -1) {
        if (unlikely(args_size > arg_count)) {
#if PYTHON_VERSION < 0x270
            formatErrorTooManyArguments(function, args_size, kw_size);
#else
            formatErrorTooManyArguments(function, args_size + kw_found);
#endif
            return false;
        }
    }
#endif

#if PYTHON_VERSION >= 0x300
    bool parameter_error = false;
#endif

    if (kw_found > 0) {
        Py_ssize_t i;
        for (i = 0; i < (args_size < arg_count ? args_size : arg_count); i++) {
            if (unlikely(python_pars[i] != NULL)) {
                formatErrorMultipleValuesGiven(function, i);
                return false;
            }

            python_pars[i] = args[i];
            Py_INCREF(python_pars[i]);
        }

        Py_ssize_t defaults_given = function->m_defaults_given;

        for (; i < arg_count; i++) {
            if (python_pars[i] == NULL) {

                if (i + defaults_given >= arg_count) {
                    python_pars[i] = PyTuple_GET_ITEM(function->m_defaults, defaults_given + i - arg_count);
                    Py_INCREF(python_pars[i]);
                } else {
#if PYTHON_VERSION < 0x270
                    formatErrorTooFewArguments(function, kw_size, args_size + kw_found);
                    return false;
#elif PYTHON_VERSION < 0x300
                    formatErrorTooFewArguments(function, args_size + kw_found);
                    return false;
#else
                    parameter_error = true;
#endif
                }
            }
        }
    } else {
        Py_ssize_t usable = (args_size < arg_count ? args_size : arg_count);
        Py_ssize_t defaults_given = function->m_defaults_given;

        if (defaults_given < arg_count - usable) {
#if PYTHON_VERSION < 0x270
            formatErrorTooFewArguments(function, kw_size, args_size + kw_found);
            return false;
#elif PYTHON_VERSION < 0x300
            formatErrorTooFewArguments(function, args_size + kw_found);
            return false;
#else
            parameter_error = true;
#endif
        }

        for (Py_ssize_t i = 0; i < usable; i++) {
            assert(python_pars[i] == NULL);

            python_pars[i] = args[i];
            Py_INCREF(python_pars[i]);
        }

#if PYTHON_VERSION >= 0x300
        if (parameter_error == false) {
#endif
            for (Py_ssize_t i = usable; i < arg_count; i++) {
                assert(python_pars[i] == NULL);
                assert(i + defaults_given >= arg_count);

                python_pars[i] = PyTuple_GET_ITEM(function->m_defaults, defaults_given + i - arg_count);
                Py_INCREF(python_pars[i]);
            }
#if PYTHON_VERSION >= 0x300
        }
#endif
    }

#if PYTHON_VERSION >= 0x300
    if (unlikely(parameter_error)) {
        formatErrorTooFewArguments(function, python_pars);
        return false;
    }

    if (function->m_args_star_list_index == -1) {
        // Check if too many arguments were given in case of non list star arg
        if (unlikely(args_size > arg_count)) {
            formatErrorTooManyArguments(function, args_size, kw_only_found);
            return false;
        }
    }
#endif

    if (function->m_args_star_list_index != -1) {
        makeStarListTupleCopy(function, python_pars, args, args_size);
    }

    return true;
}

// Release them all in case of an error.
static void releaseParameters(struct Nuitka_FunctionObject const *function, PyObject *const *python_pars) {
    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_XDECREF(python_pars[i]);
    }
}

bool parseArgumentsPos(struct Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject **args,
                       Py_ssize_t args_size) {
    bool result;

    Py_ssize_t arg_count = function->m_args_positional_count;

#if PYTHON_VERSION >= 0x300
    bool kw_only_error;
#endif

    if (unlikely(arg_count == 0 && function->m_args_simple && args_size != 0)) {
#if PYTHON_VERSION < 0x300
        formatErrorNoArgumentAllowed(function, args_size);
#else
        formatErrorNoArgumentAllowed(function, NULL, args_size);
#endif

        goto error_exit;
    }

    result = _handleArgumentsPlainOnly(function, python_pars, args, args_size);

    if (result == false) {
        goto error_exit;
    }

#if PYTHON_VERSION >= 0x300

    // For Python3.3 the keyword only errors are all reported at once.
    kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(function, &python_pars[function->m_args_positional_count]);

        goto error_exit;
    }

#endif

    if (function->m_args_star_dict_index != -1) {
        python_pars[function->m_args_star_dict_index] = PyDict_New();
    }

    return true;

error_exit:

    releaseParameters(function, python_pars);
    return false;
}

bool parseArgumentsMethodPos(struct Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *object,
                             PyObject **args, Py_ssize_t args_size) {
    bool result;

#if PYTHON_VERSION >= 0x300
    bool kw_only_error;
#endif

    result = handleMethodArgumentsPlainOnly(function, python_pars, object, args, args_size);

    if (result == false) {
        goto error_exit;
    }

#if PYTHON_VERSION >= 0x300

    // For Python3 the keyword only errors are all reported at once.
    kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(function, &python_pars[function->m_args_positional_count]);

        goto error_exit;
    }

#endif

    if (function->m_args_star_dict_index != -1) {
        python_pars[function->m_args_star_dict_index] = PyDict_New();
    }

    return true;

error_exit:

    releaseParameters(function, python_pars);
    return false;
}

static bool parseArgumentsFull(struct Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject **args,
                               Py_ssize_t args_size, PyObject *kw) {
    Py_ssize_t kw_size = kw ? DICT_SIZE(kw) : 0;
    Py_ssize_t kw_found;
    bool result;
#if PYTHON_VERSION >= 0x300
    Py_ssize_t kw_only_found;
    bool kw_only_error;
#endif

    Py_ssize_t arg_count = function->m_args_keywords_count;

    assert(kw == NULL || PyDict_CheckExact(kw));

    if (unlikely(arg_count == 0 && function->m_args_simple && args_size + kw_size > 0)) {
#if PYTHON_VERSION < 0x300
        formatErrorNoArgumentAllowed(function, args_size + kw_size);
#else
        formatErrorNoArgumentAllowed(function, kw_size > 0 ? kw : NULL, args_size);
#endif

        goto error_exit;
    }

#if PYTHON_VERSION >= 0x300
    kw_only_found = 0;
#endif
    if (function->m_args_star_dict_index != -1) {
#if PYTHON_VERSION < 0x300
        kw_found = handleKeywordArgsWithStarDict(function, python_pars, kw);
#else
        kw_found = handleKeywordArgsWithStarDict(function, python_pars, &kw_only_found, kw);
#endif
        if (kw_found == -1) {
            goto error_exit;
        }
    } else if (kw == NULL || DICT_SIZE(kw) == 0) {
        kw_found = 0;
    } else {
#if PYTHON_VERSION < 0x300
        kw_found = handleKeywordArgs(function, python_pars, kw);
#else
        kw_found = handleKeywordArgs(function, python_pars, &kw_only_found, kw);
#endif
        if (kw_found == -1) {
            goto error_exit;
        }
    }

#if PYTHON_VERSION < 0x270
    result = _handleArgumentsPlain(function, python_pars, args, args_size, kw_found, kw_size);
#elif PYTHON_VERSION < 0x300
    result = _handleArgumentsPlain(function, python_pars, args, args_size, kw_found);
#else
    result = _handleArgumentsPlain(function, python_pars, args, args_size, kw_found, kw_only_found);
#endif

    if (result == false) {
        goto error_exit;
    }

#if PYTHON_VERSION >= 0x300

    // For Python3.3 the keyword only errors are all reported at once.
    kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(function, &python_pars[function->m_args_positional_count]);

        goto error_exit;
    }

#endif

    return true;

error_exit:

    releaseParameters(function, python_pars);
    return false;
}

PyObject *Nuitka_CallFunctionPosArgsKwArgs(struct Nuitka_FunctionObject const *function, PyObject **args,
                                           Py_ssize_t args_size, PyObject *kw) {
#ifdef _MSC_VER
    PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
    PyObject *python_pars[function->m_args_overall_count];
#endif
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (!parseArgumentsFull(function, python_pars, args, args_size, kw))
        return NULL;
    return function->m_c_code(function, python_pars);
}

PyObject *Nuitka_CallMethodFunctionNoArgs(struct Nuitka_FunctionObject const *function, PyObject *object) {
#ifdef _MSC_VER
    PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
    PyObject *python_pars[function->m_args_overall_count];
#endif
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    bool result = handleMethodArgumentsPlainOnly(function, python_pars, object, NULL, 0);
    // For Python3.3 the keyword only errors are all reported at once.
#if PYTHON_VERSION >= 0x300
    bool kw_only_error;
#endif

    if (result == false) {
        goto error_exit;
    }

#if PYTHON_VERSION >= 0x300

    kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(function, &python_pars[function->m_args_positional_count]);

        goto error_exit;
    }

#endif

    if (function->m_args_star_dict_index != -1) {
        python_pars[function->m_args_star_dict_index] = PyDict_New();
    }

    return function->m_c_code(function, python_pars);

error_exit:

    releaseParameters(function, python_pars);
    return NULL;
}

PyObject *Nuitka_CallMethodFunctionPosArgs(struct Nuitka_FunctionObject const *function, PyObject *object,
                                           PyObject **args, Py_ssize_t args_size) {
#ifdef _MSC_VER
    PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
    PyObject *python_pars[function->m_args_overall_count];
#endif
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    bool result = handleMethodArgumentsPlainOnly(function, python_pars, object, args, args_size);
    // For Python3.3 the keyword only errors are all reported at once.
#if PYTHON_VERSION >= 0x300
    bool kw_only_error;
#endif

    if (result == false) {
        goto error_exit;
    }

#if PYTHON_VERSION >= 0x300
    kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(function, &python_pars[function->m_args_positional_count]);

        goto error_exit;
    }

#endif

    if (function->m_args_star_dict_index != -1) {
        python_pars[function->m_args_star_dict_index] = PyDict_New();
    }

    return function->m_c_code(function, python_pars);

error_exit:

    releaseParameters(function, python_pars);
    return NULL;
}

PyObject *Nuitka_CallMethodFunctionPosArgsKwArgs(struct Nuitka_FunctionObject const *function, PyObject *object,
                                                 PyObject **args, Py_ssize_t args_size, PyObject *kw) {
#ifdef _MSC_VER
    PyObject **new_args = (PyObject **)_alloca(sizeof(PyObject *) * (args_size + 1));
#else
    PyObject *new_args[args_size + 1];
#endif
    new_args[0] = object;
    memcpy(new_args + 1, args, args_size * sizeof(PyObject *));

    // TODO: Specialize implementation for massive gains.
    return Nuitka_CallFunctionPosArgsKwArgs(function, new_args, args_size + 1, kw);
}

#if PYTHON_VERSION >= 0x380

static Py_ssize_t handleVectorcallKeywordArgs(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                              Py_ssize_t *kw_only_found, PyObject *const *kw_names,
                                              PyObject *const *kw_values, Py_ssize_t kw_size) {
    Py_ssize_t keywords_count = function->m_args_keywords_count;

    Py_ssize_t keyword_after_index = function->m_args_positional_count;

    assert(function->m_args_star_dict_index == -1);

    Py_ssize_t kw_found = 0;

    for (Py_ssize_t ppos = 0; ppos < kw_size; ++ppos) {
        PyObject *key = kw_names[ppos];

        if (unlikely(!PyUnicode_Check(key))) {
            formatErrorKeywordsMustBeString(function);
            return -1;
        }

        NUITKA_MAY_BE_UNUSED bool found = false;

        Py_ssize_t kw_arg_start = function->m_args_pos_only_count;

        for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
            if (function->m_varnames[i] == key) {
                assert(python_pars[i] == NULL);
                python_pars[i] = kw_values[ppos];
                Py_INCREF(python_pars[i]);

                if (i >= keyword_after_index) {
                    *kw_only_found += 1;
                }

                found = true;
                break;
            }
        }

        if (found == false) {
            PyObject **varnames = function->m_varnames;

            for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
                if (RICH_COMPARE_EQ_CBOOL_OBJECT_OBJECT_NORECURSE(varnames[i], key)) {
                    assert(python_pars[i] == NULL);
                    python_pars[i] = kw_values[ppos];
                    Py_INCREF(python_pars[i]);

                    if (i >= keyword_after_index) {
                        *kw_only_found += 1;
                    }

                    found = true;
                    break;
                }
            }
        }

        if (unlikely(found == false)) {
            bool pos_only_error = false;

            for (Py_ssize_t i = 0; i < kw_arg_start; i++) {
                PyObject **varnames = function->m_varnames;

                if (RICH_COMPARE_EQ_CBOOL_OBJECT_OBJECT_NORECURSE(varnames[i], key)) {
                    pos_only_error = true;
                    break;
                }
            }

            if (pos_only_error == true) {
                PyErr_Format(PyExc_TypeError,
                             "%s() got some positional-only arguments passed as keyword arguments: '%s'",
                             Nuitka_String_AsString(function->m_name),
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");

            } else {

                PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'",
                             Nuitka_String_AsString(function->m_name),
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");
            }

            return -1;
        }

        kw_found += 1;
    }

    return kw_found;
}

static bool MAKE_STAR_DICT_DICTIONARY_COPY38(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                             PyObject *const *kw_names, PyObject *const *kw_values,
                                             Py_ssize_t kw_size) {
    Py_ssize_t star_dict_index = function->m_args_star_dict_index;
    assert(star_dict_index != -1);

    python_pars[star_dict_index] = _PyDict_NewPresized(kw_size);

    for (int i = 0; i < kw_size; i++) {
        PyObject *key = kw_names[i];

        if (unlikely(!PyUnicode_Check(key))) {
            formatErrorKeywordsMustBeString(function);
            return false;
        }

        int res = PyDict_SetItem(python_pars[star_dict_index], key, kw_values[i]);

        if (unlikely(res != 0)) {
            return false;
        }
    }

    return true;
}

static Py_ssize_t handleVectorcallKeywordArgsWithStarDict(struct Nuitka_FunctionObject const *function,
                                                          PyObject **python_pars, Py_ssize_t *kw_only_found,
                                                          PyObject *const *kw_names, PyObject *const *kw_values,
                                                          Py_ssize_t kw_size) {
    assert(function->m_args_star_dict_index != -1);

    if (unlikely(MAKE_STAR_DICT_DICTIONARY_COPY38(function, python_pars, kw_names, kw_values, kw_size) == false)) {
        return -1;
    }

    Py_ssize_t kw_found = 0;
    Py_ssize_t keywords_count = function->m_args_keywords_count;
    Py_ssize_t keyword_after_index = function->m_args_positional_count;

    Py_ssize_t dict_star_index = function->m_args_star_dict_index;

    PyObject **varnames = function->m_varnames;

    for (Py_ssize_t i = 0; i < keywords_count; i++) {
        PyObject *arg_name = varnames[i];

        PyObject *kw_arg_value = DICT_GET_ITEM1(python_pars[dict_star_index], arg_name);

        if (kw_arg_value != NULL) {
            assert(python_pars[i] == NULL);

            python_pars[i] = kw_arg_value;

            PyDict_DelItem(python_pars[dict_star_index], arg_name);

            kw_found += 1;

            if (i >= keyword_after_index) {
                *kw_only_found += 1;
            }
        }
    }

    return kw_found;
}

static bool parseArgumentsVectorcall(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                     PyObject *const *args, Py_ssize_t args_size, PyObject *const *kw_names,
                                     Py_ssize_t kw_size) {
    Py_ssize_t kw_found;
    bool result;
    Py_ssize_t kw_only_found;
    bool kw_only_error;

    Py_ssize_t arg_count = function->m_args_keywords_count;

    if (unlikely(arg_count == 0 && function->m_args_simple && args_size + kw_size > 0)) {
        char const *function_name = Nuitka_String_AsString(function->m_name);
        if (kw_size == 0) {
            PyErr_Format(PyExc_TypeError, "%s() takes 0 positional arguments but %zd was given", function_name,
                         args_size);
        } else {
            PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'", function_name,
                         Nuitka_String_AsString(kw_names[0]));
        }

        goto error_exit;
    }

    kw_only_found = 0;
    if (function->m_args_star_dict_index != -1) {
        kw_found = handleVectorcallKeywordArgsWithStarDict(function, python_pars, &kw_only_found, kw_names,
                                                           args + args_size, kw_size);
        if (kw_found == -1) {
            goto error_exit;
        }
    } else if (kw_size == 0) {
        kw_found = 0;
    } else {
        kw_found =
            handleVectorcallKeywordArgs(function, python_pars, &kw_only_found, kw_names, args + args_size, kw_size);

        if (kw_found == -1) {
            goto error_exit;
        }
    }

    result = _handleArgumentsPlain(function, python_pars, args, args_size, kw_found, kw_only_found);

    if (result == false) {
        goto error_exit;
    }

    // For Python3.3 the keyword only errors are all reported at once.
    kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(function, &python_pars[function->m_args_positional_count]);

        goto error_exit;
    }

    return true;

error_exit:

    releaseParameters(function, python_pars);
    return false;
}

static PyObject *Nuitka_CallFunctionVectorcall(struct Nuitka_FunctionObject const *function, PyObject *const *args,
                                               Py_ssize_t args_size, PyObject *const *kw_names, Py_ssize_t kw_size) {
#ifdef _MSC_VER
    PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
    PyObject *python_pars[function->m_args_overall_count];
#endif
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (!parseArgumentsVectorcall(function, python_pars, args, args_size, kw_names, kw_size))
        return NULL;
    return function->m_c_code(function, python_pars);
}

static PyObject *Nuitka_Function_tp_vectorcall(struct Nuitka_FunctionObject *function, PyObject *const *stack,
                                               size_t nargsf, PyObject *kwnames) {
    assert(kwnames == NULL || PyTuple_CheckExact(kwnames));
    Py_ssize_t nkwargs = (kwnames == NULL) ? 0 : PyTuple_GET_SIZE(kwnames);

    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    assert(nargs >= 0);
    assert((nargs == 0 && nkwargs == 0) || stack != NULL);

    return Nuitka_CallFunctionVectorcall(function, stack, nargs, kwnames ? &PyTuple_GET_ITEM(kwnames, 0) : NULL,
                                         nkwargs);
}
#endif

#include "CompiledMethodType.c"
