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
