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
#ifndef __NUITKA_CONSTANTS_BLOB_H__
#define __NUITKA_CONSTANTS_BLOB_H__

/** Declaration of the constants binary blob.
 *
 * There are multiple ways, the constants binary is accessed, and its
 * definition depends on how that is done.
 *
 * It could be a Windows resource, then it must be a pointer. If it's defined
 * externally in a C file, or at link time with "ld", it must be an array. This
 * hides these facts.
 *
 */

extern void loadConstantsBlob(PyObject **, char const *name);
#ifndef __NUITKA_NO_ASSERT__
extern void checkConstantsBlob(PyObject **, char const *name);
#endif

#endif
