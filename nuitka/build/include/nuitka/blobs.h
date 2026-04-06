//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_BLOBS_H__
#define __NUITKA_BLOBS_H__

/** Declaration of binary blobs.
 *
 * There are multiple ways, the blobs are accessed, and their
 * definition depends on how that is done.
 *
 * It could be a Windows resource, then it must be a pointer. If it's defined
 * externally in a C file, or at link time with "ld", it must be an array. This
 * hides these facts.
 *
 */

#if defined(_NUITKA_CONSTANTS_FROM_INCBIN) || defined(_NUITKA_CONSTANTS_FROM_C23_EMBED)

#ifdef __cplusplus
#define NUITKA_CONSTANTS_EXTERN_C_START extern "C" {
#define NUITKA_CONSTANTS_EXTERN_C_END }
#else
#define NUITKA_CONSTANTS_EXTERN_C_START
#define NUITKA_CONSTANTS_EXTERN_C_END
#endif

#define NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                     \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    extern unsigned modifier char *get##blob_camel_name##Data(void);                                                   \
    NUITKA_CONSTANTS_EXTERN_C_END

#define NUITKA_DECLARE_CONSTANT_BLOB_SIZED(blob_name, blob_camel_name, modifier, res_id)                               \
    NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                         \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    extern unsigned long long get##blob_camel_name##Size(void);                                                        \
    NUITKA_CONSTANTS_EXTERN_C_END

#elif defined(_NUITKA_CONSTANTS_FROM_RESOURCE)

#include <windows.h> // Ensure FindResource and loaded objects are valid

#ifdef __cplusplus
#define NUITKA_CONSTANTS_EXTERN_C_START extern "C" {
#define NUITKA_CONSTANTS_EXTERN_C_END }
#else
#define NUITKA_CONSTANTS_EXTERN_C_START
#define NUITKA_CONSTANTS_EXTERN_C_END
#endif

#if _NUITKA_EXE_MODE
#define _NUITKA_GET_RESOURCE_HANDLE() NULL
#else
extern HMODULE getDllModuleHandle(void);
#define _NUITKA_GET_RESOURCE_HANDLE() getDllModuleHandle()
#endif

#define NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                     \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    static inline unsigned modifier char *get##blob_camel_name##Data(void) {                                           \
        HMODULE handle = _NUITKA_GET_RESOURCE_HANDLE();                                                                \
        HRSRC hRes = FindResource(handle, MAKEINTRESOURCE(res_id), RT_RCDATA);                                         \
        if (unlikely(hRes == NULL)) {                                                                                  \
            abort();                                                                                                   \
        }                                                                                                              \
        HGLOBAL hData = LoadResource(handle, hRes);                                                                    \
        if (unlikely(hData == NULL)) {                                                                                 \
            abort();                                                                                                   \
        }                                                                                                              \
        return (unsigned modifier char *)LockResource(hData);                                                          \
    }                                                                                                                  \
    NUITKA_CONSTANTS_EXTERN_C_END

#define NUITKA_DECLARE_CONSTANT_BLOB_SIZED(blob_name, blob_camel_name, modifier, res_id)                               \
    NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                         \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    static inline unsigned long long get##blob_camel_name##Size(void) {                                                \
        HMODULE handle = _NUITKA_GET_RESOURCE_HANDLE();                                                                \
        HRSRC hRes = FindResource(handle, MAKEINTRESOURCE(res_id), RT_RCDATA);                                         \
        if (unlikely(hRes == NULL)) {                                                                                  \
            abort();                                                                                                   \
        }                                                                                                              \
        return SizeofResource(handle, hRes);                                                                           \
    }                                                                                                                  \
    NUITKA_CONSTANTS_EXTERN_C_END

#elif defined(_NUITKA_CONSTANTS_FROM_MACOS_SECTION)

#include <assert.h>
#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <mach-o/getsect.h>
#include <mach-o/ldsyms.h>
#include <string.h>

#ifdef __LP64__
#define mach_header_arch mach_header_64
#else
#define mach_header_arch mach_header
#endif

