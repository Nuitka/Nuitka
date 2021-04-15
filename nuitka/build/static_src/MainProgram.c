//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
 */

#if defined(_WIN32)
#include <windows.h>
#endif

#include "nuitka/prelude.h"

#ifndef __IDE_ONLY__
// Generated during build with optional defines.
#include "build_definitions.h"
#else
// For the IDE to know these exist.
#define SYSFLAG_PY3K_WARNING 0
#define SYSFLAG_DIVISION_WARNING 0
#define SYSFLAG_UNICODE 0
#define SYSFLAG_OPTIMIZE 0
#define SYSFLAG_NO_SITE 0
#define SYSFLAG_VERBOSE 0
#define SYSFLAG_BYTES_WARNING 0
#define SYSFLAG_UTF8 0
#endif

#include <osdefs.h>
#include <structseq.h>

extern PyCodeObject *codeobj_main;

/* For later use in "Py_GetArgcArgv" */
static char **orig_argv;
static int orig_argc;
#if PYTHON_VERSION >= 0x300
static wchar_t **argv_unicode;
#endif

#ifdef _NUITKA_STANDALONE

#if _NUITKA_FROZEN > 0
extern void copyFrozenModulesTo(struct _frozen *destination);

// The original frozen modules list.
#if PYTHON_VERSION < 0x340
static struct _frozen *old_frozen = NULL;
#else
static struct _frozen const *old_frozen = NULL;
#endif
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
    old_frozen = PyImport_FrozenModules;
    PyImport_FrozenModules = merged;
#endif

    /* Setup environment variables to tell CPython that we would like it to use
     * the provided binary directory as the place to look for DLLs and for
     * extension modules.
     */
#if defined(_WIN32)
    SetDllDirectoryW(getBinaryDirectoryWideChars());
#endif

#if PYTHON_VERSION < 0x300
    char *binary_directory = (char *)getBinaryDirectoryHostEncoded();
    NUITKA_PRINTF_TRACE("main(): Binary dir is %s\n", binary_directory);

    Py_SetPythonHome(binary_directory);
#else
    wchar_t *binary_directory = (wchar_t *)getBinaryDirectoryWideChars();
    NUITKA_PRINTF_TRACE("main(): Binary dir is %S\n", binary_directory);

    Py_SetPythonHome(binary_directory);

#endif
}

