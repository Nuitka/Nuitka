#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=I0021,too-many-arguments,too-many-return-statements,too-many-statements


"""Prepared code generation templates

WARNING, this code is GENERATED. Modify the template CodeTemplates*.py instead!

spell-checker: ignore __prepare__ append args autograph capitalize casefold center chars
spell-checker: ignore clear copy count decode default delete dist distribution_name encode
spell-checker: ignore encoding end endswith errors exit_code expandtabs
spell-checker: ignore experimental_attributes experimental_autograph_options
spell-checker: ignore experimental_compile experimental_follow_type_hints
spell-checker: ignore experimental_implements experimental_relax_shapes extend fillchar
spell-checker: ignore find format format_map formatmap fromkeys func get group handle
spell-checker: ignore has_key haskey index input_signature insert isalnum isalpha isascii
spell-checker: ignore isdecimal isdigit isidentifier islower isnumeric isprintable isspace
spell-checker: ignore istitle isupper item items iterable iteritems iterkeys itervalues
spell-checker: ignore jit_compile join keepends key keys kwargs ljust lower lstrip
spell-checker: ignore maketrans maxsplit mode name new old p package
spell-checker: ignore package_or_requirement pairs partition path pop popitem prefix
spell-checker: ignore prepare reduce_retracing remove replace resource resource_name
spell-checker: ignore reverse rfind rindex rjust rpartition rsplit rstrip s sep setdefault
spell-checker: ignore sort split splitlines start startswith stop strip sub suffix
spell-checker: ignore swapcase table tabsize title translate update upper use_errno
spell-checker: ignore use_last_error value values viewitems viewkeys viewvalues width
spell-checker: ignore winmode zfill
"""

# pylint: disable=unused-argument


def _emit_000_template_asyncgen_object_maker_template(emit, values):
    emit("static PyObject *")
    emit(values["asyncgen_maker_identifier"])
    emit("(")
    emit(values["asyncgen_creation_args"])
    emit(");\n")


def _emit_000_template_asyncgen_object_maker_template_readable(emit, values):
    emit("static PyObject *")
    emit(values["asyncgen_maker_identifier"])
    emit("(")
    emit(values["asyncgen_creation_args"])
    emit(");\n")


