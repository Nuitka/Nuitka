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
#ifndef __NUITKA_VARIABLES_TEMPORARY_H__
#define __NUITKA_VARIABLES_TEMPORARY_H__

// Wraps a "PyObject *" you received or acquired from another container to simplify refcount
// handling when you're not going to use the object beyond the local scope. It will hold a
// reference to the wrapped object as long as the PyObjectTemporary is alive, and will
// release the reference when the wrapper is destroyed: this eliminates the need for
// manual DECREF calls on Python objects before returning from a method call.
//
// In effect, wrapping an object inside a PyObjectTemporary is equivalent to a deferred
// Py_DECREF() call on the wrapped object.

class PyObjectTemporary
{
public:
    explicit PyObjectTemporary( PyObject *object )
    {
        assertObject( object );

        this->object = object;
    }

    ~PyObjectTemporary()
    {
        assertObject( this->object );

        Py_DECREF( this->object );
    }

    PyObject *asObject() const
    {
        assertObject( this->object );

        return this->object;
    }

    void assign1( PyObject *object )
    {
        assertObject( this->object );

        Py_DECREF( this->object );

        assertObject( object );

        this->object = object;
    }

private:

    PyObjectTemporary( const PyObjectTemporary &object ) { assert( false ); }

    PyObject *object;
};

class PyObjectTempHolder
{
public:
    explicit PyObjectTempHolder()
    {
        this->object = NULL;
    }

    ~PyObjectTempHolder()
    {
        Py_XDECREF( this->object );
    }

    PyObject *asObject()
    {
        assertObject( this->object );

        PyObject *result = this->object;
        this->object = NULL;
        return result;
    }

    PyObject *assign0( PyObject *value )
    {
        assertObject( value );

        this->object = INCREASE_REFCOUNT( value );
        return this->object;
    }

    PyObject *assign1( PyObject *value )
    {
        assertObject( value );

        this->object = value;
        return this->object;
    }

private:

    PyObjectTempHolder( const PyObjectTempHolder &other ) { assert( false ); }

    PyObject *object;
};

#endif
