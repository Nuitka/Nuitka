# -*- coding: utf-8 -*-
#
#     Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are in the public domain. It is at least Free Software
#     where it's copied from other people. In these cases, it will normally be
#     indicated.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     Please leave the whole of this copyright notice intact.
#

# All of these should be identical with correct software behaviour.

print "Output with newline."
print "Output", "with", "newline."
print "Output ", "with ", "newline."
print "Output ",
print "with ",
print "newline."
print "Output\twith tab"
print "Output\t",
print "with tab"

# These ones gave errors with previos literal bugs:
print "changed 2"
print "foo%sbar%sfred%sbob?????"

a = "partial print"
# b doesn't exist

try:
    print a, b
except Exception, e:
    print "then occured", e

print "No newline at the end",
