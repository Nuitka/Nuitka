#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Setup file for Nuitka.

This applies a few tricks. First, the Nuitka version is read from
the source code. Second, the packages are scanned from the filesystem,
and third, the byte code compilation is avoided for inline copies of
scons with mismatching Python major versions. Also a binary distribution
is enforced, to avoid being cached with wrong inline copies for the
Python version.

spellchecker: ignore chdir,pythonw,tqdm,distutil,atomicwrites,markupsafe
spellchecker: ignore wininst,distclass,Containerfile,orderedset
"""

import os
import sys

os.chdir(os.path.dirname(__file__) or ".")
sys.path.insert(0, os.path.abspath(os.getcwd()))

# Disable setuptools warnings before importing it.
import warnings

warnings.filterwarnings("ignore", "")

# Don't allow importing this, and make recognizable that
# the above imports are not to follow. Sometimes code imports
# setup and then Nuitka ends up including itself.
if __name__ != "__main__":
    sys.exit("Cannot import 'setup' module of Nuitka")

# isort:start

import fnmatch
import re

from setuptools import Distribution, setup
from setuptools.command import easy_install

from nuitka.PythonFlavors import isMSYS2MingwPython
from nuitka.utils.FileOperations import getFileList
from nuitka.Version import getNuitkaVersion

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

        # Handled separately.
        if "inline_copy" in dirnames:
            dirnames.remove("inline_copy")

        result.append(root.replace(os.path.sep, "."))

    return result


inline_copy_files = []
no_byte_compile = []


def addDataFiles(data_files, base_path, do_byte_compile=True):
    patterns = (
        "%s/*.py" % base_path,
        "%s/*/*.py" % base_path,
        "%s/*/*/*.py" % base_path,
        "%s/*/*/*/*.py" % base_path,
        "%s/*/*/*/*/*.py" % base_path,
        "%s/config*" % base_path,
        "%s/LICENSE*" % base_path,
        "%s/*/LICENSE*" % base_path,
        "%s/READ*" % base_path,
    )

    data_files.extend(patterns)

    if not do_byte_compile:
        no_byte_compile.extend(patterns)


def addInlineCopy(name, do_byte_compile=True):
    if os.getenv("NUITKA_NO_INLINE_COPY", "0") == "1":
        return

    addDataFiles(
        inline_copy_files, "inline_copy/%s" % name, do_byte_compile=do_byte_compile
    )


addInlineCopy("appdirs")
addInlineCopy("glob2")
addInlineCopy("markupsafe")
addInlineCopy("tqdm")

addInlineCopy("stubgen")

sdist_mode = "sdist" in sys.argv
install_mode = "install" in sys.argv

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

addInlineCopy("pkg_resources")

# Scons really only, with historic naming and positioning. Needs to match the
# "scons.py" in bin with respect to versions selection.
addInlineCopy("bin")

if os.name == "nt" or sdist_mode:
    addInlineCopy("lib/scons-4.3.0", do_byte_compile=sys.version_info >= (3,))
if (os.name != "nt" and sys.version_info < (2, 7)) or sdist_mode:
    addInlineCopy("lib/scons-2.3.2")
if (os.name != "nt" and sys.version_info >= (2, 7)) or sdist_mode:
    addInlineCopy("lib/scons-3.1.2")

nuitka_packages = findNuitkaPackages()

# Include extra files
package_data = {
    "": ["*.txt", "*.rst", "*.c", "*.h", "*.yml"],
    "nuitka.build": [
        "*.scons",
        "static_src/*.c",
        "static_src/*.cpp",
        "static_src/*/*.c",
        "static_src/*/*.h",
        "inline_copy/zstd/LICENSE.txt",
        "inline_copy/zstd/*.h",
        "inline_copy/zstd/*/*.h",
        "inline_copy/zstd/*/*.c",
        "inline_copy/zlib/LICENSE",
        "inline_copy/zlib/*.h",
        "inline_copy/zlib/*.c",
        "inline_copy/python_hacl/LICENSE.txt",
        "inline_copy/python_hacl/hacl_312/*.h",
        "inline_copy/python_hacl/hacl_312/*.c",
        "inline_copy/python_hacl/hacl_312/*/*.h",
        "inline_copy/python_hacl/hacl_312/*/*/*.c",
        "inline_copy/python_hacl/hacl_312/*/*/*.h",
        "inline_copy/python_hacl/hacl_312/*/*/*/*.h",
        "static_src/*/*.asm",
        "static_src/*/*.S",
        "include/*.h",
        "include/*/*.h",
        "include/*/*/*.h",
    ]
    + inline_copy_files,
    "nuitka.code_generation": ["templates_c/*.j2"],
    "nuitka.reports": ["*.j2"],
    "nuitka.plugins.standard": ["*/*.c", "*/*.py"],
}


if "nuitka.plugins.commercial" in nuitka_packages:
    commercial_data_files = []

    commercial_plugins_dir = os.path.join("nuitka", "plugins", "commercial")

    for filename in getFileList(commercial_plugins_dir):
        filename_relative = os.path.relpath(filename, commercial_plugins_dir)

        if (
            filename_relative.endswith(".py")
            and os.path.basename(filename_relative) == filename_relative
        ):
            continue

        if filename.endswith((".py", ".yml", ".c", ".h", ".plk", ".tmd")):
            commercial_data_files.append(filename_relative)
            continue

        filename_base = os.path.basename(filename_relative)

        if filename_base.startswith("LICENSE"):
            commercial_data_files.append(filename_relative)
            continue

    package_data["nuitka.plugins.commercial"] = commercial_data_files
    package_data["nuitka.tools.commercial.container_build"] = ["Containerfile"]

try:
    import distutils.util
except ImportError:
    # Python 3.12 might do this, we need to find out where to disable the
    # bytecode compilation there.
    pass
else:
    orig_byte_compile = distutils.util.byte_compile

    def byte_compile(py_files, *args, **kw):
        # Disable bytecode compilation output, too annoying.
        kw["verbose"] = 0

        # Avoid attempting files that won't work.
        py_files = [
            filename
            for filename in py_files
            if not any(
                fnmatch.fnmatch(filename, "*/*/*/" + pattern)
                for pattern in no_byte_compile
            )
        ]

        orig_byte_compile(py_files, *args, **kw)


distutils.util.byte_compile = byte_compile


# We monkey patch easy install script generation to not load pkg_resources,
# which is very slow to launch. This can save one second or more per launch
# of Nuitka.
runner_script_template = """\
# -*- coding: utf-8 -*-
# Launcher for Nuitka

