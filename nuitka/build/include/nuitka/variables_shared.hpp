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

    void assign0( PyObject *object )
    {
        assertObject( object );

        if ( this->free_value )
        {
            PyObject *old_object = this->object;

            this->object = INCREASE_REFCOUNT( object );

            // Free old value if any available and owned.
            Py_DECREF( old_object );
        }
        else
        {
            this->object = INCREASE_REFCOUNT( object );
            this->free_value = true;
        }
    }

    void assign1( PyObject *object )
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

private:
    PyObjectSharedStorage( const PyObjectSharedStorage & ) = delete;

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

    void setVariableNameAndValue( PyObject *var_name, PyObject *object )
    {
        this->setVariableName( var_name  );
        this->assign1( object );
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

    void assign0( PyObject *object )
    {
        this->storage->assign0( object );
    }

    void assign1( PyObject *object )
    {
        this->storage->assign1( object );
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

    PyObjectSharedLocalVariable( const PyObjectSharedLocalVariable & ) = delete;

    PyObjectSharedStorage *storage;
};

#endif
