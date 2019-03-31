//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

PyObject *callPythonFunction(PyObject *func, PyObject **args, int count) {
    PyCodeObject *co = (PyCodeObject *)PyFunction_GET_CODE(func);
    PyObject *globals = PyFunction_GET_GLOBALS(func);
    PyObject *argdefs = PyFunction_GET_DEFAULTS(func);

#if PYTHON_VERSION >= 300
    PyObject *kwdefs = PyFunction_GET_KW_DEFAULTS(func);

    if (kwdefs == NULL && argdefs == NULL && co->co_argcount == count &&
        co->co_flags == (CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE))
#else
    if (argdefs == NULL && co->co_argcount == count && co->co_flags == (CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE))
#endif
    {
        PyThreadState *tstate = PyThreadState_GET();
        CHECK_OBJECT(globals);

        PyFrameObject *frame = PyFrame_New(tstate, co, globals, NULL);

        if (unlikely(frame == NULL)) {
            return NULL;
        };

        for (int i = 0; i < count; i++) {
            frame->f_localsplus[i] = args[i];
            Py_INCREF(frame->f_localsplus[i]);
        }

        PyObject *result = PyEval_EvalFrameEx(frame, 0);

        // Frame release protects against recursion as it may lead to variable
        // destruction.
        ++tstate->recursion_depth;
        Py_DECREF(frame);
        --tstate->recursion_depth;

        return result;
    }

    PyObject **defaults = NULL;
    int nd = 0;

    if (argdefs != NULL) {
        defaults = &PyTuple_GET_ITEM(argdefs, 0);
        nd = (int)(Py_SIZE(argdefs));
    }

    PyObject *result = PyEval_EvalCodeEx(
#if PYTHON_VERSION >= 300
        (PyObject *)co,
#else
        co, // code object
#endif
        globals,  // globals
        NULL,     // no locals
        args,     // args
        count,    // argcount
        NULL,     // kwds
        0,        // kwcount
        defaults, // defaults
        nd,       // defcount
#if PYTHON_VERSION >= 300
        kwdefs,
#endif
        PyFunction_GET_CLOSURE(func));

    return result;
}

static PyObject *_fast_function_noargs(PyObject *func) {
    PyCodeObject *co = (PyCodeObject *)PyFunction_GET_CODE(func);
    PyObject *globals = PyFunction_GET_GLOBALS(func);
    PyObject *argdefs = PyFunction_GET_DEFAULTS(func);

#if PYTHON_VERSION >= 300
    PyObject *kwdefs = PyFunction_GET_KW_DEFAULTS(func);

    if (kwdefs == NULL && argdefs == NULL && co->co_argcount == 0 &&
        co->co_flags == (CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE))
#else
    if (argdefs == NULL && co->co_argcount == 0 && co->co_flags == (CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE))
#endif
    {
        PyThreadState *tstate = PyThreadState_GET();
        CHECK_OBJECT(globals);

        PyFrameObject *frame = PyFrame_New(tstate, co, globals, NULL);

        if (unlikely(frame == NULL)) {
            return NULL;
        };

        PyObject *result = PyEval_EvalFrameEx(frame, 0);

        // Frame release protects against recursion as it may lead to variable
        // destruction.
        ++tstate->recursion_depth;
        Py_DECREF(frame);
        --tstate->recursion_depth;

        return result;
    }

    PyObject **defaults = NULL;
    int nd = 0;

    if (argdefs != NULL) {
        defaults = &PyTuple_GET_ITEM(argdefs, 0);
        nd = (int)(Py_SIZE(argdefs));
    }

    PyObject *result = PyEval_EvalCodeEx(
#if PYTHON_VERSION >= 300
        (PyObject *)co,
#else
        co, // code object
#endif
        globals,  // globals
        NULL,     // no locals
        NULL,     // args
        0,        // argcount
        NULL,     // kwds
        0,        // kwcount
        defaults, // defaults
        nd,       // defcount
#if PYTHON_VERSION >= 300
        kwdefs,
#endif
        PyFunction_GET_CLOSURE(func));

    return result;
}

