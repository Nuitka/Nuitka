//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationComparison.c.j2 instead! */
#pragma once
#ifndef __NUITKA_COMPARISONS_EQ_H__
#define __NUITKA_COMPARISONS_EQ_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"

// Includes below require definitions from the prelude.
#include "nuitka/helper/boolean.h"
#endif

/* C helpers for type specialized "==" (EQ) comparisons */

extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_STR_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool RICH_COMPARE_EQ_CBOOL_STR_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_STR_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2);

extern bool RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION >= 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_BYTES_BYTES(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern bool RICH_COMPARE_EQ_CBOOL_BYTES_BYTES(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_BYTES(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_BYTES_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool RICH_COMPARE_EQ_CBOOL_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2);

extern bool RICH_COMPARE_EQ_CBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

extern bool RICH_COMPARE_EQ_CBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_CFLOAT_CFLOAT(double operand1, double operand2);

extern bool RICH_COMPARE_EQ_CBOOL_CFLOAT_CFLOAT(double operand1, double operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_LIST_LIST(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_LIST(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_LIST_OBJECT(PyObject *operand1, PyObject *operand2);

extern nuitka_bool RICH_COMPARE_EQ_NBOOL_LIST_LIST(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool RICH_COMPARE_EQ_CBOOL_LONG_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *RICH_COMPARE_EQ_OBJECT_INT_CLONG(PyObject *operand1, long operand2);
#endif

#if PYTHON_VERSION < 0x300
extern bool RICH_COMPARE_EQ_CBOOL_INT_CLONG(PyObject *operand1, long operand2);
#endif

extern PyObject *RICH_COMPARE_EQ_OBJECT_LONG_DIGIT(PyObject *operand1, long operand2);

extern bool RICH_COMPARE_EQ_CBOOL_LONG_DIGIT(PyObject *operand1, long operand2);

extern PyObject *RICH_COMPARE_EQ_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2);

extern bool RICH_COMPARE_EQ_CBOOL_FLOAT_CFLOAT(PyObject *operand1, double operand2);

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
