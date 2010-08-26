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


def branchingFunction( a, b, c ):
    print "branchingFunction:", a, b, c

    print "a or b", a or b
    print "a and b", a and b
    print "not a", not a
    print "not b", not b

    print "Simple branch with both branches"
    if a:
        l = "YES"
    else:
        l = "NO"

    print a, "->", l

    print "Simple not branch with both branches"
    if not a:
        l = "YES"
    else:
        l = "NO"

    print not a, "->", l

    print "Simple branch with a nested branch in else path"
    if a:
        m = "yes"
    else:
        if True:
            m = "no"

    print a, "->", m

    print "Triple and chain"

    v = "NO"
    if a and b and c:
        v = "YES"

    print a, b, c, "->", v

    print "Triple or chain"

    k = "NO"
    if a or b or c:
        k = "YES"

    print a, b, c, "->", k

    print "Nested if not chain"
    p = "NO"
    if not a:
        if not b:
            p = "YES"

    print "not a, not b", not a, not b, "->", p

    print "or condition in braces:"
    q = "NO"
    if (a or b):
        q = "YES"
    print "(a or b) ->", q

    print "Braced if not with two 'or'"

    if not (a or b or c):
        q = "YES"
    else:
        q = "NO"
    print "not (a or b or c)", q

    print "Braced if not with one 'or'"
    q = "NO"
    if not (b or b):
        q = "YES"
    print "not (b or b)", q

    print "Expression a or b", a or b
    print "Expression not(a or b)", not(a or b)
    print "Expression a and (b+5)", a and (b+5)

    print "Expression (b if b else 2)", (b if b else 2)
    print "Expression (a and (b if b else 2))", (a and (b if b else 2))

    print "Braced if not chain with 'and' and conditional expression"

    if not (a and (b if b else 2)):
        print "oki"

    print "Nested if chain with outer else"

    d=1

    if a:
        if b or c:
            if d:
                print "inside nest"

    else:
        print "outer else"

    print "Complex conditional expression"
    v = (3 if a-1 else 0) or \
        (b or (c*2 if c else 6) if b-1 else a and b and c)
    print v


branchingFunction(1,0,3)
