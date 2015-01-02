//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_ATTRIBUTES_H__
#define __NUITKA_HELPER_ATTRIBUTES_H__

#if PYTHON_VERSION < 300
NUITKA_MAY_BE_UNUSED static PyObject *FIND_ATTRIBUTE_IN_CLASS( PyClassObject *klass, PyObject *attr_name )
{
    PyObject *result = GET_STRING_DICT_VALUE( (PyDictObject *)klass->cl_dict, (PyStringObject *)attr_name );

    if ( result == NULL )
    {
        Py_ssize_t base_count = PyTuple_Size( klass->cl_bases );

        for ( Py_ssize_t i = 0; i < base_count; i++ )
        {
            result = FIND_ATTRIBUTE_IN_CLASS( (PyClassObject *)PyTuple_GetItem( klass->cl_bases, i ), attr_name );

            if ( result )
            {
                break;
            }
        }
    }

    return result;
}
#endif

#if PYTHON_VERSION < 300
extern PyObject *CALL_FUNCTION_WITH_ARGS2( PyObject *called, PyObject *arg1, PyObject *arg2 );


static PyObject *LOOKUP_INSTANCE( PyObject *source, PyObject *attr_name )
{
    assertObject( source );
    assertObject( attr_name );

    assert( PyInstance_Check( source ) );
    assert( PyString_Check( attr_name ) );

    PyInstanceObject *source_instance = (PyInstanceObject *)source;

    // TODO: The special cases should get their own SET_ATTRIBUTE variant on the
    // code generation level as SET_ATTRIBUTE is called with constants only.
    assert( attr_name != const_str_plain___dict__ );
    assert( attr_name != const_str_plain___class__ );

    // Try the instance dict first.
    PyObject *result = GET_STRING_DICT_VALUE( (PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name );

    if ( result )
    {
        return INCREASE_REFCOUNT( result );
    }

    // Next see if a class has it
    result = FIND_ATTRIBUTE_IN_CLASS( source_instance->in_class, attr_name );

    if ( result )
    {
        descrgetfunc func = Py_TYPE( result )->tp_descr_get;

        if ( func )
        {
            result = func( result, source, (PyObject *)source_instance->in_class );

            if (unlikely( result == NULL ))
            {
                return NULL;
            }

            assertObject( result );

            return result;
        }
        else
        {
            return INCREASE_REFCOUNT( result );
        }
    }
    else if ( ERROR_OCCURRED() )
    {
        if ( PyErr_ExceptionMatches( PyExc_AttributeError ) )
        {
            PyErr_Clear();
        }
        else
        {
            return NULL;
        }
    }

    // Finally allow a __getattr__ to handle it or else it's an error.
    if (unlikely( source_instance->in_class->cl_getattr == NULL ))
    {
        PyErr_Format( PyExc_AttributeError, "%s instance has no attribute '%s'", PyString_AS_STRING( source_instance->in_class->cl_name ), PyString_AS_STRING( attr_name ) );

        return NULL;
    }
    else
    {
        return CALL_FUNCTION_WITH_ARGS2(
            source_instance->in_class->cl_getattr,
            source,
            attr_name
        );
    }
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_ATTRIBUTE( PyObject *source, PyObject *attr_name )
{
    assertObject( source );
    assertObject( attr_name );

#if PYTHON_VERSION < 300
    if ( PyInstance_Check( source ) )
    {
        PyObject *result = LOOKUP_INSTANCE( source, attr_name );
        return result;
    }
    else
#endif
    {
        PyTypeObject *type = Py_TYPE( source );

        if ( type->tp_getattro != NULL )
        {
            PyObject *result = (*type->tp_getattro)( source, attr_name );
            return result;
        }
        else if ( type->tp_getattr != NULL )
        {
            PyObject *result = (*type->tp_getattr)( source, Nuitka_String_AsString_Unchecked( attr_name ) );
            return result;
        }
        else
        {
            PyErr_Format( PyExc_AttributeError, "'%s' object has no attribute '%s'", type->tp_name, Nuitka_String_AsString_Unchecked( attr_name ) );
            return NULL;
        }
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_ATTRIBUTE_DICT_SLOT( PyObject *source )
{
    assertObject( source );

#if PYTHON_VERSION < 300
    if (likely( PyInstance_Check( source ) ))
    {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        return INCREASE_REFCOUNT( source_instance->in_dict );
    }
    else
#endif
    {
        PyTypeObject *type = Py_TYPE( source );

        if ( type->tp_getattro != NULL )
        {
            PyObject *result = (*type->tp_getattro)( source, const_str_plain___dict__ );

            if (unlikely( result == NULL ))
            {
                return NULL;
            }

            assertObject( result );
            return result;
        }
        else if ( type->tp_getattr != NULL )
        {
            PyObject *result = (*type->tp_getattr)( source, (char *)"__dict__" );

            if (unlikely( result == NULL ))
            {
                return NULL;
            }

            assertObject( result );
            return result;
        }
        else
        {
            PyErr_Format( PyExc_AttributeError, "'%s' object has no attribute '__dict__'", type->tp_name );
            return NULL;
        }
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_ATTRIBUTE_CLASS_SLOT( PyObject *source )
{
    assertObject( source );

#if PYTHON_VERSION < 300
    if (likely( PyInstance_Check( source ) ))
    {
        PyInstanceObject *source_instance = (PyInstanceObject *)source;

        return INCREASE_REFCOUNT( (PyObject *)source_instance->in_class );
    }
    else
#endif
    {
        PyTypeObject *type = Py_TYPE( source );

        if ( type->tp_getattro != NULL )
        {
            PyObject *result = (*type->tp_getattro)( source, const_str_plain___class__ );

            if (unlikely( result == NULL ))
            {
                return NULL;
            }

            assertObject( result );
            return result;
        }
        else if ( type->tp_getattr != NULL )
        {
            PyObject *result = (*type->tp_getattr)( source, (char *)"__class__" );

            if (unlikely( result == NULL ))
            {
                return NULL;
            }

            assertObject( result );
            return result;
        }
        else
        {
            PyErr_Format( PyExc_AttributeError, "'%s' object has no attribute '__class__'", type->tp_name );
            return NULL;
        }
    }
}


NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_HASATTR( PyObject *source, PyObject *attr_name )
{
    assertObject( source );
    assertObject( attr_name );

    int res = PyObject_HasAttr( source, attr_name );

    if (unlikely( res == -1 ))
    {
        return NULL;
    }

    return BOOL_FROM(res == 1);
}

#if PYTHON_VERSION < 300
extern PyObject *CALL_FUNCTION_WITH_ARGS3( PyObject *called, PyObject *arg1, PyObject *arg2, PyObject *arg3 );

static bool SET_INSTANCE( PyObject *target, PyObject *attr_name, PyObject *value )
{
    assertObject( target );
    assertObject( attr_name );
    assertObject( value );

    assert( PyInstance_Check( target ) );
    assert( PyString_Check( attr_name ) );

    PyInstanceObject *target_instance = (PyInstanceObject *)target;

    // The special cases should get their own SET_ATTRIBUTE_xxxx_SLOT variants
    // on the code generation level as SET_ATTRIBUTE is called with constants
    // only.
    assert( attr_name != const_str_plain___dict__ );
    assert( attr_name != const_str_plain___class__ );

    if ( target_instance->in_class->cl_setattr != NULL )
    {
        PyObject *result = CALL_FUNCTION_WITH_ARGS3(
            target_instance->in_class->cl_setattr,
            target, attr_name, value
        );

        if (unlikely( result == NULL ))
        {
            return false;
        }

        Py_DECREF( result );

        return true;
    }
    else
    {
        int status = PyDict_SetItem(
            target_instance->in_dict,
            attr_name,
            value
        );

        if (unlikely( status != 0 ))
        {
            return false;
        }

        return true;
    }
}
#endif

NUITKA_MAY_BE_UNUSED static bool SET_ATTRIBUTE( PyObject *target, PyObject *attr_name, PyObject *value )
{
    assertObject( target );
    assertObject( attr_name );
    assertObject( value );

#if PYTHON_VERSION < 300
    if ( PyInstance_Check( target ) )
    {
        return SET_INSTANCE( target, attr_name, value );
    }
    else
#endif
    {
        PyTypeObject *type = Py_TYPE( target );

        if ( type->tp_setattro != NULL )
        {
            int status = (*type->tp_setattro)( target, attr_name, value );

            if (unlikely( status == -1 ))
            {
                return false;
            }
        }
        else if ( type->tp_setattr != NULL )
        {
            int status = (*type->tp_setattr)( target, Nuitka_String_AsString_Unchecked( attr_name ), value );

            if (unlikely( status == -1 ))
            {
                return false;
            }
        }
        else if ( type->tp_getattr == NULL && type->tp_getattro == NULL )
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object has no attributes (assign to %s)",
                type->tp_name,
                Nuitka_String_AsString_Unchecked( attr_name )
            );

            return false;
        }
        else
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object has only read-only attributes (assign to %s)",
                type->tp_name,
                Nuitka_String_AsString_Unchecked( attr_name )
            );

            return false;
        }
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static bool SET_ATTRIBUTE_DICT_SLOT( PyObject *target, PyObject *value )
{
    assertObject( target );
    assertObject( value );

#if PYTHON_VERSION < 300
    if ( likely( PyInstance_Check( target ) ))
    {
        PyInstanceObject *target_instance = (PyInstanceObject *)target;

        if (unlikely( !PyDict_Check( value ) ))
        {
            PyErr_SetString( PyExc_TypeError, "__dict__ must be set to a dictionary" );
            return false;
        }

        PyObject *old = target_instance->in_dict;
        target_instance->in_dict = INCREASE_REFCOUNT( value );
        Py_DECREF( old );
    }
    else
#endif
    {
        PyTypeObject *type = Py_TYPE( target );

        if ( type->tp_setattro != NULL )
        {
            int status = (*type->tp_setattro)( target, const_str_plain___dict__, value );

            if (unlikely( status == -1 ))
            {
                return false;
            }
        }
        else if ( type->tp_setattr != NULL )
        {
            int status = (*type->tp_setattr)( target, (char *)"__dict__", value );

            if (unlikely( status == -1 ))
            {
                return false;
            }
        }
        else if ( type->tp_getattr == NULL && type->tp_getattro == NULL )
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object has no attributes (assign to __dict__)",
                type->tp_name
            );

            return false;
        }
        else
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object has only read-only attributes (assign to __dict__)",
                type->tp_name
            );

            return false;
        }
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static bool SET_ATTRIBUTE_CLASS_SLOT( PyObject *target, PyObject *value )
{
    assertObject( target );
    assertObject( value );

#if PYTHON_VERSION < 300
    if (likely( PyInstance_Check( target ) ))
    {
        PyInstanceObject *target_instance = (PyInstanceObject *)target;

        if (unlikely( !PyClass_Check( value ) ))
        {
            PyErr_SetString( PyExc_TypeError, "__class__ must be set to a class" );
            return false;
        }

        PyObject *old = (PyObject *)( target_instance->in_class );
        target_instance->in_class = (PyClassObject *)INCREASE_REFCOUNT( value );
        Py_DECREF( old );
    }
    else
#endif
    {
        PyTypeObject *type = Py_TYPE( target );

        if ( type->tp_setattro != NULL )
        {
            int status = (*type->tp_setattro)( target, const_str_plain___class__, value );

            if (unlikely( status == -1 ))
            {
                return false;
            }
        }
        else if ( type->tp_setattr != NULL )
        {
            int status = (*type->tp_setattr)( target, (char *)"__class__", value );

            if (unlikely( status == -1 ))
            {
                return false;
            }
        }
        else if ( type->tp_getattr == NULL && type->tp_getattro == NULL )
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object has no attributes (assign to __class__)",
                type->tp_name
            );

            return false;
        }
        else
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object has only read-only attributes (assign to __class__)",
                type->tp_name
            );

            return false;
        }
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SPECIAL( PyObject *source, PyObject *attr_name )
{
#if PYTHON_VERSION < 300
    if ( PyInstance_Check( source ) )
    {
        return LOOKUP_INSTANCE( source, attr_name );
    }
#endif

    // TODO: There is heavy optimization in CPython to avoid it. Potentially
    // that's worth it to imitate that.

    PyObject *result = _PyType_Lookup( Py_TYPE( source ), attr_name );

    if (likely( result ))
    {
        descrgetfunc func = Py_TYPE( result )->tp_descr_get;

        if ( func == NULL )
        {
            return INCREASE_REFCOUNT( result );
        }
        else
        {
            PyObject *func_result = func( result, source, (PyObject *)( Py_TYPE( source ) ) );

            if (unlikely( func_result == NULL ))
            {
                return NULL;
            }

            assertObject( func_result );
            return func_result;
        }
    }

    PyErr_SetObject( PyExc_AttributeError, attr_name );
    return NULL;
}

// Necessary to abstract the with statement lookup difference between
// pre-Python2.7 and others. Since Python 2.7 the code does no full attribute
// lookup anymore, but instead treats enter and exit as specials.
NUITKA_MAY_BE_UNUSED static inline PyObject *LOOKUP_WITH_ENTER( PyObject *source )
{
#if PYTHON_VERSION < 270
    return LOOKUP_ATTRIBUTE( source, const_str_plain___enter__ );
#else
    return LOOKUP_SPECIAL( source, const_str_plain___enter__ );
#endif
}

NUITKA_MAY_BE_UNUSED static inline PyObject *LOOKUP_WITH_EXIT( PyObject *source )
{
#if PYTHON_VERSION < 270
    return LOOKUP_ATTRIBUTE( source, const_str_plain___exit__ );
#else
    return LOOKUP_SPECIAL( source, const_str_plain___exit__ );
#endif
}


#endif
