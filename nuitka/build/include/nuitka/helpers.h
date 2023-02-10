//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_FRAME
#define _DEBUG_FRAME 1
#else
#define _DEBUG_FRAME 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_REFRAME
#define _DEBUG_REFRAME 1
#else
#define _DEBUG_REFRAME 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_EXCEPTIONS
#define _DEBUG_EXCEPTIONS 1
#else
#define _DEBUG_EXCEPTIONS 0
#endif
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
    PyObject_HEAD

        PyObject *md_dict;
} PyModuleObject;

// Generated code helpers, used in static helper codes:
extern PyObject *CALL_FUNCTION_WITH_ARGS2(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_ARGS3(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_ARGS4(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_ARGS5(PyObject *called, PyObject *const *args);

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
#include "nuitka/helper/indexes.h"
#include "nuitka/helper/mappings.h"
#include "nuitka/helper/operations_builtin_types.h"
#include "nuitka/helper/sets.h"
#include "nuitka/helper/strings.h"

#include "nuitka/helper/raising.h"

#include "nuitka/helper/richcomparisons.h"
#include "nuitka/helper/sequences.h"

static inline bool Nuitka_Function_Check(PyObject *object);
static inline PyObject *Nuitka_Function_GetName(PyObject *object);

static inline bool Nuitka_Generator_Check(PyObject *object);
static inline PyObject *Nuitka_Generator_GetName(PyObject *object);

#include "nuitka/calling.h"
#include "nuitka/helper/bytes.h"
#include "nuitka/helper/complex.h"
#include "nuitka/helper/floats.h"
#include "nuitka/helper/ints.h"

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

// For quicker built-in str() functionality, Python2 str
extern PyObject *BUILTIN_STR(PyObject *value);

// For quicker built-in unicode() functionality, Python3 str or Python2 unicode
extern PyObject *BUILTIN_UNICODE1(PyObject *value);
extern PyObject *BUILTIN_UNICODE3(PyObject *value, PyObject *encoding, PyObject *errors);

// For quicker built-in open() functionality.
#if PYTHON_VERSION < 0x300
extern PyObject *BUILTIN_OPEN(PyObject *file_name, PyObject *mode, PyObject *buffering);
#else
extern PyObject *BUILTIN_OPEN(PyObject *file_name, PyObject *mode, PyObject *buffering, PyObject *encoding,
                              PyObject *errors, PyObject *newline, PyObject *closefd, PyObject *opener);
#endif

// Small helper to open files with few arguments in C.
extern PyObject *BUILTIN_OPEN_BINARY_READ_SIMPLE(PyObject *filename);
extern PyObject *BUILTIN_OPEN_SIMPLE(PyObject *filename, char const *mode, bool buffering, PyObject *encoding);

// Small helper to read file contents with few arguments in C.
extern PyObject *GET_FILE_BYTES(PyObject *filename);

// Small helpers to check file attributes
extern PyObject *OS_PATH_FILE_EXISTS(PyObject *filename);
extern PyObject *OS_PATH_FILE_ISFILE(PyObject *filename);
extern PyObject *OS_PATH_FILE_ISDIR(PyObject *filename);

// Small helper to list a directory.
extern PyObject *OS_LISTDIR(PyObject *path);

// Platform standard slash for filenames
#if defined(_WIN32)
#define const_platform_sep const_str_backslash
#else
#define const_platform_sep const_str_slash
#endif

// Small helpers to work with filenames.
extern PyObject *OS_PATH_BASENAME(PyObject *filename);

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
extern PyObject *BUILTIN_SUPER2(PyDictObject *module_dict, PyObject *type, PyObject *object);
extern PyObject *BUILTIN_SUPER0(PyDictObject *module_dict, PyObject *type, PyObject *object);

// For built-in built-in all() functionality.
extern PyObject *BUILTIN_ALL(PyObject *value);

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
#ifdef _NUITKA_EXE
extern void checkModuleConstants___main__(void);
#endif
#endif

// Call this to initialize __main__ constants in non-standard processes.
#ifdef _NUITKA_EXE
extern void createMainModuleConstants(void);
#endif

// Deserialize constants from a blob.
#include "nuitka/constants_blob.h"

// Performance enhancements to Python types.
extern void enhancePythonTypes(void);

// Setup meta path based loader if any.
extern void setupMetaPathBasedLoader(void);

/* Replace inspect functions with ones that handle compiles types too. */
#if PYTHON_VERSION >= 0x300
extern void patchInspectModule(void);
#endif

// Replace type comparison with one that accepts compiled types too, will work
// for "==" and "!=", but not for "is" checks.
extern void patchTypeComparison(void);

// Patch the CPython type for tracebacks and make it use a free list mechanism
// to be slightly faster for exception control flows.
extern void patchTracebackDealloc(void);

// Initialize value for "tp_compare" and "tp_init" defaults.
extern void _initSlotCompare(void);

// Default __init__ slot wrapper.
extern python_initproc default_tp_init_wrapper;

#if PYTHON_VERSION >= 0x300
// Select the metaclass from specified one and given bases.
extern PyObject *SELECT_METACLASS(PyObject *metaclass, PyObject *bases);
#endif

#if PYTHON_VERSION >= 0x3a0
extern PyObject *MATCH_CLASS_ARGS(PyObject *matched, Py_ssize_t max_allowed);
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
extern wchar_t const *getBinaryDirectoryWideChars(void);

#if !defined(_WIN32) || PYTHON_VERSION < 0x300
// Get the binary directory, translated to native path
extern char const *getBinaryDirectoryHostEncoded(void);
#endif

#if _NUITKA_STANDALONE
extern void setEarlyFrozenModulesFileAttribute(void);
#endif

/* For making paths relative to where we got loaded from. Do not provide any
 * absolute paths as relative value, this is not as capable as "os.path.join",
 * instead just works on strings.
 */
extern PyObject *MAKE_RELATIVE_PATH(PyObject *relative);

/* For concatenating two elements path, typically a dirname and a filename.

   We do this in a lot of helper code, and this is shared functionality.
*/
extern PyObject *JOIN_PATH2(PyObject *dirname, PyObject *filename);

#include <nuitka/threading.h>

// Make a deep copy of an object of general or specific type.
extern PyObject *DEEP_COPY(PyObject *value);
extern PyObject *DEEP_COPY_DICT(PyObject *dict_value);
extern PyObject *DEEP_COPY_LIST(PyObject *value);
extern PyObject *DEEP_COPY_TUPLE(PyObject *value);
extern PyObject *DEEP_COPY_SET(PyObject *value);

// Constants deep copies are guided by value type descriptions.
extern PyObject *DEEP_COPY_LIST_GUIDED(PyObject *value, char const *guide);
extern PyObject *DEEP_COPY_TUPLE_GUIDED(PyObject *value, char const *guide);

// UnionType, normally not accessible
extern PyTypeObject *Nuitka_PyUnion_Type;

// Force a garbage collection, for debugging purposes.
NUITKA_MAY_BE_UNUSED static void forceGC(void) {
    PyObject_CallObject(PyObject_GetAttrString(PyImport_ImportModule("gc"), "collect"), NULL);
}

// We provide the sys.version info shortcut as a global value here for ease of use.
extern PyObject *Py_SysVersionInfo;

#include "nuitka/python_pgo.h"

extern PyObject *MAKE_UNION_TYPE(PyObject *args);

#endif
