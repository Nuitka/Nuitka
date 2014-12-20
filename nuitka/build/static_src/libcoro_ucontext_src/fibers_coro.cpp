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
// Implementation of process context switch for generic targets.

#include "nuitka/prelude.hpp"

extern "C" {
#include "coro.h"
}

// TODO: Make stack size rational.
#define STACK_SIZE (1024*1024)

// Keep one stack around to avoid the overhead of repeated malloc/free in
// case of frequent instantiations in a loop.
static void *last_stack = NULL;

void _initFiber( Fiber *to )
{
    /* Not much to do. */
    to->sptr = NULL;
}

int _prepareFiber( Fiber *to, void *code, uintptr_t arg )
{
    /* Need to allocate stack manually. */
    to->sptr = last_stack ? (char *)last_stack : (char *)malloc( STACK_SIZE );
    coro_create( &to->coro_ctx, (coro_func)code, (void *)arg, to->sptr, STACK_SIZE );

    return 0;
}

void _releaseFiber( Fiber *to )
{
    if ( to->sptr != NULL )
    {
        if ( last_stack == NULL && false )
        {
            last_stack = to->sptr;
        }
        else
        {
            free( to->sptr );
        }

        to->sptr = NULL;
    }
}

void _swapFiber( Fiber *to, Fiber *from )
{
    assert( to->sptr );
    assert( from->sptr );

    coro_transfer( &to->coro_ctx, &from->coro_ctx );
}
