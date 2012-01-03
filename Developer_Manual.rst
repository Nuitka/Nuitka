
.. contents::

Developer Manual
~~~~~~~~~~~~~~~~

The purpose of this manual is to present the current design of Nuitka, the coding rules,
and the intentions of choices made. It is intended to be a guide to the source code, and to give explanations that don't fit into the source code in comments form.

It should be used as a reference for the process of planning and documenting decisions
made. We are e.g. presenting here the type inference plans before implementing them.

It grows out of discussions and presentations made at PyCON alike conferences as well as
private conversations or discussions on the mailing list.


Current State
=============

Nuitka as of 0.3.16 works like this:

   - "TreeBuilding" outputs node tree
   - "Optimization" enhances it as best as it can
   - "Finalization" marks the tree for code generation
   - "CodeGeneration" creates identifier objects and code snippets
   - "Generator" knows how identifiers and code is constructed
   - "MainControl" keeps it all together

This design is intended to last. Regarding Types, the state is:

   - Types are always "PyObject \*", implictely
   - The only more specific use of type is "constant", which can be
     used to predict some operations, conditions, etc.
   - Every operation is expected to have "PyObject \*" as result, if
     it is not a constant, then we know nothing about it.

Coding Rules
============

Line length
-----------

No more than 120 characters. Screens are wider these days, but most of the rules aim at
keeping the lines below 90.

Indentation
-----------

No tabs, 4 spaces, no trailing white space.


Identifiers
-----------

Classes are camel case with leading upper case. Methods are with leading verb in lower
case, but also camel case. Around braces, and after comma, there is spaces for better
readability. Variables and parameters are lower case with "_" as a separator.

.. code-block:: python

   class SomeClass:

      def doSomething( some_parameter ):
         some_var = ( "lala", "lele" )

Base classes that are abstract end in "Base", so that a meta class can use that
convention.

Function calls use keyword argument preferably. These are slower in CPython, but more
readable:

.. code-block:: python

   return Generator.getSequenceCreationCode(
        sequence_kind       = sequence_kind,
        element_identifiers = identifiers,
        context             = context
   )

The "=" are all aligned to the longest parameter names without extra spaces for it.

When the names don't add much value, sequential calls should be done, but ideally with one
value per line:

.. code-block:: python

    return Identifier(
        "TO_BOOL( %s )" % identifier.getCodeTemporaryRef(),
        0
    )

Here, "Identifier" will be so well known that the reader is expected to know the argument
names and their meaning, but it would be still better to add them.

Contractions may span across multiple lines for increased readability:

.. code-block:: python

   result = [
       "PyObject *decorator_%d" % ( d + 1 )
       for d in
       range( decorator_count )
   ]


Prefer list contractions over "map", "filter", and "apply"
----------------------------------------------------------

Using "map" and friends is considered worth a warning by "PyLint" e.g. "Used builtin
function 'map'". We should use list comprehensions instead, because they are more
readable.

List contractions are a generalization for all of them. We love readable and with Nuitka
as a compiler will there won't be any performance difference at all.

I can imagine that there are cases where list comprehensions are faster because you can
avoid to make a function call. And there may be cases, where map is faster, if a function
must be called. These calls can be very expensive, and if you introduce a function, just
for "map", then it might be slower.

But of course, Nuitka is the project to free us from what is faster and to allow us to use
what is more readable, so whatever is faster, we don't care. We make all options equally
fast and let people choose.

For Nuitka the choice is list contractions as these are more easily changed and readable.

Look at this code examples from Python:

.. code-block:: python

   class A:
       def getX( self ):
           return 1
       x = property( getX )

   class B( A ):
      def getX( self ):
         return 2


   A().x == 1 # True
   B().x == 1 # True (!)

This pretty much is what makes properties bad. One would hope B().x to be "2", but instead
it's not changed. Because of the way properties take the functions and not members,
because they are not part of the class, they cannot be overloaded without re-declaring
them.

Overloading is then not at all obvious anymore. Now imagine having a setter and only
overloading the getter. How to you easily update the property?

So, that's not likable about them. And then we are also for clarity in these internal APIs
too. Properties try and hide the fact that code needs to run and may do things. So lets
not use them.

