// Implementation of process context switch for ARM

#include "nuitka/prelude.hpp"

extern "C" int getmcontext( mcontext_t *mcontext );
extern "C" void setmcontext( const mcontext_t *mcontext );

#define setcontext(u) setmcontext( &(u)->uc_mcontext )
#define getcontext(u) getmcontext( &(u)->uc_mcontext )

void makecontext( ucontext_t *uc, void (*fn)(void), int argc, ... );

#define STACK_SIZE (1024*1024)

// Keep one stack around to avoid the overhead of repeated malloc/free in
// case of frequent instantiations in a loop.
static void *last_stack = NULL;

void initFiber( Fiber *to )
{
    to->f_context.uc_stack.ss_sp = NULL;
    to->f_context.uc_link = NULL;
}

void prepareFiber( Fiber *to, void *code, unsigned long arg )
{
    to->f_context.uc_stack.ss_size = STACK_SIZE;
    to->f_context.uc_stack.ss_sp = last_stack ? last_stack : malloc( STACK_SIZE );
    last_stack = NULL;

    int res = getcontext( &to->f_context );
    assert( res == 0 );

    makecontext( &to->f_context, (void (*)())code, 1, (unsigned long)arg );
}

void releaseFiber( Fiber *to )
{
    if ( last_stack == NULL )
    {
        last_stack = to->f_context.uc_stack.ss_sp;
    }
    else
    {
        free( to->f_context.uc_stack.ss_sp );
    }
}

void swapFiber( Fiber *to, Fiber *from )
{
    if ( getcontext( &to->f_context ) == 0 )
    {
        setcontext( &from->f_context );
    }
}
