#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
if (%(identifier)s.object == NULL)
{
    %(identifier)s.object = %(tmp_name)s;
}
else
{
    PyObject *old = %(identifier)s.object;
    %(identifier)s.object = %(tmp_name)s;
    Py_DECREF( old );
}"""

template_write_local_unclear_ref1 = """\
if (%(identifier)s.object == NULL)
{
    %(identifier)s.object = INCREASE_REFCOUNT( %(tmp_name)s );
}
else
{
    PyObject *old = %(identifier)s.object;
    %(identifier)s.object = INCREASE_REFCOUNT( %(tmp_name)s );
    Py_DECREF( old );
}"""

template_write_shared_unclear_ref0 = """\
if (%(identifier)s.storage->object == NULL)
{
    %(identifier)s.storage->object = %(tmp_name)s;
}
else
{
    PyObject *old = %(identifier)s.storage->object;
    %(identifier)s.storage->object = %(tmp_name)s;
    Py_DECREF( old );
}"""

template_write_shared_unclear_ref1 = """\
if (%(identifier)s.storage->object == NULL)
{
    %(identifier)s.storage->object = INCREASE_REFCOUNT( %(tmp_name)s );
}
else
{
    PyObject *old = %(identifier)s.storage->object;
    %(identifier)s.storage->object = INCREASE_REFCOUNT( %(tmp_name)s );
    Py_DECREF( old );
}"""

template_read_local = """\
%(tmp_name)s = %(identifier)s.object;
"""

template_del_local_tolerant = """\
Py_XDECREF( %(identifier)s.object );
%(identifier)s.object = NULL;
"""

template_del_shared_tolerant = """\
if ( %(identifier)s.storage )
{
    Py_XDECREF( %(identifier)s.storage->object );
    %(identifier)s.storage->object = NULL;
}
"""

template_del_local_intolerant = """\
%(result)s = %(identifier)s.object != NULL;
if ( %(result)s == true )
{
    Py_DECREF( %(identifier)s.object );
    %(identifier)s.object = NULL;
}
"""

template_del_shared_intolerant = """\
%(result)s = %(identifier)s.storage != NULL && %(identifier)s.storage->object != NULL;
if ( %(result)s == true )
{
    Py_DECREF( %(identifier)s.storage->object );
    %(identifier)s.storage->object = NULL;
}
"""


template_read_shared_unclear = """\
if ( %(identifier)s.storage == NULL)
{
    %(tmp_name)s = NULL;
}
else
{
    %(tmp_name)s = %(identifier)s.storage->object;
}
"""

template_read_shared_known = """\
%(tmp_name)s = %(identifier)s.storage->object;
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
    %(tmp_name)s = GET_STRING_DICT_VALUE( moduledict_%(module_identifier)s, (Nuitka_StringObject *)%(var_name)s );
    if (unlikely( %(tmp_name)s == NULL ))
    {
        %(tmp_name)s = GET_STRING_DICT_VALUE( dict_builtin, (Nuitka_StringObject *)%(var_name)s );
    }
}
"""

template_del_global_unclear = """\
%(res_name)s = PyDict_DelItem( (PyObject *)moduledict_%(module_identifier)s, %(var_name)s );
if ( %(res_name)s == -1 ) PyErr_Clear();
"""
