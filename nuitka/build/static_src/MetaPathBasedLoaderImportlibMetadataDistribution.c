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
// This implements the "importlib.metadata.distribution" values, also for
// the backport "importlib_metadata.distribution"

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#include "nuitka/unfreezing.h"
#endif

PyObject *Nuitka_Distribution_New(char const *distribution_name, char const *package_name, PyObject *metadata) {
    // TODO: Have our own Python code to be included in compiled form,
    // this duplicates with inspec patcher code.
    static PyObject *nuitka_distribution_type = NULL;
    static PyObject *importlib_metadata_distribution = NULL;
    // TODO: Use pathlib.Path for "locate_file" result should be more compatible.

    if (nuitka_distribution_type == NULL) {
        static char const *nuitka_distribution_code = "\n\
import os,sys\n\
if sys.version_info >= (3, 8):\n\
    from importlib.metadata import Distribution,distribution\n\
else:\n\
    from importlib_metadata import Distribution,distribution\n\
class nuitka_distribution(Distribution):\n\
    def __init__(self, base_path, metadata):\n\
        self.base_path = base_path; self.metadata_data = metadata\n\
    def read_text(self, filename):\n\
        if filename == 'METADATA':\n\
            return self.metadata_data\n\
    def locate_file(self, path):\n\
        return os.path.join(self.base_path, path)\n\
";

        PyObject *nuitka_distribution_code_object = Py_CompileString(nuitka_distribution_code, "<exec>", Py_file_input);
        CHECK_OBJECT(nuitka_distribution_code_object);

        {
            PyObject *module =
                PyImport_ExecCodeModule((char *)"nuitka_distribution_patch", nuitka_distribution_code_object);
            CHECK_OBJECT(module);

            nuitka_distribution_type = PyObject_GetAttrString(module, "nuitka_distribution");
            CHECK_OBJECT(nuitka_distribution_type);

            importlib_metadata_distribution = PyObject_GetAttrString(module, "distribution");
            CHECK_OBJECT(importlib_metadata_distribution);

            bool bool_res = Nuitka_DelModuleString("nuitka_distribution_patch");
            assert(bool_res != false);

            Py_DECREF(module);
        }
    }

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry(package_name);

    if (entry == NULL) {
        PyObject *name_obj = Nuitka_String_FromString(distribution_name);
        CHECK_OBJECT(name_obj);
        PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(importlib_metadata_distribution, name_obj);
        Py_DECREF(name_obj);

        return result;
    } else {

        PyObject *args[2] = {
            getModuleDirectory(entry),
            metadata,
        };
        PyObject *result = CALL_FUNCTION_WITH_ARGS2(nuitka_distribution_type, args);
        CHECK_OBJECT(result);
        return result;
    }
}
