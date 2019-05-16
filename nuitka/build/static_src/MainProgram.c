//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
 * *
 */

#include "nuitka/prelude.h"

#include "osdefs.h"
#include "structseq.h"

#if defined(_WIN32)
#include <windows.h>
#endif

extern PyCodeObject *codeobj_main;
extern PyObject *const_str_plain___main__;

/* For later use in "Py_GetArgcArgv" */
static char **orig_argv;
static int orig_argc;
#if PYTHON_VERSION >= 300
static wchar_t **argv_unicode;
#endif

#ifdef _NUITKA_STANDALONE

#if _NUITKA_FROZEN > 0
extern void copyFrozenModulesTo(struct _frozen *destination);
#endif

static void prepareStandaloneEnvironment() {
    // Tell the CPython library to use our pre-compiled modules as frozen
    // modules. This for those modules/packages like "encoding" that will be
    // loaded during "Py_Initialize" already, for the others they may be
    // compiled.

#if _NUITKA_FROZEN > 0
    // The CPython library has some pre-existing frozen modules, we only append
    // to that.
    struct _frozen const *search = PyImport_FrozenModules;
    while (search->name) {
        search++;
    }
    int pre_existing_count = (int)(search - PyImport_FrozenModules);

    /* Allocate new memory and merge the tables. Keeping the old ones has
     * the advantage that e.g. "import this" is going to work well.
     */
    struct _frozen *merged =
        (struct _frozen *)malloc(sizeof(struct _frozen) * (_NUITKA_FROZEN + pre_existing_count + 1));

    memcpy(merged, PyImport_FrozenModules, pre_existing_count * sizeof(struct _frozen));
    copyFrozenModulesTo(merged + pre_existing_count);
    PyImport_FrozenModules = merged;
#endif

    /* Setup environment variables to tell CPython that we would like it to use
     * the provided binary directory as the place to look for DLLs and for
     * extension modules.
     */
#if defined(_WIN32) && defined(_MSC_VER)
    SetDllDirectoryW(getBinaryDirectoryWideChars());
#endif

#if PYTHON_VERSION < 300
    char *binary_directory = getBinaryDirectoryHostEncoded();
    NUITKA_PRINTF_TRACE("Binary dir is %s\n", binary_directory);

    Py_SetPythonHome(binary_directory);
#else
    wchar_t *binary_directory = getBinaryDirectoryWideChars();
    NUITKA_PRINTF_TRACE("Binary dir is %S\n", binary_directory);

    Py_SetPythonHome(binary_directory);

#endif
}

#if PYTHON_VERSION < 300
#define PY_FORMAT_GETPATH_RESULT "%s"
#else
#define PY_FORMAT_GETPATH_RESULT "%ls"
#endif

static void restoreStandaloneEnvironment() {
    /* Make sure to use the optimal value for standalone mode only. */
#if PYTHON_VERSION < 300
    PySys_SetPath(getBinaryDirectoryHostEncoded());
    NUITKA_PRINTF_TRACE("Final PySys_GetPath is 's'.\n", PySys_GetPath());
#else
    PySys_SetPath(getBinaryDirectoryWideChars());
    Py_SetPath(getBinaryDirectoryWideChars());
    NUITKA_PRINTF_TRACE("Final Py_GetPath is '%ls'.\n", Py_GetPath());
#endif
}

#endif

extern void _initCompiledCellType();
extern void _initCompiledGeneratorType();
extern void _initCompiledFunctionType();
extern void _initCompiledMethodType();
extern void _initCompiledFrameType();
#if PYTHON_VERSION >= 350
extern void _initCompiledCoroutineTypes();
#endif
#if PYTHON_VERSION >= 360
extern void _initCompiledAsyncgenTypes();
#endif

#include <locale.h>

// Types of command line arguments are different between Python2/3.
#if PYTHON_VERSION >= 300
typedef wchar_t **argv_type_t;
static argv_type_t convertCommandLineParameters(int argc, char **argv) {
#if _WIN32
    int new_argc;

    argv_type_t result = CommandLineToArgvW(GetCommandLineW(), &new_argc);
    assert(new_argc == argc);
    return result;
#else
    // Originally taken from CPython3: There seems to be no sane way to use
    static wchar_t **argv_copy;
    argv_copy = (wchar_t **)PyMem_Malloc(sizeof(wchar_t *) * argc);

    // Temporarily disable locale for conversions to not use it.
    char *oldloc = strdup(setlocale(LC_ALL, NULL));
    setlocale(LC_ALL, "");

    for (int i = 0; i < argc; i++) {
#ifdef __APPLE__
        argv_copy[i] = _Py_DecodeUTF8_surrogateescape(argv[i], strlen(argv[i]));
#elif PYTHON_VERSION < 350
        argv_copy[i] = _Py_char2wchar(argv[i], NULL);
#else
        argv_copy[i] = Py_DecodeLocale(argv[i], NULL);
#endif

        assert(argv_copy[i]);
    }

    setlocale(LC_ALL, oldloc);
    free(oldloc);

    return argv_copy;
#endif
}
#else
typedef char **argv_type_t;
#endif

