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
""" Generator expressions code templates

"""

genexpr_context_body_template = """

// This structure is for attachment as self of %(function_identifier)s. It is allocated at
// the time the genexpr object is created.
struct _context_%(function_identifier)s_t
{
    // The generator expression can access a read-only closure of the creator.
%(context_decl)s
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

    // Copy the closure values over if any.
%(context_copy)s

    PyObject *result = Nuitka_Genexpr_New(
        %(function_identifier)s,
        %(function_name_obj)s,
        iterated, %(iterator_count)d,
        _python_context,
        _context_%(function_identifier)s_destructor
    );

    return result;
}
"""

genexpr_iterator_value_assignment = """\
case %(iterator_index)d:
%(assignment_code)s
condition = %(condition_code)s;
   break;
"""

genexpr_iterator_making = """\
case %(iterator_index)d:
   generator->iterators[ %(iterator_index)d ] = MAKE_ITERATOR( %(iterated_code)s );
   break;
"""

genexpr_function_template = """
static PyObject *frameobj_%(function_identifier)s( void )
{
   static PyObject *frameobj = NULL;

   if ( frameobj == NULL )
   {
      frameobj = MAKE_FRAME( %(filename_identifier)s, %(name_identifier)s, %(module)s );
   }

   return frameobj;
}

// The function that is iterated over during generator expression execution. It is
// supposed to yield the next value as a return value.

static PyObject *%(function_identifier)s( Nuitka_GenexprObject *generator )
{
    // The context of the genexpr.
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)generator->m_context;

    %(line_number_code)s
%(expression_temp_decl)s
    try
    {
        while ( generator->iterator_level != -1 && generator->iterator_level < %(iterator_count)d )
        {
            if ( generator->iterators[ generator->iterator_level ] == NULL )
            {
                switch( generator->iterator_level )
                {
                    case 0:
                        assert( false );
                        break;
%(iterator_making)s
#ifndef __NUITKA_NO_ASSERT__
                    default:
                        assert( false );
                        break;
#endif
                }
            }

            // Need to construct the iterators except level 0 here and create their iterator
            // if it is NULL

            PyObject *_python_genexpr_iter_value = ITERATOR_NEXT( generator->iterators[ generator->iterator_level ] );

            if ( _python_genexpr_iter_value == NULL )
            {
                Py_DECREF( generator->iterators[ generator->iterator_level ] );
                generator->iterators[ generator->iterator_level ] = NULL;

                generator->iterator_level -= 1;
            }
            else
            {
                bool condition;

                switch( generator->iterator_level )
                {
%(iterator_value_assign)s
#ifndef __NUITKA_NO_ASSERT__
                    default:
                        assert( false );
                        break;
#endif
                }

                // plug condition here, just don't increase if it mismatches
                if ( condition )
                {
                    generator->iterator_level += 1;
                }
            }
        }

        if ( generator->iterator_level == -1 )
        {
            return _sentinel_value;
        }
        else
        {
            generator->iterator_level = %(iterator_count)d - 1;

            // Actual expressions generated.
            %(function_body)s
        }
    }
    catch ( _PythonException &_exception )
    {
        _exception.addTraceback( frameobj_%(function_identifier)s() );
        _exception.toPython();

        return NULL;
    }
}
"""
