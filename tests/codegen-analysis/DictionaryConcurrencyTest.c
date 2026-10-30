//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* Standalone C concurrency stress test for the Nuitka dictionary helpers.
 *
 * This test is intentionally independent of Nuitka's generated program
 * support. It links the canonical dictionary helper implementation directly
 * and drives shared dictionaries from native threads using a mix of helper
 * and CPython C-API calls.
 */

#include <pthread.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// clang-format off
#include "nuitka/prelude.h"
#include "nuitka/compiled_types_common.h"
#include "nuitka/freelists.h"
// clang-format on

void NuitkaMem_FreeDelayed(void *ptr);

PyObject *global_constants_storage[1];
PyObject **global_constants = global_constants_storage;

#if defined(Py_DEBUG)
void *python_obj_ctx = NULL;
void *python_mem_ctx = NULL;
#endif

// Minimal implementations for helpers that are not part of the dictionary
// implementation, but are referenced by its code paths.
void *(*python_obj_malloc)(void *ctx, size_t size) = NULL;

static void *concurrencyObjMalloc(void *ctx, size_t size) {
    (void)ctx;
    return PyObject_Malloc(size);
}

static void concurrencyObjFree(void *ctx, void *ptr) {
    (void)ctx;
    PyObject_Free(ptr);
}

void (*python_obj_free)(void *ctx, void *ptr) = concurrencyObjFree;

static void *concurrencyMemMalloc(void *ctx, size_t size) {
    (void)ctx;
    return PyMem_Malloc(size);
}

static void *concurrencyMemCalloc(void *ctx, size_t nelem, size_t elsize) {
    (void)ctx;
    return PyMem_Calloc(nelem, elsize);
}

static void *concurrencyMemRealloc(void *ctx, void *ptr, size_t new_size) {
    (void)ctx;
    return PyMem_Realloc(ptr, new_size);
}

static void concurrencyMemFree(void *ctx, void *ptr) {
    (void)ctx;
    PyMem_Free(ptr);
}

void *(*python_mem_malloc)(void *ctx, size_t size) = concurrencyMemMalloc;
void *(*python_mem_calloc)(void *ctx, size_t nelem, size_t elsize) = concurrencyMemCalloc;
#ifndef Py_GIL_DISABLED
void *(*python_mem_realloc)(void *ctx, void *ptr, size_t new_size) = concurrencyMemRealloc;
#else
void (*python_mem_free)(void *ctx, void *ptr) = concurrencyMemFree;
#endif

Py_hash_t HASH_VALUE_WITH_ERROR(PyThreadState *tstate, PyObject *value) {
    (void)tstate;
    return PyObject_Hash(value);
}

Py_hash_t HASH_VALUE_WITHOUT_ERROR(PyThreadState *tstate, PyObject *value) {
    (void)tstate;
    return PyObject_Hash(value);
}

void NuitkaMem_FreeDelayed(void *ptr) { PyMem_Free(ptr); }

static PyBaseExceptionObject *Nuitka_BaseExceptionSingleArg_new(PyThreadState *tstate, PyTypeObject *type,
                                                                PyObject *arg) {
    (void)tstate;
    return (PyBaseExceptionObject *)PyObject_CallFunctionObjArgs((PyObject *)type, arg, NULL);
}

nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    int result = PyObject_RichCompareBool(operand1, operand2, Py_EQ);

    if (result < 0) {
        return NUITKA_BOOL_EXCEPTION;
    }

    return result ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
}

nuitka_bool RICH_COMPARE_EQ_NBOOL_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    return RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(operand1, operand2);
}

bool RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {
    return PyObject_RichCompareBool(operand1, operand2, Py_EQ) == 1;
}

bool RICH_COMPARE_EQ_CBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return PyObject_RichCompareBool(operand1, operand2, Py_EQ) == 1;
}

#include "HelpersDictionaries.c"

#define THREAD_COUNT 8
#define SPLIT_THREAD_COUNT 4
#define KEY_COUNT 32
#define ITERATIONS 400

typedef struct {
    int thread_id;
    PyObject *dict;
    const char *prefix;
    atomic_int *error_count;
} ConcurrencyArgs;

static void recordError(atomic_int *error_count) { atomic_fetch_add(error_count, 1); }

static PyObject *makeKey(const char *prefix, int thread_id, int index) {
    return PyUnicode_FromFormat("%s_%d_%d", prefix, thread_id, index);
}

static bool setItem(PyObject *dict, PyObject *key, PyObject *value, bool use_helper) {
    if (use_helper) {
        return DICT_SET_ITEM(dict, key, value);
    }

    return PyDict_SetItem(dict, key, value) == 0;
}

