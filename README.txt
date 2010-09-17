
Recommended reading with org-mode in Emacs.

This is an ASCII format outline, used for tasks and issue tracking in Nuitka.

* Usage

** Requirements

   You need to use the GNU g++ compiler of at least version 4.5 available or else the
   compilation will fail. This is due to uses of C++0x and precisely 4.5 because of the
   use of so called "raw string" literals in Nuitka.

** Environment

   Set the environment by executing "misc/create-environment.sh" like this e.g. eval
   `misc/create-environment` which sets the PYTHONPATH to the compiler, and extends PATH
   with the directory containing Nuitka executables.

** Command Line

   Then look at "Nuitka.py --help" and a shortcut "Python" which always sets "--exe" and
   "--execute" options, so it is somewhat similar to "python".

** Where to go next

   Remember, this project is not finished. Although most of the CPython test suite works,
   there is still unsupported functionality, and there is not much actual optimization
   done yet.

** Word of warning

   Consider this an alpha release quality, do not use it for anything important, but
   feedback is very welcome.

* Unsupported functionality

** function.func_code:

   Cannot not exist for native compiled functions. There is no bytecode with Nuitka's
   compiled function objects, so there is no way to provide bytecode.

** On function level "from import *" does not work

   Example

   def myFunction():
      from string import *

      stuff()

   Does not generate correct C++ at this time. Similar problem to "exec does not create
   function locals". Currently Nuitka doesn't support a dynamic size of locals. Same
   solution applies.

** exec does not create function locals:

   Example:

   def myFunction():
       exec( "f=2" )

   The exec does not create local variables unless they already exist, by e.g.  having
   them assigned before:

   def myFunction():
       f = None

       exec( "f=2" )

   Otherwise the code believes that f is a global variable. Solution Plan: Would require
   to fallback to checking the provided locals for new entries before checking globals
   variable accesses. Priority: I do not see much value, all you need to do is to define
   the variable before the exec to make it work.

** sys.exc_info() does not stack

   It works mostly as expected, but doesn't stack, exceptions when handling exceptions are
   not preserved to this function, which they are with CPython, where each frame has its
   own current exception.

** threading can block it seems

   The generated code never lets the CPython run time switch threads, so its chances to do
   so are reduced, which may lead to problems. I personally do not care much about
   threads, would use subprocesses anyway.

** relative import "from . import x" is partially supported only

   Relative imports of this form work perfectly in --deep mode, because only then the package
   of the importing module is known. Currently there is no way to tell the compiler what the
   package the compiled module is when compiling in stand alone mode. This may change in the
   future.

* CPython Test changes:

** Modified tests:

This is the list of tests modified from what they are in CPython.

*** test_compile:

    Changed func_code usage to get local consts to locals().  Removed tests based on
    func_code objects.  Remove test that uses exec to enrich the locals.

*** test_complexargs:

    Don't use exec to hide Py3K warning, because it means the compiler is not used for it.

*** test_copy:

    deepcopy of compiled functions refuses to work, removed these test cases, removed
    func_code check

*** test_defaultdict:

    deepcopy is not supported, removed test_deep_copy

*** test_decorators:

    A call to eval() has run time None for globals and this is not yet supported.

*** test_exceptions:

    Removed code objects using parts parts.

*** test_ftplib:

    Disabled IPv6, not on my systems.

*** test_funcattrs:

    Disabled pars that use func_code and func_defaults.

*** test_future6:

    Changed relative import from "." to normal import.

*** test_gc:

    Remove use of sys._getframe and test that checks gc very fragile way.

*** test_grammar:

    Problem with comparison chains that use "in", unrealistic code not yet done. Same with
    nested assignments that each unpack. Removed these statements from the test. Also
    removed testFuncDef parts that use func_code to test things. Also removed try:
    continue finally: test, we are not correct there, finally is not executed in that
    case.

*** test_hotshot:

    Removed test that attempts to get line numbers from the func_code object.

*** test_import:

    Removed test_foreign_code, test_relimport_star.

*** test_inspect:

    Removed checks for argument specs of functions, not supported, for frames and code.

*** test_io.py:

    test_newline_decoder and testReadClosed fails with some unicode differences, likely
    because import from future does not change literals to unicode

*** test_marshal:

    Removed marshal of func_code

*** test_math:

    Removed doc tests, they check call stack and that is not yet supported. removed usage
    of sys.argv[0] to find file in the dir of the .py, where the .exe doesn't live.

*** test_mutants:

    Added random seed so the results are predictable

*** test_new:

    Removed test_code and test_function due to referenced to func_code

*** test_pep352:

    No deprecation warnings, removing the tests that check them.

*** test_pty:

    Removed traces of pids that are not reproducible

*** test_repr:

    Relaxed test that checks lamba repr to allow compiled lambda

*** test_scope:

    A test that checks exec with free vars refusal was using func_code to do so, removed
    that part. Also removed unbound local variable test, because we can't handle that
    yet. Removed part that checks for allowed forms of "from x import *" on function
    level, we don't support that yet.

*** test_signal:

    Removed test_itimer_prof, test_itimer_virtual seems that signal doesn't get through,
    and test takes 60 seconds of CPU, also removed test_main because it forks and raises
    exception there, that seems different

