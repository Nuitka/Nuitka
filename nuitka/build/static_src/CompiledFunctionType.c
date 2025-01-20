//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Compiled function type.

// The backbone of the integration into CPython. Try to behave as well as normal
// functions and built-in functions, or even better.

#include "nuitka/prelude.h"

#include "nuitka/compiled_method.h"

#include "nuitka/freelists.h"

// Needed for offsetof
#include <stddef.h>
#include <structmember.h>

// spell-checker: ignore qualname,kwdefaults,getset,weakrefs,vectorcall,nargsf,m_varnames

#if _DEBUG_REFCOUNTS
int count_active_Nuitka_Function_Type;
int count_allocated_Nuitka_Function_Type;
int count_released_Nuitka_Function_Type;
#endif

// tp_descr_get slot, bind a function to an object.
static PyObject *Nuitka_Function_descr_get(PyObject *function, PyObject *object, PyObject *class_object) {
    assert(Nuitka_Function_Check(function));
    CHECK_OBJECT((PyObject *)function);
    assert(_PyObject_GC_IS_TRACKED(function));

#if PYTHON_VERSION >= 0x300
    if (object == NULL || object == Py_None) {
        Py_INCREF(function);
        return function;
    }
#endif

    return Nuitka_Method_New((struct Nuitka_FunctionObject *)function, object == Py_None ? NULL : object, class_object);
}

// tp_repr slot, decide how compiled function shall be output to "repr" built-in
static PyObject *Nuitka_Function_tp_repr(struct Nuitka_FunctionObject *function) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

#if PYTHON_VERSION < 0x300
    return Nuitka_String_FromFormat("<compiled_function %s at %p>", Nuitka_String_AsString(function->m_name), function);
#else
    return Nuitka_String_FromFormat("<compiled_function %U at %p>", function->m_qualname, function);
#endif
}

static long Nuitka_Function_tp_traverse(struct Nuitka_FunctionObject *function, visitproc visit, void *arg) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    // TODO: Identify the impact of not visiting other owned objects. It appears
    // to be mostly harmless, as these are strings.
    Py_VISIT(function->m_dict);

    for (Py_ssize_t i = 0; i < function->m_closure_given; i++) {
        Py_VISIT(function->m_closure[i]);
    }

    return 0;
}

static long Nuitka_Function_tp_hash(struct Nuitka_FunctionObject *function) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    return function->m_counter;
}

static PyObject *Nuitka_Function_get_name(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = function->m_name;
    CHECK_OBJECT(result);

    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_name(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));
    CHECK_OBJECT_X(value);

#if PYTHON_VERSION < 0x300
    if (unlikely(value == NULL || PyString_Check(value) == 0))
#else
    if (unlikely(value == NULL || PyUnicode_Check(value) == 0))
#endif
    {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__name__ must be set to a string object");
        return -1;
    }

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *old = function->m_name;
    CHECK_OBJECT(old);

    Py_INCREF(value);
    function->m_name = value;
    Py_DECREF(old);

    return 0;
}

#if PYTHON_VERSION >= 0x300
static PyObject *Nuitka_Function_get_qualname(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = function->m_qualname;
    CHECK_OBJECT(result);

    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_qualname(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));
    CHECK_OBJECT_X(value);

    if (unlikely(value == NULL || PyUnicode_Check(value) == 0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__qualname__ must be set to a string object");
        return -1;
    }

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *old = function->m_qualname;
    Py_INCREF(value);
    function->m_qualname = value;
    Py_DECREF(old);

    return 0;
}
#endif

static PyObject *Nuitka_Function_get_doc(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = function->m_doc;

    if (result == NULL) {
        result = Py_None;
    }

    CHECK_OBJECT(result);

    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_doc(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));
    CHECK_OBJECT_X(value);

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *old = function->m_doc;

    function->m_doc = value;
    Py_XINCREF(value);

    Py_XDECREF(old);

    return 0;
}

static PyObject *Nuitka_Function_get_dict(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    if (function->m_dict == NULL) {
        NUITKA_MAY_BE_UNUSED PyThreadState *tstate = PyThreadState_GET();

        function->m_dict = MAKE_DICT_EMPTY(tstate);
    }

    CHECK_OBJECT(function->m_dict);

    Py_INCREF(function->m_dict);
    return function->m_dict;
}

static int Nuitka_Function_set_dict(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));
    CHECK_OBJECT_X(value);

    if (unlikely(value == NULL)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "function's dictionary may not be deleted");
        return -1;
    }

    if (likely(PyDict_Check(value))) {
        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
        PyObject *old = function->m_dict;
        CHECK_OBJECT_X(old);

        Py_INCREF(value);
        function->m_dict = value;
        Py_XDECREF(old);

        return 0;
    } else {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "setting function's dictionary to a non-dict");
        return -1;
    }
}

static PyObject *Nuitka_Function_get_code(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = (PyObject *)function->m_code_object;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_code(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "__code__ is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Function_get_compiled(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyObject *result = Nuitka_dunder_compiled_value;
    CHECK_OBJECT(result);

    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_compiled(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "__compiled__ is not writable");
    return -1;
}

static PyObject *Nuitka_Function_get_compiled_constant(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = function->m_constant_return_value;

    if (result == NULL) {
        PyThreadState *tstate = PyThreadState_GET();
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_AttributeError, "non-constant return value");

        return NULL;
    }
    CHECK_OBJECT(result);

    Py_INCREF_IMMORTAL(result);
    return result;
}

static int Nuitka_Function_set_compiled_constant(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "__compiled_constant__ is not writable");
    return -1;
}

static PyObject *Nuitka_Function_get_closure(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    if (function->m_closure_given > 0) {
        NUITKA_MAY_BE_UNUSED PyThreadState *tstate = PyThreadState_GET();
        return MAKE_TUPLE(tstate, (PyObject *const *)function->m_closure, function->m_closure_given);
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

static int Nuitka_Function_set_closure(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate,
#if PYTHON_VERSION < 0x300
                                    PyExc_TypeError,
#else
                                    PyExc_AttributeError,
#endif
                                    "readonly attribute");

    return -1;
}

static PyObject *Nuitka_Function_get_defaults(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = (PyObject *)function->m_defaults;
    CHECK_OBJECT(result);

    Py_INCREF(result);
    return result;
}

static void _onUpdatedCompiledFunctionDefaultsValue(struct Nuitka_FunctionObject *function) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));

    if (function->m_defaults == Py_None) {
        function->m_defaults_given = 0;
    } else {
        function->m_defaults_given = PyTuple_GET_SIZE(function->m_defaults);
    }
}

static int Nuitka_Function_set_defaults(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));
    CHECK_OBJECT_X(value);

    if (value == NULL) {
        value = Py_None;
    }

    if (unlikely(value != Py_None && PyTuple_Check(value) == false)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__defaults__ must be set to a tuple object");
        return -1;
    }

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *old = function->m_defaults;
    CHECK_OBJECT(old);

    Py_INCREF(value);
    function->m_defaults = value;
    Py_DECREF(old);

    _onUpdatedCompiledFunctionDefaultsValue(function);

    return 0;
}

#if PYTHON_VERSION >= 0x300
static PyObject *Nuitka_Function_get_kwdefaults(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = function->m_kwdefaults;
    CHECK_OBJECT_X(result);

    if (result == NULL) {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Function_set_kwdefaults(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));
    CHECK_OBJECT_X(value);

    if (value == NULL) {
        value = Py_None;
    }

    if (unlikely(value != Py_None && PyDict_Check(value) == false)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__kwdefaults__ must be set to a dict object");
        return -1;
    }

    if (value == Py_None) {
        value = NULL;
    }

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *old = function->m_kwdefaults;
    CHECK_OBJECT_X(old);

    Py_XINCREF(value);
    function->m_kwdefaults = value;
    Py_XDECREF(old);

    return 0;
}

static PyObject *Nuitka_Function_get_annotations(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    if (function->m_annotations == NULL) {
        NUITKA_MAY_BE_UNUSED PyThreadState *tstate = PyThreadState_GET();

        function->m_annotations = MAKE_DICT_EMPTY(tstate);
    }
    CHECK_OBJECT(function->m_annotations);

    Py_INCREF(function->m_annotations);
    return function->m_annotations;
}

static int Nuitka_Function_set_annotations(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    if (unlikely(value != NULL && PyDict_Check(value) == false)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__annotations__ must be set to a dict object");
        return -1;
    }

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *old = function->m_annotations;
    CHECK_OBJECT_X(old);

    Py_XINCREF(value);
    function->m_annotations = value;
    Py_XDECREF(old);

    return 0;
}

#endif

static int Nuitka_Function_set_globals(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_Function_get_globals(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    PyObject *result = PyModule_GetDict(function->m_module);
    CHECK_OBJECT(result);

    Py_INCREF(result);
    return result;
}

#if PYTHON_VERSION >= 0x3a0
static int Nuitka_Function_set_builtins(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "readonly attribute");
    return -1;
}

static PyObject *Nuitka_Function_get_builtins(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();
    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    return LOOKUP_SUBSCRIPT(tstate, PyModule_GetDict(function->m_module), const_str_plain___builtins__);
}
#endif

#if PYTHON_VERSION >= 0x3c0
static int Nuitka_Function_set_type_params(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    CHECK_OBJECT_X(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    if (unlikely(value == NULL || !PyTuple_Check(value))) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__type_params__ must be set to a tuple");
        return -1;
    }

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    Py_SETREF(function->m_type_params, Py_NewRef(value));
    return 0;
}

