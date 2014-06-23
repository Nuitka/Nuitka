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
    explicit PyObjectLocalParameterVariableWithDel( PyObject *object )
    {
        assertObject( object );

        this->object = object;
    }

    explicit PyObjectLocalParameterVariableWithDel()
    {
        this->object = NULL;
    }

    void setVariableValue( PyObject *object )
    {
        assertObject( object );
        assert( this->object == NULL);
        this->object = object;
    }

    ~PyObjectLocalParameterVariableWithDel()
    {
        Py_XDECREF( this->object );
    }

    inline bool isInitialized() const
    {
        return this->object != NULL;
    }

private:

    PyObjectLocalParameterVariableWithDel( const PyObjectLocalParameterVariableWithDel &other ) { assert( false ); }

public:
    PyObject *object;
};

class PyObjectLocalParameterVariableNoDel
{
public:

    explicit PyObjectLocalParameterVariableNoDel( PyObject *object )
    {
        assertObject( object );

        this->object = object;
    }

    explicit PyObjectLocalParameterVariableNoDel()
    {
        this->object = NULL;
    }

    void setVariableValue( PyObject *object )
    {
        assertObject( object );
        assert( this->object == NULL);
        this->object = object;
    }

    ~PyObjectLocalParameterVariableNoDel()
    {
        assertObject( this->object );

        Py_DECREF( this->object );
    }

    inline bool isInitialized() const
    {
        return true;
    }

private:

    PyObjectLocalParameterVariableNoDel( const PyObjectLocalParameterVariableNoDel &other ) { assert( false ); }

public:
    PyObject *object;
};

#endif
