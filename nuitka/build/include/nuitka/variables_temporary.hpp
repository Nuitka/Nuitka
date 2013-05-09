//     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

// Wraps a "PyObject *" you received or acquired from another container to
// simplify refcount handling when you're not going to use the object beyond the
// local scope. It will hold a reference to the wrapped object as long as the
// PyObjectTemporary is alive, and will release the reference when the wrapper
// is destroyed: this eliminates the need for manual DECREF calls on Python
// objects before returning from a method call.
//
// In effect, wrapping an object inside a PyObjectTemporary is equivalent to a
// deferred Py_DECREF() call on the wrapped object.

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
    PyObjectTemporary() { assert( false ); };

    PyObject *object;
};


class PyObjectTempKeeper1
{
public:
    explicit PyObjectTempKeeper1()
    {
        this->object = NULL;
    }

    ~PyObjectTempKeeper1()
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

    PyObject *asObject0()
    {
        assertObject( this->object );

        return this->object;
    }

    PyObject *assign( PyObject *value )
    {
        assertObject( value );

        this->object = value;
        return this->object;
    }

    bool isKeeping() const
    {
        return this->object != NULL;
    }

private:

    PyObjectTempKeeper1( const PyObjectTempKeeper1 &other ) { assert( false ); }

    PyObject *object;
};


class PyObjectTempKeeper0
{
public:
    explicit PyObjectTempKeeper0()
    {
        this->object = NULL;
    }

    ~PyObjectTempKeeper0()
    {}

    PyObject *asObject0()
    {
        assertObject( this->object );

        PyObject *result = this->object;

        this->object = NULL;
        return result;
    }

    PyObject *asObject()
    {
        assertObject( this->object );

        PyObject *result = INCREASE_REFCOUNT( this->object );

        this->object = NULL;
        return result;
    }

    PyObject *assign( PyObject *value )
    {
        assertObject( value );

        this->object = value;
        return this->object;
    }

private:

    PyObjectTempKeeper0( const PyObjectTempKeeper0 &other ) { assert( false ); }

    PyObject *object;
};

#endif
