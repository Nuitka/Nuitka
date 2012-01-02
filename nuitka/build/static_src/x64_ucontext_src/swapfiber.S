//
//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at a later time to
//     the PSF. With this version of Nuitka, using it for a Closed Source and
//     distributing the binary only is not allowed.
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//
// Implementation of process context switch "swapFiber" for x64

#define oRBP 120
#define oRSP 160
#define oRBX 128
#define oR8 40
#define oR9 48
#define oR12 72
#define oR13 80
#define oR14 88
#define oR15 96
#define oRDI 104
#define oRSI 112
#define oRDX 136
#define oRCX 152
#define oRIP 168
#define oFPREGS 224
#define oFPREGSMEM 424

.globl swapFiber
swapFiber:

    // Save the preserved used for passing args and the return address.
    movq %rbx, oRBX(%rdi)
    movq %rbp, oRBP(%rdi)
    movq %r12, oR12(%rdi)
    movq %r13, oR13(%rdi)
    movq %r14, oR14(%rdi)
    movq %r15, oR15(%rdi)

    movq %rdi, oRDI(%rdi)
    movq %rsi, oRSI(%rdi)
    movq %rdx, oRDX(%rdi)
    movq %rcx, oRCX(%rdi)
    movq %r8, oR8(%rdi)
    movq %r9, oR9(%rdi)

    movq (%rsp), %rcx
    movq %rcx, oRIP(%rdi)

    // Make room for return address.
    leaq 8(%rsp), %rcx
    movq %rcx, oRSP(%rdi)

    // Separate floating-point register content memory
    leaq oFPREGSMEM(%rdi), %rcx
    movq %rcx, oFPREGS(%rdi)

    // Load the new stack pointer and the preserved registers.
    movq oRSP(%rsi), %rsp
    movq oRBX(%rsi), %rbx
    movq oRBP(%rsi), %rbp
    movq oR12(%rsi), %r12
    movq oR13(%rsi), %r13
    movq oR14(%rsi), %r14
    movq oR15(%rsi), %r15

    // We should return to the address provided, put it on top of stack.
    movq oRIP(%rsi), %rcx
    pushq   %rcx

    // Setup registers for arguments.
    movq oRDI(%rsi), %rdi
    movq oRDX(%rsi), %rdx
    movq oRCX(%rsi), %rcx
    movq oR8(%rsi), %r8
    movq oR9(%rsi), %r9

    // Setup %rsi.
    movq    oRSI(%rsi), %rsi

    ret
