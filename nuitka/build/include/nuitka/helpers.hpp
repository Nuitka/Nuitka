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
#ifndef __NUITKA_HELPERS_H__
#define __NUITKA_HELPERS_H__

#define _DEBUG_FRAME 0
#define _DEBUG_REFRAME 0
#define _DEBUG_EXCEPTIONS 0

extern PyObject *const_tuple_empty;
extern PyObject *const_str_plain___dict__;
extern PyObject *const_str_plain___class__;
extern PyObject *const_str_plain___enter__;
extern PyObject *const_str_plain___exit__;

// From CPython, to allow us quick access to the dictionary of an module, the
// structure is normally private, but we need it for quick access to the module
// dictionary.
typedef struct {
    PyObject_HEAD
    PyObject *md_dict;
} PyModuleObject;

extern bool PRINT_ITEM_TO( PyObject *file, PyObject *object );
extern bool PRINT_ITEM( PyObject *object );
extern bool PRINT_NEW_LINE( void );
extern bool PRINT_STRING( char const * );
extern bool PRINT_NULL( void );
static PyObject *INCREASE_REFCOUNT( PyObject *object );
static PyObject *INCREASE_REFCOUNT_X( PyObject *object );

// Helper to check that an object is valid and has positive reference count.
static inline void assertObject( PyObject *value )
{
    assert( value != NULL );
    assert( Py_REFCNT( value ) > 0 );
}

static inline void assertObject( PyTracebackObject *value )
{
    assertObject( (PyObject *)value );
}

// Due to ABI issues, it seems that on Windows the symbols used by
// _PyObject_GC_TRACK are not exported and we need to use a function that does
// it instead.
#if defined( _WIN32 )
#define Nuitka_GC_Track PyObject_GC_Track
#define Nuitka_GC_UnTrack PyObject_GC_UnTrack
#else
#define Nuitka_GC_Track _PyObject_GC_TRACK
#define Nuitka_GC_UnTrack _PyObject_GC_UNTRACK
#endif

#include "nuitka/variables_temporary.hpp"
#include "nuitka/exceptions.hpp"

// For the MAKE_TUPLE macros.
#include "__helpers.hpp"

// Helper functions for reference count handling in the fly.
NUITKA_MAY_BE_UNUSED static PyObject *INCREASE_REFCOUNT( PyObject *object )
{
    assertObject( object );

    Py_INCREF( object );

    return object;
}

NUITKA_MAY_BE_UNUSED static PyObject *INCREASE_REFCOUNT_X( PyObject *object )
{
    Py_XINCREF( object );

    return object;
}

NUITKA_MAY_BE_UNUSED static PyObject *DECREASE_REFCOUNT( PyObject *object )
{
    assertObject( object );

    Py_DECREF( object );

    return object;
}

#include "printing.hpp"

#include "nuitka/helper/boolean.hpp"

#include "nuitka/helper/dictionaries.hpp"


#if PYTHON_VERSION >= 300
static char *_PyUnicode_AS_STRING( PyObject *unicode )
{
#if PYTHON_VERSION < 330
    PyObject *bytes = _PyUnicode_AsDefaultEncodedString( unicode, NULL );

    if (unlikely( bytes == NULL ))
    {
        return NULL;
    }

    return PyBytes_AS_STRING( bytes );
#else
    return PyUnicode_AsUTF8( unicode );
#endif
}
#endif

#include "nuitka/helper/raising.hpp"

#include "helper/operations.hpp"

#include "nuitka/helper/richcomparisons.hpp"
#include "nuitka/helper/sequences.hpp"

static inline bool Nuitka_Function_Check( PyObject *object );
static inline PyObject *Nuitka_Function_GetName( PyObject *object );

static inline bool Nuitka_Generator_Check( PyObject *object );
static inline PyObject *Nuitka_Generator_GetName( PyObject *object );

#include "nuitka/calling.hpp"


