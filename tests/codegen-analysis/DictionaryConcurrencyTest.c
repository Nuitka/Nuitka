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

#if PYTHON_VERSION >= 0x3a0 && PYTHON_VERSION < 0x3c0 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_FREELIST_ALL)
// Minimal tuple helpers for the standalone harness, which does not link the
// tuple freelist implementation from HelpersTuples.c.
PyObject *MAKE_TUPLE_EMPTY(PyThreadState *tstate, Py_ssize_t size) {
    (void)tstate;
    return PyTuple_New(size);
}

PyObject *MAKE_TUPLE_EMPTY_VAR(PyThreadState *tstate, Py_ssize_t size) {
    (void)tstate;
    return PyTuple_New(size);
}
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

void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(char const *format, PyObject *mistyped) {
    PyErr_Format(PyExc_TypeError, format, Py_TYPE(mistyped)->tp_name);
}

void SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyObject *exception_type, char const *format, char const *value) {
    PyErr_Format(exception_type, format, value);
}

PyObject *CALL_FUNCTION_WITH_SINGLE_ARG(PyThreadState *tstate, PyObject *called, PyObject *arg) {
    (void)tstate;
    return PyObject_CallFunctionObjArgs(called, arg, NULL);
}

PyObject *LOOKUP_ATTRIBUTE(PyThreadState *tstate, PyObject *source, PyObject *attr_name) {
    (void)tstate;
    return PyObject_GetAttr(source, attr_name);
}

Py_ssize_t Nuitka_Number_AsSsize_t(PyObject *item, PyObject *exc) { return PyNumber_AsSsize_t(item, exc); }

static PyObject *defaultIterNext(PyObject *self) {
    (void)self;
    PyErr_SetString(PyExc_TypeError, "not an iterator");
    return NULL;
}

iternextfunc default_iternext = defaultIterNext;

bool Nuitka_Type_IsSubtype(PyTypeObject *a, PyTypeObject *b) { return PyType_IsSubtype(a, b) != 0; }

void Nuitka_PyObject_GC_Link(PyObject *op) {
    // The concurrency harness only exercises the dictionary paths, which do
    // not allocate objects through Nuitka's GC helpers.
    (void)op;
}

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
#define BULK_KEY_COUNT 4
#define BULK_ITERATIONS 50
#define HASH_KEY_COUNT 4
#define HASH_ITERATIONS 50
#define CONSUME_KEY_COUNT 4
#define CONSUME_ITERATIONS 50

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

static PyObject *makeKeyWithCategory(const char *prefix, int thread_id, const char *category, int index) {
    return PyUnicode_FromFormat("%s_%s_%d_%d", prefix, category, thread_id, index);
}

static PyObject *knownHashAlwaysEqual(PyObject *object1, PyObject *object2, int op);
static PyObject *knownHashObjectEqual(PyObject *object1, PyObject *object2, int op);

static int verifyBulkKeys(PyObject *dict, const char *prefix, int thread_count);
static int verifyHashKeys(PyObject *dict, const char *prefix, int thread_count);
static int verifyConsumeKeys(PyObject *dict, const char *prefix, int thread_count);

static bool setItem(PyObject *dict, PyObject *key, PyObject *value, bool use_helper) {
    if (use_helper) {
        return DICT_SET_ITEM(PyThreadState_GET(), dict, key, value);
    }

    return PyDict_SetItem(dict, key, value) == 0;
}

