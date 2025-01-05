//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template CodeTemplateCallsPositional.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *CALL_FUNCTION_NO_ARGS(PyThreadState *tstate, PyObject *called) {
    CHECK_OBJECT(called);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 0 == function->m_args_positional_count) {
            result = function->m_c_code(tstate, function, NULL);
        } else if (function->m_args_simple && 0 + function->m_defaults_given == function->m_args_positional_count) {
            PyObject **python_pars = &PyTuple_GET_ITEM(function->m_defaults, 0);

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionNoArgs(tstate, function);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyErr_Format(
                PyExc_TypeError,
                "unbound compiled_method %s%s must be called with %s instance as first argument (got nothing instead)",
                GET_CALLABLE_NAME((PyObject *)method->m_function), GET_CALLABLE_DESC((PyObject *)method->m_function),
                GET_CLASS_NAME(method->m_class));
            return NULL;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 0 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[0 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       0 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1 + 0, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionNoArgs(tstate, function, method->m_object);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, NULL, 0, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = const_tuple_empty;

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (likely(flags & METH_NOARGS)) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result = (*method)(self, NULL);

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif
            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (0 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = const_tuple_empty;
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = const_tuple_empty;
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, NULL, 0, NULL);
#else
                PyObject *pos_args = const_tuple_empty;
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 0);
#endif
            } else {
                PyObject *pos_args = const_tuple_empty;
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunctionNoArgs(called);
#else
        PyObject *result = _PyFunction_Vectorcall(called, NULL, 0, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = const_tuple_empty;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionNoArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj);
                        } else {
                            result = CALL_FUNCTION_NO_ARGS(tstate, init_method);

                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if ((init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            return obj;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionNoArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj);
        } else {
            result = CALL_FUNCTION_NO_ARGS(tstate, init_method);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, NULL, 0, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, const_tuple_empty, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_SINGLE_ARG(PyThreadState *tstate, PyObject *called, PyObject *arg) {
    PyObject *const *args = &arg; // For easier code compatibility.
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 1);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 1 == function->m_args_positional_count) {
            Py_INCREF(args[0]);
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 1 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 1 * sizeof(PyObject *));
            memcpy(python_pars + 1, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 1);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 1);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 1 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[1 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                python_pars[1] = args[0];
                Py_INCREF(args[0]);
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       1 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 1 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 1, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 1);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 1, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (1 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if ((flags & METH_O)) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result = (*method)(self, args[0]);

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 1, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 1);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 1);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 1, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called == (PyObject *)&PyType_Type)) {
                PyObject *result = (PyObject *)Py_TYPE(args[0]);
                Py_INCREF(result);
                return result;
            }

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 1);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 1);
                        } else {
                            result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, init_method, args[0]);

                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 1);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 1);
        } else {
            result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, init_method, args[0]);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 1, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS1(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 1);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 1);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 1 == function->m_args_positional_count) {
            Py_INCREF(args[0]);
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 1 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 1 * sizeof(PyObject *));
            memcpy(python_pars + 1, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 1);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 1);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 1 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[1 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                python_pars[1] = args[0];
                Py_INCREF(args[0]);
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       1 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 1 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 1, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 1);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 1, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (1 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if ((flags & METH_O)) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result = (*method)(self, args[0]);

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 1, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 1);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 1);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 1, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called == (PyObject *)&PyType_Type)) {
                PyObject *result = (PyObject *)Py_TYPE(args[0]);
                Py_INCREF(result);
                return result;
            }

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 1);
                        } else {
                            result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, init_method, args[0]);

                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 1);
        } else {
            result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, init_method, args[0]);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 1, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS2(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 2);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 2 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 2; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 2 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 2 * sizeof(PyObject *));
            memcpy(python_pars + 2, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 2);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 2);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 2 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[2 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 2; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       2 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 2 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 2, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 2);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 2, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (2 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (2 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 2, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 2);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 2);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 2, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 2);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 2);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS2(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 2);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 2);
        } else {
            result = CALL_FUNCTION_WITH_ARGS2(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 2, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS2(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 2);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 2);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 2 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 2; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 2 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 2 * sizeof(PyObject *));
            memcpy(python_pars + 2, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 2);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 2);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 2 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[2 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 2; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       2 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 2 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 2, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 2);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 2, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (2 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (2 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 2, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 2);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 2);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 2, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 2);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS2(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 2);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS2(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 2, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS3(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 3);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 3 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 3; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 3 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 3 * sizeof(PyObject *));
            memcpy(python_pars + 3, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 3);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 3);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 3 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[3 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 3; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       3 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 3 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 3, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 3);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 3, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (3 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (3 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 3, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 3);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 3);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 3, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 3);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 3);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS3(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 3);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 3);
        } else {
            result = CALL_FUNCTION_WITH_ARGS3(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 3, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS3(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 3);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 3);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 3 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 3; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 3 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 3 * sizeof(PyObject *));
            memcpy(python_pars + 3, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 3);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 3);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 3 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[3 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 3; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       3 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 3 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 3, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 3);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 3, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (3 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (3 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 3, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 3);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 3);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 3, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 3);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS3(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 3);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS3(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 3, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS4(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 4);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 4 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 4; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 4 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 4 * sizeof(PyObject *));
            memcpy(python_pars + 4, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 4);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 4);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 4 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[4 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 4; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       4 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 4 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 4, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 4);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 4, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (4 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (4 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 4, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 4);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 4);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 4, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 4);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 4);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS4(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 4);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 4);
        } else {
            result = CALL_FUNCTION_WITH_ARGS4(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 4, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS4(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 4);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 4);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 4 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 4; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 4 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 4 * sizeof(PyObject *));
            memcpy(python_pars + 4, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 4);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 4);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 4 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[4 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 4; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       4 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 4 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 4, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 4);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 4, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (4 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (4 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 4, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 4);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 4);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 4, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 4);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS4(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 4);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS4(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 4, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS5(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 5);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 5 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 5; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 5 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 5 * sizeof(PyObject *));
            memcpy(python_pars + 5, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 5);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 5);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 5 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[5 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 5; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       5 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 5 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 5, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 5);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 5, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (5 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (5 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 5, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 5);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 5);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 5, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 5);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 5);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS5(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 5);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 5);
        } else {
            result = CALL_FUNCTION_WITH_ARGS5(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 5, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS5(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 5);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 5);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 5 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 5; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 5 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 5 * sizeof(PyObject *));
            memcpy(python_pars + 5, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 5);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 5);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 5 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[5 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 5; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       5 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 5 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 5, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 5);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 5, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (5 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (5 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 5, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 5);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 5);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 5, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 5);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS5(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 5);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS5(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 5, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS6(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 6);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 6 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 6; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 6 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 6 * sizeof(PyObject *));
            memcpy(python_pars + 6, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 6);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 6);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 6 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[6 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 6; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       6 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 6 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 6, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 6);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 6, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (6 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (6 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 6, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 6);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 6);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 6, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 6);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 6);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS6(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 6);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 6);
        } else {
            result = CALL_FUNCTION_WITH_ARGS6(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 6, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS6(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 6);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 6);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 6 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 6; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 6 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 6 * sizeof(PyObject *));
            memcpy(python_pars + 6, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 6);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 6);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 6 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[6 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 6; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       6 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 6 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 6, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 6);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 6, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (6 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (6 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 6, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 6);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 6);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 6, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 6);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS6(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 6);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS6(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 6, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS7(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 7);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 7 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 7; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 7 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 7 * sizeof(PyObject *));
            memcpy(python_pars + 7, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 7);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 7);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 7 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[7 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 7; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       7 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 7 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 7, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 7);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 7, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (7 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (7 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 7, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 7);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 7);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 7, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 7);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 7);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS7(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 7);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 7);
        } else {
            result = CALL_FUNCTION_WITH_ARGS7(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 7, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS7(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 7);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 7);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 7 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 7; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 7 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 7 * sizeof(PyObject *));
            memcpy(python_pars + 7, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 7);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 7);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 7 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[7 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 7; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       7 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 7 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 7, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 7);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 7, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (7 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (7 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 7, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 7);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 7);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 7, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 7);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS7(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 7);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS7(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 7, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS8(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 8);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 8 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 8; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 8 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 8 * sizeof(PyObject *));
            memcpy(python_pars + 8, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 8);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 8);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 8 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[8 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 8; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       8 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 8 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 8, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 8);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 8, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (8 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (8 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 8, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 8);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 8);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 8, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 8);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 8);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS8(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 8);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 8);
        } else {
            result = CALL_FUNCTION_WITH_ARGS8(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 8, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS8(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 8);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 8);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 8 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 8; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 8 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 8 * sizeof(PyObject *));
            memcpy(python_pars + 8, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 8);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 8);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 8 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[8 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 8; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       8 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 8 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 8, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 8);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 8, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (8 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (8 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 8, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 8);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 8);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 8, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 8);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS8(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 8);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS8(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 8, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS9(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 9);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 9 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 9; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 9 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 9 * sizeof(PyObject *));
            memcpy(python_pars + 9, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 9);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 9);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 9 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[9 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 9; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       9 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 9 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 9, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 9);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 9, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (9 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (9 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 9, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 9);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 9);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 9, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 9);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 9);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS9(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 9);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 9);
        } else {
            result = CALL_FUNCTION_WITH_ARGS9(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 9, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS9(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 9);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 9);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 9 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 9; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 9 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 9 * sizeof(PyObject *));
            memcpy(python_pars + 9, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 9);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 9);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 9 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[9 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 9; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       9 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 9 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 9, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 9);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 9, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (9 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (9 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 9, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 9);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 9);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 9, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 9);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS9(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 9);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS9(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 9, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_ARGS10(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 10);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 10 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 10; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 10 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 10 * sizeof(PyObject *));
            memcpy(python_pars + 10, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 10);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 10);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 10 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[10 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 10; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       10 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 10 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 10, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 10);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 10, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (10 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (10 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

            Py_DECREF(pos_args);
#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
                Py_DECREF(pos_args);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 10, NULL);
#else
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 10);
                Py_DECREF(pos_args);
