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

from .templates.CodeTemplatesExceptions import *
from .templates.CodeTemplatesImporting import *
from .templates.CodeTemplatesPrinting import *
from .templates.CodeTemplatesTuples import *
from .templates.CodeTemplatesLists import *
from .templates.CodeTemplatesDicts import *
from .templates.CodeTemplatesCalls import *
from .templates.CodeTemplatesClass import *
from .templates.CodeTemplatesLoops import *
from .templates.CodeTemplatesWith import *

from .templates.CodeTemplatesExecEval import *

# We have some very long lines in here that should not be shorter though.
# pylint: disable=C0301

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
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
    }
    else if ( traceback == false )
    {
        _exception.addTraceback( frame_guard.getFrame() );
    }
    traceback = true;

    _caught_%(try_count)d.save( _exception );

    frame_guard.detachFrame();
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
