//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

extern PyObject *BUILTIN_RANGE3( PyObject *low, PyObject *high, PyObject *step );
extern PyObject *BUILTIN_RANGE2( PyObject *low, PyObject *high );
extern PyObject *BUILTIN_RANGE( PyObject *boundary );

/* For built-in built-in xrange() functionality. */

extern PyObject *BUILTIN_XRANGE1( PyObject *low );
extern PyObject *BUILTIN_XRANGE2( PyObject *low, PyObject *high );
extern PyObject *BUILTIN_XRANGE3( PyObject *low, PyObject *high, PyObject *step );

#if PYTHON_VERSION >= 300

/* Python3 range objects */
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

#else

typedef struct {
    PyObject_HEAD
    long        start;
    long        step;
    long        len;
} rangeobject;


/* Same as CPython: */
static unsigned long getLengthOfRange( long lo, long hi, long step )
{
     assert( step != 0 );

     if (step > 0 && lo < hi)
     {
         return 1UL + (hi - 1UL - lo) / step;
     }
     else if (step < 0 && lo > hi)
     {
         return 1UL + (lo - 1UL - hi) / (0UL - step);
     }
     else
     {
         return 0UL;
     }
}

/* Create a "xrange" object from C long values. Used for constant ranges. */
NUITKA_MAY_BE_UNUSED static PyObject *MAKE_XRANGE( long start, long stop, long step )
{
    /* TODO: It would be sweet to calculate that on user side already. */

    unsigned long n = getLengthOfRange( start, stop, step );

    if ( n > (unsigned long)LONG_MAX || (long)n > PY_SSIZE_T_MAX)
    {
        PyErr_SetString(
            PyExc_OverflowError,
            "xrange() result has too many items"
        );

        return NULL;
    }

    rangeobject *result = PyObject_New( rangeobject, &PyRange_Type );
    assert (result != NULL);

    result->start = start;
    result->len   = (long)n;
    result->step  = step;

    return (PyObject *)result;
}

#endif

#endif
