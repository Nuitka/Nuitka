-*- org -*-

Recommended reading with org-mode in Emacs. This is an ASCII format outline, used for
tasks and issue tracking in Nuitka.

* Usage

** Requirements

   C++ Compiler: You need a compiler with support for C++0x

   Currently this means, you need to use the GNU g++ compiler of at least version 4.5 or
   else the compilation will fail. This is due to uses of C++0x "raw string" literals
   only supported from that version on.

   On Windows the MinGW g++ compiler of at least version 4.5, the VC++ compiler is not
   currently supported, because it is too weak in its C++0x support.

   Python: You need at least CPython 2.6 to execute Nuitka, and because the created
   executables will link against the CPython shared library at run time.

** Environment

   Set the environment by executing "misc/create-environment.sh" like this e.g. eval
   `misc/create-environment` which sets the PYTHONPATH to the compiler, and extends PATH
   with the directory containing Nuitka executables.

** Command Line

   Then look at "Nuitka.py --help" and a shortcut "Python --help" which always sets
   "--exe" and "--execute" options, so it is somewhat similar to "python".

** Where to go next

   Remember, this project is not completed yet. Although the CPython test suite works near
   perfect, there is still more work needed, to make it do enough optimizations to be
   worth while. Try it out.

   Subscribe to its mailing list:
   http://kayhayen24x7.homelinux.org/blog/nuitka-a-python-compiler/nuitka-mailinglist/

   Or contact me via email with your questions:
   kayhayen@gmx.de

** Word of Warning

   Consider this a beta release quality, do not use it for anything important, but your
   feedback and patches are very welcome.

   Especially report it if you find that anything doesn't work, because the project is now
   at the stage that this should not happen.

* Unsupported functionality

** General

*** function.func_code:

    Cannot not exist for native compiled functions. There is no bytecode with Nuitka's
    compiled function objects, so there is no way to provide bytecode.

*** threading can block it seems

    The generated code never lets the CPython run time switch threads, so its chances to do
    so are reduced, which may lead to problems. I personally do not care much about
    threads, would use subprocesses anyway.

*** Start of function call vs. end of function call in traceback output

    In CPython the traceback points to the end of the function call, whereas Nuitka has it
    point to the first line of the function call. This is due to the use of the "ast.parse"
    over bytecode it seems and not easy to overcome. It would require parsing the Python
    source on our own and search for the end of the function call. Maybe someone will do
    it someday. I personally prefer the start of the function call, because it shows the
    function called.

*** Yield in generator expressions is not supported

    In CPython you can write this strange construct: (i for i in (yield) if (yield))

    This is not currently supported in Nuitka, "only" generator functions are. It can be and
    will be, but it's a strange corner case to start with.


* CPython Test changes:

** Modified tests:

This is the list of tests modified from what they are in CPython.

*** test_cmd_line:

    Usability Fix: Removed test that checks for the version parameter output, which
    doesn't match when the CPython binary is not the system python.

*** test_collections:

    Compatability Fix: Removed check that the __module__ is set correctly by the
    collections namedtuple module, as it uses sys._getframe() which is not currently
    supported.

    Compatability Fix: Removed test_pickle which fails because of namespace issues likely
    caused the same issue as above.

*** test_compile:

    Compatability Fix: Removed test_mangling, because of heavy use of the func_code
    attribute co_varnames which we don't support yet.

    Compatability Fix: Removed assertion in test_for_distinct_code_objects which checks
    func_code which we don't support yet.

    Compatability Fix: Removed test_32_63_bit_values which uses co_consts which we don't
    support at all.

*** test_compiler:

    Usability Fix: Removed testCompileLibrary which byte code compiled for a random time
    producing indetermistic output between runs.

*** test_complexargs:

    Usability Fix: Don't use exec with dedent to hide Py3K warning, because it means the
    compiler is not used for it.

*** test_cookie (26 only):

    Usability Fix: Removed part of the test that is a difference between Python 2.6 and
    Python 2.7 plus it is affected by the function call line difference.

