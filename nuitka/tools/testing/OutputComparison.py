#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
#
""" Tools to compare outputs of compiled and not compiled programs.

There is a couple of replacements to be done for compiled programs to
make the diff meaningful. The compiled type representations are just
an example.

"""

import difflib
import os
import re

from nuitka.Tracing import my_print

ran_tests_re = re.compile(r"^(Ran \d+ tests? in )\-?\d+\.\d+s$")
instance_re = re.compile(r"at (?:0x)?[0-9a-fA-F]+(;?\s|\>)")
thread_re = re.compile(r"[Tt]hread 0x[0-9a-fA-F]+")
compiled_types_re = re.compile(
    r"compiled_(module|function|generator|method|frame|coroutine|async_generator|cell)"
)
module_repr_re = re.compile(r"(\<module '.*?' from ').*?('\>)")

global_name_error_re = re.compile(r"global (name ')(.*?)(' is not defined)")
non_ascii_error_rt = re.compile(r"(SyntaxError: Non-ASCII character.*? on line) \d+")
python_win_lib_re = re.compile(r"[a-zA-Z]:\\\\?[Pp]ython(.*?\\\\?)[Ll]ib")
local_port_re = re.compile(r"(127\.0\.0\.1):\d{2,5}")


traceback_re = re.compile(r'(F|f)ile "(.*?)", line (\d+)')


def traceback_re_callback(match):
    return r'%sile "%s", line %s' % (
        match.group(1),
        os.path.realpath(os.path.abspath(match.group(2))),
        match.group(3),
    )


importerror_re = re.compile(
    r"""(ImportError(?:\("|: )cannot import name '\w+' from '.*?' )\((.*?)\)"""
)


def import_re_callback(match):
    #    print (match.groups(), os.path.abspath(match.group(2)))

    return r"%s( >> %s)" % (
        match.group(1),
        os.path.realpath(os.path.abspath(match.group(2))),
    )


tempfile_re = re.compile(r"/tmp/tmp[a-z0-9_]*")

logging_info_re = re.compile(r"^Nuitka.*?:INFO")
logging_warning_re = re.compile(r"^Nuitka.*?:WARNING")

# Python3.11 style traceback carets are not done by Nuitka (yet?)
syntax_error_caret_re = re.compile(r"^\s*~*\^*~*$")


def _normalizeTimeDiff(outputStr):
    """
    use regular expression to normalize the time output

    e.g.
    =================== 1059 passed, 8 warnings in 7.99 seconds ===================

    becomes
    =================== 1059 passed, 8 warnings in x.xx seconds ===================
    """

    match = re.search(b"in [0-9]+.[0-9][0-9](s| seconds)", outputStr)
    if match:
        return (
            outputStr[: match.start()] + b"in x.xx seconds" + outputStr[match.end() :]
        )
    return outputStr


