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
#ifndef __NUITKA_HELPER_COMPLEX_H__
#define __NUITKA_HELPER_COMPLEX_H__

NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_COMPLEX1(PyObject *real) {
    CHECK_OBJECT(real);

    // TODO: Very lazy here, we should create the values ourselves, surely a
    // a lot of optimization can be had that way. At least use PyComplex_RealAsDouble
    // where possible.
    return CALL_FUNCTION_WITH_SINGLE_ARG((PyObject *)&PyComplex_Type, real);
}

NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_COMPLEX2(PyObject *real, PyObject *imag) {
    if (real == NULL) {
        assert(imag != NULL);

        real = const_int_0;
    }

    CHECK_OBJECT(real);
    CHECK_OBJECT(imag);

    // TODO: Very lazy here, we should create the values ourselves, surely a
    // a lot of optimization can be had that way. At least use PyComplex_FromDoubles
    PyObject *args[] = {real, imag};
    return CALL_FUNCTION_WITH_ARGS2((PyObject *)&PyComplex_Type, args);
}

#endif
