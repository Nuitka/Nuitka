//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/defines.h"
#include "stdint.h"
#endif

// Define _NUITKA_USE_OWN_CRC32 to avoid external zlib for smaller code size,
// at the cost of speed since it does not use CPU crc32 instructions.
#ifdef _NUITKA_USE_OWN_CRC32
uint32_t _initCRC32(void) { return 0xFFFFFFFF; }

uint32_t _updateCRC32(uint32_t crc, unsigned char const *message, uint32_t size) {
    for (uint32_t i = 0; i < size; i++) {
        unsigned int c = message[i];
        crc = crc ^ c;

        for (int j = 7; j >= 0; j--) {
            uint32_t mask = ((crc & 1) != 0) ? 0xFFFFFFFF : 0;
            crc = (crc >> 1) ^ (0xEDB88320 & mask);
        }
    }

    return crc;
}

uint32_t _finalizeCRC32(uint32_t crc) { return ~crc; }

// No Python runtime is available yet, need to do this in C.
uint32_t calcCRC32With64BitSize(unsigned char const *message, uint64_t size) {
    uint32_t crc = _initCRC32();

    while (size > 0) {
        uint32_t chunk_size = size > UINT32_MAX ? UINT32_MAX : (uint32_t)size;
        crc = _updateCRC32(crc, message, chunk_size);
        message += chunk_size;
        size -= chunk_size;
    }

    return _finalizeCRC32(crc);
}
#else

#ifdef _NUITKA_USE_SYSTEM_CRC32
#include "zlib.h"
#else

// Avoid collisions with system libz containing it and being linked against.
#define ZEXTERN NUITKA_MAY_BE_UNUSED static

// The bundled zlib code does not use this export internally, and linked
// libpython variants may provide it already.
#define get_crc_table nuitka_get_crc_table
#include "crc32.c"
#undef get_crc_table
#endif

uint32_t calcCRC32With64BitSize(unsigned char const *message, uint64_t size) {
    uLong crc = 0;

    while (size > 0) {
        uInt chunk_size = size > UINT32_MAX ? (uInt)UINT32_MAX : (uInt)size;
        crc = crc32(crc, message, chunk_size);
        message += chunk_size;
        size -= chunk_size;
    }

    return crc & 0xFFFFFFFF;
}
#endif

uint32_t calcCRC32(unsigned char const *message, uint32_t size) { return calcCRC32With64BitSize(message, size); }

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
