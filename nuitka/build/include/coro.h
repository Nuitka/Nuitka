/*
 * Copyright (c) 2001-2012 Marc Alexander Lehmann <schmorp@schmorp.de>
 *
 * Redistribution and use in source and binary forms, with or without modifica-
 * tion, are permitted provided that the following conditions are met:
 *
 *   1.  Redistributions of source code must retain the above copyright notice,
 *       this list of conditions and the following disclaimer.
 *
 *   2.  Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MER-
 * CHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO
 * EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPE-
 * CIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTH-
 * ERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Alternatively, the contents of this file may be used under the terms of
 * the GNU General Public License ("GPL") version 2 or any later version,
 * in which case the provisions of the GPL are applicable instead of
 * the above. If you wish to allow the use of your version of this file
 * only under the terms of the GPL and not to allow others to use your
 * version of this file under the BSD license, indicate your decision
 * by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL. If you do not delete the
 * provisions above, a recipient may use your version of this file under
 * either the BSD or the GPL.
 *
 * This library is modelled strictly after Ralf S. Engelschalls article at
 * http://www.gnu.org/software/pth/rse-pmt.ps. So most of the credit must
 * go to Ralf S. Engelschall <rse@engelschall.com>.
 *
 * This coroutine library is very much stripped down. You should either
 * build your own process abstraction using it or - better - just use GNU
 * Portable Threads, http://www.gnu.org/software/pth/.
 *
 */

/*
 * 2006-10-26 Include stddef.h on OS X to work around one of its bugs.
 *            Reported by Michael_G_Schwern.
 * 2006-11-26 Use _setjmp instead of setjmp on GNU/Linux.
 * 2007-04-27 Set unwind frame info if gcc 3+ and ELF is detected.
 *            Use _setjmp instead of setjmp on _XOPEN_SOURCE >= 600.
 * 2007-05-02 Add assembly versions for x86 and amd64 (to avoid reliance
 *            on SIGUSR2 and sigaltstack in Crossfire).
 * 2008-01-21 Disable CFI usage on anything but GNU/Linux.
 * 2008-03-02 Switched to 2-clause BSD license with GPL exception.
 * 2008-04-04 New (but highly unrecommended) pthreads backend.
 * 2008-04-24 Reinstate CORO_LOSER (had wrong stack adjustments).
 * 2008-10-30 Support assembly method on x86 with and without frame pointer.
 * 2008-11-03 Use a global asm statement for CORO_ASM, idea by pippijn.
 * 2008-11-05 Hopefully fix misaligned stacks with CORO_ASM/SETJMP.
 * 2008-11-07 rbp wasn't saved in CORO_ASM on x86_64.
 *            introduce coro_destroy, which is a nop except for pthreads.
 *            speed up CORO_PTHREAD. Do no longer leak threads either.
 *            coro_create now allows one to create source coro_contexts.
 *            do not rely on makecontext passing a void * correctly.
 *            try harder to get _setjmp/_longjmp.
 *            major code cleanup/restructuring.
 * 2008-11-10 the .cfi hacks are no longer needed.
 * 2008-11-16 work around a freebsd pthread bug.
 * 2008-11-19 define coro_*jmp symbols for easier porting.
 * 2009-06-23 tentative win32-backend support for mingw32 (Yasuhiro Matsumoto).
 * 2010-12-03 tentative support for uclibc (which lacks all sorts of things).
 * 2011-05-30 set initial callee-saved-registers to zero with CORO_ASM.
 *            use .cfi_undefined rip on linux-amd64 for better backtraces.
 * 2011-06-08 maybe properly implement weird windows amd64 calling conventions.
 * 2011-07-03 rely on __GCC_HAVE_DWARF2_CFI_ASM for cfi detection.
 * 2011-08-08 cygwin trashes stacks, use pthreads with double stack on cygwin.
 * 2012-12-04 reduce misprediction penalty for x86/amd64 assembly switcher.
 * 2012-12-05 experimental fiber backend (allocates stack twice).
 * 2012-12-07 API version 3 - add coro_stack_alloc/coro_stack_free.
 * 2012-12-21 valgrind stack registering was broken.
 */

#ifndef CORO_H
#define CORO_H

