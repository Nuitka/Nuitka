//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_SEQUENCES_H__
#define __NUITKA_HELPER_SEQUENCES_H__

// TODO: Provide enhanced form of PySequence_Contains with less overhead as well.

extern bool SEQUENCE_SET_ITEM(PyObject *sequence, Py_ssize_t index, PyObject *value);

extern Py_ssize_t Nuitka_PyObject_Size(PyObject *sequence);

#endif
