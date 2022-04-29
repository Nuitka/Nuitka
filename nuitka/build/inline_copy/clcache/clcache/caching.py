""" Clcache module with core caching functionality. """

# This file is part of the clcache project.
#
# The contents of this file are subject to the BSD 3-Clause License, the
# full text of which is available in the accompanying LICENSE file at the
# root directory of this project.
#
from __future__ import print_function
from __future__ import absolute_import
import codecs
import concurrent.futures
import contextlib
import errno
import gzip
import hashlib
import json
import multiprocessing
import os
import pickle
import re
import subprocess
import sys
import threading
from collections import defaultdict, namedtuple
from copy import copy
from ctypes import windll, wintypes
from shutil import copyfile, copyfileobj, rmtree
from tempfile import TemporaryFile

from atomicwrites import atomic_write
from io import open

VERSION = "5.0.0-dev"

HashAlgorithm = hashlib.md5

OUTPUT_LOCK = threading.Lock()

# try to use os.scandir or scandir.scandir
# fall back to os.listdir if not found
# same for scandir.walk
try:
    import scandir

    WALK = scandir.walk
    LIST = scandir.scandir
except ImportError:
    WALK = os.walk
    try:
        LIST = os.scandir  # type: ignore # pylint: disable=I0021,no-name-in-module
    except AttributeError:
        LIST = os.listdir

# The codec that is used by clcache to store compiler STDOUR and STDERR in
# output.txt and stderr.txt.
# This codec is up to us and only used for clcache internal storage.
# For possible values see https://docs.python.org/2/library/codecs.html
CACHE_COMPILER_OUTPUT_STORAGE_CODEC = "utf-8"

# The cl default codec
CL_DEFAULT_CODEC = "mbcs"

# Manifest file will have at most this number of hash lists in it. Need to avoi
# manifests grow too large.
MAX_MANIFEST_HASHES = 100

# String, by which BASE_DIR will be replaced in paths, stored in manifests.
# ? is invalid character for file name, so it seems ok
# to use it as mark for relative path.
BASEDIR_REPLACEMENT = "?"

# Define some Win32 API constants here to avoid dependency on win32pipe
NMPWAIT_WAIT_FOREVER = wintypes.DWORD(0xFFFFFFFF)
ERROR_PIPE_BUSY = 231

# ManifestEntry: an entry in a manifest file
# `includeFiles`: list of paths to include files, which this source file uses
# `includesContentsHash`: hash of the contents of the includeFiles
# `objectHash`: hash of the object in cache
ManifestEntry = namedtuple(
    "ManifestEntry", ["includeFiles", "includesContentHash", "objectHash"]
)

CompilerArtifacts = namedtuple(
    "CompilerArtifacts", ["objectFilePath", "stdout", "stderr"]
)


def printBinary(stream, rawData):
    with OUTPUT_LOCK:
        stream.buffer.write(rawData)
        stream.flush()


def basenameWithoutExtension(path):
    basename = os.path.basename(path)
    return os.path.splitext(basename)[0]


def filesBeneath(baseDir):
    for path, _, filenames in WALK(baseDir):
        for filename in filenames:
            yield os.path.join(path, filename)


def childDirectories(path, absolute=True):
    supportsScandir = LIST != os.listdir  # pylint: disable=comparison-with-callable
    for entry in LIST(path):
        if supportsScandir:
            if entry.is_dir():
                yield entry.path if absolute else entry.name
        else:
            absPath = os.path.join(path, entry)
            if os.path.isdir(absPath):
                yield absPath if absolute else entry


def normalizeBaseDir(baseDir):
    if baseDir:
        baseDir = os.path.normcase(baseDir)
        if baseDir.endswith(os.path.sep):
            baseDir = baseDir[0:-1]
        return baseDir
    else:
        # Converts empty string to None
        return None


def getCachedCompilerConsoleOutput(path):
    try:
        with open(path, "rb") as f:
            return f.read().decode(CACHE_COMPILER_OUTPUT_STORAGE_CODEC)
    except IOError:
        return ""


def setCachedCompilerConsoleOutput(path, output):
    with open(path, "wb") as f:
        f.write(output.encode(CACHE_COMPILER_OUTPUT_STORAGE_CODEC))


class IncludeNotFoundException(Exception):
    pass


class CacheLockException(Exception):
    pass


class CompilerFailedException(Exception):
    def __init__(self, exitCode, msgErr, msgOut=""):
        Exception.__init__(self, msgErr)
        self.exitCode = exitCode
        self.msgOut = msgOut
        self.msgErr = msgErr

    def getReturnTuple(self):
        return self.exitCode, self.msgErr, self.msgOut, False


class Manifest(object):
    def __init__(self, entries=None):
        if entries is None:
            entries = []
        self._entries = copy(entries)

    def entries(self):
        return self._entries

    def addEntry(self, entry):
        """Adds entry at the top of the entries"""
        self._entries.insert(0, entry)

    def touchEntry(self, objectHash):
        """Moves entry in entryIndex position to the top of entries()"""
        entryIndex = next(
            (i for i, e in enumerate(self.entries()) if e.objectHash == objectHash), 0
        )
        self._entries.insert(0, self._entries.pop(entryIndex))


class ManifestSection(object):
    def __init__(self, manifestSectionDir):
        self.manifestSectionDir = manifestSectionDir
        self.lock = CacheLock.forPath(self.manifestSectionDir)

    def manifestPath(self, manifestHash):
        return os.path.join(self.manifestSectionDir, manifestHash + ".json")

    def manifestFiles(self):
        return filesBeneath(self.manifestSectionDir)

    def setManifest(self, manifestHash, manifest):
        manifestPath = self.manifestPath(manifestHash)
        printTraceStatement(
            "Writing manifest with manifestHash = {} to {}".format(
                manifestHash, manifestPath
            )
        )
        ensureDirectoryExists(self.manifestSectionDir)
        with atomic_write(manifestPath, overwrite=True) as outFile:
            # Converting namedtuple to JSON via OrderedDict preserves key names and keys order
            entries = [e._asdict() for e in manifest.entries()]
            jsonobject = {"entries": entries}
            json.dump(jsonobject, outFile, sort_keys=True, indent=2)

    def getManifest(self, manifestHash):
        fileName = self.manifestPath(manifestHash)
        if not os.path.exists(fileName):
            return None
        try:
            with open(fileName, "r") as inFile:
                doc = json.load(inFile)
                return Manifest(
                    [
                        ManifestEntry(
                            e["includeFiles"], e["includesContentHash"], e["objectHash"]
                        )
                        for e in doc["entries"]
                    ]
                )
        except IOError:
            return None
        except ValueError:
            printErrStr("clcache: manifest file %s was broken" % fileName)
            return None


@contextlib.contextmanager
def allSectionsLocked(repository):
    sections = list(repository.sections())
    for section in sections:
        section.lock.acquire()
    try:
        yield
    finally:
        for section in sections:
            section.lock.release()


