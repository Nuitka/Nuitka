/* Python 2.x/3.x compitibility tools
 */

#if !defined(PGCOMPAT_H)
#define PGCOMPAT_H

#if PY_MAJOR_VERSION >= 3

#define PY3 1

/* Define some aliases for the removed PyInt_* functions */
#define PyInt_Check(op) PyLong_Check(op)
#define PyInt_FromString PyLong_FromString
#define PyInt_FromUnicode PyLong_FromUnicode
#define PyInt_FromLong PyLong_FromLong
#define PyInt_FromSize_t PyLong_FromSize_t
#define PyInt_FromSsize_t PyLong_FromSsize_t
#define PyInt_AsLong PyLong_AsLong
#define PyInt_AsSsize_t PyLong_AsSsize_t
#define PyInt_AsUnsignedLongMask PyLong_AsUnsignedLongMask
#define PyInt_AsUnsignedLongLongMask PyLong_AsUnsignedLongLongMask
#define PyInt_AS_LONG PyLong_AS_LONG
#define PyNumber_Int PyNumber_Long

/* Weakrefs flags changed in 3.x */
#define Py_TPFLAGS_HAVE_WEAKREFS 0

/* Module init function returns new module instance. */
#define MODINIT_RETURN(x) return x
#define MODINIT_DEFINE(mod_name) PyMODINIT_FUNC PyInit_##mod_name (void)
#define DECREF_MOD(mod) Py_DECREF (mod)

/* Type header differs. */
#define TYPE_HEAD(x,y) PyVarObject_HEAD_INIT(x,y)

/* Text interface. Use unicode strings. */
#define Text_Type PyUnicode_Type
#define Text_Check PyUnicode_Check
#define Text_FromUTF8 PyUnicode_FromString
#define Text_FromUTF8AndSize PyUnicode_FromStringAndSize
#define Text_FromFormat PyUnicode_FromFormat
#define Text_GetSize PyUnicode_GetSize
#define Text_GET_SIZE PyUnicode_GET_SIZE

/* Binary interface. Use bytes. */
#define Bytes_Type PyBytes_Type
#define Bytes_Check PyBytes_Check
#define Bytes_Size PyBytes_Size
#define Bytes_AsString PyBytes_AsString
#define Bytes_AsStringAndSize PyBytes_AsStringAndSize
#define Bytes_FromStringAndSize PyBytes_FromStringAndSize
#define Bytes_FromFormat PyBytes_FromFormat
#define Bytes_AS_STRING PyBytes_AS_STRING
#define Bytes_GET_SIZE PyBytes_GET_SIZE
#define Bytes_AsDecodeObject PyBytes_AsDecodedObject

#define Object_Unicode PyObject_Str

#define IsTextObj(x) (PyUnicode_Check(x) || PyBytes_Check(x))

/* Renamed builtins */
#define BUILTINS_MODULE "builtins"
#define BUILTINS_UNICODE "str"
#define BUILTINS_UNICHR "chr"

/* Defaults for unicode file path encoding */
#define UNICODE_DEF_FS_CODEC Py_FileSystemDefaultEncoding
#if defined(MS_WIN32)
#define UNICODE_DEF_FS_ERROR "replace"
#else
#define UNICODE_DEF_FS_ERROR "surrogateescape"
#endif

#else /* #if PY_MAJOR_VERSION >= 3 */

#define PY3 0

/* Module init function returns nothing. */
#define MODINIT_RETURN(x) return
#define MODINIT_DEFINE(mod_name) PyMODINIT_FUNC init##mod_name (void)
#define DECREF_MOD(mod)

/* Type header differs. */
#define TYPE_HEAD(x,y)                          \
    PyObject_HEAD_INIT(x)                       \
    0,

/* Text interface. Use ascii strings. */
#define Text_Type PyString_Type
#define Text_Check PyString_Check
#define Text_FromUTF8 PyString_FromString
#define Text_FromUTF8AndSize PyString_FromStringAndSize
#define Text_FromFormat PyString_FromFormat
#define Text_GetSize PyString_GetSize
#define Text_GET_SIZE PyString_GET_SIZE

