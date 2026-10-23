//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* The main program for onefile bootstrap.
 *
 * It needs to unpack the attached files and and then loads and executes
 * the compiled program as a separate process.
 *
 * spell-checker: ignore HINSTANCE
 *
 */

#define _CRT_SECURE_NO_WARNINGS

#if !defined(_WIN32) && !defined(__APPLE__) && !defined(__FreeBSD__) && !defined(__NetBSD__) &&                        \
    !defined(__OpenBSD__) && !defined(__DragonFly__)
#define _POSIX_C_SOURCE 200809L
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#endif

#if defined(__APPLE__)
#ifndef _DARWIN_C_SOURCE
#define _DARWIN_C_SOURCE
#endif
#endif

#ifdef __NUITKA_NO_ASSERT__
#undef NDEBUG
#define NDEBUG
#endif

#if defined(_WIN32)
// Note: Keep this separate line, must be included before other Windows headers.
#include <windows.h>

// Other windows header files.
#include <psapi.h>

#endif

#include <assert.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <wchar.h>

/* Type bool */
#ifndef __cplusplus
#include <stdbool.h>
#endif

#if !defined(_WIN32)
#include <dirent.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

#ifndef __IDE_ONLY__
// Generated during build with optional defines.
#include "onefile_definitions.h"
#else
#define _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
#define _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
#define _NUITKA_ONEFILE_TEMP_BOOL 0
#define _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT 5000
#define _NUITKA_ONEFILE_TEMP_SPEC "{TEMP}/onefile_{PID}_{TIME_US}_{RANDOM}"

#define _NUITKA_ONEFILE_PAYLOAD_SIZE_INT 27272

#define _NUITKA_ONEFILE_DLL_RUN_CODE_ORDINAL_INT 1

#define _NUITKA_ATTACH_CONSOLE_WINDOW 1

// Most often used modes per OS, more exist and could be used of course.
#if defined(_WIN32)
#define _NUITKA_CONSTANTS_FROM_COFF_OBJ 1
#elif defined(__APPLE__)
#define _NUITKA_CONSTANTS_FROM_MACOS_SECTION 1
#else
#define _NUITKA_CONSTANTS_FROM_CODE 1
#endif
#endif

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
#ifdef _NUITKA_USE_SYSTEM_ZSTD
// Use system installed zstd for the public API only, e.g. for Debian packages
// that do not contain the inline copy, but link against the system library.
#include <zstd.h>
#else
// Header of zstd goes first, spellchecker: ignore ZSTDERRORLIB,ZSTDLIB
#define ZSTDERRORLIB_VISIBILITY
#define ZSTDLIB_VISIBILITY
#include "zstd.h"

// Should be in our inline copy, we include all C files into this one.
#include "common/error_private.c"
#include "common/fse_decompress.c"
#include "common/xxhash.c"
#include "common/zstd_common.c"
// Need to make sure this is last in common as it depends on the others.
#include "common/entropy_common.c"

// Decompression stuff.
#include "decompress/huf_decompress.c"
#include "decompress/zstd_ddict.c"
#include "decompress/zstd_decompress.c"
#include "decompress/zstd_decompress_block.c"
#endif
#endif

#include "nuitka/defines.h"

#if _NUITKA_EXPERIMENTAL_EXTRA_ONEFILE_INCLUDES_BOOL
#include "extra_onefile_includes.h"
#endif

#include "nuitka/blobs.h"

#include "HelpersChecksumTools.c"
#include "HelpersEnvironmentVariablesSystem.c"
#include "HelpersFilesystemPaths.c"
#include "HelpersSafeStrings.c"

#if defined(_WIN32) && (defined(_NUITKA_ATTACH_CONSOLE_WINDOW) || defined(_NUITKA_HIDE_CONSOLE_WINDOW))
#include "HelpersConsole.c"
#endif

// For tracing outputs if enabled at compile time.
#include "nuitka/tracing.h"

static void fatalError(char const *message) {
    puts(message);
    exit(2);
}

static void fatalIOError(char const *message, error_code_t error_code) {
    printOSErrorMessage(message, error_code);
    exit(2);
}

// Failure to expand the template for where to extract to.
static void fatalErrorTempFiles(void) {
    fatalIOError("Error, couldn't unpack file to target path.", getLastErrorCode());
}

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
static void fatalErrorAttachedData(void) { fatalError("Error, couldn't decode attached data."); }
#endif

static void fatalErrorHeaderAttachedData(void) { fatalError("Error, couldn't find attached data header."); }

// Out of memory error.
#if !defined(_WIN32) || _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
static void fatalErrorMemory(void) { fatalError("Error, couldn't allocate memory."); }
#endif

// Could not launch child process.
static void fatalErrorChild(char const *message, error_code_t error_code) { fatalIOError(message, error_code); }

static void fatalErrorTempFileCreate(filename_char_t const *filename) {
    fprintf(stderr, "Error, failed to open '" FILENAME_FORMAT_STR "' for writing.\n", filename);
    exit(2);
}

static void fatalErrorSpec(filename_char_t const *spec) {
    fprintf(stderr, "Error, couldn't runtime expand spec '" FILENAME_FORMAT_STR "'.\n", spec);
    abort();
}

static FILE_HANDLE createFileForWritingChecked(filename_char_t const *filename) {
    FILE_HANDLE result = createFileForWriting(filename);

    if (result == FILE_HANDLE_NULL) {
        fatalErrorTempFileCreate(filename);
    }

    return result;
}

static unsigned char const *payload_data = NULL;
static unsigned long long payload_size = 0;

static filename_char_t payload_path[4096] = {0};

#if defined(_NUITKA_ONEFILE_PAYLOAD_OVERLAY_BOOL)

// The payload is attached to the executable file instead of being embedded
// as a constant blob, which is done when the embedded data would exceed the
// size limits of the executable file format. The payload size is stored in
// the 8 bytes at the end of the payload.
static struct MapFileToMemoryInfo exe_file_mapped;

static uint32_t readFileUint32(unsigned char const *data) {
    uint32_t result;

    memcpy(&result, data, sizeof(result));

    return result;
}

// Determine the offset where the attached payload ends. This is at the end
// of the file, unless the executable is code signed, in which case the
// certificate table follows the attached data, and the PE header has to
// tell us where that starts.
static unsigned long long getAttachedPayloadEndOffset(void) {
    unsigned long long file_size = (unsigned long long)exe_file_mapped.file_size;

#if defined(_WIN32)
    if (file_size >= 0x40) {
        uint32_t pe_offset = readFileUint32(exe_file_mapped.data + 0x3C);
        uint16_t optional_magic;
        uint32_t security_directory_offset;

        if (pe_offset <= file_size - 24 && memcmp(exe_file_mapped.data + pe_offset, "PE\0\0", 4) == 0) {
            memcpy(&optional_magic, exe_file_mapped.data + pe_offset + 24, sizeof(optional_magic));

            // The PE32 and PE32+ optional headers have the security entry
            // (certificate table) of the data directory at different places.
            if (optional_magic == 0x10b) {
                security_directory_offset = pe_offset + 24 + 96 + 4 * 8;
            } else if (optional_magic == 0x20b) {
                security_directory_offset = pe_offset + 24 + 112 + 4 * 8;
            } else {
                return file_size;
            }

            if ((unsigned long long)security_directory_offset + 8 <= file_size) {
                uint32_t certificate_table_offset = readFileUint32(exe_file_mapped.data + security_directory_offset);
                uint32_t certificate_table_size = readFileUint32(exe_file_mapped.data + security_directory_offset + 4);

                if (certificate_table_size != 0 && certificate_table_offset >= 8 &&
                    (unsigned long long)certificate_table_offset <= file_size) {
                    return certificate_table_offset;
                }
            }
        }
    }
#endif

    return file_size;
}

