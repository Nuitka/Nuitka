//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_BYTES_H__
#define __NUITKA_HELPER_BYTES_H__

#if PYTHON_VERSION >= 0x3a0
#define NUITKA_BYTES_HAS_FREELIST 1
extern PyObject *Nuitka_Bytes_FromStringAndSize(const char *data, Py_ssize_t size);
#else
#define NUITKA_BYTES_HAS_FREELIST 0
#define Nuitka_Bytes_FromStringAndSize PyBytes_FromStringAndSize
#endif

extern void Nuitka_Bytes_AsStringAndSize(PyObject *obj, char **s, Py_ssize_t *len);
extern char *Nuitka_Bytes_AsString(PyObject *obj);

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.gnu.org/licenses/agpl.txt
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
