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
#include <string>

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

// From CPython, to allow us quick access to the dictionary of an module, the structure is
// normally private
typedef struct {
    PyObject_HEAD
    PyObject *md_dict;
} PyModuleObject;

#endif
