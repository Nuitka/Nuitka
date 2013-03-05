#!/usr/bin/env python
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

""" Collect the performance data from multiple Nuitka versions. """

import subprocess, sys, os, tempfile, shutil, datetime, socket
import sqlite3, time

# Quick check that we actually in the correct spot.
assert os.path.exists( "debian" )

from optparse import OptionParser

from git import Repo

parser = OptionParser()

parser.add_option(
    "--run-benchmarks",
    action  = "store_true",
    dest    = "run_benchmarks",
    default = False,
    help    = """Run the benchmarks not previously run."""
)

parser.add_option(
    "--generate-graphs",
    action  = "store",
    dest    = "graphs_output_dir",
    default = None,
    help    = """Generate graphs for the benchmark data."""
)

parser.add_option(
    "--export-repo",
    action  = "store_true",
    dest    = "export_repo",
    default = False,
    help    = """Export the benchmark data as SQL text file."""
)

parser.add_option(
    "--import-repo",
    action  = "store_true",
    dest    = "import_repo",
    default = False,
    help    = """Import the benchmark data from SQL text file."""
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
# print "Using git dir", os.environ[ "GIT_DIR" ]

repo = Repo()

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
    commit = repo.rev_parse( commit_id )

    if hasattr( commit, "object" ):
        commit = commit.object

    return commit.committed_date


def getCommitHash( commit_id ):
    commit = repo.rev_parse( commit_id )

    if hasattr( commit, "object" ):
        commit = commit.object

    commit_hash = commit.hexsha

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

    def execute( self, nuitka_version ):
        if os.path.exists( os.path.join( "bin", "Nuitka.py" ) ):
            binary = "Nuitka.py"
        else:
            binary = "nuitka"

        binary = os.path.join( "bin", binary )

        # Used by run_valgrind.py
        os.environ[ "NUITKA_BINARY" ] = "python%s %s" % ( nuitka_version.getPythonVersion(), binary )

        # Very old Nuitka needs that.
        if os.path.exists( "scons" ):
            os.environ[ "NUITKA_SCONS" ] = "scons"

        # Very old Nuitka needs that.
        if os.path.exists( "include" ):
            os.environ[ "NUITKA_INCLUDE" ] = "include"

        os.environ[ "NUITKA_EXTRA_OPTIONS" ] = self.getExtraArguments( nuitka_version )
        # false alarm, pylint: disable=E1103

        output = subprocess.check_output(
            (
                os.path.join( start_dir, "misc", "run-valgrind.py" ),
                benchmark_path,
                "number"
            )
        ).strip()

        self.result[ "EXE_SIZE" ] = int( output.split( "\n" )[-2].split("=")[1] )
        self.result[ "CPU_TICKS" ] = int( output.split( "\n" )[-1].split("=")[1] )

    def getResults( self ):
        return dict( self.result )

    def getExtraArguments( self, nuitka_version ):
        nuitka_version = nuitka_version.getNuitkaVersion()

        if nuitka_version.startswith( "0.3" ) and nuitka_version < "0.3.17":
            return ""
        else:
            return "--remove-output"

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
    Configuration( "Kay - Mobile Dev", "Intel Core i5-2520M CPU@2.50GHz" )
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

def setNuitkaVersions():
    global nuitka_versions

    # false alarm, pylint: disable=E1103

    # These were too bad for one reason of the other.
    blacklist = ( "0.3.12c", "0.3.11", "0.3.11a", "0.3.11b", "0.3.11c" )

    # Collect the versions.
    nuitka_versions = [ tag.name for tag in repo.tags if tag.name not in blacklist ]
    nuitka_versions.append( "develop" )

    result = []

    for nuitka_version in nuitka_versions:
        for python_version in ( "2.6", "2.7", "3.2" ):
            result.append(
                NuitkaVersion( nuitka_version, python_version )
            )

    nuitka_versions = result

nuitka_versions = None
setNuitkaVersions()

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

    def exportToFile( self ):
        assert not self.connection and not self.cursor

        if not os.path.exists( self.db_filename ):
            return

        command = "sqlite3 '%s' .dump" % self.db_filename

        process = subprocess.Popen(
            args   = command,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            shell  = True
        )

        data, stderr = process.communicate()
        assert process.returncode == 0, stderr

        sql_filename = self.db_filename[:-2] + "sql"

        with open( sql_filename, "w" ) as out_file:
            out_file.write( data )

    def importFromFile( self ):
        assert not self.connection and not self.cursor

        if os.path.exists( self.db_filename ):
            return

        sql_filename = self.db_filename[:-2] + "sql"

        command = """sqlite3 '%s' ".read '%s'" """ % ( self.db_filename, sql_filename )
        os.system( command )


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
        stored = self._doSql(
            """SELECT * FROM results WHERE nuitka_version=? AND python_version=? AND benckmark_name=?""",

            nuitka_version,
            python_version,
            benchmark_name
        )

        result = []

        for res in stored:
            if res[ 1 ] == getCommitHash( nuitka_version ):
                result.append( res )
            else:
                self._doSql(
                    """DELETE FROM results where nuitka_version=? and commit_id=?""",
                    nuitka_version,
                    res[1]
                )

        return result

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

def getResultDatabase( machine ):
    if machine not in result_databases:
        result_databases[ machine ] = ResultDatabase( machine )

    return result_databases[ machine ]

class Execution:
    def __init__( self, machine, nuitka_version, benchmark ):
        self.machine = machine
        self.nuitka_version = nuitka_version
        self.benchmark = benchmark

        self.result_database = getResultDatabase( machine )

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

        nuitka_version = self.nuitka_version.getNuitkaVersion()

        print "Prepare playground with Nuitka version '%s'." % nuitka_version
        sys.stdout.flush()

        setupPlayground( nuitka_version )

        print "Execute benchmark '%s' with '%s'." % (
            self.benchmark.getName(),
            self.nuitka_version,
        )

        self.benchmark.execute(
            self.nuitka_version
        )

        result = self.benchmark.getResults()

        for key, value in result.iteritems():
            result_databases[ self.machine ].setData(
                nuitka_version,
                getCommitHash( nuitka_version ),
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



def defineTasks():
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

defineTasks()

# Remove the playground again from /tmp
shutil.rmtree( playground_dir, True )

if options.run_benchmarks:
    for task in tasks[ this_config ]:
        if not task.hasData():
            task.execute()

if options.export_repo:
    for machine in machines:
        ResultDatabase( machine ).exportToFile()

if options.import_repo:
    for machine in machines:
        ResultDatabase( machine ).importFromFile()


def createGraphs():
    graphs = {}

    dates_pystone_26 = []
    values_pystone_26 = []
    names_pystone_26 = []

    dates_pystone_27 = []
    values_pystone_27 = []
    names_pystone_27 = []

    def isInterestingVersion( name ):
        if name in ( "master", "develop", "0.3.13a" ):
            return True

        if name[-1].isalpha():
            return False

        if name.count( "." ) == 3:
            return False

        return True

    def considerResult( environment, executable, commit_id, benchmark, size, ticks ):
        commit_date = getCommitDate( commit_id )
        commit_date = datetime.datetime.fromtimestamp( commit_date )

        if benchmark == "pystone":
            assert type( ticks ) is int, repr( ticks )

            if not isInterestingVersion( commit_id ):
                return

            if executable == "nuitka-python2.7":
                dates_pystone_27.append( commit_date )
                values_pystone_27.append( ticks )
                names_pystone_27.append( commit_id )
            elif executable == "nuitka-python2.6":
                dates_pystone_26.append( commit_date )
                values_pystone_26.append( ticks )
                names_pystone_26.append( commit_id )
            else:
                assert False, executable

    for configuration, task_list in tasks.iteritems():
        for task in task_list:
            if not task.getData():
                continue

            considerResult(
                environment = task.getMachine().getName(),
                executable  = task.getExecutable(),
                commit_id   = task.getVersion().getNuitkaVersion(),
                benchmark   = task.getBenchmark().getName(),
                size        = int( task.getData()[ "EXE_SIZE" ] ),
                ticks       = int( task.getData()[ "CPU_TICKS" ] )
            )


    assert len( values_pystone_27 ) == len( values_pystone_26 )

    import matplotlib.pyplot as plt

    plt.title( "PyStone ticks after entering '__main__' (i.e. without initialisation)" )
    plt.ylabel( "ticks" )
    plt.xlabel( "version" )

    counts = [ i*3+1.2 for i in range( 0, len( values_pystone_27 ) ) ]

    p27 = plt.bar( counts, values_pystone_27, width = 1, color = "orange" )
    plt.xticks( counts, names_pystone_27 )

    plt.yticks( ( 900000000, 950000000, 1000000000, ), ( "900M", "950M", "1000M", ) )

    sizes = plt.gcf().get_size_inches()

    counts = [ i*3 for i in range( 0, len( values_pystone_26 ) ) ]

    p26 = plt.bar( counts, values_pystone_26, width = 1 )

    sizes = plt.gcf().get_size_inches()
    plt.gcf().set_size_inches( sizes[0]*1.5, sizes[1]*1.5 )

    plt.legend( ( p26[0], p27[0] ), ( "2.6", "2.7" ), bbox_to_anchor=(1.005, 1), loc=2, borderaxespad=0.0,  )

    plt.savefig( os.path.join( orig_dir, options.graphs_output_dir, "pystone-nuitka.svg" ) )


if options.graphs_output_dir is not None:
    createGraphs()
