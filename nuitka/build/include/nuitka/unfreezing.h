//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_UNFREEZING_H__
#define __NUITKA_UNFREEZING_H__

#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#ifndef NUITKA_LOADER_NAME_MAX_LEN
#define NUITKA_LOADER_NAME_MAX_LEN 2048
#endif

/* Modes for loading modules, can be compiled, external shared library, or
 * bytecode. */
#define NUITKA_COMPILED_MODULE 0
#define NUITKA_EXTENSION_MODULE_FLAG 1
#define NUITKA_PACKAGE_FLAG 2
#define NUITKA_BYTECODE_FLAG 4

#define NUITKA_ABORT_MODULE_FLAG 8

#define NUITKA_INTERNAL_MODULE_FLAG 16

#define NUITKA_PERFECT_SUPPORTED_FLAG 32

#define NUITKA_MAIN_MODULE_FLAG 128

#if _NUITKA_STANDALONE_MODE && !defined(_NUITKA_DEPLOYMENT_MODE) &&                                                    \
    !defined(_NUITKA_NO_DEPLOYMENT_EXCLUDED_MODULE_USAGE)
#define NUITKA_EXCLUDED_MODULE_FLAG 64
#endif

struct Nuitka_MetaPathBasedLoaderEntry;

typedef PyObject *(*module_init_func)(PyThreadState *tstate, PyObject *module);

#if PYTHON_VERSION >= 0x370 && _NUITKA_EXE_MODE && !_NUITKA_STANDALONE_MODE &&                                         \
    defined(_NUITKA_FILE_REFERENCE_ORIGINAL_MODE)
#define _NUITKA_FREEZER_HAS_FILE_PATH
#endif

struct Nuitka_MetaPathBasedLoaderEntry {
    // The module name data, either the plain name, or for commercial code the
    // encoded values, turned into the runtime name by "m_get_name" when it is
    // non-NULL, and used directly otherwise.
    char const *m_name;
    void (*m_get_name)(char *buffer, size_t buffer_size, char const *name);

    // Optional function to check if a given module name matches this entry.
    // When NULL, the name is compared against the runtime name.
    bool (*m_compare_name)(char const *name, char const *m_name);

    // Optional function returning a display name for this entry, used for
    // error messages and debug output. When NULL, the runtime name is used.
    char const *(*m_get_display_name)(void);

    // Optional entry of the "preLoad" code to be executed before this module,
    // or NULL. This avoids a name based connection to that trigger module.
    struct Nuitka_MetaPathBasedLoaderEntry const *m_pre_load;

    // Optional entry of the "postLoad" code to be executed after this module,
    // or NULL. This avoids a name based connection to that trigger module.
    struct Nuitka_MetaPathBasedLoaderEntry const *m_post_load;

    // Optional entry of the parent package, or NULL for top level modules.
    // This avoids a name based connection for "iter_modules".
    struct Nuitka_MetaPathBasedLoaderEntry const *m_parent;

    // Entry function if compiled module, otherwise NULL.
    module_init_func python_init_func;

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
extern void registerMetaPathBasedLoader(struct Nuitka_MetaPathBasedLoaderEntry **loader_entries,
                                        unsigned char **bytecode_data, int entry_count);

/* Produce the runtime name of a loader entry into a buffer. When "m_get_name"
 * is non-NULL it is invoked with "m_name"; otherwise "m_name" is copied directly.
 */
extern void Nuitka_LoaderEntryName(struct Nuitka_MetaPathBasedLoaderEntry const *entry, char *buffer,
                                   size_t buffer_size);

/* Check if a module name matches a loader entry. When "m_compare_name" is
 * non-NULL it is invoked with "m_name"; otherwise the runtime name is produced
 * via "Nuitka_LoaderEntryName" and compared with "strcmp".
 */
extern bool Nuitka_LoaderEntryCompareName(struct Nuitka_MetaPathBasedLoaderEntry const *entry, char const *name);

// For module mode, embedded modules may have to be shifted to below the
// namespace they are loaded into.
#if _NUITKA_MODULE_MODE
extern char const *getMetaPathBasedLoaderModuleRoot(void);
extern void updateMetaPathBasedLoaderModuleRoot(char const *module_root_name);
extern void getModuleNameWithPackageLoadedPrefix(char *buffer, size_t buffer_size, char const *name);
#endif

/* Create a loader object responsible for a package. */
extern PyObject *Nuitka_Loader_New(struct Nuitka_MetaPathBasedLoaderEntry const *entry);

// Create a distribution object from the given metadata.
extern PyObject *Nuitka_Distribution_New(PyThreadState *tstate, PyObject *name);

// Check if we provide a distribution object ourselves.
extern bool Nuitka_DistributionNext(Py_ssize_t *pos, PyObject **distribution_name_ptr);

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
