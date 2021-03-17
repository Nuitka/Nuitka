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
#ifndef __NUITKA_SAFE_STRING_OPS_H__
#define __NUITKA_SAFE_STRING_OPS_H__

/* Safe to use function to copy a string, will abort program for overflow. */
extern void copyStringSafe(char *buffer, char const *source, size_t buffer_size);
extern void copyStringSafeN(char *buffer, char const *source, size_t n, size_t buffer_size);
/* Safe to use function to append a string, will abort program for overflow. */
extern void appendCharSafe(char *buffer, char c, size_t buffer_size);
extern void appendStringSafe(char *buffer, char const *source, size_t buffer_size);

/* Safe to use functions to append a wide char string, will abort program for overflow. */
extern void appendCharSafeW(wchar_t *target, char c, size_t buffer_size);
extern void appendStringSafeW(wchar_t *target, char const *source, size_t buffer_size);
extern void appendWStringSafeW(wchar_t *target, wchar_t const *source, size_t buffer_size);

/* Expand symbolic paths, containing %TEMP%, %PID% without overflowing. */
extern bool expandWindowsPath(wchar_t *target, wchar_t const *source, size_t buffer_size);

#endif