*** test_sort:

    Added random seed

*** test_strftime:

    Don't use current time to be reproducible, removed verbose outputs

*** test_struct:

    Removed test that requires deprecation warnings to be allowed to be disabled, we don't
    support that yet.

*** test_structmembers:

    Removed test class that only checks for deprecation warnings we don't give

*** test_sys:

    Removed usages of getframe, func_closure, and call stack, removed test_object, I do
    not understand it. removed test that does require sys.stdout and sys.stderr to have
    same encoding which they do not in my test environment, when I e.g. redirect stdout to
    a file and leave stderr on terminal.

*** test_undocumented_details:

    Removed usage of func_closure

*** test_weakref:

    Removed one test from test_proxy_ref which fails due to a detail of how a temp
    variable is destroyed a bit late. removed the doctest execution, it is verbose and not
    really a test of the compiler

*** test_zlib:

    Removed one test which uses much RAM

** Deleted tests:

*** test_aepack:

    I don't have the module being tested it seems.

*** test_al:

    I don't have the module being tested it seems.

*** test_applesingle:

    MacOS specific

*** test/test_bsddb185.py:

    Outdated module of no interest.

*** test_bsddb3.py:

    The "from bsddb.test import test_all" fails, likely also outdated, test_bsddb.py passed.

*** test_cd:

    I don't have the module being tested it seems.

*** test_cl:

    I don't have the module being tested it seems.

*** test_cmd_line_script:

    Aborts with mismatch message that seems not correct. But this tests running CPython as
    a child more than anything else, so it's mostly useless to debug. Could indicate wrong
    printing though. TODO: Check if it can be reactivated.

*** test_codecmaps_cn|hk|jp|kr|tw.py:

    These uses "urlfetch" and therefore have side effects not wanted.

*** test_collections:

    The collections module uses _sys._getframe(1) which is not set in --exe mode,
    rendering it useless.

*** test_ctypes:

    No ctypes.test module, where would it be?

*** test_curses:

    Uses getframe tricks, and fails to capture my mouse, so simply removed, out of scope
    for now.

*** test_decimal:

    One test failed with my CPython already, plus it uses execfile, which we cannot inline
    yet, so it doesn't test the compiler much. TODO: Revisit once we can inline exec and
    execfile of constants.

*** test_cProfile:

    Performance numbers differ obviously, removed test that doesn't provide much info.

*** test_dis:

    We don't have any bytecode in func_code ever, removed

*** test_distutils:

    Removed, out of scope

*** test_dl:

    Removed, no such module

*** test_docxmlrpc:

    Uses inspection and complains about compiled function

*** test_email:

    Removed, out of scope

*** test_email_codecs:

    Removed, out of scope

*** test_email_renamed:

    Removed, out of scope

*** test_file:

    Removed, because it uses heavy threading is more of a performance test. Blocked in
    some tests, indicating locking issues.

*** test_gdbm:

    No such module, out of scope

*** test_gl:

    No such module, out of scope

*** test_imageop:

    No such module, out of scope

*** test_imaplib:

    Output differed due to unknown reasons in imap details, removed therefore

*** test_imgfile:

    No such module, out of scope

*** test_json:

    No such module json.test, out of scope

*** test_kqueue:

    Runs only on BSD (how ever much I love my first Unix NetBSD, I don't have it
    currently), removed

*** test_lib2to3:

    No such module lib2to3.test module, out of scope

*** test_linuxaudiodev:

    Removed because it wants /dev/sdp, out of scope

*** test_macos|macostools|macospath|macfs:

    Removed, macos only

*** test_normalization:

    Removed, wants internet

*** test_os:

    Removed, works, but out of scope and number of tests run differs, making it
    annoying. Need to find out why not all tests can be run

*** test_ossaudiodev:

    Removed, want to use /dev/dsp, out of scope

*** test_pep277:

    Removed, windows only

*** test_profilehooks:

    Removed, excessive dependence on func_code

*** test_py3kwarn:

    Removed, out of scope

*** test_rgbimg:

    No such module

*** test_runpy:

    Removed, outputs a lot of paths in /tmp that differ each time

*** test_scriptpackages:

    Removed, no such module aetools

*** test_smtpnet:

    Removed, requires internet access

*** test_socket_ssl:

    Removed, didn't work with CPython

*** test_socketserver:

    Removed, out of scope

*** test_sqlite:

    No sqlite.test module, removed

*** test_startfile:

    No such module

*** test_sunaudiodev:

    Removed, no such module

*** test_tcl:

    Removed, no such module

*** test_thread|threading.py:

    Removed, out of scope and not determistic outputs

*** test_timeout:

    Removed, wants network

*** test_trace:

    Removed, out of scope

*** test_traceback:

    Removed, not yet supported

*** test_urllib2:

    Removed, fails mysteriously in the library core

*** test_urllibnet:

    Removed, wants internet

*** test_urllib2net:

    Removed, wants internet

*** test_warnings:

    Removed, not yet supported

*** test_winsound:

    Removed, no such module

*** test_winreg:

    Removed, windows only

*** test_with:

    Removed, there is a lot we don't support yet.

*** test_zipfile64:

    Removed, wants to do 6G files, thank you so much.

*** test_zipimport_support:

    Removed, does not run with CPython