static void restoreStandaloneEnvironment() {
    /* Make sure to use the optimal value for standalone mode only. */
#if PYTHON_VERSION < 0x300
    PySys_SetPath((char *)getBinaryDirectoryHostEncoded());
    // NUITKA_PRINTF_TRACE("Final PySys_GetPath is 's'.\n", PySys_GetPath());
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

#include <locale.h>

// Types of command line arguments are different between Python2/3.
#if PYTHON_VERSION >= 0x300
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
#if PYTHON_VERSION >= 0x350
        argv_copy[i] = Py_DecodeLocale(argv[i], NULL);
#elif defined(__APPLE__) && PYTHON_VERSION >= 0x320
        argv_copy[i] = _Py_DecodeUTF8_surrogateescape(argv[i], strlen(argv[i]));
#else
        argv_copy[i] = _Py_char2wchar(argv[i], NULL);
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

#ifdef _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
extern void SvcInstall();
extern void SvcLaunchService();

// Callback from Windows Service logic.
DWORD WINAPI SvcStartPython(LPVOID lpParam) {
    if (lpParam == NULL) {
        IMPORT_EMBEDDED_MODULE("__main__");

        // TODO: Log exception and call ReportSvcStatus
        if (ERROR_OCCURRED()) {
            return 1;
        } else {
            return 0;
        }
    } else {
        PyErr_SetInterrupt();
        return 0;
    }
}
#endif

// Parse the command line parameters and provide it to "sys" built-in module,
// as well as decide if it's a multiprocessing usage.
static bool is_multiprocessing_fork = false;

static void setCommandLineParameters(int argc, argv_type_t argv, bool initial) {
    if (initial) {
        /* We might need to handle special parameters from plugins that are
           very deeply woven into command line handling. These are right now
           multiprocessing, which indicates that it's forking via extra
           command line argument. And Windows Service indicates need to
           install and exit here too.
         */
        for (int i = 1; i < argc; i++) {
#if PYTHON_VERSION < 0x300
            if ((strcmp(argv[i], "--multiprocessing-fork")) == 0 && (i + 1 < argc))
#else
            // TODO: Should simply use wide char literal
            if ((wcscmp(argv[i], L"--multiprocessing-fork")) == 0 && (i + 1 < argc))
#endif
            {
                is_multiprocessing_fork = true;
                break;
            }

#ifdef _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
            if (i == 1) {
#if PYTHON_VERSION < 0x300
                if (strcmp(argv[i], "install") == 0)
#else
                if (wcscmp(argv[i], L"install") == 0)
#endif
                {
                    NUITKA_PRINT_TRACE("main(): Calling plugin SvcInstall().");

                    SvcInstall();
                    NUITKA_CANNOT_GET_HERE("SvcInstall must not return");
                }
            }
#endif
        }
    }

    if (initial) {
        // Py_SetProgramName(argv[0]);
    } else {
        PySys_SetArgv(argc, argv);
    }
}

#if defined(_WIN32) && PYTHON_VERSION >= 0x300 && SYSFLAG_NO_RANDOMIZATION == 1
static void setenv(char const *name, char const *value, int overwrite) {
    assert(overwrite);

    SetEnvironmentVariableA(name, value);
}

static void unsetenv(char const *name) { SetEnvironmentVariableA(name, NULL); }
#endif

#if _DEBUG_REFCOUNTS
static void PRINT_REFCOUNTS() {
    PRINT_STRING("REFERENCE counts at program end:\n");
    PRINT_STRING("active | allocated | released\n");
    PRINT_FORMAT("Compiled Coroutines: %d | %d | %d\n", count_active_Nuitka_Coroutine_Type,
                 count_allocated_Nuitka_Coroutine_Type, count_released_Nuitka_Coroutine_Type);
    PRINT_FORMAT("Compiled Coroutines Wrappers: %d | %d | %d\n", count_active_Nuitka_CoroutineWrapper_Type,
                 count_allocated_Nuitka_CoroutineWrapper_Type, count_released_Nuitka_CoroutineWrapper_Type);

    PRINT_FORMAT("Compiled Coroutines AIter Wrappers: %d | %d | %d\n", count_active_Nuitka_AIterWrapper_Type,
                 count_allocated_Nuitka_AIterWrapper_Type, count_released_Nuitka_AIterWrapper_Type);
#if PYTHON_VERSION >= 0x360
    PRINT_FORMAT("Compiled Asyncgen: %d | %d | %d\n", count_active_Nuitka_Asyncgen_Type,
                 count_allocated_Nuitka_Asyncgen_Type, count_released_Nuitka_Asyncgen_Type);
    PRINT_FORMAT("Compiled Asyncgen Wrappers: %d | %d | %d\n", count_active_Nuitka_AsyncgenValueWrapper_Type,
                 count_allocated_Nuitka_AsyncgenValueWrapper_Type, count_released_Nuitka_AsyncgenValueWrapper_Type);
    PRINT_FORMAT("Compiled Asyncgen Asend: %d | %d | %d\n", count_active_Nuitka_AsyncgenAsend_Type,
                 count_allocated_Nuitka_AsyncgenAsend_Type, count_released_Nuitka_AsyncgenAsend_Type);
    PRINT_FORMAT("Compiled Asyncgen Athrow: %d | %d | %d\n", count_active_Nuitka_AsyncgenAthrow_Type,
                 count_allocated_Nuitka_AsyncgenAthrow_Type, count_released_Nuitka_AsyncgenAthrow_Type);
#endif

    PRINT_FORMAT("Compiled Frames: %d | %d | %d (cache usage may occur)\n", count_active_Nuitka_Frame_Type,
                 count_allocated_Nuitka_Frame_Type, count_released_Nuitka_Frame_Type);
    PRINT_STRING("CACHED counts at program end:\n");
    PRINT_STRING("active | allocated | released | hits\n");
    PRINT_FORMAT("Cached Frames: %d | %d | %d | %d\n", count_active_frame_cache_instances,
                 count_allocated_frame_cache_instances, count_released_frame_cache_instances,
                 count_hit_frame_cache_instances);
}
#endif

// Small helper to open files with few arguments.
static PyObject *BUILTIN_OPEN_SIMPLE(PyObject *filename, char const *mode, PyObject *buffering) {
#if PYTHON_VERSION < 0x300
    return BUILTIN_OPEN(filename, Nuitka_String_FromString(mode), buffering);
#else
    return BUILTIN_OPEN(filename, Nuitka_String_FromString(mode), buffering, NULL, NULL, NULL, NULL, NULL);
#endif
}

#if defined(_NUITKA_ONEFILE) && defined(_WIN32)

static long onefile_ppid;

DWORD WINAPI doOnefileParentMonitoring(LPVOID lpParam) {
    for (;;) {
        Sleep(1000);

        HANDLE handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, onefile_ppid);

        if (handle == NULL) {
            if (GetLastError() == ERROR_INVALID_PARAMETER) {
                break;
            } else {
                continue;
            }
        } else {
            DWORD ret = WaitForSingleObject(handle, 0);

            CloseHandle(handle);

            if (ret == WAIT_OBJECT_0) {
                break;
            }
        }
    }

    // puts("Onefile parent monitoring kicks in.");

    PyErr_SetInterrupt();

    return 0;
}
#endif

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

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Prepare standalone environment.");
    prepareStandaloneEnvironment();
