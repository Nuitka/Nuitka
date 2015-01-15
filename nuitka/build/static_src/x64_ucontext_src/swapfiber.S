//     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

.globl _swapFiber
_swapFiber:

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
