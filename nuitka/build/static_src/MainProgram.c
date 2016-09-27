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

#include "nuitka/prelude.h"

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

#ifdef _NUITKA_STANDALONE

static char *original_home;
static char *original_path;


#if _NUITKA_FROZEN > 0
extern void copyFrozenModulesTo( struct _frozen *destination );
#endif

static void prepareStandaloneEnvironment()
{
    // Tell the CPython library to use our pre-compiled modules as frozen
    // modules. This for those modules/packages like "encoding" that will be
    // loaded during "Py_Initialize" already, for the others they may be
    // compiled.

#if _NUITKA_FROZEN > 0
    // The CPython library has some pre-existing frozen modules, we only append
    // to that.
    struct _frozen const *search = PyImport_FrozenModules;
    while( search->name )
    {
        search++;
    }
    int pre_existing_count = (int)( search - PyImport_FrozenModules );

    /* Allocate new memory and merge the tables. Keeping the old ones has
     * the advantage that e.g. "import this" is going to work well.
     */
    struct _frozen *merged = (struct _frozen *)malloc(
        sizeof(struct _frozen) * (_NUITKA_FROZEN + pre_existing_count + 1)
    );

    memcpy(
        merged,
        PyImport_FrozenModules,
        pre_existing_count * sizeof( struct _frozen )
    );
    copyFrozenModulesTo(merged + pre_existing_count);
    PyImport_FrozenModules = merged;
#endif

    /* Setup environment variables to tell CPython that we would like it to use
     * the provided binary directory as the place to look for DLLs.
     */
    char *binary_directory = getBinaryDirectoryHostEncoded();

#if defined( _WIN32 ) && defined( _MSC_VER )
    SetDllDirectory( binary_directory );
#endif

    /* get original environment variable values */
    original_home = getenv( "PYTHONHOME" );
    original_path = getenv( "PYTHONPATH" );
    size_t original_home_size = ( original_home ) ? strlen( original_home ) : 0;
    size_t original_path_size = ( original_path ) ? strlen( original_path ) : 0;

    /* Get the value to insert into it. */
    size_t insert_size = strlen( binary_directory ) * 2 + 50;
    char *insert_path = (char *) malloc( insert_size );

#if defined( _WIN32 )
    char const env_string[] = "%s;";
#else
    char const env_string[] = "%s:";
#endif

    memset( insert_path, 0, insert_size );
    snprintf( insert_path, insert_size, env_string, binary_directory );

    // set environment
    size_t python_home_size = original_home_size + insert_size;
    size_t python_path_size = original_path_size + insert_size;
    char *python_home = (char *) malloc( python_home_size );
    char *python_path = (char *) malloc( python_path_size );
    memset( python_home, 0, python_home_size );
    memset( python_path, 0, python_path_size );
    snprintf( python_home, python_home_size, "%s%s",
        insert_path, original_home ? original_home : "" );
    snprintf( python_path, python_path_size, "%s%s",
        insert_path, original_path ? original_path : "" );

    if ( !( original_home && strstr( original_home, insert_path ) ) )
    {
#if defined( _WIN32 )
        SetEnvironmentVariable( "PYTHONHOME", python_home );
#else
        setenv( "PYTHONHOME", python_home, 1 );
#endif
    }
    if ( !( original_path && strstr( original_path, insert_path ) ) )
    {
#if defined( _WIN32 )
        SetEnvironmentVariable( "PYTHONPATH", python_path );
#else
        setenv( "PYTHONPATH", python_path, 1 );
#endif
    }

    // clean up
    free( insert_path );
}

static void restoreStandaloneEnvironment()
{
#if defined( _WIN32 )
    SetEnvironmentVariable( "PYTHONHOME", original_home );
#else
    if ( original_home == NULL )
    {
        unsetenv( "PYTHONHOME" );
    }
    else
    {
        setenv( "PYTHONHOME", original_home, 1 );
    }
#endif

#if defined( _WIN32 )
    SetEnvironmentVariable( "PYTHONHOME", original_path );
#else
    if ( original_path == NULL )
    {
        unsetenv( "PYTHONHOME" );
    }
    else
    {
        setenv( "PYTHONHOME", original_path, 1 );
    }
#endif
}

#endif

extern void _initCompiledGeneratorType();
extern void _initCompiledFunctionType();
extern void _initCompiledMethodType();
extern void _initCompiledFrameType();
#if PYTHON_VERSION >= 350
extern void _initCompiledCoroutineType();
extern void _initCompiledCoroutineWrapperType();
#endif

