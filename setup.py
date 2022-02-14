#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Setup file for Nuitka.

This applies a few tricks. First, the Nuitka version is read from
the source code. Second, the packages are scanned from the filesystem,
and third, the byte code compilation is avoided for inline copies of
scons with mismatching Python major versions.

"""
import os
import sys

os.chdir(os.path.dirname(__file__) or ".")
sys.path.insert(0, os.path.abspath(os.getcwd()))

# isort:start

import re

from setuptools import setup
from setuptools.command import easy_install

# TODO: We need a better solution for this, probably error exit, once sys.exit
# is optimized for. This is to avoid descending into Nuitka through distutils.
if __name__ == "__main__":
    from nuitka.PythonFlavors import isMSYS2MingwPython
    from nuitka.Version import getNuitkaMsiVersion, getNuitkaVersion

scripts = []

# For Windows, there are batch files to launch Nuitka.
if os.name == "nt" and not isMSYS2MingwPython():
    scripts += ["misc/nuitka.bat", "misc/nuitka-run.bat"]


# The MSI installer enforces a 3 digit version number, which is stupid, but no
# way around it, so we map our number to it, in some way.
if os.name == "nt" and "bdist_msi" in sys.argv:
    version = getNuitkaMsiVersion()
else:
    version = getNuitkaVersion()


def findNuitkaPackages():
    result = []

    for root, dirnames, filenames in os.walk("nuitka"):
        # Packages must contain "__init__.py" or they are merely directories
        # in Nuitka as we are Python2 compatible.
        if "__init__.py" not in filenames:
            continue

        # The "release" namespace is code used to release, but not itself for
        # release, same goes for "quality".
        if "release" in dirnames:
            dirnames.remove("release")
        if "quality" in dirnames:
            dirnames.remove("quality")

        # Handled separatedly.
        if "inline_copy" in dirnames:
            dirnames.remove("inline_copy")

        result.append(root.replace(os.path.sep, "."))

    return result


inline_copy_files = []


def addInlineCopy(name):
    inline_copy_files.extend(
        (
            "inline_copy/%s/*.py" % name,
            "inline_copy/%s/*/*.py" % name,
            "inline_copy/%s/*/*/*.py" % name,
            "inline_copy/%s/*/*/*/*.py" % name,
            "inline_copy/%s/*/*/*/*/*.py" % name,
            "inline_copy/%s/LICENSE*",
            "inline_copy/%s/*/LICENSE*",
            "inline_copy/%s/READ*",
        )
    )


addInlineCopy("appdirs")
addInlineCopy("glob2")
addInlineCopy("markupsafe")
addInlineCopy("tqdm")

sdist_mode = "sdist" in sys.argv

if os.name == "nt" or sdist_mode:
    addInlineCopy("atomicwrites")
    addInlineCopy("clcache")
    addInlineCopy("colorama")

if sys.version_info < (3,) or sdist_mode:
    addInlineCopy("yaml_27")
if (3,) < sys.version_info < (3, 6) or sdist_mode:
    addInlineCopy("yaml_35")
if sys.version_info >= (3, 6) or sdist_mode:
    addInlineCopy("yaml")

if sys.version_info < (3, 6) or sdist_mode:
    addInlineCopy("jinja2_35")
if sys.version_info >= (3, 6) or sdist_mode:
    addInlineCopy("jinja2")


# Scons really only, with historic naming and positioning. Needs to match the
# "scons.py" in bin with respect to versions selection.
addInlineCopy("bin")

if os.name == "nt" or sdist_mode:
    addInlineCopy("lib/scons-4.3.0")
if (os.name != "nt" and sys.version_info < (2, 7)) or sdist_mode:
    addInlineCopy("lib/scons-2.3.2")
if (os.name != "nt" and sys.version_info >= (2, 7)) or sdist_mode:
    addInlineCopy("lib/scons-3.1.2")

# Have different project names for MSI installers, so 32 and 64 bit versions do
# not conflict.
if "bdist_msi" in sys.argv:
    project_name = "Nuitka%s" % (64 if "AMD64" in sys.version else 32)
else:
    project_name = "Nuitka"

import distutils.util

orig_byte_compile = distutils.util.byte_compile


def byte_compile(py_files, *args, **kw):
    # Disable bytecode compilation output, too annoying.
    kw["verbose"] = 0

    orig_byte_compile(py_files, *args, **kw)


distutils.util.byte_compile = byte_compile


# We monkey patch easy install script generation to not load pkg_resources,
# which is very slow to launch. This can save one second or more per launch
# of Nuitka.
runner_script_template = """\
# -*- coding: utf-8 -*-
# Launcher for Nuitka