static bool removeItem(PyObject *dict, PyObject *key, bool use_helper) {
    if (use_helper) {
        return DICT_REMOVE_ITEM(PyThreadState_GET(), dict, key);
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

    for (int i = 0; i < BULK_ITERATIONS; i++) {
        PyObject *map_source = PyDict_New();
        PyObject *seq_pairs = PyList_New(0);

        if (map_source == NULL || seq_pairs == NULL) {
            Py_XDECREF(map_source);
            Py_XDECREF(seq_pairs);
            recordError(args->error_count);
            PyErr_Clear();
            continue;
        }

        bool build_ok = true;

        for (int j = 0; j < BULK_KEY_COUNT; j++) {
            PyObject *map_key = makeKeyWithCategory(args->prefix, args->thread_id, "bulk", j);
            PyObject *map_value = PyLong_FromLong(i + 20000 + j);
            PyObject *seq_key = makeKeyWithCategory(args->prefix, args->thread_id, "seq", j);
            PyObject *seq_value = PyLong_FromLong(i + 30000 + j);
            PyObject *pair = NULL;

            if (map_key != NULL && map_value != NULL && seq_key != NULL && seq_value != NULL) {
                pair = PyTuple_Pack(2, seq_key, seq_value);
            }

            if (map_key == NULL || map_value == NULL || seq_key == NULL || seq_value == NULL || pair == NULL ||
                PyDict_SetItem(map_source, map_key, map_value) != 0 || PyList_Append(seq_pairs, pair) != 0) {
                Py_XDECREF(map_key);
                Py_XDECREF(map_value);
                Py_XDECREF(seq_key);
                Py_XDECREF(seq_value);
                Py_XDECREF(pair);
                recordError(args->error_count);
                PyErr_Clear();
                build_ok = false;
                break;
            }

            Py_DECREF(map_key);
            Py_DECREF(map_value);
            Py_DECREF(seq_key);
            Py_DECREF(seq_value);
            Py_DECREF(pair);
        }

        if (build_ok) {
            if ((i + args->thread_id) % 2) {
                if (DICT_UPDATE_FROM(tstate, args->dict, map_source) < 0) {
                    recordError(args->error_count);
                    PyErr_Clear();
                }
            } else if (PyDict_Update(args->dict, map_source) != 0) {
                recordError(args->error_count);
                PyErr_Clear();
            }

            if ((i + args->thread_id) % 2 == 0) {
                if (DICT_UPDATE_FROM_SEQ(tstate, args->dict, seq_pairs) < 0) {
                    recordError(args->error_count);
                    PyErr_Clear();
                }
            } else if (PyDict_MergeFromSeq2(args->dict, seq_pairs, 1) != 0) {
                recordError(args->error_count);
                PyErr_Clear();
            }
        }

        Py_DECREF(map_source);
        Py_DECREF(seq_pairs);
    }

    for (int i = 0; i < HASH_ITERATIONS; i++) {
        for (int j = 0; j < HASH_KEY_COUNT; j++) {
            int key_value = 1000000 + args->thread_id * 1000 + j;
            PyObject *key = PyLong_FromLong(key_value);
            PyObject *value = PyLong_FromLong(i + 40000 + j);

            if (key == NULL || value == NULL) {
                Py_XDECREF(key);
                Py_XDECREF(value);
                recordError(args->error_count);
                PyErr_Clear();
                continue;
            }

            // Use a supplied hash different from the integer's actual hash so
            // this exercises forced hashes in a general keyed table.
            Py_hash_t hash = (Py_hash_t)(2000000 + args->thread_id * 1000 + j);
            bool result;

            if ((i + args->thread_id + j) % 2) {
                result = DICT_SET_ITEM_WITH_HASH_AND_EQ(tstate, args->dict, key, hash, knownHashObjectEqual, value);
            } else {
                result = DICT_SET_ITEM_WITH_HASH(tstate, args->dict, key, hash, value);
            }

            if (!result) {
                recordError(args->error_count);
                PyErr_Clear();
            }

            Py_DECREF(key);
            Py_DECREF(value);
        }
    }

    for (int i = 0; i < CONSUME_ITERATIONS; i++) {
        for (int j = 0; j < CONSUME_KEY_COUNT; j++) {
            PyObject *key = makeKeyWithCategory(args->prefix, args->thread_id, "consume", j);
            PyObject *value = PyLong_FromLong(i + 50000 + j);

            if (key == NULL || value == NULL) {
                Py_XDECREF(key);
                Py_XDECREF(value);
                recordError(args->error_count);
                PyErr_Clear();
                continue;
            }

            if (!DICT_SET_ITEM1(tstate, args->dict, key, value)) {
                recordError(args->error_count);
                PyErr_Clear();
            }

            Py_DECREF(key);
        }
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

static int verifyDict(PyObject *dict, const char *prefix, int thread_count, int extra_entries, int additional_entries) {
    Py_ssize_t expected = extra_entries + additional_entries;
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

static int verifyBulkKeys(PyObject *dict, const char *prefix, int thread_count) {
    int errors = 0;

    for (int thread_id = 0; thread_id < thread_count; thread_id++) {
        for (int index = 0; index < BULK_KEY_COUNT; index++) {
            PyObject *key = makeKeyWithCategory(prefix, thread_id, "bulk", index);
            PyObject *result;
            long expected = BULK_ITERATIONS - 1 + 20000 + index;

            if (key == NULL) {
                errors++;
                PyErr_Clear();
                continue;
            }

            result = PyDict_GetItemWithError(dict, key);

            if (result == NULL || !PyLong_Check(result) || PyLong_AsLong(result) != expected) {
                errors++;
                PyErr_Clear();
            }

            Py_DECREF(key);

            key = makeKeyWithCategory(prefix, thread_id, "seq", index);
            expected = BULK_ITERATIONS - 1 + 30000 + index;

            if (key == NULL) {
                errors++;
                PyErr_Clear();
                continue;
            }

            result = PyDict_GetItemWithError(dict, key);

            if (result == NULL || !PyLong_Check(result) || PyLong_AsLong(result) != expected) {
                errors++;
                PyErr_Clear();
            }

            Py_DECREF(key);
        }
    }

    return errors;
}

static int verifyHashKeys(PyObject *dict, const char *prefix, int thread_count) {
    int errors = 0;
    PyThreadState *tstate = PyThreadState_GET();

    for (int thread_id = 0; thread_id < thread_count; thread_id++) {
        for (int index = 0; index < HASH_KEY_COUNT; index++) {
            int key_value = 1000000 + thread_id * 1000 + index;
            PyObject *key = PyLong_FromLong(key_value);
            Py_hash_t hash = (Py_hash_t)(2000000 + thread_id * 1000 + index);
            PyObject *result;
            long expected = HASH_ITERATIONS - 1 + 40000 + index;

            if (key == NULL) {
                errors++;
                PyErr_Clear();
                continue;
            }

            result = DICT_GET_ITEM0_WITH_HASH_AND_EQ(tstate, dict, key, hash, knownHashObjectEqual);

            if (result == NULL || !PyLong_Check(result) || PyLong_AsLong(result) != expected) {
                errors++;
                PyErr_Clear();
            }

            Py_DECREF(key);
        }
    }

    return errors;
}

static int verifyConsumeKeys(PyObject *dict, const char *prefix, int thread_count) {
    int errors = 0;

    for (int thread_id = 0; thread_id < thread_count; thread_id++) {
        for (int index = 0; index < CONSUME_KEY_COUNT; index++) {
            PyObject *key = makeKeyWithCategory(prefix, thread_id, "consume", index);
            PyObject *result;
            long expected = CONSUME_ITERATIONS - 1 + 50000 + index;

            if (key == NULL) {
                errors++;
                PyErr_Clear();
                continue;
            }

            result = PyDict_GetItemWithError(dict, key);

            if (result == NULL || !PyLong_Check(result) || PyLong_AsLong(result) != expected) {
                errors++;
                PyErr_Clear();
            }

            Py_DECREF(key);
        }
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
    errors += verifyDict(dict, "combined", THREAD_COUNT, 0,
                         THREAD_COUNT * (2 * BULK_KEY_COUNT + HASH_KEY_COUNT + CONSUME_KEY_COUNT));
    errors += verifyBulkKeys(dict, "combined", THREAD_COUNT);
    errors += verifyHashKeys(dict, "combined", THREAD_COUNT);
    errors += verifyConsumeKeys(dict, "combined", THREAD_COUNT);

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
    errors += verifyDict(dict, "split", SPLIT_THREAD_COUNT, 1,
                         SPLIT_THREAD_COUNT * (2 * BULK_KEY_COUNT + HASH_KEY_COUNT + CONSUME_KEY_COUNT));
    errors += verifyBulkKeys(dict, "split", SPLIT_THREAD_COUNT);
    errors += verifyHashKeys(dict, "split", SPLIT_THREAD_COUNT);
    errors += verifyConsumeKeys(dict, "split", SPLIT_THREAD_COUNT);

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

        if (key == NULL || value == NULL || !DICT_SET_ITEM(PyThreadState_GET(), dict, key, value)) {
            errors++;
            PyErr_Clear();
        }

        Py_XDECREF(key);
        Py_XDECREF(value);
    }

    for (int i = 0; i < 64; i += 2) {
        PyObject *key = PyObject_CallFunction(class_object, "i", i);

        if (key == NULL || !DICT_REMOVE_ITEM(PyThreadState_GET(), dict, key)) {
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

    if (dict == NULL || key == NULL || value == NULL || !DICT_SET_ITEM1(PyThreadState_GET(), dict, key, value)) {
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

    if (dict == NULL || key == NULL || value == NULL || !DICT_SET_ITEM(PyThreadState_GET(), dict, key, value)) {
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

static bool DICT_REMOVE_ITEM_WITH_HASH_AND_EQ(PyThreadState *tstate, PyObject *dict, PyObject *key, Py_hash_t hash,
                                              richcmpfunc equal_func) {
    return Nuitka_DictRemoveItemWithHash(tstate, dict, key, hash, equal_func);
}

static PyObject *knownHashAlwaysEqual(PyObject *object1, PyObject *object2, int op) {
    (void)object1;
    (void)object2;
    assert(op == Py_EQ);

    Py_INCREF(Py_True);
    return Py_True;
}

static PyObject *knownHashObjectEqual(PyObject *object1, PyObject *object2, int op) {
    assert(op == Py_EQ);

    int result = PyObject_RichCompareBool(object1, object2, Py_EQ);

    if (result < 0) {
        return NULL;
    }

    PyObject *equal = result ? Py_True : Py_False;
    Py_INCREF(equal);

    return equal;
}

static int runKnownHashReadTest(void) {
    int errors = 0;

    PyObject *dict = PyDict_New();
    PyObject *stored_key = PyUnicode_FromString("stored_key");
    PyObject *lookup_key = PyUnicode_FromString("lookup_key");
    PyObject *value = PyLong_FromLong(7);

    if (dict == NULL || stored_key == NULL || lookup_key == NULL || value == NULL) {
        Py_XDECREF(dict);
        Py_XDECREF(stored_key);
        Py_XDECREF(lookup_key);
        Py_XDECREF(value);
        PyErr_Clear();
        return 1;
    }

    if (!DICT_SET_ITEM(PyThreadState_GET(), dict, stored_key, value)) {
        PyErr_Clear();
        errors++;
    }

    Py_hash_t hash = PyObject_Hash(stored_key);

    if (hash == -1 ||
        DICT_GET_ITEM0_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, lookup_key, hash, knownHashAlwaysEqual) != value) {
        PyErr_Clear();
        errors++;
    }

    Py_DECREF(dict);
    Py_DECREF(stored_key);
    Py_DECREF(lookup_key);
    Py_DECREF(value);

    return errors;
}

static PyObject *knownHashPointerEqual(PyObject *object1, PyObject *object2, int op) {
    assert(op == Py_EQ);

    PyObject *result = object1 == object2 ? Py_True : Py_False;
    Py_INCREF(result);

    return result;
}

static int runKnownHashTest(void) {
    int errors = 0;

    PyObject *dict = PyDict_New();
    PyObject *key = PyUnicode_FromString("known_hash_key");
    PyObject *value = PyLong_FromLong(42);

    if (dict == NULL || key == NULL || value == NULL) {
        Py_XDECREF(dict);
        Py_XDECREF(key);
        Py_XDECREF(value);
        PyErr_Clear();
        return 1;
    }

    Py_hash_t hash = PyObject_Hash(key);

    if (hash == -1 || !DICT_SET_ITEM_WITH_HASH(PyThreadState_GET(), dict, key, hash, value)) {
        PyErr_Clear();
        errors++;
    }

    if (DICT_GET_ITEM0_WITH_HASH(PyThreadState_GET(), dict, key, hash) != value || PyDict_Size(dict) != 1) {
        errors++;
    }

    if (!DICT_REMOVE_ITEM_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key, hash, NULL) || PyDict_Size(dict) != 0) {
        PyErr_Clear();
        errors++;
    }

    // The supplied hash must be stored, not the object's own hash. Use an
    // integer key to force a general keyed table that stores the hash.
    PyObject *int_key = PyLong_FromLong(7);

    if (int_key == NULL || !DICT_SET_ITEM_WITH_HASH(PyThreadState_GET(), dict, int_key, 12345, value)) {
        PyErr_Clear();
        errors++;
    }

    if (DICT_GET_ITEM0_WITH_HASH(PyThreadState_GET(), dict, int_key, PyObject_Hash(int_key)) != NULL ||
        DICT_GET_ITEM0_WITH_HASH(PyThreadState_GET(), dict, int_key, 12345) != value) {
        errors++;
    }

    if (!DICT_REMOVE_ITEM_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, int_key, 12345, NULL) || PyDict_Size(dict) != 0) {
        PyErr_Clear();
        errors++;
    }

    Py_XDECREF(int_key);

    // Caller supplied equality rules must allow distinct keys with equal hashes.
    PyObject *key1 = PyUnicode_FromString("same");
    PyObject *key2 = PyUnicode_FromString("same");
    PyObject *value1 = PyLong_FromLong(1);
    PyObject *value2 = PyLong_FromLong(2);

    if (key1 == NULL || key2 == NULL || value1 == NULL || value2 == NULL) {
        Py_XDECREF(key1);
        Py_XDECREF(key2);
        Py_XDECREF(value1);
        Py_XDECREF(value2);
        Py_DECREF(dict);
        Py_DECREF(key);
        Py_DECREF(value);
        PyErr_Clear();
        return errors + 1;
    }

    hash = PyObject_Hash(key1);

    if (!DICT_SET_ITEM_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key1, hash, knownHashPointerEqual, value1) ||
        !DICT_SET_ITEM_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key2, hash, knownHashPointerEqual, value2) ||
        PyDict_Size(dict) != 2) {
        PyErr_Clear();
        errors++;
    }

    if (DICT_GET_ITEM0_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key1, hash, knownHashPointerEqual) != value1 ||
        DICT_GET_ITEM0_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key2, hash, knownHashPointerEqual) != value2) {
        errors++;
    }

    if (!DICT_REMOVE_ITEM_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key1, hash, knownHashPointerEqual) ||
        !DICT_REMOVE_ITEM_WITH_HASH_AND_EQ(PyThreadState_GET(), dict, key2, hash, knownHashPointerEqual) ||
        PyDict_Size(dict) != 0) {
        PyErr_Clear();
        errors++;
    }

    Py_DECREF(key1);
    Py_DECREF(key2);
    Py_DECREF(value1);
    Py_DECREF(value2);
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

        if (key == NULL || !DICT_SET_ITEM(PyThreadState_GET(), dict, key, value)) {
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

        if (key == NULL || !DICT_REMOVE_ITEM(PyThreadState_GET(), dict, key)) {
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

#define RUN_TEST(name)                                                                                                 \
    do {                                                                                                               \
        int test_errors = name();                                                                                      \
        if (test_errors != 0) {                                                                                        \
            fprintf(stderr, "%s failed with %d errors\n", #name, test_errors);                                         \
            errors += test_errors;                                                                                     \
        }                                                                                                              \
    } while (0)

    RUN_TEST(runCombinedStressTest);
    RUN_TEST(runSplitStressTest);
    RUN_TEST(runCollisionTest);
    RUN_TEST(runBorrowedGetTest);
    RUN_TEST(runConsumeSetTest);
    RUN_TEST(runKnownHashReadTest);
    RUN_TEST(runKnownHashTest);

#ifndef Py_GIL_DISABLED
    RUN_TEST(runRefcountTest);
#endif

#undef RUN_TEST

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
