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
#ifndef __NUITKA_IMPORTING_H__
#define __NUITKA_IMPORTING_H__

/* These are for the built-in import.
 *
 * They call the real thing with varying amount of arguments. For keyword
 * calls using default values, the _KW helper is used.
 *
 */
extern PyObject *IMPORT_MODULE1(PyObject *module_name);
extern PyObject *IMPORT_MODULE2(PyObject *module_name, PyObject *globals);
extern PyObject *IMPORT_MODULE3(PyObject *module_name, PyObject *globals, PyObject *locals);
extern PyObject *IMPORT_MODULE4(PyObject *module_name, PyObject *globals, PyObject *locals, PyObject *import_items);
extern PyObject *IMPORT_MODULE5(PyObject *module_name, PyObject *globals, PyObject *locals, PyObject *import_items,
                                PyObject *level);
extern PyObject *IMPORT_MODULE_KW(PyObject *module_name, PyObject *globals, PyObject *locals, PyObject *import_items,
                                  PyObject *level);

extern bool IMPORT_MODULE_STAR(PyObject *target, bool is_module, PyObject *module);

extern PyObject *IMPORT_EMBEDDED_MODULE(PyObject *module_name, char const *name);

extern PyObject *const_str_plain___name__;

// Import a name from a module.
extern PyObject *IMPORT_NAME(PyObject *module, PyObject *import_name);

// import a name from a module, potentially making an import of it if necessary.
#if PYTHON_VERSION >= 350
extern PyObject *IMPORT_NAME_OR_MODULE(PyObject *module, PyObject *globals, PyObject *import_name, PyObject *level);
#endif

#endif
