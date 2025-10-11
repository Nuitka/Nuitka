// Copyright (c) 2019 Calvin Buckley
//
// Permission to use, copy, modify, and distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

#include <stdio.h>
#include <string.h>
#include <dlfcn.h>
#include <sys/errno.h>
#include <stdlib.h>

/* AIX specific headers for loadquery and traceback structure */
#include <sys/ldr.h>
#include <sys/debug.h>

/*
 * The structure that holds information for dladdr. Unfortunately, on AIX,
 * the information returned by loadquery lives in an allocated buffer, so it
 * should be freed when no longer needed. Note that sname /is/ still constant
 * (it points to the traceback info in the image), so don't free it.
 */
typedef struct dl_info {
  char* dli_fname;
  void* dli_fbase;
  const char* dli_sname;
  void* dli_sbase;
} Dl_info;

/**
 * Gets the base address and name of a symbol.
 *
 * This uses the traceback table at the function epilogue to get the base
 * address and the name of a symbol. As such, this means that the input must
 * be a word-aligned address within the text section.
 *
 * The way to support non-text (data/bss/whatever) would be to use an XCOFF
 * parser on the image loaded in memory and snarf its symbol table. However,
 * that is much more complex, and presumably, most addresses passed would be
 * code in the text section anyways (I hope so, anyways...) Unfortunately,
 * this does mean that function descriptors, which live in data, won't work.
 * The traceback approach actually works with JITted code too, provided it
 * could be emitted with XCOFF traceback...
 */
static void dladdr_get_symbol(void **sbase, const char **sname, void *where) {
	unsigned int *s = (unsigned int*)where;
	while (*s) {
		/* look for zero word (invalid op) that begins epilogue */
		s++;
	}
	/* We're on a zero word now, seek after the traceback table. */
	struct tbtable_short *tb = (struct tbtable_short*)(s + 1);
	/* The extended traceback is variable length, so more seeking. */
	char *ext = (char*)(tb + 1);
	/* Skip a lot of cruft, in order according to the ext "structure". */
	if (tb->fixedparms || tb->floatparms) {
		ext += sizeof(unsigned int);
	}
	if (tb->has_tboff) {
		/* tb_offset */
		void *start = (char*)s - *((unsigned int*)ext);
		ext += sizeof (unsigned int);
		*sbase = (void*)start;
	} else {
		/*
		 * Can we go backwards instead until we hit a null word,
		 * that /precedes/ the block of code?
		 * Does the XCOFF/traceback format allow for that?
		 */
		*sbase = NULL; /* NULL base address as a sentinel */
	}
	if (tb->int_hndl) {
		ext += sizeof(int);
	}
	if (tb->has_ctl) {
		/* array */
		int ctlnum =  (*(int*)ext);
		ext += sizeof(int) + (sizeof(int) * ctlnum);
	}
	if (tb->name_present) {
		/*
		 * The 16-bit name length is here, but the name seems to
		 * include a NUL, so we don't reallocate it, and instead
		 * just point to its location in memory.
		 */
		ext += sizeof(short);
		*sname = ext;
	} else {
		*sname = NULL;
	}
}

/**
 * Look for the base address and name of both a symbol and the corresponding
 * executable in memory. This is a simplistic reimplementation for AIX.
 *
 * Returns 1 on failure and 0 on success. "s" is the address of the symbol,
 * and "i" points to a Dl_info structure to fill. Note that i.dli_fname is
 * not const, and should be freed.
 */
int dladdr(void* s, Dl_info* i) {
	/*
	 * Don't put this on the stack, we'll allocate some hideously large
	 * buffer on the heap and avoid any reallocations. Also init the
	 * returned structure members to clear out any garbage.
	 */
	char *buf = malloc(10000);
	i->dli_fbase = NULL;
	i->dli_fname = NULL;
	i->dli_sbase = NULL;
	i->dli_sname = NULL;
	int r = loadquery (L_GETINFO, buf, 10000);
	if (r == -1) {
		return 0;
	}
	/* The loader info structures are also a linked list. */
	struct ld_info *cur = (struct ld_info*) buf;
	while (1) {
		/*
		 * Check in text and data sections. Function descriptors are
		 * stored in the data section.
		 */
		char *db = (char*)cur->ldinfo_dataorg;
		char *tb = (char*)cur->ldinfo_textorg;
		char *de = db + cur->ldinfo_datasize;
		char *te = tb + cur->ldinfo_textsize;
		/* Just casting comparing to these */
		char *cs = (char*)s;

		if ((cs >= db && cs <= de) || (cs >= tb && cs <= te)) {
			/* Look for file name and base address. */
			i->dli_fbase = tb; /* Includes XCOFF header */
			/* library filename + ( + member + ) + NUL */
			char *libname = malloc ((PATH_MAX * 2) + 3);
			/*
			 * This can't be a const char*, because it exists from
			 * an allocated buffer in memory that should probably
			 * be freed. We might as well add the member name too.
			 */
			sprintf(libname, "%s(%s)", cur->ldinfo_filename,
				cur->ldinfo_filename + strlen(cur->ldinfo_filename) + 1);
			i->dli_fname = libname;

			/*
			 * Find the symbol's name and base address. To make it
			 * easier, we use the traceback in the text section.
			 * See the function's comments above as to why.
			 * (Perhaps we could deref if a descriptor though...)
			 */
			if (cs >= tb && cs <= te) {
				dladdr_get_symbol(&i->dli_sbase, &i->dli_sname, s);
			}

			free(buf);
			return 1;
		} else if (cur->ldinfo_next == 0) {
			/* Nothing. */
			free(buf);
			return 0;
		} else {
			/* Try the next image in memory. */
			cur = (struct ld_info*)((char*)cur + cur->ldinfo_next);
		}
	}
}

int
main (int argc, char **argv)
{
	Dl_info dli;
	void *dll, *dls;
	int ret;
	dlerror();
	dll = dlopen(argv [1], RTLD_NOW | RTLD_MEMBER);
	if (!dll) {
		fprintf (stderr, "dlopen: errno %d dlerror %s *or* %s\n", errno, dlerror (), dlerror ());
		return 0;
	}
	dls = dlsym (dll, argv [2]);
	if (!dls) {
		fprintf (stderr, "dlsym: errno %d dlerror %s *or* %s\n", errno, dlerror (), dlerror());
		return 0;
	}
//	ret = dladdr (dls, &dli);
	/* get that function descriptor */
	ret = dladdr (*(void**)dls, &dli);
	printf ("dladdr returned %d and %s / %s\n", ret, dli.dli_fname, dli.dli_sname);
	return ret;
}