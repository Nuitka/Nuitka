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
static PyObject *str_builtin_capitalize = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_center = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_count = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_decode = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_encode = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_endswith = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_expandtabs = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_find = NULL;
#endif
#if PYTHON_VERSION < 0x300
PyObject *str_builtin_format = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_index = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_isalnum = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_isalpha = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_isdigit = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_islower = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_isspace = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_istitle = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_isupper = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_join = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_ljust = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_lower = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_lstrip = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_partition = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_replace = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_rfind = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_rindex = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_rjust = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_rpartition = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_rsplit = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_rstrip = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_split = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_splitlines = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_startswith = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_strip = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_swapcase = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_title = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_translate = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_upper = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *str_builtin_zfill = NULL;
#endif
#if PYTHON_VERSION < 0x300
static void _initStrBuiltinMethods(void) {
    str_builtin_capitalize = PyObject_GetAttrString((PyObject *)&PyString_Type, "capitalize");
    str_builtin_center = PyObject_GetAttrString((PyObject *)&PyString_Type, "center");
    str_builtin_count = PyObject_GetAttrString((PyObject *)&PyString_Type, "count");
    str_builtin_decode = PyObject_GetAttrString((PyObject *)&PyString_Type, "decode");
    str_builtin_encode = PyObject_GetAttrString((PyObject *)&PyString_Type, "encode");
    str_builtin_endswith = PyObject_GetAttrString((PyObject *)&PyString_Type, "endswith");
    str_builtin_expandtabs = PyObject_GetAttrString((PyObject *)&PyString_Type, "expandtabs");
    str_builtin_find = PyObject_GetAttrString((PyObject *)&PyString_Type, "find");
    str_builtin_format = PyObject_GetAttrString((PyObject *)&PyString_Type, "format");
    str_builtin_index = PyObject_GetAttrString((PyObject *)&PyString_Type, "index");
    str_builtin_isalnum = PyObject_GetAttrString((PyObject *)&PyString_Type, "isalnum");
    str_builtin_isalpha = PyObject_GetAttrString((PyObject *)&PyString_Type, "isalpha");
    str_builtin_isdigit = PyObject_GetAttrString((PyObject *)&PyString_Type, "isdigit");
    str_builtin_islower = PyObject_GetAttrString((PyObject *)&PyString_Type, "islower");
    str_builtin_isspace = PyObject_GetAttrString((PyObject *)&PyString_Type, "isspace");
    str_builtin_istitle = PyObject_GetAttrString((PyObject *)&PyString_Type, "istitle");
    str_builtin_isupper = PyObject_GetAttrString((PyObject *)&PyString_Type, "isupper");
    str_builtin_join = PyObject_GetAttrString((PyObject *)&PyString_Type, "join");
    str_builtin_ljust = PyObject_GetAttrString((PyObject *)&PyString_Type, "ljust");
    str_builtin_lower = PyObject_GetAttrString((PyObject *)&PyString_Type, "lower");
    str_builtin_lstrip = PyObject_GetAttrString((PyObject *)&PyString_Type, "lstrip");
    str_builtin_partition = PyObject_GetAttrString((PyObject *)&PyString_Type, "partition");
    str_builtin_replace = PyObject_GetAttrString((PyObject *)&PyString_Type, "replace");
    str_builtin_rfind = PyObject_GetAttrString((PyObject *)&PyString_Type, "rfind");
    str_builtin_rindex = PyObject_GetAttrString((PyObject *)&PyString_Type, "rindex");
    str_builtin_rjust = PyObject_GetAttrString((PyObject *)&PyString_Type, "rjust");
    str_builtin_rpartition = PyObject_GetAttrString((PyObject *)&PyString_Type, "rpartition");
    str_builtin_rsplit = PyObject_GetAttrString((PyObject *)&PyString_Type, "rsplit");
    str_builtin_rstrip = PyObject_GetAttrString((PyObject *)&PyString_Type, "rstrip");
    str_builtin_split = PyObject_GetAttrString((PyObject *)&PyString_Type, "split");
    str_builtin_splitlines = PyObject_GetAttrString((PyObject *)&PyString_Type, "splitlines");
    str_builtin_startswith = PyObject_GetAttrString((PyObject *)&PyString_Type, "startswith");
    str_builtin_strip = PyObject_GetAttrString((PyObject *)&PyString_Type, "strip");
    str_builtin_swapcase = PyObject_GetAttrString((PyObject *)&PyString_Type, "swapcase");
    str_builtin_title = PyObject_GetAttrString((PyObject *)&PyString_Type, "title");
    str_builtin_translate = PyObject_GetAttrString((PyObject *)&PyString_Type, "translate");
    str_builtin_upper = PyObject_GetAttrString((PyObject *)&PyString_Type, "upper");
    str_builtin_zfill = PyObject_GetAttrString((PyObject *)&PyString_Type, "zfill");
}
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_capitalize = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_center = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_count = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_decode = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_endswith = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_expandtabs = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_find = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_hex = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_index = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_isalnum = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_isalpha = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_isascii = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_isdigit = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_islower = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_isspace = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_istitle = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_isupper = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_join = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_ljust = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_lower = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_lstrip = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_maketrans = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_partition = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_replace = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_rfind = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_rindex = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_rjust = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_rpartition = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_rsplit = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_rstrip = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_split = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_splitlines = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_startswith = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_strip = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_swapcase = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_title = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_translate = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_upper = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static PyObject *bytes_builtin_zfill = NULL;
#endif
#if PYTHON_VERSION >= 0x300
static void _initBytesBuiltinMethods(void) {
    bytes_builtin_capitalize = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "capitalize");
    bytes_builtin_center = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "center");
    bytes_builtin_count = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "count");
    bytes_builtin_decode = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "decode");
    bytes_builtin_endswith = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "endswith");
    bytes_builtin_expandtabs = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "expandtabs");
    bytes_builtin_find = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "find");
    bytes_builtin_hex = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "hex");
    bytes_builtin_index = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "index");
    bytes_builtin_isalnum = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "isalnum");
    bytes_builtin_isalpha = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "isalpha");
    bytes_builtin_isascii = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "isascii");
    bytes_builtin_isdigit = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "isdigit");
    bytes_builtin_islower = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "islower");
    bytes_builtin_isspace = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "isspace");
    bytes_builtin_istitle = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "istitle");
    bytes_builtin_isupper = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "isupper");
    bytes_builtin_join = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "join");
    bytes_builtin_ljust = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "ljust");
    bytes_builtin_lower = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "lower");
    bytes_builtin_lstrip = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "lstrip");
    bytes_builtin_maketrans = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "maketrans");
    bytes_builtin_partition = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "partition");
    bytes_builtin_replace = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "replace");
    bytes_builtin_rfind = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "rfind");
    bytes_builtin_rindex = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "rindex");
    bytes_builtin_rjust = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "rjust");
    bytes_builtin_rpartition = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "rpartition");
    bytes_builtin_rsplit = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "rsplit");
    bytes_builtin_rstrip = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "rstrip");
    bytes_builtin_split = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "split");
    bytes_builtin_splitlines = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "splitlines");
    bytes_builtin_startswith = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "startswith");
    bytes_builtin_strip = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "strip");
    bytes_builtin_swapcase = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "swapcase");
    bytes_builtin_title = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "title");
    bytes_builtin_translate = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "translate");
    bytes_builtin_upper = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "upper");
    bytes_builtin_zfill = PyObject_GetAttrString((PyObject *)&PyBytes_Type, "zfill");
}
#endif
static PyObject *unicode_builtin_capitalize = NULL;
#if PYTHON_VERSION >= 0x300
static PyObject *unicode_builtin_casefold = NULL;
#endif
static PyObject *unicode_builtin_center = NULL;
static PyObject *unicode_builtin_count = NULL;
#if PYTHON_VERSION < 0x300
static PyObject *unicode_builtin_decode = NULL;
#endif
static PyObject *unicode_builtin_encode = NULL;
static PyObject *unicode_builtin_endswith = NULL;
static PyObject *unicode_builtin_expandtabs = NULL;
static PyObject *unicode_builtin_find = NULL;
PyObject *unicode_builtin_format = NULL;
#if PYTHON_VERSION >= 0x300
static PyObject *unicode_builtin_format_map = NULL;
#endif
static PyObject *unicode_builtin_index = NULL;
static PyObject *unicode_builtin_isalnum = NULL;
static PyObject *unicode_builtin_isalpha = NULL;
#if PYTHON_VERSION >= 0x300
static PyObject *unicode_builtin_isascii = NULL;
#endif
static PyObject *unicode_builtin_isdecimal = NULL;
static PyObject *unicode_builtin_isdigit = NULL;
#if PYTHON_VERSION >= 0x300
static PyObject *unicode_builtin_isidentifier = NULL;
#endif
static PyObject *unicode_builtin_islower = NULL;
static PyObject *unicode_builtin_isnumeric = NULL;
#if PYTHON_VERSION >= 0x300
static PyObject *unicode_builtin_isprintable = NULL;
#endif
static PyObject *unicode_builtin_isspace = NULL;
static PyObject *unicode_builtin_istitle = NULL;
static PyObject *unicode_builtin_isupper = NULL;
static PyObject *unicode_builtin_join = NULL;
static PyObject *unicode_builtin_ljust = NULL;
static PyObject *unicode_builtin_lower = NULL;
static PyObject *unicode_builtin_lstrip = NULL;
#if PYTHON_VERSION >= 0x300
static PyObject *unicode_builtin_maketrans = NULL;
#endif
static PyObject *unicode_builtin_partition = NULL;
static PyObject *unicode_builtin_replace = NULL;
static PyObject *unicode_builtin_rfind = NULL;
static PyObject *unicode_builtin_rindex = NULL;
static PyObject *unicode_builtin_rjust = NULL;
static PyObject *unicode_builtin_rpartition = NULL;
static PyObject *unicode_builtin_rsplit = NULL;
static PyObject *unicode_builtin_rstrip = NULL;
static PyObject *unicode_builtin_split = NULL;
static PyObject *unicode_builtin_splitlines = NULL;
static PyObject *unicode_builtin_startswith = NULL;
static PyObject *unicode_builtin_strip = NULL;
static PyObject *unicode_builtin_swapcase = NULL;
static PyObject *unicode_builtin_title = NULL;
static PyObject *unicode_builtin_translate = NULL;
static PyObject *unicode_builtin_upper = NULL;
static PyObject *unicode_builtin_zfill = NULL;
static void _initUnicodeBuiltinMethods(void) {
    unicode_builtin_capitalize = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "capitalize");
