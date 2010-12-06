//
//     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an attempt of building an optimizing Python compiler
//     that is compatible and integrates with CPython, but also works on its
//     own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//
#ifndef __NUITKA_PRELUDE_H__
#define __NUITKA_PRELUDE_H__

#ifdef __NUITKA_NO_ASSERT__
#define NDEBUG
#endif

// Include the Python C/API header files

#include "Python.h"
#include "methodobject.h"
#include "frameobject.h"
#include <stdio.h>

// An idea I first saw used with Cython, hint the compiler about branches that are more or
// less likely to be taken. And hint the compiler about things that we assume to be
// normally true. If other compilers can do similar, I would be grateful for howtos.

#ifdef __GNUC__
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

// An idea to reduce the amount of exported symbols, esp. as we are using C++ and classes
// do not allow to limit their visibility normally.
#ifdef __GNUC__
#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC __attribute__((visibility( "default" )))
#else
#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC
#endif

static PyObject *_expression_temps[100];
static PyObject *_eval_globals_tmp;
static PyObject *_eval_locals_tmp;

#include "nuitka/helpers.hpp"

#include "nuitka/compiled_function.hpp"

// Sentinel PyObject to be used for all our call iterator endings.
extern PyObject *_sentinel_value;

#include "nuitka/compiled_generator.hpp"
#include "nuitka/compiled_genexpr.hpp"

#endif