static PyObject *Nuitka_Function_get_type_params(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    // TODO: Probably not needed anymore?
    Py_INCREF(const_tuple_empty);
    return const_tuple_empty;
}
#endif

static int Nuitka_Function_set_module(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));
    CHECK_OBJECT_X(value);

    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    if (function->m_dict == NULL) {
        NUITKA_MAY_BE_UNUSED PyThreadState *tstate = PyThreadState_GET();

        function->m_dict = MAKE_DICT_EMPTY(tstate);
    }

    if (value == NULL) {
        value = Py_None;
    }

    return DICT_SET_ITEM(function->m_dict, const_str_plain___module__, value) ? 0 : -1;
}

static PyObject *Nuitka_Function_get_module(PyObject *self, void *data) {
    CHECK_OBJECT(self);
    assert(Nuitka_Function_Check(self));
    assert(_PyObject_GC_IS_TRACKED(self));

    PyObject *result;

    PyThreadState *tstate = PyThreadState_GET();

    // The __dict__ might overrule this.
    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)self;
    if (function->m_dict) {
        result = DICT_GET_ITEM1(tstate, function->m_dict, const_str_plain___module__);

        if (result != NULL) {
            return result;
        }
    }

    result = MODULE_NAME1(tstate, function->m_module);
    return result;
}

static PyGetSetDef Nuitka_Function_getset[] = {
#if PYTHON_VERSION >= 0x300
    {(char *)"__qualname__", Nuitka_Function_get_qualname, Nuitka_Function_set_qualname, NULL},
#endif
#if PYTHON_VERSION < 0x300
    {(char *)"func_name", Nuitka_Function_get_name, Nuitka_Function_set_name, NULL},
#endif
    {(char *)"__name__", Nuitka_Function_get_name, Nuitka_Function_set_name, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_doc", Nuitka_Function_get_doc, Nuitka_Function_set_doc, NULL},
#endif
    {(char *)"__doc__", Nuitka_Function_get_doc, Nuitka_Function_set_doc, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_dict", Nuitka_Function_get_dict, Nuitka_Function_set_dict, NULL},
#endif
    {(char *)"__dict__", Nuitka_Function_get_dict, Nuitka_Function_set_dict, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_code", Nuitka_Function_get_code, Nuitka_Function_set_code, NULL},
#endif
    {(char *)"__code__", Nuitka_Function_get_code, Nuitka_Function_set_code, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_defaults", Nuitka_Function_get_defaults, Nuitka_Function_set_defaults, NULL},
#endif
    {(char *)"__defaults__", Nuitka_Function_get_defaults, Nuitka_Function_set_defaults, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_globals", Nuitka_Function_get_globals, Nuitka_Function_set_globals, NULL},
#endif
    {(char *)"__closure__", Nuitka_Function_get_closure, Nuitka_Function_set_closure, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"func_closure", Nuitka_Function_get_closure, Nuitka_Function_set_closure, NULL},
#endif
    {(char *)"__globals__", Nuitka_Function_get_globals, Nuitka_Function_set_globals, NULL},
    {(char *)"__module__", Nuitka_Function_get_module, Nuitka_Function_set_module, NULL},
#if PYTHON_VERSION >= 0x300
    {(char *)"__kwdefaults__", Nuitka_Function_get_kwdefaults, Nuitka_Function_set_kwdefaults, NULL},
    {(char *)"__annotations__", Nuitka_Function_get_annotations, Nuitka_Function_set_annotations, NULL},
#endif
#if PYTHON_VERSION >= 0x3a0
    {(char *)"__builtins__", Nuitka_Function_get_builtins, Nuitka_Function_set_builtins, NULL},
#endif
#if PYTHON_VERSION >= 0x3c0
    {(char *)"__type_params__", Nuitka_Function_get_type_params, Nuitka_Function_set_type_params, NULL},
#endif
    {(char *)"__compiled__", Nuitka_Function_get_compiled, Nuitka_Function_set_compiled, NULL},
    {(char *)"__compiled_constant__", Nuitka_Function_get_compiled_constant, Nuitka_Function_set_compiled_constant,
     NULL},
    {NULL}};

static PyObject *Nuitka_Function_reduce(struct Nuitka_FunctionObject *function, PyObject *unused) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    PyObject *result;

#if PYTHON_VERSION < 0x300
    result = function->m_name;
#else
    result = function->m_qualname;
#endif

    Py_INCREF(result);
    return result;
}

static PyObject *Nuitka_Function_clone(struct Nuitka_FunctionObject *function, PyObject *unused) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    for (Py_ssize_t i = 0; i < function->m_closure_given; i++) {
        assert(function->m_closure[i]);
        Py_INCREF(function->m_closure[i]);
    }

    Py_INCREF(function->m_defaults);

#if PYTHON_VERSION >= 0x300
#if 0
    PRINT_STRING("Nuitka_Function_clone:");
    PRINT_ITEM((PyObject *)function);
    PRINT_NEW_LINE();
#endif

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *annotations = function->m_annotations;
    if (annotations != NULL) {
        if (DICT_SIZE(annotations) != 0) {
            annotations = DICT_COPY(tstate, annotations);
        } else {
            annotations = NULL;
        }
    }

    PyObject *kwdefaults = function->m_kwdefaults;
    if (kwdefaults != NULL) {
        if (DICT_SIZE(kwdefaults) != 0) {
            kwdefaults = DICT_COPY(tstate, kwdefaults);
        } else {
            kwdefaults = NULL;
        }
    }
#endif

    struct Nuitka_FunctionObject *result =
        Nuitka_Function_New(function->m_c_code, function->m_name,
#if PYTHON_VERSION >= 0x300
                            function->m_qualname,
#endif
                            function->m_code_object, function->m_defaults,
#if PYTHON_VERSION >= 0x300
                            kwdefaults, annotations,
#endif
                            function->m_module, function->m_doc, function->m_closure, function->m_closure_given);

    return (PyObject *)result;
}

// Freelist setup
#define MAX_FUNCTION_FREE_LIST_COUNT 100
static struct Nuitka_FunctionObject *free_list_functions = NULL;
static int free_list_functions_count = 0;

static void Nuitka_Function_tp_dealloc(struct Nuitka_FunctionObject *function) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Function_Type -= 1;
    count_released_Nuitka_Function_Type += 1;
#endif

    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

#ifndef __NUITKA_NO_ASSERT__
    PyThreadState *tstate = PyThreadState_GET();

    // Save the current exception, if any, we must to not corrupt it.
    struct Nuitka_ExceptionPreservationItem saved_exception_state1;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state1);
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state1);
#endif
    assert(_PyObject_GC_IS_TRACKED(function));
    Nuitka_GC_UnTrack(function);

    if (function->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)function);
    }

    Py_DECREF(function->m_name);
#if PYTHON_VERSION >= 0x300
    Py_DECREF(function->m_qualname);
#endif

#if PYTHON_VERSION >= 0x3c0
    Py_DECREF(function->m_type_params);
#endif

    // These may actually resurrect the object, not?
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

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_functions, function, MAX_FUNCTION_FREE_LIST_COUNT);

#ifndef __NUITKA_NO_ASSERT__
    struct Nuitka_ExceptionPreservationItem saved_exception_state2;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state2);
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state2);

    ASSERT_SAME_EXCEPTION_STATE(&saved_exception_state1, &saved_exception_state2);
#endif
}

static PyMethodDef Nuitka_Function_methods[] = {{"__reduce__", (PyCFunction)Nuitka_Function_reduce, METH_NOARGS, NULL},
                                                {"clone", (PyCFunction)Nuitka_Function_clone, METH_NOARGS, NULL},
                                                {NULL}};

static PyObject *Nuitka_Function_tp_call(struct Nuitka_FunctionObject *function, PyObject *tuple_args, PyObject *kw);

PyTypeObject Nuitka_Function_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_function", // tp_name
    sizeof(struct Nuitka_FunctionObject),               // tp_basicsize
    sizeof(struct Nuitka_CellObject *),                 // tp_itemsize
    (destructor)Nuitka_Function_tp_dealloc,             // tp_dealloc
#if PYTHON_VERSION < 0x380 || defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_SLOT)
    0, // tp_print
#else
    offsetof(struct Nuitka_FunctionObject, m_vectorcall), // tp_vectorcall_offset
#endif
    0,                                    // tp_getattr
    0,                                    // tp_setattr
    0,                                    // tp_compare
    (reprfunc)Nuitka_Function_tp_repr,    // tp_repr
    0,                                    // tp_as_number
    0,                                    // tp_as_sequence
    0,                                    // tp_as_mapping
    (hashfunc)Nuitka_Function_tp_hash,    // tp_hash
    (ternaryfunc)Nuitka_Function_tp_call, // tp_call
    0,                                    // tp_str
    0,                                    // tp_getattro (PyObject_GenericGetAttr)
    0,                                    // tp_setattro
    0,                                    // tp_as_buffer
    Py_TPFLAGS_DEFAULT |
#if PYTHON_VERSION < 0x300
        Py_TPFLAGS_HAVE_WEAKREFS |
#endif
#if PYTHON_VERSION >= 0x380
        _Py_TPFLAGS_HAVE_VECTORCALL | Py_TPFLAGS_METHOD_DESCRIPTOR |