#if PYTHON_VERSION >= 0x300
    unicode_builtin_casefold = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "casefold");
#endif
    unicode_builtin_center = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "center");
    unicode_builtin_count = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "count");
#if PYTHON_VERSION < 0x300
    unicode_builtin_decode = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "decode");
#endif
    unicode_builtin_encode = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "encode");
    unicode_builtin_endswith = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "endswith");
    unicode_builtin_expandtabs = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "expandtabs");
    unicode_builtin_find = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "find");
    unicode_builtin_format = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "format");
#if PYTHON_VERSION >= 0x300
    unicode_builtin_format_map = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "format_map");
#endif
    unicode_builtin_index = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "index");
    unicode_builtin_isalnum = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isalnum");
    unicode_builtin_isalpha = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isalpha");
#if PYTHON_VERSION >= 0x300
    unicode_builtin_isascii = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isascii");
#endif
    unicode_builtin_isdecimal = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isdecimal");
    unicode_builtin_isdigit = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isdigit");
#if PYTHON_VERSION >= 0x300
    unicode_builtin_isidentifier = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isidentifier");
#endif
    unicode_builtin_islower = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "islower");
    unicode_builtin_isnumeric = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isnumeric");
#if PYTHON_VERSION >= 0x300
    unicode_builtin_isprintable = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isprintable");
