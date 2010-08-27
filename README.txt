
Recommended reading with org-mode in Emacs. An ascii format outline,
tasks and issue tracking.

* Usage

** Requirements

   You need to gcc C++ compiler of at least version 4.5 available or
   else the compilation will fail. This is due to uses of C++0x and
   precisely the use of so called raw string literals.

** Environment

   Set the environment by executing misc/create-environment.sh like
   this e.g. eval `misc/create-environment` which sets the PYTHONPATH
   to the compiler, and extends PATH with a directory containing its
   binaries.

** Command Line

   Then look at "Nuitka.py --help" and a shortcut "Python" which always
   sets --exe and --execute, so it is somewhat similar to "python".

** Where to go next

   Remember, this project is not finished. Although a lot of the CPython
   test suite works, there is still unsupported functionality, and there
   is not much actual optimization done yet.

** Word of warning

   Consider this an Alpha release quality, do not use it for anything
   important, but feedback is very welcome.

* Unsupported functionality

** function.func_code:

   Does not exist. There is no bytecode anymore, so it doesn't make as much sense
   anymore.

** On function level "from import *" does not work

   Example
   def myFunction():
      from string import *

      stuff()

   Does not generate correct C++ at this time. Similar problem to "exec does
   not create function locals". Currently Nuitka doesn't support a dynamic
   size of locals. Same solution applies.

** exec does not create function locals:

   Example:

   def myFunction():
      exec( "f=2" )

   The exec does not create local variables unless they already exist, by e.g.
   having them assigned before:

   def myFunction():
      f = None

      exec( "f=2" )

   Otherwise it assigns to the global variable. Solution Plan: Would require to
   fallback to checking the provided locals for new entries before checking
   globals variable accesses. Priority: I do not see much value, all you need to
   do is to define the variable before the exec to make it work.

** generators have no throw() method:

   Not used by anything but contextlib yet. Will have to work in the future, or
   else we won't be able to fully support contextlib, which I expect will see a
   more widespread usage.

   eval does not default to globals()/locals() when None is provided

** sys.exc_info() does not stack

   It works mostly as expected, but doesn't stack, exceptions when handling
   exceptions are not preserved to this function, which they are with CPython,
   where each frame has its own current exception.

** threading can block it seems

   The generated code never lets the CPython run time switch threads, so its
   chances to do so are reduced, which may lead to problems. I personally do
   not care much about threads, would use subprocesses anyway.

** relative imports from . are not supported yet

   May show up in the future. Easy to work around by changing these to the
   absolute exports normally.

** UnboundLocalError is not given:

   Instead a closure variable from e.g. module may be used. Solution: Slightly
   more difficult to fix, because getVariableForReference() is called and later
   the getVariableForAssignment() should notice that there is already is a
   reference variable, which should be replaced then. Priority: Not too
   important though.

* CPython Test changes:

** Modified tests:

This is the list of tests modified from what they are in CPython.

*** test_class:

    Part of the test uses the extended slicing syntax that
    I do not yet fully understand.

*** test_compile:

    Removed extended slice syntax. Changed func_code
    usage to get local consts to locals(). Removed tests based on
    func_code objects. Remove test that uses exec to enrich the
    locals

*** test_contextlib:

    Everything except exceptions is working. It uses the throw method of generators that
    we don't have. For the time being the "with" statement works, but not with generator
    expressions where there are exceptions.

*** test_complexargs:

    Don't use exec to hide Py3K warning, because it means the compiler is not
    used for it.

*** test_copy:

    deepcopy of compiled functions refuses to work, removed these test cases,
    removed func_code check

*** test_defaultdict:

    deepcopy is not supported, removed test_deep_copy

*** test_decorators:

    A call to eval() has run time None for globals and this is not yet
    supported.

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

*** test_grammer:

    Problem with comparison chains that use "in", unrealistic
    code not yet done. Same with nested assignments that each unpack. Removed
    these statements from the test. Also removed testFuncDef parts that use
    func_code to test things. Also removed try: continue finally: test, we are not
    correct there, finally is not executed in that case.

*** test_hotshot:

    remove test that attempts to get line numbers from the func_code object.

*** test_import:

    Removed test_foreign_code, disabled relative import tests

*** test_inspect:

    Removed checks for argument specs of functions, not supported, for
    frames and code.

*** test_io.py:

    test_newline_decoder and testReadClosed fails with some unicode
    differences, likely because import from future does not change
    literals to unicode

*** test_marshal:

    removed marshal of func_code

*** test_math:

    removed doc tests, they check call stack and that is not
    yet supported. removed usage of sys.argv[0] to find file in the dir
    of the .py, where the .exe doesn't live.

*** test_mutants:

    added random seed so the results are predictable

*** test_new:

    removed test_code and test_function due to referenced to func_code

*** test_pep352:

    No deprecation warnings, removing the tests that check them.

*** test_pty:

    removed traces of pids that are not reproducible

*** test_repr:

    relaxed test that checks lamba repr to allow compiled lambda

*** test_scope:

    test that checks exec with free vars refusal was using func_code to do
    so, removed that part. Also removed unbound local variable test, because
    we can't handle that yet. Removed part that checks for allowed forms of
    "from x import *" on function level, we don't support that yet.

