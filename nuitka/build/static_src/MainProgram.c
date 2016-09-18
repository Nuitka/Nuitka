//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
//
/* The main program for a compiled program.
 *
 * It needs to prepare the interpreter and then loads and executes
 * the "__main__" module.
 *
 * This is currently still C++ code, but should become C code eventually. Maybe
 * this finished sooner than others.
 *
 */

#include "nuitka/prelude.hpp"

#include "structseq.h"
#include "osdefs.h"

#if _NUITKA_NO_WARNINGSSYSFLAGS
extern PyObject *const_str_plain_ignore;
#endif

extern PyCodeObject *codeobj_main;
extern PyObject *const_str_plain___main__;

#if _NUITKA_NO_PYTHON_WARNINGS
extern PyObject *const_str_plain_ignore;
#endif

/* For later use in "Py_GetArgcArgv" */
static char **orig_argv;
static int orig_argc;
#if PYTHON_VERSION >= 300
static wchar_t **argv_unicode;
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

    orig_argv = argv;
    orig_argc = argc;

#ifdef __FreeBSD__
    /* 754 requires that FP exceptions run in "no stop" mode by default, and
     *
     *    until C vendors implement C99's ways to control FP exceptions, Python
     *    requires non-stop mode.  Alas, some platforms enable FP exceptions by
     *    default.  Here we disable them.
     */

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

    /* For Python installations that need the PYTHONHOME set, we inject it back here. */
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

    /* Initialize CPython library environment. */
    Py_DebugFlag = 0;
#if PYTHON_VERSION < 300
    Py_Py3kWarningFlag = _NUITKA_SYSFLAG_PY3K_WARNING;
    Py_DivisionWarningFlag = _NUITKA_SYSFLAG_DIVISION_WARNING;
    Py_UnicodeFlag = _NUITKA_SYSFLAG_UNICODE;
    Py_TabcheckFlag = 0;
#endif
    Py_InspectFlag = 0;
    Py_InteractiveFlag = 0;
    Py_OptimizeFlag = 0;
    Py_DontWriteBytecodeFlag = 0;
    Py_NoUserSiteDirectory = _NUITKA_SYSFLAG_NO_SITE;
    Py_IgnoreEnvironmentFlag = 0;
    Py_VerboseFlag = _NUITKA_SYSFLAG_VERBOSE;
    Py_BytesWarningFlag = _NUITKA_SYSFLAG_BYTES_WARNING;
#if _NUITKA_SYSFLAG_BYTES_WARNING
    Py_HashRandomizationFlag = 1;
#endif

    /* We want to import the site module, but only after we finished our own
     * setup. The site module import will be the first thing, the main module
     * does.
     */
    Py_NoSiteFlag = 1;

    /* Initial command line handling only. */

#ifdef _NUITKA_TRACE
    puts("main(): Calling convert/setCommandLineParameters.");
#endif

#if PYTHON_VERSION >= 300
    argv_unicode = convertCommandLineParameters( argc, argv );
#endif

#if PYTHON_VERSION < 300
    bool is_multiprocess_forking = setCommandLineParameters( argc, argv, true );
#else
    bool is_multiprocess_forking = setCommandLineParameters( argc, argv_unicode, true );
#endif

    /* Initialize the embedded CPython interpreter. */
#ifdef _NUITKA_TRACE
    puts("main(): Calling Py_Initialize.");
#endif
    Py_Initialize();
#ifdef _NUITKA_TRACE
    puts("main(): Returned from Py_Initialize.");
#endif

    /* Lie about it, believe it or not, there are "site" files, that check
     * against later imports, see below.
     */
    Py_NoSiteFlag = _NUITKA_SYSFLAG_NO_SITE;

    /* Set the command line parameters for run time usage. */
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

    /* Initialize the built-in module tricks used. */
#ifdef _NUITKA_TRACE
    puts("main(): Calling _initBuiltinModule().");
#endif
    _initBuiltinModule();
#ifdef _NUITKA_TRACE
    puts("main(): Returned from _initBuiltinModule.");
#endif

    /* Initialize the Python constant values used. This also sets
     * "sys.executable" while at it.*/
#ifdef _NUITKA_TRACE
    puts("main(): Calling createGlobalConstants().");
#endif
    createGlobalConstants();
#ifdef _NUITKA_TRACE
    puts("main(): Calling _initBuiltinOriginalValues().");
#endif
    _initBuiltinOriginalValues();

    /* Revert the wrong "sys.flags" value, it's used by "site" on at least
     * Debian for Python 3.3, more uses may exist. */
