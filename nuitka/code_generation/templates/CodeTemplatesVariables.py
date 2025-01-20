#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Templates for the variable handling.

"""

template_write_local_unclear_ref0 = """\
{
    PyObject *old = %(identifier)s;
    %(identifier)s = %(tmp_name)s;
    Py_XDECREF(old);
}
"""

template_write_local_unclear_ref1 = """\
{
    PyObject *old = %(identifier)s;
    %(identifier)s = %(tmp_name)s;
    Py_INCREF(%(identifier)s);
    Py_XDECREF(old);
}
"""

template_write_local_empty_ref0 = """\
assert(%(identifier)s == NULL);
%(identifier)s = %(tmp_name)s;"""

template_write_local_empty_ref1 = """\
assert(%(identifier)s == NULL);
Py_INCREF(%(tmp_name)s);
%(identifier)s = %(tmp_name)s;"""

template_write_local_clear_ref0 = """\
{
    PyObject *old = %(identifier)s;
    assert(old != NULL);
    %(identifier)s = %(tmp_name)s;
    Py_DECREF(old);
}
"""

template_write_local_inplace = """\
%(identifier)s = %(tmp_name)s;
"""

template_write_shared_inplace = """\
Nuitka_Cell_SET(%(identifier)s, %(tmp_name)s);
"""


template_write_local_clear_ref1 = """\
{
    PyObject *old = %(identifier)s;
    assert(old != NULL);
    %(identifier)s = %(tmp_name)s;
    Py_INCREF(%(identifier)s);
    Py_DECREF(old);
}
"""

template_write_shared_unclear_ref0 = """\
{
    PyObject *old = Nuitka_Cell_GET(%(identifier)s);
    Nuitka_Cell_SET(%(identifier)s, %(tmp_name)s);
    Py_XDECREF(old);
}
"""

template_write_shared_unclear_ref1 = """\
{
    PyObject *old = Nuitka_Cell_GET(%(identifier)s);
    Nuitka_Cell_SET(%(identifier)s, %(tmp_name)s);
    Py_INCREF(%(tmp_name)s);
    Py_XDECREF(old);
}
"""

template_write_shared_clear_ref0 = """\
assert(Nuitka_Cell_GET(%(identifier)s) == NULL);
Nuitka_Cell_SET(%(identifier)s, %(tmp_name)s);
"""

template_write_shared_clear_ref1 = """\
assert(Nuitka_Cell_GET(%(identifier)s) == NULL);
Py_INCREF(%(tmp_name)s);
Nuitka_Cell_SET(%(identifier)s, %(tmp_name)s);
"""


template_del_local_tolerant = """\
Py_XDECREF(%(identifier)s);
%(identifier)s = NULL;
"""

template_del_shared_tolerant = """\
{
    PyObject *old = Nuitka_Cell_GET(%(identifier)s);
    Nuitka_Cell_SET(%(identifier)s, NULL);
    Py_XDECREF(old);
}
"""

template_del_local_intolerant = """\
%(result)s = %(identifier)s != NULL;
if (likely(%(result)s)) {
    Py_DECREF(%(identifier)s);
    %(identifier)s = NULL;
}
"""

template_del_shared_intolerant = """\
{
    PyObject *old = Nuitka_Cell_GET(%(identifier)s);
    Nuitka_Cell_SET(%(identifier)s, NULL);
    Py_XDECREF(old);

    %(result)s = old != NULL;
}
"""

template_del_local_known = """\
CHECK_OBJECT(%(identifier)s);
Py_DECREF(%(identifier)s);
%(identifier)s = NULL;
"""

template_del_shared_known = """\
{
    PyObject *old = Nuitka_Cell_GET(%(identifier)s);
    Nuitka_Cell_SET(%(identifier)s, NULL);

    CHECK_OBJECT(old);
    Py_DECREF(old);
}
"""


template_release_object_unclear = """\
Py_XDECREF(%(identifier)s);"""

template_release_object_clear = """\
Py_DECREF(%(identifier)s);"""

template_read_shared_known = """\
%(tmp_name)s = Nuitka_Cell_GET(%(identifier)s);
"""

# For module variable values, need to lookup in module dictionary or in
# built-in dictionary.

# TODO: Only provide fallback for known actually possible values. Do this
# by keeping track of things that were added by "site.py" mechanisms. Then
# we can avoid the second call entirely for most cases.
template_read_mvar_unclear = """\
%(tmp_name)s = LOOKUP_MODULE_VALUE(moduledict_%(module_identifier)s, %(var_name)s);
"""

template_read_locals_dict_with_fallback = """\
%(to_name)s = %(dict_get_item)s(tstate, %(locals_dict)s, %(var_name)s);

if (%(to_name)s == NULL) {
%(fallback)s
}
"""

template_read_locals_dict_without_fallback = """\
%(to_name)s = DICT_GET_ITEM0(tstate, %(locals_dict)s, %(var_name)s);
"""


# Fallback has no ref, so take one to agree with PyObject_GetItem doing
# it.
template_read_locals_mapping_with_fallback_no_ref = """\
%(to_name)s = PyObject_GetItem(%(locals_dict)s, %(var_name)s);