For an external API you may exactly want to hide things, but internally that has no use,
and in Nuitka, every API is internal API. One exception may be the "hints" module, which
will gladly use such tricks for easier write syntax.

Design Descriptions
===================

These should be a lot more and contain graphics from presentations given. It will be
filled in, but not now.

nuitka.Importing Module
-----------------------

* From the module documentation

   The actual import of a module may already execute code that changes things. Imagine a
   module that does "os.system()", it will be done. People often connect to databases,
   and these kind of things, at import time. Not a good style, but it's being done.

   Therefore CPython exhibits the interfaces in an "imp" module in standard library,
   which one can use those to know ahead of time, what file import would load. For us
   unfortunately there is nothing in CPython that is easily accessible and gives us this
   functionality for packages and search paths exactly like CPython does, so we implement
   here a multi step search process that is compatible.

   This approach is much safer of course and there is no loss. To determine if it's from
   the standard library, one can abuse the attribute "__file__" of the "os" module like
   it's done in "isStandardLibraryPath" of this module.

* Role

  This module serves the recursion into modules and analysis if a module is a known
  one. It will give warnings for modules attempted to be located, but not found. These
  warnings are controlled by a while list inside the module.

Plan to add ctypes
==================

Add interfacing to C code, so Nuitka can turn a "ctypes" binding into an efficient binding
as written with C.

Goals/Allowances to the task
----------------------------

1. Goal: Must not use any existing headers, only generate declarations in generated
   C++ code ourselves.
2. Allowance: May use "ctypes" module at compile time if that makes sense.
3. Goal: We should use that allowance to use "ctypes", to e.g. not hard code what
   "ctypes.c_int()" gives unless there is a specific benefit.
4. Allowance: Not all "ctypes" usages must be supported immediately.
5. Goal: Try and be as general as possible. For the compiler, "ctypes" support should be
   hidden behind a generic interface of some sort


Type inference - The general Problem
------------------------------------

Part of the goal is to forward value knowledge. When you have "a = b", that means that a
and b now "alias". And if you know the value of "b" you can assume to know the value of
"a".

If that value is a constant, you will want to push it forward, because storing the
constant has a cost and loading the variable as well. So, you want to be able collapse
such code:

.. code-block:: python

   a = 3
   b = 7
   c = a / b

to:

.. code-block:: python

   c = 3 / 7

and that obviously to:

.. code-block:: python

   c = 0

This may be called (Constant) Value Propagation. But we are aiming for more. In order to
fully benefit from type knowledge, the new type system must be able to be fully friends
with existing builtin types. The behavior of a type "long", "str", etc. ought to be
implemented as far as possible with the builtin "long", "str" as well.

.. note::

   This use the real thing concept extends beyond builtin types, "ctypes.c_int()" should
   also be used, but we must be aware of platform dependencies. The maximum size of
   "ctypes.c_int" values would be an example of that.

This approach has well proven itself with builtin functions already, when many times the
real builtin was used to make computations. We have the problem though is, that builtins
may have problems to execute everything.

.. code-block:: python

   len( "a" * 1000000000000 )

To predict this code, calculating it at compile time, while feasible puts a
burden. Esp. we wouldn't want to produce such a constant and stream it, the C++ code would
be huge. So, we need to stop the "*" operator from being used at compile time and live
with reduced knowledge, already here:

.. code-block:: python

   "a" * 10000000000000

Instead, we would probably say that for this expression:

   - The result is a "str" or "PyStringObject"
   - We know its length exactly, "10000000000000"
   - and we can predict every of its elements, if need be, with a function.

Similar is true for this nice thing:

.. code-block:: python

   range( 10000000000000 )

We know:

   - The result is a "list" or "PyListObject"
   - We know its length exactly, "10000000000000"
   - and we can predict every of its elements, if need be, with a function.

Again, we wouldn't want to create the list. Nuitka currently refuses to compile time
calculate lists with more than 256 elements, an arbitrary choice.

We could know, from use of the "range" result maybe, that we ought to prefer a "xrange",
but that's not as much.

In our builtin code, we have specialized "range()" to check for the result size in a
prediction. This ought to be generalized.

Now lets look at a use:

.. code-block:: python

   for x in range( 10000000000000 ):
       doSomething()

