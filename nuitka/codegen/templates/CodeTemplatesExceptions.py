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
""" Templates for raising exceptions, making assertions, and try/finally
    construct.

"""

try_except_template = """\
try
{
%(tried_code)s
}
catch ( PythonException &_exception )
{
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
    }
    else
    {
        _exception.addTraceback( frame_guard.getFrame0() );
    }

    frame_guard.preserveExistingException();

#if PYTHON_VERSION >= 300
    ExceptionRestorer%(guard_class)s restorer( &frame_guard );
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
    PyTracebackObject *tb_next = tb->tb_next;
    tb->tb_next = NULL;
    _exception.setTraceback( tb_next );

    throw;
}"""

try_except_reraise_finally_template = """\
if ( _caught_%(try_count)d.isEmpty() )
{
%(thrower_code)s
}
else
{
    _caught_%(try_count)d.rethrow();
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
PythonExceptionKeeper _caught_%(try_count)d;
#if PYTHON_VERSION < 300
int _at_lineno_%(try_count)d = 0;
#endif

%(rethrow_setups)s
try
{
    // Tried block:
%(tried_code)s
}
catch ( PythonException &_exception )
{
#if PYTHON_VERSION >= 300
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
    }
    else
    {
        _exception.addTraceback( frame_guard.getFrame0() );
    }
#else
    _at_lineno_%(try_count)d = frame_guard.getLineNumber();
#endif

    _caught_%(try_count)d.save( _exception );

#if PYTHON_VERSION >= 300
    frame_guard.preserveExistingException();

    _exception.toExceptionHandler();
#endif
}
%(rethrow_catchers)s
// Final block:
%(final_code)s
#if PYTHON_VERSION < 300
if ( _at_lineno_%(try_count)d != 0 )
{
   frame_guard.setLineNumber( _at_lineno_%(try_count)d );
}
#endif
_caught_%(try_count)d.rethrow();
// Final end
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
PyObjectTempKeeper1 _return_value_%(try_count)d;
"""

try_finally_template_catch_continue = """\
catch ( ContinueException const & )
{
    _continue_%(try_count)d = true;
}
"""

try_finally_template_catch_break = """\
catch ( BreakException const & )
{
    _break_%(try_count)d = true;
}
"""

try_finally_template_catch_return_value = """\
catch ( ReturnValueException const &e )
{
    _return_value_%(try_count)d.assign( e.getValue1() );
}
"""

try_finally_template_reraise_continue = """\
if ( _continue_%(try_count)d )
{
    throw ContinueException();
}"""

try_finally_template_reraise_break = """\
if ( _break_%(try_count)d )
{
    throw BreakException();
}"""

try_finally_template_reraise_return_value = """\
if ( _return_value_%(try_count)d.isKeeping() )
{
    throw ReturnValueException( _return_value_%(try_count)d.asObject1() );
}"""

try_finally_template_direct_return_value = """\
assert( _return_value_%(try_count)d.isKeeping() ); // Must be true as this is last.
return _return_value_%(try_count)d.asObject1();"""

try_finally_template_direct_generator_return_value = """\
assert( _return_value_%(try_count)d.isKeeping() ); // Must be true as this is last.
throw ReturnValueException( _return_value_%(try_count)d.asObject1() );"""


try_finally_template_indirect_return_value = """\
if ( _return_value_%(try_count)d.isKeeping() )
{
    return _return_value_%(try_count)d.asObject1();
}"""

try_finally_template_indirect_generator_return_value = """\
if ( _return_value_%(try_count)d.isKeeping() )
{
    throw ReturnValueException( _return_value_%(try_count)d.asObject1() );
}"""



# Very special template for:
# try:
#  x = next(iter)
# except StopIteration:
#  handler_code

template_try_next_except_stop_iteration = """\
PyObject *%(temp_var)s = ITERATOR_NEXT( %(source_identifier)s );

if ( %(temp_var)s == NULL )
{
%(handler_code)s
}
%(assignment_code)s"""