#endif
        Py_TPFLAGS_HAVE_GC,                             // tp_flags
    0,                                                  // tp_doc
    (traverseproc)Nuitka_Function_tp_traverse,          // tp_traverse
    0,                                                  // tp_clear
    0,                                                  // tp_richcompare
    offsetof(struct Nuitka_FunctionObject, m_weakrefs), // tp_weaklistoffset
    0,                                                  // tp_iter
    0,                                                  // tp_iternext
    Nuitka_Function_methods,                            // tp_methods
    0,                                                  // tp_members
    Nuitka_Function_getset,                             // tp_getset
    0,                                                  // tp_base
    0,                                                  // tp_dict
    Nuitka_Function_descr_get,                          // tp_descr_get
    0,                                                  // tp_descr_set
    offsetof(struct Nuitka_FunctionObject, m_dict),     // tp_dictoffset
    0,                                                  // tp_init
    0,                                                  // tp_alloc
    0,                                                  // tp_new
    0,                                                  // tp_free
    0,                                                  // tp_is_gc
    0,                                                  // tp_bases
    0,                                                  // tp_mro
    0,                                                  // tp_cache
    0,                                                  // tp_subclasses
    0,                                                  // tp_weaklist
    0,                                                  // tp_del
    0                                                   // tp_version_tag
#if PYTHON_VERSION >= 0x300
    ,
    0 // tp_finalizer
#endif
};

void _initCompiledFunctionType(void) {
    Nuitka_PyType_Ready(&Nuitka_Function_Type, &PyFunction_Type, true, false, false, false, false);

    // Be a paranoid subtype of uncompiled function, we want nothing shared.
    assert(Nuitka_Function_Type.tp_doc != PyFunction_Type.tp_doc);
    assert(Nuitka_Function_Type.tp_traverse != PyFunction_Type.tp_traverse);
    assert(Nuitka_Function_Type.tp_clear != PyFunction_Type.tp_clear || PyFunction_Type.tp_clear == NULL);
    assert(Nuitka_Function_Type.tp_richcompare != PyFunction_Type.tp_richcompare ||
           PyFunction_Type.tp_richcompare == NULL);
    assert(Nuitka_Function_Type.tp_weaklistoffset != PyFunction_Type.tp_weaklistoffset);
    assert(Nuitka_Function_Type.tp_iter != PyFunction_Type.tp_iter || PyFunction_Type.tp_iter == NULL);
    assert(Nuitka_Function_Type.tp_iternext != PyFunction_Type.tp_iternext || PyFunction_Type.tp_iternext == NULL);
    assert(Nuitka_Function_Type.tp_methods != PyFunction_Type.tp_methods);
    assert(Nuitka_Function_Type.tp_members != PyFunction_Type.tp_members);
    assert(Nuitka_Function_Type.tp_getset != PyFunction_Type.tp_getset);
    assert(Nuitka_Function_Type.tp_dict != PyFunction_Type.tp_dict);
    assert(Nuitka_Function_Type.tp_descr_get != PyFunction_Type.tp_descr_get);

    assert(Nuitka_Function_Type.tp_descr_set != PyFunction_Type.tp_descr_set || PyFunction_Type.tp_descr_set == NULL);
    assert(Nuitka_Function_Type.tp_dictoffset != PyFunction_Type.tp_dictoffset);
    // TODO: These get changed and into the same thing, not sure what to compare against, project something
    // assert(Nuitka_Function_Type.tp_init != PyFunction_Type.tp_init || PyFunction_Type.tp_init == NULL);
    // assert(Nuitka_Function_Type.tp_alloc != PyFunction_Type.tp_alloc || PyFunction_Type.tp_alloc == NULL);
    // assert(Nuitka_Function_Type.tp_new != PyFunction_Type.tp_new || PyFunction_Type.tp_new == NULL);
    // assert(Nuitka_Function_Type.tp_free != PyFunction_Type.tp_free || PyFunction_Type.tp_free == NULL);
    assert(Nuitka_Function_Type.tp_bases != PyFunction_Type.tp_bases);
    assert(Nuitka_Function_Type.tp_mro != PyFunction_Type.tp_mro);
    assert(Nuitka_Function_Type.tp_cache != PyFunction_Type.tp_cache || PyFunction_Type.tp_cache == NULL);
    assert(Nuitka_Function_Type.tp_subclasses != PyFunction_Type.tp_subclasses || PyFunction_Type.tp_cache == NULL);
    assert(Nuitka_Function_Type.tp_weaklist != PyFunction_Type.tp_weaklist);
    assert(Nuitka_Function_Type.tp_del != PyFunction_Type.tp_del || PyFunction_Type.tp_del == NULL);
#if PYTHON_VERSION >= 0x300
    assert(Nuitka_Function_Type.tp_finalize != PyFunction_Type.tp_finalize || PyFunction_Type.tp_finalize == NULL);
#endif

    // Make sure we don't miss out on attributes we are not having or should not have.
#ifndef __NUITKA_NO_ASSERT__
    for (struct PyGetSetDef *own = &Nuitka_Function_getset[0]; own->name != NULL; own++) {
        bool found = false;

        for (struct PyGetSetDef *related = PyFunction_Type.tp_getset; related->name != NULL; related++) {
            if (strcmp(related->name, own->name) == 0) {
                found = true;
            }
        }

        if (found == false) {
            if (strcmp(own->name, "__doc__") == 0) {
                // We do that one differently right now.
                continue;
            }
#if PYTHON_VERSION < 0x300
            if (strcmp(own->name, "func_doc") == 0) {
                // We do that one differently right now.
                continue;
            }
#endif

            if (strcmp(own->name, "__globals__") == 0) {
                // We do that one differently right now.
                continue;
            }

#if PYTHON_VERSION < 0x300
            if (strcmp(own->name, "func_globals") == 0) {
                // We do that one differently right now.
                continue;
            }
#endif

#if PYTHON_VERSION >= 0x3a0
            if (strcmp(own->name, "__builtins__") == 0) {
                // We do that one differently right now.
                continue;
            }
#endif

            if (strcmp(own->name, "__module__") == 0) {
                // We do that one differently right now.
                continue;
            }

            if (strcmp(own->name, "__closure__") == 0) {
                // We have to do that differently, because we do not keep this around until
                // needed, and we make it read-only
                continue;
            }

#if PYTHON_VERSION < 0x300
            if (strcmp(own->name, "func_closure") == 0) {
                // We have to do that differently, because we do not keep this around until
                // needed, and we make it read-only
                continue;
            }
#endif

            if (strcmp(own->name, "__compiled__") == 0 || strcmp(own->name, "__compiled_constant__") == 0) {
                // We have to do that differently, because we do not keep this around until
                // needed, and we make it read-only
                continue;
            }

            PRINT_FORMAT("Not found in uncompiled type: %s\n", own->name);
            NUITKA_CANNOT_GET_HERE("Type problem");
        }
    }

    for (struct PyGetSetDef *related = PyFunction_Type.tp_getset; related->name != NULL; related++) {
        bool found = false;

        for (struct PyGetSetDef *own = &Nuitka_Function_getset[0]; own->name != NULL; own++) {
            if (strcmp(related->name, own->name) == 0) {
                found = true;
            }
        }

        if (found == false) {
            PRINT_FORMAT("Not found in compiled type: %s\n", related->name);
            NUITKA_CANNOT_GET_HERE("Type problem");
        }
    }

    for (struct PyMemberDef *related = PyFunction_Type.tp_members; related->name != NULL; related++) {
        bool found = false;

        for (struct PyGetSetDef *own = &Nuitka_Function_getset[0]; own->name != NULL; own++) {
            if (strcmp(related->name, own->name) == 0) {
                found = true;
            }
        }

        if (found == false) {
            PRINT_FORMAT("Not found in compiled type: %s\n", related->name);
            NUITKA_CANNOT_GET_HERE("Type problem");
        }
    }
#endif
}

// Shared implementations for empty functions. When a function body is empty, but
// still needs to exist, e.g. overloaded functions, this is saving the effort to
// produce one.
static PyObject *_Nuitka_FunctionEmptyCodeNoneImpl(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                                   PyObject **python_pars) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = Py_None;

    Py_INCREF(result);
    return result;
}

static PyObject *_Nuitka_FunctionEmptyCodeTrueImpl(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                                   PyObject **python_pars) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = Py_True;

    Py_INCREF_IMMORTAL(result);
    return result;
}

static PyObject *_Nuitka_FunctionEmptyCodeFalseImpl(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                                    PyObject **python_pars) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = Py_False;
    Py_INCREF_IMMORTAL(result);
    return result;
}

static PyObject *_Nuitka_FunctionEmptyCodeGenericImpl(PyThreadState *tstate,
                                                      struct Nuitka_FunctionObject const *function,
                                                      PyObject **python_pars) {
    CHECK_OBJECT((PyObject *)function);
    assert(Nuitka_Function_Check((PyObject *)function));
    assert(_PyObject_GC_IS_TRACKED(function));

    Py_ssize_t arg_count = function->m_args_overall_count;

    for (Py_ssize_t i = 0; i < arg_count; i++) {
        Py_DECREF(python_pars[i]);
    }

    PyObject *result = function->m_constant_return_value;

    Py_INCREF_IMMORTAL(result);
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

#ifdef _NUITKA_PLUGIN_DILL_ENABLED
int Nuitka_Function_GetFunctionCodeIndex(struct Nuitka_FunctionObject *function,
                                         function_impl_code const *function_table) {

    if (function->m_c_code == _Nuitka_FunctionEmptyCodeTrueImpl) {
        return -2;
    }

    if (function->m_c_code == _Nuitka_FunctionEmptyCodeFalseImpl) {
        return -3;
    }

    if (function->m_c_code == _Nuitka_FunctionEmptyCodeNoneImpl) {
        return -4;
    }

    if (function->m_c_code == _Nuitka_FunctionEmptyCodeGenericImpl) {
        return -5;
    }

    function_impl_code const *current = function_table;
    int offset = 0;

    while (*current != NULL) {
        if (*current == function->m_c_code) {
            break;
        }

        current += 1;
        offset += 1;
    }

    if (*current == NULL) {
        PyThreadState *tstate = PyThreadState_GET();
#if 0
        PRINT_STRING("Looking for:");
        PRINT_ITEM((PyObject *)function);
        PRINT_NEW_LINE();
#endif
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "Cannot find compiled function in module.");
        return -1;
    }

    return offset;
}