NUITKA_MAY_BE_UNUSED static PyObject *TO_FLOAT( PyObject *value )
{
    PyObject *result;

#if PYTHON_VERSION < 300
    if ( PyString_CheckExact( value ) )
    {
        result = PyFloat_FromString( value, NULL );
    }
#else
    if ( PyUnicode_CheckExact( value ) )
    {
        result = PyFloat_FromString( value );
    }
#endif
    else
    {
        result = PyNumber_Float( value );
    }

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *TO_INT2( PyObject *value, PyObject *base )
{
    // TODO: Need to check if 3.4 is really the first version to do this.
#if PYTHON_VERSION < 340
    long base_int = PyInt_AsLong( base );
#else
    Py_ssize_t base_int = PyNumber_AsSsize_t( base, NULL );
#endif

    if (unlikely( base_int == -1 ))
    {
        if (likely( ERROR_OCCURED() ))
        {
#if PYTHON_VERSION >= 300
            if ( PyErr_ExceptionMatches( PyExc_OverflowError ) )
            {
                PyErr_Format(
                        PyExc_ValueError,
#if PYTHON_VERSION < 324
                        "int() arg 2 must be >= 2 and <= 36"
#else
                        "int() base must be >= 2 and <= 36"
#endif
                );
            }
#endif
            return NULL;
        }
    }

#if PYTHON_VERSION >= 300
    if (unlikely( ( base_int != 0 && base_int < 2 ) || base_int > 36 ))
    {
        PyErr_Format(
                PyExc_ValueError,
#if PYTHON_VERSION < 324
                "int() arg 2 must be >= 2 and <= 36"
#else
                "int() base must be >= 2 and <= 36"
#endif
        );

        return NULL;
    }
#endif

#if PYTHON_VERSION < 300
    if (unlikely( !Nuitka_String_Check( value ) && !PyUnicode_Check( value ) ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "int() can't convert non-string with explicit base"
        );
        return NULL;
    }

    char *value_str = Nuitka_String_AsString( value );
    if (unlikely( value_str == NULL ))
    {
        return NULL;
    }

    PyObject *result = PyInt_FromString( value_str, NULL, base_int );
    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
#else
    if ( PyUnicode_Check( value ) )
    {
#if PYTHON_VERSION < 330
        char *value_str = Nuitka_String_AsString( value );

        if (unlikely( value_str == NULL ))
        {
            return NULL;
        }

        PyObject *result = PyInt_FromString( value_str, NULL, base_int );

        if (unlikely( result == NULL ))
        {
            return NULL;
        }

        return result;
#else
        return PyLong_FromUnicodeObject( value, (int)base_int );
#endif
    }
    else if ( PyBytes_Check( value ) || PyByteArray_Check( value ) )
    {
        // Check for "NUL" as PyLong_FromString has no length parameter,
        Py_ssize_t size = Py_SIZE( value );
        char *value_str;

        if ( PyByteArray_Check( value ) )
        {
            value_str = PyByteArray_AS_STRING( value );
        }
        else
        {
            value_str = PyBytes_AS_STRING( value );
        }

        if ( strlen( value_str ) != (size_t)size || size == 0 )
        {
            PyErr_Format(
                PyExc_ValueError,
                "invalid literal for int() with base %d: %R",
                base_int,
                value
            );

            return NULL;
        }

        return PyInt_FromString( value_str, NULL, (int)base_int );
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "int() can't convert non-string with explicit base"
        );
        return NULL;
    }
#endif
}

