-*- org -*-

Recommended reading with org-mode in Emacs. This is an ASCII format outline, used for
tasks and issue tracking in Nuitka.

* Usage

** Requirements

   You need to use the GNU g++ compiler of at least version 4.5 available or else the
   compilation will fail. This is due to uses of C++0x and at least 4.5 because of the use
   of so called "raw string" literals in Nuitka, which are new in that version of g++.

** Environment

   Set the environment by executing "misc/create-environment.sh" like this e.g. eval
   `misc/create-environment` which sets the PYTHONPATH to the compiler, and extends PATH
   with the directory containing Nuitka executables.

** Command Line

   Then look at "Nuitka.py --help" and a shortcut "Python" which always sets "--exe" and
   "--execute" options, so it is somewhat similar to "python".

** Where to go next

   Remember, this project is not yet complete. Although most of the CPython test suite
   works perfectly, there is still more polish needed, to make it do enough optimizations
   to be worth while. Try it out.

   Subscribe to its mailing list:
   http://kayhayen24x7.homelinux.org/blog/nuitka-a-python-compiler/nuitka-mailinglist/

   Or contact me via email with your questions:
   kayhayen@gmx.de

** Word of Warning

   Consider this a beta release quality, do not use it for anything important, but your
   feedback and patches are very welcome. Esp. if you find that anything doesn't work,
   because the project is now at the stage that this should not happen.

* Unsupported functionality

** General

*** function.func_code:

    Cannot not exist for native compiled functions. There is no bytecode with Nuitka's
    compiled function objects, so there is no way to provide bytecode.

*** sys.exc_info() does not stack

    It works mostly as expected, but doesn't stack, exceptions when handling exceptions
    are not preserved to this function, which they are with CPython, where each frame has
    its own current exception.

*** threading can block it seems

    The generated code never lets the CPython run time switch threads, so its chances to do
    so are reduced, which may lead to problems. I personally do not care much about
    threads, would use subprocesses anyway.

*** Start of function call vs. end of function call in traceback output

    In CPython the traceback points to the end of the function call, whereas Nuitka has it
    point to the first line of the function call. This is due to the use of the ast.parse
    over bytecode it seems and not easy to overcome. It would require parsing the source
    on our own and search for the end of the function call.

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
constant propagation or function inlining would be. So this one is not be underestimated
and a very important step of successful optimizations.

The folding of constants is considered implemented, but it may not be entirely complete
yet. Please report it as a bug when you find an operation in Nuitka that has only
constants are input and is not folded.

** Constant Propagation

At the core of optimizations there is an attempt to determine values of variables at run
time and predictions of assignments. It determines if their inputs are constants or of
similar values. An expression, e.g. a module variable access, an expensive operation, may
be constant across the module of the function scope and then there needs to be none, or no
repeated module variable lookup.

Consider e.g. the module attribute "__name__" which likely is only ever be read, so its
value could be predicted to a constant string known at compile time. This can then be used
as input to the constant folding. Currently there is module variable usage analysis, but
only "__name__" is currently actually optimized.

At this stage it is more a proof of concept in Nuitka and will need considerably more
work, so that the whole node tree contains only one form of assignments. Until then we
cannot implement this fully.

** Builtin Call Prediction

For builtin calls like "type", "len", "range" it is often possible to predict the result
at compile time, esp. for constant inputs the resulting value often can be precomputed by
Nuitka. It can simply determine the result or the raised exception and replace the builtin
call with it allowing for more constant folding or code path folding.

The builtin call prediction is considered implemented, but may not cover all the builtins
there are yet. Sometimes builtins are not predicted when the result is big. A range() call
e.g. may give too big values to include the result in the binary.

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

This is not implemented yet.

** Unpacking Prediction

When the length of the right hand side of an assignment to a sequence can be predicted,
the unpacking can be replaced with multiple assigments.

This is of course only really safe if the left hand side cannot raise an exception while
building the assignment targets.

We do this now, but only for constants, because we currently have no ability to predict if
an expression can raise an exception or not.

** Builtin Type Inference

Future (Not even started): When a construct like "in xrange()" or "in range()" is used, it
should be possible to know what the iteration does and represent that, so that iterator
users can use that instead.

I consider that:

for i in xrange(1000):
   something(i)

could translate xrange(1000) or into an object of a special class that does the integer
looping more efficiently. In case "i" is only assigned from there, this could be a nice
case for a dedicated class.

** Quicker function calls

Functions are structured so that their parameter parsing and tp_call interface is separate
from the actual function code. This way the call can be optimized. One problem is that the
evaluation order can differ.

def f( a, b, c ):
   return a, b, c

f( c = get1(), b = get2(), c = get3() )

This will evaluate first get1(), then get2() and then get3() and then make the call. In
C++ whatever way the signature is written, its order is fixed. Therefore it would be
necessary to have a staging of the parameters before making the actual call.

To solve this, every call with keywords could have its own function in between to allow
it. This is subject to the same compiler/platform dependent parameter order problem, we
have seen before.

We could also consider kw-only and args-only entry points to parsing, and call them from
the compiled function tp_call interface. Parsing needs to do less checks in these cases.
