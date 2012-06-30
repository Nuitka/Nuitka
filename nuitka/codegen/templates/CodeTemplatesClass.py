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
""" Class building and defining related templates.

"""

class_decl_template = """
static PyObject *%(class_identifier)s( %(class_dict_args)s );
"""

class_dict_template = """
static PyFrameObject *frame_%(class_identifier)s = NULL;
static PyCodeObject *_CODEOBJ_%(class_identifier)s = NULL;

static PyObject *%(class_identifier)s( %(class_dict_args)s )
{
    bool traceback = false;

    if ( isFrameUnusable( frame_%(class_identifier)s ) )
    {
        if ( frame_%(class_identifier)s )
        {
#if _DEBUG_REFRAME
            puts( "reframe for %(class_identifier)s" );
#endif

            Py_DECREF( frame_%(class_identifier)s );
        }

        if ( _CODEOBJ_%(class_identifier)s == NULL )
        {
            _CODEOBJ_%(class_identifier)s = MAKE_CODEOBJ( %(filename_identifier)s, %(name_identifier)s, %(line_number)d, _python_tuple_empty, 0, false );
        }

        frame_%(class_identifier)s = MAKE_FRAME( _CODEOBJ_%(class_identifier)s, %(module_identifier)s );
    }

    FrameGuard frame_guard( frame_%(class_identifier)s );

    // Local variable declarations.
%(class_var_decl)s

    try
    {
        // Actual class code.
%(class_body)s
    }
    catch ( _PythonException &_exception )
    {
        if ( traceback == false )
        {
            _exception.addTraceback( frame_guard.getFrame() );
            throw _exception;
        }
        else
        {
            throw;
        }
    }
}

"""