static bool removeItem(PyObject *dict, PyObject *key, bool use_helper) {
    if (use_helper) {
        return DICT_REMOVE_ITEM(dict, key);
    }

    return PyDict_DelItem(dict, key) == 0;
}

static PyObject *getItem(PyThreadState *tstate, PyObject *dict, PyObject *key, bool use_helper) {
    if (use_helper) {
        return DICT_GET_ITEM0(tstate, dict, key);
    }

    return PyDict_GetItemWithError(dict, key);
}

static void *stressWorker(void *argument) {
    ConcurrencyArgs *args = (ConcurrencyArgs *)argument;
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyThreadState *tstate = PyThreadState_GET();

    for (int i = 0; i < KEY_COUNT; i++) {
        PyObject *key = makeKey(args->prefix, args->thread_id, i);
        PyObject *value = PyLong_FromLong(i + 1);

        if (key == NULL || value == NULL) {
            Py_XDECREF(key);
            Py_XDECREF(value);
            recordError(args->error_count);
            PyErr_Clear();
            continue;
        }

        if (!setItem(args->dict, key, value, (i + args->thread_id) % 2)) {
            recordError(args->error_count);
            PyErr_Clear();
        }

        Py_DECREF(key);
        Py_DECREF(value);
    }

    for (int i = 0; i < ITERATIONS; i++) {
        int index = i % KEY_COUNT;
        PyObject *key = makeKey(args->prefix, args->thread_id, index);
        PyObject *value = PyLong_FromLong(i + 1000);
        bool use_helper = (i + args->thread_id) % 2;

        if (key == NULL || value == NULL) {
            Py_XDECREF(key);
            Py_XDECREF(value);
            recordError(args->error_count);
            PyErr_Clear();
            continue;
        }

        if (!setItem(args->dict, key, value, use_helper)) {
            recordError(args->error_count);
            PyErr_Clear();
        }

        if (!removeItem(args->dict, key, !use_helper)) {
            recordError(args->error_count);
            PyErr_Clear();
        }

        if (!setItem(args->dict, key, value, use_helper)) {
            recordError(args->error_count);
            PyErr_Clear();
        }

        PyObject *result = getItem(tstate, args->dict, key, !use_helper);

        if (result == NULL) {
            if (!PyErr_Occurred()) {
                recordError(args->error_count);
            }

            PyErr_Clear();
        }

        Py_DECREF(key);
        Py_DECREF(value);
    }

    for (int i = 0; i < KEY_COUNT; i++) {
        PyObject *key = makeKey(args->prefix, args->thread_id, i);

        if (key == NULL) {
            recordError(args->error_count);
            PyErr_Clear();
            continue;
        }

        if (i % 5 == 0) {
            if (!removeItem(args->dict, key, i % 2)) {
                recordError(args->error_count);
                PyErr_Clear();
            }
        } else {
            PyObject *value = PyLong_FromLong(i + 10000);

            if (value == NULL || !setItem(args->dict, key, value, i % 2)) {
                recordError(args->error_count);
                PyErr_Clear();
            }

            Py_XDECREF(value);
        }

        Py_DECREF(key);
    }

    PyGILState_Release(gil_state);

    return NULL;
}

static int runThreads(PyObject *dict, const char *prefix, int thread_count) {
    pthread_t threads[THREAD_COUNT];
    ConcurrencyArgs args[THREAD_COUNT];
    atomic_int error_count = 0;

    for (int i = 0; i < thread_count; i++) {
        args[i].thread_id = i;
        args[i].dict = dict;
        args[i].prefix = prefix;
        args[i].error_count = &error_count;
    }

    PyThreadState *main_tstate = PyEval_SaveThread();
    bool thread_created[THREAD_COUNT] = {false};

    for (int i = 0; i < thread_count; i++) {
        if (pthread_create(&threads[i], NULL, stressWorker, &args[i]) != 0) {
            atomic_fetch_add(&error_count, 1);
        } else {
            thread_created[i] = true;
        }
    }

    for (int i = 0; i < thread_count; i++) {
        if (thread_created[i] && pthread_join(threads[i], NULL) != 0) {
            atomic_fetch_add(&error_count, 1);
        }
    }

    PyEval_RestoreThread(main_tstate);

    return atomic_load(&error_count);
}