class ManifestRepository(object):
    # Bump this counter whenever the current manifest file format changes.
    # E.g. changing the file format from {'oldkey': ...} to {'newkey': ...} requires
    # invalidation, such that a manifest that was stored using the old format is not
    # interpreted using the new format. Instead the old file will not be touched
    # again due to a new manifest hash and is cleaned away after some time.
    MANIFEST_FILE_FORMAT_VERSION = 6

    def __init__(self, manifestsRootDir):
        self._manifestsRootDir = manifestsRootDir

    def section(self, manifestHash):
        return ManifestSection(os.path.join(self._manifestsRootDir, manifestHash[:3]))

    def sections(self):
        return (
            ManifestSection(path) for path in childDirectories(self._manifestsRootDir)
        )

    def clean(self, maxManifestsSize):
        manifestFileInfos = []
        for section in self.sections():
            for filePath in section.manifestFiles():
                try:
                    manifestFileInfos.append((os.stat(filePath), filePath))
                except OSError:
                    pass

        manifestFileInfos.sort(key=lambda t: t[0].st_atime, reverse=True)

        remainingObjectsSize = 0
        for stat, filepath in manifestFileInfos:
            if remainingObjectsSize + stat.st_size <= maxManifestsSize:
                remainingObjectsSize += stat.st_size
            else:
                os.remove(filepath)
        return remainingObjectsSize

    @staticmethod
    def getManifestHash(compilerBinary, commandLine, sourceFile):
        compilerHash = getCompilerHash(compilerBinary)

        # NOTE: We intentionally do not normalize command line to include
        # preprocessor options.  In direct mode we do not perform preprocessing
        # before cache lookup, so all parameters are important.  One of the few
        # exceptions to this rule is the /MP switch, which only defines how many
        # compiler processes are running simultaneously.  Arguments that specify
        # the compiler where to find the source files are parsed to replace
        # occurrences of CLCACHE_BASEDIR by a placeholder.
        arguments, inputFiles = CommandLineAnalyzer.parseArgumentsAndInputFiles(
            commandLine
        )
        collapseBasedirInCmdPath = lambda path: collapseBasedirToPlaceholder(
            os.path.normcase(os.path.abspath(path))
        )

        commandLine = []
        argumentsWithPaths = ("AI", "I", "FU")
        for k in sorted(arguments.keys()):
            if k in argumentsWithPaths:
                commandLine.extend(
                    ["/" + k + collapseBasedirInCmdPath(arg) for arg in arguments[k]]
                )
            else:
                commandLine.extend(["/" + k + arg for arg in arguments[k]])

        commandLine.extend(collapseBasedirInCmdPath(arg) for arg in inputFiles)

        additionalData = "{}|{}|{}".format(
            compilerHash, commandLine, ManifestRepository.MANIFEST_FILE_FORMAT_VERSION
        )
        return getFileHash(sourceFile, additionalData)

    @staticmethod
    def getIncludesContentHashForFiles(includes):
        try:
            listOfHashes = getFileHashes(includes)
        except FileNotFoundError:
            raise IncludeNotFoundException
        return ManifestRepository.getIncludesContentHashForHashes(listOfHashes)

    @staticmethod
    def getIncludesContentHashForHashes(listOfHashes):
        return HashAlgorithm(",".join(listOfHashes).encode()).hexdigest()


# Lets be inefficient and have just one lock for all things, won't be a big deal
# if it's only used for stats.
from threading import RLock
cache_lock = RLock()

class CacheLock2(object):
    """Implement a lock inside the process only. """

    def __init__(self):
        self._rlock = None

    def __enter__(self):
        cache_lock.acquire()

    def __exit__(self, typ, value, traceback):
        cache_lock.release()

    @staticmethod
    def forPath(path):
        return CacheLock2()

class CacheLock(object):
    """Implements a lock for the object cache which
    can be used in 'with' statements."""

    INFINITE = 0xFFFFFFFF
    WAIT_ABANDONED_CODE = 0x00000080
    WAIT_TIMEOUT_CODE = 0x00000102

    def __init__(self, mutexName, timeoutMs):
        self._mutexName = u"Local\\" + mutexName
        self._mutex = None
        self._timeoutMs = timeoutMs

    def createMutex(self):
        with CacheLock2():
            self._mutex = windll.kernel32.CreateMutexW(
                None, wintypes.BOOL(False), self._mutexName
            )
            assert self._mutex

    def __enter__(self):
        self.acquire()

    def __exit__(self, typ, value, traceback):
        self.release()

    def __del__(self):
        if self._mutex:
            windll.kernel32.CloseHandle(self._mutex)

    def acquire(self):
        if not self._mutex:
            self.createMutex()
        result = windll.kernel32.WaitForSingleObject(
            self._mutex, wintypes.INT(self._timeoutMs)
        )
        if result not in [0, self.WAIT_ABANDONED_CODE]:
            if result == self.WAIT_TIMEOUT_CODE:
                errorString = (
                    "Failed to acquire lock {} after {}ms; "
                    "try setting CLCACHE_OBJECT_CACHE_TIMEOUT_MS environment variable to a larger value.".format(
                        self._mutexName, self._timeoutMs
                    )
                )
            else:
                errorString = "Error! WaitForSingleObject returns {result}, last error {error}".format(
                    result=result, error=windll.kernel32.GetLastError()
                )
            raise CacheLockException(errorString)

    def release(self):
        windll.kernel32.ReleaseMutex(self._mutex)

    @staticmethod
    def forPath(path):
        timeoutMs = int(os.environ.get("CLCACHE_OBJECT_CACHE_TIMEOUT_MS", 10 * 1000))
        lockName = path.replace(":", "-").replace("\\", "-")
        return CacheLock(lockName, timeoutMs)


class CompilerArtifactsSection(object):
    OBJECT_FILE = "object"
    STDOUT_FILE = "output.txt"
    STDERR_FILE = "stderr.txt"

    def __init__(self, compilerArtifactsSectionDir):
        self.compilerArtifactsSectionDir = compilerArtifactsSectionDir
        self.lock = CacheLock.forPath(self.compilerArtifactsSectionDir)

    def cacheEntryDir(self, key):
        return os.path.join(self.compilerArtifactsSectionDir, key)

    def cacheEntries(self):
        return childDirectories(self.compilerArtifactsSectionDir, absolute=False)

    def cachedObjectName(self, key):
        return os.path.join(
            self.cacheEntryDir(key), CompilerArtifactsSection.OBJECT_FILE
        )

    def hasEntry(self, key):
        return os.path.exists(self.cacheEntryDir(key))

    def setEntry(self, key, artifacts):
        cacheEntryDir = self.cacheEntryDir(key)
        # Write new files to a temporary directory
        tempEntryDir = cacheEntryDir + ".new"
        # Remove any possible left-over in tempEntryDir from previous executions
        rmtree(tempEntryDir, ignore_errors=True)
        ensureDirectoryExists(tempEntryDir)
        if artifacts.objectFilePath is not None:
            dstFilePath = os.path.join(
                tempEntryDir, CompilerArtifactsSection.OBJECT_FILE
            )
            copyOrLink(artifacts.objectFilePath, dstFilePath, True)
            size = os.path.getsize(dstFilePath)
        setCachedCompilerConsoleOutput(
            os.path.join(tempEntryDir, CompilerArtifactsSection.STDOUT_FILE),
            artifacts.stdout,
        )
        if artifacts.stderr != "":
            setCachedCompilerConsoleOutput(
                os.path.join(tempEntryDir, CompilerArtifactsSection.STDERR_FILE),
                artifacts.stderr,
            )
        # Replace the full cache entry atomically
        os.replace(tempEntryDir, cacheEntryDir)
        return size

    def getEntry(self, key):
        assert self.hasEntry(key)
        cacheEntryDir = self.cacheEntryDir(key)
        return CompilerArtifacts(
            os.path.join(cacheEntryDir, CompilerArtifactsSection.OBJECT_FILE),
            getCachedCompilerConsoleOutput(
                os.path.join(cacheEntryDir, CompilerArtifactsSection.STDOUT_FILE)
            ),
            getCachedCompilerConsoleOutput(
                os.path.join(cacheEntryDir, CompilerArtifactsSection.STDERR_FILE)
            ),
        )


