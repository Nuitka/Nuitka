/* Extract of libtask, just the ARM specific portions. */

/*

This software was developed as part of a project at MIT.

Copyright (c) 2005-2007 Russ Cox,
                   Massachusetts Institute of Technology

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

===

Contains parts of an earlier library that has:

 * The authors of this software are Rob Pike, Sape Mullender, and Russ Cox
 *       Copyright (c) 2003 by Lucent Technologies.
 * Permission to use, copy, modify, and distribute this software for any
 * purpose without fee is hereby granted, provided that this entire notice
 * is included in all copies of any software which is or includes a copy
 * or modification of this software and in all copies of the supporting
 * documentation for such software.
 * THIS SOFTWARE IS BEING PROVIDED "AS IS", WITHOUT ANY EXPRESS OR IMPLIED
 * WARRANTY.  IN PARTICULAR, NEITHER THE AUTHORS NOR LUCENT TECHNOLOGIES MAKE ANY
 * REPRESENTATION OR WARRANTY OF ANY KIND CONCERNING THE MERCHANTABILITY
 * OF THIS SOFTWARE OR ITS FITNESS FOR ANY PARTICULAR PURPOSE.
*/

#include "ucontext.h"

#include <stdarg.h>
#include <assert.h>

void makecontext(ucontext_t *uc, void (*fn)(void), int argc, ...)
{
    int *sp;
    va_list arg;

    sp = (int*)uc->uc_stack.ss_sp+uc->uc_stack.ss_size/4;
    va_start(arg, argc);

    assert( argc == 1 ); // That allows me to hard code r0
    uc->uc_mcontext.trap_no = va_arg(arg, unsigned long);

    va_end(arg);

    uc->uc_mcontext.arm_r10 = (unsigned long)sp;
    uc->uc_mcontext.arm_fp = (unsigned long)fn;
}