static int verifyDict(PyObject *dict, const char *prefix, int thread_count, int extra_entries) {
    Py_ssize_t expected = extra_entries;
    int errors = 0;

    for (int thread_id = 0; thread_id < thread_count; thread_id++) {
        for (int index = 0; index < KEY_COUNT; index++) {
            PyObject *key = makeKey(prefix, thread_id, index);

            if (key == NULL) {
                PyErr_Clear();
                errors++;
                continue;
            }

            PyObject *result = PyDict_GetItemWithError(dict, key);

            if (index % 5 == 0) {
                if (result != NULL || PyErr_Occurred()) {
                    errors++;
                    PyErr_Clear();
                }
            } else {
                expected++;

                if (result == NULL) {
                    errors++;
                    PyErr_Clear();
                } else {
                    long value = PyLong_AsLong(result);

                    if (value != index + 10000) {
                        errors++;
                    }
                }
            }

            Py_DECREF(key);
        }
    }

    if (PyDict_Size(dict) != expected) {
        errors++;
    }

    return errors;
}

static int runCombinedStressTest(void) {
    PyObject *dict = PyDict_New();
    int errors = 0;

    if (dict == NULL) {
        return 1;
    }

    errors += runThreads(dict, "combined", THREAD_COUNT);
    errors += verifyDict(dict, "combined", THREAD_COUNT, 0);

    Py_DECREF(dict);

    return errors;
}

static PyObject *runPythonCode(const char *code, const char *result_name) {
    PyObject *globals = PyDict_New();

    if (globals == NULL) {
        return NULL;
    }

    PyDict_SetItemString(globals, "__builtins__", PyEval_GetBuiltins());

    PyObject *result = PyRun_String(code, Py_file_input, globals, globals);

    if (result == NULL) {
        Py_DECREF(globals);
        return NULL;
    }

    Py_DECREF(result);

    PyObject *value = PyDict_GetItemString(globals, result_name);

    Py_XINCREF(value);
    Py_DECREF(globals);

    return value;
}

static int runSplitStressTest(void) {
    PyObject *obj = runPythonCode("class SplitObject:\n    pass\nsplit_object = SplitObject()\n", "split_object");

    if (obj == NULL) {
        PyErr_Clear();
        return 1;
    }

    PyObject *seed = PyLong_FromLong(0);
    PyObject_SetAttrString(obj, "seed", seed);
    Py_DECREF(seed);

    PyObject *dict = PyObject_GetAttrString(obj, "__dict__");
    int errors = 0;

    if (dict == NULL) {
        Py_DECREF(obj);
        return 1;
    }

    if (((PyDictObject *)dict)->ma_values == NULL) {
        fprintf(stderr, "split stress target is not a split dictionary\n");
        Py_DECREF(dict);
        Py_DECREF(obj);
        return 1;
    }

    errors += runThreads(dict, "split", SPLIT_THREAD_COUNT);
    errors += verifyDict(dict, "split", SPLIT_THREAD_COUNT, 1);

    Py_DECREF(dict);
    Py_DECREF(obj);

    return errors;
}

static int runCollisionTest(void) {
    PyObject *class_object =
        runPythonCode("class CollisionKey:\n"
                      "    def __init__(self, value):\n"
                      "        self.value = value\n"
                      "    def __hash__(self):\n"
                      "        return 1\n"
                      "    def __eq__(self, other):\n"
                      "        return isinstance(other, CollisionKey) and self.value == other.value\n",
                      "CollisionKey");

    if (class_object == NULL) {
        PyErr_Clear();
        return 1;
    }

    PyObject *dict = PyDict_New();
    int errors = 0;

    if (dict == NULL) {
        Py_DECREF(class_object);
        return 1;
    }

    for (int i = 0; i < 64; i++) {
        PyObject *key = PyObject_CallFunction(class_object, "i", i);
        PyObject *value = PyLong_FromLong(i);

        if (key == NULL || value == NULL || !DICT_SET_ITEM(dict, key, value)) {
            errors++;
            PyErr_Clear();
        }

        Py_XDECREF(key);
        Py_XDECREF(value);
    }

    for (int i = 0; i < 64; i += 2) {
        PyObject *key = PyObject_CallFunction(class_object, "i", i);

        if (key == NULL || !DICT_REMOVE_ITEM(dict, key)) {
            errors++;
            PyErr_Clear();
        }

        Py_XDECREF(key);
    }

    for (int i = 0; i < 64; i++) {
        PyObject *key = PyObject_CallFunction(class_object, "i", i);

        if (key == NULL) {
            errors++;
            PyErr_Clear();
            continue;
        }

        PyObject *result = DICT_GET_ITEM0(PyThreadState_GET(), dict, key);

        if ((i % 2 == 0) != (result == NULL)) {
            errors++;
        }

        Py_DECREF(key);
    }

    if (PyDict_Size(dict) != 32) {
        errors++;
    }

    Py_DECREF(dict);
    Py_DECREF(class_object);

    return errors;
}

