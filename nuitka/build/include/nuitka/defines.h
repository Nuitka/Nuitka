//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_DEFINES_H__
#define __NUITKA_DEFINES_H__

/* A way to not give warnings about things that are declared, but might not
 * be used like in-line helper functions in headers or static per module
 * variables from headers.
 */
#if defined(__GNUC__) || defined(__clang__)
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

/* A way to make a struct type alias any other type, disabling strict-aliasing
 * optimizations for accesses through it.
 */
#if defined(__GNUC__) || defined(__clang__)
#define NUITKA_MAY_ALIAS __attribute__((__may_alias__))
#else
#define NUITKA_MAY_ALIAS
#endif

#include "hedley.h"

/* Use annotations for branch prediction. They still make sense as the L1
 * cache space is saved.
 */

#define likely(x) HEDLEY_LIKELY(x)
#define unlikely(x) HEDLEY_UNLIKELY(x)

#define STATIC_ASSERT(expr, msg) HEDLEY_STATIC_ASSERT(expr, msg)

/* A way to indicate that a specific function won't return, so the C compiler
 * can create better code.
 */

#define NUITKA_NO_RETURN HEDLEY_NO_RETURN

/* This is used to indicate code control flows we know cannot happen. */
#ifndef __NUITKA_NO_ASSERT__
#define NUITKA_CANNOT_GET_HERE(NAME)                                                                                   \
    PRINT_FORMAT("%s : %s\n", __FUNCTION__, #NAME);                                                                    \
    abort();
#else
#define NUITKA_CANNOT_GET_HERE(NAME) abort();
#endif

#define NUITKA_ERROR_EXIT(NAME)                                                                                        \
    PRINT_FORMAT("%s : %s\n", __FUNCTION__, #NAME);                                                                    \
    abort();

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