PyObject *CALL_FUNCTION_NO_ARGS(PyObject *called) {
    CHECK_OBJECT(called);

    if (Nuitka_Function_Check(called)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)called;

        PyObject *result;

        if (function->m_args_simple && 0 == function->m_args_positional_count) {
            result = function->m_c_code(function, NULL);
        } else if (function->m_args_simple && function->m_defaults_given == function->m_args_positional_count) {
            PyObject **python_pars = &PyTuple_GET_ITEM(function->m_defaults, 0);

            for (Py_ssize_t i = 0; i < function->m_defaults_given; i++) {
                Py_INCREF(python_pars[i]);
            }

            result = function->m_c_code(function, python_pars);
        } else {
#ifdef _MSC_VER
            PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
            PyObject *python_pars[function->m_args_overall_count];
#endif
            memset(python_pars, 0, function->m_args_overall_count * sizeof(PyObject *));

            if (parseArgumentsPos(function, python_pars, NULL, 0)) {
                result = function->m_c_code(function, python_pars);
            } else {
                result = NULL;
            }
        }

        Py_LeaveRecursiveCall();

        return result;
    } else if (Nuitka_Method_Check(called)) {
        struct Nuitka_MethodObject *method = (struct Nuitka_MethodObject *)called;

        // Unbound method without arguments, let the error path be slow.
        if (method->m_object != NULL) {
            if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
                return NULL;
            }

            struct Nuitka_FunctionObject *function = method->m_function;
            PyObject *result;

            if (function->m_args_simple && 1 == function->m_args_positional_count) {
                Py_INCREF(method->m_object);

                result = function->m_c_code(function, &method->m_object);
            } else if (function->m_args_simple && function->m_defaults_given == function->m_args_positional_count - 1) {
#ifdef _MSC_VER
                PyObject **python_pars = (PyObject **)_alloca(sizeof(PyObject *) * function->m_args_overall_count);
#else
                PyObject *python_pars[function->m_args_overall_count];
#endif
                python_pars[0] = method->m_object;
                memcpy(python_pars + 1, &PyTuple_GET_ITEM(function->m_defaults, 0),
                       sizeof(PyObject *) * function->m_defaults_given);

                for (Py_ssize_t i = 0; i < function->m_args_positional_count; i++) {
                    Py_INCREF(python_pars[i]);
                }

                result = function->m_c_code(function, python_pars);
            } else {
                result = Nuitka_CallMethodFunctionNoArgs(function, method->m_object);
            }

            Py_LeaveRecursiveCall();

            return result;
        }
    } else if (PyFunction_Check(called)) {
        return _fast_function_noargs(called);
    }

    return CALL_FUNCTION(called, const_tuple_empty, NULL);
}

PyObject *CALL_METHOD_WITH_POSARGS(PyObject *source, PyObject *attribute, PyObject *positional_args) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attribute);
    CHECK_OBJECT(positional_args);

#if PYTHON_VERSION < 300
    if (PyInstance_Check(source)) {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        // The special cases have their own variant on the code generation level
        // as we are called with constants only.
        assert(attribute != const_str_plain___dict__);
        assert(attribute != const_str_plain___class__);

        // Try the instance dict first.
        PyObject *called_object =
            GET_STRING_DICT_VALUE((PyDictObject *)source_instance->in_dict, (PyStringObject *)attribute);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            return CALL_FUNCTION_WITH_POSARGS(called_object, positional_args);
        }
        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attribute);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionPosArgs((struct Nuitka_FunctionObject const *)called_object, source,
                                                        &PyTuple_GET_ITEM(positional_args, 0),
                                                        PyTuple_GET_SIZE(positional_args));
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_WITH_POSARGS(method, positional_args);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_WITH_POSARGS(called_object, positional_args);
            }
        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            PyErr_Format(PyExc_AttributeError, "%s instance has no attribute '%s'",
                         PyString_AS_STRING(source_instance->in_class->cl_name), PyString_AS_STRING(attribute));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args[] = {source, attribute};

            called_object = CALL_FUNCTION_WITH_ARGS2(source_instance->in_class->cl_getattr, args);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_WITH_POSARGS(called_object, positional_args);
            Py_DECREF(called_object);
            return result;
        }
    } else
#endif
    {
        PyObject *called_object;

        PyTypeObject *type = Py_TYPE(source);

        if (type->tp_getattro != NULL) {
            called_object = (*type->tp_getattro)(source, attribute);
        } else if (type->tp_getattr != NULL) {
            called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attribute));
        } else {
            PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                         Nuitka_String_AsString_Unchecked(attribute));

            return NULL;
        }

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_WITH_POSARGS(called_object, positional_args);
        Py_DECREF(called_object);
        return result;
    }
}