#if PYTHON_VERSION < 300
// Note: Python3 uses TO_INT2 function.
NUITKA_MAY_BE_UNUSED static PyObject *TO_LONG2( PyObject *value, PyObject *base )
{
    long base_int = PyInt_AsLong( base );

    if (unlikely( base_int == -1 ))
    {
        if (likely( ERROR_OCCURED() ))
        {
            return NULL;
        }
    }

    if (unlikely( !Nuitka_String_Check( value ) && !PyUnicode_Check( value ) ))
    {
        PyErr_Format( PyExc_TypeError, "long() can't convert non-string with explicit base" );
        return NULL;
    }

    char *value_str = Nuitka_String_AsString( value );
    if (unlikely( value_str == NULL ))
    {
        return NULL;
    }

    PyObject *result = PyLong_FromString( value_str, NULL, base_int );
    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *TO_BOOL( PyObject *value )
{
    int res = CHECK_IF_TRUE( value );

    if (unlikely( res == -1 )) return NULL;
    return BOOL_FROM( res != 0 );
}


NUITKA_MAY_BE_UNUSED static PyObject *TO_UNICODE3( PyObject *value, PyObject *encoding, PyObject *errors )
{
    assertObject( value );
    if ( encoding ) assertObject( encoding );
    if ( errors ) assertObject( errors );

    char *encoding_str;

    if ( encoding == NULL )
    {
        encoding_str = NULL;
    }
    else if ( Nuitka_String_Check( encoding ) )
    {
        encoding_str = Nuitka_String_AsString_Unchecked( encoding );
    }
#if PYTHON_VERSION < 300
    else if ( PyUnicode_Check( encoding ) )
    {
        PyObject *uarg2 = _PyUnicode_AsDefaultEncodedString( encoding, NULL );
        assertObject( uarg2 );

        encoding_str = Nuitka_String_AsString_Unchecked( uarg2 );
    }
#endif
    else
    {
        PyErr_Format( PyExc_TypeError, "unicode() argument 2 must be string, not %s", Py_TYPE( encoding )->tp_name );
        return NULL;
    }

    char *errors_str;

    if ( errors == NULL )
    {
        errors_str = NULL;
    }
    else if ( Nuitka_String_Check( errors ) )
    {
        errors_str = Nuitka_String_AsString_Unchecked( errors );
    }
#if PYTHON_VERSION < 300
    else if ( PyUnicode_Check( errors ) )
    {
        PyObject *uarg3 = _PyUnicode_AsDefaultEncodedString( errors, NULL );
        assertObject( uarg3 );

        errors_str = Nuitka_String_AsString_Unchecked( uarg3 );
    }
#endif
    else
    {
        PyErr_Format( PyExc_TypeError, "unicode() argument 3 must be string, not %s", Py_TYPE( errors )->tp_name );
        return NULL;
    }

    PyObject *result = PyUnicode_FromEncodedObject( value, encoding_str, errors_str );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    assert( PyUnicode_Check( result ) );

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_STATIC_METHOD( PyObject *method )
{
    assertObject( method );

    PyObject *attempt = PyStaticMethod_New( method );

    if ( attempt )
    {
        return attempt;
    }
    else
    {
        PyErr_Clear();

        return method;
    }
}

// Stolen from CPython implementation, so we can access it.
typedef struct {
    PyObject_HEAD
    long      it_index;
    PyObject *it_seq;
} seqiterobject;

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_ITERATOR( PyObject *iterated )
{
    getiterfunc tp_iter = NULL;

#if PYTHON_VERSION < 300
    if ( PyType_HasFeature( Py_TYPE( iterated ), Py_TPFLAGS_HAVE_ITER ))
    {
#endif
        tp_iter = Py_TYPE( iterated )->tp_iter;
#if PYTHON_VERSION < 300
    }
#endif

    if ( tp_iter )
    {
        PyObject *result = (*Py_TYPE( iterated )->tp_iter)( iterated );

        if (likely( result != NULL ))
        {
            if (unlikely( !PyIter_Check( result )) )
            {
                PyErr_Format( PyExc_TypeError, "iter() returned non-iterator of type '%s'", Py_TYPE( result )->tp_name );

                Py_DECREF( result );
                return NULL;
            }

            return result;
        }
        else
        {
            return NULL;
        }
    }
    else if ( PySequence_Check( iterated ) )
    {
        seqiterobject *result = PyObject_GC_New( seqiterobject, &PySeqIter_Type );
        assert( result );

        result->it_index = 0;
        result->it_seq = INCREASE_REFCOUNT( iterated );

        Nuitka_GC_Track( result );

        return (PyObject *)result;
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object is not iterable",
            Py_TYPE( iterated )->tp_name
        );

        return NULL;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *ITERATOR_NEXT( PyObject *iterator )
{
    assertObject( iterator );

    iternextfunc iternext = Py_TYPE( iterator )->tp_iternext;

    if (unlikely( iternext == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
#if PYTHON_VERSION < 330
            "%s object is not an iterator",
#else
            "'%s' object is not an iterator",
#endif
            Py_TYPE( iterator )->tp_name
        );

        return NULL;
    }

    PyObject *result = (*iternext)( iterator );

#if PYTHON_VERSION < 330
    if ( result == NULL && PyErr_Occurred() && PyErr_ExceptionMatches( PyExc_StopIteration ) )
    {
        PyErr_Clear();
    }
#endif

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_NEXT1( PyObject *iterator )
{
    assertObject( iterator );

    iternextfunc iternext = Py_TYPE( iterator )->tp_iternext;

    if (unlikely( iternext == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
#if PYTHON_VERSION < 330
            "%s object is not an iterator",
#else
            "'%s' object is not an iterator",
#endif
            Py_TYPE( iterator )->tp_name
        );

        return NULL;
    }

    PyObject *result = (*iternext)( iterator );

    if (unlikely( result == NULL ))
    {
        // The iteration can return NULL with no error, which means
        // StopIteration.
        if ( !ERROR_OCCURED() )
        {
            PyErr_SetNone( PyExc_StopIteration );
        }

        return NULL;
    }
    else
    {
        assertObject( result );
    }

    return result;
}


NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_NEXT2( PyObject *iterator, PyObject *default_value )
{
    assertObject( iterator );
    assertObject( default_value );

    PyObject *result = (*Py_TYPE( iterator )->tp_iternext)( iterator );

    if (unlikely( result == NULL ))
    {
        if ( ERROR_OCCURED() )
        {
            if ( PyErr_ExceptionMatches( PyExc_StopIteration ))
            {
                PyErr_Clear();

                return INCREASE_REFCOUNT( default_value );
            }
            else
            {
                return NULL;
            }
        }
        else
        {
            return INCREASE_REFCOUNT( default_value );
        }
    }
    else
    {
        assertObject( result );
    }

    return result;
}


NUITKA_MAY_BE_UNUSED static inline PyObject *UNPACK_NEXT( PyObject *iterator, int seq_size_so_far )
{
    assertObject( iterator ); assert( PyIter_Check( iterator ) );

    PyObject *result = (*Py_TYPE( iterator )->tp_iternext)( iterator );

    if (unlikely( result == NULL ))
    {
#if PYTHON_VERSION < 300
        if (unlikely( !ERROR_OCCURED() ))
#else
        if (unlikely( !ERROR_OCCURED() || PyErr_ExceptionMatches( PyExc_StopIteration ) ))
#endif
        {
            if ( seq_size_so_far == 1 )
            {
                PyErr_Format( PyExc_ValueError, "need more than 1 value to unpack" );
            }
            else
            {
                PyErr_Format( PyExc_ValueError, "need more than %d values to unpack", seq_size_so_far );
            }
        }

        return NULL;
    }

    assertObject( result );

    return result;
}

NUITKA_MAY_BE_UNUSED static inline PyObject *UNPACK_PARAMETER_NEXT( PyObject *iterator, int seq_size_so_far )
{
    assertObject( iterator );
    assert( PyIter_Check( iterator ) );

    PyObject *result = (*Py_TYPE( iterator )->tp_iternext)( iterator );

    if (unlikely( result == NULL ))
    {
#if PYTHON_VERSION < 300
        if (unlikely( !ERROR_OCCURED() ))
#else
        if (unlikely( !ERROR_OCCURED() || PyErr_ExceptionMatches( PyExc_StopIteration ) ))
#endif
        {
            if ( seq_size_so_far == 1 )
            {
                PyErr_Format( PyExc_ValueError, "need more than 1 value to unpack" );
            }
            else
            {
                PyErr_Format( PyExc_ValueError, "need more than %d values to unpack", seq_size_so_far );
            }
        }

        return NULL;
    }

    assertObject( result );

    return result;
}

NUITKA_MAY_BE_UNUSED static inline bool UNPACK_PARAMETER_ITERATOR_CHECK( PyObject *iterator )
{
    assertObject( iterator );
    assert( PyIter_Check( iterator ) );

    PyObject *attempt = (*Py_TYPE( iterator )->tp_iternext)( iterator );

    if (likely( attempt == NULL ))
    {
        if ( ERROR_OCCURED() )
        {
            if (likely( PyErr_ExceptionMatches( PyExc_StopIteration ) ))
            {
                PyErr_Clear();
            }
            else
            {
                return false;
            }
        }

        return true;
    }
    else
    {
        Py_DECREF( attempt );

        PyErr_Format( PyExc_ValueError, "too many values to unpack" );
        return false;
    }
}


NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_VARS( PyObject *source )
{
    assertObject( source );

    PyObject *result = PyObject_GetAttr( source, const_str_plain___dict__ );

    if (unlikely( result == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "vars() argument must have __dict__ attribute"
        );

        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *IMPORT_NAME( PyObject *module, PyObject *import_name )
{
    assertObject( module );
    assertObject( import_name );

    PyObject *result = PyObject_GetAttr( module, import_name );

    if (unlikely( result == NULL ))
    {
        if ( PyErr_ExceptionMatches( PyExc_AttributeError ) )
        {
#if PYTHON_VERSION < 340
            PyErr_Format( PyExc_ImportError, "cannot import name %s", Nuitka_String_AsString( import_name ));
#else
            PyErr_Format( PyExc_ImportError, "cannot import name '%s'", Nuitka_String_AsString( import_name ));
#endif
        }

        return NULL;
    }

    return result;
}


#include "nuitka/helper/indexes.hpp"
#include "nuitka/helper/subscripts.hpp"
#include "nuitka/helper/slices.hpp"
#include "nuitka/helper/attributes.hpp"

#include "nuitka/builtins.hpp"

#include "nuitka/frame_stack.hpp"

#include "nuitka/variables_locals.hpp"
#include "nuitka/variables_shared.hpp"

NUITKA_MAY_BE_UNUSED static PyObject *LIST_COPY( PyObject *list )
{
    assertObject( list );
    assert( PyList_CheckExact( list ) );

    Py_ssize_t size = PyList_GET_SIZE( list );
    PyObject *result = PyList_New( size );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        PyList_SET_ITEM( result, i, INCREASE_REFCOUNT( PyList_GET_ITEM( list, i ) ) );
    }

    return result;
}


// Compile source code given, pretending the file name was given.
#if PYTHON_VERSION < 300
extern PyObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags, PyObject *dont_inherit );
#else
extern PyObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags, PyObject *dont_inherit, PyObject *optimize );
#endif


// For quicker builtin open() functionality.
extern PyObject *BUILTIN_OPEN( PyObject *file_name, PyObject *mode, PyObject *buffering );

// For quicker builtin chr() functionality.
extern PyObject *BUILTIN_CHR( PyObject *value );

// For quicker builtin ord() functionality.
extern PyObject *BUILTIN_ORD( PyObject *value );

// For quicker builtin bin() functionality.
extern PyObject *BUILTIN_BIN( PyObject *value );

// For quicker builtin oct() functionality.
extern PyObject *BUILTIN_OCT( PyObject *value );

// For quicker builtin hex() functionality.
extern PyObject *BUILTIN_HEX( PyObject *value );

// For quicker callable() functionality.
extern PyObject *BUILTIN_CALLABLE( PyObject *value );

// For quicker iter() functionality if 2 arguments arg given.
extern PyObject *BUILTIN_ITER2( PyObject *callable, PyObject *sentinel );

// For quicker type() functionality if 1 argument is given.
extern PyObject *BUILTIN_TYPE1( PyObject *arg );

// For quicker type() functionality if 3 arguments are given (to build a new
// type).
extern PyObject *BUILTIN_TYPE3( PyObject *module_name, PyObject *name, PyObject *bases, PyObject *dict );

// For built-in builtin range() functionality.
extern PyObject *BUILTIN_RANGE3( PyObject *low, PyObject *high, PyObject *step );
extern PyObject *BUILTIN_RANGE2( PyObject *low, PyObject *high );
extern PyObject *BUILTIN_RANGE( PyObject *boundary );

extern PyObject *BUILTIN_XRANGE( PyObject *low, PyObject *high, PyObject *step );

// For built-in builtin len() functionality.
extern PyObject *BUILTIN_LEN( PyObject *boundary );

// For built-in builtin super() functionality.
extern PyObject *BUILTIN_SUPER( PyObject *type, PyObject *object );

// For built-in isinstance() functionality.
extern PyObject *BUILTIN_ISINSTANCE( PyObject *inst, PyObject *cls );

// The patched isinstance() functionality used for the built-in.
extern int Nuitka_IsInstance( PyObject *inst, PyObject *cls );

// For built-in getattr() functionality.
extern PyObject *BUILTIN_GETATTR( PyObject *object, PyObject *attribute, PyObject *default_value );

// For built-in setattr() functionality.
extern PyObject *BUILTIN_SETATTR( PyObject *object, PyObject *attribute, PyObject *value );

// For built-in bytearray() functionality.
extern PyObject *BUILTIN_BYTEARRAY( PyObject *value );

extern PyObject *const_str_plain___builtins__;
//
extern PyObject *EVAL_CODE( PyObject *code, PyObject *globals, PyObject *locals );


#include "nuitka/importing.hpp"

// For the constant loading:

// Call this to initialize all common constants pre-main.
void _initConstants( void );

#if defined(_WIN32) && defined(_NUITKA_EXE)
#include <Windows.h>
extern const unsigned char* constant_bin;
#else
extern "C" const unsigned char constant_bin[];
#endif

extern void UNSTREAM_INIT( void );
extern PyObject *UNSTREAM_CONSTANT( unsigned char const *buffer, Py_ssize_t size );
extern PyObject *UNSTREAM_STRING( unsigned char const *buffer, Py_ssize_t size, bool intern );
extern PyObject *UNSTREAM_CHAR( unsigned char value, bool intern );
#if PYTHON_VERSION < 300
extern PyObject *UNSTREAM_UNICODE( unsigned char const *buffer, Py_ssize_t size );
#else
extern PyObject *UNSTREAM_BYTES( unsigned char const *buffer, Py_ssize_t size );
#endif
extern PyObject *UNSTREAM_FLOAT( unsigned char const *buffer );

extern void enhancePythonTypes( void );

// Parse the command line parameters and provide it to sys module.
extern void setCommandLineParameters( int argc, char *argv[], bool initial );

// Replace builtin functions with ones that accept compiled types too.
extern void patchBuiltinModule( void );

// Replace type comparison with one that accepts compiled types too, will work
// for "==" and "!=", but not for "is" checks.
extern void patchTypeComparison( void );

#if PYTHON_VERSION < 300
// Initialize value for tp_compare default.
extern cmpfunc DefaultSlotCompare;
extern void initSlotCompare( void );
#endif

#if PYTHON_VERSION >= 300
NUITKA_MAY_BE_UNUSED static PyObject *SELECT_METACLASS( PyObject *metaclass, PyObject *bases )
{
    assertObject( metaclass );
    assertObject( bases );

    if (likely( PyType_Check( metaclass ) ))
    {
        // Determine the proper metatype
        Py_ssize_t nbases = PyTuple_GET_SIZE( bases );
        PyTypeObject *winner = (PyTypeObject *)metaclass;

        for ( int i = 0; i < nbases; i++ )
        {
            PyObject *base = PyTuple_GET_ITEM( bases, i );

            PyTypeObject *base_type = Py_TYPE( base );

            if ( PyType_IsSubtype( winner, base_type ) )
            {
                // Ignore if current winner is already a subtype.
                continue;
            }
            else if ( PyType_IsSubtype( base_type, winner ) )
            {
                // Use if, if it's a subtype of the current winner.
                winner = base_type;
                continue;
            }
            else
            {
                PyErr_Format(
                    PyExc_TypeError,
                    "metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases"
                );

                return NULL;
            }
        }

        if (unlikely( winner == NULL ))
        {
            return NULL;
        }

        return INCREASE_REFCOUNT( (PyObject *)winner );
    }
    else
    {
        return INCREASE_REFCOUNT( metaclass );
    }
}
#else

NUITKA_MAY_BE_UNUSED static PyObject *SELECT_METACLASS( PyObject *bases, PyObject *metaclass_global )
{
    assertObject( bases );

    PyObject *metaclass;

    assert( bases != Py_None );

    if ( PyTuple_GET_SIZE( bases ) > 0 )
    {
        PyObject *base = PyTuple_GET_ITEM( bases, 0 );

        metaclass = PyObject_GetAttr( base, const_str_plain___class__ );

        if ( metaclass == NULL )
        {
            PyErr_Clear();

            metaclass = INCREASE_REFCOUNT( (PyObject *)Py_TYPE( base ) );
        }
    }
    else if ( metaclass_global != NULL )
    {
        metaclass = INCREASE_REFCOUNT( metaclass_global );
    }
    else
    {
        // Default to old style class.
        metaclass = INCREASE_REFCOUNT( (PyObject *)&PyClass_Type );
    }

    // Cannot fail on Python2.
    assertObject( metaclass );

    return metaclass;
}

#endif

extern PyObject *const_str_plain___name__;

NUITKA_MAY_BE_UNUSED static PyObject *MODULE_NAME( PyObject *module )
{
    assert( PyModule_Check( module ) );
    PyObject *module_dict = ((PyModuleObject *)module)->md_dict;

    return PyDict_GetItem( module_dict, const_str_plain___name__ );
}

#if defined(_NUITKA_STANDALONE) || _NUITKA_FROZEN > 0
extern void prepareStandaloneEnvironment();
extern void restoreStandaloneEnvironment();
extern char *getBinaryDirectory();
#endif

#if _NUITKA_STANDALONE
extern void setEarlyFrozenModulesFileAttribute( void );
#endif

#include <nuitka/threading.hpp>

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE( PyObject **elements, Py_ssize_t size )
{
    PyObject *result = PyTuple_New( size );

    for( Py_ssize_t i = 0; i < size; i++ )
    {
        PyTuple_SET_ITEM( result, i, INCREASE_REFCOUNT( elements[i] ) );
    }

    return result;
}

// Make a deep copy of an object.
extern PyObject *DEEP_COPY( PyObject *value );

// Force a garbage collection, for debugging purposes.
NUITKA_MAY_BE_UNUSED static void forceGC()
{
    PyObject_CallObject(PyObject_GetAttrString(PyImport_ImportModule("gc"), "collect"), NULL );
}

#endif
