//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_RICHCOMPARISONS_H__
#define __NUITKA_HELPER_RICHCOMPARISONS_H__

extern int RICH_COMPARE_BOOL_LT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_LTE_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_EQ_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_EQ_INT_OBJECT_NORECURSE(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_NOTEQ_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GTE_INT_OBJECT(PyObject *operand1, PyObject *operand2);

extern int RICH_COMPARE_BOOL_LT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_LTE_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_EQ_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_EQ_OBJECT_INT_NORECURSE(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_NOTEQ_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GTE_OBJECT_INT(PyObject *operand1, PyObject *operand2);

extern int RICH_COMPARE_BOOL_LT_INT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_LTE_INT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_EQ_INT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_NOTEQ_INT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GT_INT_INT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GTE_INT_INT(PyObject *operand1, PyObject *operand2);
#define RICH_COMPARE_BOOL_EQ_INT_INT_NORECURSE RICH_COMPARE_BOOL_EQ_INT_INT

extern int RICH_COMPARE_BOOL_LT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_LTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_EQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_EQ_OBJECT_OBJECT_NORECURSE(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_NOTEQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern int RICH_COMPARE_BOOL_GTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_LT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_LTE_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_EQ_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_EQ_INT_OBJECT_NORECURSE(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_NOTEQ_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_GT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_GTE_INT_OBJECT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_LT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_LTE_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_EQ_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_EQ_OBJECT_INT_NORECURSE(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_NOTEQ_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_GT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_GTE_OBJECT_INT(PyObject *operand1, PyObject *operand2);

extern PyObject *RICH_COMPARE_LT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_LTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_NORECURSE(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_NOTEQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_GT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
extern PyObject *RICH_COMPARE_GTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

#endif
