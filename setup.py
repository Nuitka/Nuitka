#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

scripts = [ "bin/nuitka", "bin/nuitka-python" ]

if os.name == "nt":
    scripts += [ "misc/nuitka.bat", "misc/nuitka-python.bat" ]

def detectVersion():
    version_line, = [
        line
        for line in
        open( "nuitka/Options.py" )
        if line.startswith( "Nuitka V" )
    ]

    return version_line.split( "V" )[1].strip()

version = detectVersion()

def find_packages():
    result = []

    for root, _dirnames, filenames in os.walk( "nuitka" ):
        if "scons-2.0.1" in root:
            continue

        if "__init__.py" not in filenames:
            continue

        result.append( root.replace( os.path.sep, "." ) )

    return result

package = find_packages()

from distutils.core import setup, Command, Extension

from distutils.command.install_scripts import install_scripts
class nuitka_installscripts( install_scripts ):
    """
    This is a specialization of install_scripts that replaces the @LIBDIR@ with
    the configured directory for modules. If possible, the path is made relative
    to the directory for scripts.
    """

    def initialize_options( self ):
        install_scripts.initialize_options( self )

        self.install_lib = None

    def finalize_options( self ):
        install_scripts.finalize_options(self)

        self.set_undefined_options( "install", ( "install_lib", "install_lib" ) )

    def run( self ):
        install_scripts.run( self )

        if ( os.path.splitdrive( self.install_dir )[0] != os.path.splitdrive( self.install_lib )[0] ):
            # can't make relative paths from one drive to another, so use an
            # absolute path instead
            libdir = self.install_lib
        else:
            common = os.path.commonprefix( (self. install_dir, self.install_lib ) )
            rest = self.install_dir[ len(common) : ]
            uplevel = len( [n for n in os.path.split( rest ) if n ] )

            libdir = uplevel * ( ".." + os.sep ) + self.install_lib[ len(common) : ]

        for outfile in self.outfiles:
            fp = open( outfile, "rb" )
            data = fp.read()
            fp.close()

            # skip binary files
            if b'\0' in data:
                continue

            data = data.replace( b"@LIBDIR@", libdir.encode( "unicode_escape" ) )
            fp = open( outfile, "wb" )
            fp.write( data )
            fp.close()

cmdclass = {
    "install_scripts": nuitka_installscripts
}

def findSources():
    result = []

    for root, _dirnames, filenames in os.walk( "src" ):
        for filename in filenames:
            if filename.endswith( ".cpp" ) or filename.endswith( ".h" ) or filename.endswith( ".asm" ) or filename.endswith( ".S" ):
                result.append( os.path.join( root, filename ) )

    return result


setup(
    name     = "Nuitka",
    license  = "Apache License, Version 2.0",
    version  = version,
    packages = find_packages(),
    scripts  = scripts,
    cmdclass = cmdclass,

    package_data = {
        # Include extra files
        "" : ['*.txt', '*.rst', '*.cpp', '*.hpp', '*.ui' ],
        "nuitka.build" : [
            "SingleExe.scons",
            "inline_copy/*/*.py",
            "inline_copy/*/*/*.py",
            "inline_copy/*/*/*/*.py",
            "inline_copy/*/*/*/*/*.py",
            "inline_copy/*/*/*/*/*/*.py",
            "static_src/*.cpp",
            "static_src/*/*.cpp",
            "static_src/*/*.h",
            "static_src/*/*.asm",
            "static_src/*/*.S",
            "include/*.hpp",
            "include/*/*.hpp",
            "include/*/*/*.hpp",
        ],
        "nuitka.gui" : [
            "dialogs/*.ui",
        ],
    },

    # metadata for upload to PyPI
    author       = "Kay Hayen",
    author_email = "Kay.Hayen@gmail.com",
    url          = "http://nuitka.net",
    description  = "Python compiler with full language support and CPython compatibility",

    keywords     = "compiler,python,nuitka",
)
