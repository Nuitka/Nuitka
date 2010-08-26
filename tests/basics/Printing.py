# 
#     Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Python test that I originally created or extracted from other peoples
#     work. I put my parts of it in the public domain. It is at least Free
#     Software where it's copied from other people. In these cases, I will
#     indicate it.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the new code, or in the alternative
#     a BSD license to the new code, should your jurisdiction prevent this. This
#     is to reserve my ability to re-license the code at any time.
# 
# -*- coding: utf-8 -*-

# All of these 3 should be identical with correct software behaviour.

print "Output with newline."
print "Output", "with", "newline."
print "Output ", "with ", "newline."
print "Output ",
print "with ",
print "newline."
print "Output\twith tab"
print "Output\t",
print "with tab"