class CompilerArtifactsRepository(object):
    def __init__(self, compilerArtifactsRootDir):
        self._compilerArtifactsRootDir = compilerArtifactsRootDir

    def section(self, key):
        return CompilerArtifactsSection(
            os.path.join(self._compilerArtifactsRootDir, key[:3])
        )

    def sections(self):
        return (
            CompilerArtifactsSection(path)
            for path in childDirectories(self._compilerArtifactsRootDir)
        )

    def removeEntry(self, keyToBeRemoved):
        compilerArtifactsDir = self.section(keyToBeRemoved).cacheEntryDir(
            keyToBeRemoved
        )
        rmtree(compilerArtifactsDir, ignore_errors=True)

    def clean(self, maxCompilerArtifactsSize):
        objectInfos = []
        for section in self.sections():
            for cachekey in section.cacheEntries():
                try:
                    objectStat = os.stat(section.cachedObjectName(cachekey))
                    objectInfos.append((objectStat, cachekey))
                except OSError:
                    pass

        objectInfos.sort(key=lambda t: t[0].st_atime)

        # compute real current size to fix up the stored cacheSize
        currentSizeObjects = sum(x[0].st_size for x in objectInfos)

        removedItems = 0
        for stat, cachekey in objectInfos:
            self.removeEntry(cachekey)
            removedItems += 1
            currentSizeObjects -= stat.st_size
            if currentSizeObjects < maxCompilerArtifactsSize:
                break

        return len(objectInfos) - removedItems, currentSizeObjects

    @staticmethod
    def computeKeyDirect(manifestHash, includesContentHash):
        # We must take into account manifestHash to avoid
        # collisions when different source files use the same
        # set of includes.
        return getStringHash(manifestHash + includesContentHash)

    @staticmethod
    def computeKeyNodirect(compilerBinary, commandLine, environment):
        ppcmd = ["/EP"] + [arg for arg in commandLine if arg not in ("-c", "/c")]

        returnCode, preprocessedSourceCode, ppStderrBinary = invokeRealCompiler(
            compilerBinary,
            ppcmd,
            captureOutput=True,
            outputAsString=False,
            environment=environment,
        )

        if returnCode != 0:
            errMsg = (
                ppStderrBinary.decode(CL_DEFAULT_CODEC)
                + "\nclcache: preprocessor failed"
            )
            raise CompilerFailedException(returnCode, errMsg)

        compilerHash = getCompilerHash(compilerBinary)
        normalizedCmdLine = CompilerArtifactsRepository._normalizedCommandLine(
            commandLine
        )

        h = HashAlgorithm()
        h.update(compilerHash.encode("UTF-8"))
        h.update(" ".join(normalizedCmdLine).encode("UTF-8"))
        h.update(preprocessedSourceCode)
        return h.hexdigest()

    @staticmethod
    def _normalizedCommandLine(cmdline):
        # Remove all arguments from the command line which only influence the
        # preprocessor; the preprocessor's output is already included into the
        # hash sum so we don't have to care about these switches in the
        # command line as well.
        argsToStrip = (
            "AI",
            "C",
            "E",
            "P",
            "FI",
            "u",
            "X",
            "FU",
            "D",
            "EP",
            "Fx",
            "U",
            "I",
        )

        # Also remove the switch for specifying the output file name; we don't
        # want two invocations which are identical except for the output file
        # name to be treated differently.
        argsToStrip += ("Fo",)

        # Also strip the switch for specifying the number of parallel compiler
        # processes to use (when specifying multiple source files on the
        # command line).
        argsToStrip += ("MP",)

        return [
            arg
            for arg in cmdline
            if not (arg[0] in "/-" and arg[1:].startswith(argsToStrip))
        ]


class CacheFileStrategy(object):
    def __init__(self, cacheDirectory=None):
        self.dir = cacheDirectory
        if not self.dir:
            try:
                self.dir = os.environ["CLCACHE_DIR"]
            except KeyError:
                self.dir = os.path.join(os.path.expanduser("~"), "clcache")

        manifestsRootDir = os.path.join(self.dir, "manifests")
        ensureDirectoryExists(manifestsRootDir)
        self.manifestRepository = ManifestRepository(manifestsRootDir)

        compilerArtifactsRootDir = os.path.join(self.dir, "objects")
        ensureDirectoryExists(compilerArtifactsRootDir)
        self.compilerArtifactsRepository = CompilerArtifactsRepository(
            compilerArtifactsRootDir
        )

        self.configuration = Configuration(os.path.join(self.dir, "config.txt"))

        stats_filename = os.environ.get(
            "CLCACHE_STATS", os.path.join(self.dir, "stats.txt")
        )
        self.statistics = Statistics(stats_filename)

    def __str__(self):
        return "Disk cache at {}".format(self.dir)

    @property  # type: ignore
    @contextlib.contextmanager
    def lock(self):
        with allSectionsLocked(self.manifestRepository), allSectionsLocked(
            self.compilerArtifactsRepository
        ):
            yield

    def lockFor(self, key):
        assert isinstance(self.compilerArtifactsRepository.section(key).lock, CacheLock)
        return self.compilerArtifactsRepository.section(key).lock

    def manifestLockFor(self, key):
        return self.manifestRepository.section(key).lock

    def getEntry(self, key):
        return self.compilerArtifactsRepository.section(key).getEntry(key)

    def setEntry(self, key, value):
        return self.compilerArtifactsRepository.section(key).setEntry(key, value)

    def pathForObject(self, key):
        return self.compilerArtifactsRepository.section(key).cachedObjectName(key)

    def directoryForCache(self, key):
        return self.compilerArtifactsRepository.section(key).cacheEntryDir(key)

    def deserializeCacheEntry(self, key, objectData):
        path = self.pathForObject(key)
        ensureDirectoryExists(self.directoryForCache(key))
        with open(path, "wb") as f:
            f.write(objectData)
        return path

    def hasEntry(self, cachekey):
        return self.compilerArtifactsRepository.section(cachekey).hasEntry(cachekey)

    def setManifest(self, manifestHash, manifest):
        self.manifestRepository.section(manifestHash).setManifest(
            manifestHash, manifest
        )

    def getManifest(self, manifestHash):
        return self.manifestRepository.section(manifestHash).getManifest(manifestHash)

    def clean(self, stats, maximumSize):
        currentSize = stats.currentCacheSize()
        if currentSize < maximumSize:
            return

        # Free at least 10% to avoid cleaning up too often which
        # is a big performance hit with large caches.
        effectiveMaximumSizeOverall = maximumSize * 0.9

        # Split limit in manifests (10 %) and objects (90 %)
        effectiveMaximumSizeManifests = effectiveMaximumSizeOverall * 0.1
        effectiveMaximumSizeObjects = (
            effectiveMaximumSizeOverall - effectiveMaximumSizeManifests
        )

        # Clean manifests
        currentSizeManifests = self.manifestRepository.clean(
            effectiveMaximumSizeManifests
        )

        # Clean artifacts
        (
            currentCompilerArtifactsCount,
            currentCompilerArtifactsSize,
        ) = self.compilerArtifactsRepository.clean(effectiveMaximumSizeObjects)

        stats.setCacheSize(currentCompilerArtifactsSize + currentSizeManifests)
        stats.setNumCacheEntries(currentCompilerArtifactsCount)


class Cache(object):
    def __init__(self, cacheDirectory=None):
        if os.environ.get("CLCACHE_MEMCACHED"):
            from .storage import CacheFileWithMemcacheFallbackStrategy

            self.strategy = CacheFileWithMemcacheFallbackStrategy(
                os.environ.get("CLCACHE_MEMCACHED"), cacheDirectory=cacheDirectory
            )
        else:
            self.strategy = CacheFileStrategy(cacheDirectory=cacheDirectory)

    def __str__(self):
        return str(self.strategy)

    @property
    def lock(self):
        return self.strategy.lock

    @contextlib.contextmanager
    def manifestLockFor(self, key):
        with self.strategy.manifestLockFor(key):
            yield

    @property
    def configuration(self):
        return self.strategy.configuration

    @property
    def statistics(self):
        return self.strategy.statistics

    def clean(self, stats, maximumSize):
        return self.strategy.clean(stats, maximumSize)

    @contextlib.contextmanager
    def lockFor(self, key):
        with self.strategy.lockFor(key):
            yield

    def getEntry(self, key):
        return self.strategy.getEntry(key)

    def setEntry(self, key, value):
        return self.strategy.setEntry(key, value)

    def hasEntry(self, cachekey):
        return self.strategy.hasEntry(cachekey)

    def setManifest(self, manifestHash, manifest):
        self.strategy.setManifest(manifestHash, manifest)

    def getManifest(self, manifestHash):
        return self.strategy.getManifest(manifestHash)