#endif
            } else {
                PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);
                result = (*method)(self, pos_args);
                Py_DECREF(pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 10);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 10, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *pos_args = NULL;
            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                pos_args = MAKE_TUPLE(tstate, args, 10);
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    Py_DECREF(pos_args);
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {
                        Py_XDECREF(pos_args);
                        pos_args = NULL;

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 10);
                        } else {
                            result = CALL_FUNCTION_WITH_ARGS10(tstate, init_method, args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {
                        if (pos_args == NULL) {
                            pos_args = MAKE_TUPLE(tstate, args, 10);
                        }

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            Py_XDECREF(pos_args);
                            return NULL;
                        }
                    }
                }
            }

            Py_XDECREF(pos_args);

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 10);
        } else {
            result = CALL_FUNCTION_WITH_ARGS10(tstate, init_method, args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 10, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS10(PyThreadState *tstate, PyObject *called, PyObject *pos_args) {
    assert(PyTuple_CheckExact(pos_args));
    assert(PyTuple_GET_SIZE(pos_args) == 10);
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 10);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;
        PyObject *result;

        if (function->m_args_simple && 10 == function->m_args_positional_count) {
            for (Py_ssize_t i = 0; i < 10; i++) {
                Py_INCREF(args[i]);
            }
            result = function->m_c_code(tstate, function, (PyObject **)args);
        } else if (function->m_args_simple && 10 + function->m_defaults_given == function->m_args_positional_count) {
            NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

            memcpy(python_pars, args, 10 * sizeof(PyObject *));
            memcpy(python_pars + 10, &PyTuple_GET_ITEM(function->m_defaults, 0),
                   function->m_defaults_given * sizeof(PyObject *));

            for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(tstate, function, python_pars);
        } else {
            result = Nuitka_CallFunctionPosArgs(tstate, function, args, 10);
        }

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        if (method->m_object == NULL) {
            PyObject *self = args[0];

            int res = PyObject_IsInstance(self, method->m_class);

            if (unlikely(res < 0)) {
                return NULL;
            } else if (unlikely(res == 0)) {
                PyErr_Format(PyExc_TypeError,
                             "unbound compiled_method %s%s must be called with %s instance as first argument (got %s "
                             "instance instead)",
                             GET_CALLABLE_NAME((PyObject *)method->m_function),
                             GET_CALLABLE_DESC((PyObject *)method->m_function), GET_CLASS_NAME(method->m_class),
                             GET_INSTANCE_CLASS_NAME(tstate, (PyObject *)self));

                return NULL;
            }

            PyObject *result = Nuitka_CallFunctionPosArgs(tstate, method->m_function, args, 10);

            CHECK_OBJECT_X(result);

            return result;
        } else {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;

            PyObject *result;

            if (function->m_args_simple && 10 + 1 == function->m_args_positional_count) {
                PyObject *python_pars[10 + 1];

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                for (Py_ssize_t i = 0; i < 10; i++) {
                    python_pars[i + 1] = args[i];
                    Py_INCREF(args[i]);
                }
                result = function->m_c_code(tstate, function, python_pars);
            } else if (function->m_args_simple &&
                       10 + 1 + function->m_defaults_given == function->m_args_positional_count) {
                NUITKA_DYNAMIC_ARRAY_DECL(python_pars, PyObject *, function->m_args_positional_count);

                python_pars[0] = method->m_object;
                Py_INCREF(method->m_object);

                memcpy(python_pars + 1, args, 10 * sizeof(PyObject *));
                memcpy(python_pars + 1 + 10, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       function->m_defaults_given * sizeof(PyObject *));

                for (Py_ssize_t i = 1; i < function->m_args_overall_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(tstate, function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionPosArgs(tstate, function, method->m_object, args, 10);
            }

            Py_LeaveRecursiveCall();

            CHECK_OBJECT_X(result);

            return result;
        }
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_CFUNCTION_CALL_OPT)
    } else if (PyCFunction_CheckExact(called)) {
#if PYTHON_VERSION >= 0x380
#ifdef _NUITKA_FULL_COMPAT
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }
#endif

        int flags = PyCFunction_GET_FLAGS(called);

        PyObject *result;

        if (!(flags & METH_VARARGS)) {
            vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

            assert(func != NULL);
            result = func(called, args, 10, NULL);

            CHECK_OBJECT_X(result);
        } else {
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)(void (*)(void))method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }
        }

