#!/usr/bin/env python
#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Collect the performance data from multiple Nuitka versions. """

import subprocess, sys, os, tempfile, shutil, urllib, urllib2, datetime, socket
import sqlite3, decimal, time

# Quick check that we actually in the correct spot.
assert os.path.exists( "debian" )

from optparse import OptionParser, OptionGroup

parser = OptionParser()

parser.add_option(
    "--run-benchmarks",
    action  = "store_true",
    dest    = "run_benchmarks",
    default = False,
    help    = """Run the benchmarks not previously run."""
)

parser.add_option(
    "--export-codespeed",
    action  = "store_true",
    dest    = "export_codespeed",
    default = False,
    help    = """Export the benchmark data into codespeed."""
)

options, positional_args = parser.parse_args()

# Directory, to locate data in
orig_dir = os.getcwd()

# Directory to use tools from
start_dir = os.getcwd()

# To facilate my home environment
if os.path.exists( "public-repo" ):
    os.chdir( "public-repo" )

# Make git work on here, even if we leave it soon.
os.environ[ "GIT_DIR" ] = os.path.join( os.path.abspath( os.getcwd() ), ".git" )
print "Using git dir", os.environ[ "GIT_DIR" ]

playground_dir = os.path.join( tempfile.gettempdir(), "nuitka_playground" )

def setupPlayground( commit_id ):
    # Go somewhere else.
    os.chdir( tempfile.gettempdir() )

    # Erase the directory.
    shutil.rmtree( playground_dir, True )
    os.makedirs( playground_dir )
    os.chdir( playground_dir )

    # Unpack from git into playground.
    subprocess.check_output( ( "git archive --format=tar %s | tar xf -" % commit_id ), shell = True )

    if commit_id not in ( "develop", ):
        search_id = commit_id

        if search_id[-1].isalpha():
            search_id = search_id[:-1]

        assert search_id in open( "nuitka/Options.py" ).read()

    # Make sure, even old Nuitka will find "nuitka" package.
    os.environ[ "PYTHONPATH" ] = os.getcwd()

def getCommitDate( commit_id ):
    return int( subprocess.check_output( ( 'git show --format=%ct ' + commit_id ).split() ).strip().split( "\n" )[-1] )

def getCommitHash( commit_id ):
    commit_hash = subprocess.check_output( ( 'git show --format=%H ' + commit_id ).split() ).strip().split( "\n" )[-1].strip()

    assert len( commit_hash ) == 40, commit_hash

    return commit_hash

sys.stdout.flush()
sys.stderr.flush()

benchmark_path = "tests/benchmarks/pystone.py"
blacklist_versions = ( "0.3.12c", "0.3.11", "0.3.11a", "0.3.11c" )

class ValgrindBenchmarkBase:
    def __init__( self, name ):
        self.name = name
        self.result = {}

    def execute( self, python_version, compiler = None ):
        if os.path.exists( os.path.join( "bin", "Nuitka.py" ) ):
            binary = "Nuitka.py"
        else:
            binary = "nuitka"

        binary = os.path.join( "bin", binary )

        # Used by run_valgrind.py
        os.environ[ "NUITKA_BINARY" ] = "python%s %s" % ( python_version, binary )

        # Very old Nuitka needs that.
        if os.path.exists( "scons" ):
            os.environ[ "NUITKA_SCONS" ] = "scons"

        # Very old Nuitka needs that.
        if os.path.exists( "include" ):
            os.environ[ "NUITKA_INCLUDE" ] = "include"

        os.environ[ "NUITKA_EXTRA_OPTIONS" ] = self.getExtraArguments()

        output = subprocess.check_output( ( os.path.join( start_dir, "misc", "run-valgrind.py" ), benchmark_path, "number" ) ).strip()

        self.result[ "EXE_SIZE" ] = int( output.split( "\n" )[-2].split("=")[1] )
        self.result[ "CPU_TICKS" ] = int( output.split( "\n" )[-1].split("=")[1] )

    def getResults( self ):
        return dict( self.result )

    def getExtraArguments( self ):
        return ""

    def getFilename( self ):
        assert False

    def getProvided( self ):
        return "CPU_TICKS", "EXE_SIZE"

class ValgrindBenchmark( ValgrindBenchmarkBase ):
    def __init__( self, name, filename ):
        ValgrindBenchmarkBase.__init__( self, name )

        filename = os.path.abspath( filename )

        self.filename = filename

    def getName( self ):
        return self.name

    def getFilename( self ):
        return self.filename

    def __repr__( self ):
        return "<%s>" % self.name


