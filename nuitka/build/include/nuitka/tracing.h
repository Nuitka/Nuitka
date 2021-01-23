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
#ifndef __NUITKA_TRACING_H__
#define __NUITKA_TRACING_H__

/* Stupid tracing, intended to help where debugging is not an option
 * and to give kind of progress record of startup and the running of
 * the program.
 */

#ifdef _NUITKA_TRACE
#define NUITKA_PRINT_TRACE(value)                                                                                      \
    {                                                                                                                  \
        puts(value);                                                                                                   \
        fflush(stdout);                                                                                                \
    }
#define NUITKA_PRINTF_TRACE(...)                                                                                       \
    {                                                                                                                  \
        printf(__VA_ARGS__);                                                                                           \
        fflush(stdout);                                                                                                \
    }
#else
#define NUITKA_PRINT_TRACE(value)
#define NUITKA_PRINTF_TRACE(...)
#endif

#endif