#ifdef _NUITKA_FULL_COMPAT
        Py_LeaveRecursiveCall();
#endif
        CHECK_OBJECT_X(result);

        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS(called) & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

        if (unlikely(flags & METH_NOARGS)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes no arguments (10 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (unlikely(flags & METH_O)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (10 given)",
                                                ((PyCFunctionObject *)called)->m_ml->ml_name);
            return NULL;
        } else if (flags & METH_VARARGS) {
            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }
#endif
            PyCFunction method = PyCFunction_GET_FUNCTION(called);
            PyObject *self = PyCFunction_GET_SELF(called);

            PyObject *result;

#if PYTHON_VERSION < 0x360
            if (flags & METH_KEYWORDS) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else {
                result = (*method)(self, pos_args);
            }

#else
            if (flags == (METH_VARARGS | METH_KEYWORDS)) {
                result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
                result = (*(_PyCFunctionFast)method)(self, (PyObject **)args, 10, NULL);
#else
                result = (*(_PyCFunctionFast)method)(self, &pos_args, 10);
#endif
            } else {
                result = (*method)(self, pos_args);
            }
#endif

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
#endif
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(called)) {
#if PYTHON_VERSION < 0x3b0
        PyObject *result = callPythonFunction(called, args, 10);
#else
        PyObject *result = _PyFunction_Vectorcall(called, args, 10, NULL);
#endif
        CHECK_OBJECT_X(result);

        return result;
#endif
#if !defined(_NUITKA_EXPERIMENTAL_DISABLE_TYPE_CREATION_OPT)
    } else if (PyType_Check(called)) {
        PyTypeObject *type = Py_TYPE(called);

        if (type->tp_call == PyType_Type.tp_call) {
            PyTypeObject *called_type = (PyTypeObject *)(called);

            if (unlikely(called_type->tp_new == NULL)) {
                PyErr_Format(PyExc_TypeError, "cannot create '%s' instances", called_type->tp_name);
                return NULL;
            }

            PyObject *obj;

            if (called_type->tp_new == PyBaseObject_Type.tp_new) {
                if (unlikely(called_type->tp_flags & Py_TPFLAGS_IS_ABSTRACT)) {
                    formatCannotInstantiateAbstractClass(tstate, called_type);
                    return NULL;
                }

                obj = called_type->tp_alloc(called_type, 0);
                CHECK_OBJECT(obj);
            } else {
                obj = called_type->tp_new(called_type, pos_args, NULL);
            }

            if (likely(obj != NULL)) {
                if (!Nuitka_Type_IsSubtype(obj->ob_type, called_type)) {
                    return obj;
                }

                // Work on produced type.
                type = Py_TYPE(obj);

                if (NuitkaType_HasFeatureClass(type) && type->tp_init != NULL) {
                    if (type->tp_init == default_tp_init_wrapper) {

                        PyObject *init_method = Nuitka_TypeLookup(type, const_str_plain___init__);

                        // Not really allowed, since we wouldn't have the default wrapper set.
                        assert(init_method != NULL);

                        bool is_compiled_function = false;
                        bool init_method_needs_release = false;

                        if (likely(init_method != NULL)) {
                            descrgetfunc func = Py_TYPE(init_method)->tp_descr_get;

                            if (func == Nuitka_Function_Type.tp_descr_get) {
                                is_compiled_function = true;
                            } else if (func != NULL) {
                                init_method = func(init_method, obj, (PyObject *)(type));
                                init_method_needs_release = true;
                            }
                        }

                        if (unlikely(init_method == NULL)) {
                            if (!HAS_ERROR_OCCURRED(tstate)) {
                                SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_AttributeError,
                                                                   const_str_plain___init__);
                            }

                            return NULL;
                        }

                        PyObject *result;
                        if (is_compiled_function) {
                            result = Nuitka_CallMethodFunctionPosArgs(
                                tstate, (struct Nuitka_FunctionObject const *)init_method, obj, args, 10);
                        } else {
                            result = CALL_FUNCTION_WITH_POS_ARGS10(tstate, init_method, pos_args);
                            if (init_method_needs_release) {
                                Py_DECREF(init_method);
                            }
                        }

                        if (unlikely(result == NULL)) {
                            Py_DECREF(obj);
                            return NULL;
                        }

                        Py_DECREF(result);

                        if (unlikely(result != Py_None)) {
                            Py_DECREF(obj);

                            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
                            return NULL;
                        }
                    } else {

                        if (unlikely(type->tp_init(obj, pos_args, NULL) < 0)) {
                            Py_DECREF(obj);
                            return NULL;
                        }
                    }
                }
            }

            CHECK_OBJECT_X(obj);

            return obj;
        }
