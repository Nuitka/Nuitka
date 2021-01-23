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
/* WARNING, this code is GENERATED. Modify the template HelperImportHard.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helper for hard import of module "__future__" import. */

extern PyObject *IMPORT_HARD___FUTURE__(void);
/* C helper for hard import of module "_frozen_importlib" import. */

#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x350
extern PyObject *IMPORT_HARD__FROZEN_IMPORTLIB(void);
#endif
/* C helper for hard import of module "_frozen_importlib_external" import. */

#if PYTHON_VERSION >= 0x350
extern PyObject *IMPORT_HARD__FROZEN_IMPORTLIB_EXTERNAL(void);
#endif
/* C helper for hard import of module "importlib" import. */

extern PyObject *IMPORT_HARD_IMPORTLIB(void);
/* C helper for hard import of module "os" import. */

extern PyObject *IMPORT_HARD_OS(void);
/* C helper for hard import of module "site" import. */

extern PyObject *IMPORT_HARD_SITE(void);
/* C helper for hard import of module "sys" import. */

extern PyObject *IMPORT_HARD_SYS(void);
/* C helper for hard import of module "types" import. */

extern PyObject *IMPORT_HARD_TYPES(void);
