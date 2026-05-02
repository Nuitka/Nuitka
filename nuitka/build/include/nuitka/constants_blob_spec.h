//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_CONSTANTS_BLOB_SPEC_H__
#define __NUITKA_CONSTANTS_BLOB_SPEC_H__

/* Keep these defines in simple numeric form, so Python code can parse this
 * file directly without a C preprocessor.
 */

#define NUITKA_CONSTANT_BLOB_TAG_PREVIOUS 0x70                  /* 'p' */
#define NUITKA_CONSTANT_BLOB_TAG_NONE 0x6e                      /* 'n' */
#define NUITKA_CONSTANT_BLOB_TAG_TRUE 0x74                      /* 't' */
#define NUITKA_CONSTANT_BLOB_TAG_FALSE 0x46                     /* 'F' */
#define NUITKA_CONSTANT_BLOB_TAG_TUPLE 0x54                     /* 'T' */
#define NUITKA_CONSTANT_BLOB_TAG_LIST 0x4c                      /* 'L' */
#define NUITKA_CONSTANT_BLOB_TAG_DICT 0x44                      /* 'D' */
#define NUITKA_CONSTANT_BLOB_TAG_SET 0x53                       /* 'S' */
#define NUITKA_CONSTANT_BLOB_TAG_FROZENSET 0x50                 /* 'P' */
#define NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_SMALL 0x6c       /* 'l' */
#define NUITKA_CONSTANT_BLOB_TAG_LONG_NEGATIVE_SMALL 0x71       /* 'q' */
#define NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_LARGE 0x67       /* 'g' */
#define NUITKA_CONSTANT_BLOB_TAG_LONG_NEGATIVE_LARGE 0x47       /* 'G' */
#define NUITKA_CONSTANT_BLOB_TAG_INT_POSITIVE 0x69              /* 'i' */
#define NUITKA_CONSTANT_BLOB_TAG_INT_NEGATIVE 0x49              /* 'I' */
#define NUITKA_CONSTANT_BLOB_TAG_FLOAT_SPECIAL 0x5a             /* 'Z' */
#define NUITKA_CONSTANT_BLOB_TAG_FLOAT 0x66                     /* 'f' */
#define NUITKA_CONSTANT_BLOB_TAG_TEXT_EMPTY 0x73                /* 's' */
#define NUITKA_CONSTANT_BLOB_TAG_TEXT_SINGLE 0x77               /* 'w' */
#define NUITKA_CONSTANT_BLOB_TAG_TEXT_UTF8_LENGTH_PREFIXED 0x76 /* 'v' */
#define NUITKA_CONSTANT_BLOB_TAG_TEXT_UTF8_ZERO_TERMINATED 0x75 /* 'u' */
#define NUITKA_CONSTANT_BLOB_TAG_ATTRIBUTE_NAME 0x61            /* 'a' */
#define NUITKA_CONSTANT_BLOB_TAG_BYTES_LENGTH_PREFIXED 0x62     /* 'b' */
#define NUITKA_CONSTANT_BLOB_TAG_BYTES_ZERO_TERMINATED 0x63     /* 'c' */
#define NUITKA_CONSTANT_BLOB_TAG_BYTES_SINGLE 0x64              /* 'd' */
#define NUITKA_CONSTANT_BLOB_TAG_SLICE 0x3a                     /* ':' */
#define NUITKA_CONSTANT_BLOB_TAG_RANGE 0x3b                     /* ';' */
#define NUITKA_CONSTANT_BLOB_TAG_COMPLEX_SPECIAL 0x4a           /* 'J' */
#define NUITKA_CONSTANT_BLOB_TAG_COMPLEX 0x6a                   /* 'j' */
#define NUITKA_CONSTANT_BLOB_TAG_BYTEARRAY 0x42                 /* 'B' */
#define NUITKA_CONSTANT_BLOB_TAG_BUILTIN_ANON 0x4d              /* 'M' */
#define NUITKA_CONSTANT_BLOB_TAG_BUILTIN_SPECIAL 0x51           /* 'Q' */
#define NUITKA_CONSTANT_BLOB_TAG_BLOB_DATA 0x58                 /* 'X' */
#define NUITKA_CONSTANT_BLOB_TAG_GENERIC_ALIAS 0x41             /* 'A' */
#define NUITKA_CONSTANT_BLOB_TAG_UNION_TYPE 0x48                /* 'H' */
#define NUITKA_CONSTANT_BLOB_TAG_BUILTIN_NAMED 0x4f             /* 'O' */
#define NUITKA_CONSTANT_BLOB_TAG_BUILTIN_EXCEPTION 0x45         /* 'E' */
#define NUITKA_CONSTANT_BLOB_TAG_CODE_OBJECT 0x43               /* 'C' */
#define NUITKA_CONSTANT_BLOB_TAG_END 0x2e                       /* '.' */

#define NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_ZERO 0x00
#define NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_ZERO 0x01
#define NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_NAN 0x02
#define NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_NAN 0x03
#define NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_INF 0x04
#define NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_INF 0x05

/* Code object flags use fixed bit assignments. Unused version-specific bits
 * remain clear for runtimes that do not support the corresponding payload.
 */
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_QUALNAME 0x0000000000000001ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FREE_VARS 0x0000000000000002ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_KW_ONLY 0x0000000000000004ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_POS_ONLY 0x0000000000000008ULL
#define NUITKA_CONSTANT_BLOB_CODE_KIND_MASK 0x0000000000000030ULL
#define NUITKA_CONSTANT_BLOB_CODE_KIND_GENERATOR 0x0000000000000010ULL
#define NUITKA_CONSTANT_BLOB_CODE_KIND_COROUTINE 0x0000000000000020ULL
#define NUITKA_CONSTANT_BLOB_CODE_KIND_ASYNCGEN 0x0000000000000030ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_OPTIMIZED 0x0000000000000040ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_NEWLOCALS 0x0000000000000080ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_VARARGS 0x0000000000000100ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_VARKEYWORDS 0x0000000000000200ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_DIVISION 0x0000000000000400ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_UNICODE_LITERALS 0x0000000000000800ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_PRINT_FUNCTION 0x0000000000001000ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_ABSOLUTE_IMPORT 0x0000000000002000ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_GENERATOR_STOP 0x0000000000004000ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_ANNOTATIONS 0x0000000000008000ULL
#define NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_BARRY_AS_BDFL 0x0000000000010000ULL

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
