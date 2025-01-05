//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type in-place "@" (MATMULT) operations */

#if PYTHON_VERSION >= 0x350
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MATMULT_LONG_LONG(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
extern bool INPLACE_OPERATION_MATMULT_OBJECT_LONG(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MATMULT_LONG_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
extern bool INPLACE_OPERATION_MATMULT_FLOAT_FLOAT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
extern bool INPLACE_OPERATION_MATMULT_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MATMULT_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern bool INPLACE_OPERATION_MATMULT_OBJECT_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

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
