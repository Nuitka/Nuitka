//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* These helpers are used to report C backtraces */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#include "backtrace/backtrace.h"

static struct backtrace_state *our_backtrace_state = NULL;

void INIT_C_BACKTRACES(void) {
    our_backtrace_state = backtrace_create_state(NULL, 1, NULL, NULL);
    assert(our_backtrace_state != NULL);
}

static int bt_frame_count = 0;

static int ourBacktraceFullCallback(void *data, uintptr_t pc, const char *filename, int lineno, const char *function) {
    if ((function == NULL) || (strcmp(function, "DUMP_C_BACKTRACE") != 0)) {
        fprintf(stderr, "#%d %p in %s at %s:%d\n", bt_frame_count, (void *)pc, function ? function : "<unknown>",
                filename ? filename : "<unknown>", lineno);
        bt_frame_count += 1;
    }

    if (function != NULL && strcmp(function, "main") == 0) {
        return 1;
    }

    return 0;
}

void DUMP_C_BACKTRACE(void) {
    assert(our_backtrace_state != NULL);

    bt_frame_count = 0;
    // Skip 1 frame, which is DUMP_C_BACKTRACE itself.
    backtrace_full(our_backtrace_state, 1, ourBacktraceFullCallback, NULL, NULL);
}

// Dumps the C stack from a ucontext_t, which is provided by a signal handler.
void DUMP_C_BACKTRACE_FROM_CONTEXT(void *ucontext) {
    assert(our_backtrace_state != NULL);

    ucontext_t *uc = (ucontext_t *)ucontext;

#if defined(__x86_64__)
    uintptr_t pc = uc->uc_mcontext.gregs[REG_RIP];
    uintptr_t fp = uc->uc_mcontext.gregs[REG_RBP];
#elif defined(__i386__)
    uintptr_t pc = uc->uc_mcontext.gregs[REG_EIP];
    uintptr_t fp = uc->uc_mcontext.gregs[REG_EBP];
#elif defined(__aarch64__)
    uintptr_t pc = uc->uc_mcontext.pc;
    uintptr_t fp = uc->uc_mcontext.regs[29]; // FP is x29
#else
#warning "Cannot get backtrace from ucontext on this architecture, falling back to current stack."
    // Fallback to current stack, which is better than nothing.
    DUMP_C_BACKTRACE();
    return;
#endif

    bt_frame_count = 0;

    // Unwind the stack using frame pointers. This requires the program to be
    // compiled with -fno-omit-frame-pointer for reliable results.
    while (fp != 0 && pc != 0) {
        backtrace_pcinfo(our_backtrace_state, pc, ourBacktraceFullCallback, NULL, NULL);

        // Basic sanity check for the frame pointer to avoid infinite loops.
        if (*(uintptr_t *)fp <= fp) {
            fprintf(stderr, "  (corrupt frame pointer, backtrace truncated)\n");
            break;
        }

        pc = ((uintptr_t *)fp)[1];
        fp = ((uintptr_t *)fp)[0];
    }
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
