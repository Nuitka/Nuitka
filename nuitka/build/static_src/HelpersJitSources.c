//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#ifdef _NUITKA_STANDALONE

static char const *uncompiled_sources_dict_attribute_name = "_uncompiled_function_sources_dict";

void SET_UNCOMPILED_FUNCTION_SOURCE_DICT(PyObject *name, PyObject *source) {
    PyObject *uncompiled_function_sources_dict =
        PyObject_GetAttrString((PyObject *)builtin_module, uncompiled_sources_dict_attribute_name);

    if (uncompiled_function_sources_dict == NULL) {
        PyThreadState *tstate = PyThreadState_GET();

        DROP_ERROR_OCCURRED(tstate);

        uncompiled_function_sources_dict = MAKE_DICT_EMPTY(tstate);

        PyObject_SetAttrString((PyObject *)builtin_module, uncompiled_sources_dict_attribute_name,
                               uncompiled_function_sources_dict);
    }

    bool res = DICT_SET_ITEM(uncompiled_function_sources_dict, name, source);
    assert(res == false);
}

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