static int runConsumeSetTest(void) {
    PyObject *dict = PyDict_New();
    PyObject *key = PyUnicode_FromString("consume_set");
    PyObject *value = PyList_New(0);
    int errors = 0;

    if (dict == NULL || key == NULL || value == NULL || !DICT_SET_ITEM1(dict, key, value)) {
        Py_XDECREF(dict);
        Py_XDECREF(key);
        Py_XDECREF(value);
        PyErr_Clear();
        return 1;
    }

    if (Py_REFCNT(value) != 1) {
        errors++;
    }

    PyObject *result = DICT_GET_ITEM0(PyThreadState_GET(), dict, key);

    if (result != value || Py_REFCNT(value) != 1) {
        errors++;
    }

    Py_DECREF(dict);
    Py_DECREF(key);

    return errors;
}

static int runBorrowedGetTest(void) {
    PyObject *dict = PyDict_New();
    PyObject *key = PyUnicode_FromString("get_ref");
    PyObject *value = PyList_New(0);
    int errors = 0;

    if (dict == NULL || key == NULL || value == NULL || !DICT_SET_ITEM(dict, key, value)) {
        Py_XDECREF(dict);
        Py_XDECREF(key);
        Py_XDECREF(value);
        PyErr_Clear();
        return 1;
    }

    Py_ssize_t refcount_before = Py_REFCNT(value);
    PyObject *borrowed = DICT_GET_ITEM0(PyThreadState_GET(), dict, key);

    if (borrowed != value || Py_REFCNT(value) != refcount_before) {
        errors++;
    }

    PyObject *owned = DICT_GET_ITEM1(PyThreadState_GET(), dict, key);

    if (owned != value || Py_REFCNT(value) != refcount_before + 1) {
        errors++;
    }

    Py_XDECREF(owned);

    PyObject *hash_error_owned = DICT_GET_ITEM_WITH_HASH_ERROR1(PyThreadState_GET(), dict, key);

    if (hash_error_owned != value || Py_REFCNT(value) != refcount_before + 1) {
        errors++;
    }

    Py_XDECREF(hash_error_owned);

    PyObject *with_error = DICT_GET_ITEM_WITH_ERROR(PyThreadState_GET(), dict, key);

    if (with_error != value || Py_REFCNT(value) != refcount_before + 1) {
        errors++;
    }

    Py_XDECREF(with_error);

    if (DICT_HAS_ITEM(PyThreadState_GET(), dict, key) != 1 || Py_REFCNT(value) != refcount_before) {
        errors++;
    }

    Py_DECREF(dict);
    Py_DECREF(key);
    Py_DECREF(value);

    return errors;
}

#ifndef Py_GIL_DISABLED
static int runRefcountTest(void) {
    PyObject *dict = PyDict_New();
    PyObject *value = PyList_New(0);
    int errors = 0;

    if (dict == NULL || value == NULL) {
        Py_XDECREF(dict);
        Py_XDECREF(value);
        return 1;
    }

    Py_ssize_t refcount_before = Py_REFCNT(value);

    for (int i = 0; i < 64; i++) {
        PyObject *key = PyUnicode_FromFormat("refcount_%d", i);

        if (key == NULL || !DICT_SET_ITEM(dict, key, value)) {
            errors++;
            PyErr_Clear();
        }

        Py_XDECREF(key);
    }

    if (Py_REFCNT(value) != refcount_before + 64) {
        errors++;
    }

    for (int i = 0; i < 64; i++) {
        PyObject *key = PyUnicode_FromFormat("refcount_%d", i);

        if (key == NULL || !DICT_REMOVE_ITEM(dict, key)) {
            errors++;
            PyErr_Clear();
        }

        Py_XDECREF(key);
    }

    if (Py_REFCNT(value) != refcount_before) {
        errors++;
    }

    Py_DECREF(dict);
    Py_DECREF(value);

    return errors;
}
#endif

int main(void) {
    Py_Initialize();

    global_constants[0] = PyDict_New();
    python_obj_malloc = concurrencyObjMalloc;

    int errors = 0;

    errors += runCombinedStressTest();
    errors += runSplitStressTest();
    errors += runCollisionTest();
    errors += runBorrowedGetTest();
    errors += runConsumeSetTest();

#ifndef Py_GIL_DISABLED
    errors += runRefcountTest();
#endif

    if (errors != 0) {
        fprintf(stderr, "dictionary concurrency stress failed with %d errors\n", errors);
        Py_Finalize();
        return 1;
    }

#ifdef Py_GIL_DISABLED
    fprintf(stderr, "dictionary concurrency stress passed (free-threaded)\n");
#else
    fprintf(stderr, "dictionary concurrency stress passed (GIL build)\n");
#endif

    Py_Finalize();

    return 0;
}

//     Python test originally created or extracted from other peoples work. The
//     parts from me are licensed as below. It is at least Free Software where
//     it's copied from other people. In these cases, that will normally be
//     indicated.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
