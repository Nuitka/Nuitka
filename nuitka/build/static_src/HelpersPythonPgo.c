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
/**
 * This is responsible for collection of Nuitka Python PGO information. It writes
 * traces to files, for reuse in a future Python compilation of the same program.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static FILE *pgo_output;

// Saving space by not repeating strings.

// Allocated strings
static char const **PGO_ProbeNameMappings = NULL;
static int PGO_ProbeNameMappings_size = 0;
static uint32_t PGO_ProbeNameMappings_used = 0;

int PGO_getStringID(char const *str) {
    for (int i = 0; i < PGO_ProbeNameMappings_used; i++) {
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

    if (unlikely(output_filename == NULL)) {
        fprintf(stderr, "Error, failed to open '%s' for writing.", output_filename);
        exit(27);
    }

    fputs("KAY.PGO", pgo_output);
    fflush(pgo_output);

    PGO_ProbeNameMappings_size = 10000;
    PGO_ProbeNameMappings = malloc(PGO_ProbeNameMappings_size * sizeof(char const *));
}

void PGO_Finalize(void) {
    PGO_writeString("END");

    uint32_t offset = (uint32_t)ftell(pgo_output);

    for (int i = 0; i < PGO_ProbeNameMappings_used; i++) {
        fputs(PGO_ProbeNameMappings[i], pgo_output);
        fputc(0, pgo_output);
    }

    fwrite(&PGO_ProbeNameMappings_used, sizeof(PGO_ProbeNameMappings_used), 1, pgo_output);
    fwrite(&offset, sizeof(offset), 1, pgo_output);

    fputs("YAK.PGO", pgo_output);
    fclose(pgo_output);
}

void PGO_onProbePassed(char const *probe_str, char const *module_name, uint32_t probe_arg) {
    PGO_writeString(probe_str);
    PGO_writeString(module_name);
    // TODO: Variable args depending on probe type?
    fwrite(&probe_arg, sizeof(probe_arg), 1, pgo_output);
}

void PGO_onModuleEntered(char const *module_name) { PGO_onProbePassed("ModuleEnter", module_name, 0); }
void PGO_onModuleExit(char const *module_name, bool error) { PGO_onProbePassed("ModuleExit", module_name, error); }
void PGO_onTechnicalModule(char const *module_name) { PGO_onProbePassed("ModuleTechnical", module_name, 0); }