static void initPayloadData2(void) {
    unsigned long long attached_payload_end;
    unsigned long long attached_payload_size;
    unsigned long long attached_payload_start;

    exe_file_mapped = mapFileToMemory(getBinaryPath());

    if (unlikely(exe_file_mapped.error)) {
        printOSErrorMessage("Error, failed to map the executable for its attached payload.",
                            exe_file_mapped.error_code);
        exit(2);
    }

    attached_payload_end = getAttachedPayloadEndOffset();

    if (unlikely(attached_payload_end < sizeof(attached_payload_size))) {
        fatalErrorHeaderAttachedData();
    }

    // Note: This is little endian data, which is what all platforms that use
    // this mode have in common.
    memcpy(&attached_payload_size, exe_file_mapped.data + attached_payload_end - sizeof(attached_payload_size),
           sizeof(attached_payload_size));

    if (unlikely(attached_payload_size >= attached_payload_end)) {
        fatalErrorHeaderAttachedData();
    }

    attached_payload_start = attached_payload_end - sizeof(attached_payload_size) - attached_payload_size;

    payload_data = exe_file_mapped.data + attached_payload_start;

    payload_size = attached_payload_size;
}

static void closePayloadData(void) { unmapFileFromMemory(&exe_file_mapped); }

#elif defined(_NUITKA_CONSTANTS_FROM_LINKER) || defined(_NUITKA_CONSTANTS_FROM_COFF_OBJ) ||                            \
    defined(_NUITKA_CONSTANTS_FROM_XCOFF_OBJ) || defined(_NUITKA_CONSTANTS_FROM_CODE) ||                               \
    defined(_NUITKA_CONSTANTS_FROM_INCBIN) || defined(_NUITKA_CONSTANTS_FROM_C23_EMBED) ||                             \
    defined(_NUITKA_CONSTANTS_FROM_MACOS_SECTION)

NUITKA_DECLARE_CONSTANT_BLOB(payload_bin, payload_bin, const)

// The payload blob size is a generated onefile build definition.
static void initPayloadData2(void) {
    payload_data = getpayload_binData();

    payload_size = (unsigned long long)_NUITKA_ONEFILE_PAYLOAD_SIZE_INT;
}

static void closePayloadData(void) {}

#elif _NUITKA_ONEFILE_HAS_PAYLOAD_BOOL == 0
// Note: There is no payload to unpack, either because there is none at all,
// or because the payload is in a separate file, the latter not implemented
// yet.
static void initPayloadData2(void) {}

static void closePayloadData(void) {}

#else
#error "Unknown resource mode"
#endif

static void initPayloadData(void) { initPayloadData2(); }

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1

static ZSTD_DCtx *dest_ctx = NULL;
static ZSTD_inBuffer input = {NULL, 0, 0};
static ZSTD_outBuffer output = {NULL, 0, 0};

static void initZSTD(void) {
    input.src = NULL;

    size_t const output_buffer_size = ZSTD_DStreamOutSize();
    output.dst = malloc(output_buffer_size);
    if (output.dst == NULL) {
        fatalErrorMemory();
    }

    dest_ctx = ZSTD_createDCtx();
    if (dest_ctx == NULL) {
        fatalErrorMemory();
    }
}

static void releaseZSTD(void) {
    ZSTD_freeDCtx(dest_ctx);

    free(output.dst);
}

#endif

#if _NUITKA_ONEFILE_HAS_PAYLOAD_BOOL == 1

// The payload starts with a table of contents. It is kept uncompressed, so
// cache validation and locating files does not require decompressing the
// payload body.
// The magic is only present in debug builds, it is a development aid only.
#if defined(_NUITKA_DEBUG)
#define ONEFILE_PAYLOAD_MAGIC "KAYKAY!"
#define ONEFILE_PAYLOAD_MAGIC_SIZE (sizeof(ONEFILE_PAYLOAD_MAGIC) - 1)
#else
#define ONEFILE_PAYLOAD_MAGIC_SIZE 0
#endif

#define ONEFILE_PAYLOAD_HEADER_SIZE (16 + ONEFILE_PAYLOAD_MAGIC_SIZE)

// Temporary mode has no checksums, so the CRC field is omitted there.
#if _NUITKA_ONEFILE_TEMP_BOOL == 0
#define ONEFILE_PAYLOAD_ENTRY_SIZE 16
#else
#define ONEFILE_PAYLOAD_ENTRY_SIZE 12
#endif

#define ONEFILE_PAYLOAD_ENTRY_FLAG_EXECUTABLE 1
#define ONEFILE_PAYLOAD_ENTRY_FLAG_SYMLINK 2
#define ONEFILE_PAYLOAD_ENTRY_FLAG_LAST 4

struct OnefilePayloadHeader {
    uint64_t toc_size;
    uint64_t body_size;
};

struct OnefilePayloadEntry {
    uint32_t flags;
    uint32_t crc32;
    uint64_t size;

    // Computed while parsing, not part of the serialized TOC.
    uint32_t name_length;
    uint32_t link_target_length;
};

static struct OnefilePayloadHeader payload_header;

static char const *payload_toc_start = NULL;
static char const *payload_toc_current = NULL;
static char const *payload_toc_end = NULL;
static char const *payload_body_start = NULL;
static char const *payload_body_current = NULL;
static char const *payload_body_end = NULL;

static uint32_t readPayloadUInt32(char const *data) {
    uint32_t result;

    memcpy(&result, data, sizeof(result));

    return result;
}

static uint64_t readPayloadUInt64(char const *data) {
    uint64_t result;

    memcpy(&result, data, sizeof(result));

    return result;
}

static void initPayloadHeader(void) {
    if (payload_size < ONEFILE_PAYLOAD_HEADER_SIZE) {
        fatalErrorHeaderAttachedData();
    }

    char const *header = (char const *)payload_data;

#if defined(_NUITKA_DEBUG)
    static char const magic[] = ONEFILE_PAYLOAD_MAGIC;

    if (memcmp(header, magic, ONEFILE_PAYLOAD_MAGIC_SIZE) != 0) {
        fatalErrorHeaderAttachedData();
    }

    header += ONEFILE_PAYLOAD_MAGIC_SIZE;
#endif

    payload_header.toc_size = readPayloadUInt64(header);
    payload_header.body_size = readPayloadUInt64(header + 8);

    if (payload_header.toc_size > payload_size - ONEFILE_PAYLOAD_HEADER_SIZE) {
        fatalErrorHeaderAttachedData();
    }

    if (payload_header.toc_size > 256 * 1024 * 1024) {
        fatalErrorHeaderAttachedData();
    }

    if (payload_header.body_size > payload_size - ONEFILE_PAYLOAD_HEADER_SIZE - payload_header.toc_size) {
        fatalErrorHeaderAttachedData();
    }

    payload_toc_start = (char const *)payload_data + ONEFILE_PAYLOAD_HEADER_SIZE;
    payload_toc_current = payload_toc_start;
    payload_toc_end = payload_toc_start + payload_header.toc_size;
    payload_body_start = payload_toc_end;
    payload_body_current = payload_body_start;
    payload_body_end = payload_body_start + payload_header.body_size;
}

