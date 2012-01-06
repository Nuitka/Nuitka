#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Assignments - inplace primarily - related templates.

"""


template_inplace_var_assignment = """\
{
    PyObjectTemporary value( %(assign_source_identifier)s );
    PyObject *result = %(inplace_operation_code)s;

    if ( result != value.asObject() )
    {
        %(assignment_code)s
    }

    Py_DECREF( result );
}"""

template_inplace_subscript_assignment = """\
{
    PyObjectTemporary subscribed( %(subscribed_identifier)s );
    PyObjectTemporary subscript( %(subscript_identifier)s );
    PyObjectTemporary value( LOOKUP_SUBSCRIPT( subscribed.asObject(), subscript.asObject() ) );

    PyObject *result = %(operation_identifier)s;

    // Must set the subscript in any case, a subscript list object will otherwise
    // not be updated.
    SET_SUBSCRIPT( result, subscribed.asObject(), subscript.asObject() );

    Py_DECREF( result );
}"""

template_inplace_attribute_assignment = """\
{
    PyObjectTemporary target( %(target_identifier)s );
    PyObject *attribute = %(attribute_identifier)s;
    PyObjectTemporary value( LOOKUP_ATTRIBUTE ( target.asObject(), attribute ) );

    PyObject *result = %(operation_identifier)s;

    if ( result != value.asObject() )
    {
        SET_ATTRIBUTE( target.asObject(), attribute, result );
    }

    Py_DECREF( result );
}"""

template_inplace_slice_assignment = """\
{
    PyObjectTemporary target( %(target_identifier)s );
    Py_ssize_t lower = %(lower)s;
    Py_ssize_t upper = %(upper)s;
    PyObjectTemporary value( LOOKUP_INDEX_SLICE( target.asObject(), lower, upper ) );
    PyObjectTemporary updated( %(operation_identifier)s );

    SET_INDEX_SLICE( target.asObject(), lower, upper, updated.asObject() );
}"""
