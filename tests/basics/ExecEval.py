#
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

import tempfile

print "eval 3+3=", eval("3+3")
print "eval  3+3=", eval(" 3+3")

def functionEval1():
    return eval(" 3+3")

print "eval in a function with nothing provided", functionEval1()

def functionEval2():
    a = [2]

    g = {}

    r = eval( "1+3", g )

    return r, g.keys()

print "eval in a function with globals provided", functionEval2()

def functionEval3():
    result = []

    for x in eval( "(1,2)"):
        result.append( x )

    return result

print "eval in a for loop as iterator giver", functionEval3()

print "exec on a global level",
exec( "d=2+2" )
print "2+2=",d

def functionExec1():
    a = 1

    code = "a=2"
    exec( code )

    return a

def functionExec2():
    a = 1

    code = "a=2"
    exec code in globals(), locals()

    return a

print "exec in function without and with locals() provided:", functionExec1(), functionExec2()

tmp_filename = tempfile.gettempdir() + "/execfile.py"

f = open( tmp_filename, "wb" )
f.write( "e=7\nf=8\n" )
f.close()

execfile( tmp_filename )

print "execfile with defaults f,g=", e, f

global_vars = { 'e' : '0', 'f' : 0 }
local_vars = dict( global_vars )

execfile( tmp_filename, global_vars )

print "execfile with globals dict:", global_vars.keys()

execfile( tmp_filename, global_vars, local_vars )

print "execfile with globals and locals dict:", local_vars

def functionExecfile():
    e = 0
    f = 0

    global_vars = { 'e' : '0', 'f' : 0 }
    local_vars = dict( global_vars )

    print "execfile with globals and locals dict in a function:",
    print execfile( tmp_filename, global_vars, local_vars ),
    print global_vars.keys(), local_vars, e, f

functionExecfile()

class classExecfile:
    e = 0
    f = 0

    print "execfile in a class:",
    # TODO: Won't work yet, Issue#5
    # print execfile( tmp_filename ),
    execfile( tmp_filename )
    print e, f


def functionExecNones():
    f = 0

    exec( "f=1", None, None )

    print "Exec with None as tuple args did update locals:", f

    exec "f=2" in None, None

    print "Exec with None as normal args did update locals:", f

functionExecNones()

def functionEvalNones2():
    f = 11

    code = "f"
    g = None
    l = None

    f1 = eval ( code, l, g )

    print "Eval with None arguments from variables did access locals:", f1


functionEvalNones2()

def functionExecNones2():
    f = 0

    code = "f=1"
    g = None
    l = None

    exec ( code, l, g )

    print "Exec with None as tuple args from variable did update locals:", f

    code = "f=2"

    exec code in l, g

    print "Exec with None as normal args did update locals:", f

functionExecNones2()

print "Exec with a future division definition and one without:"

exec """
from __future__ import division
print "3/2 is with future division", 3/2
"""

exec """
print "3/2 is without future division", 3/2
"""

x = 1
y = 1

def functionGlobalsExecShadow():
    global x
    print "Global x outside is", x

    y = 0
    print "Local y is initially", y

    print "Locals initially", locals()
    exec """
x = 2
print "Exec local x is", x
"""
    print "Function global x is", x

    exec """
print "Re-exec local x", x
"""
    print "Locals after exec assigning to local x", locals()

    exec """
global x
x = 3
print "Exec global x is", x
"""
    print "Exec level global x is", x

    exec """
def change_y():
   global y
   y = 4

   print "Exec function global y is", y

y = 7
change_y()

# TODO: The below will not work
print "Exec local y is", y

"""
    # print "Local y is afterwards", y

    def print_global_y():
        global y

        # TODO: The below will not work
        print "Global y outside", y

    print_global_y()
    print "Outside y", y

functionGlobalsExecShadow()

def functionWithClosureProvidedByExec():

    code = "ValueError = TypeError"

    exec code in None, None

    def func( ):
        print "Closure from exec not used", ValueError

    func()

functionWithClosureProvidedByExec()

x = 2

def functionWithExecAffectingClosure():

    x = 4

    code = "d=3"
    space = locals()

    exec code in space

    def closureMaker():
        return x

    return d, closureMaker()

print "Closure in a function with exec to not none", functionWithExecAffectingClosure()

def generatorFunctionWithExec():
    yield 1

    code = "y = 2"
    exec code

    yield y

print "Exec in a generator function", tuple( generatorFunctionWithExec() )

def evalInContractions():

    r1 = list( eval( str( s ) ) for s in range( 3 ) )
    r2 = [ eval( str( s ) ) for s in range( 4 ) ]

    return r1, r2

print "Eval in a list contraction or generator expression", evalInContractions()
