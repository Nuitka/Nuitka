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

#include "ucontext.h"

int getcontext(ucontext_t *ucp)
{
	int ret;

	/* Retrieve the full machine context */
	ucp->uc_mcontext.ContextFlags = CONTEXT_FULL;
	ret = GetThreadContext(GetCurrentThread(), &ucp->uc_mcontext);

	return (ret == 0) ? -1: 0;
}

int setcontext(const ucontext_t *ucp)
{
	int ret;
	
	/* Restore the full machine context (already set) */
	ret = SetThreadContext(GetCurrentThread(), &ucp->uc_mcontext);

	return (ret == 0) ? -1: 0;
}

int makecontext(ucontext_t *ucp, void (*func)(), int argc, ...)
{
	int i;
    va_list ap;
	char *sp;

	/* Stack grows down */
	sp = (char *) (size_t) ucp->uc_stack.ss_sp + ucp->uc_stack.ss_size;	

	/* Reserve stack space for the arguments (maximum possible: argc*(8 bytes per argument)) */
	sp -= argc*8;

	if ( sp < (char *)ucp->uc_stack.ss_sp) {
		/* errno = ENOMEM;*/
		return -1;
	}

	/* Set the instruction and the stack pointer */
	ucp->uc_mcontext.Eip = (unsigned long) func;
	ucp->uc_mcontext.Esp = (unsigned long) sp - 4;

	/* Save/Restore the full machine context */
	ucp->uc_mcontext.ContextFlags = CONTEXT_FULL;

	/* Copy the arguments */
	va_start (ap, argc);
	for (i=0; i<argc; i++) {
		memcpy(sp, ap, 8);
		ap +=8;
		sp += 8;
	}
	va_end(ap);

	return 0;
}

int swapcontext(ucontext_t *oucp, const ucontext_t *ucp)
{
	int ret;

	if ((oucp == NULL) || (ucp == NULL)) {
		/*errno = EINVAL;*/
		return -1;
	}

	ret = getcontext(oucp);
	if (ret == 0) {
		ret = setcontext(ucp);
	}
	return ret;
}