*** test_signal:

    removed test_itimer_prof, test_itimer_virtual seems
    that signal doesn't get through, and test takes 60 seconds of CPU,
    also removed test_main because it forks and raises exception there,
    that seems different

*** test_sort:

    added random seed

*** test_strftime:

    don't use current time to be reproducible, removed verbose outputs

*** test_struct:

    removed test that requires deprecation warnings to be
    allowed to be disabled, we don't support that yet.

*** test_structmembers:

    removed test class that only checks for deprecation warnings we don't give

*** test_sys:

    removed usages of getframe, func_closure, and call stack,
    removed test_object, I do not understand it. removed test that does
    require sys.stdout and sys.stderr to have same encoding which they
    do not in my test environment, when I e.g. redirect stdout to a file
    and leave stderr on terminal.

*** test_undocumented_details:

    removed usage of func_closure

*** test_weakref:

    removed one test from test_proxy_ref which fails due to a detail of how a temp
    variable is destroyed a bit late. removed the doctest execution, it is verbose
    and not really a test of the compiler

*** test_zlib:

    removed one test which uses much RAM

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

    from bsddb.test import test_all fails, likely also outdated, test_bsddb.py passed.

*** test_cd:

    I don't have the module being tested it seems.

*** test_cl:
    I don't have the module being tested it seems.

*** test_cmd_line_script:

    Aborts with mismatch message that seems not correct. But this tests running CPython
    as a child more than anything else, so it's mostly useless to debug. Could indicate
    wrong printing though. TODO: Check if it can be reactivated.

*** test_codecmaps_cn|hk|jp|kr|tw.py:

    These uses "urlfetch" and therefore have side effects not wanted.

*** test_collections:

    The collections module uses _sys._getframe(1) which is not set in --exe mode,
    rendering it useless.

*** test_ctypes:

    no ctypes.test module, where would it be?

*** test_curses:

    uses getframe tricks, and fails to capture my mouse, so simply removed, out of
    scope for now.

*** test_decimal:

    One test failed with my CPython already, plus it uses execfile, which we cannot
    inline yet, so it doesn't test the compiler much. TODO: Revisit once we can inline
    exec and execfile of constants.

*** test_cProfile:

    Performance numbers differ obviously, removed test that doesn't provide much info.

*** test_dis:

    We don't have any bytecode in func_code ever, removed

*** test_distutils:

    removed, out of scope

*** test_dl:

    removed, no such module

*** test_docxmlrpc:

    uses inspection and complains about compiled function

*** test_email:

    removed, out of scope

*** test_email_codecs:

    removed, out of scope

*** test_email_renamed:

    removed, out of scope

*** test_file:

    Removed, because it uses heavy threading is more of a performance test. Blocked in
    some tests, indicating locking issues.

*** test_gdbm:

    no such module, out of scope

*** test_gl:

    no such module, out of scope

*** test_imageop:

    no such module, out of scope

*** test_imaplib:

    output differed due to unknown reasons in imap details, removed therefore

*** test_imgfile:

    no such module, out of scope

*** test_json:

    no such module json.test, out of scope

*** test_kqueue:

    runs only on BSD (how ever much I love my first Unix NetBSD, I don't have it
    currently), removed

*** test_lib2to3:

   no such module lib2to3.test module, out of scope

*** test_linuxaudiodev:

    removed because it wants /dev/sdp, out of scope

*** test_macos|macostools|macospath|macfs:

    removed, macos only

*** test_normalization:

    removed, wants internet

*** test_os:

    removed, works, but out of scope and number of tests run differs, making it annoying. Need
    to find out why not all tests can be run

*** test_ossaudiodev:

    removed, want to use /dev/dsp, out of scope

*** test_pep277:

    removed, windows only

*** test_profilehooks:

    removed, excessive dependence on func_code

*** test_py3kwarn:

    removed, out of scope

*** test_rgbimg:

    no such module

*** test_runpy:

    removed, outputs a lot of paths in /tmp that differ each time

*** test_scriptpackages:

    removed, no such module aetools

*** test_smtpnet:

    removed, requires internet access

*** test_socket_ssl:

    removed, didn't work with CPython

*** test_socketserver:

    removed, out of scope

*** test_sqlite:

    no sqlite.test module, removed

*** test_startfile:

    no such module

*** test_sunaudiodev:

    removed, no such module

*** test_tcl:

    removed, no such module

*** test_thread|threading.py:

    removed, out of scope and not determistic outputs

*** test_timeout:

    removed, wants network

*** test_trace:

    removed, out of scope

*** test_traceback:

    removed, not yet supported

*** test_urllib2:

    removed, fails mysteriously in the library core

*** test_urllibnet:

    removed, wants internet

*** test_urllib2net:

    removed, wants internet

*** test_warnings:

    removed, not yet supported

*** test_winsound:

    removed, no such module

*** test_winreg:

    removed, windows only

*** test_with:

    removed, there is a lot we don't support yet.

*** test_zipfile64:

    removed, wants to do 6G files, thank you so much.

*** test_zipimport_support:

    removed, does not run with CPython