class Configuration:
    def __init__( self, name, cpu_model ):
        self.name = name
        self.cpu_model = cpu_model

    def getName( self ):
        return self.name

    def getFullName( self ):
        return "%s %s" % ( self.name, self.cpu_model )

    def __repr__( self ):
        return "<%s / %s>" % ( self.name, self.cpu_model )

    def __cmp__( self, other ):
        r = cmp( self.name, other.name )

        if r == 0:
            return cmp( self.cpu_model, other.cpu_model )
        else:
            return r

    def __hash__( self ):
        return 42


class PystoneValgrindBenchmark( ValgrindBenchmark ):
    def __init__( self ):
        ValgrindBenchmark.__init__(
            self,
            name = "pystone",
            filename = "tests/benchmarks/pystone.py"
        )


    def supports( self, nuitka_version ):
        return nuitka_version.getPythonVersion() < "3"

benchmarks = [
    PystoneValgrindBenchmark(),
]

def detectConfiguration():
    cpu_model = set( [
        line.split( ":", 2 )[1].strip()
        for line in
        open( "/proc/cpuinfo" ).readlines()
        if line.startswith( "model name" )
    ] )

    assert len( cpu_model ) == 1
    cpu_model, = cpu_model

    host_name = socket.gethostname()

    if host_name == "anna":
        host_name = "Kay - Main Dev"

    if host_name == "Juschinka":
        host_name = "Kay - Mobile Dev"

    cpu_model = cpu_model.replace( "(TM)", "" )
    cpu_model = cpu_model.replace( "(tm)", "" )
    cpu_model = cpu_model.replace( "(R)", "" )
    cpu_model = " ".join( cpu_model.split() )
    cpu_model = cpu_model.replace( " @ ", "@" )

    return Configuration( host_name, cpu_model )

this_config = detectConfiguration()

print "Running on", this_config

machines = (
    Configuration( "Kay - Main Dev", "AMD Phenom II X6 1055T Processor" ),
    Configuration( "Kay - Mobile Dev", "Intel Core2 Duo CPU T9300@2.50GHz" )
)

if this_config not in machines:
    sys.exit( "Error, this machine not in configurations, please add %s" % this_config )

class NuitkaVersion:
    def __init__( self, commit_id, python_version ):
        self.commit_id = commit_id
        self.python_version = python_version

    def __repr__( self ):
        return "<Nuitka Version %s on CPython%s>" % ( self.commit_id, self.python_version )

    def getNuitkaVersion( self ):
        return self.commit_id

    def getPythonVersion( self ):
        return self.python_version

def getNuitkaVersions():

    # Collect the versions.
    nuitka_versions = subprocess.check_output( "git tag --list".split() ).strip()
    nuitka_versions = list( sorted( nuitka_versions.split( "\n" ) ) )

    for blacklist_version in ( "0.3.12c", "0.3.11", "0.3.11a", "0.3.11b", "0.3.11c" ):
        nuitka_versions.remove( blacklist_version )

    result = []

    for nuitka_version in nuitka_versions:
        for python_version in ( "2.6", "2.7", "3.2" ):
            result.append(
                NuitkaVersion( nuitka_version, python_version )
            )

    return result

nuitka_versions = getNuitkaVersions()

from collections import defaultdict
tasks = defaultdict( lambda : [] )

class ResultDatabase:
    def __init__( self, machine ):
        self.machine = machine

        self.db_filename = os.path.join( orig_dir, "perf-data", "%s.db" % self.machine.getName() )

        if not os.path.exists( self.db_filename ):
            print "Warning, using absent result database", self.db_filename

        self.connection = None
        self.cursor = None

    def _doSql( self, sql, *args ):
        sql = sql.strip()

        # print "SQL", sql, args

        if self.cursor is None:
            self.connection = sqlite3.connect(
                self.db_filename,
                detect_types = sqlite3.PARSE_DECLTYPES
            )

            self.cursor = self.connection.cursor()

        try:
            result = self.cursor.execute( sql, args ).fetchall()
        except sqlite3.OperationalError, e:
            if "no such table: results" in str(e):
                self._doSql( """
CREATE TABLE results (
nuitka_version varchar(40) not NULL,
commit_id      char(40) not NULL,
python_version varchar(10) not NULL,
benckmark_name varchar(10) not NULL,
key            varchar(40) not NULL,
value          varchar(40) not NULL
);""" )
                result = self.cursor.execute( sql, args ).fetchall()
            else:
                raise

        return result

    def _doCommit( self ):
        self.connection.commit()

    def __cmp__( self, other ):
        return cmp( self.machine, other.machine )

    def getData( self, nuitka_version, python_version, benchmark_name ):
        r = self._doSql(
            """SELECT * FROM results WHERE nuitka_version=? AND python_version=? AND benckmark_name=?""",

            nuitka_version,
            python_version,
            benchmark_name
        )

        return r

    def setData( self, nuitka_version, commit_id, python_version, benchmark_name, key, value ):
        r = self._doSql(
            """INSERT INTO results VALUES ( ?, ?, ?, ?, ?, ? ) """,

            nuitka_version,
            commit_id,
            python_version,
            benchmark_name,
            key,
            value
        )

        self._doCommit()


