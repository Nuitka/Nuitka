//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_GC_RUNTIME_H__
#define __NUITKA_GC_RUNTIME_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/cpython_api_compat.h"
#include "nuitka/defines.h"

#if PYTHON_VERSION >= 0x3e0
#include "internal/pycore_ceval.h"
#endif
#endif

#if _NUITKA_MODULE_MODE
NUITKA_MAY_BE_UNUSED static inline int Nuitka_GetRuntimeVersion(void) {
    static int runtime_version = 0;

    if (runtime_version == 0) {
        const char *ver = Py_GetVersion();

        while (*ver && *ver != '.') {
            ver++;
        }

        if (*ver) {
            ver++;
        }

        while (*ver && *ver != '.') {
            ver++;
        }

        if (*ver) {
            ver++;
        }

        int micro = 0;

        while (*ver >= '0' && *ver <= '9') {
            micro = micro * 10 + (*ver - '0');
            ver++;
        }

        if (micro >= 16) {
            micro = 15;
        }

        runtime_version = PY_MAJOR_VERSION * 256 + PY_MINOR_VERSION * 16 + micro;
    }

    return runtime_version;
}
#else
#define Nuitka_GetRuntimeVersion() PYTHON_VERSION
#endif

#if PYTHON_VERSION >= 0x3e0
// TODO: Does this code have to be in the header really?
static inline void Nuitka_Py_ScheduleGC(PyThreadState *tstate) {
    if (!_Py_eval_breaker_bit_is_set(tstate, _PY_GC_SCHEDULED_BIT)) {
        _Py_set_eval_breaker_bit(tstate, _PY_GC_SCHEDULED_BIT);
    }
}

static inline bool Nuitka_GC_UsesGeneration0List(void) {
#if _NUITKA_MODULE_MODE && PYTHON_VERSION < 0x3f0 && !defined(Py_GIL_DISABLED)
    static int uses_generation0_list = -1;

    if (uses_generation0_list == -1) {
        uses_generation0_list = Nuitka_GetRuntimeVersion() >= 0x3e5;
    }

    return uses_generation0_list != 0;
#else
    return PYTHON_VERSION >= 0x3e5;
#endif
}
#endif

#if PYTHON_VERSION >= 0x3e0 && PYTHON_VERSION < 0x3f0
// CPython 3.14.5 grew "_gc_runtime_state" in GIL builds, shifting all later
// interpreter fields by three pointer widths.
static inline int Nuitka_PyInterpreterState_PostGcPointerDelta(void) {
#if _NUITKA_MODULE_MODE && !defined(Py_GIL_DISABLED)
    static int post_gc_pointer_delta = 99;

    if (post_gc_pointer_delta == 99) {
        int runtime_pointer_shift = 0;
        int compile_time_pointer_shift = 0;
        int runtime_version = Nuitka_GetRuntimeVersion();

        if (runtime_version >= 0x3e5) {
            runtime_pointer_shift += 3;
        }

#if PYTHON_VERSION >= 0x3e5
        compile_time_pointer_shift += 3;
#endif
        post_gc_pointer_delta = runtime_pointer_shift - compile_time_pointer_shift;
    }

    return post_gc_pointer_delta;
#else
    return 0;
#endif
}

static inline void *Nuitka_PyInterpreterState_AdjustPostGcPointer(void *field_ptr) {
    return (char *)field_ptr + Nuitka_PyInterpreterState_PostGcPointerDelta() * sizeof(void *);
}

// CPython 3.14 changed the interpreter layout twice before fields after
// "_qsbr_shared": 3.14.4 added "_qsbr_shared.array_raw" (+1 pointer) and
// 3.14.5 grew "_gc_runtime_state" in GIL builds (+3 pointers).
static inline int Nuitka_PyInterpreterState_PostQsbrPointerDelta(void) {
#if _NUITKA_MODULE_MODE && !defined(Py_GIL_DISABLED)
    static int post_qsbr_pointer_delta = 99;

    if (post_qsbr_pointer_delta == 99) {
        int post_gc_pointer_delta = Nuitka_PyInterpreterState_PostGcPointerDelta();
        int runtime_version = Nuitka_GetRuntimeVersion();
        int qsbr_pointer_delta = 0;

        if (runtime_version >= 0x3e4) {
            qsbr_pointer_delta += 1;
        }

#if PYTHON_VERSION >= 0x3e4
        qsbr_pointer_delta -= 1;
#endif
        post_qsbr_pointer_delta = post_gc_pointer_delta + qsbr_pointer_delta;
    }

    return post_qsbr_pointer_delta;
#else
    return 0;
#endif
}

static inline void *Nuitka_PyInterpreterState_AdjustPostQsbrPointer(void *field_ptr) {
    return (char *)field_ptr + Nuitka_PyInterpreterState_PostQsbrPointerDelta() * sizeof(void *);
}
#endif

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
