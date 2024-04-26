#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Templates for the constants handling.

"""

template_constants_reading = r"""
#include "nuitka/prelude.h"
#include "structseq.h"

#include "build_definitions.h"

// Global constants storage
PyObject *global_constants[%(global_constants_count)d];

// Sentinel PyObject to be used for all our call iterator endings. It will
// become a PyCObject pointing to NULL. It's address is unique, and that's
// enough for us to use it as sentinel value.
PyObject *_sentinel_value = NULL;

PyObject *Nuitka_dunder_compiled_value = NULL;


#ifdef _NUITKA_STANDALONE
extern PyObject *getStandaloneSysExecutablePath(PyObject *basename);

NUITKA_MAY_BE_UNUSED static PyObject *STRIP_DIRNAME(PyObject *path) {
#if PYTHON_VERSION < 0x300
    char const *path_cstr = PyString_AS_STRING(path);

#ifdef _WIN32
    char const *last_sep = strrchr(path_cstr, '\\');
#else
    char const *last_sep = strrchr(path_cstr, '/');
#endif
    if (unlikely(last_sep == NULL)) {
        Py_INCREF(path);
        return path;
    }

    return PyString_FromStringAndSize(path_cstr, last_sep - path_cstr);
#else
#ifdef _WIN32
    Py_ssize_t dot_index = PyUnicode_Find(path, const_str_backslash, 0, PyUnicode_GetLength(path), -1);
#else
    Py_ssize_t dot_index = PyUnicode_Find(path, const_str_slash, 0, PyUnicode_GetLength(path), -1);
#endif
    if (likely(dot_index != -1)) {
        return PyUnicode_Substring(path, 0, dot_index);
    } else {
        Py_INCREF(path);
        return path;
    }
#endif
}
#endif

extern void setDistributionsMetadata(PyObject *metadata_values);

// We provide the sys.version info shortcut as a global value here for ease of use.
PyObject *Py_SysVersionInfo = NULL;

static void _createGlobalConstants(PyThreadState *tstate) {
    // We provide the sys.version info shortcut as a global value here for ease of use.
    Py_SysVersionInfo = Nuitka_SysGetObject("version_info");

    // The empty name means global.
    loadConstantsBlob(tstate, &global_constants[0], "");

#if _NUITKA_EXE
    /* Set the "sys.executable" path to the original CPython executable or point to inside the
       distribution for standalone. */
    Nuitka_SysSetObject(
        "executable",
#ifndef _NUITKA_STANDALONE
        %(sys_executable)s
#else
        getStandaloneSysExecutablePath(%(sys_executable)s)
#endif
    );

#ifndef _NUITKA_STANDALONE
    /* Set the "sys.prefix" path to the original one. */
    Nuitka_SysSetObject(
        "prefix",
        %(sys_prefix)s
    );

    /* Set the "sys.prefix" path to the original one. */
    Nuitka_SysSetObject(
        "exec_prefix",
        %(sys_exec_prefix)s
    );


#if PYTHON_VERSION >= 0x300
    /* Set the "sys.base_prefix" path to the original one. */
    Nuitka_SysSetObject(
        "base_prefix",
        %(sys_base_prefix)s
    );

    /* Set the "sys.exec_base_prefix" path to the original one. */
    Nuitka_SysSetObject(
        "base_exec_prefix",
        %(sys_base_exec_prefix)s
    );

#endif
#endif
#endif

    static PyTypeObject Nuitka_VersionInfoType;

    // Same fields as "sys.version_info" except no serial number.
    static PyStructSequence_Field Nuitka_VersionInfoFields[] = {
        {(char *)"major", (char *)"Major release number"},
        {(char *)"minor", (char *)"Minor release number"},
        {(char *)"micro", (char *)"Micro release number"},
        {(char *)"releaselevel", (char *)"'alpha', 'beta', 'candidate', or 'release'"},
        {(char *)"containing_dir", (char *)"directory of the containing binary"},
        {(char *)"standalone", (char *)"boolean indicating standalone mode usage"},
        {(char *)"onefile", (char *)"boolean indicating onefile mode usage"},
        {(char *)"macos_bundle_mode", (char *)"boolean indicating macOS app bundle mode usage"},
        {(char *)"no_asserts", (char *)"boolean indicating --python-flag=no_asserts usage"},
        {(char *)"no_docstrings", (char *)"boolean indicating --python-flag=no_docstrings usage"},
        {(char *)"no_annotations", (char *)"boolean indicating --python-flag=no_annotations usage"},
        {(char *)"module", (char *)"boolean indicating --module usage"},
        {(char *)"main", (char *)"name of main module at runtime"},
        {0}
    };

    static PyStructSequence_Desc Nuitka_VersionInfoDesc = {
        (char *)"__nuitka_version__",                                       /* name */
        (char *)"__compiled__\\n\\nVersion information as a named tuple.",  /* doc */
        Nuitka_VersionInfoFields,                                           /* fields */
        sizeof(Nuitka_VersionInfoFields) / sizeof(PyStructSequence_Field)-1 /* count */
    };

    PyStructSequence_InitType(&Nuitka_VersionInfoType, &Nuitka_VersionInfoDesc);

    Nuitka_dunder_compiled_value = PyStructSequence_New(&Nuitka_VersionInfoType);
    assert(Nuitka_dunder_compiled_value != NULL);

    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 0, PyInt_FromLong(%(nuitka_version_major)s));
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 1, PyInt_FromLong(%(nuitka_version_minor)s));
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 2, PyInt_FromLong(%(nuitka_version_micro)s));

    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 3, Nuitka_String_FromString("%(nuitka_version_level)s"));

    PyObject *binary_directory = getContainingDirectoryObject(false);
    binary_directory = OS_PATH_ABSPATH(tstate, binary_directory);
