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
#ifndef __NUITKA_VARIABLES_LOCALS_H__
#define __NUITKA_VARIABLES_LOCALS_H__

class PyObjectLocalVariable
{
public:
    explicit PyObjectLocalVariable( PyObject *var_name, PyObject *object = NULL  )
    {
        this->var_name   = var_name;
        this->object     = object;
    }

    explicit PyObjectLocalVariable()
    {
        this->var_name   = NULL;
        this->object     = NULL;
    }

    ~PyObjectLocalVariable()
    {
        Py_XDECREF( this->object );
    }

    void setVariableName( PyObject *var_name )
    {
        assertObject( var_name );
        assert( this->var_name == NULL);

        this->var_name = var_name;
    }

    void assign0( PyObject *object )
    {
        assertObject( object );

        PyObject *old_object = this->object;
        this->object = INCREASE_REFCOUNT( object );
        Py_XDECREF( old_object );
    }

    void assign1( PyObject *object )
    {
        assertObject( object );

        PyObject *old_object = this->object;
        this->object = object;
        Py_XDECREF( old_object );
    }

    PyObject *asObject0() const
    {
        if ( this->object == NULL && this->var_name != NULL )
        {
            PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", Nuitka_String_AsString( this->var_name ) );
            throw PythonException();
        }

        assertObject( this->object );

        return this->object;
    }

    PyObject *asObject1() const
    {
        return INCREASE_REFCOUNT( this->asObject0() );
    }

    bool isInitialized() const
    {
        return this->object != NULL;
    }

    void del( bool tolerant )
    {
        if ( this->object == NULL )
        {
            if ( tolerant == false )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", Nuitka_String_AsString( this->var_name ) );
                throw PythonException();
            }
        }
        else
        {
            PyObject *old_object = this->object;
            this->object = NULL;
            Py_DECREF( old_object );
        }
    }

    PyObject *getVariableName() const
    {
        return this->var_name;
    }

    PyObject *updateLocalsDict( PyObject *locals_dict ) const
    {
        assert( PyDict_Check( locals_dict ) );

        if ( this->isInitialized() )
        {
#if PYTHON_VERSION < 300
            int status = PyDict_SetItem(
#else
            int status = PyObject_SetItem(
#endif
                locals_dict,
                this->getVariableName(),
                this->asObject0()
            );

            if (unlikely( status == -1 ))
            {
                throw PythonException();
            }
        }

        return locals_dict;
    }

    PyObject *updateLocalsDir( PyObject *locals_list ) const
    {
        assert( PyList_Check( locals_list ) );

        if ( this->isInitialized() )
        {
            int status = PyList_Append(
                locals_list,
                this->getVariableName()
            );

            if (unlikely( status == -1 ))
            {
                throw PythonException();
            }
        }

        return locals_list;
    }

private:

    PyObjectLocalVariable( const PyObjectLocalVariable &other ) { assert( false ); }

    PyObject *var_name;
    PyObject *object;
};

#endif