struct Nuitka_FunctionObject *
Nuitka_Function_CreateFunctionViaCodeIndex(PyObject *module, PyObject *function_qualname, PyObject *function_index,
                                           PyObject *code_object_desc, PyObject *constant_return_value,
                                           PyObject *defaults, PyObject *kw_defaults, PyObject *doc, PyObject *closure,
                                           function_impl_code const *function_table, int function_table_size) {
    int offset = PyLong_AsLong(function_index);

    if (offset > function_table_size || offset < -5 || offset == -1) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "Wrong offset for compiled function.");
        return NULL;
    }

    PyObject *filename = PyTuple_GET_ITEM(code_object_desc, 0);
    PyObject *function_name = PyTuple_GET_ITEM(code_object_desc, 1);
    PyObject *line = PyTuple_GET_ITEM(code_object_desc, 2);
    int line_int = PyLong_AsLong(line);
    assert(line_int != -1);

    PyObject *arg_names = PyTuple_GET_ITEM(code_object_desc, 3);
    PyObject *arg_count = PyTuple_GET_ITEM(code_object_desc, 4);
    int arg_count_int = PyLong_AsLong(arg_count);
    assert(arg_count_int != -1);

    PyObject *flags = PyTuple_GET_ITEM(code_object_desc, 5);
    int flags_int = PyLong_AsLong(flags);
    assert(flags_int != -1);

    PyObject *kw_only_count = PyTuple_GET_ITEM(code_object_desc, 6);
    int kw_only_count_int = PyLong_AsLong(kw_only_count);
    assert(kw_only_count_int != -1);

    PyObject *pos_only_count = PyTuple_GET_ITEM(code_object_desc, 7);
    int pos_only_count_int = PyLong_AsLong(pos_only_count);
    assert(pos_only_count_int != -1);

    PyCodeObject *code_object =
        MAKE_CODE_OBJECT(filename, line_int, flags_int, function_name, function_qualname, arg_names,
                         NULL, // free_vars
                         arg_count_int, kw_only_count_int, pos_only_count_int);
    if (unlikely(code_object == NULL)) {
        return NULL;
    }

    Py_ssize_t closure_size;

    if (closure != Py_None) {
        closure_size = PyTuple_GET_SIZE(closure);
    } else {
        closure_size = 0;
    }

    NUITKA_DYNAMIC_ARRAY_DECL(closure_cells, struct Nuitka_CellObject *, closure_size);

    for (Py_ssize_t i = 0; i < closure_size; i++) {
        closure_cells[i] = Nuitka_Cell_New0(PyTuple_GET_ITEM(closure, i));
    }

    struct Nuitka_FunctionObject *result =
        Nuitka_Function_New(offset >= 0 ? function_table[offset] : NULL, code_object->co_name,
#if PYTHON_VERSION >= 0x300
                            NULL, // TODO: Not transferring qualname yet
#endif
                            code_object, defaults,
#if PYTHON_VERSION >= 0x300
                            kw_defaults,
                            NULL, // TODO: Not transferring annotations
#endif
                            module, doc, closure_cells, closure_size);

    CHECK_OBJECT(result);

    if (offset == -2) {
        Nuitka_Function_EnableConstReturnTrue(result);
    }
    if (offset == -3) {
        Nuitka_Function_EnableConstReturnFalse(result);
    }
    if (offset == -4) {
        result->m_c_code = _Nuitka_FunctionEmptyCodeNoneImpl;
    }
    if (offset == -5) {
        CHECK_OBJECT(constant_return_value);

        Nuitka_Function_EnableConstReturnGeneric(result, constant_return_value);

        Py_INCREF_IMMORTAL(constant_return_value);
    }

    assert(result->m_c_code != NULL);

    return result;
}

PyObject *Nuitka_Function_ExtractCodeObjectDescription(PyThreadState *tstate, struct Nuitka_FunctionObject *function) {
    PyObject *code_object_desc = MAKE_TUPLE_EMPTY(tstate, 8);

    PyTuple_SET_ITEM0(code_object_desc, 0, function->m_code_object->co_filename);
    PyTuple_SET_ITEM0(code_object_desc, 1, function->m_code_object->co_name);
    PyTuple_SET_ITEM(code_object_desc, 2, Nuitka_PyLong_FromLong(function->m_code_object->co_firstlineno));
#if PYTHON_VERSION < 0x3b0
    PyTuple_SET_ITEM0(code_object_desc, 3, function->m_code_object->co_varnames);
#else
    // spell-checker: ignore PyCode_GetVarnames
    PyTuple_SET_ITEM(code_object_desc, 3, PyCode_GetVarnames(function->m_code_object));
#endif
    PyTuple_SET_ITEM(code_object_desc, 4, Nuitka_PyLong_FromLong(function->m_code_object->co_argcount));
    PyTuple_SET_ITEM(code_object_desc, 5, Nuitka_PyLong_FromLong(function->m_code_object->co_flags));

#if PYTHON_VERSION < 0x380
    PyTuple_SET_ITEM(code_object_desc, 6, const_int_0);
#else
    PyTuple_SET_ITEM(code_object_desc, 6, Nuitka_PyLong_FromLong(function->m_code_object->co_posonlyargcount));
#endif

#if PYTHON_VERSION < 0x3b0
    PyTuple_SET_ITEM(code_object_desc, 7, const_int_0);
#else
    PyTuple_SET_ITEM(code_object_desc, 7, Nuitka_PyLong_FromLong(function->m_code_object->co_kwonlyargcount));
#endif

    CHECK_OBJECT_DEEP(code_object_desc);

    return code_object_desc;
}
#endif

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_SLOT)
static PyObject *Nuitka_Function_tp_vectorcall(struct Nuitka_FunctionObject *function, PyObject *const *stack,
                                               size_t nargsf, PyObject *kw_names);
#endif

// Make a function with closure.
#if PYTHON_VERSION < 0x300
struct Nuitka_FunctionObject *Nuitka_Function_New(function_impl_code c_code, PyObject *name, PyCodeObject *code_object,
                                                  PyObject *defaults, PyObject *module, PyObject *doc,
                                                  struct Nuitka_CellObject **closure, Py_ssize_t closure_given)
#else
struct Nuitka_FunctionObject *Nuitka_Function_New(function_impl_code c_code, PyObject *name, PyObject *qualname,
                                                  PyCodeObject *code_object, PyObject *defaults, PyObject *kw_defaults,
                                                  PyObject *annotations, PyObject *module, PyObject *doc,
                                                  struct Nuitka_CellObject **closure, Py_ssize_t closure_given)
#endif
{
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Function_Type += 1;
    count_allocated_Nuitka_Function_Type += 1;
#endif

    struct Nuitka_FunctionObject *result;

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_functions, struct Nuitka_FunctionObject, Nuitka_Function_Type, closure_given);

    assert(closure_given == 0 || closure != NULL);

    memcpy(&result->m_closure[0], closure, closure_given * sizeof(struct Nuitka_CellObject *));
    result->m_closure_given = closure_given;

    if (c_code != NULL) {
        result->m_c_code = c_code;
        result->m_constant_return_value = NULL;
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
        Py_INCREF_IMMORTAL(Py_None);
        defaults = Py_None;
    }
    CHECK_OBJECT(defaults);
    assert(defaults == Py_None || (PyTuple_Check(defaults) && PyTuple_GET_SIZE(defaults) > 0));
    result->m_defaults = defaults;

    _onUpdatedCompiledFunctionDefaultsValue(result);

#if PYTHON_VERSION >= 0x300
    assert(kw_defaults == NULL || (PyDict_Check(kw_defaults) && DICT_SIZE(kw_defaults) > 0));
    result->m_kwdefaults = kw_defaults;

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

    result->m_varnames = Nuitka_GetCodeVarNames(code_object);

    result->m_module = module;

    Py_XINCREF(doc);
    result->m_doc = doc;

    result->m_dict = NULL;
    result->m_weakrefs = NULL;

    static long Nuitka_Function_counter = 0;
    result->m_counter = Nuitka_Function_counter++;

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_SLOT)
    result->m_vectorcall = (vectorcallfunc)Nuitka_Function_tp_vectorcall;
#endif

#if PYTHON_VERSION >= 0x3c0
    result->m_type_params = const_tuple_empty;
    assert(_Py_IsImmortal(result->m_type_params));
#endif

    Nuitka_GC_Track(result);

    assert(Py_REFCNT(result) == 1);

    return result;
}

