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
#ifndef __NUITKA_HELPERS_H__
#define __NUITKA_HELPERS_H__

#define _DEBUG_FRAME 0
#define _DEBUG_REFRAME 0
#define _DEBUG_EXCEPTIONS 0
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_GENERATOR
#define _DEBUG_GENERATOR 1
#else
#define _DEBUG_GENERATOR 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_COROUTINE
#define _DEBUG_COROUTINE 1
#else
#define _DEBUG_COROUTINE 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ASYNCGEN
#define _DEBUG_ASYNCGEN 1
#else
#define _DEBUG_ASYNCGEN 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CLASSES
#define _DEBUG_CLASSES 1
#else
#define _DEBUG_CLASSES 0
#endif

#ifdef _NUITKA_EXPERIMENTAL_REPORT_REFCOUNTS
#define _DEBUG_REFCOUNTS 1
#else
#define _DEBUG_REFCOUNTS 0
#endif

// From CPython, to allow us quick access to the dictionary of an module, the
// structure is normally private, but we need it for quick access to the module
// dictionary.
typedef struct {
    /* Python object folklore: */
    PyObject_HEAD;

    PyObject *md_dict;
} PyModuleObject;

// Generated code helpers, used in static helper codes:
extern PyObject *CALL_FUNCTION_WITH_ARGS2(PyObject *called, PyObject **args);
extern PyObject *CALL_FUNCTION_WITH_ARGS3(PyObject *called, PyObject **args);
extern PyObject *CALL_FUNCTION_WITH_ARGS4(PyObject *called, PyObject **args);
extern PyObject *CALL_FUNCTION_WITH_ARGS5(PyObject *called, PyObject **args);

// Most fundamental, because we use it for debugging in everything else.
#include "nuitka/helper/printing.h"

// Helper to check that an object is valid and has positive reference count.
#define CHECK_OBJECT(value) (assert((value) != NULL), assert(Py_REFCNT(value) > 0))
#define CHECK_OBJECT_X(value) (assert((value) == NULL || Py_REFCNT(value) > 0))

extern void CHECK_OBJECT_DEEP(PyObject *value);

#include "nuitka/exceptions.h"

// For use with "--trace-execution", code can make outputs. Otherwise they
// are just like comments.
#include "nuitka/tracing.h"

// For checking values if they changed or not.
#ifndef __NUITKA_NO_ASSERT__
extern Py_hash_t DEEP_HASH(PyObject *value);
#endif

// For profiling of Nuitka compiled binaries
#if _NUITKA_PROFILE
extern void startProfiling(void);
extern void stopProfiling(void);
#endif

#include "nuitka/helper/boolean.h"
#include "nuitka/helper/dictionaries.h"
#include "nuitka/helper/mappings.h"
#include "nuitka/helper/sets.h"

#include "nuitka/helper/raising.h"

#include "nuitka/helper/richcomparisons.h"
#include "nuitka/helper/sequences.h"

static inline bool Nuitka_Function_Check(PyObject *object);
static inline PyObject *Nuitka_Function_GetName(PyObject *object);

static inline bool Nuitka_Generator_Check(PyObject *object);
static inline PyObject *Nuitka_Generator_GetName(PyObject *object);

#include "nuitka/calling.h"

NUITKA_MAY_BE_UNUSED static PyObject *TO_FLOAT(PyObject *value) {
    PyObject *result;

#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(value)) {
        result = PyFloat_FromString(value, NULL);
    }
#else
    if (PyUnicode_CheckExact(value)) {
        result = PyFloat_FromString(value);
    }
#endif
    else {
        result = PyNumber_Float(value);
    }

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

#include "nuitka/helper/complex.h"

#include "nuitka/helper/ints.h"