#ifdef __cplusplus
#define NUITKA_CONSTANTS_EXTERN_C_START extern "C" {
#define NUITKA_CONSTANTS_EXTERN_C_END }
#else
#define NUITKA_CONSTANTS_EXTERN_C_START
#define NUITKA_CONSTANTS_EXTERN_C_END
#endif

// Helper to find the mach header of the current module or executable
static inline const struct mach_header_arch *_getNuitkaMachHeader(void) {
#if _NUITKA_EXE_MODE
    return &_mh_execute_header;
#else
    Dl_info where;
    int res = dladdr((void *)_getNuitkaMachHeader, &where);
    assert(res != 0);

    char const *dll_filename = where.dli_fname;
    unsigned long image_count = _dyld_image_count();

    for (unsigned long i = 0; i < image_count; i++) {
        struct mach_header const *header = _dyld_get_image_header(i);
        if (header == NULL) {
            continue;
        }
        if (strcmp(dll_filename, _dyld_get_image_name(i)) == 0) {
            return (const struct mach_header_arch *)header;
        }
    }
    return NULL;
#endif
}

#define NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                     \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    static inline unsigned modifier char *get##blob_camel_name##Data(void) {                                           \
        const struct mach_header_arch *header = _getNuitkaMachHeader();                                                \
        unsigned long size;                                                                                            \
        return (unsigned modifier char *)getsectiondata(header, #blob_name, #blob_name, &size);                        \
    }                                                                                                                  \
    NUITKA_CONSTANTS_EXTERN_C_END

#define NUITKA_DECLARE_CONSTANT_BLOB_SIZED(blob_name, blob_camel_name, modifier, res_id)                               \
    NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                         \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    static inline unsigned long long get##blob_camel_name##Size(void) {                                                \
        const struct mach_header_arch *header = _getNuitkaMachHeader();                                                \
        unsigned long size;                                                                                            \
        getsectiondata(header, #blob_name, #blob_name, &size);                                                         \
        return size;                                                                                                   \
    }                                                                                                                  \
    NUITKA_CONSTANTS_EXTERN_C_END

#else

#ifdef __cplusplus
#define NUITKA_CONSTANTS_EXTERN_C_START extern "C" {
#define NUITKA_CONSTANTS_EXTERN_C_END }
#else
#define NUITKA_CONSTANTS_EXTERN_C_START
#define NUITKA_CONSTANTS_EXTERN_C_END
#endif

#define NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                     \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    extern modifier unsigned char blob_name##_data[];                                                                  \
    NUITKA_CONSTANTS_EXTERN_C_END                                                                                      \
    static inline unsigned modifier char *get##blob_camel_name##Data(void) {                                           \
        return (unsigned modifier char *)(blob_name##_data);                                                           \
    }

#if defined(_NUITKA_CONSTANTS_FROM_CODE)
// The size for code mode is provided as an actual variable value
#define NUITKA_DECLARE_CONSTANT_BLOB_SIZED(blob_name, blob_camel_name, modifier, res_id)                               \
    NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                         \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    extern const unsigned long long blob_name##_size_value;                                                            \
    NUITKA_CONSTANTS_EXTERN_C_END                                                                                      \
    static inline unsigned long long get##blob_camel_name##Size(void) { return blob_name##_size_value; }
#else
// The size for linker/coff_obj mode is provided as an address variable by GNU linker or CoffObj
#define NUITKA_DECLARE_CONSTANT_BLOB_SIZED(blob_name, blob_camel_name, modifier, res_id)                               \
    NUITKA_DECLARE_CONSTANT_BLOB(blob_name, blob_camel_name, modifier, res_id)                                         \
    NUITKA_CONSTANTS_EXTERN_C_START                                                                                    \
    extern const unsigned char blob_name##_size_value[];                                                               \
    NUITKA_CONSTANTS_EXTERN_C_END                                                                                      \
    static inline unsigned long long get##blob_camel_name##Size(void) {                                                \
        return (unsigned long long)&(blob_name##_size_value);                                                          \
    }
#endif

#endif // INCBIN

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.gnu.org/licenses/agpl.txt
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
