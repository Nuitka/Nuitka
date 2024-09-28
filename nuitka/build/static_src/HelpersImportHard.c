//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperImportHard.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helper for hard import of module "__future__" import. */
PyObject *IMPORT_HARD___FUTURE__(void) {
    static PyObject *module_import_hard___future__ = NULL;

    if (module_import_hard___future__ == NULL) {
        module_import_hard___future__ = PyImport_ImportModule("__future__");

        if (unlikely(module_import_hard___future__ == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of '__future__'");
        }
    }

    return module_import_hard___future__;
}

/* C helper for hard import of module "_frozen_importlib" import. */
#if PYTHON_VERSION >= 0x300
PyObject *IMPORT_HARD__FROZEN_IMPORTLIB(void) {
    static PyObject *module_import_hard__frozen_importlib = NULL;

    if (module_import_hard__frozen_importlib == NULL) {
        module_import_hard__frozen_importlib = PyImport_ImportModule("_frozen_importlib");

        if (unlikely(module_import_hard__frozen_importlib == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of '_frozen_importlib'");
        }
    }

    return module_import_hard__frozen_importlib;
}
#endif

/* C helper for hard import of module "_frozen_importlib_external" import. */
#if PYTHON_VERSION >= 0x350
PyObject *IMPORT_HARD__FROZEN_IMPORTLIB_EXTERNAL(void) {
    static PyObject *module_import_hard__frozen_importlib_external = NULL;

    if (module_import_hard__frozen_importlib_external == NULL) {
        module_import_hard__frozen_importlib_external = PyImport_ImportModule("_frozen_importlib_external");

        if (unlikely(module_import_hard__frozen_importlib_external == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of '_frozen_importlib_external'");
        }
    }

    return module_import_hard__frozen_importlib_external;
}
#endif

/* C helper for hard import of module "_io" import. */
PyObject *IMPORT_HARD__IO(void) {
    static PyObject *module_import_hard__io = NULL;

    if (module_import_hard__io == NULL) {
        module_import_hard__io = PyImport_ImportModule("_io");

        if (unlikely(module_import_hard__io == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of '_io'");
        }
    }

    return module_import_hard__io;
}

/* C helper for hard import of module "builtins" import. */
PyObject *IMPORT_HARD_BUILTINS(void) {
    static PyObject *module_import_hard_builtins = NULL;

    if (module_import_hard_builtins == NULL) {
        module_import_hard_builtins = PyImport_ImportModule("builtins");

        if (unlikely(module_import_hard_builtins == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'builtins'");
        }
    }

    return module_import_hard_builtins;
}

/* C helper for hard import of module "ctypes" import. */
PyObject *IMPORT_HARD_CTYPES(void) {
    static PyObject *module_import_hard_ctypes = NULL;

    if (module_import_hard_ctypes == NULL) {
        module_import_hard_ctypes = PyImport_ImportModule("ctypes");

        if (unlikely(module_import_hard_ctypes == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'ctypes'");
        }
    }

    return module_import_hard_ctypes;
}

/* C helper for hard import of module "ctypes.macholib" import. */
PyObject *IMPORT_HARD_CTYPES__MACHOLIB(void) {
    static PyObject *module_import_hard_ctypes__macholib = NULL;

    if (module_import_hard_ctypes__macholib == NULL) {
        module_import_hard_ctypes__macholib = PyImport_ImportModule("ctypes.macholib");

        if (unlikely(module_import_hard_ctypes__macholib == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'ctypes.macholib'");
        }
    }

    return module_import_hard_ctypes__macholib;
}

/* C helper for hard import of module "ctypes.wintypes" import. */
#if defined(_WIN32)
PyObject *IMPORT_HARD_CTYPES__WINTYPES(void) {
    static PyObject *module_import_hard_ctypes__wintypes = NULL;

    if (module_import_hard_ctypes__wintypes == NULL) {
        module_import_hard_ctypes__wintypes = PyImport_ImportModule("ctypes.wintypes");

        if (unlikely(module_import_hard_ctypes__wintypes == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'ctypes.wintypes'");
        }
    }

    return module_import_hard_ctypes__wintypes;
}
#endif

/* C helper for hard import of module "functools" import. */
PyObject *IMPORT_HARD_FUNCTOOLS(void) {
    static PyObject *module_import_hard_functools = NULL;

    if (module_import_hard_functools == NULL) {
        module_import_hard_functools = PyImport_ImportModule("functools");

        if (unlikely(module_import_hard_functools == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'functools'");
        }
    }

    return module_import_hard_functools;
}

/* C helper for hard import of module "importlib" import. */
PyObject *IMPORT_HARD_IMPORTLIB(void) {
    static PyObject *module_import_hard_importlib = NULL;

    if (module_import_hard_importlib == NULL) {
        module_import_hard_importlib = PyImport_ImportModule("importlib");

        if (unlikely(module_import_hard_importlib == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'importlib'");
        }
    }

    return module_import_hard_importlib;
}

/* C helper for hard import of module "importlib.metadata" import. */
#if PYTHON_VERSION >= 0x380
PyObject *IMPORT_HARD_IMPORTLIB__METADATA(void) {
    static PyObject *module_import_hard_importlib__metadata = NULL;

    if (module_import_hard_importlib__metadata == NULL) {
        module_import_hard_importlib__metadata = PyImport_ImportModule("importlib.metadata");

        if (unlikely(module_import_hard_importlib__metadata == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'importlib.metadata'");
        }
    }

    return module_import_hard_importlib__metadata;
}
#endif

/* C helper for hard import of module "importlib.resources" import. */
#if PYTHON_VERSION >= 0x370
PyObject *IMPORT_HARD_IMPORTLIB__RESOURCES(void) {
    static PyObject *module_import_hard_importlib__resources = NULL;

    if (module_import_hard_importlib__resources == NULL) {
        module_import_hard_importlib__resources = PyImport_ImportModule("importlib.resources");

        if (unlikely(module_import_hard_importlib__resources == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'importlib.resources'");
        }
    }

    return module_import_hard_importlib__resources;
}
#endif

/* C helper for hard import of module "importlib_metadata" import. */
PyObject *IMPORT_HARD_IMPORTLIB_METADATA(void) {
    static PyObject *module_import_hard_importlib_metadata = NULL;

    if (module_import_hard_importlib_metadata == NULL) {
        module_import_hard_importlib_metadata = PyImport_ImportModule("importlib_metadata");

        if (unlikely(module_import_hard_importlib_metadata == NULL)) {
            return NULL;
        }
    }

    return module_import_hard_importlib_metadata;
}

/* C helper for hard import of module "importlib_resources" import. */
PyObject *IMPORT_HARD_IMPORTLIB_RESOURCES(void) {
    static PyObject *module_import_hard_importlib_resources = NULL;

    if (module_import_hard_importlib_resources == NULL) {
        module_import_hard_importlib_resources = PyImport_ImportModule("importlib_resources");

        if (unlikely(module_import_hard_importlib_resources == NULL)) {
            return NULL;
        }
    }

    return module_import_hard_importlib_resources;
}

/* C helper for hard import of module "io" import. */
PyObject *IMPORT_HARD_IO(void) {
    static PyObject *module_import_hard_io = NULL;

    if (module_import_hard_io == NULL) {
        module_import_hard_io = PyImport_ImportModule("io");

        if (unlikely(module_import_hard_io == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'io'");
        }
    }

    return module_import_hard_io;
}

/* C helper for hard import of module "ntpath" import. */
PyObject *IMPORT_HARD_NTPATH(void) {
    static PyObject *module_import_hard_ntpath = NULL;

    if (module_import_hard_ntpath == NULL) {
        module_import_hard_ntpath = PyImport_ImportModule("ntpath");

        if (unlikely(module_import_hard_ntpath == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'ntpath'");
        }
    }

    return module_import_hard_ntpath;
}

/* C helper for hard import of module "os" import. */
PyObject *IMPORT_HARD_OS(void) {
    static PyObject *module_import_hard_os = NULL;

    if (module_import_hard_os == NULL) {
        module_import_hard_os = PyImport_ImportModule("os");

        if (unlikely(module_import_hard_os == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'os'");
        }
    }

    return module_import_hard_os;
}

/* C helper for hard import of module "pkg_resources" import. */
PyObject *IMPORT_HARD_PKG_RESOURCES(void) {
    static PyObject *module_import_hard_pkg_resources = NULL;

    if (module_import_hard_pkg_resources == NULL) {
        module_import_hard_pkg_resources = PyImport_ImportModule("pkg_resources");

        if (unlikely(module_import_hard_pkg_resources == NULL)) {
            return NULL;
        }
    }

    return module_import_hard_pkg_resources;
}

/* C helper for hard import of module "pkgutil" import. */
PyObject *IMPORT_HARD_PKGUTIL(void) {
    static PyObject *module_import_hard_pkgutil = NULL;

    if (module_import_hard_pkgutil == NULL) {
        module_import_hard_pkgutil = PyImport_ImportModule("pkgutil");

        if (unlikely(module_import_hard_pkgutil == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'pkgutil'");
        }
    }

    return module_import_hard_pkgutil;
}

/* C helper for hard import of module "posixpath" import. */
PyObject *IMPORT_HARD_POSIXPATH(void) {
    static PyObject *module_import_hard_posixpath = NULL;

    if (module_import_hard_posixpath == NULL) {
        module_import_hard_posixpath = PyImport_ImportModule("posixpath");

        if (unlikely(module_import_hard_posixpath == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'posixpath'");
        }
    }

    return module_import_hard_posixpath;
}

/* C helper for hard import of module "site" import. */
PyObject *IMPORT_HARD_SITE(void) {
    static PyObject *module_import_hard_site = NULL;

    if (module_import_hard_site == NULL) {
        module_import_hard_site = PyImport_ImportModule("site");

        if (unlikely(module_import_hard_site == NULL)) {
            return NULL;
        }
    }

    return module_import_hard_site;
}

/* C helper for hard import of module "sys" import. */
PyObject *IMPORT_HARD_SYS(void) {
    static PyObject *module_import_hard_sys = NULL;

    if (module_import_hard_sys == NULL) {
        module_import_hard_sys = PyImport_ImportModule("sys");

        if (unlikely(module_import_hard_sys == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'sys'");
        }
    }

    return module_import_hard_sys;
}

/* C helper for hard import of module "sysconfig" import. */
PyObject *IMPORT_HARD_SYSCONFIG(void) {
    static PyObject *module_import_hard_sysconfig = NULL;

    if (module_import_hard_sysconfig == NULL) {
        module_import_hard_sysconfig = PyImport_ImportModule("sysconfig");

        if (unlikely(module_import_hard_sysconfig == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'sysconfig'");
        }
    }

    return module_import_hard_sysconfig;
}

/* C helper for hard import of module "tensorflow" import. */
PyObject *IMPORT_HARD_TENSORFLOW(void) {
    static PyObject *module_import_hard_tensorflow = NULL;

    if (module_import_hard_tensorflow == NULL) {
        module_import_hard_tensorflow = PyImport_ImportModule("tensorflow");

        if (unlikely(module_import_hard_tensorflow == NULL)) {
            return NULL;
        }
    }

    return module_import_hard_tensorflow;
}

/* C helper for hard import of module "types" import. */
PyObject *IMPORT_HARD_TYPES(void) {
    static PyObject *module_import_hard_types = NULL;

    if (module_import_hard_types == NULL) {
        module_import_hard_types = PyImport_ImportModule("types");

        if (unlikely(module_import_hard_types == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'types'");
        }
    }

    return module_import_hard_types;
}

/* C helper for hard import of module "typing" import. */
#if PYTHON_VERSION >= 0x350
PyObject *IMPORT_HARD_TYPING(void) {
    static PyObject *module_import_hard_typing = NULL;

    if (module_import_hard_typing == NULL) {
        module_import_hard_typing = PyImport_ImportModule("typing");

        if (unlikely(module_import_hard_typing == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'typing'");
        }
    }

    return module_import_hard_typing;
}
#endif

/* C helper for hard import of module "unittest" import. */
PyObject *IMPORT_HARD_UNITTEST(void) {
    static PyObject *module_import_hard_unittest = NULL;

    if (module_import_hard_unittest == NULL) {
        module_import_hard_unittest = PyImport_ImportModule("unittest");

        if (unlikely(module_import_hard_unittest == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'unittest'");
        }
    }

    return module_import_hard_unittest;
}

/* C helper for hard import of module "unittest.mock" import. */
#if PYTHON_VERSION >= 0x300
PyObject *IMPORT_HARD_UNITTEST__MOCK(void) {
    static PyObject *module_import_hard_unittest__mock = NULL;

    if (module_import_hard_unittest__mock == NULL) {
        module_import_hard_unittest__mock = PyImport_ImportModule("unittest.mock");

        if (unlikely(module_import_hard_unittest__mock == NULL)) {
#ifndef __NUITKA_NO_ASSERT__
            PyErr_PrintEx(0);
#endif
            NUITKA_ERROR_EXIT("Unexpected failure of hard import of 'unittest.mock'");
        }
    }

    return module_import_hard_unittest__mock;
}
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
