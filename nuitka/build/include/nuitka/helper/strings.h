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
#ifndef __NUITKA_STRINGS_H__
#define __NUITKA_STRINGS_H__

#if PYTHON_VERSION < 0x300
extern PyObject *STR_JOIN(PyObject *str, PyObject *iterable);
extern PyObject *STR_PARTITION(PyObject *str, PyObject *sep);
extern PyObject *STR_RPARTITION(PyObject *str, PyObject *sep);
extern PyObject *STR_STRIP1(PyObject *str);
extern PyObject *STR_LSTRIP1(PyObject *str);
extern PyObject *STR_RSTRIP1(PyObject *str);
extern PyObject *STR_STRIP2(PyObject *str, PyObject *chars);
extern PyObject *STR_LSTRIP2(PyObject *str, PyObject *chars);
extern PyObject *STR_RSTRIP2(PyObject *str, PyObject *chars);
#endif

extern PyObject *UNICODE_JOIN(PyObject *str, PyObject *iterable);
extern PyObject *UNICODE_PARTITION(PyObject *str, PyObject *sep);
extern PyObject *UNICODE_RPARTITION(PyObject *str, PyObject *sep);
extern PyObject *UNICODE_STRIP1(PyObject *str);
extern PyObject *UNICODE_LSTRIP1(PyObject *str);
extern PyObject *UNICODE_RSTRIP1(PyObject *str);
extern PyObject *UNICODE_STRIP2(PyObject *str, PyObject *chars);
extern PyObject *UNICODE_LSTRIP2(PyObject *str, PyObject *chars);
extern PyObject *UNICODE_RSTRIP2(PyObject *str, PyObject *chars);

#endif