Looking at this example, one way to look at it, would be to turn "range" into "xrange",
note that "x" is unused. But in fact, what would be best, is to notice that "range()"
values is not used, but only the length of the expression matters. And even if "x" were
used, only the ability to predict the value from a function would be interesting.

Predict from a function could mean to have Python code to do it, as well as C++ code to do
it. And of course, it would only make sense where such calculations are "O(1)", i.e. do
not require recursion like "n!" does.

.. note::

   The other thing is that CPython appears to take length hints from objects for some
   operations, and there it would help too, to track length of objects.

Back to the orginal example:

.. code-block:: python

   len( "a" * 1000000000000 )

The theme here, is that when we can't pre-compute all intermediate expressions, and we
sure can't always in the general case. But we can still, predict properties of an
expression result, more or less.

Here we have "len" to look at an argument that we know the size of. Great. We need to ask
if there are any side effects, and if there are, we need to maintain them of course, but
generally this appears feasible.


Applying this to "ctypes"
-------------------------

The not so specific problem to be solved to understand "ctypes" declarations is maybe as
follows:

.. code-block:: python

   import ctypes

This leads to Nuitka tree containing an "import module expression", that can be predicted
to be a module object, and it can be better known as "ctypes" from standard library with
more or less certainty. See the section about "Importing".

So that part is easy, and it's what should happen. During optimization, when the module
import expression is examined, it should say:

   - "ctypes" is a module
   - "ctypes" is from standard library (may not be true)
   - "ctypes" has a "ModuleFriend" that knows things about it attributes, that should be
     asked.

The later is the generic interface, and the optimization should connect the two, of course
via package and module full names. It will need a "ModuleFriendRegistry", from which it
can be pulled. It would be nice if we can avoid "ctypes" to be loaded into Nuitka unless
necessary, so these need to be more like a plug-in, loaded only if necessary.

Coming back to the original expression, it also contains an assignment expression, because
it is more like this:

.. code-block:: python

   ctypes = __import__( "ctypes" )

The assigned to object, simply gets the type inferred propagated, and the question is now,
if the propagation should be done as soon as possible and to what, or later.

For variables, we don't currently track at all any more than there usages read/write and
that is it. And we are not good at it either.

The problem with tracking it, is that such information may continuously become invalid at
many instances, and it can be hard to notice mistakes due to it. But if do not have it
fixed, how to we detect this:

.. code-block:: python

   ctypes.c_int()

How do we tell that "ctypes" is at that point a variable of module object or even the
ctypes module, and that we know what it's "c_int" attribute is, and what it's call result
is.

We should therefore, forward the usage of all we know and see if we hit any "ctypes.c_int"
alike. This is more like a value forward propagation than anything else. In fact, constant
propagation should only be the special case of it.

Excursion to Functions
----------------------

In order to decide what is best, forward or backward, we consider functions. If we
propagate forward, how to handle this:

.. code-block:: python

   def my_append( a, b ):
      a.append( b )

      return a

We would notate that "a" is first a "PyObject parameter object", then something that has
an "append" attribute, when returned. The type of "a" changes after "a.append" lookup
succeeds. It might be an object, but e.g. it could have a higher probability of being a
"PyListObject".

.. note::

   If classes in the program have an "append" attribute, it should play a role too, there
   needs to be a way to plug-in to this decisions.

This is a more global property of "a" value, and true even before the append succeeds, but
not as much maybe, so it would make sense to apply that information after an analysis of
all the node. This may be "Finalization" work.

.. code-block:: python

   b = my_append( [], 3 )

   assert b == [3] # Can be known now

Goal: The structure we use should make it easy to visit "my_append" and then have
something that easily allows to plug in the given values and know things. We need to be
able to tell, if evaluating "my_append" makes sense with given parameters or not.

We should e.g. be able to make "my_append" tell, one or more of these:

   - Returns the first parameter value (unless it raises an exception)
   - The return value has the same type as "a" (unless it raises an exception)

It would be nice, if "my_append" had information, we could instantiate with "list" and
"int" from the parameters, and then e.g. know what it does in that case.

