#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Launching and querying the Python interpreter of the selected target.

The host runs a small JSON broker in the target Python. Requests are sent on
stdin and responses are read from stdout; diagnostics are kept separate on
stderr. This keeps the transport usable for a local Python, Wine, WSL, SSH, or
Wasmtime hosted interpreter without requiring a socket or a shared filesystem.
"""

import base64
import os
import struct
import subprocess
import sys
import threading
import time

from nuitka import PythonVersions
from nuitka.Constants import TargetVersionInfo
from nuitka.Errors import NuitkaNotYetSupported
from nuitka.Tracing import cross_compilation_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Execution import getExecutablePath
from nuitka.utils.FileOperations import getNormalizedPathJoin, withFileLock
from nuitka.utils.Hashing import getHashFromValues
from nuitka.utils.Json import (
    jsonDumps,
    jsonLoads,
    loadJsonFromFilename,
    writeJsonToFilename,
)
from nuitka.utils.Utils import isWin32OrPosixWindows
from nuitka.utils.WasiPython import getWasiPythonPrefix
from nuitka.utils.Wasmtime import getWasmtimePath

_TARGET_PYTHON_PROTOCOL_VERSION = 3

# This is executed with the target interpreter. Keep it compatible with both
# Python 2.6 and Python 3, and keep it small enough for "-c".
_TARGET_PYTHON_BROKER = r"""
import base64
import os
import struct
import sys

from json import dumps, loads

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

if str is bytes:
    _text_type = unicode
    _bytes_type = str
else:
    _text_type = str
    _bytes_type = bytes

try:
    _int_types = (int, long)
except NameError:
    _int_types = (int,)

if os.name == "nt":
    import msvcrt

    msvcrt.setmode(0, os.O_BINARY)
    msvcrt.setmode(1, os.O_BINARY)


def _read_exact(count):
    result = []
    while count:
        data = os.read(0, count)
        if not data:
            return None
        result.append(data)
        count -= len(data)
    return "".join(result) if str is bytes else b"".join(result)


def _write_all(data):
    if str is not bytes and type(data) is not bytes:
        data = data.encode("utf8")

    while data:
        written = os.write(1, data)
        data = data[written:]


def _send(message):
    payload = dumps(message)
    if str is not bytes and type(payload) is not bytes:
        payload = payload.encode("utf8")
    _write_all(struct.pack(">I", len(payload)) + payload)


def _read_message():
    header = _read_exact(4)
    if header is None:
        return None
    length = struct.unpack(">I", header)[0]
    payload = _read_exact(length)
    if payload is None:
        return None
    if str is not bytes and type(payload) is bytes:
        payload = payload.decode("utf8")
    return loads(payload)


def _encode_float(value):
    try:
        return {"t": "float", "v": value.hex()}
    except AttributeError:
        return {"t": "float", "v": repr(value)}


def _encode_value(value):
    if value is None:
        return {"t": "none"}
    if value is True:
        return {"t": "bool", "v": True}
    if value is False:
        return {"t": "bool", "v": False}
    if type(value) in _int_types:
        return {"t": "int", "v": str(value)}
    if type(value) is float:
        return _encode_float(value)
    if type(value) is complex:
        return {
            "t": "complex",
            "re": _encode_float(value.real),
            "im": _encode_float(value.imag),
        }
    if type(value) is _bytes_type:
        encoded = base64.b64encode(value)
        if str is not bytes and type(encoded) is bytes:
            encoded = encoded.decode("ascii")
        return {"t": "bytes", "v": encoded}
    if type(value) is _text_type:
        return {"t": "text", "v": value}
    if type(value) is tuple:
        return {"t": "tuple", "v": [_encode_value(item) for item in value]}
    if type(value) is list:
        return {"t": "list", "v": [_encode_value(item) for item in value]}
    if type(value) is dict:
        return {
            "t": "dict",
            "v": [
                [_encode_value(key), _encode_value(item)]
                for key, item in value.items()
            ],
        }
    if type(value) is set:
        return {"t": "set", "v": [_encode_value(item) for item in value]}
    if type(value) is frozenset:
        return {"t": "frozenset", "v": [_encode_value(item) for item in value]}

    return {"t": "repr", "v": repr(value)}


