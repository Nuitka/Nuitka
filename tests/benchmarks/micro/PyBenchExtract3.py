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


def someFunction( rounds ):
    # define functions
    def f(a,b,c,d=1,e=2,f=3):
        return f

    args = 1,2
    kwargs = dict(c=3,d=4,e=5)

    # do calls
    for i in xrange(rounds):
        f(a=i,b=i,c=i)
        f(f=i,e=i,d=i,c=2,b=i,a=3)
        f(1,b=i,**kwargs)
        f(*args,**kwargs)

        f(a=i,b=i,c=i)
        f(f=i,e=i,d=i,c=2,b=i,a=3)
        f(1,b=i,**kwargs)
        f(*args,**kwargs)

        f(a=i,b=i,c=i)
        f(f=i,e=i,d=i,c=2,b=i,a=3)
        f(1,b=i,**kwargs)
        f(*args,**kwargs)

        f(a=i,b=i,c=i)
        f(f=i,e=i,d=i,c=2,b=i,a=3)
        f(1,b=i,**kwargs)
        f(*args,**kwargs)

        f(a=i,b=i,c=i)
        f(f=i,e=i,d=i,c=2,b=i,a=3)
        f(1,b=i,**kwargs)
        f(*args,**kwargs)

someFunction( 10000 );
