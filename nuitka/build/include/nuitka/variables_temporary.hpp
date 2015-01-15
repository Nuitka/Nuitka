//     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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


class PyObjectTempVariable
{
public:
    explicit PyObjectTempVariable()
    {
        this->object = NULL;
    }

    ~PyObjectTempVariable()
    {
        if ( this->object ) assertObject( this->object );

        // TODO: We ought to be able to do this, but e.g. conditional
        // expressions still do not "del" in a try/finally handler.
        assert( !this->object );

        Py_XDECREF( this->object );
    }

private:

    PyObjectTempVariable( const PyObjectTempVariable &object )
    {
        assert( false );
    }

public:

    PyObject *object;
};


#endif