// Parse the command line parameters and provide it to "sys" built-in module,
// as well as decide if it's a multiprocessing usage.

static bool setCommandLineParameters(int argc, argv_type_t argv, bool initial) {
    bool is_multiprocessing_fork = false;

    if (initial) {
        /* We might need to skip what multiprocessing has told us. */
        for (int i = 1; i < argc; i++) {
#if PYTHON_VERSION < 300
            if ((strcmp(argv[i], "--multiprocessing-fork")) == 0 && (i + 1 < argc))
#else
            wchar_t constant_buffer[100];
            mbstowcs(constant_buffer, "--multiprocessing-fork", 100);
            if ((wcscmp(argv[i], constant_buffer)) == 0 && (i + 1 < argc))
#endif
            {
                is_multiprocessing_fork = true;
                break;
            }
        }
    }

    if (initial) {
        // Py_SetProgramName(argv[0]);
    } else {
        PySys_SetArgv(argc, argv);
    }

    return is_multiprocessing_fork;
}

#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, char *lpCmdLine, int nCmdShow) {
#if defined(__MINGW32__) && !defined(_W64)
    /* MINGW32 */
    int argc = _argc;
    char **argv = _argv;
#else
    /* MSVC, MINGW64 */
    int argc = __argc;
    char **argv = __argv;
