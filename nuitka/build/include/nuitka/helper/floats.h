//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_FLOATS_H__
#define __NUITKA_HELPER_FLOATS_H__

#if PYTHON_VERSION >= 0x3a0
#define NUITKA_FLOAT_HAS_FREELIST 1

// Replacement for PyFloat_FromDouble that is faster
extern PyObject *MAKE_FLOAT_FROM_DOUBLE(double value);
#else
#define NUITKA_FLOAT_HAS_FREELIST 0
#define MAKE_FLOAT_FROM_DOUBLE(value) PyFloat_FromDouble(value)
#endif

extern PyObject *TO_FLOAT(PyObject *value);

#endif