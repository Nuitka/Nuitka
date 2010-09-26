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

def cond():
    return False

def loopingFunction( a = 1*2 ):
    c = []
    f = [ c, a ]

    for a in range(6 or 8):
        for b in range(8):
            if a == b:
                c.append( (a,b,True) )
            elif a < b:
                c.append( (b,a,False) )
            else:
                c.append( (a,b,False) )

            if a != b:
                z = 1
            else:
                z = 0

            if z == 0:
                continue


            if z == 1 and b == 6:
                break

            if a == b:
                z = 0

    print c

    f = 1

    while f < (10 or 8):
        m = 1
        f += 1

    print "m=", m

    x = [u for u in range(8)]

    x = [(u,v) for (u,v) in zip(range(8),reversed(range(8))) ]
    print x

    x = [(u if u%2==0 else 0) for u in range(10)]
    print x

    x = [(u if u%2==0 else 0) for u in (a if cond() else range(9))]
    print x

    y = [ [ 3+ (l if l else -1) for l in [m,m+1] ] for m in [f for f in range(2)] ]
    print "f=", f
    print "y=", y

    if x:
        l = "YES"
    else:
        l = "NO"

    if x:
        l = "yes"
    else:
        if True:
            l = "no"

    print "Triple and chain"

    if m and l and f:
        print "OK"

    print "Triple or chain"
    if m or l or f:
        print "Okey"

    print "Nested if not chain"
    if not m:
        if not l:
            print "ok"

    print "Braced if not chain with 'or'"
    if not (m or l):
        print "oki"

    print "Braced if not chain with 'and'"
    if not (m and l):
        print "oki"

    d=1
    print "Nested if chain with outer else"
    if a:
        if b or c:
            if d:
                print "inside nest"

    else:
        print "outer else"

    print x

    while False:
        pass
    else:
        print "Executed else branch for False condition while loop"

    while True:
        break
    else:
        print "Executed else branch for True condition while loop"

    for x in range( 7 ):
        pass
    else:
        print "Executed else branch for no break for loop"
 
    for x in range( 7 ):
        break
    else:
        print "Executed else branch despite break in for loop"

loopingFunction()
