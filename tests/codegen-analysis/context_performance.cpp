//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
//
//     Python test originally created or extracted from other peoples work. The
//     parts from me are licensed as below. It is at least Free Software where
//     it's copied from other people. In these cases, that will normally be
//     indicated.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
//
// Small program to benchmark the context switches.

#include <ucontext.h>

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

ucontext_t m_yielder_context;
ucontext_t m_caller_context;

static void *last_stack = NULL;

int return_value = 1;

#define MAX_TIMES (10000000)

// Context function
static void m_code( unsigned long value )
{
    for( int i = MAX_TIMES; i > 0; i-- )
    {
        return_value = i;

        swapcontext( &m_yielder_context, &m_caller_context );
    }

    return_value = 0;
    swapcontext( &m_yielder_context, &m_caller_context );
}

int main()
{
    // Nuitka_Generator_New
    m_yielder_context.uc_stack.ss_sp = NULL;
    m_yielder_context.uc_link = NULL;

    // Nuitka_Generator_send first time
    m_yielder_context.uc_stack.ss_size = 1024*1024;
    m_yielder_context.uc_stack.ss_sp = last_stack ? last_stack : malloc( m_yielder_context.uc_stack.ss_size );
    last_stack = NULL;

    int res = getcontext( &m_yielder_context );
    assert( res == 0 );

    makecontext( &m_yielder_context, (void (*)())m_code, 1, (unsigned long)27 );

    while ( return_value > 0 )
    {
        swapcontext( &m_caller_context, &m_yielder_context );
        // printf( "%ld\n", return_value );
    }

    // puts( "completed!" );

    return 0;
}
