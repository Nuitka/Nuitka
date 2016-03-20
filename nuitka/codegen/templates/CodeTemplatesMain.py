#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Templates for main program.

"""


template_main_program = """\
// The main program for C++. It needs to prepare the interpreter and then
// calls the initialization code of the "__main__" module.

#include "structseq.h"
#include "osdefs.h"

#if %(python_no_warnings)d
extern PyObject *const_str_plain_ignore;
#endif

#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall WinMain( HINSTANCE hInstance, HINSTANCE hPrevInstance, char* lpCmdLine, int nCmdShow )
{
#if defined(__MINGW32__) && !defined(_W64)
    /* MINGW32 */
    int argc = _argc;
    char** argv = _argv;
#else
    /* MSVC, MINGW64 */
    int argc = __argc;
    char** argv = __argv;
#endif
#else
int main( int argc, char **argv )
{
#endif
#ifdef _NUITKA_TRACE
    puts("main(): Entered.");
#endif

#ifdef __FreeBSD__
    // 754 requires that FP exceptions run in "no stop" mode by default, and
    // until C vendors implement C99's ways to control FP exceptions, Python
    // requires non-stop mode.  Alas, some platforms enable FP exceptions by
    // default.  Here we disable them.

    fp_except_t m;

    m = fpgetmask();
    fpsetmask( m & ~FP_X_OFL );
#endif

#ifdef _NUITKA_STANDALONE
#ifdef _NUITKA_TRACE
    puts("main(): Prepare standalone environment.");
#endif
    prepareStandaloneEnvironment();
#else
    /* For Python installations that need the PYTHONHOME set. */
#if defined(PYTHON_HOME_PATH)
    puts("main(): Prepare run environment.");
    {
        char buffer[MAXPATHLEN+10];

        strcpy(buffer, "PYTHONHOME=");
        strcat(buffer, PYTHON_HOME_PATH);

        int res = putenv(buffer);
        assert( res == 0 );
    }
#endif
#endif

    // Initialize CPython library environment.
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

    // Initial command line handling only.

#ifdef _NUITKA_TRACE
    puts("main(): Calling convert/setCommandLineParameters.");
#endif

#if PYTHON_VERSION >= 300
    wchar_t **argv_unicode = convertCommandLineParameters( argc, argv );
#endif

#if PYTHON_VERSION < 300
    bool is_multiprocess_forking = setCommandLineParameters( argc, argv, true );
#else
    bool is_multiprocess_forking = setCommandLineParameters( argc, argv_unicode, true );
#endif

    // Initialize the embedded CPython interpreter.
#ifdef _NUITKA_TRACE
    puts("main(): Calling Py_Initialize.");
#endif
    Py_Initialize();
#ifdef _NUITKA_TRACE
    puts("main(): Returned from Py_Initialize.");
#endif

    // Lie about it, believe it or not, there are "site" files, that check
    // against later imports, see below.
    Py_NoSiteFlag = %(python_sysflag_no_site)s;

    // Set the command line parameters for run time usage.
#ifdef _NUITKA_TRACE
    puts("main(): Calling setCommandLineParameters.");
#endif

#if PYTHON_VERSION < 300
    setCommandLineParameters( argc, argv, false );
#else
    setCommandLineParameters( argc, argv_unicode, false );
#endif

#ifdef _NUITKA_STANDALONE
#ifdef _NUITKA_TRACE
    puts("main(): Restore standalone environment.");
#endif
    restoreStandaloneEnvironment();
#endif

    // Initialize the built-in module tricks used.
#ifdef _NUITKA_TRACE
    puts("main(): Calling _initBuiltinModule().");
#endif
    _initBuiltinModule();
#ifdef _NUITKA_TRACE
    puts("main(): Returned from _initBuiltinModule.");
#endif

    // Initialize the constant values used.
#ifdef _NUITKA_TRACE
    puts("main(): Calling createGlobalConstants().");
#endif
    createGlobalConstants();
#ifdef _NUITKA_TRACE
    puts("main(): Calling _initBuiltinOriginalValues().");
#endif
    _initBuiltinOriginalValues();

    // Revert the wrong "sys.flags" value, it's used by "site" on at least
    // Debian for Python 3.3, more uses may exist.
#if %(python_sysflag_no_site)s == 0
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
#if PYTHON_VERSION >= 350
    PyType_Ready( &Nuitka_Coroutine_Type );
    PyType_Ready( &Nuitka_CoroutineWrapper_Type );
#endif


#if PYTHON_VERSION < 300
    _initSlotCompare();
#endif
#if PYTHON_VERSION >= 270
    _initSlotIternext();
#endif

#ifdef _NUITKA_TRACE
    puts("main(): Calling enhancePythonTypes().");
#endif
    enhancePythonTypes();

    // Set the sys.executable path to the original Python executable on Linux
    // or to python.exe on Windows.
    PySys_SetObject(
        (char *)"executable",
        %(sys_executable)s
    );

#ifdef _NUITKA_TRACE
    puts("main(): Calling patchBuiltinModule().");
#endif
    patchBuiltinModule();
#ifdef _NUITKA_TRACE
    puts("main(): Calling patchTypeComparison().");
#endif
    patchTypeComparison();

    // Allow to override the ticker value, to remove checks for threads in
    // CPython core from impact on benchmarks.
    char const *ticker_value = getenv( "NUITKA_TICKER" );
    if ( ticker_value != NULL )
    {
        _Py_Ticker = atoi( ticker_value );
        assert ( _Py_Ticker >= 20 );
    }

#ifdef _NUITKA_STANDALONE
#ifdef _NUITKA_TRACE
    puts("main(): Calling setEarlyFrozenModulesFileAttribute().");
#endif
#if PYTHON_VERSION >= 300
    PyObject *os_module = PyImport_ImportModule("os");
    CHECK_OBJECT( os_module );
#endif
    setEarlyFrozenModulesFileAttribute();
#endif

#ifdef _NUITKA_TRACE
    puts("main(): Calling setupMetaPathBasedLoader().");
#endif
    /* Enable meta path based loader. */
    setupMetaPathBasedLoader();


    // Disable Python warnings if requested to.
#if %(python_no_warnings)d
    // Should be same as:
    //   warnings.simplefilter("ignore", UserWarning)
    //   warnings.simplefilter("ignore", DeprecationWarning)
    // There is no C-API to control warnings. We don't care if it actually
    // works, i.e. return code of "simplefilter" function is not checked.
    {
        PyObject *warnings = PyImport_ImportModule( "warnings" );
        if ( warnings != NULL )
        {
            PyObject *simplefilter = PyObject_GetAttrString( warnings, "simplefilter" );

            if ( simplefilter != NULL )
            {
                PyObject *result1 = PyObject_CallFunctionObjArgs( simplefilter, const_str_plain_ignore, PyExc_UserWarning, NULL );
                assert( result1 );
                Py_XDECREF( result1 );
                PyObject *result2 = PyObject_CallFunctionObjArgs( simplefilter, const_str_plain_ignore, PyExc_DeprecationWarning, NULL );
                assert( result2 );
                Py_XDECREF( result2 );
            }
        }
    }
#endif

#if PYTHON_VERSION >= 300
#ifdef _NUITKA_TRACE
    puts("main(): Calling patchInspectModule().");
#endif
    patchInspectModule();
#endif

#if _NUITKA_PROFILE
    startProfiling();
#endif

    // Execute the main module. In case of multiprocessing making a fork on
    // Windows, we should execute something else instead.
#if _NUITKA_MODULE_COUNT > 1
    if (unlikely( is_multiprocess_forking ))
    {
#ifdef _NUITKA_TRACE
        puts("main(): Calling __parents_main__.");
#endif
        PyObject *result = IMPORT_COMPILED_MODULE(
            PyUnicode_FromString("__parents_main__"),
            "__parents_main__"
        );

        if ( result == NULL )
        {
            PyErr_PrintEx( 0 );
            Py_Exit( 1 );
        }
    }
    else
#endif
    {
        assert( !is_multiprocess_forking );

#ifdef _NUITKA_TRACE
        puts("main(): Calling __main__.");
#endif
        // Execute the "__main__" module init function.
        MOD_INIT_NAME( __main__ )();
    }

#if _NUITKA_PROFILE
    stopProfiling();
#endif

#ifndef __NUITKA_NO_ASSERT__
    checkGlobalConstants();
    checkModuleConstants___main__();
#endif

    if ( ERROR_OCCURRED() )
    {
        // Cleanup code may need a frame, so put one back.
        PyThreadState_GET()->frame = MAKE_MODULE_FRAME( %(code_identifier)s, module___main__ );

        PyErr_PrintEx( 0 );
        Py_Exit( 1 );
    }
    else
    {
        Py_Exit( 0 );
    }

    // The above branches both do "Py_Exit()" calls which are not supposed to
    // return.
    NUITKA_CANNOT_GET_HERE( main );
}
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
