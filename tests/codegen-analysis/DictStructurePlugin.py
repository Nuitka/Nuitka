#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test-only plugin adding C dictionary helpers to the structural harness."""

import os

from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileContents

TEST_METHODS_C = r"""
static PyObject *nuitka_test_dict_set_item(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *key;
    PyObject *value;

    if (!PyArg_ParseTuple(args, "OOO:nuitka_test_dict_set_item", &dict, &key, &value)) {
        return NULL;
    }

    if (!DICT_SET_ITEM(dict, key, value)) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_remove_item(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *key;

    if (!PyArg_ParseTuple(args, "OO:nuitka_test_dict_remove_item", &dict, &key)) {
        return NULL;
    }

    if (!DICT_REMOVE_ITEM(dict, key)) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_update_from(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *other;

    if (!PyArg_ParseTuple(args, "OO:nuitka_test_dict_update_from", &dict, &other)) {
        return NULL;
    }

    if (DICT_UPDATE_FROM(PyThreadState_GET(), dict, other) < 0) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_update_from_seq(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *other;

    if (!PyArg_ParseTuple(args, "OO:nuitka_test_dict_update_from_seq", &dict, &other)) {
        return NULL;
    }

    if (DICT_UPDATE_FROM_SEQ(PyThreadState_GET(), dict, other) < 0) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyMethodDef nuitka_test_dict_methods[] = {
    {"_nuitka_test_dict_set_item", (PyCFunction)nuitka_test_dict_set_item, METH_VARARGS, NULL},
    {"_nuitka_test_dict_remove_item", (PyCFunction)nuitka_test_dict_remove_item, METH_VARARGS, NULL},
    {"_nuitka_test_dict_update_from", (PyCFunction)nuitka_test_dict_update_from, METH_VARARGS, NULL},
    {"_nuitka_test_dict_update_from_seq", (PyCFunction)nuitka_test_dict_update_from_seq, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

static void nuitka_register_test_dict_methods(PyObject *module_dict) {
    int i;

    for (i = 0; nuitka_test_dict_methods[i].ml_name != NULL; i++) {
        PyObject *function =
            PyCFunction_New(&nuitka_test_dict_methods[i], NULL);

        if (function == NULL) {
            PyErr_Clear();
            continue;
        }

        if (PyDict_SetItemString(module_dict, nuitka_test_dict_methods[i].ml_name, function) < 0) {
            PyErr_Clear();
        }

        Py_DECREF(function);
    }
}
"""


class NuitkaPluginDictStructure(NuitkaPluginBase):
    plugin_name = "dict-structure-harness"

    def onGeneratedSourceCode(self, source_dir, onefile):
        module_filename = os.path.join(source_dir, "module.__main__.c")

        if not os.path.exists(module_filename):
            return

        source_code = getFileContents(module_filename)

        include_marker = '#include "nuitka/prelude.h"'
        register_marker = "moduledict___main__ = MODULE_DICT(module___main__);"

        if include_marker not in source_code or register_marker not in source_code:
            return

        source_code = source_code.replace(
            include_marker, include_marker + "\n" + TEST_METHODS_C, 1
        )
        source_code = source_code.replace(
            register_marker,
            register_marker
            + "\n    nuitka_register_test_dict_methods((PyObject *)moduledict___main__);",
            1,
        )

        with open(module_filename, "w") as output:
            output.write(source_code)


#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
