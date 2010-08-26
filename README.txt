
******************************************************************
** Usage
******************************************************************

Set the environment by executing misc/create-environment.sh like
this e.g. eval `misc/create-environment` which sets the PYTHONPATH
to the compiler, and extends PATH with a directory containing its
binaries.

Then look at "Nuitka.py --help" and a shortcut "Python" which always
sets --exe and --execute, so it is somewhat similar to "python".

Remember, this project is not finished. Although a lot of the CPython
test suite works, there is still unsupported functionality, and there
is not much actual optimization done yet.

Consider this an Alpha release quality, do not use it for anything
important, but feedback is very welcome.

******************************************************************
** Unsupported functionality
******************************************************************

repr( __unicode__) differences: Slightly different representations
when using libpython, but this should not be a big concern yet and
ought to be a CPython bug.

function.func_code: Does not exist. There is no bytecode anymore,
so it doesn't make as much sense anymore.

lambdas cannot be generators, I didn't know they could be.

exec does not add to locals. Would require to fallback to checking
the provided locals for new entries before checking globals. I do
not see much value, all you need to do is to define the variable
before the exec to make it work.

generators have no throw() method. Would require them to not be
callable iterators simply, but a type of their own. Not used by
anything but contextlib yet.

eval does not default to globals()/locals() when None is provided

sys.exc_info() seems to return None, None, None in exception handler
which it probably should not. May need some special treatment to get
at current exception instead.

threading can block it seems

relative imports from . are not supported yet

try:   continue finally:   stuff

does not execute stuff, continue needs to be treated as if it were an exception,
the continue needs to inline the finally code or something similar.

exec open( filename) does not work

UnboundLocalError is not given, instead a closure variable from e.g. module
may be used. Slightly more difficult to fix, because getVariableForReference()
is called and later getVariableForAssignment() should notice that there is
already a reference variable, which should be replaced then. Not too important
though.

try: yield: finally does not execute the finally maybe

** CPython Test changes:

********************************************************************
* Modified tests:
********************************************************************

test_array: Removed unicode tests, they have the repr() problem
and an attribute test of __slots__ in test_subclassing that is
not really an array test.

test_asyncore: Removed test_compact_traceback, we don't yet provide
tracebacks yet, so this gives an exception.

test_compile: Removed extended slice syntax. Changed func_code
usage to get local consts to locals(). Removed tests based on
func_code objects. Remove test that uses exec to enrich the
locals

test_contextlib: Everything except exceptions is working. It uses
the throw method of generators that we don't have. For the time
being the "with" statement works, but not with generator expressions
where there are exceptions.

test_dict: Part of test_dir checks classes with __slots__ active
and notices that it fails to work as expected, this was deactivated

test_class: Part of the test uses the extended slicing syntax that
I do not understand.

test_codeccallbacks: Removed tests that are victim of unicode repr
differences.

test_collections: Removed yield lambdas from the test, these are
not supported yet.

test_compiler: unreproducible results and testing a function of
CPython does we don't need to test ourselves.

test_copy: deepcopy of compiled functions refuses to work, removed
these test cases.

test_copy_reg: removed extended slice use, removed tests of slots,
we don't implement them.

test_datetime: Everything pickling was removed, due to complaints
about version mismatch of the pickler. Seems the pickler module
is using something we don't have to determine its supporting
pickling protocol.

test_decorators: A call to eval() has run time None for globals and
this is not yet supported.

test_defaultdict: deepcopy is not supported, removed test_deep_copy

test_desc: test_properties checks against an implementation detail
of properties, removed. Removed __slots__ tests, we ignore these so
far. Also __slots__ variables are not initialized, removed tests
that use it. The name mangling of __class_attr does not get applied
and therefore some metaclasses do not work, removed much of
test_metaclass that uses __class_attr tricks

test_dict: crasher in test_le, no clue why __eq__ returning an
exception is to bad

test_exceptions: Removed unicode repr causing parts. Seems deprecation
warnings are not given, probably by design, removed that test part. And
also sys.exc_info() seems not updated in case of exceptions.

test_file: Removed, because it uses heavy threading is more of a
performance test. Blocked in some tests, indicating locking issues.

test_ftplib: Disabled IPv6, not on my systems

test_funcattrs: Disabled pars that use func_code and func_defaults

test_functools: Cannot create weakrefs to compiled functions, removed
that part

test_future3: Somehow the true division as default doesn't work as
expected, likely the C-API Py_NumberDivide should be replaced in
Tree transforming.

test_future6: Changed relative import from "." to normal import.

test_gc: Remove use of sys._getframe and test that checks gc very
fragile way.

test_grammer: Remove test that uses extended slices. Problem with
comparison chains that use "in", unrealistic code not yet done. Same
with nested assignments that each unpack. Removed these statements
from the test. Also removed testFuncDef parts that use func_code to
test things. Also removed try: continue finally: test, we are not
correct there, finally is not executed in that case.

test_hotshot: remove test that attempts to get line numbers from
the func_code object.

test_import: Removed test_foreign_code, disabled relative import
tests

test_inspect: No exception tracebacks yet, removed these parts

test_io.py: test_newline_decoder and testReadClosed fails
mysteriously with some unicode differences, likely because import
from future does not change literals to unicode

test_logging: Logging exceptions doesn't work with every config,
removed test_config4_ok

