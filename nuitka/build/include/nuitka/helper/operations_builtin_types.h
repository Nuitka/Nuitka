//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperBuiltinMethodOperation.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION < 0x300
extern PyObject *str_builtin_format;
#endif
extern PyObject *unicode_builtin_format;
extern PyObject *dict_builtin_fromkeys;
extern PyObject *DICT_POP2(PyThreadState *tstate, PyObject *dict, PyObject *key);
extern PyObject *DICT_POP3(PyThreadState *tstate, PyObject *dict, PyObject *key, PyObject *default_value);
extern PyObject *DICT_POPITEM(PyThreadState *tstate, PyObject *dict);
extern PyObject *DICT_SETDEFAULT2(PyThreadState *tstate, PyObject *dict, PyObject *key);
extern PyObject *DICT_SETDEFAULT3(PyThreadState *tstate, PyObject *dict, PyObject *key, PyObject *default_value);
extern PyObject *LIST_POP1(PyThreadState *tstate, PyObject *list);
extern PyObject *LIST_POP2(PyThreadState *tstate, PyObject *list, PyObject *index);
#if PYTHON_VERSION < 0x300
extern PyObject *STR_CAPITALIZE(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_CENTER2(PyThreadState *tstate, PyObject *str, PyObject *width);
extern PyObject *STR_CENTER3(PyThreadState *tstate, PyObject *str, PyObject *width, PyObject *fillchar);
extern PyObject *STR_COUNT2(PyThreadState *tstate, PyObject *str, PyObject *sub);
extern PyObject *STR_COUNT3(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_COUNT4(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_DECODE1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_DECODE2(PyThreadState *tstate, PyObject *str, PyObject *encoding);
extern PyObject *STR_DECODE3(PyThreadState *tstate, PyObject *str, PyObject *encoding, PyObject *errors);
extern PyObject *STR_ENCODE1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ENCODE2(PyThreadState *tstate, PyObject *str, PyObject *encoding);
extern PyObject *STR_ENCODE3(PyThreadState *tstate, PyObject *str, PyObject *encoding, PyObject *errors);
extern PyObject *STR_ENDSWITH2(PyThreadState *tstate, PyObject *str, PyObject *suffix);
extern PyObject *STR_ENDSWITH3(PyThreadState *tstate, PyObject *str, PyObject *suffix, PyObject *start);
extern PyObject *STR_ENDSWITH4(PyThreadState *tstate, PyObject *str, PyObject *suffix, PyObject *start, PyObject *end);
extern PyObject *STR_EXPANDTABS1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_EXPANDTABS2(PyThreadState *tstate, PyObject *str, PyObject *tabsize);
extern PyObject *STR_FIND2(PyThreadState *tstate, PyObject *str, PyObject *sub);
extern PyObject *STR_FIND3(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_FIND4(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_INDEX2(PyThreadState *tstate, PyObject *str, PyObject *sub);
extern PyObject *STR_INDEX3(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_INDEX4(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_ISALNUM(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ISALPHA(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ISDIGIT(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ISLOWER(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ISSPACE(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ISTITLE(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ISUPPER(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_LJUST2(PyThreadState *tstate, PyObject *str, PyObject *width);
extern PyObject *STR_LJUST3(PyThreadState *tstate, PyObject *str, PyObject *width, PyObject *fillchar);
extern PyObject *STR_LOWER(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_LSTRIP1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_LSTRIP2(PyThreadState *tstate, PyObject *str, PyObject *chars);
extern PyObject *STR_PARTITION(PyThreadState *tstate, PyObject *str, PyObject *sep);
extern PyObject *STR_REPLACE3(PyThreadState *tstate, PyObject *str, PyObject *old, PyObject *new_value);
extern PyObject *STR_REPLACE4(PyThreadState *tstate, PyObject *str, PyObject *old, PyObject *new_value,
                              PyObject *count);
extern PyObject *STR_RFIND2(PyThreadState *tstate, PyObject *str, PyObject *sub);
extern PyObject *STR_RFIND3(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_RFIND4(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_RINDEX2(PyThreadState *tstate, PyObject *str, PyObject *sub);
extern PyObject *STR_RINDEX3(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start);
extern PyObject *STR_RINDEX4(PyThreadState *tstate, PyObject *str, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *STR_RJUST2(PyThreadState *tstate, PyObject *str, PyObject *width);
extern PyObject *STR_RJUST3(PyThreadState *tstate, PyObject *str, PyObject *width, PyObject *fillchar);
extern PyObject *STR_RPARTITION(PyThreadState *tstate, PyObject *str, PyObject *sep);
extern PyObject *STR_RSPLIT1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_RSPLIT2(PyThreadState *tstate, PyObject *str, PyObject *sep);
extern PyObject *STR_RSPLIT3(PyThreadState *tstate, PyObject *str, PyObject *sep, PyObject *maxsplit);
extern PyObject *STR_RSTRIP1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_RSTRIP2(PyThreadState *tstate, PyObject *str, PyObject *chars);
extern PyObject *STR_SPLIT1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_SPLIT2(PyThreadState *tstate, PyObject *str, PyObject *sep);
extern PyObject *STR_SPLIT3(PyThreadState *tstate, PyObject *str, PyObject *sep, PyObject *maxsplit);
extern PyObject *STR_SPLITLINES1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_SPLITLINES2(PyThreadState *tstate, PyObject *str, PyObject *keepends);
extern PyObject *STR_STARTSWITH2(PyThreadState *tstate, PyObject *str, PyObject *prefix);
extern PyObject *STR_STARTSWITH3(PyThreadState *tstate, PyObject *str, PyObject *prefix, PyObject *start);
extern PyObject *STR_STARTSWITH4(PyThreadState *tstate, PyObject *str, PyObject *prefix, PyObject *start,
                                 PyObject *end);
extern PyObject *STR_STRIP1(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_STRIP2(PyThreadState *tstate, PyObject *str, PyObject *chars);
extern PyObject *STR_SWAPCASE(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_TITLE(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_TRANSLATE(PyThreadState *tstate, PyObject *str, PyObject *table);
extern PyObject *STR_UPPER(PyThreadState *tstate, PyObject *str);
extern PyObject *STR_ZFILL(PyThreadState *tstate, PyObject *str, PyObject *width);
#endif
extern PyObject *UNICODE_CAPITALIZE(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_CENTER2(PyThreadState *tstate, PyObject *unicode, PyObject *width);
extern PyObject *UNICODE_CENTER3(PyThreadState *tstate, PyObject *unicode, PyObject *width, PyObject *fillchar);
extern PyObject *UNICODE_COUNT2(PyThreadState *tstate, PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_COUNT3(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_COUNT4(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start,
                                PyObject *end);
extern PyObject *UNICODE_ENCODE1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ENCODE2(PyThreadState *tstate, PyObject *unicode, PyObject *encoding);
extern PyObject *UNICODE_ENCODE3(PyThreadState *tstate, PyObject *unicode, PyObject *encoding, PyObject *errors);
extern PyObject *UNICODE_ENDSWITH2(PyThreadState *tstate, PyObject *unicode, PyObject *suffix);
extern PyObject *UNICODE_ENDSWITH3(PyThreadState *tstate, PyObject *unicode, PyObject *suffix, PyObject *start);
extern PyObject *UNICODE_ENDSWITH4(PyThreadState *tstate, PyObject *unicode, PyObject *suffix, PyObject *start,
                                   PyObject *end);
extern PyObject *UNICODE_EXPANDTABS1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_EXPANDTABS2(PyThreadState *tstate, PyObject *unicode, PyObject *tabsize);
extern PyObject *UNICODE_FIND2(PyThreadState *tstate, PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_FIND3(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_FIND4(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *UNICODE_INDEX2(PyThreadState *tstate, PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_INDEX3(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_INDEX4(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start,
                                PyObject *end);
extern PyObject *UNICODE_ISALNUM(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ISALPHA(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ISDIGIT(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ISLOWER(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ISSPACE(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ISTITLE(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ISUPPER(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_LJUST2(PyThreadState *tstate, PyObject *unicode, PyObject *width);
extern PyObject *UNICODE_LJUST3(PyThreadState *tstate, PyObject *unicode, PyObject *width, PyObject *fillchar);
extern PyObject *UNICODE_LOWER(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_LSTRIP1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_LSTRIP2(PyThreadState *tstate, PyObject *unicode, PyObject *chars);
extern PyObject *UNICODE_REPLACE3(PyThreadState *tstate, PyObject *unicode, PyObject *old, PyObject *new_value);
extern PyObject *UNICODE_REPLACE4(PyThreadState *tstate, PyObject *unicode, PyObject *old, PyObject *new_value,
                                  PyObject *count);
extern PyObject *UNICODE_RFIND2(PyThreadState *tstate, PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_RFIND3(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_RFIND4(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start,
                                PyObject *end);
extern PyObject *UNICODE_RINDEX2(PyThreadState *tstate, PyObject *unicode, PyObject *sub);
extern PyObject *UNICODE_RINDEX3(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start);
extern PyObject *UNICODE_RINDEX4(PyThreadState *tstate, PyObject *unicode, PyObject *sub, PyObject *start,
                                 PyObject *end);
extern PyObject *UNICODE_RJUST2(PyThreadState *tstate, PyObject *unicode, PyObject *width);
extern PyObject *UNICODE_RJUST3(PyThreadState *tstate, PyObject *unicode, PyObject *width, PyObject *fillchar);
extern PyObject *UNICODE_RSPLIT1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_RSPLIT2(PyThreadState *tstate, PyObject *unicode, PyObject *sep);
extern PyObject *UNICODE_RSPLIT3(PyThreadState *tstate, PyObject *unicode, PyObject *sep, PyObject *maxsplit);
extern PyObject *UNICODE_RSTRIP1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_RSTRIP2(PyThreadState *tstate, PyObject *unicode, PyObject *chars);
extern PyObject *UNICODE_SPLIT1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_SPLIT2(PyThreadState *tstate, PyObject *unicode, PyObject *sep);
extern PyObject *UNICODE_SPLIT3(PyThreadState *tstate, PyObject *unicode, PyObject *sep, PyObject *maxsplit);
extern PyObject *UNICODE_SPLITLINES1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_SPLITLINES2(PyThreadState *tstate, PyObject *unicode, PyObject *keepends);
extern PyObject *UNICODE_STARTSWITH2(PyThreadState *tstate, PyObject *unicode, PyObject *prefix);
extern PyObject *UNICODE_STARTSWITH3(PyThreadState *tstate, PyObject *unicode, PyObject *prefix, PyObject *start);
extern PyObject *UNICODE_STARTSWITH4(PyThreadState *tstate, PyObject *unicode, PyObject *prefix, PyObject *start,
                                     PyObject *end);
extern PyObject *UNICODE_STRIP1(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_STRIP2(PyThreadState *tstate, PyObject *unicode, PyObject *chars);
extern PyObject *UNICODE_SWAPCASE(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_TITLE(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_TRANSLATE(PyThreadState *tstate, PyObject *unicode, PyObject *table);
extern PyObject *UNICODE_UPPER(PyThreadState *tstate, PyObject *unicode);
extern PyObject *UNICODE_ZFILL(PyThreadState *tstate, PyObject *unicode, PyObject *width);
#if PYTHON_VERSION >= 0x300
extern PyObject *BYTES_CAPITALIZE(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_CENTER2(PyThreadState *tstate, PyObject *bytes, PyObject *width);
extern PyObject *BYTES_CENTER3(PyThreadState *tstate, PyObject *bytes, PyObject *width, PyObject *fillchar);
extern PyObject *BYTES_COUNT2(PyThreadState *tstate, PyObject *bytes, PyObject *sub);
extern PyObject *BYTES_COUNT3(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start);
extern PyObject *BYTES_COUNT4(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *BYTES_DECODE1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_DECODE2(PyThreadState *tstate, PyObject *bytes, PyObject *encoding);
extern PyObject *BYTES_DECODE3(PyThreadState *tstate, PyObject *bytes, PyObject *encoding, PyObject *errors);
extern PyObject *BYTES_ENDSWITH2(PyThreadState *tstate, PyObject *bytes, PyObject *suffix);
extern PyObject *BYTES_ENDSWITH3(PyThreadState *tstate, PyObject *bytes, PyObject *suffix, PyObject *start);
extern PyObject *BYTES_ENDSWITH4(PyThreadState *tstate, PyObject *bytes, PyObject *suffix, PyObject *start,
                                 PyObject *end);
extern PyObject *BYTES_EXPANDTABS1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_EXPANDTABS2(PyThreadState *tstate, PyObject *bytes, PyObject *tabsize);
extern PyObject *BYTES_FIND2(PyThreadState *tstate, PyObject *bytes, PyObject *sub);
extern PyObject *BYTES_FIND3(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start);
extern PyObject *BYTES_FIND4(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *BYTES_INDEX2(PyThreadState *tstate, PyObject *bytes, PyObject *sub);
extern PyObject *BYTES_INDEX3(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start);
extern PyObject *BYTES_INDEX4(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *BYTES_ISALNUM(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_ISALPHA(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_ISDIGIT(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_ISLOWER(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_ISSPACE(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_ISTITLE(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_ISUPPER(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_JOIN(PyThreadState *tstate, PyObject *bytes, PyObject *iterable);
extern PyObject *BYTES_LJUST2(PyThreadState *tstate, PyObject *bytes, PyObject *width);
extern PyObject *BYTES_LJUST3(PyThreadState *tstate, PyObject *bytes, PyObject *width, PyObject *fillchar);
extern PyObject *BYTES_LOWER(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_LSTRIP1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_LSTRIP2(PyThreadState *tstate, PyObject *bytes, PyObject *chars);
extern PyObject *BYTES_PARTITION(PyThreadState *tstate, PyObject *bytes, PyObject *sep);
extern PyObject *BYTES_REPLACE3(PyThreadState *tstate, PyObject *bytes, PyObject *old, PyObject *new_value);
extern PyObject *BYTES_REPLACE4(PyThreadState *tstate, PyObject *bytes, PyObject *old, PyObject *new_value,
                                PyObject *count);
extern PyObject *BYTES_RFIND2(PyThreadState *tstate, PyObject *bytes, PyObject *sub);
extern PyObject *BYTES_RFIND3(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start);
extern PyObject *BYTES_RFIND4(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *BYTES_RINDEX2(PyThreadState *tstate, PyObject *bytes, PyObject *sub);
extern PyObject *BYTES_RINDEX3(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start);
extern PyObject *BYTES_RINDEX4(PyThreadState *tstate, PyObject *bytes, PyObject *sub, PyObject *start, PyObject *end);
extern PyObject *BYTES_RJUST2(PyThreadState *tstate, PyObject *bytes, PyObject *width);
extern PyObject *BYTES_RJUST3(PyThreadState *tstate, PyObject *bytes, PyObject *width, PyObject *fillchar);
extern PyObject *BYTES_RPARTITION(PyThreadState *tstate, PyObject *bytes, PyObject *sep);
extern PyObject *BYTES_RSPLIT1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_RSPLIT2(PyThreadState *tstate, PyObject *bytes, PyObject *sep);
extern PyObject *BYTES_RSPLIT3(PyThreadState *tstate, PyObject *bytes, PyObject *sep, PyObject *maxsplit);
extern PyObject *BYTES_RSTRIP1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_RSTRIP2(PyThreadState *tstate, PyObject *bytes, PyObject *chars);
extern PyObject *BYTES_SPLIT1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_SPLIT2(PyThreadState *tstate, PyObject *bytes, PyObject *sep);
extern PyObject *BYTES_SPLIT3(PyThreadState *tstate, PyObject *bytes, PyObject *sep, PyObject *maxsplit);
extern PyObject *BYTES_SPLITLINES1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_SPLITLINES2(PyThreadState *tstate, PyObject *bytes, PyObject *keepends);
extern PyObject *BYTES_STARTSWITH2(PyThreadState *tstate, PyObject *bytes, PyObject *prefix);
extern PyObject *BYTES_STARTSWITH3(PyThreadState *tstate, PyObject *bytes, PyObject *prefix, PyObject *start);
extern PyObject *BYTES_STARTSWITH4(PyThreadState *tstate, PyObject *bytes, PyObject *prefix, PyObject *start,
                                   PyObject *end);
extern PyObject *BYTES_STRIP1(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_STRIP2(PyThreadState *tstate, PyObject *bytes, PyObject *chars);
extern PyObject *BYTES_SWAPCASE(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_TITLE(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_TRANSLATE2(PyThreadState *tstate, PyObject *bytes, PyObject *table);
extern PyObject *BYTES_TRANSLATE3(PyThreadState *tstate, PyObject *bytes, PyObject *table, PyObject *delete_value);
extern PyObject *BYTES_UPPER(PyThreadState *tstate, PyObject *bytes);
extern PyObject *BYTES_ZFILL(PyThreadState *tstate, PyObject *bytes, PyObject *width);
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
