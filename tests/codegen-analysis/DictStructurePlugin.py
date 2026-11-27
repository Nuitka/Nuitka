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

    if (!DICT_SET_ITEM(PyThreadState_GET(), dict, key, value)) {
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

    if (!DICT_REMOVE_ITEM(PyThreadState_GET(), dict, key)) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_set_item_with_hash(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *key;
    PyObject *value;
    Py_ssize_t hash;

    if (!PyArg_ParseTuple(args, "OOnO:nuitka_test_dict_set_item_with_hash", &dict, &key, &hash, &value)) {
        return NULL;
    }

    if (!DICT_SET_ITEM_WITH_HASH(PyThreadState_GET(), dict, key, (Py_hash_t)hash, value)) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_get_item_with_hash(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *key;
    Py_ssize_t hash;

    if (!PyArg_ParseTuple(args, "OOn:nuitka_test_dict_get_item_with_hash", &dict, &key, &hash)) {
        return NULL;
    }

    PyObject *value = DICT_GET_ITEM0_WITH_HASH(PyThreadState_GET(), dict, key, (Py_hash_t)hash);

    if (value == NULL) {
        if (PyErr_Occurred()) {
            return NULL;
        }

        Py_RETURN_NONE;
    }

    Py_INCREF(value);
    return value;
}

static PyObject *nuitka_test_dict_pointer_equal(PyObject *object1, PyObject *object2, int op) {
    assert(op == Py_EQ);

    PyObject *result = object1 == object2 ? Py_True : Py_False;
    Py_INCREF_IMMORTAL(result);

    return result;
}

static PyObject *nuitka_test_dict_set_item_with_hash_and_eq(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *key;
    PyObject *value;
    Py_ssize_t hash;

    if (!PyArg_ParseTuple(args, "OOnO:nuitka_test_dict_set_item_with_hash_and_eq", &dict, &key, &hash, &value)) {
        return NULL;
    }

    if (!DICT_SET_ITEM_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key, (Py_hash_t)hash,
                                               nuitka_test_dict_pointer_equal, value)) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_get_item_with_hash_and_eq(PyObject *self, PyObject *args) {
    PyObject *dict;
    PyObject *key;
    Py_ssize_t hash;

    if (!PyArg_ParseTuple(args, "OOn:nuitka_test_dict_get_item_with_hash_and_eq", &dict, &key, &hash)) {
        return NULL;
    }

    PyObject *value = DICT_GET_ITEM0_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key, (Py_hash_t)hash,
                                                      nuitka_test_dict_pointer_equal);

    if (value == NULL) {
        if (PyErr_Occurred()) {
            return NULL;
        }

        Py_RETURN_NONE;
    }

    Py_INCREF(value);
    return value;
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

#if PYTHON_VERSION >= 0x3c0
#define NUITKA_TEST_DICT_WATCHER_MAX_EVENTS 512

typedef struct {
    int event;
    uintptr_t dict;
    uintptr_t key;
    uintptr_t value;
    Py_ssize_t size;
    int key_present;
    uintptr_t old_value;
} NuitkaTestDictWatcherEvent;

static NuitkaTestDictWatcherEvent nuitka_test_dict_watcher_records[NUITKA_TEST_DICT_WATCHER_MAX_EVENTS];
static int nuitka_test_dict_watcher_event_count = 0;
static int nuitka_test_dict_watcher_id = -1;
static int nuitka_test_dict_watcher_unwatch_event = -1;
static uintptr_t nuitka_test_dict_watcher_unwatch_key = 0;
static int nuitka_test_dict_watcher_raise_event = -1;
static uintptr_t nuitka_test_dict_watcher_raise_key = 0;
static int nuitka_test_dict_watcher_clear_key_event = -1;
static uintptr_t nuitka_test_dict_watcher_clear_key_key = 0;

static int nuitka_test_dict_watcher_callback(PyDict_WatchEvent event, PyObject *dict, PyObject *key, PyObject *value) {
    if (nuitka_test_dict_watcher_event_count < NUITKA_TEST_DICT_WATCHER_MAX_EVENTS) {
        NuitkaTestDictWatcherEvent *record =
            &nuitka_test_dict_watcher_records[nuitka_test_dict_watcher_event_count];

        record->event = (int)event;
        record->dict = (uintptr_t)dict;
        record->key = (uintptr_t)key;
        record->value = (uintptr_t)value;
        record->size = DICT_SIZE(dict);
        record->key_present = 0;
        record->old_value = 0;

        if (key != NULL && (event == PyDict_EVENT_ADDED || event == PyDict_EVENT_MODIFIED ||
                            event == PyDict_EVENT_DELETED)) {
            PyObject *old_value = DICT_GET_ITEM0(PyThreadState_GET(), dict, key);

            if (old_value != NULL) {
                record->key_present = 1;
                record->old_value = (uintptr_t)old_value;
            } else {
                CLEAR_ERROR_OCCURRED(PyThreadState_GET());
            }
        }

        nuitka_test_dict_watcher_event_count++;
    }

    if ((int)event == nuitka_test_dict_watcher_raise_event &&
        (uintptr_t)key == nuitka_test_dict_watcher_raise_key) {
        nuitka_test_dict_watcher_raise_event = -1;
        nuitka_test_dict_watcher_raise_key = 0;
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyThreadState_GET(), PyExc_RuntimeError,
                                        "dict watcher callback failure");
        return -1;
    }

    if ((int)event == nuitka_test_dict_watcher_unwatch_event &&
        (uintptr_t)key == nuitka_test_dict_watcher_unwatch_key) {
        nuitka_test_dict_watcher_unwatch_event = -1;
        nuitka_test_dict_watcher_unwatch_key = 0;
        PyDict_Unwatch(nuitka_test_dict_watcher_id, dict);
    }

    if ((int)event == nuitka_test_dict_watcher_clear_key_event &&
        (uintptr_t)key == nuitka_test_dict_watcher_clear_key_key) {
        nuitka_test_dict_watcher_clear_key_event = -1;
        nuitka_test_dict_watcher_clear_key_key = 0;

        if (key != NULL && PyDict_Check(key)) {
            PyDict_Clear(key);
        }
    }

    return 0;
}

static PyObject *nuitka_test_dict_watcher_register(PyObject *self, PyObject *args) {
    (void)self;
    (void)args;

    int watcher_id = PyDict_AddWatcher(nuitka_test_dict_watcher_callback);

    if (watcher_id < 0) {
        return NULL;
    }

    nuitka_test_dict_watcher_id = watcher_id;

    return PyLong_FromLong(watcher_id);
}

static PyObject *nuitka_test_dict_watcher_clear(PyObject *self, PyObject *args) {
    int watcher_id;

    (void)self;

    if (!PyArg_ParseTuple(args, "i:_nuitka_test_dict_watcher_clear", &watcher_id)) {
        return NULL;
    }

    if (PyDict_ClearWatcher(watcher_id) < 0) {
        return NULL;
    }

    if (watcher_id == nuitka_test_dict_watcher_id) {
        nuitka_test_dict_watcher_id = -1;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_watcher_watch(PyObject *self, PyObject *args) {
    int watcher_id;
    PyObject *dict;

    (void)self;

    if (!PyArg_ParseTuple(args, "iO:_nuitka_test_dict_watcher_watch", &watcher_id, &dict)) {
        return NULL;
    }

    if (PyDict_Watch(watcher_id, dict) < 0) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_watcher_unwatch(PyObject *self, PyObject *args) {
    int watcher_id;
    PyObject *dict;

    (void)self;

    if (!PyArg_ParseTuple(args, "iO:_nuitka_test_dict_watcher_unwatch", &watcher_id, &dict)) {
        return NULL;
    }

    if (PyDict_Unwatch(watcher_id, dict) < 0) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_watcher_reset(PyObject *self, PyObject *args) {
    (void)self;
    (void)args;

    nuitka_test_dict_watcher_event_count = 0;
    nuitka_test_dict_watcher_unwatch_event = -1;
    nuitka_test_dict_watcher_unwatch_key = 0;
    nuitka_test_dict_watcher_raise_event = -1;
    nuitka_test_dict_watcher_raise_key = 0;
    nuitka_test_dict_watcher_clear_key_event = -1;
    nuitka_test_dict_watcher_clear_key_key = 0;

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_watcher_events(PyObject *self, PyObject *args) {
    (void)self;
    (void)args;

    PyObject *result = PyList_New(nuitka_test_dict_watcher_event_count);

    if (result == NULL) {
        return NULL;
    }

    for (int i = 0; i < nuitka_test_dict_watcher_event_count; i++) {
        NuitkaTestDictWatcherEvent *record = &nuitka_test_dict_watcher_records[i];

        PyObject *tuple = Py_BuildValue("(iKKKniK)", record->event, (unsigned long long)record->dict,
                                       (unsigned long long)record->key, (unsigned long long)record->value,
                                       record->size, record->key_present,
                                       (unsigned long long)record->old_value);

        if (tuple == NULL) {
            Py_DECREF(result);
            return NULL;
        }

        PyList_SET_ITEM(result, i, tuple);
    }

    return result;
}

static PyObject *nuitka_test_dict_watcher_set_unwatch(PyObject *self, PyObject *args) {
    int event;
    PyObject *key;

    (void)self;

    if (!PyArg_ParseTuple(args, "iO:_nuitka_test_dict_watcher_set_unwatch", &event, &key)) {
        return NULL;
    }

    nuitka_test_dict_watcher_unwatch_event = event;
    nuitka_test_dict_watcher_unwatch_key = (uintptr_t)key;

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_watcher_set_raise(PyObject *self, PyObject *args) {
    int event;
    PyObject *key;

    (void)self;

    if (!PyArg_ParseTuple(args, "iO:_nuitka_test_dict_watcher_set_raise", &event, &key)) {
        return NULL;
    }

    nuitka_test_dict_watcher_raise_event = event;
    nuitka_test_dict_watcher_raise_key = (uintptr_t)key;

    Py_RETURN_NONE;
}

static PyObject *nuitka_test_dict_watcher_set_clear_key(PyObject *self, PyObject *args) {
    int event;
    PyObject *key;

    (void)self;

    if (!PyArg_ParseTuple(args, "iO:_nuitka_test_dict_watcher_set_clear_key", &event, &key)) {
        return NULL;
    }

    nuitka_test_dict_watcher_clear_key_event = event;
    nuitka_test_dict_watcher_clear_key_key = (uintptr_t)key;

    Py_RETURN_NONE;
}
#endif

static PyMethodDef nuitka_test_dict_methods[] = {
    {"_nuitka_test_dict_set_item", (PyCFunction)nuitka_test_dict_set_item, METH_VARARGS, NULL},
    {"_nuitka_test_dict_remove_item", (PyCFunction)nuitka_test_dict_remove_item, METH_VARARGS, NULL},
    {"_nuitka_test_dict_set_item_with_hash", (PyCFunction)nuitka_test_dict_set_item_with_hash, METH_VARARGS, NULL},
    {"_nuitka_test_dict_get_item_with_hash", (PyCFunction)nuitka_test_dict_get_item_with_hash, METH_VARARGS, NULL},
    {"_nuitka_test_dict_set_item_with_hash_and_eq", (PyCFunction)nuitka_test_dict_set_item_with_hash_and_eq,
     METH_VARARGS, NULL},
    {"_nuitka_test_dict_get_item_with_hash_and_eq", (PyCFunction)nuitka_test_dict_get_item_with_hash_and_eq,
     METH_VARARGS, NULL},
    {"_nuitka_test_dict_update_from", (PyCFunction)nuitka_test_dict_update_from, METH_VARARGS, NULL},
    {"_nuitka_test_dict_update_from_seq", (PyCFunction)nuitka_test_dict_update_from_seq, METH_VARARGS, NULL},
#if PYTHON_VERSION >= 0x3c0
    {"_nuitka_test_dict_watcher_register", (PyCFunction)nuitka_test_dict_watcher_register, METH_VARARGS, NULL},
    {"_nuitka_test_dict_watcher_clear", (PyCFunction)nuitka_test_dict_watcher_clear, METH_VARARGS, NULL},
    {"_nuitka_test_dict_watcher_watch", (PyCFunction)nuitka_test_dict_watcher_watch, METH_VARARGS, NULL},
    {"_nuitka_test_dict_watcher_unwatch", (PyCFunction)nuitka_test_dict_watcher_unwatch, METH_VARARGS, NULL},
    {"_nuitka_test_dict_watcher_reset", (PyCFunction)nuitka_test_dict_watcher_reset, METH_VARARGS, NULL},
    {"_nuitka_test_dict_watcher_events", (PyCFunction)nuitka_test_dict_watcher_events, METH_VARARGS, NULL},
    {"_nuitka_test_dict_watcher_set_unwatch", (PyCFunction)nuitka_test_dict_watcher_set_unwatch, METH_VARARGS,
     NULL},
    {"_nuitka_test_dict_watcher_set_raise", (PyCFunction)nuitka_test_dict_watcher_set_raise, METH_VARARGS, NULL},
    {"_nuitka_test_dict_watcher_set_clear_key", (PyCFunction)nuitka_test_dict_watcher_set_clear_key, METH_VARARGS,
     NULL},
#endif
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
