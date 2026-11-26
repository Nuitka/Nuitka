//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_DLL_EXPORT_H__
#define __NUITKA_DLL_EXPORT_H__

#if !defined(__cplusplus)
#include <stdbool.h>
#endif
#if defined(_WIN32)
#include <wchar.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32)
typedef wchar_t nuitka_dll_char_t;
#else
typedef char nuitka_dll_char_t;
#endif

#if defined(NUITKA_DLL_FUNCTION)
#define NUITKA_DLL_API NUITKA_DLL_FUNCTION
#elif defined(_WIN32)
#define NUITKA_DLL_API __declspec(dllimport)
#else
#define NUITKA_DLL_API
#endif

typedef int (*nuitka_dll_function_ptr)(int argc, nuitka_dll_char_t **argv, nuitka_dll_char_t const *dll_filename,
                                       bool fork_only);
typedef nuitka_dll_function_ptr nuitka_dll_run_code_fn;

NUITKA_DLL_API int run_code(int argc, nuitka_dll_char_t **argv, nuitka_dll_char_t const *dll_filename, bool fork_only);

#ifdef __cplusplus
}
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
