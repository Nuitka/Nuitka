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
#ifndef __NUITKA_PGO_H__
#define __NUITKA_PGO_H__

// In Visual Code, evaluate the code for PGO so we see errors of it sooner.
#ifdef __IDE_ONLY__
#define _NUITKA_PGO_GENERATE
#include "nuitka/prelude.h"
#endif

#if defined(_NUITKA_PGO_GENERATE)

// Initialize PGO data collection.
void initPgoOutput();

// When a module is entered.
void onModuleEntered(char const *module_name);
// When a module is exit.
void onModuleExit(char const *module_name, bool had_error);

void onProbePassed(char const *module_name, char const *probe_id, int probe_arg);

#else
#define initPgoOutput()

#define onModuleEntered(module_name) ;
#define onModuleExit(module_name, had_error) ;

#define onProbePassed(module_name, probe_id, probe_arg) ;

#endif

#endif