class PersistentJSONDict(object):
    def __init__(self, fileName):
        self._dirty = False
        self._dict = {}
        self._fileName = fileName
        try:
            with open(self._fileName, "r") as f:
                self._dict = json.load(f)
        except IOError:
            pass
        except ValueError:
            printErrStr("clcache: persistent json file %s was broken" % fileName)

    def save(self):
        if self._dirty:
            with atomic_write(self._fileName, overwrite=True) as f:
                json.dump(self._dict, f, sort_keys=True, indent=4)

    def __setitem__(self, key, value):
        self._dict[key] = value
        self._dirty = True

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def __eq__(self, other):
        return type(self) is type(other) and self.__dict__ == other.__dict__


class Configuration(object):
    _defaultValues = {"MaximumCacheSize": 1073741824}  # 1 GiB

    def __init__(self, configurationFile):
        self._configurationFile = configurationFile
        self._cfg = None

    def __enter__(self):
        self._cfg = PersistentJSONDict(self._configurationFile)
        for setting, defaultValue in self._defaultValues.items():
            if setting not in self._cfg:
                self._cfg[setting] = defaultValue
        return self

    def __exit__(self, typ, value, traceback):
        # Does not write to disc when unchanged
        self._cfg.save()

    def maximumCacheSize(self):
        return self._cfg["MaximumCacheSize"]

    def setMaximumCacheSize(self, size):
        self._cfg["MaximumCacheSize"] = size

stats = None

class Statistics(object):
    CALLS_WITH_INVALID_ARGUMENT = "CallsWithInvalidArgument"
    CALLS_WITHOUT_SOURCE_FILE = "CallsWithoutSourceFile"
    CALLS_WITH_MULTIPLE_SOURCE_FILES = "CallsWithMultipleSourceFiles"
    CALLS_WITH_PCH = "CallsWithPch"
    CALLS_FOR_LINKING = "CallsForLinking"
    CALLS_FOR_EXTERNAL_DEBUG_INFO = "CallsForExternalDebugInfo"
    CALLS_FOR_PREPROCESSING = "CallsForPreprocessing"
    CACHE_HITS = "CacheHits"
    CACHE_MISSES = "CacheMisses"
    EVICTED_MISSES = "EvictedMisses"
    HEADER_CHANGED_MISSES = "HeaderChangedMisses"
    SOURCE_CHANGED_MISSES = "SourceChangedMisses"
    CACHE_ENTRIES = "CacheEntries"
    CACHE_SIZE = "CacheSize"

    RESETTABLE_KEYS = {
        CALLS_WITH_INVALID_ARGUMENT,
        CALLS_WITHOUT_SOURCE_FILE,
        CALLS_WITH_MULTIPLE_SOURCE_FILES,
        CALLS_WITH_PCH,
        CALLS_FOR_LINKING,
        CALLS_FOR_EXTERNAL_DEBUG_INFO,
        CALLS_FOR_PREPROCESSING,
        CACHE_HITS,
        CACHE_MISSES,
        EVICTED_MISSES,
        HEADER_CHANGED_MISSES,
        SOURCE_CHANGED_MISSES,
    }
    NON_RESETTABLE_KEYS = {
        CACHE_ENTRIES,
        CACHE_SIZE,
    }

    def __init__(self, statsFile):
        self._statsFile = statsFile

        global stats
        if stats is None:
            stats = PersistentJSONDict(self._statsFile)

        self._stats = stats

    def __enter__(self):
        for k in Statistics.RESETTABLE_KEYS | Statistics.NON_RESETTABLE_KEYS:
            if k not in self._stats:
                self._stats[k] = 0
        return self

    def __exit__(self, typ, value, traceback):
        # Does not write to disc when unchanged
        # Nuitka: Only write at the end.
        # self._stats.save()
        pass

    def __eq__(self, other):
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def numCallsWithInvalidArgument(self):
        return self._stats[Statistics.CALLS_WITH_INVALID_ARGUMENT]

    def registerCallWithInvalidArgument(self):
        self._stats[Statistics.CALLS_WITH_INVALID_ARGUMENT] += 1

    def numCallsWithoutSourceFile(self):
        return self._stats[Statistics.CALLS_WITHOUT_SOURCE_FILE]

    def registerCallWithoutSourceFile(self):
        self._stats[Statistics.CALLS_WITHOUT_SOURCE_FILE] += 1

    def numCallsWithMultipleSourceFiles(self):
        return self._stats[Statistics.CALLS_WITH_MULTIPLE_SOURCE_FILES]

    def registerCallWithMultipleSourceFiles(self):
        self._stats[Statistics.CALLS_WITH_MULTIPLE_SOURCE_FILES] += 1

    def numCallsWithPch(self):
        return self._stats[Statistics.CALLS_WITH_PCH]

    def registerCallWithPch(self):
        self._stats[Statistics.CALLS_WITH_PCH] += 1

    def numCallsForLinking(self):
        return self._stats[Statistics.CALLS_FOR_LINKING]

    def registerCallForLinking(self):
        self._stats[Statistics.CALLS_FOR_LINKING] += 1

    def numCallsForExternalDebugInfo(self):
        return self._stats[Statistics.CALLS_FOR_EXTERNAL_DEBUG_INFO]

    def registerCallForExternalDebugInfo(self):
        self._stats[Statistics.CALLS_FOR_EXTERNAL_DEBUG_INFO] += 1

    def numEvictedMisses(self):
        return self._stats[Statistics.EVICTED_MISSES]

    def registerEvictedMiss(self):
        self.registerCacheMiss()
        self._stats[Statistics.EVICTED_MISSES] += 1

    def numHeaderChangedMisses(self):
        return self._stats[Statistics.HEADER_CHANGED_MISSES]

    def registerHeaderChangedMiss(self):
        self.registerCacheMiss()
        self._stats[Statistics.HEADER_CHANGED_MISSES] += 1

    def numSourceChangedMisses(self):
        return self._stats[Statistics.SOURCE_CHANGED_MISSES]

    def registerSourceChangedMiss(self):
        self.registerCacheMiss()
        self._stats[Statistics.SOURCE_CHANGED_MISSES] += 1

    def numCacheEntries(self):
        return self._stats[Statistics.CACHE_ENTRIES]

    def setNumCacheEntries(self, number):
        self._stats[Statistics.CACHE_ENTRIES] = number

    def registerCacheEntry(self, size):
        self._stats[Statistics.CACHE_ENTRIES] += 1
        self._stats[Statistics.CACHE_SIZE] += size

    def unregisterCacheEntry(self, size):
        self._stats[Statistics.CACHE_ENTRIES] -= 1
        self._stats[Statistics.CACHE_SIZE] -= size

    def currentCacheSize(self):
        return self._stats[Statistics.CACHE_SIZE]

    def setCacheSize(self, size):
        self._stats[Statistics.CACHE_SIZE] = size

    def numCacheHits(self):
        return self._stats[Statistics.CACHE_HITS]

    def registerCacheHit(self):
        self._stats[Statistics.CACHE_HITS] += 1

    def numCacheMisses(self):
        return self._stats[Statistics.CACHE_MISSES]

    def registerCacheMiss(self):
        self._stats[Statistics.CACHE_MISSES] += 1

    def numCallsForPreprocessing(self):
        return self._stats[Statistics.CALLS_FOR_PREPROCESSING]

    def registerCallForPreprocessing(self):
        self._stats[Statistics.CALLS_FOR_PREPROCESSING] += 1

    def resetCounters(self):
        for k in Statistics.RESETTABLE_KEYS:
            self._stats[k] = 0