#endif
#if PYTHON_VERSION < 0x300
    } else if (PyClass_Check(called)) {
        PyObject *obj = PyInstance_NewRaw(called, NULL);

        PyObject *init_method = FIND_ATTRIBUTE_IN_CLASS((PyClassObject *)called, const_str_plain___init__);

        if (unlikely(init_method == NULL)) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                Py_DECREF(obj);
                return NULL;
            }

            Py_DECREF(obj);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "this constructor takes no arguments");
            return NULL;
        }

        bool is_compiled_function = false;

        descrgetfunc descr_get = Py_TYPE(init_method)->tp_descr_get;

        if (descr_get == NULL) {
            Py_INCREF(init_method);
        } else if (descr_get == Nuitka_Function_Type.tp_descr_get) {
            is_compiled_function = true;
        } else if (descr_get != NULL) {
            PyObject *descr_method = descr_get(init_method, obj, called);

            if (unlikely(descr_method == NULL)) {
                return NULL;
            }

            init_method = descr_method;
        }

        PyObject *result;
        if (is_compiled_function) {
            result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)init_method, obj,
                                                      args, 10);
        } else {
            result = CALL_FUNCTION_WITH_POS_ARGS10(tstate, init_method, pos_args);
            Py_DECREF(init_method);
        }
        if (unlikely(result == NULL)) {
            return NULL;
        }

        Py_DECREF(result);

        if (unlikely(result != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__init__() should return None, not '%s'", result);
            return NULL;
        }

        CHECK_OBJECT_X(obj);

        return obj;
#endif
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 10, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    CHECK_OBJECT_X(result);

    return result;
}
PyObject *CALL_FUNCTION_WITH_NO_ARGS_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *kw_values,
                                              PyObject *kw_names) {

    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, NULL, 0, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, kw_values, 0, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = const_tuple_empty;

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS1_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 1);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[1], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 1, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 1, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[1 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS1_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 1);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 1, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 1 + nkwargs);

            memcpy(vectorcall_args, args, 1 * sizeof(PyObject *));
            memcpy(&vectorcall_args[1], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 1, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS1_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 1);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 1, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 1 + nkwargs);

            memcpy(vectorcall_args, args, 1 * sizeof(PyObject *));
            memcpy(&vectorcall_args[1], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 1, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS2_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 2);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[2], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 2, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 2, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[2 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS2_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 2);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 2, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 2 + nkwargs);

            memcpy(vectorcall_args, args, 2 * sizeof(PyObject *));
            memcpy(&vectorcall_args[2], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 2, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS2_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 2);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 2, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 2 + nkwargs);

            memcpy(vectorcall_args, args, 2 * sizeof(PyObject *));
            memcpy(&vectorcall_args[2], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 2, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS3_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 3);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[3], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 3, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 3, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[3 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS3_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 3);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 3, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 3 + nkwargs);

            memcpy(vectorcall_args, args, 3 * sizeof(PyObject *));
            memcpy(&vectorcall_args[3], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 3, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS3_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 3);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 3, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 3 + nkwargs);

            memcpy(vectorcall_args, args, 3 * sizeof(PyObject *));
            memcpy(&vectorcall_args[3], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 3, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS4_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 4);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[4], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 4, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 4, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[4 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS4_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 4);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 4, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 4 + nkwargs);

            memcpy(vectorcall_args, args, 4 * sizeof(PyObject *));
            memcpy(&vectorcall_args[4], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 4, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS4_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 4);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 4, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 4 + nkwargs);

            memcpy(vectorcall_args, args, 4 * sizeof(PyObject *));
            memcpy(&vectorcall_args[4], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 4, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS5_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 5);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[5], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 5, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 5, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[5 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS5_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 5);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 5, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 5 + nkwargs);

            memcpy(vectorcall_args, args, 5 * sizeof(PyObject *));
            memcpy(&vectorcall_args[5], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 5, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 5);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS5_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 5);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 5, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 5 + nkwargs);

            memcpy(vectorcall_args, args, 5 * sizeof(PyObject *));
            memcpy(&vectorcall_args[5], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 5, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS6_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 6);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[6], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 6, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 6, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[6 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS6_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 6);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 6, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 6 + nkwargs);

            memcpy(vectorcall_args, args, 6 * sizeof(PyObject *));
            memcpy(&vectorcall_args[6], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 6, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 6);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS6_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 6);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 6, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 6 + nkwargs);

            memcpy(vectorcall_args, args, 6 * sizeof(PyObject *));
            memcpy(&vectorcall_args[6], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 6, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS7_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 7);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[7], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 7, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 7, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[7 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS7_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 7);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 7, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 7 + nkwargs);

            memcpy(vectorcall_args, args, 7 * sizeof(PyObject *));
            memcpy(&vectorcall_args[7], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 7, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 7);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS7_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 7);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 7, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 7 + nkwargs);

            memcpy(vectorcall_args, args, 7 * sizeof(PyObject *));
            memcpy(&vectorcall_args[7], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 7, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS8_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 8);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[8], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 8, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 8, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[8 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS8_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 8);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 8, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 8 + nkwargs);

            memcpy(vectorcall_args, args, 8 * sizeof(PyObject *));
            memcpy(&vectorcall_args[8], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 8, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 8);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS8_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 8);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 8, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 8 + nkwargs);

            memcpy(vectorcall_args, args, 8 * sizeof(PyObject *));
            memcpy(&vectorcall_args[8], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 8, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS9_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                              PyObject *kw_names) {
    CHECK_OBJECTS(args, 9);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[9], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 9, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 9, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[9 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS9_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                            PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 9);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 9, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 9 + nkwargs);

            memcpy(vectorcall_args, args, 9 * sizeof(PyObject *));
            memcpy(&vectorcall_args[9], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 9, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 9);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS9_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 9);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 9, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 9 + nkwargs);

            memcpy(vectorcall_args, args, 9 * sizeof(PyObject *));
            memcpy(&vectorcall_args[9], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 9, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS10_VECTORCALL(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                               PyObject *kw_names) {
    CHECK_OBJECTS(args, 10);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(&args[10], nkwargs);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result =
            Nuitka_CallFunctionVectorcall(tstate, function, args, 10, &PyTuple_GET_ITEM(kw_names, 0), nkwargs);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(called, args, 10, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = args[10 + i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_ARGS10_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *const *args,
                                             PyObject *const *kw_values, PyObject *kw_names) {
    CHECK_OBJECTS(args, 10);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 10, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 10 + nkwargs);

            memcpy(vectorcall_args, args, 10 * sizeof(PyObject *));
            memcpy(&vectorcall_args[10], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 10, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 10);

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(pos_args);
    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_FUNCTION_WITH_POS_ARGS10_KW_SPLIT(PyThreadState *tstate, PyObject *called, PyObject *pos_args,
                                                 PyObject *const *kw_values, PyObject *kw_names) {
    assert(PyTuple_CheckExact(pos_args));
    PyObject *const *args = &PyTuple_GET_ITEM(pos_args, 0);
    CHECK_OBJECTS(args, 10);
    CHECK_OBJECT(kw_names);
    assert(PyTuple_CheckExact(kw_names));
    CHECK_OBJECT(called);

    Py_ssize_t nkwargs = PyTuple_GET_SIZE(kw_names);

    CHECK_OBJECTS(kw_values, PyTuple_GET_SIZE(kw_names));

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result = Nuitka_CallFunctionPosArgsKwSplit(tstate, function, args, 10, kw_values, kw_names);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    } else if (PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            NUITKA_DYNAMIC_ARRAY_DECL(vectorcall_args, PyObject *, 10 + nkwargs);

            memcpy(vectorcall_args, args, 10 * sizeof(PyObject *));
            memcpy(&vectorcall_args[10], kw_values, nkwargs * sizeof(PyObject *));

            PyObject *result = func(called, vectorcall_args, 10, kw_names);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, called, result);
        }
#endif
    }

#if 0
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    ternaryfunc call_slot = Py_TYPE(called)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", called);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *named_args = _PyDict_NewPresized(nkwargs);

    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *key = PyTuple_GET_ITEM(kw_names, i);

        PyObject *value = kw_values[i];

        CHECK_OBJECT(key);
        CHECK_OBJECT(value);

        DICT_SET_ITEM(named_args, key, value);
    }

    PyObject *result = (*call_slot)(called, pos_args, named_args);

    Py_DECREF(named_args);

    Py_LeaveRecursiveCall();

    CHECK_OBJECT_X(result);

    return Nuitka_CheckFunctionResult(tstate, called, result);
}
PyObject *CALL_METHODDESCR_WITH_SINGLE_ARG(PyThreadState *tstate, PyObject *called, PyObject *arg) {
    PyObject *const *args = &arg; // For easier code compatibility.
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 1);

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    assert(PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL));
    vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));
    assert(func != NULL);
    PyObject *result = func(called, args, 1, NULL);

