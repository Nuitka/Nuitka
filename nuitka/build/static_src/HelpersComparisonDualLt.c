//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationComparisonDual.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized "<" (LT) comparisons */

static PyObject *COMPARE_LT_OBJECT_CLONG_CLONG(long operand1, long operand2) {

    const long a = operand1;
    const long b = operand2;

    bool r = a < b;

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
/* Code referring to "NILONG" corresponds to Nuitka int/long/C long value and "NILONG" to Nuitka int/long/C long value.
 */
PyObject *RICH_COMPARE_LT_OBJECT_NILONG_NILONG(nuitka_ilong *operand1, nuitka_ilong *operand2) {
    CHECK_NILONG_OBJECT(operand1);
    CHECK_NILONG_OBJECT(operand2);

    bool left_c_usable = IS_NILONG_C_VALUE_VALID(operand1);
    bool right_c_usable = IS_NILONG_C_VALUE_VALID(operand2);

    if (left_c_usable && right_c_usable) {
        return COMPARE_LT_OBJECT_CLONG_CLONG(operand1->c_value, operand2->c_value);
    } else if (!left_c_usable && !right_c_usable) {
        return RICH_COMPARE_LT_OBJECT_LONG_LONG(operand1->python_value, operand2->python_value);
    } else {
        bool r;
        if (left_c_usable) {
            r = COMPARE_GT_CBOOL_LONG_CLONG(operand2->python_value, operand1->c_value);
            r = !r;
        } else {
            r = COMPARE_LT_CBOOL_LONG_CLONG(operand1->python_value, operand2->c_value);
        }

        // Convert to target type.
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
}

static bool COMPARE_LT_CBOOL_CLONG_CLONG(long operand1, long operand2) {

    const long a = operand1;
    const long b = operand2;

    bool r = a < b;

    // Convert to target type.
    bool result = r;

    return result;
}
/* Code referring to "NILONG" corresponds to Nuitka int/long/C long value and "NILONG" to Nuitka int/long/C long value.
 */
bool RICH_COMPARE_LT_CBOOL_NILONG_NILONG(nuitka_ilong *operand1, nuitka_ilong *operand2) {
    CHECK_NILONG_OBJECT(operand1);
    CHECK_NILONG_OBJECT(operand2);

    bool left_c_usable = IS_NILONG_C_VALUE_VALID(operand1);
    bool right_c_usable = IS_NILONG_C_VALUE_VALID(operand2);

    if (left_c_usable && right_c_usable) {
        return COMPARE_LT_CBOOL_CLONG_CLONG(operand1->c_value, operand2->c_value);
    } else if (!left_c_usable && !right_c_usable) {
        return RICH_COMPARE_LT_CBOOL_LONG_LONG(operand1->python_value, operand2->python_value);
    } else {
        bool r;
        if (left_c_usable) {
            r = COMPARE_GT_CBOOL_LONG_CLONG(operand2->python_value, operand1->c_value);
            r = !r;
        } else {
            r = COMPARE_LT_CBOOL_LONG_CLONG(operand1->python_value, operand2->c_value);
        }

        // Convert to target type.
        bool result = r;

        return result;
    }
}

/* Code referring to "NILONG" corresponds to Nuitka int/long/C long value and "CLONG" to C platform long value. */
PyObject *RICH_COMPARE_LT_OBJECT_NILONG_CLONG(nuitka_ilong *operand1, long operand2) {
    CHECK_NILONG_OBJECT(operand1);

    bool left_c_usable = IS_NILONG_C_VALUE_VALID(operand1);
    bool right_c_usable = true;

    if (left_c_usable && right_c_usable) {
        return COMPARE_LT_OBJECT_CLONG_CLONG(operand1->c_value, operand2);
    } else if (!left_c_usable && !right_c_usable) {
        ENFORCE_NILONG_OBJECT_VALUE(operand1);

        return COMPARE_LT_OBJECT_LONG_CLONG(operand1->python_value, operand2);
    } else {
        return COMPARE_LT_OBJECT_LONG_CLONG(operand1->python_value, operand2);
    }
}

/* Code referring to "NILONG" corresponds to Nuitka int/long/C long value and "CLONG" to C platform long value. */
bool RICH_COMPARE_LT_CBOOL_NILONG_CLONG(nuitka_ilong *operand1, long operand2) {
    CHECK_NILONG_OBJECT(operand1);

    bool left_c_usable = IS_NILONG_C_VALUE_VALID(operand1);
    bool right_c_usable = true;

    if (left_c_usable && right_c_usable) {
        return COMPARE_LT_CBOOL_CLONG_CLONG(operand1->c_value, operand2);
    } else if (!left_c_usable && !right_c_usable) {
        ENFORCE_NILONG_OBJECT_VALUE(operand1);

        return COMPARE_LT_CBOOL_LONG_CLONG(operand1->python_value, operand2);
    } else {
        return COMPARE_LT_CBOOL_LONG_CLONG(operand1->python_value, operand2);
    }
}

/* Code referring to "NILONG" corresponds to Nuitka int/long/C long value and "DIGIT" to C platform digit value for long
 * Python objects. */
PyObject *RICH_COMPARE_LT_OBJECT_NILONG_DIGIT(nuitka_ilong *operand1, long operand2) {
    CHECK_NILONG_OBJECT(operand1);
    assert(Py_ABS(operand2) < (1 << PyLong_SHIFT));

    bool left_c_usable = IS_NILONG_C_VALUE_VALID(operand1);
    bool right_c_usable = true;

    if (left_c_usable && right_c_usable) {
        return COMPARE_LT_OBJECT_CLONG_CLONG(operand1->c_value, operand2);
    } else if (!left_c_usable && !right_c_usable) {
        ENFORCE_NILONG_OBJECT_VALUE(operand1);

        return COMPARE_LT_OBJECT_LONG_DIGIT(operand1->python_value, operand2);
    } else {
        return COMPARE_LT_OBJECT_LONG_DIGIT(operand1->python_value, operand2);
    }
}

/* Code referring to "NILONG" corresponds to Nuitka int/long/C long value and "DIGIT" to C platform digit value for long
 * Python objects. */
bool RICH_COMPARE_LT_CBOOL_NILONG_DIGIT(nuitka_ilong *operand1, long operand2) {
    CHECK_NILONG_OBJECT(operand1);
    assert(Py_ABS(operand2) < (1 << PyLong_SHIFT));

    bool left_c_usable = IS_NILONG_C_VALUE_VALID(operand1);
    bool right_c_usable = true;

    if (left_c_usable && right_c_usable) {
        return COMPARE_LT_CBOOL_CLONG_CLONG(operand1->c_value, operand2);
    } else if (!left_c_usable && !right_c_usable) {
        ENFORCE_NILONG_OBJECT_VALUE(operand1);

        return COMPARE_LT_CBOOL_LONG_DIGIT(operand1->python_value, operand2);
    } else {
        return COMPARE_LT_CBOOL_LONG_DIGIT(operand1->python_value, operand2);
    }
}

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