Doing it "forward" appears to be best suited for functions and therefore long term. We
will try it that way. If it fails, we will do it backwards, i.e. on demand. While backward
looks like a perfect match for loops, for function calls, it would require heavy
operations to be repeated for every call, over and over.

Mixed Types
-----------

Consider the following inside a function or module:

.. code-block:: python

   if cond is not None:
      a = [ x for x in something() if cond(x) ]
   else:
      a = ()



A programmer will often not make a difference between "list" and "tuple". In fact, using a
tuple is a good way to express that something won't be changed later, as these are mutable.

To Nuitka though this means, that if "cond" is not predictable, after the conditional
statement we may either have a "tuple" or a "list". In order to represent that without
resorting to "I know nothing about it", we need a kind of "min/max" operating mechanism
that is capable of say what is common with multiple alternative values.

Back to "ctypes"
----------------

.. code-block:: python

   v = ctypes.c_int()

Coming back to this example, we needed to propagate "ctypes", then we can propagate
"something" from "ctypes.int" and then known what this gives with a call and no arguments,
so the walk of the nodes, and diverse operations should be addressed by a module friend.

In case a module friend doesn't know what to do, it needs to say so by default. This
should be enforced by a base class and give a warning or note.

Now to the interface
--------------------

The following is the intended interface

- Name for module "ModuleFriend"

- Base class "ValueFriendBase"

- The "ModuleFriends" should emit derived classes of type "ValueFriendBase" for their
  attributes

- A collection of "ValueFriend" instances expresses the current data flow state.

  - This collection should carry the name "DataFlowState"

  - Updates to the collection should be done via methods

      - "addVariableValue( var_name, value_friend )"
      - "onOutsideCode()"
      - "passedByReference( var_name )"
      - etc. (will decide the actual interface of this when implementing its use)

  - This collection is the input to walking the tree by "scope", i.e. per module body,
    per function body, etc.

  - The walk should initially be single pass, that means it does not maintain any
    history.

.. note:: Warning

   With this, the order of node walking becomes vital to correctness. The evaluation
   order of the generated code is now enforced, I am not so sure, that the walk of
   the node tree, really right now, is always exactly in the order of execution for
   CPython yet.

   This may carry bug potential. We need tests that cover this.

Discussing with examples
------------------------

The following examples:

.. code-block:: python

   # Assignment, the source decides the type of the assigned expression
   a = b

   # Operator "attribute lookup", the looked up expression decides via its "ValueFriend"
   ctypes.c_int

   # Call operator, the called expressions decides with help of arguments, which may
   # receive value friends after walking to them too.
   called_expression_of_any_complexity()

   # import gives a module any case, and the "ModuleRegistry" may say more.
   import ctypes

   # From import need not give module, "x" decides
   from x import y

   # Operations are decided by arguments, and CPython operator rules between argument
   # "ValueFriend"s.
   a + b


The walking of the tree is best done in "Optimization" and can be used to implement many
optimizations in a more consistent and faster way. We currently check the tree for calls
to builtins with constant arguments. But with the new way of walking, we reverse the order
of the check.

Now:

   - Check all tree for suitable "builtin" function calls
   - Check their arguments if they are constants
   - Replace builtin call node with constant results or known exception

Future:

   - Walk the tree and enter arguments of builtin function calls
   - Collect knowledge about the argument, including maybe that they are constant or known
     length
   - Ask the "BuiltinValueFriend" what it can say. If it says the value is of constant value,
     replace the node with constant results or known exception

It's really exciting to see, how this proposal cleans up the existing code and integrates
with it.

The "TreeBuilding" result should already contain default "ValueFriends" for constants and
for everything else. In fact the expression nodes should do that during build time and
then "ctypes" would be an module object, but most things will be of no real type, and that
one should be cheap.

Code Generation Impact
----------------------

Right now, code generation assumes that everything is an object, and does not take "int"
or these at all, and it should remain like that for some time to come.

Instead, ctypes value friend will be asked give "Identifiers", like other codes do too
from calls. And these need to be able to convert themselves to objects to work with the
other things.

But Code Generation should no longer require that operations must be performed on that
level. Imagine e.g. the following calls:

.. code-block:: python

   c_call( other_c_call() )

