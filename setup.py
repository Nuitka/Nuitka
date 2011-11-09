#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#

import sys, os

if not hasattr( sys, "version_info" ) or sys.version_info < ( 2, 6, 0, "final" ):
    raise SystemExit( "Nuitka requires Python 2.6 or later." )

if sys.version_info[0] >= 3:
    raise SystemExit( "Nuitka is not currently ported to 3.x, please help." )

scripts = [ "bin/Nuitka.py" ]

if "win" in sys.platform:
    scripts.append( "misc/Nuitka.bat" )
else:
    scripts.append( "bin/Python" )

def detectVersion():
    version_line, = [
        line
        for line in
        open( "nuitka/Options.py" )
        if line.startswith( "Nuitka V" )
    ]

    return version_line.split( "V" )[1].strip()

version = detectVersion()

# py2exe needs to be installed to work
try:
    import py2exe
    py2exeloaded = True
except ImportError:
    py2exeloaded = False

extra = {}

if py2exeloaded:
    extra[ "console" ] = [
        {
            "script"          : "Nuitka.py",
            "copyright"       : "Copyright (C) 2011 Kay Hayen",
            "product_version" : version
        }
    ]

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
            if '\0' in data:
                continue

            data = data.replace( "@LIBDIR@", libdir.encode( "string_escape" ) )
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
            if filename.endswith( ".cpp" ) or filename.endswith( ".h" ) or filename.endswith( ".asm" ):
                result.append( os.path.join( root, filename ) )

    return result


setup(
    name     = "Nuitka",
    license  = "GPLv3",
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
    author_email = "kayhayen@gmx.de",
    url          = "http://nuitka.net",
    description  = "Python compiler with full language support and CPython compatibility",

    keywords     = "compiler,python,nuitka",
)