#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
unsigned char const* constant_bin = NULL;
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
    NUITKA_PRINT_TRACE("main(): Entered.");

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

    /* On Windows we support loading the constants blob from an embedded
     * resource. On Linux, where possible this is done automatically by
     * the linker already.
     */
#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
    NUITKA_PRINT_TRACE("main(): Loading constants blob from Windows resource.");

    constant_bin = (const unsigned char*)LockResource(
        LoadResource(
            NULL,
            FindResource(NULL, MAKEINTRESOURCE(3), RT_RCDATA)
        )
    );

    assert( constant_bin );
#endif


#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Prepare standalone environment.");
    prepareStandaloneEnvironment();
#else

    /* For Python installations that need the PYTHONHOME set, we inject it back here. */
#if defined(PYTHON_HOME_PATH)
    NUITKA_PRINT_TRACE("main(): Prepare run environment PYTHONHOME.");
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

    NUITKA_PRINT_TRACE("main(): Calling convert/setCommandLineParameters.");

#if PYTHON_VERSION >= 300
    argv_unicode = convertCommandLineParameters( argc, argv );
#endif

#if PYTHON_VERSION < 300
    bool is_multiprocess_forking = setCommandLineParameters( argc, argv, true );
#else
    bool is_multiprocess_forking = setCommandLineParameters( argc, argv_unicode, true );
#endif

    /* Initialize the embedded CPython interpreter. */
    NUITKA_PRINT_TRACE("main(): Calling Py_Initialize to initialize interpreter.");
    Py_Initialize();

    /* Lie about it, believe it or not, there are "site" files, that check
     * against later imports, see below.
     */
    Py_NoSiteFlag = _NUITKA_SYSFLAG_NO_SITE;

    /* Set the command line parameters for run time usage. */
    NUITKA_PRINT_TRACE("main(): Calling setCommandLineParameters.");

#if PYTHON_VERSION < 300
    setCommandLineParameters( argc, argv, false );
#else
    setCommandLineParameters( argc, argv_unicode, false );
#endif

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Restore standalone environment.");
    restoreStandaloneEnvironment();
#endif

    /* Initialize the built-in module tricks used. */
    NUITKA_PRINT_TRACE("main(): Calling _initBuiltinModule().");
    _initBuiltinModule();

    /* Initialize the Python constant values used. This also sets
     * "sys.executable" while at it.
     */
    NUITKA_PRINT_TRACE("main(): Calling createGlobalConstants().");
    createGlobalConstants();

    NUITKA_PRINT_TRACE("main(): Calling _initBuiltinOriginalValues().");
    _initBuiltinOriginalValues();

    /* Revert the wrong "sys.flags" value, it's used by "site" on at least
     * Debian for Python 3.3, more uses may exist.
     */
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
    _initCompiledGeneratorType();
    _initCompiledFunctionType();
    _initCompiledMethodType();
    _initCompiledFrameType();

#if PYTHON_VERSION >= 350
    _initCompiledCoroutineType();
    _initCompiledCoroutineWrapperType();
#endif

#if PYTHON_VERSION < 300
    _initSlotCompare();
#endif
#if PYTHON_VERSION >= 270
    _initSlotIternext();
#endif

    NUITKA_PRINT_TRACE("main(): Calling enhancePythonTypes().");
    enhancePythonTypes();

    NUITKA_PRINT_TRACE("main(): Calling patchBuiltinModule().");
    patchBuiltinModule();

    NUITKA_PRINT_TRACE("main(): Calling patchTypeComparison().");
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
    NUITKA_PRINT_TRACE("main(): Calling setEarlyFrozenModulesFileAttribute().");

#if PYTHON_VERSION >= 300
    PyObject *os_module = PyImport_ImportModule("os");
    CHECK_OBJECT( os_module );
#endif
    setEarlyFrozenModulesFileAttribute();
#endif

    NUITKA_PRINT_TRACE("main(): Calling setupMetaPathBasedLoader().");
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
    NUITKA_PRINT_TRACE("main(): Calling patchInspectModule().");
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
        NUITKA_PRINT_TRACE("main(): Calling __parents_main__.");
        IMPORT_EMBEDDED_MODULE(PyUnicode_FromString("__parents_main__"), "__parents_main__");
    }
    else
#endif
    {
        assert( !is_multiprocess_forking );

        NUITKA_PRINT_TRACE("main(): Calling __main__.");

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
