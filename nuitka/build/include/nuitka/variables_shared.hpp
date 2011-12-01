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
#ifndef __NUITKA_VARIABLES_SHARED_H__
#define __NUITKA_VARIABLES_SHARED_H__

class PyObjectSharedStorage
{
    public:
        explicit PyObjectSharedStorage( PyObject *var_name, PyObject *object, bool free_value )
        {
            assert( object == NULL || Py_REFCNT( object ) > 0 );

            this->var_name   = var_name;
            this->object     = object;
            this->free_value = free_value;
            this->ref_count  = 1;
        }

        ~PyObjectSharedStorage()
        {
            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }
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

        inline PyObject *getVarName() const
        {
            return this->var_name;
        }

        PyObject *var_name;
        PyObject *object;
        bool free_value;
        int ref_count;
};

class PyObjectSharedLocalVariable
{
    public:
        explicit PyObjectSharedLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = false )
        {
            this->storage = new PyObjectSharedStorage( var_name, object, free_value );
        }

        explicit PyObjectSharedLocalVariable()
        {
            this->storage = NULL;
        }

        ~PyObjectSharedLocalVariable()
        {
            if ( this->storage )
            {
                assert( this->storage->ref_count > 0 );
                this->storage->ref_count -= 1;

                if (this->storage->ref_count == 0)
                {
                    delete this->storage;
                }
            }
        }

        void setVariableName( PyObject *var_name )
        {
            assert( this->storage == NULL );

            this->storage = new PyObjectSharedStorage( var_name, NULL, false );
        }

        void shareWith( const PyObjectSharedLocalVariable &other )
        {
            assert( this->storage == NULL );
            assert( other.storage != NULL );

            this->storage = other.storage;
            this->storage->ref_count += 1;
        }

        void operator=( PyObject *object )
        {
            this->storage->operator=( object );
        }

        PyObject *asObject() const
        {
            assert( this->storage );

            if ( this->storage->object == NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "free variable '%s' referenced before assignment in enclosing scope", Nuitka_String_AsString( this->storage->getVarName() ) );
                throw _PythonException();

            }

            if ( Py_REFCNT( this->storage->object ) == 0 )
            {
                PyErr_Format( PyExc_UnboundLocalError, "free variable '%s' referenced after its finalization in enclosing scope", Nuitka_String_AsString( this->storage->getVarName() ) );
                throw _PythonException();
            }

            return this->storage->object;
        }

        PyObject *asObject1() const
        {
            return INCREASE_REFCOUNT( this->asObject() );
        }

        bool isInitialized() const
        {
            return this->storage->object != NULL;
        }

        PyObject *getVariableName() const
        {
            return this->storage->var_name;
        }

    private:
        PyObjectSharedLocalVariable( PyObjectSharedLocalVariable & );

        PyObjectSharedStorage *storage;
};

#endif