static bool readPayloadEntry(struct OnefilePayloadEntry *entry, char const **name, char const **link_target,
                             bool *is_last) {
    if ((uint64_t)(payload_toc_end - payload_toc_current) < ONEFILE_PAYLOAD_ENTRY_SIZE) {
        return false;
    }

    entry->flags = readPayloadUInt32(payload_toc_current);

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
    entry->crc32 = readPayloadUInt32(payload_toc_current + 4);
    entry->size = readPayloadUInt64(payload_toc_current + 8);
#else
    entry->crc32 = 0;
    entry->size = readPayloadUInt64(payload_toc_current + 4);
#endif

    if ((entry->flags & ~(ONEFILE_PAYLOAD_ENTRY_FLAG_EXECUTABLE | ONEFILE_PAYLOAD_ENTRY_FLAG_SYMLINK |
                          ONEFILE_PAYLOAD_ENTRY_FLAG_LAST)) != 0) {
        return false;
    }

    char const *cursor = payload_toc_current + ONEFILE_PAYLOAD_ENTRY_SIZE;
    size_t name_characters = 0;

    for (;;) {
        if (name_characters >= 4096) {
            return false;
        }

        if ((uint64_t)(payload_toc_end - cursor) < (name_characters + 1) * sizeof(filename_char_t)) {
            return false;
        }

        filename_char_t character;
        memcpy(&character, cursor + name_characters * sizeof(filename_char_t), sizeof(character));

        if (character == 0) {
            break;
        }

        name_characters += 1;
    }

    if (name_characters == 0) {
        return false;
    }

    entry->name_length = (uint32_t)(name_characters * sizeof(filename_char_t));
    *name = cursor;
    cursor += entry->name_length + sizeof(filename_char_t);

    if ((entry->flags & ONEFILE_PAYLOAD_ENTRY_FLAG_SYMLINK) != 0) {
        size_t link_characters = 0;

        for (;;) {
            if (link_characters >= 4096) {
                return false;
            }

            if ((uint64_t)(payload_toc_end - cursor) < (link_characters + 1) * sizeof(filename_char_t)) {
                return false;
            }

            filename_char_t character;
            memcpy(&character, cursor + link_characters * sizeof(filename_char_t), sizeof(character));

            if (character == 0) {
                break;
            }

            link_characters += 1;
        }

        if (link_characters == 0) {
            return false;
        }

        entry->link_target_length = (uint32_t)(link_characters * sizeof(filename_char_t));
        *link_target = cursor;
        cursor += entry->link_target_length + sizeof(filename_char_t);
    } else {
        entry->link_target_length = 0;
        *link_target = NULL;
    }

    payload_toc_current = cursor;

    *is_last = (entry->flags & ONEFILE_PAYLOAD_ENTRY_FLAG_LAST) != 0;

    return true;
}

#if defined(_NUITKA_DEBUG)
// Reject names that could escape the payload directory. The payload is
// produced by the packer, but the attached data may be corrupted.
static bool isSafePayloadName(filename_char_t const *name, size_t name_length) {
    if (name_length == 0) {
        return false;
    }

    size_t component_start = 0;

    for (size_t i = 0; i <= name_length; i++) {
        bool is_separator = false;

        if (i == name_length) {
            is_separator = true;
        } else if (name[i] == FILENAME_SEP_CHAR) {
            is_separator = true;
        }
#if defined(_WIN32)
        else if (name[i] == '/') {
            is_separator = true;
        }
#endif

        if (is_separator) {
            size_t component_length = i - component_start;

            if (component_length == 0) {
                return false;
            }

            if (component_length == 1 && name[component_start] == '.') {
                return false;
            }

            if (component_length == 2 && name[component_start] == '.' && name[component_start + 1] == '.') {
                return false;
            }

#if defined(_WIN32)
            for (size_t j = component_start; j < i; j++) {
                if (name[j] == ':') {
                    return false;
                }
            }
#endif

            component_start = i + 1;
        }
    }

    return true;
}
#endif

static bool getPayloadTargetPath(char const *name, uint32_t name_length, filename_char_t *buffer, size_t buffer_size) {
    buffer[0] = 0;

    appendStringSafeFilename(buffer, payload_path, buffer_size);
    appendCharSafeFilename(buffer, FILENAME_SEP_CHAR, buffer_size);

    size_t offset = strlenFilename(buffer);
    size_t name_characters = name_length / sizeof(filename_char_t);

    if (offset + name_characters + 1 > buffer_size) {
        return false;
    }

    memcpy(buffer + offset, name, name_length);
    buffer[offset + name_characters] = 0;

#if defined(_NUITKA_DEBUG)
    return isSafePayloadName(buffer + offset, name_characters);
#else
    return true;
#endif
}

static void readPayloadChunk(void *buffer, size_t size) {
#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
    bool end_of_buffer = false;

    // Loop until finished with asked chunk.
    while (size > 0) {
        size_t available = output.size - output.pos;

        // Consider available data.
        if (available != 0) {
            size_t use = available;
            if (size < use) {
                use = size;
            }

            memcpy(buffer, ((char *)output.dst) + output.pos, use);
            buffer = (void *)(((char *)buffer) + use);
            size -= use;

            output.pos += use;

            continue;
        }

        // Nothing available, make sure to make it available from existing input.
        if (input.pos < input.size || end_of_buffer) {
            output.pos = 0;
            output.size = ZSTD_DStreamOutSize();

            size_t const ret = ZSTD_decompressStream(dest_ctx, &output, &input);
            end_of_buffer = (output.pos == output.size);

            if (ZSTD_isError(ret)) {
                fatalErrorAttachedData();
            }

            output.size = output.pos;
            output.pos = 0;

            continue;
        }

        fatalErrorAttachedData();
    }
#else
    if (size > (size_t)(payload_body_end - payload_body_current)) {
        fatalErrorHeaderAttachedData();
    }

    memcpy(buffer, payload_body_current, size);
    payload_body_current += size;
#endif
}

static void writeSequentialPayloadFile(FILE_HANDLE target_file, unsigned long long file_size) {
    while (file_size > 0) {
        static char chunk[32768];

        size_t chunk_size;

        // Doing min manually, as otherwise the compiler is confused from types.
        if (file_size <= sizeof(chunk)) {
            chunk_size = (size_t)file_size;
        } else {
            chunk_size = sizeof(chunk);
        }

        readPayloadChunk(chunk, chunk_size);

        if (target_file != FILE_HANDLE_NULL) {
            if (writeFileChunk(target_file, chunk, chunk_size) == false) {
                fatalErrorTempFiles();
            }
        }

        file_size -= chunk_size;
    }
}

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
static void makeProcessTemporaryFilename(filename_char_t *buffer, filename_char_t const *filename, size_t buffer_size) {
    copyStringSafeFilename(buffer, filename, buffer_size);
    appendCharSafeFilename(buffer, '.', buffer_size);
#if defined(_WIN32)
    {
        wchar_t pid_buffer[32];
        _snwprintf(pid_buffer, sizeof(pid_buffer) / sizeof(wchar_t), L"tmp%lu", (unsigned long)GetCurrentProcessId());
        pid_buffer[31] = 0;
        appendWStringSafeW(buffer, pid_buffer, buffer_size);
    }
#else
    {
        char pid_buffer[32];
        snprintf(pid_buffer, sizeof(pid_buffer), "tmp%ld", (long)getpid());
        appendStringSafe(buffer, pid_buffer, buffer_size);
    }
#endif
}

static bool replaceFileAtomically(filename_char_t const *source, filename_char_t const *dest) {
#if defined(_WIN32)
    return MoveFileExW(source, dest, MOVEFILE_REPLACE_EXISTING) != 0;
#else
    return renameFile(source, dest);
#endif
}

// Unpacked files get the current time with the CRC32 in the sub-second part,
// which allows cached mode to validate them without reading or decompressing
// them.
#define ONEFILE_PAYLOAD_MTIME_WINDOWS_MODULO 10000000ULL
#define ONEFILE_PAYLOAD_MTIME_POSIX_MODULO 1000000ULL

struct OnefilePayloadFileIdentity {
    uint64_t size;
    uint64_t subsecond;
    bool is_regular;
};

static bool getPayloadFileIdentity(filename_char_t const *filename, struct OnefilePayloadFileIdentity *identity) {
#if defined(_WIN32)
    WIN32_FILE_ATTRIBUTE_DATA data;

    if (GetFileAttributesExW(filename, GetFileExInfoStandard, &data) == 0) {
        return false;
    }

    if ((data.dwFileAttributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)) != 0) {
        return false;
    }

    uint64_t mtime = ((uint64_t)data.ftLastWriteTime.dwHighDateTime << 32) | data.ftLastWriteTime.dwLowDateTime;

    identity->size = ((uint64_t)data.nFileSizeHigh << 32) | data.nFileSizeLow;
    identity->subsecond = mtime % ONEFILE_PAYLOAD_MTIME_WINDOWS_MODULO;
    identity->is_regular = true;
