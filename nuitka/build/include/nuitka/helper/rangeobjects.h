//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_RANGEOBJECTS_H__
#define __NUITKA_HELPER_RANGEOBJECTS_H__

/* For built-in built-in range() functionality. */

extern PyObject *BUILTIN_RANGE3(PyObject *low, PyObject *high, PyObject *step);
extern PyObject *BUILTIN_RANGE2(PyObject *low, PyObject *high);
extern PyObject *BUILTIN_RANGE(PyObject *boundary);

/* For built-in built-in xrange() functionality. */

extern PyObject *BUILTIN_XRANGE1(PyObject *high);
extern PyObject *BUILTIN_XRANGE2(PyObject *low, PyObject *high);
extern PyObject *BUILTIN_XRANGE3(PyObject *low, PyObject *high, PyObject *step);

#if PYTHON_VERSION >= 0x300

/* Python3 range objects */
struct _rangeobject3 {
    /* Python object folklore: */
    PyObject_HEAD

        PyObject *start;
    PyObject *stop;
    PyObject *step;
    PyObject *length;
};

NUITKA_MAY_BE_UNUSED static PyObject *PyRange_Start(PyObject *range) { return ((struct _rangeobject3 *)range)->start; }

NUITKA_MAY_BE_UNUSED static PyObject *PyRange_Stop(PyObject *range) { return ((struct _rangeobject3 *)range)->stop; }

NUITKA_MAY_BE_UNUSED static PyObject *PyRange_Step(PyObject *range) { return ((struct _rangeobject3 *)range)->step; }

#else

struct _rangeobject2 {
    /* Python object folklore: */
    PyObject_HEAD

        long start;
    long step;
    long len;
};

extern PyObject *MAKE_XRANGE(long start, long stop, long step);

#endif

#endif
