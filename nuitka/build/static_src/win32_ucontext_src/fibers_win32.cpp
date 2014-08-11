//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
// Implementation of process context switch for Win32

#include "nuitka/prelude.hpp"

// Less than 1MB is ignored on Win32 apparently.
#define STACK_SIZE (1024*1024)

void _initFiber( Fiber *to )
{
    // Need to call this at least once per thread, so we have a main FIBER.
    ConvertThreadToFiber( NULL );
    to->fiber = NULL;
}

int _prepareFiber( Fiber *to, void *code, intptr_t arg )
{
    to->fiber = CreateFiber( STACK_SIZE, (LPFIBER_START_ROUTINE)code, (LPVOID)arg );
    return to->fiber != NULL ? 0 : 1;
}

void _releaseFiber( Fiber *to )
{
    if ( to->fiber )
    {
        DeleteFiber( to->fiber );
        to->fiber = NULL;
    }
}

void _swapFiber( Fiber *to, Fiber *from )
{
    to->fiber = GetCurrentFiber();

    assert( from->fiber != NULL );
    SwitchToFiber( from->fiber );
}
