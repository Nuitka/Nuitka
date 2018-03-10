#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os
import sys
from distutils.command.install_scripts import install_scripts
from setuptools import setup

os.chdir(os.path.dirname(__file__) or '.')


# Detect the version of Nuitka from its source directly. Without calling it, we
# don't mean to pollute with ".pyc" files and similar effects.
def detectVersion():
    with open("nuitka/Version.py") as version_file:
        version_line, = [
            line
            for line in
            version_file

            if line.startswith("Nuitka V")
        ]

        return version_line.split('V')[1].strip()

version = detectVersion()

# The MSI installer enforces a 3 digit version number, which is stupid, but no
# way around it, so we map our number to it, in some way.
if os.name == "nt" and "bdist_msi" in sys.argv:

    # Pre-releases are always smaller, official releases get the "1".
    middle = 1 if "rc" not in version else 0
    version = version.replace("rc", "")
    parts = version.split('.')
    major, first, last = parts[:3]
    hotfix = parts[3] if len(parts) > 3 else 0

    version = '.'.join(
        "%s" % value
        for value in
        (
            int(major)*10+int(first),
            middle,
            int(last)*10+int(hotfix)
        )
    )


def findNuitkaPackages():
    result = []

    for root, dirnames, filenames in os.walk("nuitka"):
        # Ignore the inline copy of scons, these are not packages of Nuitka.
        if "scons-" in root:
            continue

        # Packages must contain "__init__.py" or they are merely directories
        # in Nuitka as we are Python2 compatible.
        if "__init__.py" not in filenames:
            continue

        # The "release" namespace is code used to release, but not itself for
        # release, same goes for "qualit"y.
        if "release" in dirnames:
            dirnames.remove("release")
        if "quality" in dirnames:
            dirnames.remove("quality")

        result.append(
            root.replace(os.path.sep,'.')
        )

    return result


# Fix for "develop", where the generated scripts from easy install are not
# capable of running in their re-executing, not finding pkg_resources anymore.
if "develop" in sys.argv:
    try:
        import setuptools.command.easy_install
    except ImportError:
        pass
    else:
        orig_easy_install = setuptools.command.easy_install.easy_install

        class NuitkaEasyInstall(setuptools.command.easy_install.easy_install):
            @staticmethod
            def _load_template(dev_path):
                result = orig_easy_install._load_template(dev_path)
                result = result.replace(
                    "__import__('pkg_resources')",
                    "# __import__('pkg_resources')",
                )

                return result

        setuptools.command.easy_install.easy_install = NuitkaEasyInstall

if os.path.exists("/usr/bin/scons") and \
   "sdist" not in sys.argv and \
   "bdist_wininst" not in sys.argv and \
   "bdist_msi" not in sys.argv:
    scons_files = []
else:
    scons_files = [
        "inline_copy/*/*.py",
        "inline_copy/*/*/*.py",
        "inline_copy/*/*/*/*.py",
        "inline_copy/*/*/*/*/*.py",
        "inline_copy/*/*/*/*/*/*.py",
    ]

# Have different project names for MSI installers, so 32 and 64 bit versions do
# not conflict.
if "bdist_msi" in sys.argv:
    project_name = "Nuitka%s" % (64 if "AMD64" in sys.version else 32)
else:
    project_name = "Nuitka"

# Lets hack the byte_compile function so it doesn't byte compile Scons built-in
# copy with Python3.
if sys.version_info >= (3,):
    from distutils import util

    real_byte_compile = util.byte_compile

    def byte_compile(py_files, *args, **kw):
        py_files = [
            py_file
            for py_file in py_files
            if "inline_copy" not in py_file
        ]

        real_byte_compile(py_files, *args, **kw)

    util.byte_compile = byte_compile


setup(
    name         = project_name,
    license      = "Apache License, Version 2.0",
    version      = version,
    classifiers  = [
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
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",

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
    packages     = findNuitkaPackages(),
    # cmdclass     = cmdclass,

    package_data = {
        # Include extra files
        "" : ["*.txt", "*.rst", "*.c", "*.h", "*.ui"],
        "nuitka.build" : [
            "SingleExe.scons",
            "static_src/*.c",
            "static_src/*/*.c",
            "static_src/*/*.h",
            "static_src/*/*.asm",
            "static_src/*/*.S",
            "include/*.h",
            "include/*/*.h",
            "include/*/*/*.h",
        ] + scons_files,
        "nuitka.gui" : [
            "dialogs/*.ui",
        ],
    },

    # metadata for upload to PyPI
    author       = "Kay Hayen",
    author_email = "Kay.Hayen@gmail.com",
    url          = "http://nuitka.net",
    description  = """\
Python compiler with full language support and CPython compatibility""",
    keywords     = "compiler,python,nuitka",
    entry_points = {"distutils.commands": [
                        'bdist_nuitka = \
                         nuitka.distutils.bdist_nuitka:bdist_nuitka'
                    ],
                    "distutils.setup_keywords": [
                        'build_with_nuitka = \
                         nuitka.distutils.bdist_nuitka:setuptools_build_hook'
                    ],
                    "console_scripts": ['nuitka = nuitka.__main__',
                                        'nuitka-run = nuitka.__main__'],
                   },
)