#else

#if PYTHON_VERSION >= 0x350 && defined(DLL_EXTRA_PATH)
    NUITKA_PRINT_TRACE("main(): Prepare DLL extra path.");
    SetDllDirectory(DLL_EXTRA_PATH);
#endif

#endif

    /* Initialize CPython library environment. */
    Py_DebugFlag = 0;
#if PYTHON_VERSION < 0x300
    Py_Py3kWarningFlag = SYSFLAG_PY3K_WARNING;
    Py_DivisionWarningFlag = SYSFLAG_DIVISION_WARNING;
    Py_UnicodeFlag = SYSFLAG_UNICODE;
    Py_TabcheckFlag = 0;
#endif
    Py_InspectFlag = 0;
    Py_InteractiveFlag = 0;
    Py_OptimizeFlag = SYSFLAG_OPTIMIZE;
    Py_DontWriteBytecodeFlag = 0;
    Py_NoUserSiteDirectory = SYSFLAG_NO_SITE;
    Py_IgnoreEnvironmentFlag = 0;
    Py_VerboseFlag = SYSFLAG_VERBOSE;
    Py_BytesWarningFlag = SYSFLAG_BYTES_WARNING;
#if SYSFLAG_NO_RANDOMIZATION == 1
    Py_HashRandomizationFlag = 0;
#if PYTHON_VERSION < 0x300
    // For Python2 this is all it takes to have static hashes.
    _PyRandom_Init();
#endif
#endif
#if PYTHON_VERSION >= 0x370
    Py_UTF8Mode = SYSFLAG_UTF8;
#endif

    /* This suppresses warnings from getpath.c */
    Py_FrozenFlag = 1;

    /* We want to import the site module, but only after we finished our own
     * setup. The site module import will be the first thing, the main module
     * does.
     */
    Py_NoSiteFlag = 1;

    /* Initial command line handling only. */

#if PYTHON_VERSION >= 0x300
    NUITKA_PRINT_TRACE("main(): Calling convertCommandLineParameters.");
    argv_unicode = convertCommandLineParameters(argc, argv);
#endif

    NUITKA_PRINT_TRACE("main(): Calling setCommandLineParameters.");

#if PYTHON_VERSION < 0x300
    setCommandLineParameters(argc, argv, true);
#else
    setCommandLineParameters(argc, argv_unicode, true);
#endif

    /* For Python installations that need the home set, we inject it back here. */
#if defined(PYTHON_HOME_PATH)
#if PYTHON_VERSION < 0x300
    NUITKA_PRINT_TRACE("main(): Prepare run environment '" PYTHON_HOME_PATH "'.");
    Py_SetPythonHome(PYTHON_HOME_PATH);
#else
    NUITKA_PRINTF_TRACE("main(): Prepare run environment '%S'.\n", L"" PYTHON_HOME_PATH);
    Py_SetPythonHome(L"" PYTHON_HOME_PATH);
    // Make sure the above Py_SetPythonHome call has effect already.
    Py_GetPath();
#endif
#endif

#if PYTHON_VERSION >= 0x300 && SYSFLAG_NO_RANDOMIZATION == 1
    char const *old_env = getenv("PYTHONHASHSEED");
    setenv("PYTHONHASHSEED", "0", 1);
#endif
    /* Initialize the embedded CPython interpreter. */
    NUITKA_PRINT_TRACE("main(): Calling Py_Initialize to initialize interpreter.");
    Py_Initialize();

