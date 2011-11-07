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
#ifndef __NUITKA_VARIABLES_LOCALS_H__
#define __NUITKA_VARIABLES_LOCALS_H__

class PyObjectLocalVariable
{
    public:
        explicit PyObjectLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = false )
        {
            this->var_name   = var_name;
            this->object     = object;
            this->free_value = free_value;
        }

        explicit PyObjectLocalVariable()
        {
            this->var_name   = NULL;
            this->object     = NULL;
            this->free_value = false;
        }

        ~PyObjectLocalVariable()
        {
            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }
        }

        void setVariableName( PyObject *var_name )
        {
            assertObject( var_name );
            assert( this->var_name == NULL);

            this->var_name = var_name;
        }

        void operator=( PyObject *object )
        {
            assertObject( object );

            if ( this->free_value )
            {
                PyObject *old_object = this->object;

                this->object = object;

                // Free old value if any available and owned.
                Py_DECREF( old_object );
            }
            else
            {
                this->object = object;
                this->free_value = true;
            }
        }

        PyObject *asObject() const
        {
            if ( this->object == NULL && this->var_name != NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", Nuitka_String_AsString( this->var_name ) );
                throw _PythonException();
            }

            assertObject( this->object );

            return this->object;
        }

        PyObject *asObject1() const
        {
            return INCREASE_REFCOUNT( this->asObject() );
        }

        bool isInitialized() const
        {
            return this->object != NULL;
        }

        void del()
        {
            if ( this->object == NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", Nuitka_String_AsString( this->var_name ) );
                throw _PythonException();
            }

            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }

            this->object = NULL;
            this->free_value = false;
        }

        PyObject *getVariableName() const
        {
            return this->var_name;
        }

    private:

        PyObject *var_name;
        PyObject *object;
        bool free_value;
};

#endif
