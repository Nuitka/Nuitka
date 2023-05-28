//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_PYTHON_PGO_H__
#define __NUITKA_PYTHON_PGO_H__

// In Visual Code, evaluate the code for PGO so we see errors of it sooner.
#ifdef __IDE_ONLY__
#define _NUITKA_PGO_PYTHON 1
#include "nuitka/prelude.h"
#endif

#if _NUITKA_PGO_PYTHON

// Initialize PGO data collection.
extern void PGO_Initialize(void);

// At end of program, write tables.
extern void PGO_Finalize(void);

// When a module is entered.
extern void PGO_onModuleEntered(char const *module_name);
// When a module is exited.
extern void PGO_onModuleExit(char const *module_name, bool had_error);

extern void PGO_onProbePassed(char const *module_name, char const *probe_id, uint32_t probe_arg);

extern void PGO_onTechnicalModule(char const *module_name);

#else

#define PGO_Initialize()
#define PGO_Finalize()

#define PGO_onModuleEntered(module_name) ;
#define PGO_onModuleExit(module_name, had_error) ;

#define PGO_onProbePassed(module_name, probe_id, probe_arg) ;

#endif

#endif