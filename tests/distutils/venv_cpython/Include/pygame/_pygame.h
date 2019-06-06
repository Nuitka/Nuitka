/*
    pygame - Python Game Library
    Copyright (C) 2000-2001  Pete Shinners

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Library General Public
    License as published by the Free Software Foundation; either
    version 2 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Library General Public License for more details.

    You should have received a copy of the GNU Library General Public
    License along with this library; if not, write to the Free
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Pete Shinners
    pete@shinners.org
*/

#ifndef _PYGAME_H
#define _PYGAME_H

/** This header file includes all the definitions for the
 ** base pygame extensions. This header only requires
 ** SDL and Python includes. The reason for functions
 ** prototyped with #define's is to allow for maximum
 ** python portability. It also uses python as the
 ** runtime linker, which allows for late binding. For more
 ** information on this style of development, read the Python
 ** docs on this subject.
 ** http://www.python.org/doc/current/ext/using-cobjects.html
 **
 ** If using this to build your own derived extensions,
 ** you'll see that the functions available here are mainly
 ** used to help convert between python objects and SDL objects.
 ** Since this library doesn't add a lot of functionality to
 ** the SDL libarary, it doesn't need to offer a lot either.
 **
 ** When initializing your extension module, you must manually
 ** import the modules you want to use. (this is the part about
 ** using python as the runtime linker). Each module has its
 ** own import_xxx() routine. You need to perform this import
 ** after you have initialized your own module, and before
 ** you call any routines from that module. Since every module
 ** in pygame does this, there are plenty of examples.
 **
 ** The base module does include some useful conversion routines
 ** that you are free to use in your own extension.
 **
 ** When making changes, it is very important to keep the
 ** FIRSTSLOT and NUMSLOT constants up to date for each
 ** section. Also be sure not to overlap any of the slots.
 ** When you do make a mistake with this, it will result
 ** is a dereferenced NULL pointer that is easier to diagnose
 ** than it could be :]
 **/
#if defined(HAVE_SNPRINTF)  /* defined in python.h (pyerrors.h) and SDL.h (SDL_config.h) */
#undef HAVE_SNPRINTF        /* remove GCC redefine warning */
#endif

// This must be before all else
#if defined(__SYMBIAN32__) && defined( OPENC )
#include <sys/types.h>

#if defined(__WINS__)
void* _alloca(size_t size);
#  define alloca _alloca
#endif

#endif

/* This is unconditionally defined in Python.h */
#if defined(_POSIX_C_SOURCE)
#undef _POSIX_C_SOURCE
#endif

#include <Python.h>

/* Cobjects vanish in Python 3.2; so we will code as though we use capsules */
#if defined(Py_CAPSULE_H)
#define PG_HAVE_CAPSULE 1
#else
#define PG_HAVE_CAPSULE 0
#endif
#if defined(Py_COBJECT_H)
#define PG_HAVE_COBJECT 1
#else
#define PG_HAVE_COBJECT 0
#endif
#if !PG_HAVE_CAPSULE
#define PyCapsule_New(ptr, n, dfn) PyCObject_FromVoidPtr(ptr, dfn)
#define PyCapsule_GetPointer(obj, n) PyCObject_AsVoidPtr(obj)
#define PyCapsule_CheckExact(obj) PyCObject_Check(obj)
#endif

/* Pygame uses Py_buffer (PEP 3118) to exchange array information internally;
 * define here as needed.
 */
#if !defined(PyBUF_SIMPLE)
typedef struct bufferinfo {
    void *buf;
    PyObject *obj;
    Py_ssize_t len;
    Py_ssize_t itemsize;
    int readonly;
    int ndim;
    char *format;
    Py_ssize_t *shape;
    Py_ssize_t *strides;
    Py_ssize_t *suboffsets;
    void *internal;
} Py_buffer;

