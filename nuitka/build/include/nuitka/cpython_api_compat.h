//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_CPYTHON_API_COMPAT_H__
#define __NUITKA_CPYTHON_API_COMPAT_H__

/* CPython uses "initproc" for the "tp_init" slot type, and Python2 uses
 * "initfunc" and "initstate" for module init related declarations. Rename
 * them to our own names while the CPython headers are included, so that we
 * have stable names for them, and so that Python2 modules named "proc" can
 * define their "initproc" init function without conflicts.
   spell-checker: ignore initproc,initfunc
 */
#define initproc python_init_proc
#define initfunc python_init_func
#define initstate python_initstate
#include <Python.h>
#undef initproc
#undef initfunc
#undef initstate

// The pycore headers require these, but "Python.h" does not provide them.
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

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