*** test_copy:

    Compatability Fix: Removed func_code attribute usage from test_copy_atomic.

    Compatability Fix: Removed func_code attribute usage from test_deepcopy_atomic.

    Compatability Fix: Removed test_copy_function test, which is refused by copy with an
    exception "TypeError: object.__new__(compiled_function) is not safe, use
    compiled_function.__new__()"

    Compatability Fix: Removed test_deepcopy_function test, which is refused by copy with
    an exception "TypeError: object.__new__(compiled_function) is not safe, use
    compiled_function.__new__()"

    TODO: Add __reduce__ and/or __reduce_ex__ slots to resolve the later. They would allow
    to pickle compiled functions too.

*** test_decimal:

    Usability Fix: Was using sys.argv[0] to find the containing directory which may not be
    what we are using.

*** test_defaultdict:

    Compatability Fix: Removed test_deep_copy test

*** test_exceptions:

    Compatability Fix: Removed usage of f_back of frame objects in tracebacks, they are not
    linked with Nuitka, although the traceback itself is.

*** test_funcattrs:

    Compatability Fix: Disabled parts that use func_code and func_defaults:
    test_blank_func_defaults, test_copying_func_code, test_empty_cell, test_func_closure,
    test_func_code, test_func_default_args

    Note: We could support the attribute func_defaults or even func_closure relatively easy,
    but it's probably not worth it.

*** test_functools:

    Compatability Fix: Disabled test_pickle, because compiled functions cannot be pickled
    yet.

*** test_gc:

    Compatability Fix: Disabled test_frame, test_function, test_count because of use of
    sys._getframe and test that checks gc very fragile way.

*** test_grammar:

    Workaround: Problem with comparison chains that use "in", unrealistic code not yet
    support, one day these need to be supported though.

    Compatability Fix: Removed parts of testFuncDef parts that use func_code to test things.

*** test_hotshot:

    Compatability Fix: Removed test_line_numbers because that one attempts to get line
    numbers from the func_code object.

*** test_inspect:

    Compatability Fix: Removed checks for argument specs of functions, not supported by
    the module for compiled functions.

    Compatability Fix: Removed checks for type of generator, doesn't match for compiled
    generator expressions.

*** test_io.py:

    Compatability Fix: Removed tests that require threading to work.

*** test_marshal:

    Compatability Fix: Removed marshal of func_code

*** test_math:

    Compatability Fix: Removed doc test read from file, it checks call stack and that is
    not yet supported.

    Usability Fix: Was using sys.argv[0] to find the containing directory which may not be
    what we are using.

*** test_module:

    Usability Fix: Strangely the test_dont_clear_dict fails with CPython here, so disabled
    it, because with Nuitka it passes.

*** test_mutants:

    Usability Fix: Added random seed so the results are predictable.

*** test_new:

    Compatability Fix: Removed test_code and test_function due to referenced to func_code.

*** test_pep352:

    Usability Fix: No deprecation warnings, removing the test that checks them.

*** test_pydoc:

    Usability Fix: Removed test_not_here, test_bad_import, test_input_strip, because they
    try to run py_doc with the compiled exe, which cannot work and wouldn't be a test of
    the compiler anyway.

*** test_pty:

    Usability Fix: Disabled verbose tracing of pids that are not reproducible.

*** test_repr:

    Usability Fix: Relaxed test that checks lamba repr to allow compiled lambda.

*** test_scope:

    Compatability Fix: Removed testEvalExecFreeVars due to reference to func_code.

    Compatability Fix: Removed testComplexDefinitions due to usage of "exec in locals()"
    which is not supported when it comes to actually changing locals.

*** test_signal:

    Usability Fix: Removed test_itimer_prof, test_itimer_virtual seems that signal doesn't
    get through, and test takes 60 seconds of CPU.

*** test_site:

    Usability Fix: Removed test that wants to check the Python -s function, which the
    compiled test doesn't have of course.

    Usability Fix: Removed check for site package directory which seems to differ for
    Debian.

*** test_sort:

    Usability Fix: Added random seed

*** test_strftime:

    Usability Fix: Don't use current time to be reproducible, removed verbose outputs

*** test_struct:

    Compatability Fix: Removed test parts that use the inspect module to determine the line
    number.