def makeDiffable(output, ignore_warnings, syntax_errors):
    # Of course many cases to deal with,
    # pylint: disable=too-many-branches,too-many-statements

    # do not compare time differences
    output = _normalizeTimeDiff(output)

    result = []

    # Fix import "readline" because output sometimes starts with "\x1b[?1034h"
    m = re.match(b"\\x1b\\[[^h]+h", output)
    if m:
        output = output[len(m.group()) :]

    lines = output.split(b"\n")
    if syntax_errors:

        for line in lines:
            if line.startswith(b"SyntaxError:"):
                lines = [line]
                break

    for line in lines:
        if type(line) is not str:
            try:
                line = line.decode("utf-8" if os.name != "nt" else "cp850")
            except UnicodeDecodeError:
                line = repr(line)

        if line.endswith("\r"):
            line = line[:-1]

        if line.startswith("REFCOUNTS"):
            first_value = line[line.find("[") + 1 : line.find(",")]
            last_value = line[line.rfind(" ") + 1 : line.rfind("]")]
            line = line.replace(first_value, "xxxxx").replace(last_value, "xxxxx")

        if line.startswith("[") and line.endswith("refs]"):
            continue

        if ignore_warnings and logging_warning_re.match(line):
            continue

        # Infos are always ignored.
        if logging_info_re.match(line):
            continue

        if line.startswith("Nuitka-Inclusion:WARNING: Cannot follow import to module"):
            continue
        if line.startswith("Nuitka:WARNING: Cannot detect Linux distribution"):
            continue
        if line.startswith(
            "Nuitka-Options:WARNING: You did not specify to follow or include"
        ):
            continue
        if line.startswith("Nuitka:WARNING: Using very slow fallback for ordered sets"):
            continue

        if syntax_error_caret_re.match(line):
            continue

        line = instance_re.sub(r"at 0xxxxxxxxx\1", line)
        line = thread_re.sub(r"Thread 0xXXXXXXXX", line)
        line = compiled_types_re.sub(r"\1", line)
        line = global_name_error_re.sub(r"\1\2\3", line)
        line = module_repr_re.sub(r"\1xxxxx\2", line)
        line = non_ascii_error_rt.sub(r"\1 xxxx", line)

        # Windows has a different "os.path", update according to it.
        line = line.replace("ntpath", "posixpath")

        # This URL is updated, and Nuitka outputs the new one, but we test
        # against versions that don't have that.
        line = line.replace(
            "http://www.python.org/peps/pep-0263.html",
            "http://python.org/dev/peps/pep-0263/",
        )

        line = ran_tests_re.sub(r"\1x.xxxs", line)

        line = traceback_re.sub(traceback_re_callback, line)

        line = importerror_re.sub(import_re_callback, line)

        line = tempfile_re.sub(r"/tmp/tmpxxxxxxx", line)

        # This is a bug potentially, occurs only for CPython when re-directed,
        # we are going to ignore the issue as Nuitka is fine.
        if (
            line
            == """\
Exception RuntimeError: 'maximum recursion depth \
exceeded while calling a Python object' in \
<type 'exceptions.AttributeError'> ignored"""
        ):
            continue

        # TODO: Harmonize exception ignored in function or method.
        if re.match("Exception ignored in:.*__del__", line):
            continue

        # This is also a bug potentially, but only visible under
        # CPython
        line = python_win_lib_re.sub(r"C:\\Python\1Lib", line)

        # Port numbers can be random, lets ignore them
        line = local_port_re.sub(r"\1:xxxxx", line)

        # This is a bug with clang potentially, can't find out why it says that.
        if line == "/usr/bin/ld: warning: .init_array section has zero size":
            continue

        # This is for NetBSD and OpenBSD, which seems to build "libpython" so
        # that it gives such warnings.
        if "() possibly used unsafely" in line or "() is almost always misused" in line:
            continue

        # This is for CentOS5, where the linker says this, and it's hard to
        # disable
        if "skipping incompatible /usr/lib/libpython2.6.so" in line:
            continue

        # This is for self compiled Python with default options, gives this
        # harmless option for every time we link to "libpython".
        if (
            "is dangerous, better use `mkstemp'" in line
            or "In function `posix_tempnam'" in line
            or "In function `posix_tmpnam'" in line
        ):
            continue

        # Ignore spurious clcache warning.
        if "clcache: persistent json file" in line or "clcache: manifest file" in line:
            continue

        # Ignore manual error message of CPython 3.11 that is different from the generic one for super
        line = line.replace(
            "super() argument 1 must be a type, not NoneType",
            "super() argument 1 must be type, not None",
        )
        line = line.replace(
            "super() argument 1 must be a type", "super() argument 1 must be type"
        )

        result.append(line)

    return result


def compareOutput(
    kind, out_cpython, out_nuitka, ignore_warnings, syntax_errors, trace_result=True
):
    from_date = ""
    to_date = ""

    diff = difflib.unified_diff(
        makeDiffable(out_cpython, ignore_warnings, syntax_errors),
        makeDiffable(out_nuitka, ignore_warnings, syntax_errors),
        "{program} ({detail})".format(program=os.environ["PYTHON"], detail=kind),
        "{program} ({detail})".format(program="nuitka", detail=kind),
        from_date,
        to_date,
        n=3,
    )

    result = list(diff)

    if result:
        if trace_result:
            for line in result:
                my_print(line, end="\n" if not line.startswith("---") else "")

        return 1
    else:
        return 0