test_math: removed doc tests, they check call stack and that is not
yet supported. removed usage of sys.argv[0] to find file in the dir
of the .py, where the .exe doesn't live.

test_memoryio: removed unicode sensitive parts, due to future use
of unicode literals

test_multibytecodec: removed unicode encoding causing test, avoid
exec of file

test_mutants: added random seed

test_new: removed test_code and test_function due to referenced to
func_code

test_pep352: No deprecation warnings, removing the tests that check
them.

test_property: removed test that checked enforcing of __slots__ which
we don't support yet.

test_pty: removed traces of pids that are not reproducible

test_pyexpat: removed check that is affected by unicode repr problem

test_repr: removed test that checks lamba repr

test_scope: test that checks exec with free vars refusal was using
func_code to do so, removed that part. Also removed unbound local
variable test, because we can't handle that yet.

test_signal: removed test_itimer_prof, test_itimer_virtual seems
that signal doesn't get through, and test takes 60 seconds of CPU,
also removed test_main because it forks and raises exception there,
that seems different

test_sort: added random seed

test_strftime: don't use current time to be reproducible, removed
verbose outputs

test_struct: removed test that requires deprecation warnings to be
allowed to be disabled, we don't support that yet.

test_structmembers: removed test class that only checks for
deprecation warnings we don't give

test_sys: removed usages of getframe, func_closure, and call stack,
removed test_object, I do not understand it. removed test that does
require sys.stdout and sys.stderr to have same encoding which they
do not in my test environment

test_undocumented_details: removed usage of func_closure

test_weakref: removed one test from test_proxy_ref which fails due
to a detail of how a temp variable is destroyed a bit late. removed
the doctest execution, it is verbose and not really a test of the
compiler

test_zlib: removed one test which uses much RAM

********************************************************************
* Deleted tests:
********************************************************************

test_aepack: ?
test_al: ?
test_applesingle: MacOS specific
test/test_bsddb185.py: Outdated module of no interest.
test_bsddb3.py: from bsddb.test import test_all fails, likely
also outdated, test_bsddb.py passed.
test_cd: ?
test_cl: ?
test_cmd_line_script: Aborts with mismatch message that seems
not correct. But this tests running CPython as a child more
than anything else, so it's mostly useless to debug. Could
indicate wrong printing though.
test_codecmaps_cn|hk|jp|kr|tw.py: These uses "urlfetch" and
therefore have side effects not wanted.

test_collections: The collections module uses _sys._getframe(1)
which is not set in --exe mode, rendering it useless.

test_ctypes: no ctypes.test module, where would it be?

test_curses: uses getframe tricks, and fails to capture my mouse,
so simply removed, out of scope for now.

test_decimal: One test failed with my CPython already, plus it
uses execfile, which we cannot inline yet, so it doesn't test
the compiler much.

test_cProfile: Performance numbers differ obviously, removed test
that doesn't provide much info.

test_dis: we don't have any bytecode in func_code ever, removed

test_distutils: removed, out of scope

test_dl: removed, no such module

test_docxmlrpc: uses inspection and complains about compiled function

test_email: removed, out of scope
test_email_codecs: removed, out of scope
test_email_renamed: removed, out of scope

test_future4: The __future__ import doesn't change unicode literals
to string literals. Removed.

test_gdbm: no such module, out of scope

test_gl: no such module, out of scope

test_imageop: no such module, out of scope

test_imaplib: an import didn't work, adapted, but output differed
due to unknown reasons in imap details, removed therefore

test_imgfile: no such module, out of scope

test_json: no such module json.test, out of scope

test_kqueue: runs only on BSD (how ever much I love my first Unix
NetBSD, I don't have it currently), removed

test_lib2to3: no such module lib2to3.test module, out of scope

test_linuxaudiodev: removed because it wants /dev/sdp, out of scope

test_long_future: removed, because it only tests future true division,
but we don't yet support that.

test_macos|macostools|macospath|macfs: removed, macos only

test_normalization: removed, wants internet

test_os: removed, works, but out of scope and number of tests run
differs, making it annoying. Need to find out why not all tests can
be run

test_ossaudiodev: removed, want to use /dev/dsp, out of scope

Test_pep277: removed, windows only

test_profilehools: removed, excessive dependence on func_code

test_py3kwarn: removed, out of scope

test_rgbimg: no such module

test_runpy: removed, outputs a lot of paths in /tmp that differ
each time

test_scriptpackages: removed, no such module aetools

test_smtpnet: removed, requires internet access

test_socket_ssl: removed, didn't work with CPython

test_socketserver: removed, out of scope

test_sqlite: no sqlite.test module, removed

test_startfile: no such module

test_sunaudiodev: removed, no such module

test_tcl: removed, no such module

test_thread|threading.py: removed, out of scope and not determistic
outputs

test_timeout: removed, wants network

test_trace: removed, out of scope

test_traceback: removed, not yet supported

test_unicode: removed test_repr, it fails with the hard to find
repr error

test_urllib2: removed, fails mysteriously in the library core

test_urllibnet: removed, wants internet
test_urllib2net: removed, wants internet

test_warnings: removed, not yet supported

test_winsound: removed, no such module
test_winreg: removed, windows only

test_with: removed, there is a lot we don't support yet.

test_zipfile64: removed, wants to do 6G files, thank you so much.

test_zipimport_support: removed, does not run with CPython
