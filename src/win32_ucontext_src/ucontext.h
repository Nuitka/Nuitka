/*
 *      win32-ucontext: Unix ucontext_t operations on Windows platforms
 *      Copyright(C) 2007 Panagiotis E. Hadjidoukas
 *
 *      Contact Email: phadjido@cs.uoi.gr, xdoukas@ceid.upatras.gr
 *
 *      win32-ucontext is free software; you can redistribute it and/or
 *      modify it under the terms of the GNU Lesser General Public
 *      License as published by the Free Software Foundation; either
 *      version 2 of the License, or (at your option) any later version.
 *
 *      win32-ucontext is distributed in the hope that it will be useful,
 *      but WITHOUT ANY WARRANTY; without even the implied warranty of
 *      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *      Lesser General Public License for more details.
 *
 *      You should have received a copy of the GNU Lesser General Public
 *      License along with QueueUserAPCEx in the file COPYING.LIB;
 *      if not, write to the Free Software Foundation, Inc.,
 *      59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
 */

#ifndef UCONTEXT_H
#define UCONTEXT_H

#include <windows.h>

typedef struct __stack {
	void *ss_sp;
	size_t ss_size;
	int ss_flags;
} stack_t;

typedef CONTEXT mcontext_t;
typedef unsigned long __sigset_t;

typedef struct __ucontext {
	unsigned long int	uc_flags;
	struct __ucontext	*uc_link;
	stack_t				uc_stack;
	mcontext_t			uc_mcontext; 
	__sigset_t			uc_sigmask;
} ucontext_t;


int getcontext(ucontext_t *ucp);
int setcontext(const ucontext_t *ucp);
int makecontext(ucontext_t *, void (*)(), int, ...);
int swapcontext(ucontext_t *, const ucontext_t *);

#endif /* UCONTEXT_H */