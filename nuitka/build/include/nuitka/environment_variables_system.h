//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_ENVIRONMENT_VARIABLES_SYSTEM_H__
#define __NUITKA_ENVIRONMENT_VARIABLES_SYSTEM_H__

#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#include "nuitka/filesystem_paths.h"

// Helpers for working with environment variables in a portable way. This mainly
// abstracts the string type differences between Win32 and non-Win32 environment
// variables.
#if defined(_WIN32)
#define environment_char_t wchar_t
#define compareEnvironmentString(a, b) wcscmp(a, b)
#define makeEnvironmentLiteral(x) L##x
#else
#define environment_char_t char
#define compareEnvironmentString(a, b) strcmp(a, b)
#define makeEnvironmentLiteral(x) x
#endif

extern environment_char_t const *getEnvironmentVariable(char const *name);
extern void setEnvironmentVariable(char const *name, environment_char_t const *value);
extern void setEnvironmentVariableFromLong(char const *name, long value);
extern void setEnvironmentVariableFromFilename(char const *name, filename_char_t const *value);
extern void unsetEnvironmentVariable(char const *name);

#endif
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
