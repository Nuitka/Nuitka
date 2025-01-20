//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// No guard on purpose, must include this only once for real.

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_FRAME
#define _DEBUG_FRAME 1
#else
#define _DEBUG_FRAME 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_REFRAME
#define _DEBUG_REFRAME 1
#else
#define _DEBUG_REFRAME 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_EXCEPTIONS
#define _DEBUG_EXCEPTIONS 1
#else
#define _DEBUG_EXCEPTIONS 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_GENERATOR
#define _DEBUG_GENERATOR 1
#else
#define _DEBUG_GENERATOR 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_COROUTINE
#define _DEBUG_COROUTINE 1
#else
#define _DEBUG_COROUTINE 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ASYNCGEN
#define _DEBUG_ASYNCGEN 1
#else
#define _DEBUG_ASYNCGEN 0
#endif
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_CLASSES
#define _DEBUG_CLASSES 1
#else
#define _DEBUG_CLASSES 0
#endif

#ifdef _NUITKA_EXPERIMENTAL_REPORT_REFCOUNTS
#define _DEBUG_REFCOUNTS 1
#else
#define _DEBUG_REFCOUNTS 0
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
