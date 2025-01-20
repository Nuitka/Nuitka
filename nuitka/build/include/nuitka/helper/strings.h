//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_STRINGS_H__
#define __NUITKA_STRINGS_H__

#if PYTHON_VERSION < 0x300
extern PyObject *STR_JOIN(PyThreadState *tstate, PyObject *str, PyObject *iterable);
#endif

extern PyObject *UNICODE_JOIN(PyThreadState *tstate, PyObject *str, PyObject *iterable);
extern PyObject *UNICODE_PARTITION(PyThreadState *tstate, PyObject *str, PyObject *sep);
extern PyObject *UNICODE_RPARTITION(PyThreadState *tstate, PyObject *str, PyObject *sep);

extern PyObject *NuitkaUnicode_FromWideChar(wchar_t const *str, Py_ssize_t size);

#endif
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