class AnalysisError(Exception):
    pass


class NoSourceFileError(AnalysisError):
    pass


class MultipleSourceFilesComplexError(AnalysisError):
    pass


class CalledForLinkError(AnalysisError):
    pass


class CalledWithPchError(AnalysisError):
    pass


class ExternalDebugInfoError(AnalysisError):
    pass


class CalledForPreprocessingError(AnalysisError):
    pass


class InvalidArgumentError(AnalysisError):
    pass


def getCompilerHash(compilerBinary):
    stat = os.stat(compilerBinary)
    data = "|".join(
        [
            str(stat.st_mtime),
            str(stat.st_size),
            VERSION,
        ]
    )
    hasher = HashAlgorithm()
    hasher.update(data.encode("UTF-8"))
    return hasher.hexdigest()


def getFileHashes(filePaths):
    if "CLCACHE_SERVER" in os.environ:
        pipeName = r"\\.\pipe\clcache_srv"
        while True:
            try:
                with open(pipeName, "w+b") as f:
                    f.write("\n".join(filePaths).encode("utf8"))
                    f.write(b"\x00")
                    response = f.read()
                    if response.startswith(b"!"):
                        raise pickle.loads(response[1:-1])
                    return response[:-1].decode("utf8").splitlines()
            except OSError as e:
                if (
                    e.errno == errno.EINVAL
                    and windll.kernel32.GetLastError() == ERROR_PIPE_BUSY
                ):
                    windll.kernel32.WaitNamedPipeW(pipeName, NMPWAIT_WAIT_FOREVER)
                else:
                    raise
    else:
        return [getFileHash(filePath) for filePath in filePaths]


_hash_cache = {}

def getFileHash(filePath, additionalData=None):
    key = (filePath, additionalData)

    if key in _hash_cache:
        return _hash_cache[key]

    hasher = HashAlgorithm()
    with open(filePath, "rb") as inFile:
        hasher.update(inFile.read())
    if additionalData is not None:
        # Encoding of this additional data does not really matter
        # as long as we keep it fixed, otherwise hashes change.
        # The string should fit into ASCII, so UTF8 should not change anything
        hasher.update(additionalData.encode("UTF-8"))

    _hash_cache[key] = hasher.hexdigest()
    return _hash_cache[key]


def getStringHash(dataString):
    hasher = HashAlgorithm()
    hasher.update(dataString.encode("UTF-8"))
    return hasher.hexdigest()


def expandBasedirPlaceholder(path):
    baseDir = normalizeBaseDir(os.environ.get("CLCACHE_BASEDIR"))
    if path.startswith(BASEDIR_REPLACEMENT):
        if not baseDir:
            print(
                "No CLCACHE_BASEDIR set, but found relative path " + path,
                file=sys.stderr,
            )
            sys.exit(1)
        return path.replace(BASEDIR_REPLACEMENT, baseDir, 1)
    else:
        return path


def collapseBasedirToPlaceholder(path):
    baseDir = normalizeBaseDir(os.environ.get("CLCACHE_BASEDIR"))
    if baseDir is None:
        return path
    else:
        assert path == os.path.normcase(path)
        assert baseDir == os.path.normcase(baseDir)
        if path.startswith(baseDir):
            return path.replace(baseDir, BASEDIR_REPLACEMENT, 1)
        else:
            return path


