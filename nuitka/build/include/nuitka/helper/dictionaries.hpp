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
#ifndef __NUITKA_DICTIONARIES_H__
#define __NUITKA_DICTIONARIES_H__

extern PyObject *_python_dict_empty;

// Quick dictionary lookup for a string value.
static PyDictEntry *GET_PYDICT_ENTRY( PyDictObject *dict, Nuitka_StringObject *key )
{
    assert( PyDict_CheckExact( dict ) );
    assert( Nuitka_String_Check( key ) );

#if PYTHON_VERSION < 300
    long hash = key->ob_shash;
#else
    long hash = key->hash;
#endif

    // Only improvement would be to identify how to ensure that the hash is computed
    // already. Calling hash early on could do that potentially.
    if ( hash == -1 )
    {
#if PYTHON_VERSION < 300
        hash = PyString_Type.tp_hash( (PyObject *)key );
        key->ob_shash = hash;
#else
        hash = PyUnicode_Type.tp_hash( (PyObject *)key );
        key->hash = hash;
#endif
    }

    PyDictEntry *entry = dict->ma_lookup( dict, (PyObject *)key, hash );

    // The "entry" cannot be NULL, it can only be empty for a string dict lookup, but at
    // least assert it.
    assert( entry != NULL );

    return entry;
}

// Quick module lookup for a string value.
static PyDictEntry *GET_PYDICT_ENTRY( PyModuleObject *module, Nuitka_StringObject *key )
{
    // Idea similar to LOAD_GLOBAL in CPython. Because the variable name is a string, we
    // can shortcut much of the dictionary code by using its hash and dictionary knowledge
    // here.

    PyDictObject *dict = (PyDictObject *)(module->md_dict);

    return GET_PYDICT_ENTRY( dict, key );
}

// Check if a dictionary can contain strings. It doesn't if the ma_lookup wasn't changed
// away from the variant that is active in dictionaries that never saw one.
static inline bool COULD_CONTAIN_NON_STRINGS( PyObject *dict )
{
    return ( ((PyDictObject *)( dict ))->ma_lookup != ((PyDictObject *)_python_dict_empty)->ma_lookup );
}

NUITKA_MAY_BE_UNUSED static void DICT_SET_ITEM( PyObject *dict, PyObject *key, PyObject *value )
{
    int status = PyDict_SetItem( dict, key, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

NUITKA_MAY_BE_UNUSED static void DICT_REMOVE_ITEM( PyObject *dict, PyObject *key )
{
    int status = PyDict_DelItem( dict, key );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}


NUITKA_MAY_BE_UNUSED static PyObject *DICT_GET_ITEM( PyObject *dict, PyObject *key )
{
    assertObject( dict );
    assert( PyDict_Check( dict ) );

    assertObject( key );

    PyObject *result = PyDict_GetItem( dict, key );

    if ( result == NULL )
    {
        if (unlikely( PyErr_Occurred() ))
        {
            throw _PythonException();
        }

        PyErr_SetObject( PyExc_KeyError, key );
        throw _PythonException();
    }
    else
    {
        return INCREASE_REFCOUNT( result );
    }
}


// Convert to dictionary, helper for builtin dict mainly.
NUITKA_MAY_BE_UNUSED static PyObject *TO_DICT( PyObject *seq_obj, PyObject *dict_obj )
{
    PyObject *result = PyDict_New();

    if ( seq_obj != NULL )
    {
        int res;

        if ( PyObject_HasAttrString( seq_obj, "keys" ) )
        {
            res = PyDict_Merge( result, seq_obj, 1 );
        }
        else
        {
            res = PyDict_MergeFromSeq2( result, seq_obj, 1 );
        }

        if ( res == -1 )
        {
            throw _PythonException();
        }
    }

    if ( dict_obj != NULL )
    {
        int res = PyDict_Merge( result, dict_obj, 1 );

        if ( res == -1 )
        {
            throw _PythonException();
        }

    }

    return result;
}



#endif
