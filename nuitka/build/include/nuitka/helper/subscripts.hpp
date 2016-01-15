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
#ifndef __NUITKA_HELPER_SUBSCRIPTS_H__
#define __NUITKA_HELPER_SUBSCRIPTS_H__

extern PyObject *BUILTIN_CHR( unsigned char c );

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SUBSCRIPT_CONST( PyObject *source, PyObject *const_subscript, Py_ssize_t int_subscript )
{
    CHECK_OBJECT( source );
    CHECK_OBJECT( const_subscript );

    PyTypeObject *type = Py_TYPE( source );
    PyMappingMethods *mapping_methods = type->tp_as_mapping;

    PyObject *result;

    if ( mapping_methods && mapping_methods->mp_subscript )
    {
        if ( PyList_CheckExact( source ) )
        {
            Py_ssize_t list_size = PyList_GET_SIZE( source );

            if ( int_subscript < 0 )
            {
                if ( -int_subscript > list_size )
                {
                    PyErr_Format( PyExc_IndexError, "list index out of range" );
                    return NULL;
                }

                int_subscript += list_size;
            }
            else
            {
                if ( int_subscript >= list_size )
                {
                    PyErr_Format( PyExc_IndexError, "list index out of range" );
                    return NULL;
                }
            }

            return INCREASE_REFCOUNT( ((PyListObject *)source)->ob_item[ int_subscript ] );
        }
#if PYTHON_VERSION < 300
        else if ( PyString_CheckExact( source ) )
        {
            Py_ssize_t string_size = PyString_GET_SIZE( source );

            if ( int_subscript < 0 )
            {
                if ( -int_subscript > string_size )
                {
                    PyErr_Format( PyExc_IndexError, "string index out of range" );
                    return NULL;
                }

                int_subscript += string_size;
            }
            else
            {
                if ( int_subscript >= string_size )
                {
                    PyErr_Format( PyExc_IndexError, "string index out of range" );
                    return NULL;
                }
            }

            unsigned char c = ((PyStringObject *)source)->ob_sval[ int_subscript ];
            return BUILTIN_CHR( c );
        }
#else
        else if ( PyUnicode_CheckExact( source ) )
        {
            if ( int_subscript < 0 )
            {
#if PYTHON_VERSION < 330
                int_subscript += PyUnicode_GET_SIZE( source );
#else
                int_subscript += PyUnicode_GET_LENGTH( source );
#endif
            }

            result = type->tp_as_sequence->sq_item( source, int_subscript );
        }
#endif
        else
        {
            result = mapping_methods->mp_subscript( source, const_subscript );
        }
    }
    else if ( type->tp_as_sequence )
    {
        result = PySequence_GetItem( source, int_subscript );
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
#if PYTHON_VERSION < 270
            "'%s' object is unsubscriptable",
#elif PYTHON_VERSION >= 300 || PYTHON_VERSION <= 272
            "'%s' object is not subscriptable",
#else
            "'%s' object has no attribute '__getitem__'",
#endif
            Py_TYPE( source )->tp_name
        );
        return NULL;
    }

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SUBSCRIPT( PyObject *source, PyObject *subscript )
{
    CHECK_OBJECT( source );
    CHECK_OBJECT( subscript );

    PyTypeObject *type = Py_TYPE( source );
    PyMappingMethods *mapping = type->tp_as_mapping;

    PyObject *result;

    if ( mapping != NULL && mapping->mp_subscript != NULL )
    {
        result = mapping->mp_subscript( source, subscript );
    }
    else if ( type->tp_as_sequence != NULL )
    {
        if ( PyIndex_Check( subscript ) )
        {
            Py_ssize_t index = PyNumber_AsSsize_t( subscript, NULL );

            if ( index == -1 && ERROR_OCCURRED() )
            {
                return NULL;
            }

            result = PySequence_GetItem( source, index );
        }
        else if ( type->tp_as_sequence->sq_item )
        {
            PyErr_Format( PyExc_TypeError, "sequence index must be integer, not '%s'", Py_TYPE( subscript )->tp_name );
            return NULL;
        }
        else
        {
            PyErr_Format(
                PyExc_TypeError,
#if PYTHON_VERSION < 270
                "'%s' object is unsubscriptable",
#elif PYTHON_VERSION >= 300 || PYTHON_VERSION <= 272
                "'%s' object is not subscriptable",
#else
                "'%s' object has no attribute '__getitem__'",
#endif
                Py_TYPE( source )->tp_name
            );
            return NULL;
        }
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
#if PYTHON_VERSION < 270
            "'%s' object is unsubscriptable",
#elif PYTHON_VERSION >= 300 || PYTHON_VERSION <= 272
            "'%s' object is not subscriptable",
#else
            "'%s' object has no attribute '__getitem__'",
#endif
            Py_TYPE( source )->tp_name
        );

        return NULL;
    }

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static bool SET_SUBSCRIPT_CONST( PyObject *target, PyObject *subscript, Py_ssize_t int_subscript, PyObject *value )
{
    CHECK_OBJECT( value );
    CHECK_OBJECT( target );
    CHECK_OBJECT( subscript );

    PyMappingMethods *mapping_methods = Py_TYPE( target )->tp_as_mapping;

    if ( mapping_methods != NULL && mapping_methods->mp_ass_subscript )
    {
        if ( PyList_CheckExact( target ) )
        {
            Py_ssize_t list_size = PyList_GET_SIZE( target );

            if ( int_subscript < 0 )
            {
                if ( -int_subscript > list_size )
                {
                    PyErr_Format(
                        PyExc_IndexError,
                        "list assignment index out of range"
                    );

                    return false;
                }

                int_subscript += list_size;
            }

            PyListObject *target_list = (PyListObject *)target;

            PyObject *old_value = target_list->ob_item[ int_subscript ];
            target_list->ob_item[ int_subscript ] = INCREASE_REFCOUNT( value );
            Py_DECREF( old_value );

            return true;
        }
        else
        {
            int res = mapping_methods->mp_ass_subscript( target, subscript, value );

            if (unlikely( res == -1 ))
            {
                return false;
            }

            return true;
        }
    }
    else if ( Py_TYPE( target )->tp_as_sequence )
    {
        if ( PyIndex_Check( subscript ) )
        {
            Py_ssize_t key_value = PyNumber_AsSsize_t( subscript, PyExc_IndexError );

            if ( key_value == -1 )
            {
                if ( ERROR_OCCURRED() )
                {
                    return false;
                }
            }

            return SEQUENCE_SETITEM( target, key_value, value );
        }
        else if ( Py_TYPE( target )->tp_as_sequence->sq_ass_item )
        {
            PyErr_Format(
                PyExc_TypeError,
                "sequence index must be integer, not '%s'",
                Py_TYPE( subscript )->tp_name
            );

            return false;
        }
        else
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object does not support item assignment",
                Py_TYPE( target )->tp_name
            );

            return false;
        }
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object does not support item assignment",
            Py_TYPE( target )->tp_name
        );

        return false;
    }
}

