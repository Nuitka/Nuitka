#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
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
PyCell_SET(%(identifier)s, %(tmp_name)s);
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
    PyCell_SET(%(identifier)s, %(tmp_name)s);
    Py_XDECREF(old);
}
"""

template_write_shared_unclear_ref1 = """\
{
    PyObject *old = Nuitka_Cell_GET(%(identifier)s);
    PyCell_SET(%(identifier)s, %(tmp_name)s);
    Py_INCREF(%(tmp_name)s);
    Py_XDECREF(old);
}
"""

template_write_shared_clear_ref0 = """\
assert(Nuitka_Cell_GET(%(identifier)s) == NULL);
PyCell_SET(%(identifier)s, %(tmp_name)s);
"""

template_write_shared_clear_ref1 = """\
assert(Nuitka_Cell_GET(%(identifier)s) == NULL);
Py_INCREF(%(tmp_name)s);
PyCell_SET(%(identifier)s, %(tmp_name)s);
"""


template_del_local_tolerant = """\
Py_XDECREF(%(identifier)s);
%(identifier)s = NULL;
"""

template_del_shared_tolerant = """\
{
    PyObject *old = Nuitka_Cell_GET(%(identifier)s);
    PyCell_SET(%(identifier)s, NULL);
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
    PyCell_SET(%(identifier)s, NULL);
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
    PyCell_SET(%(identifier)s, NULL);

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
%(to_name)s = DICT_GET_ITEM0(%(locals_dict)s, %(var_name)s);

if (%(to_name)s == NULL) {
%(fallback)s
}
"""

template_read_locals_dict_without_fallback = """\
%(to_name)s = DICT_GET_ITEM0(%(locals_dict)s, %(var_name)s);
"""


template_read_locals_mapping_with_fallback = """\
%(to_name)s = PyObject_GetItem(%(locals_dict)s, %(var_name)s);

if (%(to_name)s == NULL) {
    if (CHECK_AND_CLEAR_KEY_ERROR_OCCURRED()) {
%(fallback)s
        Py_INCREF(%(to_name)s);
    } else {
        goto %(exception_exit)s;
    }
}
"""

template_read_locals_mapping_without_fallback = """\
%(to_name)s = PyObject_GetItem(%(locals_dict)s, %(var_name)s);
"""

template_del_global_unclear = """\
%(res_name)s = PyDict_DelItem((PyObject *)moduledict_%(module_identifier)s, %(var_name)s);
%(result)s = %(res_name)s != -1;
if (%(result)s == false) CLEAR_ERROR_OCCURRED();
"""

template_del_global_known = """\
%(res_name)s = PyDict_DelItem((PyObject *)moduledict_%(module_identifier)s, %(var_name)s);
if (%(res_name)s == -1) CLEAR_ERROR_OCCURRED();
"""


template_update_locals_dict_value = """\
if (%(test_code)s) {
    PyObject *value;
%(access_code)s

    UPDATE_STRING_DICT0((PyDictObject *)%(dict_name)s, (Nuitka_StringObject *)%(var_name)s, value);
} else {
    int res = PyDict_DelItem(%(dict_name)s, %(var_name)s);

    if (res != 0) {
        CLEAR_ERROR_OCCURRED();
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
        CLEAR_ERROR_OCCURRED();
        %(tmp_name)s = true;
    }
}
"""

template_set_locals_mapping_value = """\
if (%(test_code)s) {
    PyObject *value;
%(access_code)s

    %(tmp_name)s = SET_SUBSCRIPT(
        %(mapping_name)s,
        %(var_name)s,
        value
    );
} else {
    %(tmp_name)s = true;
}
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())
