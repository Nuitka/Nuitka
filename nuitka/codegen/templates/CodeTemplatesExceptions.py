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
""" Templates for raising exceptions, making assertions, and try/finally construct.

"""

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
    }
    else
    {
        _exception.addTraceback( frame_guard.getFrame0() );
    }

#if PYTHON_VERSION > 300
    PythonExceptionStacker exception_restorer;
#endif

    _exception.toExceptionHandler();

%(exception_code)s
}"""

template_setup_except_handler_detaching = """\
frame_guard.detachFrame();"""

try_except_reraise_template = """\
{
    PyTracebackObject *tb = _exception.getTraceback();
    frame_guard.setLineNumber( tb->tb_lineno );
    _exception.setTraceback( tb->tb_next );
    tb->tb_next = NULL;

    throw;
}"""

try_except_reraise_unmatched_template = """\
else
{
    PyTracebackObject *tb = _exception.getTraceback();
    frame_guard.setLineNumber( tb->tb_lineno );
    _exception.setTraceback( tb->tb_next );
    tb->tb_next = NULL;

    throw;
}"""

try_finally_template = """\
_PythonExceptionKeeper _caught_%(try_count)d;

%(rethrow_setups)s
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
    else
    {
        _exception.addTraceback( frame_guard.getFrame0() );
    }

    _caught_%(try_count)d.save( _exception );

#if PYTHON_VERSION > 300
    _exception.toExceptionHandler();
#endif
}
%(rethrow_catchers)s
// Final code:
%(final_code)s
_caught_%(try_count)d.rethrow();
%(rethrow_raisers)s"""

try_finally_template_setup_continue = """\
bool _continue_%(try_count)d = false;
"""

try_finally_template_setup_break = """\
bool _break_%(try_count)d = false;
"""

try_finally_template_setup_generator_return = """\
bool _return_%(try_count)d = false;
"""

try_finally_template_setup_return_value = """\
PyObject *_return_value_%(try_count)d = NULL;
"""

try_finally_template_catch_continue = """\
catch ( ContinueException & )
{
    _continue_%(try_count)d = true;
}
"""

try_finally_template_catch_break = """\
catch ( BreakException & )
{
    _break_%(try_count)d = true;
}
"""

try_finally_template_catch_generator_return = """\
catch ( GeneratorReturnException & )
{
    _return_%(try_count)d = true;
}
"""

try_finally_template_catch_return_value = """\
catch ( ReturnValueException &e )
{
    _return_value_%(try_count)d = e.getValue();
}
"""

try_finally_template_reraise_continue = """\
if ( _continue_%(try_count)d )
{
    throw ContinueException();
}
"""

try_finally_template_reraise_break = """\
if ( _break_%(try_count)d )
{
    throw BreakException();
}
"""

try_finally_template_reraise_generator_return = """\
if ( _return_%(try_count)d )
{
    throw GeneratorReturnException();
}
"""

try_finally_template_reraise_return_value = """\
if ( _return_value_%(try_count)d != NULL )
{
    throw ReturnValueException( _return_value_%(try_count)d );
}"""


frame_exceptionkeeper_setup = """\
FrameExceptionKeeper _frame_exception_keeper;"""
