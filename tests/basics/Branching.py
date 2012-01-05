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

""" Some random branching to cover most cases """

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

    if True:
        print "Predictable branch taken"

branchingFunction(1,0,3)

x = 3

def optimizationVictim():

    if x:
        pass
    else:
        pass

    if x:
        pass
        pass


optimizationVictim()