NUITKA_MAY_BE_UNUSED static PyObject *TO_UNICODE3(PyObject *value, PyObject *encoding, PyObject *errors) {
    CHECK_OBJECT(value);
    CHECK_OBJECT_X(encoding);
    CHECK_OBJECT_X(errors);

    char const *encoding_str;

    if (encoding == NULL) {
        encoding_str = NULL;
    } else if (Nuitka_String_Check(encoding)) {
        encoding_str = Nuitka_String_AsString_Unchecked(encoding);
    }
#if PYTHON_VERSION < 0x300
    else if (PyUnicode_Check(encoding)) {
        PyObject *uarg2 = _PyUnicode_AsDefaultEncodedString(encoding, NULL);
        CHECK_OBJECT(uarg2);

        encoding_str = Nuitka_String_AsString_Unchecked(uarg2);
    }
#endif
    else {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("unicode() argument 2 must be string, not %s", encoding);
        return NULL;
    }

    char const *errors_str;

    if (errors == NULL) {
        errors_str = NULL;
    } else if (Nuitka_String_Check(errors)) {
        errors_str = Nuitka_String_AsString_Unchecked(errors);
    }
#if PYTHON_VERSION < 0x300
    else if (PyUnicode_Check(errors)) {
        PyObject *uarg3 = _PyUnicode_AsDefaultEncodedString(errors, NULL);
        CHECK_OBJECT(uarg3);

        errors_str = Nuitka_String_AsString_Unchecked(uarg3);
    }
#endif
    else {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("unicode() argument 3 must be string, not %s", errors);
        return NULL;
    }

    PyObject *result = PyUnicode_FromEncodedObject(value, encoding_str, errors_str);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    assert(PyUnicode_Check(result));

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_VARS(PyObject *source) {
    CHECK_OBJECT(source);

    PyObject *result = PyObject_GetAttr(source, const_str_plain___dict__);

    if (unlikely(result == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "vars() argument must have __dict__ attribute");

        return NULL;
    }

    return result;
}

#include "nuitka/helper/attributes.h"
#include "nuitka/helper/bytearrays.h"
#include "nuitka/helper/iterators.h"
#include "nuitka/helper/lists.h"
#include "nuitka/helper/rangeobjects.h"
#include "nuitka/helper/slices.h"
#include "nuitka/helper/subscripts.h"
#include "nuitka/helper/tuples.h"

#include "nuitka/builtins.h"

#include "nuitka/allocator.h"

#include "helper/operations.h"

// Compile source code given, pretending the file name was given.
#if PYTHON_VERSION < 0x300
extern PyObject *COMPILE_CODE(PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags,
                              PyObject *dont_inherit);
#else
extern PyObject *COMPILE_CODE(PyObject *source_code, PyObject *file_name, PyObject *mode, PyObject *flags,
                              PyObject *dont_inherit, PyObject *optimize);
#endif

#if PYTHON_VERSION < 0x300
extern bool EXEC_FILE_ARG_HANDLING(PyObject **prog, PyObject **name);
#endif

// For quicker built-in open() functionality.
#if PYTHON_VERSION < 0x300
extern PyObject *BUILTIN_OPEN(PyObject *file_name, PyObject *mode, PyObject *buffering);
#else
extern PyObject *BUILTIN_OPEN(PyObject *file_name, PyObject *mode, PyObject *buffering, PyObject *encoding,
                              PyObject *errors, PyObject *newline, PyObject *closefd, PyObject *opener);
#endif

// For quicker built-in chr() functionality.
extern PyObject *BUILTIN_CHR(PyObject *value);

// For quicker built-in ord() functionality.
extern PyObject *BUILTIN_ORD(PyObject *value);

// For quicker built-in bin() functionality.
extern PyObject *BUILTIN_BIN(PyObject *value);

// For quicker built-in oct() functionality.
extern PyObject *BUILTIN_OCT(PyObject *value);

// For quicker built-in hex() functionality.
extern PyObject *BUILTIN_HEX(PyObject *value);

// For quicker callable() functionality.
extern PyObject *BUILTIN_CALLABLE(PyObject *value);

// For quicker iter() functionality if 2 arguments arg given.
extern PyObject *BUILTIN_ITER2(PyObject *callable, PyObject *sentinel);

// For quicker type() functionality if 1 argument is given.
extern PyObject *BUILTIN_TYPE1(PyObject *arg);

// For quicker type() functionality if 3 arguments are given (to build a new
// type).
extern PyObject *BUILTIN_TYPE3(PyObject *module_name, PyObject *name, PyObject *bases, PyObject *dict);

// For built-in built-in len() functionality.
extern PyObject *BUILTIN_LEN(PyObject *boundary);

// For built-in built-in any() functionality.
extern PyObject *BUILTIN_ANY(PyObject *value);

// For built-in built-in super() no args and 2 user args functionality.
extern PyObject *BUILTIN_SUPER2(PyObject *type, PyObject *object);
extern PyObject *BUILTIN_SUPER0(PyObject *type, PyObject *object);

// For built-in built-in all() functionality.
extern PyObject *BUILTIN_ALL(PyObject *value);

// The patched isinstance() functionality used for the built-in.
extern int Nuitka_IsInstance(PyObject *inst, PyObject *cls);

// For built-in getattr() functionality.
extern PyObject *BUILTIN_GETATTR(PyObject *object, PyObject *attribute, PyObject *default_value);

// For built-in setattr() functionality.
extern PyObject *BUILTIN_SETATTR(PyObject *object, PyObject *attribute, PyObject *value);

// For built-in bytearray() functionality.
extern PyObject *BUILTIN_BYTEARRAY1(PyObject *value);
extern PyObject *BUILTIN_BYTEARRAY3(PyObject *string, PyObject *encoding, PyObject *errors);

// For built-in hash() functionality.
extern PyObject *BUILTIN_HASH(PyObject *value);
extern Py_hash_t HASH_VALUE_WITHOUT_ERROR(PyObject *value);
extern Py_hash_t HASH_VALUE_WITH_ERROR(PyObject *value);

// For built-in sum() functionality.
extern PyObject *BUILTIN_SUM1(PyObject *sequence);
extern PyObject *BUILTIN_SUM2(PyObject *sequence, PyObject *start);

// For built-in built-in abs() functionality.
extern PyObject *BUILTIN_ABS(PyObject *o);

// For built-in bytes() functionality.
#if PYTHON_VERSION >= 0x300
extern PyObject *BUILTIN_BYTES1(PyObject *value);
extern PyObject *BUILTIN_BYTES3(PyObject *value, PyObject *encoding, PyObject *errors);
#endif

// For built-in eval() functionality, works on byte compiled code already.
extern PyObject *EVAL_CODE(PyObject *code, PyObject *globals, PyObject *locals);

// For built-in format() functionality.
extern PyObject *BUILTIN_FORMAT(PyObject *value, PyObject *format_spec);

// For built-in staticmethod() functionality.
extern PyObject *BUILTIN_STATICMETHOD(PyObject *function);

// For built-in classmethod() functionality.
extern PyObject *BUILTIN_CLASSMETHOD(PyObject *function);

// For built-in "int()" functionality with 2 arguments.
extern PyObject *BUILTIN_INT2(PyObject *value, PyObject *base);

#if PYTHON_VERSION < 0x300
// For built-in "long()" functionality with 2 arguments.
extern PyObject *BUILTIN_LONG2(PyObject *value, PyObject *base);
#endif

#include "nuitka/importing.h"

// Hard imports have their own helpers.
#include "nuitka/helper/import_hard.h"

// For the constant loading:

// Call this to initialize all common constants pre-main.
extern void createGlobalConstants(void);

// Call this to check of common constants are still intact.
#ifndef __NUITKA_NO_ASSERT__
extern void checkGlobalConstants(void);
#endif

#if _NUITKA_PLUGIN_MULTIPROCESSING_ENABLED || _NUITKA_PLUGIN_TRACEBACK_ENCRYPTION_ENABLED
// Call this to initialize __main__ constants in non-standard processes.
extern void createMainModuleConstants(void);
#endif

// Unstreaming constants from a blob.
#include "nuitka/constants_blob.h"

// Performance enhancements to Python types.
extern void enhancePythonTypes(void);

// Setup meta path based loader if any.
extern void setupMetaPathBasedLoader(void);

// Replace built-in functions with ones that accept compiled types too.
extern void patchBuiltinModule(void);

/* Replace inspect functions with ones that handle compiles types too. */
#if PYTHON_VERSION >= 0x300
extern void patchInspectModule(void);
#endif

// Replace type comparison with one that accepts compiled types too, will work
// for "==" and "!=", but not for "is" checks.
extern void patchTypeComparison(void);

// Patch the CPython type for tracebacks and make it use a freelist mechanism
// to be slightly faster for exception control flows.
extern void patchTracebackDealloc(void);

#if PYTHON_VERSION < 0x300
// Initialize value for "tp_compare" default.
extern void _initSlotCompare(void);
#endif

#if PYTHON_VERSION >= 0x300
// Select the metaclass from specified one and given bases.
extern PyObject *SELECT_METACLASS(PyObject *metaclass, PyObject *bases);
#endif

NUITKA_MAY_BE_UNUSED static PyObject *MODULE_NAME1(PyObject *module) {
    assert(PyModule_Check(module));
    PyObject *module_dict = ((PyModuleObject *)module)->md_dict;

    return DICT_GET_ITEM1(module_dict, const_str_plain___name__);
}

NUITKA_MAY_BE_UNUSED static PyObject *MODULE_NAME0(PyObject *module) {
    assert(PyModule_Check(module));
    PyObject *module_dict = ((PyModuleObject *)module)->md_dict;

    return DICT_GET_ITEM0(module_dict, const_str_plain___name__);
}

// Get the binary directory was wide characters.
extern wchar_t const *getBinaryDirectoryWideChars();

#if !defined(_WIN32) || PYTHON_VERSION < 0x300
// Get the binary directory, translated to native path
extern char const *getBinaryDirectoryHostEncoded();
#endif

#if _NUITKA_STANDALONE
extern void setEarlyFrozenModulesFileAttribute(void);
#endif

/* For making paths relative to where we got loaded from. Do not provide any
 * absolute paths as relative value, this is not as capable as "os.path.join",
 * instead just works on strings.
 */
extern PyObject *MAKE_RELATIVE_PATH(PyObject *relative);

/* For concatenating two elemented path, typically a dirname and a filename.

   We do this in a lot of helper code, and this is shared functionality.
*/
extern PyObject *JOIN_PATH2(PyObject *dirname, PyObject *filename);

#include <nuitka/threading.h>

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE(PyObject **elements, Py_ssize_t size) {
    PyObject *result = PyTuple_New(size);

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = elements[i];
        Py_INCREF(item);
        PyTuple_SET_ITEM(result, i, item);
    }

    return result;
}

// Make a deep copy of an object.
extern PyObject *DEEP_COPY(PyObject *value);

// Force a garbage collection, for debugging purposes.
NUITKA_MAY_BE_UNUSED static void forceGC() {
    PyObject_CallObject(PyObject_GetAttrString(PyImport_ImportModule("gc"), "collect"), NULL);
}

#endif
