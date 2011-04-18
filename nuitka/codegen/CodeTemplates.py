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
""" Code templates one stop access. """

# Wildcard imports are here to centralize the templates for access through one module
# name, this one, they are not used here though. pylint: disable=W0401,W0614

from .templates.CodeTemplatesMain import *
from .templates.CodeTemplatesConstants import *

from .templates.CodeTemplatesFunction import *
from .templates.CodeTemplatesGeneratorExpression import *
from .templates.CodeTemplatesGeneratorFunction import *
from .templates.CodeTemplatesContraction import *

from .templates.CodeTemplatesParameterParsing import *

from .templates.CodeTemplatesAssignments import *
from .templates.CodeTemplatesExceptions import *
from .templates.CodeTemplatesImporting import *
from .templates.CodeTemplatesClass import *
from .templates.CodeTemplatesLoops import *
from .templates.CodeTemplatesWith import *

from .templates.CodeTemplatesExecEval import *

# We have some very long lines in here that should not be shorter though.
# pylint: disable=C0301

global_copyright = """\
// Generated code for Python source for module '%(name)s'

// This code is in part copyright Kay Hayen, license GPLv3. This has the consequence that
// your must either obtain a commercial license or also publish your original source code
// under the same license unless you don't distribute this source or its binary.
"""

try_finally_template = """\
_PythonExceptionKeeper _caught_%(try_count)d;
bool _continue_%(try_count)d = false;
bool _break_%(try_count)d = false;
bool _return_%(try_count)d = false;
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    _caught_%(try_count)d.save( _exception );
}
catch ( ContinueException &e )
{
    _continue_%(try_count)d = true;
}
catch ( BreakException &e )
{
    _break_%(try_count)d = true;
}
catch ( ReturnException &e )
{
    _return_%(try_count)d = true;
}

// Final code:
%(final_code)s

_caught_%(try_count)d.rethrow();

if ( _continue_%(try_count)d )
{
    throw ContinueException();
}
if ( _break_%(try_count)d )
{
    throw BreakException();
}
if ( _return_%(try_count)d )
{
    throw ReturnException();
}"""

try_except_template = """\
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


template_branch_one = """\
if ( %(condition)s )
{
%(branch_code)s
}"""

template_branch_two = """\
if ( %(condition)s )
{
%(branch_yes_code)s
}
else
{
%(branch_no_code)s
}"""