#if PYTHON_VERSION >= 0x300
static void formatErrorNoArgumentAllowedKwSplit(struct Nuitka_FunctionObject const *function, PyObject *kw_name,
                                                Py_ssize_t given) {
#if PYTHON_VERSION < 0x3a0
    char const *function_name = Nuitka_String_AsString(function->m_name);
#else
    char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

    PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'", function_name,
                 Nuitka_String_AsString(kw_name));
}
#endif

static void formatErrorNoArgumentAllowed(struct Nuitka_FunctionObject const *function,
#if PYTHON_VERSION >= 0x300
                                         PyObject *kw,
#endif
                                         Py_ssize_t given) {
#if PYTHON_VERSION < 0x3a0
    char const *function_name = Nuitka_String_AsString(function->m_name);
#else
    char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

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
static void formatErrorTooFewArguments(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
#if PYTHON_VERSION < 0x270
                                       Py_ssize_t kw_size,
#endif
                                       Py_ssize_t given) {
    Py_ssize_t required_parameter_count = function->m_args_positional_count - function->m_defaults_given;

#if PYTHON_VERSION < 0x390
    char const *function_name = Nuitka_String_AsString(function->m_name);
#else
    char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif
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
static void formatErrorTooFewArguments(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                       PyObject **values) {
#if PYTHON_VERSION < 0x3a0
    char const *function_name = Nuitka_String_AsString(function->m_name);
#else
    char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

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

                list_str = UNICODE_CONCAT(tstate, list_str, current);

                Py_DECREF(old);
            } else if (missing == 1) {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(tstate, and_str, list_str);

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(tstate, current, list_str);

                Py_DECREF(old);
            } else {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(tstate, comma_str, list_str);

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(tstate, current, list_str);

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

#if PYTHON_VERSION < 0x3a0
    char const *function_name = Nuitka_String_AsString(function->m_name);
#else
    char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

#if PYTHON_VERSION < 0x300
    char const *violation = function->m_defaults != Py_None ? "at most" : "exactly";
#endif
    char const *plural = top_level_parameter_count == 1 ? "" : "s";

#if PYTHON_VERSION < 0x270
    PyErr_Format(PyExc_TypeError, "%s() takes %s %zd%s argument%s (%zd given)", function_name, violation,
                 top_level_parameter_count, kw_size > 0 ? " non-keyword" : "", plural, given);
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
static void formatErrorTooFewKwOnlyArguments(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                             PyObject **kw_vars) {
#if PYTHON_VERSION < 0x3a0
    char const *function_name = Nuitka_String_AsString(function->m_name);
#else
    char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

    Py_ssize_t co_kwonlyargcount = function->m_code_object->co_kwonlyargcount;

    Py_ssize_t max_missing = 0;

    for (Py_ssize_t i = co_kwonlyargcount - 1; i >= 0; --i) {
        if (kw_vars[i] == NULL) {
            max_missing += 1;
        }
    }

    PyObject *list_str = PyUnicode_FromString("");

    PyObject *comma_str = PyUnicode_FromString(", ");
    PyObject *and_str = PyUnicode_FromString(max_missing == 2 ? " and " : ", and ");

    Py_ssize_t missing = 0;
    for (Py_ssize_t i = co_kwonlyargcount - 1; i >= 0; --i) {
        if (kw_vars[i] == NULL) {
            PyObject *current_str = function->m_varnames[function->m_args_positional_count + i];

            PyObject *current = PyObject_Repr(current_str);

            if (missing == 0) {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(tstate, list_str, current);

                if (unlikely(list_str == NULL)) {
                    list_str = old;
                    break;
                }

                Py_DECREF(old);
            } else if (missing == 1) {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(tstate, and_str, list_str);

                if (unlikely(list_str == NULL)) {
                    list_str = old;
                    break;
                }

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(tstate, current, list_str);

                if (unlikely(list_str == NULL)) {
                    list_str = old;
                    break;
                }

                Py_DECREF(old);
            } else {
                PyObject *old = list_str;

                list_str = UNICODE_CONCAT(tstate, comma_str, list_str);

                if (unlikely(list_str == NULL)) {
                    list_str = old;
                    break;
                }

                Py_DECREF(old);
                old = list_str;

                list_str = UNICODE_CONCAT(tstate, current, list_str);

                if (unlikely(list_str == NULL)) {
                    list_str = old;
                    break;
                }

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

static void formatErrorKeywordsMustBeString(PyThreadState *tstate, struct Nuitka_FunctionObject const *function) {
#if PYTHON_VERSION < 0x390
    char const *function_name = Nuitka_String_AsString(function->m_name);
    SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() keywords must be strings", function_name);
#else
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "keywords must be strings");
#endif
}

static inline bool checkKeywordType(PyObject *arg_name) {
#if PYTHON_VERSION < 0x300
    return (PyString_Check(arg_name) || PyUnicode_Check(arg_name));
#else
    return PyUnicode_Check(arg_name) != 0;
#endif
}

static inline bool RICH_COMPARE_EQ_CBOOL_ARG_NAMES(PyObject *operand1, PyObject *operand2) {
    // Compare with argument name. We know our type, but from the outside, it
    // can be a derived type, or in case of Python2, a unicode value to compare
    // with a string. These half sided comparisons will make the switch to the
    // special one immediately if possible though.

#if PYTHON_VERSION < 0x300
    nuitka_bool result = RICH_COMPARE_EQ_NBOOL_STR_OBJECT(operand1, operand2);
#else
    nuitka_bool result = RICH_COMPARE_EQ_NBOOL_UNICODE_OBJECT(operand1, operand2);
#endif

    // Should be close to impossible, we will have to ignore it though.
    if (unlikely(result == NUITKA_BOOL_EXCEPTION)) {
        PyThreadState *tstate = PyThreadState_GET();

        CLEAR_ERROR_OCCURRED(tstate);
        return false;
    }

    return result == NUITKA_BOOL_TRUE;
}

#if PYTHON_VERSION < 0x300
static Py_ssize_t handleKeywordArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                    PyObject **python_pars, PyObject *kw)
#else
static Py_ssize_t handleKeywordArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                    PyObject **python_pars, Py_ssize_t *kw_only_found, PyObject *kw)
#endif
{
    Py_ssize_t keywords_count = function->m_args_keywords_count;

#if PYTHON_VERSION >= 0x300
    Py_ssize_t keyword_after_index = function->m_args_positional_count;
#endif

    assert(function->m_args_star_dict_index == -1);

    Py_ssize_t kw_found = 0;
    Py_ssize_t pos = 0;
    PyObject *key, *value;

    while (Nuitka_DictNext(kw, &pos, &key, &value)) {
        if (unlikely(!checkKeywordType(key))) {
            formatErrorKeywordsMustBeString(tstate, function);
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
            PyObject **var_names = function->m_varnames;

            for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
                if (RICH_COMPARE_EQ_CBOOL_ARG_NAMES(var_names[i], key)) {
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
                PyObject **var_names = function->m_varnames;

                if (RICH_COMPARE_EQ_CBOOL_ARG_NAMES(var_names[i], key)) {
                    pos_only_error = true;
                    break;
                }
            }

#if PYTHON_VERSION < 0x3a0
            char const *function_name = Nuitka_String_AsString(function->m_name);
#else
            char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

            if (pos_only_error == true) {
                PyErr_Format(PyExc_TypeError,
                             "%s() got some positional-only arguments passed as keyword arguments: '%s'", function_name,
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");

            } else {
                PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'", function_name,
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

#if PYTHON_VERSION < 0x300
static Py_ssize_t handleKeywordArgsSplit(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                         PyObject *const *kw_values, PyObject *kw_names)
#else
static Py_ssize_t handleKeywordArgsSplit(struct Nuitka_FunctionObject const *function, PyObject **python_pars,
                                         Py_ssize_t *kw_only_found, PyObject *const *kw_values, PyObject *kw_names)
#endif
{
    Py_ssize_t keywords_count = function->m_args_keywords_count;

#if PYTHON_VERSION >= 0x300
    Py_ssize_t keyword_after_index = function->m_args_positional_count;
#endif

    assert(function->m_args_star_dict_index == -1);

    Py_ssize_t kw_found = 0;

    Py_ssize_t kw_names_size = PyTuple_GET_SIZE(kw_names);

    for (Py_ssize_t kw_index = 0; kw_index < kw_names_size; kw_index++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, kw_index);
        PyObject *value = kw_values[kw_index];

        assert(checkKeywordType(key));

        NUITKA_MAY_BE_UNUSED bool found = false;

#if PYTHON_VERSION < 0x380
        Py_ssize_t kw_arg_start = 0;
#else
        Py_ssize_t kw_arg_start = function->m_args_pos_only_count;
#endif

        Py_INCREF(value);

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
            PyObject **var_names = function->m_varnames;

            for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
                // TODO: Could do better here, STR/UNICODE key knowledge being there.
                if (RICH_COMPARE_EQ_CBOOL_ARG_NAMES(var_names[i], key)) {
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
                PyObject **var_names = function->m_varnames;

                if (RICH_COMPARE_EQ_CBOOL_ARG_NAMES(var_names[i], key)) {
                    pos_only_error = true;
                    break;
                }
            }

#if PYTHON_VERSION < 0x3a0
            char const *function_name = Nuitka_String_AsString(function->m_name);
#else
            char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

            if (pos_only_error == true) {
                PyErr_Format(PyExc_TypeError,
                             "%s() got some positional-only arguments passed as keyword arguments: '%s'", function_name,
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");

            } else {
                PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'", function_name,
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");
            }

            Py_DECREF(value);

            return -1;
        }

        kw_found += 1;
    }

    return kw_found;
}

static PyObject *COPY_DICT_KW(PyThreadState *tstate, PyObject *dict_value);

static bool MAKE_STAR_DICT_DICTIONARY_COPY(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                           PyObject **python_pars, PyObject *kw) {
    Py_ssize_t star_dict_index = function->m_args_star_dict_index;
    assert(star_dict_index != -1);

    if (kw == NULL || ((PyDictObject *)kw)->ma_used == 0) {
        python_pars[star_dict_index] = MAKE_DICT_EMPTY(tstate);
    } else {
        python_pars[star_dict_index] = COPY_DICT_KW(tstate, kw);

        if (unlikely(python_pars[star_dict_index] == NULL)) {
            formatErrorKeywordsMustBeString(tstate, function);
            return false;
        }
    }

    return true;
}

#if PYTHON_VERSION < 0x300
static Py_ssize_t handleKeywordArgsWithStarDict(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                                PyObject **python_pars, PyObject *kw)
#else
static Py_ssize_t handleKeywordArgsWithStarDict(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                                PyObject **python_pars, Py_ssize_t *kw_only_found, PyObject *kw)
#endif
{
    assert(function->m_args_star_dict_index != -1);

    if (unlikely(MAKE_STAR_DICT_DICTIONARY_COPY(tstate, function, python_pars, kw) == false)) {
        return -1;
    }

    Py_ssize_t kw_found = 0;
    Py_ssize_t keywords_count = function->m_args_keywords_count;
#if PYTHON_VERSION >= 0x300
    Py_ssize_t keyword_after_index = function->m_args_positional_count;
#endif

    Py_ssize_t star_dict_index = function->m_args_star_dict_index;

    PyObject **var_names = function->m_varnames;

#if PYTHON_VERSION < 0x380
    Py_ssize_t kw_arg_start = 0;
#else
    Py_ssize_t kw_arg_start = function->m_args_pos_only_count;
#endif

    for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
        PyObject *arg_name = var_names[i];

        PyObject *kw_arg_value = DICT_GET_ITEM1(tstate, python_pars[star_dict_index], arg_name);

        if (kw_arg_value != NULL) {
            assert(python_pars[i] == NULL);

            python_pars[i] = kw_arg_value;

            DICT_REMOVE_ITEM(python_pars[star_dict_index], arg_name);

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

#if PYTHON_VERSION < 0x300
static Py_ssize_t
handleKeywordArgsSplitWithStarDict(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                   PyObject **python_pars, PyObject *const *kw_values, PyObject *kw_names)
#else
static Py_ssize_t handleKeywordArgsSplitWithStarDict(PyThreadState *tstate,
                                                     struct Nuitka_FunctionObject const *function,
                                                     PyObject **python_pars, Py_ssize_t *kw_only_found,
                                                     PyObject *const *kw_values, PyObject *kw_names)
#endif
{

    Py_ssize_t star_dict_index = function->m_args_star_dict_index;
    assert(star_dict_index != -1);

    Py_ssize_t kw_names_size = PyTuple_GET_SIZE(kw_names);

    python_pars[star_dict_index] = _PyDict_NewPresized(kw_names_size);

    for (Py_ssize_t i = 0; i < kw_names_size; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);
        PyObject *value = kw_values[i];

        DICT_SET_ITEM(python_pars[star_dict_index], key, value);
    }

    Py_ssize_t kw_found = 0;
    Py_ssize_t keywords_count = function->m_args_keywords_count;
#if PYTHON_VERSION >= 0x300
    Py_ssize_t keyword_after_index = function->m_args_positional_count;
#endif

    PyObject **var_names = function->m_varnames;

#if PYTHON_VERSION < 0x380
    Py_ssize_t kw_arg_start = 0;
#else
    Py_ssize_t kw_arg_start = function->m_args_pos_only_count;
#endif

    for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
        PyObject *arg_name = var_names[i];

        PyObject *kw_arg_value = DICT_GET_ITEM1(tstate, python_pars[star_dict_index], arg_name);

        if (kw_arg_value != NULL) {
            assert(python_pars[i] == NULL);

            python_pars[i] = kw_arg_value;

            DICT_REMOVE_ITEM(python_pars[star_dict_index], arg_name);

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

static void makeStarListTupleCopy(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                  PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size) {
    assert(function->m_args_star_list_index != -1);
    Py_ssize_t list_star_index = function->m_args_star_list_index;

    // Copy left-over argument values to the star list parameter given.
    if (args_size > function->m_args_positional_count) {
        python_pars[list_star_index] =
            MAKE_TUPLE(tstate, &args[function->m_args_positional_count], args_size - function->m_args_positional_count);
    } else {
        python_pars[list_star_index] = const_tuple_empty;
        Py_INCREF(const_tuple_empty);
    }
}

static void makeStarListTupleCopyMethod(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                        PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size) {
    assert(function->m_args_star_list_index != -1);
    Py_ssize_t list_star_index = function->m_args_star_list_index;

    // Copy left-over argument values to the star list parameter given.
    if (args_size + 1 > function->m_args_positional_count) {
        python_pars[list_star_index] = MAKE_TUPLE(tstate, &args[function->m_args_positional_count - 1],
                                                  args_size + 1 - function->m_args_positional_count);
    } else {
        python_pars[list_star_index] = const_tuple_empty;
        Py_INCREF(const_tuple_empty);
    }
}

static bool _handleArgumentsPlainOnly(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                      PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size) {
    Py_ssize_t arg_count = function->m_args_positional_count;

    // Check if too many arguments were given in case of non list star arg.
    // For Python3 it's done only later, when more knowledge has
    // been gained.
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
        formatErrorTooFewArguments(tstate, function, 0, args_size);
        return false;
#elif PYTHON_VERSION < 0x300
        formatErrorTooFewArguments(tstate, function, args_size);
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
        formatErrorTooFewArguments(tstate, function, python_pars);
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
        makeStarListTupleCopy(tstate, function, python_pars, args, args_size);
    }

    return true;
}

static bool handleMethodArgumentsPlainOnly(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                           PyObject **python_pars, PyObject *object, PyObject *const *args,
                                           Py_ssize_t args_size) {
    Py_ssize_t arg_count = function->m_args_positional_count;

    // There may be no self, otherwise we can directly assign it.
    if (arg_count >= 1) {
        python_pars[0] = object;
        Py_INCREF(object);
    } else {
        // Without self, there can only be star list to get the object as its
        // first element. Or we complain about illegal arguments.
        if (function->m_args_star_list_index == 0) {
            python_pars[0] = MAKE_TUPLE_EMPTY(tstate, args_size + 1);
            PyTuple_SET_ITEM0(python_pars[0], 0, object);

            for (Py_ssize_t i = 0; i < args_size; i++) {
                PyTuple_SET_ITEM0(python_pars[0], i + 1, args[i]);
            }

            return true;
        }
    }

    // Check if too many arguments were given in case of non list star arg.
    // For Python3 it's done only later, when more knowledge has
    // been gained.
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
        formatErrorTooFewArguments(tstate, function, 0, args_size + 1);
        return false;
#elif PYTHON_VERSION < 0x300
        formatErrorTooFewArguments(tstate, function, args_size + 1);
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
        formatErrorTooFewArguments(tstate, function, python_pars);
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
        makeStarListTupleCopyMethod(tstate, function, python_pars, args, args_size);
    }

    return true;
}

#if PYTHON_VERSION < 0x270
static bool _handleArgumentsPlain(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                  PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size,
                                  Py_ssize_t kw_found, Py_ssize_t kw_size)
#elif PYTHON_VERSION < 0x300
static bool _handleArgumentsPlain(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                  PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size,
                                  Py_ssize_t kw_found)
#else
static bool _handleArgumentsPlain(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                  PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size,
                                  Py_ssize_t kw_found, Py_ssize_t kw_only_found)
#endif
{
    Py_ssize_t arg_count = function->m_args_positional_count;

    // Check if too many arguments were given in case of non list star arg.
    // For Python3 it's done only later, when more knowledge has
    // been gained.
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
                    formatErrorTooFewArguments(tstate, function, kw_size, args_size + kw_found);
                    return false;
#elif PYTHON_VERSION < 0x300
                    formatErrorTooFewArguments(tstate, function, args_size + kw_found);
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
            formatErrorTooFewArguments(tstate, function, kw_size, args_size + kw_found);
            return false;
#elif PYTHON_VERSION < 0x300
            formatErrorTooFewArguments(tstate, function, args_size + kw_found);
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
        formatErrorTooFewArguments(tstate, function, python_pars);
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
        makeStarListTupleCopy(tstate, function, python_pars, args, args_size);
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

static bool parseArgumentsPos(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                              PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size) {
    bool result;

    Py_ssize_t arg_count = function->m_args_positional_count;

    if (unlikely(arg_count == 0 && function->m_args_simple && args_size != 0)) {
#if PYTHON_VERSION < 0x300
        formatErrorNoArgumentAllowed(function, args_size);
#else
        formatErrorNoArgumentAllowed(function, NULL, args_size);
#endif

        releaseParameters(function, python_pars);
        return false;
    }

    result = _handleArgumentsPlainOnly(tstate, function, python_pars, args, args_size);

    if (result == false) {
        releaseParameters(function, python_pars);
        return false;
    }

#if PYTHON_VERSION >= 0x300
    // For Python3 the keyword only errors are all reported at once.
    bool kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(tstate, function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(tstate, function, &python_pars[function->m_args_positional_count]);

        releaseParameters(function, python_pars);
        return false;
    }

#endif

    if (function->m_args_star_dict_index != -1) {
        python_pars[function->m_args_star_dict_index] = MAKE_DICT_EMPTY(tstate);
    }

    return true;
}

// We leave it to partial inlining to specialize this.
static bool parseArgumentsEmpty(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                PyObject **python_pars) {
    return parseArgumentsPos(tstate, function, python_pars, NULL, 0);
}

static bool parseArgumentsMethodPos(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                    PyObject **python_pars, PyObject *object, PyObject *const *args,
                                    Py_ssize_t args_size) {
    bool result;

    result = handleMethodArgumentsPlainOnly(tstate, function, python_pars, object, args, args_size);

    if (result == false) {
        releaseParameters(function, python_pars);
        return false;
    }

#if PYTHON_VERSION >= 0x300
    // For Python3 the keyword only errors are all reported at once.
    bool kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(tstate, function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(tstate, function, &python_pars[function->m_args_positional_count]);

        releaseParameters(function, python_pars);
        return false;
    }

#endif

    if (function->m_args_star_dict_index != -1) {
        python_pars[function->m_args_star_dict_index] = MAKE_DICT_EMPTY(tstate);
    }

    return true;
}

static bool parseArgumentsFullKwSplit(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                      PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size,
                                      PyObject *const *kw_values, PyObject *kw_names) {
    Py_ssize_t kw_size = PyTuple_GET_SIZE(kw_names);
    Py_ssize_t kw_found;
    bool result;

    Py_ssize_t arg_count = function->m_args_keywords_count;

    if (unlikely(arg_count == 0 && function->m_args_simple && args_size + kw_size > 0)) {
#if PYTHON_VERSION < 0x300
        formatErrorNoArgumentAllowed(function, args_size + kw_size);
#else
        formatErrorNoArgumentAllowedKwSplit(function, PyTuple_GET_ITEM(kw_names, 0), args_size);
#endif

        releaseParameters(function, python_pars);
        return false;
    }

#if PYTHON_VERSION >= 0x300
    Py_ssize_t kw_only_found = 0;
#endif
    if (function->m_args_star_dict_index != -1) {
#if PYTHON_VERSION < 0x300
        kw_found = handleKeywordArgsSplitWithStarDict(tstate, function, python_pars, kw_values, kw_names);
#else
        kw_found =
            handleKeywordArgsSplitWithStarDict(tstate, function, python_pars, &kw_only_found, kw_values, kw_names);
#endif
        if (unlikely(kw_found == -1)) {
            releaseParameters(function, python_pars);
            return false;
        }
    } else {
#if PYTHON_VERSION < 0x300
        kw_found = handleKeywordArgsSplit(function, python_pars, kw_values, kw_names);
#else
        kw_found = handleKeywordArgsSplit(function, python_pars, &kw_only_found, kw_values, kw_names);
#endif
        if (unlikely(kw_found == -1)) {
            releaseParameters(function, python_pars);
            return false;
        }
    }

#if PYTHON_VERSION < 0x270
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found, kw_size);
#elif PYTHON_VERSION < 0x300
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found);
#else
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found, kw_only_found);
#endif

    if (result == false) {
        releaseParameters(function, python_pars);
        return false;
    }

#if PYTHON_VERSION >= 0x300
    // For Python3 the keyword only errors are all reported at once.
    bool kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(tstate, function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(tstate, function, &python_pars[function->m_args_positional_count]);

        releaseParameters(function, python_pars);
        return false;
    }

#endif

    return true;
}

static bool parseArgumentsFull(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                               PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size, PyObject *kw) {
    Py_ssize_t kw_size = kw ? DICT_SIZE(kw) : 0;
    Py_ssize_t kw_found;
    bool result;

    Py_ssize_t arg_count = function->m_args_keywords_count;

    assert(kw == NULL || PyDict_CheckExact(kw));

    if (unlikely(arg_count == 0 && function->m_args_simple && args_size + kw_size > 0)) {
#if PYTHON_VERSION < 0x300
        formatErrorNoArgumentAllowed(function, args_size + kw_size);
#else
        formatErrorNoArgumentAllowed(function, kw_size > 0 ? kw : NULL, args_size);
#endif

        releaseParameters(function, python_pars);
        return false;
    }

#if PYTHON_VERSION >= 0x300
    Py_ssize_t kw_only_found = 0;
#endif
    if (function->m_args_star_dict_index != -1) {
#if PYTHON_VERSION < 0x300
        kw_found = handleKeywordArgsWithStarDict(tstate, function, python_pars, kw);
#else
        kw_found = handleKeywordArgsWithStarDict(tstate, function, python_pars, &kw_only_found, kw);
#endif
        if (unlikely(kw_found == -1)) {
            releaseParameters(function, python_pars);
            return false;
        }
    } else if (kw == NULL || DICT_SIZE(kw) == 0) {
        kw_found = 0;
    } else {
#if PYTHON_VERSION < 0x300
        kw_found = handleKeywordArgs(tstate, function, python_pars, kw);
#else
        kw_found = handleKeywordArgs(tstate, function, python_pars, &kw_only_found, kw);
#endif
        if (unlikely(kw_found == -1)) {
            releaseParameters(function, python_pars);
            return false;
        }
    }

#if PYTHON_VERSION < 0x270
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found, kw_size);
#elif PYTHON_VERSION < 0x300
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found);
#else
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found, kw_only_found);
#endif

    if (result == false) {
        releaseParameters(function, python_pars);
        return false;
    }

#if PYTHON_VERSION >= 0x300
    // For Python3 the keyword only errors are all reported at once.
    bool kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(tstate, function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(tstate, function, &python_pars[function->m_args_positional_count]);

        releaseParameters(function, python_pars);
        return false;
    }

#endif

    return true;
}

PyObject *Nuitka_CallFunctionNoArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function) {
    NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (unlikely(!parseArgumentsEmpty(tstate, function, python_pars))) {
        return NULL;
    }

    return function->m_c_code(tstate, function, python_pars);
}

PyObject *Nuitka_CallFunctionPosArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                     PyObject *const *args, Py_ssize_t args_size) {
    NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (unlikely(!parseArgumentsPos(tstate, function, python_pars, args, args_size))) {
        return NULL;
    }

    return function->m_c_code(tstate, function, python_pars);
}

PyObject *Nuitka_CallFunctionPosArgsKwArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                           PyObject *const *args, Py_ssize_t args_size, PyObject *kw) {
    NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (unlikely(!parseArgumentsFull(tstate, function, python_pars, args, args_size, kw))) {
        return NULL;
    }

    return function->m_c_code(tstate, function, python_pars);
}

PyObject *Nuitka_CallFunctionPosArgsKwSplit(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                            PyObject *const *args, Py_ssize_t args_size, PyObject *const *kw_values,
                                            PyObject *kw_names) {
    NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (unlikely(!parseArgumentsFullKwSplit(tstate, function, python_pars, args, args_size, kw_values, kw_names))) {
        return NULL;
    }

    return function->m_c_code(tstate, function, python_pars);
}

PyObject *Nuitka_CallMethodFunctionNoArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                          PyObject *object) {
    NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (unlikely(!parseArgumentsMethodPos(tstate, function, python_pars, object, NULL, 0))) {
        return NULL;
    }

    return function->m_c_code(tstate, function, python_pars);
}

