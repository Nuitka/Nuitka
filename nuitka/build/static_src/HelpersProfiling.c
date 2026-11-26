//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Profiling Nuitka using "vmprof".

#if _NUITKA_PROFILE

#include <time.h>

struct timespec diff(struct timespec start, struct timespec end);

static struct timespec getTimespecDiff(struct timespec start, struct timespec end) {
    struct timespec temp;

    if ((end.tv_nsec - start.tv_nsec) < 0) {
        temp.tv_sec = end.tv_sec - start.tv_sec - 1;
        temp.tv_nsec = 1000000000 + end.tv_nsec - start.tv_nsec;
    } else {
        temp.tv_sec = end.tv_sec - start.tv_sec;
        temp.tv_nsec = end.tv_nsec - start.tv_nsec;
    }

    return temp;
}

static FILE *tempfile_profile;
static PyObject *vmprof_module;

static struct timespec time1, time2;

void startProfiling(void) {
    tempfile_profile = fopen("nuitka-performance.dat", "w+b");

    PyThreadState *tstate = PyThreadState_GET();

    // Importing "site" may be needed to locate "vmprof" on sys.path.
    PyObject *site_module = PyImport_ImportModule("site");
    if (site_module == NULL) {
        CLEAR_ERROR_OCCURRED(tstate);
    } else {
        Py_DECREF(site_module);
    }

    vmprof_module = PyImport_ImportModule("vmprof");

    if (vmprof_module == NULL) {
        PyErr_Print();
        abort();
    }

    PyObject *enable_func = PyObject_GetAttrString(vmprof_module, "enable");
    if (enable_func == NULL) {
        PyErr_Print();
        abort();
    }

    PyObject *fd_arg = Nuitka_PyInt_FromLong(fileno(tempfile_profile));
    if (fd_arg == NULL) {
        Py_DECREF(enable_func);
        PyErr_Print();
        abort();
    }

    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, enable_func, fd_arg);
    Py_DECREF(enable_func);
    Py_DECREF(fd_arg);

    if (result == NULL) {
        PyErr_Print();
        abort();
    }
    Py_DECREF(result);

    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &time1);
}

void stopProfiling(void) {
    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &time2);

    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    PyObject *disable_func = PyObject_GetAttrString(vmprof_module, "disable");
    if (disable_func == NULL) {
        CLEAR_ERROR_OCCURRED(tstate);
    } else {
        PyObject *result = CALL_FUNCTION_NO_ARGS(tstate, disable_func);
        Py_DECREF(disable_func);

        if (result == NULL) {
            CLEAR_ERROR_OCCURRED(tstate);
        } else {
            Py_DECREF(result);
        }
    }

    fclose(tempfile_profile);

    FILE *tempfile_times = fopen("nuitka-times.dat", "wb");

    struct timespec diff = getTimespecDiff(time1, time2);

    long delta_ns = diff.tv_sec * 1000000000 + diff.tv_nsec;
    fprintf(tempfile_times, "%ld\n", delta_ns);

    fclose(tempfile_times);

    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
}

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