#ifndef __NUITKA_NO_ASSERT__
    return Nuitka_CheckFunctionResult(tstate, called, result);
#else
    return result;
#endif
#else
    PyMethodDescrObject *called_descr = (PyMethodDescrObject *)called;
    PyMethodDef *method_def = called_descr->d_method;

    // Try to be fast about wrapping the arguments.
    int flags = method_def->ml_flags & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

    if (likely(flags & METH_NOARGS)) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result = (*method)(self, NULL);

#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    } else if ((flags & METH_O)) {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (1 given)",
                                            method_def->ml_name);
        return NULL;
    } else if (flags & METH_VARARGS) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result;

#if PYTHON_VERSION < 0x360
        if (flags & METH_KEYWORDS) {
            result = (*(PyCFunctionWithKeywords)method)(self, const_tuple_empty, NULL);
        } else {
            result = (*method)(self, const_tuple_empty);
        }
#else
        if (flags == (METH_VARARGS | METH_KEYWORDS)) {
            result = (*(PyCFunctionWithKeywords)method)(self, const_tuple_empty, NULL);
        } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
            result = (*(_PyCFunctionFast)method)(self, (PyObject **)args + 1, 0, NULL);
#else
            result = (*(_PyCFunctionFast)method)(self, &const_tuple_empty, 1);