/* Flags for getting buffers */
#define PyBUF_SIMPLE 0
#define PyBUF_WRITABLE 0x0001
/*  we used to include an E, backwards compatible alias  */
#define PyBUF_WRITEABLE PyBUF_WRITABLE
#define PyBUF_FORMAT 0x0004
#define PyBUF_ND 0x0008
#define PyBUF_STRIDES (0x0010 | PyBUF_ND)
#define PyBUF_C_CONTIGUOUS (0x0020 | PyBUF_STRIDES)
#define PyBUF_F_CONTIGUOUS (0x0040 | PyBUF_STRIDES)
#define PyBUF_ANY_CONTIGUOUS (0x0080 | PyBUF_STRIDES)
#define PyBUF_INDIRECT (0x0100 | PyBUF_STRIDES)

#define PyBUF_CONTIG (PyBUF_ND | PyBUF_WRITABLE)
#define PyBUF_CONTIG_RO (PyBUF_ND)

#define PyBUF_STRIDED (PyBUF_STRIDES | PyBUF_WRITABLE)
#define PyBUF_STRIDED_RO (PyBUF_STRIDES)

#define PyBUF_RECORDS (PyBUF_STRIDES | PyBUF_WRITABLE | PyBUF_FORMAT)
#define PyBUF_RECORDS_RO (PyBUF_STRIDES | PyBUF_FORMAT)

#define PyBUF_FULL (PyBUF_INDIRECT | PyBUF_WRITABLE | PyBUF_FORMAT)
#define PyBUF_FULL_RO (PyBUF_INDIRECT | PyBUF_FORMAT)


#define PyBUF_READ  0x100
#define PyBUF_WRITE 0x200
#define PyBUF_SHADOW 0x400

typedef int (*getbufferproc)(PyObject *, Py_buffer *, int);
typedef void (*releasebufferproc)(Py_buffer *);
#endif /* #if !defined(PyBUF_SIMPLE) */

/* Flag indicating a Pg_buffer; used for assertions within callbacks */
#ifndef NDEBUG
#define PyBUF_PYGAME 0x4000
#endif

#define PyBUF_HAS_FLAG(f, F) (((f) & (F)) == (F))

/* Array information exchange struct C type; inherits from Py_buffer
 *
 * Pygame uses its own Py_buffer derived C struct as an internal representation
 * of an imported array buffer. The extended Py_buffer allows for a
 * per-instance release callback, 
 */
typedef void (*pybuffer_releaseproc)(Py_buffer *);

typedef struct pg_bufferinfo_s {
    Py_buffer view;
    PyObject *consumer;                   /* Input: Borrowed reference */
    pybuffer_releaseproc release_buffer;
} Pg_buffer;

/* Operating system specific adjustments
 */
// No signal()
#if defined(__SYMBIAN32__) && defined(HAVE_SIGNAL_H)
#undef HAVE_SIGNAL_H
#endif

#if defined(HAVE_SNPRINTF)
#undef HAVE_SNPRINTF
#endif

#ifdef MS_WIN32 /*Python gives us MS_WIN32, SDL needs just WIN32*/
#ifndef WIN32
#define WIN32
#endif
#endif


/// Prefix when initializing module
#define MODPREFIX ""
/// Prefix when importing module
#define IMPPREFIX "pygame."

#ifdef __SYMBIAN32__
#undef MODPREFIX
#undef IMPPREFIX
// On Symbian there is no pygame package. The extensions are built-in or in sys\bin.
#define MODPREFIX "pygame_"
#define IMPPREFIX "pygame_"
#endif

#include <SDL.h>

/* macros used throughout the source */
#define RAISE(x,y) (PyErr_SetString((x), (y)), (PyObject*)NULL)

#if PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION == 3
#  define Py_RETURN_NONE return Py_INCREF(Py_None), Py_None
#  define Py_RETURN_TRUE return Py_INCREF(Py_True), Py_True
#  define Py_RETURN_FALSE return Py_INCREF(Py_False), Py_False
#endif

/* Py_ssize_t availability. */
#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
typedef inquiry lenfunc;
typedef intargfunc ssizeargfunc;
typedef intobjargproc ssizeobjargproc;
typedef intintargfunc ssizessizeargfunc;
typedef intintobjargproc ssizessizeobjargproc;
typedef getreadbufferproc readbufferproc;
typedef getwritebufferproc writebufferproc;
typedef getsegcountproc segcountproc;
typedef getcharbufferproc charbufferproc;
#endif