*** test_sys:

    Usability Fix: Removed test_43581 that does require sys.stdout and sys.stderr to have
    same encoding which they do not in my test environment, when I e.g. redirect stdout to
    a file and leave stderr on terminal.

    Compatability Fix: Removed usage of sys._getframe in test_getframe which we don't support.

    Compatability Fix: Removed usage of func_closure in test_objecttypes.

    Compatability Fix: Removed test_current_frames due to reference to CPython only list
    of current frames of all threads.

    Compatability Fix: Removed test_exc_clear which fails to work because exceptions
    currently do not stack.

    Compatability Fix: Removed check for dictionary size, PyDict_Copy() doesn't match the
    expectations and uses more memory for copied constants. Also bytecode functions are a
    bit bigger than the uncompiled ones. And generator functions are way bigger as they
    store 2 contexts for the switch.

*** test_sysconfig:

    Usability Fix: Removed test that insisted on a specific set of flags, but Debian's
    Python seems to have more.

*** test_undocumented_details:

    Compatability Fix: Removed usage of func_closure

*** test_weakref:

    Compatability Fix: Removed one test from test_proxy_ref which fails due to a detail of
    how a temp variable is destroyed a bit late.

    Usability Fix: Removed the doctest execution, it is verbose and not really a test of
    the compiler.

*** test_zlib:

    Usability Fix: Removed tests which use too much RAM

*** test_zimport:

    Compatability Fix: Removed testTraceback which exhibits that tracebacks are somehow
    not perfect yet.


** Deleted tests:

*** test_argparse:

    Removed, out of scope, wants to fork a new Python similar to the running Python which
    doesn't work when sys.argv[0] is an executable instead.

*** test_curses:

    Uses getframe tricks, and fails to capture my mouse, so simply removed, out of scope
    for now.

*** test_capi:

    Removed, because it requires threading to work.

*** test_cprofile:

    Removed, performance numbers differ obviously, doesn't provide much info.

*** test_dis:

    Removed, we don't have any bytecode in func_code ever.

*** test_distutils:

    Removed, out of scope

*** test_dl:

    Removed, no such module

*** test_doctest:

    Removed, doctest uses inspection and won't find all the tests and produce differences
    from that.

*** test_docxmlrpc:

    Removed, uses inspection and complains about compiled function not being a function.

*** test_file:

    Removed, because it uses heavy threading is more of a performance test. Blocked in
    some tests, indicating locking issues.

*** test_gdb:

    Removed, out of scope.

*** test_imaplib:

    Usability Fix: Import test_support through test package.

    Usability Fix: Verbose output differed due to unknown reasons in imap details, removed
    therefore disabled verbose output.

*** test_import:

    Usability Fix: Removed test_import_initless_directory_warning because it relies on a
    directory to exist that doesn't on my Debian Squeeze system.

*** test_peepholer:

    Removed, refers only to bytecode which compiled functions don't have, so it's out of
    scope.

*** test_pdb:

    Removed, depended on test_doctest which was removed and didn't contain much test at
    all.

*** test_profilehooks:
    Removed, excessive dependence on func_code.

*** test_runpy:

    Usability Fix: Set verbose = 0 to avoid output of lot of temporary filenames and paths
    in /tmp that differ each time.

*** test_socketserver:

    Removed, out of scope

*** test_sundry:

    Removed, out of scope

*** test_threading.py:

    Removed, out of scope.

*** test_threading_local.py:

    Removed, out of scope (although it most of the time works the same way).

*** test_timeout:

    Removed, wants network

*** test_trace:

    Removed, out of scope

*** test_urllib2:

    Removed, fails mysteriously in the library core

*** test_urllibnet:

    Removed, wants internet

*** test_urllib2net:

    Removed, wants internet

*** test_warnings:

    Removed, not yet supported

***  test_zipfile|test_zipfile64:

    Removed, out of scope.

*** test_zipimport_support:

    Removed, does not run with CPython


* Shedskin Example changes:

This section is building up only. The Shed Skin example programs are very valueable,
because they show how programs that allow type inference can be improved, and generally
although Nuitka and Shed Skin are different beasts, it's very interesting to look at what
Shed Skin is good at and potentially benefit from it in decisions for Nuitka.

** Modified examples:

This is the list of examples modified from the original tarball, most often to make them
complete in less time, so it's more feasible to consider them in valgrind.

*** ant.py

Changed numCities from 200 to 100, so it runs faster. It took 30 seconds before and I
consider 10 seconds or below a must.

The speedup compared to CPython is currently insufficient. The code is bound by floating
point speed of the CPython objects that have a lot of overhead, because of checks and the
handling of exceptions. Without recognizing the types of variables and treating floating
point objects in a special way, there is no chance to be competetive on this example.

