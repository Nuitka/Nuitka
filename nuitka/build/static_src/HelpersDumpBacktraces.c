//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* These helpers are used to report C backtraces */

#include "backtrace/backtrace.h"

static struct backtrace_state *our_backtrace_state = NULL;

void INIT_C_BACKTRACES(void) {
    our_backtrace_state = backtrace_create_state(NULL, 1, NULL, NULL);
    assert(our_backtrace_state != NULL);
}

static int bt_frame_count = 0;

static int ourBacktraceFullCallback(void *data, uintptr_t pc, const char *filename, int lineno, const char *function) {
    if (strcmp(function, "DUMP_C_BACKTRACE") != 0) {
        fprintf(stderr, "#%d %s:%d %s\n", bt_frame_count, filename, lineno, function);
        bt_frame_count += 1;
    }

    if (strcmp(function, "main") == 0) {
        return 1;
    }

    return 0;
}

void DUMP_C_BACKTRACE(void) {
    assert(our_backtrace_state != NULL);

    bt_frame_count = 0;
    backtrace_full(our_backtrace_state, 0, ourBacktraceFullCallback, NULL, NULL);
}

#include "backtrace/backtrace.c"
#include "backtrace/dwarf.c"
#if !defined(_WIN32)
#include "backtrace/elf.c"
#include "backtrace/mmap.c"
#else
#include "backtrace/alloc.c"
#include "backtrace/pecoff.c"
#endif
#include "backtrace/fileline.c"
#include "backtrace/posix.c"
#include "backtrace/read.c"
#include "backtrace/sort.c"
#include "backtrace/state.c"
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
