//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_HELPER_SEQUENCES_H__
#define __NUITKA_HELPER_SEQUENCES_H__

#ifdef __IDE_ONLY__
#include "nuitka/checkers.h"
#include "nuitka/constants.h"
#include "nuitka/cpython_api_compat.h"
#include "nuitka/defines.h"
#include "nuitka/helper/attributes.h"
#endif

#include "nuitka/helper/attributes.h"

// TODO: Provide enhanced form of PySequence_Contains with less overhead as well.

extern bool SEQUENCE_SET_ITEM(PyObject *sequence, Py_ssize_t index, PyObject *value);

extern Py_ssize_t Nuitka_PyObject_Size(PyObject *sequence);
extern Py_ssize_t Nuitka_PyObject_LengthHint(PyObject *sequence, Py_ssize_t default_value);

NUITKA_MAY_BE_UNUSED static int Nuitka_PySequence_Check(PyObject *candidate) {
    CHECK_OBJECT(candidate);

#if PYTHON_VERSION < 0x300
    // Old-style instances are sequences only if they provide "__getitem__".
    if (PyInstance_Check(candidate)) {
        return HAS_ATTR_BOOL(PyThreadState_GET(), candidate, const_str_plain___getitem__) ? 1 : 0;
    }
#endif

#if PYTHON_VERSION < 0x270
    // Python 2.6 used "PyObject_IsInstance" here, not "PyDict_Check".
    if (Nuitka_Object_IsInstance(PyThreadState_GET(), candidate, (PyObject *)&PyDict_Type)) {
        return 0;
    }
#endif

    PyTypeObject *type = Py_TYPE(candidate);

    if (type->tp_as_sequence == NULL || type->tp_as_sequence->sq_item == NULL) {
        return 0;
    }

#if PYTHON_VERSION >= 0x270
    // Dictionaries are excluded like in CPython's "PySequence_Check".
    return !PyType_FastSubclass(type, Py_TPFLAGS_DICT_SUBCLASS);
#else
    return 1;
#endif
}

NUITKA_MAY_BE_UNUSED static int Nuitka_PyObject_HasLen(PyObject *o) {
    return (Py_TYPE(o)->tp_as_sequence && Py_TYPE(o)->tp_as_sequence->sq_length) ||
           (Py_TYPE(o)->tp_as_mapping && Py_TYPE(o)->tp_as_mapping->mp_length);
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