#endif
        } else {
            result = (*method)(self, const_tuple_empty);
        }
#endif
#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 1);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    return result;
#endif
}
PyObject *CALL_METHODDESCR_WITH_ARGS2(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 2);

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    assert(PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL));
    vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));
    assert(func != NULL);
    PyObject *result = func(called, args, 2, NULL);

#ifndef __NUITKA_NO_ASSERT__
    return Nuitka_CheckFunctionResult(tstate, called, result);
#else
    return result;
#endif
#else
    PyMethodDescrObject *called_descr = (PyMethodDescrObject *)called;
    PyMethodDef *method_def = called_descr->d_method;

    // Try to be fast about wrapping the arguments.
    int flags = method_def->ml_flags & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

    if (unlikely(flags & METH_NOARGS)) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result = (*method)(self, NULL);

#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    } else if (unlikely(flags & METH_O)) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result = (*method)(self, args[1]);

#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    } else if (flags & METH_VARARGS) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result;

#if PYTHON_VERSION < 0x360
        PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 1);

        if (flags & METH_KEYWORDS) {
            result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
        } else {
            result = (*method)(self, pos_args);
        }

        Py_DECREF(pos_args);
#else
        if (flags == (METH_VARARGS | METH_KEYWORDS)) {
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 1);
            result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            Py_DECREF(pos_args);
        } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
            result = (*(_PyCFunctionFast)method)(self, (PyObject **)args + 1, 1, NULL);
