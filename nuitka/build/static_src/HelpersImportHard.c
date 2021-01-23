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

PyObject *IMPORT_HARD___FUTURE__(void) {
    static PyObject *module___future__ = NULL;

    if (module___future__ == NULL) {
        module___future__ = PyImport_ImportModule("__future__");
    }

    CHECK_OBJECT(module___future__);

    return module___future__;
}
/* C helper for hard import of module "_frozen_importlib" import. */

#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x350
PyObject *IMPORT_HARD__FROZEN_IMPORTLIB(void) {
    static PyObject *module__frozen_importlib = NULL;

    if (module__frozen_importlib == NULL) {
        module__frozen_importlib = PyImport_ImportModule("_frozen_importlib");
    }

    CHECK_OBJECT(module__frozen_importlib);

    return module__frozen_importlib;
}
#endif
/* C helper for hard import of module "_frozen_importlib_external" import. */

#if PYTHON_VERSION >= 0x350
PyObject *IMPORT_HARD__FROZEN_IMPORTLIB_EXTERNAL(void) {
    static PyObject *module__frozen_importlib_external = NULL;

    if (module__frozen_importlib_external == NULL) {
        module__frozen_importlib_external = PyImport_ImportModule("_frozen_importlib_external");
    }

    CHECK_OBJECT(module__frozen_importlib_external);

    return module__frozen_importlib_external;
}
#endif
/* C helper for hard import of module "importlib" import. */

PyObject *IMPORT_HARD_IMPORTLIB(void) {
    static PyObject *module_importlib = NULL;

    if (module_importlib == NULL) {
        module_importlib = PyImport_ImportModule("importlib");
    }

    CHECK_OBJECT(module_importlib);

    return module_importlib;
}
/* C helper for hard import of module "os" import. */

PyObject *IMPORT_HARD_OS(void) {
    static PyObject *module_os = NULL;

    if (module_os == NULL) {
        module_os = PyImport_ImportModule("os");
    }

    CHECK_OBJECT(module_os);

    return module_os;
}
/* C helper for hard import of module "site" import. */

PyObject *IMPORT_HARD_SITE(void) {
    static PyObject *module_site = NULL;

    if (module_site == NULL) {
        module_site = PyImport_ImportModule("site");
    }

    CHECK_OBJECT(module_site);

    return module_site;
}
/* C helper for hard import of module "sys" import. */

PyObject *IMPORT_HARD_SYS(void) {
    static PyObject *module_sys = NULL;

    if (module_sys == NULL) {
        module_sys = PyImport_ImportModule("sys");
    }

    CHECK_OBJECT(module_sys);

    return module_sys;
}
/* C helper for hard import of module "types" import. */

PyObject *IMPORT_HARD_TYPES(void) {
    static PyObject *module_types = NULL;

    if (module_types == NULL) {
        module_types = PyImport_ImportModule("types");
    }

    CHECK_OBJECT(module_types);

    return module_types;
}
