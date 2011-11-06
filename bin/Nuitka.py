#!/usr/bin/env python
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

"""

This main program translates one module to a C++ source code using Python C/API and
optionally compiles it to either an executable or an extension module.

"""

import sys, os

libdir = '@LIBDIR@'

# Two cases:
if libdir != '@' 'LIBDIR' '@':
    # Changed by our distutils hook, then use the given path.

    if not os.path.isabs( libdir ):
        libdir = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), libdir )
        libdir = os.path.abspath( libdir )

    sys.path.insert( 0, libdir )
else:
    # Unchanged, running from checkout, use the parent directory, the nuitka package ought be there.
    sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), ".." ) )

import logging
logging.basicConfig( format = 'Nuitka:%(levelname)s:%(message)s' )

from nuitka import MainControl, Options

positional_args = Options.getPositionalArgs()

if len( positional_args ) == 0:
    sys.exit( "Error, need arg with python module or main program." )

filename = Options.getPositionalArgs()[0]

# Turn that source code into a node tree structure.
try:
    tree = MainControl.createNodeTree(
        filename = filename
    )
except (SyntaxError, IndentationError) as e:
    filename, lineno, colno, message = e.args[1]

    colno = colno - len( message ) + len( message.lstrip() )

    exit_message = """\
  File "%s", line %d
    %s
    %s^
%s: invalid syntax""" % (
       filename,
       lineno,
       message.strip(),
       " " * (colno-1),
       e.__class__.__name__
    )

    sys.exit( exit_message )

if Options.shallDumpBuiltTree():
    MainControl.dumpTree( tree )
elif Options.shallDumpBuiltTreeXML():
    MainControl.dumpTreeXML( tree )
elif Options.shallDisplayBuiltTree():
    MainControl.displayTree( tree )
else:
    if not Options.shallOnlyExecGcc():
        # Now build the target language code for the whole tree.
        MainControl.makeSourceDirectory(
            main_module = tree
        )

    # Run the Scons to build things.
    result, options = MainControl.runScons(
        tree  = tree,
        quiet = not Options.isShowScons()
    )

    # Exit if compilation failed.
    if not result:
        sys.exit( 1 )


    # Execute the module immediately if option was given.
    if Options.shallExecuteImmediately():
        if Options.shallMakeModule():
            MainControl.executeModule( tree )
        else:
            MainControl.executeMain( options[ "result_file" ] + ".exe", tree )
