#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

import sys, os

scripts = ["bin/nuitka", "bin/nuitka-run"]

# For Windows, there are batch files to launch Nuitka.
if os.name == "nt":
    scripts += ["misc/nuitka.bat", "misc/nuitka-run.bat"]

# Detect the version of Nuitka from its source directly. Without calling it, we
# don't mean to pollute with ".pyc" files and similar effects.
def detectVersion():
    version_line, = [
        line
        for line in
        open("nuitka/Options.py")
        if line.startswith( "Nuitka V")
    ]

    return version_line.split("V")[1].strip()

version = detectVersion()

# The MSI installer enforces a 3 digit version number, which is stupid, but no
# way around it, so we map our number to it, in some way.
if os.name == "nt" and "bdist_msi" in sys.argv:

    # Prereleases are always smaller, official releases get the "1".
    middle = 1 if "pre" not in version else 0
    version = version.replace("pre", "")
    parts = version.split(".")
    major, first, last = parts[:3]
    hotfix = parts[3] if len(parts) > 3 else 0

    version = ".".join(
        "%s" % value
        for value in
        (
            int(major)*10+int(first),
            middle,
            int(last)*10+int(hotfix)
        )
    )

def find_packages():
    result = []

    for root, _dirnames, filenames in os.walk("nuitka"):
        # Ignore the inline copy of scons, these are not packages of Nuitka.
        if "scons-" in root:
            continue

        # Packages must contain "__init__.py" or they are merely directories.
        if "__init__.py" not in filenames:
            continue

        result.append(
            root.replace(os.path.sep,".")
        )

    return result

package = find_packages()

from distutils.command.install_scripts import install_scripts
class nuitka_installscripts( install_scripts ):
    """
    This is a specialization of install_scripts that replaces the @LIBDIR@ with
    the configured directory for modules. If possible, the path is made relative
    to the directory for scripts.
    """

    def initialize_options( self ):
        install_scripts.initialize_options(self)

        self.install_lib = None

    def finalize_options( self ):
        install_scripts.finalize_options(self)

        self.set_undefined_options("install", ("install_lib", "install_lib"))

    def run(self):
        install_scripts.run(self)

        if os.path.splitdrive(self.install_dir)[0] != os.path.splitdrive(self.install_lib)[0]:
            # can't make relative paths from one drive to another, so use an
            # absolute path instead
            libdir = self.install_lib
        else:
            common = os.path.commonprefix(
                (self.install_dir, self.install_lib )
            )
            rest = self.install_dir[len(common):]
            uplevel = len([n for n in os.path.split(rest) if n ])

            libdir = uplevel * (".." + os.sep) + self.install_lib[len(common):]

        patch_bats = os.path.exists(
            os.path.join(self.install_dir, "Python.exe")
        )

        for outfile in self.outfiles:
            fp = open(outfile, "rb")
            data = fp.read()
            fp.close()

            # skip binary files
            if b'\0' in data:
                continue

            data = data.replace( b"@LIBDIR@", libdir.encode("unicode_escape"))

            if patch_bats and outfile.endswith(".bat"):
                data = data.replace("..\\","")

            fp = open(outfile, "wb")
            fp.write(data)
            fp.close()

cmdclass = {
    "install_scripts" : nuitka_installscripts
}

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

from distutils.core import setup

setup(
    name     = project_name,
    license  = "Apache License, Version 2.0",
    version  = version,
    packages = find_packages(),
    scripts  = scripts,
    cmdclass = cmdclass,

    package_data = {
        # Include extra files
        "" : ['*.txt', '*.rst', '*.cpp', '*.hpp', '*.ui'],
        "nuitka.build" : [
            "SingleExe.scons",
            "static_src/*.cpp",
            "static_src/*/*.cpp",
            "static_src/*/*.h",
            "static_src/*/*.asm",
            "static_src/*/*.S",
            "include/*.hpp",
            "include/*/*.hpp",
            "include/*/*/*.hpp",
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
)
