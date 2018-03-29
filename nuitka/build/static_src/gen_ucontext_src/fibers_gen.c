//     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "nuitka/prelude.h"

// TODO: Make stack size rational.
#define STACK_SIZE (1024*1024)

// Keep one stack around to avoid the overhead of repeated malloc/free in
// case of frequent instantiations in a loop.
static void *last_stack = NULL;

void _initFiber( Fiber *to )
{
    to->f_context.uc_stack.ss_sp = NULL;
    to->f_context.uc_link = NULL;
    to->start_stack = NULL;
}

int _prepareFiber( Fiber *to, void *code, uintptr_t arg )
{
    int res = getcontext( &to->f_context );
    if (unlikely( res != 0 ))
    {
        return 1;
    }

    to->f_context.uc_stack.ss_size = STACK_SIZE;
    to->f_context.uc_stack.ss_sp = last_stack ? (char *)last_stack : (char *)malloc( STACK_SIZE );
    to->start_stack = to->f_context.uc_stack.ss_sp;
    to->f_context.uc_link = NULL;
    last_stack = NULL;

    makecontext( &to->f_context, (void (*)())code, 1, (unsigned long)arg );

    return 0;
}

void _releaseFiber( Fiber *to )
{
    if ( to->start_stack != NULL )
    {
        if ( last_stack == NULL )
        {
            last_stack = to->start_stack;
        }
        else
        {
            free( to->start_stack );
        }

        to->start_stack = NULL;
    }
}

void _swapFiber( Fiber *to, Fiber *from )
{
    int res = swapcontext( &to->f_context, &from->f_context );

    assert( res == 0 );
}
