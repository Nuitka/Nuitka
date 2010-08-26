# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
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


main_program = """\
// The main program for C++. It needs to prepare the interpreter and then
// calls the initialization code of the __main__ module.

int main( int argc, char *argv[] )
{
    // Register the initialization functions for modules included in the binary if any
    %(prepare_modules)s

    Py_Initialize();
    PySys_SetArgv( argc, argv );

    init__main__();
}

"""

module_template = """\

// The _module_%(module_name)s is a Python object pointer.

// Note: For full compatability with CPython, every module variable access needs to go through it
// except for cases where the module cannot possibly have changed in the mean time.

static PyObject *_module_%(module_name)s;

// The module filename.
static PyObject *_module_filename_%(module_name)s;

// The module level variables.
%(module_globals)s

// The module function declarations.
%(module_functions_decl)s

// The module function definitions.
%(module_functions_code)s

// The exported interface to CPython. On import of the module, this function gets called. It has have that exact function
// name.

static PyTracebackObject *%(module_tb_maker)s( int line )
{
   PyFrameObject *frame = MAKE_FRAME( _module_%(module_name)s, %(file_identifier)s, _python_str_angle_module, line );

   PyTracebackObject *result = MAKE_TRACEBACK_START( frame, line );

   Py_DECREF( frame );

   assert( result );

   return result;
}

void %(module_tb_adder)s( int line )
{
   ADD_TRACEBACK( _module_%(module_name)s, %(file_identifier)s, _python_str_angle_module, line );
}

PyMODINIT_FUNC init%(module_name)s(void)
{
    // puts( "in init%(module_name)s" );

    _module_builtin = PyImport_ImportModule( "__builtin__" );
    assert( _module_builtin );

    _module_marshal = PyImport_ImportModule( "marshal" );
    assert( _module_marshal );
    _module_marshal_function_loads = PyObject_GetAttrString( _module_marshal, "loads" );
    assert( _module_marshal_function_loads );

    _module_%(module_name)s = Py_InitModule4(
        "%(module_name)s",       // Module Name
        NULL,                    // No methods initially, all are added dynamically in actual code only.
        NULL,                    // No __doc__ is initially set, as it could not contain 0 this way, added early in actual code.
        NULL,                    // No self for modules, we don't use it.
        PYTHON_API_VERSION
    );

    // Initialize the constant values used.
    _initConstants();

    // Initialize the compiled type for functions.
    initKFunctionType();

    _mvar_%(module_name)s___doc__.assign( %(doc_identifier)s );
    _mvar_%(module_name)s___file__.assign( %(file_identifier)s );

    bool traceback = false;

    try
    {
        %(module_code)s
    }
    catch ( _PythonException &e )
    {
        e.toPython();

        if ( traceback == false )
        {
            %(module_tb_adder)s( e.getLine() );
        }

        PyErr_Print();
    }
}
"""

constant_reading = """

// We unstream some constant objects using the "marshal" module function "loads"
static PyObject *_module_marshal = NULL;
static PyObject *_module_marshal_function_loads = NULL;

// Sentinel PyObject to be used for all our call iterator endings. It will become
// a PyCObject pointing to NULL. TODO: Hopefully that is unique enough.
static PyObject *_sentinel_value = NULL;

%(const_declarations)s

static PyObject *_unstreamConstant( char const *buffer, int size )
{
    PyObject *temp = PyString_FromStringAndSize( buffer, size );

    PyObject *result = PyObject_CallFunctionObjArgs( _module_marshal_function_loads, temp, NULL );
    assert( result );

    Py_DECREF( temp );


    return result;
}

static int _initConstants()
{
    if (_sentinel_value == NULL)
    {
        _sentinel_value = PyCObject_FromVoidPtr( NULL, NULL );

        %(const_init)s
    }
}

"""
