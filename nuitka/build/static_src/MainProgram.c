//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* The main program for a compiled program.
 *
 * It needs to prepare the interpreter and then loads and executes
 * the "__main__" module.
 *
 * For multiprocessing, joblib, loky there is things here that will
 * allow them to fork properly with their intended entry points.
 *
 * spell-checker: ignore joblib loky anyio platlibdir
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
#define SYSFLAG_UNBUFFERED 0
#define SYSFLAG_DONTWRITEBYTECODE 0
#define NUITKA_MAIN_MODULE_NAME "__main__"
#define NUITKA_MAIN_IS_PACKAGE_BOOL false
#define _NUITKA_ATTACH_CONSOLE_WINDOW 1
#endif

// It doesn't work for MinGW64 to update the standard output handles early on,
// so make a difference here.
#if defined(NUITKA_FORCED_STDOUT_PATH) || defined(NUITKA_FORCED_STDERR_PATH)
#if defined(__MINGW64__) || defined(__MINGW32__)
#define NUITKA_STANDARD_HANDLES_EARLY 0
#else
#define NUITKA_STANDARD_HANDLES_EARLY 1
#endif
#else
#define NUITKA_STANDARD_HANDLES_EARLY 0
#endif

#if defined(_WIN32) && (defined(_NUITKA_ATTACH_CONSOLE_WINDOW) || defined(_NUITKA_HIDE_CONSOLE_WINDOW))
#include "HelpersConsole.c"
#endif

extern PyCodeObject *code_objects_main;

/* For later use in "Py_GetArgcArgv" we expose the needed value  */
#if PYTHON_VERSION >= 0x300
static wchar_t **orig_argv;
#else
static char **orig_argv;
#endif
static int orig_argc;

#if _NUITKA_FROZEN > 0
extern void copyFrozenModulesTo(struct _frozen *destination);

// The original frozen modules list.
#if PYTHON_VERSION < 0x300
static struct _frozen *old_frozen = NULL;
#else
static struct _frozen const *old_frozen = NULL;
#endif

static void prepareFrozenModules(void) {
    // Tell the CPython library to use our pre-compiled modules as frozen
    // modules. This for those modules/packages like "encoding" that will be
    // loaded during "Py_Initialize" already, for the others they may be
    // compiled.

    // The CPython library before 3.11 has some pre-existing frozen modules, we
    // only append to those to keep compatible.
    struct _frozen const *search = PyImport_FrozenModules;
    int pre_existing_count;

    if (search) {
        while (search->name) {
            search++;
        }
        pre_existing_count = (int)(search - PyImport_FrozenModules);
    } else {
        pre_existing_count = 0;
    }

    // Allocate new memory and merge the tables. Keeping the old ones has the
    // advantage that e.g. "import this" is going to be compatible, and there
    // might be Python flavors that add more.
    struct _frozen *merged =
        (struct _frozen *)malloc(sizeof(struct _frozen) * (_NUITKA_FROZEN + pre_existing_count + 1));

    memcpy(merged, PyImport_FrozenModules, pre_existing_count * sizeof(struct _frozen));
    copyFrozenModulesTo(merged + pre_existing_count);
    old_frozen = PyImport_FrozenModules;
    PyImport_FrozenModules = merged;
}
#endif

#include "nuitka/environment_variables.h"

#ifdef _NUITKA_STANDALONE

#include "pythonrun.h"

static environment_char_t const *old_env_path;
static environment_char_t const *old_env_pythonhome;

static void prepareStandaloneEnvironment(void) {
    /* Setup environment variables to tell CPython that we would like it to use
     * the provided binary directory as the place to look for DLLs and for
     * extension modules.
     */
    old_env_path = getEnvironmentVariable("PATH");
    // Remove the PATH during Python init, so it won't pick up stuff from there.
    setEnvironmentVariable("PATH", makeEnvironmentLiteral("/"));

    old_env_pythonhome = getEnvironmentVariable("PYTHONHOME");
#if defined(_WIN32)
    setEnvironmentVariable("PYTHONHOME", getBinaryDirectoryWideChars(true));
#else
    setEnvironmentVariable("PYTHONHOME", getBinaryDirectoryHostEncoded(true));
#endif

#if defined(_WIN32)
    SetDllDirectoryW(getBinaryDirectoryWideChars(true));
#endif

#if PYTHON_VERSION < 0x300
    char *binary_directory = (char *)getBinaryDirectoryHostEncoded(true);
    NUITKA_PRINTF_TRACE("main(): Binary dir is %s\n", binary_directory);

    Py_SetPythonHome(binary_directory);
#elif PYTHON_VERSION < 0x370
    wchar_t *binary_directory = (wchar_t *)getBinaryDirectoryWideChars(true);
    NUITKA_PRINTF_TRACE("main(): Binary dir is %S\n", binary_directory);

    Py_SetPythonHome(binary_directory);
    Py_SetPath(binary_directory);

#endif

#if PYTHON_VERSION >= 0x380 && PYTHON_VERSION < 0x3b0 && defined(_WIN32)
    _Py_path_config.isolated = 1;
#endif
}

static void restoreStandaloneEnvironment(void) {
    /* Make sure to use the optimal value for standalone mode only. */
#if PYTHON_VERSION < 0x300
    PySys_SetPath((char *)getBinaryDirectoryHostEncoded(true));
    // NUITKA_PRINTF_TRACE("Final PySys_GetPath is 's'.\n", PySys_GetPath());
#elif PYTHON_VERSION < 0x370
    PySys_SetPath(getBinaryDirectoryWideChars(true));
    Py_SetPath(getBinaryDirectoryWideChars(true));
    // NUITKA_PRINTF_TRACE("Final Py_GetPath is '%ls'.\n", Py_GetPath());
#endif

#ifdef _NUITKA_EXPERIMENTAL_DUMP_PY_PATH_CONFIG
    wprintf(L"_Py_path_config.program_full_path='%lS'\n", _Py_path_config.program_full_path);
    wprintf(L"_Py_path_config.program_name='%lS'\n", _Py_path_config.program_name);
    wprintf(L"_Py_path_config.prefix='%lS'\n", _Py_path_config.prefix);
    wprintf(L"_Py_path_config.exec_prefix='%lS'\n", _Py_path_config.exec_prefix);
    wprintf(L"_Py_path_config.module_search_path='%lS'\n", _Py_path_config.module_search_path);
    wprintf(L"_Py_path_config.home='%lS'\n", _Py_path_config.home);
#endif
}

#endif

extern void _initCompiledCellType();
extern void _initCompiledGeneratorType();
extern void _initCompiledFunctionType();
extern void _initCompiledMethodType();
extern void _initCompiledFrameType();

#include <locale.h>

#ifdef _WIN32
#define _NUITKA_NATIVE_WCHAR_ARGV 1
#else
#define _NUITKA_NATIVE_WCHAR_ARGV 0
#endif

// Types of command line arguments are different between Python2/3.
#if PYTHON_VERSION >= 0x300 && _NUITKA_NATIVE_WCHAR_ARGV == 0
static wchar_t **convertCommandLineParameters(int argc, char **argv) {
    // Originally taken from CPython3: There seems to be no sane way to use
    static wchar_t **argv_copy;
    argv_copy = (wchar_t **)malloc(sizeof(wchar_t *) * argc);

    // Temporarily disable locale for conversions to not use it.
    char *old_locale = strdup(setlocale(LC_ALL, NULL));
    setlocale(LC_ALL, "");

    for (int i = 0; i < argc; i++) {
#if PYTHON_VERSION >= 0x350
        argv_copy[i] = Py_DecodeLocale(argv[i], NULL);
#elif defined(__APPLE__) && PYTHON_VERSION >= 0x300
        argv_copy[i] = _Py_DecodeUTF8_surrogateescape(argv[i], strlen(argv[i]));
#else
        argv_copy[i] = _Py_char2wchar(argv[i], NULL);
#endif

        assert(argv_copy[i]);
    }

    setlocale(LC_ALL, old_locale);
    free(old_locale);

    return argv_copy;
}
#endif