if (%(to_name)s == NULL) {
    if (CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {
%(fallback)s
        Py_INCREF(%(to_name)s);
    } else {
        goto %(exception_exit)s;
    }
}
"""

template_read_locals_mapping_with_fallback_ref = """\
%(to_name)s = PyObject_GetItem(%(locals_dict)s, %(var_name)s);

if (%(to_name)s == NULL) {
    if (CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(tstate)) {
%(fallback)s
    } else {
        goto %(exception_exit)s;
    }
}
"""

template_read_locals_mapping_without_fallback = """\
%(to_name)s = PyObject_GetItem(%(locals_dict)s, %(var_name)s);
"""

# TODO: Have DICT_REMOVE_ITEM_WITHOUT_ERROR and use that instead.
template_del_global_unclear = """\
%(result)s = DICT_REMOVE_ITEM((PyObject *)moduledict_%(module_identifier)s, %(var_name)s);
if (%(result)s == false) CLEAR_ERROR_OCCURRED(tstate);
"""

template_del_global_known = """\
if (DICT_REMOVE_ITEM((PyObject *)moduledict_%(module_identifier)s, %(var_name)s) == false) {
    CLEAR_ERROR_OCCURRED(tstate);
}
"""

template_update_locals_dict_value = """\
if (%(test_code)s) {
    PyObject *value;
%(access_code)s

    UPDATE_STRING_DICT0((PyDictObject *)%(dict_name)s, (Nuitka_StringObject *)%(var_name)s, value);
} else {
    if (DICT_REMOVE_ITEM(%(dict_name)s, %(var_name)s) == false) {
        CLEAR_ERROR_OCCURRED(tstate);
    }
}
"""

template_set_locals_dict_value = """\
if (%(test_code)s) {
    PyObject *value;
%(access_code)s

    int res = PyDict_SetItem(
        %(dict_name)s,
        %(var_name)s,
        value
    );

    assert(res == 0);
}
"""

template_update_locals_mapping_value = """\
if (%(test_code)s) {
    PyObject *value;
%(access_code)s

    int res = PyObject_SetItem(
        %(mapping_name)s,
        %(var_name)s,
        value
    );

    %(tmp_name)s = res == 0;
} else {
    PyObject *test_value = PyObject_GetItem(
        %(mapping_name)s,
        %(var_name)s
    );

    if (test_value) {
        Py_DECREF(test_value);

        int res = PyObject_DelItem(
            %(mapping_name)s,
            %(var_name)s
        );

        %(tmp_name)s = res == 0;
    } else {
        CLEAR_ERROR_OCCURRED(tstate);
        %(tmp_name)s = true;
    }
}
"""

template_set_locals_mapping_value = """\
if (%(test_code)s) {
    PyObject *value;
%(access_code)s

    %(tmp_name)s = SET_SUBSCRIPT(
        tstate,
        %(mapping_name)s,
        %(var_name)s,
        value
    );
} else {
    %(tmp_name)s = true;
}
"""

template_module_variable_accessor_function = """\
static PyObject *%(accessor_function_name)s(PyThreadState *tstate) {
#if %(caching)s
    PyObject *result;

#if PYTHON_VERSION < 0x3b0
    static uint64_t dict_version = 0;
    static PyObject *cache_value = NULL;

    if (moduledict_%(module_identifier)s->ma_version_tag == dict_version) {
        CHECK_OBJECT_X(cache_value);
        result = cache_value;
    } else {
        dict_version = moduledict_%(module_identifier)s->ma_version_tag;

        result = GET_STRING_DICT_VALUE(moduledict_%(module_identifier)s, (Nuitka_StringObject *)%(var_name)s);
        cache_value = result;
    }
#else
    static uint32_t dict_keys_version = 0xFFFFFFFF;
    static Py_ssize_t cache_dk_index = 0;

    PyDictKeysObject *dk = moduledict_%(module_identifier)s->ma_keys;
    if (likely(DK_IS_UNICODE(dk))) {

#if PYTHON_VERSION >= 0x3c0
        uint32_t current_dk_version = _Nuitka_PyDictKeys_GetVersionForCurrentState(tstate->interp, dk);
#else
        uint32_t current_dk_version = _Nuitka_PyDictKeys_GetVersionForCurrentState(dk);
#endif

        if (current_dk_version != dict_keys_version) {
            dict_keys_version = current_dk_version;
            Py_hash_t hash = ((Nuitka_StringObject *)%(var_name)s)->_base._base.hash;
            assert(hash != -1);

            cache_dk_index = Nuitka_Py_unicodekeys_lookup_unicode(dk, %(var_name)s, hash);
        }

        if (cache_dk_index >= 0) {
            assert(dk->dk_kind != DICT_KEYS_SPLIT);

            PyDictUnicodeEntry *entries = DK_UNICODE_ENTRIES(dk);

            result = entries[cache_dk_index].me_value;

            if (unlikely(result == NULL)) {
                Py_hash_t hash = ((Nuitka_StringObject *)%(var_name)s)->_base._base.hash;
                assert(hash != -1);

                cache_dk_index = Nuitka_Py_unicodekeys_lookup_unicode(dk, %(var_name)s, hash);

                if (cache_dk_index >= 0) {
                    result = entries[cache_dk_index].me_value;
                }
            }
        } else {
            result = NULL;
        }
    } else {
        result = GET_STRING_DICT_VALUE(moduledict_%(module_identifier)s, (Nuitka_StringObject *)%(var_name)s);
    }
#endif

#else
    PyObject *result = GET_STRING_DICT_VALUE(moduledict_%(module_identifier)s, (Nuitka_StringObject *)%(var_name)s);
#endif

    if (unlikely(result == NULL)) {
        result = GET_STRING_DICT_VALUE(dict_builtin, (Nuitka_StringObject *)%(var_name)s);
    }

    return result;
}
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
