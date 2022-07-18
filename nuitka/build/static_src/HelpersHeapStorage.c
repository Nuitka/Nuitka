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
/** For making "yield" and "yield from" capable of persisting current C stack.
 *
 * These copy objects pointed to into an array foreseen for this task.
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

void Nuitka_PreserveHeap(void *dest, ...) {
    va_list(ap);
    va_start(ap, dest);

    char *w = (char *)dest;

    for (;;) {
        void *source = va_arg(ap, void *);
        if (source == NULL) {
            break;
        }

        size_t size = va_arg(ap, size_t);
        memcpy(w, source, size);
        w += size;
    }
}

void Nuitka_RestoreHeap(void *source, ...) {
    va_list(ap);
    va_start(ap, source);

    char *w = (char *)source;

    for (;;) {
        void *dest = va_arg(ap, void *);
        if (dest == NULL) {
            break;
        }

        size_t size = va_arg(ap, size_t);
        memcpy(dest, w, size);
        w += size;
    }
}