#endif
    unicode_builtin_isspace = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isspace");
    unicode_builtin_istitle = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "istitle");
    unicode_builtin_isupper = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "isupper");
    unicode_builtin_join = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "join");
    unicode_builtin_ljust = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "ljust");
    unicode_builtin_lower = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "lower");
    unicode_builtin_lstrip = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "lstrip");
#if PYTHON_VERSION >= 0x300
    unicode_builtin_maketrans = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "maketrans");
#endif
    unicode_builtin_partition = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "partition");
    unicode_builtin_replace = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "replace");
    unicode_builtin_rfind = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "rfind");
    unicode_builtin_rindex = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "rindex");
    unicode_builtin_rjust = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "rjust");
    unicode_builtin_rpartition = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "rpartition");
    unicode_builtin_rsplit = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "rsplit");
    unicode_builtin_rstrip = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "rstrip");
    unicode_builtin_split = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "split");
    unicode_builtin_splitlines = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "splitlines");
    unicode_builtin_startswith = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "startswith");
    unicode_builtin_strip = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "strip");
    unicode_builtin_swapcase = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "swapcase");
    unicode_builtin_title = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "title");
    unicode_builtin_translate = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "translate");
    unicode_builtin_upper = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "upper");
    unicode_builtin_zfill = PyObject_GetAttrString((PyObject *)&PyUnicode_Type, "zfill");
}
static PyObject *dict_builtin_clear = NULL;
static PyObject *dict_builtin_copy = NULL;
static PyObject *dict_builtin_get = NULL;
#if PYTHON_VERSION < 0x300
static PyObject *dict_builtin_has_key = NULL;
#endif
static PyObject *dict_builtin_items = NULL;
#if PYTHON_VERSION < 0x300
static PyObject *dict_builtin_iteritems = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *dict_builtin_iterkeys = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *dict_builtin_itervalues = NULL;
#endif
static PyObject *dict_builtin_keys = NULL;
static PyObject *dict_builtin_pop = NULL;
static PyObject *dict_builtin_popitem = NULL;
static PyObject *dict_builtin_setdefault = NULL;
static PyObject *dict_builtin_update = NULL;
static PyObject *dict_builtin_values = NULL;
#if PYTHON_VERSION < 0x300
static PyObject *dict_builtin_viewitems = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *dict_builtin_viewkeys = NULL;
#endif
#if PYTHON_VERSION < 0x300
static PyObject *dict_builtin_viewvalues = NULL;
#endif
static void _initDictBuiltinMethods(void) {
    dict_builtin_clear = PyObject_GetAttrString((PyObject *)&PyDict_Type, "clear");
    dict_builtin_copy = PyObject_GetAttrString((PyObject *)&PyDict_Type, "copy");
    dict_builtin_get = PyObject_GetAttrString((PyObject *)&PyDict_Type, "get");
#if PYTHON_VERSION < 0x300
    dict_builtin_has_key = PyObject_GetAttrString((PyObject *)&PyDict_Type, "has_key");
#endif
    dict_builtin_items = PyObject_GetAttrString((PyObject *)&PyDict_Type, "items");
#if PYTHON_VERSION < 0x300
    dict_builtin_iteritems = PyObject_GetAttrString((PyObject *)&PyDict_Type, "iteritems");
#endif
#if PYTHON_VERSION < 0x300
    dict_builtin_iterkeys = PyObject_GetAttrString((PyObject *)&PyDict_Type, "iterkeys");
#endif
#if PYTHON_VERSION < 0x300
    dict_builtin_itervalues = PyObject_GetAttrString((PyObject *)&PyDict_Type, "itervalues");
#endif
    dict_builtin_keys = PyObject_GetAttrString((PyObject *)&PyDict_Type, "keys");
    dict_builtin_pop = PyObject_GetAttrString((PyObject *)&PyDict_Type, "pop");
    dict_builtin_popitem = PyObject_GetAttrString((PyObject *)&PyDict_Type, "popitem");
    dict_builtin_setdefault = PyObject_GetAttrString((PyObject *)&PyDict_Type, "setdefault");
    dict_builtin_update = PyObject_GetAttrString((PyObject *)&PyDict_Type, "update");
    dict_builtin_values = PyObject_GetAttrString((PyObject *)&PyDict_Type, "values");
#if PYTHON_VERSION < 0x300
    dict_builtin_viewitems = PyObject_GetAttrString((PyObject *)&PyDict_Type, "viewitems");
#endif
#if PYTHON_VERSION < 0x300
    dict_builtin_viewkeys = PyObject_GetAttrString((PyObject *)&PyDict_Type, "viewkeys");
#endif
#if PYTHON_VERSION < 0x300
    dict_builtin_viewvalues = PyObject_GetAttrString((PyObject *)&PyDict_Type, "viewvalues");
#endif
}
PyObject *DICT_POP2(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);

    PyObject *called = dict_builtin_pop;
    CHECK_OBJECT(called);

    PyObject *args[2] = {dict, key};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *DICT_POP3(PyObject *dict, PyObject *key, PyObject *default_value) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);
    CHECK_OBJECT(default_value);

    PyObject *called = dict_builtin_pop;
    CHECK_OBJECT(called);

    PyObject *args[3] = {dict, key, default_value};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *DICT_POPITEM(PyObject *dict) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    PyObject *called = dict_builtin_popitem;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, dict);

    return result;
}
PyObject *DICT_SETDEFAULT2(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);

    PyObject *called = dict_builtin_setdefault;
    CHECK_OBJECT(called);

    PyObject *args[2] = {dict, key};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *DICT_SETDEFAULT3(PyObject *dict, PyObject *key, PyObject *default_value) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);
    CHECK_OBJECT(default_value);

    PyObject *called = dict_builtin_setdefault;
    CHECK_OBJECT(called);

    PyObject *args[3] = {dict, key, default_value};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
