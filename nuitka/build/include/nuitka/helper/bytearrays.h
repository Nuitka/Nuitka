//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_BYTEARRAYS_H__
#define __NUITKA_HELPER_BYTEARRAYS_H__

NUITKA_MAY_BE_UNUSED static PyObject *BYTEARRAY_COPY(PyThreadState *tstate, PyObject *bytearray) {
    CHECK_OBJECT(bytearray);
    assert(PyByteArray_CheckExact(bytearray));

    PyObject *result = PyByteArray_FromObject(bytearray);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

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