#define PyType_Init(x) (((x).ob_type) = &PyType_Type)
#define PYGAMEAPI_LOCAL_ENTRY "_PYGAME_C_API"

#ifndef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))
#endif

#ifndef MAX
#define MAX(a,b) ( (a) > (b) ? (a) : (b))
#endif

#ifndef ABS
#define ABS(a) (((a) < 0) ? -(a) : (a))
#endif

/* test sdl initializations */
#define VIDEO_INIT_CHECK()                                              \
    if(!SDL_WasInit(SDL_INIT_VIDEO))                                    \
        return RAISE(PyExc_SDLError, "video system not initialized")

#define CDROM_INIT_CHECK()                                              \
    if(!SDL_WasInit(SDL_INIT_CDROM))                                    \
        return RAISE(PyExc_SDLError, "cdrom system not initialized")

#define JOYSTICK_INIT_CHECK()                                           \
    if(!SDL_WasInit(SDL_INIT_JOYSTICK))                                 \
        return RAISE(PyExc_SDLError, "joystick system not initialized")

/* BASE */
#define VIEW_CONTIGUOUS    1
#define VIEW_C_ORDER       2
#define VIEW_F_ORDER       4

#define PYGAMEAPI_BASE_FIRSTSLOT 0
#define PYGAMEAPI_BASE_NUMSLOTS 19
#ifndef PYGAMEAPI_BASE_INTERNAL
#define PyExc_SDLError ((PyObject*)PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT])

#define PyGame_RegisterQuit                                             \
    (*(void(*)(void(*)(void)))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 1])

#define IntFromObj                                                      \
    (*(int(*)(PyObject*, int*))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 2])

#define IntFromObjIndex                                                 \
    (*(int(*)(PyObject*, int, int*))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 3])

#define TwoIntsFromObj                                                  \
    (*(int(*)(PyObject*, int*, int*))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 4])

#define FloatFromObj                                                    \
    (*(int(*)(PyObject*, float*))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 5])

#define FloatFromObjIndex                                               \
    (*(int(*)(PyObject*, int, float*))                                \
     PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 6])

#define TwoFloatsFromObj                                \
    (*(int(*)(PyObject*, float*, float*))               \
     PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 7])

#define UintFromObj                                                     \
    (*(int(*)(PyObject*, Uint32*))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 8])

#define UintFromObjIndex                                                \
    (*(int(*)(PyObject*, int, Uint32*))                                 \
     PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 9])

#define PyGame_Video_AutoQuit                                           \
    (*(void(*)(void))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 10])

#define PyGame_Video_AutoInit                                           \
    (*(int(*)(void))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 11])

#define RGBAFromObj                                                     \
    (*(int(*)(PyObject*, Uint8*))PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 12])

#define PgBuffer_AsArrayInterface                                       \
    (*(PyObject*(*)(Py_buffer*)) PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 13])

#define PgBuffer_AsArrayStruct                                          \
    (*(PyObject*(*)(Py_buffer*))                                        \
     PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 14])

#define PgObject_GetBuffer                                              \
    (*(int(*)(PyObject*, Pg_buffer*, int))                              \
     PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 15])

#define PgBuffer_Release                                                \
    (*(void(*)(Pg_buffer*))                                             \
     PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 16])

#define PgDict_AsBuffer                                                 \
    (*(int(*)(Pg_buffer*, PyObject*, int))                              \
     PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 17])

#define PgExc_BufferError                                               \
    ((PyObject*)PyGAME_C_API[PYGAMEAPI_BASE_FIRSTSLOT + 18])

#define import_pygame_base() IMPORT_PYGAME_MODULE(base, BASE)
#endif


/* RECT */
#define PYGAMEAPI_RECT_FIRSTSLOT                                \
    (PYGAMEAPI_BASE_FIRSTSLOT + PYGAMEAPI_BASE_NUMSLOTS)
