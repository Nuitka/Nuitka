//     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_UNFREEZING_H__
#define __NUITKA_UNFREEZING_H__

// This define guards these definitions from being used without the unfreezing
// mode actually being active at all.

struct Nuitka_FreezeTableEntry
{
    char *name; // Full module name, including package

#if PYTHON_VERSION < 300
    void (*python_initfunc)( void );
#else
    PyObject * (*python_initfunc)( void );
#endif

    int flags;
};

// For embedded modules, to be unpacked. Used by main program/package only
extern void registerMetaPathBasedUnfreezer( struct Nuitka_FreezeTableEntry *_frozen_modules );

// For the "__loader__" attribute of modules.
#if PYTHON_VERSION >= 330
extern PyObject *loader_frozen_modules;
#endif

#endif
