#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Check for Nuitka release updates."""

from __future__ import absolute_import

import os
import re
import time

from nuitka.PythonVersions import python_version
from nuitka.Tracing import general
from nuitka.TreeXML import convertStringToXML
from nuitka.Version import (
    getCommercialVersion,
    getNuitkaVersion,
    parseNuitkaVersionToTuple,
)

from .utils.AppDirs import getCacheDir
from .utils.Download import withUrlOpen
from .utils.FileOperations import (
    deleteFile,
    getNormalizedPathJoin,
    replaceFileAtomic,
    withTemporaryFilename,
)
from .utils.Json import loadJsonFromFilename, writeJsonToFilename

_update_check_cache_ttl = 7 * 24 * 60 * 60  # One week in seconds.
_update_check_cache_filename = "update_check.json"
_update_check_url = "https://pypi.org/rss/project/nuitka/releases.xml"
_update_check_timeout = 3.0
_update_check_mnemonic = "outdated-nuitka-version"
_stable_version_regex = re.compile(r"^[0-9]+(\.[0-9]+)+$")


def _getCurrentTimeInSeconds():
    return int(time.time())


def _getResponseHeader(response, header_name):
    if python_version < 0x300:
        return response.info().getheader(header_name)
    else:
        return response.headers.get(header_name)


def _normalizeStableNuitkaVersion(version):
    if version is None:
        return None

    version = version.strip()

    for prefix in ("Nuitka V", "Nuitka v", "Nuitka ", "V", "v"):
        if version.startswith(prefix):
            version = version[len(prefix) :].strip()
            break

    if _stable_version_regex.match(version):
        return version

    return None


def _isCacheStillFresh(cache_data, current_time):
    last_check = cache_data.get("last_check")

    if type(last_check) is not int:
        return False

    return current_time - last_check < _update_check_cache_ttl


def _getCachedAge(cache_data, current_time):
    last_check = cache_data.get("last_check")

    if type(last_check) is not int:
        return None

    return max(0, current_time - last_check)


def _getUpdateCheckCacheFilename():
    return getNormalizedPathJoin(
        getCacheDir("updates", create=True),
        _update_check_cache_filename,
    )


def _readUpdateCheckCache():
    cache_filename = _getUpdateCheckCacheFilename()

    if os.path.exists(cache_filename):
        cache_data = loadJsonFromFilename(cache_filename)
    else:
        cache_data = {}

    if type(cache_data) is not dict:
        cache_data = {}

    latest_version = _normalizeStableNuitkaVersion(cache_data.get("latest_version"))

    if latest_version is not None:
        cache_data["latest_version"] = latest_version
    else:
        cache_data.pop("latest_version", None)

    for key in ("etag", "last_modified"):
        if key in cache_data and type(cache_data[key]) is not str:
            cache_data.pop(key)

    if type(cache_data.get("last_check")) is not int:
        cache_data.pop("last_check", None)

    return cache_filename, cache_data


def _writeUpdateCheckCache(cache_filename, cache_data):
    cache_dir = os.path.dirname(cache_filename)

    with withTemporaryFilename(
        prefix="update-check-", suffix=".json", temp_path=cache_dir
    ) as temp_filename:
        try:
            writeJsonToFilename(temp_filename, cache_data)
            replaceFileAtomic(temp_filename, cache_filename)
        finally:
            deleteFile(temp_filename, must_exist=False)


def fetchLatestNuitkaVersion(
    etag=None, last_modified=None, timeout=_update_check_timeout
):
    """Fetch the latest stable Nuitka release version.

    Returns:
        tuple(state, latest_version, etag, last_modified)
    """

    request_headers = {"User-Agent": "Nuitka Update Check/%s" % getNuitkaVersion()}

    if etag is not None:
        request_headers["If-None-Match"] = etag

    if last_modified is not None:
        request_headers["If-Modified-Since"] = last_modified

    try:
        with withUrlOpen(
            url=_update_check_url,
            request_headers=request_headers,
            timeout=timeout,
            allow_http_fallback=False,
        ) as response:
            xml_contents = response.read()
            etag = _getResponseHeader(response, "ETag")
            last_modified = _getResponseHeader(response, "Last-Modified")
    except Exception as e:  # pylint: disable=broad-except
        if getattr(e, "code", None) == 304:
            return "not-modified", None, etag, last_modified

        return "failed", None, etag, last_modified

    root = convertStringToXML(xml_contents)

    if root is None:
        return "failed", None, etag, last_modified

    for item in root.findall("./channel/item"):
        title = item.findtext("title")
        latest_version = _normalizeStableNuitkaVersion(title)

        if latest_version is not None:
            return "modified", latest_version, etag, last_modified

    return "failed", None, etag, last_modified


