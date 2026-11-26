//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperImportHard.c.j2 instead! */
#pragma once
#ifndef __NUITKA_IMPORT_HARD_H__
#define __NUITKA_IMPORT_HARD_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

extern PyObject *IMPORT_HARD___FUTURE__(void);

#if PYTHON_VERSION >= 0x300
extern PyObject *IMPORT_HARD__FROZEN_IMPORTLIB(void);
#endif

#if PYTHON_VERSION >= 0x350
extern PyObject *IMPORT_HARD__FROZEN_IMPORTLIB_EXTERNAL(void);
#endif

extern PyObject *IMPORT_HARD__IO(void);

extern PyObject *IMPORT_HARD_BUILTINS(void);

extern PyObject *IMPORT_HARD_CTYPES(void);

extern PyObject *IMPORT_HARD_CTYPES___AIX(void);

extern PyObject *IMPORT_HARD_CTYPES___ENDIAN(void);

extern PyObject *IMPORT_HARD_CTYPES__MACHOLIB(void);

extern PyObject *IMPORT_HARD_CTYPES__UTIL(void);

#if defined(_WIN32)
extern PyObject *IMPORT_HARD_CTYPES__WINTYPES(void);
#endif

extern PyObject *IMPORT_HARD_FUNCTOOLS(void);

#if PYTHON_VERSION < 0x300
extern PyObject *IMPORT_HARD_IMP(void);
#endif

extern PyObject *IMPORT_HARD_IMPORTLIB(void);

#if PYTHON_VERSION >= 0x380
extern PyObject *IMPORT_HARD_IMPORTLIB__METADATA(void);
#endif

#if PYTHON_VERSION >= 0x370
extern PyObject *IMPORT_HARD_IMPORTLIB__RESOURCES(void);
#endif

extern PyObject *IMPORT_HARD_IMPORTLIB_METADATA(void);

extern PyObject *IMPORT_HARD_IMPORTLIB_RESOURCES(void);

extern PyObject *IMPORT_HARD_IO(void);

extern PyObject *IMPORT_HARD_NTPATH(void);

extern PyObject *IMPORT_HARD_OS(void);

#if PYTHON_VERSION >= 0x3d0
extern PyObject *IMPORT_HARD_PATHLIB(void);
#endif

#if PYTHON_VERSION >= 0x3d0
extern PyObject *IMPORT_HARD_PATHLIB___ABC(void);
#endif

#if PYTHON_VERSION >= 0x3d0
extern PyObject *IMPORT_HARD_PATHLIB___LOCAL(void);
#endif

extern PyObject *IMPORT_HARD_PKG_RESOURCES(void);

extern PyObject *IMPORT_HARD_PKGUTIL(void);

extern PyObject *IMPORT_HARD_POSIXPATH(void);

extern PyObject *IMPORT_HARD_SITE(void);

extern PyObject *IMPORT_HARD_SYS(void);

extern PyObject *IMPORT_HARD_SYSCONFIG(void);

extern PyObject *IMPORT_HARD_TENSORFLOW(void);

extern PyObject *IMPORT_HARD_TYPES(void);

#if PYTHON_VERSION >= 0x350
extern PyObject *IMPORT_HARD_TYPING(void);
#endif

extern PyObject *IMPORT_HARD_UNITTEST(void);

#if PYTHON_VERSION >= 0x300
extern PyObject *IMPORT_HARD_UNITTEST__MOCK(void);
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
