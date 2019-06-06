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

#include <Python.h>
#if defined(HAVE_SNPRINTF)  /* also defined in SDL_ttf (SDL.h) */
#undef HAVE_SNPRINTF        /* remove GCC macro redefine warning */
#endif
#include <SDL_ttf.h>


/* test font initialization */
#define FONT_INIT_CHECK() \
    if(!(*(int*)PyFONT_C_API[2])) \
        return RAISE(PyExc_SDLError, "font system not initialized")



#define PYGAMEAPI_FONT_FIRSTSLOT 0
#define PYGAMEAPI_FONT_NUMSLOTS 3
typedef struct {
  PyObject_HEAD
  TTF_Font* font;
  PyObject* weakreflist;
} PyFontObject;
#define PyFont_AsFont(x) (((PyFontObject*)x)->font)

#ifndef PYGAMEAPI_FONT_INTERNAL
#define PyFont_Check(x) ((x)->ob_type == (PyTypeObject*)PyFONT_C_API[0])
#define PyFont_Type (*(PyTypeObject*)PyFONT_C_API[0])
#define PyFont_New (*(PyObject*(*)(TTF_Font*))PyFONT_C_API[1])
/*slot 2 taken by FONT_INIT_CHECK*/

#define import_pygame_font() \
    _IMPORT_PYGAME_MODULE(font, FONT, PyFONT_C_API)

static void* PyFONT_C_API[PYGAMEAPI_FONT_NUMSLOTS] = {NULL};
#endif