NUITKA_MAY_BE_UNUSED static bool SET_SUBSCRIPT( PyObject *target, PyObject *subscript, PyObject *value )
{
    CHECK_OBJECT( value );
    CHECK_OBJECT( target );
    CHECK_OBJECT( subscript );

    PyMappingMethods *mapping_methods = Py_TYPE( target )->tp_as_mapping;

    if ( mapping_methods != NULL && mapping_methods->mp_ass_subscript )
    {
        int res = mapping_methods->mp_ass_subscript( target, subscript, value );

        if (unlikely( res == -1 ))
        {
            return false;
        }
    }
    else if ( Py_TYPE( target )->tp_as_sequence )
    {
        if ( PyIndex_Check( subscript ) )
        {
            Py_ssize_t key_value = PyNumber_AsSsize_t( subscript, PyExc_IndexError );

            if ( key_value == -1 )
            {
                if ( ERROR_OCCURRED() )
                {
                    return false;
                }
            }

            return SEQUENCE_SETITEM( target, key_value, value );
        }
        else if ( Py_TYPE( target )->tp_as_sequence->sq_ass_item )
        {
            PyErr_Format(
                PyExc_TypeError,
                "sequence index must be integer, not '%s'",
                Py_TYPE( subscript )->tp_name
            );

            return false;
        }
        else
        {
            PyErr_Format(
                PyExc_TypeError,
                "'%s' object does not support item assignment",
                Py_TYPE( target )->tp_name
            );

            return false;
        }
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object does not support item assignment",
            Py_TYPE( target )->tp_name
        );

        return false;
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static bool DEL_SUBSCRIPT( PyObject *target, PyObject *subscript )
{
    CHECK_OBJECT( target );
    CHECK_OBJECT( subscript );

    int status = PyObject_DelItem( target, subscript );

    if (unlikely( status == -1 ))
    {
        return false;
    }

    return true;
}

#endif