PyObject *Nuitka_CallMethodFunctionPosArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                           PyObject *object, PyObject *const *args, Py_ssize_t args_size) {
    NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (unlikely(!parseArgumentsMethodPos(tstate, function, python_pars, object, args, args_size))) {
        return NULL;
    }

    return function->m_c_code(tstate, function, python_pars);
}

PyObject *Nuitka_CallMethodFunctionPosArgsKwArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                                 PyObject *object, PyObject *const *args, Py_ssize_t args_size,
                                                 PyObject *kw) {
    NUITKA_DYNAMIC_ARRAY_DECL(new_args, PyObject *, args_size + 1);

    new_args[0] = object;
    memcpy(new_args + 1, args, args_size * sizeof(PyObject *));

    // TODO: Specialize implementation for massive gains.
    return Nuitka_CallFunctionPosArgsKwArgs(tstate, function, new_args, args_size + 1, kw);
}

static Py_ssize_t _handleVectorcallKeywordArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                               PyObject **python_pars, Py_ssize_t *kw_only_found,
                                               PyObject *const *kw_names, PyObject *const *kw_values,
                                               Py_ssize_t kw_size) {
    Py_ssize_t keywords_count = function->m_args_keywords_count;

    Py_ssize_t keyword_after_index = function->m_args_positional_count;

    assert(function->m_args_star_dict_index == -1);

    Py_ssize_t kw_found = 0;

    for (Py_ssize_t pos = 0; pos < kw_size; pos++) {
        PyObject *key = kw_names[pos];

        if (unlikely(!checkKeywordType(key))) {
            formatErrorKeywordsMustBeString(tstate, function);
            return -1;
        }

        NUITKA_MAY_BE_UNUSED bool found = false;

#if PYTHON_VERSION < 0x380
        Py_ssize_t kw_arg_start = 0;
#else
        Py_ssize_t kw_arg_start = function->m_args_pos_only_count;
#endif

        for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
            if (function->m_varnames[i] == key) {
                assert(python_pars[i] == NULL);
                python_pars[i] = kw_values[pos];
                Py_INCREF(python_pars[i]);

                if (i >= keyword_after_index) {
                    *kw_only_found += 1;
                }

                found = true;
                break;
            }
        }

        if (found == false) {
            PyObject **var_names = function->m_varnames;

            for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
                if (RICH_COMPARE_EQ_CBOOL_ARG_NAMES(var_names[i], key)) {
                    assert(python_pars[i] == NULL);
                    python_pars[i] = kw_values[pos];
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
                PyObject **var_names = function->m_varnames;

                if (RICH_COMPARE_EQ_CBOOL_ARG_NAMES(var_names[i], key)) {
                    pos_only_error = true;
                    break;
                }
            }

#if PYTHON_VERSION < 0x3a0
            char const *function_name = Nuitka_String_AsString(function->m_name);
#else
            char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

            if (pos_only_error == true) {
                PyErr_Format(PyExc_TypeError,
                             "%s() got some positional-only arguments passed as keyword arguments: '%s'", function_name,
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");

            } else {
                PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'", function_name,
                             Nuitka_String_Check(key) ? Nuitka_String_AsString(key) : "<non-string>");
            }

            return -1;
        }

        kw_found += 1;
    }

    return kw_found;
}

