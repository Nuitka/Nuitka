#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Build and run the standalone dictionary concurrency stress test.

The C test links the Nuitka dictionary helpers directly and exercises shared
dictionaries from native threads. Run this script with the Python interpreter
whose C API should be used, for example:

    python3.13t tests/codegen-analysis/DictionaryConcurrencyTest.py
"""

import os
import shlex
import shutil
import subprocess
import sys
import tempfile


def getRepositoryRoot():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def findPythonConfig(python):
    candidates = [
        python + "-config",
        os.path.join(os.path.dirname(python), os.path.basename(python) + "-config"),
    ]
    config_name = os.path.basename(python) + "-config"
    found_config = shutil.which(config_name)

    if found_config is not None:
        candidates.append(found_config)

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return None


def getConfigFlags(config, *flags):
    output = subprocess.check_output([config] + list(flags))
    return shlex.split(output.decode("utf8"))


def getCompiler():
    return os.environ.get("CC", "cc")


def getSysconfigFlags(python):
    code = """
import sysconfig
print(sysconfig.get_path("include"))
print(sysconfig.get_path("platinclude"))
print(sysconfig.get_config_var("LIBDIR") or "")
print(sysconfig.get_config_var("LDLIBRARY") or "")
"""
    output = subprocess.check_output([python, "-c", code]).decode("utf8").splitlines()
    include = output[0]
    platinclude = output[1]
    libdir = output[2]
    library = output[3]

    includes = ["-I", include]

    if platinclude and platinclude != include:
        includes += ["-I", platinclude]

    if library.startswith("libpython"):
        library_name = library[3:]

        for suffix in (".so", ".dylib", ".a"):
            if suffix in library_name:
                library_name = library_name.split(suffix)[0]
                break

        ldflags = [
            "-L",
            libdir,
            "-l" + library_name,
            "-Wl,-rpath," + libdir,
            "-ldl",
            "-lm",
            "-lpthread",
        ]
    else:
        ldflags = ["-L", libdir, "-lpython", "-ldl", "-lm", "-lpthread"]

    return includes, ldflags


def getPythonVersion(python):
    output = subprocess.check_output(
        [python, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"]
    )
    return tuple(int(part) for part in output.decode("utf8").strip().split("."))


def buildAndRun(python, keep, gil, tsan):
    repo_root = getRepositoryRoot()
    source_dir = os.path.join(repo_root, "tests", "codegen-analysis")
    source_filename = os.path.join(source_dir, "DictionaryConcurrencyTest.c")
    constants_dir = os.path.join(source_dir, "concurrency_constants")
    scratch_root = os.path.join(repo_root, "tests", "scratch")

    if not os.path.isdir(scratch_root):
        os.makedirs(scratch_root)

    build_dir = tempfile.mkdtemp(prefix="dict-concurrency-", dir=scratch_root)
    object_filename = os.path.join(build_dir, "DictionaryConcurrencyTest.o")
    binary_filename = os.path.join(build_dir, "DictionaryConcurrencyTest")

    config = findPythonConfig(python)

    if config is None:
        includes, ldflags = getSysconfigFlags(python)
    else:
        includes = getConfigFlags(config, "--includes")
        ldflags = getConfigFlags(config, "--embed", "--ldflags")

    compile_command = [
        getCompiler(),
        "-std=gnu11",
        "-O2",
        "-g",
        "-pthread",
        "-ffunction-sections",
        "-fdata-sections",
    ]

    if tsan:
        compile_command += ["-fsanitize=thread", "-fno-omit-frame-pointer", "-O1"]
    compile_command += includes

    if getPythonVersion(python) >= (3, 14):
        # The standalone test includes Nuitka helper headers directly. Python
        # 3.14 renamed an immortal refcount helper and has a typo in a helper
        # header variable name that is otherwise unused by this test.
        compile_command += ["-D_Py_IMMORTAL_REFCNT=UINT32_MAX", "-Dop=obj"]

    compile_command += [
        "-I",
        os.path.join(repo_root, "nuitka", "build", "include"),
        "-I",
        os.path.join(repo_root, "nuitka", "build", "static_src"),
        "-I",
        constants_dir,
        "-c",
        source_filename,
        "-o",
        object_filename,
    ]

    link_command = [getCompiler(), object_filename, "-pthread"]

    if tsan:
        link_command.append("-fsanitize=thread")

    if sys.platform == "darwin":
        link_command.append("-Wl,-dead_strip")
    else:
        link_command.append("-Wl,--gc-sections")

    link_command += ldflags
    link_command += ["-o", binary_filename]

    try:
        subprocess.check_call(compile_command)
        subprocess.check_call(link_command)
        environment = os.environ.copy()

        if gil is not None:
            environment["PYTHON_GIL"] = gil

        if tsan:
            environment.setdefault(
                "TSAN_OPTIONS", "halt_on_error=1:second_deadlock_stack=1"
            )

        subprocess.check_call([binary_filename], env=environment)
    except subprocess.CalledProcessError as exception:
        sys.stderr.write(
            "Concurrency test command failed: %s\n" % (" ".join(exception.cmd),)
        )
        return exception.returncode
    finally:
        if not keep:
            shutil.rmtree(build_dir)

    return 0


def main():
    args = sys.argv[1:]
    python = sys.executable
    keep = False
    gil = None
    tsan = False

    while args:
        argument = args.pop(0)

        if argument == "--python" and args:
            python = args.pop(0)
        elif argument == "--gil" and args:
            gil = args.pop(0)
        elif argument == "--tsan":
            tsan = True
        elif argument == "--keep":
            keep = True
        else:
            sys.stderr.write("Unknown argument: %s\n" % argument)
            return 1

    return buildAndRun(python, keep, gil, tsan)


if __name__ == "__main__":
    sys.exit(main())

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
