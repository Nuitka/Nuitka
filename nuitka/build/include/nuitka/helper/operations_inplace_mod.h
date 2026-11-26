//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */
#pragma once
#ifndef __NUITKA_OPERATIONS_INPLACE_MOD_H__
#define __NUITKA_OPERATIONS_INPLACE_MOD_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type in-place "%" (MOD) operations */

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_INT_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_OBJECT_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_INT_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

extern bool INPLACE_OPERATION_MOD_LONG_LONG(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_OBJECT_LONG(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_LONG_OBJECT(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_FLOAT_FLOAT(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_FLOAT_LONG(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_LONG_FLOAT(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_FLOAT_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_INT_FLOAT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_LONG_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_INT_LONG(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_INT_CLONG(PyObject **operand1, long operand2);
#endif

extern bool INPLACE_OPERATION_MOD_FLOAT_CFLOAT(PyObject **operand1, double operand2);

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_INT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_LONG(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_FLOAT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_STR(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_UNICODE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_TUPLE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_LIST(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_DICT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_STR_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_UNICODE_INT(PyObject **operand1, PyObject *operand2);
#endif

extern bool INPLACE_OPERATION_MOD_UNICODE_LONG(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_UNICODE_FLOAT(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
extern bool INPLACE_OPERATION_MOD_UNICODE_STR(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_UNICODE_BYTES(PyObject **operand1, PyObject *operand2);
#endif

extern bool INPLACE_OPERATION_MOD_UNICODE_UNICODE(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_UNICODE_TUPLE(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_UNICODE_LIST(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_UNICODE_DICT(PyObject **operand1, PyObject *operand2);

extern bool INPLACE_OPERATION_MOD_UNICODE_OBJECT(PyObject **operand1, PyObject *operand2);

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_LONG(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_FLOAT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_BYTES(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_UNICODE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_TUPLE(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_LIST(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_DICT(PyObject **operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool INPLACE_OPERATION_MOD_BYTES_OBJECT(PyObject **operand1, PyObject *operand2);
#endif

extern bool INPLACE_OPERATION_MOD_OBJECT_OBJECT(PyObject **operand1, PyObject *operand2);

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
