//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// C code for use when the dill-plugin is active

#include "nuitka/prelude.h"

void registerDillPluginTables(PyThreadState *tstate, char const *module_name, PyMethodDef *reduce_compiled_function,
                              PyMethodDef *create_compiled_function) {
    PyObject *function_tables = PyObject_GetAttrString((PyObject *)builtin_module, "compiled_function_tables");

    if (function_tables == NULL) {
        CLEAR_ERROR_OCCURRED(tstate);

        function_tables = MAKE_DICT_EMPTY(tstate);
        PyObject_SetAttrString((PyObject *)builtin_module, "compiled_function_tables", function_tables);
    }

    PyObject *funcs = MAKE_TUPLE2_0(tstate, PyCFunction_New(reduce_compiled_function, NULL),
                                    PyCFunction_New(create_compiled_function, NULL));

    PyDict_SetItemString(function_tables, module_name, funcs);
}

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
