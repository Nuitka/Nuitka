# -*- coding: utf-8 -*-
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts and resulting tests are too small to be protected and therefore
#     is in the public domain.
#
#     If you submit Kay Hayen patches to this in either form, you automatically
#     grant him a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. Obviously it
#     won't affect code that comes to him indirectly or code you don't submit to
#     him.
#
#     This is to reserve my ability to re-license the official code at any time,
#     to put it into public domain or under PSF.
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