Value return by other_c_call() of say "c_int" type, should be possible to be fed directly
into another call. That should be easy by having a "asIntC()" in the identifier classes,
which the "ctypes" Identifiers handle without conversions.

Code Generation should one day also become able to tell that all uses of a variable have
only "c_int" value, and use "int" instead of "PyObjectLocalVariable" directly, or at least
a "PyIntLocalVariable" of similar complexity as "int" after inlining.

Such decisions would be prepared by finalization, which then would track the history of
values throughout a function or part of it.

Initial Implementation
----------------------

The "ValueFriend" will at first only be added to constants. And it will be constructed at
node creation time, being little more than a tool to do lookups.

It will then be used to turn the following code into better performing one:

.. code-block:: python

   def f():
      a = []

      print a

      for i in range(1000):
          print a

          a.append( i )

      return len( a )

The first goal will be that the "list" ValueFriend annotation from the constant assignment
will be copied to "a" until "a.append" is done. Then it must be detached, because "a" has
changed value by calling a then unknown member "append" of it. But at "print a" time it
knows that it is really "[]", which has a "__str__" that the "list" value friend provides.

Now:

   - Print has an argument "a" that is a variable reference
   - After loop, "a" is a variable reference

Future:

   - Print has a constant node argument
   - After loop "a" is of type list still

With that, we would have constant value propagation for lists in place, which is not much,
but an important step clearly.

The second goal will be that the "ValueFriendConstantList" knows that append changes "a"
value, but it remains a list, and that the size increases by one. It should provide an
other value friend "ValueFriendList" for "a" due to that.

The third and challenging goal will be to make the code generation be impacted by the
tracked types. It should have a knowledge that "PyList_Append" does the job of append and
use "PyList_Size" for "len". The "ValueFriends" should aid code generation too.

Last and right now optional goal will be to make "range" have a value friend, that can
interact with iteration of the for loop, and "append" of the "list" value friend, so it
knows it's possible to iterate 5000 times, and that "a" has then after the "loop" this
size, so "len( a )" could be predicted. For during the loop, about a the range of its
length should be known to be less than 5000.

Limitations for now
-------------------

- The collection of value friends will not have a history and be mutated as the processing
  goes.

  We will see, if we need any better at all. One day we might have passes with more
  expensive and history maintaining variants, that will be able to look at one variable and
  decide "value is only written, never read" and make something out of it.

- Only enough to trace "ctypes" information through the code

  We won't cover everything immediately. We should consider to re-factor existing
  optimizations into such that happen during the pass with value information. The builtins
  have already been mentioned as a worth-while target.

- Aim only for limited examples. For ctypes that means to compile time evaluate:

  .. code-block:: python

     print ctypes.c_int( 17 ) + ctypes.c_long( 19 )

  Later then call to "libc" or something else universally available, e.g. "strlen()" or
  "strcmp()" from full blown declarations of the callable.

- We won't have the ability to test that optimizations are actually performed, we will
  check the generated code by hand.

  With time, I will add XML based checks with "xpath" queries, expressed as hints, but
  that is some work that will be based on this work here. The "hints" fits into the
  "ValueFriends" concept nicely or so the hope is.

- Not too much.

  Try and get simple things to work now. We shall see, what kinds of constraints really
  make the most sense. Understanding list values e.g. is not strictly useful immediately
  and should not block us. This new design is not the final one likely, it just needs to
  be better than existing optimizations design.

Realization
-----------

Kay will attempt to provide the framework parts that provide the interface and Christopher
will work on the "ctypes" as an example.

The work is likely to happen on a git feature branch named "ctypes_annotation" or
something similar to be thought on. It will likely be long lived, and Kay will move usable
bits out of it for releases, causing rebases at agreed to times.

.. note::

   After handing over the work in a usable state, Kay will focus on allowing other
   developers to push branches like these at their own discretion and with some form of
   git commit emails for better collaboration. In the mean time, "git format-patch" will
   do.


Updates for this Manual
=======================

This document is written in REST. That is an ASCII format readable as ASCII, but used to generate a PDF or HTML document.

You will find the current source under:
http://nuitka.net/gitweb/?p=Nuitka.git;a=blob_plain;f=Developer_Manual.txt

And the current PDF under:
http://nuitka.net/doc/Developer_Manual.pdf
