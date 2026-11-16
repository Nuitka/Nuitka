//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationBinary.c.j2 instead! */
#pragma once
#ifndef __NUITKA_OPERATIONS_BINARY_MULT_H__
#define __NUITKA_OPERATIONS_BINARY_MULT_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"

#include "nuitka/helper/boolean.h"
#endif

/* C helpers for type specialized "*" (MULT) operations */

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

extern PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_LONG(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_INT_CLONG(PyObject *operand1, long operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_CLONG(PyObject *operand1, long operand2);
#endif

extern PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_CFLOAT(PyObject *operand1, double operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_CFLOAT_FLOAT(double operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_CFLOAT_CFLOAT(double operand1, double operand2);

extern double BINARY_OPERATION_MULT_CFLOAT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

extern double BINARY_OPERATION_MULT_CFLOAT_FLOAT_CFLOAT(PyObject *operand1, double operand2);

extern double BINARY_OPERATION_MULT_CFLOAT_CFLOAT_FLOAT(double operand1, PyObject *operand2);

extern double BINARY_OPERATION_MULT_CFLOAT_CFLOAT_CFLOAT(double operand1, double operand2);

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_STR_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_INT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_INT_UNICODE(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_INT_TUPLE(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_INT_LIST(PyObject *operand1, PyObject *operand2);
#endif

extern PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION >= 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_BYTES_LONG(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_BYTES(PyObject *operand1, PyObject *operand2);
#endif

extern PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_LONG(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_LIST(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION >= 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern PyObject *BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
