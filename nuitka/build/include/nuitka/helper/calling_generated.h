//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* WARNING, this code is GENERATED. Modify the template CodeTemplateCallsPositional.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

extern PyObject *CALL_FUNCTION_NO_ARGS(PyObject *called);
extern PyObject *CALL_FUNCTION_WITH_SINGLE_ARG(PyObject *called, PyObject *arg);
extern PyObject *CALL_FUNCTION_WITH_POSARGS1(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS2(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS2(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS3(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS3(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS4(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS4(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS5(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS5(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS6(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS6(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS7(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS7(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS8(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS8(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS9(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS9(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_ARGS10(PyObject *called, PyObject *const *args);
extern PyObject *CALL_FUNCTION_WITH_POSARGS10(PyObject *called, PyObject *pos_args);
extern PyObject *CALL_FUNCTION_WITH_NO_ARGS_KWSPLIT(PyObject *called, PyObject *const *kw_values, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS1_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS1_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS1_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS2_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS2_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS2_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS3_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS3_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS3_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS4_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS4_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS4_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS5_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS5_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS5_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS6_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS6_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS6_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS7_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS7_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS7_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS8_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS8_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS8_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS9_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS9_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                  PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS9_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                     PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS10_VECTORCALL(PyObject *called, PyObject *const *args, PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_ARGS10_KWSPLIT(PyObject *called, PyObject *const *args, PyObject *const *kw_values,
                                                   PyObject *kw_names);
extern PyObject *CALL_FUNCTION_WITH_POSARGS10_KWSPLIT(PyObject *called, PyObject *pos_args, PyObject *const *kw_values,
                                                      PyObject *kw_names);
extern PyObject *CALL_METHODDESCR_WITH_SINGLE_ARG(PyObject *called, PyObject *arg);
extern PyObject *CALL_METHODDESCR_WITH_ARGS2(PyObject *called, PyObject *const *args);
extern PyObject *CALL_METHODDESCR_WITH_ARGS3(PyObject *called, PyObject *const *args);
extern PyObject *CALL_METHODDESCR_WITH_ARGS4(PyObject *called, PyObject *const *args);
extern PyObject *CALL_METHOD_NO_ARGS(PyObject *source, PyObject *attr_name);
extern PyObject *CALL_METHOD_WITH_SINGLE_ARG(PyObject *source, PyObject *attr_name, PyObject *arg);
extern PyObject *CALL_METHOD_WITH_ARGS2(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS3(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS4(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS5(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS6(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS7(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS8(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS9(PyObject *source, PyObject *attr_name, PyObject *const *args);
extern PyObject *CALL_METHOD_WITH_ARGS10(PyObject *source, PyObject *attr_name, PyObject *const *args);
