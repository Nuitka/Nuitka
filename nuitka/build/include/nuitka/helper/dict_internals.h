//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_HELPER_DICT_INTERNALS_H__
#define __NUITKA_HELPER_DICT_INTERNALS_H__

/* Shared helpers for the dictionary internals.
 *
 * The implementations are in "HelpersDictionaries.c", which is chained into
 * the same compilation unit, and therefore the declarations are "static" to
 * it. The generated dictionary helpers use them too.
 *
 * This file is included from another C file, help IDEs to still parse it on its own.
 */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Usable fraction of keys.
#define DK_USABLE_FRACTION(n) (((n) << 1) / 3)

#if PYTHON_VERSION < 0x3b0
typedef PyObject *PyDictValues;
#endif

#if PYTHON_VERSION < 0x360
#define DK_ENTRIES_SIZE(keys) (keys->dk_size)
#elif PYTHON_VERSION < 0x3b0
#define DK_ENTRIES_SIZE(keys) DK_USABLE_FRACTION(DK_SIZE(keys))
#else
#define DK_ENTRIES_SIZE(keys) (keys->dk_nentries)
#endif

// More than 2/3 of the keys are used, i.e. no space is wasted.
#if PYTHON_VERSION < 0x360
#define IS_COMPACT(dict_mp) (dict_mp->ma_used >= (dict_mp->ma_keys->dk_size * 2) / 3)
#else
#define IS_COMPACT(dict_mp) (dict_mp->ma_used >= (dict_mp->ma_keys->dk_nentries * 2) / 3)
#endif

#if PYTHON_VERSION >= 0x300 && (NUITKA_DICT_HAS_FREELIST || !_NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT)
static PyDictObject *_Nuitka_AllocatePyDictObject(PyThreadState *tstate);
#endif
#if PYTHON_VERSION >= 0x360
static PyDictKeysObject *_Nuitka_AllocatePyDictKeysObject(PyThreadState *tstate, Py_ssize_t keys_size);
static Py_ssize_t _Nuitka_Py_PyDict_KeysSize(PyDictKeysObject *keys);
#endif
static PyDictValues *_Nuitka_PyDict_new_values(Py_ssize_t size);

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