def _makeUpdateCheckMessage(current_version, latest_version):
    return "Nuitka '%s' is older than the latest stable release '%s'." % (
        current_version,
        latest_version,
    )


def _getCurrentToLatestVersionRelation(latest_version):
    current_version = getNuitkaVersion()

    current_version = parseNuitkaVersionToTuple(current_version)
    latest_version = parseNuitkaVersionToTuple(latest_version)

    if current_version < latest_version:
        return "older"
    elif current_version > latest_version:
        return "newer"
    else:
        return "equal"


def _getAgeDescription(age):
    if age < 60:
        unit = "second"
        value = age
    elif age < 3600:
        unit = "minute"
        value = age // 60
    elif age < 24 * 3600:
        unit = "hour"
        value = age // 3600
    else:
        unit = "day"
        value = age // (24 * 3600)

    if value != 1:
        unit += "s"

    return "%d %s old" % (value, unit)


def _checkNuitkaUpdateStatus(update_check_mode):
    if getCommercialVersion() is not None:
        return "disabled", None, None

    if update_check_mode == "never":
        return "disabled", None, None

    current_time = _getCurrentTimeInSeconds()
    cache_filename, cache_data = _readUpdateCheckCache()
    old_age = _getCachedAge(cache_data, current_time)

    if update_check_mode != "force" and _isCacheStillFresh(cache_data, current_time):
        return (
            "cached",
            cache_data.get("latest_version"),
            _getCachedAge(cache_data, current_time),
        )

    fetch_state, latest_version, etag, last_modified = fetchLatestNuitkaVersion(
        etag=None if update_check_mode == "force" else cache_data.get("etag"),
        last_modified=(
            None if update_check_mode == "force" else cache_data.get("last_modified")
        ),
    )

    cache_data["last_check"] = current_time

    age = None

    if fetch_state == "modified":
        cache_data["latest_version"] = latest_version
        cache_data["etag"] = etag
        cache_data["last_modified"] = last_modified
        status = "fetched"
    elif fetch_state == "not-modified":
        if etag is not None:
            cache_data["etag"] = etag

        if last_modified is not None:
            cache_data["last_modified"] = last_modified

        latest_version = cache_data.get("latest_version")
        status = "checked"
        age = 0
    else:
        latest_version = cache_data.get("latest_version")

        if latest_version is None:
            status = "failed"
            age = None
        else:
            status = "stale-cache"
            age = old_age

    if fetch_state == "modified":
        age = 0

    _writeUpdateCheckCache(cache_filename, cache_data)

    return status, latest_version, age


def _reportUpdateCheckResult(update_check_mode, latest_version):
    if latest_version is None:
        return

    if _getCurrentToLatestVersionRelation(latest_version) != "older":
        return

    current_version = getNuitkaVersion()

    message = _makeUpdateCheckMessage(
        current_version=current_version,
        latest_version=latest_version,
    )

    if update_check_mode == "error":
        return general.sysexit(message)
    elif update_check_mode in ("warning", "force"):
        general.warning(message, mnemonic=_update_check_mnemonic)
    elif update_check_mode == "info":
        general.info(message)
    else:
        assert False, update_check_mode


def getNuitkaUpdateStatusValue(update_check_mode):
    status, latest_version, age = _checkNuitkaUpdateStatus(update_check_mode)

    if status == "disabled":
        return "Update status: disabled."

    if latest_version is None:
        return "Update status: unavailable."

    relation = _getCurrentToLatestVersionRelation(latest_version)

    if relation == "older":
        result = "Update status: stable release '%s' available" % (latest_version,)
    elif relation == "equal":
        result = "Update status: up to date with stable release '%s'" % (
            latest_version,
        )
    else:
        result = "Update status: newer than stable release '%s'" % (latest_version,)

    if status == "cached":
        result += " (cached, %s)." % _getAgeDescription(age)
    elif status == "stale-cache":
        result += " (using cached data after refresh failed, %s)." % (
            _getAgeDescription(age),
        )
    else:
        result += "."

    return result


def checkNuitkaUpdate(update_check_mode):
    status, latest_version, _age = _checkNuitkaUpdateStatus(update_check_mode)

    if status == "disabled":
        return

    _reportUpdateCheckResult(
        update_check_mode=update_check_mode,
        latest_version=latest_version,
    )


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
