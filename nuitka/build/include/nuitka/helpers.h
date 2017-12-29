//     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
#define _DEBUG_COROUTINE 0
#define _DEBUG_ASYNCGEN 0

extern PyObject *const_tuple_empty;
extern PyObject *const_str_plain___dict__;
extern PyObject *const_str_plain___class__;
extern PyObject *const_str_plain___enter__;
extern PyObject *const_str_plain___exit__;

extern PyObject *const_int_0;
extern PyObject *const_int_pos_1;

// From CPython, to allow us quick access to the dictionary of an module, the
// structure is normally private, but we need it for quick access to the module
// dictionary.
typedef struct {
    PyObject_HEAD
    PyObject *md_dict;
} PyModuleObject;

// Most fundamental, because we use it for debugging in everything else.
#include "nuitka/helper/printing.h"

// Helper to check that an object is valid and has positive reference count.
#define CHECK_OBJECT( value ) ( assert( value != NULL ), assert( Py_REFCNT( value ) > 0 ) );


#include "nuitka/exceptions.h"

// For use with "--trace-execution", code can make outputs. Otherwise they
// are just like comments.
#include "nuitka/tracing.h"

// For checking values if they changed or not.
#ifndef __NUITKA_NO_ASSERT__
extern Py_hash_t DEEP_HASH( PyObject *value );
#endif

// For profiling of Nuitka compiled binaries
#if _NUITKA_PROFILE
extern void startProfiling( void );
extern void stopProfiling( void );
#endif


#include "nuitka/helper/boolean.h"
#include "nuitka/helper/dictionaries.h"
#include "nuitka/helper/mappings.h"

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

#include "nuitka/helper/raising.h"

#include "helper/operations.h"

#include "nuitka/helper/richcomparisons.h"
#include "nuitka/helper/sequences.h"

static inline bool Nuitka_Function_Check( PyObject *object );
static inline PyObject *Nuitka_Function_GetName( PyObject *object );

static inline bool Nuitka_Generator_Check( PyObject *object );
static inline PyObject *Nuitka_Generator_GetName( PyObject *object );

#include "nuitka/calling.h"


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