#define PYGAMEAPI_RECT_NUMSLOTS 4

typedef struct {
    int x, y;
    int w, h;
}GAME_Rect;

typedef struct {
    PyObject_HEAD
    GAME_Rect r;
    PyObject *weakreflist;
} PyRectObject;

#define PyRect_AsRect(x) (((PyRectObject*)x)->r)
#ifndef PYGAMEAPI_RECT_INTERNAL
#define PyRect_Check(x) \
    ((x)->ob_type == (PyTypeObject*)PyGAME_C_API[PYGAMEAPI_RECT_FIRSTSLOT + 0])
#define PyRect_Type (*(PyTypeObject*)PyGAME_C_API[PYGAMEAPI_RECT_FIRSTSLOT + 0])
#define PyRect_New                                                      \
    (*(PyObject*(*)(SDL_Rect*))PyGAME_C_API[PYGAMEAPI_RECT_FIRSTSLOT + 1])
#define PyRect_New4                                                     \
    (*(PyObject*(*)(int,int,int,int))PyGAME_C_API[PYGAMEAPI_RECT_FIRSTSLOT + 2])
#define GameRect_FromObject                                             \
    (*(GAME_Rect*(*)(PyObject*, GAME_Rect*))                            \
     PyGAME_C_API[PYGAMEAPI_RECT_FIRSTSLOT + 3])

#define import_pygame_rect() IMPORT_PYGAME_MODULE(rect, RECT)
#endif


/* CDROM */
#define PYGAMEAPI_CDROM_FIRSTSLOT                               \
    (PYGAMEAPI_RECT_FIRSTSLOT + PYGAMEAPI_RECT_NUMSLOTS)
#define PYGAMEAPI_CDROM_NUMSLOTS 2

typedef struct {
    PyObject_HEAD
    int id;
} PyCDObject;

#define PyCD_AsID(x) (((PyCDObject*)x)->id)
#ifndef PYGAMEAPI_CDROM_INTERNAL
#define PyCD_Check(x)                                                   \
    ((x)->ob_type == (PyTypeObject*)PyGAME_C_API[PYGAMEAPI_CDROM_FIRSTSLOT + 0])
#define PyCD_Type (*(PyTypeObject*)PyGAME_C_API[PYGAMEAPI_CDROM_FIRSTSLOT + 0])
#define PyCD_New                                                        \
    (*(PyObject*(*)(int))PyGAME_C_API[PYGAMEAPI_CDROM_FIRSTSLOT + 1])

#define import_pygame_cd() IMPORT_PYGAME_MODULE(cdrom, CDROM)
#endif


/* JOYSTICK */
#define PYGAMEAPI_JOYSTICK_FIRSTSLOT \
    (PYGAMEAPI_CDROM_FIRSTSLOT + PYGAMEAPI_CDROM_NUMSLOTS)
#define PYGAMEAPI_JOYSTICK_NUMSLOTS 2

typedef struct {
    PyObject_HEAD
    int id;
} PyJoystickObject;

#define PyJoystick_AsID(x) (((PyJoystickObject*)x)->id)

#ifndef PYGAMEAPI_JOYSTICK_INTERNAL
#define PyJoystick_Check(x)                                             \
    ((x)->ob_type == (PyTypeObject*)                                    \
     PyGAME_C_API[PYGAMEAPI_JOYSTICK_FIRSTSLOT + 0])

#define PyJoystick_Type                                                 \
    (*(PyTypeObject*)PyGAME_C_API[PYGAMEAPI_JOYSTICK_FIRSTSLOT + 0])
#define PyJoystick_New                                                  \
    (*(PyObject*(*)(int))PyGAME_C_API[PYGAMEAPI_JOYSTICK_FIRSTSLOT + 1])

#define import_pygame_joystick() IMPORT_PYGAME_MODULE(joystick, JOYSTICK)
#endif


