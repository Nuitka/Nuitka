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
#ifndef __NUITKA_VARIABLES_SHARED_H__
#define __NUITKA_VARIABLES_SHARED_H__

class PyObjectSharedStorage
{
public:
    explicit PyObjectSharedStorage( PyObject *object )
    {
        assert( object == NULL || Py_REFCNT( object ) > 0 );

        this->object     = object;
        this->ref_count  = 1;
    }

    ~PyObjectSharedStorage()
    {
        Py_XDECREF( this->object );
    }

    PyObject *object;
    int ref_count;

private:

    PyObjectSharedStorage( const PyObjectSharedStorage & ) { assert( false ); };

};

class PyObjectSharedLocalVariable
{
public:

    explicit PyObjectSharedLocalVariable()
    {
        this->storage = new PyObjectSharedStorage( NULL );
    };

    ~PyObjectSharedLocalVariable()
    {
        if ( this->storage )
        {
            assert( this->storage->ref_count > 0 );
            this->storage->ref_count -= 1;

            if ( this->storage->ref_count == 0 )
            {
                delete this->storage;
            }
        }
    }

    void shareWith( const PyObjectSharedLocalVariable &other )
    {
        assert( other.storage != NULL );
        assert( this->storage != NULL );

        delete this->storage;

        this->storage = other.storage;
        this->storage->ref_count += 1;
    }

    PyObjectSharedStorage *storage;

private:

    PyObjectSharedLocalVariable( const PyObjectSharedLocalVariable & ) {  assert( false ); };

};

class PyObjectSharedTempStorage
{
public:
    explicit PyObjectSharedTempStorage( PyObject *object )
    {
        assert( object == NULL || Py_REFCNT( object ) > 0 );

        this->object     = object;
        this->ref_count  = 1;
    }

    ~PyObjectSharedTempStorage()
    {
        Py_XDECREF( this->object );
    }

    PyObject *object;
    int ref_count;

private:

    PyObjectSharedTempStorage( const PyObjectSharedTempStorage & ) { assert( false ); };

};

class PyObjectSharedTempVariable
{
public:
    explicit PyObjectSharedTempVariable( PyObject *object )
    {
        this->storage = new PyObjectSharedTempStorage( object );
    }

    explicit PyObjectSharedTempVariable()
    {
        this->storage = NULL;
    };

    ~PyObjectSharedTempVariable()
    {
        if ( this->storage )
        {
            assert( this->storage->ref_count > 0 );
            this->storage->ref_count -= 1;

            if ( this->storage->ref_count == 0 )
            {
                delete this->storage;
            }
        }
    }

    void shareWith( const PyObjectSharedTempVariable &other )
    {
        assert( this->storage == NULL );
        assert( other.storage != NULL );

        this->storage = other.storage;
        this->storage->ref_count += 1;
    }

public:

    PyObjectSharedTempStorage *storage;

private:

    PyObjectSharedTempVariable( const PyObjectSharedTempVariable & ) {  assert( false ); };

};

#endif
