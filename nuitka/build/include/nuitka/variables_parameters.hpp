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
#ifndef __NUITKA_VARIABLES_PARAMETERS_H__
#define __NUITKA_VARIABLES_PARAMETERS_H__

class PyObjectLocalParameterVariableWithDel
{
public:
    explicit PyObjectLocalParameterVariableWithDel( PyObject *var_name, PyObject *object )
    {
        assertObject( var_name );
        assertObject( object );

        this->var_name = var_name;
        this->object = object;
    }

    explicit PyObjectLocalParameterVariableWithDel()
    {
        this->var_name = NULL;
        this->object = NULL;
    }

    void setVariableNameAndValue( PyObject *var_name, PyObject *object )
    {
        assertObject( var_name );
        assert( this->var_name == NULL);

        this->var_name = var_name;

        assertObject( object );
        assert( this->object == NULL);
        this->object = object;
    }

    ~PyObjectLocalParameterVariableWithDel()
    {
        assertObject( this->var_name );

        Py_XDECREF( this->object );
    }

    void assign0( PyObject *object )
    {
        assertObject( object );

        PyObject *old_object = this->object;

        this->object = INCREASE_REFCOUNT( object );

        // Free old value if any available and owned.
        Py_XDECREF( old_object );
    }


    void assign1( PyObject *object )
    {
        assertObject( object );

        PyObject *old_object = this->object;

        this->object = object;

        // Free old value if any available and owned.
        Py_XDECREF( old_object );
    }

    PyObject *asObject0() const
    {
        if ( this->object == NULL )
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
        if (unlikely( this->object == NULL ))
        {
            if ( tolerant == false )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", Nuitka_String_AsString( this->var_name ) );
                throw PythonException();
            }
        }
        else
        {
            assertObject( this->object );

            Py_DECREF( this->object );
            this->object = NULL;
        }
    }

    PyObject *getVariableName() const
    {
        assertObject( this->var_name );

        return this->var_name;
    }

    PyObject *updateLocalsDict( PyObject *locals_dict ) const
    {
        if ( this->isInitialized() )
        {
            int status = PyDict_SetItem(
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

    PyObjectLocalParameterVariableWithDel( const PyObjectLocalParameterVariableWithDel &other ) { assert( false ); }

    PyObject *var_name;
    PyObject *object;
};

class PyObjectLocalParameterVariableNoDel
{
public:

    explicit PyObjectLocalParameterVariableNoDel( PyObject *var_name, PyObject *object )
    {
        assertObject( object );
        assertObject( var_name );

        this->var_name = var_name;
        this->object = object;
    }

    explicit PyObjectLocalParameterVariableNoDel()
    {
        this->var_name = NULL;
        this->object = NULL;
    }

    void setVariableNameAndValue( PyObject *var_name, PyObject *object )
    {
        assertObject( var_name );
        assert( this->var_name == NULL);

        this->var_name = var_name;

        assertObject( object );
        assert( this->object == NULL);
        this->object = object;
    }

    ~PyObjectLocalParameterVariableNoDel()
    {
        assertObject( this->object );
        assertObject( this->var_name );

        Py_DECREF( this->object );
    }

    void assign0( PyObject *object )
    {
        assertObject( object );
        assertObject( this->object );

        PyObject *old_object = this->object;
        this->object = INCREASE_REFCOUNT( object );

        // Free old value if any available and owned.
        Py_DECREF( old_object );
    }

    void assign1( PyObject *object )
    {
        assertObject( object );
        assertObject( this->object );

        PyObject *old_object = this->object;
        this->object = object;

        // Free old value if any available and owned.
        Py_DECREF( old_object );
    }

    PyObject *asObject0() const
    {
        assertObject( this->object );

        return this->object;
    }

    PyObject *asObject1() const
    {
        return INCREASE_REFCOUNT( this->asObject0() );
    }

    PyObject *getVariableName() const
    {
        assertObject( this->var_name );

        return this->var_name;
    }

    PyObject *updateLocalsDict( PyObject *locals_dict ) const
    {
        int status = PyDict_SetItem(
            locals_dict,
            this->getVariableName(),
            this->asObject0()
        );

        if (unlikely( status == -1 ))
        {
            throw PythonException();
        }

        return locals_dict;
    }

    PyObject *updateLocalsDir( PyObject *locals_list ) const
    {
        assert( PyList_Check( locals_list ) );

        int status = PyList_Append(
            locals_list,
            this->getVariableName()
        );

        if (unlikely( status == -1 ))
        {
            throw PythonException();
        }

        return locals_list;
    }

private:

    PyObjectLocalParameterVariableNoDel( const PyObjectLocalParameterVariableNoDel &other ) { assert( false ); }

    PyObject *var_name;
    PyObject *object;
};

#endif
