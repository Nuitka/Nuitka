//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type in-place "*" (MULT) operations */

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_INT_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_OBJECT_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_INT_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MULT_LONG_LONG(PyObject **operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MULT_OBJECT_LONG(PyObject **operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_LONG_OBJECT(PyObject **operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
extern bool INPLACE_OPERATION_MULT_FLOAT_FLOAT(PyObject **operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
extern bool INPLACE_OPERATION_MULT_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MULT_FLOAT_LONG(PyObject **operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "FLOAT" to Python 'float'. */
extern bool INPLACE_OPERATION_MULT_LONG_FLOAT(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_FLOAT_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "FLOAT" to Python 'float'. */
extern bool INPLACE_OPERATION_MULT_INT_FLOAT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_LONG_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MULT_INT_LONG(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
extern bool INPLACE_OPERATION_MULT_INT_CLONG(PyObject **operand1, long operand2);
#endif

/* Code referring to "FLOAT" corresponds to Python 'float' and "CFLOAT" to C platform float value. */
extern bool INPLACE_OPERATION_MULT_FLOAT_CFLOAT(PyObject **operand1, double operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_STR_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "STR" to Python2 'str'. */
extern bool INPLACE_OPERATION_MULT_INT_STR(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_UNICODE_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "UNICODE" to Python2 'unicode', Python3 'str'. */
extern bool INPLACE_OPERATION_MULT_INT_UNICODE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "TUPLE" corresponds to Python 'tuple' and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_TUPLE_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "TUPLE" to Python 'tuple'. */
extern bool INPLACE_OPERATION_MULT_INT_TUPLE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LIST" corresponds to Python 'list' and "INT" to Python2 'int'. */
extern bool INPLACE_OPERATION_MULT_LIST_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LIST" to Python 'list'. */
extern bool INPLACE_OPERATION_MULT_INT_LIST(PyObject **operand1, PyObject *operand2);
#endif

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "LONG" to Python2 'long', Python3
 * 'int'. */
extern bool INPLACE_OPERATION_MULT_UNICODE_LONG(PyObject **operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "UNICODE" to Python2 'unicode', Python3
 * 'str'. */
extern bool INPLACE_OPERATION_MULT_LONG_UNICODE(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MULT_BYTES_LONG(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "BYTES" to Python3 'bytes'. */
extern bool INPLACE_OPERATION_MULT_LONG_BYTES(PyObject **operand1, PyObject *operand2);
#endif

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MULT_TUPLE_LONG(PyObject **operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "TUPLE" to Python 'tuple'. */
extern bool INPLACE_OPERATION_MULT_LONG_TUPLE(PyObject **operand1, PyObject *operand2);

/* Code referring to "LIST" corresponds to Python 'list' and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MULT_LIST_LONG(PyObject **operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LIST" to Python 'list'. */
extern bool INPLACE_OPERATION_MULT_LONG_LIST(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_STR_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_UNICODE_OBJECT(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_BYTES_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_TUPLE_OBJECT(PyObject **operand1, PyObject *operand2);

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_LIST_OBJECT(PyObject **operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MULT_OBJECT_OBJECT(PyObject **operand1, PyObject *operand2);

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