import %(package_name)s
%(package_name)s.%(function_name)s()
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

        for name, ep in dist.get_entry_map(group).items():
            package_name, function_name = str(ep).split("=")[1].strip().split(":")

            script_text = runner_script_template % {
                "package_name": package_name,
                "function_name": function_name,
            }

            args = cls._get_script_args(type_, name, header, script_text)
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

if str is bytes:
    binary_suffix = "2"
else:
    binary_suffix = ""

if os.name == "nt" and not isMSYS2MingwPython():
    console_scripts = []
else:
    console_scripts = [
        "nuitka%s = nuitka.__main__:main" % binary_suffix,
        "nuitka%s-run = nuitka.__main__:main" % binary_suffix,
    ]

    if "nuitka.plugins.commercial" in nuitka_packages:
        console_scripts.append(
            "nuitka-decrypt = nuitka.tools.commercial.decrypt.__main__:main"
        )

scripts = []

# For Windows, there are CMD batch files to launch Nuitka.
if os.name == "nt" and not isMSYS2MingwPython():
    scripts += ["misc/nuitka.cmd", "misc/nuitka-run.cmd"]

    if "nuitka.plugins.commercial" in nuitka_packages:
        scripts.append("misc/nuitka-decrypt.cmd")


# With this, we can enforce a binary package.
class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""

    @staticmethod
    def has_ext_modules():
        # For "python setup.py install" this triggers an attempt to lookup
        # package dependencies, which fails to work, since it's not yet
        # installed and might not yet be in PyPI as well.
        return not install_mode


with open("README.rst", "rb") as input_file:
    long_description = input_file.read().decode("utf8")

    # Need to remove the ..contents etc from the rest, or else PyPI will not render
    # it.
    long_description = long_description.replace(".. contents::\n", "")
    long_description = long_description.replace(
        ".. image:: doc/images/Nuitka-Logo-Symbol.png\n", ""
    )

install_requires = []
if sys.version_info >= (3, 7):
    install_requires.append("ordered-set >= 4.1.0")
if sys.version_info[:2] == (2, 7):
    install_requires.append("subprocess32")
if sys.version_info >= (3, 7):
    install_requires.append("zstandard >= 0.15")
if os.name != "nt" and sys.platform != "darwin" and sys.version_info < (3, 7):
    install_requires.append("orderedset >= 2.0.3")
if sys.platform == "darwin" and sys.version_info < (3, 7):
    install_requires.append("orderedset >= 2.0.3")

setup(
    name="Nuitka",
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
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
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
        "Operating System :: MacOS",
        "Operating System :: Android",
        # License
        "License :: OSI Approved :: Apache Software License",
    ],
    packages=nuitka_packages,
    package_data=package_data,
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
        "Mastodon": "https://fosstodon.org/@kayhayen",
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
    install_requires=install_requires,
    # As we do version specific hacks for installed inline copies, make the
    # wheel version and platform specific.
    distclass=BinaryDistribution,
    verbose=0,
)

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
