//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

#define STACK_SIZE (1024*1024)

// Keep one stack around to avoid the overhead of repeated malloc/free in
// case of frequent instantiations in a loop.
static void *last_stack = NULL;

void initFiber( Fiber *to )
{
    assert( to );

    to->ss_sp = NULL;
}

void prepareFiber( Fiber *to, void *code, unsigned long arg )
{
    assert( to );
    assert( code );

    to->ss_size = STACK_SIZE;
    to->ss_sp = last_stack ? last_stack : malloc( STACK_SIZE );
    last_stack = NULL;

    // TODO: Is CONTEXT_FULL needed?
    to->f_context.ContextFlags = CONTEXT_FULL;
    int res = GetThreadContext( GetCurrentThread(), &to->f_context );

    assert( res != 0 );

    // Stack pointer from the bottem side with one argument reserved.
    char *sp = (char *) (size_t) to->ss_sp + to->ss_size - 8;
    memcpy( sp, &arg, sizeof(unsigned long) );

    // Set the instruction pointer
    to->f_context.Eip = (unsigned long)code;

    // Set the stack pointer
    to->f_context.Esp = (unsigned long)sp - 4;
}

void releaseFiber( Fiber *to )
{
    assert( to );

    if ( last_stack == NULL )
    {
        last_stack = to->ss_sp;
    }
    else
    {
        free( to->ss_sp );
    }
}

void swapFiber( Fiber *to, Fiber *from )
{
    assert( to );
    assert( from );

    to->f_context.ContextFlags = CONTEXT_FULL;
    int res = GetThreadContext( GetCurrentThread(), &to->f_context );

    assert( res != 0 );

    res = SetThreadContext( GetCurrentThread(), &from->f_context );

    assert( res != 0 );
}
