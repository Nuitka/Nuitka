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
""" Pack and copy files for portable mode.

usage: PortableSetup.py mainscript outputdir

"""

import sys
import os
import zipfile

python_library_archive_name = "_python.zip"
python_dll_dir_name = "_python"

python_executable_suffixes = ( ".py", ".pyc", ".pyo" )
builtin_module_names = list( sys.builtin_module_names ) + [ "_io" ]

def importList( *names ):
    for name in names:
        __import__( name )

DependencyResolver = {
    "_ssl": ( importList, "socket", "_socket" ),
}

def isPythonScript( path ):
    for end in python_executable_suffixes:
        if path.endswith( end ):
            return 1
    return 0

def copyFile( src, dst ):
    if os.path.isfile( dst ):
        os.remove( dst )
    with open( src, "rb" ) as p:
        data = p.read()
    with open( dst, "wb" ) as p:
        p.write( data )
        p.flush()

def getImportedDict( mainscript ):
    # importing a lot of stuff, just because they are dependencies, pylint: disable=W0612,R0914

    # chdir to mainscript directory and add it to sys.path
    main_dir = os.path.dirname( mainscript )
    os.chdir( main_dir )
    sys.path.insert( 0, main_dir )

    # import modules needed but not listed in sys.modules
    import imp, zipimport, site, io, marshal, pickle
    import encodings, encodings.aliases, codecs
    import zlib, inspect, threading, traceback
    import ctypes
    if sys.version_info < ( 3, 0, 0 ):
        import StringIO, cStringIO
        import cPickle
        import thread
    for code in encodings.aliases.aliases.keys():
        try:
            encodings.search_function( code )
        except ( ImportError, AttributeError ):
            pass

    # get modules from main script
    import modulefinder
    finder = modulefinder.ModuleFinder()
    finder.run_script( mainscript )

    # resolve dependency
    for name in finder.modules.keys():
        method = DependencyResolver.get( name )
        if not method:
            continue
        method[0]( *method[1:] )

    # merge sys.modules
    imported_dict = {}
    imported_dict.update( sys.modules )
    imported_dict.update( finder.modules )
    return imported_dict

def getImportedPathList( imported_dict ):
    imported_list = []
    module_base = os.path.dirname( os.__file__ )
    if os.name == "nt":
        module_base_dlls = os.path.join(
            os.path.dirname( sys.executable ),
            "DLLs"
        )
    for name, mod in imported_dict.items():
        if not mod:
            continue
        if not hasattr( mod, "__file__" ) or mod.__file__ is None:
            # builtin module, if mod is modulefinder.Module then __file__ will
            # be None
            if name not in builtin_module_names:
                import warnings
                warnings.warn( "unknown builtin module %s\n" % repr( name ), Warning )
            continue
        path = mod.__file__
        if path.startswith( module_base ):
            imported_list.append( path )
            continue
        if ( os.name == "nt" and not isPythonScript( path )
            and path.startswith( module_base_dlls ) ):
            imported_list.append( path )
            continue
    return imported_list

def getCopyList( imported_list ):
    zip_list = []
    bin_list = []
    for path in imported_list:
        if isPythonScript( path ):
            path_base = path.rsplit( ".", 1 )[0]
            for end in python_executable_suffixes:
                path_pack = path_base + end
                if os.path.isfile( path_pack ):
                    zip_list.append( path_pack )
        else:
            bin_list.append( path )
    return zip_list, bin_list

def copyPythonLibrary( outputdir ):
    if os.name == "posix" and os.uname()[0] == "Linux":
        with open( "/proc/%s/smaps" % os.getpid() ) as pmap:
            for line in pmap:
                if line.find("libpython") != -1:
                    src = line[ line.find( "/" ): ].strip()
                    dst = os.path.join( outputdir, os.path.basename ( src ) )
                    copyFile( src, dst )
                    break
    elif os.name == "nt":
        import ctypes
        from ctypes import windll
        from ctypes.wintypes import HANDLE, LPCSTR, DWORD
        dll = getattr( windll, "python%s%s" % ( sys.version_info[:2] ) )
        getname = windll.kernel32.GetModuleFileNameA
        getname.argtypes = ( HANDLE, LPCSTR, DWORD )
        getname.restype = DWORD
        result = ctypes.create_string_buffer( 1024 )
        size = getname( dll._handle, result, 1024 ) # needed for this call, pylint: disable=W0212
        src = result.value[ :size ]
        dst = os.path.join( outputdir, os.path.basename ( src ) )
        copyFile( src, dst )
    else:
        # TODO: Add support for bsd and osx here
        sys.exit( "Error, unsupported platform for portable binaries." )

def main( mainscript, outputdir ):
    imported_dict = getImportedDict( mainscript )
    imported_list = getImportedPathList( imported_dict )
    zip_list, bin_list = getCopyList( imported_list )

    # pack script to archive
    base_length = len( os.path.dirname( os.__file__ ) ) + 1
    zip_path = os.path.join( outputdir, python_library_archive_name )

    with zipfile.ZipFile( zip_path, "w", zipfile.ZIP_STORED ) as zip_file:
        for path in zip_list:
            zip_file.write( path, path[ base_length: ] )

    # copy extensions to directory
    import shutil
    library_directory = os.path.join( outputdir, python_dll_dir_name )
    if os.path.isdir( library_directory ):
        shutil.rmtree( library_directory )
    if not os.path.isdir( library_directory ):
        os.makedirs( library_directory )
    for src in bin_list:
        dst = os.path.join( library_directory, os.path.basename( src ) )
        copyFile( src, dst )

    # copy libpython
    copyPythonLibrary( outputdir )

def setup( mainscript, outputdir ):
    # if use this script as module, use this method
    import subprocess
    proc = subprocess.Popen(
        args   = ( sys.executable, __file__, mainscript, outputdir ),
        stdout = sys.stdout,
        stderr = sys.stderr,
        stdin  = sys.stdin,
        shell  = 0
    )
    proc.wait()
    return ( proc.poll() == 0 )

if __name__ == "__main__":
    main(
        mainscript = os.path.abspath( sys.argv[1] ),
        outputdir  = os.path.abspath( sys.argv[2] )
    )