/* DISPLAY */
#define PYGAMEAPI_DISPLAY_FIRSTSLOT \
    (PYGAMEAPI_JOYSTICK_FIRSTSLOT + PYGAMEAPI_JOYSTICK_NUMSLOTS)
#define PYGAMEAPI_DISPLAY_NUMSLOTS 2
typedef struct {
    PyObject_HEAD
    SDL_VideoInfo info;
} PyVidInfoObject;

#define PyVidInfo_AsVidInfo(x) (((PyVidInfoObject*)x)->info)
#ifndef PYGAMEAPI_DISPLAY_INTERNAL
#define PyVidInfo_Check(x)                                              \
    ((x)->ob_type == (PyTypeObject*)                                    \
     PyGAME_C_API[PYGAMEAPI_DISPLAY_FIRSTSLOT + 0])

#define PyVidInfo_Type                                                  \
    (*(PyTypeObject*)PyGAME_C_API[PYGAMEAPI_DISPLAY_FIRSTSLOT + 0])
#define PyVidInfo_New                                   \
    (*(PyObject*(*)(SDL_VideoInfo*))                    \
     PyGAME_C_API[PYGAMEAPI_DISPLAY_FIRSTSLOT + 1])
#define import_pygame_display() IMPORT_PYGAME_MODULE(display, DISPLAY)
#endif


/* SURFACE */
#define PYGAMEAPI_SURFACE_FIRSTSLOT                             \
    (PYGAMEAPI_DISPLAY_FIRSTSLOT + PYGAMEAPI_DISPLAY_NUMSLOTS)
#define PYGAMEAPI_SURFACE_NUMSLOTS 3
typedef struct {
    PyObject_HEAD
    SDL_Surface* surf;
    struct SubSurface_Data* subsurface;  /*ptr to subsurface data (if a
                                          * subsurface)*/
    PyObject *weakreflist;
    PyObject *locklist;
    PyObject *dependency;
} PySurfaceObject;
#define PySurface_AsSurface(x) (((PySurfaceObject*)x)->surf)
#ifndef PYGAMEAPI_SURFACE_INTERNAL
#define PySurface_Check(x)                                              \
    ((x)->ob_type == (PyTypeObject*)                                    \
     PyGAME_C_API[PYGAMEAPI_SURFACE_FIRSTSLOT + 0])
#define PySurface_Type                                                  \
    (*(PyTypeObject*)PyGAME_C_API[PYGAMEAPI_SURFACE_FIRSTSLOT + 0])
#define PySurface_New                                                   \
    (*(PyObject*(*)(SDL_Surface*))                                      \
     PyGAME_C_API[PYGAMEAPI_SURFACE_FIRSTSLOT + 1])
#define PySurface_Blit                                                  \
    (*(int(*)(PyObject*,PyObject*,SDL_Rect*,SDL_Rect*,int))             \
     PyGAME_C_API[PYGAMEAPI_SURFACE_FIRSTSLOT + 2])

#define import_pygame_surface() do {                                   \
    IMPORT_PYGAME_MODULE(surface, SURFACE);                            \
    if (PyErr_Occurred() != NULL) break;                               \
    IMPORT_PYGAME_MODULE(surflock, SURFLOCK);                          \
    } while (0)
#endif


/* SURFLOCK */    /*auto import/init by surface*/
#define PYGAMEAPI_SURFLOCK_FIRSTSLOT                            \
    (PYGAMEAPI_SURFACE_FIRSTSLOT + PYGAMEAPI_SURFACE_NUMSLOTS)
#define PYGAMEAPI_SURFLOCK_NUMSLOTS 8
struct SubSurface_Data
{
    PyObject* owner;
    int pixeloffset;
    int offsetx, offsety;
};

typedef struct
{
    PyObject_HEAD
    PyObject *surface;
    PyObject *lockobj;
    PyObject *weakrefs;
} PyLifetimeLock;

#ifndef PYGAMEAPI_SURFLOCK_INTERNAL
#define PyLifetimeLock_Check(x)                         \
    ((x)->ob_type == (PyTypeObject*)                    \
        PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 0])
