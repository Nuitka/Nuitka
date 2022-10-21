//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
#define SYSFLAG_UNBUFFERED 0
#endif

#ifndef NUITKA_MAIN_MODULE_NAME
#define NUITKA_MAIN_MODULE_NAME "__main__"
#endif

extern PyCodeObject *codeobj_main;

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
#if PYTHON_VERSION < 0x340
static struct _frozen *old_frozen = NULL;
#else
static struct _frozen const *old_frozen = NULL;
#endif

static void prepareFrozenModules(void) {
    // Tell the CPython library to use our pre-compiled modules as frozen
    // modules. This for those modules/packages like "encoding" that will be
    // loaded during "Py_Initialize" already, for the others they may be
    // compiled.

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
}
#endif

#ifdef _NUITKA_STANDALONE

static void prepareStandaloneEnvironment(void) {

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

static void restoreStandaloneEnvironment(void) {
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
    argv_copy = (wchar_t **)PyMem_Malloc(sizeof(wchar_t *) * argc);

    // Temporarily disable locale for conversions to not use it.
    char *old_locale = strdup(setlocale(LC_ALL, NULL));
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

    setlocale(LC_ALL, old_locale);
    free(old_locale);

    return argv_copy;
}
#endif

static int HANDLE_PROGRAM_EXIT(void) {
    int exit_code;

    if (ERROR_OCCURRED()) {
#if PYTHON_VERSION >= 0x300
        /* Remove the frozen importlib traceback part, which would not be compatible. */
        PyThreadState *thread_state = PyThreadState_GET();

        while (thread_state->curexc_traceback) {
            PyTracebackObject *tb = (PyTracebackObject *)thread_state->curexc_traceback;
            PyFrameObject *frame = tb->tb_frame;

            if (0 ==
                strcmp(PyUnicode_AsUTF8(Nuitka_FrameGetCode(frame)->co_filename), "<frozen importlib._bootstrap>")) {
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

    return exit_code;
}

static PyObject *EXECUTE_MAIN_MODULE(char const *module_name) {
    NUITKA_INIT_PROGRAM_LATE(module_name);

#if NUITKA_MAIN_PACKAGE_MODE
    {
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

            PyObject *result = IMPORT_EMBEDDED_MODULE(buffer);

            if (ERROR_OCCURRED()) {
                return result;
            }
        }
    }
#endif

    return IMPORT_EMBEDDED_MODULE(module_name);
}

#ifdef _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
extern void SvcInstall();
extern void SvcLaunchService();

// Callback from Windows Service logic.
DWORD WINAPI SvcStartPython(LPVOID lpParam) {
    if (lpParam == NULL) {
        EXECUTE_MAIN_MODULE(NUITKA_MAIN_MODULE_NAME);

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

// This is a multiprocessing fork
static bool is_multiprocessing_fork = false;
// This is a multiprocessing resource tracker.
static PyObject *multiprocessing_resource_tracker_arg = NULL;

// Parse the command line parameters and provide it to "sys" built-in module,
// as well as decide if it's a multiprocessing usage.
#if _NUITKA_NATIVE_WCHAR_ARGV == 0
static void setCommandLineParameters(int argc, char **argv, bool initial) {
#else
static void setCommandLineParameters(int argc, wchar_t **argv, bool initial) {
#endif
    if (initial) {
        /* We might need to handle special parameters from plugins that are
           very deeply woven into command line handling. These are right now
           multiprocessing, which indicates that it's forking via extra
           command line argument. And Windows Service indicates need to
           install and exit here too.
         */
        for (int i = 1; i < argc; i++) {
#if _NUITKA_NATIVE_WCHAR_ARGV == 0
            if ((strcmp(argv[i], "--multiprocessing-fork")) == 0 && (i + 1 < argc))
#else
            if ((wcscmp(argv[i], L"--multiprocessing-fork")) == 0 && (i + 1 < argc))
#endif
            {
                is_multiprocessing_fork = true;
                break;
            }

#if _NUITKA_NATIVE_WCHAR_ARGV == 0
            if ((strcmp(argv[i], "--multiprocessing-resource-tracker")) == 0 && (i + 1 < argc))
#else
            if ((wcscmp(argv[i], L"--multiprocessing-resource-tracker")) == 0 && (i + 1 < argc))
#endif
            {
#if _NUITKA_NATIVE_WCHAR_ARGV == 0
                multiprocessing_resource_tracker_arg = PyInt_FromLong(atoi(argv[i + 1]));
#else
                multiprocessing_resource_tracker_arg = PyLong_FromLong(_wtoi(argv[i + 1]));
#endif
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
}

#if defined(_WIN32) && PYTHON_VERSION >= 0x300 && (SYSFLAG_NO_RANDOMIZATION == 1 || SYSFLAG_UNBUFFERED == 1)
static void setenv(char const *name, char const *value, int overwrite) {
    assert(overwrite);

    SetEnvironmentVariableA(name, value);
}

static void unsetenv(char const *name) { SetEnvironmentVariableA(name, NULL); }
#endif

#if _DEBUG_REFCOUNTS
static void PRINT_REFCOUNTS(void) {
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

#if PYTHON_VERSION >= 0x300 && (SYSFLAG_NO_RANDOMIZATION == 1 || SYSFLAG_UNBUFFERED == 1)
static void undoEnvironmentVariable(char const *variable_name, char const *old_value) {
    if (old_value) {
        setenv(variable_name, old_value, 1);

        PyObject *env_value = PyUnicode_FromString(old_value);
        PyObject *variable_name_str = PyUnicode_FromString(variable_name);

        int res = PyDict_SetItem(PyObject_GetAttrString(PyImport_ImportModule("os"), "environ"), variable_name_str,
                                 env_value);
        assert(res == 0);

        Py_DECREF(env_value);
        Py_DECREF(variable_name_str);
    } else {
        unsetenv(variable_name);

        int res =
            PyDict_DelItemString(PyObject_GetAttrString(PyImport_ImportModule("os"), "environ"), (char *)variable_name);
        assert(res == 0);
    }
}
#endif

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
static PyObject *getExpandedTemplatePath(char const *template) {
    char filename_buffer[1024];
    bool res = expandTemplatePath(filename_buffer, template, sizeof(filename_buffer));

    if (res == false) {
        printf("Error, couldn't expand pattern: %s\n", template);
        abort();
    }

    return Nuitka_String_FromString(filename_buffer);
}
#endif
#endif

#ifdef _WIN32
static void setStdFileHandleNumber(DWORD std_handle_id, PyObject *file_handle) {
    PyObject *file_no_value = CALL_METHOD_NO_ARGS(file_handle, const_str_plain_fileno);

    if (unlikely(file_no_value == NULL)) {
        DROP_ERROR_OCCURRED();
        return;
    }

    long file_number = PyLong_AsLong(file_no_value);

    Py_DECREF(file_no_value);

    if (unlikely(file_number == -1 && ERROR_OCCURRED())) {
        DROP_ERROR_OCCURRED();
        return;
    }

    // Casting from long to handle gives warnings if not using a suitable
    // sized integer type in between.
    if (std_handle_id != STD_INPUT_HANDLE) {
        SetStdHandle(std_handle_id, (HANDLE)(intptr_t)file_number);
    }
}
#endif

static void setInputOutputHandles(void) {
    /* At least on Windows, we support disabling the console via linker flag, but now
       need to provide the NUL standard file handles manually in this case. */
#if defined(_WIN32) && PYTHON_VERSION >= 0x300
    PyObject *encoding = Nuitka_String_FromString("utf-8");
#else
    PyObject *encoding = NULL;
#endif

    {
        PyObject *nul_filename = Nuitka_String_FromString("NUL:");

        PyObject *sys_stdin = Nuitka_SysGetObject("stdin");
        if (sys_stdin == NULL || sys_stdin == Py_None) {
            // CPython core requires stdin to be buffered due to methods usage, and it won't matter
            // here much.
            PyObject *stdin_file = BUILTIN_OPEN_SIMPLE(nul_filename, "r", true, encoding);

            CHECK_OBJECT(stdin_file);
            Nuitka_SysSetObject("stdin", stdin_file);

#ifdef _WIN32
            setStdFileHandleNumber(STD_INPUT_HANDLE, stdin_file);
#endif
        }

        PyObject *sys_stdout = Nuitka_SysGetObject("stdout");
        if (sys_stdout == NULL || sys_stdout == Py_None) {
            PyObject *stdout_file = BUILTIN_OPEN_SIMPLE(nul_filename, "w", false, encoding);

            CHECK_OBJECT(stdout_file);
            Nuitka_SysSetObject("stdout", stdout_file);

#ifdef _WIN32
            setStdFileHandleNumber(STD_OUTPUT_HANDLE, stdout_file);
#endif
        }

        PyObject *sys_stderr = Nuitka_SysGetObject("stderr");
        if (sys_stderr == NULL || sys_stderr == Py_None) {
            PyObject *stderr_file = BUILTIN_OPEN_SIMPLE(nul_filename, "w", false, encoding);

            CHECK_OBJECT(stderr_file);

            Nuitka_SysSetObject("stderr", stderr_file);

#ifdef _WIN32
            setStdFileHandleNumber(STD_ERROR_HANDLE, stderr_file);
#endif
        }

        Py_DECREF(nul_filename);
    }

#if defined(NUITKA_FORCED_STDOUT_PATH)
    {
#ifdef _WIN32
        PyObject *filename = getExpandedTemplatePath(L"" NUITKA_FORCED_STDOUT_PATH);
#else
        PyObject *filename = getExpandedTemplatePath(NUITKA_FORCED_STDOUT_PATH);
#endif
        PyObject *stdout_file = BUILTIN_OPEN_SIMPLE(filename, "w", SYSFLAG_UNBUFFERED != 1, encoding);
        if (unlikely(stdout_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        Nuitka_SysSetObject("stdout", stdout_file);

#ifdef _WIN32
        setStdFileHandleNumber(STD_OUTPUT_HANDLE, stdout_file);
#endif
    }
#endif

#if defined(NUITKA_FORCED_STDERR_PATH)
    {
#ifdef _WIN32
        PyObject *filename = getExpandedTemplatePath(L"" NUITKA_FORCED_STDERR_PATH);
#else
        PyObject *filename = getExpandedTemplatePath(NUITKA_FORCED_STDERR_PATH);
#endif
        PyObject *stderr_file = BUILTIN_OPEN_SIMPLE(filename, "w", false, encoding);
        if (unlikely(stderr_file == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        Nuitka_SysSetObject("stderr", stderr_file);

#ifdef _WIN32
        setStdFileHandleNumber(STD_ERROR_HANDLE, stderr_file);
#endif
    }
#endif

    Py_XDECREF(encoding);
}

#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, wchar_t *lpCmdLine, int nCmdShow) {
    /* MSVC, MINGW64 */
    int argc = __argc;
    wchar_t **argv = __wargv;
#else
#if defined(_WIN32)
int wmain(int argc, wchar_t **argv) {
#else
int main(int argc, char **argv) {
#endif
#endif
    NUITKA_PRINT_TIMING("main(): Entered.");
    NUITKA_INIT_PROGRAM_EARLY(argc, argv);

#if SYSFLAG_UNBUFFERED == 1
    setbuf(stdin, (char *)NULL);
    setbuf(stdout, (char *)NULL);
    setbuf(stderr, (char *)NULL);

#if PYTHON_VERSION >= 0x300
    char const *old_env_unbuffered = getenv("PYTHONUNBUFFERED");
    setenv("PYTHONUNBUFFERED", "1", 1);
#endif
#endif

#ifdef __FreeBSD__
    /* FP exceptions run in "no stop" mode by default */

    fp_except_t m;

    m = fpgetmask();
    fpsetmask(m & ~FP_X_OFL);
#endif

#ifdef _NUITKA_STANDALONE
    NUITKA_PRINT_TIMING("main(): Prepare standalone environment.");
    prepareStandaloneEnvironment();
#else

#endif

#if _NUITKA_FROZEN > 0
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
    Py_DontWriteBytecodeFlag = 0;
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

#if PYTHON_VERSION >= 0x300 && _NUITKA_NATIVE_WCHAR_ARGV == 0
    NUITKA_PRINT_TRACE("main(): Calling convertCommandLineParameters.");
    orig_argv = convertCommandLineParameters(argc, argv);
#elif PYTHON_VERSION < 0x300 && _NUITKA_NATIVE_WCHAR_ARGV == 1
    orig_argv = getCommandLineToArgvA(GetCommandLineA());
#else
orig_argv = argv;
#endif
    orig_argc = argc;

    NUITKA_PRINT_TRACE("main(): Calling initial setCommandLineParameters.");

    setCommandLineParameters(argc, argv, true);

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
    char const *old_env_hash_seed = getenv("PYTHONHASHSEED");
    setenv("PYTHONHASHSEED", "0", 1);
#endif

    /* Disable CPython warnings if requested to. */
#if NO_PYTHON_WARNINGS
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
#if PYTHON_VERSION >= 0x340 && PYTHON_VERSION < 0x380
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
    NUITKA_PRINT_TIMING("main(): Calling Py_Initialize to initialize interpreter.");
    Py_Initialize();

#if PYTHON_VERSION >= 0x300 && SYSFLAG_NO_RANDOMIZATION == 1
    if (old_env_hash_seed) {
        undoEnvironmentVariable("PYTHONHASHSEED", old_env_hash_seed);
    }
#endif

#if PYTHON_VERSION >= 0x300 && SYSFLAG_UNBUFFERED == 1
    if (old_env_unbuffered) {
        undoEnvironmentVariable("PYTHONUNBUFFERED", old_env_unbuffered);
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

    setCommandLineParameters(argc, argv, false);

    PySys_SetArgv(argc, orig_argv);

    /* Initialize the built-in module tricks used and builtin-type methods */
    NUITKA_PRINT_TRACE("main(): Calling _initBuiltinModule().");
    _initBuiltinModule();

    /* Initialize the Python constant values used. This also sets
     * "sys.executable" while at it.
     */
    NUITKA_PRINT_TIMING("main(): Calling createGlobalConstants().");
    createGlobalConstants();
    NUITKA_PRINT_TIMING("main(): Returned createGlobalConstants().");

    /* Complex call helpers need "__main__" constants, even if we only
     * go into "__parents__main__" module as a start point.
     */
    NUITKA_PRINT_TIMING("main(): Calling createMainModuleConstants().");
    createMainModuleConstants();
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

#ifndef NUITKA_USE_PYCORE_THREADSTATE
    /* Allow to override the ticker value, to remove checks for threads in
     * CPython core from impact on benchmarks. */
    char const *ticker_value = getenv("NUITKA_TICKER");
    if (ticker_value != NULL) {
        _Py_Ticker = atoi(ticker_value);
        assert(_Py_Ticker >= 20);
    }
#endif

    setInputOutputHandles();

#ifdef _NUITKA_STANDALONE

#if PYTHON_VERSION >= 0x300
    // Make sure the importlib fully bootstraps as we couldn't load it with the
    // standard loader.
    PyObject *importlib_module = getImportLibBootstrapModule();
    CHECK_OBJECT(importlib_module);
#endif

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

    /* Initialize warnings module. */
    _PyWarnings_Init();

#if NO_PYTHON_WARNINGS && PYTHON_VERSION >= 0x342 && PYTHON_VERSION < 0x3a0 && defined(_NUITKA_FULL_COMPAT)
    // For full compatibility bump the warnings registry version,
    // otherwise modules "__warningsregistry__" will mismatch.
    PyObject *warnings_module = PyImport_ImportModule("warnings");
    PyObject *meth = PyObject_GetAttrString(warnings_module, "_filters_mutated");

    CALL_FUNCTION_NO_ARGS(meth);
#if PYTHON_VERSION < 0x380
    // Two times, so "__warningregistry__" version matches.
    CALL_FUNCTION_NO_ARGS(meth);
#endif
#endif

#if PYTHON_VERSION >= 0x300
    NUITKA_PRINT_TRACE("main(): Calling patchInspectModule().");
    patchInspectModule();
#endif

#if _NUITKA_PROFILE
    // Profiling with "vmprof" if enabled.
    startProfiling();
#endif

#if _NUITKA_PGO_PYTHON
    // Profiling with our own Python PGO if enabled.
    PGO_Initialize();
#endif

    /* Execute the main module unless plugins want to do something else. In case of
       multiprocessing making a fork on Windows, we should execute "__parents_main__"
       instead. And for Windows Service we call the plugin C code to call us back
       to launch main code in a callback. */
#ifdef _NUITKA_PLUGIN_MULTIPROCESSING_ENABLED
    if (unlikely(is_multiprocessing_fork)) {
        NUITKA_PRINT_TRACE("main(): Calling __parents_main__.");
        EXECUTE_MAIN_MODULE("__parents_main__");

        int exit_code = HANDLE_PROGRAM_EXIT();

        NUITKA_PRINT_TRACE("main(): Calling __parents_main__ Py_Exit.");

        // TODO: Should maybe call Py_Exit here, but there were issues with that.
        exit(exit_code);
    } else if (unlikely(multiprocessing_resource_tracker_arg != NULL)) {
        NUITKA_PRINT_TRACE("main(): Calling resource_tracker.");
        PyObject *resource_tracker_module = EXECUTE_MAIN_MODULE("multiprocessing.resource_tracker");

        PyObject *main_function = PyObject_GetAttrString(resource_tracker_module, "main");

        CALL_FUNCTION_WITH_SINGLE_ARG(main_function, multiprocessing_resource_tracker_arg);

        int exit_code = HANDLE_PROGRAM_EXIT();

        NUITKA_PRINT_TRACE("main(): Calling resource_tracker Py_Exit.");
        // TODO: Should maybe call Py_Exit here, but there were issues with that.
        exit(exit_code);
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
        PyDict_DelItemString(PyImport_GetModuleDict(), NUITKA_MAIN_MODULE_NAME);

#if _NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED
        NUITKA_PRINT_TRACE("main(): Calling plugin SvcLaunchService() entry point.");
        SvcLaunchService();
#else
    /* Execute the "__main__" module. */
    NUITKA_PRINT_TIMING("main(): Calling " NUITKA_MAIN_MODULE_NAME ".");
    EXECUTE_MAIN_MODULE(NUITKA_MAIN_MODULE_NAME);
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
#if !NUITKA_MAIN_PACKAGE_MODE
    checkModuleConstants___main__();
#endif

#endif

    int exit_code = HANDLE_PROGRAM_EXIT();

#if _DEBUG_REFCOUNTS
    PRINT_REFCOUNTS();
#endif

    NUITKA_PRINT_TIMING("main(): Calling Py_Exit.");
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

#ifdef __cplusplus
}
#endif
#endif
