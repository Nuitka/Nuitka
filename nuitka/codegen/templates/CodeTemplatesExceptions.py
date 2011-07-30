#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
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
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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
""" Templates for raising exceptions and making assertions.

"""

assertion_without_arg = """\
if ( %(condition)s )
{
    RAISE_EXCEPTION( &traceback, INCREASE_REFCOUNT( PyExc_AssertionError ), %(tb_maker)s );
}"""

assertion_with_arg = """\
if ( %(condition)s )
{
    RAISE_EXCEPTION( &traceback, INCREASE_REFCOUNT( PyExc_AssertionError ), %(failure_arg)s, %(tb_maker)s );
}"""

try_except_template = """\
_frame_exception_keeper.preserveExistingException();
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
        traceback = true;
    }

    _exception.toExceptionHandler();

%(exception_code)s
}"""

try_except_else_template = """\
_frame_exception_keeper.preserveExistingException();
bool _caught_%(except_count)d = false;
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    _caught_%(except_count)d = true;

    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
        traceback = true;
    }

    _exception.toExceptionHandler();

%(exception_code)s
}
if ( _caught_%(except_count)d == false )
{
%(else_code)s
}"""

frame_exceptionkeeper_setup = """\
FrameExceptionKeeper _frame_exception_keeper;"""
