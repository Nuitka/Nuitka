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
/* These slots are still manually coded and are used by the generated code.
 *
 * The plan should be to generate these as well, so e.g. we can have a slot
 * SLOT_nb_add_LONG_INT that is optimal too.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static PyObject *LIST_CONCAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    Py_ssize_t size = Py_SIZE(operand1) + Py_SIZE(operand2);

    PyListObject *result = (PyListObject *)PyList_New(size);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    PyObject **src = ((PyListObject *)operand1)->ob_item;
    PyObject **dest = result->ob_item;

    for (Py_ssize_t i = 0; i < Py_SIZE(operand1); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    src = ((PyListObject *)operand2)->ob_item;
    dest = result->ob_item + Py_SIZE(operand1);
    for (Py_ssize_t i = 0; i < Py_SIZE(operand2); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    return (PyObject *)result;
}

#if PYTHON_VERSION < 0x300
#include <longintrepr.h>

#if PYTHON_VERSION < 0x270
// Renamed from Python2.6
#define sdigit wdigit
#endif
#endif

// Convert single digit to sdigit (int32_t)
#define MEDIUM_VALUE(x)                                                                                                \
    (Py_SIZE(x) < 0 ? -(sdigit)((PyLongObject *)(x))->ob_digit[0]                                                      \
                    : (Py_SIZE(x) == 0 ? (sdigit)0 : (sdigit)((PyLongObject *)(x))->ob_digit[0]))

// Needed for offsetof
#include <stddef.h>

#define MAX_LONG_DIGITS ((PY_SSIZE_T_MAX - offsetof(PyLongObject, ob_digit)) / sizeof(digit))
#define Nuitka_LongGetDigitPointer(value) (&(((PyLongObject *)value)->ob_digit[0]))
#define Nuitka_LongGetDigitSize(value) (Py_ABS(Py_SIZE(value)))

// Our version of _PyLong_New(size);
static PyLongObject *Nuitka_LongNew(Py_ssize_t size) {
    assert(size < (Py_ssize_t)MAX_LONG_DIGITS);

#if PYTHON_VERSION >= 0x300
    PyLongObject *result;

    result = (PyLongObject *)PyObject_MALLOC(offsetof(PyLongObject, ob_digit) + size * sizeof(digit));
    return (PyLongObject *)PyObject_INIT_VAR(result, &PyLong_Type, size);
#else
    return (PyLongObject *)PyObject_NEW_VAR(PyLongObject, &PyLong_Type, size);
#endif
}

static PyObject *Nuitka_LongRealloc(PyObject *value, Py_ssize_t size) {
    PyLongObject *result = Nuitka_LongNew(size);
    Py_SIZE(result) = size;
    Py_DECREF(value);

    return (PyObject *)result;
}

static PyObject *Nuitka_LongFromCLong(long ival) {
#if PYTHON_VERSION < 0x300
    if (ival == 0) {
        PyLongObject *result = Nuitka_LongNew(0);

        return (PyObject *)result;
    }
#else
    if (ival >= NUITKA_STATIC_SMALLINT_VALUE_MIN && ival <= NUITKA_STATIC_SMALLINT_VALUE_MAX) {
        PyObject *result = Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(ival)];
        Py_INCREF(result);

        return result;
    }
#endif

    // We go via unsigned long to avoid overflows when shifting and we need
    // the sign separate in the end anyway.
    unsigned long abs_ival;
    bool negative;

    if (ival < 0) {
        abs_ival = 0U - (unsigned long)ival;
        negative = true;
    } else {
        abs_ival = (unsigned long)ival;
        negative = false;
    }

    // Fast path for single digit values
    if (!(abs_ival >> PyLong_SHIFT)) {
        PyLongObject *result = Nuitka_LongNew(1);
        assert(result != NULL);
        if (negative) {
            Py_SIZE(result) = -1;
        }

        result->ob_digit[0] = (digit)abs_ival;

        return (PyObject *)result;
    }

    // Fast path for two digit values on suitable platforms.
#if PyLong_SHIFT == 15
    if (!(abs_ival >> 2 * PyLong_SHIFT)) {
        PyLongObject *result = Nuitka_LongNew(2);
        assert(result != NULL);
        if (negative) {
            Py_SIZE(result) = -2;
        }

        result->ob_digit[0] = (digit)(abs_ival & PyLong_MASK);
        result->ob_digit[1] = (digit)(abs_ival >> PyLong_SHIFT);

        return (PyObject *)result;
    }
#endif

    // Slow path for the rest.
    unsigned long t = abs_ival;
    Py_ssize_t ndigits = 0;

    // First determine the number of digits needed.
    while (t != 0) {
        ++ndigits;
        t >>= PyLong_SHIFT;
    }

    PyLongObject *result = _PyLong_New(ndigits);
    assert(result != NULL);

    Py_SIZE(result) = negative ? -ndigits : ndigits;

    digit *d = result->ob_digit;

    // Now copy the digits
    t = abs_ival;
    while (t != 0) {
        *d++ = (digit)(t & PyLong_MASK);
        t >>= PyLong_SHIFT;
    }

    return (PyObject *)result;
}

static void Nuitka_LongUpdateFromCLong(PyObject **value, long ival) {
    assert(Py_REFCNT(*value) == 1);

#if PYTHON_VERSION < 0x300
    if (ival == 0) {
        if (Py_SIZE(*value) == 0) {
            return;
        }

        Py_DECREF(*value);
        *value = (PyObject *)Nuitka_LongNew(0);

        return;
    }
#else
    if (ival >= NUITKA_STATIC_SMALLINT_VALUE_MIN && ival <= NUITKA_STATIC_SMALLINT_VALUE_MAX) {
        Py_DECREF(*value);

        *value = Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(ival)];
        Py_INCREF(*value);

        return;
    }
#endif

    // We go via unsigned long to avoid overflows when shifting and we need
    // the sign separate in the end anyway.
    unsigned long abs_ival;
    bool negative;

    if (ival < 0) {
        abs_ival = 0U - (unsigned long)ival;
        negative = true;
    } else {
        abs_ival = (unsigned long)ival;
        negative = false;
    }

    // Fast path for single digit values
    if (!(abs_ival >> PyLong_SHIFT)) {
        PyLongObject *result;

        if (unlikely(Py_SIZE(*value) == 0)) {
            *value = Nuitka_LongRealloc(*value, 1);
            CHECK_OBJECT(*value);

            result = (PyLongObject *)*value;
        } else {
            result = (PyLongObject *)(*value);
        }

        Py_SIZE(result) = negative ? -1 : 1;

        result->ob_digit[0] = (digit)abs_ival;

        return;
    }

    // Fast path for two digit values on suitable platforms, e.g. armv7l
#if PyLong_SHIFT == 15
    if (!(abs_ival >> 2 * PyLong_SHIFT)) {
        PyLongObject *result;
        if (unlikely(Py_ABS(Py_SIZE(*value)) < 2)) {
            *value = Nuitka_LongRealloc(*value, 2);
            CHECK_OBJECT(*value);

            result = (PyLongObject *)*value;
        } else {
            result = (PyLongObject *)(*value);
        }

        Py_SIZE(result) = negative ? -2 : 2;

        result->ob_digit[0] = (digit)(abs_ival & PyLong_MASK);
        result->ob_digit[1] = (digit)(abs_ival >> PyLong_SHIFT);

        return;
    }
#endif

    // Slow path for the rest.
    unsigned long t = abs_ival;
    Py_ssize_t ndigits = 0;

    // First determine the number of digits needed.
    while (t != 0) {
        ndigits++;
        t >>= PyLong_SHIFT;
    }

    if (unlikely(Py_ABS(Py_SIZE(*value)) < ndigits)) {
        *value = Nuitka_LongRealloc(*value, ndigits);
    }

    CHECK_OBJECT(*value);

    Py_SIZE(*value) = negative ? -ndigits : ndigits;

    digit *d = ((PyLongObject *)(*value))->ob_digit;

    // Now copy the digits
    t = abs_ival;
    while (t) {
        *d++ = (digit)(t & PyLong_MASK);
        t >>= PyLong_SHIFT;
    }

    return;
}

#if 0
// Note: We are manually inlining this so far.
static PyLongObject *Nuitka_LongStripZeros(PyLongObject *v) {
    Py_ssize_t j = Py_ABS(Py_SIZE(v));

    Py_ssize_t i = j;
    while (i > 0 && v->ob_digit[i - 1] == 0) {
        i -= 1;
    }

    if (i != j) {
        Py_SIZE(v) = (Py_SIZE(v) < 0) ? -i : i;
    }

    return v;
}
#endif

static PyLongObject *_Nuitka_LongAddDigits(digit const *a, Py_ssize_t size_a, digit const *b, Py_ssize_t size_b) {
    // Make sure we know a is the longest value.
    if (size_a < size_b) {
        {
            digit const *temp = a;
            a = b;
            b = temp;
        }

        {
            Py_ssize_t temp = size_a;
            size_a = size_b;
            size_b = temp;
        }
    }

    // We do not know ahead of time, if we need a new digit, lets just allocate it.
    PyLongObject *result = Nuitka_LongNew(size_a + 1);
    CHECK_OBJECT(result);

    digit *r = &result->ob_digit[0];

    digit carry = 0;

    // First common digits.
    Py_ssize_t i;
    for (i = 0; i < size_b; i++) {
        carry += a[i] + b[i];
        r[i] = carry & PyLong_MASK;
        carry >>= PyLong_SHIFT;
    }
    // Digits from longest one only.
    for (; i < size_a; i++) {
        carry += a[i];
        r[i] = carry & PyLong_MASK;
        carry >>= PyLong_SHIFT;
    }

    // Only the top digit can be zero, so we can strip this faster.
    if (carry) {
        r[i] = carry;
    } else {
        Py_SIZE(result) -= 1;
    }

    return result;
}

static PyObject *_Nuitka_LongAddInplaceDigits(PyObject *left, digit const *b, Py_ssize_t size_b) {
    digit const *a = Nuitka_LongGetDigitPointer(left);
    Py_ssize_t size_a = Nuitka_LongGetDigitSize(left);

    digit const *aa = a;
    digit const *bb = b;

    // Make sure we know aa is the longest value by swapping a/b attributes.
    if (size_a < size_b) {
        {
            aa = b;
            bb = a;
        }

        {
            Py_ssize_t temp = size_a;
            size_a = size_b;
            size_b = temp;
        }
    }

    digit carry = 0;

    // First common digits.
    Py_ssize_t i;
    for (i = 0; i < size_b; i++) {
        carry += aa[i] + bb[i];
        carry >>= PyLong_SHIFT;
    }

    // Digits from longest one only might cause a new digit through carry.
    Py_ssize_t needed = size_a;

    for (; i < size_a; i++) {
        carry += aa[i];
        carry >>= PyLong_SHIFT;

        // No more carry, that means size cannot increase.
        if (carry == 0) {
            break;
        }
    }

    // Final digit needs to be added.
    if (carry) {
        needed = i + 1;
    }

    // Need to keep the old value around, or else we commit use after free potentially.
    PyObject *old = left;

    if (needed > Nuitka_LongGetDigitSize(left)) {
        left = (PyObject *)Nuitka_LongNew(needed);
    } else {
        Py_INCREF(old);
    }

    digit *r = Nuitka_LongGetDigitPointer(left);

    // Now do the real thing, with actual storage to left digits.
    carry = 0;

    // First common digits.
    for (i = 0; i < size_b; i++) {
        carry += aa[i] + bb[i];
        r[i] = carry & PyLong_MASK;
        carry >>= PyLong_SHIFT;
    }
    // Digits from longest one only.
    for (; i < size_a; i++) {
        carry += aa[i];
        r[i] = carry & PyLong_MASK;
        carry >>= PyLong_SHIFT;
    }

    // Final digit from the carry.
    if (carry != 0) {
        r[i] = carry;

        Py_SIZE(left) = i + 1;
    } else {
        Py_SIZE(left) = i;
    }

    // Release reference to old value
    Py_DECREF(old);

    return left;
}

static PyLongObject *_Nuitka_LongSubDigits(digit const *a, Py_ssize_t size_a, digit const *b, Py_ssize_t size_b) {
    // Sign of the result.
    int sign = 1;

    // Make sure we know a is the largest value.
    if (size_a < size_b) {
        sign = -1;

        {
            digit const *temp = a;
            a = b;
            b = temp;
        }

        {
            Py_ssize_t temp = size_a;
            size_a = size_b;
            size_b = temp;
        }
    } else if (size_a == size_b) {
        // Find highest digit where a and b differ:
        Py_ssize_t i = size_a;
        while (--i >= 0 && a[i] == b[i]) {
        }

        if (i < 0) {
#if PYTHON_VERSION < 0x300
            return (PyLongObject *)Nuitka_LongFromCLong(0);
#else
            // For Python3, we have this prepared.
            PyObject *result = Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(0)];
            Py_INCREF(result);
            return (PyLongObject *)result;
#endif
        }

        if (a[i] < b[i]) {
            sign = -1;

            {
                digit const *temp = a;
                a = b;
                b = temp;
            }
        }

        size_a = size_b = i + 1;
    }

    PyLongObject *result = Nuitka_LongNew(size_a);
    CHECK_OBJECT(result);

    digit *r = &result->ob_digit[0];

    digit borrow = 0;

    Py_ssize_t i;
    // First common digits.
    for (i = 0; i < size_b; i++) {
        borrow = a[i] - b[i] - borrow;
        r[i] = borrow & PyLong_MASK;
        borrow >>= PyLong_SHIFT;
        borrow &= 1;
    }
    // Digits from largest one only.
    for (; i < size_a; i++) {
        borrow = a[i] - borrow;
        r[i] = borrow & PyLong_MASK;
        borrow >>= PyLong_SHIFT;
        borrow &= 1;
    }
    assert(borrow == 0);

    // Strip leading zeros.
    while (i > 0 && r[i - 1] == 0) {
        i -= 1;
    }

    Py_SIZE(result) = (sign < 0) ? -i : i;

#if PYTHON_VERSION >= 0x300
    // Normalize small integers.
    if (i <= 1) {
        long ival = MEDIUM_VALUE(result);

        if (ival >= NUITKA_STATIC_SMALLINT_VALUE_MIN && ival <= NUITKA_STATIC_SMALLINT_VALUE_MAX) {
            Py_DECREF(result);

            result = (PyLongObject *)Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(ival)];
            Py_INCREF(result);
        }
    }
#endif

    return result;
}

static PyObject *_Nuitka_LongSubInplaceDigits(PyObject *left, digit const *b, Py_ssize_t size_b, int sign) {
    digit const *a = Nuitka_LongGetDigitPointer(left);
    Py_ssize_t size_a = Nuitka_LongGetDigitSize(left);

    digit const *aa = a;
    digit const *bb = b;

    // Make sure we know a is the largest value.
    if (size_a < size_b) {
        // Invert the sign of the result by swapping the order.
        sign *= -1;

        {
            aa = b;
            bb = a;
        }

        {
            Py_ssize_t temp = size_a;
            size_a = size_b;
            size_b = temp;
        }
    } else if (size_a == size_b) {
        // Find highest digit where a and b differ:
        Py_ssize_t i = size_a;
        while (--i >= 0 && a[i] == b[i]) {
        }

        // TODO: This will benefit a lot by being in a template.
        if (i < 0) {
#if PYTHON_VERSION < 0x300
            PyObject *r = const_long_0;
#else
            PyObject *r = Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(0)];
#endif
            Py_INCREF(r);
            Py_DECREF(left);

            return r;
        }

        if (aa[i] < bb[i]) {
            sign *= -1;

            {
                aa = b;
                bb = a;
            }
        }

        size_a = size_b = i + 1;
    }

    Py_ssize_t needed = size_a;

    // Need to keep the old value around, or else we commit use after free potentially.
    PyObject *old = left;

    if (needed > Nuitka_LongGetDigitSize(left)) {
        left = (PyObject *)Nuitka_LongNew(needed);
    } else {
        Py_INCREF(old);
    }

    digit *r = Nuitka_LongGetDigitPointer(left);

    digit borrow = 0;

    Py_ssize_t i;
    // First common digits.
    for (i = 0; i < size_b; i++) {
        borrow = aa[i] - bb[i] - borrow;
        r[i] = borrow & PyLong_MASK;
        borrow >>= PyLong_SHIFT;
        borrow &= 1;
    }
    // Digits from largest one only.
    for (; i < size_a; i++) {
        borrow = aa[i] - borrow;
        r[i] = borrow & PyLong_MASK;
        borrow >>= PyLong_SHIFT;
        borrow &= 1;
    }
    assert(borrow == 0);

    // Strip leading zeros.
    while (i > 0 && r[i - 1] == 0) {
        i -= 1;
    }

    Py_SIZE(left) = (sign < 0) ? -i : i;

    // Release reference to old value
    Py_DECREF(old);

#if PYTHON_VERSION >= 0x300
    // Normalize small integers.
    if (i <= 1) {
        long ival = MEDIUM_VALUE(left);

        if (ival >= NUITKA_STATIC_SMALLINT_VALUE_MIN && ival <= NUITKA_STATIC_SMALLINT_VALUE_MAX) {
            Py_DECREF(left);

            left = Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(ival)];
            Py_INCREF(left);
        }
    }
#endif

    return left;
}
