//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
static PyObject *str_builtin_format = NULL;
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
static void _initStrBuiltinMethods() {
#if PYTHON_VERSION < 0x300
    str_builtin_capitalize = PyObject_GetAttrString((PyObject *)&PyString_Type, "capitalize");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_center = PyObject_GetAttrString((PyObject *)&PyString_Type, "center");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_count = PyObject_GetAttrString((PyObject *)&PyString_Type, "count");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_decode = PyObject_GetAttrString((PyObject *)&PyString_Type, "decode");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_encode = PyObject_GetAttrString((PyObject *)&PyString_Type, "encode");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_endswith = PyObject_GetAttrString((PyObject *)&PyString_Type, "endswith");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_expandtabs = PyObject_GetAttrString((PyObject *)&PyString_Type, "expandtabs");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_find = PyObject_GetAttrString((PyObject *)&PyString_Type, "find");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_format = PyObject_GetAttrString((PyObject *)&PyString_Type, "format");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_index = PyObject_GetAttrString((PyObject *)&PyString_Type, "index");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_isalnum = PyObject_GetAttrString((PyObject *)&PyString_Type, "isalnum");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_isalpha = PyObject_GetAttrString((PyObject *)&PyString_Type, "isalpha");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_isdigit = PyObject_GetAttrString((PyObject *)&PyString_Type, "isdigit");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_islower = PyObject_GetAttrString((PyObject *)&PyString_Type, "islower");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_isspace = PyObject_GetAttrString((PyObject *)&PyString_Type, "isspace");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_istitle = PyObject_GetAttrString((PyObject *)&PyString_Type, "istitle");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_isupper = PyObject_GetAttrString((PyObject *)&PyString_Type, "isupper");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_join = PyObject_GetAttrString((PyObject *)&PyString_Type, "join");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_ljust = PyObject_GetAttrString((PyObject *)&PyString_Type, "ljust");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_lower = PyObject_GetAttrString((PyObject *)&PyString_Type, "lower");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_lstrip = PyObject_GetAttrString((PyObject *)&PyString_Type, "lstrip");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_partition = PyObject_GetAttrString((PyObject *)&PyString_Type, "partition");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_replace = PyObject_GetAttrString((PyObject *)&PyString_Type, "replace");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_rfind = PyObject_GetAttrString((PyObject *)&PyString_Type, "rfind");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_rindex = PyObject_GetAttrString((PyObject *)&PyString_Type, "rindex");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_rjust = PyObject_GetAttrString((PyObject *)&PyString_Type, "rjust");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_rpartition = PyObject_GetAttrString((PyObject *)&PyString_Type, "rpartition");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_rsplit = PyObject_GetAttrString((PyObject *)&PyString_Type, "rsplit");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_rstrip = PyObject_GetAttrString((PyObject *)&PyString_Type, "rstrip");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_split = PyObject_GetAttrString((PyObject *)&PyString_Type, "split");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_splitlines = PyObject_GetAttrString((PyObject *)&PyString_Type, "splitlines");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_startswith = PyObject_GetAttrString((PyObject *)&PyString_Type, "startswith");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_strip = PyObject_GetAttrString((PyObject *)&PyString_Type, "strip");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_swapcase = PyObject_GetAttrString((PyObject *)&PyString_Type, "swapcase");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_title = PyObject_GetAttrString((PyObject *)&PyString_Type, "title");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_translate = PyObject_GetAttrString((PyObject *)&PyString_Type, "translate");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_upper = PyObject_GetAttrString((PyObject *)&PyString_Type, "upper");
#endif
#if PYTHON_VERSION < 0x300
    str_builtin_zfill = PyObject_GetAttrString((PyObject *)&PyString_Type, "zfill");
#endif
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
static PyObject *unicode_builtin_format = NULL;
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
static void _initUnicodeBuiltinMethods() {
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
static PyObject *dict_builtin_fromkeys = NULL;
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
static void _initDictBuiltinMethods() {
    dict_builtin_clear = PyObject_GetAttrString((PyObject *)&PyDict_Type, "clear");
    dict_builtin_copy = PyObject_GetAttrString((PyObject *)&PyDict_Type, "copy");
    dict_builtin_fromkeys = PyObject_GetAttrString((PyObject *)&PyDict_Type, "fromkeys");
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

    PyObject *args[2] = {dict, key};
    return CALL_METHODDESCR_WITH_ARGS2(dict_builtin_pop, args);
}
PyObject *DICT_POP3(PyObject *dict, PyObject *key, PyObject *default_value) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);
    CHECK_OBJECT(default_value);

    PyObject *args[3] = {dict, key, default_value};
    return CALL_METHODDESCR_WITH_ARGS3(dict_builtin_pop, args);
}
PyObject *DICT_SETDEFAULT2(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);

    PyObject *args[2] = {dict, key};
    return CALL_METHODDESCR_WITH_ARGS2(dict_builtin_setdefault, args);
}
PyObject *DICT_SETDEFAULT3(PyObject *dict, PyObject *key, PyObject *default_value) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);
    CHECK_OBJECT(default_value);

    PyObject *args[3] = {dict, key, default_value};
    return CALL_METHODDESCR_WITH_ARGS3(dict_builtin_setdefault, args);
}
#if PYTHON_VERSION < 0x300
PyObject *STR_CAPITALIZE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_capitalize, str);
}
PyObject *STR_ENDSWITH2(PyObject *str, PyObject *suffix) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(suffix);

    PyObject *args[2] = {str, suffix};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_endswith, args);
}
PyObject *STR_ENDSWITH3(PyObject *str, PyObject *suffix, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);

    PyObject *args[3] = {str, suffix, start};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_endswith, args);
}
PyObject *STR_ENDSWITH4(PyObject *str, PyObject *suffix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {str, suffix, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(str_builtin_endswith, args);
}
PyObject *STR_FIND2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {str, sub};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_find, args);
}
PyObject *STR_FIND3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {str, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_find, args);
}
PyObject *STR_FIND4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {str, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(str_builtin_find, args);
}
PyObject *STR_INDEX2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {str, sub};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_index, args);
}
PyObject *STR_INDEX3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {str, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_index, args);
}
PyObject *STR_INDEX4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {str, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(str_builtin_index, args);
}
PyObject *STR_ISALNUM(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_isalnum, str);
}
PyObject *STR_ISALPHA(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_isalpha, str);
}
PyObject *STR_ISDIGIT(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_isdigit, str);
}
PyObject *STR_ISLOWER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_islower, str);
}
PyObject *STR_ISSPACE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_isspace, str);
}
PyObject *STR_ISTITLE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_istitle, str);
}
PyObject *STR_ISUPPER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_isupper, str);
}
PyObject *STR_LOWER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_lower, str);
}
PyObject *STR_LSTRIP1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_lstrip, str);
}
PyObject *STR_LSTRIP2(PyObject *str, PyObject *chars) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(chars);

    PyObject *args[2] = {str, chars};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_lstrip, args);
}
PyObject *STR_PARTITION(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *args[2] = {str, sep};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_partition, args);
}
PyObject *STR_REPLACE3(PyObject *str, PyObject *old, PyObject *new_value) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);

    PyObject *args[3] = {str, old, new_value};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_replace, args);
}
PyObject *STR_REPLACE4(PyObject *str, PyObject *old, PyObject *new_value, PyObject *count) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);
    CHECK_OBJECT(count);

    PyObject *args[4] = {str, old, new_value, count};
    return CALL_METHODDESCR_WITH_ARGS4(str_builtin_replace, args);
}
PyObject *STR_RFIND2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {str, sub};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_rfind, args);
}
PyObject *STR_RFIND3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {str, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_rfind, args);
}
PyObject *STR_RFIND4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {str, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(str_builtin_rfind, args);
}
PyObject *STR_RINDEX2(PyObject *str, PyObject *sub) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {str, sub};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_rindex, args);
}
PyObject *STR_RINDEX3(PyObject *str, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {str, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_rindex, args);
}
PyObject *STR_RINDEX4(PyObject *str, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {str, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(str_builtin_rindex, args);
}
PyObject *STR_RPARTITION(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *args[2] = {str, sep};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_rpartition, args);
}
PyObject *STR_RSPLIT1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_rsplit, str);
}
PyObject *STR_RSPLIT2(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *args[2] = {str, sep};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_rsplit, args);
}
PyObject *STR_RSPLIT3(PyObject *str, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *args[3] = {str, sep, maxsplit};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_rsplit, args);
}
PyObject *STR_RSTRIP1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_rstrip, str);
}
PyObject *STR_RSTRIP2(PyObject *str, PyObject *chars) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(chars);

    PyObject *args[2] = {str, chars};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_rstrip, args);
}
PyObject *STR_SPLIT1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_split, str);
}
PyObject *STR_SPLIT2(PyObject *str, PyObject *sep) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);

    PyObject *args[2] = {str, sep};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_split, args);
}
PyObject *STR_SPLIT3(PyObject *str, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *args[3] = {str, sep, maxsplit};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_split, args);
}
PyObject *STR_STARTSWITH2(PyObject *str, PyObject *prefix) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(prefix);

    PyObject *args[2] = {str, prefix};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_startswith, args);
}
PyObject *STR_STARTSWITH3(PyObject *str, PyObject *prefix, PyObject *start) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);

    PyObject *args[3] = {str, prefix, start};
    return CALL_METHODDESCR_WITH_ARGS3(str_builtin_startswith, args);
}
PyObject *STR_STARTSWITH4(PyObject *str, PyObject *prefix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {str, prefix, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(str_builtin_startswith, args);
}
PyObject *STR_STRIP1(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_strip, str);
}
PyObject *STR_STRIP2(PyObject *str, PyObject *chars) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    CHECK_OBJECT(chars);

    PyObject *args[2] = {str, chars};
    return CALL_METHODDESCR_WITH_ARGS2(str_builtin_strip, args);
}
PyObject *STR_SWAPCASE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_swapcase, str);
}
PyObject *STR_TITLE(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_title, str);
}
PyObject *STR_UPPER(PyObject *str) {
    CHECK_OBJECT(str);
    assert(PyString_CheckExact(str));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(str_builtin_upper, str);
}
#endif
PyObject *UNICODE_CAPITALIZE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_capitalize, unicode);
}
PyObject *UNICODE_ENDSWITH2(PyObject *unicode, PyObject *suffix) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(suffix);

    PyObject *args[2] = {unicode, suffix};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_endswith, args);
}
PyObject *UNICODE_ENDSWITH3(PyObject *unicode, PyObject *suffix, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);

    PyObject *args[3] = {unicode, suffix, start};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_endswith, args);
}
PyObject *UNICODE_ENDSWITH4(PyObject *unicode, PyObject *suffix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(suffix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {unicode, suffix, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(unicode_builtin_endswith, args);
}
PyObject *UNICODE_FIND2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {unicode, sub};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_find, args);
}
PyObject *UNICODE_FIND3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {unicode, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_find, args);
}
PyObject *UNICODE_FIND4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {unicode, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(unicode_builtin_find, args);
}
PyObject *UNICODE_INDEX2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {unicode, sub};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_index, args);
}
PyObject *UNICODE_INDEX3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {unicode, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_index, args);
}
PyObject *UNICODE_INDEX4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {unicode, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(unicode_builtin_index, args);
}
PyObject *UNICODE_ISALNUM(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_isalnum, unicode);
}
PyObject *UNICODE_ISALPHA(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_isalpha, unicode);
}
PyObject *UNICODE_ISDIGIT(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_isdigit, unicode);
}
PyObject *UNICODE_ISLOWER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_islower, unicode);
}
PyObject *UNICODE_ISSPACE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_isspace, unicode);
}
PyObject *UNICODE_ISTITLE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_istitle, unicode);
}
PyObject *UNICODE_ISUPPER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_isupper, unicode);
}
PyObject *UNICODE_LOWER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_lower, unicode);
}
PyObject *UNICODE_LSTRIP1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_lstrip, unicode);
}
PyObject *UNICODE_LSTRIP2(PyObject *unicode, PyObject *chars) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(chars);

    PyObject *args[2] = {unicode, chars};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_lstrip, args);
}
PyObject *UNICODE_REPLACE3(PyObject *unicode, PyObject *old, PyObject *new_value) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);

    PyObject *args[3] = {unicode, old, new_value};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_replace, args);
}
PyObject *UNICODE_REPLACE4(PyObject *unicode, PyObject *old, PyObject *new_value, PyObject *count) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(old);
    CHECK_OBJECT(new_value);
    CHECK_OBJECT(count);

    PyObject *args[4] = {unicode, old, new_value, count};
    return CALL_METHODDESCR_WITH_ARGS4(unicode_builtin_replace, args);
}
PyObject *UNICODE_RFIND2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {unicode, sub};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_rfind, args);
}
PyObject *UNICODE_RFIND3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {unicode, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_rfind, args);
}
PyObject *UNICODE_RFIND4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {unicode, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(unicode_builtin_rfind, args);
}
PyObject *UNICODE_RINDEX2(PyObject *unicode, PyObject *sub) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);

    PyObject *args[2] = {unicode, sub};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_rindex, args);
}
PyObject *UNICODE_RINDEX3(PyObject *unicode, PyObject *sub, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);

    PyObject *args[3] = {unicode, sub, start};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_rindex, args);
}
PyObject *UNICODE_RINDEX4(PyObject *unicode, PyObject *sub, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sub);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {unicode, sub, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(unicode_builtin_rindex, args);
}
PyObject *UNICODE_RSPLIT1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_rsplit, unicode);
}
PyObject *UNICODE_RSPLIT2(PyObject *unicode, PyObject *sep) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);

    PyObject *args[2] = {unicode, sep};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_rsplit, args);
}
PyObject *UNICODE_RSPLIT3(PyObject *unicode, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *args[3] = {unicode, sep, maxsplit};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_rsplit, args);
}
PyObject *UNICODE_RSTRIP1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_rstrip, unicode);
}
PyObject *UNICODE_RSTRIP2(PyObject *unicode, PyObject *chars) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(chars);

    PyObject *args[2] = {unicode, chars};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_rstrip, args);
}
PyObject *UNICODE_SPLIT1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_split, unicode);
}
PyObject *UNICODE_SPLIT2(PyObject *unicode, PyObject *sep) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);

    PyObject *args[2] = {unicode, sep};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_split, args);
}
PyObject *UNICODE_SPLIT3(PyObject *unicode, PyObject *sep, PyObject *maxsplit) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(sep);
    CHECK_OBJECT(maxsplit);

    PyObject *args[3] = {unicode, sep, maxsplit};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_split, args);
}
PyObject *UNICODE_STARTSWITH2(PyObject *unicode, PyObject *prefix) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(prefix);

    PyObject *args[2] = {unicode, prefix};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_startswith, args);
}
PyObject *UNICODE_STARTSWITH3(PyObject *unicode, PyObject *prefix, PyObject *start) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);

    PyObject *args[3] = {unicode, prefix, start};
    return CALL_METHODDESCR_WITH_ARGS3(unicode_builtin_startswith, args);
}
PyObject *UNICODE_STARTSWITH4(PyObject *unicode, PyObject *prefix, PyObject *start, PyObject *end) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(prefix);
    CHECK_OBJECT(start);
    CHECK_OBJECT(end);

    PyObject *args[4] = {unicode, prefix, start, end};
    return CALL_METHODDESCR_WITH_ARGS4(unicode_builtin_startswith, args);
}
PyObject *UNICODE_STRIP1(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_strip, unicode);
}
PyObject *UNICODE_STRIP2(PyObject *unicode, PyObject *chars) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    CHECK_OBJECT(chars);

    PyObject *args[2] = {unicode, chars};
    return CALL_METHODDESCR_WITH_ARGS2(unicode_builtin_strip, args);
}
PyObject *UNICODE_SWAPCASE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_swapcase, unicode);
}
PyObject *UNICODE_TITLE(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_title, unicode);
}
PyObject *UNICODE_UPPER(PyObject *unicode) {
    CHECK_OBJECT(unicode);
    assert(PyUnicode_CheckExact(unicode));

    return CALL_METHODDESCR_WITH_SINGLE_ARG(unicode_builtin_upper, unicode);
}
