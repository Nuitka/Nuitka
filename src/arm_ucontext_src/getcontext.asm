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


.globl getmcontext
getmcontext:
        str     r1, [r0,#4]
        str     r2, [r0,#8]
        str     r3, [r0,#12]
        str     r4, [r0,#16]
        str     r5, [r0,#20]
        str     r6, [r0,#24]
        str     r7, [r0,#28]
        str     r8, [r0,#32]
        str     r9, [r0,#36]
        str     r10, [r0,#40]
        str     r11, [r0,#44]
        str     r12, [r0,#48]
        str     r13, [r0,#52]
        str     r14, [r0,#56]
        /* store 1 as r0-to-restore */
        mov     r1, #1
        str     r1, [r0]
        /* return 0 */
        mov     r0, #0
        mov     pc, lr

.globl setmcontext
setmcontext:
        ldr     r1, [r0,#4]
        ldr     r2, [r0,#8]
        ldr     r3, [r0,#12]
        ldr     r4, [r0,#16]
        ldr     r5, [r0,#20]
        ldr     r6, [r0,#24]
        ldr     r7, [r0,#28]
        ldr     r8, [r0,#32]
        ldr     r9, [r0,#36]
        ldr     r10, [r0,#40]
        ldr     r11, [r0,#44]
        ldr     r12, [r0,#48]
        ldr     r13, [r0,#52]
        ldr     r14, [r0,#56]
        ldr     r0, [r0]
        mov     pc, lr