#if _NUITKA_SYSFLAG_NO_SITE == 0
#if PYTHON_VERSION >= 330
    PyStructSequence_SetItem( PySys_GetObject( "flags" ), 6, const_int_0 );
#elif PYTHON_VERSION >= 320
    PyStructSequence_SetItem( PySys_GetObject( "flags" ), 7, const_int_0 );
#elif PYTHON_VERSION >= 260
    PyStructSequence_SET_ITEM( PySys_GetObject( (char *)"flags" ), 9, const_int_0 );
#endif
#endif

    /* Initialize the compiled types of Nuitka. */
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

#ifdef _NUITKA_TRACE
    puts("main(): Calling patchBuiltinModule().");
#endif
    patchBuiltinModule();
#ifdef _NUITKA_TRACE
    puts("main(): Calling patchTypeComparison().");
#endif
    patchTypeComparison();

    /* Allow to override the ticker value, to remove checks for threads in
     * CPython core from impact on benchmarks. */
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

    _PyWarnings_Init();

    /* Disable CPython warnings if requested to. */
#if _NUITKA_NO_PYTHON_WARNINGS
    /* Should be same as:
     *
     *   warnings.simplefilter("ignore", UserWarning)
     *   warnings.simplefilter("ignore", DeprecationWarning)
     * There is no C-API to control warnings. We don't care if it actually
     * works, i.e. return code of "simplefilter" function is not checked.
     */
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

    /* Execute the main module. In case of multiprocessing making a fork on
     * Windows, we should execute something else instead. */
#if _NUITKA_MODULE_COUNT > 1
    if (unlikely( is_multiprocess_forking ))
    {
#ifdef _NUITKA_TRACE
        puts("main(): Calling __parents_main__.");
#endif
        IMPORT_EMBEDDED_MODULE(PyUnicode_FromString("__parents_main__"), "__parents_main__");
    }
    else
#endif
    {
        assert( !is_multiprocess_forking );

#ifdef _NUITKA_TRACE
        puts("main(): Calling __main__.");
#endif
        /* Execute the "__main__" module. */
        PyDict_DelItemString(PySys_GetObject((char *)"modules"), "__main__");
        IMPORT_EMBEDDED_MODULE(const_str_plain___main__, "__main__");
    }

#if _NUITKA_PROFILE
    stopProfiling();
#endif

#ifndef __NUITKA_NO_ASSERT__
    checkGlobalConstants();

    /* TODO: Walk over all loaded compiled modules, and make this kind of checks. */
#if 0
    checkModuleConstants___main__();
#endif

#endif

    if ( ERROR_OCCURRED() )
    {
#if PYTHON_VERSION >= 330
        /* Remove the frozen importlib traceback part, which would not be compatible. */
        PyThreadState *thread_state = PyThreadState_GET();

        while( thread_state->curexc_traceback )
        {
            PyTracebackObject *tb = (PyTracebackObject *)thread_state->curexc_traceback;
            PyFrameObject *frame = tb->tb_frame;

            if ( 0 == strcmp( PyUnicode_AsUTF8( frame->f_code->co_filename ), "<frozen importlib._bootstrap>" ) )
            {
                thread_state->curexc_traceback = (PyObject *)tb->tb_next;
                Py_INCREF( tb->tb_next );

                continue;
            }

            break;
        }
#endif

        PyErr_PrintEx( 0 );
        Py_Exit( 1 );
    }
    else
    {
        Py_Exit( 0 );
    }

    /* The above branches both do "Py_Exit()" calls which are not supposed to
     * return.
     */
    NUITKA_CANNOT_GET_HERE( main );
}

/* This is an inofficial API, not available on Windows, but on Linux and others
 * it is exported, and has been used by some code.
 */
#ifndef _WIN32
#ifdef __cplusplus
extern "C" {
#endif

#if PYTHON_VERSION >= 300
#if defined( __GNUC__ )
__attribute__(( visibility( "default" )))
#endif
void Py_GetArgcArgv( int *argc, wchar_t ***argv )
{
    *argc = orig_argc;
    *argv = argv_unicode;
}

#else
#if defined( __GNUC__ )
__attribute__(( visibility( "default" )))
#endif
void Py_GetArgcArgv( int *argc, char ***argv )
{
    *argc = orig_argc;
    *argv = orig_argv;
}
#endif

#ifdef __cplusplus
}
#endif

#endif