PyObject *CALL_METHOD_NO_ARGS(PyObject *source, PyObject *attr_name) {
    CHECK_OBJECT(source);
    CHECK_OBJECT(attr_name);

    PyTypeObject *type = Py_TYPE(source);

    if (type->tp_getattro == PyObject_GenericGetAttr) {
        // Unfortunately this is required, although of cause rarely necessary.
        if (unlikely(type->tp_dict == NULL)) {
            if (unlikely(PyType_Ready(type) < 0)) {
                return NULL;
            }
        }

        PyObject *descr = _PyType_Lookup(type, attr_name);
        descrgetfunc func = NULL;

        if (descr != NULL) {
            Py_INCREF(descr);

#if PYTHON_VERSION < 300
            if (PyType_HasFeature(Py_TYPE(descr), Py_TPFLAGS_HAVE_CLASS)) {
#endif
                func = Py_TYPE(descr)->tp_descr_get;

                if (func != NULL && PyDescr_IsData(descr)) {
                    PyObject *called_object = func(descr, source, (PyObject *)type);
                    Py_DECREF(descr);

                    PyObject *result = CALL_FUNCTION_NO_ARGS(called_object);
                    Py_DECREF(called_object);
                    return result;
                }
#if PYTHON_VERSION < 300
            }
#endif
        }

        Py_ssize_t dictoffset = type->tp_dictoffset;
        PyObject *dict = NULL;

        if (dictoffset != 0) {
            // Negative dictionary offsets have special meaning.
            if (dictoffset < 0) {
                Py_ssize_t tsize;
                size_t size;

                tsize = ((PyVarObject *)source)->ob_size;
                if (tsize < 0)
                    tsize = -tsize;
                size = _PyObject_VAR_SIZE(type, tsize);

                dictoffset += (long)size;
            }

            PyObject **dictptr = (PyObject **)((char *)source + dictoffset);
            dict = *dictptr;
        }

        if (dict != NULL) {
            CHECK_OBJECT(dict);

            Py_INCREF(dict);

            PyObject *called_object = PyDict_GetItem(dict, attr_name);

            if (called_object != NULL) {
                Py_INCREF(called_object);
                Py_XDECREF(descr);
                Py_DECREF(dict);

                PyObject *result = CALL_FUNCTION_NO_ARGS(called_object);
                Py_DECREF(called_object);
                return result;
            }

            Py_DECREF(dict);
        }

        if (func != NULL) {
            if (func == Nuitka_Function_Type.tp_descr_get) {
                PyObject *result = Nuitka_CallMethodFunctionNoArgs((struct Nuitka_FunctionObject const *)descr, source);

                Py_DECREF(descr);

                return result;
            } else {
                PyObject *called_object = func(descr, source, (PyObject *)type);
                CHECK_OBJECT(called_object);

                Py_DECREF(descr);

                PyObject *result = CALL_FUNCTION_NO_ARGS(called_object);
                Py_DECREF(called_object);

                return result;
            }
        }

        if (descr != NULL) {
            CHECK_OBJECT(descr);

            PyObject *result = CALL_FUNCTION_NO_ARGS(descr);
            Py_DECREF(descr);

            return result;
        }

#if PYTHON_VERSION < 300
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                     PyString_AS_STRING(attr_name));
#else
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%U'", type->tp_name, attr_name);
#endif
        return NULL;
    }
#if PYTHON_VERSION < 300
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
            return CALL_FUNCTION_NO_ARGS(called_object);
        }

        // Then check the class dictionaries.
        called_object = FIND_ATTRIBUTE_IN_CLASS(source_instance->in_class, attr_name);

        // Note: The "called_object" was found without taking a reference,
        // so we need not release it in this branch.
        if (called_object != NULL) {
            descrgetfunc descr_get = Py_TYPE(called_object)->tp_descr_get;

            if (descr_get == Nuitka_Function_Type.tp_descr_get) {
                return Nuitka_CallMethodFunctionNoArgs((struct Nuitka_FunctionObject const *)called_object, source);
            } else if (descr_get != NULL) {
                PyObject *method = descr_get(called_object, source, (PyObject *)source_instance->in_class);

                if (unlikely(method == NULL)) {
                    return NULL;
                }

                PyObject *result = CALL_FUNCTION_NO_ARGS(method);
                Py_DECREF(method);
                return result;
            } else {
                return CALL_FUNCTION_NO_ARGS(called_object);
            }
        } else if (unlikely(source_instance->in_class->cl_getattr == NULL)) {
            PyErr_Format(PyExc_AttributeError, "%s instance has no attribute '%s'",
                         PyString_AS_STRING(source_instance->in_class->cl_name), PyString_AS_STRING(attr_name));

            return NULL;
        } else {
            // Finally allow the "__getattr__" override to provide it or else
            // it's an error.

            PyObject *args[] = {source, attr_name};

            called_object = CALL_FUNCTION_WITH_ARGS2(source_instance->in_class->cl_getattr, args);

            if (unlikely(called_object == NULL)) {
                return NULL;
            }

            PyObject *result = CALL_FUNCTION_NO_ARGS(called_object);
            Py_DECREF(called_object);
            return result;
        }
    }
#endif
    else if (type->tp_getattro != NULL) {
        PyObject *called_object = (*type->tp_getattro)(source, attr_name);

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_NO_ARGS(called_object);
        Py_DECREF(called_object);
        return result;
    } else if (type->tp_getattr != NULL) {
        PyObject *called_object = (*type->tp_getattr)(source, (char *)Nuitka_String_AsString_Unchecked(attr_name));

        if (unlikely(called_object == NULL)) {
            return NULL;
        }

        PyObject *result = CALL_FUNCTION_NO_ARGS(called_object);
        Py_DECREF(called_object);
        return result;
    } else {
        PyErr_Format(PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name,
                     Nuitka_String_AsString_Unchecked(attr_name));

        return NULL;
    }
}
