//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type in-place "^" (BITXOR) operations */

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
extern bool BINARY_OPERATION_BITXOR_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
extern bool BINARY_OPERATION_BITXOR_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
extern bool BINARY_OPERATION_BITXOR_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
extern bool BINARY_OPERATION_BITXOR_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
extern bool BINARY_OPERATION_BITXOR_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
extern bool BINARY_OPERATION_BITXOR_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
extern bool BINARY_OPERATION_BITXOR_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
extern bool BINARY_OPERATION_BITXOR_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2);
#endif

/* Code referring to "SET" corresponds to Python 'set' and "SET" to Python 'set'. */
extern bool BINARY_OPERATION_BITXOR_SET_SET_INPLACE(PyObject **operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "SET" to Python 'set'. */
extern bool BINARY_OPERATION_BITXOR_OBJECT_SET_INPLACE(PyObject **operand1, PyObject *operand2);

/* Code referring to "SET" corresponds to Python 'set' and "OBJECT" to any Python object. */
extern bool BINARY_OPERATION_BITXOR_SET_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern bool BINARY_OPERATION_BITXOR_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
