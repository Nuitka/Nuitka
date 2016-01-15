#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
    Py_XDECREF( old );
}
"""

template_write_local_unclear_ref1 = """\
{
    PyObject *old = %(identifier)s;
    %(identifier)s = %(tmp_name)s;
    Py_INCREF( %(identifier)s );
    Py_XDECREF( old );
}
"""

template_write_local_empty_ref0 = """\
assert( %(identifier)s == NULL );
%(identifier)s = %(tmp_name)s;
"""

template_write_local_empty_ref1 = """\
assert( %(identifier)s == NULL );
Py_INCREF( %(tmp_name)s );
%(identifier)s = %(tmp_name)s;
"""

template_write_local_clear_ref0 = """\
{
    PyObject *old = %(identifier)s;
    assert( old != NULL );
    %(identifier)s = %(tmp_name)s;
    Py_DECREF( old );
}
"""

template_write_local_inplace = """\
%(identifier)s = %(tmp_name)s;
"""

template_write_shared_inplace = """\
PyCell_SET( %(identifier)s, %(tmp_name)s );
"""


template_write_local_clear_ref1 = """\
{
    PyObject *old = %(identifier)s;
    assert( old != NULL );
    %(identifier)s = %(tmp_name)s;
    Py_INCREF( %(identifier)s );
    Py_DECREF( old );
}
"""

template_write_shared_unclear_ref0 = """\
{
    PyObject *old = PyCell_GET( %(identifier)s );
    PyCell_SET( %(identifier)s, %(tmp_name)s );
    Py_XDECREF( old );
}
"""

template_write_shared_unclear_ref1 = """\
{
    PyObject *old = PyCell_GET( %(identifier)s );
    PyCell_SET( %(identifier)s, %(tmp_name)s );
    Py_INCREF( %(tmp_name)s );
    Py_XDECREF( old );
}
"""

template_write_shared_clear_ref0 = """\
assert( PyCell_GET( %(identifier)s ) == NULL );
PyCell_SET( %(identifier)s, %(tmp_name)s );
"""

template_write_shared_clear_ref1 = """\
assert( PyCell_GET( %(identifier)s ) == NULL );
Py_INCREF( %(tmp_name)s );
PyCell_SET( %(identifier)s, %(tmp_name)s );
"""


template_read_local = """\
%(tmp_name)s = %(identifier)s;
"""

template_del_local_tolerant = """\
Py_XDECREF( %(identifier)s );
%(identifier)s = NULL;
"""

template_del_shared_tolerant = """\
if ( %(identifier)s )
{
    Py_XDECREF( PyCell_GET( %(identifier)s ));
    PyCell_SET( %(identifier)s, NULL );
}
"""

template_del_local_intolerant = """\
%(result)s = %(identifier)s != NULL;
if ( %(result)s == true )
{
    Py_DECREF( %(identifier)s );
    %(identifier)s = NULL;
}
"""

# TODO: Storage will not be NULL. What is this used for.
template_del_shared_intolerant = """\
%(result)s = %(identifier)s != NULL && PyCell_GET( %(identifier)s ) != NULL;
if ( %(result)s == true )
{
    Py_DECREF( PyCell_GET( %(identifier)s ) );
    PyCell_SET( %(identifier)s, NULL );
}
"""

template_del_local_known = """\
CHECK_OBJECT( %(identifier)s );
Py_DECREF( %(identifier)s );
%(identifier)s = NULL;
"""

template_del_shared_known = """\
Py_DECREF( PyCell_GET( %(identifier)s ) );
PyCell_SET( %(identifier)s, NULL );
"""


template_release_unclear = """\
Py_XDECREF( %(identifier)s );
%(identifier)s = NULL;
"""

template_release_clear = """\
CHECK_OBJECT( (PyObject *)%(identifier)s );
Py_DECREF( %(identifier)s );
%(identifier)s = NULL;
"""

# TODO: Storage will not be NULL.
template_read_shared_unclear = """\
if ( %(identifier)s == NULL )
{
    %(tmp_name)s = NULL;
}
else
{
    %(tmp_name)s = PyCell_GET( %(identifier)s );
}
"""

template_read_shared_known = """\
%(tmp_name)s = PyCell_GET( %(identifier)s );
"""

# For module variable values, need to lookup in module dictionary or in
# built-in dictionary.

template_read_mvar_unclear = """\
%(tmp_name)s = GET_STRING_DICT_VALUE( moduledict_%(module_identifier)s, (Nuitka_StringObject *)%(var_name)s );

if (unlikely( %(tmp_name)s == NULL ))
{
    %(tmp_name)s = GET_STRING_DICT_VALUE( dict_builtin, (Nuitka_StringObject *)%(var_name)s );
}
"""

template_read_maybe_local_unclear = """\
%(tmp_name)s = PyDict_GetItem( %(locals_dict)s, %(var_name)s );

if ( %(tmp_name)s == NULL )
{
%(fallback)s
}
"""

template_del_global_unclear = """\
%(res_name)s = PyDict_DelItem( (PyObject *)moduledict_%(module_identifier)s, %(var_name)s );
if ( %(res_name)s == -1 ) CLEAR_ERROR_OCCURRED();
"""

template_update_locals_dict_value = """\
DICT_SYNC_FROM_VARIABLE(
    %(dict_name)s,
    %(var_name)s,
    %(access_code)s
);
"""

template_set_locals_dict_value = """\
if ( %(access_code)s )
{
    int res = PyDict_SetItem(
        %(dict_name)s,
        %(var_name)s,
        %(access_code)s
    );

    assert( res == 0 );
}
"""

template_update_locals_mapping_value = """\
%(tmp_name)s = MAPPING_SYNC_FROM_VARIABLE( %(mapping_name)s, %(var_name)s, %(access_code)s );
"""

template_set_locals_mapping_value = """\
if %(check_code)s
{
    %(tmp_name)s = SET_SUBSCRIPT(
        %(mapping_name)s,
        %(var_name)s,
        %(access_code)s
    );
}
"""


# TODO: Unused now.
template_assign_from_frame_locals = """\
if ( %(frame_identifier)s->f_locals == NULL )
{
    %(frame_identifier)s->f_locals = PyDict_New();
}
%(to_name)s = %(frame_identifier)s->f_locals;
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