#if __cplusplus
extern "C" {
#endif

/*
 * This library consists of only three files
 * coro.h, coro.c and LICENSE (and optionally README)
 *
 * It implements what is known as coroutines, in a hopefully
 * portable way.
 *
 * All compiletime symbols must be defined both when including coro.h
 * (using libcoro) as well as when compiling coro.c (the implementation).
 *
 * You can manually specify which flavour you want. If you don't define
 * any of these, libcoro tries to choose a safe and fast default:
 *
 * -DCORO_UCONTEXT
 *
 *    This flavour uses SUSv2's get/set/swap/makecontext functions that
 *    unfortunately only some unices support, and is quite slow.
 *
 * -DCORO_SJLJ
 *
 *    This flavour uses SUSv2's setjmp/longjmp and sigaltstack functions to
 *    do it's job. Coroutine creation is much slower than UCONTEXT, but
 *    context switching is a bit cheaper. It should work on almost all unices.
 *
 * -DCORO_LINUX
 *
 *    CORO_SJLJ variant.
 *    Old GNU/Linux systems (<= glibc-2.1) only work with this implementation
 *    (it is very fast and therefore recommended over other methods, but
 *    doesn't work with anything newer).
 *
 * -DCORO_LOSER
 *
 *    CORO_SJLJ variant.
 *    Microsoft's highly proprietary platform doesn't support sigaltstack, and
 *    this selects a suitable workaround for this platform. It might not work
 *    with your compiler though - it has only been tested with MSVC 6.
 *
 * -DCORO_FIBER
 *
 *    Slower, but probably more portable variant for the Microsoft operating
 *    system, using fibers. Ignores the passed stack and allocates it internally.
 *    Also, due to bugs in cygwin, this does not work with cygwin.
 *
 * -DCORO_IRIX
 *
 *    CORO_SJLJ variant.
 *    For SGI's version of Microsoft's NT ;)
 *
 * -DCORO_ASM
 *
 *    Hand coded assembly, known to work only on a few architectures/ABI:
 *    GCC + x86/IA32 and amd64/x86_64 + GNU/Linux and a few BSDs. Fastest choice,
 *    if it works.
 *
 * -DCORO_PTHREAD
 *
 *    Use the pthread API. You have to provide <pthread.h> and -lpthread.
 *    This is likely the slowest backend, and it also does not support fork(),
 *    so avoid it at all costs.
 *
 * If you define neither of these symbols, coro.h will try to autodetect
 * the best/safest model. To help with the autodetection, you should check
 * (e.g. using autoconf) and define the following symbols: HAVE_UCONTEXT_H
 * / HAVE_SETJMP_H / HAVE_SIGALTSTACK.
 */

/*
 * Changes when the API changes incompatibly.
 * This is ONLY the API version - there is no ABI compatibility between releases.
 *
 * Changes in API version 2:
 * replaced bogus -DCORO_LOOSE with grammatically more correct -DCORO_LOSER
 * Changes in API version 3:
 * introduced stack management (CORO_STACKALLOC)
 */
#define CORO_VERSION 3

#include <stddef.h>

/*
 * This is the type for the initialization function of a new coroutine.
 */
typedef void (*coro_func)(void *);

/*
 * A coroutine state is saved in the following structure. Treat it as an
 * opaque type. errno and sigmask might be saved, but don't rely on it,
 * implement your own switching primitive if you need that.
 */
typedef struct coro_context coro_context;

/*
 * This function creates a new coroutine. Apart from a pointer to an
 * uninitialised coro_context, it expects a pointer to the entry function
 * and the single pointer value that is given to it as argument.
 *
 * Allocating/deallocating the stack is your own responsibility.
 *
 * As a special case, if coro, arg, sptr and ssze are all zero,
 * then an "empty" coro_context will be created that is suitable
 * as an initial source for coro_transfer.
 *
 * This function is not reentrant, but putting a mutex around it
 * will work.
 */
void coro_create (coro_context *ctx, /* an uninitialised coro_context */
                  coro_func coro,    /* the coroutine code to be executed */
                  void *arg,         /* a single pointer passed to the coro */
                  void *sptr,        /* start of stack area */
                  size_t ssze);      /* size of stack area in bytes */

/*
 * The following prototype defines the coroutine switching function. It is
 * sometimes implemented as a macro, so watch out.
 *
 * This function is thread-safe and reentrant.
 */
#if 0
void coro_transfer (coro_context *prev, coro_context *next);
#endif

/*
 * The following prototype defines the coroutine destroy function. It
 * is sometimes implemented as a macro, so watch out. It also serves no
 * purpose unless you want to use the CORO_PTHREAD backend, where it is
 * used to clean up the thread. You are responsible for freeing the stack
 * and the context itself.
 *
 * This function is thread-safe and reentrant.
 */
#if 0
void coro_destroy (coro_context *ctx);
#endif

/*****************************************************************************/
/* optional stack management                                                 */
/*****************************************************************************/
/*
 * You can disable all of the stack management functions by
 * defining CORO_STACKALLOC to 0. Otherwise, they are enabled by default.
 *
 * If stack management is enabled, you can influence the implementation via these
 * symbols:
 *
 * -DCORO_USE_VALGRIND
 *
 *    If defined, then libcoro will include valgrind/valgrind.h and register
 *    and unregister stacks with valgrind.
 *
 * -DCORO_GUARDPAGES=n
 *
 *    libcoro will try to use the specified number of guard pages to protect against
 *    stack overflow. If n is 0, then the feature will be disabled. If it isn't
 *    defined, then libcoro will choose a suitable default. If guardpages are not
 *    supported on the platform, then the feature will be silently disabled.
 */
#ifndef CORO_STACKALLOC
# define CORO_STACKALLOC 1
#endif

#if CORO_STACKALLOC

/*
 * The only allowed operations on these struct members is to read the
 * "sptr" and "ssze" members to pass it to coro_create, to read the "sptr"
 * member to see if it is false, in which case the stack isn't allocated,
 * and to set the "sptr" member to 0, to indicate to coro_stack_free to
 * not actually do anything.
 */

struct coro_stack
{
  void *sptr;
  size_t ssze;
#if CORO_USE_VALGRIND
  int valgrind_id;
#endif
};

/*
 * Try to allocate a stack of at least the given size and return true if
 * successful, or false otherwise.
 *
 * The size is *NOT* specified in bytes, but in units of sizeof (void *),
 * i.e. the stack is typically 4(8) times larger on 32 bit(64 bit) platforms
 * then the size passed in.
 *
 * If size is 0, then a "suitable" stack size is chosen (usually 1-2MB).
 */
int coro_stack_alloc (struct coro_stack *stack, unsigned int size);

/*
 * Free the stack allocated by coro_stack_alloc again. It is safe to
 * call this function on the coro_stack structure even if coro_stack_alloc
 * failed.
 */
void coro_stack_free (struct coro_stack *stack);

#endif

/*
 * That was it. No other user-serviceable parts below here.
 */

/*****************************************************************************/

#if !defined CORO_LOSER      && !defined CORO_UCONTEXT \
    && !defined CORO_SJLJ    && !defined CORO_LINUX \
    && !defined CORO_IRIX    && !defined CORO_ASM \
    && !defined CORO_PTHREAD && !defined CORO_FIBER
# if defined WINDOWS && (defined __i386 || defined __x86_64 || defined _M_IX86 || defined _M_AMD64)
#  define CORO_ASM 1
# elif defined WINDOWS || defined _WIN32
#  define CORO_LOSER 1 /* you don't win with windoze */
# elif __linux && (__i386 || (__x86_64 && !__ILP32))
#  define CORO_ASM 1
# elif defined HAVE_UCONTEXT_H
#  define CORO_UCONTEXT 1
# elif defined HAVE_SETJMP_H && defined HAVE_SIGALTSTACK
#  define CORO_SJLJ 1
# else
error unknown or unsupported architecture
# endif
#endif

/*****************************************************************************/

#if CORO_UCONTEXT

# include <ucontext.h>

struct coro_context
{
  ucontext_t uc;
};

# define coro_transfer(p,n) swapcontext (&((p)->uc), &((n)->uc))
# define coro_destroy(ctx) (void *)(ctx)

#elif CORO_SJLJ || CORO_LOSER || CORO_LINUX || CORO_IRIX

# if defined(CORO_LINUX) && !defined(_GNU_SOURCE)
#  define _GNU_SOURCE /* for glibc */
# endif

# if !CORO_LOSER
#  include <unistd.h>
# endif

/* solaris is hopelessly borked, it expands _XOPEN_UNIX to nothing */
# if __sun
#  undef _XOPEN_UNIX
#  define _XOPEN_UNIX 1
# endif

# include <setjmp.h>

# if _XOPEN_UNIX > 0 || defined (_setjmp)
#  define coro_jmp_buf      jmp_buf
#  define coro_setjmp(env)  _setjmp (env)
#  define coro_longjmp(env) _longjmp ((env), 1)
# elif CORO_LOSER
#  define coro_jmp_buf      jmp_buf
#  define coro_setjmp(env)  setjmp (env)
#  define coro_longjmp(env) longjmp ((env), 1)
# else
#  define coro_jmp_buf      sigjmp_buf
#  define coro_setjmp(env)  sigsetjmp (env, 0)
#  define coro_longjmp(env) siglongjmp ((env), 1)
# endif

struct coro_context
{
  coro_jmp_buf env;
};

# define coro_transfer(p,n) do { if (!coro_setjmp ((p)->env)) coro_longjmp ((n)->env); } while (0)
# define coro_destroy(ctx) (void *)(ctx)

#elif CORO_ASM

struct coro_context
{
  void **sp; /* must be at offset 0 */
};

void __attribute__ ((__noinline__, __regparm__(2)))
coro_transfer (coro_context *prev, coro_context *next);

# define coro_destroy(ctx) (void *)(ctx)

#elif CORO_PTHREAD

# include <pthread.h>

extern pthread_mutex_t coro_mutex;

struct coro_context
{
  pthread_cond_t cv;
  pthread_t id;
};

void coro_transfer (coro_context *prev, coro_context *next);
void coro_destroy (coro_context *ctx);

#elif CORO_FIBER

struct coro_context
{
  void *fiber;
  /* only used for initialisation */
  coro_func coro;
  void *arg;
};

void coro_transfer (coro_context *prev, coro_context *next);
void coro_destroy (coro_context *ctx);

#endif

#if __cplusplus
}
#endif

#endif