I got the idea though, that a "local only" float object makes sense, potentially also for
temporary variables. Avoiding the malloc per new value would give the most benefit of all
things I assume.

*** pylife.py

Changed iteration from 20 to 7 and initial population to only 800 to reduce the run time
of the test. Takes 1 second now only, before it was 16s.

** Deleted examples:

*** ac_encode.py

Too fast running to be useful.

* Optimizations

** Constant Folding

The most important form of optimization is the constant folding. This is when an operation
can be predicted. Examples would be "7+6", "range(3)". Currently Nuitka does these for
some builtins (but not all yet), and it does it for binary/unary operations and
comparisons.

Literals are one source of constants, but also most likely other optimization steps like
constant propagation or function inlining would be. So this one should not be underestimated
and a very important step of successful optimizations. Every option to produce a constant
may implact the generated code quality a lot.

Status: The folding of constants is considered implemented, but it may not be entirely
complete yet. Please report it as a bug when you find an operation in Nuitka that has only
constants are input and is not folded.

** Constant Propagation

At the core of optimizations there is an attempt to determine values of variables at run
time and predictions of assignments. It determines if their inputs are constants or of
similar values. An expression, e.g. a module variable access, an expensive operation, may
be constant across the module of the function scope and then there needs to be none, or no
repeated module variable lookup.

Consider e.g. the module attribute "__name__" which likely is only ever be read, so its
value could be predicted to a constant string known at compile time. This can then be used
as input to the constant folding.

Currently there is module variable usage analysis, but only "__name__" is currently actually
optimized. Also builtin exception name references are optimized if they are uses as module
level read only variables.

Status: At this stage it is more a proof of concept in Nuitka and will need considerably
more work, before it can be applied to local variables and their values.

** Builtin Call Prediction

For builtin calls like "type", "len", "range" it is often possible to predict the result
at compile time, esp. for constant inputs the resulting value often can be precomputed by
Nuitka. It can simply determine the result or the raised exception and replace the builtin
call with it allowing for more constant folding or code path folding.

The builtin call prediction is considered implemented, but may not cover all the builtins
there are yet. Sometimes builtins are not predicted when the result is big. A range() call
e.g. may give too big values to include the result in the binary.

Status: This is considered mostly implemented. Please file bugs for builtins that are
predictable but are not computed by Nuitka at compile time.

** Conditional Statement Prediction

For conditional statements, some branches may not ever be taken, because of the conditions
being possible to predict. In these cases, the branch not taken and the condition check is
removed.

This can typically predict code like this:

if __name__ == "__main__":
   do_something_nether_done_as_module()

It will also greatly benefit from constant propagations, or enable them because once some
branches have been removed, other things may become more predictable, so this is critical.

With some code branches removed, access patterns may be more friendly. Imagine e.g. that a
function is only called in a removed branch. It may be possible to remove it entirely, and
that may have other consequences too.

Status: This is considered implemented, but for the most benefit, more constants needs to
be determined at compile time.

** Exception propagation

For exceptions that are determined at compile time, there is an expression that will simply do
raise the exception. These can be propagated, collecting potentially "side effects", i.e. parts
of expressions that must still be executed.

Consider the following code:

print side_effect_having() + 1 / 0
print something_else()

The 1 / 0 can be predicted to raise a "ZeroDivisionError" exception, which will be propagated
through the "+" operation. The call to "side_effect_having" will have to be retained, but the
print statement, can be turned into an explicit raise. The statement sequence can be aborted
and as such the "something_else" call needs no code generation or consideration anymore.

Status: The propagation of exceptions is implemented on a very basic level. It works, but
exceptions will not propagate through many different expression and statement types. As work
progresses or examples arise, these will be extended.

** Exception Scope Reduction

Consider the following code:

try:
    b = 8
    print range( 3, b, 0 )
    print "Will not be executed"
except ValueError, e:
    print e

The try block is bigger than it needs to be. The statement "b = 8" cannot cause a ValueError
to be raised. As such it can be moved to outside the try without any risk.

b = 8
try:
    print range( 3, b, 0 )
    print "Will not be executed"
except ValueError, e:
    print e

Status: Not yet done yet. The infrastructure is in place, but until exception block inlining
works perfectly, there is not much of a point.