/* Binary interface. Use ascii strings. */
#define Bytes_Type PyString_Type
#define Bytes_Check PyString_Check
#define Bytes_Size PyString_Size
#define Bytes_AsString PyString_AsString
#define Bytes_AsStringAndSize PyString_AsStringAndSize
#define Bytes_FromStringAndSize PyString_FromStringAndSize
#define Bytes_FromFormat PyString_FromFormat
#define Bytes_AS_STRING PyString_AS_STRING
#define Bytes_GET_SIZE PyString_GET_SIZE
#define Bytes_AsDecodedObject PyString_AsDecodedObject

#define Object_Unicode PyObject_Unicode

/* Renamed builtins */
#define BUILTINS_MODULE "__builtin__"
#define BUILTINS_UNICODE "unicode"
#define BUILTINS_UNICHR "unichr"

/* Defaults for unicode file path encoding */
#define UNICODE_DEF_FS_CODEC Py_FileSystemDefaultEncoding
#define UNICODE_DEF_FS_ERROR "strict"

#endif /* #if PY_MAJOR_VERSION >= 3 */

#define PY2 (!PY3)

#define MODINIT_ERROR MODINIT_RETURN (NULL)

/* Module state. These macros are used to define per-module macros.
 * v - global state variable (Python 2.x)
 * s - global state structure (Python 3.x)
 */
#define PY2_GETSTATE(v) (&(v))
#define PY3_GETSTATE(s, m) ((struct s *) PyModule_GetState (m))

/* Pep 3123: Making PyObject_HEAD conform to standard C */
#if !defined(Py_TYPE)
#define Py_TYPE(o)    (((PyObject *)(o))->ob_type)
#define Py_REFCNT(o)  (((PyObject *)(o))->ob_refcnt)
#define Py_SIZE(o)    (((PyVarObject *)(o))->ob_size)
#endif

/* Encode a unicode file path */
#define Unicode_AsEncodedPath(u) \
    PyUnicode_AsEncodedString ((u), UNICODE_DEF_FS_CODEC, UNICODE_DEF_FS_ERROR)

/* Relative paths introduced in Python 2.6 */
#if PY_VERSION_HEX >= 0x02060000
#define HAVE_RELATIVE_IMPORT 1
#else
#define HAVE_RELATIVE_IMPORT 0
#endif

#if HAVE_RELATIVE_IMPORT
#define RELATIVE_MODULE(m) ("." m)
#else
#define RELATIVE_MODULE(m) (m)
#endif

/* Python 3 (PEP 3118) buffer protocol */
#if PY_VERSION_HEX >= 0x02060000
#define HAVE_NEW_BUFPROTO 1
#else
#define HAVE_NEW_BUFPROTO 0
#endif

#define HAVE_OLD_BUFPROTO PY2

#if !defined(PG_ENABLE_OLDBUF)  /* allow for command line override */
#if HAVE_OLD_BUFPROTO
#define PG_ENABLE_OLDBUF 1
#else
#define PG_ENABLE_OLDBUF 0
#endif
#endif

#ifndef Py_TPFLAGS_HAVE_NEWBUFFER
#define Py_TPFLAGS_HAVE_NEWBUFFER 0
#endif

#ifndef Py_TPFLAGS_HAVE_CLASS
#define Py_TPFLAGS_HAVE_CLASS 0
#endif

#ifndef Py_TPFLAGS_CHECKTYPES
#define Py_TPFLAGS_CHECKTYPES 0
#endif

#if PY_VERSION_HEX >= 0x03020000
#define Slice_GET_INDICES_EX(slice, length, start, stop, step, slicelength) \
    PySlice_GetIndicesEx(slice, length, start, stop, step, slicelength)
#else
#define Slice_GET_INDICES_EX(slice, length, start, stop, step, slicelength) \
    PySlice_GetIndicesEx((PySliceObject *)(slice), length, \
                         start, stop, step, slicelength)
#endif

/* Python 2.4 (PEP 353) ssize_t */
#if PY_VERSION_HEX < 0x02050000
#define PyInt_AsSsize_t PyInt_AsLong
#define PyInt_FromSsizt_t PyInt_FromLong
#endif

/* Support new buffer protocol? */
#if !defined(PG_ENABLE_NEWBUF)  /* allow for command line override */
#if HAVE_NEW_BUFPROTO && !defined(PYPY_VERSION)
#define PG_ENABLE_NEWBUF 1
#else
#define PG_ENABLE_NEWBUF 0
#endif
#endif

#endif /* #if !defined(PGCOMPAT_H) */
