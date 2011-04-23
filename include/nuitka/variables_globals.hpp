//
//     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
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
#ifndef __NUITKA_VARIABLES_GLOBALS_H__
#define __NUITKA_VARIABLES_GLOBALS_H__

extern PyModuleObject *_module_builtin;

#if 0
class PyObjectGlobalVariable
{
    public:
        explicit PyObjectGlobalVariable( PyObject **module_ptr, PyObject **var_name )
        {
            assert( module_ptr );
            assert( var_name );

            this->module_ptr = (PyModuleObject **)module_ptr;
            this->var_name   = (PyStringObject **)var_name;
        }

        PyObject *asObject0() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assert( entry->me_value->ob_refcnt > 0 );

                return entry->me_value;
            }

            entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assert( entry->me_value->ob_refcnt > 0 );

                return entry->me_value;
            }

            PyErr_Format( PyExc_NameError, "global name '%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
            throw _PythonException();
        }

        PyObject *asObject() const
        {
            return INCREASE_REFCOUNT( this->asObject0() );
        }

        PyObject *asObject0( PyObject *dict ) const
        {
            if ( PyDict_Contains( dict, (PyObject *)*this->var_name ) )
            {
                return PyDict_GetItem( dict, (PyObject *)*this->var_name );
            }
            else
            {
                return this->asObject0();
            }
        }

        void assign( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = value;

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name, value );

                Py_DECREF( value );
            }
        }

        void assign0( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = INCREASE_REFCOUNT( value );

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name, value );
            }
        }

        void del() const
        {
            int status = PyDict_DelItem( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name );

            if (unlikely( status == -1 ))
            {
                PyErr_Format( PyExc_NameError, "name '%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
                throw _PythonException();
            }
        }

        bool isInitialized( bool allow_builtins = true ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                return true;
            }

            if ( allow_builtins )
            {
                entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

                return entry->me_value != NULL;
            }
            else
            {
                return false;
            }
        }

    private:
        PyModuleObject **module_ptr;
        PyStringObject **var_name;
};

#endif

#endif
