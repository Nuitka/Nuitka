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

// TODO: Make stack size rational.
#define STACK_SIZE (1024*1024)

void initFiber( Fiber *to )
{
    // Need to call this at least once per thread, so we have a main FIBER.
    ConvertThreadToFiber( NULL );

    assert( to );
    to->fiber = NULL;
}

void prepareFiber( Fiber *to, void *code, intptr_t arg )
{
    assert( to );
    assert( code );

    to->fiber = CreateFiber( STACK_SIZE, (LPFIBER_START_ROUTINE)code, (LPVOID)arg );
}

void releaseFiber( Fiber *to )
{
    if ( to->fiber )
    {
        DeleteFiber( to->fiber );
    }
    to->fiber = NULL;
}

void swapFiber( Fiber *to, Fiber *from )
{
    to->fiber = GetCurrentFiber();

    assert( from->fiber );
    SwitchToFiber( from->fiber );
}