result_databases = dict()

class Execution:
    def __init__( self, machine, nuitka_version, benchmark ):
        self.machine = machine
        self.nuitka_version = nuitka_version
        self.benchmark = benchmark

        if self.machine in result_databases:
            self.result_database = result_databases[ self.machine ]
        else:
            self.result_database = result_databases[ self.machine ] = ResultDatabase( self.machine )

    def __repr__( self ):
        return "<Machine %s version %s to run %s>" % (
            self.machine,
            self.nuitka_version,
            self.benchmark
        )

    def getMachine( self ):
        return self.machine

    def getExecutable( self ):
        return "nuitka-python%s" % (
            self.nuitka_version.getPythonVersion()
        )

    def getVersion( self ):
        return self.nuitka_version

    def getBenchmark( self ):
        return self.benchmark

    def execute( self ):
        print "Executing", self

        print "Prepare playground", self.nuitka_version.getNuitkaVersion()
        sys.stdout.flush()

        setupPlayground( self.nuitka_version.getNuitkaVersion() )

        self.benchmark.execute( self.nuitka_version.getPythonVersion() )

        result = self.benchmark.getResults()

        for key, value in result.iteritems():
            result_databases[ self.machine ].setData(
                self.nuitka_version.getNuitkaVersion(),
                getCommitHash( self.nuitka_version.getNuitkaVersion() ),
                self.nuitka_version.getPythonVersion(),
                self.benchmark.getName(),
                key,
                value
            )

    def getData( self ):
        result = result_databases[ self.machine ].getData(
            self.nuitka_version.getNuitkaVersion(),
            self.nuitka_version.getPythonVersion(),
            self.benchmark.getName()
        )

        d = {}

        for values in result:
            d[ values[-2] ] = values[-1]

        # print d

        return d

    def hasData( self ):
        return sorted( self.getData().keys() ) == sorted( self.benchmark.getProvided() )



for machine in machines:
    # The pystone should be run everywhere with historic versions and current.

    for nuitka_version in nuitka_versions:
        for benchmark in benchmarks:
            if not benchmark.supports( nuitka_version ):
                continue

            tasks[ machine ].append(
                Execution(
                    machine        = machine,
                    nuitka_version = nuitka_version,
                    benchmark      = benchmark
                )
            )

# Remove the playground again from /tmp
shutil.rmtree( playground_dir, True )

if options.run_benchmarks:
    for task in tasks[ this_config ]:
        if not task.hasData():
            task.execute()


if options.export_codespeed:
    def publishResult( environment, executable, commit_id, benchmark, size, ticks ):
        commit_date = getCommitDate( commit_id )
        commit_date = datetime.datetime.fromtimestamp( commit_date )

        def postdata( params ):
            CODESPEED_URL = 'http://localhost:8000/'

            try:
                f = urllib2.urlopen( CODESPEED_URL + 'result/add/', params )
            except urllib2.URLError as e:
                if "Connection refused" in str(e):
                    print "Launching speedcenter deamon."

                    os.system( "cd %s/web/codespeed/speedcenter; python manage.py runserver &" % orig_dir )
                    time.sleep( 2 )

                    f = urllib2.urlopen( CODESPEED_URL + 'result/add/', params )
                else:
                    raise
            except urllib2.HTTPError as e:
                print str(e)
                print e.read()

                raise

            response = f.read()
            f.close()

        data = {
            # Mandatory fields
            'commitid'      : commit_id,
            'revision_date' : commit_date,
            'branch'        : "default",
            'project'       : "Nuitka",
            'executable'    : executable,
            'benchmark'     : benchmark + " ticks",
            'environment'   : environment,
            'result_value'  : ticks,
            # Optional fields
            'result_date'   : commit_date
        }

        postdata( urllib.urlencode( data ) )

        data = {
            # Mandatory fields
            'commitid'      : commit_id,
            'revision_date' : commit_date,
            'branch'        : 'default',
            'project'       : 'Nuitka',
            'executable'    : executable,
            'benchmark'     : benchmark + ' bytes',
            'environment'   : environment,
            'result_value'  : size,
            # Optional fields
            'result_date'   : commit_date
        }

        postdata( urllib.urlencode( data ) )


    for configuration, tasks in tasks.iteritems():
        for task in tasks:

            publishResult(
                environment = task.getMachine().getName(),
                executable  = task.getExecutable(),
                commit_id   = task.getVersion().getNuitkaVersion(),
                benchmark   = task.getBenchmark().getName(),
                size        = task.getData()[ "EXE_SIZE" ],
                ticks       = task.getData()[ "CPU_TICKS" ]
            )
