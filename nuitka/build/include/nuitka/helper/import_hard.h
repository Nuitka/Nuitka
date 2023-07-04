//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* WARNING, this code is GENERATED. Modify the template HelperImportHard.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helper for hard import of module "__future__" import. */
extern PyObject *IMPORT_HARD___FUTURE__(void);

/* C helper for hard import of module "_frozen_importlib" import. */
#if PYTHON_VERSION >= 0x300
extern PyObject *IMPORT_HARD__FROZEN_IMPORTLIB(void);
#endif

/* C helper for hard import of module "_frozen_importlib_external" import. */
#if PYTHON_VERSION >= 0x350
extern PyObject *IMPORT_HARD__FROZEN_IMPORTLIB_EXTERNAL(void);
#endif

/* C helper for hard import of module "ctypes" import. */
extern PyObject *IMPORT_HARD_CTYPES(void);

/* C helper for hard import of module "ctypes.macholib" import. */
extern PyObject *IMPORT_HARD_CTYPES__MACHOLIB(void);

/* C helper for hard import of module "ctypes.wintypes" import. */
#if defined(_WIN32)
extern PyObject *IMPORT_HARD_CTYPES__WINTYPES(void);
#endif

/* C helper for hard import of module "functools" import. */
extern PyObject *IMPORT_HARD_FUNCTOOLS(void);

/* C helper for hard import of module "importlib" import. */
extern PyObject *IMPORT_HARD_IMPORTLIB(void);

/* C helper for hard import of module "importlib.metadata" import. */
#if PYTHON_VERSION >= 0x380
extern PyObject *IMPORT_HARD_IMPORTLIB__METADATA(void);
#endif

/* C helper for hard import of module "importlib.resources" import. */
#if PYTHON_VERSION >= 0x370
extern PyObject *IMPORT_HARD_IMPORTLIB__RESOURCES(void);
#endif

/* C helper for hard import of module "importlib_metadata" import. */
extern PyObject *IMPORT_HARD_IMPORTLIB_METADATA(void);

/* C helper for hard import of module "io" import. */
extern PyObject *IMPORT_HARD_IO(void);

/* C helper for hard import of module "ntpath" import. */
extern PyObject *IMPORT_HARD_NTPATH(void);

/* C helper for hard import of module "os" import. */
extern PyObject *IMPORT_HARD_OS(void);

/* C helper for hard import of module "pkg_resources" import. */
extern PyObject *IMPORT_HARD_PKG_RESOURCES(void);

/* C helper for hard import of module "pkgutil" import. */
extern PyObject *IMPORT_HARD_PKGUTIL(void);

/* C helper for hard import of module "posixpath" import. */
extern PyObject *IMPORT_HARD_POSIXPATH(void);

/* C helper for hard import of module "site" import. */
extern PyObject *IMPORT_HARD_SITE(void);

/* C helper for hard import of module "sys" import. */
extern PyObject *IMPORT_HARD_SYS(void);

/* C helper for hard import of module "sysconfig" import. */
extern PyObject *IMPORT_HARD_SYSCONFIG(void);

/* C helper for hard import of module "types" import. */
extern PyObject *IMPORT_HARD_TYPES(void);

/* C helper for hard import of module "typing" import. */
#if PYTHON_VERSION >= 0x350
extern PyObject *IMPORT_HARD_TYPING(void);
#endif

/* C helper for hard import of module "unittest" import. */
extern PyObject *IMPORT_HARD_UNITTEST(void);

/* C helper for hard import of module "unittest.mock" import. */
extern PyObject *IMPORT_HARD_UNITTEST__MOCK(void);