#if PYTHON_VERSION < 0x300
PyObject *STR_CAPITALIZE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_capitalize;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_CENTER2(PyObject *str, PyObject *width) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(width);

    PyObject *called = str_builtin_center;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_CENTER3(PyObject *str, PyObject *width, PyObject *fillchar) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(width);
    CHECK_OBJECT(fillchar);

    PyObject *called = str_builtin_center;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, width, fillchar};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_COUNT2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *called = str_builtin_count;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_COUNT3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = str_builtin_count;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_COUNT4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = str_builtin_count;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_DECODE1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_decode;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_DECODE2(PyObject *str, PyObject *encoding) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(encoding);

    PyObject *called = str_builtin_decode;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, encoding};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_DECODE3(PyObject *str, PyObject *encoding, PyObject *errors) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    if (encoding == NULL) {
        encoding = PyString_FromString(PyUnicode_GetDefaultEncoding());
    } else {
        Py_INCREF(encoding);
    }
    CHECK_OBJECT(errors);

    PyObject *called = str_builtin_decode;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, encoding, errors};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    Py_DECREF(encoding);

    return result;
}
PyObject *STR_ENCODE1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_encode;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ENCODE2(PyObject *str, PyObject *encoding) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(encoding);

    PyObject *called = str_builtin_encode;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, encoding};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_ENCODE3(PyObject *str, PyObject *encoding, PyObject *errors) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(encoding);
    CHECK_OBJECT(errors);

    PyObject *called = str_builtin_encode;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, encoding, errors};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_ENDSWITH2(PyObject *str, PyObject *suffix) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(suffix);

    PyObject *called = str_builtin_endswith;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, suffix};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_ENDSWITH3(PyObject *str, PyObject *suffix, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);

    PyObject *called = str_builtin_endswith;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, suffix, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_ENDSWITH4(PyObject *str, PyObject *suffix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = str_builtin_endswith;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, suffix, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_EXPANDTABS1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_expandtabs;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_EXPANDTABS2(PyObject *str, PyObject *tabsize) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(tabsize);

    PyObject *called = str_builtin_expandtabs;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, tabsize};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_FIND2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *called = str_builtin_find;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_FIND3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = str_builtin_find;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_FIND4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = str_builtin_find;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_INDEX2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *called = str_builtin_index;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_INDEX3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = str_builtin_index;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_INDEX4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = str_builtin_index;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_ISALNUM(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_isalnum;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ISALPHA(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_isalpha;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ISDIGIT(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_isdigit;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ISLOWER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_islower;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ISSPACE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_isspace;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ISTITLE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_istitle;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ISUPPER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_isupper;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_LJUST2(PyObject *str, PyObject *width) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(width);

    PyObject *called = str_builtin_ljust;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_LJUST3(PyObject *str, PyObject *width, PyObject *fillchar) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(width);
    CHECK_OBJECT(fillchar);

    PyObject *called = str_builtin_ljust;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, width, fillchar};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_LOWER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_lower;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_LSTRIP1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_lstrip;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_LSTRIP2(PyObject *str, PyObject *chars) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(chars);

    PyObject *called = str_builtin_lstrip;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, chars};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_PARTITION(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *called = str_builtin_partition;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sep};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_REPLACE3(PyObject *str, PyObject *old, PyObject *new_value) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);

    PyObject *called = str_builtin_replace;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, old, new_value};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_REPLACE4(PyObject *str, PyObject *old, PyObject *new_value, PyObject *count) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);
    CHECK_OBJECT(count);

    PyObject *called = str_builtin_replace;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, old, new_value, count};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_RFIND2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *called = str_builtin_rfind;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_RFIND3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = str_builtin_rfind;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_RFIND4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = str_builtin_rfind;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_RINDEX2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *called = str_builtin_rindex;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_RINDEX3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = str_builtin_rindex;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_RINDEX4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = str_builtin_rindex;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_RJUST2(PyObject *str, PyObject *width) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(width);

    PyObject *called = str_builtin_rjust;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_RJUST3(PyObject *str, PyObject *width, PyObject *fillchar) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(width);
    CHECK_OBJECT(fillchar);

    PyObject *called = str_builtin_rjust;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, width, fillchar};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_RPARTITION(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *called = str_builtin_rpartition;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sep};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_RSPLIT1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_rsplit;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_RSPLIT2(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *called = str_builtin_rsplit;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sep};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_RSPLIT3(PyObject *str, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *called = str_builtin_rsplit;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, sep, maxsplit};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_RSTRIP1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_rstrip;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_RSTRIP2(PyObject *str, PyObject *chars) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(chars);

    PyObject *called = str_builtin_rstrip;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, chars};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_SPLIT1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_split;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_SPLIT2(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *called = str_builtin_split;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, sep};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_SPLIT3(PyObject *str, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *called = str_builtin_split;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, sep, maxsplit};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_SPLITLINES1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_splitlines;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_SPLITLINES2(PyObject *str, PyObject *keepends) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(keepends);

    PyObject *called = str_builtin_splitlines;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, keepends};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_STARTSWITH2(PyObject *str, PyObject *prefix) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(prefix);

    PyObject *called = str_builtin_startswith;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, prefix};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_STARTSWITH3(PyObject *str, PyObject *prefix, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);

    PyObject *called = str_builtin_startswith;
    CHECK_OBJECT(called);

    PyObject *args[3] = {str, prefix, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *STR_STARTSWITH4(PyObject *str, PyObject *prefix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = str_builtin_startswith;
    CHECK_OBJECT(called);

    PyObject *args[4] = {str, prefix, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *STR_STRIP1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_strip;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_STRIP2(PyObject *str, PyObject *chars) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(chars);

    PyObject *called = str_builtin_strip;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, chars};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_SWAPCASE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_swapcase;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_TITLE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_title;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_TRANSLATE(PyObject *str, PyObject *table) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(table);

    PyObject *called = str_builtin_translate;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, table};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *STR_UPPER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    PyObject *called = str_builtin_upper;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, str);

    return result;
}
PyObject *STR_ZFILL(PyObject *str, PyObject *width) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(width);

    PyObject *called = str_builtin_zfill;
    CHECK_OBJECT(called);

    PyObject *args[2] = {str, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
#endif
PyObject *UNICODE_CAPITALIZE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_capitalize;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_CENTER2(PyObject *unicode, PyObject *width) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(width);

    PyObject *called = unicode_builtin_center;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_CENTER3(PyObject *unicode, PyObject *width, PyObject *fillchar) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(width);
    CHECK_OBJECT(fillchar);

    PyObject *called = unicode_builtin_center;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, width, fillchar};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_COUNT2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *called = unicode_builtin_count;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_COUNT3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = unicode_builtin_count;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_COUNT4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = unicode_builtin_count;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_ENCODE1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_encode;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ENCODE2(PyObject *unicode, PyObject *encoding) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(encoding);

    PyObject *called = unicode_builtin_encode;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, encoding};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_ENCODE3(PyObject *unicode, PyObject *encoding, PyObject *errors) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(encoding);
    CHECK_OBJECT(errors);

    PyObject *called = unicode_builtin_encode;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, encoding, errors};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_ENDSWITH2(PyObject *unicode, PyObject *suffix) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(suffix);

    PyObject *called = unicode_builtin_endswith;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, suffix};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_ENDSWITH3(PyObject *unicode, PyObject *suffix, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);

    PyObject *called = unicode_builtin_endswith;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, suffix, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_ENDSWITH4(PyObject *unicode, PyObject *suffix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = unicode_builtin_endswith;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, suffix, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_EXPANDTABS1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_expandtabs;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_EXPANDTABS2(PyObject *unicode, PyObject *tabsize) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(tabsize);

    PyObject *called = unicode_builtin_expandtabs;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, tabsize};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_FIND2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *called = unicode_builtin_find;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_FIND3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = unicode_builtin_find;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_FIND4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = unicode_builtin_find;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_INDEX2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *called = unicode_builtin_index;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_INDEX3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = unicode_builtin_index;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_INDEX4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = unicode_builtin_index;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_ISALNUM(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_isalnum;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ISALPHA(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_isalpha;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ISDIGIT(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_isdigit;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ISLOWER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_islower;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ISSPACE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_isspace;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ISTITLE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_istitle;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ISUPPER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_isupper;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_LJUST2(PyObject *unicode, PyObject *width) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(width);

    PyObject *called = unicode_builtin_ljust;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_LJUST3(PyObject *unicode, PyObject *width, PyObject *fillchar) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(width);
    CHECK_OBJECT(fillchar);

    PyObject *called = unicode_builtin_ljust;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, width, fillchar};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_LOWER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_lower;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_LSTRIP1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_lstrip;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_LSTRIP2(PyObject *unicode, PyObject *chars) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(chars);

    PyObject *called = unicode_builtin_lstrip;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, chars};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_REPLACE3(PyObject *unicode, PyObject *old, PyObject *new_value) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);

    PyObject *called = unicode_builtin_replace;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, old, new_value};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_REPLACE4(PyObject *unicode, PyObject *old, PyObject *new_value, PyObject *count) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);
    CHECK_OBJECT(count);

    PyObject *called = unicode_builtin_replace;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, old, new_value, count};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_RFIND2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *called = unicode_builtin_rfind;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_RFIND3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = unicode_builtin_rfind;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_RFIND4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = unicode_builtin_rfind;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_RINDEX2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *called = unicode_builtin_rindex;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, sub};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_RINDEX3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *called = unicode_builtin_rindex;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, sub, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_RINDEX4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = unicode_builtin_rindex;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, sub, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_RJUST2(PyObject *unicode, PyObject *width) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(width);

    PyObject *called = unicode_builtin_rjust;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_RJUST3(PyObject *unicode, PyObject *width, PyObject *fillchar) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(width);
    CHECK_OBJECT(fillchar);

    PyObject *called = unicode_builtin_rjust;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, width, fillchar};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_RSPLIT1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_rsplit;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_RSPLIT2(PyObject *unicode, PyObject *sep) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);

    PyObject *called = unicode_builtin_rsplit;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, sep};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_RSPLIT3(PyObject *unicode, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *called = unicode_builtin_rsplit;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, sep, maxsplit};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_RSTRIP1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_rstrip;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_RSTRIP2(PyObject *unicode, PyObject *chars) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(chars);

    PyObject *called = unicode_builtin_rstrip;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, chars};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_SPLIT1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_split;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_SPLIT2(PyObject *unicode, PyObject *sep) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);

    PyObject *called = unicode_builtin_split;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, sep};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_SPLIT3(PyObject *unicode, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *called = unicode_builtin_split;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, sep, maxsplit};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_SPLITLINES1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_splitlines;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_SPLITLINES2(PyObject *unicode, PyObject *keepends) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(keepends);

    PyObject *called = unicode_builtin_splitlines;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, keepends};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_STARTSWITH2(PyObject *unicode, PyObject *prefix) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(prefix);

    PyObject *called = unicode_builtin_startswith;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, prefix};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_STARTSWITH3(PyObject *unicode, PyObject *prefix, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);

    PyObject *called = unicode_builtin_startswith;
    CHECK_OBJECT(called);

    PyObject *args[3] = {unicode, prefix, start};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
