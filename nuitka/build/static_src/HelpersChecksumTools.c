//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Comment in to disable outside zlib usage for code size, very slow though,
// since it doesn't use assembly to use CPU crc32 instructions.
// #define _NUITKA_USE_OWN_CRC32

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
uint32_t calcCRC32(unsigned char const *message, uint32_t size) {
    return _finalizeCRC32(_updateCRC32(_initCRC32(), message, size));
}
#else

#ifdef _NUITKA_USE_SYSTEM_CRC32
#include "zlib.h"
#else
#include "crc32.c"
#endif

uint32_t calcCRC32(unsigned char const *message, uint32_t size) { return crc32(0, message, size) & 0xFFFFFFFF; }
#endif
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