#define PySurface_Prep(x)                                               \
    if(((PySurfaceObject*)x)->subsurface)                               \
        (*(*(void(*)(PyObject*))                                        \
           PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 1]))(x)

#define PySurface_Unprep(x)                                             \
    if(((PySurfaceObject*)x)->subsurface)                               \
        (*(*(void(*)(PyObject*))                                        \
           PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 2]))(x)

#define PySurface_Lock                                                  \
    (*(int(*)(PyObject*))PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 3])
#define PySurface_Unlock                                                \
    (*(int(*)(PyObject*))PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 4])
#define PySurface_LockBy                                                \
    (*(int(*)(PyObject*,PyObject*))                                     \
        PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 5])
#define PySurface_UnlockBy                                              \
    (*(int(*)(PyObject*,PyObject*))                                     \
        PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 6])
#define PySurface_LockLifetime                                          \
    (*(PyObject*(*)(PyObject*,PyObject*))                               \
        PyGAME_C_API[PYGAMEAPI_SURFLOCK_FIRSTSLOT + 7])
#endif


/* EVENT */
#define PYGAMEAPI_EVENT_FIRSTSLOT                                       \
    (PYGAMEAPI_SURFLOCK_FIRSTSLOT + PYGAMEAPI_SURFLOCK_NUMSLOTS)
#define PYGAMEAPI_EVENT_NUMSLOTS 4

typedef struct {
    PyObject_HEAD
    int type;
    PyObject* dict;
} PyEventObject;

#ifndef PYGAMEAPI_EVENT_INTERNAL
#define PyEvent_Check(x)                                                \
    ((x)->ob_type == (PyTypeObject*)PyGAME_C_API[PYGAMEAPI_EVENT_FIRSTSLOT + 0])
#define PyEvent_Type \
    (*(PyTypeObject*)PyGAME_C_API[PYGAMEAPI_EVENT_FIRSTSLOT + 0])
#define PyEvent_New \
    (*(PyObject*(*)(SDL_Event*))PyGAME_C_API[PYGAMEAPI_EVENT_FIRSTSLOT + 1])
#define PyEvent_New2                                                    \
    (*(PyObject*(*)(int, PyObject*))PyGAME_C_API[PYGAMEAPI_EVENT_FIRSTSLOT + 2])
#define PyEvent_FillUserEvent                           \
    (*(int (*)(PyEventObject*, SDL_Event*))             \
     PyGAME_C_API[PYGAMEAPI_EVENT_FIRSTSLOT + 3])
#define import_pygame_event() IMPORT_PYGAME_MODULE(event, EVENT)
#endif


/* RWOBJECT */
/*the rwobject are only needed for C side work, not accessable from python*/
#define PYGAMEAPI_RWOBJECT_FIRSTSLOT                            \
    (PYGAMEAPI_EVENT_FIRSTSLOT + PYGAMEAPI_EVENT_NUMSLOTS)
#define PYGAMEAPI_RWOBJECT_NUMSLOTS 7
#ifndef PYGAMEAPI_RWOBJECT_INTERNAL
#define RWopsFromObject \
    (*(SDL_RWops*(*)(PyObject*))PyGAME_C_API[PYGAMEAPI_RWOBJECT_FIRSTSLOT + 0])
#define RWopsCheckObject                                               \
    (*(int(*)(SDL_RWops*))PyGAME_C_API[PYGAMEAPI_RWOBJECT_FIRSTSLOT + 1])
#define RWopsFromFileObjectThreaded                                         \
    (*(SDL_RWops*(*)(PyObject*))PyGAME_C_API[PYGAMEAPI_RWOBJECT_FIRSTSLOT + 2])
#define RWopsCheckObjectThreaded                                        \
    (*(int(*)(SDL_RWops*))PyGAME_C_API[PYGAMEAPI_RWOBJECT_FIRSTSLOT + 3])
#define RWopsEncodeFilePath \
    (*(PyObject*(*)(PyObject*, PyObject*)) \
        PyGAME_C_API[PYGAMEAPI_RWOBJECT_FIRSTSLOT + 4])
