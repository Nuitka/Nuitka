#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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
genfunc_context_body_template = """

#include <ucontext.h>

// This structure is for attachment as self of the generator function %(function_identifier)s and
// contains the common closure. It is allocated at the time the genexpr object is created.
struct _context_common_%(function_identifier)s_t
{
    // The generator function can access a read-only closure of the creator.
    %(function_common_context_decl)s
};

struct _context_generator_%(function_identifier)s_t
{
    _context_common_%(function_identifier)s_t *common_context;

    // The context to which the yielder hands over.
    ucontext_t yielder_context;
    ucontext_t caller_context;

    // The yielded value, to be filled by yielder before stopping activity and read
    // back by generator after switch back
    PyObject *yielded;

    // The generator function instance can access its parameters from creation time.
    %(function_instance_context_decl)s

    int magic;
    int number;
};

#ifndef __INSTANCE_COUNTER__
static int instance_counter = 0;
#define __INSTANCE_COUNTER__
#endif

static void _context_common_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_common_%(function_identifier)s_t *_python_context = (struct _context_common_%(function_identifier)s_t *)context_voidptr;

    %(function_context_free)s

    delete _python_context;
}

static void _context_generator_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_generator_%(function_identifier)s_t *_python_context = (struct _context_generator_%(function_identifier)s_t *)context_voidptr;

    assert( _python_context && _python_context->magic == 27772 );

    free( _python_context->yielder_context.uc_stack.ss_sp );

    delete _python_context;
}
"""

make_genfunc_with_context_template = """
static PyMethodDef _methoddef_%(function_identifier)s = {"%(function_name)s", (PyCFunction)%(function_identifier)s, METH_VARARGS | METH_KEYWORDS, NULL};

static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_common_%(function_identifier)s_t *_python_context = new _context_common_%(function_identifier)s_t;

    // Copy the parameter default values and closure values over.
    %(function_context_copy)s

    PyObject *_python_self = PyCObject_FromVoidPtr( _python_context, _context_common_%(function_identifier)s_destructor );

    if (_python_self == NULL)
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
        throw _PythonException();
    }

    PyObject *result = PyKFunction_New( &_methoddef_%(function_identifier)s, _python_self, %(module)s, %(function_doc)s );

    // The self is to be released along with the new function which holds its own reference now, so release ours.
    Py_DECREF( _python_self );

    if (result == NULL)
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
        throw _PythonException();
    }

    // Apply decorators if any
    %(function_decorator_calls)s

    return result;
}

"""

genfunc_yielder_template = """

static PyTracebackObject *%(function_tb_maker)s( int line )
{
   PyFrameObject *frame = MAKE_FRAME( %(module)s, %(file_identifier)s, %(name_identifier)s, line );

   PyTracebackObject *result = MAKE_TRACEBACK_START( frame, line );

   Py_DECREF( frame );

   assert( result );

   return result;
}

static PyTracebackObject *%(function_tb_adder)s( int line )
{
    PyFrameObject *frame = MAKE_FRAME( %(module)s, %(file_identifier)s, %(name_identifier)s, line );

    // Inlining PyTraceBack_Here may be faster
    PyTraceBack_Here( frame );

    Py_DECREF( frame );
}

static void %(function_identifier)s_context( struct _context_generator_%(function_identifier)s_t *_python_context )
{
    assert( _python_context && _python_context->magic == 27772 );

    // Set the names of local variables if any
    %(local_var_naming)s

    bool traceback = false;

    try
    {
        // Actual function code.
        %(function_body)s

        _python_context->yielded = INCREASE_REFCOUNT( _sentinel_value );
    }
    catch (_PythonException &_exception)
    {
        _exception.toPython();

        if ( traceback == false )
        {
           ADD_TRACEBACK( %(module)s, %(file_identifier)s, %(name_identifier)s, _exception.getLine() );
        }

        _python_context->yielded = INCREASE_REFCOUNT( _sentinel_value );
    }

    swapcontext( &_python_context->yielder_context, &_python_context->caller_context );
}

static PyObject *%(function_identifier)s_yielder( PyObject *self, PyObject *args, PyObject *kw )
{
    struct _context_generator_%(function_identifier)s_t *_python_context = (struct _context_generator_%(function_identifier)s_t *)PyCObject_AsVoidPtr( self );

    assert( _python_context && _python_context->magic == 27772 );

    if ( _python_context->yielded != _sentinel_value )
    {
        _python_context->yielded = NULL;

        // Continue the yielder function.
        swapcontext( &_python_context->caller_context, &_python_context->yielder_context );

        // It is expected to fill next value before the swap back.
        PyObject *result = _python_context->yielded;

        if ( _python_context->yielded != _sentinel_value )
        {
            _python_context->yielded = NULL;
        }

        return result;
    }
    else
    {
       PyErr_Format( PyExc_StopIteration, "generator function is finished" );
       return NULL;
    }
}
"""

genfunc_function_template = """

static PyMethodDef _methoddef_%(function_identifier)s_yielder = {"%(function_name)s", (PyCFunction)%(function_identifier)s_yielder, METH_NOARGS, NULL};

static PyObject *%(function_identifier)s( PyObject *self, PyObject *args, PyObject *kw )
{
    struct _context_common_%(function_identifier)s_t *_python_common_context = (struct _context_common_%(function_identifier)s_t *)PyCObject_AsVoidPtr( self );

    try
    {
        struct _context_generator_%(function_identifier)s_t *_python_context = new _context_generator_%(function_identifier)s_t;

        _python_context->yielder_context.uc_stack.ss_sp = NULL;
        _python_context->yielder_context.uc_link = NULL;
        _python_context->yielded = NULL;

        %(parameter_parsing_code)s

        // TODO: Is this one necessary at all?
        if (getcontext( &_python_context->yielder_context ) == -1)
        {
            PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
            throw _PythonException();
        }

        // Prepare the generator context to run
        _python_context->yielder_context.uc_stack.ss_size = 1024*1024;
        _python_context->yielder_context.uc_stack.ss_sp = malloc( _python_context->yielder_context.uc_stack.ss_size );

        makecontext( &_python_context->yielder_context, (void (*)())%(function_identifier)s_context, 1, _python_context );

        _python_context->common_context = _python_common_context;
        _python_context->magic = 27772;
        _python_context->number = ++instance_counter;

        PyObject *_generator_self = PyCObject_FromVoidPtr( _python_context, _context_generator_%(function_identifier)s_destructor );

        PyObject *yielder = PyKFunction_New( &_methoddef_%(function_identifier)s_yielder, _generator_self, %(module)s, Py_None );

        // The _generator_self is to be released along with the new function which holds its own reference now, so release ours.
        Py_DECREF( _generator_self );

        if (yielder == NULL)
        {
            PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
            throw _PythonException();
        }

        PyObject *result = PyCallIter_New( yielder, _sentinel_value );

        Py_DECREF( yielder );

        if (result == NULL)
        {
            PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
            throw _PythonException();
        }

        return result;
    }
    catch (_PythonException &_exception)
    {
        _exception.toPython();

        return NULL;
    }
}
"""
