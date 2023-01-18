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
#ifndef __NUITKA_UNFREEZING_H__
#define __NUITKA_UNFREEZING_H__

/* Modes for loading modules, can be compiled, external shared library, or
 * bytecode. */
#define NUITKA_COMPILED_MODULE 0
#define NUITKA_EXTENSION_MODULE_FLAG 1
#define NUITKA_PACKAGE_FLAG 2
#define NUITKA_BYTECODE_FLAG 4

#define NUITKA_ABORT_MODULE_FLAG 8

#define NUITKA_TRANSLATED_FLAG 16

struct Nuitka_MetaPathBasedLoaderEntry;

typedef PyObject *(*module_initfunc)(PyObject *module, struct Nuitka_MetaPathBasedLoaderEntry const *loader_entry);

#if PYTHON_VERSION >= 0x370 && defined(_NUITKA_EXE) && !defined(_NUITKA_STANDALONE)
#define _NUITKA_FREEZER_HAS_FILE_PATH
#endif

struct Nuitka_MetaPathBasedLoaderEntry {
    // Full module name, including package name.
    char const *name;

    // Entry function if compiled module, otherwise NULL.
    module_initfunc python_initfunc;

    // For bytecode modules, start and size inside the constants blob.
    int bytecode_index;
    int bytecode_size;

    // Flags: Indicators if this is compiled, bytecode or shared library.
    int flags;

    // For accelerated mode, we need to be able to tell where the module "__file__"
    // lives, so we can resolve resource reader paths, not relative to the binary
    // but to code location without loading it.
#if defined(_NUITKA_FREEZER_HAS_FILE_PATH)
#if defined _WIN32
    wchar_t const *file_path;
#else
    char const *file_path;
#endif
#endif
};

/* For embedded modules, register the meta path based loader. Used by main
 * program/package only.
 */
extern void registerMetaPathBasedUnfreezer(struct Nuitka_MetaPathBasedLoaderEntry *loader_entries,
                                           unsigned char **bytecode_data);

/* Create a loader object responsible for a package. */
extern PyObject *Nuitka_Loader_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry);

// Create a distribution object from the given metadata.
extern PyObject *Nuitka_Distribution_New(char const *distribution_name, char const *package_name, PyObject *metadata);

#endif