#endif
#else
int main(int argc, char **argv) {
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
    fpsetmask(m & ~FP_X_OFL);
#endif

    /* On Windows we support loading the constants blob from an embedded
     * resource. On Linux, where possible this is done automatically by
     * the linker already.
     */
#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
    NUITKA_PRINT_TRACE("main(): Loading constants blob from Windows resource.");

    loadConstantsResource();
#endif

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Prepare standalone environment.");
    prepareStandaloneEnvironment();
#else

#if PYTHON_VERSION >= 350 && defined(DLL_EXTRA_PATH)
    NUITKA_PRINT_TRACE("main(): Prepare DLL extra path.");
    SetDllDirectory(DLL_EXTRA_PATH);
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
    Py_OptimizeFlag = _NUITKA_SYSFLAG_OPTIMIZE;
    Py_DontWriteBytecodeFlag = 0;
    Py_NoUserSiteDirectory = _NUITKA_SYSFLAG_NO_SITE;
    Py_IgnoreEnvironmentFlag = 0;
    Py_VerboseFlag = _NUITKA_SYSFLAG_VERBOSE;
    Py_BytesWarningFlag = _NUITKA_SYSFLAG_BYTES_WARNING;
#if _NUITKA_SYSFLAG_BYTES_WARNING
    Py_HashRandomizationFlag = 1;
#endif
#if PYTHON_VERSION >= 370
    Py_UTF8Mode = _NUITKA_SYSFLAG_UTF8;
#endif

    /* This suppresses warnings from getpath.c */
    Py_FrozenFlag = 1;

    /* We want to import the site module, but only after we finished our own
     * setup. The site module import will be the first thing, the main module
     * does.
     */
    Py_NoSiteFlag = 1;

    /* Initial command line handling only. */

#if PYTHON_VERSION >= 300
    NUITKA_PRINT_TRACE("main(): Calling convertCommandLineParameters.");
    argv_unicode = convertCommandLineParameters(argc, argv);
#endif

    NUITKA_PRINT_TRACE("main(): Calling setCommandLineParameters.");

#if PYTHON_VERSION < 300
    bool is_multiprocess_forking = setCommandLineParameters(argc, argv, true);
#else
    bool is_multiprocess_forking = setCommandLineParameters(argc, argv_unicode, true);
#endif

    /* For Python installations that need the home set, we inject it back here. */
#if defined(PYTHON_HOME_PATH)
#if PYTHON_VERSION < 300
    NUITKA_PRINT_TRACE("main(): Prepare run environment '" PYTHON_HOME_PATH "'.");
    Py_SetPythonHome(PYTHON_HOME_PATH);
#else
    NUITKA_PRINTF_TRACE("main(): Prepare run environment '%S'.\n", L"" PYTHON_HOME_PATH);
    Py_SetPythonHome(L"" PYTHON_HOME_PATH);
    // Make sure the above Py_SetPythonHome call has effect already.
    Py_GetPath();
#endif
#endif

    /* Initialize the embedded CPython interpreter. */
    NUITKA_PRINT_TRACE("main(): Calling Py_Initialize to initialize interpreter.");
    Py_Initialize();

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Restore standalone environment.");
    restoreStandaloneEnvironment();
#endif

    /* Lie about it, believe it or not, there are "site" files, that check
     * against later imports, see below.
     */
    Py_NoSiteFlag = _NUITKA_SYSFLAG_NO_SITE;

    /* Set the command line parameters for run time usage. */
    NUITKA_PRINT_TRACE("main(): Calling setCommandLineParameters.");

#if PYTHON_VERSION < 300
    setCommandLineParameters(argc, argv, false);
#else
    setCommandLineParameters(argc, argv_unicode, false);
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
#if PYTHON_VERSION < 300
    PyStructSequence_SET_ITEM(PySys_GetObject((char *)"flags"), 9, const_int_0);
#else
    PyStructSequence_SetItem(PySys_GetObject("flags"), 6, const_int_0);
#endif
#endif

    /* Initialize the compiled types of Nuitka. */
    _initCompiledCellType();
    _initCompiledGeneratorType();
    _initCompiledFunctionType();
    _initCompiledMethodType();
    _initCompiledFrameType();
#if PYTHON_VERSION >= 350
    _initCompiledCoroutineTypes();
#endif
#if PYTHON_VERSION >= 360
    _initCompiledAsyncgenTypes();
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

    NUITKA_PRINT_TRACE("main(): Calling patchTracebackDealloc().");
    patchTracebackDealloc();

    /* Allow to override the ticker value, to remove checks for threads in
     * CPython core from impact on benchmarks. */
    char const *ticker_value = getenv("NUITKA_TICKER");
    if (ticker_value != NULL) {
        _Py_Ticker = atoi(ticker_value);
        assert(_Py_Ticker >= 20);
    }

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Calling setEarlyFrozenModulesFileAttribute().");

#if PYTHON_VERSION >= 300
    PyObject *os_module = PyImport_ImportModule("os");
    CHECK_OBJECT(os_module);
#endif
    setEarlyFrozenModulesFileAttribute();
#endif

    NUITKA_PRINT_TRACE("main(): Calling setupMetaPathBasedLoader().");
    /* Enable meta path based loader. */
    setupMetaPathBasedLoader();

    _PyWarnings_Init();

    /* Disable CPython warnings if requested to. */
#if _NUITKA_NO_PYTHON_WARNINGS
    {
#if PYTHON_VERSION >= 300
        wchar_t ignore[] = L"ignore";
#else
        char ignore[] = "ignore";
#endif

        PySys_AddWarnOption(ignore);

#if PYTHON_VERSION >= 342 && defined(_NUITKA_FULL_COMPAT)
        // For full compatibility bump the warnings registry version,
        // otherwise modules "__warningsregistry__" will mismatch.
        PyObject *warnings_module = PyImport_ImportModule("warnings");
        PyObject *meth = PyObject_GetAttrString(warnings_module, "_filters_mutated");

        CALL_FUNCTION_NO_ARGS(meth);
#endif
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
    if (unlikely(is_multiprocess_forking)) {
        NUITKA_PRINT_TRACE("main(): Calling __parents_main__.");
        IMPORT_EMBEDDED_MODULE(PyUnicode_FromString("__parents_main__"), "__parents_main__");
    } else
#endif
    {
        assert(!is_multiprocess_forking);

        NUITKA_PRINT_TRACE("main(): Calling __main__.");

        /* Execute the "__main__" module. */
        PyDict_DelItem(PyImport_GetModuleDict(), const_str_plain___main__);
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

    if (ERROR_OCCURRED()) {
#if PYTHON_VERSION >= 300
        /* Remove the frozen importlib traceback part, which would not be compatible. */
        PyThreadState *thread_state = PyThreadState_GET();

        while (thread_state->curexc_traceback) {
            PyTracebackObject *tb = (PyTracebackObject *)thread_state->curexc_traceback;
            PyFrameObject *frame = tb->tb_frame;

            if (0 == strcmp(PyUnicode_AsUTF8(frame->f_code->co_filename), "<frozen importlib._bootstrap>")) {
                thread_state->curexc_traceback = (PyObject *)tb->tb_next;
                Py_INCREF(tb->tb_next);

                continue;
            }

            break;
        }
#endif

        PyErr_PrintEx(0);
        Py_Exit(1);
    } else {
        Py_Exit(0);
    }

    /* The above branches both do "Py_Exit()" calls which are not supposed to
     * return.
     */
    NUITKA_CANNOT_GET_HERE(main);
}

/* This is an unofficial API, not available on Windows, but on Linux and others
 * it is exported, and has been used by some code.
 */
#ifndef _WIN32
#ifdef __cplusplus
extern "C" {
#endif

#if PYTHON_VERSION >= 300
#if defined(__GNUC__)
__attribute__(( visibility( "default" )))
#endif
void Py_GetArgcArgv( int *argc, wchar_t ***argv )
{
    *argc = orig_argc;
    *argv = argv_unicode;
}

#else
#if defined(__GNUC__)
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