def ensureDirectoryExists(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def copyOrLink(srcFilePath, dstFilePath, writeCache=False):
    ensureDirectoryExists(os.path.dirname(os.path.abspath(dstFilePath)))

    if "CLCACHE_HARDLINK" in os.environ:
        ret = windll.kernel32.CreateHardLinkW(str(dstFilePath), str(srcFilePath), None)
        if ret != 0:
            # Touch the time stamp of the new link so that the build system
            # doesn't confused by a potentially old time on the file. The
            # hard link gets the same timestamp as the cached file.
            # Note that touching the time stamp of the link also touches
            # the time stamp on the cache (and hence on all over hard
            # links). This shouldn't be a problem though.
            os.utime(dstFilePath, None)
            return

    # If hardlinking fails for some reason (or it's not enabled), just
    # fall back to moving bytes around. Always to a temporary path first to
    # lower the chances of corrupting it.
    tempDst = dstFilePath + ".tmp"

    if "CLCACHE_COMPRESS" in os.environ:
        if "CLCACHE_COMPRESSLEVEL" in os.environ:
            compress = int(os.environ["CLCACHE_COMPRESSLEVEL"])
        else:
            compress = 6

        if writeCache is True:
            with open(srcFilePath, "rb") as fileIn, gzip.open(
                tempDst, "wb", compress
            ) as fileOut:
                copyfileobj(fileIn, fileOut)
        else:
            with gzip.open(srcFilePath, "rb", compress) as fileIn, open(
                tempDst, "wb"
            ) as fileOut:
                copyfileobj(fileIn, fileOut)
    else:
        copyfile(srcFilePath, tempDst)
    os.replace(tempDst, dstFilePath)


def printTraceStatement(msg):
    if "CLCACHE_LOG" in os.environ:
        scriptDir = os.path.realpath(os.path.dirname(sys.argv[0]))
        with OUTPUT_LOCK:
            print(os.path.join(scriptDir, "clcache.py") + " " + msg)


class CommandLineTokenizer(object):
    def __init__(self, content):
        self.argv = []
        self._content = content
        self._pos = 0
        self._token = ""
        self._parser = self._initialState

        while self._pos < len(self._content):
            self._parser = self._parser(self._content[self._pos])
            self._pos += 1

        if self._token:
            self.argv.append(self._token)

    def _initialState(self, currentChar):
        if currentChar.isspace():
            return self._initialState

        if currentChar == '"':
            return self._quotedState

        if currentChar == "\\":
            self._parseBackslash()
            return self._unquotedState

        self._token += currentChar
        return self._unquotedState

    def _unquotedState(self, currentChar):
        if currentChar.isspace():
            self.argv.append(self._token)
            self._token = ""
            return self._initialState

        if currentChar == '"':
            return self._quotedState

        if currentChar == "\\":
            self._parseBackslash()
            return self._unquotedState

        self._token += currentChar
        return self._unquotedState

    def _quotedState(self, currentChar):
        if currentChar == '"':
            return self._unquotedState

        if currentChar == "\\":
            self._parseBackslash()
            return self._quotedState

        self._token += currentChar
        return self._quotedState

    def _parseBackslash(self):
        numBackslashes = 0
        while self._pos < len(self._content) and self._content[self._pos] == "\\":
            self._pos += 1
            numBackslashes += 1

        followedByDoubleQuote = (
            self._pos < len(self._content) and self._content[self._pos] == '"'
        )
        if followedByDoubleQuote:
            self._token += "\\" * (numBackslashes // 2)
            if numBackslashes % 2 == 0:
                self._pos -= 1
            else:
                self._token += '"'
        else:
            self._token += "\\" * numBackslashes
            self._pos -= 1


def splitCommandsFile(content):
    return CommandLineTokenizer(content).argv


def expandCommandLine(cmdline):
    ret = []

    for arg in cmdline:
        if arg[0] == "@":
            includeFile = arg[1:]
            with open(includeFile, "rb") as f:
                rawBytes = f.read()

            encoding = None

            bomToEncoding = {
                codecs.BOM_UTF32_BE: "utf-32-be",
                codecs.BOM_UTF32_LE: "utf-32-le",
                codecs.BOM_UTF16_BE: "utf-16-be",
                codecs.BOM_UTF16_LE: "utf-16-le",
            }

            for bom, enc in bomToEncoding.items():
                if rawBytes.startswith(bom):
                    encoding = enc
                    rawBytes = rawBytes[len(bom) :]
                    break

            if encoding:
                includeFileContents = rawBytes.decode(encoding)
            else:
                includeFileContents = rawBytes.decode("UTF-8")

            ret.extend(
                expandCommandLine(splitCommandsFile(includeFileContents.strip()))
            )
        else:
            ret.append(arg)

    return ret


def extendCommandLineFromEnvironment(cmdLine, environment):
    remainingEnvironment = environment.copy()

    prependCmdLineString = remainingEnvironment.pop("CL", None)
    if prependCmdLineString is not None:
        cmdLine = splitCommandsFile(prependCmdLineString.strip()) + cmdLine

    appendCmdLineString = remainingEnvironment.pop("_CL_", None)
    if appendCmdLineString is not None:
        cmdLine = cmdLine + splitCommandsFile(appendCmdLineString.strip())

    return cmdLine, remainingEnvironment


class Argument(object):
    def __init__(self, name):
        self.name = name

    def __len__(self):
        return len(self.name)

    def __str__(self):
        return "/" + self.name

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __hash__(self):
        key = (type(self), self.name)
        return hash(key)


# /NAMEparameter (no space, required parameter).
class ArgumentT1(Argument):
    pass


# /NAME[parameter] (no space, optional parameter)
class ArgumentT2(Argument):
    pass


# /NAME[ ]parameter (optional space)
class ArgumentT3(Argument):
    pass


# /NAME parameter (required space)
class ArgumentT4(Argument):
    pass


class CommandLineAnalyzer(object):
    argumentsWithParameter = {
        # /NAMEparameter
        ArgumentT1("Ob"),
        ArgumentT1("Yl"),
        ArgumentT1("Zm"),
        # /NAME[parameter]
        ArgumentT2("doc"),
        ArgumentT2("FA"),
        ArgumentT2("FR"),
        ArgumentT2("Fr"),
        ArgumentT2("Gs"),
        ArgumentT2("MP"),
        ArgumentT2("Yc"),
        ArgumentT2("Yu"),
        ArgumentT2("Zp"),
        ArgumentT2("Fa"),
        ArgumentT2("Fd"),
        ArgumentT2("Fe"),
        ArgumentT2("Fi"),
        ArgumentT2("Fm"),
        ArgumentT2("Fo"),
        ArgumentT2("Fp"),
        ArgumentT2("Wv"),
        # /NAME[ ]parameter
        ArgumentT3("AI"),
        ArgumentT3("D"),
        ArgumentT3("Tc"),
        ArgumentT3("Tp"),
        ArgumentT3("FI"),
        ArgumentT3("U"),
        ArgumentT3("I"),
        ArgumentT3("F"),
        ArgumentT3("FU"),
        ArgumentT3("w1"),
        ArgumentT3("w2"),
        ArgumentT3("w3"),
        ArgumentT3("w4"),
        ArgumentT3("wd"),
        ArgumentT3("we"),
        ArgumentT3("wo"),
        ArgumentT3("V"),
        ArgumentT3("imsvc"),
        # /NAME parameter
        ArgumentT4("Xclang"),
    }
    argumentsWithParameterSorted = sorted(argumentsWithParameter, key=len, reverse=True)

    @staticmethod
    def _getParameterizedArgumentType(cmdLineArgument):
        # Sort by length to handle prefixes
        for arg in CommandLineAnalyzer.argumentsWithParameterSorted:
            if cmdLineArgument.startswith(arg.name, 1):
                return arg
        return None

    @staticmethod
    def parseArgumentsAndInputFiles(cmdline):
        arguments = defaultdict(list)
        inputFiles = []
        i = 0
        while i < len(cmdline):
            cmdLineArgument = cmdline[i]

            # Plain arguments starting with / or -
            if cmdLineArgument.startswith("/") or cmdLineArgument.startswith("-"):
                arg = CommandLineAnalyzer._getParameterizedArgumentType(cmdLineArgument)
                if arg is not None:
                    if isinstance(arg, ArgumentT1):
                        value = cmdLineArgument[len(arg) + 1 :]
                        if not value:
                            raise InvalidArgumentError(
                                "Parameter for {} must not be empty".format(arg)
                            )
                    elif isinstance(arg, ArgumentT2):
                        value = cmdLineArgument[len(arg) + 1 :]
                    elif isinstance(arg, ArgumentT3):
                        value = cmdLineArgument[len(arg) + 1 :]
                        if not value:
                            value = cmdline[i + 1]
                            i += 1
                    elif isinstance(arg, ArgumentT4):
                        value = cmdline[i + 1]
                        i += 1
                    else:
                        raise AssertionError("Unsupported argument type.")

                    arguments[arg.name].append(value)
                else:
                    argumentName = cmdLineArgument[
                        1:
                    ]  # name not followed by parameter in this case
                    arguments[argumentName].append("")

            # Response file
            elif cmdLineArgument[0] == "@":
                raise AssertionError(
                    "No response file arguments (starting with @) must be left here."
                )

            # Source file arguments
            else:
                inputFiles.append(cmdLineArgument)

            i += 1

        return dict(arguments), inputFiles

    @staticmethod
    def analyze(cmdline):
        options, inputFiles = CommandLineAnalyzer.parseArgumentsAndInputFiles(cmdline)
        # Use an override pattern to shadow input files that have
        # already been specified in the function above
        inputFiles = {inputFile: "" for inputFile in inputFiles}
        compl = False
        if "Tp" in options:
            inputFiles.update({inputFile: "/Tp" for inputFile in options["Tp"]})
            compl = True
        if "Tc" in options:
            inputFiles.update({inputFile: "/Tc" for inputFile in options["Tc"]})
            compl = True

        # Now collect the inputFiles into the return format
        inputFiles = list(inputFiles.items())
        if not inputFiles:
            raise NoSourceFileError()

        for opt in ["E", "EP", "P"]:
            if opt in options:
                raise CalledForPreprocessingError()

        # Technically, it would be possible to support /Zi: we'd just need to
        # copy the generated .pdb files into/out of the cache.
        if "Zi" in options:
            raise ExternalDebugInfoError()

        if "Yc" in options or "Yu" in options:
            raise CalledWithPchError()

        if "link" in options or "c" not in options:
            raise CalledForLinkError()

        if len(inputFiles) > 1 and compl:
            raise MultipleSourceFilesComplexError()

        objectFiles = None
        prefix = ""
        if "Fo" in options and options["Fo"][0]:
            # Handle user input
            tmp = os.path.normpath(options["Fo"][0])
            if os.path.isdir(tmp):
                prefix = tmp
            elif len(inputFiles) == 1:
                objectFiles = [tmp]
        if objectFiles is None:
            # Generate from .c/.cpp filenames
            objectFiles = [
                os.path.join(prefix, basenameWithoutExtension(f)) + ".obj"
                for f, _ in inputFiles
            ]

        printTraceStatement("Compiler source files: {}".format(inputFiles))
        printTraceStatement("Compiler object file: {}".format(objectFiles))
        return inputFiles, objectFiles


def invokeRealCompiler(
    compilerBinary, cmdLine, captureOutput=False, outputAsString=True, environment=None
):
    realCmdline = [compilerBinary] + cmdLine
    printTraceStatement("Invoking real compiler as {}".format(realCmdline))

    environment = environment or os.environ

    # Environment variable set by the Visual Studio IDE to make cl.exe write
    # Unicode output to named pipes instead of stdout. Unset it to make sure
    # we can catch stdout output.
    environment.pop("VS_UNICODE_OUTPUT", None)

    returnCode = None
    stdout = b""
    stderr = b""
    if captureOutput:
        # Don't use subprocess.communicate() here, it's slow due to internal
        # threading.
        with TemporaryFile() as stdoutFile, TemporaryFile() as stderrFile:
            compilerProcess = subprocess.Popen(
                realCmdline, stdout=stdoutFile, stderr=stderrFile, env=environment
            )
            returnCode = compilerProcess.wait()
            stdoutFile.seek(0)
            stdout = stdoutFile.read()
            stderrFile.seek(0)
            stderr = stderrFile.read()
    else:
        returnCode = subprocess.call(realCmdline, env=environment)

    printTraceStatement("Real compiler returned code {0:d}".format(returnCode))

    if outputAsString:
        stdoutString = stdout.decode(CL_DEFAULT_CODEC)
        stderrString = stderr.decode(CL_DEFAULT_CODEC)
        return returnCode, stdoutString, stderrString

    return returnCode, stdout, stderr


# Returns the amount of jobs which should be run in parallel when
# invoked in batch mode as determined by the /MP argument
def jobCount(cmdLine):
    mpSwitches = [arg for arg in cmdLine if re.match(r"^/MP(\d+)?$", arg)]
    if not mpSwitches:
        return 1

    # the last instance of /MP takes precedence
    mpSwitch = mpSwitches.pop()

    count = mpSwitch[3:]
    if count != "":
        return int(count)

    # /MP, but no count specified; use CPU count
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        # not expected to happen
        return 2


def printStatistics(cache):
    template = """
clcache statistics:
  current cache dir         : {}
  cache size                : {:,} bytes
  maximum cache size        : {:,} bytes
  cache entries             : {}
  cache hits                : {}
  cache misses
    total                      : {}
    evicted                    : {}
    header changed             : {}
    source changed             : {}
  passed to real compiler
    called w/ invalid argument : {}
    called for preprocessing   : {}
    called for linking         : {}
    called for external debug  : {}
    called w/o source          : {}
    called w/ multiple sources : {}
    called w/ PCH              : {}""".strip()

    with cache.statistics as stats, cache.configuration as cfg:
        print(
            template.format(
                str(cache),
                stats.currentCacheSize(),
                cfg.maximumCacheSize(),
                stats.numCacheEntries(),
                stats.numCacheHits(),
                stats.numCacheMisses(),
                stats.numEvictedMisses(),
                stats.numHeaderChangedMisses(),
                stats.numSourceChangedMisses(),
                stats.numCallsWithInvalidArgument(),
                stats.numCallsForPreprocessing(),
                stats.numCallsForLinking(),
                stats.numCallsForExternalDebugInfo(),
                stats.numCallsWithoutSourceFile(),
                stats.numCallsWithMultipleSourceFiles(),
                stats.numCallsWithPch(),
            )
        )


def resetStatistics(cache):
    with cache.statistics as stats:
        stats.resetCounters()


def cleanCache(cache):
    with cache.lock, cache.statistics as stats, cache.configuration as cfg:
        cache.clean(stats, cfg.maximumCacheSize())


def clearCache(cache):
    with cache.lock, cache.statistics as stats:
        cache.clean(stats, 0)


# Returns pair:
#   1. set of include filepaths
#   2. new compiler output
# Output changes if strip is True in that case all lines with include
# directives are stripped from it
def parseIncludesSet(compilerOutput, sourceFile, strip):
    newOutput = []
    includesSet = set()

    # Example lines
    # Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\INCLUDE\limits.h
    # Hinweis: Einlesen der Datei:   C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\INCLUDE\iterator
    #
    # So we match
    # - one word (translation of "note")
    # - colon
    # - space
    # - a phrase containing characters and spaces (translation of "including file")
    # - colon
    # - one or more spaces
    # - the file path, starting with a non-whitespace character
    reFilePath = re.compile(r"^(\w+): ([ \w]+):( +)(?P<file_path>\S.*)$")

    absSourceFile = os.path.normcase(os.path.abspath(sourceFile))
    for line in compilerOutput.splitlines(True):
        match = reFilePath.match(line.rstrip("\r\n"))
        if match is not None:
            filePath = match.group("file_path")
            filePath = os.path.normcase(os.path.abspath(filePath))
            if filePath != absSourceFile:
                includesSet.add(filePath)
        elif strip:
            newOutput.append(line)
    if strip:
        return includesSet, "".join(newOutput)
    else:
        return includesSet, compilerOutput


def addObjectToCache(stats, cache, cachekey, artifacts):
    # This function asserts that the caller locked 'section' and 'stats'
    # already and also saves them
    printTraceStatement(
        "Adding file {} to cache using key {}".format(
            artifacts.objectFilePath, cachekey
        )
    )

    size = cache.setEntry(cachekey, artifacts)
    if size is None:
        size = os.path.getsize(artifacts.objectFilePath)
    stats.registerCacheEntry(size)

    with cache.configuration as cfg:
        return stats.currentCacheSize() >= cfg.maximumCacheSize()


def processCacheHit(cache, objectFile, cachekey):
    printTraceStatement(
        "Reusing cached object for key {} for object file {}".format(
            cachekey, objectFile
        )
    )

    with cache.lockFor(cachekey):
        with cache.statistics as stats:
            stats.registerCacheHit()

        if os.path.exists(objectFile):
            os.remove(objectFile)

        cachedArtifacts = cache.getEntry(cachekey)
        copyOrLink(cachedArtifacts.objectFilePath, objectFile)
        printTraceStatement("Finished. Exit code 0")
        return 0, cachedArtifacts.stdout, cachedArtifacts.stderr, False


def createManifestEntry(manifestHash, includePaths):
    sortedIncludePaths = sorted(set(includePaths))
    includeHashes = getFileHashes(sortedIncludePaths)

    safeIncludes = [collapseBasedirToPlaceholder(path) for path in sortedIncludePaths]
    includesContentHash = ManifestRepository.getIncludesContentHashForHashes(
        includeHashes
    )
    cachekey = CompilerArtifactsRepository.computeKeyDirect(
        manifestHash, includesContentHash
    )

    return ManifestEntry(safeIncludes, includesContentHash, cachekey)


def run(cache, compiler, compiler_args, env):
    printTraceStatement("Found real compiler binary at '{0!s}'".format(compiler))

    if "CLCACHE_DISABLE" in os.environ:
        exit_code, out, err = invokeRealCompiler(compiler, compiler_args, env)
        return exit_code, [out], [err]
    else:
        return processCompileRequest(cache, compiler, compiler_args, env)


cache = None


def runClCache(compiler, compiler_args, env):
    """ Entry point, designed to be used by external tools like Nuitka's scons. """
    global cache  # This is a singleton if this is called multiple times, pylint: disable=global-statement

    if cache is None:
        cache = Cache()

    exit_code, out, err = run(cache, compiler, compiler_args, env)

    assert len(out) == 1 == len(err)

    # Preferred order in Nuitka scons is output, error, exit_code and we expect
    # bytes.
    return out[0].encode(CL_DEFAULT_CODEC), err[0].encode(CL_DEFAULT_CODEC), exit_code


def updateCacheStatistics(cache, method):
    with cache.statistics as stats:
        method(stats)


def printOutAndErr(out, err):
    if "CLCACHE_HIDE_OUTPUTS" not in os.environ:
        printBinary(sys.stdout, out.encode(CL_DEFAULT_CODEC))
        printBinary(sys.stderr, err.encode(CL_DEFAULT_CODEC))


def printErrStr(message):
    with OUTPUT_LOCK:
        print(message, file=sys.stderr)


def processCompileRequest(cache, compiler, args, env):
    printTraceStatement("Parsing given commandline '{0!s}'".format(args))

    cmdLine, environment = extendCommandLineFromEnvironment(args, env)
    cmdLine = expandCommandLine(cmdLine)
    printTraceStatement("Expanded commandline '{0!s}'".format(cmdLine))

    try:
        sourceFiles, objectFiles = CommandLineAnalyzer.analyze(cmdLine)
        return scheduleJobs(
            cache, compiler, cmdLine, environment, sourceFiles, objectFiles
        )
    except InvalidArgumentError:
        printTraceStatement(
            "Cannot cache invocation as {}: invalid argument".format(cmdLine)
        )
        updateCacheStatistics(cache, Statistics.registerCallWithInvalidArgument)
    except NoSourceFileError:
        printTraceStatement(
            "Cannot cache invocation as {}: no source file found".format(cmdLine)
        )
        updateCacheStatistics(cache, Statistics.registerCallWithoutSourceFile)
    except MultipleSourceFilesComplexError:
        printTraceStatement(
            "Cannot cache invocation as {}: multiple source files found".format(cmdLine)
        )
        updateCacheStatistics(cache, Statistics.registerCallWithMultipleSourceFiles)
    except CalledWithPchError:
        printTraceStatement(
            "Cannot cache invocation as {}: precompiled headers in use".format(cmdLine)
        )
        updateCacheStatistics(cache, Statistics.registerCallWithPch)
    except CalledForLinkError:
        printTraceStatement(
            "Cannot cache invocation as {}: called for linking".format(cmdLine)
        )
        updateCacheStatistics(cache, Statistics.registerCallForLinking)
    except ExternalDebugInfoError:
        printTraceStatement(
            "Cannot cache invocation as {}: external debug information (/Zi) is not supported".format(
                cmdLine
            )
        )
        updateCacheStatistics(cache, Statistics.registerCallForExternalDebugInfo)
    except CalledForPreprocessingError:
        printTraceStatement(
            "Cannot cache invocation as {}: called for preprocessing".format(cmdLine)
        )
        updateCacheStatistics(cache, Statistics.registerCallForPreprocessing)

    exitCode, out, err = invokeRealCompiler(compiler, args, env)
    printOutAndErr(out, err)
    return exitCode, [out], [err]


def filterSourceFiles(
    cmdLine, sourceFiles
):
    setOfSources = set(sourceFile for sourceFile, _ in sourceFiles)
    skippedArgs = ("/Tc", "/Tp", "-Tp", "-Tc")
    return (
        arg
        for arg in cmdLine
        if not (arg in setOfSources or arg.startswith(skippedArgs))
    )


def scheduleJobs(
    cache,
    compiler,
    cmdLine,
    environment,
    sourceFiles,
    objectFiles,
):
    result_out = []
    result_err = []

    # Filter out all source files from the command line to form baseCmdLine
    baseCmdLine = [
        arg
        for arg in filterSourceFiles(cmdLine, sourceFiles)
        if not arg.startswith("/MP")
    ]

    exitCode = 0
    cleanupRequired = False
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=jobCount(cmdLine)
    ) as executor:
        jobs = []
        for (srcFile, srcLanguage), objFile in zip(sourceFiles, objectFiles):
            jobCmdLine = baseCmdLine + [srcLanguage + srcFile]
            jobs.append(
                executor.submit(
                    processSingleSource,
                    compiler,
                    jobCmdLine,
                    srcFile,
                    objFile,
                    environment,
                )
            )
        for future in concurrent.futures.as_completed(jobs):
            exitCode, out, err, doCleanup = future.result()
            printTraceStatement("Finished. Exit code {0:d}".format(exitCode))
            cleanupRequired |= doCleanup
            printOutAndErr(out, err)

            result_out.append(out)
            result_err.append(err)

            if exitCode != 0:
                break

    if cleanupRequired:
        cleanCache(cache)

    return exitCode, result_out, result_err


def processSingleSource(compiler, cmdLine, sourceFile, objectFile, environment):
    try:
        assert objectFile is not None
        cache = Cache()

        if "CLCACHE_NODIRECT" in os.environ and os.environ["CLCACHE_NODIRECT"] != "0":
            return processNoDirect(cache, objectFile, compiler, cmdLine, environment)
        else:
            return processDirect(
                cache, objectFile, compiler, cmdLine, sourceFile, environment
            )

    except IncludeNotFoundException:
        return invokeRealCompiler(compiler, cmdLine, environment=environment), False
    except CompilerFailedException as e:
        return e.getReturnTuple()


def processDirect(cache, objectFile, compiler, cmdLine, sourceFile, env):
    manifestHash = ManifestRepository.getManifestHash(compiler, cmdLine, sourceFile)
    manifestHit = None
    with cache.manifestLockFor(manifestHash):
        manifest = cache.getManifest(manifestHash)
        if manifest:
            for entryIndex, entry in enumerate(manifest.entries()):
                # NOTE: command line options already included in hash for manifest name
                try:
                    includesContentHash = (
                        ManifestRepository.getIncludesContentHashForFiles(
                            [
                                expandBasedirPlaceholder(path)
                                for path in entry.includeFiles
                            ]
                        )
                    )

                    if entry.includesContentHash == includesContentHash:
                        cachekey = entry.objectHash
                        assert cachekey is not None
                        if entryIndex > 0:
                            # Move manifest entry to the top of the entries in the manifest
                            manifest.touchEntry(cachekey)
                            cache.setManifest(manifestHash, manifest)

                        manifestHit = True
                        with cache.lockFor(cachekey):
                            if cache.hasEntry(cachekey):
                                return processCacheHit(cache, objectFile, cachekey)

                except IncludeNotFoundException:
                    pass

            unusableManifestMissReason = Statistics.registerHeaderChangedMiss
        else:
            unusableManifestMissReason = Statistics.registerSourceChangedMiss

    if manifestHit is None:
        stripIncludes = False
        if "/showIncludes" not in cmdLine:
            cmdLine = list(cmdLine)
            cmdLine.insert(0, "/showIncludes")
            stripIncludes = True
    compilerResult = invokeRealCompiler(
        compiler, cmdLine, captureOutput=True, environment=env
    )
    if manifestHit is None:
        includePaths, compilerOutput = parseIncludesSet(
            compilerResult[1], sourceFile, stripIncludes
        )
        compilerResult = (compilerResult[0], compilerOutput, compilerResult[2])

    with cache.manifestLockFor(manifestHash):
        if manifestHit is not None:
            return ensureArtifactsExist(
                cache, cachekey, unusableManifestMissReason, objectFile, compilerResult
            )

        entry = createManifestEntry(manifestHash, includePaths)
        cachekey = entry.objectHash

        def addManifest():
            manifest = cache.getManifest(manifestHash) or Manifest()
            manifest.addEntry(entry)
            cache.setManifest(manifestHash, manifest)

        return ensureArtifactsExist(
            cache,
            cachekey,
            unusableManifestMissReason,
            objectFile,
            compilerResult,
            addManifest,
        )


def processNoDirect(cache, objectFile, compiler, cmdLine, environment):
    cachekey = CompilerArtifactsRepository.computeKeyNodirect(
        compiler, cmdLine, environment
    )
    with cache.lockFor(cachekey):
        if cache.hasEntry(cachekey):
            return processCacheHit(cache, objectFile, cachekey)

    compilerResult = invokeRealCompiler(
        compiler, cmdLine, captureOutput=True, environment=environment
    )

    return ensureArtifactsExist(
        cache, cachekey, Statistics.registerCacheMiss, objectFile, compilerResult
    )


def ensureArtifactsExist(
    cache, cachekey, reason, objectFile, compilerResult, extraCallable=None
):
    cleanupRequired = False
    returnCode, compilerOutput, compilerStderr = compilerResult
    correctCompiliation = returnCode == 0 and os.path.exists(objectFile)
    with cache.lockFor(cachekey):
        if not cache.hasEntry(cachekey):
            with cache.statistics as stats:
                reason(stats)
                if correctCompiliation:
                    artifacts = CompilerArtifacts(
                        objectFile, compilerOutput, compilerStderr
                    )
                    cleanupRequired = addObjectToCache(
                        stats, cache, cachekey, artifacts
                    )
            if extraCallable and correctCompiliation:
                extraCallable()
    return returnCode, compilerOutput, compilerStderr, cleanupRequired