** Exception Block Inlining

With the exception propagation it is then possible to transform this code:

try:
    b = 8
    print range( 3, b, 0 )
    print "Will not be executed"
except ValueError, e:
    print e

try:
    raise ValueError, "range() step argument must not be zero"
except ValueError, e:
    print e

Which then can be reduced by avoiding the raise and catch of the exception, making
it:

e = ValueError( "range() step argument must not be zero" )
print e

Status: For this to work, the builtin or user defined exception types from the raise
must be matched against the catching ones. This works partially, but to simulate the
effects of a raise statement and the normalization at compile time is something new
and not yet done correctly, so this is currently disabled.

** Empty branch removal

For loops and conditional statements that contain only code without effect, it should be
possible to remove the whole construct:

for i in range(1000):
    pass

The loop could be removed, at maximum it should be considered an assignment of variable
"i" to 999 and no more.

Another example:

if side_effect_free:
   pass

The condition should be removed in this case, as its evaluation is not needed. It may be
difficult to predict that side_effect_free has no side effects, but this might be
possible.

Status: This is not implemented yet.

** Unpacking Prediction

When the length of the right hand side of an assignment to a sequence can be predicted,
the unpacking can be replaced with multiple assigments.

This is of course only really safe if the left hand side cannot raise an exception while
building the assignment targets.

We do this now, but only for constants, because we currently have no ability to predict if
an expression can raise an exception or not.

Status: Not really implemented, and should use mayHaveSideEffect() to be actually good at
things.

** Builtin Type Inference

When a construct like "in xrange()" or "in range()" is used, it is possible to know what
the iteration does and represent that, so that iterator users can use that instead.

I consider that:

for i in xrange(1000):
   something(i)

could translate "xrange(1000)" into an object of a special class that does the integer
looping more efficiently. In case "i" is only assigned from there, this could be a nice
case for a dedicated class.

Status: Future work, not even started.

** Quicker function calls

Functions are structured so that their parameter parsing and "tp_call" interface is separate
from the actual function code. This way the call can be optimized away. One problem is that
the evaluation order can differ.

def f( a, b, c ):
   return a, b, c

f( c = get1(), b = get2(), a = get3() )

This will evaluate first get1(), then get2() and then get3() and then make the call. In
C++ whatever way the signature is written, its order is fixed. Therefore it would be
necessary to have a staging of the parameters before making the actual call, to avoid
an re-ordering of the calls to get1(), get2() and get3().

To solve this, every call with keywords could have its own function in between to allow
it. This is subject to the same compiler/platform dependent parameter order problem, we
have seen before.

Status: Not even started.

* Credits

** Contributors to Nuitka

Thanks go to these individuals for their much valued contributions to Nuitka. The order is
sorted by time.

Li Xuan Ji: Contributed patches for general portability issue and enhancements to the
environment variable settings.

Nicolas Dumazet: Found and fixed refcounting issues, import work, improved some of the
English and generally made improvements all over the place.

Khalid Abu Bakr: Submitted patches for his work to support MinGW and Windows, debugged the
issues, and helped me to get cross compile with MinGW from Linux to Windows. This was
quite a feat.

** Projects used by Nuitka

*** The CPython project http://www.python.org/

Thanks for giving us CPython, which is the base of Nuitka.

*** The gcc project http://gcc.gnu.org/

Thanks for not only the best compiler suite, but also thanks for supporting C++0x which
has made the generation of code much easier. Currently no other compiler is usable for
Nuitka than yours.

*** The scons project http://www.scons.org/

Thanks for tackling the difficult points and providing a Python environment to make the
build results. This is such a perfect fit to Nuitka and a dependency that will likely
remain.

*** The valgrind project http://valgrind.org/

Luckily we can use Valgrind to determine if something is an actual improvement without the
noise. And it's also helpful to determine what's actually happening when comparing.

*** The MinGW project http://www.mingw.org/

Thanks for porting the best compiler to Windows. This allows portability of Nuitka with
relatively little effort.

*** The mingw-cross-env project http://mingw-cross-env.nongnu.org

Thanks for enabling us to easily setup a cross compiler for my Debian that will produce
working Windows binaries.

*** The wine project http://www.winehq.org/

Thanks for enabling us to run the cross compiled binaries without have to maintain a
windows installation at all.
