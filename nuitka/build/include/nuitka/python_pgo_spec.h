//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_PYTHON_PGO_SPEC_H__
#define __NUITKA_PYTHON_PGO_SPEC_H__

/* Keep these defines in simple numeric form, so the Python code can parse this
 * file directly without a C preprocessor, and both sides share one source.
 */

/* Probe IDs of the PGO file format. */
#define NUITKA_PGO_PROBE_END 0
#define NUITKA_PGO_PROBE_MODULE_ENTER 1
#define NUITKA_PGO_PROBE_MODULE_EXIT 2
#define NUITKA_PGO_PROBE_CLASS_PREPARE_RESULT 3
#define NUITKA_PGO_PROBE_CLASS_PREPARE_RESULT_ONCE 4
#define NUITKA_PGO_PROBE_STRING_DEFINITION 5
#define NUITKA_PGO_PROBE_KEY_DEFINITION 6
#define NUITKA_PGO_PROBE_VALUE_DEFINITION 7

/* Key scopes of the PGO file format. */
#define NUITKA_PGO_SCOPE_MODULE 1
#define NUITKA_PGO_SCOPE_CLASS 2

/* Value tags of the PGO file format. */
#define NUITKA_PGO_VALUE_TAG_NONE 0x4e               /* 'N' */
#define NUITKA_PGO_VALUE_TAG_TRUE 0x54               /* 'T' */
#define NUITKA_PGO_VALUE_TAG_FALSE 0x46              /* 'F' */
#define NUITKA_PGO_VALUE_TAG_ELLIPSIS 0x45           /* 'E' */
#define NUITKA_PGO_VALUE_TAG_INT_POSITIVE 0x69       /* 'i' */
#define NUITKA_PGO_VALUE_TAG_INT_NEGATIVE 0x6e       /* 'n' */
#define NUITKA_PGO_VALUE_TAG_FLOAT 0x66              /* 'f' */
#define NUITKA_PGO_VALUE_TAG_COMPLEX 0x63            /* 'c' */
#define NUITKA_PGO_VALUE_TAG_STR 0x73                /* 's' */
#define NUITKA_PGO_VALUE_TAG_UNICODE 0x75            /* 'u' */
#define NUITKA_PGO_VALUE_TAG_BYTES 0x62              /* 'b' */
#define NUITKA_PGO_VALUE_TAG_BYTEARRAY 0x42          /* 'B' */
#define NUITKA_PGO_VALUE_TAG_LIST 0x4c               /* 'L' */
#define NUITKA_PGO_VALUE_TAG_TUPLE 0x55              /* 'U' */
#define NUITKA_PGO_VALUE_TAG_DICT 0x44               /* 'D' */
#define NUITKA_PGO_VALUE_TAG_SET 0x53                /* 'S' */
#define NUITKA_PGO_VALUE_TAG_FROZENSET 0x5a          /* 'Z' */
#define NUITKA_PGO_VALUE_TAG_TOO_LARGE 0x58          /* 'X' */
#define NUITKA_PGO_VALUE_TAG_TOO_LARGE_ENCODING 0x59 /* 'Y' */
#define NUITKA_PGO_VALUE_TAG_TOO_MANY 0x4d           /* 'M' */
#define NUITKA_PGO_VALUE_TAG_BIG_INT 0x49            /* 'I' */
#define NUITKA_PGO_VALUE_TAG_GLOBAL 0x47             /* 'G' */
#define NUITKA_PGO_VALUE_TAG_REDUCED 0x52            /* 'R' */
#define NUITKA_PGO_VALUE_TAG_UNSUPPORTED 0x56        /* 'V' */

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
