#ifndef _FASTEVENTS_H_
#define _FASTEVENTS_H_
/*
    NET2 is a threaded, event based, network IO library for SDL.
    Copyright (C) 2002 Bob Pendleton

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public License
    as published by the Free Software Foundation; either version 2.1
    of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free
    Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
    02111-1307 USA

    If you do not wish to comply with the terms of the LGPL please
    contact the author as other terms are available for a fee.

    Bob Pendleton
    Bob@Pendleton.com
*/

#include "SDL.h"

#ifdef __cplusplus
extern "C" {
#endif

  int FE_Init(void);                     // Initialize FE
  void FE_Quit(void);                    // shutdown FE

  void FE_PumpEvents(void);              // replacement for SDL_PumpEvents
  int FE_PollEvent(SDL_Event *event);    // replacement for SDL_PollEvent
  int FE_WaitEvent(SDL_Event *event);    // replacement for SDL_WaitEvent
  int FE_PushEvent(SDL_Event *event);    // replacement for SDL_PushEvent

  char *FE_GetError(void);               // get the last error
#ifdef __cplusplus
}
#endif

#endif
