//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/**
 * This is responsible for collection of Nuitka Python PGO information. It writes
 * traces to files, for reuse in a future Python compilation of the same program.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static FILE *pgo_output = NULL;

// Saving space by not repeating strings.

// Allocated strings
static char const **PGO_ProbeNameMappings = NULL;
uint32_t PGO_ProbeNameMappings_size = 0;
uint32_t PGO_ProbeNameMappings_used = 0;

uint32_t PGO_getStringID(char const *str) {
    for (uint32_t i = 0; i < PGO_ProbeNameMappings_used; i++) {
        if (str == PGO_ProbeNameMappings[i]) {
            return i;
        }
    }

    if (PGO_ProbeNameMappings_used == PGO_ProbeNameMappings_size) {
        PGO_ProbeNameMappings_size += 10000;
        PGO_ProbeNameMappings = realloc(PGO_ProbeNameMappings, PGO_ProbeNameMappings_size);
    }

    PGO_ProbeNameMappings[PGO_ProbeNameMappings_used] = str;
    PGO_ProbeNameMappings_used += 1;

    return PGO_ProbeNameMappings_used - 1;
}

static void PGO_writeString(char const *value) {
    assert(pgo_output != NULL);

    uint32_t id = PGO_getStringID(value);
    fwrite(&id, sizeof(id), 1, pgo_output);
}

void PGO_Initialize(void) {
    // We expect an environment variable to guide us to where the PGO information
    // shall be written to.
    char const *output_filename = getenv("NUITKA_PGO_OUTPUT");

    if (unlikely(output_filename == NULL)) {
        NUITKA_CANNOT_GET_HERE("NUITKA_PGO_OUTPUT needs to be set");
    }

    pgo_output = fopen(output_filename, "wb");

    if (unlikely(pgo_output == NULL)) {
        fprintf(stderr, "Error, failed to open '%s' for writing.\n", output_filename);
        exit(27);
    }

    fputs("KAY.PGO", pgo_output);
    fflush(pgo_output);

    PGO_ProbeNameMappings_size = 10000;
    PGO_ProbeNameMappings = malloc(PGO_ProbeNameMappings_size * sizeof(char const *));
}

void PGO_Finalize(void) {
    PGO_writeString("END");

    assert(pgo_output != NULL);
    uint32_t offset = (uint32_t)ftell(pgo_output);

    for (uint32_t i = 0; i < PGO_ProbeNameMappings_used; i++) {
        fputs(PGO_ProbeNameMappings[i], pgo_output);
        fputc(0, pgo_output);
    }

    fwrite(&PGO_ProbeNameMappings_used, sizeof(PGO_ProbeNameMappings_used), 1, pgo_output);
    fwrite(&offset, sizeof(offset), 1, pgo_output);

    fputs("YAK.PGO", pgo_output);
    fclose(pgo_output);
}

void PGO_onProbePassed(char const *probe_str, char const *format, ...) {
    va_list args;
    va_start(args, format);

    PGO_writeString(probe_str);
    size_t len = strlen(format);
    for (size_t index = 0; index < len; ++index) {
        char character = format[index];
        switch (character) {
        case 'u': { // uint32
            uint32_t arg = va_arg(args, uint32_t);
            fwrite(&arg, sizeof(arg), 1, pgo_output);
            break;
        }

        case 's': { // const char *
            const char *arg = va_arg(args, const char *);
            PGO_writeString(arg);
            break;
        }

        case 'o': { // PyObject *
            // TODO: Error handling
            PyObject *arg = va_arg(args, PyObject *);
            CHECK_OBJECT(arg);
            PyObject *marshal = PyImport_ImportModule("marshal");
            CHECK_OBJECT(marshal);
            PyObject *dumps = PyObject_GetAttrString(marshal, "dumps");
            CHECK_OBJECT(dumps);
            PyObject *result = PyObject_CallOneArg(dumps, arg);
            if (result == NULL) {
                PyErr_Clear();
                result = PyObject_CallOneArg(dumps, Py_None);
            }
            CHECK_OBJECT(result);
            char *result_str;
            Py_ssize_t length;
            PyBytes_AsStringAndSize(result, &result_str, &length);
            fwrite(result_str, sizeof(char), length, pgo_output);
            fputc(0, pgo_output);
            Py_DECREF(result);
            Py_DECREF(dumps);
            Py_DECREF(marshal);
            break;
        }
        }
    }

    va_end(args);
}

void PGO_onModuleEntered(char const *module_name) { PGO_onProbePassed("ModuleEnter", "s", module_name); }
void PGO_onModuleExit(char const *module_name, bool error) {
    PGO_onProbePassed("ModuleExit", "su", module_name, error);
}
void PGO_onTechnicalModule(char const *module_name) { PGO_onProbePassed("ModuleTechnical", "s", module_name); }
void PGO_onClassPrepareCalled(const char *id, PyObject *result) { PGO_onProbePassed("ClassPrepare", "so", id, result); }

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
