//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_HELPER_REPEAT_HELPERS_H__
#define __NUITKA_HELPER_REPEAT_HELPERS_H__

/* Shared helpers for the sequence repetition, i.e. "seq * n".
 *
 * The implementations are in "HelpersOperationBinaryMultUtils.c", which is
 * chained into the same compilation unit, and therefore the declarations are
 * "static" to it. The generated in-place multiply helpers use them too.
 *
 * This file is included from another C file, help IDEs to still parse it on its own.
 */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static Py_ssize_t CONVERT_LONG_TO_REPEAT_FACTOR(PyObject *value);
static Py_ssize_t CONVERT_TO_REPEAT_FACTOR(PyObject *value);
static PyObject *SEQUENCE_REPEAT(ssizeargfunc repeatfunc, PyObject *seq, PyObject *n);

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
