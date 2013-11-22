#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Main module code templates

This for the main program in case of executables, the module templates and
stuff related to importing, and of course the generated code license.

"""

global_copyright = """\
// Generated code for Python source for module '%(name)s'
// created by Nuitka version %(version)s

// This code is in part copyright 2013 Kay Hayen.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
"""

module_inittab_entry = """\
{ (char *)"%(module_name)s", MOD_INIT_NAME( %(module_identifier)s ), 0 },"""

main_program = """\
// The main program for C++. It needs to prepare the interpreter and then
// calls the initialization code of the __main__ module.

#include "structseq.h"
#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall WinMain( HINSTANCE hInstance, HINSTANCE hPrevInstance, char* lpCmdLine, int nCmdShow )
{
    int argc = __argc;
    char** argv = __argv;
#else
int main( int argc, char *argv[] )
{
#endif
#if _NUITKA_FROZEN
    preparePortableEnvironment( argv[0] );
#endif

    // Initialize Python environment.
    Py_DebugFlag = %(python_sysflag_debug)d;
#if %(python_sysflag_py3k_warning)d
    Py_Py3kWarningFlag = %(python_sysflag_py3k_warning)d;
#endif
#if %(python_sysflag_division_warning)d
    Py_DivisionWarningFlag =
#if %(python_sysflag_py3k_warning)d
        Py_Py3kWarningFlag ||
#endif
        %(python_sysflag_division_warning)d;
#endif
    Py_InspectFlag = %(python_sysflag_inspect)d;
    Py_InteractiveFlag = %(python_sysflag_interactive)d;
    Py_OptimizeFlag = %(python_sysflag_optimize)d;
    Py_DontWriteBytecodeFlag = %(python_sysflag_dont_write_bytecode)d;
    Py_NoUserSiteDirectory = %(python_sysflag_no_user_site)d;
    Py_IgnoreEnvironmentFlag = %(python_sysflag_ignore_environment)d;
#if %(python_sysflag_tabcheck)d
    Py_TabcheckFlag = %(python_sysflag_tabcheck)d;
#endif
    Py_VerboseFlag = %(python_sysflag_verbose)d;
#if %(python_sysflag_unicode)d
    Py_UnicodeFlag = %(python_sysflag_unicode)d;
#endif
    Py_BytesWarningFlag = %(python_sysflag_bytes_warning)d;
#if %(python_sysflag_hash_randomization)d
    Py_HashRandomizationFlag = %(python_sysflag_hash_randomization)d;
#endif

    // We want to import the site module, but only after we finished our own
    // setup. The site module import will be the first thing, the main module
    // does.
    Py_NoSiteFlag = 1;

    // Initialize the embedded CPython interpreter.
    setCommandLineParameters( argc, argv, true );
    Py_Initialize();

    // Lie about it, believe it or not, there are "site" files, that check
    // against later imports, see below.
    Py_NoSiteFlag = %(python_sysflag_no_site)d;

    // Set the command line parameters for run time usage.
    setCommandLineParameters( argc, argv, false );

    // Initialize the constant values used.
    _initBuiltinModule();
    _initConstants();
    _initBuiltinOriginalValues();

    // Revert the wrong sys.flags value, it's used by "site" on at least Debian
    // for Python3.3, more uses may exist.
#if %(python_sysflag_no_site)d == 0
#if PYTHON_VERSION >= 330
    PyStructSequence_SetItem( PySys_GetObject( "flags" ), 6, const_int_0 );
#elif PYTHON_VERSION >= 320
    PyStructSequence_SetItem( PySys_GetObject( "flags" ), 7, const_int_0 );
#elif PYTHON_VERSION >= 260
    PyStructSequence_SET_ITEM( PySys_GetObject( (char *)"flags" ), 9, const_int_0 );
#endif
#endif

    // Initialize the compiled types of Nuitka.
    PyType_Ready( &Nuitka_Generator_Type );
    PyType_Ready( &Nuitka_Function_Type );
    PyType_Ready( &Nuitka_Method_Type );
    PyType_Ready( &Nuitka_Frame_Type );
#if PYTHON_VERSION < 300
    initSlotCompare();
#endif

    enhancePythonTypes();

    // Set the sys.executable path to the original Python executable on Linux
    // or to python.exe on Windows.
    PySys_SetObject(
        (char *)"executable",
        %(sys_executable)s
    );

    patchBuiltinModule();
    patchTypeComparison();

    // Allow to override the ticker value, to remove checks for threads in
    // CPython core from impact on benchmarks.
    char const *ticker_value = getenv( "NUITKA_TICKER" );
    if ( ticker_value != NULL )
    {
        _Py_Ticker = atoi( ticker_value );
        assert ( _Py_Ticker >= 20 );
    }

    // Execute the "__main__" module init function.
    MOD_INIT_NAME( __main__ )();

    if ( ERROR_OCCURED() )
    {
        // Cleanup code may need a frame, so put one back.
        PyThreadState_GET()->frame = MAKE_FRAME( %(code_identifier)s, module___main__ );

        PyErr_PrintEx( 0 );
        Py_Exit( 1 );
    }
    else
    {
        Py_Exit( 0 );
    }
}
"""

module_header_template = """\

#include <nuitka/helpers.hpp>

MOD_INIT_DECL( %(module_identifier)s );

extern PyObject *module_%(module_identifier)s;
extern PyDictObject *moduledict_%(module_identifier)s;

// Declarations from this module to other modules if any.
%(extra_declarations)s
"""

module_body_template = """
#include "nuitka/prelude.hpp"

#include "__modules.hpp"
#include "__constants.hpp"
#include "__helpers.hpp"

// The _module_%(module_identifier)s is a Python object pointer of module type.

// Note: For full compatability with CPython, every module variable access
// needs to go through it except for cases where the module cannot possibly
// have changed in the mean time.

PyObject *module_%(module_identifier)s;
PyDictObject *moduledict_%(module_identifier)s;

NUITKA_MAY_BE_UNUSED static PyObject *GET_MODULE_VALUE0( PyObject *var_name )
{
    // For module variable values, need to lookup in module dictionary or in
    // built-in dictionary.

    PyObject *result = GET_STRING_DICT_VALUE( moduledict_%(module_identifier)s, (Nuitka_StringObject *)var_name );

    if (likely( result != NULL ))
    {
        assertObject( result );

        return result;
    }

    result = GET_STRING_DICT_VALUE( dict_builtin, (Nuitka_StringObject *)var_name );

    if (likely( result != NULL ))
    {
        assertObject( result );

        return result;
    }

    PyErr_Format( PyExc_NameError, "global name '%%s' is not defined", Nuitka_String_AsString( var_name ) );
    throw PythonException();
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_MODULE_VALUE1( PyObject *var_name )
{
    return INCREASE_REFCOUNT( GET_MODULE_VALUE0( var_name ) );
}

NUITKA_MAY_BE_UNUSED void static DEL_MODULE_VALUE( PyObject *var_name, bool tolerant )
{
    int status = PyDict_DelItem( (PyObject *)moduledict_%(module_identifier)s, var_name );

    if (unlikely( status == -1 && tolerant == false ))
    {
        PyErr_Format(
            PyExc_NameError,
            "global name '%%s' is not defined",
            Nuitka_String_AsString( var_name )
        );

        throw PythonException();
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_LOCALS_OR_MODULE_VALUE0( PyObject *locals_dict, PyObject *var_name )
{
    PyObject *result = PyDict_GetItem( locals_dict, var_name );

    if ( result != NULL )
    {
        return result;
    }
    else
    {
        return GET_MODULE_VALUE0( var_name );
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_LOCALS_OR_MODULE_VALUE1( PyObject *locals_dict, PyObject *var_name )
{
    PyObject *result = PyDict_GetItem( locals_dict, var_name );

    if ( result != NULL )
    {
        return INCREASE_REFCOUNT( result );
    }
    else
    {
        return GET_MODULE_VALUE1( var_name );
    }
}

// The module function declarations.
%(module_functions_decl)s

// The module function definitions.
%(module_functions_code)s

#if PYTHON_VERSION >= 300
static struct PyModuleDef mdef_%(module_identifier)s =
{
    PyModuleDef_HEAD_INIT,
    "%(module_name)s",   /* m_name */
    NULL,                /* m_doc */
    -1,                  /* m_size */
    NULL,                /* m_methods */
    NULL,                /* m_reload */
    NULL,                /* m_traverse */
    NULL,                /* m_clear */
    NULL,                /* m_free */
  };
#endif

#define _MODULE_UNFREEZER %(use_unfreezer)d

#if _MODULE_UNFREEZER

#include "nuitka/unfreezing.hpp"

// Table for lookup to find "frozen" modules or DLLs, i.e. the ones included in
// or along this binary.
static struct Nuitka_FreezeTableEntry _frozen_modules[] =
{
%(module_inittab)s
    { NULL, NULL, 0 }
};

#endif

// The exported interface to CPython. On import of the module, this function
// gets called. It has to have an exact function name, in cases it's a shared
// library export. This is hidden behind the MOD_INIT_DECL.

MOD_INIT_DECL( %(module_identifier)s )
{

#if defined( _NUITKA_EXE ) || PYTHON_VERSION >= 300
    static bool _init_done = false;

    // Packages can be imported recursively in deep executables.
    if ( _init_done )
    {
        return MOD_RETURN_VALUE( module_%(module_identifier)s );
    }
    else
    {
        _init_done = true;
    }
#endif

#ifdef _NUITKA_MODULE
    // In case of a stand alone extension module, need to call initialization
    // the init here because that's the first and only time we are going to get
    // called here.

    // Initialize the constant values used.
    _initBuiltinModule();
    _initConstants();

    // Initialize the compiled types of Nuitka.
    PyType_Ready( &Nuitka_Generator_Type );
    PyType_Ready( &Nuitka_Function_Type );
    PyType_Ready( &Nuitka_Method_Type );
    PyType_Ready( &Nuitka_Frame_Type );
#if PYTHON_VERSION < 300
    initSlotCompare();
#endif

    patchBuiltinModule();
    patchTypeComparison();

#endif

#if _MODULE_UNFREEZER
    registerMetaPathBasedUnfreezer( _frozen_modules );
#endif

    // puts( "in init%(module_identifier)s" );

    // Create the module object first. There are no methods initially, all are
    // added dynamically in actual code only.  Also no "__doc__" is initially
    // set at this time, as it could not contain NUL characters this way, they
    // are instead set in early module code.  No "self" for modules, we have no
    // use for it.
#if PYTHON_VERSION < 300
    module_%(module_identifier)s = Py_InitModule4(
        "%(module_name)s",       // Module Name
        NULL,                    // No methods initially, all are added
                                 // dynamically in actual module code only.
        NULL,                    // No __doc__ is initially set, as it could
                                 // not contain NUL this way, added early in
                                 // actual code.
        NULL,                    // No self for modules, we don't use it.
        PYTHON_API_VERSION
    );
#else
    module_%(module_identifier)s = PyModule_Create( &mdef_%(module_identifier)s );
#endif

    moduledict_%(module_identifier)s = (PyDictObject *)((PyModuleObject *)module_%(module_identifier)s)->md_dict;

    assertObject( module_%(module_identifier)s );

#ifndef _NUITKA_MODULE
// Seems to work for Python2.7 out of the box, but for Python3.2, the module
// doesn't automatically enter "sys.modules" with the object that it should, so
// do it manually.
#if PYTHON_VERSION >= 300
    {
        int r = PyObject_SetItem( PySys_GetObject( (char *)"modules" ), %(module_name_obj)s, module_%(module_identifier)s );

        assert( r != -1 );
    }
#endif
#endif

    // For deep importing of a module we need to have "__builtins__", so we set
    // it ourselves in the same way than CPython does. Note: This must be done
    // before the frame object is allocated, or else it may fail.

    PyObject *module_dict = PyModule_GetDict( module_%(module_identifier)s );

    if ( PyDict_GetItem( module_dict, const_str_plain___builtins__ ) == NULL )
    {
        PyObject *value = ( PyObject *)module_builtin;

#ifdef _NUITKA_EXE
        if ( module_%(module_identifier)s != module___main__ )
        {
#endif
            value = PyModule_GetDict( value );
#ifdef _NUITKA_EXE
        }
#endif

#ifndef __NUITKA_NO_ASSERT__
        int res =
#endif
            PyDict_SetItem( module_dict, const_str_plain___builtins__, value );

        assert( res == 0 );
    }

#if PYTHON_VERSION >= 330
#if _MODULE_UNFREEZER
    PyDict_SetItem( module_dict, const_str_plain___loader__, loader_frozen_modules );
#else
    PyDict_SetItem( module_dict, const_str_plain___loader__, Py_None );
#endif
#endif

    // Temp variables if any
%(temps_decl)s

    // Module code
%(module_code)s

   return MOD_RETURN_VALUE( module_%(module_identifier)s );
}
"""

template_helper_impl_decl = """\
// This file contains helper functions that are automatically created from
// templates.

#include "nuitka/prelude.hpp"

"""

template_header_guard = """\
#ifndef %(header_guard_name)s
#define %(header_guard_name)s

%(header_body)s
#endif
"""

template_frozen_modules = """\
// This provides the frozen (precompiled bytecode) files that are included if
// any.
#include <Python.h>

// Blob from which modules are unstreamed.
static const unsigned char stream_data[] =
{
%(stream_data)s
};

// These modules must be loadable during "Py_Initialize" already, these are
// not compiled by Nuitka, and not accelerated, merely bundled with the
// binary, so that Python library can start out.
struct _frozen PortableMode_FrozenModules[] =
{
%(frozen_modules)s
    { NULL, NULL, 0 }
};

"""
