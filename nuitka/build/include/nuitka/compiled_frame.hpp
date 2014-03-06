//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_COMPILED_FRAME_H__
#define __NUITKA_COMPILED_FRAME_H__

// Create a frame object for the given code object and module
extern PyFrameObject *MAKE_FRAME( PyCodeObject *code, PyObject *module );

// Create a code object for the given filename and function name
#if PYTHON_VERSION < 300
extern PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name, int line, PyObject *argnames, int arg_count, int flags );
#else
extern PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name, int line, PyObject *argnames, int arg_count, int kw_only_count, int flags );
#endif

extern PyTypeObject Nuitka_Frame_Type;

static inline bool Nuitka_Frame_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Frame_Type;
}

#endif