def _execute(setup_code, code):
    if str is bytes:
        if isinstance(setup_code, _text_type):
            setup_code = setup_code.encode("utf8")
        if isinstance(code, _text_type):
            code = code.encode("utf8")

    stdout = StringIO()
    stderr = StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        sys.stdout = stdout
        sys.stderr = stderr
        namespace = {"__builtins__": __builtins__, "sys": sys, "os": os}
        if setup_code:
            exec(setup_code, namespace)  # pylint: disable=exec-used
        value = eval(
            code,
            namespace,
            {},
        )
    except BaseException as e:
        return {
            "ok": False,
            "error": {"type": type(e).__name__, "message": str(e)},
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return {
        "ok": True,
        "value": _encode_value(value),
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
    }


while True:
    request = _read_message()
    if request is None:
        break

    request_id = request.get("id")
    operation = request.get("op")

    if operation == "hello":
        response = {
            "ok": True,
            "protocol": 3,
            "python_version": list(sys.version_info[:3]),
            "python_version_str": sys.version.split()[0],
            "platform": sys.platform,
            "maxsize": getattr(sys, "maxsize", getattr(sys, "maxint", None)),
            "byteorder": sys.byteorder,
            "version_info": list(sys.version_info),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "hash_seed": os.environ.get("PYTHONHASHSEED"),
        }
    elif operation == "eval":
        response = _execute(request["setup"], request["code"])
    elif operation == "find_spec":
        try:
            from importlib.util import find_spec
        except ImportError:
            from pkgutil import get_loader

            value = get_loader(request["module_name"]) is not None
        else:
            try:
                value = find_spec(request["module_name"]) is not None
            except ImportError:
                value = False

        response = {"ok": True, "value": _encode_value(value)}
    elif operation == "walk_packages":
        import pkgutil

        module = __import__(request["module_name"])

        response = {
            "ok": True,
            "value": _encode_value(
                [
                    module_info[1]
                    for module_info in pkgutil.walk_packages(module.__path__)
                ]
            ),
        }
    elif operation == "shutdown":
        response = {"ok": True}
    else:
        response = {
            "ok": False,
            "error": {
                "type": "ProtocolError",
                "message": "Unknown operation '%s'" % operation,
            },
        }

    response["id"] = request_id
    _send(response)

    if operation == "shutdown":
        break
"""


class TargetPythonError(Exception):
    """Error while starting or communicating with the target Python."""


def _getEnvironment():
    """Return a sanitized environment for target Python execution."""
    env = dict(os.environ)

    for variable_name in (
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
        "PYTHONSAFEPATH",
    ):
        env.pop(variable_name, None)

    env["PYTHONHASHSEED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    env["LC_ALL"] = "C"
    env["TZ"] = "UTC"

    return env


def _getWasiCommand(python_prefix, assume_yes_for_downloads):
    if python_prefix is None:
        python_prefix = getWasiPythonPrefix(
            assume_yes_for_downloads=assume_yes_for_downloads
        )

    python_executable = getNormalizedPathJoin(
        python_prefix,
        "bin",
        "python%s.wasm" % PythonVersions.python_version_str,
    )

    if not os.path.isfile(python_executable):
        raise TargetPythonError(
            "WASI Python executable '%s' does not exist." % python_executable
        )

    wasmtime_path = getWasmtimePath(assume_yes_for_downloads=assume_yes_for_downloads)

    if wasmtime_path is None:
        raise TargetPythonError("Could not locate Wasmtime.")

    return [
        wasmtime_path,
        "run",
        "--dir=%s::/usr/local" % python_prefix,
        "--env=PYTHONHASHSEED=0",
        python_executable,
    ]


def _findWindowsPython(python_prefix):
    if os.path.isfile(python_prefix):
        return python_prefix

    for candidate in (
        "python.exe",
        "python3.exe",
        os.path.join("bin", "python.exe"),
        os.path.join("bin", "python3.exe"),
    ):
        candidate_path = getNormalizedPathJoin(python_prefix, candidate)

        if os.path.isfile(candidate_path):
            return candidate_path

    raise TargetPythonError(
        "No Python executable found in Windows Python prefix '%s'." % python_prefix
    )


def _getWin32Command(python_prefix):
    if python_prefix is None:
        raise NuitkaNotYetSupported(
            "Target Python execution for Win32 requires a Windows Python prefix."
        )

    python_executable = _findWindowsPython(python_prefix)

    if isWin32OrPosixWindows():
        return [python_executable]

    wine_path = getExecutablePath("wine")

    if wine_path is None:
        raise TargetPythonError(
            "Running the Win32 target Python requires 'wine' on this host."
        )

    return [wine_path, python_executable]


def _getBrokerCommand(python_command):
    return python_command + [
        "-u",
        "-S",
        "-s",
        "-B",
        "-c",
        _TARGET_PYTHON_BROKER,
    ]


def getTargetPythonCommand(target_spec, python_prefix, assume_yes_for_downloads):
    """Return the command and environment for the selected target Python.

    Args:
        target_spec: TargetBase of the selected target.
        python_prefix: str or None, target Python prefix. For WASI this may be
            None to use the cached automatic download. Native targets ignore
            this value.
        assume_yes_for_downloads: bool, whether missing WASI SDK components may
            be downloaded without asking.

    Returns:
        tuple(command, environment)
    """
    if target_spec.isWasiTarget():
        python_command = _getWasiCommand(
            python_prefix=python_prefix,
            assume_yes_for_downloads=assume_yes_for_downloads,
        )
    elif target_spec.isWin32Target():
        python_command = _getWin32Command(python_prefix=python_prefix)
    else:
        python_command = [sys.executable]

    return _getBrokerCommand(python_command), _getEnvironment()


def _writeFrame(fileobj, message):
    payload = jsonDumps(message)
    if str is not bytes and type(payload) is not bytes:
        payload = payload.encode("utf8")

    data = struct.pack(">I", len(payload)) + payload
    file_descriptor = fileobj.fileno()

    while data:
        written = os.write(file_descriptor, data)
        data = data[written:]


def _readExact(fileobj, count):
    result = []
    file_descriptor = fileobj.fileno()

    while count:
        data = os.read(file_descriptor, count)

        if not data:
            return None

        result.append(data)
        count -= len(data)

    return "".join(result) if str is bytes else b"".join(result)


def _readFrame(fileobj):
    header = _readExact(fileobj, 4)

    if header is None:
        return None

    length = struct.unpack(">I", header)[0]
    payload = _readExact(fileobj, length)

    if payload is None:
        return None

    return jsonLoads(payload)


def _decodeValue(value):
    # This is deliberately a type dispatch with one return per value type.
    # pylint: disable=too-many-branches,too-many-return-statements
    value_type = value["t"]

    if value_type == "none":
        return None
    if value_type == "bool":
        return value["v"]
    if value_type == "int":
        return int(value["v"])
    if value_type == "float":
        try:
            return float.fromhex(value["v"])
        except AttributeError:
            return float(value["v"])
    if value_type == "complex":
        return complex(
            _decodeValue(value["re"]),
            _decodeValue(value["im"]),
        )
    if value_type == "bytes":
        return base64.b64decode(value["v"])
    if value_type == "text":
        return value["v"]
    if value_type == "tuple":
        return tuple(_decodeValue(item) for item in value["v"])
    if value_type == "list":
        return [_decodeValue(item) for item in value["v"]]
    if value_type == "dict":
        return dict((_decodeValue(key), _decodeValue(item)) for key, item in value["v"])
    if value_type == "set":
        return set(_decodeValue(item) for item in value["v"])
    if value_type == "frozenset":
        return frozenset(_decodeValue(item) for item in value["v"])
    if value_type == "repr":
        raise TargetPythonError(
            "Target Python returned an unsupported value: %s." % value["v"]
        )

    raise TargetPythonError("Unknown target value type '%s'." % value_type)


class TargetPython(object):
    """A persistent target Python broker using framed JSON over stdio."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, target_spec, python_prefix, assume_yes_for_downloads, use_cache):
        self.target_spec = target_spec
        self.assume_yes_for_downloads = assume_yes_for_downloads
        self.use_cache = use_cache

        self.process = None
        self.target_info = None
        self._request_id = 0
        self._stderr_chunks = []
        self._stderr_thread = None

        self.python_prefix = self._getResolvedPythonPrefix(python_prefix)
        self.cache_fingerprint = self._getCacheFingerprint()

    def _getResolvedPythonPrefix(self, python_prefix):
        if python_prefix is None:
            if self.target_spec.isWasiTarget():
                python_prefix = getWasiPythonPrefix(
                    assume_yes_for_downloads=self.assume_yes_for_downloads
                )
            else:
                return cross_compilation_logger.sysexit(
                    "Error, no target Python prefix specified for target '%s'."
                    % self.target_spec.getDescription()
                )

        return python_prefix

    def _getCacheFingerprint(self):
        return [
            ("protocol", _TARGET_PYTHON_PROTOCOL_VERSION),
            ("target", self.target_spec.getDescription()),
            ("target_os", self.target_spec.getTargetOS()),
            ("python_version", PythonVersions.python_version_str),
            ("prefix", self.python_prefix or ""),
        ]

    @staticmethod
    def _getCacheKey(fingerprint, expression, setup_code):
        key = fingerprint + [
            ("expression", expression),
            ("setup", setup_code),
        ]
        key_text = jsonDumps(key)

        cache_dir = getCacheDir("target-python", create=True)
        cache_filename = getNormalizedPathJoin(
            cache_dir, getHashFromValues(key_text) + ".json"
        )

        return key_text, cache_filename

    @staticmethod
    def _loadCachedValue(cache_key, cache_filename):
        if not os.path.isfile(cache_filename):
            return None

        try:
            cached = loadJsonFromFilename(cache_filename)
        except (IOError, OSError):
            return None

        if not isinstance(cached, dict):
            return None

        if cached.get("protocol") != _TARGET_PYTHON_PROTOCOL_VERSION:
            return None

        if cached.get("key") != cache_key:
            return None

        return cached.get("value")

    @staticmethod
    def _storeCachedValue(cache_key, cache_filename, value):
        with withFileLock("writing target Python cache"):
            writeJsonToFilename(
                filename=cache_filename,
                contents={
                    "protocol": _TARGET_PYTHON_PROTOCOL_VERSION,
                    "key": cache_key,
                    "value": value,
                },
            )

    def getCommand(self):
        """Return the command used to launch the target Python."""
        command, _environment = getTargetPythonCommand(
            target_spec=self.target_spec,
            python_prefix=self.python_prefix,
            assume_yes_for_downloads=self.assume_yes_for_downloads,
        )
        return command

    def start(self):
        """Start the target Python and perform the protocol handshake."""
        if self.process is not None:
            return self.target_info

        command, environment = getTargetPythonCommand(
            target_spec=self.target_spec,
            python_prefix=self.python_prefix,
            assume_yes_for_downloads=self.assume_yes_for_downloads,
        )

        self.process = subprocess.Popen(  # pylint: disable=consider-using-with
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            bufsize=0,
        )

        self._startStderrReader()
        self.target_info = self._request({"op": "hello"})

        if self.target_info.get("protocol") != _TARGET_PYTHON_PROTOCOL_VERSION:
            raise TargetPythonError(
                "Target Python protocol version mismatch (%r != %r)."
                % (
                    self.target_info.get("protocol"),
                    _TARGET_PYTHON_PROTOCOL_VERSION,
                )
            )

        return self.target_info

    def _startStderrReader(self):
        def readStderr():
            while True:
                data = self.process.stderr.read(4096)

                if not data:
                    break

                self._stderr_chunks.append(data)

        self._stderr_thread = threading.Thread(target=readStderr)
        self._stderr_thread.daemon = True
        self._stderr_thread.start()

    def _getStderrText(self):
        data = b"".join(self._stderr_chunks)

        if str is not bytes and type(data) is bytes:
            data = data.decode("utf8", "replace")

        return data

    def _request(self, message):
        if self.process is None:
            raise TargetPythonError("Target Python is not running.")

        self._request_id += 1
        message["id"] = self._request_id

        _writeFrame(self.process.stdin, message)
        response = _readFrame(self.process.stdout)

        if response is None:
            stderr_text = self._getStderrText()

            if stderr_text:
                raise TargetPythonError(
                    "Target Python terminated unexpectedly: %s" % stderr_text
                )

            raise TargetPythonError("Target Python terminated unexpectedly.")

        if response.get("id") != message["id"]:
            raise TargetPythonError(
                "Target Python protocol response id mismatch (%r != %r)."
                % (response.get("id"), message["id"])
            )

        if not response.get("ok"):
            error = response.get("error", {})
            raise TargetPythonError(
                "%s: %s"
                % (
                    error.get("type", "TargetPythonError"),
                    error.get("message", "unknown error"),
                )
            )

        return response

    def evaluate(self, expression, setup_code):
        """Evaluate an expression in the target Python and return its value."""
        cache_key = None
        cache_filename = None

        if self.use_cache:
            cache_key, cache_filename = self._getCacheKey(
                self.cache_fingerprint, expression, setup_code
            )

            cached_value = self._loadCachedValue(
                cache_key=cache_key, cache_filename=cache_filename
            )

            if cached_value is not None:
                try:
                    return _decodeValue(cached_value)
                except TargetPythonError:
                    # Ignore stale or unusable cache entries.
                    pass

        if self.process is None:
            self.start()

        response = self._request(
            {"op": "eval", "code": expression, "setup": setup_code}
        )
        value = _decodeValue(response["value"])

        if self.use_cache and not response.get("stdout") and not response.get("stderr"):
            self._storeCachedValue(
                cache_key=cache_key,
                cache_filename=cache_filename,
                value=response["value"],
            )

        return value

    def getPythonVersionInfo(self):
        """Return the target Python's version information."""
        return TargetVersionInfo(*self.start()["version_info"])

    def getModuleSubPackages(self, module_name):
        """Return importable subpackages for a module on the target Python."""
        if self.process is None:
            self.start()

        response = self._request(
            {
                "op": "walk_packages",
                "module_name": module_name,
            }
        )

        return _decodeValue(response["value"])

    def canImportModule(self, module_name):
        """Return whether a module is importable in the target Python."""
        if self.process is None:
            self.start()

        response = self._request(
            {
                "op": "find_spec",
                "module_name": module_name,
            }
        )

        return _decodeValue(response["value"])

    def close(self):
        """Stop the target Python broker."""
        if self.process is None:
            return

        try:
            _writeFrame(self.process.stdin, {"op": "shutdown"})
        except (IOError, OSError):
            pass

        try:
            self.process.stdin.close()
        except (IOError, OSError):
            pass

        deadline = time.time() + 5.0

        while self.process.poll() is None and time.time() < deadline:
            time.sleep(0.05)

        if self.process.poll() is None:
            self.process.terminate()

            deadline = time.time() + 5.0

            while self.process.poll() is None and time.time() < deadline:
                time.sleep(0.05)

        if self.process.poll() is None:
            self.process.kill()

        try:
            self.process.wait()
        except OSError:
            pass

        if self._stderr_thread is not None:
            self._stderr_thread.join(1.0)

        self.process = None


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