import nuitka.__main__
nuitka.__main__.main()
"""

# This is for newer setuptools:
@classmethod
def get_args(cls, dist, header=None):
    """
    Yield write_script() argument tuples for a distribution's
    console_scripts and gui_scripts entry points.
    """
    if header is None:
        header = cls.get_header()

    for type_ in "console", "gui":
        group = type_ + "_scripts"

        for name, _ep in dist.get_entry_map(group).items():
            script_text = runner_script_template

            args = cls._get_script_args(  # pylint: disable=protected-access
                type_, name, header, script_text
            )
            for res in args:
                yield res


try:
    easy_install.ScriptWriter.get_args = get_args
except AttributeError:
    pass

# This is for older setuptools:
def get_script_args(dist, executable=os.path.normpath(sys.executable), wininst=False):
    """Yield write_script() argument tuples for a distribution's entrypoints"""
    header = easy_install.get_script_header("", executable, wininst)
    for group in "console_scripts", "gui_scripts":
        for name, _ep in dist.get_entry_map(group).items():
            script_text = runner_script_template
            if sys.platform == "win32" or wininst:
                # On Windows/wininst, add a .py extension and an .exe launcher
                if group == "gui_scripts":
                    launcher_type = "gui"
                    ext = "-script.pyw"
                    old = [".pyw"]
                    new_header = re.sub("(?i)python.exe", "pythonw.exe", header)
                else:
                    launcher_type = "cli"
                    ext = "-script.py"
                    old = [".py", ".pyc", ".pyo"]
                    new_header = re.sub("(?i)pythonw.exe", "python.exe", header)
                if (
                    os.path.exists(new_header[2:-1].strip('"'))
                    or sys.platform != "win32"
                ):
                    hdr = new_header
                else:
                    hdr = header
                yield (name + ext, hdr + script_text, "t", [name + x for x in old])
                yield (
                    name + ".exe",
                    easy_install.get_win_launcher(launcher_type),
                    "b",  # write in binary mode
                )
                if not easy_install.is_64bit():
                    # install a manifest for the launcher to prevent Windows
                    #  from detecting it as an installer (which it will for
                    #  launchers like easy_install.exe). Consider only
                    #  adding a manifest for launchers detected as installers.
                    #  See Distribute #143 for details.
                    m_name = name + ".exe.manifest"
                    yield (m_name, easy_install.load_launcher_manifest(name), "t")
            else:
                # On other platforms, we assume the right thing to do is to
                # just write the stub with no extension.
                yield (name, header + script_text)


try:
    easy_install.get_script_args
except AttributeError:
    pass
else:
    easy_install.get_script_args = get_script_args

binary_suffix = "%d" % sys.version_info[0]

if os.name == "nt" and not isMSYS2MingwPython():
    console_scripts = []
else:
    console_scripts = [
        "nuitka%s = nuitka.__main__:main" % binary_suffix,
        "nuitka%s-run = nuitka.__main__:main" % binary_suffix,
    ]


with open("README.rst", "rb") as input_file:
    long_description = input_file.read().decode("utf8")

    # Need to remove the ..contents etc from the rest, or else PyPI will not render
    # it.
    long_description = long_description.replace(".. contents::\n", "")
    long_description = long_description.replace(
        ".. image:: doc/images/Nuitka-Logo-Symbol.png\n", ""
    )

setup(
    name=project_name,
    license="Apache License, Version 2.0",
    version=version,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        # Nuitka is mature even
        "Development Status :: 5 - Production/Stable",
        # Indicate who Nuitka is for
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        # Nuitka is a compiler and a build tool as such.
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Build Tools",
        # Is has a weak subset of PyLint, but aims for more long term
        "Topic :: Software Development :: Quality Assurance",
        # Nuitka standalone mode aims at distribution
        "Topic :: System :: Software Distribution",
        # Python2 supported versions.
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        # Python3 supported versions.
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        # We depend on CPython.
        "Programming Language :: Python :: Implementation :: CPython",
        # We generate C intermediate code and implement part of the
        # run time environment in C. Actually C11.
        "Programming Language :: C",
        # Supported OSes are many
        "Operating System :: POSIX :: Linux",
        "Operating System :: POSIX :: BSD :: FreeBSD",
        "Operating System :: POSIX :: BSD :: NetBSD",
        "Operating System :: POSIX :: BSD :: OpenBSD",
        "Operating System :: Microsoft :: Windows",
        # License
        "License :: OSI Approved :: Apache Software License",
    ],
    packages=findNuitkaPackages(),
    package_data={
        # Include extra files
        "": ["*.txt", "*.rst", "*.c", "*.h", "*.yml"],
        "nuitka.build": [
            "Backend.scons",
            "Onefile.scons",
            "static_src/*.c",
            "static_src/*.cpp",
            "static_src/*/*.c",
            "static_src/*/*.h",
            "inline_copy/zstd/*.h",
            "inline_copy/zstd/*/*.h",
            "inline_copy/zstd/*/*.c",
            "static_src/*/*.asm",
            "static_src/*/*.S",
            "include/*.h",
            "include/*/*.h",
            "include/*/*/*.h",
        ]
        + inline_copy_files,
        "nuitka.codegen": ["templates_c/*.j2"],
    },
    # metadata for upload to PyPI
    author="Kay Hayen",
    author_email="Kay.Hayen@gmail.com",
    url="https://nuitka.net",
    description="""\
Python compiler with full language support and CPython compatibility""",
    keywords="compiler,python,nuitka",
    project_urls={
        "Commercial": "https://nuitka.net/doc/commercial.html",
        "Support": "https://nuitka.net/pages/support.html",
        "Documentation": "https://nuitka.net/doc/user-manual.html",
        "Donations": "https://nuitka.net/pages/donations.html",
        "Twitter": "https://twitter.com/KayHayen",
        "Source": "https://github.com/Nuitka/Nuitka",
    },
    zip_safe=False,
    scripts=scripts,
    entry_points={
        "distutils.commands": [
            "bdist_nuitka = \
             nuitka.distutils.DistutilCommands:bdist_nuitka",
            "build_nuitka = \
             nuitka.distutils.DistutilCommands:build",
            "install_nuitka = \
             nuitka.distutils.DistutilCommands:install",
        ],
        "distutils.setup_keywords": [
            "build_with_nuitka = nuitka.distutils.DistutilCommands:setupNuitkaDistutilsCommands"
        ],
        "console_scripts": console_scripts,
    },
)
