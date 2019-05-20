//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include <float.h>

/* Check if unary negation would not fit into long */
#define UNARY_NEG_WOULD_OVERFLOW(x) ((x) < 0 && (unsigned long)(x) == 0 - (unsigned long)(x))
/* This is from pyport.h */
#define WIDTH_OF_ULONG (CHAR_BIT * SIZEOF_LONG)

// TODO: Move to truediv utils

extern PyObject *const_float_minus_0_0, *const_float_0_0;