#else
    struct stat stat_buffer;

    if (lstat(filename, &stat_buffer) != 0) {
        return false;
    }

    identity->size = (uint64_t)stat_buffer.st_size;

#if defined(__APPLE__)
    identity->subsecond = (uint64_t)stat_buffer.st_mtimespec.tv_nsec;
#elif defined(__linux__) || defined(__FreeBSD__) || defined(__NetBSD__) || defined(__OpenBSD__) ||                     \
    defined(__DragonFly__)
    identity->subsecond = (uint64_t)stat_buffer.st_mtim.tv_nsec;
#else
    identity->subsecond = 0;
#endif

    identity->is_regular = S_ISREG(stat_buffer.st_mode);
#endif

    return true;
}

static void setPayloadFileTimeFromCrc(filename_char_t const *filename, uint32_t crc32) {
#if defined(_WIN32)
    HANDLE handle = CreateFileW(filename, FILE_WRITE_ATTRIBUTES, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

    if (handle != INVALID_HANDLE_VALUE) {
        FILETIME now;
        GetSystemTimeAsFileTime(&now);

        uint64_t file_time = ((uint64_t)now.dwHighDateTime << 32) | now.dwLowDateTime;
        file_time -= file_time % ONEFILE_PAYLOAD_MTIME_WINDOWS_MODULO;
        file_time += crc32 % ONEFILE_PAYLOAD_MTIME_WINDOWS_MODULO;

        FILETIME last_write_time;
        last_write_time.dwLowDateTime = (DWORD)file_time;
        last_write_time.dwHighDateTime = (DWORD)(file_time >> 32);

        SetFileTime(handle, NULL, NULL, &last_write_time);
        CloseHandle(handle);
    }
#else
    time_t now = time(NULL);

    if (unlikely(now == (time_t)-1)) {
        return;
    }

    struct timeval times[2];
    times[0].tv_sec = now;
    times[0].tv_usec = (long)(crc32 % ONEFILE_PAYLOAD_MTIME_POSIX_MODULO);
    times[1] = times[0];

    utimes(filename, times);
#endif
}

// Check if the unpacked files still match the payload table of contents. Only
// metadata is examined, no payload data is decompressed or read.
static bool checkPayloadCache(filename_char_t *first_filename, size_t first_filename_size) {
    static filename_char_t target_path[4096];

    bool first = true;

    payload_toc_current = payload_toc_start;

    bool is_last = false;

    while (is_last == false && payload_header.toc_size != 0) {
        struct OnefilePayloadEntry entry;
        char const *name;
        char const *link_target;

        if (readPayloadEntry(&entry, &name, &link_target, &is_last) == false) {
            return false;
        }

        if (getPayloadTargetPath(name, entry.name_length, target_path, sizeof(target_path) / sizeof(filename_char_t)) ==
            false) {
            return false;
        }

        if ((entry.flags & ONEFILE_PAYLOAD_ENTRY_FLAG_SYMLINK) != 0) {
#if !defined(_WIN32) && !defined(__MSYS__)
            char link_buffer[4096];

            ssize_t link_length = readlink(target_path, link_buffer, sizeof(link_buffer));

            if (link_length < 0 || (uint64_t)link_length != entry.link_target_length ||
                memcmp(link_buffer, link_target, entry.link_target_length) != 0) {
                return false;
            }
#else
            return false;
#endif
        } else {
            struct OnefilePayloadFileIdentity identity;

            if (entry.crc32 == 0) {
                return false;
            }

            if (getPayloadFileIdentity(target_path, &identity) == false || identity.is_regular == false ||
                identity.size != entry.size) {
                return false;
            }

#if defined(_WIN32)
            if (identity.subsecond != entry.crc32 % ONEFILE_PAYLOAD_MTIME_WINDOWS_MODULO) {
                return false;
            }
#else
            if (identity.subsecond / 1000 != entry.crc32 % ONEFILE_PAYLOAD_MTIME_POSIX_MODULO) {
                return false;
            }
#endif
        }

        if (first && first_filename[0] == 0) {
            copyStringSafeFilename(first_filename, target_path, first_filename_size);
        }

        first = false;
    }

    return first == false && payload_toc_current == payload_toc_end;
}
#endif
#endif

// Zero means, not yet created, created unsuccessfully, terminated already.
#if defined(_WIN32)
HANDLE handle_process = 0;
#else
pid_t handle_process = 0;
#endif

#if _NUITKA_ONEFILE_TEMP_BOOL
static bool payload_created = false;
#endif

#define MAX_CREATED_DIRS 1024
static filename_char_t *created_dir_paths[MAX_CREATED_DIRS];
int created_dir_count = 0;

static bool createDirectory(filename_char_t const *path) {
    bool bool_res;

#if defined(_WIN32)
    if (created_dir_count == 0) {
        filename_char_t home_path[4096];
        wchar_t *pattern = L"{HOME}";

        bool_res = expandTemplatePathFilename(home_path, pattern, sizeof(payload_path) / sizeof(filename_char_t));

        if (unlikely(bool_res == false)) {
            fatalErrorSpec(pattern);
        }

        created_dir_paths[created_dir_count] = wcsdup(home_path);
        created_dir_count += 1;
    }
#endif

    for (int i = 0; i < created_dir_count; i++) {
        if (strcmpFilename(path, created_dir_paths[i]) == 0) {
            return true;
        }
    }

#if defined(_WIN32)
    // On Windows, lets not try to create drive letters.
    if (strlenFilename(path) == 2 && path[1] == L':') {
        return true;
    }
#endif

#if defined(_WIN32)
    bool_res = CreateDirectoryW(path, NULL);

    if (bool_res == false && GetLastError() == 183) {
        bool_res = true;
    }
#else
    if (access(path, F_OK) != -1) {
        bool_res = true;
    } else {
        bool_res = mkdir(path, 0700) == 0;
    }
#endif

    if (bool_res != false && created_dir_count < MAX_CREATED_DIRS) {
        created_dir_paths[created_dir_count] = strdupFilename(path);
        created_dir_count += 1;
    }

    return bool_res;
}

static bool createContainingDirectory(filename_char_t const *path) {
    filename_char_t dir_path[4096] = {0};
    dir_path[0] = 0;

    appendStringSafeFilename(dir_path, path, sizeof(dir_path) / sizeof(filename_char_t));

    filename_char_t *w = dir_path + strlenFilename(dir_path);

    while (w > dir_path) {
        if (*w == FILENAME_SEP_CHAR) {
            *w = 0;

            bool res = createDirectory(dir_path);
            if (res != false) {
                return true;
            }

            createContainingDirectory(dir_path);
            return createDirectory(dir_path);
        }

        w--;
    }

    return true;
}

#if _NUITKA_ONEFILE_TEMP_BOOL
#if defined(_WIN32)

static bool _removeDirectoryOnce(wchar_t const *path) {
    DWORD attributes = GetFileAttributesW(path);

    if (attributes == INVALID_FILE_ATTRIBUTES) {
        return true;
    }

    // Never follow reparse points, remove the link itself instead.
    if ((attributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0) {
        if ((attributes & FILE_ATTRIBUTE_DIRECTORY) != 0) {
            return RemoveDirectoryW(path) != 0;
        } else {
            return DeleteFileW(path) != 0;
        }
    }

    if ((attributes & FILE_ATTRIBUTE_DIRECTORY) == 0) {
        return DeleteFileW(path) != 0;
    }

    wchar_t pattern[4096];
    pattern[0] = 0;
    appendWStringSafeW(pattern, path, sizeof(pattern) / sizeof(wchar_t));
    appendWStringSafeW(pattern, L"\\*", sizeof(pattern) / sizeof(wchar_t));

    WIN32_FIND_DATAW find_data;
    HANDLE find_handle = FindFirstFileW(pattern, &find_data);

    if (find_handle == INVALID_HANDLE_VALUE) {
        return false;
    }

    bool success = true;

    do {
        if (wcscmp(find_data.cFileName, L".") == 0 || wcscmp(find_data.cFileName, L"..") == 0) {
            continue;
        }

        wchar_t child_path[4096];
        child_path[0] = 0;
        appendWStringSafeW(child_path, path, sizeof(child_path) / sizeof(wchar_t));
        appendWStringSafeW(child_path, L"\\", sizeof(child_path) / sizeof(wchar_t));
        appendWStringSafeW(child_path, find_data.cFileName, sizeof(child_path) / sizeof(wchar_t));

        if (_removeDirectoryOnce(child_path) == false) {
            success = false;
        }
    } while (FindNextFileW(find_handle, &find_data));

    FindClose(find_handle);

    if (RemoveDirectoryW(path) == 0) {
        success = false;
    }

    return success;
}

static void removeDirectory(wchar_t const *path) {
    for (int i = 0; i < 20; i++) {
        if (_removeDirectoryOnce(path)) {
            break;
        }

        // Delay 0.1s before trying again.
        Sleep(100);
    }
}

#else
static int removeDirectory(char const *path) {
    DIR *d = opendir(path);
    size_t path_len = strlen(path);

    int r = -1;

    if (d != NULL) {
        struct dirent *p;

        r = 0;
        while (!r && (p = readdir(d))) {
            int r2 = -1;

            size_t len;

            // Ignore special names
            if (!strcmp(p->d_name, ".") || !strcmp(p->d_name, "..")) {
                continue;
            }

            len = path_len + strlen(p->d_name) + 2;
            char *buf = (char *)malloc(len);

            if (buf == NULL) {
                fatalErrorMemory();
            }

            struct stat statbuf;

            snprintf(buf, len, "%s/%s", path, p->d_name);

            if (!lstat(buf, &statbuf)) {
                if (S_ISDIR(statbuf.st_mode))
                    r2 = removeDirectory(buf);
                else
                    r2 = unlink(buf);
            }
            free(buf);
            r = r2;
        }
        closedir(d);
    }

    if (!r) {
        rmdir(path);
    }

    return r;
}
#endif
#endif

#if !defined(_WIN32)
// When the child is reaped while handling a signal, the main waitpid no
// longer sees its status, so it is recorded here for the exit code.
static volatile sig_atomic_t reaped_child_status = 0;
static volatile sig_atomic_t reaped_child_status_valid = 0;

static int waitpid_retried(pid_t pid, int *status, bool async) {
    int res;

    for (;;) {
        if (status != NULL) {
            *status = 0;
        }

        res = waitpid(pid, status, async ? WNOHANG : 0);

        if ((res == -1) && (errno == EINTR)) {
            continue;
        }

        break;
    }

    return res;
}

static int waitpid_timeout(pid_t pid) {
    int status;
    int res = waitpid_retried(pid, &status, true);

    // Child can already be gone when cleanup is entered from signal handling or
    // when an earlier wait has already collected it for us.
    if (res == -1) {
        if (errno != ECHILD) {
            perror("waitpid");

            return -1;
        }

        return 0;
    }

    if (res != 0) {
        reaped_child_status = status;
        reaped_child_status_valid = 1;

        return 0;
    }

    // A value of -1 means wait indefinitely.
    if (_NUITKA_ONEFILE_CHILD_GRACE_TIME_INT == -1) {
        res = waitpid_retried(pid, &status, false);

        if (res == -1 && errno != ECHILD) {
            perror("waitpid");

            return -1;
        }

        if (res > 0) {
            reaped_child_status = status;
            reaped_child_status_valid = 1;
        }

        return 0;
    }

    // Checking 5 times per second should be good enough.
    long ns = 200000000L; // 0.2s

    // Seconds, nanoseconds from our milliseconds value.
    struct timespec timeout = {
        _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT / 1000,
        (_NUITKA_ONEFILE_CHILD_GRACE_TIME_INT % 1000) * 1000,
    };
    struct timespec delay = {0, ns};
    struct timespec elapsed = {0, 0};
    struct timespec rem;

    do {
        // Only want to care about SIGCHLD here.
        res = waitpid_retried(pid, &status, true);

        if (unlikely(res < 0)) {
            if (errno == ECHILD) {
                return 0;
            }

            perror("waitpid");

            return -1;
        }

        if (res != 0) {
            reaped_child_status = status;
            reaped_child_status_valid = 1;

            break;
        }

        nanosleep(&delay, &rem);

        elapsed.tv_sec += (elapsed.tv_nsec + ns) / 1000000000L;
        elapsed.tv_nsec = (elapsed.tv_nsec + ns) % 1000000000L;
    } while (elapsed.tv_sec < timeout.tv_sec ||
             (elapsed.tv_sec == timeout.tv_sec && elapsed.tv_nsec < timeout.tv_nsec));

    return 0;
}
#endif

static void cleanupChildProcess(bool send_sigint) {

    // Cause KeyboardInterrupt in the child process.
    if (handle_process != 0) {

        if (send_sigint) {
#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
            puts("Sending CTRL-C to child\n");
#endif

#if defined(_WIN32)
            BOOL res = GenerateConsoleCtrlEvent(CTRL_C_EVENT, GetProcessId(handle_process));

            if (res == false) {
                printOSErrorMessage("Failed to send CTRL-C to child process.", GetLastError());
                // No error exit is done, we still want to cleanup when it does exit
            }
#else
            kill(handle_process, SIGINT);
#endif
        }

        // TODO: We ought to only need to wait if there is a need to cleanup
        // files when we are on Windows, on Linux maybe exec can be used so
        // this process to exist anymore if there is nothing to do.
#if _NUITKA_ONEFILE_TEMP_BOOL || 1
        NUITKA_PRINT_TRACE("Waiting for child to exit.\n");
#if defined(_WIN32) && _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT == -1
        WaitForSingleObject(handle_process, INFINITE);
#elif defined(_WIN32)
        if (WaitForSingleObject(handle_process, _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT) != 0) {
            TerminateProcess(handle_process, 0);
        }

        CloseHandle(handle_process);
#else
        waitpid_timeout(handle_process);

#if _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT != -1
        kill(handle_process, SIGKILL);
#endif
#endif
        NUITKA_PRINT_TRACE("Child is exited.\n");
#endif
    }

#if _NUITKA_ONEFILE_TEMP_BOOL
    if (payload_created) {
#if _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        wprintf(L"Removing payload path '%lS'\n", payload_path);
#endif
        removeDirectory(payload_path);
    }
#endif
}

#if defined(_WIN32)
BOOL WINAPI ourConsoleCtrlHandler(DWORD fdwCtrlType) {
    NUITKA_PRINT_TIMING("ONEFILE: ourConsoleCtrlHandler().");

    switch (fdwCtrlType) {
        // Handle the CTRL-C signal.
    case CTRL_C_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-C event");
#endif
        cleanupChildProcess(false);
        return FALSE;

        // CTRL-CLOSE: confirm that the user wants to exit.
    case CTRL_CLOSE_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Close event");
#endif
        cleanupChildProcess(false);
        return FALSE;

        // Pass other signals to the next handler.
    case CTRL_BREAK_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Break event");
#endif
        cleanupChildProcess(false);
        return FALSE;

    case CTRL_LOGOFF_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Logoff event");
#endif
        cleanupChildProcess(false);
        return FALSE;

    case CTRL_SHUTDOWN_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Shutdown event");
#endif
        cleanupChildProcess(false);
        return FALSE;

    default:
        return FALSE;
    }
}

#else
void ourConsoleCtrlHandler(int sig, siginfo_t *info, void *ucontext) {
#if defined(SI_KERNEL)
    bool signal_from_terminal = (info->si_code == SI_KERNEL);
#elif defined(__APPLE__)
    // On macOS, both terminal-originated signals and kill(2) deliver
    // si_code == 0, so they cannot be told apart. Always forward and
    // let the child suppress the duplicate SIGINT it already received
    // from the terminal process group.
    bool signal_from_terminal = false;
#else
    // On BSD, terminal-originated signals have si_code == 0, while
    // kill(2) sends with si_code == SI_USER.
    bool signal_from_terminal = (info->si_code == 0);
#endif

    // Forward to child only when the signal did NOT originate from the
    // terminal kernel delivery. Terminal signals (Ctrl+C) are delivered
    // to the foreground process group, so both parent and child already
    // receive them. Targeted signals (kill(2), Docker) only reach this
    // process and must be forwarded.
    cleanupChildProcess(!signal_from_terminal);
}
#endif

#ifdef _NUITKA_ONEFILE_SPLASH_SCREEN
#ifdef __cplusplus
extern "C" {
#endif
extern void initSplashScreen(void);
extern bool checkSplashScreen(void);
#ifdef __cplusplus
}
#endif
#endif

#ifdef _WIN32

static bool containsWStringAny(wchar_t const *source, wchar_t const *characters) {
    while (*characters) {
        if (wcschr(source, *characters) != NULL) {
            return true;
        }

        characters++;
    }

    return false;
}

static wchar_t *getCommandLineForChildProcess(void) {

    wchar_t *orig_command_line = GetCommandLineW();
#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
    wprintf(L"Command line was '%ls'\n", orig_command_line);
#endif

    int argc;
    LPWSTR *argv = CommandLineToArgvW(orig_command_line, &argc);
    assert(argv != NULL);
    assert(argc > 0);

    static wchar_t result[32768];
    result[0] = 0;

    // Assigning constant value to there, strongly hoping nothing ever modifies
    // the contents.
    argv[0] = (wchar_t *)getBinaryPath();

    for (int i = 0; i < argc; i++) {
        if (i >= 1) {
            appendWCharSafeW(result, L' ', sizeof(result) / sizeof(wchar_t));
        }

        bool needs_quote = containsWStringAny(argv[i], L" \t\n\v\"");

#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
        wprintf(L"Command line arg %d was '%ls' needs quoting %ls\n", i, argv[i], needs_quote ? L"yes" : L"no");
#endif

        if (needs_quote) {
            appendWCharSafeW(result, L'"', sizeof(result) / sizeof(wchar_t));

            wchar_t const *current = argv[i];

            for (;;) {
                int backslash_count = 0;

                while (*current == L'\\') {
                    current++;
                    backslash_count += 1;
                }

                if (*current == 0) {
                    for (int j = 0; j < backslash_count * 2; j++) {
                        appendWCharSafeW(result, L'\\', sizeof(result) / sizeof(wchar_t));
                    }

                    break;
                } else if (*current == L'"') {
                    for (int j = 0; j < backslash_count * 2 + 1; j++) {
                        appendWCharSafeW(result, L'\\', sizeof(result) / sizeof(wchar_t));
                    }
                } else {
                    for (int j = 0; j < backslash_count; j++) {
                        appendWCharSafeW(result, L'\\', sizeof(result) / sizeof(wchar_t));
                    }
                }

                appendWCharSafeW(result, *current, sizeof(result) / sizeof(wchar_t));

                current++;
            }

            appendWCharSafeW(result, L'"', sizeof(result) / sizeof(wchar_t));

        } else {
            appendWStringSafeW(result, argv[i], sizeof(result) / sizeof(wchar_t));
        }
    }

#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
    wprintf(L"Command line composed to '%ls'\n", result);
#endif
    return result;
}
#endif

#if _NUITKA_ONEFILE_DLL_MODE
static int runPythonCodeDLL(filename_char_t const *dll_filename, int argc, native_command_line_argument_t **argv) {

#if defined(_WIN32)
    DLL_DIRECTORY_COOKIE dll_dir_cookie = AddDllDirectory(payload_path);
    assert(dll_dir_cookie != 0);

    HINSTANCE hGetProcIDDLL =
        LoadLibraryExW(dll_filename, NULL,
                       LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32 | LOAD_LIBRARY_SEARCH_USER_DIRS);

    if (!hGetProcIDDLL) {
        fatalIOError("Error, load DLL.", getLastErrorCode());
    }

    typedef int(__stdcall * nuitka_dll_function_ptr)(int, wchar_t **, wchar_t const *);

    // Avoid a cast between incompatible function types, which newer compilers
    // warn about.
    union {
        FARPROC as_proc;
        nuitka_dll_function_ptr as_function;
    } dll_function;

#if defined(_NUITKA_ONEFILE_DLL_RUN_CODE_ORDINAL_INT)
    dll_function.as_proc = GetProcAddress(hGetProcIDDLL, MAKEINTRESOURCEA(_NUITKA_ONEFILE_DLL_RUN_CODE_ORDINAL_INT));
#else
    dll_function.as_proc = GetProcAddress(hGetProcIDDLL, "run_code");
#endif

    if (dll_function.as_function == NULL) {
        fatalError("Error, DLL entry point not found.");
    }

    return (*dll_function.as_function)(argc, argv, dll_filename);
#else
    typedef int (*nuitka_dll_function_ptr)(int, native_command_line_argument_t **, filename_char_t const *);

    void *handle = dlopen(dll_filename, RTLD_LOCAL | RTLD_NOW);

    if (unlikely(handle == NULL)) {
        const char *error = dlerror();

        if (unlikely(error == NULL)) {
            error = "unknown dlopen() error";
        }

        fatalError(error);
    }

    nuitka_dll_function_ptr nuitka_dll_function = (nuitka_dll_function_ptr)dlsym(handle, "run_code");
    assert(nuitka_dll_function);

    return (*nuitka_dll_function)(argc, argv, dll_filename);
#endif
}
#endif

#if defined(__OpenBSD__) || defined(_AIX) || defined(_NUITKA_EXPERIMENTAL_FORCE_UNIX_BINARY_NAME)
#define NEEDS_ORIGINAL_ARGV0
#endif

#if defined(NEEDS_ORIGINAL_ARGV0)
static native_command_line_argument_t const *original_argv0 = NULL;

native_command_line_argument_t const *getOriginalArgv0(void) {
    assert(original_argv0 != NULL);
    return original_argv0;
}
#endif

#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, wchar_t *lpCmdLine, int nCmdShow) {
    int argc = __argc;
    wchar_t **argv = __wargv;

    NUITKA_UNREFERENCED_PARAMETER(argc);
#else
#if defined(_WIN32)
int wmain(int argc, wchar_t **argv) {
    NUITKA_UNREFERENCED_PARAMETER(argc);
#else
int main(int argc, char **argv) {
#endif
#endif

#if defined(_WIN32)
    // We want to force the loading of the DLLs from the payload directory only
    // ideally, but Windows is not good at allowing %PATH% changes to be
    // followed if we do that. So we remove only the CWD, but that is the best
    // we can do while allowing os.environ["PATH"] updates to be still used and
    // updated by Python.
    SetDllDirectoryW(L"");
#endif

#if defined(NEEDS_ORIGINAL_ARGV0)
    original_argv0 = argv[0];
#endif

    // Hide the console window if asked to do so.
#if defined(_NUITKA_HIDE_CONSOLE_WINDOW)
    hideConsoleIfSpawned();
#endif

    // Attach to the parent console respecting redirection only, otherwise we cannot
    // even output traces.
#if defined(_WIN32) && defined(_NUITKA_ATTACH_CONSOLE_WINDOW)
    inheritAttachedConsole();
#endif

    // NUITKA_ONEFILE_INIT_EARLY(argc, argv);

    NUITKA_PRINT_TIMING("ONEFILE: Entered main().");

#if _NUITKA_ONEFILE_DLL_MODE
    NUITKA_PRINT_TIMING("ONEFILE: Checking role of process.");
    environment_char_t const *process_role = getEnvironmentVariable("NUITKA_ONEFILE_PARENT");

    // Empty strings do not count.
    if (process_role != NULL && *process_role == 0) {
        process_role = NULL;
    }

#if defined(_WIN32)
    if (process_role != NULL) {
        long onefile_parent_pid;

        if (getEnvironmentVariableValueAsLong(process_role, &onefile_parent_pid)) {
            HANDLE parent_process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, onefile_parent_pid);

            if (parent_process != NULL) {
                filename_char_t onefile_parent_path[2048];

                DWORD len = GetModuleFileNameExW(parent_process, NULL, onefile_parent_path,
                                                 sizeof(onefile_parent_path) / sizeof(onefile_parent_path[0]));

                if (len == 0) {
                    process_role = NULL;
                } else {
                    resolveFileSymbolicLink(onefile_parent_path, onefile_parent_path,
                                            sizeof(onefile_parent_path) / sizeof(wchar_t), true);
                    makeShortDirFilename(onefile_parent_path, sizeof(onefile_parent_path) / sizeof(wchar_t));
                }

                if (strcmpFilename(onefile_parent_path, getBinaryFilenameWideChars(true)) != 0) {
                    process_role = NULL;
                }
            } else {
                process_role = NULL;
            }

            CloseHandle(parent_process);
        } else {
            process_role = NULL;
        }

        if (process_role != NULL) {
            NUITKA_PRINT_TIMING("ONEFILE: Decided we child environment.");
        }
    }
#endif
#else
    // TODO: Only Windows has the solved so far, it's also the only platform we
    // use it on right now.
    environment_char_t const *process_role = NULL;
#endif

    // Pass our pid value to the child. If we exit for some reason, re-parenting
    // might change it by the time the child looks at its parent and we will use it
    // for calculating the template path potentially as well.
    if (process_role == NULL) {
        NUITKA_PRINT_TIMING("ONEFILE: Removing other onefile environment.");

        unsetEnvironmentVariable("NUITKA_ONEFILE_START");
        unsetEnvironmentVariable("NUITKA_ONEFILE_TIME_US");
        unsetEnvironmentVariable("NUITKA_ONEFILE_RANDOM");

#if defined(_WIN32)
        setEnvironmentVariableFromLong("NUITKA_ONEFILE_PARENT", GetCurrentProcessId());
#else
        setEnvironmentVariableFromLong("NUITKA_ONEFILE_PARENT", (long)getpid());
#endif
    }

    filename_char_t const *pattern = FILENAME_EMPTY_STR _NUITKA_ONEFILE_TEMP_SPEC;
    bool bool_res = expandTemplatePathFilename(payload_path, pattern, sizeof(payload_path) / sizeof(filename_char_t));

#if defined(_WIN32)
    makeAbsolutePath(payload_path, sizeof(payload_path) / sizeof(filename_char_t));
#endif

    // _putws(payload_path);

    // If we are the onefile initial bootstrap binary, show the splash screen.
#if defined(_NUITKA_ONEFILE_SPLASH_SCREEN) && _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
    if (process_role == NULL) {
        initSplashScreen();
    }
#endif

#if _NUITKA_ONEFILE_HAS_PAYLOAD_BOOL == 1
    NUITKA_PRINT_TIMING("ONEFILE: Unpacking payload.");
    initPayloadData();
#endif

    static filename_char_t first_filename[4096] = {0};

#ifdef _NUITKA_ONEFILE_MAIN_FILENAME
    appendStringSafeFilename(first_filename, payload_path, sizeof(first_filename) / sizeof(filename_char_t));
    appendCharSafeFilename(first_filename, FILENAME_SEP_CHAR, sizeof(first_filename) / sizeof(filename_char_t));
    appendStringSafeFilename(first_filename, _NUITKA_ONEFILE_MAIN_FILENAME,
                             sizeof(first_filename) / sizeof(filename_char_t));

    // Run the Python code DLL if we are the child process, no unpacking needed
#if _NUITKA_ONEFILE_DLL_MODE
    if (process_role != NULL) {
        return runPythonCodeDLL(first_filename, argc, argv);
    }
#endif
#endif

    if (unlikely(bool_res == false)) {
        fatalErrorSpec(pattern);
    }

#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
    wprintf(L"payload path: '" FILENAME_FORMAT_STR "'\n", payload_path);
#endif

    if (process_role == NULL) {
#if defined(_WIN32)
        bool_res = SetConsoleCtrlHandler(ourConsoleCtrlHandler, true);
        if (bool_res == false) {
            fatalError("Error, failed to register signal handler.");
        }
#else
        {
            struct sigaction sa;
            sa.sa_sigaction = ourConsoleCtrlHandler;
            sa.sa_flags = SA_SIGINFO;
            sigemptyset(&sa.sa_mask);

            sigaction(SIGINT, &sa, NULL);
            sigaction(SIGQUIT, &sa, NULL);
            sigaction(SIGTERM, &sa, NULL);
        }
#endif
    }

    // The onefile bootstrap is setup now.

#if _NUITKA_ONEFILE_HAS_PAYLOAD_BOOL == 1
    NUITKA_PRINT_TIMING("ONEFILE: Reading payload header.");

    initPayloadHeader();

    bool payload_cached = false;

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
    NUITKA_PRINT_TIMING("ONEFILE: Checking payload cache.");

    payload_cached = checkPayloadCache(first_filename, sizeof(first_filename) / sizeof(filename_char_t));

    if (payload_cached) {
        NUITKA_PRINT_TIMING("ONEFILE: Cached payload is unchanged.");
    }
#endif

    if (payload_cached == false) {
        NUITKA_PRINT_TIMING("ONEFILE: Unpacking payload.");

#if _NUITKA_ONEFILE_TEMP_BOOL
        payload_created = true;
#endif

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
        initZSTD();

        input.src = payload_body_start;
        input.pos = 0;

        // TODO: Ought to assert that this doesn't truncate anything.
        input.size = (size_t)payload_header.body_size;
#endif

        payload_toc_current = payload_toc_start;

        bool is_last = false;

        while (is_last == false && payload_header.toc_size != 0) {
            struct OnefilePayloadEntry entry;
            char const *name;
            char const *link_target;

            if (readPayloadEntry(&entry, &name, &link_target, &is_last) == false) {
                fatalErrorHeaderAttachedData();
            }

            static filename_char_t target_path[4096] = {0};
#if _NUITKA_ONEFILE_TEMP_BOOL == 0
            static filename_char_t target_path_tmp[4096] = {0};
#endif

            if (getPayloadTargetPath(name, entry.name_length, target_path,
                                     sizeof(target_path) / sizeof(filename_char_t)) == false) {
                fatalErrorHeaderAttachedData();
            }

            if (first_filename[0] == 0) {
                appendStringSafeFilename(first_filename, target_path, sizeof(first_filename) / sizeof(filename_char_t));

                // Run the Python code DLL if it's already unpacked.
#if _NUITKA_ONEFILE_DLL_MODE
                if (process_role != NULL) {
                    return runPythonCodeDLL(first_filename, argc, argv);
                }
#endif
            }

            if ((entry.flags & ONEFILE_PAYLOAD_ENTRY_FLAG_SYMLINK) != 0) {
#if !defined(_WIN32) && !defined(__MSYS__)
                char link_target_path[4096];

                if (entry.link_target_length + 1 > sizeof(link_target_path)) {
                    fatalErrorHeaderAttachedData();
                }

                memcpy(link_target_path, link_target, entry.link_target_length);
                link_target_path[entry.link_target_length] = 0;

                createContainingDirectory(target_path);

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
                makeProcessTemporaryFilename(target_path_tmp, target_path,
                                             sizeof(target_path_tmp) / sizeof(filename_char_t));

                unlink(target_path_tmp);
                if (symlink(link_target_path, target_path_tmp) != 0) {
                    fatalErrorTempFileCreate(target_path_tmp);
                }
                if (replaceFileAtomically(target_path_tmp, target_path) == false) {
                    unlink(target_path_tmp);
                    fatalErrorTempFileCreate(target_path);
                }
#else
                unlink(target_path);
                if (symlink(link_target_path, target_path) != 0) {
                    fatalErrorTempFileCreate(target_path);
                }
#endif
#else
                fatalErrorHeaderAttachedData();
#endif

                continue;
            }

            bool needs_write = true;

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
            if (entry.crc32 != 0 && getFileCRC32(target_path) == entry.crc32) {
                needs_write = false;

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
                fprintf(stderr, "CACHE HIT for '" FILENAME_FORMAT_STR "'.\n", target_path);
#endif
            } else {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
                fprintf(stderr, "CACHE MISS for '" FILENAME_FORMAT_STR "'.\n", target_path);
#endif
            }
#endif

            FILE_HANDLE target_file = FILE_HANDLE_NULL;

            if (needs_write) {
                createContainingDirectory(target_path);

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
                makeProcessTemporaryFilename(target_path_tmp, target_path,
                                             sizeof(target_path_tmp) / sizeof(filename_char_t));
                target_file = createFileForWritingChecked(target_path_tmp);
#else
                target_file = createFileForWritingChecked(target_path);
#endif
            }

            writeSequentialPayloadFile(target_file, entry.size);

#if !defined(_WIN32) && !defined(__MSYS__)
            if ((entry.flags & ONEFILE_PAYLOAD_ENTRY_FLAG_EXECUTABLE) && (target_file != FILE_HANDLE_NULL)) {
                int fd = fileno(target_file);

                struct stat stat_buffer;
                int res = fstat(fd, &stat_buffer);

                if (res == -1) {
                    printOSErrorMessage("fstat", errno);
                }

                // User shall be able to execute if at least.
                stat_buffer.st_mode |= S_IXUSR;

                // Follow read flags for group, others according to umask.
                if ((stat_buffer.st_mode & S_IRGRP) != 0) {
                    stat_buffer.st_mode |= S_IXGRP;
                }

                if ((stat_buffer.st_mode & S_IROTH) != 0) {
                    stat_buffer.st_mode |= S_IXOTH;
                }

                res = fchmod(fd, stat_buffer.st_mode);

                if (res == -1) {
                    printOSErrorMessage("fchmod", errno);
                }
            }
#endif

            if (target_file != FILE_HANDLE_NULL) {
                if (closeFile(target_file) == false) {
                    fatalErrorTempFiles();
                }

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
                if (replaceFileAtomically(target_path_tmp, target_path) == false) {
                    deleteFile(target_path_tmp);

                    // A concurrent start may have put the same file in place and
                    // already be running it, which on Windows prevents replacing
                    // it. That is only an error if what is there is not the file.
                    if (entry.crc32 == 0 || getFileCRC32(target_path) != entry.crc32) {
                        fatalErrorTempFileCreate(target_path);
                    }
                }
#endif
            }

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
            setPayloadFileTimeFromCrc(target_path, entry.crc32);
#endif
        }

        if (payload_toc_current != payload_toc_end) {
            fatalErrorHeaderAttachedData();
        }

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 0
        if (payload_body_current != payload_body_end) {
            fatalErrorHeaderAttachedData();
        }
#endif
    }

    NUITKA_PRINT_TIMING("ONEFILE: Finishing unpacking, cleanup payload.");

    closePayloadData();
#endif

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
    releaseZSTD();
#endif

    // We are done with the unpacking now.

#if defined(_WIN32)
    filename_char_t const *binary_filename = getBinaryFilenameWideChars(false);
#else
    filename_char_t const *binary_filename = getBinaryFilenameHostEncoded(false);
#endif
    setEnvironmentVariable("NUITKA_ONEFILE_DIRECTORY", stripBaseFilename(binary_filename));

    setEnvironmentVariable("NUITKA_ORIGINAL_ARGV0", argv[0]);

    NUITKA_PRINT_TIMING("ONEFILE: Preparing forking of slave process.");

#if _NUITKA_ONEFILE_DLL_MODE
    filename_char_t const *fork_binary = getBinaryPath();
#else
    filename_char_t const *fork_binary = first_filename;
#endif

#if defined(_AIX)
    // Force DLL loading from the distribution.
    setEnvironmentVariable("LIBPATH", payload_path);
#endif

#if defined(_WIN32)

    // spell-checker: ignore STARTF_USESTDHANDLES,STARTUPINFOW
    STARTUPINFOW si;
    memset(&si, 0, sizeof(si));
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    si.cb = sizeof(si);

    PROCESS_INFORMATION pi;

    bool_res = CreateProcessW(fork_binary,
                              getCommandLineForChildProcess(), // command line
                              NULL,                            // process attributes
                              NULL,                            // thread attributes
                              TRUE,                            // inherit handles
                              NORMAL_PRIORITY_CLASS,           // creation flags
                              NULL, NULL, &si, &pi);

    NUITKA_PRINT_TIMING("ONEFILE: Started slave process.");

    if (bool_res == false) {
        fatalErrorChild("Error, couldn't launch child", GetLastError());
    }

    CloseHandle(pi.hThread);
    handle_process = pi.hProcess;

    DWORD exit_code = 0;

#if _NUITKA_ONEFILE_SPLASH_SCREEN
    DWORD wait_time = 50;
#else
    DWORD wait_time = INFINITE;
#endif

    // Loop with splash screen, otherwise this will be only once.
    while (handle_process != 0) {
        WaitForSingleObject(handle_process, wait_time);

        if (!GetExitCodeProcess(handle_process, &exit_code)) {
            exit_code = 1;
        }

#if _NUITKA_ONEFILE_SPLASH_SCREEN
        if (process_role == NULL) {
            if (exit_code == STILL_ACTIVE) {
                bool done = checkSplashScreen();

                // Stop checking splash screen, can increase timeout.
                if (done) {
                    wait_time = INFINITE;
                }

                continue;
            }
        }
#endif
        CloseHandle(handle_process);

        handle_process = 0;
    }

    cleanupChildProcess(false);
#else
    pid_t pid = fork();
    int exit_code;

    if (pid < 0) {
        int error_code = errno;

        cleanupChildProcess(false);

        fatalErrorChild("Error, couldn't launch child (fork)", error_code);
        exit_code = 2;
    } else if (pid == 0) {
        // Child process

        // Make sure, we use the absolute program path for argv[0]
        argv[0] = (char *)getBinaryPath();

        // On WSL, the AVs can cause this, not sure about Linux in general, but
        // we can wait for a bit.
        int retry_count = 0;
        while (retry_count < 10) {
            execv(fork_binary, argv);

            if (errno == ETXTBSY) {
                usleep(100000); // 100ms delay
                retry_count++;
            } else {
                break;
            }
        }

        fatalErrorChild("Error, couldn't launch child (exec)", errno);
        exit_code = 2;
    } else {
        // Onefile bootstrap process
        handle_process = pid;

        int status;
        int res = waitpid_retried(handle_process, &status, false);

        // Signal handling may have reaped the child already, in which case
        // use the recorded status to report how it ended.
        if ((res == -1) && (errno == ECHILD) && reaped_child_status_valid) {
            status = reaped_child_status;
        }

        if (res == -1 && errno != ECHILD) {
            exit_code = 2;
        } else if (WIFSIGNALED(status)) {
            exit_code = 128 + WTERMSIG(status);
        } else {
            exit_code = WEXITSTATUS(status);
        }

        cleanupChildProcess(false);
    }

#endif

    // The onefile program is finished now and can exit.

    NUITKA_PRINT_TIMING("ONEFILE: Exiting.");

    return exit_code;
}

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
