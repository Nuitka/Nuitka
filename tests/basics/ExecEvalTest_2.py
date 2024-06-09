#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import os
import sys
import tempfile

print "eval 3+3=", eval("3+3")
print "eval  4+4=", eval(" 4+4")


def functionEval1():
    return eval(" 5+5")


print "eval in a function with nothing provided", functionEval1()


def functionEval2():
    a = [2]

    g = {}

    r = eval("1+3", g)

    return r, g.keys(), a


print "eval in a function with globals provided", functionEval2()


def functionEval3():
    result = []

    for x in eval("(1,2)"):
        result.append(x)

    return result


print "eval in a for loop as iterator giver", functionEval3()

print "exec on a global level",
exec ("d=2+2")
print "2+2=", d


def functionExec1():
    a = 1

    code = "a=2"
    exec (code)

    return a


def functionExec2():
    a = 1

    code = "a=2"
    exec code in globals(), locals()

    return a


print "exec in function without and with locals() provided:", functionExec1(), functionExec2()

tmp_filename = tempfile.gettempdir() + "/execfile.py"

f = open(tmp_filename, "w")
f.write("e=7\nf=8\n")
f.close()

execfile(tmp_filename)

print "execfile with defaults f,g=", e, f

global_vars = {"e": "0", "f": 0}
local_vars = dict(global_vars)

execfile(tmp_filename, global_vars)

print "execfile with globals dict:", global_vars.keys()

execfile(tmp_filename, global_vars, local_vars)

print "execfile with globals and locals dict:", local_vars


def functionExecfile():
    e = 0
    f = 0

    global_vars = {"e": "0", "f": 0}
    local_vars = dict(global_vars)

    print "execfile with globals and locals dict in a function:",
    x = execfile(tmp_filename, global_vars, local_vars)
    print x,
    print global_vars.keys(), local_vars, e, f


functionExecfile()


class classExecfile:
    e = 0
    f = 0

    print "execfile in a class:",
    # TODO: Won't work yet, Issue#5
    # print execfile( tmp_filename ),
    execfile(tmp_filename)
    print "execfile changed local values:", e, f


f = 7


def functionExecNonesTuple():
    f = 0

    exec ("f=1", None, None)
    print "Exec with None as optimizable tuple args did update locals:", f


def functionExecNonesSyntax():
    f = 0
    exec "f=2" in None, None
    print "Exec with None as optimizable normal args did update locals:", f


functionExecNonesTuple()
functionExecNonesSyntax()

print "Global value is untouched", f


def functionEvalNones2():
    f = 11

    code = "f"
    g = None
    l = None

    f1 = eval(code, l, g)

    print "Eval with None arguments from variables did access locals:", f1


functionEvalNones2()


def functionExecNonesTuple2():
    f = 0

    code = "f=1"
    g = None
    l = None

    exec (code, l, g)

    print "Exec with None as tuple args from variable did update locals:", f


def functionExecNonesSyntax2():
    f = 0

    code = "f=2"
    g = None
    l = None

    exec code in l, g

    print "Exec with None as normal args did update locals:", f


functionExecNonesTuple2()
functionExecNonesSyntax2()

print "Exec with a future division definition and one without:"

exec """
from __future__ import division
from __future__ import print_function
print( "3/2 is with future division", 3/2 )
"""

exec """
from __future__ import print_function
print( "3/2 is without future division", 3/2 )
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
from __future__ import print_function
x = 2
print( "Exec local x is", x )
"""
    print "Function global x referenced as local x in exec is", x

    exec """
from __future__ import print_function
print( "Re-exec local x", x )
"""
    print "Locals after exec assigning to local x", locals()

    exec """
from __future__ import print_function
global x
x = 3
print( "Exec global x is inside exec", x )
"""
    print "Global x referenced as global x in exec is", x

    exec """
from __future__ import print_function
def change_y():
   global y
   y = 4

   print( "Exec function global y is", y )

y = 7
change_y()

# TODO: The below will not work
print( "Exec local y is", y )
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

    def func():
        print "Closure from exec not used", ValueError

    func()


functionWithClosureProvidedByExec()

x = 2


def functionWithExecAffectingClosure():
    x = 4

    code = "d=3;x=5"
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


print "Exec in a generator function", tuple(generatorFunctionWithExec())


def evalInContractions():

    r1 = list(eval(str(s)) for s in range(3))
    r2 = [eval(str(s)) for s in range(4)]

    return r1, r2


print "Eval in a list contraction or generator expression", evalInContractions()


def execDefinesFunctionToLocalsExplicitly():
    exec """\
def makeAddPair(a, b):
    def addPair(c, d):
        return (a + c, b + d)
    return addPair
""" in locals()

    if sys.version_info < (3,):
        assert makeAddPair

    return "yes"


print "Exec adds functions declares in explicit locals() given.", execDefinesFunctionToLocalsExplicitly()

os.unlink(tmp_filename)


def execWithShortTuple():
    try:
        exec ("print hey",)
    except Exception as e:
        return "gives exception: " + repr(e)


print "Exec with too short tuple argument:", execWithShortTuple()

if str is not bytes:

    def evalMemoryView(value):
        return eval(memoryview(value))

    print "Eval with memory view:", evalMemoryView(b"27")

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