PyObject *UNICODE_STARTSWITH4(PyObject *unicode, PyObject *prefix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *called = unicode_builtin_startswith;
    CHECK_OBJECT(called);

    PyObject *args[4] = {unicode, prefix, start, end};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS4(called, args);

    return result;
}
PyObject *UNICODE_STRIP1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_strip;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_STRIP2(PyObject *unicode, PyObject *chars) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(chars);

    PyObject *called = unicode_builtin_strip;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, chars};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_SWAPCASE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_swapcase;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_TITLE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_title;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_TRANSLATE(PyObject *unicode, PyObject *table) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(table);

    PyObject *called = unicode_builtin_translate;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, table};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *UNICODE_UPPER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    PyObject *called = unicode_builtin_upper;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, unicode);

    return result;
}
PyObject *UNICODE_ZFILL(PyObject *unicode, PyObject *width) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(width);

    PyObject *called = unicode_builtin_zfill;
    CHECK_OBJECT(called);

    PyObject *args[2] = {unicode, width};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
#if PYTHON_VERSION >= 0x300
PyObject *BYTES_DECODE1(PyObject *bytes) {
    CHECK_OBJECT(bytes);
    assert(PyBytes_CheckExact(bytes));

    PyObject *called = bytes_builtin_decode;
    CHECK_OBJECT(called);

    PyObject *result = CALL_METHODDESCR_WITH_SINGLE_ARG(called, bytes);

    return result;
}
PyObject *BYTES_DECODE2(PyObject *bytes, PyObject *encoding) {
    CHECK_OBJECT(bytes);
    assert(PyBytes_CheckExact(bytes));

    CHECK_OBJECT(encoding);

    PyObject *called = bytes_builtin_decode;
    CHECK_OBJECT(called);

    PyObject *args[2] = {bytes, encoding};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS2(called, args);

    return result;
}
PyObject *BYTES_DECODE3(PyObject *bytes, PyObject *encoding, PyObject *errors) {
    CHECK_OBJECT(bytes);
    assert(PyBytes_CheckExact(bytes));

    CHECK_OBJECT(encoding);
    CHECK_OBJECT(errors);

    PyObject *called = bytes_builtin_decode;
    CHECK_OBJECT(called);

    PyObject *args[3] = {bytes, encoding, errors};
    PyObject *result = CALL_METHODDESCR_WITH_ARGS3(called, args);

    return result;
}
#endif
