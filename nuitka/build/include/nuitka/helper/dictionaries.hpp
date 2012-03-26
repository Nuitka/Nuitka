//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit patches or make the software available to licensors of
//     this software in either form, you automatically them grant them a
//     license for your part of the code under "Apache License 2.0" unless you
//     choose to remove this notice.
//
//     Kay Hayen uses the right to license his code under only GPL version 3,
//     to discourage a fork of Nuitka before it is "finished". He will later
//     make a new "Nuitka" release fully under "Apache License 2.0".
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
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
