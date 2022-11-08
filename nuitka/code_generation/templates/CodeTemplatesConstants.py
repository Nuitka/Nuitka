#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Templates for the constants handling.

"""

template_constants_reading = r"""
#include "nuitka/prelude.h"
#include "structseq.h"

// Global constants storage
PyObject *global_constants[%(global_constants_count)d];

// Sentinel PyObject to be used for all our call iterator endings. It will
// become a PyCObject pointing to NULL. It's address is unique, and that's
// enough for us to use it as sentinel value.
PyObject *_sentinel_value = NULL;

PyObject *Nuitka_dunder_compiled_value = NULL;


#ifdef _NUITKA_STANDALONE
extern PyObject *getStandaloneSysExecutablePath(PyObject *basename);
#endif

// We provide the sys.version info shortcut as a global value here for ease of use.
PyObject *Py_SysVersionInfo = NULL;

static void _createGlobalConstants(void) {
    // We provide the sys.version info shortcut as a global value here for ease of use.
    Py_SysVersionInfo = Nuitka_SysGetObject("version_info");

    // The empty name means global.
    loadConstantsBlob(&global_constants[0], "");

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
        {(char *)"standalone", (char *)"boolean indicating standalone mode usage"},
        {(char *)"onefile", (char *)"boolean indicating standalone mode usage"},
        {0}
    };

    static PyStructSequence_Desc Nuitka_VersionInfoDesc = {
        (char *)"__nuitka_version__",                                    /* name */
        (char *)"__compiled__\\n\\nVersion information as a named tuple.", /* doc */
        Nuitka_VersionInfoFields,                                        /* fields */
        6
    };

    PyStructSequence_InitType(&Nuitka_VersionInfoType, &Nuitka_VersionInfoDesc);

    Nuitka_dunder_compiled_value = PyStructSequence_New(&Nuitka_VersionInfoType);
    assert(Nuitka_dunder_compiled_value != NULL);

    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 0, PyInt_FromLong(%(nuitka_version_major)s));
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 1, PyInt_FromLong(%(nuitka_version_minor)s));
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 2, PyInt_FromLong(%(nuitka_version_micro)s));

    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 3, Nuitka_String_FromString("%(nuitka_version_level)s"));

#ifdef _NUITKA_STANDALONE
    PyObject *is_standalone_mode = Py_True;
#else
    PyObject *is_standalone_mode = Py_False;
#endif
#ifdef _NUITKA_ONEFILE_MODE
    PyObject *is_onefile_mode = Py_True;
#else
    PyObject *is_onefile_mode = Py_False;
#endif

    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 4, is_standalone_mode);
    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 5, is_onefile_mode);

    // Prevent users from creating the Nuitka version type object.
    Nuitka_VersionInfoType.tp_init = NULL;
    Nuitka_VersionInfoType.tp_new = NULL;
}

// In debug mode we can check that the constants were not tampered with in any
// given moment. We typically do it at program exit, but we can add extra calls
// for sanity.
#ifndef __NUITKA_NO_ASSERT__
void checkGlobalConstants(void) {
// TODO: Ask constant code to check values.

}
#endif

void createGlobalConstants(void) {
    if (_sentinel_value == NULL) {
#if PYTHON_VERSION < 0x300
        _sentinel_value = PyCObject_FromVoidPtr(NULL, NULL);
#else
        // The NULL value is not allowed for a capsule, so use something else.
        _sentinel_value = PyCapsule_New((void *)27, "sentinel", NULL);
#endif
        assert(_sentinel_value);

        _createGlobalConstants();
    }
}
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())