static bool MAKE_STAR_DICT_DICTIONARY_COPY38(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                             PyObject **python_pars, PyObject *const *kw_names,
                                             PyObject *const *kw_values, Py_ssize_t kw_size) {
    Py_ssize_t star_dict_index = function->m_args_star_dict_index;
    assert(star_dict_index != -1);

    python_pars[star_dict_index] = _PyDict_NewPresized(kw_size);

    for (int i = 0; i < kw_size; i++) {
        PyObject *key = kw_names[i];

        if (unlikely(!checkKeywordType(key))) {
            formatErrorKeywordsMustBeString(tstate, function);
            return false;
        }

        bool result = DICT_SET_ITEM(python_pars[star_dict_index], key, kw_values[i]);

        if (unlikely(result == false)) {
            return false;
        }
    }

    return true;
}

static Py_ssize_t handleVectorcallKeywordArgsWithStarDict(PyThreadState *tstate,
                                                          struct Nuitka_FunctionObject const *function,
                                                          PyObject **python_pars, Py_ssize_t *kw_only_found,
                                                          PyObject *const *kw_names, PyObject *const *kw_values,
                                                          Py_ssize_t kw_size) {
    assert(function->m_args_star_dict_index != -1);

    if (unlikely(MAKE_STAR_DICT_DICTIONARY_COPY38(tstate, function, python_pars, kw_names, kw_values, kw_size) ==
                 false)) {
        return -1;
    }

    Py_ssize_t kw_found = 0;
    Py_ssize_t keywords_count = function->m_args_keywords_count;
    Py_ssize_t keyword_after_index = function->m_args_positional_count;

    Py_ssize_t star_dict_index = function->m_args_star_dict_index;

    PyObject **var_names = function->m_varnames;

#if PYTHON_VERSION < 0x380
    Py_ssize_t kw_arg_start = 0;
#else
    Py_ssize_t kw_arg_start = function->m_args_pos_only_count;
#endif

    for (Py_ssize_t i = kw_arg_start; i < keywords_count; i++) {
        PyObject *arg_name = var_names[i];

        PyObject *kw_arg_value = DICT_GET_ITEM1(tstate, python_pars[star_dict_index], arg_name);

        if (kw_arg_value != NULL) {
            assert(python_pars[i] == NULL);

            python_pars[i] = kw_arg_value;

            DICT_REMOVE_ITEM(python_pars[star_dict_index], arg_name);

            kw_found += 1;

            if (i >= keyword_after_index) {
                *kw_only_found += 1;
            }
        }
    }

    return kw_found;
}