#if _DEBUG_REFCOUNTS
static void PRINT_REFCOUNTS(void) {
    // spell-checker: ignore Asend, Athrow

    PRINT_STRING("REFERENCE counts at program end:\n");
    PRINT_STRING("active | allocated | released\n");
    PRINT_FORMAT("Compiled Functions: %d | %d | %d (module/class ownership may occur)\n",
                 count_active_Nuitka_Function_Type, count_allocated_Nuitka_Function_Type,
                 count_released_Nuitka_Function_Type);
    PRINT_FORMAT("Compiled Generators: %d | %d | %d\n", count_active_Nuitka_Generator_Type,
                 count_allocated_Nuitka_Generator_Type, count_released_Nuitka_Generator_Type);
#if PYTHON_VERSION >= 0x350
    PRINT_FORMAT("Compiled Coroutines: %d | %d | %d\n", count_active_Nuitka_Coroutine_Type,
                 count_allocated_Nuitka_Coroutine_Type, count_released_Nuitka_Coroutine_Type);
    PRINT_FORMAT("Compiled Coroutines Wrappers: %d | %d | %d\n", count_active_Nuitka_CoroutineWrapper_Type,
                 count_allocated_Nuitka_CoroutineWrapper_Type, count_released_Nuitka_CoroutineWrapper_Type);

    PRINT_FORMAT("Compiled Coroutines AIter Wrappers: %d | %d | %d\n", count_active_Nuitka_AIterWrapper_Type,
                 count_allocated_Nuitka_AIterWrapper_Type, count_released_Nuitka_AIterWrapper_Type);
#endif
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
    PRINT_FORMAT("Compiled Cells: %d | %d | %d (function ownership may occur)\n", count_active_Nuitka_Cell_Type,
                 count_allocated_Nuitka_Cell_Type, count_released_Nuitka_Cell_Type);
    PRINT_STRING("CACHED counts at program end:\n");
    PRINT_STRING("active | allocated | released | hits\n");
    PRINT_FORMAT("Cached Frames: %d | %d | %d | %d\n", count_active_frame_cache_instances,
                 count_allocated_frame_cache_instances, count_released_frame_cache_instances,
                 count_hit_frame_cache_instances);
}
#endif

static int HANDLE_PROGRAM_EXIT(PyThreadState *tstate) {
#if _DEBUG_REFCOUNTS
    PRINT_REFCOUNTS();
#endif

    int exit_code;

    if (HAS_ERROR_OCCURRED(tstate)) {
        // TODO: Clarify which versions this applies to still
#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x3c0
        /* Remove the frozen importlib traceback part, which would not be compatible. */

        while (tstate->curexc_traceback) {
            PyTracebackObject *tb = (PyTracebackObject *)tstate->curexc_traceback;
            PyFrameObject *frame = tb->tb_frame;

            if (0 == strcmp(PyUnicode_AsUTF8(Nuitka_Frame_GetCodeObject(frame)->co_filename),
                            "<frozen importlib._bootstrap>")) {
                tstate->curexc_traceback = (PyObject *)tb->tb_next;
                Py_INCREF(tb->tb_next);

                continue;
            }

            break;
        }
#endif
        NUITKA_FINALIZE_PROGRAM(tstate);

        PyErr_PrintEx(0);

        exit_code = 1;
    } else {
        exit_code = 0;
    }

    return exit_code;
}

static PyObject *EXECUTE_MAIN_MODULE(PyThreadState *tstate, char const *module_name, bool is_package) {
    NUITKA_INIT_PROGRAM_LATE(module_name);

    if (is_package) {
        char const *w = module_name;

        for (;;) {
            char const *s = strchr(w, '.');

            if (s == NULL) {
                break;
            }

            w = s + 1;

            char buffer[1024];
            memset(buffer, 0, sizeof(buffer));
            memcpy(buffer, module_name, s - module_name);

            PyObject *result = IMPORT_EMBEDDED_MODULE(tstate, buffer);

            if (HAS_ERROR_OCCURRED(tstate)) {
                return result;
            }
        }
    }

    return IMPORT_EMBEDDED_MODULE(tstate, module_name);
}

#if _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
#include "nuitka_windows_service.h"

// Callback from Windows Service logic.
void SvcStartPython(void) {
    PyThreadState *tstate = PyThreadState_GET();

    EXECUTE_MAIN_MODULE(tstate, NUITKA_MAIN_MODULE_NAME, NUITKA_MAIN_IS_PACKAGE_BOOL);

    NUITKA_PRINT_TIMING("SvcStartPython() Python exited.")

    int exit_code = HANDLE_PROGRAM_EXIT(tstate);

    // TODO: Log exception and call ReportSvcStatus

    NUITKA_PRINT_TIMING("SvcStartPython(): Calling Py_Exit.");
    Py_Exit(exit_code);
}

void SvcStopPython(void) { PyErr_SetInterrupt(); }

#endif

// This is a multiprocessing fork
static bool is_multiprocessing_fork = false;
// This is a multiprocessing resource tracker if not -1
static int multiprocessing_resource_tracker_arg = -1;

// This is a joblib loky fork
#ifdef _WIN32
static bool is_joblib_popen_loky_win32 = false;
static int loky_joblib_pipe_handle_arg = 0;
static int loky_joblib_parent_pid_arg = 0;
#else
static bool is_joblib_popen_loky_posix = false;
#endif

// This is a joblib resource tracker if not -1
static int loky_resource_tracker_arg = -1;

// This is a "anyio.to_process" fork
static bool is_anyio_to_process = false;