#if PYTHON_VERSION >= 0x300 && SYSFLAG_NO_RANDOMIZATION == 1
    if (old_env) {
        setenv("PYTHONHASHSEED", old_env, 1);

        PyObject *env_value = PyUnicode_FromString(old_env);
        PyObject *hashseed_str = PyUnicode_FromString("PYTHONHASHSEED");

        int res =
            PyObject_SetItem(PyObject_GetAttrString(PyImport_ImportModule("os"), "environ"), hashseed_str, env_value);
        assert(res == 0);

        Py_DECREF(env_value);
        Py_DECREF(hashseed_str);
    } else {
        unsetenv("PYTHONHASHSEED");

        int res =
            PyObject_DelItemString(PyObject_GetAttrString(PyImport_ImportModule("os"), "environ"), "PYTHONHASHSEED");
        assert(res == 0);
    }
#endif

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Restore standalone environment.");
    restoreStandaloneEnvironment();
#endif

    /* Lie about it, believe it or not, there are "site" files, that check
     * against later imports, see below.
     */
    Py_NoSiteFlag = SYSFLAG_NO_SITE;

    /* Set the command line parameters for run time usage. */
    NUITKA_PRINT_TRACE("main(): Calling setCommandLineParameters.");

#if PYTHON_VERSION < 0x300
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

    /* Complex call helpers need "__main__" constants, even if we only
     * go into "__parents__main__" module as a start point.
     */
#if _NUITKA_PLUGIN_MULTIPROCESSING_ENABLED || _NUITKA_PLUGIN_TRACEBACK_ENCRYPTION_ENABLED
    createMainModuleConstants();
#endif

    NUITKA_PRINT_TRACE("main(): Calling _initBuiltinOriginalValues().");
    _initBuiltinOriginalValues();

    /* Revert the wrong "sys.flags" value, it's used by "site" on at least
     * Debian for Python 3.3, more uses may exist.
     */
#if SYSFLAG_NO_SITE == 0
#if PYTHON_VERSION < 0x300
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

#if PYTHON_VERSION < 0x300
    _initSlotCompare();
#endif
#if PYTHON_VERSION >= 0x270
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

    /* At least on Windows, we support disabling the console via linker flag, but now
       need to provide the NUL standard file handles manually in this case. */
    {
        PyObject *nul_filename = Nuitka_String_FromString("NUL:");

        if (PySys_GetObject((char *)"stdin") == NULL) {
            PyObject *stdin_file = BUILTIN_OPEN_SIMPLE(nul_filename, "r", NULL);

            CHECK_OBJECT(stdin_file);
            PySys_SetObject((char *)"stdin", stdin_file);
        }

        if (PySys_GetObject((char *)"stdout") == NULL) {
            PyObject *stdout_file = BUILTIN_OPEN_SIMPLE(nul_filename, "w", NULL);

            CHECK_OBJECT(stdout_file);
            PySys_SetObject((char *)"stdout", stdout_file);
        }

        if (PySys_GetObject((char *)"stderr") == NULL) {
            PyObject *stderr_file = BUILTIN_OPEN_SIMPLE(nul_filename, "w", NULL);

            CHECK_OBJECT(stderr_file);

            PySys_SetObject((char *)"stderr", stderr_file);
        }

        Py_DECREF(nul_filename);
    }