NUITKA_MAY_BE_UNUSED static PyObject *TO_COMPLEX( PyObject *real, PyObject *imag )
{
    // TODO: Very lazy here, we should create the values ourselves, surely a
    // a lot of optimization can be had that way.
    if ( real == NULL )
    {
        assert( imag != NULL );

        real = const_int_0;
    }

    if ( imag == NULL)
    {
        PyObject *args[] = { real };
        return CALL_FUNCTION_WITH_ARGS1( (PyObject *)&PyComplex_Type, args );
    }
    else
    {
        PyObject *args[] = { real, imag };
        return CALL_FUNCTION_WITH_ARGS2( (PyObject *)&PyComplex_Type, args );
    }
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
        PyObject *error = GET_ERROR_OCCURRED();

        if (likely( error ))
        {
#if PYTHON_VERSION >= 300
            if ( EXCEPTION_MATCH_BOOL_SINGLE( error, PyExc_OverflowError ) )
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

        PyObject *result = NULL;

        if ( size != 0 && strlen( value_str ) == (size_t)size )
        {
            result = PyInt_FromString( value_str, NULL, (int)base_int );
        }

        if (unlikely( result == NULL ))
        {
            PyErr_Format(
                PyExc_ValueError,
                "invalid literal for int() with base %d: %R",
                base_int,
                value
            );

            return NULL;
        }

        return result;
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
        if (likely( ERROR_OCCURRED() ))
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
    CHECK_OBJECT( value );
    if ( encoding ) CHECK_OBJECT( encoding );
    if ( errors ) CHECK_OBJECT( errors );

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
        CHECK_OBJECT( uarg2 );

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
        CHECK_OBJECT( uarg3 );

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


NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_VARS( PyObject *source )
{
    CHECK_OBJECT( source );

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

#include "nuitka/helper/subscripts.h"
#include "nuitka/helper/attributes.h"
#include "nuitka/helper/iterators.h"
#include "nuitka/helper/slices.h"
#include "nuitka/helper/rangeobjects.h"
#include "nuitka/helper/lists.h"
#include "nuitka/helper/bytearrays.h"

#include "nuitka/builtins.h"

#include "nuitka/allocator.h"



// Compile source code given, pretending the file name was given.
#if PYTHON_VERSION < 300
extern PyObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags, PyObject *dont_inherit );
#else
extern PyObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags, PyObject *dont_inherit, PyObject *optimize );
#endif


// For quicker built-in open() functionality.
#if PYTHON_VERSION < 300
extern PyObject *BUILTIN_OPEN( PyObject *file_name, PyObject *mode, PyObject *buffering );
#else
extern PyObject *BUILTIN_OPEN( PyObject *file_name, PyObject *mode, PyObject *buffering, PyObject *encoding, PyObject *errors, PyObject *newline, PyObject *closefd, PyObject *opener );
#endif

// For quicker built-in chr() functionality.
extern PyObject *BUILTIN_CHR( PyObject *value );

// For quicker built-in ord() functionality.
extern PyObject *BUILTIN_ORD( PyObject *value );

// For quicker built-in bin() functionality.
extern PyObject *BUILTIN_BIN( PyObject *value );

// For quicker built-in oct() functionality.
extern PyObject *BUILTIN_OCT( PyObject *value );

// For quicker built-in hex() functionality.
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

// For built-in built-in len() functionality.
extern PyObject *BUILTIN_LEN( PyObject *boundary );

// For built-in built-in super() functionality.
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
extern PyObject *BUILTIN_BYTEARRAY1( PyObject *value );
extern PyObject *BUILTIN_BYTEARRAY3( PyObject *string, PyObject *encoding, PyObject *errors );

// For built-in hash() functionality.
extern PyObject *BUILTIN_HASH( PyObject *value );

// For built-in sum() functionality.
extern PyObject *BUILTIN_SUM1( PyObject *sequence );
extern PyObject *BUILTIN_SUM2( PyObject *sequence, PyObject *start );

// For built-in bytes() functionality.
#if PYTHON_VERSION >= 300
extern PyObject *BUILTIN_BYTES3( PyObject *value, PyObject *encoding, PyObject *errors );
#endif

extern PyObject *const_str_plain___builtins__;

// For built-in eval() functionality, works on byte compiled code already.
extern PyObject *EVAL_CODE( PyObject *code, PyObject *globals, PyObject *locals );

// For built-in format() functionality.
extern PyObject *BUILTIN_FORMAT( PyObject *value, PyObject *format_spec );

// For built-in staticmethod() functionality.
extern PyObject *BUILTIN_STATICMETHOD( PyObject *function );

// For built-in classmethod() functionality.
extern PyObject *BUILTIN_CLASSMETHOD( PyObject *function );

// For built-in divmod() functionality.
extern PyObject *BUILTIN_DIVMOD( PyObject *operand1, PyObject *operand2 );

#include "nuitka/importing.h"

// For the constant loading:

// Call this to initialize all common constants pre-main.
extern void createGlobalConstants( void );

// Call this to check of common constants are still intact.
#ifndef __NUITKA_NO_ASSERT__
extern void checkGlobalConstants( void );
#endif

// Unstreaming constants from a blob.
#include "nuitka/constants_blob.h"

extern void UNSTREAM_INIT( void );
extern PyObject *UNSTREAM_STRING( unsigned char const *buffer, Py_ssize_t size, bool intern );
extern PyObject *UNSTREAM_CHAR( unsigned char value, bool intern );
#if PYTHON_VERSION < 300
extern PyObject *UNSTREAM_UNICODE( unsigned char const *buffer, Py_ssize_t size );
#else
extern PyObject *UNSTREAM_BYTES( unsigned char const *buffer, Py_ssize_t size );
#endif
extern PyObject *UNSTREAM_FLOAT( unsigned char const *buffer );
extern PyObject *UNSTREAM_BYTEARRAY( unsigned char const *buffer, Py_ssize_t size );

// Performance enhancements to Python types.
extern void enhancePythonTypes( void );

// Setup meta path based loader if any.
extern void setupMetaPathBasedLoader( void );

// Parse the command line parameters and provide it to "sys" built-in module.

#if PYTHON_VERSION >= 300
typedef wchar_t ** argv_type_t;
extern argv_type_t convertCommandLineParameters( int argc, char **argv );
#else
typedef char ** argv_type_t;
#endif
extern bool setCommandLineParameters( int argc, argv_type_t argv, bool initial );

// Replace built-in functions with ones that accept compiled types too.
extern void patchBuiltinModule( void );

/* Replace inspect functions with ones that handle compiles types too. */
#if PYTHON_VERSION >= 300
extern void patchInspectModule( void );
#endif

// Replace type comparison with one that accepts compiled types too, will work
// for "==" and "!=", but not for "is" checks.
extern void patchTypeComparison( void );

// Patch the CPython type for tracebacks and make it use a freelist mechanism
// to be slightly faster for exception control flows.
extern void patchTracebackDealloc( void );

#if PYTHON_VERSION < 300
// Initialize value for "tp_compare" default.
extern void _initSlotCompare( void );
#endif

#if PYTHON_VERSION >= 300
NUITKA_MAY_BE_UNUSED static PyObject *SELECT_METACLASS( PyObject *metaclass, PyObject *bases )
{
    CHECK_OBJECT( metaclass );
    CHECK_OBJECT( bases );

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

        Py_INCREF( winner );
        return (PyObject *)winner;
    }
    else
    {
        Py_INCREF( metaclass );
        return metaclass;
    }
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
// Get the binary directory, translated to UTF8 or usable as a native path,
// e.g. ANSI on Windows.
extern char *getBinaryDirectoryUTF8Encoded();
extern char *getBinaryDirectoryHostEncoded();
#endif

#if _NUITKA_STANDALONE
extern void setEarlyFrozenModulesFileAttribute( void );
#endif

/* For making paths relative to where we got loaded from. Do not provide any
 * absolute paths as relative value, this is not as capable as "os.path.join",
 * instead just works on strings.
 */
extern PyObject *MAKE_RELATIVE_PATH( PyObject *relative );

#include <nuitka/threading.h>

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE( PyObject **elements, Py_ssize_t size )
{
    PyObject *result = PyTuple_New( size );

    for( Py_ssize_t i = 0; i < size; i++ )
    {
        PyObject *item = elements[i];
        Py_INCREF( item );
        PyTuple_SET_ITEM( result, i, item );
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