// Parse the command line parameters to decide if it's a multiprocessing usage
// or something else special.
#if _NUITKA_NATIVE_WCHAR_ARGV == 0
static void setCommandLineParameters(int argc, char **argv) {
#else
static void setCommandLineParameters(int argc, wchar_t **argv) {
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_SELF_FORKING
#if _NUITKA_NATIVE_WCHAR_ARGV == 0
    printf("Command line: ");
    for (int i = 0; i < argc; i++) {
        if (i != 0) {
            printf(" ");
        }
        printf("'%s'", argv[i]);
    }
    printf("\n");
#else
    wprintf(L"Command line: '%lS' %d\n", GetCommandLineW(), argc);
#endif
#endif

    // We might need to handle special parameters from plugins that are
    // very deeply woven into command line handling. These are right now
    // multiprocessing, which indicates that it's forking via extra

    // command line argument. And Windows Service indicates need to
    //   install and exit here too.

    for (int i = 1; i < argc; i++) {
        if ((i + 1 < argc) && (strcmpFilename(argv[i], FILENAME_EMPTY_STR "--multiprocessing-fork")) == 0) {
            is_multiprocessing_fork = true;
            break;
        }

        if ((i + 1 < argc) && (strcmpFilename(argv[i], FILENAME_EMPTY_STR "--multiprocessing-resource-tracker")) == 0) {
#if _NUITKA_NATIVE_WCHAR_ARGV == 0
            multiprocessing_resource_tracker_arg = atoi(argv[i + 1]);
#else
            multiprocessing_resource_tracker_arg = _wtoi(argv[i + 1]);
#endif
            break;
        }

        if (i == 1) {
#if _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
            if (strcmpFilename(argv[i], FILENAME_EMPTY_STR "install") == 0) {
                NUITKA_PRINT_TRACE("main(): Calling plugin SvcInstall().");

                SvcInstall();
                NUITKA_CANNOT_GET_HERE("main(): SvcInstall must not return");
            }
#endif
        }

        if ((i + 1 < argc) && (strcmpFilename(argv[i], FILENAME_EMPTY_STR "-c") == 0)) {
            // The joblib loky resource tracker is launched like this.
            if (scanFilename(argv[i + 1],
                             FILENAME_EMPTY_STR
                             "from joblib.externals.loky.backend.resource_tracker import main; main(%i, False)",
                             &loky_resource_tracker_arg)) {
                break;
            }

#if defined(_WIN32)
            if (strcmpFilename(argv[i + 1], FILENAME_EMPTY_STR
                               "from joblib.externals.loky.backend.popen_loky_win32 import main; main()") == 0) {
                is_joblib_popen_loky_win32 = true;
                break;
            }

            if (scanFilename(argv[i + 1],
                             FILENAME_EMPTY_STR "from joblib.externals.loky.backend.popen_loky_win32 import main; "
                                                "main(pipe_handle=%i, parent_pid=%i)",
                             &loky_joblib_pipe_handle_arg, &loky_joblib_parent_pid_arg)) {
                is_joblib_popen_loky_win32 = true;
                break;
            }

#endif
        }

        if ((i + 1 < argc) && (strcmpFilename(argv[i], FILENAME_EMPTY_STR "-m") == 0)) {
#if !defined(_WIN32)
            // The joblib loky posix popen is launching like this.
            if (strcmpFilename(argv[i + 1], FILENAME_EMPTY_STR "joblib.externals.loky.backend.popen_loky_posix") == 0) {
                is_joblib_popen_loky_posix = true;
                break;
            }
#endif

            // The anyio.to_process module is launching like this.
            if (strcmpFilename(argv[i + 1], FILENAME_EMPTY_STR "anyio.to_process") == 0) {
                is_anyio_to_process = true;
                break;
            }
        }

#if !defined(_NUITKA_DEPLOYMENT_MODE) && !defined(_NUITKA_NO_DEPLOYMENT_SELF_EXECUTION)
        if ((strcmpFilename(argv[i], FILENAME_EMPTY_STR "-c") == 0) ||
            (strcmpFilename(argv[i], FILENAME_EMPTY_STR "-m") == 0)) {
            fprintf(stderr,
                    "Error, the program tried to call itself with '" FILENAME_FORMAT_STR "' argument. Disable with "
                    "'--no-deployment-flag=self-execution'.\n",
                    argv[i]);
            exit(2);
        }
#endif
    }
}

#if defined(_NUITKA_ONEFILE_MODE) && defined(_WIN32)

static long onefile_ppid;

DWORD WINAPI doOnefileParentMonitoring(LPVOID lpParam) {
    NUITKA_PRINT_TRACE("Onefile parent monitoring starts.");

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

    NUITKA_PRINT_TRACE("Onefile parent monitoring causes KeyboardInterrupt.");
    PyErr_SetInterrupt();

    Sleep(_NUITKA_ONEFILE_CHILD_GRACE_TIME_INT);

    NUITKA_PRINT_TRACE("Onefile parent monitoring hard kills after ignored KeyboardInterrupt.");
    ExitProcess(1);

    return 0;
}
#endif

#if defined(_WIN32) && PYTHON_VERSION < 0x300
static char **getCommandLineToArgvA(char *lpCmdline) {
    char *s = lpCmdline;

    int argc = 1;

    if (*s == '"') {
        s++;

        while (*s != 0) {
            if (*s++ == '"') {
                break;
            }
        }
    } else {
        while (*s != 0 && *s != ' ' && *s != '\t') {
            s++;
        }
    }

    while (*s == ' ' || *s == '\t') {
        s++;
    }

    if (*s != 0) {
        argc++;
    }

    int quote_count = 0;
    int slash_count = 0;

    while (*s != 0) {
        if ((*s == ' ' || *s == '\t') && quote_count == 0) {
            while (*s == ' ' || *s == '\t') {
                s++;
            }

            if (*s != 0) {
                argc++;
            }
            slash_count = 0;
        } else if (*s == '\\') {
            slash_count++;
            s++;
        } else if (*s == '"') {
            if ((slash_count & 1) == 0) {
                quote_count++;
            }

            slash_count = 0;
            s++;

            while (*s == '"') {
                quote_count++;
                s++;
            }

            quote_count = quote_count % 3;

            if (quote_count == 2) {
                quote_count = 0;
            }
        } else {
            slash_count = 0;
            s++;
        }
    }

    char **argv = (char **)malloc((argc + 1) * sizeof(char *) + (strlen(lpCmdline) + 1));
    assert(argv);

    char *cmdline = (char *)(argv + argc + 1);
    strcpy(cmdline, lpCmdline);

    argv[0] = cmdline;
    argc = 1;

    char *d = cmdline;

    if (*d == '"') {
        s = d + 1;

        while (*s != 0) {
            if (*s == '"') {
                s++;
                break;
            }

            *d++ = *s++;
        }
    } else {
        while (*d && *d != ' ' && *d != '\t') {
            d++;
        }

        s = d;

        if (*s) {
            s++;
        }
    }

    *d++ = 0;

    while (*s == ' ' || *s == '\t') {
        s++;
    }

    if (*s == 0) {
        argv[argc] = NULL;
        return argv;
    }

    argv[argc++] = d;
    quote_count = 0;
    slash_count = 0;

    while (*s != 0) {
        if ((*s == ' ' || *s == '\t') && quote_count == 0) {
            *d++ = 0;
            slash_count = 0;

            do {
                s++;
            } while (*s == ' ' || *s == '\t');

            if (*s) {
                argv[argc++] = d;
            }

        } else if (*s == '\\') {
            *d++ = *s++;
            slash_count++;
        } else if (*s == '"') {
            if ((slash_count & 1) == 0) {
                d -= slash_count / 2;
                quote_count++;
            } else {
                d = d - slash_count / 2 - 1;
                *d++ = '"';
            }
            s++;
            slash_count = 0;

            while (*s == '"') {
                if (++quote_count == 3) {
                    *d++ = '"';
                    quote_count = 0;
                }
                s++;
            }
            if (quote_count == 2)
                quote_count = 0;
        } else {
            *d++ = *s++;
            slash_count = 0;
        }
    }

    *d = '\0';
    argv[argc] = NULL;

    return argv;
}
#endif

// Disable wild card expansion for MinGW64, spell-checker: ignore _dowildcard
#if defined(__MINGW64__) || defined(__MINGW32__)
int _dowildcard = 0;
#endif

#ifdef _WIN32
static void setStdFileHandleNumber(PyThreadState *tstate, DWORD std_handle_id, PyObject *file_handle) {
    PyObject *file_no_value = CALL_METHOD_NO_ARGS(tstate, file_handle, const_str_plain_fileno);

    if (unlikely(file_no_value == NULL)) {
        CLEAR_ERROR_OCCURRED(tstate);
        return;
    }

    long file_number = PyLong_AsLong(file_no_value);

    Py_DECREF(file_no_value);

    if (unlikely(file_number == -1 && DROP_ERROR_OCCURRED(tstate))) {
        return;
    }

    // Casting from long to handle gives warnings if not using a suitable
    // sized integer type in between.
    if (std_handle_id != STD_INPUT_HANDLE) {
        SetStdHandle(std_handle_id, (HANDLE)(intptr_t)file_number);
    }
}
#endif

static bool shallSetOutputHandleToNull(char const *name) {
#if NUITKA_FORCED_STDOUT_NULL_BOOL
    if (strcmp(name, "stdout") == 0) {
        return true;
    }
#endif

#if NUITKA_FORCED_STDERR_NULL_BOOL
    if (strcmp(name, "stderr") == 0) {
        return true;
    }
#elif defined(NUITKA_FORCED_STDERR_PATH) || defined(NUITKA_FORCED_STDERR_NONE_BOOL)
    if (strcmp(name, "stderr") == 0) {
        return false;
    }
#endif

    PyObject *sys_std_handle = Nuitka_SysGetObject(name);
    if (sys_std_handle == NULL || sys_std_handle == Py_None) {
        return true;
    }

    return false;
}

static void setStdinHandle(PyThreadState *tstate, PyObject *stdin_file) {

    CHECK_OBJECT(stdin_file);
    Nuitka_SysSetObject("stdin", stdin_file);

#ifdef _WIN32
    setStdFileHandleNumber(tstate, STD_INPUT_HANDLE, stdin_file);
#endif
}

static void setStdoutHandle(PyThreadState *tstate, PyObject *stdout_file) {
    CHECK_OBJECT(stdout_file);
    Nuitka_SysSetObject("stdout", stdout_file);

#ifdef _WIN32
    setStdFileHandleNumber(tstate, STD_OUTPUT_HANDLE, stdout_file);
#endif
}

static void setStderrHandle(PyThreadState *tstate, PyObject *stderr_file) {
    CHECK_OBJECT(stderr_file);

    Nuitka_SysSetObject("stderr", stderr_file);

#ifdef _WIN32
    setStdFileHandleNumber(tstate, STD_ERROR_HANDLE, stderr_file);
#endif
}

#if NUITKA_STANDARD_HANDLES_EARLY == 0
#if defined(NUITKA_FORCED_STDOUT_PATH) || defined(NUITKA_FORCED_STDERR_PATH)
#ifdef _WIN32
static PyObject *getExpandedTemplatePath(wchar_t const *template_path) {
    wchar_t filename_buffer[1024];
    bool res = expandTemplatePathW(filename_buffer, template_path, sizeof(filename_buffer) / sizeof(wchar_t));

    if (res == false) {
        puts("Error, couldn't expand pattern:");
        abort();
    }

    return NuitkaUnicode_FromWideChar(filename_buffer, -1);
}
#else
static PyObject *getExpandedTemplatePath(char const *template_path) {
    char filename_buffer[1024];
    bool res = expandTemplatePath(filename_buffer, template_path, sizeof(filename_buffer));

    if (res == false) {
        printf("Error, couldn't expand pattern: %s\n", template_path);
        abort();
    }

    return Nuitka_String_FromString(filename_buffer);
}
#endif
#endif
#endif

static void setInputOutputHandles(PyThreadState *tstate) {
    // We support disabling the stdout/stderr through options as well as
    // building for GUI on Windows, which has inputs disabled by default, this
    // code repairs that by setting or forcing them to "os.devnull"
    // input/outputs

    // This defaults to "utf-8" internally. We may add an argument of use
    // platform ones in the future.
    PyObject *encoding = NULL;

// Reconfigure stdout for line buffering, for mixing traces and Python IO
// better, and force it to utf-8, it often becomes platform IO for no good
// reason.
#if NUITKA_STANDARD_HANDLES_EARLY == 1 && PYTHON_VERSION >= 0x370
    NUITKA_PRINT_TRACE("setInputOutputHandles(): Early handles.");
#if defined(NUITKA_FORCED_STDOUT_PATH) || defined(NUITKA_FORCED_STDERR_PATH)
    PyObject *args = MAKE_DICT_EMPTY(tstate);

    DICT_SET_ITEM(args, const_str_plain_encoding, Nuitka_String_FromString("utf-8"));
    DICT_SET_ITEM(args, const_str_plain_line_buffering, Py_True);

#if defined(NUITKA_FORCED_STDOUT_PATH)
    NUITKA_PRINT_TRACE("setInputOutputHandles(): Forced stdout update.");
    {
        PyObject *sys_stdout = Nuitka_SysGetObject("stdout");

        PyObject *method = LOOKUP_ATTRIBUTE(tstate, sys_stdout, const_str_plain_reconfigure);
        CHECK_OBJECT(method);

        PyObject *result = CALL_FUNCTION_WITH_KW_ARGS(tstate, method, args);
        CHECK_OBJECT(result);
    }
#endif

#if defined(NUITKA_FORCED_STDERR_PATH)
    NUITKA_PRINT_TRACE("setInputOutputHandles(): Forced stderr update.");
    {
        PyObject *sys_stderr = Nuitka_SysGetObject("stderr");
        if (sys_stderr != Py_None) {
            PyObject *method = LOOKUP_ATTRIBUTE(tstate, sys_stderr, const_str_plain_reconfigure);
            CHECK_OBJECT(method);

            PyObject *result = CALL_FUNCTION_WITH_KW_ARGS(tstate, method, args);
            CHECK_OBJECT(result);
        }
    }
#endif

    Py_DECREF(args);
#endif

    NUITKA_PRINT_TRACE("setInputOutputHandles(): Done with early handles.");
#endif

#if NUITKA_STANDARD_HANDLES_EARLY == 0
    NUITKA_PRINT_TRACE("setInputOutputHandles(): Late handles.");
#if defined(NUITKA_FORCED_STDOUT_PATH)
    {
#if defined(_WIN32)
        PyObject *filename = getExpandedTemplatePath(L"" NUITKA_FORCED_STDOUT_PATH);
#else
        PyObject *filename = getExpandedTemplatePath(NUITKA_FORCED_STDOUT_PATH);
#endif
        PyObject *stdout_file = BUILTIN_OPEN_SIMPLE(tstate, filename, "w", SYSFLAG_UNBUFFERED != 1, encoding);
        if (unlikely(stdout_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        setStdoutHandle(tstate, stdout_file);
    }
#endif

#if defined(NUITKA_FORCED_STDERR_PATH)
    {
#ifdef _WIN32
        PyObject *filename = getExpandedTemplatePath(L"" NUITKA_FORCED_STDERR_PATH);
#else
        PyObject *filename = getExpandedTemplatePath(NUITKA_FORCED_STDERR_PATH);
#endif
        PyObject *stderr_file = BUILTIN_OPEN_SIMPLE(tstate, filename, "w", false, encoding);
        if (unlikely(stderr_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        setStderrHandle(tstate, stderr_file);
    }
#endif
#endif

    {
#if defined(_WIN32)
        PyObject *devnull_filename = Nuitka_String_FromString("NUL:");
#else
        PyObject *devnull_filename = Nuitka_String_FromString("/dev/null");
#endif

        NUITKA_PRINT_TRACE("setInputOutputHandles(): Considering stdin.");

        if (shallSetOutputHandleToNull("stdin")) {
            NUITKA_PRINT_TRACE("setInputOutputHandles(): Set stdin to NULL file.");

            // CPython core requires stdin to be buffered due to methods usage, and it won't matter
            // here much.
            PyObject *stdin_file = BUILTIN_OPEN_SIMPLE(tstate, devnull_filename, "r", true, encoding);
            CHECK_OBJECT(stdin_file);

            setStdinHandle(tstate, stdin_file);
        }

        NUITKA_PRINT_TRACE("setInputOutputHandles(): Considering stdout.");

        if (shallSetOutputHandleToNull("stdout")) {
            NUITKA_PRINT_TRACE("setInputOutputHandles(): Set stdout to NULL file.");

            PyObject *stdout_file = BUILTIN_OPEN_SIMPLE(tstate, devnull_filename, "w", false, encoding);
            CHECK_OBJECT(stdout_file);

            setStdoutHandle(tstate, stdout_file);
        }

        NUITKA_PRINT_TRACE("setInputOutputHandles(): Considering stderr.");

        if (shallSetOutputHandleToNull("stderr")) {
            NUITKA_PRINT_TRACE("setInputOutputHandles(): Set stderr to NULL file.");

            PyObject *stderr_file = BUILTIN_OPEN_SIMPLE(tstate, devnull_filename, "w", false, encoding);
            CHECK_OBJECT(stderr_file);

            setStderrHandle(tstate, stderr_file);
        }

        Py_DECREF(devnull_filename);
    }

#if NUITKA_FORCED_STDOUT_NONE_BOOL
    NUITKA_PRINT_TRACE("setInputOutputHandles(): Forcing stdout to None.");
    setStdoutHandle(tstate, Py_None);
#endif

#if NUITKA_FORCED_STDERR_NONE_BOOL
    NUITKA_PRINT_TRACE("setInputOutputHandles(): Forcing stderr to None.");
    setStderrHandle(tstate, Py_None);
#endif

    Py_XDECREF(encoding);
}

static void Nuitka_Py_Initialize(void) {
#if PYTHON_VERSION > 0x350 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_ALLOCATORS)
    initNuitkaAllocators();
#endif

#if PYTHON_VERSION < 0x380 || defined(_NUITKA_EXPERIMENTAL_OLD_PY_INITIALIZE)
    Py_Initialize();
#else
#if PYTHON_VERSION < 0x3d0
    PyStatus status = _PyRuntime_Initialize();
    if (unlikely(status._type != 0)) {
        Py_ExitStatusException(status);
    }
    NUITKA_MAY_BE_UNUSED _PyRuntimeState *runtime = &_PyRuntime;
    assert(!runtime->initialized);
#else
    PyStatus status;
#endif

    PyConfig config;
    _PyConfig_InitCompatConfig(&config);

    assert(orig_argv[0]);
    status = PyConfig_SetArgv(&config, orig_argc, orig_argv);

    if (PyStatus_Exception(status)) {
        Py_ExitStatusException(status);
    }

#ifdef _NUITKA_STANDALONE
    wchar_t *binary_directory = (wchar_t *)getBinaryDirectoryWideChars(true);

    PyConfig_SetString(&config, &config.executable, orig_argv[0]);
    PyConfig_SetString(&config, &config.prefix, binary_directory);
    PyConfig_SetString(&config, &config.exec_prefix, binary_directory);
    PyConfig_SetString(&config, &config.base_prefix, binary_directory);
    PyConfig_SetString(&config, &config.base_exec_prefix, binary_directory);
    PyConfig_SetString(&config, &config.home, binary_directory);
#if PYTHON_VERSION >= 0x390
    PyConfig_SetString(&config, &config.platlibdir, binary_directory);
#endif

    PyWideStringList_Append(&config.module_search_paths, binary_directory);
    config.module_search_paths_set = 1;
#endif

    // Need to disable frozen modules, Nuitka can handle them better itself.
#if PYTHON_VERSION >= 0x3b0
#ifdef _NUITKA_STANDALONE
    config.use_frozen_modules = 0;
#else
// Emulate PYTHON_FROZEN_MODULES for accelerated mode, it is only added in 3.13,
// but we need to control it for controlling things for accelerated binaries
// too.
#if PYTHON_VERSION >= 0x3b0 && PYTHON_VERSION <= 0x3d0
    environment_char_t const *frozen_modules_env = getEnvironmentVariable("PYTHON_FROZEN_MODULES");

    if (frozen_modules_env == NULL ||
        (compareEnvironmentString(frozen_modules_env, makeEnvironmentLiteral("off")) == 0)) {
        config.use_frozen_modules = 0;
    }
#endif
#endif
#endif

    config.install_signal_handlers = 1;

    NUITKA_PRINT_TIMING("Nuitka_Py_Initialize(): Calling Py_InitializeFromConfig.");

    status = Py_InitializeFromConfig(&config);
    if (unlikely(status._type != 0)) {
        Py_ExitStatusException(status);
    }

#ifdef _NUITKA_STANDALONE
    assert(wcscmp(config.exec_prefix, binary_directory) == 0);

// Empty "sys.path" first time, will be revived, but keep it
// short lived.
#if SYSFLAG_ISOLATED
    Nuitka_SysSetObject("path", PyList_New(0));
#endif
#endif

#endif
}

#include <fcntl.h>

#if NUITKA_STANDARD_HANDLES_EARLY == 1
#if defined(_WIN32)

static void changeStandardHandleTarget(int std_handle_id, FILE *std_handle, filename_char_t const *template_path) {
    filename_char_t filename_buffer[1024];

    bool res =
        expandTemplatePathFilename(filename_buffer, template_path, sizeof(filename_buffer) / sizeof(filename_char_t));

    if (res == false) {
        printf("Error, couldn't expand pattern '" FILENAME_FORMAT_STR "'\n", template_path);
        abort();
    }

    if (GetStdHandle(std_handle_id) == 0) {
        FILE *file_handle;

        if (std_handle_id == STD_INPUT_HANDLE) {
            file_handle = _wfreopen(filename_buffer, L"rb", std_handle);
        } else {
            file_handle = _wfreopen(filename_buffer, L"wb", std_handle);
        }

        if (file_handle == NULL) {
            perror("_wfreopen");
            abort();
        }

        BOOL r = SetStdHandle(std_handle_id, (HANDLE)_get_osfhandle(fileno(file_handle)));
        assert(r);

        *std_handle = *file_handle;

        assert(fileno(file_handle) == fileno(std_handle));

        int stdout_dup = dup(fileno(std_handle));
        if (stdout_dup >= 0) {
            close(stdout_dup);
        }

        DWORD mode = 0;
        if (GetConsoleMode((HANDLE)_get_osfhandle(fileno(std_handle)), &mode)) {
            exit(66);
        }
    } else {
        HANDLE w = CreateFileW(filename_buffer, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                               CREATE_ALWAYS, 0, NULL);

        if (w == INVALID_HANDLE_VALUE) {
            printOSErrorMessage("standard handle failed to create", GetLastError());
            abort();
        }
        BOOL r = SetStdHandle(std_handle_id, w);
        assert(r);

        int os_handle = _open_osfhandle((intptr_t)GetStdHandle(std_handle_id), O_WRONLY | O_TEXT);
        if (os_handle == -1) {
            perror("_open_osfhandle");
            abort();
        }

        int _int_res = dup2(os_handle, fileno(std_handle));

        if (_int_res == -1) {
            // Note: Without a console, this is normal to get no file number to
            // work with.
        }

        close(os_handle);
    }

    setvbuf(std_handle, NULL, _IOLBF, 4096);
}
#else
static void changeStandardHandleTarget(FILE *std_handle, filename_char_t const *template_path) {
    filename_char_t filename_buffer[1024];

    bool res = expandTemplatePath(filename_buffer, template_path, sizeof(filename_buffer) / sizeof(filename_char_t));

    if (res == false) {
        printf("Error, couldn't expand pattern: '%s'\n", template_path);
        abort();
    }

    int os_handle = open(filename_buffer, O_CREAT | O_WRONLY, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
    if (os_handle == -1) {
        perror("open");
        abort();
    }

    int int_res = dup2(os_handle, fileno(std_handle));
    if (int_res == -1) {
        perror("dup2");
        abort();
    }

    close(os_handle);
}
#endif
#endif

#if defined(_NUITKA_EXPERIMENTAL_SHOW_STARTUP_TIME)
static void Nuitka_at_exit(void) { NUITKA_PRINT_TIMING("Nuitka_at_exit(): Called by C exit()"); }
#endif

#if !defined(_NUITKA_DEPLOYMENT_MODE) && !defined(_NUITKA_NO_DEPLOYMENT_SEGFAULT)
#include <signal.h>
static void nuitka_segfault_handler(int sig) {
    puts("Nuitka: A segmentation fault has occurred. This is highly unusual and can");
    puts("have multiple reasons. Please check https://nuitka.net/info/segfault.html");
    puts("for solutions.");

    signal(SIGSEGV, SIG_DFL);
    raise(SIGSEGV);
}
#endif

#if _NUITKA_NATIVE_WCHAR_ARGV == 1
extern wchar_t const *getBinaryFilenameWideChars(bool resolve_symlinks);
#else
extern char const *getBinaryFilenameHostEncoded(bool resolve_symlinks);
#endif

// No longer in header files, but still usable.
#if PYTHON_VERSION >= 0x3d0
PyAPI_FUNC(void) PySys_AddWarnOption(const wchar_t *s);
#endif

// Preserve and provide the original argv[0] as recorded by the bootstrap stage.
static environment_char_t const *original_argv0 = NULL;

PyObject *getOriginalArgv0Object(void) {
    assert(original_argv0 != NULL);
    return Nuitka_String_FromFilename(original_argv0);
}

#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, wchar_t *lpCmdLine, int nCmdShow) {
    /* MSVC, MINGW64 */
    int argc = __argc;
    wchar_t **argv = __wargv;
#else
#if defined(_WIN32)
int wmain(int argc, wchar_t **argv) {
#if defined(_NUITKA_HIDE_CONSOLE_WINDOW)
    hideConsoleIfSpawned();
#endif
#else
int main(int argc, char **argv) {
#endif
#endif

    // Installer a segfault handler that outputs a helpful message.
#if !defined(_NUITKA_DEPLOYMENT_MODE) && !defined(_NUITKA_NO_DEPLOYMENT_SEGFAULT)
    signal(SIGSEGV, nuitka_segfault_handler);
#endif

#ifdef _NUITKA_EXPERIMENTAL_DUMP_C_TRACEBACKS
    INIT_C_BACKTRACES();
    DUMP_C_BACKTRACE();
#endif
    // Trace when the process exits.
#if defined(_NUITKA_EXPERIMENTAL_SHOW_STARTUP_TIME)
    atexit(Nuitka_at_exit);
#endif

    // Attach to the parent console respecting redirection only, otherwise we
    // cannot even output traces.
#if defined(_WIN32) && defined(_NUITKA_ATTACH_CONSOLE_WINDOW)
    inheritAttachedConsole();
#endif

    // Set up stdout/stderr according to user specification.
#if NUITKA_STANDARD_HANDLES_EARLY == 1
#if defined(NUITKA_FORCED_STDOUT_PATH)
#ifdef _WIN32
    changeStandardHandleTarget(STD_OUTPUT_HANDLE, stdout, L"" NUITKA_FORCED_STDOUT_PATH);
#else
    changeStandardHandleTarget(stdout, NUITKA_FORCED_STDOUT_PATH);
#endif
#endif
#if defined(NUITKA_FORCED_STDERR_PATH)
#ifdef _WIN32
    changeStandardHandleTarget(STD_ERROR_HANDLE, stderr, L"" NUITKA_FORCED_STDERR_PATH);
#else
    changeStandardHandleTarget(stderr, NUITKA_FORCED_STDERR_PATH);
#endif
#endif
#if defined(NUITKA_FORCED_STDIN_PATH)
#ifdef _WIN32
    changeStandardHandleTarget(STD_INPUT_HANDLE, stdin, L"" NUITKA_FORCED_STDIN_PATH);
#else
    changeStandardHandleTarget(stdin, NUITKA_FORCED_STDIN_PATH);
#endif
#endif
#endif

#if SYSFLAG_UNBUFFERED == 1
    setbuf(stdin, (char *)NULL);
    setbuf(stdout, (char *)NULL);
    setbuf(stderr, (char *)NULL);

#if PYTHON_VERSION >= 0x300
    // spell-checker: ignore PYTHONUNBUFFERED

    environment_char_t const *old_env_unbuffered = getEnvironmentVariable("PYTHONUNBUFFERED");
    setEnvironmentVariable("PYTHONUNBUFFERED", makeEnvironmentLiteral("1"));
#endif
#endif

    NUITKA_PRINT_TIMING("main(): Entered.");
    NUITKA_INIT_PROGRAM_EARLY(argc, argv);

#ifdef __FreeBSD__
    // FP exceptions run in "no stop" mode by default
    // spell-checker: ignore fpgetmask,fpsetmask

    fp_except_t m;

    m = fpgetmask();
    fpsetmask(m & ~FP_X_OFL);
#endif

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TIMING("main(): Prepare standalone environment.");
    prepareStandaloneEnvironment();
#endif

#if _NUITKA_FROZEN > 0
    NUITKA_PRINT_TIMING("main(): Preparing frozen modules.");
    prepareFrozenModules();
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
    Py_DontWriteBytecodeFlag = SYSFLAG_DONTWRITEBYTECODE;
    Py_NoUserSiteDirectory = SYSFLAG_NO_SITE;
    Py_IgnoreEnvironmentFlag = 0;
    Py_VerboseFlag = SYSFLAG_VERBOSE;
    Py_BytesWarningFlag = SYSFLAG_BYTES_WARNING;
#if PYTHON_VERSION >= 0x300 && SYSFLAG_UNBUFFERED == 1
    Py_UnbufferedStdioFlag = SYSFLAG_UNBUFFERED;
#endif
#if SYSFLAG_NO_RANDOMIZATION == 1
    Py_HashRandomizationFlag = 0;
#if PYTHON_VERSION < 0x300
    // For Python2 this is all it takes to have static hashes.
    _PyRandom_Init();
#endif
#endif
#if PYTHON_VERSION >= 0x370
    Py_UTF8Mode = SYSFLAG_UTF8;

    if (Py_UTF8Mode) {
        if (Py_FileSystemDefaultEncoding == NULL) {
            Py_FileSystemDefaultEncoding = "utf-8";
            Py_HasFileSystemDefaultEncoding = 1;
        }
    }
#endif

#ifdef NUITKA_PYTHON_STATIC
    NUITKA_PRINT_TIMING("main(): Preparing static modules.");
    Py_InitStaticModules();
#endif

    /* This suppresses warnings from getpath.c */
    Py_FrozenFlag = 1;

    /* We want to import the site module, but only after we finished our own
     * setup. The site module import will be the first thing, the main module
     * does.
     */
    Py_NoSiteFlag = 1;

    /* Initial command line handling only. */

// Make sure, we use the absolute program path for argv[0]
#if !defined(_NUITKA_ONEFILE_MODE) && _NUITKA_NATIVE_WCHAR_ARGV == 0
    original_argv0 = argv[0];
    argv[0] = (char *)getBinaryFilenameHostEncoded(false);
#endif

#if defined(_NUITKA_ONEFILE_MODE)
    {
        environment_char_t const *parent_original_argv0 = getEnvironmentVariable("NUITKA_ORIGINAL_ARGV0");

        if (parent_original_argv0 != NULL) {
            original_argv0 = strdupFilename(parent_original_argv0);

            unsetEnvironmentVariable("NUITKA_ORIGINAL_ARGV0");
        }
    }
#endif

#if PYTHON_VERSION >= 0x300 && _NUITKA_NATIVE_WCHAR_ARGV == 0
    NUITKA_PRINT_TRACE("main(): Calling convertCommandLineParameters.");
    orig_argv = convertCommandLineParameters(argc, argv);
#elif PYTHON_VERSION < 0x300 && _NUITKA_NATIVE_WCHAR_ARGV == 1
    NUITKA_PRINT_TRACE("main(): Calling getCommandLineToArgvA.");
    orig_argv = getCommandLineToArgvA(GetCommandLineA());
#else
orig_argv = argv;
#endif

// Make sure, we use the absolute program path for argv[0]
#if !defined(_NUITKA_ONEFILE_MODE) && _NUITKA_NATIVE_WCHAR_ARGV == 1
    original_argv0 = argv[0];
#if PYTHON_VERSION >= 0x300
    orig_argv[0] = (wchar_t *)getBinaryFilenameWideChars(false);
#endif
#endif

    // Make sure the compiled path of Python is replaced.
    Py_SetProgramName(orig_argv[0]);

    orig_argc = argc;

    // Early command line parsing.
    NUITKA_PRINT_TRACE("main(): Calling setCommandLineParameters.");
    setCommandLineParameters(argc, argv);

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
    environment_char_t const *old_env_hash_seed = getEnvironmentVariable("PYTHONHASHSEED");
    setEnvironmentVariable("PYTHONHASHSEED", makeEnvironmentLiteral("0"));
#endif

    /* Disable CPython warnings if requested to. */
#if NO_PYTHON_WARNINGS
    NUITKA_PRINT_TRACE("main(): Disabling Python warnings.");
    {
#if PYTHON_VERSION >= 0x300
        wchar_t ignore[] = L"ignore";
#else
        char ignore[] = "ignore";
#endif

        PySys_ResetWarnOptions();
        PySys_AddWarnOption(ignore);
    }
#endif

// Workaround older Python not handling stream setup on redirected files properly.
#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x380
    {
        char const *encoding = NULL;

        if (SYSFLAG_UTF8) {
            encoding = "utf-8";
        } else {
            encoding = getenv("PYTHONIOENCODING");
            if (encoding == NULL) {
                encoding = "utf-8";
            }
        }

        Py_SetStandardStreamEncoding(encoding, NULL);
    }
#endif

    /* Initialize the embedded CPython interpreter. */
    NUITKA_PRINT_TIMING("main(): Calling Nuitka_Py_Initialize to initialize interpreter.");
    Nuitka_Py_Initialize();

    PyThreadState *tstate = PyThreadState_GET();

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TRACE("main(): Restore standalone environment.");
    restoreStandaloneEnvironment();
#else
    {
        environment_char_t const *python_path_cstr = getEnvironmentVariable("NUITKA_PYTHONPATH");

        if (python_path_cstr != NULL) {
            PyObject *python_path_str = Nuitka_String_FromFilename(python_path_cstr);
#ifdef _WIN32
            PyObject *python_path_list = PyObject_CallMethod(python_path_str, (char *)"split", (char *)"s", ";");
#else
            PyObject *python_path_list = PyObject_CallMethod(python_path_str, (char *)"split", (char *)"s", ":");
#endif
            Py_DECREF(python_path_str);

            PySys_SetObject("path", python_path_list);

            unsetEnvironmentVariable("NUITKA_PYTHONPATH");
        }
    }
#endif

    /* Lie about it, believe it or not, there are "site" files, that check
     * against later imports, see below.
     */
    Py_NoSiteFlag = SYSFLAG_NO_SITE;

    /* Set the command line parameters for run time usage. */
    PySys_SetArgv(argc, orig_argv);
// Empty "sys.path" again, the above adds program directory to it.
#if SYSFLAG_ISOLATED
    Nuitka_SysSetObject("path", PyList_New(0));
#endif

    /* Initialize the built-in module tricks used and builtin-type methods */
    NUITKA_PRINT_TRACE("main(): Calling _initBuiltinModule().");
    _initBuiltinModule();

    /* Initialize the Python constant values used. This also sets
     * "sys.executable" while at it.
     */
    NUITKA_PRINT_TIMING("main(): Calling createGlobalConstants().");
    createGlobalConstants(tstate);
    NUITKA_PRINT_TIMING("main(): Returned createGlobalConstants().");

    /* Complex call helpers need "__main__" constants, even if we only
     * go into "__parents__main__" module as a start point.
     */
    NUITKA_PRINT_TIMING("main(): Calling createMainModuleConstants().");
    createMainModuleConstants(tstate);
    NUITKA_PRINT_TIMING("main(): Returned createMainModuleConstants().");

    NUITKA_PRINT_TRACE("main(): Calling _initBuiltinOriginalValues().");
    _initBuiltinOriginalValues();

    /* Revert the wrong "sys.flags" value, it's used by "site" on at least
     * Debian for Python 3.3, more uses may exist.
     */
#if SYSFLAG_NO_SITE == 0
#if PYTHON_VERSION < 0x300
    PyStructSequence_SET_ITEM(Nuitka_SysGetObject("flags"), 9, const_int_0);
#else
    PyStructSequence_SetItem(Nuitka_SysGetObject("flags"), 6, const_int_0);
#endif
#endif

    /* Initialize the compiled types of Nuitka. */
    _initCompiledCellType();
    _initCompiledGeneratorType();
    _initCompiledFunctionType();
    _initCompiledMethodType();
    _initCompiledFrameType();

    _initSlotCompare();
#if PYTHON_VERSION >= 0x270
    _initSlotIterNext();
#endif

    NUITKA_PRINT_TRACE("main(): Calling enhancePythonTypes().");
    enhancePythonTypes();

    NUITKA_PRINT_TRACE("main(): Calling patchTypeComparison().");
    patchTypeComparison();

    NUITKA_PRINT_TRACE("main(): Calling patchTracebackDealloc().");
    patchTracebackDealloc();

#ifndef NUITKA_USE_PYCORE_THREAD_STATE
    /* Allow to override the ticker value, to remove checks for threads in
     * CPython core from impact on benchmarks. */
    char const *ticker_value = getenv("NUITKA_TICKER");
    if (ticker_value != NULL) {
        _Py_Ticker = atoi(ticker_value);
        assert(_Py_Ticker >= 20);
    }
#endif

#if defined(_WIN32) && defined(_NUITKA_ATTACH_CONSOLE_WINDOW)
    if (needs_stdout_attaching) {
        PyObject *filename = Nuitka_String_FromString("CONOUT$");
        // This defaults to "utf-8" internally. We may add an argument of use
        // platform ones in the future.
        PyObject *encoding = NULL;

        PyObject *stdout_file = BUILTIN_OPEN_SIMPLE(tstate, filename, "w", SYSFLAG_UNBUFFERED != 1, encoding);
        if (unlikely(stdout_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        Py_DECREF(filename);

        Nuitka_SysSetObject("stdout", stdout_file);
    }

    if (needs_stderr_attaching) {
        PyObject *filename = Nuitka_String_FromString("CONOUT$");
        // This defaults to "utf-8" internally. We may add an argument of use
        // platform ones in the future.
        PyObject *encoding = NULL;

        PyObject *stderr_file = BUILTIN_OPEN_SIMPLE(tstate, filename, "w", SYSFLAG_UNBUFFERED != 1, encoding);
        if (unlikely(stderr_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        Py_DECREF(filename);

        Nuitka_SysSetObject("stderr", stderr_file);
    }

    if (needs_stdin_attaching) {
        PyObject *filename = Nuitka_String_FromString("CONIN$");
        // This defaults to "utf-8" internally. We may add an argument of use
        // platform ones in the future.
        PyObject *encoding = NULL;

        // CPython core requires stdin to be buffered due to methods usage, and it won't matter
        // here much.
        PyObject *stdin_file = BUILTIN_OPEN_SIMPLE(tstate, filename, "r", true, encoding);

        Py_DECREF(filename);

        Nuitka_SysSetObject("stdin", stdin_file);
    }
#endif

    NUITKA_PRINT_TRACE("main(): Setting Python input/output handles.");
    setInputOutputHandles(tstate);

#ifdef _NUITKA_STANDALONE

#if PYTHON_VERSION >= 0x300
    // Make sure the importlib fully bootstraps as we couldn't load it with the
    // standard loader.
    {
        NUITKA_MAY_BE_UNUSED PyObject *importlib_module = getImportLibBootstrapModule();
        CHECK_OBJECT(importlib_module);
    }
#endif

    NUITKA_PRINT_TRACE("main(): Calling setEarlyFrozenModulesFileAttribute().");

    setEarlyFrozenModulesFileAttribute(tstate);
#endif

#if _NUITKA_FROZEN > 0
    NUITKA_PRINT_TRACE("main(): Removing early frozen module table again.");
    PyImport_FrozenModules = old_frozen;
#endif

    NUITKA_PRINT_TRACE("main(): Calling setupMetaPathBasedLoader().");
    /* Enable meta path based loader. */
    setupMetaPathBasedLoader(tstate);

#if PYTHON_VERSION < 0x3d0
    /* Initialize warnings module. */
    _PyWarnings_Init();
#endif

#if NO_PYTHON_WARNINGS && PYTHON_VERSION >= 0x342 && PYTHON_VERSION < 0x3a0 && defined(_NUITKA_FULL_COMPAT)
    // For full compatibility bump the warnings registry version,
    // otherwise modules "__warningregistry__" will mismatch.
    PyObject *warnings_module = PyImport_ImportModule("warnings");
    PyObject *meth = PyObject_GetAttrString(warnings_module, "_filters_mutated");

    CALL_FUNCTION_NO_ARGS(tstate, meth);
#if PYTHON_VERSION < 0x380
    // Two times, so "__warningregistry__" version matches.
    CALL_FUNCTION_NO_ARGS(tstate, meth);
#endif
#endif

#if PYTHON_VERSION >= 0x300
    NUITKA_PRINT_TRACE("main(): Calling patchInspectModule().");

// TODO: Python3.13 NoGIL: This is causing errors during bytecode import
// that are unexplained.
#if !defined(Py_GIL_DISABLED)
    patchInspectModule(tstate);
#endif
#endif

#if PYTHON_VERSION >= 0x300 && SYSFLAG_NO_RANDOMIZATION == 1
    NUITKA_PRINT_TRACE("main(): Reverting to initial 'PYTHONHASHSEED' value.");
    undoEnvironmentVariable(tstate, "PYTHONHASHSEED", old_env_hash_seed);
#endif

#if PYTHON_VERSION >= 0x300 && SYSFLAG_UNBUFFERED == 1
    NUITKA_PRINT_TRACE("main(): Reverting to initial 'PYTHONUNBUFFERED' value.");
    undoEnvironmentVariable(tstate, "PYTHONUNBUFFERED", old_env_unbuffered);
#endif

#ifdef _NUITKA_STANDALONE
    // Restore the PATH, so the program can use it.
    NUITKA_PRINT_TRACE("main(): Reverting to initial 'PATH' value.");
    undoEnvironmentVariable(tstate, "PATH", old_env_path);
    undoEnvironmentVariable(tstate, "PYTHONHOME", old_env_pythonhome);
#endif

#if _NUITKA_PROFILE
    // Profiling with "vmprof" if enabled.
    startProfiling();
#endif

#if _NUITKA_PGO_PYTHON
    // Profiling with our own Python PGO if enabled.
    PGO_Initialize();
#endif

    // Execute the main module unless plugins want to do something else. In case
    // of multiprocessing making a fork on Windows, we should execute
    // "__parents_main__" instead. And for Windows Service we call the plugin C
    // code to call us back to launch main code in a callback.
#ifdef _NUITKA_PLUGIN_MULTIPROCESSING_ENABLED
    if (unlikely(is_multiprocessing_fork)) {
        NUITKA_PRINT_TRACE("main(): Calling __parents_main__.");
        EXECUTE_MAIN_MODULE(tstate, "__parents_main__", false);

        int exit_code = HANDLE_PROGRAM_EXIT(tstate);

        NUITKA_PRINT_TRACE("main(): Calling __parents_main__ Py_Exit.");
        Py_Exit(exit_code);
#if defined(_WIN32)
    } else if (unlikely(is_joblib_popen_loky_win32)) {
        NUITKA_PRINT_TRACE("main(): Calling joblib.externals.loky.backend.popen_loky_win32.");
        PyObject *joblib_popen_loky_win32_module =
            EXECUTE_MAIN_MODULE(tstate, "joblib.externals.loky.backend.popen_loky_win32", true);

        // Remove the "-c" and options part like CPython would do as well.
        PyObject *argv_list = Nuitka_SysGetObject("argv");
        Py_ssize_t size = PyList_Size(argv_list);

        // Negative indexes are not supported by this function.
        int res = PyList_SetSlice(argv_list, 1, size - 2, const_tuple_empty);
        assert(res == 0);

        PyObject *main_function = PyObject_GetAttrString(joblib_popen_loky_win32_module, "main");
        CHECK_OBJECT(main_function);

        if (loky_joblib_pipe_handle_arg == 0) {
            CALL_FUNCTION_NO_ARGS(tstate, main_function);
        } else {
            char const *kw_keys[] = {"pipe_handle", "parent_pid"};
            PyObject *kw_values[] = {
                Nuitka_PyLong_FromLong(loky_joblib_pipe_handle_arg),
                Nuitka_PyLong_FromLong(loky_joblib_parent_pid_arg),
            };

            PyObject *kw_args = MAKE_DICT_X_CSTR(kw_keys, kw_values, sizeof(kw_values) / sizeof(PyObject *));

            CALL_FUNCTION_WITH_KW_ARGS(tstate, main_function, kw_args);
        }

        int exit_code = HANDLE_PROGRAM_EXIT(tstate);

        NUITKA_PRINT_TRACE("main(): Calling 'joblib.externals.loky.backend.popen_loky_posix' Py_Exit.");
        Py_Exit(exit_code);
#else
    } else if (unlikely(is_joblib_popen_loky_posix)) {
        NUITKA_PRINT_TRACE("main(): Calling joblib.externals.loky.backend.popen_loky_posix.");
        PyObject *joblib_popen_loky_posix_module =
            EXECUTE_MAIN_MODULE(tstate, "joblib.externals.loky.backend.popen_loky_posix", true);

        // Remove the "-m" like CPython would do as well.
        int res = PyList_SetSlice(Nuitka_SysGetObject("argv"), 0, 2, const_tuple_empty);
        assert(res == 0);

        PyObject *main_function = PyObject_GetAttrString(joblib_popen_loky_posix_module, "main");
        CHECK_OBJECT(main_function);

        CALL_FUNCTION_NO_ARGS(tstate, main_function);

        int exit_code = HANDLE_PROGRAM_EXIT(tstate);

        NUITKA_PRINT_TRACE("main(): Calling 'joblib.externals.loky.backend.popen_loky_posix' Py_Exit.");
        Py_Exit(exit_code);
#endif
    } else if (unlikely(multiprocessing_resource_tracker_arg != -1)) {
        NUITKA_PRINT_TRACE("main(): Launching as 'multiprocessing.resource_tracker'.");
        PyObject *resource_tracker_module = EXECUTE_MAIN_MODULE(tstate, "multiprocessing.resource_tracker", true);

        PyObject *main_function = PyObject_GetAttrString(resource_tracker_module, "main");
        CHECK_OBJECT(main_function);

        CALL_FUNCTION_WITH_SINGLE_ARG(tstate, main_function,
                                      Nuitka_PyInt_FromLong(multiprocessing_resource_tracker_arg));

        int exit_code = HANDLE_PROGRAM_EXIT(tstate);

        NUITKA_PRINT_TRACE("main(): Calling 'multiprocessing.resource_tracker' Py_Exit.");
        Py_Exit(exit_code);
    } else if (unlikely(loky_resource_tracker_arg != -1)) {
        NUITKA_PRINT_TRACE("main(): Launching as 'joblib.externals.loky.backend.resource_tracker'.");
        PyObject *resource_tracker_module =
            EXECUTE_MAIN_MODULE(tstate, "joblib.externals.loky.backend.resource_tracker", true);
        CHECK_OBJECT(resource_tracker_module);

        PyObject *main_function = PyObject_GetAttrString(resource_tracker_module, "main");
        CHECK_OBJECT(main_function);

        CALL_FUNCTION_WITH_SINGLE_ARG(tstate, main_function, Nuitka_PyInt_FromLong(loky_resource_tracker_arg));

        int exit_code = HANDLE_PROGRAM_EXIT(tstate);

        NUITKA_PRINT_TRACE("main(): Calling 'joblib.externals.loky.backend.resource_tracker' Py_Exit.");
        Py_Exit(exit_code);
    } else if (unlikely(is_anyio_to_process)) {
        PyObject *anyio_module = EXECUTE_MAIN_MODULE(tstate, "anyio.to_process", false);

        PyObject *main_function = PyObject_GetAttrString(anyio_module, "process_worker");
        CHECK_OBJECT(main_function);

        CALL_FUNCTION_NO_ARGS(tstate, main_function);

        int exit_code = HANDLE_PROGRAM_EXIT(tstate);

        NUITKA_PRINT_TRACE("main(): Calling 'anyio.to_process' Py_Exit.");
        Py_Exit(exit_code);
    } else {
#endif
#if defined(_NUITKA_ONEFILE_MODE) && defined(_WIN32)
        {
            char buffer[128] = {0};
            DWORD size = GetEnvironmentVariableA("NUITKA_ONEFILE_PARENT", buffer, sizeof(buffer));

            if (size > 0 && size < 127) {
                onefile_ppid = atol(buffer);

                CreateThread(NULL, 0, doOnefileParentMonitoring, NULL, 0, NULL);
            }
        }
#endif
        PyDict_DelItemString(Nuitka_GetSysModules(), NUITKA_MAIN_MODULE_NAME);
        DROP_ERROR_OCCURRED(tstate);

#if _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
        NUITKA_PRINT_TRACE("main(): Calling plugin SvcLaunchService() entry point.");
        SvcLaunchService();
#else
    /* Execute the "__main__" module. */
    NUITKA_PRINT_TIMING("main(): Calling " NUITKA_MAIN_MODULE_NAME ".");
    EXECUTE_MAIN_MODULE(tstate, NUITKA_MAIN_MODULE_NAME, NUITKA_MAIN_IS_PACKAGE_BOOL);
    NUITKA_PRINT_TIMING("main(): Exited from " NUITKA_MAIN_MODULE_NAME ".");

#endif
#ifdef _NUITKA_PLUGIN_MULTIPROCESSING_ENABLED
    }
#endif

#if _NUITKA_PROFILE
    stopProfiling();
#endif

#if _NUITKA_PGO_PYTHON
    // Write out profiling with our own Python PGO if enabled.
    PGO_Finalize();
#endif

#ifndef __NUITKA_NO_ASSERT__
    checkGlobalConstants();

    /* TODO: Walk over all loaded compiled modules, and make this kind of checks. */
#if !NUITKA_MAIN_IS_PACKAGE_BOOL
    checkModuleConstants___main__(tstate);
#endif

#endif

    int exit_code = HANDLE_PROGRAM_EXIT(tstate);

    NUITKA_PRINT_TIMING("main(): Calling Py_Exit.");
    Py_Exit(exit_code);

    // The "Py_Exit()" calls is not supposed to return.
    NUITKA_CANNOT_GET_HERE("Py_Exit does not return");
}

/* This is an unofficial API, not available on Windows, but on Linux and others
 * it is exported, and has been used by some code.
 */
#if !defined(_WIN32) && !defined(__MSYS__)
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

    *argv = orig_argv;
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

#if defined(__linux__)
__attribute__((weak))
__attribute__((visibility("default")))
#endif
#if PYTHON_VERSION >= 0x300
int Py_Main(int argc, wchar_t **argv) {
    return 0;
}
#else
int Py_Main(int argc, char **argv) { return 0; }
#endif
#ifdef __cplusplus
}
#endif
#endif

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