#else
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 1);
            result = (*(_PyCFunctionFast)method)(self, &pos_args, 2);
            Py_DECREF(pos_args);
#endif
        } else {
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 1);
            result = (*method)(self, pos_args);
            Py_DECREF(pos_args);
        }
#endif
#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 2);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    return result;
#endif
}
PyObject *CALL_METHODDESCR_WITH_ARGS3(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 3);

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    assert(PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL));
    vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));
    assert(func != NULL);
    PyObject *result = func(called, args, 3, NULL);

#ifndef __NUITKA_NO_ASSERT__
    return Nuitka_CheckFunctionResult(tstate, called, result);
#else
    return result;
#endif
#else
    PyMethodDescrObject *called_descr = (PyMethodDescrObject *)called;
    PyMethodDef *method_def = called_descr->d_method;

    // Try to be fast about wrapping the arguments.
    int flags = method_def->ml_flags & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

    if (unlikely(flags & METH_NOARGS)) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result = (*method)(self, NULL);

#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    } else if (unlikely(flags & METH_O)) {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (3 given)",
                                            method_def->ml_name);
        return NULL;
    } else if (flags & METH_VARARGS) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result;

#if PYTHON_VERSION < 0x360
        PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 2);

        if (flags & METH_KEYWORDS) {
            result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
        } else {
            result = (*method)(self, pos_args);
        }

        Py_DECREF(pos_args);
#else
        if (flags == (METH_VARARGS | METH_KEYWORDS)) {
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 2);
            result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            Py_DECREF(pos_args);
        } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
            result = (*(_PyCFunctionFast)method)(self, (PyObject **)args + 1, 2, NULL);
#else
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 2);
            result = (*(_PyCFunctionFast)method)(self, &pos_args, 3);
            Py_DECREF(pos_args);
#endif
        } else {
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 2);
            result = (*method)(self, pos_args);
            Py_DECREF(pos_args);
        }
#endif
#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 3);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    return result;
#endif
}
PyObject *CALL_METHODDESCR_WITH_ARGS4(PyThreadState *tstate, PyObject *called, PyObject *const *args) {
    CHECK_OBJECT(called);
    CHECK_OBJECTS(args, 4);

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    assert(PyType_HasFeature(Py_TYPE(called), _Py_TPFLAGS_HAVE_VECTORCALL));
    vectorcallfunc func = *((vectorcallfunc *)(((char *)called) + Py_TYPE(called)->tp_vectorcall_offset));
    assert(func != NULL);
    PyObject *result = func(called, args, 4, NULL);

#ifndef __NUITKA_NO_ASSERT__
    return Nuitka_CheckFunctionResult(tstate, called, result);
#else
    return result;
#endif
#else
    PyMethodDescrObject *called_descr = (PyMethodDescrObject *)called;
    PyMethodDef *method_def = called_descr->d_method;

    // Try to be fast about wrapping the arguments.
    int flags = method_def->ml_flags & ~(METH_CLASS | METH_STATIC | METH_COEXIST);

    if (unlikely(flags & METH_NOARGS)) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result = (*method)(self, NULL);

#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    } else if (unlikely(flags & METH_O)) {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, "%s() takes exactly one argument (4 given)",
                                            method_def->ml_name);
        return NULL;
    } else if (flags & METH_VARARGS) {
        PyCFunction method = method_def->ml_meth;
        PyObject *self = args[0];

        PyObject *result;

#if PYTHON_VERSION < 0x360
        PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 3);

        if (flags & METH_KEYWORDS) {
            result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
        } else {
            result = (*method)(self, pos_args);
        }

        Py_DECREF(pos_args);
