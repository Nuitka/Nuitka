//     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_PRINTING_H__
#define __NUITKA_PRINTING_H__

// Helper functions for print. Need to play nice with Python softspace
// behaviour.

#include "nuitka/exceptions.hpp"

extern bool PRINT_NEW_LINE( void );
extern bool PRINT_ITEM( PyObject *object );

extern bool PRINT_ITEM_TO( PyObject *file, PyObject *object );
extern bool PRINT_NEW_LINE_TO( PyObject *file );

extern PyObject *GET_STDOUT();
extern PyObject *GET_STDERR();

// Helper functions to debug the compiler operation.
extern void PRINT_REFCOUNT( PyObject *object );

#endif
