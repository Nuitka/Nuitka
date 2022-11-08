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
// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

uint32_t initCRC32(void) { return 0xFFFFFFFF; }

uint32_t updateCRC32(uint32_t crc, unsigned char const *message, uint32_t size) {
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

uint32_t finalizeCRC32(uint32_t crc) { return ~crc; }

// No Python runtime is available yet, need to do this in C.
uint32_t calcCRC32(unsigned char const *message, uint32_t size) {
    return finalizeCRC32(updateCRC32(initCRC32(), message, size));
}