def _emit_001_template_asyncgen_object_body(emit, values):
    emit("\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nstruct ")
    emit(values["function_identifier"])
    emit("_locals {\n")
    emit(values["function_local_types"])
    emit("\n};\n#endif\n\nstatic PyObject *")
    emit(values["function_identifier"])
    emit(
        "_context(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen, PyObject *yield_return_value) {\nCHECK_OBJECT(asyncgen);\nassert(Nuitka_Asyncgen_Check((PyObject *)asyncgen));\nCHECK_OBJECT_X(yield_return_value);\n\n#if "
    )
    emit(values["has_heap_declaration"])
    emit("\n\n")
    emit(values["heap_declaration"])
    emit("\n#endif\n\n\n")
    emit(values["function_dispatch"])
    emit("\n\n\n")
    emit(values["function_var_inits"])
    emit("\n\n\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["asyncgen_exit"])
    emit("\n}\n\nstatic PyObject *")
    emit(values["asyncgen_maker_identifier"])
    emit("(")
    emit(values["asyncgen_creation_args"])
    emit(") {\nreturn Nuitka_Asyncgen_New(\n")
    emit(values["function_identifier"])
    emit("_context,\n")
    emit(values["asyncgen_module"])
    emit(",\n")
    emit(values["asyncgen_name_obj"])
    emit(",\n")
    emit(values["asyncgen_qualname_obj"])
    emit(",\n")
    emit(values["code_identifier"])
    emit(",\n")
    emit(values["closure_name"])
    emit(",\n")
    emit(str(values["closure_count"]))
    emit(",\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nsizeof(struct ")
    emit(values["function_identifier"])
    emit("_locals)\n#else\n0\n#endif\n);\n}\n")


def _emit_001_template_asyncgen_object_body_readable(emit, values):
    emit("\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nstruct ")
    emit(values["function_identifier"])
    emit("_locals {\n")
    emit(values["function_local_types"])
    emit("\n};\n#endif\n\nstatic PyObject *")
    emit(values["function_identifier"])
    emit(
        "_context(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen, PyObject *yield_return_value) {\n    CHECK_OBJECT(asyncgen);\n    assert(Nuitka_Asyncgen_Check((PyObject *)asyncgen));\n    CHECK_OBJECT_X(yield_return_value);\n\n#if "
    )
    emit(values["has_heap_declaration"])
    emit("\n    // Heap access.\n")
    emit(values["heap_declaration"])
    emit("\n#endif\n\n    // Dispatch to yield based on return label index:\n")
    emit(values["function_dispatch"])
    emit("\n\n    // Local variable initialization\n")
    emit(values["function_var_inits"])
    emit("\n\n    // Actual asyncgen body.\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["asyncgen_exit"])
    emit("\n}\n\nstatic PyObject *")
    emit(values["asyncgen_maker_identifier"])
    emit("(")
    emit(values["asyncgen_creation_args"])
    emit(") {\n    return Nuitka_Asyncgen_New(\n        ")
    emit(values["function_identifier"])
    emit("_context,\n        ")
    emit(values["asyncgen_module"])
    emit(",\n        ")
    emit(values["asyncgen_name_obj"])
    emit(",\n        ")
    emit(values["asyncgen_qualname_obj"])
    emit(",\n        ")
    emit(values["code_identifier"])
    emit(",\n        ")
    emit(values["closure_name"])
    emit(",\n        ")
    emit(str(values["closure_count"]))
    emit(",\n#if ")
    emit(values["has_heap_declaration"])
    emit("\n        sizeof(struct ")
    emit(values["function_identifier"])
    emit("_locals)\n#else\n        0\n#endif\n    );\n}\n")


def _emit_002_template_make_asyncgen(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["asyncgen_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_002_template_make_asyncgen_readable(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["asyncgen_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_003_template_asyncgen_exception_exit(emit, values):
    emit(
        'NUITKA_CANNOT_GET_HERE("return must be present");\n\nfunction_exception_exit:\n'
    )
    emit(values["function_cleanup"])
    emit("\nCHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\nRESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\nreturn NULL;\n")


def _emit_003_template_asyncgen_exception_exit_readable(emit, values):
    emit(
        '    NUITKA_CANNOT_GET_HERE("return must be present");\n\n    function_exception_exit:\n'
    )
    emit(values["function_cleanup"])
    emit("\n    CHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\n    RESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n    return NULL;\n")


def _emit_004_template_asyncgen_no_exception_exit(emit, values):
    emit('NUITKA_CANNOT_GET_HERE("return must be present");\n\n')
    emit(values["function_cleanup"])
    emit("\nreturn NULL;\n")


def _emit_004_template_asyncgen_no_exception_exit_readable(emit, values):
    emit('    NUITKA_CANNOT_GET_HERE("return must be present");\n\n')
    emit(values["function_cleanup"])
    emit("\n    return NULL;\n")


def _emit_005_template_asyncgen_return_exit(emit, values):
    emit("function_return_exit:;\n\nreturn NULL;\n")


def _emit_005_template_asyncgen_return_exit_readable(emit, values):
    emit("    function_return_exit:;\n\n    return NULL;\n")


def _emit_006_template_constants_reading(emit, values):
    emit(
        '\n#include "nuitka/prelude.h"\n#include <structseq.h>\n\n#include "build_definitions.h"\n#include "nuitka/constants_blob.h"\n\n\nPyObject *global_constants['
    )
    emit(str(values["global_constants_count"]))
    emit(
        "] = {0};\n\n\n\n\nPyObject *Nuitka_sentinel_value = NULL;\n\nPyObject *Nuitka_dunder_compiled_value = NULL;\n\n\n#if _NUITKA_STANDALONE_MODE\nextern PyObject *getStandaloneSysExecutablePath(PyObject *basename);\n\nNUITKA_MAY_BE_UNUSED static PyObject *STRIP_DIRNAME(PyObject *path) {\n#if PYTHON_VERSION < 0x300\nchar const *path_cstr = PyString_AS_STRING(path);\n\n#ifdef _WIN32\nchar const *last_sep = strrchr(path_cstr, '\\\\');\n#else\nchar const *last_sep = strrchr(path_cstr, '/');\n#endif\nif (unlikely(last_sep == NULL)) {\nPy_INCREF(path);\nreturn path;\n}\n\nreturn PyString_FromStringAndSize(path_cstr, last_sep - path_cstr);\n#else\n#ifdef _WIN32\nPy_ssize_t dot_index = PyUnicode_Find(path, const_str_backslash, 0, PyUnicode_GetLength(path), -1);\n#else\nPy_ssize_t dot_index = PyUnicode_Find(path, const_str_slash, 0, PyUnicode_GetLength(path), -1);\n#endif\nif (likely(dot_index != -1)) {\nreturn PyUnicode_Substring(path, 0, dot_index);\n} else {\nPy_INCREF(path);\nreturn path;\n}\n#endif\n}\n#endif\n\nextern void setDistributionsMetadata(PyThreadState *tstate, PyObject *metadata_items);\n\n\nPyObject *Py_SysVersionInfo = NULL;\n\nNUITKA_DECLARE_CONSTANT_BLOB(\n"
    )
    emit(values["global_constants_blob_symbol_name"])
    emit(",\n")
    emit(values["global_constants_blob_symbol_name"])
    emit(
        ',\nconst\n);\n\n#if _NUITKA_MODULE_MODE\nstatic void _createGlobalConstants(PyThreadState *tstate, PyObject *real_module_name) {\n#else\nstatic void _createGlobalConstants(PyThreadState *tstate) {\n#endif\n\nPy_SysVersionInfo = Nuitka_SysGetObject("version_info");\n\n\n#if '
    )
    emit(str(values["use_direct_constant_blobs"]))
    emit("\nLOAD_DIRECT_CONSTANTS_BLOB(tstate, &global_constants[0], ")
    emit(values["global_constants_blob_symbol_name"])
    emit(
        ');\n#else\nloadConstantsBlob(tstate, &global_constants[0], "");\n#endif\n\n#if _NUITKA_EXE_MODE || _NUITKA_DLL_MODE\n\n\nNuitka_SysSetObject(\n"executable",\n#if !_NUITKA_STANDALONE_MODE\n'
    )
    emit(values["sys_executable"])
    emit("\n#else\ngetStandaloneSysExecutablePath(")
    emit(values["sys_executable"])
    emit(
        ')\n#endif\n);\n\n#if !_NUITKA_STANDALONE_MODE\n\nNuitka_SysSetObject(\n"prefix",\n'
    )
    emit(values["sys_prefix"])
    emit('\n);\n\n\nNuitka_SysSetObject(\n"exec_prefix",\n')
    emit(values["sys_exec_prefix"])
    emit(
        '\n);\n\n\n#if PYTHON_VERSION >= 0x300\n\nNuitka_SysSetObject(\n"base_prefix",\n'
    )
    emit(values["sys_base_prefix"])
    emit('\n);\n\n\nNuitka_SysSetObject(\n"base_exec_prefix",\n')
    emit(values["sys_base_exec_prefix"])
    emit(
        '\n);\n\n#endif\n#endif\n#endif\n\nstatic PyTypeObject Nuitka_VersionInfoType;\n\n\n\nstatic PyStructSequence_Field Nuitka_VersionInfoFields[] = {\n{(char *)"major", (char *)"Major release number"},\n{(char *)"minor", (char *)"Minor release number"},\n{(char *)"micro", (char *)"Micro release number"},\n{(char *)"releaselevel", (char *)"\'alpha\', \'beta\', \'candidate\', or \'release\'"},\n{(char *)"containing_dir", (char *)"directory of the containing binary"},\n{(char *)"standalone", (char *)"boolean indicating standalone mode usage"},\n{(char *)"onefile", (char *)"boolean indicating onefile mode usage"},\n{(char *)"macos_bundle_mode", (char *)"boolean indicating macOS app bundle mode usage"},\n{(char *)"no_asserts", (char *)"boolean indicating --python-flag=no_asserts usage"},\n{(char *)"no_docstrings", (char *)"boolean indicating --python-flag=no_docstrings usage"},\n{(char *)"no_annotations", (char *)"boolean indicating --python-flag=no_annotations usage"},\n{(char *)"module", (char *)"boolean indicating --module usage"},\n{(char *)"main", (char *)"name of main module at runtime"},\n{(char *)"original_argv0", (char *)"original argv[0] as received by the onefile binary, None otherwise"},\n{(char *)"extension_filename", (char *)"loaded extension filename in module/package mode, None otherwise"},\n{0}\n};\n\nstatic PyStructSequence_Desc Nuitka_VersionInfoDesc = {\n(char *)"__nuitka_version__",                                       \n(char *)"__compiled__\\\\n\\\\nVersion information as a named tuple.",  \nNuitka_VersionInfoFields,                                           \nsizeof(Nuitka_VersionInfoFields) / sizeof(PyStructSequence_Field)-1 \n};\n\nPyStructSequence_InitType(&Nuitka_VersionInfoType, &Nuitka_VersionInfoDesc);\n\nNuitka_dunder_compiled_value = PyStructSequence_New(&Nuitka_VersionInfoType);\nassert(Nuitka_dunder_compiled_value != NULL);\n\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 0, Nuitka_PyInt_FromLong('
    )
    emit(values["nuitka_version_major"])
    emit(
        "));\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 1, Nuitka_PyInt_FromLong("
    )
    emit(values["nuitka_version_minor"])
    emit(
        "));\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 2, Nuitka_PyInt_FromLong("
    )
    emit(values["nuitka_version_micro"])
    emit(
        '));\n\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 3, Nuitka_String_FromString("'
    )
    emit(values["nuitka_version_level"])
    emit(
        '"));\n\nPyObject *containing_directory = getContainingDirectoryObject(false);\n#if _NUITKA_STANDALONE_MODE\n#if !_NUITKA_ONEFILE_MODE\ncontaining_directory = STRIP_DIRNAME(containing_directory);\n#endif\n\n#if _NUITKA_MACOS_BUNDLE_MODE\ncontaining_directory = STRIP_DIRNAME(containing_directory);\ncontaining_directory = STRIP_DIRNAME(containing_directory);\n#endif\n#endif\n\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 4, containing_directory);\n\n#if _NUITKA_STANDALONE_MODE\nPyObject *is_standalone_mode = Py_True;\n#else\nPyObject *is_standalone_mode = Py_False;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 5, is_standalone_mode);\n#ifdef _NUITKA_ONEFILE_MODE\nPyObject *is_onefile_mode = Py_True;\n#else\nPyObject *is_onefile_mode = Py_False;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 6, is_onefile_mode);\n\n#if _NUITKA_MACOS_BUNDLE_MODE\nPyObject *is_macos_bundle_mode = Py_True;\n#else\nPyObject *is_macos_bundle_mode = Py_False;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 7, is_macos_bundle_mode);\n\n#if _NUITKA_NO_ASSERTS == 1\nPyObject *is_no_asserts = Py_True;\n#else\nPyObject *is_no_asserts = Py_False;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 8, is_no_asserts);\n\n#if _NUITKA_NO_DOCSTRINGS == 1\nPyObject *is_no_docstrings = Py_True;\n#else\nPyObject *is_no_docstrings = Py_False;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 9, is_no_docstrings);\n\n#if _NUITKA_NO_ANNOTATIONS == 1\nPyObject *is_no_annotations = Py_True;\n#else\nPyObject *is_no_annotations = Py_False;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 10, is_no_annotations);\n\n#if _NUITKA_MODULE_MODE\nPyObject *is_module_mode = Py_True;\n#else\nPyObject *is_module_mode = Py_False;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 11, is_module_mode);\n\n#if _NUITKA_MODULE_MODE\nPyObject *main_name = real_module_name;\nPy_INCREF(real_module_name);\n#else\nPyObject *main_name = Nuitka_String_FromString("__main__");\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 12, main_name);\n\n#if _NUITKA_EXE_MODE || _NUITKA_DLL_MODE\nPyObject *original_argv0 = getOriginalArgv0Object();\n#else\nPyObject *original_argv0 = Py_None;\n# endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 13, original_argv0);\n\n#if _NUITKA_MODULE_MODE\nPyObject *extension_filename = getDllFilenameObject();\n#else\nPyObject *extension_filename = Py_None;\n#endif\nPyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 14, extension_filename);\n\n// Prevent users from creating the Nuitka version type object.\nNuitka_VersionInfoType.tp_init = NULL;\nNuitka_VersionInfoType.tp_new = NULL;\n\n// Register included meta data.\nsetDistributionsMetadata(tstate, '
    )
    emit(values["metadata_values"])
    emit(
        ');\n}\n\n\n\n\n#ifndef __NUITKA_NO_ASSERT__\nvoid checkGlobalConstants(void) {\n\n\n}\n#endif\n\n#if _NUITKA_MODULE_MODE\nvoid createGlobalConstants(PyThreadState *tstate, PyObject *real_module_name) {\n#else\nvoid createGlobalConstants(PyThreadState *tstate) {\n#endif\nif (Nuitka_sentinel_value == NULL) {\n#if PYTHON_VERSION < 0x300\nNuitka_sentinel_value = PyCObject_FromVoidPtr(NULL, NULL);\n#else\n\nNuitka_sentinel_value = PyCapsule_New((void *)27, "sentinel", NULL);\n#endif\nassert(Nuitka_sentinel_value);\n\nPy_SET_REFCNT_IMMORTAL(Nuitka_sentinel_value);\n\n#if _NUITKA_MODULE_MODE\n_createGlobalConstants(tstate, real_module_name);\n#else\n_createGlobalConstants(tstate);\n#endif\n}\n}\n'
    )


def _emit_006_template_constants_reading_readable(emit, values):
    emit(
        '\n#include "nuitka/prelude.h"\n#include <structseq.h>\n\n#include "build_definitions.h"\n#include "nuitka/constants_blob.h"\n\n// Global constants storage\nPyObject *global_constants['
    )
    emit(str(values["global_constants_count"]))
    emit(
        "] = {0};\n\n// Sentinel PyObject to be used for all our call iterator endings. It will\n// become a PyCObject pointing to NULL. It's address is unique, and that's\n// enough for us to use it as sentinel value.\nPyObject *Nuitka_sentinel_value = NULL;\n\nPyObject *Nuitka_dunder_compiled_value = NULL;\n\n\n#if _NUITKA_STANDALONE_MODE\nextern PyObject *getStandaloneSysExecutablePath(PyObject *basename);\n\nNUITKA_MAY_BE_UNUSED static PyObject *STRIP_DIRNAME(PyObject *path) {\n#if PYTHON_VERSION < 0x300\n    char const *path_cstr = PyString_AS_STRING(path);\n\n#ifdef _WIN32\n    char const *last_sep = strrchr(path_cstr, '\\\\');\n#else\n    char const *last_sep = strrchr(path_cstr, '/');\n#endif\n    if (unlikely(last_sep == NULL)) {\n        Py_INCREF(path);\n        return path;\n    }\n\n    return PyString_FromStringAndSize(path_cstr, last_sep - path_cstr);\n#else\n#ifdef _WIN32\n    Py_ssize_t dot_index = PyUnicode_Find(path, const_str_backslash, 0, PyUnicode_GetLength(path), -1);\n#else\n    Py_ssize_t dot_index = PyUnicode_Find(path, const_str_slash, 0, PyUnicode_GetLength(path), -1);\n#endif\n    if (likely(dot_index != -1)) {\n        return PyUnicode_Substring(path, 0, dot_index);\n    } else {\n        Py_INCREF(path);\n        return path;\n    }\n#endif\n}\n#endif\n\nextern void setDistributionsMetadata(PyThreadState *tstate, PyObject *metadata_items);\n\n// We provide the sys.version info shortcut as a global value here for ease of use.\nPyObject *Py_SysVersionInfo = NULL;\n\nNUITKA_DECLARE_CONSTANT_BLOB(\n    "
    )
    emit(values["global_constants_blob_symbol_name"])
    emit(",\n    ")
    emit(values["global_constants_blob_symbol_name"])
    emit(
        ',\n    const\n);\n\n#if _NUITKA_MODULE_MODE\nstatic void _createGlobalConstants(PyThreadState *tstate, PyObject *real_module_name) {\n#else\nstatic void _createGlobalConstants(PyThreadState *tstate) {\n#endif\n    // We provide the sys.version info shortcut as a global value here for ease of use.\n    Py_SysVersionInfo = Nuitka_SysGetObject("version_info");\n\n    // The empty name means global.\n#if '
    )
    emit(str(values["use_direct_constant_blobs"]))
    emit("\n    LOAD_DIRECT_CONSTANTS_BLOB(tstate, &global_constants[0], ")
    emit(values["global_constants_blob_symbol_name"])
    emit(
        ');\n#else\n    loadConstantsBlob(tstate, &global_constants[0], "");\n#endif\n\n#if _NUITKA_EXE_MODE || _NUITKA_DLL_MODE\n    /* Set the "sys.executable" path to the original CPython executable or point to inside the\n       distribution for standalone. */\n    Nuitka_SysSetObject(\n        "executable",\n#if !_NUITKA_STANDALONE_MODE\n        '
    )
    emit(values["sys_executable"])
    emit("\n#else\n        getStandaloneSysExecutablePath(")
    emit(values["sys_executable"])
    emit(
        ')\n#endif\n    );\n\n#if !_NUITKA_STANDALONE_MODE\n    /* Set the "sys.prefix" path to the original one. */\n    Nuitka_SysSetObject(\n        "prefix",\n        '
    )
    emit(values["sys_prefix"])
    emit(
        '\n    );\n\n    /* Set the "sys.prefix" path to the original one. */\n    Nuitka_SysSetObject(\n        "exec_prefix",\n        '
    )
    emit(values["sys_exec_prefix"])
    emit(
        '\n    );\n\n\n#if PYTHON_VERSION >= 0x300\n    /* Set the "sys.base_prefix" path to the original one. */\n    Nuitka_SysSetObject(\n        "base_prefix",\n        '
    )
    emit(values["sys_base_prefix"])
    emit(
        '\n    );\n\n    /* Set the "sys.exec_base_prefix" path to the original one. */\n    Nuitka_SysSetObject(\n        "base_exec_prefix",\n        '
    )
    emit(values["sys_base_exec_prefix"])
    emit(
        '\n    );\n\n#endif\n#endif\n#endif\n\n    static PyTypeObject Nuitka_VersionInfoType;\n\n    // Same fields as "sys.version_info" except no serial number\n    // spell-checker: ignore releaselevel\n    static PyStructSequence_Field Nuitka_VersionInfoFields[] = {\n        {(char *)"major", (char *)"Major release number"},\n        {(char *)"minor", (char *)"Minor release number"},\n        {(char *)"micro", (char *)"Micro release number"},\n        {(char *)"releaselevel", (char *)"\'alpha\', \'beta\', \'candidate\', or \'release\'"},\n        {(char *)"containing_dir", (char *)"directory of the containing binary"},\n        {(char *)"standalone", (char *)"boolean indicating standalone mode usage"},\n        {(char *)"onefile", (char *)"boolean indicating onefile mode usage"},\n        {(char *)"macos_bundle_mode", (char *)"boolean indicating macOS app bundle mode usage"},\n        {(char *)"no_asserts", (char *)"boolean indicating --python-flag=no_asserts usage"},\n        {(char *)"no_docstrings", (char *)"boolean indicating --python-flag=no_docstrings usage"},\n        {(char *)"no_annotations", (char *)"boolean indicating --python-flag=no_annotations usage"},\n        {(char *)"module", (char *)"boolean indicating --module usage"},\n        {(char *)"main", (char *)"name of main module at runtime"},\n        {(char *)"original_argv0", (char *)"original argv[0] as received by the onefile binary, None otherwise"},\n        {(char *)"extension_filename", (char *)"loaded extension filename in module/package mode, None otherwise"},\n        {0}\n    };\n\n    static PyStructSequence_Desc Nuitka_VersionInfoDesc = {\n        (char *)"__nuitka_version__",                                       /* name */\n        (char *)"__compiled__\\\\n\\\\nVersion information as a named tuple.",  /* doc */\n        Nuitka_VersionInfoFields,                                           /* fields */\n        sizeof(Nuitka_VersionInfoFields) / sizeof(PyStructSequence_Field)-1 /* count */\n    };\n\n    PyStructSequence_InitType(&Nuitka_VersionInfoType, &Nuitka_VersionInfoDesc);\n\n    Nuitka_dunder_compiled_value = PyStructSequence_New(&Nuitka_VersionInfoType);\n    assert(Nuitka_dunder_compiled_value != NULL);\n\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 0, Nuitka_PyInt_FromLong('
    )
    emit(values["nuitka_version_major"])
    emit(
        "));\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 1, Nuitka_PyInt_FromLong("
    )
    emit(values["nuitka_version_minor"])
    emit(
        "));\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 2, Nuitka_PyInt_FromLong("
    )
    emit(values["nuitka_version_micro"])
    emit(
        '));\n\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 3, Nuitka_String_FromString("'
    )
    emit(values["nuitka_version_level"])
    emit(
        '"));\n\n    PyObject *containing_directory = getContainingDirectoryObject(false);\n#if _NUITKA_STANDALONE_MODE\n#if !_NUITKA_ONEFILE_MODE\n    containing_directory = STRIP_DIRNAME(containing_directory);\n#endif\n\n#if _NUITKA_MACOS_BUNDLE_MODE\n    containing_directory = STRIP_DIRNAME(containing_directory);\n    containing_directory = STRIP_DIRNAME(containing_directory);\n#endif\n#endif\n\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 4, containing_directory);\n\n#if _NUITKA_STANDALONE_MODE\n    PyObject *is_standalone_mode = Py_True;\n#else\n    PyObject *is_standalone_mode = Py_False;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 5, is_standalone_mode);\n#ifdef _NUITKA_ONEFILE_MODE\n    PyObject *is_onefile_mode = Py_True;\n#else\n    PyObject *is_onefile_mode = Py_False;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 6, is_onefile_mode);\n\n#if _NUITKA_MACOS_BUNDLE_MODE\n    PyObject *is_macos_bundle_mode = Py_True;\n#else\n    PyObject *is_macos_bundle_mode = Py_False;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 7, is_macos_bundle_mode);\n\n#if _NUITKA_NO_ASSERTS == 1\n    PyObject *is_no_asserts = Py_True;\n#else\n    PyObject *is_no_asserts = Py_False;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 8, is_no_asserts);\n\n#if _NUITKA_NO_DOCSTRINGS == 1\n    PyObject *is_no_docstrings = Py_True;\n#else\n    PyObject *is_no_docstrings = Py_False;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 9, is_no_docstrings);\n\n#if _NUITKA_NO_ANNOTATIONS == 1\n    PyObject *is_no_annotations = Py_True;\n#else\n    PyObject *is_no_annotations = Py_False;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 10, is_no_annotations);\n\n#if _NUITKA_MODULE_MODE\n    PyObject *is_module_mode = Py_True;\n#else\n    PyObject *is_module_mode = Py_False;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 11, is_module_mode);\n\n#if _NUITKA_MODULE_MODE\n    PyObject *main_name = real_module_name;\n    Py_INCREF(real_module_name);\n#else\n    PyObject *main_name = Nuitka_String_FromString("__main__");\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 12, main_name);\n\n#if _NUITKA_EXE_MODE || _NUITKA_DLL_MODE\n    PyObject *original_argv0 = getOriginalArgv0Object();\n#else\n    PyObject *original_argv0 = Py_None;\n# endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 13, original_argv0);\n\n#if _NUITKA_MODULE_MODE\n    PyObject *extension_filename = getDllFilenameObject();\n#else\n    PyObject *extension_filename = Py_None;\n#endif\n    PyStructSequence_SET_ITEM(Nuitka_dunder_compiled_value, 14, extension_filename);\n\n    // Prevent users from creating the Nuitka version type object.\n    Nuitka_VersionInfoType.tp_init = NULL;\n    Nuitka_VersionInfoType.tp_new = NULL;\n\n    // Register included meta data.\n    setDistributionsMetadata(tstate, '
    )
    emit(values["metadata_values"])
    emit(
        ');\n}\n\n// In debug mode we can check that the constants were not tampered with in any\n// given moment. We typically do it at program exit, but we can add extra calls\n// for sanity.\n#ifndef __NUITKA_NO_ASSERT__\nvoid checkGlobalConstants(void) {\n// TODO: Ask constant code to check values.\n\n}\n#endif\n\n#if _NUITKA_MODULE_MODE\nvoid createGlobalConstants(PyThreadState *tstate, PyObject *real_module_name) {\n#else\nvoid createGlobalConstants(PyThreadState *tstate) {\n#endif\n    if (Nuitka_sentinel_value == NULL) {\n#if PYTHON_VERSION < 0x300\n        Nuitka_sentinel_value = PyCObject_FromVoidPtr(NULL, NULL);\n#else\n        // The NULL value is not allowed for a capsule, so use something else.\n        Nuitka_sentinel_value = PyCapsule_New((void *)27, "sentinel", NULL);\n#endif\n        assert(Nuitka_sentinel_value);\n\n        Py_SET_REFCNT_IMMORTAL(Nuitka_sentinel_value);\n\n#if _NUITKA_MODULE_MODE\n        _createGlobalConstants(tstate, real_module_name);\n#else\n        _createGlobalConstants(tstate);\n#endif\n    }\n}\n'
    )


def _emit_007_template_coroutine_object_maker(emit, values):
    emit("static PyObject *")
    emit(values["coroutine_maker_identifier"])
    emit("(")
    emit(values["coroutine_creation_args"])
    emit(");\n")


def _emit_007_template_coroutine_object_maker_readable(emit, values):
    emit("static PyObject *")
    emit(values["coroutine_maker_identifier"])
    emit("(")
    emit(values["coroutine_creation_args"])
    emit(");\n")


def _emit_008_template_coroutine_object_body(emit, values):
    emit("\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nstruct ")
    emit(values["function_identifier"])
    emit("_locals {\n")
    emit(values["function_local_types"])
    emit("\n};\n#endif\n\nstatic PyObject *")
    emit(values["function_identifier"])
    emit(
        "_context(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine, PyObject *yield_return_value) {\nCHECK_OBJECT(coroutine);\nassert(Nuitka_Coroutine_Check((PyObject *)coroutine));\nCHECK_OBJECT_X(yield_return_value);\n\n#if "
    )
    emit(values["has_heap_declaration"])
    emit("\n\n")
    emit(values["heap_declaration"])
    emit("\n#endif\n\n\n")
    emit(values["function_dispatch"])
    emit("\n\n\n")
    emit(values["function_var_inits"])
    emit("\n\n\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["coroutine_exit"])
    emit("\n}\n\nstatic PyObject *")
    emit(values["coroutine_maker_identifier"])
    emit("(")
    emit(values["coroutine_creation_args"])
    emit(") {\nreturn Nuitka_Coroutine_New(\ntstate,\n")
    emit(values["function_identifier"])
    emit("_context,\n")
    emit(values["coroutine_module"])
    emit(",\n")
    emit(values["coroutine_name_obj"])
    emit(",\n")
    emit(values["coroutine_qualname_obj"])
    emit(",\n")
    emit(values["code_identifier"])
    emit(",\n")
    emit(values["closure_name"])
    emit(",\n")
    emit(str(values["closure_count"]))
    emit(",\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nsizeof(struct ")
    emit(values["function_identifier"])
    emit("_locals)\n#else\n0\n#endif\n);\n}\n")


def _emit_008_template_coroutine_object_body_readable(emit, values):
    emit("\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nstruct ")
    emit(values["function_identifier"])
    emit("_locals {\n")
    emit(values["function_local_types"])
    emit("\n};\n#endif\n\nstatic PyObject *")
    emit(values["function_identifier"])
    emit(
        "_context(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine, PyObject *yield_return_value) {\n    CHECK_OBJECT(coroutine);\n    assert(Nuitka_Coroutine_Check((PyObject *)coroutine));\n    CHECK_OBJECT_X(yield_return_value);\n\n#if "
    )
    emit(values["has_heap_declaration"])
    emit("\n    // Heap access.\n")
    emit(values["heap_declaration"])
    emit("\n#endif\n\n    // Dispatch to yield based on return label index:\n")
    emit(values["function_dispatch"])
    emit("\n\n    // Local variable initialization\n")
    emit(values["function_var_inits"])
    emit("\n\n    // Actual coroutine body.\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["coroutine_exit"])
    emit("\n}\n\nstatic PyObject *")
    emit(values["coroutine_maker_identifier"])
    emit("(")
    emit(values["coroutine_creation_args"])
    emit(") {\n    return Nuitka_Coroutine_New(\n        tstate,\n        ")
    emit(values["function_identifier"])
    emit("_context,\n        ")
    emit(values["coroutine_module"])
    emit(",\n        ")
    emit(values["coroutine_name_obj"])
    emit(",\n        ")
    emit(values["coroutine_qualname_obj"])
    emit(",\n        ")
    emit(values["code_identifier"])
    emit(",\n        ")
    emit(values["closure_name"])
    emit(",\n        ")
    emit(str(values["closure_count"]))
    emit(",\n#if ")
    emit(values["has_heap_declaration"])
    emit("\n        sizeof(struct ")
    emit(values["function_identifier"])
    emit("_locals)\n#else\n        0\n#endif\n    );\n}\n")


def _emit_009_template_make_coroutine(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["coroutine_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_009_template_make_coroutine_readable(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["coroutine_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_010_template_coroutine_exception_exit(emit, values):
    emit(
        'NUITKA_CANNOT_GET_HERE("Return statement must be present");\n\nfunction_exception_exit:\n'
    )
    emit(values["function_cleanup"])
    emit("\nCHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\nRESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\nreturn NULL;\n")


def _emit_010_template_coroutine_exception_exit_readable(emit, values):
    emit(
        '    NUITKA_CANNOT_GET_HERE("Return statement must be present");\n\n    function_exception_exit:\n'
    )
    emit(values["function_cleanup"])
    emit("\n    CHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\n    RESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n    return NULL;\n")


def _emit_011_template_coroutine_no_exception_exit(emit, values):
    emit('NUITKA_CANNOT_GET_HERE("Return statement must be present");\n\n')
    emit(values["function_cleanup"])
    emit("\nreturn NULL;\n")


def _emit_011_template_coroutine_no_exception_exit_readable(emit, values):
    emit('    NUITKA_CANNOT_GET_HERE("Return statement must be present");\n\n')
    emit(values["function_cleanup"])
    emit("\n    return NULL;\n")


def _emit_012_template_coroutine_return_exit(emit, values):
    emit("function_return_exit:;\n\ncoroutine->m_returned = ")
    emit(values["return_value"])
    emit(";\n\nreturn NULL;\n")


def _emit_012_template_coroutine_return_exit_readable(emit, values):
    emit("    function_return_exit:;\n\n    coroutine->m_returned = ")
    emit(values["return_value"])
    emit(";\n\n    return NULL;\n")


def _emit_013_template_publish_exception_to_handler(emit, values):
    emit("{\nPyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(&")
    emit(values["keeper_exception_state_name"])
    emit(");\nif (exception_tb == NULL) {\nexception_tb = ")
    emit(values["tb_making"])
    emit(";\nSET_EXCEPTION_STATE_TRACEBACK(&")
    emit(values["keeper_exception_state_name"])
    emit(", exception_tb);\n} else if (")
    emit(values["keeper_lineno"])
    emit(" != 0) {\nexception_tb = ADD_TRACEBACK(exception_tb, ")
    emit(values["frame_identifier"])
    emit(", ")
    emit(values["keeper_lineno"])
    emit(");\nSET_EXCEPTION_STATE_TRACEBACK(&")
    emit(values["keeper_exception_state_name"])
    emit(", exception_tb);\n}\n}\n")


def _emit_013_template_publish_exception_to_handler_readable(emit, values):
    emit("{\n    PyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(&")
    emit(values["keeper_exception_state_name"])
    emit(");\n    if (exception_tb == NULL) {\n        exception_tb = ")
    emit(values["tb_making"])
    emit(";\n        SET_EXCEPTION_STATE_TRACEBACK(&")
    emit(values["keeper_exception_state_name"])
    emit(", exception_tb);\n    } else if (")
    emit(values["keeper_lineno"])
    emit(" != 0) {\n        exception_tb = ADD_TRACEBACK(exception_tb, ")
    emit(values["frame_identifier"])
    emit(", ")
    emit(values["keeper_lineno"])
    emit(");\n        SET_EXCEPTION_STATE_TRACEBACK(&")
    emit(values["keeper_exception_state_name"])
    emit(", exception_tb);\n    }\n}\n")


def _emit_014_template_error_catch_fetched_exception(emit, values):
    emit("if (")
    emit(values["condition"])
    emit(") {\nassert(HAS_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit("));\n\n")
    emit(values["release_temps"])
    emit("\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\ngoto ")
    emit(values["exception_exit"])
    emit(";\n}")


def _emit_014_template_error_catch_fetched_exception_readable(emit, values):
    emit("if (")
    emit(values["condition"])
    emit(") {\n    assert(HAS_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit("));\n\n")
    emit(values["release_temps"])
    emit("\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\n    goto ")
    emit(values["exception_exit"])
    emit(";\n}")


def _emit_015_template_error_catch_exception(emit, values):
    emit("if (")
    emit(values["condition"])
    emit(
        ") {\nassert(HAS_ERROR_OCCURRED(tstate));\n\nFETCH_ERROR_OCCURRED_STATE(tstate, &"
    )
    emit(values["exception_state_name"])
    emit(");\n")
    emit(values["release_temps"])
    emit("\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\ngoto ")
    emit(values["exception_exit"])
    emit(";\n}")


def _emit_015_template_error_catch_exception_readable(emit, values):
    emit("if (")
    emit(values["condition"])
    emit(
        ") {\n    assert(HAS_ERROR_OCCURRED(tstate));\n\n    FETCH_ERROR_OCCURRED_STATE(tstate, &"
    )
    emit(values["exception_state_name"])
    emit(");\n")
    emit(values["release_temps"])
    emit("\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\n    goto ")
    emit(values["exception_exit"])
    emit(";\n}")


def _emit_016_template_error_format_string_exception(emit, values):
    emit("if (")
    emit(values["condition"])
    emit(") {\n")
    emit(values["release_temps"])
    emit("\n")
    emit(values["set_exception"])
    emit("\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\ngoto ")
    emit(values["exception_exit"])
    emit(";\n}\n")


def _emit_016_template_error_format_string_exception_readable(emit, values):
    emit("if (")
    emit(values["condition"])
    emit(") {\n")
    emit(values["release_temps"])
    emit("\n")
    emit(values["set_exception"])
    emit("\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\n    goto ")
    emit(values["exception_exit"])
    emit(";\n}\n")


def _emit_017_template_error_format_name_error_exception(emit, values):
    emit("if (unlikely(")
    emit(values["condition"])
    emit(")) {\n")
    emit(values["release_temps"])
    emit("\n")
    emit(values["raise_name_error_helper"])
    emit("(tstate, &")
    emit(values["exception_state_name"])
    emit(", ")
    emit(values["variable_name"])
    emit(");\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\ngoto ")
    emit(values["exception_exit"])
    emit(";\n}\n")


def _emit_017_template_error_format_name_error_exception_readable(emit, values):
    emit("if (unlikely(")
    emit(values["condition"])
    emit(")) {\n")
    emit(values["release_temps"])
    emit("\n")
    emit(values["raise_name_error_helper"])
    emit("(tstate, &")
    emit(values["exception_state_name"])
    emit(", ")
    emit(values["variable_name"])
    emit(");\n\n")
    emit(values["line_number_code"])
    emit("\n")
    emit(values["var_description_code"])
    emit("\n    goto ")
    emit(values["exception_exit"])
    emit(";\n}\n")


def _emit_018_template_frame_attach_locals(emit, values):
    emit("Nuitka_Frame_AttachLocals(\n")
    emit(values["frame_identifier"])
    emit(",\n")
    emit(values["type_description"])
    emit(values["frame_variable_refs"])
    emit("\n);\n")


def _emit_018_template_frame_attach_locals_readable(emit, values):
    emit("Nuitka_Frame_AttachLocals(\n    ")
    emit(values["frame_identifier"])
    emit(",\n    ")
    emit(values["type_description"])
    emit(values["frame_variable_refs"])
    emit("\n);\n")


def _emit_019_template_frame_guard_generator_return_handler(emit, values):
    emit(values["frame_return_exit"])
    emit(
        ":;\n\n#if PYTHON_VERSION >= 0x300\n#if PYTHON_VERSION < 0x3b0\nPy_CLEAR(EXC_TYPE_F("
    )
    emit(values["context_identifier"])
    emit("));\n#endif\nPy_CLEAR(EXC_VALUE_F(")
    emit(values["context_identifier"])
    emit("));\n#if PYTHON_VERSION < 0x3b0\nPy_CLEAR(EXC_TRACEBACK_F(")
    emit(values["context_identifier"])
    emit("));\n#endif\n#endif\n\ngoto ")
    emit(values["return_exit"])
    emit(";\n")


def _emit_019_template_frame_guard_generator_return_handler_readable(emit, values):
    emit(values["frame_return_exit"])
    emit(
        ":;\n\n#if PYTHON_VERSION >= 0x300\n#if PYTHON_VERSION < 0x3b0\nPy_CLEAR(EXC_TYPE_F("
    )
    emit(values["context_identifier"])
    emit("));\n#endif\nPy_CLEAR(EXC_VALUE_F(")
    emit(values["context_identifier"])
    emit("));\n#if PYTHON_VERSION < 0x3b0\nPy_CLEAR(EXC_TRACEBACK_F(")
    emit(values["context_identifier"])
    emit("));\n#endif\n#endif\n\ngoto ")
    emit(values["return_exit"])
    emit(";\n")


def _emit_020_template_function_make_declaration(emit, values):
    emit("static PyObject *MAKE_FUNCTION_")
    emit(values["function_identifier"])
    emit("(")
    emit(values["function_creation_args"])
    emit(");\n")


def _emit_020_template_function_make_declaration_readable(emit, values):
    emit("static PyObject *MAKE_FUNCTION_")
    emit(values["function_identifier"])
    emit("(")
    emit(values["function_creation_args"])
    emit(");\n")


def _emit_021_template_function_direct_declaration(emit, values):
    emit(values["file_scope"])
    emit(" PyObject *impl_")
    emit(values["function_identifier"])
    emit("(PyThreadState *tstate, ")
    emit(values["direct_call_arg_spec"])
    emit(");\n")


def _emit_021_template_function_direct_declaration_readable(emit, values):
    emit(values["file_scope"])
    emit(" PyObject *impl_")
    emit(values["function_identifier"])
    emit("(PyThreadState *tstate, ")
    emit(values["direct_call_arg_spec"])
    emit(");\n")


def _emit_022_template_maker_function_body(emit, values):
    emit("\nstatic PyObject *")
    emit(values["function_maker_identifier"])
    emit("(")
    emit(values["function_creation_args"])
    emit(") {\nstruct Nuitka_FunctionObject *result = Nuitka_Function_New(\n")
    emit(values["function_impl_identifier"])
    emit(",\n")
    emit(values["function_name_obj"])
    emit(",\n#if PYTHON_VERSION >= 0x300\n")
    emit(values["function_qualname_obj"])
    emit(",\n#endif\n")
    emit(values["code_identifier"])
    emit(",\n")
    emit(values["defaults"])
    emit(",\n#if PYTHON_VERSION >= 0x300\n")
    emit(values["kw_defaults"])
    emit(",\n")
    emit(values["annotations"])
    emit(",\n#endif\n")
    emit(values["module_identifier"])
    emit(",\n")
    emit(values["function_doc"])
    emit(",\n")
    emit(values["closure_name"])
    emit(",\n")
    emit(str(values["closure_count"]))
    emit("\n#if PYTHON_VERSION >= 0x300\n, ")
    emit(values["type_params"])
    emit("\n#endif\n);\n")
    emit(values["constant_return_code"])
    emit("\n\nreturn (PyObject *)result;\n}\n")


def _emit_022_template_maker_function_body_readable(emit, values):
    emit("\nstatic PyObject *")
    emit(values["function_maker_identifier"])
    emit("(")
    emit(values["function_creation_args"])
    emit(
        ") {\n    struct Nuitka_FunctionObject *result = Nuitka_Function_New(\n        "
    )
    emit(values["function_impl_identifier"])
    emit(",\n        ")
    emit(values["function_name_obj"])
    emit(",\n#if PYTHON_VERSION >= 0x300\n        ")
    emit(values["function_qualname_obj"])
    emit(",\n#endif\n        ")
    emit(values["code_identifier"])
    emit(",\n        ")
    emit(values["defaults"])
    emit(",\n#if PYTHON_VERSION >= 0x300\n        ")
    emit(values["kw_defaults"])
    emit(",\n        ")
    emit(values["annotations"])
    emit(",\n#endif\n        ")
    emit(values["module_identifier"])
    emit(",\n        ")
    emit(values["function_doc"])
    emit(",\n        ")
    emit(values["closure_name"])
    emit(",\n        ")
    emit(str(values["closure_count"]))
    emit("\n#if PYTHON_VERSION >= 0x300\n        , ")
    emit(values["type_params"])
    emit("\n#endif\n    );\n")
    emit(values["constant_return_code"])
    emit("\n\n    return (PyObject *)result;\n}\n")


def _emit_023_template_make_function(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["function_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_023_template_make_function_readable(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["function_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_024_template_function_body(emit, values):
    emit("static PyObject *impl_")
    emit(values["function_identifier"])
    emit("(PyThreadState *tstate, ")
    emit(values["parameter_objects_decl"])
    emit(
        ") {\n\n#ifndef __NUITKA_NO_ASSERT__\nNUITKA_MAY_BE_UNUSED bool had_error = HAS_ERROR_OCCURRED(tstate);\n#endif\n\n\n"
    )
    emit(values["function_locals"])
    emit("\n\n\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["function_exit"])
    emit("\n}\n")


def _emit_024_template_function_body_readable(emit, values):
    emit("static PyObject *impl_")
    emit(values["function_identifier"])
    emit("(PyThreadState *tstate, ")
    emit(values["parameter_objects_decl"])
    emit(
        ") {\n    // Preserve error status for checks\n#ifndef __NUITKA_NO_ASSERT__\n    NUITKA_MAY_BE_UNUSED bool had_error = HAS_ERROR_OCCURRED(tstate);\n#endif\n\n    // Local variable declarations.\n"
    )
    emit(values["function_locals"])
    emit("\n\n    // Actual function body.\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["function_exit"])
    emit("\n}\n")


def _emit_025_template_function_exception_exit(emit, values):
    emit("function_exception_exit:\n")
    emit(values["function_cleanup"])
    emit("\nCHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\nRESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n\nreturn NULL;\n")


def _emit_025_template_function_exception_exit_readable(emit, values):
    emit("function_exception_exit:\n")
    emit(values["function_cleanup"])
    emit("\n    CHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\n    RESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n\n    return NULL;\n")


def _emit_026_template_function_return_exit(emit, values):
    emit("\nfunction_return_exit:\n\n")
    emit(values["function_cleanup"])
    emit(
        "\n\n\n\nCHECK_OBJECT(tmp_return_value);\nassert(had_error || !HAS_ERROR_OCCURRED(tstate));\nreturn tmp_return_value;"
    )


def _emit_026_template_function_return_exit_readable(emit, values):
    emit("\nfunction_return_exit:\n   // Function cleanup code if any.\n")
    emit(values["function_cleanup"])
    emit(
        "\n\n   // Actual function exit with return value, making sure we did not make\n   // the error status worse despite non-NULL return.\n   CHECK_OBJECT(tmp_return_value);\n   assert(had_error || !HAS_ERROR_OCCURRED(tstate));\n   return tmp_return_value;"
    )


def _emit_027_template_generator_context_maker_decl(emit, values):
    emit("static PyObject *")
    emit(values["generator_maker_identifier"])
    emit("(")
    emit(values["generator_creation_args"])
    emit(");\n")


def _emit_027_template_generator_context_maker_decl_readable(emit, values):
    emit("static PyObject *")
    emit(values["generator_maker_identifier"])
    emit("(")
    emit(values["generator_creation_args"])
    emit(");\n")


def _emit_028_template_generator_context_body_template(emit, values):
    emit("\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nstruct ")
    emit(values["function_identifier"])
    emit("_locals {\n")
    emit(values["function_local_types"])
    emit("\n};\n#endif\n\nstatic PyObject *")
    emit(values["function_identifier"])
    emit(
        "_context(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator, PyObject *yield_return_value) {\nCHECK_OBJECT(generator);\nassert(Nuitka_Generator_Check((PyObject *)generator));\nCHECK_OBJECT_X(yield_return_value);\n\n#if "
    )
    emit(values["has_heap_declaration"])
    emit("\n\n")
    emit(values["heap_declaration"])
    emit("\n#endif\n\n\n")
    emit(values["function_dispatch"])
    emit("\n\n\n")
    emit(values["function_var_inits"])
    emit("\n\n\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["generator_exit"])
    emit("\n}\n\nstatic PyObject *")
    emit(values["generator_maker_identifier"])
    emit("(")
    emit(values["generator_creation_args"])
    emit(") {\nreturn Nuitka_Generator_New(\n")
    emit(values["function_identifier"])
    emit("_context,\n")
    emit(values["generator_module"])
    emit(",\n")
    emit(values["generator_name_obj"])
    emit(",\n#if PYTHON_VERSION >= 0x350\n")
    emit(values["generator_qualname_obj"])
    emit(",\n#endif\n")
    emit(values["code_identifier"])
    emit(",\n")
    emit(values["closure_name"])
    emit(",\n")
    emit(str(values["closure_count"]))
    emit(",\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nsizeof(struct ")
    emit(values["function_identifier"])
    emit("_locals)\n#else\n0\n#endif\n);\n}\n")


def _emit_028_template_generator_context_body_template_readable(emit, values):
    emit("\n#if ")
    emit(values["has_heap_declaration"])
    emit("\nstruct ")
    emit(values["function_identifier"])
    emit("_locals {\n")
    emit(values["function_local_types"])
    emit("\n};\n#endif\n\nstatic PyObject *")
    emit(values["function_identifier"])
    emit(
        "_context(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator, PyObject *yield_return_value) {\n    CHECK_OBJECT(generator);\n    assert(Nuitka_Generator_Check((PyObject *)generator));\n    CHECK_OBJECT_X(yield_return_value);\n\n#if "
    )
    emit(values["has_heap_declaration"])
    emit("\n    // Heap access.\n")
    emit(values["heap_declaration"])
    emit("\n#endif\n\n    // Dispatch to yield based on return label index:\n")
    emit(values["function_dispatch"])
    emit("\n\n    // Local variable initialization\n")
    emit(values["function_var_inits"])
    emit("\n\n    // Actual generator function body.\n")
    emit(values["function_body"])
    emit("\n\n")
    emit(values["generator_exit"])
    emit("\n}\n\nstatic PyObject *")
    emit(values["generator_maker_identifier"])
    emit("(")
    emit(values["generator_creation_args"])
    emit(") {\n    return Nuitka_Generator_New(\n        ")
    emit(values["function_identifier"])
    emit("_context,\n        ")
    emit(values["generator_module"])
    emit(",\n        ")
    emit(values["generator_name_obj"])
    emit(",\n#if PYTHON_VERSION >= 0x350\n        ")
    emit(values["generator_qualname_obj"])
    emit(",\n#endif\n        ")
    emit(values["code_identifier"])
    emit(",\n        ")
    emit(values["closure_name"])
    emit(",\n        ")
    emit(str(values["closure_count"]))
    emit(",\n#if ")
    emit(values["has_heap_declaration"])
    emit("\n        sizeof(struct ")
    emit(values["function_identifier"])
    emit("_locals)\n#else\n        0\n#endif\n    );\n}\n")


def _emit_029_template_make_generator(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["generator_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_029_template_make_generator_readable(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = ")
    emit(values["generator_maker_identifier"])
    emit("(")
    emit(values["args"])
    emit(");\n")


def _emit_030_template_make_empty_generator(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = Nuitka_Generator_NewEmpty(\n")
    emit(values["generator_module"])
    emit(",\n")
    emit(values["generator_name_obj"])
    emit(",\n#if PYTHON_VERSION >= 0x350\n")
    emit(values["generator_qualname_obj"])
    emit(",\n#endif\n")
    emit(values["code_identifier"])
    emit(",\n")
    emit(values["closure_name"])
    emit(",\n")
    emit(str(values["closure_count"]))
    emit("\n);\n")


def _emit_030_template_make_empty_generator_readable(emit, values):
    emit(values["closure_copy"])
    emit("\n")
    emit(values["to_name"])
    emit(" = Nuitka_Generator_NewEmpty(\n    ")
    emit(values["generator_module"])
    emit(",\n    ")
    emit(values["generator_name_obj"])
    emit(",\n#if PYTHON_VERSION >= 0x350\n    ")
    emit(values["generator_qualname_obj"])
    emit(",\n#endif\n    ")
    emit(values["code_identifier"])
    emit(",\n    ")
    emit(values["closure_name"])
    emit(",\n    ")
    emit(str(values["closure_count"]))
    emit("\n);\n")


def _emit_031_template_generator_exception_exit(emit, values):
    emit(values["function_cleanup"])
    emit("\nreturn NULL;\n\nfunction_exception_exit:\n")
    emit(values["function_cleanup"])
    emit("\nCHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\nRESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n\nreturn NULL;\n")


def _emit_031_template_generator_exception_exit_readable(emit, values):
    emit(values["function_cleanup"])
    emit("\n    return NULL;\n\n    function_exception_exit:\n")
    emit(values["function_cleanup"])
    emit("\n    CHECK_EXCEPTION_STATE(&")
    emit(values["exception_state_name"])
    emit(");\n    RESTORE_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n\n    return NULL;\n")


def _emit_032_template_generator_no_exception_exit(emit, values):
    emit("\n")
    emit(values["function_cleanup"])
    emit("\nreturn NULL;\n")


def _emit_032_template_generator_no_exception_exit_readable(emit, values):
    emit("    // Return statement need not be present.\n")
    emit(values["function_cleanup"])
    emit("\n    return NULL;\n")


def _emit_033_template_generator_return_exit(emit, values):
    emit(
        'NUITKA_CANNOT_GET_HERE("Generator must have exited already.");\nreturn NULL;\n\nfunction_return_exit:\n#if PYTHON_VERSION >= 0x300\ngenerator->m_returned = '
    )
    emit(values["return_value"])
    emit(";\n#endif\n\n")
    emit(values["function_cleanup"])
    emit("\nreturn NULL;\n")


def _emit_033_template_generator_return_exit_readable(emit, values):
    emit(
        '    NUITKA_CANNOT_GET_HERE("Generator must have exited already.");\n    return NULL;\n\n    function_return_exit:\n#if PYTHON_VERSION >= 0x300\n    generator->m_returned = '
    )
    emit(values["return_value"])
    emit(";\n#endif\n\n")
    emit(values["function_cleanup"])
    emit("\n    return NULL;\n")


def _emit_034_template_loop_break_next(emit, values):
    emit("if (")
    emit(values["to_name"])
    emit(" == NULL) {\nif (CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate)) {\n")
    emit(values["break_indicator_code"])
    emit("\ngoto ")
    emit(values["break_target"])
    emit(";\n} else {\n")
    emit(values["release_temps"])
    emit("\nFETCH_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n")
    emit(values["var_description_code"])
    emit("\n")
    emit(values["line_number_code"])
    emit("\ngoto ")
    emit(values["exception_target"])
    emit(";\n}\n}\n")


def _emit_034_template_loop_break_next_readable(emit, values):
    emit("if (")
    emit(values["to_name"])
    emit(" == NULL) {\n    if (CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate)) {\n")
    emit(values["break_indicator_code"])
    emit("\n        goto ")
    emit(values["break_target"])
    emit(";\n    } else {\n")
    emit(values["release_temps"])
    emit("\n        FETCH_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n")
    emit(values["var_description_code"])
    emit("\n")
    emit(values["line_number_code"])
    emit("\n        goto ")
    emit(values["exception_target"])
    emit(";\n    }\n}\n")


def _emit_035_template_metapath_loader_body(emit, values):
    emit(
        '\n\n\n#include "nuitka/prelude.h"\n\n\n#if PY_MICRO_VERSION < 16\n#define PYTHON_VERSION (PY_MAJOR_VERSION * 256 + PY_MINOR_VERSION * 16 + PY_MICRO_VERSION)\n#else\n#define PYTHON_VERSION (PY_MAJOR_VERSION * 256 + PY_MINOR_VERSION * 16 + 15)\n#endif\n\n#include "nuitka/constants_blob.h"\n\n#include "nuitka/tracing.h"\n#include "nuitka/unfreezing.h"\n\n\n#ifndef __cplusplus\n#include <stdbool.h>\n#endif\n\n#if '
    )
    emit(str(values["bytecode_count"]))
    emit(" > 0\nstatic unsigned char *bytecode_data[")
    emit(str(values["bytecode_count"]))
    emit(
        "];\n#else\nstatic unsigned char **bytecode_data = NULL;\n#endif\n\n\n#ifdef __cplusplus\n#define NUITKA_CAST_INIT_REASON(x) reinterpret_cast<module_init_func>((void*)(x))\n#else\n#define NUITKA_CAST_INIT_REASON(x) (module_init_func)(x)\n#endif\n\n\n\n\n\n"
    )
    emit(values["metapath_module_decls"])
    emit("\n\nstatic struct Nuitka_MetaPathBasedLoaderEntry meta_path_loader_entries[")
    emit(str(values["entry_count"]))
    emit("] = {\n")
    emit(values["metapath_loader_inittab"])
    emit(
        '\n};\n\nstatic void _loadBytesCodesBlob(PyThreadState *tstate) {\nstatic bool init_done = false;\n\nif (init_done == false) {\n\nloadConstantsBlob(tstate, bytecode_data, ".bytecode");\n\ninit_done = true;\n}\n}\n\nvoid setupMetaPathBasedLoader(PyThreadState *tstate) {\nstatic bool init_done = false;\nif (init_done == false) {\n_loadBytesCodesBlob(tstate);\nregisterMetaPathBasedLoader(meta_path_loader_entries, bytecode_data, '
    )
    emit(str(values["entry_count"]))
    emit(
        ");\n\ninit_done = true;\n}\n}\n\n\n\n\n\n\n\n\n\n\nstruct frozen_desc {\nchar const *name;\nint index;\nint size;\n};\n\nstatic struct frozen_desc _frozen_modules[] = {\n"
    )
    emit(values["frozen_modules"])
    emit(
        '\n{NULL, 0, 0}\n};\n\n\nvoid copyFrozenModulesTo(struct _frozen *destination) {\nNUITKA_PRINT_TIMING("copyFrozenModulesTo(): Calling _loadBytesCodesBlob.");\n_loadBytesCodesBlob(NULL);\n\nNUITKA_PRINT_TIMING("copyFrozenModulesTo(): Updating frozen module table sizes.");\n\nstruct frozen_desc *current = _frozen_modules;\n\nfor (;;) {\ndestination->name = (char *)current->name;\ndestination->code = bytecode_data[current->index];\ndestination->size = current->size;\n#if PYTHON_VERSION >= 0x3b0\ndestination->is_package = current->size < 0;\ndestination->size = Py_ABS(destination->size);\n#if PYTHON_VERSION < 0x3d0\ndestination->get_code = NULL;\n#endif\n#endif\nif (destination->name == NULL) break;\n\ncurrent += 1;\ndestination += 1;\n};\n}\n\n#if _NUITKA_MODULE_MODE\n\n#ifndef NUITKA_LOADER_COMPARE_NAME\n#define NUITKA_LOADER_COMPARE_NAME(name, index, entry) strcmp(name, (entry)->name)\n#endif\n\nstruct Nuitka_MetaPathBasedLoaderEntry const *getLoaderEntry(char const *name) {\nfor (int i = 0; i < '
    )
    emit(str(values["entry_count"]))
    emit(
        "; i++) {\nif (NUITKA_LOADER_COMPARE_NAME(name, i, &meta_path_loader_entries[i]) == 0) {\nreturn &meta_path_loader_entries[i];\n}\n}\n\nassert(false);\nreturn NULL;\n}\n#endif\n\n"
    )


def _emit_035_template_metapath_loader_body_readable(emit, values):
    emit(
        '\n/* Code to register embedded modules for meta path based loading if any. */\n\n#include "nuitka/prelude.h"\n\n/* Use a hex version of our own to compare for versions. We do not care about pre-releases */\n#if PY_MICRO_VERSION < 16\n#define PYTHON_VERSION (PY_MAJOR_VERSION * 256 + PY_MINOR_VERSION * 16 + PY_MICRO_VERSION)\n#else\n#define PYTHON_VERSION (PY_MAJOR_VERSION * 256 + PY_MINOR_VERSION * 16 + 15)\n#endif\n\n#include "nuitka/constants_blob.h"\n\n#include "nuitka/tracing.h"\n#include "nuitka/unfreezing.h"\n\n/* Type bool, spell-checker: ignore stdbool */\n#ifndef __cplusplus\n#include <stdbool.h>\n#endif\n\n#if '
    )
    emit(str(values["bytecode_count"]))
    emit(" > 0\nstatic unsigned char *bytecode_data[")
    emit(str(values["bytecode_count"]))
    emit(
        "];\n#else\nstatic unsigned char **bytecode_data = NULL;\n#endif\n\n/* Helper for portable cast, to use string literals as module_init_func */\n#ifdef __cplusplus\n#define NUITKA_CAST_INIT_REASON(x) reinterpret_cast<module_init_func>((void*)(x))\n#else\n#define NUITKA_CAST_INIT_REASON(x) (module_init_func)(x)\n#endif\n\n/* Table for lookup to find compiled or bytecode modules included in this\n * binary or module, or put along this binary as extension modules. We do\n * our own loading for each of these.\n */\n"
    )
    emit(values["metapath_module_decls"])
    emit("\n\nstatic struct Nuitka_MetaPathBasedLoaderEntry meta_path_loader_entries[")
    emit(str(values["entry_count"]))
    emit("] = {\n")
    emit(values["metapath_loader_inittab"])
    emit(
        '\n};\n\nstatic void _loadBytesCodesBlob(PyThreadState *tstate) {\n    static bool init_done = false;\n\n    if (init_done == false) {\n        // Note needed for mere data.\n        loadConstantsBlob(tstate, bytecode_data, ".bytecode");\n\n        init_done = true;\n    }\n}\n\nvoid setupMetaPathBasedLoader(PyThreadState *tstate) {\n    static bool init_done = false;\n    if (init_done == false) {\n        _loadBytesCodesBlob(tstate);\n        registerMetaPathBasedLoader(meta_path_loader_entries, bytecode_data, '
    )
    emit(str(values["entry_count"]))
    emit(
        ');\n\n        init_done = true;\n    }\n}\n\n// This provides the frozen (compiled bytecode) files that are included if\n// any.\n\n// These modules should be loaded as bytecode. They may e.g. have to be loadable\n// during "Py_Initialize" already, or for irrelevance, they are only included\n// in this un-optimized form. These are not compiled by Nuitka, and therefore\n// are not accelerated at all, merely bundled with the binary or module, so\n// that CPython library can start out finding them.\n\nstruct frozen_desc {\n    char const *name;\n    int index;\n    int size;\n};\n\nstatic struct frozen_desc _frozen_modules[] = {\n'
    )
    emit(values["frozen_modules"])
    emit(
        '\n    {NULL, 0, 0}\n};\n\n\nvoid copyFrozenModulesTo(struct _frozen *destination) {\n    NUITKA_PRINT_TIMING("copyFrozenModulesTo(): Calling _loadBytesCodesBlob.");\n    _loadBytesCodesBlob(NULL);\n\n    NUITKA_PRINT_TIMING("copyFrozenModulesTo(): Updating frozen module table sizes.");\n\n    struct frozen_desc *current = _frozen_modules;\n\n    for (;;) {\n        destination->name = (char *)current->name;\n        destination->code = bytecode_data[current->index];\n        destination->size = current->size;\n#if PYTHON_VERSION >= 0x3b0\n        destination->is_package = current->size < 0;\n        destination->size = Py_ABS(destination->size);\n#if PYTHON_VERSION < 0x3d0\n        destination->get_code = NULL;\n#endif\n#endif\n        if (destination->name == NULL) break;\n\n        current += 1;\n        destination += 1;\n    };\n}\n\n#if _NUITKA_MODULE_MODE\n\n#ifndef NUITKA_LOADER_COMPARE_NAME\n#define NUITKA_LOADER_COMPARE_NAME(name, index, entry) strcmp(name, (entry)->name)\n#endif\n\nstruct Nuitka_MetaPathBasedLoaderEntry const *getLoaderEntry(char const *name) {\n    for (int i = 0; i < '
    )
    emit(str(values["entry_count"]))
    emit(
        "; i++) {\n        if (NUITKA_LOADER_COMPARE_NAME(name, i, &meta_path_loader_entries[i]) == 0) {\n            return &meta_path_loader_entries[i];\n        }\n    }\n\n    assert(false);\n    return NULL;\n}\n#endif\n\n"
    )


def _emit_036_template_global_copyright(emit, values):
    emit(values["module_identifier"])
    emit("'\n* created by Nuitka version ")
    emit(values["version"])
    emit("\n*\n* This code is in part copyright ")
    emit(values["year"])
    emit(
        ' Kay Hayen.\n*\n* Licensed under the GNU Affero General Public License, Version 3 (the "License");\n* you may not use this file except in compliance with the License.\n*\n* You may obtain a copy of the License in "LICENSE.txt" and the runtime\n* exception granted in "LICENSE-RUNTIME.txt" from Nuitka source code. For\n* deploying the generated code it is intended to not restrict distributing\n* created binaries.\n*\n* Unless required by applicable law or agreed to in writing, software\n* distributed under the License is distributed on an "AS IS" BASIS,\n* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n* See the License for the specific language governing permissions and\n* limitations under the License.\n*/\n'
    )


def _emit_036_template_global_copyright_readable(emit, values):
    emit("/* Generated code for Python module '")
    emit(values["module_identifier"])
    emit("'\n * created by Nuitka version ")
    emit(values["version"])
    emit("\n *\n * This code is in part copyright ")
    emit(values["year"])
    emit(
        ' Kay Hayen.\n *\n * Licensed under the GNU Affero General Public License, Version 3 (the "License");\n * you may not use this file except in compliance with the License.\n *\n * You may obtain a copy of the License in "LICENSE.txt" and the runtime\n * exception granted in "LICENSE-RUNTIME.txt" from Nuitka source code. For\n * deploying the generated code it is intended to not restrict distributing\n * created binaries.\n *\n * Unless required by applicable law or agreed to in writing, software\n * distributed under the License is distributed on an "AS IS" BASIS,\n * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n * See the License for the specific language governing permissions and\n * limitations under the License.\n */\n'
    )


def _emit_037_template_module_body_template(emit, values):
    emit(
        '\n#include "nuitka/prelude.h"\n\n#include "nuitka/unfreezing.h"\n\n#include "__helpers.h"\n\n'
    )
    emit(values["module_includes"])
    emit("\n\n")
    emit(values["module_identifier"])
    emit(
        '" is a Python object pointer of module type.\n*\n* Note: For full compatibility with CPython, every module variable access\n* needs to go through it except for cases where the module cannot possibly\n* have changed in the mean time.\n*/\n\nPyObject *module_'
    )
    emit(values["module_identifier"])
    emit(";\nPyDictObject *moduledict_")
    emit(values["module_identifier"])
    emit(";\n\n\nstatic struct ModuleConstants {\n")
    emit(values["module_constants_decl"])
    emit(
        "\n} mod_consts;\n#ifndef __NUITKA_NO_ASSERT__\nstatic Py_hash_t mod_consts_hash["
    )
    emit(str(values["constants_count"]))
    emit(
        "];\n#endif\n\nstatic PyObject *module_filename_obj = NULL;\n\n\nstatic bool constants_created = false;\n\nNUITKA_DECLARE_CONSTANT_BLOB(\n"
    )
    emit(values["module_const_blob_symbol_name"])
    emit(",\n")
    emit(values["module_const_blob_symbol_name"])
    emit(
        ",\nconst\n);\n\n\nstatic void createModuleConstants(PyThreadState *tstate) {\nif (constants_created == false) {\n#if "
    )
    emit(str(values["use_direct_constant_blobs"]))
    emit("\nLOAD_DIRECT_CONSTANTS_BLOB(tstate, (PyObject **)&mod_consts, ")
    emit(values["module_const_blob_symbol_name"])
    emit(");\n#else\nloadConstantsBlob(tstate, &mod_consts, UN_TRANSLATE(")
    emit(values["module_const_blob_name"])
    emit("));\n#endif\nconstants_created = true;\n\n#ifndef __NUITKA_NO_ASSERT__\n")
    emit(values["module_constants_check_hash"])
    emit("\n#endif\n}\n}\n\n\n#if ")
    emit(values["is_dunder_main"])
    emit(
        "\nvoid createMainModuleConstants(PyThreadState *tstate) {\ncreateModuleConstants(tstate);\n}\n#endif\n\n\n#ifndef __NUITKA_NO_ASSERT__\nvoid checkModuleConstants_"
    )
    emit(values["module_identifier"])
    emit("(PyThreadState *tstate) {\n\nif (constants_created == false) return;\n\n")
    emit(values["module_constants_check_object"])
    emit("\n}\n#endif\n\n\n#if ")
    emit(str(values["module_variable_accessors_count"]))
    emit(
        "\n#if PYTHON_VERSION >= 0x3c0\nNUITKA_MAY_BE_UNUSED static uint32_t _Nuitka_PyDictKeys_GetVersionForCurrentState(PyInterpreterState *interp, PyDictKeysObject *dk)\n{\nif (dk->dk_version != 0) {\nreturn dk->dk_version;\n}\nuint32_t result = Nuitka_PyInterpreterState_GetDictState(interp)->next_keys_version++;\ndk->dk_version = result;\nreturn result;\n}\n#elif PYTHON_VERSION >= 0x3b0\nstatic uint32_t _Nuitka_next_dict_keys_version = 2;\n\nNUITKA_MAY_BE_UNUSED static uint32_t _Nuitka_PyDictKeys_GetVersionForCurrentState(PyDictKeysObject *dk)\n{\nif (dk->dk_version != 0) {\nreturn dk->dk_version;\n}\nuint32_t result = _Nuitka_next_dict_keys_version++;\ndk->dk_version = result;\nreturn result;\n}\n#endif\n#endif\n\n\n"
    )
    emit(values["module_variable_accessors"])
    emit("\n\n#if !defined(_NUITKA_EXPERIMENTAL_NEW_CODE_OBJECTS)\n\n")
    emit(values["module_code_objects_decl"])
    emit("\n\nstatic void createModuleCodeObjects(void) {\n")
    emit(values["module_code_objects_init"])
    emit("\n}\n#endif\n\n\n")
    emit(values["module_functions_decl"])
    emit("\n\n\n")
    emit(values["module_functions_code"])
    emit(
        "\n\nextern void _initCompiledCellType();\nextern void _initCompiledGeneratorType();\nextern void _initCompiledFunctionType();\nextern void _initCompiledMethodType();\nextern void _initCompiledFrameType();\n\nextern PyTypeObject Nuitka_Loader_Type;\n\n#ifdef _NUITKA_PLUGIN_DILL_ENABLED\n\n\nextern void registerDillPluginTables(PyThreadState *tstate, char const *module_name, PyMethodDef *reduce_compiled_function, PyMethodDef *create_compiled_function);\n\nstatic function_impl_code const function_table_"
    )
    emit(values["module_identifier"])
    emit("[] = {\n")
    emit(values["module_function_table_entries"])
    emit(
        '\nNULL\n};\n\nstatic PyObject *_reduce_compiled_function(PyObject *self, PyObject *args, PyObject *kwds) {\nPyObject *func;\n\nif (!PyArg_ParseTuple(args, "O:reduce_compiled_function", &func, NULL)) {\nreturn NULL;\n}\n\nif (Nuitka_Function_Check(func) == false) {\nPyThreadState *tstate = PyThreadState_GET();\n\nSET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "not a compiled function");\nreturn NULL;\n}\n\nstruct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)func;\n\nreturn Nuitka_Function_GetFunctionState(function, function_table_'
    )
    emit(values["module_identifier"])
    emit(
        ');\n}\n\nstatic PyMethodDef _method_def_reduce_compiled_function = {"reduce_compiled_function", (PyCFunction)_reduce_compiled_function,\nMETH_VARARGS, NULL};\n\n\nstatic PyObject *_create_compiled_function(PyObject *self, PyObject *args, PyObject *kwds) {\nCHECK_OBJECT_DEEP(args);\n\nPyObject *function_index;\nPyObject *code_object_desc;\nPyObject *defaults;\nPyObject *kw_defaults;\nPyObject *doc;\nPyObject *constant_return_value;\nPyObject *function_qualname;\nPyObject *closure;\nPyObject *annotations;\nPyObject *func_dict;\n\nif (!PyArg_ParseTuple(args, "OOOOOOOOOO:create_compiled_function", &function_index, &code_object_desc, &defaults, &kw_defaults, &doc, &constant_return_value, &function_qualname, &closure, &annotations, &func_dict, NULL)) {\nreturn NULL;\n}\n\nreturn (PyObject *)Nuitka_Function_CreateFunctionViaCodeIndex(\nmodule_'
    )
    emit(values["module_identifier"])
    emit(
        ",\nfunction_qualname,\nfunction_index,\ncode_object_desc,\nconstant_return_value,\ndefaults,\nkw_defaults,\ndoc,\nclosure,\nannotations,\nfunc_dict,\nfunction_table_"
    )
    emit(values["module_identifier"])
    emit(",\nsizeof(function_table_")
    emit(values["module_identifier"])
    emit(
        ') / sizeof(function_impl_code)\n);\n}\n\nstatic PyMethodDef _method_def_create_compiled_function = {\n"create_compiled_function",\n(PyCFunction)_create_compiled_function,\nMETH_VARARGS, NULL\n};\n\n\n#endif\n\n\n#if _NUITKA_MODULE_MODE && '
    )
    emit(str(values["is_top"]))
    emit("\nstatic char const *module_full_name = ")
    emit(values["module_name_cstr"])
    emit(";\n#endif\n\n\nPyObject *module_code_")
    emit(values["module_identifier"])
    emit(
        '(PyThreadState *tstate, PyObject *module, struct Nuitka_MetaPathBasedLoaderEntry const *loader_entry) {\n\nPGO_onModuleEntered("'
    )
    emit(values["module_identifier"])
    emit('");\n\n// Store the module for future use.\nmodule_')
    emit(values["module_identifier"])
    emit(" = module;\n\nmoduledict_")
    emit(values["module_identifier"])
    emit(" = MODULE_DICT(module_")
    emit(values["module_identifier"])
    emit(
        ");\n\n\nstatic bool init_done = false;\n\nif (init_done == false) {\n#if _NUITKA_MODULE_MODE && "
    )
    emit(str(values["is_top"]))
    emit(
        '\n\n\n\n#if PYTHON_VERSION > 0x350 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_ALLOCATORS)\ninitNuitkaAllocators();\n#endif\n\n_initBuiltinModule(tstate);\n\nPyObject *real_module_name = PyObject_GetAttrString(module, "__name__");\nCHECK_OBJECT(real_module_name);\nmodule_full_name = strdup(Nuitka_String_AsString(real_module_name));\n\ncreateGlobalConstants(tstate, real_module_name);\n\n\n_initCompiledCellType();\n_initCompiledGeneratorType();\n_initCompiledFunctionType();\n_initCompiledMethodType();\n_initCompiledFrameType();\n\n_initSlotCompare();\n#if PYTHON_VERSION >= 0x270\n_initSlotIterNext();\n#endif\n\npatchTypeComparison();\n\n\n#ifdef _NUITKA_TRACE\nPRINT_STRING("'
    )
    emit(values["module_identifier"])
    emit(
        ': Calling setupMetaPathBasedLoader().\\n");\n#endif\nsetupMetaPathBasedLoader(tstate);\n#if '
    )
    emit(values["module_def_size"])
    emit(' >= 0\n#ifdef _NUITKA_TRACE\nPRINT_STRING("')
    emit(values["module_identifier"])
    emit(
        ': Calling updateMetaPathBasedLoaderModuleRoot().\\n");\n#endif\nupdateMetaPathBasedLoaderModuleRoot(module_full_name);\n#endif\n\n\n#if PYTHON_VERSION >= 0x300\npatchInspectModule(tstate);\n#endif\n\n#endif\n\n/* The constants only used by this module are created now. */\nNUITKA_PRINT_TRACE("'
    )
    emit(values["module_identifier"])
    emit(
        ': Calling createModuleConstants().\\n");\ncreateModuleConstants(tstate);\n\n#if !defined(_NUITKA_EXPERIMENTAL_NEW_CODE_OBJECTS)\ncreateModuleCodeObjects();\n#endif\ninit_done = true;\n}\n\n#if _NUITKA_MODULE_MODE && '
    )
    emit(str(values["is_top"]))
    emit("\nPyObject *pre_load = IMPORT_EMBEDDED_MODULE(tstate, ")
    emit(values["module_name_cstr"])
    emit(' "-preLoad");\nif (pre_load == NULL) {\nreturn NULL;\n}\n#endif\n\n')
    emit(values["module_identifier"])
    emit(
        '\\n");\n\n#ifdef _NUITKA_PLUGIN_DILL_ENABLED\n{\nchar const *module_name_c;\nif (loader_entry != NULL) {\nmodule_name_c = loader_entry->name;\n} else {\nPyObject *module_name = GET_STRING_DICT_VALUE(moduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___name__);\nmodule_name_c = Nuitka_String_AsString(module_name);\n}\n\nregisterDillPluginTables(tstate, module_name_c, &_method_def_reduce_compiled_function, &_method_def_create_compiled_function);\n}\n#endif\n\n\n\n\n#if PYTHON_VERSION >= 0x3b0 && PYTHON_VERSION < 0x3c0 && _NUITKA_STANDALONE_MODE && !"
    )
    emit(values["is_package"])
    emit("\nUPDATE_STRING_DICT0(\nmoduledict_")
    emit(values["module_identifier"])
    emit(
        ",\n(Nuitka_StringObject *)const_str_plain___compiled__,\nNuitka_dunder_compiled_value\n);\n#endif\n\n\n{\n#if "
    )
    emit(values["is_dunder_main"])
    emit("\nUPDATE_STRING_DICT0(\nmoduledict_")
    emit(values["module_identifier"])
    emit(",\n(Nuitka_StringObject *)const_str_plain___package__,\n")
    emit(values["dunder_main_package"])
    emit("\n);\n#elif ")
    emit(values["is_package"])
    emit("\nPyObject *module_name = GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___name__);\n\nUPDATE_STRING_DICT0(\nmoduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n(Nuitka_StringObject *)const_str_plain___package__,\nmodule_name\n);\n#else\n\n#if PYTHON_VERSION < 0x300\nPyObject *module_name = GET_STRING_DICT_VALUE(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___name__);\nchar const *module_name_cstr = PyString_AS_STRING(module_name);\n\nchar const *last_dot = strrchr(module_name_cstr, '.');\n\nif (last_dot != NULL) {\nUPDATE_STRING_DICT1(\nmoduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n(Nuitka_StringObject *)const_str_plain___package__,\nPyString_FromStringAndSize(module_name_cstr, last_dot - module_name_cstr)\n);\n}\n#else\nPyObject *module_name = GET_STRING_DICT_VALUE(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___name__);\nPy_ssize_t dot_index = PyUnicode_Find(module_name, const_str_dot, 0, PyUnicode_GetLength(module_name), -1);\n\nif (dot_index != -1) {\nUPDATE_STRING_DICT1(\nmoduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n(Nuitka_StringObject *)const_str_plain___package__,\nPyUnicode_Substring(module_name, 0, dot_index)\n);\n}\n#endif\n#endif\n}\n\nCHECK_OBJECT(module_"
    )
    emit(values["module_identifier"])
    emit(");\n\n\n\n\n\nif (GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___builtins__) == NULL) {\nPyObject *value = (PyObject *)builtin_module;\n\n\n#if _NUITKA_MODULE_MODE || !"
    )
    emit(values["is_dunder_main"])
    emit(
        "\nvalue = PyModule_GetDict(value);\n#endif\n\nUPDATE_STRING_DICT0(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___builtins__, value);\n}\n\nPyObject *module_loader = Nuitka_Loader_New(loader_entry);\nUPDATE_STRING_DICT0(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___loader__, module_loader);\n\n#if PYTHON_VERSION >= 0x300\n\n\n#if "
    )
    emit(values["is_dunder_main"])
    emit("\n\nUPDATE_STRING_DICT0(moduledict_")
    emit(values["module_identifier"])
    emit(
        ', (Nuitka_StringObject *)const_str_plain___spec__, Py_None);\n#else\n\n{\nPyObject *bootstrap_module = getImportLibBootstrapModule();\nCHECK_OBJECT(bootstrap_module);\n\nPyObject *_spec_from_module = PyObject_GetAttrString(bootstrap_module, "_spec_from_module");\nCHECK_OBJECT(_spec_from_module);\n\nPyObject *spec_value = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, _spec_from_module, module_'
    )
    emit(values["module_identifier"])
    emit(
        ");\nPy_DECREF(_spec_from_module);\n\n\n\n\nif (spec_value == NULL) {\nPyErr_PrintEx(0);\nabort();\n}\n\n\nSET_ATTRIBUTE(tstate, spec_value, const_str_plain__initializing, Py_True);\n\n#if _NUITKA_MODULE_MODE && "
    )
    emit(str(values["is_top"]))
    emit(" && ")
    emit(values["module_def_size"])
    emit(
        " >= 0\n\nSET_ATTRIBUTE(tstate, spec_value, const_str_plain_loader, module_loader);\n#endif\n\nUPDATE_STRING_DICT1(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___spec__, spec_value);\n}\n#endif\n#endif\n\n\n"
    )
    emit(values["temps_decl"])
    emit("\n\n\n")
    emit(values["module_init_codes"])
    emit("\n\n\n")
    emit(values["module_codes"])
    emit('\n\n\nPGO_onModuleExit("')
    emit(values["module_identifier"])
    emit('", false);\n\n#if _NUITKA_MODULE_MODE && ')
    emit(str(values["is_top"]))
    emit("\n{\nPyObject *post_load = IMPORT_EMBEDDED_MODULE(tstate, ")
    emit(values["module_name_cstr"])
    emit(
        ' "-postLoad");\nif (post_load == NULL) {\nreturn NULL;\n}\n}\n#endif\n\nPy_INCREF(module_'
    )
    emit(values["module_identifier"])
    emit(");\nreturn module_")
    emit(values["module_identifier"])
    emit(";\n")
    emit(values["module_exit"])
    emit("\n")


def _emit_037_template_module_body_template_readable(emit, values):
    emit(
        '\n#include "nuitka/prelude.h"\n\n#include "nuitka/unfreezing.h"\n\n#include "__helpers.h"\n\n'
    )
    emit(values["module_includes"])
    emit('\n\n/* The "module_')
    emit(values["module_identifier"])
    emit(
        '" is a Python object pointer of module type.\n *\n * Note: For full compatibility with CPython, every module variable access\n * needs to go through it except for cases where the module cannot possibly\n * have changed in the mean time.\n */\n\nPyObject *module_'
    )
    emit(values["module_identifier"])
    emit(";\nPyDictObject *moduledict_")
    emit(values["module_identifier"])
    emit(
        ";\n\n/* The declarations of module constants used, if any. */\nstatic struct ModuleConstants {\n"
    )
    emit(values["module_constants_decl"])
    emit(
        "\n} mod_consts;\n#ifndef __NUITKA_NO_ASSERT__\nstatic Py_hash_t mod_consts_hash["
    )
    emit(str(values["constants_count"]))
    emit(
        "];\n#endif\n\nstatic PyObject *module_filename_obj = NULL;\n\n/* Indicator if this modules private constants were created yet. */\nstatic bool constants_created = false;\n\nNUITKA_DECLARE_CONSTANT_BLOB(\n    "
    )
    emit(values["module_const_blob_symbol_name"])
    emit(",\n    ")
    emit(values["module_const_blob_symbol_name"])
    emit(
        ",\n    const\n);\n\n/* Function to create module private constants. */\nstatic void createModuleConstants(PyThreadState *tstate) {\n    if (constants_created == false) {\n#if "
    )
    emit(str(values["use_direct_constant_blobs"]))
    emit("\n        LOAD_DIRECT_CONSTANTS_BLOB(tstate, (PyObject **)&mod_consts, ")
    emit(values["module_const_blob_symbol_name"])
    emit(");\n#else\n        loadConstantsBlob(tstate, &mod_consts, UN_TRANSLATE(")
    emit(values["module_const_blob_name"])
    emit(
        "));\n#endif\n        constants_created = true;\n\n#ifndef __NUITKA_NO_ASSERT__\n"
    )
    emit(values["module_constants_check_hash"])
    emit(
        '\n#endif\n    }\n}\n\n// We want to be able to initialize the "__main__" constants in any case.\n#if '
    )
    emit(values["is_dunder_main"])
    emit(
        "\nvoid createMainModuleConstants(PyThreadState *tstate) {\n    createModuleConstants(tstate);\n}\n#endif\n\n/* Function to verify module private constants for non-corruption. */\n#ifndef __NUITKA_NO_ASSERT__\nvoid checkModuleConstants_"
    )
    emit(values["module_identifier"])
    emit(
        "(PyThreadState *tstate) {\n    // The module may not have been used at all, then ignore this.\n    if (constants_created == false) return;\n\n"
    )
    emit(values["module_constants_check_object"])
    emit(
        "\n}\n#endif\n\n// Helper to preserving module variables for Python3.11+\n#if "
    )
    emit(str(values["module_variable_accessors_count"]))
    emit(
        "\n#if PYTHON_VERSION >= 0x3c0\nNUITKA_MAY_BE_UNUSED static uint32_t _Nuitka_PyDictKeys_GetVersionForCurrentState(PyInterpreterState *interp, PyDictKeysObject *dk)\n{\n    if (dk->dk_version != 0) {\n        return dk->dk_version;\n    }\n    uint32_t result = Nuitka_PyInterpreterState_GetDictState(interp)->next_keys_version++;\n    dk->dk_version = result;\n    return result;\n}\n#elif PYTHON_VERSION >= 0x3b0\nstatic uint32_t _Nuitka_next_dict_keys_version = 2;\n\nNUITKA_MAY_BE_UNUSED static uint32_t _Nuitka_PyDictKeys_GetVersionForCurrentState(PyDictKeysObject *dk)\n{\n    if (dk->dk_version != 0) {\n        return dk->dk_version;\n    }\n    uint32_t result = _Nuitka_next_dict_keys_version++;\n    dk->dk_version = result;\n    return result;\n}\n#endif\n#endif\n\n// Accessors to module variables.\n"
    )
    emit(values["module_variable_accessors"])
    emit(
        "\n\n#if !defined(_NUITKA_EXPERIMENTAL_NEW_CODE_OBJECTS)\n// The module code objects.\n"
    )
    emit(values["module_code_objects_decl"])
    emit("\n\nstatic void createModuleCodeObjects(void) {\n")
    emit(values["module_code_objects_init"])
    emit("\n}\n#endif\n\n// The module function declarations.\n")
    emit(values["module_functions_decl"])
    emit("\n\n// The module function definitions.\n")
    emit(values["module_functions_code"])
    emit(
        "\n\nextern void _initCompiledCellType();\nextern void _initCompiledGeneratorType();\nextern void _initCompiledFunctionType();\nextern void _initCompiledMethodType();\nextern void _initCompiledFrameType();\n\nextern PyTypeObject Nuitka_Loader_Type;\n\n#ifdef _NUITKA_PLUGIN_DILL_ENABLED\n// Provide a way to create find a function via its C code and create it back\n// in another process, useful for multiprocessing extensions like dill\nextern void registerDillPluginTables(PyThreadState *tstate, char const *module_name, PyMethodDef *reduce_compiled_function, PyMethodDef *create_compiled_function);\n\nstatic function_impl_code const function_table_"
    )
    emit(values["module_identifier"])
    emit("[] = {\n")
    emit(values["module_function_table_entries"])
    emit(
        '\n    NULL\n};\n\nstatic PyObject *_reduce_compiled_function(PyObject *self, PyObject *args, PyObject *kwds) {\n    PyObject *func;\n\n    if (!PyArg_ParseTuple(args, "O:reduce_compiled_function", &func, NULL)) {\n        return NULL;\n    }\n\n    if (Nuitka_Function_Check(func) == false) {\n        PyThreadState *tstate = PyThreadState_GET();\n\n        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "not a compiled function");\n        return NULL;\n    }\n\n    struct Nuitka_FunctionObject *function = (struct Nuitka_FunctionObject *)func;\n\n    return Nuitka_Function_GetFunctionState(function, function_table_'
    )
    emit(values["module_identifier"])
    emit(
        ');\n}\n\nstatic PyMethodDef _method_def_reduce_compiled_function = {"reduce_compiled_function", (PyCFunction)_reduce_compiled_function,\n                                                           METH_VARARGS, NULL};\n\n\nstatic PyObject *_create_compiled_function(PyObject *self, PyObject *args, PyObject *kwds) {\n    CHECK_OBJECT_DEEP(args);\n\n    PyObject *function_index;\n    PyObject *code_object_desc;\n    PyObject *defaults;\n    PyObject *kw_defaults;\n    PyObject *doc;\n    PyObject *constant_return_value;\n    PyObject *function_qualname;\n    PyObject *closure;\n    PyObject *annotations;\n    PyObject *func_dict;\n\n    if (!PyArg_ParseTuple(args, "OOOOOOOOOO:create_compiled_function", &function_index, &code_object_desc, &defaults, &kw_defaults, &doc, &constant_return_value, &function_qualname, &closure, &annotations, &func_dict, NULL)) {\n        return NULL;\n    }\n\n    return (PyObject *)Nuitka_Function_CreateFunctionViaCodeIndex(\n        module_'
    )
    emit(values["module_identifier"])
    emit(
        ",\n        function_qualname,\n        function_index,\n        code_object_desc,\n        constant_return_value,\n        defaults,\n        kw_defaults,\n        doc,\n        closure,\n        annotations,\n        func_dict,\n        function_table_"
    )
    emit(values["module_identifier"])
    emit(",\n        sizeof(function_table_")
    emit(values["module_identifier"])
    emit(
        ') / sizeof(function_impl_code)\n    );\n}\n\nstatic PyMethodDef _method_def_create_compiled_function = {\n    "create_compiled_function",\n    (PyCFunction)_create_compiled_function,\n    METH_VARARGS, NULL\n};\n\n\n#endif\n\n// Actual name might be different when loaded as a package.\n#if _NUITKA_MODULE_MODE && '
    )
    emit(str(values["is_top"]))
    emit("\nstatic char const *module_full_name = ")
    emit(values["module_name_cstr"])
    emit(
        ";\n#endif\n\n// Internal entry point for module code.\nPyObject *module_code_"
    )
    emit(values["module_identifier"])
    emit(
        '(PyThreadState *tstate, PyObject *module, struct Nuitka_MetaPathBasedLoaderEntry const *loader_entry) {\n    // Report entry to PGO.\n    PGO_onModuleEntered("'
    )
    emit(values["module_identifier"])
    emit('");\n\n    // Store the module for future use.\n    module_')
    emit(values["module_identifier"])
    emit(" = module;\n\n    moduledict_")
    emit(values["module_identifier"])
    emit(" = MODULE_DICT(module_")
    emit(values["module_identifier"])
    emit(
        ");\n\n    // Modules can be loaded again in case of errors, avoid the init being done again.\n    static bool init_done = false;\n\n    if (init_done == false) {\n#if _NUITKA_MODULE_MODE && "
    )
    emit(str(values["is_top"]))
    emit(
        '\n        // In case of an extension module loaded into a process, we need to call\n        // initialization here because that\'s the first and potentially only time\n        // we are going called.\n#if PYTHON_VERSION > 0x350 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_ALLOCATORS)\n        initNuitkaAllocators();\n#endif\n        // Initialize the constant values used.\n        _initBuiltinModule(tstate);\n\n        PyObject *real_module_name = PyObject_GetAttrString(module, "__name__");\n        CHECK_OBJECT(real_module_name);\n        module_full_name = strdup(Nuitka_String_AsString(real_module_name));\n\n        createGlobalConstants(tstate, real_module_name);\n\n        /* Initialize the compiled types of Nuitka. */\n        _initCompiledCellType();\n        _initCompiledGeneratorType();\n        _initCompiledFunctionType();\n        _initCompiledMethodType();\n        _initCompiledFrameType();\n\n        _initSlotCompare();\n#if PYTHON_VERSION >= 0x270\n        _initSlotIterNext();\n#endif\n\n        patchTypeComparison();\n\n        // Enable meta path based loader if not already done.\n#ifdef _NUITKA_TRACE\n        PRINT_STRING("'
    )
    emit(values["module_identifier"])
    emit(
        ': Calling setupMetaPathBasedLoader().\\n");\n#endif\n        setupMetaPathBasedLoader(tstate);\n#if '
    )
    emit(values["module_def_size"])
    emit(' >= 0\n#ifdef _NUITKA_TRACE\n        PRINT_STRING("')
    emit(values["module_identifier"])
    emit(
        ': Calling updateMetaPathBasedLoaderModuleRoot().\\n");\n#endif\n        updateMetaPathBasedLoaderModuleRoot(module_full_name);\n#endif\n\n\n#if PYTHON_VERSION >= 0x300\n        patchInspectModule(tstate);\n#endif\n\n#endif\n\n        /* The constants only used by this module are created now. */\n        NUITKA_PRINT_TRACE("'
    )
    emit(values["module_identifier"])
    emit(
        ': Calling createModuleConstants().\\n");\n        createModuleConstants(tstate);\n\n#if !defined(_NUITKA_EXPERIMENTAL_NEW_CODE_OBJECTS)\n        createModuleCodeObjects();\n#endif\n        init_done = true;\n    }\n\n#if _NUITKA_MODULE_MODE && '
    )
    emit(str(values["is_top"]))
    emit("\n    PyObject *pre_load = IMPORT_EMBEDDED_MODULE(tstate, ")
    emit(values["module_name_cstr"])
    emit(
        ' "-preLoad");\n    if (pre_load == NULL) {\n        return NULL;\n    }\n#endif\n\n    // PRINT_STRING("in init'
    )
    emit(values["module_identifier"])
    emit(
        '\\n");\n\n#ifdef _NUITKA_PLUGIN_DILL_ENABLED\n    {\n        char const *module_name_c;\n        if (loader_entry != NULL) {\n            module_name_c = loader_entry->name;\n        } else {\n            PyObject *module_name = GET_STRING_DICT_VALUE(moduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ', (Nuitka_StringObject *)const_str_plain___name__);\n            module_name_c = Nuitka_String_AsString(module_name);\n        }\n\n        registerDillPluginTables(tstate, module_name_c, &_method_def_reduce_compiled_function, &_method_def_create_compiled_function);\n    }\n#endif\n\n    // For Python 3.11 standalone modules, package "__path__" is inserted by the\n    // loader before module code runs. Pre-seed "__compiled__" for non-packages\n    // to keep their dangerous dict slots aligned with packages.\n#if PYTHON_VERSION >= 0x3b0 && PYTHON_VERSION < 0x3c0 && _NUITKA_STANDALONE_MODE && !'
    )
    emit(values["is_package"])
    emit("\n    UPDATE_STRING_DICT0(\n        moduledict_")
    emit(values["module_identifier"])
    emit(
        ',\n        (Nuitka_StringObject *)const_str_plain___compiled__,\n        Nuitka_dunder_compiled_value\n    );\n#endif\n\n    // Update "__package__" value to what it ought to be.\n    {\n#if '
    )
    emit(values["is_dunder_main"])
    emit("\n        UPDATE_STRING_DICT0(\n            moduledict_")
    emit(values["module_identifier"])
    emit(
        ",\n            (Nuitka_StringObject *)const_str_plain___package__,\n            "
    )
    emit(values["dunder_main_package"])
    emit("\n        );\n#elif ")
    emit(values["is_package"])
    emit("\n        PyObject *module_name = GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___name__);\n\n        UPDATE_STRING_DICT0(\n            moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n            (Nuitka_StringObject *)const_str_plain___package__,\n            module_name\n        );\n#else\n\n#if PYTHON_VERSION < 0x300\n        PyObject *module_name = GET_STRING_DICT_VALUE(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___name__);\n        char const *module_name_cstr = PyString_AS_STRING(module_name);\n\n        char const *last_dot = strrchr(module_name_cstr, '.');\n\n        if (last_dot != NULL) {\n            UPDATE_STRING_DICT1(\n                moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n                (Nuitka_StringObject *)const_str_plain___package__,\n                PyString_FromStringAndSize(module_name_cstr, last_dot - module_name_cstr)\n            );\n        }\n#else\n        PyObject *module_name = GET_STRING_DICT_VALUE(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___name__);\n        Py_ssize_t dot_index = PyUnicode_Find(module_name, const_str_dot, 0, PyUnicode_GetLength(module_name), -1);\n\n        if (dot_index != -1) {\n            UPDATE_STRING_DICT1(\n                moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n                (Nuitka_StringObject *)const_str_plain___package__,\n                PyUnicode_Substring(module_name, 0, dot_index)\n            );\n        }\n#endif\n#endif\n    }\n\n    CHECK_OBJECT(module_"
    )
    emit(values["module_identifier"])
    emit(
        ');\n\n    // For deep importing of a module we need to have "__builtins__", so we set\n    // it ourselves in the same way than CPython does. Note: This must be done\n    // before the frame object is allocated, or else it may fail.\n\n    if (GET_STRING_DICT_VALUE(moduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___builtins__) == NULL) {\n        PyObject *value = (PyObject *)builtin_module;\n\n        // Check if main module, not a dict then but the module itself.\n#if _NUITKA_MODULE_MODE || !"
    )
    emit(values["is_dunder_main"])
    emit(
        "\n        value = PyModule_GetDict(value);\n#endif\n\n        UPDATE_STRING_DICT0(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___builtins__, value);\n    }\n\n    PyObject *module_loader = Nuitka_Loader_New(loader_entry);\n    UPDATE_STRING_DICT0(moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ', (Nuitka_StringObject *)const_str_plain___loader__, module_loader);\n\n#if PYTHON_VERSION >= 0x300\n// Set the "__spec__" value\n\n#if '
    )
    emit(values["is_dunder_main"])
    emit(
        '\n    // Main modules just get "None" as spec.\n    UPDATE_STRING_DICT0(moduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ', (Nuitka_StringObject *)const_str_plain___spec__, Py_None);\n#else\n    // Other modules get a "ModuleSpec" from the standard mechanism.\n    {\n        PyObject *bootstrap_module = getImportLibBootstrapModule();\n        CHECK_OBJECT(bootstrap_module);\n\n        PyObject *_spec_from_module = PyObject_GetAttrString(bootstrap_module, "_spec_from_module");\n        CHECK_OBJECT(_spec_from_module);\n\n        PyObject *spec_value = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, _spec_from_module, module_'
    )
    emit(values["module_identifier"])
    emit(
        ');\n        Py_DECREF(_spec_from_module);\n\n        // We can assume this to never fail, or else we are in trouble anyway.\n        // CHECK_OBJECT(spec_value);\n\n        if (spec_value == NULL) {\n            PyErr_PrintEx(0);\n            abort();\n        }\n\n        // Mark the execution in the "__spec__" value.\n        SET_ATTRIBUTE(tstate, spec_value, const_str_plain__initializing, Py_True);\n\n#if _NUITKA_MODULE_MODE && '
    )
    emit(str(values["is_top"]))
    emit(" && ")
    emit(values["module_def_size"])
    emit(
        ' >= 0\n        // Set our loader object in the "__spec__" value.\n        SET_ATTRIBUTE(tstate, spec_value, const_str_plain_loader, module_loader);\n#endif\n\n        UPDATE_STRING_DICT1(moduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ", (Nuitka_StringObject *)const_str_plain___spec__, spec_value);\n    }\n#endif\n#endif\n\n    // Temp variables if any\n"
    )
    emit(values["temps_decl"])
    emit("\n\n    // Module init code if any\n")
    emit(values["module_init_codes"])
    emit("\n\n    // Module code.\n")
    emit(values["module_codes"])
    emit(
        '\n\n    // Report to PGO about leaving the module without error.\n    PGO_onModuleExit("'
    )
    emit(values["module_identifier"])
    emit('", false);\n\n#if _NUITKA_MODULE_MODE && ')
    emit(str(values["is_top"]))
    emit("\n    {\n        PyObject *post_load = IMPORT_EMBEDDED_MODULE(tstate, ")
    emit(values["module_name_cstr"])
    emit(
        ' "-postLoad");\n        if (post_load == NULL) {\n            return NULL;\n        }\n    }\n#endif\n\n    Py_INCREF(module_'
    )
    emit(values["module_identifier"])
    emit(");\n    return module_")
    emit(values["module_identifier"])
    emit(";\n")
    emit(values["module_exit"])
    emit("\n")


def _emit_038_template_module_external_entry_point(emit, values):
    emit(
        '\n\n\n#if defined(__GNUC__)\n\n#if PYTHON_VERSION < 0x300\n\n#if defined(_WIN32)\n#define NUITKA_MODULE_INIT_FUNCTION __declspec(dllexport) PyMODINIT_FUNC\n#else\n#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC __attribute__((visibility("default")))\n#endif\n\n#else\n\n#if defined(_WIN32)\n#define NUITKA_MODULE_INIT_FUNCTION __declspec(dllexport) PyObject *\n#else\n\n#ifdef __cplusplus\n#define NUITKA_MODULE_INIT_FUNCTION extern "C" __attribute__((visibility("default"))) PyObject *\n#else\n#define NUITKA_MODULE_INIT_FUNCTION __attribute__((visibility("default"))) PyObject *\n#endif\n\n#endif\n#endif\n\n#else\n#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC\n#endif\n\nstatic PyObject *orig_dunder_file_value;\n\n#if PYTHON_VERSION >= 0x300\nstatic setattrofunc orig_PyModule_Type_tp_setattro;\n\n\nstatic int Nuitka_TopLevelModule_tp_setattro(PyObject *module, PyObject *name, PyObject *value) {\nPyModule_Type.tp_setattro = orig_PyModule_Type_tp_setattro;\n\nif (orig_dunder_file_value != NULL) {\nUPDATE_STRING_DICT0(\nmoduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ",\n(Nuitka_StringObject *)const_str_plain___file__,\norig_dunder_file_value\n);\n}\n\n\n#if PYTHON_VERSION >= 0x300\nif (PyUnicode_Check(name) && PyUnicode_Compare(name, const_str_plain___spec__) == 0) {\nreturn 0;\n}\n#endif\n\nreturn orig_PyModule_Type_tp_setattro(module, name, value);\n}\n#endif\n\n#if PYTHON_VERSION >= 0x300\nstatic struct PyModuleDef mdef_"
    )
    emit(values["module_identifier"])
    emit(" = {\nPyModuleDef_HEAD_INIT,\nNULL,                \nNULL,                \n")
    emit(values["module_def_size"])
    emit(
        ", \nNULL,                \nNULL,                \nNULL,                \nNULL,                \nNULL,                \n};\n#endif\n\n#if PYTHON_VERSION < 0x300\nstatic void onModuleFileValueRelease(void *v) {\nif (orig_dunder_file_value != NULL) {\nUPDATE_STRING_DICT0(\nmoduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n(Nuitka_StringObject *)const_str_plain___file__,\norig_dunder_file_value\n);\n}\n}\n#endif\n\n\n\n\n\n\nextern struct Nuitka_MetaPathBasedLoaderEntry const *getLoaderEntry(char const *name);\n\nstatic PyObject *"
    )
    emit(values["module_dll_entry_point"])
    emit(
        "_phase2(PyObject *module) {\nPyThreadState *tstate = PyThreadState_GET();\n\nPyObject *result = module_code_"
    )
    emit(values["module_identifier"])
    emit("(tstate, module, getLoaderEntry(")
    emit(values["module_name_cstr"])
    emit(
        "));\n\n#if PYTHON_VERSION < 0x300\n\n\n\n\nif (HAS_ERROR_OCCURRED(tstate) == false) {\norig_dunder_file_value = DICT_GET_ITEM_WITH_HASH_ERROR1(tstate, (PyObject *)moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ", const_str_plain___file__);\n\nPyObject *fake_file_value = PyCObject_FromVoidPtr(NULL, onModuleFileValueRelease);\n\nUPDATE_STRING_DICT1(\nmoduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n(Nuitka_StringObject *)const_str_plain___file__,\nfake_file_value\n);\n}\n#else\nif (result != NULL) {\n\n\norig_PyModule_Type_tp_setattro = PyModule_Type.tp_setattro;\nPyModule_Type.tp_setattro = Nuitka_TopLevelModule_tp_setattro;\n\norig_dunder_file_value = DICT_GET_ITEM_WITH_HASH_ERROR1(tstate, (PyObject *)moduledict_"
    )
    emit(values["module_identifier"])
    emit(", const_str_plain___file__);\n}\n#endif\n\nreturn result;\n}\n\n#if ")
    emit(values["module_def_size"])
    emit(" >= 0\nstatic int ")
    emit(values["module_dll_entry_point"])
    emit("_slot(PyObject *module) {\nPyObject *result = ")
    emit(values["module_dll_entry_point"])
    emit(
        "_phase2(module);\n\nif (unlikely(result == NULL)) {\nreturn 1;\n} else {\nreturn 0;\n}\n}\n#endif\n\nNUITKA_MODULE_INIT_FUNCTION ("
    )
    emit(values["module_dll_entry_point"])
    emit(
        ")(void) {\n#if PYTHON_VERSION < 0x3c0\nif (_Py_PackageContext != NULL) {\nif (strcmp(module_full_name, _Py_PackageContext) != 0) {\nmodule_full_name = strdup(_Py_PackageContext);\n}\n}\n#endif\n\n#if PYTHON_VERSION < 0x300\nPyObject *module = Py_InitModule4(\nmodule_full_name,        \nNULL,                    \n\nNULL,                    \n\n\nNULL,                    \nPYTHON_API_VERSION\n);\n#else\nmdef_"
    )
    emit(values["module_identifier"])
    emit(".m_name = module_full_name;\n\n#if ")
    emit(values["module_def_size"])
    emit(" == -1\nPyObject *module = PyModule_Create(&mdef_")
    emit(values["module_identifier"])
    emit(
        ");\nCHECK_OBJECT(module);\n\n{\nNUITKA_MAY_BE_UNUSED bool res = Nuitka_SetModuleString(module_full_name, module);\nassert(res != false);\n}\n\n#endif\n#endif\n\n#if "
    )
    emit(values["module_def_size"])
    emit(" >= 0\nstatic PyModuleDef_Slot _module_slots[] = {\n{Py_mod_exec, (void *)")
    emit(values["module_dll_entry_point"])
    emit("_slot},\n{0, NULL}\n};\n\nmdef_")
    emit(values["module_identifier"])
    emit(".m_slots = _module_slots;\n\nreturn PyModuleDef_Init(&mdef_")
    emit(values["module_identifier"])
    emit(");\n#elif PYTHON_VERSION >= 0x300\nreturn ")
    emit(values["module_dll_entry_point"])
    emit("_phase2(module);\n#else\n")
    emit(values["module_dll_entry_point"])
    emit("_phase2(module);\n#endif\n}\n")


def _emit_038_template_module_external_entry_point_readable(emit, values):
    emit(
        '\n\n/* Visibility definitions to make the DLL entry point exported */\n#if defined(__GNUC__)\n\n#if PYTHON_VERSION < 0x300\n\n#if defined(_WIN32)\n#define NUITKA_MODULE_INIT_FUNCTION __declspec(dllexport) PyMODINIT_FUNC\n#else\n#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC __attribute__((visibility("default")))\n#endif\n\n#else\n\n#if defined(_WIN32)\n#define NUITKA_MODULE_INIT_FUNCTION __declspec(dllexport) PyObject *\n#else\n\n#ifdef __cplusplus\n#define NUITKA_MODULE_INIT_FUNCTION extern "C" __attribute__((visibility("default"))) PyObject *\n#else\n#define NUITKA_MODULE_INIT_FUNCTION __attribute__((visibility("default"))) PyObject *\n#endif\n\n#endif\n#endif\n\n#else\n#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC\n#endif\n\nstatic PyObject *orig_dunder_file_value;\n\n#if PYTHON_VERSION >= 0x300\nstatic setattrofunc orig_PyModule_Type_tp_setattro;\n\n/* This is used one time only. */\nstatic int Nuitka_TopLevelModule_tp_setattro(PyObject *module, PyObject *name, PyObject *value) {\n    PyModule_Type.tp_setattro = orig_PyModule_Type_tp_setattro;\n\n    if (orig_dunder_file_value != NULL) {\n        UPDATE_STRING_DICT0(\n            moduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ',\n            (Nuitka_StringObject *)const_str_plain___file__,\n            orig_dunder_file_value\n        );\n    }\n\n    // Prevent "__spec__" update as well.\n#if PYTHON_VERSION >= 0x300\n    if (PyUnicode_Check(name) && PyUnicode_Compare(name, const_str_plain___spec__) == 0) {\n        return 0;\n    }\n#endif\n\n    return orig_PyModule_Type_tp_setattro(module, name, value);\n}\n#endif\n\n#if PYTHON_VERSION >= 0x300\nstatic struct PyModuleDef mdef_'
    )
    emit(values["module_identifier"])
    emit(
        " = {\n    PyModuleDef_HEAD_INIT,\n    NULL,                /* m_name, filled later */\n    NULL,                /* m_doc */\n    "
    )
    emit(values["module_def_size"])
    emit(
        ", /* m_size */\n    NULL,                /* m_methods */\n    NULL,                /* m_slots */\n    NULL,                /* m_traverse */\n    NULL,                /* m_clear */\n    NULL,                /* m_free */\n};\n#endif\n\n#if PYTHON_VERSION < 0x300\nstatic void onModuleFileValueRelease(void *v) {\n    if (orig_dunder_file_value != NULL) {\n        UPDATE_STRING_DICT0(\n            moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ",\n            (Nuitka_StringObject *)const_str_plain___file__,\n            orig_dunder_file_value\n        );\n    }\n}\n#endif\n\n/* The exported interface to CPython. On import of the module, this function\n * gets called. It has to have an exact function name, in cases it's a shared\n * library export.\n */\n\nextern struct Nuitka_MetaPathBasedLoaderEntry const *getLoaderEntry(char const *name);\n\nstatic PyObject *"
    )
    emit(values["module_dll_entry_point"])
    emit(
        "_phase2(PyObject *module) {\n    PyThreadState *tstate = PyThreadState_GET();\n\n    PyObject *result = module_code_"
    )
    emit(values["module_identifier"])
    emit("(tstate, module, getLoaderEntry(")
    emit(values["module_name_cstr"])
    emit(
        '));\n\n#if PYTHON_VERSION < 0x300\n    // Our "__file__" value will not be respected by CPython and one\n    // way we can avoid it, is by having a capsule type, that when\n    // it gets released, we are called and repair the value.\n\n    if (HAS_ERROR_OCCURRED(tstate) == false) {\n        orig_dunder_file_value = DICT_GET_ITEM_WITH_HASH_ERROR1(tstate, (PyObject *)moduledict_'
    )
    emit(values["module_identifier"])
    emit(
        ", const_str_plain___file__);\n\n        PyObject *fake_file_value = PyCObject_FromVoidPtr(NULL, onModuleFileValueRelease);\n\n        UPDATE_STRING_DICT1(\n            moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        ',\n            (Nuitka_StringObject *)const_str_plain___file__,\n            fake_file_value\n        );\n    }\n#else\n    if (result != NULL) {\n        // Make sure we undo the change of the "__file__" attribute during importing. We do not\n        // know how to achieve it for Python2 though. TODO: Find something for Python2 too.\n        orig_PyModule_Type_tp_setattro = PyModule_Type.tp_setattro;\n        PyModule_Type.tp_setattro = Nuitka_TopLevelModule_tp_setattro;\n\n        orig_dunder_file_value = DICT_GET_ITEM_WITH_HASH_ERROR1(tstate, (PyObject *)moduledict_'
    )
    emit(values["module_identifier"])
    emit(", const_str_plain___file__);\n    }\n#endif\n\n    return result;\n}\n\n#if ")
    emit(values["module_def_size"])
    emit(" >= 0\nstatic int ")
    emit(values["module_dll_entry_point"])
    emit("_slot(PyObject *module) {\n    PyObject *result = ")
    emit(values["module_dll_entry_point"])
    emit(
        "_phase2(module);\n\n    if (unlikely(result == NULL)) {\n        return 1;\n    } else {\n        return 0;\n    }\n}\n#endif\n\nNUITKA_MODULE_INIT_FUNCTION ("
    )
    emit(values["module_dll_entry_point"])
    emit(
        ')(void) {\n#if PYTHON_VERSION < 0x3c0\n    if (_Py_PackageContext != NULL) {\n        if (strcmp(module_full_name, _Py_PackageContext) != 0) {\n            module_full_name = strdup(_Py_PackageContext);\n        }\n    }\n#endif\n\n#if PYTHON_VERSION < 0x300\n    PyObject *module = Py_InitModule4(\n        module_full_name,        // Module Name\n        NULL,                    // No methods initially, all are added\n                                 // dynamically in actual module code only.\n        NULL,                    // No "__doc__" is initially set, as it could\n                                 // not contain NUL this way, added early in\n                                 // actual code.\n        NULL,                    // No self for modules, we don\'t use it.\n        PYTHON_API_VERSION\n    );\n#else\n    mdef_'
    )
    emit(values["module_identifier"])
    emit(".m_name = module_full_name;\n\n#if ")
    emit(values["module_def_size"])
    emit(" == -1\n    PyObject *module = PyModule_Create(&mdef_")
    emit(values["module_identifier"])
    emit(
        ");\n    CHECK_OBJECT(module);\n\n    {\n        NUITKA_MAY_BE_UNUSED bool res = Nuitka_SetModuleString(module_full_name, module);\n        assert(res != false);\n    }\n\n#endif\n#endif\n\n#if "
    )
    emit(values["module_def_size"])
    emit(
        " >= 0\n    static PyModuleDef_Slot _module_slots[] = {\n        {Py_mod_exec, (void *)"
    )
    emit(values["module_dll_entry_point"])
    emit("_slot},\n        {0, NULL}\n    };\n\n    mdef_")
    emit(values["module_identifier"])
    emit(".m_slots = _module_slots;\n\n    return PyModuleDef_Init(&mdef_")
    emit(values["module_identifier"])
    emit(");\n#elif PYTHON_VERSION >= 0x300\n    return ")
    emit(values["module_dll_entry_point"])
    emit("_phase2(module);\n#else\n    ")
    emit(values["module_dll_entry_point"])
    emit("_phase2(module);\n#endif\n}\n")


def _emit_039_template_module_exception_exit(emit, values):
    emit("module_exception_exit:\n\n#if _NUITKA_MODULE_MODE && ")
    emit(str(values["is_top"]))
    emit("\n{\nPyObject *module_name = GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(
        ', (Nuitka_StringObject *)const_str_plain___name__);\n\nif (module_name != NULL) {\nNuitka_DelModule(tstate, module_name);\n}\n}\n#endif\nPGO_onModuleExit("'
    )
    emit(values["module_identifier"])
    emit(
        '", false);\n\nRESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);\nreturn NULL;\n}'
    )


def _emit_039_template_module_exception_exit_readable(emit, values):
    emit("    module_exception_exit:\n\n#if _NUITKA_MODULE_MODE && ")
    emit(str(values["is_top"]))
    emit("\n    {\n        PyObject *module_name = GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(
        ', (Nuitka_StringObject *)const_str_plain___name__);\n\n        if (module_name != NULL) {\n            Nuitka_DelModule(tstate, module_name);\n        }\n    }\n#endif\n    PGO_onModuleExit("'
    )
    emit(values["module_identifier"])
    emit(
        '", false);\n\n    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);\n    return NULL;\n}'
    )


def _emit_040_template_module_no_exception_exit(emit, values):
    emit("}")


def _emit_040_template_module_no_exception_exit_readable(emit, values):
    emit("}")


def _emit_041_template_helper_impl_decl(emit, values):
    emit(
        '\n\n\n#include "nuitka/prelude.h"\n\nextern PyObject *callPythonFunction(PyObject *func, PyObject *const *args, int count);\n\n'
    )


def _emit_041_template_helper_impl_decl_readable(emit, values):
    emit(
        '// This file contains helper functions that are automatically created from\n// templates.\n\n#include "nuitka/prelude.h"\n\nextern PyObject *callPythonFunction(PyObject *func, PyObject *const *args, int count);\n\n'
    )


def _emit_042_template_header_guard(emit, values):
    emit("#ifndef ")
    emit(values["header_guard_name"])
    emit("\n#define ")
    emit(values["header_guard_name"])
    emit("\n\n")
    emit(values["header_body"])
    emit("\n#endif\n")


def _emit_042_template_header_guard_readable(emit, values):
    emit("#ifndef ")
    emit(values["header_guard_name"])
    emit("\n#define ")
    emit(values["header_guard_name"])
    emit("\n\n")
    emit(values["header_body"])
    emit("\n#endif\n")


def _emit_043_template_write_local_unclear_ref0(emit, values):
    emit("{\nPyObject *old = ")
    emit(values["identifier"])
    emit(";\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\nPy_XDECREF(old);\n}\n")


def _emit_043_template_write_local_unclear_ref0_readable(emit, values):
    emit("{\n    PyObject *old = ")
    emit(values["identifier"])
    emit(";\n    ")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\n    Py_XDECREF(old);\n}\n")


def _emit_044_template_write_local_unclear_ref1(emit, values):
    emit("{\nPyObject *old = ")
    emit(values["identifier"])
    emit(";\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\nPy_INCREF(")
    emit(values["identifier"])
    emit(");\nPy_XDECREF(old);\n}\n")


def _emit_044_template_write_local_unclear_ref1_readable(emit, values):
    emit("{\n    PyObject *old = ")
    emit(values["identifier"])
    emit(";\n    ")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\n    Py_INCREF(")
    emit(values["identifier"])
    emit(");\n    Py_XDECREF(old);\n}\n")


def _emit_045_template_write_local_empty_ref0(emit, values):
    emit("assert(")
    emit(values["identifier"])
    emit(" == NULL);\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";")


def _emit_045_template_write_local_empty_ref0_readable(emit, values):
    emit("assert(")
    emit(values["identifier"])
    emit(" == NULL);\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";")


def _emit_046_template_write_local_empty_ref1(emit, values):
    emit("assert(")
    emit(values["identifier"])
    emit(" == NULL);\nPy_INCREF(")
    emit(values["tmp_name"])
    emit(");\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";")


def _emit_046_template_write_local_empty_ref1_readable(emit, values):
    emit("assert(")
    emit(values["identifier"])
    emit(" == NULL);\nPy_INCREF(")
    emit(values["tmp_name"])
    emit(");\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";")


def _emit_047_template_write_local_clear_ref0(emit, values):
    emit("{\nPyObject *old = ")
    emit(values["identifier"])
    emit(";\nassert(old != NULL);\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\nPy_DECREF(old);\n}\n")


def _emit_047_template_write_local_clear_ref0_readable(emit, values):
    emit("{\n    PyObject *old = ")
    emit(values["identifier"])
    emit(";\n    assert(old != NULL);\n    ")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\n    Py_DECREF(old);\n}\n")


def _emit_048_template_write_local_inplace(emit, values):
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\n")


def _emit_048_template_write_local_inplace_readable(emit, values):
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\n")


def _emit_049_template_write_shared_inplace(emit, values):
    emit("Nuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_049_template_write_shared_inplace_readable(emit, values):
    emit("Nuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_050_template_write_local_clear_ref1(emit, values):
    emit("{\nPyObject *old = ")
    emit(values["identifier"])
    emit(";\nassert(old != NULL);\n")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\nPy_INCREF(")
    emit(values["identifier"])
    emit(");\nPy_DECREF(old);\n}\n")


def _emit_050_template_write_local_clear_ref1_readable(emit, values):
    emit("{\n    PyObject *old = ")
    emit(values["identifier"])
    emit(";\n    assert(old != NULL);\n    ")
    emit(values["identifier"])
    emit(" = ")
    emit(values["tmp_name"])
    emit(";\n    Py_INCREF(")
    emit(values["identifier"])
    emit(");\n    Py_DECREF(old);\n}\n")


def _emit_051_template_write_shared_unclear_ref0(emit, values):
    emit("{\nPyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\nPy_XDECREF(old);\n}\n")


def _emit_051_template_write_shared_unclear_ref0_readable(emit, values):
    emit("{\n    PyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\n    Nuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n    Py_XDECREF(old);\n}\n")


def _emit_052_template_write_shared_unclear_ref1(emit, values):
    emit("{\nPyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\nPy_INCREF(")
    emit(values["tmp_name"])
    emit(");\nPy_XDECREF(old);\n}\n")


def _emit_052_template_write_shared_unclear_ref1_readable(emit, values):
    emit("{\n    PyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\n    Nuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n    Py_INCREF(")
    emit(values["tmp_name"])
    emit(");\n    Py_XDECREF(old);\n}\n")


def _emit_053_template_write_shared_clear_ref0(emit, values):
    emit("assert(Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(") == NULL);\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_053_template_write_shared_clear_ref0_readable(emit, values):
    emit("assert(Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(") == NULL);\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_054_template_write_shared_clear_ref1(emit, values):
    emit("assert(Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(") == NULL);\nPy_INCREF(")
    emit(values["tmp_name"])
    emit(");\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_054_template_write_shared_clear_ref1_readable(emit, values):
    emit("assert(Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(") == NULL);\nPy_INCREF(")
    emit(values["tmp_name"])
    emit(");\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_055_template_del_local_tolerant(emit, values):
    emit("Py_XDECREF(")
    emit(values["identifier"])
    emit(");\n")
    emit(values["identifier"])
    emit(" = NULL;\n")


def _emit_055_template_del_local_tolerant_readable(emit, values):
    emit("Py_XDECREF(")
    emit(values["identifier"])
    emit(");\n")
    emit(values["identifier"])
    emit(" = NULL;\n")


def _emit_056_template_del_shared_tolerant(emit, values):
    emit("{\nPyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", NULL);\nPy_XDECREF(old);\n}\n")


def _emit_056_template_del_shared_tolerant_readable(emit, values):
    emit("{\n    PyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\n    Nuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", NULL);\n    Py_XDECREF(old);\n}\n")


def _emit_057_template_del_local_intolerant(emit, values):
    emit(values["result"])
    emit(" = ")
    emit(values["identifier"])
    emit(" != NULL;\nif (likely(")
    emit(values["result"])
    emit(")) {\nPy_DECREF(")
    emit(values["identifier"])
    emit(");\n")
    emit(values["identifier"])
    emit(" = NULL;\n}\n")


def _emit_057_template_del_local_intolerant_readable(emit, values):
    emit(values["result"])
    emit(" = ")
    emit(values["identifier"])
    emit(" != NULL;\nif (likely(")
    emit(values["result"])
    emit(")) {\n    Py_DECREF(")
    emit(values["identifier"])
    emit(");\n    ")
    emit(values["identifier"])
    emit(" = NULL;\n}\n")


def _emit_058_template_del_shared_intolerant(emit, values):
    emit("{\nPyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", NULL);\nPy_XDECREF(old);\n\n")
    emit(values["result"])
    emit(" = old != NULL;\n}\n")


def _emit_058_template_del_shared_intolerant_readable(emit, values):
    emit("{\n    PyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\n    Nuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", NULL);\n    Py_XDECREF(old);\n\n    ")
    emit(values["result"])
    emit(" = old != NULL;\n}\n")


def _emit_059_template_del_local_known(emit, values):
    emit("CHECK_OBJECT(")
    emit(values["identifier"])
    emit(");\nPy_DECREF(")
    emit(values["identifier"])
    emit(");\n")
    emit(values["identifier"])
    emit(" = NULL;\n")


def _emit_059_template_del_local_known_readable(emit, values):
    emit("CHECK_OBJECT(")
    emit(values["identifier"])
    emit(");\nPy_DECREF(")
    emit(values["identifier"])
    emit(");\n")
    emit(values["identifier"])
    emit(" = NULL;\n")


def _emit_060_template_del_shared_known(emit, values):
    emit("{\nPyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\nNuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", NULL);\n\nCHECK_OBJECT(old);\nPy_DECREF(old);\n}\n")


def _emit_060_template_del_shared_known_readable(emit, values):
    emit("{\n    PyObject *old = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\n    Nuitka_Cell_SET(")
    emit(values["identifier"])
    emit(", NULL);\n\n    CHECK_OBJECT(old);\n    Py_DECREF(old);\n}\n")


def _emit_061_template_release_object_unclear(emit, values):
    emit("Py_XDECREF(")
    emit(values["identifier"])
    emit(");")


def _emit_061_template_release_object_unclear_readable(emit, values):
    emit("Py_XDECREF(")
    emit(values["identifier"])
    emit(");")


def _emit_062_template_release_object_clear(emit, values):
    emit("CHECK_OBJECT(")
    emit(values["identifier"])
    emit(");\nPy_DECREF(")
    emit(values["identifier"])
    emit(");")


def _emit_062_template_release_object_clear_readable(emit, values):
    emit("CHECK_OBJECT(")
    emit(values["identifier"])
    emit(");\nPy_DECREF(")
    emit(values["identifier"])
    emit(");")


def _emit_063_template_read_shared_known(emit, values):
    emit(values["tmp_name"])
    emit(" = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\n")


def _emit_063_template_read_shared_known_readable(emit, values):
    emit(values["tmp_name"])
    emit(" = Nuitka_Cell_GET(")
    emit(values["identifier"])
    emit(");\n")


def _emit_064_template_read_mvar_unclear(emit, values):
    emit(values["tmp_name"])
    emit(" = LOOKUP_MODULE_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n")


def _emit_064_template_read_mvar_unclear_readable(emit, values):
    emit(values["tmp_name"])
    emit(" = LOOKUP_MODULE_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n")


def _emit_065_template_read_locals_dict_with_fallback(emit, values):
    emit(values["to_name"])
    emit(" = ")
    emit(values["dict_get_item"])
    emit("(tstate, ")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n\nif (")
    emit(values["to_name"])
    emit(" == NULL) {\n")
    emit(values["fallback"])
    emit("\n}\n")


def _emit_065_template_read_locals_dict_with_fallback_readable(emit, values):
    emit(values["to_name"])
    emit(" = ")
    emit(values["dict_get_item"])
    emit("(tstate, ")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n\nif (")
    emit(values["to_name"])
    emit(" == NULL) {\n")
    emit(values["fallback"])
    emit("\n}\n")


def _emit_066_template_read_locals_dict_without_fallback(emit, values):
    emit(values["to_name"])
    emit(" = DICT_GET_ITEM0(tstate, ")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n")


def _emit_066_template_read_locals_dict_without_fallback_readable(emit, values):
    emit(values["to_name"])
    emit(" = DICT_GET_ITEM0(tstate, ")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n")


def _emit_067_template_read_locals_mapping_with_fallback_no_ref(emit, values):
    emit(values["to_name"])
    emit(" = PyObject_GetItem(")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n\nif (")
    emit(values["to_name"])
    emit(" == NULL) {\nif (CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {\n")
    emit(values["fallback"])
    emit("\nPy_INCREF(")
    emit(values["to_name"])
    emit(");\n} else {\nFETCH_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\ngoto ")
    emit(values["exception_exit"])
    emit(";\n}\n}\n")


def _emit_067_template_read_locals_mapping_with_fallback_no_ref_readable(emit, values):
    emit(values["to_name"])
    emit(" = PyObject_GetItem(")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n\nif (")
    emit(values["to_name"])
    emit(" == NULL) {\n    if (CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {\n")
    emit(values["fallback"])
    emit("\n        Py_INCREF(")
    emit(values["to_name"])
    emit(");\n    } else {\n        FETCH_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n        goto ")
    emit(values["exception_exit"])
    emit(";\n    }\n}\n")


def _emit_068_template_read_locals_mapping_with_fallback_ref(emit, values):
    emit(values["to_name"])
    emit(" = PyObject_GetItem(")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n\nif (")
    emit(values["to_name"])
    emit(" == NULL) {\nif (CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {\n")
    emit(values["fallback"])
    emit("\n} else {\nFETCH_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\ngoto ")
    emit(values["exception_exit"])
    emit(";\n}\n}\n")


def _emit_068_template_read_locals_mapping_with_fallback_ref_readable(emit, values):
    emit(values["to_name"])
    emit(" = PyObject_GetItem(")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n\nif (")
    emit(values["to_name"])
    emit(" == NULL) {\n    if (CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {\n")
    emit(values["fallback"])
    emit("\n    } else {\n        FETCH_ERROR_OCCURRED_STATE(tstate, &")
    emit(values["exception_state_name"])
    emit(");\n        goto ")
    emit(values["exception_exit"])
    emit(";\n    }\n}\n")


def _emit_069_template_read_locals_mapping_without_fallback(emit, values):
    emit(values["to_name"])
    emit(" = PyObject_GetItem(")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n")


def _emit_069_template_read_locals_mapping_without_fallback_readable(emit, values):
    emit(values["to_name"])
    emit(" = PyObject_GetItem(")
    emit(values["locals_dict"])
    emit(", ")
    emit(values["var_name"])
    emit(");\n")


def _emit_070_template_del_global_unclear(emit, values):
    emit(values["result"])
    emit(" = DICT_REMOVE_ITEM((PyObject *)moduledict_")
    emit(values["module_identifier"])
    emit(", ")
    emit(values["var_name"])
    emit(");\nif (")
    emit(values["result"])
    emit(" == false) CLEAR_ERROR_OCCURRED(tstate);\n")


def _emit_070_template_del_global_unclear_readable(emit, values):
    emit(values["result"])
    emit(" = DICT_REMOVE_ITEM((PyObject *)moduledict_")
    emit(values["module_identifier"])
    emit(", ")
    emit(values["var_name"])
    emit(");\nif (")
    emit(values["result"])
    emit(" == false) CLEAR_ERROR_OCCURRED(tstate);\n")


def _emit_071_template_del_global_known(emit, values):
    emit("if (DICT_REMOVE_ITEM((PyObject *)moduledict_")
    emit(values["module_identifier"])
    emit(", ")
    emit(values["var_name"])
    emit(") == false) {\nCLEAR_ERROR_OCCURRED(tstate);\n}\n")


def _emit_071_template_del_global_known_readable(emit, values):
    emit("if (DICT_REMOVE_ITEM((PyObject *)moduledict_")
    emit(values["module_identifier"])
    emit(", ")
    emit(values["var_name"])
    emit(") == false) {\n    CLEAR_ERROR_OCCURRED(tstate);\n}\n")


def _emit_072_template_update_locals_dict_value(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\nPyObject *value;\n")
    emit(values["access_code"])
    emit("\n\nUPDATE_STRING_DICT0((PyDictObject *)")
    emit(values["dict_name"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(", value);\n} else {\nif (DICT_REMOVE_ITEM(")
    emit(values["dict_name"])
    emit(", ")
    emit(values["var_name"])
    emit(") == false) {\nCLEAR_ERROR_OCCURRED(tstate);\n}\n}\n")


def _emit_072_template_update_locals_dict_value_readable(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\n    PyObject *value;\n")
    emit(values["access_code"])
    emit("\n\n    UPDATE_STRING_DICT0((PyDictObject *)")
    emit(values["dict_name"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(", value);\n} else {\n    if (DICT_REMOVE_ITEM(")
    emit(values["dict_name"])
    emit(", ")
    emit(values["var_name"])
    emit(") == false) {\n        CLEAR_ERROR_OCCURRED(tstate);\n    }\n}\n")


def _emit_073_template_set_locals_dict_value(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\nPyObject *value;\n")
    emit(values["access_code"])
    emit("\n\nint res = PyDict_SetItem(\n")
    emit(values["dict_name"])
    emit(",\n")
    emit(values["var_name"])
    emit(",\nvalue\n);\n\nassert(res == 0);\n}\n")


def _emit_073_template_set_locals_dict_value_readable(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\n    PyObject *value;\n")
    emit(values["access_code"])
    emit("\n\n    int res = PyDict_SetItem(\n        ")
    emit(values["dict_name"])
    emit(",\n        ")
    emit(values["var_name"])
    emit(",\n        value\n    );\n\n    assert(res == 0);\n}\n")


def _emit_074_template_update_locals_mapping_value(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\nPyObject *value;\n")
    emit(values["access_code"])
    emit("\n\nint res = PyObject_SetItem(\n")
    emit(values["mapping_name"])
    emit(",\n")
    emit(values["var_name"])
    emit(",\nvalue\n);\n\n")
    emit(values["tmp_name"])
    emit(" = res == 0;\n} else {\nPyObject *test_value = PyObject_GetItem(\n")
    emit(values["mapping_name"])
    emit(",\n")
    emit(values["var_name"])
    emit(
        "\n);\n\nif (test_value) {\nPy_DECREF(test_value);\n\nint res = PyObject_DelItem(\n"
    )
    emit(values["mapping_name"])
    emit(",\n")
    emit(values["var_name"])
    emit("\n);\n\n")
    emit(values["tmp_name"])
    emit(" = res == 0;\n} else {\nCLEAR_ERROR_OCCURRED(tstate);\n")
    emit(values["tmp_name"])
    emit(" = true;\n}\n}\n")


def _emit_074_template_update_locals_mapping_value_readable(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\n    PyObject *value;\n")
    emit(values["access_code"])
    emit("\n\n    int res = PyObject_SetItem(\n        ")
    emit(values["mapping_name"])
    emit(",\n        ")
    emit(values["var_name"])
    emit(",\n        value\n    );\n\n    ")
    emit(values["tmp_name"])
    emit(
        " = res == 0;\n} else {\n    PyObject *test_value = PyObject_GetItem(\n        "
    )
    emit(values["mapping_name"])
    emit(",\n        ")
    emit(values["var_name"])
    emit(
        "\n    );\n\n    if (test_value) {\n        Py_DECREF(test_value);\n\n        int res = PyObject_DelItem(\n            "
    )
    emit(values["mapping_name"])
    emit(",\n            ")
    emit(values["var_name"])
    emit("\n        );\n\n        ")
    emit(values["tmp_name"])
    emit(" = res == 0;\n    } else {\n        CLEAR_ERROR_OCCURRED(tstate);\n        ")
    emit(values["tmp_name"])
    emit(" = true;\n    }\n}\n")


def _emit_075_template_set_locals_mapping_value(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\nPyObject *value;\n")
    emit(values["access_code"])
    emit("\n\n")
    emit(values["tmp_name"])
    emit(" = SET_SUBSCRIPT(\ntstate,\n")
    emit(values["mapping_name"])
    emit(",\n")
    emit(values["var_name"])
    emit(",\nvalue\n);\n} else {\n")
    emit(values["tmp_name"])
    emit(" = true;\n}\n")


def _emit_075_template_set_locals_mapping_value_readable(emit, values):
    emit("if (")
    emit(values["test_code"])
    emit(") {\n    PyObject *value;\n")
    emit(values["access_code"])
    emit("\n\n    ")
    emit(values["tmp_name"])
    emit(" = SET_SUBSCRIPT(\n        tstate,\n        ")
    emit(values["mapping_name"])
    emit(",\n        ")
    emit(values["var_name"])
    emit(",\n        value\n    );\n} else {\n    ")
    emit(values["tmp_name"])
    emit(" = true;\n}\n")


def _emit_076_template_module_variable_accessor_function(emit, values):
    emit("static PyObject *")
    emit(values["accessor_function_name"])
    emit("(PyThreadState *tstate) {\n#if ")
    emit(values["caching"])
    emit(
        "\nPyObject *result;\n\n#if PYTHON_VERSION < 0x3b0\nstatic uint64_t dict_version = 0;\nstatic PyObject *cache_value = NULL;\n\nif (moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        "->ma_version_tag == dict_version) {\nCHECK_OBJECT_X(cache_value);\nresult = cache_value;\n} else {\ndict_version = moduledict_"
    )
    emit(values["module_identifier"])
    emit("->ma_version_tag;\n\nresult = GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(
        ");\ncache_value = result;\n}\n#else\nstatic uint32_t dict_keys_version = 0xFFFFFFFF;\nstatic Py_ssize_t cache_dk_index = 0;\n\nPyDictKeysObject *dk = moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        "->ma_keys;\nif (likely(DK_IS_UNICODE(dk))) {\n\n#if PYTHON_VERSION >= 0x3c0\nuint32_t current_dk_version = _Nuitka_PyDictKeys_GetVersionForCurrentState(tstate->interp, dk);\n#else\nuint32_t current_dk_version = _Nuitka_PyDictKeys_GetVersionForCurrentState(dk);\n#endif\n\nif (current_dk_version != dict_keys_version) {\ndict_keys_version = current_dk_version;\nPy_hash_t hash = Nuitka_Py_unicode_get_hash("
    )
    emit(values["var_name"])
    emit(
        ");\nassert(hash != -1);\n\ncache_dk_index = Nuitka_Py_unicodekeys_lookup_unicode(dk, "
    )
    emit(values["var_name"])
    emit(
        ", hash);\n}\n\nif (cache_dk_index >= 0) {\nassert(dk->dk_kind != DICT_KEYS_SPLIT);\n\nPyDictUnicodeEntry *entries = DK_UNICODE_ENTRIES(dk);\n\nresult = entries[cache_dk_index].me_value;\n\nif (unlikely(result == NULL)) {\nPy_hash_t hash = Nuitka_Py_unicode_get_hash("
    )
    emit(values["var_name"])
    emit(
        ");\nassert(hash != -1);\n\ncache_dk_index = Nuitka_Py_unicodekeys_lookup_unicode(dk, "
    )
    emit(values["var_name"])
    emit(
        ", hash);\n\nif (cache_dk_index >= 0) {\nresult = entries[cache_dk_index].me_value;\n}\n}\n} else {\nresult = NULL;\n}\n} else {\nresult = GET_STRING_DICT_VALUE(moduledict_"
    )
    emit(values["module_identifier"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(");\n}\n#endif\n\n#else\nPyObject *result = GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(
        ");\n#endif\n\nif (unlikely(result == NULL)) {\nresult = GET_STRING_DICT_VALUE(dict_builtin, (Nuitka_StringObject *)"
    )
    emit(values["var_name"])
    emit(");\n}\n\nreturn result;\n}\n")


def _emit_076_template_module_variable_accessor_function_readable(emit, values):
    emit("static PyObject *")
    emit(values["accessor_function_name"])
    emit("(PyThreadState *tstate) {\n#if ")
    emit(values["caching"])
    emit(
        "\n    PyObject *result;\n\n#if PYTHON_VERSION < 0x3b0\n    static uint64_t dict_version = 0;\n    static PyObject *cache_value = NULL;\n\n    if (moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        "->ma_version_tag == dict_version) {\n        CHECK_OBJECT_X(cache_value);\n        result = cache_value;\n    } else {\n        dict_version = moduledict_"
    )
    emit(values["module_identifier"])
    emit("->ma_version_tag;\n\n        result = GET_STRING_DICT_VALUE(moduledict_")
    emit(values["module_identifier"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(
        ");\n        cache_value = result;\n    }\n#else\n    static uint32_t dict_keys_version = 0xFFFFFFFF;\n    static Py_ssize_t cache_dk_index = 0;\n\n    PyDictKeysObject *dk = moduledict_"
    )
    emit(values["module_identifier"])
    emit(
        "->ma_keys;\n    if (likely(DK_IS_UNICODE(dk))) {\n\n#if PYTHON_VERSION >= 0x3c0\n        uint32_t current_dk_version = _Nuitka_PyDictKeys_GetVersionForCurrentState(tstate->interp, dk);\n#else\n        uint32_t current_dk_version = _Nuitka_PyDictKeys_GetVersionForCurrentState(dk);\n#endif\n\n        if (current_dk_version != dict_keys_version) {\n            dict_keys_version = current_dk_version;\n            Py_hash_t hash = Nuitka_Py_unicode_get_hash("
    )
    emit(values["var_name"])
    emit(
        ");\n            assert(hash != -1);\n\n            cache_dk_index = Nuitka_Py_unicodekeys_lookup_unicode(dk, "
    )
    emit(values["var_name"])
    emit(
        ", hash);\n        }\n\n        if (cache_dk_index >= 0) {\n            assert(dk->dk_kind != DICT_KEYS_SPLIT);\n\n            PyDictUnicodeEntry *entries = DK_UNICODE_ENTRIES(dk);\n\n            result = entries[cache_dk_index].me_value;\n\n            if (unlikely(result == NULL)) {\n                Py_hash_t hash = Nuitka_Py_unicode_get_hash("
    )
    emit(values["var_name"])
    emit(
        ");\n                assert(hash != -1);\n\n                cache_dk_index = Nuitka_Py_unicodekeys_lookup_unicode(dk, "
    )
    emit(values["var_name"])
    emit(
        ", hash);\n\n                if (cache_dk_index >= 0) {\n                    result = entries[cache_dk_index].me_value;\n                }\n            }\n        } else {\n            result = NULL;\n        }\n    } else {\n        result = GET_STRING_DICT_VALUE(moduledict_"
    )
    emit(values["module_identifier"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(
        ");\n    }\n#endif\n\n#else\n    PyObject *result = GET_STRING_DICT_VALUE(moduledict_"
    )
    emit(values["module_identifier"])
    emit(", (Nuitka_StringObject *)")
    emit(values["var_name"])
    emit(
        ");\n#endif\n\n    if (unlikely(result == NULL)) {\n        result = GET_STRING_DICT_VALUE(dict_builtin, (Nuitka_StringObject *)"
    )
    emit(values["var_name"])
    emit(");\n    }\n\n    return result;\n}\n")


def _emit_077_template_write_py_cell_inplace(emit, values):
    emit("PyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_077_template_write_py_cell_inplace_readable(emit, values):
    emit("PyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n")


def _emit_078_template_write_py_cell_unclear_ref0(emit, values):
    emit("{\nPyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\nPyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\nPy_XDECREF(old);\n}\n")


def _emit_078_template_write_py_cell_unclear_ref0_readable(emit, values):
    emit("{\n    PyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\n    PyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n    Py_XDECREF(old);\n}\n")


def _emit_079_template_write_py_cell_unclear_ref1(emit, values):
    emit("{\nPyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\nPyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\nPy_INCREF(")
    emit(values["tmp_name"])
    emit(");\nPy_XDECREF(old);\n}\n")


def _emit_079_template_write_py_cell_unclear_ref1_readable(emit, values):
    emit("{\n    PyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\n    PyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", ")
    emit(values["tmp_name"])
    emit(");\n    Py_INCREF(")
    emit(values["tmp_name"])
    emit(");\n    Py_XDECREF(old);\n}\n")


def _emit_080_template_del_py_cell_tolerant(emit, values):
    emit("{\nPyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\nPyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", NULL);\nPy_XDECREF(old);\n}\n")


def _emit_080_template_del_py_cell_tolerant_readable(emit, values):
    emit("{\n    PyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\n    PyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", NULL);\n    Py_XDECREF(old);\n}\n")


def _emit_081_template_del_py_cell_intolerant(emit, values):
    emit("{\nPyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\nPyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", NULL);\nPy_XDECREF(old);\n\n")
    emit(values["result"])
    emit(" = old != NULL;\n}\n")


def _emit_081_template_del_py_cell_intolerant_readable(emit, values):
    emit("{\n    PyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\n    PyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", NULL);\n    Py_XDECREF(old);\n\n    ")
    emit(values["result"])
    emit(" = old != NULL;\n}\n")


def _emit_082_template_del_py_cell_known(emit, values):
    emit("{\nPyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\nPyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", NULL);\n\nCHECK_OBJECT(old);\nPy_DECREF(old);\n}\n")


def _emit_082_template_del_py_cell_known_readable(emit, values):
    emit("{\n    PyObject *old = PyCell_GET((PyObject *)")
    emit(values["identifier"])
    emit(");\n    PyCell_SET((PyObject *)")
    emit(values["identifier"])
    emit(", NULL);\n\n    CHECK_OBJECT(old);\n    Py_DECREF(old);\n}\n")


template_infos = {
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_exception_exit": (
        "fdfee2c9f7bccad9a853084c86a456e406070ec5757624d1a4c997a6f4a64992",
        ("exception_state_name", "function_cleanup"),
        _emit_003_template_asyncgen_exception_exit,
        _emit_003_template_asyncgen_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_no_exception_exit": (
        "9ad77684635c02f14f189cffc115a6434f5dbce53b39573feca479db33741696",
        ("function_cleanup",),
        _emit_004_template_asyncgen_no_exception_exit,
        _emit_004_template_asyncgen_no_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_object_body": (
        "0ce04e63a80c615fff789a587fc892167450e0c4e95c3ea1a9bd04d400f32e4f",
        (
            "asyncgen_creation_args",
            "asyncgen_exit",
            "asyncgen_maker_identifier",
            "asyncgen_module",
            "asyncgen_name_obj",
            "asyncgen_qualname_obj",
            "closure_count",
            "closure_name",
            "code_identifier",
            "function_body",
            "function_dispatch",
            "function_identifier",
            "function_local_types",
            "function_var_inits",
            "has_heap_declaration",
            "heap_declaration",
        ),
        _emit_001_template_asyncgen_object_body,
        _emit_001_template_asyncgen_object_body_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_object_maker_template": (
        "af9933f64c3277bc73d7422d7e7235a8f1d36b6dfdf2acb93db9cb20a939bebb",
        ("asyncgen_creation_args", "asyncgen_maker_identifier"),
        _emit_000_template_asyncgen_object_maker_template,
        _emit_000_template_asyncgen_object_maker_template_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_return_exit": (
        "0fc8594ba021dfbeaa4188a2a278130d668b9c4380b1d16ff16186f3204d121a",
        (),
        _emit_005_template_asyncgen_return_exit,
        _emit_005_template_asyncgen_return_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_make_asyncgen": (
        "4b09731eaa7056d9f36803f846959e6ce25beb4a7b7a339f8610c22387f56218",
        ("args", "asyncgen_maker_identifier", "closure_copy", "to_name"),
        _emit_002_template_make_asyncgen,
        _emit_002_template_make_asyncgen_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesConstants.template_constants_reading": (
        "7729d73fd61b541277e3d8f59c670ddd4aedf197c29abfe5a013a6495a93f9f4",
        (
            "global_constants_blob_symbol_name",
            "global_constants_count",
            "metadata_values",
            "nuitka_version_level",
            "nuitka_version_major",
            "nuitka_version_micro",
            "nuitka_version_minor",
            "sys_base_exec_prefix",
            "sys_base_prefix",
            "sys_exec_prefix",
            "sys_executable",
            "sys_prefix",
            "use_direct_constant_blobs",
        ),
        _emit_006_template_constants_reading,
        _emit_006_template_constants_reading_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_exception_exit": (
        "7664a919ec522a97beb762c44ef5fe22c93234801469b476a8d83860068fe7bd",
        ("exception_state_name", "function_cleanup"),
        _emit_010_template_coroutine_exception_exit,
        _emit_010_template_coroutine_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_no_exception_exit": (
        "9d03b9ebe9900efec98234b09b34f09c119c4b3b1e3cc8e5558b6bb243f52970",
        ("function_cleanup",),
        _emit_011_template_coroutine_no_exception_exit,
        _emit_011_template_coroutine_no_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_object_body": (
        "ee293a333a6815606344706122d3c7430750a49d17068ba0839790701347582a",
        (
            "closure_count",
            "closure_name",
            "code_identifier",
            "coroutine_creation_args",
            "coroutine_exit",
            "coroutine_maker_identifier",
            "coroutine_module",
            "coroutine_name_obj",
            "coroutine_qualname_obj",
            "function_body",
            "function_dispatch",
            "function_identifier",
            "function_local_types",
            "function_var_inits",
            "has_heap_declaration",
            "heap_declaration",
        ),
        _emit_008_template_coroutine_object_body,
        _emit_008_template_coroutine_object_body_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_object_maker": (
        "d9e27395be5157a8e15227a2d458f9466a7f7bc8ded156a9331cf0be256fd2c5",
        ("coroutine_creation_args", "coroutine_maker_identifier"),
        _emit_007_template_coroutine_object_maker,
        _emit_007_template_coroutine_object_maker_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_return_exit": (
        "552fe90a12d730bf51d0d4b493946a15da05c4c251540c97f0acb17583089587",
        ("return_value",),
        _emit_012_template_coroutine_return_exit,
        _emit_012_template_coroutine_return_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_make_coroutine": (
        "9405f5447ee6ee02231e05f690b3ee8134c21c065085595ba553b5bd502edae1",
        ("args", "closure_copy", "coroutine_maker_identifier", "to_name"),
        _emit_009_template_make_coroutine,
        _emit_009_template_make_coroutine_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_catch_exception": (
        "5cd3c7520240314c1b45cd9b5ea038aac3fc725eab596a8edf360d871eff8a2d",
        (
            "condition",
            "exception_exit",
            "exception_state_name",
            "line_number_code",
            "release_temps",
            "var_description_code",
        ),
        _emit_015_template_error_catch_exception,
        _emit_015_template_error_catch_exception_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_catch_fetched_exception": (
        "e91473cc9899908ac56d77a2c673496a82a700de12ebb2c3bd39fdbcfdc8fe51",
        (
            "condition",
            "exception_exit",
            "exception_state_name",
            "line_number_code",
            "release_temps",
            "var_description_code",
        ),
        _emit_014_template_error_catch_fetched_exception,
        _emit_014_template_error_catch_fetched_exception_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_format_name_error_exception": (
        "d21d6d44207ff6637e0b9edbee7027ed766a7d1f3e44f9ffd54af1875f1bc07d",
        (
            "condition",
            "exception_exit",
            "exception_state_name",
            "line_number_code",
            "raise_name_error_helper",
            "release_temps",
            "var_description_code",
            "variable_name",
        ),
        _emit_017_template_error_format_name_error_exception,
        _emit_017_template_error_format_name_error_exception_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_format_string_exception": (
        "303553f8e179c9ced0148190114ea69e79ebf98447ebc404f674660bb56ce770",
        (
            "condition",
            "exception_exit",
            "line_number_code",
            "release_temps",
            "set_exception",
            "var_description_code",
        ),
        _emit_016_template_error_format_string_exception,
        _emit_016_template_error_format_string_exception_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_publish_exception_to_handler": (
        "03d8dbaab51f6f10b340bb432c93883c6b26742c68d8d681f6a330d5b94cff65",
        (
            "frame_identifier",
            "keeper_exception_state_name",
            "keeper_lineno",
            "tb_making",
        ),
        _emit_013_template_publish_exception_to_handler,
        _emit_013_template_publish_exception_to_handler_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFrames.template_frame_attach_locals": (
        "69b906d206fc8eb6abbce373d76189f2b4c08b93359b8abc976aca51aabd8be0",
        ("frame_identifier", "frame_variable_refs", "type_description"),
        _emit_018_template_frame_attach_locals,
        _emit_018_template_frame_attach_locals_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFrames.template_frame_guard_generator_return_handler": (
        "423327429dc8ae7813f026afbe6bbe50877d81a49fd35e5fa40cfbda7e1c3c56",
        ("context_identifier", "frame_return_exit", "return_exit"),
        _emit_019_template_frame_guard_generator_return_handler,
        _emit_019_template_frame_guard_generator_return_handler_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_body": (
        "2d7cb5291aae792b27e74052c346322d2afc5264235acd0487e128235c19ff5b",
        (
            "function_body",
            "function_exit",
            "function_identifier",
            "function_locals",
            "parameter_objects_decl",
        ),
        _emit_024_template_function_body,
        _emit_024_template_function_body_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_direct_declaration": (
        "5fd5c08bee3a373a51d5e622b3f64fe6b2065ef75e0d37382a73eb3c944dac02",
        ("direct_call_arg_spec", "file_scope", "function_identifier"),
        _emit_021_template_function_direct_declaration,
        _emit_021_template_function_direct_declaration_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_exception_exit": (
        "79a829dcd03d3765d6d3119424156540102d4dd8edbc75d51bdb46839f972450",
        ("exception_state_name", "function_cleanup"),
        _emit_025_template_function_exception_exit,
        _emit_025_template_function_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_make_declaration": (
        "ebb127bc1a6bc70379b85971b4b8c5ac16ae8b34605a199cf15f075649475858",
        ("function_creation_args", "function_identifier"),
        _emit_020_template_function_make_declaration,
        _emit_020_template_function_make_declaration_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_return_exit": (
        "629e15e23d40f87a4fa746d0c00ce0ce6d5a774265bf8dd6ff68f9b8da328e03",
        ("function_cleanup",),
        _emit_026_template_function_return_exit,
        _emit_026_template_function_return_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_make_function": (
        "34110e3ef76b33413f79ac563ae66882d50fe418730fc4ba6eae28a900bd1dff",
        ("args", "closure_copy", "function_maker_identifier", "to_name"),
        _emit_023_template_make_function,
        _emit_023_template_make_function_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_maker_function_body": (
        "8803e28f801aceac25ab81dd23e2881909c43b7aa9ebabb79d396606df9c2c0b",
        (
            "annotations",
            "closure_count",
            "closure_name",
            "code_identifier",
            "constant_return_code",
            "defaults",
            "function_creation_args",
            "function_doc",
            "function_impl_identifier",
            "function_maker_identifier",
            "function_name_obj",
            "function_qualname_obj",
            "kw_defaults",
            "module_identifier",
            "type_params",
        ),
        _emit_022_template_maker_function_body,
        _emit_022_template_maker_function_body_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_context_body_template": (
        "9ec657d601dcab36c0062329c6e2a59683f3b4c162af0d2edfa6341915b1e323",
        (
            "closure_count",
            "closure_name",
            "code_identifier",
            "function_body",
            "function_dispatch",
            "function_identifier",
            "function_local_types",
            "function_var_inits",
            "generator_creation_args",
            "generator_exit",
            "generator_maker_identifier",
            "generator_module",
            "generator_name_obj",
            "generator_qualname_obj",
            "has_heap_declaration",
            "heap_declaration",
        ),
        _emit_028_template_generator_context_body_template,
        _emit_028_template_generator_context_body_template_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_context_maker_decl": (
        "4841f0b6421846e27390df65257fe96abf7e40d49834810445261474ca913234",
        ("generator_creation_args", "generator_maker_identifier"),
        _emit_027_template_generator_context_maker_decl,
        _emit_027_template_generator_context_maker_decl_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_exception_exit": (
        "430ad39a236f3d3c0e4c34d54d8a77b3e62dd83968284b2adfe52cd12a2f9b91",
        ("exception_state_name", "function_cleanup"),
        _emit_031_template_generator_exception_exit,
        _emit_031_template_generator_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_no_exception_exit": (
        "87995cc27186872b078370fc4dfba2b182d6a19360233f080640b3061ce0c4ed",
        ("function_cleanup",),
        _emit_032_template_generator_no_exception_exit,
        _emit_032_template_generator_no_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_return_exit": (
        "f06ad373e40a6038b3e2569fc28ca1ab262ef37815156fd2e0c6fbe6f3589b60",
        ("function_cleanup", "return_value"),
        _emit_033_template_generator_return_exit,
        _emit_033_template_generator_return_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_make_empty_generator": (
        "b99cf335642cd23e7ce6dd8de5d28c547e4dce566169ba9a137990b9c53fc676",
        (
            "closure_copy",
            "closure_count",
            "closure_name",
            "code_identifier",
            "generator_module",
            "generator_name_obj",
            "generator_qualname_obj",
            "to_name",
        ),
        _emit_030_template_make_empty_generator,
        _emit_030_template_make_empty_generator_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_make_generator": (
        "ef18f2f53fae77d87d02568d173349aab047ab21aeba825b26ab6473ff665c7e",
        ("args", "closure_copy", "generator_maker_identifier", "to_name"),
        _emit_029_template_make_generator,
        _emit_029_template_make_generator_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesIterators.template_loop_break_next": (
        "92add9ba69be2a694b88e75c06b386542d271d43c9a21dd11bd2f47516b8eb20",
        (
            "break_indicator_code",
            "break_target",
            "exception_state_name",
            "exception_target",
            "line_number_code",
            "release_temps",
            "to_name",
            "var_description_code",
        ),
        _emit_034_template_loop_break_next,
        _emit_034_template_loop_break_next_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesLoader.template_metapath_loader_body": (
        "1f90f9fd9849405949fd86dc4397208da06b0b8f3239f4c751e05ffa6af3e7ce",
        (
            "bytecode_count",
            "entry_count",
            "frozen_modules",
            "metapath_loader_inittab",
            "metapath_module_decls",
        ),
        _emit_035_template_metapath_loader_body,
        _emit_035_template_metapath_loader_body_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_global_copyright": (
        "16bd6ceb6d060356654eb1bf718a9e1b04d44ad1a3ed96d41f30c0346de14001",
        ("module_identifier", "version", "year"),
        _emit_036_template_global_copyright,
        _emit_036_template_global_copyright_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_header_guard": (
        "1fffdd3b3c781d73b532acd2667d4c3701bf8da886bed3bc5be2a948e01f3008",
        ("header_body", "header_guard_name"),
        _emit_042_template_header_guard,
        _emit_042_template_header_guard_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_helper_impl_decl": (
        "b4dbfc627b20fb92231456a7edb1a3a689ede4ddcb1b01b879911ab239a2fd3a",
        (),
        _emit_041_template_helper_impl_decl,
        _emit_041_template_helper_impl_decl_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_body_template": (
        "929231ce442e0b271649c7b370813a1d7e7296b0aeb68d585e28fc4ae0943f9e",
        (
            "constants_count",
            "dunder_main_package",
            "is_dunder_main",
            "is_package",
            "is_top",
            "module_code_objects_decl",
            "module_code_objects_init",
            "module_codes",
            "module_const_blob_name",
            "module_const_blob_symbol_name",
            "module_constants_check_hash",
            "module_constants_check_object",
            "module_constants_decl",
            "module_def_size",
            "module_exit",
            "module_function_table_entries",
            "module_functions_code",
            "module_functions_decl",
            "module_identifier",
            "module_includes",
            "module_init_codes",
            "module_name_cstr",
            "module_variable_accessors",
            "module_variable_accessors_count",
            "temps_decl",
            "use_direct_constant_blobs",
        ),
        _emit_037_template_module_body_template,
        _emit_037_template_module_body_template_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_exception_exit": (
        "7545624bdd6f885197f6c6962c271d2169176b2619f7cbab5175f2558524d452",
        ("is_top", "module_identifier"),
        _emit_039_template_module_exception_exit,
        _emit_039_template_module_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_external_entry_point": (
        "e6ccf0cd90836dcc9581272fc6769743f2d933010dcaa9c40fe2faed75d0c68e",
        (
            "module_def_size",
            "module_dll_entry_point",
            "module_identifier",
            "module_name_cstr",
        ),
        _emit_038_template_module_external_entry_point,
        _emit_038_template_module_external_entry_point_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_no_exception_exit": (
        "d10b36aa74a59bcf4a88185837f658afaf3646eff2bb16c3928d0e9335e945d2",
        (),
        _emit_040_template_module_no_exception_exit,
        _emit_040_template_module_no_exception_exit_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_global_known": (
        "d52dabfbda2d73a75b60f8517c134170b673ebc5625dab0e4b117113f1aaa277",
        ("module_identifier", "var_name"),
        _emit_071_template_del_global_known,
        _emit_071_template_del_global_known_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_global_unclear": (
        "e19f5a72a151a717a270dc98327195283acfd7b8e7d64ceaf4f9b69202a0ac4d",
        ("module_identifier", "result", "var_name"),
        _emit_070_template_del_global_unclear,
        _emit_070_template_del_global_unclear_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_local_intolerant": (
        "fc2bcef2d97262102249aad6861201353e36b8cbd127c98a74d4532d99e040c6",
        ("identifier", "result"),
        _emit_057_template_del_local_intolerant,
        _emit_057_template_del_local_intolerant_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_local_known": (
        "ae5576a4e417926a6b8eaa943c8c79acfa65a057eb58f9997b1481e891bda0b0",
        ("identifier",),
        _emit_059_template_del_local_known,
        _emit_059_template_del_local_known_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_local_tolerant": (
        "7c519e95013bbe50865ee8bdf7e1927a9b98f8d10e67604acd13b76b12462295",
        ("identifier",),
        _emit_055_template_del_local_tolerant,
        _emit_055_template_del_local_tolerant_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_py_cell_intolerant": (
        "26d8c64439200a202fd0963d8b602913897455bfec7faf97303e84d1a2172d68",
        ("identifier", "result"),
        _emit_081_template_del_py_cell_intolerant,
        _emit_081_template_del_py_cell_intolerant_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_py_cell_known": (
        "9b803de889dc98ab0a644cbe18256966ecd44342a12f8f76446175bf9ef5bc52",
        ("identifier",),
        _emit_082_template_del_py_cell_known,
        _emit_082_template_del_py_cell_known_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_py_cell_tolerant": (
        "70b2303a20bfc14342ed69a42e0c0d204f02fe207056d5aa6bc6cc2375450eb9",
        ("identifier",),
        _emit_080_template_del_py_cell_tolerant,
        _emit_080_template_del_py_cell_tolerant_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_shared_intolerant": (
        "ddf1157ea0de7012d54093e6cffdee00f8dd5050b6d63162d17b66c166d3ae54",
        ("identifier", "result"),
        _emit_058_template_del_shared_intolerant,
        _emit_058_template_del_shared_intolerant_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_shared_known": (
        "417c1768ca66c155bd9c48d2ada3bf6aebdeedd6da4643b5620fdc39f5fce0f4",
        ("identifier",),
        _emit_060_template_del_shared_known,
        _emit_060_template_del_shared_known_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_shared_tolerant": (
        "2e0d1aa2d273ac3be4aa858f4ad5d60ca15295a09fc0107cd151d16766143abf",
        ("identifier",),
        _emit_056_template_del_shared_tolerant,
        _emit_056_template_del_shared_tolerant_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_module_variable_accessor_function": (
        "e6d5affebd0b8808d0fd3537203650ed25009ab4f65d6b0bce4d95c25b982dd6",
        ("accessor_function_name", "caching", "module_identifier", "var_name"),
        _emit_076_template_module_variable_accessor_function,
        _emit_076_template_module_variable_accessor_function_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_dict_with_fallback": (
        "26ee6849e18e5334d362a7e2411510fa02896be7b9fff97bfdc47b46f3d06f36",
        ("dict_get_item", "fallback", "locals_dict", "to_name", "var_name"),
        _emit_065_template_read_locals_dict_with_fallback,
        _emit_065_template_read_locals_dict_with_fallback_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_dict_without_fallback": (
        "5f07e5195932f38611856adaddbc68ff3452e5ffa81a93a035aff354250c6842",
        ("locals_dict", "to_name", "var_name"),
        _emit_066_template_read_locals_dict_without_fallback,
        _emit_066_template_read_locals_dict_without_fallback_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_mapping_with_fallback_no_ref": (
        "4d673ff262ce29766823cbfef3c60f8e264e8d6210d36dfbf42631163a77f3be",
        (
            "exception_exit",
            "exception_state_name",
            "fallback",
            "locals_dict",
            "to_name",
            "var_name",
        ),
        _emit_067_template_read_locals_mapping_with_fallback_no_ref,
        _emit_067_template_read_locals_mapping_with_fallback_no_ref_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_mapping_with_fallback_ref": (
        "bea3d667173723884aeb8e387b9bd2882b365b49ef26d2507a0a4a3d13079ce1",
        (
            "exception_exit",
            "exception_state_name",
            "fallback",
            "locals_dict",
            "to_name",
            "var_name",
        ),
        _emit_068_template_read_locals_mapping_with_fallback_ref,
        _emit_068_template_read_locals_mapping_with_fallback_ref_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_mapping_without_fallback": (
        "a1e8dceb6a326ffbf9e3492637406666a6cf25770e66df8db00e82b80c93a2ff",
        ("locals_dict", "to_name", "var_name"),
        _emit_069_template_read_locals_mapping_without_fallback,
        _emit_069_template_read_locals_mapping_without_fallback_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_mvar_unclear": (
        "edfa07c85fa85055bf44003e44de9dc22aab0bcad78ceec5c8282846d8a79c76",
        ("module_identifier", "tmp_name", "var_name"),
        _emit_064_template_read_mvar_unclear,
        _emit_064_template_read_mvar_unclear_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_shared_known": (
        "fd308f64b50e21c8f68921086401e41b3c0a4dd16d84644d2a05dd085547f69e",
        ("identifier", "tmp_name"),
        _emit_063_template_read_shared_known,
        _emit_063_template_read_shared_known_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_release_object_clear": (
        "6cc31fe6f8c8c5bc622389deb2a50a23baa6e33861249043997def820b8cc5ca",
        ("identifier",),
        _emit_062_template_release_object_clear,
        _emit_062_template_release_object_clear_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_release_object_unclear": (
        "4673b63d7274ed62ee911fab568304a54ba15172fac5807feb319f40980413ac",
        ("identifier",),
        _emit_061_template_release_object_unclear,
        _emit_061_template_release_object_unclear_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_set_locals_dict_value": (
        "e12be7b1c99f8ce52bca406a677a0e2b4c3f91a34d0166674077b6c9009234e9",
        ("access_code", "dict_name", "test_code", "var_name"),
        _emit_073_template_set_locals_dict_value,
        _emit_073_template_set_locals_dict_value_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_set_locals_mapping_value": (
        "65e3faa0b16044876f203e0e27b89c01d61bc2fffa0f34a1e331289db87abf4f",
        ("access_code", "mapping_name", "test_code", "tmp_name", "var_name"),
        _emit_075_template_set_locals_mapping_value,
        _emit_075_template_set_locals_mapping_value_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_update_locals_dict_value": (
        "d138fbf7934aea407c19732e68a8d428f3be62e9f8d009a804a22829ca8bac6f",
        ("access_code", "dict_name", "test_code", "var_name"),
        _emit_072_template_update_locals_dict_value,
        _emit_072_template_update_locals_dict_value_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_update_locals_mapping_value": (
        "2763851919448fde41dbd1a23d1a1f6d865d3219a3241c873c062c6cc11412c6",
        ("access_code", "mapping_name", "test_code", "tmp_name", "var_name"),
        _emit_074_template_update_locals_mapping_value,
        _emit_074_template_update_locals_mapping_value_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_clear_ref0": (
        "a79a193ae3f6f03bb44483feb56bce2461277064436ecc4e62bba12d99d87a44",
        ("identifier", "tmp_name"),
        _emit_047_template_write_local_clear_ref0,
        _emit_047_template_write_local_clear_ref0_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_clear_ref1": (
        "7187806a4d01c37782eb5b370cc23b688465b881a0cc5c86ae928978dbb9073a",
        ("identifier", "tmp_name"),
        _emit_050_template_write_local_clear_ref1,
        _emit_050_template_write_local_clear_ref1_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_empty_ref0": (
        "0f28bb1b6eb41e78703952a33bb5bb3c49601bc22dd1ea52f8efd9c36a752360",
        ("identifier", "tmp_name"),
        _emit_045_template_write_local_empty_ref0,
        _emit_045_template_write_local_empty_ref0_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_empty_ref1": (
        "6231a9e663b590213380cd3e0f8e9f56655c7d89f437ff4c9ce6f256d73b593e",
        ("identifier", "tmp_name"),
        _emit_046_template_write_local_empty_ref1,
        _emit_046_template_write_local_empty_ref1_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_inplace": (
        "6b24114fbcb93f554d4781e910348485bc78f481a014561090ada2455a5ec3fd",
        ("identifier", "tmp_name"),
        _emit_048_template_write_local_inplace,
        _emit_048_template_write_local_inplace_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_unclear_ref0": (
        "68600ea7a983e8b1aa261d952eac01d16b755a50fc9471a38420ee6b46f8e044",
        ("identifier", "tmp_name"),
        _emit_043_template_write_local_unclear_ref0,
        _emit_043_template_write_local_unclear_ref0_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_unclear_ref1": (
        "0f9acd29e95ee650e8a1fd1da3f93b7a203824f3fd4653f35187c8c926651eab",
        ("identifier", "tmp_name"),
        _emit_044_template_write_local_unclear_ref1,
        _emit_044_template_write_local_unclear_ref1_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_py_cell_inplace": (
        "fc77fd03121d1e92e3fe96f671c15ac7b2ae79a48aca3c7ad54244cfe03b19a3",
        ("identifier", "tmp_name"),
        _emit_077_template_write_py_cell_inplace,
        _emit_077_template_write_py_cell_inplace_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_py_cell_unclear_ref0": (
        "4c6ebda925fecb94e4ddb776400505503e564fe6826f0a7406553b25b00e9fa4",
        ("identifier", "tmp_name"),
        _emit_078_template_write_py_cell_unclear_ref0,
        _emit_078_template_write_py_cell_unclear_ref0_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_py_cell_unclear_ref1": (
        "585df5b46aee34892618de24cd09ace82adc3896f5933ac50b774eea56f55b59",
        ("identifier", "tmp_name"),
        _emit_079_template_write_py_cell_unclear_ref1,
        _emit_079_template_write_py_cell_unclear_ref1_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_clear_ref0": (
        "9ef33805b0a960ae8d02ed8ec5e301511cf817db9fac344f022d35500b084bfb",
        ("identifier", "tmp_name"),
        _emit_053_template_write_shared_clear_ref0,
        _emit_053_template_write_shared_clear_ref0_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_clear_ref1": (
        "9e6b8b16a7e64f00f1e7a4af6351c029804798364c40cf4832e5db20bf6de789",
        ("identifier", "tmp_name"),
        _emit_054_template_write_shared_clear_ref1,
        _emit_054_template_write_shared_clear_ref1_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_inplace": (
        "e8d516dfe1e92289de7d98e57e5ca7276fedb034c40fc670225c3af9c2850215",
        ("identifier", "tmp_name"),
        _emit_049_template_write_shared_inplace,
        _emit_049_template_write_shared_inplace_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_unclear_ref0": (
        "fdc9447573fc677fc96af34112a885dda897ee604699ff2e7d86f9c195f25002",
        ("identifier", "tmp_name"),
        _emit_051_template_write_shared_unclear_ref0,
        _emit_051_template_write_shared_unclear_ref0_readable,
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_unclear_ref1": (
        "4b91c4cfef66190226abf7510f5c24ae23b23c9bbf410048b91e9632c3494349",
        ("identifier", "tmp_name"),
        _emit_052_template_write_shared_unclear_ref1,
        _emit_052_template_write_shared_unclear_ref1_readable,
    ),
}

template_variables = {
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_exception_exit": (
        ("function_cleanup", "s"),
        ("exception_state_name", "s"),
        ("exception_state_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_no_exception_exit": (
        ("function_cleanup", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_object_body": (
        ("has_heap_declaration", "s"),
        ("function_identifier", "s"),
        ("function_local_types", "s"),
        ("function_identifier", "s"),
        ("has_heap_declaration", "s"),
        ("heap_declaration", "s"),
        ("function_dispatch", "s"),
        ("function_var_inits", "s"),
        ("function_body", "s"),
        ("asyncgen_exit", "s"),
        ("asyncgen_maker_identifier", "s"),
        ("asyncgen_creation_args", "s"),
        ("function_identifier", "s"),
        ("asyncgen_module", "s"),
        ("asyncgen_name_obj", "s"),
        ("asyncgen_qualname_obj", "s"),
        ("code_identifier", "s"),
        ("closure_name", "s"),
        ("closure_count", "d"),
        ("has_heap_declaration", "s"),
        ("function_identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_object_maker_template": (
        ("asyncgen_maker_identifier", "s"),
        ("asyncgen_creation_args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_asyncgen_return_exit": (),
    "nuitka.code_generation.templates.CodeTemplatesAsyncgens.template_make_asyncgen": (
        ("closure_copy", "s"),
        ("to_name", "s"),
        ("asyncgen_maker_identifier", "s"),
        ("args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesConstants.template_constants_reading": (
        ("global_constants_count", "d"),
        ("global_constants_blob_symbol_name", "s"),
        ("global_constants_blob_symbol_name", "s"),
        ("use_direct_constant_blobs", "d"),
        ("global_constants_blob_symbol_name", "s"),
        ("sys_executable", "s"),
        ("sys_executable", "s"),
        ("sys_prefix", "s"),
        ("sys_exec_prefix", "s"),
        ("sys_base_prefix", "s"),
        ("sys_base_exec_prefix", "s"),
        ("nuitka_version_major", "s"),
        ("nuitka_version_minor", "s"),
        ("nuitka_version_micro", "s"),
        ("nuitka_version_level", "s"),
        ("metadata_values", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_exception_exit": (
        ("function_cleanup", "s"),
        ("exception_state_name", "s"),
        ("exception_state_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_no_exception_exit": (
        ("function_cleanup", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_object_body": (
        ("has_heap_declaration", "s"),
        ("function_identifier", "s"),
        ("function_local_types", "s"),
        ("function_identifier", "s"),
        ("has_heap_declaration", "s"),
        ("heap_declaration", "s"),
        ("function_dispatch", "s"),
        ("function_var_inits", "s"),
        ("function_body", "s"),
        ("coroutine_exit", "s"),
        ("coroutine_maker_identifier", "s"),
        ("coroutine_creation_args", "s"),
        ("function_identifier", "s"),
        ("coroutine_module", "s"),
        ("coroutine_name_obj", "s"),
        ("coroutine_qualname_obj", "s"),
        ("code_identifier", "s"),
        ("closure_name", "s"),
        ("closure_count", "d"),
        ("has_heap_declaration", "s"),
        ("function_identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_object_maker": (
        ("coroutine_maker_identifier", "s"),
        ("coroutine_creation_args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_coroutine_return_exit": (
        ("return_value", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesCoroutines.template_make_coroutine": (
        ("closure_copy", "s"),
        ("to_name", "s"),
        ("coroutine_maker_identifier", "s"),
        ("args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_catch_exception": (
        ("condition", "s"),
        ("exception_state_name", "s"),
        ("release_temps", "s"),
        ("line_number_code", "s"),
        ("var_description_code", "s"),
        ("exception_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_catch_fetched_exception": (
        ("condition", "s"),
        ("exception_state_name", "s"),
        ("release_temps", "s"),
        ("line_number_code", "s"),
        ("var_description_code", "s"),
        ("exception_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_format_name_error_exception": (
        ("condition", "s"),
        ("release_temps", "s"),
        ("raise_name_error_helper", "s"),
        ("exception_state_name", "s"),
        ("variable_name", "s"),
        ("line_number_code", "s"),
        ("var_description_code", "s"),
        ("exception_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_error_format_string_exception": (
        ("condition", "s"),
        ("release_temps", "s"),
        ("set_exception", "s"),
        ("line_number_code", "s"),
        ("var_description_code", "s"),
        ("exception_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesExceptions.template_publish_exception_to_handler": (
        ("keeper_exception_state_name", "s"),
        ("tb_making", "s"),
        ("keeper_exception_state_name", "s"),
        ("keeper_lineno", "s"),
        ("frame_identifier", "s"),
        ("keeper_lineno", "s"),
        ("keeper_exception_state_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFrames.template_frame_attach_locals": (
        ("frame_identifier", "s"),
        ("type_description", "s"),
        ("frame_variable_refs", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFrames.template_frame_guard_generator_return_handler": (
        ("frame_return_exit", "s"),
        ("context_identifier", "s"),
        ("context_identifier", "s"),
        ("context_identifier", "s"),
        ("return_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_body": (
        ("function_identifier", "s"),
        ("parameter_objects_decl", "s"),
        ("function_locals", "s"),
        ("function_body", "s"),
        ("function_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_direct_declaration": (
        ("file_scope", "s"),
        ("function_identifier", "s"),
        ("direct_call_arg_spec", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_exception_exit": (
        ("function_cleanup", "s"),
        ("exception_state_name", "s"),
        ("exception_state_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_make_declaration": (
        ("function_identifier", "s"),
        ("function_creation_args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_function_return_exit": (
        ("function_cleanup", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_make_function": (
        ("closure_copy", "s"),
        ("to_name", "s"),
        ("function_maker_identifier", "s"),
        ("args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesFunction.template_maker_function_body": (
        ("function_maker_identifier", "s"),
        ("function_creation_args", "s"),
        ("function_impl_identifier", "s"),
        ("function_name_obj", "s"),
        ("function_qualname_obj", "s"),
        ("code_identifier", "s"),
        ("defaults", "s"),
        ("kw_defaults", "s"),
        ("annotations", "s"),
        ("module_identifier", "s"),
        ("function_doc", "s"),
        ("closure_name", "s"),
        ("closure_count", "d"),
        ("type_params", "s"),
        ("constant_return_code", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_context_body_template": (
        ("has_heap_declaration", "s"),
        ("function_identifier", "s"),
        ("function_local_types", "s"),
        ("function_identifier", "s"),
        ("has_heap_declaration", "s"),
        ("heap_declaration", "s"),
        ("function_dispatch", "s"),
        ("function_var_inits", "s"),
        ("function_body", "s"),
        ("generator_exit", "s"),
        ("generator_maker_identifier", "s"),
        ("generator_creation_args", "s"),
        ("function_identifier", "s"),
        ("generator_module", "s"),
        ("generator_name_obj", "s"),
        ("generator_qualname_obj", "s"),
        ("code_identifier", "s"),
        ("closure_name", "s"),
        ("closure_count", "d"),
        ("has_heap_declaration", "s"),
        ("function_identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_context_maker_decl": (
        ("generator_maker_identifier", "s"),
        ("generator_creation_args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_exception_exit": (
        ("function_cleanup", "s"),
        ("function_cleanup", "s"),
        ("exception_state_name", "s"),
        ("exception_state_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_no_exception_exit": (
        ("function_cleanup", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_generator_return_exit": (
        ("return_value", "s"),
        ("function_cleanup", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_make_empty_generator": (
        ("closure_copy", "s"),
        ("to_name", "s"),
        ("generator_module", "s"),
        ("generator_name_obj", "s"),
        ("generator_qualname_obj", "s"),
        ("code_identifier", "s"),
        ("closure_name", "s"),
        ("closure_count", "d"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesGeneratorFunction.template_make_generator": (
        ("closure_copy", "s"),
        ("to_name", "s"),
        ("generator_maker_identifier", "s"),
        ("args", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesIterators.template_loop_break_next": (
        ("to_name", "s"),
        ("break_indicator_code", "s"),
        ("break_target", "s"),
        ("release_temps", "s"),
        ("exception_state_name", "s"),
        ("var_description_code", "s"),
        ("line_number_code", "s"),
        ("exception_target", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesLoader.template_metapath_loader_body": (
        ("bytecode_count", "d"),
        ("bytecode_count", "d"),
        ("metapath_module_decls", "s"),
        ("entry_count", "d"),
        ("metapath_loader_inittab", "s"),
        ("entry_count", "d"),
        ("frozen_modules", "s"),
        ("entry_count", "d"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_global_copyright": (
        ("module_identifier", "s"),
        ("version", "s"),
        ("year", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_header_guard": (
        ("header_guard_name", "s"),
        ("header_guard_name", "s"),
        ("header_body", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_helper_impl_decl": (),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_body_template": (
        ("module_includes", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_constants_decl", "s"),
        ("constants_count", "d"),
        ("module_const_blob_symbol_name", "s"),
        ("module_const_blob_symbol_name", "s"),
        ("use_direct_constant_blobs", "d"),
        ("module_const_blob_symbol_name", "s"),
        ("module_const_blob_name", "s"),
        ("module_constants_check_hash", "s"),
        ("is_dunder_main", "s"),
        ("module_identifier", "s"),
        ("module_constants_check_object", "s"),
        ("module_variable_accessors_count", "d"),
        ("module_variable_accessors", "s"),
        ("module_code_objects_decl", "s"),
        ("module_code_objects_init", "s"),
        ("module_functions_decl", "s"),
        ("module_functions_code", "s"),
        ("module_identifier", "s"),
        ("module_function_table_entries", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("is_top", "d"),
        ("module_name_cstr", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("is_top", "d"),
        ("module_identifier", "s"),
        ("module_def_size", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("is_top", "d"),
        ("module_name_cstr", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("is_package", "s"),
        ("module_identifier", "s"),
        ("is_dunder_main", "s"),
        ("module_identifier", "s"),
        ("dunder_main_package", "s"),
        ("is_package", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("is_dunder_main", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("is_dunder_main", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("is_top", "d"),
        ("module_def_size", "s"),
        ("module_identifier", "s"),
        ("temps_decl", "s"),
        ("module_init_codes", "s"),
        ("module_codes", "s"),
        ("module_identifier", "s"),
        ("is_top", "d"),
        ("module_name_cstr", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_exception_exit": (
        ("is_top", "d"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_external_entry_point": (
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_def_size", "s"),
        ("module_identifier", "s"),
        ("module_dll_entry_point", "s"),
        ("module_identifier", "s"),
        ("module_name_cstr", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_def_size", "s"),
        ("module_dll_entry_point", "s"),
        ("module_dll_entry_point", "s"),
        ("module_dll_entry_point", "s"),
        ("module_identifier", "s"),
        ("module_def_size", "s"),
        ("module_identifier", "s"),
        ("module_def_size", "s"),
        ("module_dll_entry_point", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_dll_entry_point", "s"),
        ("module_dll_entry_point", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesModules.template_module_no_exception_exit": (),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_global_known": (
        ("module_identifier", "s"),
        ("var_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_global_unclear": (
        ("result", "s"),
        ("module_identifier", "s"),
        ("var_name", "s"),
        ("result", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_local_intolerant": (
        ("result", "s"),
        ("identifier", "s"),
        ("result", "s"),
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_local_known": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_local_tolerant": (
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_py_cell_intolerant": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("result", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_py_cell_known": (
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_py_cell_tolerant": (
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_shared_intolerant": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("result", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_shared_known": (
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_del_shared_tolerant": (
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_module_variable_accessor_function": (
        ("accessor_function_name", "s"),
        ("caching", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("module_identifier", "s"),
        ("var_name", "s"),
        ("module_identifier", "s"),
        ("var_name", "s"),
        ("var_name", "s"),
        ("var_name", "s"),
        ("var_name", "s"),
        ("module_identifier", "s"),
        ("var_name", "s"),
        ("module_identifier", "s"),
        ("var_name", "s"),
        ("var_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_dict_with_fallback": (
        ("to_name", "s"),
        ("dict_get_item", "s"),
        ("locals_dict", "s"),
        ("var_name", "s"),
        ("to_name", "s"),
        ("fallback", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_dict_without_fallback": (
        ("to_name", "s"),
        ("locals_dict", "s"),
        ("var_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_mapping_with_fallback_no_ref": (
        ("to_name", "s"),
        ("locals_dict", "s"),
        ("var_name", "s"),
        ("to_name", "s"),
        ("fallback", "s"),
        ("to_name", "s"),
        ("exception_state_name", "s"),
        ("exception_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_mapping_with_fallback_ref": (
        ("to_name", "s"),
        ("locals_dict", "s"),
        ("var_name", "s"),
        ("to_name", "s"),
        ("fallback", "s"),
        ("exception_state_name", "s"),
        ("exception_exit", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_locals_mapping_without_fallback": (
        ("to_name", "s"),
        ("locals_dict", "s"),
        ("var_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_mvar_unclear": (
        ("tmp_name", "s"),
        ("module_identifier", "s"),
        ("var_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_read_shared_known": (
        ("tmp_name", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_release_object_clear": (
        ("identifier", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_release_object_unclear": (
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_set_locals_dict_value": (
        ("test_code", "s"),
        ("access_code", "s"),
        ("dict_name", "s"),
        ("var_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_set_locals_mapping_value": (
        ("test_code", "s"),
        ("access_code", "s"),
        ("tmp_name", "s"),
        ("mapping_name", "s"),
        ("var_name", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_update_locals_dict_value": (
        ("test_code", "s"),
        ("access_code", "s"),
        ("dict_name", "s"),
        ("var_name", "s"),
        ("dict_name", "s"),
        ("var_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_update_locals_mapping_value": (
        ("test_code", "s"),
        ("access_code", "s"),
        ("mapping_name", "s"),
        ("var_name", "s"),
        ("tmp_name", "s"),
        ("mapping_name", "s"),
        ("var_name", "s"),
        ("mapping_name", "s"),
        ("var_name", "s"),
        ("tmp_name", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_clear_ref0": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_clear_ref1": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_empty_ref0": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_empty_ref1": (
        ("identifier", "s"),
        ("tmp_name", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_inplace": (
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_unclear_ref0": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_local_unclear_ref1": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
        ("identifier", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_py_cell_inplace": (
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_py_cell_unclear_ref0": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_py_cell_unclear_ref1": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_clear_ref0": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_clear_ref1": (
        ("identifier", "s"),
        ("tmp_name", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_inplace": (
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_unclear_ref0": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
    ),
    "nuitka.code_generation.templates.CodeTemplatesVariables.template_write_shared_unclear_ref1": (
        ("identifier", "s"),
        ("identifier", "s"),
        ("tmp_name", "s"),
        ("tmp_name", "s"),
    ),
}

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
