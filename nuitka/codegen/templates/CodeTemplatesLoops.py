#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at a later time to
#     the PSF. With this version of Nuitka, using it for a Closed Source and
#     distributing the binary only is not allowed.
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
""" For and while loop related templates.

"""


_template_for_loop_break_continue_direct_else = """\
{
    PyObjectTemporary %(loop_iter_identifier)s( %(iterator)s );
    bool %(indicator_name)s = false;
    while( true )
    {
        %(line_number_code)s

        PyObject *%(loop_value_identifier)s = ITERATOR_NEXT( %(loop_iter_identifier)s.asObject() );

        // Check if end of iterator is reached
        if ( %(loop_value_identifier)s == NULL )
        {
            %(indicator_name)s = true;
            break;
        }

        // Assign from iterator returned value to for loop variables
        {
%(loop_var_assignment_code)s
        }

%(body)s
    }

    if ( %(indicator_name)s)
    {
%(else_codes)s
    }
}"""

_template_for_loop_break_continue_direct_no_else = """\
{
    PyObjectTemporary %(loop_iter_identifier)s( %(iterator)s );
    while( true )
    {
        %(line_number_code)s

        PyObject *%(loop_value_identifier)s = ITERATOR_NEXT( %(loop_iter_identifier)s.asObject() );

        // Check if end of iterator is reached
        if ( %(loop_value_identifier)s == NULL )
        {
            break;
        }

        // Assign from iterator returned value to for loop variables
        {
%(loop_var_assignment_code)s
        }

%(body)s
    }
}"""


_template_for_loop_break_continue_catching_else = """\
{
    PyObjectTemporary %(loop_iter_identifier)s( %(iterator)s );
    bool %(indicator_name)s = false;
    while( true )
    {
        %(line_number_code)s

        try
        {
            PyObject *%(loop_value_identifier)s = ITERATOR_NEXT( %(loop_iter_identifier)s.asObject() );

            // Check if end of iterator is reached
            if ( %(loop_value_identifier)s == NULL )
            {
                %(indicator_name)s = true;
                break;
            }

            // Assign from iterator returned value to for loop variables
            {
%(loop_var_assignment_code)s
            }

%(body)s
        }
        catch( ContinueException &e )
        { /* Nothing to do */
        }
        catch ( BreakException &e )
        { /* Break the loop */
            break;
        }
    }

    if ( %(indicator_name)s)
    {
%(else_codes)s
    }
}"""

_template_for_loop_break_continue_catching_no_else = """\
{
    PyObjectTemporary %(loop_iter_identifier)s( %(iterator)s );
    while( true )
    {
        %(line_number_code)s

        try
        {
            PyObject *%(loop_value_identifier)s = ITERATOR_NEXT( %(loop_iter_identifier)s.asObject() );

            // Check if end of iterator is reached
            if ( %(loop_value_identifier)s == NULL )
            {
                break;
            }

            // Assign from iterator returned value to for loop variables
            {
%(loop_var_assignment_code)s
            }

%(body)s
        }
        catch( ContinueException &e )
        { /* Nothing to do */
        }
        catch ( BreakException &e )
        { /* Break the loop */
            break;
        }
    }
}"""


def getForLoopTemplate( needs_exceptions, has_else_codes ):
    if needs_exceptions:
        if has_else_codes:
            return _template_for_loop_break_continue_catching_else
        else:
            return _template_for_loop_break_continue_catching_no_else
    else:
        if has_else_codes:
            return _template_for_loop_break_continue_direct_else
        else:
            return _template_for_loop_break_continue_direct_no_else




_template_while_loop_break_continue_catching_else = """\
bool %(indicator_name)s = false;
while ( %(condition)s )
{
    %(indicator_name)s = true;
    try
    {
%(loop_body_codes)s
    }
    catch( ContinueException &e )
    { /* Nothing to do */
    }
    catch ( BreakException &e )
    { /* Break the loop */
       break;
    }
}
if (%(indicator_name)s == false)
{
%(loop_else_codes)s
}"""

_template_while_loop_break_continue_catching_no_else = """\
while ( %(condition)s )
{
    try
    {
%(loop_body_codes)s
    }
    catch( ContinueException &e )
    { /* Nothing to do */
    }
    catch ( BreakException &e )
    { /* Break the loop */
       break;
    }
}"""

_template_while_loop_break_continue_direct_else = """\
bool %(indicator_name)s = false;
while ( %(condition)s )
{
    %(indicator_name)s = true;
%(loop_body_codes)s
}
if (%(indicator_name)s == false)
{
%(loop_else_codes)s
}"""

_template_while_loop_break_continue_direct_no_else = """\
while ( %(condition)s )
{
%(loop_body_codes)s
}"""

def getWhileLoopTemplate( needs_exceptions, has_else_codes ):
    if needs_exceptions:
        if has_else_codes:
            return _template_while_loop_break_continue_catching_else
        else:
            return _template_while_loop_break_continue_catching_no_else
    else:
        if has_else_codes:
            return _template_while_loop_break_continue_direct_else
        else:
            return _template_while_loop_break_continue_direct_no_else