#else
        if (flags == (METH_VARARGS | METH_KEYWORDS)) {
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 3);
            result = (*(PyCFunctionWithKeywords)method)(self, pos_args, NULL);
            Py_DECREF(pos_args);
        } else if (flags == METH_FASTCALL) {
#if PYTHON_VERSION < 0x370
            result = (*(_PyCFunctionFast)method)(self, (PyObject **)args + 1, 3, NULL);
#else
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 3);
            result = (*(_PyCFunctionFast)method)(self, &pos_args, 4);
            Py_DECREF(pos_args);
#endif
        } else {
            PyObject *pos_args = MAKE_TUPLE(tstate, args + 1, 3);
            result = (*method)(self, pos_args);
            Py_DECREF(pos_args);
        }
#endif
#ifndef __NUITKA_NO_ASSERT__
        return Nuitka_CheckFunctionResult(tstate, called, result);
#else
        return result;
#endif
    }

#if 0
    PRINT_NEW_LINE();
    PRINT_STRING("FALLBACK");
    PRINT_ITEM(called);
    PRINT_NEW_LINE();
#endif

    PyObject *pos_args = MAKE_TUPLE(tstate, args, 4);

    PyObject *result = CALL_FUNCTION(tstate, called, pos_args, NULL);

    Py_DECREF(pos_args);

    return result;
#endif
}
PyObject *CALL_METHOD_NO_ARGS(PyThreadState *tstate, PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, called_object);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, called_object);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result =
                    Nuitka_CallMethodFunctionNoArgs(tstate, (struct Nuitka_FunctionObject const *)descr, source);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, called_object);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, descr);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_NO_ARGS(tstate, called_object);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionNoArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                       source);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, method);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_NO_ARGS(tstate, called_object);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, called_object);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, called_object);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, descr);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, called_object);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_SINGLE_ARG(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *arg) {
    PyObject *const *args = &arg; // For easier code compatibility.
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 1);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 1);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, descr, args[0]);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 1);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, method, args[0]);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, descr, args[0]);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, called_object, args[0]);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS2(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 2);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 2);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 2);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS2(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS3(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 3);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 3);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 3);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS3(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS4(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 4);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 4);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 4);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS4(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS5(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 5);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 5);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 5);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS5(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS6(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 6);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 6);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 6);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS6(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS7(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 7);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 7);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 7);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS7(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS8(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 8);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 8);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 8);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS8(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS9(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 9);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 9);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 9);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS9(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
PyObject *CALL_METHOD_WITH_ARGS10(PyThreadState *tstate, PyObject *source, PyObject *attr_name, PyObject *const *args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    CHECK_OBJECTS(args, 10);

    PyTypeObject *type = Py_TYPE(source);

    if (hasTypeGenericGetAttr(type)) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = Nuitka_TypeLookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

            if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && Nuitka_Descr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
                    Py_DECREF(called_object);
                    return result;
                }
            }
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0) {
                    tsize = -tsize;
                }
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = DICT_GET_ITEM1(tstate, dict, attr_name);

            if (called_object != NULL) {
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)descr,
                                                                    source, args, 10);
                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, descr, args);
            Py_DECREF(descr);
            return result;
        }

#if PYTHON_VERSION < 0x300
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 0x300
    else if (type == &PyInstance_Type) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attr_name != const_str_plain___dict__);
        assert(attr_name != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)called_object,
                                                        source, args, 10);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, method, args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
            }

        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "%s instance has no attribute '%s'",
                                                PyString_AS_STRING(source_instance->in_class->cl_name),
                                                PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args2[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(tstate, source_instance->in_class->cl_getattr, args2);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *descr = (*type->tp_getattro)(source, attr_name);

        if (unlikely(descr == NULL)) {
            return NULL;
        }

        descrgetfunc func = NULL;
        if (NuitkaType_HasFeatureClass(Py_TYPE(descr))) {
            func = Py_TYPE(descr)->tp_descr_get;

            if (func != NULL && Nuitka_Descr_IsData(descr)) {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                Py_DECREF(descr);

                if (unlikely(called_object == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
                Py_DECREF(called_object);
                return result;
            }
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, descr, args);
        Py_DECREF(descr);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_ARGS10(tstate, called_object, args);
        Py_DECREF(called_object);
        return result;
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                                            Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}

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
