//
//     Kay Hayen, mailto:kayhayen@gmx.de
//
//     Python test originally created or extracted from other peoples work. The
//     parts from me are in the public domain. It is at least Free Software
//     where it's copied from other people. In these cases, it will normally be
//     indicated.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
//
//     Please leave the whole of this copyright notice intact.
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
