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
#ifndef __NUITKA_RANGEOBJECTS_H__
#define __NUITKA_RANGEOBJECTS_H__

// Python3 range objects
#if PYTHON_VERSION >= 300

typedef struct {
    PyObject_HEAD
    PyObject *start;
    PyObject *stop;
    PyObject *step;
    PyObject *length;
} _rangeobject;

NUITKA_MAY_BE_UNUSED static PyObject *PyRange_Start( PyObject *range )
{
    return ((_rangeobject *)range)->start;
}

NUITKA_MAY_BE_UNUSED static PyObject *PyRange_Stop( PyObject *range )
{
    return ((_rangeobject *)range)->stop;
}

NUITKA_MAY_BE_UNUSED static PyObject *PyRange_Step( PyObject *range )
{
    return ((_rangeobject *)range)->step;
}

#endif

#endif
