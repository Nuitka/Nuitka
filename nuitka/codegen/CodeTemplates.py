#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Code templates one stop access. """

# Wildcard imports are here to centralize the templates for access through one module
# name, this one, they are not used here though. pylint: disable=W0401,W0614

from .templates.CodeTemplatesMain import *
from .templates.CodeTemplatesConstants import *

from .templates.CodeTemplatesFunction import *
from .templates.CodeTemplatesGeneratorFunction import *

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

def enableDebug():
    templates = dict( globals() )

    class TemplateWrapper:
        """ Wrapper around templates, to better trace and control template usage. """
        def __init__( self, name, value ):
            self.name = name
            self.value = value

        def __str__( self ):
            return self.value

        def __mod__( self, other ):
            assert type( other ) is dict, self.name

            for key in other.keys():
                if "%%(%s)" % key not in self.value:
                    from logging import warning

                    warning( "Extra value '%s' provided to template '%s'.", key, self.name )

            return self.value % other

        def split( self, sep ):
            return self.value.split( sep )

    from nuitka.__past__ import iterItems

    for template_name, template_value in iterItems( templates ):
        if template_name.startswith( "_" ):
            continue

        if type( template_value ) is str:
            globals()[ template_name ] = TemplateWrapper(
                template_name,
                template_value
            )

from nuitka.Options import isDebug

if isDebug():
    enableDebug()
