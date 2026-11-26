//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_DEFINES_H__
#define __NUITKA_DEFINES_H__

#if defined(__GNUC__) || defined(__clang__)
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

#define NUITKA_UNREFERENCED_PARAMETER(parameter) ((void)(parameter))

#if defined(__GNUC__) || defined(__clang__)
#define NUITKA_MAY_ALIAS __attribute__((__may_alias__))
#else
#define NUITKA_MAY_ALIAS
#endif

#include "hedley.h"

#define likely(x) HEDLEY_LIKELY(x)
#define unlikely(x) HEDLEY_UNLIKELY(x)

#define STATIC_ASSERT(expr, msg) HEDLEY_STATIC_ASSERT(expr, msg)

#define NUITKA_NO_RETURN HEDLEY_NO_RETURN

#ifndef __NUITKA_NO_ASSERT__
#define NUITKA_CANNOT_GET_HERE(NAME)                                                                                   \
    fprintf(stderr, "%s : %s\n", __FUNCTION__, #NAME);                                                                 \
    abort();
#else
#define NUITKA_CANNOT_GET_HERE(NAME) abort();
#endif

#ifndef __NUITKA_NO_ASSERT__
#define NUITKA_ONCE(message)                                                                                           \
    static bool _nuitka_once = false;                                                                                  \
    if (unlikely(_nuitka_once)) {                                                                                      \
        NUITKA_CANNOT_GET_HERE(message);                                                                               \
    }                                                                                                                  \
    _nuitka_once = true
#else
#define NUITKA_ONCE(message)
#endif

#define NUITKA_ERROR_EXIT(NAME)                                                                                        \
    fprintf(stderr, "%s : %s\n", __FUNCTION__, #NAME);                                                                 \
    abort();

#if !defined(Py_GIL_DISABLED) || (!_NUITKA_MODULE_MODE && defined(_NUITKA_SYSFLAG_GIL))
#define _NUITKA_GIL_PROTECTED 1
#else
#define _NUITKA_GIL_PROTECTED 0
#endif

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