#if defined(NUITKA_FORCED_STDOUT_PATH)
    {
        wchar_t filename_buffer[1024];
        wchar_t const *pattern = L"" NUITKA_FORCED_STDOUT_PATH;

        bool res = expandWindowsPath(filename_buffer, pattern, sizeof(filename_buffer) / sizeof(wchar_t));

        if (res == false) {
            puts("Error, couldn't expand pattern:");
            _putws(pattern);
            abort();
        }

        PyObject *filename = PyUnicode_FromWideChar(filename_buffer, wcslen(filename_buffer));

        PyObject *stdout_file = BUILTIN_OPEN_SIMPLE(filename, "w", const_int_pos_1);
        if (unlikely(stdout_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        PySys_SetObject((char *)"stdout", stdout_file);
    }
#endif

#if defined(NUITKA_FORCED_STDERR_PATH)
    {
        wchar_t filename_buffer[1024];
        wchar_t const *pattern = L"" NUITKA_FORCED_STDERR_PATH;

        bool res = expandWindowsPath(filename_buffer, pattern, sizeof(filename_buffer) / sizeof(wchar_t));

        if (res == false) {
            puts("Error, couldn't expand pattern:");
            _putws(pattern);
            abort();
        }

        PyObject *filename = PyUnicode_FromWideChar(filename_buffer, wcslen(filename_buffer));

        PyObject *stderr_file = BUILTIN_OPEN_SIMPLE(filename, "w", const_int_pos_1);
        if (unlikely(stderr_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        PySys_SetObject((char *)"stderr", stderr_file);
    }
#endif

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Calling setEarlyFrozenModulesFileAttribute().");

    setEarlyFrozenModulesFileAttribute();
#endif

#if _NUITKA_FROZEN > 0
    NUITKA_PRINT_TRACE("main(): Removing early frozen module table again.");
    PyImport_FrozenModules = old_frozen;
    assert(old_frozen != NULL);
#endif

    NUITKA_PRINT_TRACE("main(): Calling setupMetaPathBasedLoader().");
    /* Enable meta path based loader. */
    setupMetaPathBasedLoader();

    _PyWarnings_Init();

    /* Disable CPython warnings if requested to. */
#if NO_PYTHON_WARNINGS
    {
#if PYTHON_VERSION >= 0x300
        wchar_t ignore[] = L"ignore";
#else
        char ignore[] = "ignore";
#endif

        PySys_AddWarnOption(ignore);

#if PYTHON_VERSION >= 0x342 && defined(_NUITKA_FULL_COMPAT)
        // For full compatibility bump the warnings registry version,
        // otherwise modules "__warningsregistry__" will mismatch.
        PyObject *warnings_module = PyImport_ImportModule("warnings");
        PyObject *meth = PyObject_GetAttrString(warnings_module, "_filters_mutated");

        CALL_FUNCTION_NO_ARGS(meth);
#endif
    }
#endif

#if PYTHON_VERSION >= 0x300
    NUITKA_PRINT_TRACE("main(): Calling patchInspectModule().");
    patchInspectModule();
#endif

#if _NUITKA_PROFILE
    startProfiling();
#endif

    /* Execute the main module unless plugins want to do something else. In case of
       multiprocessing making a fork on Windows, we should execute __parents_main__
       instead. And for Windows Service we call the plugin C code to call us back
       to launch main code in a callback. */
#ifdef _NUITKA_PLUGIN_MULTIPROCESSING_ENABLED
    if (unlikely(is_multiprocessing_fork)) {
        NUITKA_PRINT_TRACE("main(): Calling __parents_main__.");
        IMPORT_EMBEDDED_MODULE("__parents_main__");
    } else {
#endif
#if defined(_NUITKA_ONEFILE) && defined(_WIN32)
        {
            char buffer[128] = {0};
            DWORD size = GetEnvironmentVariableA("NUITKA_ONEFILE_PARENT", buffer, sizeof(buffer));

            if (size > 0 && size < 127) {
                onefile_ppid = atol(buffer);

                HANDLE onefile_thread = CreateThread(NULL, 0, doOnefileParentMonitoring, NULL, 0, NULL);
            }
        }
#endif
        PyDict_DelItem(PyImport_GetModuleDict(), const_str_plain___main__);

#if _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
        NUITKA_PRINT_TRACE("main(): Calling plugin SvcLaunchService() entry point.");
        SvcLaunchService();
#else
    /* Execute the "__main__" module. */
    NUITKA_PRINT_TRACE("main(): Calling __main__.");

    IMPORT_EMBEDDED_MODULE("__main__");
#endif
#ifdef _NUITKA_PLUGIN_MULTIPROCESSING_ENABLED
    }
#endif

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

    int exit_code;

    if (ERROR_OCCURRED()) {
#if PYTHON_VERSION >= 0x300
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

        exit_code = 1;
    } else {
        exit_code = 0;
    }

#if _DEBUG_REFCOUNTS
    PRINT_REFCOUNTS();
#endif

    Py_Exit(exit_code);

    // The "Py_Exit()" calls is not supposed to return.
    NUITKA_CANNOT_GET_HERE("Py_Exit does not return");
}

/* This is an unofficial API, not available on Windows, but on Linux and others
 * it is exported, and has been used by some code.
 */
#ifndef _WIN32
#ifdef __cplusplus
extern "C" {
#endif

#if PYTHON_VERSION >= 0x300
#if defined(__GNUC__)
__attribute__((weak))
__attribute__((visibility("default")))
#endif
void Py_GetArgcArgv(int *argc, wchar_t ***argv) {
    *argc = orig_argc;
    *argv = argv_unicode;
}

#else
#if defined(__GNUC__)
__attribute__((weak))
__attribute__((visibility("default")))
#endif
void Py_GetArgcArgv(int *argc, char ***argv) {
    *argc = orig_argc;
    *argv = orig_argv;
}
#endif

#ifdef __cplusplus
}
#endif
#endif
