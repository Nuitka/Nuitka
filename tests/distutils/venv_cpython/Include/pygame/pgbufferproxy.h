/*
  pygame - Python Game Library
  Copyright (C) 2000-2001  Pete Shinners
  Copyright (C) 2007  Rene Dudfield, Richard Goedeken

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

/* Bufferproxy module C api.
   Depends on pygame.h being included first.
 */
#if !defined(PG_BUFPROXY_HEADER)

#define PYGAMEAPI_BUFPROXY_NUMSLOTS 4
#define PYGAMEAPI_BUFPROXY_FIRSTSLOT 0

#if !(defined(PYGAMEAPI_BUFPROXY_INTERNAL) || defined(NO_PYGAME_C_API))
static void *PgBUFPROXY_C_API[PYGAMEAPI_BUFPROXY_NUMSLOTS];

typedef PyObject *(*_pgbufproxy_new_t)(PyObject *, getbufferproc);
typedef PyObject *(*_pgbufproxy_get_obj_t)(PyObject *);
typedef int (*_pgbufproxy_trip_t)(PyObject *);

#define PgBufproxy_Type (*(PyTypeObject*)PgBUFPROXY_C_API[0])
#define PgBufproxy_New (*(_pgbufproxy_new_t)PgBUFPROXY_C_API[1])
#define PgBufproxy_GetParent \
    (*(_pgbufproxy_get_obj_t)PgBUFPROXY_C_API[2])
#define PgBufproxy_Trip (*(_pgbufproxy_trip_t)PgBUFPROXY_C_API[3])
#define PgBufproxy_Check(x) ((x)->ob_type == (PgBufproxy_Type))
#define import_pygame_bufferproxy() \
    _IMPORT_PYGAME_MODULE(bufferproxy, BUFPROXY, PgBUFPROXY_C_API)

#endif /* #if !(defined(PYGAMEAPI_BUFPROXY_INTERNAL) || ... */

#define PG_BUFPROXY_HEADER

#endif /* #if !defined(PG_BUFPROXY_HEADER) */