#define RWopsEncodeString \
    (*(PyObject*(*)(PyObject*, const char*, const char*, PyObject*)) \
        PyGAME_C_API[PYGAMEAPI_RWOBJECT_FIRSTSLOT + 5])
#define RWopsFromFileObject                                         \
    (*(SDL_RWops*(*)(PyObject*))PyGAME_C_API[PYGAMEAPI_RWOBJECT_FIRSTSLOT + 6])
#define import_pygame_rwobject() IMPORT_PYGAME_MODULE(rwobject, RWOBJECT)

/* For backward compatibility */
#define RWopsFromPython RWopsFromObject
#define RWopsCheckPython RWopsCheckObject
#define RWopsFromPythonThreaded RWopsFromFileObjectThreaded
#define RWopsCheckPythonThreaded RWopsCheckObjectThreaded
#endif

/* PixelArray */
#define PYGAMEAPI_PIXELARRAY_FIRSTSLOT                                 \
    (PYGAMEAPI_RWOBJECT_FIRSTSLOT + PYGAMEAPI_RWOBJECT_NUMSLOTS)
#define PYGAMEAPI_PIXELARRAY_NUMSLOTS 2
#ifndef PYGAMEAPI_PIXELARRAY_INTERNAL
#define PyPixelArray_Check(x)                                           \
    ((x)->ob_type == (PyTypeObject*)                                    \
     PyGAME_C_API[PYGAMEAPI_PIXELARRAY_FIRSTSLOT + 0])
#define PyPixelArray_New                                                \
    (*(PyObject*(*)) PyGAME_C_API[PYGAMEAPI_PIXELARRAY_FIRSTSLOT + 1])
#define import_pygame_pixelarray() IMPORT_PYGAME_MODULE(pixelarray, PIXELARRAY)
#endif /* PYGAMEAPI_PIXELARRAY_INTERNAL */

/* Color */
#define PYGAMEAPI_COLOR_FIRSTSLOT                                       \
    (PYGAMEAPI_PIXELARRAY_FIRSTSLOT + PYGAMEAPI_PIXELARRAY_NUMSLOTS)
#define PYGAMEAPI_COLOR_NUMSLOTS 4
#ifndef PYGAMEAPI_COLOR_INTERNAL
#define PyColor_Check(x)                                                \
    ((x)->ob_type == (PyTypeObject*)                                    \
        PyGAME_C_API[PYGAMEAPI_COLOR_FIRSTSLOT + 0])
#define PyColor_Type (*(PyObject *) PyGAME_C_API[PYGAMEAPI_COLOR_FIRSTSLOT])
#define PyColor_New                                                     \
    (*(PyObject *(*)(Uint8*)) PyGAME_C_API[PYGAMEAPI_COLOR_FIRSTSLOT + 1])
#define PyColor_NewLength                                               \
    (*(PyObject *(*)(Uint8*, Uint8)) PyGAME_C_API[PYGAMEAPI_COLOR_FIRSTSLOT + 3])

#define RGBAFromColorObj                                                \
    (*(int(*)(PyObject*, Uint8*)) PyGAME_C_API[PYGAMEAPI_COLOR_FIRSTSLOT + 2])
#define import_pygame_color() IMPORT_PYGAME_MODULE(color, COLOR)
#endif /* PYGAMEAPI_COLOR_INTERNAL */


/* Math */
#define PYGAMEAPI_MATH_FIRSTSLOT                                       \
    (PYGAMEAPI_COLOR_FIRSTSLOT + PYGAMEAPI_COLOR_NUMSLOTS)
#define PYGAMEAPI_MATH_NUMSLOTS 2
#ifndef PYGAMEAPI_MATH_INTERNAL
#define PyVector2_Check(x)                                                \
    ((x)->ob_type == (PyTypeObject*)                                    \
        PyGAME_C_API[PYGAMEAPI_MATH_FIRSTSLOT + 0])
#define PyVector3_Check(x)                                                \
    ((x)->ob_type == (PyTypeObject*)                                    \
        PyGAME_C_API[PYGAMEAPI_MATH_FIRSTSLOT + 1])
