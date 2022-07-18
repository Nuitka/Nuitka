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

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *str_builtin_format;
#endif
extern PyObject *unicode_builtin_format;
extern PyObject *DICT_POP2(PyObject *dict, PyObject *key);
extern PyObject *DICT_POP3(PyObject *dict, PyObject *key, PyObject *default_value);
extern PyObject *DICT_POPITEM(PyObject *dict);
extern PyObject *DICT_SETDEFAULT2(PyObject *dict, PyObject *key);
extern PyObject *DICT_SETDEFAULT3(PyObject *dict, PyObject *key, PyObject *default_value);
#if PYTHON_VERSION < 0x300
extern PyObject *STR_CAPITALIZE(PyObject *str);
extern PyObject *STR_CENTER2(PyObject *str, PyObject *width);
extern PyObject *STR_CENTER3(PyObject *str, PyObject *width, PyObject *fillchar);
extern PyObject *STR_COUNT2(PyObject *str, PyObject *sub);
extern PyObject *STR_COUNT3(PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_COUNT4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_DECODE1(PyObject *str);
extern PyObject *STR_DECODE2(PyObject *str, PyObject *encoding);
extern PyObject *STR_DECODE3(PyObject *str, PyObject *encoding, PyObject *errors);
extern PyObject *STR_ENCODE1(PyObject *str);
extern PyObject *STR_ENCODE2(PyObject *str, PyObject *encoding);
extern PyObject *STR_ENCODE3(PyObject *str, PyObject *encoding, PyObject *errors);
extern PyObject *STR_ENDSWITH2(PyObject *str, PyObject *suffix);
extern PyObject *STR_ENDSWITH3(PyObject *str, PyObject *suffix, PyObject *start);
extern PyObject *STR_ENDSWITH4(PyObject *str, PyObject *suffix, PyObject *start, PyObject *end);
extern PyObject *STR_EXPANDTABS1(PyObject *str);
extern PyObject *STR_EXPANDTABS2(PyObject *str, PyObject *tabsize);
extern PyObject *STR_FIND2(PyObject *str, PyObject *sub);
extern PyObject *STR_FIND3(PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_FIND4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_INDEX2(PyObject *str, PyObject *sub);
extern PyObject *STR_INDEX3(PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_INDEX4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_ISALNUM(PyObject *str);
extern PyObject *STR_ISALPHA(PyObject *str);
extern PyObject *STR_ISDIGIT(PyObject *str);
extern PyObject *STR_ISLOWER(PyObject *str);
extern PyObject *STR_ISSPACE(PyObject *str);
extern PyObject *STR_ISTITLE(PyObject *str);
extern PyObject *STR_ISUPPER(PyObject *str);
extern PyObject *STR_LJUST2(PyObject *str, PyObject *width);
extern PyObject *STR_LJUST3(PyObject *str, PyObject *width, PyObject *fillchar);
extern PyObject *STR_LOWER(PyObject *str);
extern PyObject *STR_LSTRIP1(PyObject *str);
extern PyObject *STR_LSTRIP2(PyObject *str, PyObject *chars);
extern PyObject *STR_PARTITION(PyObject *str, PyObject *sep);
extern PyObject *STR_REPLACE3(PyObject *str, PyObject *old, PyObject *new_value);
extern PyObject *STR_REPLACE4(PyObject *str, PyObject *old, PyObject *new_value, PyObject *count);
extern PyObject *STR_RFIND2(PyObject *str, PyObject *sub);
extern PyObject *STR_RFIND3(PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_RFIND4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_RINDEX2(PyObject *str, PyObject *sub);
extern PyObject *STR_RINDEX3(PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_RINDEX4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_RJUST2(PyObject *str, PyObject *width);
extern PyObject *STR_RJUST3(PyObject *str, PyObject *width, PyObject *fillchar);
extern PyObject *STR_RPARTITION(PyObject *str, PyObject *sep);
extern PyObject *STR_RSPLIT1(PyObject *str);
extern PyObject *STR_RSPLIT2(PyObject *str, PyObject *sep);
extern PyObject *STR_RSPLIT3(PyObject *str, PyObject *sep, PyObject *maxsplit);
extern PyObject *STR_RSTRIP1(PyObject *str);
extern PyObject *STR_RSTRIP2(PyObject *str, PyObject *chars);
extern PyObject *STR_SPLIT1(PyObject *str);
extern PyObject *STR_SPLIT2(PyObject *str, PyObject *sep);
extern PyObject *STR_SPLIT3(PyObject *str, PyObject *sep, PyObject *maxsplit);
extern PyObject *STR_SPLITLINES1(PyObject *str);
extern PyObject *STR_SPLITLINES2(PyObject *str, PyObject *keepends);
extern PyObject *STR_STARTSWITH2(PyObject *str, PyObject *prefix);
extern PyObject *STR_STARTSWITH3(PyObject *str, PyObject *prefix, PyObject *start);
extern PyObject *STR_STARTSWITH4(PyObject *str, PyObject *prefix, PyObject *start, PyObject *end);
extern PyObject *STR_STRIP1(PyObject *str);
extern PyObject *STR_STRIP2(PyObject *str, PyObject *chars);
extern PyObject *STR_SWAPCASE(PyObject *str);
extern PyObject *STR_TITLE(PyObject *str);
extern PyObject *STR_TRANSLATE(PyObject *str, PyObject *table);
extern PyObject *STR_UPPER(PyObject *str);
extern PyObject *STR_ZFILL(PyObject *str, PyObject *width);
#endif
extern PyObject *UNICODE_CAPITALIZE(PyObject *unicode);
extern PyObject *UNICODE_CENTER2(PyObject *unicode, PyObject *width);
extern PyObject *UNICODE_CENTER3(PyObject *unicode, PyObject *width, PyObject *fillchar);
extern PyObject *UNICODE_COUNT2(PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_COUNT3(PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_COUNT4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *UNICODE_ENCODE1(PyObject *unicode);
extern PyObject *UNICODE_ENCODE2(PyObject *unicode, PyObject *encoding);
extern PyObject *UNICODE_ENCODE3(PyObject *unicode, PyObject *encoding, PyObject *errors);
extern PyObject *UNICODE_ENDSWITH2(PyObject *unicode, PyObject *suffix);
extern PyObject *UNICODE_ENDSWITH3(PyObject *unicode, PyObject *suffix, PyObject *start);
extern PyObject *UNICODE_ENDSWITH4(PyObject *unicode, PyObject *suffix, PyObject *start, PyObject *end);
extern PyObject *UNICODE_EXPANDTABS1(PyObject *unicode);
extern PyObject *UNICODE_EXPANDTABS2(PyObject *unicode, PyObject *tabsize);
extern PyObject *UNICODE_FIND2(PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_FIND3(PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_FIND4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *UNICODE_INDEX2(PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_INDEX3(PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_INDEX4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *UNICODE_ISALNUM(PyObject *unicode);
extern PyObject *UNICODE_ISALPHA(PyObject *unicode);
extern PyObject *UNICODE_ISDIGIT(PyObject *unicode);
extern PyObject *UNICODE_ISLOWER(PyObject *unicode);
extern PyObject *UNICODE_ISSPACE(PyObject *unicode);
extern PyObject *UNICODE_ISTITLE(PyObject *unicode);
extern PyObject *UNICODE_ISUPPER(PyObject *unicode);
extern PyObject *UNICODE_LJUST2(PyObject *unicode, PyObject *width);
extern PyObject *UNICODE_LJUST3(PyObject *unicode, PyObject *width, PyObject *fillchar);
extern PyObject *UNICODE_LOWER(PyObject *unicode);
extern PyObject *UNICODE_LSTRIP1(PyObject *unicode);
extern PyObject *UNICODE_LSTRIP2(PyObject *unicode, PyObject *chars);
extern PyObject *UNICODE_REPLACE3(PyObject *unicode, PyObject *old, PyObject *new_value);
extern PyObject *UNICODE_REPLACE4(PyObject *unicode, PyObject *old, PyObject *new_value, PyObject *count);
extern PyObject *UNICODE_RFIND2(PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_RFIND3(PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_RFIND4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *UNICODE_RINDEX2(PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_RINDEX3(PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_RINDEX4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *UNICODE_RJUST2(PyObject *unicode, PyObject *width);
extern PyObject *UNICODE_RJUST3(PyObject *unicode, PyObject *width, PyObject *fillchar);
extern PyObject *UNICODE_RSPLIT1(PyObject *unicode);
extern PyObject *UNICODE_RSPLIT2(PyObject *unicode, PyObject *sep);
extern PyObject *UNICODE_RSPLIT3(PyObject *unicode, PyObject *sep, PyObject *maxsplit);
extern PyObject *UNICODE_RSTRIP1(PyObject *unicode);
extern PyObject *UNICODE_RSTRIP2(PyObject *unicode, PyObject *chars);
extern PyObject *UNICODE_SPLIT1(PyObject *unicode);
extern PyObject *UNICODE_SPLIT2(PyObject *unicode, PyObject *sep);
extern PyObject *UNICODE_SPLIT3(PyObject *unicode, PyObject *sep, PyObject *maxsplit);
extern PyObject *UNICODE_SPLITLINES1(PyObject *unicode);
extern PyObject *UNICODE_SPLITLINES2(PyObject *unicode, PyObject *keepends);
extern PyObject *UNICODE_STARTSWITH2(PyObject *unicode, PyObject *prefix);
extern PyObject *UNICODE_STARTSWITH3(PyObject *unicode, PyObject *prefix, PyObject *start);
extern PyObject *UNICODE_STARTSWITH4(PyObject *unicode, PyObject *prefix, PyObject *start, PyObject *end);
extern PyObject *UNICODE_STRIP1(PyObject *unicode);
extern PyObject *UNICODE_STRIP2(PyObject *unicode, PyObject *chars);
extern PyObject *UNICODE_SWAPCASE(PyObject *unicode);
extern PyObject *UNICODE_TITLE(PyObject *unicode);
extern PyObject *UNICODE_TRANSLATE(PyObject *unicode, PyObject *table);
extern PyObject *UNICODE_UPPER(PyObject *unicode);
extern PyObject *UNICODE_ZFILL(PyObject *unicode, PyObject *width);
#if PYTHON_VERSION >= 0x300
extern PyObject *BYTES_DECODE1(PyObject *bytes);
extern PyObject *BYTES_DECODE2(PyObject *bytes, PyObject *encoding);
extern PyObject *BYTES_DECODE3(PyObject *bytes, PyObject *encoding, PyObject *errors);
#endif
