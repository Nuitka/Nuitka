//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_HELPERS_H__
#define __NUITKA_HELPERS_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/allocator.h"
#include "nuitka/cpython_api_compat.h"
#include "nuitka/defines.h"
#endif

// CPython's PyModuleObject is private before 3.10; mirror its layout for fast md_dict access.
#if PYTHON_VERSION < 0x3a0
typedef struct {
    PyObject_HEAD

        PyObject *md_dict;
} PyModuleObject;
#endif

extern PyObject *CALL_FUNCTION_WITH_ARGS2(PyThreadState *tstate, PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_ARGS3(PyThreadState *tstate, PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_ARGS4(PyThreadState *tstate, PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_ARGS5(PyThreadState *tstate, PyObject *called, PyObject *const *args);

#include "nuitka/tracing.h"

#ifndef __NUITKA_NO_ASSERT__
extern Py_hash_t DEEP_HASH(PyThreadState *tstate, PyObject *value);
extern void DEEP_HASH_BLOB(Py_hash_t *hash, void const *s, Py_ssize_t size);
#endif

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

#include "nuitka/helper/ints.h"
#include "nuitka/helper/richcomparisons.h"
#include "nuitka/helper/sequences.h"

static inline bool Nuitka_Function_Check(PyObject *obj);
static inline PyObject *Nuitka_Function_GetName(PyObject *obj);

struct Nuitka_FunctionObject;
extern PyObject *Nuitka_CallFunctionNoArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function);
extern PyObject *Nuitka_CallFunctionPosArgs(PyThreadState *tstate, struct Nuitka_FunctionObject const *function,
                                            PyObject *const *args, Py_ssize_t args_size);

static inline bool Nuitka_Generator_Check(PyObject *obj);
static inline PyObject *Nuitka_Generator_GetName(PyObject *obj);

#include "nuitka/calling.h"
#include "nuitka/helper/bytes.h"
#include "nuitka/helper/complex.h"
#include "nuitka/helper/floats.h"

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_VARS(PyThreadState *tstate, PyObject *source) {
    CHECK_OBJECT(source);

    PyObject *result = PyObject_GetAttr(source, const_str_plain___dict__);

    if (unlikely(result == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "vars() argument must have __dict__ attribute");

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

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_WITH_ARGS(PyThreadState *tstate, PyObject *function_object,
                                                              PyObject *const *args, Py_ssize_t count) {
    if (count == 0) {
        return CALL_FUNCTION_NO_ARGS(tstate, function_object);
    } else if (count == 1) {
        return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, function_object, args[0]);
    }

#if PYTHON_VERSION >= 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_VECTORCALL_USAGE)
    if (PyType_HasFeature(Py_TYPE(function_object), _Py_TPFLAGS_HAVE_VECTORCALL)) {
        vectorcallfunc func =
            *((vectorcallfunc *)(((char *)function_object) + Py_TYPE(function_object)->tp_vectorcall_offset));

        if (likely(func != NULL)) {
            PyObject *result = func(function_object, args, count, NULL);

            CHECK_OBJECT_X(result);

            return Nuitka_CheckFunctionResult(tstate, function_object, result);
        }
    }
#endif

    if (Nuitka_Function_Check(function_object)) {
        if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
            return NULL;
        }

        PyObject *result =
            Nuitka_CallFunctionPosArgs(tstate, (struct Nuitka_FunctionObject const *)function_object, args, count);

        Py_LeaveRecursiveCall();

        CHECK_OBJECT_X(result);

        return result;
#if PYTHON_VERSION < 0x380 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_UNCOMPILED_FUNCTION_CALL_OPT)
    } else if (PyFunction_Check(function_object)) {
        PyObject *result = callPythonFunction(function_object, args, (int)count);

        CHECK_OBJECT_X(result);

        return result;
#endif
    }

    PyObject *args_tuple = MAKE_TUPLE_VAR(tstate, args, count);

    PyObject *result = CALL_FUNCTION(tstate, function_object, args_tuple, NULL);

    Py_DECREF(args_tuple);

    return result;
}

#include "nuitka/builtins.h"

#include "helper/operations.h"

#if PYTHON_VERSION < 0x300
extern PyObject *COMPILE_CODE(PyThreadState *tstate, PyObject *source_code, PyObject *file_name, PyObject *mode,
                              PyObject *flags, PyObject *dont_inherit);
#else
extern PyObject *COMPILE_CODE(PyThreadState *tstate, PyObject *source_code, PyObject *file_name, PyObject *mode,
                              PyObject *flags, PyObject *dont_inherit, PyObject *optimize);
#endif

// Compile source code for "exec" and "eval", which do not suppress constant
// immortalization in CPython.
#if PYTHON_VERSION < 0x300
extern PyObject *COMPILE_CODE_EXEC(PyThreadState *tstate, PyObject *source_code, PyObject *file_name, PyObject *mode,
                                   PyObject *flags, PyObject *dont_inherit);
#else
extern PyObject *COMPILE_CODE_EXEC(PyThreadState *tstate, PyObject *source_code, PyObject *file_name, PyObject *mode,
                                   PyObject *flags, PyObject *dont_inherit, PyObject *optimize);
#endif

#if PYTHON_VERSION < 0x300
extern bool EXEC_FILE_ARG_HANDLING(PyThreadState *tstate, PyObject **prog, PyObject **name);
#endif

#if PYTHON_VERSION < 0x300
// Python 2 str() built-in.
extern PyObject *BUILTIN_STR(PyObject *value);
#define BUILTIN_STR_OR_UNICODE1(value) BUILTIN_STR(value)
#else
#define BUILTIN_STR_OR_UNICODE1(value) BUILTIN_UNICODE1(value)
#endif

// Python 3 str() / Python 2 unicode() built-in.
extern PyObject *BUILTIN_UNICODE1(PyObject *value);
extern PyObject *BUILTIN_UNICODE3(PyObject *value, PyObject *encoding, PyObject *errors);

#if PYTHON_VERSION < 0x300
extern PyObject *BUILTIN_OPEN(PyThreadState *tstate, PyObject *file_name, PyObject *mode, PyObject *buffering);
#else
extern PyObject *BUILTIN_OPEN(PyThreadState *tstate, PyObject *file_name, PyObject *mode, PyObject *buffering,
                              PyObject *encoding, PyObject *errors, PyObject *newline, PyObject *closefd,
                              PyObject *opener);
#endif

extern PyObject *BUILTIN_OPEN_BINARY_READ_SIMPLE(PyThreadState *tstate, PyObject *filename);
extern PyObject *BUILTIN_OPEN_SIMPLE(PyThreadState *tstate, PyObject *filename, char const *mode, bool buffering,
                                     PyObject *encoding);

extern PyObject *GET_FILE_BYTES(PyThreadState *tstate, PyObject *filename);

extern PyObject *OS_PATH_FILE_EXISTS(PyThreadState *tstate, PyObject *filename);
extern PyObject *OS_PATH_FILE_ISFILE(PyThreadState *tstate, PyObject *filename);
extern PyObject *OS_PATH_FILE_ISDIR(PyThreadState *tstate, PyObject *filename);

extern PyObject *OS_LISTDIR(PyThreadState *tstate, PyObject *path);

extern PyObject *OS_STAT(PyThreadState *tstate, PyObject *path, PyObject *dir_fd, PyObject *follow_symlinks);
extern PyObject *OS_LSTAT(PyThreadState *tstate, PyObject *path, PyObject *dir_fd);

#if defined(_WIN32)
#define const_platform_sep const_str_backslash
#else
#define const_platform_sep const_str_slash
#endif

extern PyObject *OS_PATH_BASENAME(PyThreadState *tstate, PyObject *filename);
extern PyObject *OS_PATH_DIRNAME(PyThreadState *tstate, PyObject *filename);
extern PyObject *OS_PATH_JOIN(PyThreadState *tstate, PyObject *const *paths, Py_ssize_t count);
extern PyObject *OS_PATH_ABSPATH(PyThreadState *tstate, PyObject *filename);
extern PyObject *OS_PATH_ISABS(PyThreadState *tstate, PyObject *filename);
extern PyObject *OS_PATH_NORMPATH(PyThreadState *tstate, PyObject *filename);

nuitka_bool compareFilePaths(PyThreadState *tstate, PyObject *filename_a, PyObject *filename_b);

extern PyObject *BUILTIN_CHR(PyThreadState *tstate, PyObject *value);
extern PyObject *BUILTIN_ORD(PyObject *value);
extern PyObject *BUILTIN_BIN(PyObject *value);
extern PyObject *BUILTIN_OCT(PyThreadState *tstate, PyObject *value);
extern PyObject *BUILTIN_HEX(PyThreadState *tstate, PyObject *value);
extern PyObject *BUILTIN_CALLABLE(PyObject *value);
extern PyObject *BUILTIN_ITER2(PyObject *callable, PyObject *sentinel);

extern PyObject *BUILTIN_ENUMERATE1(PyThreadState *tstate, PyObject *sequence);
extern PyObject *BUILTIN_ENUMERATE2(PyThreadState *tstate, PyObject *sequence, PyObject *start);
extern PyObject *BUILTIN_ZIP(PyThreadState *tstate, PyObject *const *iterables, Py_ssize_t count);
#if PYTHON_VERSION >= 0x3a0
extern PyObject *BUILTIN_ZIP310(PyThreadState *tstate, PyObject *iterables, PyObject *strict);
#endif

extern PyObject *BUILTIN_TYPE1(PyObject *arg);
extern PyObject *BUILTIN_TYPE3(PyThreadState *tstate, PyObject *module_name, PyObject *name, PyObject *bases,
                               PyObject *dict);

#if PYTHON_VERSION >= 0x3f0
extern PyObject *BUILTIN_SENTINEL(PyThreadState *tstate, PyObject *name, PyObject *repr, PyDictObject *module_dict);
#endif

extern PyObject *BUILTIN_LEN(PyThreadState *tstate, PyObject *boundary);
extern PyObject *BUILTIN_ANY(PyThreadState *tstate, PyObject *value);
extern PyObject *BUILTIN_SUPER2(PyThreadState *tstate, PyDictObject *module_dict, PyObject *type, PyObject *obj);
extern PyObject *BUILTIN_SUPER0(PyThreadState *tstate, PyDictObject *module_dict, PyObject *type, PyObject *obj);
extern PyObject *BUILTIN_ALL(PyThreadState *tstate, PyObject *value);
extern PyObject *BUILTIN_GETATTR(PyThreadState *tstate, PyObject *obj, PyObject *attribute, PyObject *default_value);
extern PyObject *BUILTIN_SETATTR(PyObject *obj, PyObject *attribute, PyObject *value);
extern PyObject *BUILTIN_DELATTR(PyObject *obj, PyObject *attribute);

extern PyObject *BUILTIN_BYTEARRAY1(PyObject *value);
extern PyObject *BUILTIN_BYTEARRAY3(PyThreadState *tstate, PyObject *string_arg, PyObject *encoding, PyObject *errors);

extern PyObject *BUILTIN_HASH(PyThreadState *tstate, PyObject *value);
extern Py_hash_t HASH_VALUE_WITHOUT_ERROR(PyThreadState *tstate, PyObject *value);
extern Py_hash_t HASH_VALUE_WITH_ERROR(PyThreadState *tstate, PyObject *value);

extern PyObject *BUILTIN_SUM1(PyThreadState *tstate, PyObject *sequence);
extern PyObject *BUILTIN_SUM2(PyThreadState *tstate, PyObject *sequence, PyObject *start);

extern PyObject *BUILTIN_ABS(PyObject *o);

#if PYTHON_VERSION >= 0x300
extern PyObject *BUILTIN_BYTES1(PyThreadState *tstate, PyObject *value);
extern PyObject *BUILTIN_BYTES3(PyThreadState *tstate, PyObject *value, PyObject *encoding, PyObject *errors);
#endif

// Evaluates pre-compiled code objects.
extern PyObject *EVAL_CODE(PyThreadState *tstate, PyObject *code, PyObject *globals, PyObject *locals,
                           PyObject *closure);

extern PyObject *BUILTIN_FORMAT(PyThreadState *tstate, PyObject *value, PyObject *format_spec);
extern PyObject *BUILTIN_STATICMETHOD(PyThreadState *tstate, PyObject *function);
extern PyObject *BUILTIN_CLASSMETHOD(PyThreadState *tstate, PyObject *function);

// prompt may be NULL.
extern PyObject *BUILTIN_INPUT(PyThreadState *tstate, PyObject *prompt);

extern PyObject *BUILTIN_INT2(PyThreadState *tstate, PyObject *value, PyObject *base);

#if PYTHON_VERSION < 0x300
extern PyObject *BUILTIN_LONG2(PyThreadState *tstate, PyObject *value, PyObject *base);
#endif

extern PyObject *BUILTIN_REVERSED(PyThreadState *tstate, PyObject *value);

#if PYTHON_VERSION < 0x300
extern PyObject *BUILTIN_SORTED(PyThreadState *tstate, PyObject *iterable, PyObject *cmp, PyObject *key,
                                PyObject *reverse);
#else
extern PyObject *BUILTIN_SORTED(PyThreadState *tstate, PyObject *iterable, PyObject *key, PyObject *reverse);
extern PyObject *BUILTIN_SORTED1(PyThreadState *tstate, PyObject *iterable);
#endif

extern PyObject *BUILTIN_MEMORYVIEW(PyThreadState *tstate, PyObject *value);

#if PYTHON_VERSION < 0x300
extern PyObject *BUILTIN_PRINT(PyThreadState *tstate, PyObject **values, int count, PyObject *sep, PyObject *end,
                               PyObject *file);
#else
extern PyObject *BUILTIN_PRINT(PyThreadState *tstate, PyObject **values, int count, PyObject *sep, PyObject *end,
                               PyObject *file, PyObject *flush);
#endif

extern PyObject *BUILTIN_PRINT1(PyThreadState *tstate, PyObject **values, int count);
extern PyObject *BUILTIN_PRINT1_NO_ARGS(PyThreadState *tstate);
extern PyObject *BUILTIN_PRINT1_SINGLE_ARG(PyThreadState *tstate, PyObject *arg);
extern PyObject *BUILTIN_PRINT1_TWO_ARGS(PyThreadState *tstate, PyObject *arg1, PyObject *arg2);

#include "nuitka/helper/import_hard.h"
#include "nuitka/importing.h"

#if _NUITKA_MODULE_MODE
extern void createGlobalConstants(PyThreadState *tstate, PyObject *real_module_name);
#else
extern void createGlobalConstants(PyThreadState *tstate);
#endif

#ifndef __NUITKA_NO_ASSERT__
extern void checkGlobalConstants(void);
#if !_NUITKA_MODULE_MODE
extern void checkModuleConstants___main__(PyThreadState *tstate);
#endif
#endif

// Initialize "__main__" constants in non-standard entry points (e.g. multiprocessing spawn).
#if !_NUITKA_MODULE_MODE
extern void createMainModuleConstants(PyThreadState *tstate);
#endif

#include "nuitka/constants_blob.h"

extern void enhancePythonTypes(void);

extern void setupMetaPathBasedLoader(PyThreadState *tstate);

#if PYTHON_VERSION >= 0x300
extern void patchInspectModule(PyThreadState *tstate);
#endif

// Replace "eval", "exec", and frame locals built-ins with ones that handle
// compiled frames. Must run after global constants are created and before
// module constants are created.
#if PYTHON_VERSION >= 0x3d0
extern void patchBuiltinFrameFunctions(PyThreadState *tstate);
#endif

// Replace type comparison with one that accepts compiled types too; works for
// "==" and "!=", not "is".
extern void patchTypeComparison(void);

extern void patchTracebackDealloc(void);

extern void _initSlotCompare(void);

extern python_init_proc default_tp_init_wrapper;

#if PYTHON_VERSION >= 0x300
extern PyObject *SELECT_METACLASS(PyThreadState *tstate, PyObject *metaclass, PyObject *bases);
#endif

#if PYTHON_VERSION >= 0x3a0
extern PyObject *MATCH_CLASS_ARGS(PyThreadState *tstate, PyObject *matched, PyObject *matched_type,
                                  Py_ssize_t positional_count, PyObject **keywords, Py_ssize_t keywords_count);
#endif

NUITKA_MAY_BE_UNUSED static PyObject *MODULE_NAME1(PyThreadState *tstate, PyObject *module) {
    assert(PyModule_Check(module));
    PyObject *module_dict = ((PyModuleObject *)module)->md_dict;

    return DICT_GET_ITEM1(tstate, module_dict, const_str_plain___name__);
}

extern wchar_t const *getBinaryDirectoryWideChars(bool resolve_symlinks);
extern char const *getBinaryDirectoryHostEncoded(bool resolve_symlinks);
extern PyObject *getPythonProgramDirectoryObject(bool resolve_symlinks);
extern PyObject *getContainingDirectoryObject(bool resolve_symlinks);

// Returns a new reference.
extern PyObject *getPythonRuntimeDirObject(void);

// Returns a new reference.
extern PyObject *getProcessExeObject(void);

extern PyObject *getDllFilenameObject(void);

// Original argv[0] recorded during bootstrap; returns None if unavailable.
#if _NUITKA_EXE_MODE || _NUITKA_DLL_MODE
extern PyObject *getOriginalArgv0Object(void);
#endif

#if _NUITKA_STANDALONE_MODE
extern void setEarlyFrozenModulesFileAttribute(PyThreadState *tstate);
#endif

// Join relative path to the loaded binary/module directory; relative must not
// be an absolute path (string concatenation, not full os.path.join).
extern PyObject *MAKE_RELATIVE_PATH(PyObject *relative);

extern PyObject *JOIN_PATH2(PyObject *dirname, PyObject *filename);

#include <nuitka/threading.h>

extern PyObject *DEEP_COPY(PyThreadState *tstate, PyObject *value);
extern PyObject *DEEP_COPY_DICT(PyThreadState *tstate, PyObject *dict_value);
#if PYTHON_VERSION >= 0x3f0
extern PyObject *DEEP_COPY_FROZENDICT(PyThreadState *tstate, PyObject *frozendict_value);
#endif
extern PyObject *DEEP_COPY_LIST(PyThreadState *tstate, PyObject *value);
extern PyObject *DEEP_COPY_TUPLE(PyThreadState *tstate, PyObject *value);
extern PyObject *DEEP_COPY_SET(PyThreadState *tstate, PyObject *value);

// Constants deep copies guided by value type descriptions.
extern PyObject *DEEP_COPY_LIST_GUIDED(PyThreadState *tstate, PyObject *value, char const *guide);
extern PyObject *DEEP_COPY_TUPLE_GUIDED(PyThreadState *tstate, PyObject *value, char const *guide);

extern PyTypeObject *Nuitka_PyUnion_Type;

NUITKA_MAY_BE_UNUSED static void forceGC(void) {
    PyObject_CallObject(PyObject_GetAttrString(PyImport_ImportModule("gc"), "collect"), NULL);
}

extern PyObject *Py_SysVersionInfo;

#include "nuitka/python_pgo.h"

extern PyObject *MAKE_UNION_TYPE(PyObject *args);

// Wrapper for "PyType_Ready" that avoids DLL entry points for generic
// attribute/iterator slots. spell-checker: ignore aiter
extern void Nuitka_PyType_Ready(PyTypeObject *type, PyTypeObject *base, bool generic_get_attr, bool generic_set_attr,
                                bool self_iter, bool await_self_iter, bool self_aiter);

#if PYTHON_VERSION >= 0x3b0
#include "nuitka/exception_groups.h"
#endif

#if PYTHON_VERSION >= 0x3c0
#include "nuitka/type_aliases.h"
#endif

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