/*
#define PyVector2_New                                             \
    (*(PyObject*(*)) PyGAME_C_API[PYGAMEAPI_MATH_FIRSTSLOT + 1])
*/
#define import_pygame_math() IMPORT_PYGAME_MODULE(math, MATH)
#endif /* PYGAMEAPI_MATH_INTERNAL */

#define PG_CAPSULE_NAME(m) (IMPPREFIX m "." PYGAMEAPI_LOCAL_ENTRY)

#define _IMPORT_PYGAME_MODULE(module, MODULE, api_root) {                   \
        PyObject *_module = PyImport_ImportModule (IMPPREFIX #module);      \
                                                                            \
        if (_module != NULL) {                                              \
            PyObject *_c_api =                                              \
                PyObject_GetAttrString (_module, PYGAMEAPI_LOCAL_ENTRY);    \
                                                                            \
            Py_DECREF (_module);                                            \
            if (_c_api != NULL && PyCapsule_CheckExact (_c_api)) {          \
                void **localptr =                                           \
                    (void**) PyCapsule_GetPointer (_c_api,                  \
                         PG_CAPSULE_NAME(#module));                         \
                                                                            \
                if (localptr != NULL) {                                     \
                    memcpy (api_root + PYGAMEAPI_##MODULE##_FIRSTSLOT,      \
                            localptr,                                       \
                            sizeof(void **)*PYGAMEAPI_##MODULE##_NUMSLOTS); \
                }                                                           \
            }                                                               \
            Py_XDECREF(_c_api);                                             \
        }                                                                   \
    }

#ifndef NO_PYGAME_C_API
#define IMPORT_PYGAME_MODULE(module, MODULE)                                \
    _IMPORT_PYGAME_MODULE(module, MODULE, PyGAME_C_API)
#define PYGAMEAPI_TOTALSLOTS                                                \
    (PYGAMEAPI_MATH_FIRSTSLOT + PYGAMEAPI_MATH_NUMSLOTS)

#ifdef PYGAME_H
void* PyGAME_C_API[PYGAMEAPI_TOTALSLOTS] = { NULL };
#else
extern void* PyGAME_C_API[PYGAMEAPI_TOTALSLOTS];
#endif
#endif

#if PG_HAVE_CAPSULE
#define encapsulate_api(ptr, module) \
    PyCapsule_New(ptr, PG_CAPSULE_NAME(module), NULL)
#else
#define encapsulate_api(ptr, module) \
    PyCObject_FromVoidPtr(ptr, NULL)
#endif

/*last platform compiler stuff*/
#if defined(macintosh) && defined(__MWERKS__) || defined(__SYMBIAN32__)
#define PYGAME_EXPORT __declspec(export)
#else
#define PYGAME_EXPORT
#endif

#if defined(__SYMBIAN32__) && PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION == 2

// These are missing from Python 2.2
#ifndef Py_RETURN_NONE

#define Py_RETURN_NONE     return Py_INCREF(Py_None), Py_None
#define Py_RETURN_TRUE     return Py_INCREF(Py_True), Py_True
#define Py_RETURN_FALSE    return Py_INCREF(Py_False), Py_False

#ifndef intrptr_t
#define intptr_t int

// No PySlice_GetIndicesEx on Py 2.2
#define PySlice_GetIndicesEx(a,b,c,d,e,f) PySlice_GetIndices(a,b,c,d,e)

#define PyBool_FromLong(x) Py_BuildValue("b", x)
#endif

// _symport_free and malloc are not exported in python.dll
// See http://discussion.forum.nokia.com/forum/showthread.php?t=57874
#undef PyObject_NEW
#define PyObject_NEW PyObject_New
#undef PyMem_MALLOC
#define PyMem_MALLOC PyMem_Malloc
#undef PyObject_DEL
#define PyObject_DEL PyObject_Del

#endif // intptr_t

#endif // __SYMBIAN32__ Python 2.2.2

#endif /* PYGAME_H */