static bool parseArgumentsVectorcall(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                     PyObject **python_pars, PyObject *const *args, Py_ssize_t args_size,
                                     PyObject *const *kw_names, Py_ssize_t kw_size) {
    Py_ssize_t kw_found;
    bool result;
    Py_ssize_t kw_only_found;

    Py_ssize_t arg_count = function->m_args_keywords_count;

    // TODO: Create different the vector call slot entries for different function types for extra
    // performance.

    if (unlikely(arg_count == 0 && function->m_args_simple && args_size + kw_size > 0)) {
#if PYTHON_VERSION < 0x3a0
        char const *function_name = Nuitka_String_AsString(function->m_name);
#else
        char const *function_name = Nuitka_String_AsString(function->m_qualname);
#endif

        if (kw_size == 0) {
            PyErr_Format(PyExc_TypeError, "%s() takes 0 positional arguments but %zd was given", function_name,
                         args_size);
        } else {
            PyErr_Format(PyExc_TypeError, "%s() got an unexpected keyword argument '%s'", function_name,
                         Nuitka_String_AsString(kw_names[0]));
        }

        releaseParameters(function, python_pars);
        return false;
    }

    kw_only_found = 0;
    if (function->m_args_star_dict_index != -1) {
        kw_found = handleVectorcallKeywordArgsWithStarDict(tstate, function, python_pars, &kw_only_found, kw_names,
                                                           &args[args_size], kw_size);
        if (unlikely(kw_found == -1)) {
            releaseParameters(function, python_pars);
            return false;
        }
    } else if (kw_size == 0) {
        kw_found = 0;
    } else {
        kw_found = _handleVectorcallKeywordArgs(tstate, function, python_pars, &kw_only_found, kw_names,
                                                &args[args_size], kw_size);

        if (unlikely(kw_found == -1)) {
            releaseParameters(function, python_pars);
            return false;
        }
    }

#if PYTHON_VERSION < 0x270
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found, kw_size);
#elif PYTHON_VERSION < 0x300
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found);
#else
    result = _handleArgumentsPlain(tstate, function, python_pars, args, args_size, kw_found, kw_only_found);
#endif

    if (result == false) {
        releaseParameters(function, python_pars);
        return false;
    }

#if PYTHON_VERSION >= 0x300
    // For Python3 the keyword only errors are all reported at once.
    bool kw_only_error = false;

    for (Py_ssize_t i = function->m_args_positional_count; i < function->m_args_keywords_count; i++) {
        if (python_pars[i] == NULL) {
            PyObject *arg_name = function->m_varnames[i];

            if (function->m_kwdefaults != NULL) {
                python_pars[i] = DICT_GET_ITEM1(tstate, function->m_kwdefaults, arg_name);
            }

            if (unlikely(python_pars[i] == NULL)) {
                kw_only_error = true;
            }
        }
    }

    if (unlikely(kw_only_error)) {
        formatErrorTooFewKwOnlyArguments(tstate, function, &python_pars[function->m_args_positional_count]);

        releaseParameters(function, python_pars);
        return false;
    }
#endif

    return true;
}

PyObject *Nuitka_CallFunctionVectorcall(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                        PyObject *const *args, Py_ssize_t args_size, PyObject *const *kw_names,
                                        Py_ssize_t kw_size) {
    NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
    memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

    if (unlikely(!parseArgumentsVectorcall(tstate, function, python_pars, args, args_size, kw_names, kw_size))) {
        return NULL;
    }
    return function->m_c_code(tstate, function, python_pars);
}

static PyObject *Nuitka_Function_tp_call(struct Nuitka_FunctionObject *function, PyObject *tuple_args, PyObject *kw) {
    CHECK_OBJECT(tuple_args);
    assert(PyTuple_CheckExact(tuple_args));

    PyThreadState *tstate = PyThreadState_GET();

    if (kw == NULL) {
        PyObject **args = &PyTuple_GET_ITEM(tuple_args, 0);
        Py_ssize_t args_size = PyTuple_GET_SIZE(tuple_args);

        if (function->m_args_simple && args_size == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < args_size; i++) {
                Py_INCREF(args[i]);
            }

            return function->m_c_code(tstate, function, args);
        } else if (function->m_args_simple &&
                   args_size + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
            memcpy(python_pars, args, args_size * sizeof(PyObject *));
            memcpy(python_pars + args_size, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_overall_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            return function->m_c_code(tstate, function, python_pars);
        } else {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_overall_count);
            memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

            if (parseArgumentsPos(tstate, function, python_pars, args, args_size)) {
                return function->m_c_code(tstate, function, python_pars);
            } else {
                return NULL;
            }
        }
    } else {
        return Nuitka_CallFunctionPosArgsKwArgs(tstate, function, &PyTuple_GET_ITEM(tuple_args, 0),
                                                PyTuple_GET_SIZE(tuple_args), kw);
    }
}

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_SLOT)
static PyObject *Nuitka_Function_tp_vectorcall(struct Nuitka_FunctionObject *function, PyObject *const *stack,
                                               size_t nargsf, PyObject *kw_names) {
    assert(kw_names == NULL || PyTuple_CheckExact(kw_names));
    Py_ssize_t kwargs_count = (kw_names == NULL) ? 0 : PyTuple_GET_SIZE(kw_names);

    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    assert(nargs >= 0);
    assert((nargs == 0 && kwargs_count == 0) || stack != NULL);

    PyThreadState *tstate = PyThreadState_GET();
    return Nuitka_CallFunctionVectorcall(tstate, function, stack, nargs,
                                         kw_names ? &PyTuple_GET_ITEM(kw_names, 0) : NULL, kwargs_count);
}
#endif

#include "CompiledMethodType.c"

#include "CompiledGeneratorType.c"

#include "CompiledCellType.c"

#include "CompiledCodeHelpers.c"

#include "InspectPatcher.c"
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
