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
genexpr_context_body_template = """

// This structure is for attachment as self of %(function_identifier)s.
// It is allocated at the time the genexpr object is created.
struct _context_%(function_identifier)s_t
{
    // Store the iterator provided at creation time here.
    PyObject *iterators[ %(iterator_count)d ];

    int iterator_level;

    // The generator expression can access a read-only closure of the creator.
    %(function_context_decl)s
};

static void _context_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)context_voidptr;

    %(function_context_release)s

    delete _python_context;
}
"""

make_genexpr_with_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_%(function_identifier)s_t *_python_context = new _context_%(function_identifier)s_t;

    // Set the iterator for the yielder to use
    _python_context->iterators[ 0 ] = MAKE_ITERATOR( iterated );
    _python_context->iterator_level = 0;

    for( int i = 1; i <= sizeof( _python_context->iterators ) / sizeof( PyObject * ); i++ )
    {
        _python_context->iterators[ i ] = NULL;
    }

    // Copy the closure values over.
    %(function_context_copy)s

    PyObject *yielder = PyKFunction_New( %(function_identifier)s, %(function_name_obj)s, %(module)s, %(function_doc)s, _python_context, _context_%(function_identifier)s_destructor );

    // Return an iterator to the yielder function.
    PyObject *result = PyCallIter_New( yielder, _sentinel_value );

    if ( result == NULL )
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create genexpr %(function_name)s" );
        throw _PythonException();
    }

    return result;
}
"""

genexpr_iterator_value_assignment = """
case %(iterator_index)d:
%(assignment_code)s
condition = %(condition_code)s;
   break;
"""

genexpr_iterator_making = """
case %(iterator_index)d:
   _python_context->iterators[ %(iterator_index)d ] = MAKE_ITERATOR( %(iterated_code)s );
   break;
"""

genexpr_function_template = """
// The function that is iterated over during generator expression execution. It is supposed to yield the next
// value as a return value.

static PyObject *%(function_identifier)s( PyObject *self )
{
    // The context of the genexpr.
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)self;

    try
    {
        while (_python_context->iterator_level != -1 && _python_context->iterator_level < %(iterator_count)d)
        {
            if ( _python_context->iterators[ _python_context->iterator_level ] == NULL )
            {
                switch(_python_context->iterator_level)
                {
                   case 0:
                       assert( false );
                       break;
                   %(iterator_making)s
                }
            }
            // TODO: Need to construct the iterators except level 0 here and create their iterator
            // if it is NULL

            PyObject *_python_genexpr_iter_value = ITERATOR_NEXT( _python_context->iterators[ _python_context->iterator_level ] );

            if ( _python_genexpr_iter_value == NULL )
            {
                Py_DECREF( _python_context->iterators[ _python_context->iterator_level ] );
                _python_context->iterators[ _python_context->iterator_level ] = NULL;

                _python_context->iterator_level -= 1;
            }
            else
            {
                bool condition;

                switch (_python_context->iterator_level)
                {
                    %(iterator_value_assign)s
                }

                // plug condition here, just don't increase if it mismatches
                if ( condition )
                {
                    _python_context->iterator_level += 1;
                }
            }
        }

        if ( _python_context->iterator_level == -1)
        {
            return INCREASE_REFCOUNT( _sentinel_value );
        }
        else
        {
            _python_context->iterator_level = %(iterator_count)d - 1;

            // Actual expressions generated.
            %(function_body)s
        }
    }
    catch (_PythonException &_exception)
    {
        _exception.toPython();
        ADD_TRACEBACK( %(module)s, %(file_identifier)s, %(name_identifier)s, _exception.getLine() );

        return NULL;
    }
}
"""
