//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_HELPER_RICHCOMPARISONS_H__
#define __NUITKA_HELPER_RICHCOMPARISONS_H__

#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"

// Includes below require definitions from the prelude.
#include "nuitka/helper/boolean.h"
#endif

#include "nuitka/helper/comparisons_eq.h"
#include "nuitka/helper/comparisons_ge.h"
#include "nuitka/helper/comparisons_gt.h"
#include "nuitka/helper/comparisons_le.h"
#include "nuitka/helper/comparisons_lt.h"
#include "nuitka/helper/comparisons_ne.h"

#include "nuitka/helper/comparisons_dual_eq.h"
#include "nuitka/helper/comparisons_dual_ge.h"
#include "nuitka/helper/comparisons_dual_gt.h"
#include "nuitka/helper/comparisons_dual_le.h"
#include "nuitka/helper/comparisons_dual_lt.h"
#include "nuitka/helper/comparisons_dual_ne.h"

NUITKA_MAY_BE_UNUSED static inline bool RICH_COMPARE_CBOOL_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2,
                                                                           int op) {
    switch (op) {
    case Py_EQ:
        return RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(operand1, operand2);
    case Py_NE:
        return !RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(operand1, operand2);
    case Py_LE:
        return RICH_COMPARE_LE_CBOOL_UNICODE_UNICODE(operand1, operand2);
    case Py_GT:
        return !RICH_COMPARE_LE_CBOOL_UNICODE_UNICODE(operand1, operand2);
    case Py_LT:
        return RICH_COMPARE_LT_CBOOL_UNICODE_UNICODE(operand1, operand2);
    case Py_GE:
        return !RICH_COMPARE_LT_CBOOL_UNICODE_UNICODE(operand1, operand2);
    default:
        NUITKA_CANNOT_GET_HERE("Invalid richcompare op");
    }
}

NUITKA_MAY_BE_UNUSED static inline PyObject *RICH_COMPARE_OBJECT_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2,
                                                                                 int op) {
    return Py_NewRef_IMMORTAL(BOOL_FROM(RICH_COMPARE_CBOOL_UNICODE_UNICODE(operand1, operand2, op)));
}

NUITKA_MAY_BE_UNUSED static inline PyObject *RICH_COMPARE_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2,
                                                                               int op) {
    switch (op) {
    case Py_EQ:
        return RICH_COMPARE_EQ_OBJECT_OBJECT_OBJECT(operand1, operand2);
    case Py_NE:
        return RICH_COMPARE_NE_OBJECT_OBJECT_OBJECT(operand1, operand2);
    case Py_LE:
        return RICH_COMPARE_LE_OBJECT_OBJECT_OBJECT(operand1, operand2);
    case Py_GE:
        return RICH_COMPARE_GE_OBJECT_OBJECT_OBJECT(operand1, operand2);
    case Py_LT:
        return RICH_COMPARE_LT_OBJECT_OBJECT_OBJECT(operand1, operand2);
    case Py_GT:
        return RICH_COMPARE_GT_OBJECT_OBJECT_OBJECT(operand1, operand2);
    default:
        NUITKA_CANNOT_GET_HERE("Invalid richcompare op");
    }
}

NUITKA_MAY_BE_UNUSED static inline nuitka_bool RICH_COMPARE_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2,
                                                                                int op) {
    switch (op) {
    case Py_EQ:
        return RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(operand1, operand2);
    case Py_NE:
        return RICH_COMPARE_NE_NBOOL_OBJECT_OBJECT(operand1, operand2);
    case Py_LE:
        return RICH_COMPARE_LE_NBOOL_OBJECT_OBJECT(operand1, operand2);
    case Py_GE:
        return RICH_COMPARE_GE_NBOOL_OBJECT_OBJECT(operand1, operand2);
    case Py_LT:
        return RICH_COMPARE_LT_NBOOL_OBJECT_OBJECT(operand1, operand2);
    case Py_GT:
        return RICH_COMPARE_GT_NBOOL_OBJECT_OBJECT(operand1, operand2);
    default:
        NUITKA_CANNOT_GET_HERE("Invalid richcompare op");
    }
}

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