#ifdef _NUITKA_STANDALONE
#ifndef _NUITKA_ONEFILE_MODE
    binary_directory = STRIP_DIRNAME(binary_directory);
#endif

#ifdef _NUITKA_MACOS_BUNDLE
    binary_directory = STRIP_DIRNAME(binary_directory);
    binary_directory = STRIP_DIRNAME(binary_directory);
#endif
#endif

    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 4, binary_directory);

#ifdef _NUITKA_STANDALONE
    PyObject *is_standalone_mode = Py_True;
#else
    PyObject *is_standalone_mode = Py_False;
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 5, is_standalone_mode);
#ifdef _NUITKA_ONEFILE_MODE
    PyObject *is_onefile_mode = Py_True;
#else
    PyObject *is_onefile_mode = Py_False;
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 6, is_onefile_mode);

#ifdef _NUITKA_MACOS_BUNDLE
    PyObject *is_macos_bundle_mode = Py_True;
#else
    PyObject *is_macos_bundle_mode = Py_False;
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 7, is_macos_bundle_mode);

#if _NUITKA_NO_ASSERTS == 1
    PyObject *is_no_asserts = Py_True;
#else
    PyObject *is_no_asserts = Py_False;
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 8, is_no_asserts);

#if _NUITKA_NO_DOCSTRINGS == 1
    PyObject *is_no_docstrings = Py_True;
#else
    PyObject *is_no_docstrings = Py_False;
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 9, is_no_docstrings);

#if _NUITKA_NO_ANNOTATIONS == 1
    PyObject *is_no_annotations = Py_True;
#else
    PyObject *is_no_annotations = Py_False;
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 10, is_no_annotations);

#ifdef _NUITKA_MODULE
    PyObject *is_module_mode = Py_True;
#else
    PyObject *is_module_mode = Py_False;
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 11, is_module_mode);

#ifdef _NUITKA_MODULE
    PyObject *main_name;

    if (_Py_PackageContext != NULL) {
        main_name = Nuitka_String_FromString(_Py_PackageContext);
    } else {
        main_name = Nuitka_String_FromString(%(module_name_cstr)s);
    }
#else
    PyObject *main_name = Nuitka_String_FromString("__main__");
#endif
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 12, main_name);

    // Prevent users from creating the Nuitka version type object.
    Nuitka_VersionInfoType.tp_init = NULL;
    Nuitka_VersionInfoType.tp_new = NULL;

    setDistributionsMetadata(%(metadata_values)s);
}

// In debug mode we can check that the constants were not tampered with in any
// given moment. We typically do it at program exit, but we can add extra calls
// for sanity.
#ifndef __NUITKA_NO_ASSERT__
void checkGlobalConstants(void) {
// TODO: Ask constant code to check values.

}
#endif

void createGlobalConstants(PyThreadState *tstate) {
    if (_sentinel_value == NULL) {
#if PYTHON_VERSION < 0x300
        _sentinel_value = PyCObject_FromVoidPtr(NULL, NULL);
#else
        // The NULL value is not allowed for a capsule, so use something else.
        _sentinel_value = PyCapsule_New((void *)27, "sentinel", NULL);
#endif
        assert(_sentinel_value);

        _createGlobalConstants(tstate);
    }
}
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
