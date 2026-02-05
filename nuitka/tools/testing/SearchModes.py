#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Search modes for Nuitka's test runner.

The test runner can handle found errors, skip tests, etc. with search
modes, which are implemented here.
"""

import os
import sys
from fnmatch import fnmatch

from nuitka.__past__ import md5
from nuitka.utils.FileOperations import (
    areSamePaths,
    getFileContents,
    putTextFileContents,
)


class SearchMode(object):
    # Lots of details, to keep track of pylint: disable=too-many-instance-attributes

    __slots__ = (
        "active",
        "start_at",
        "only",
        "skip",
        "coverage",
        "abort_on_error",
        "start_dir",
        "logger",
        "may_fail",
        "verifications",
        "failed",
        "had_match",
        "cache_filename",
        "resume_from",
        "max_failures",
    )

    def __init__(
        self,
        logger,
        start_at,
        start_dir,
        resume=False,
        only=False,
        skip=False,
        abort_on_error=True,
        coverage=False,
        max_failures=None,
    ):
        self.active = False
        self.start_at = start_at
        self.only = only
        self.skip = skip
        self.coverage = coverage
        self.had_match = False
        self.abort_on_error = abort_on_error
        self.max_failures = max_failures

        self.start_dir = start_dir
        self.logger = logger
        self.may_fail = []

        if only and not abort_on_error:
            self.logger.sysexit("Error, cannot combine --only-one and --all.")

        self.verifications = 0
        self.failed = []

        # We are going to produce a hash from the command line script we are running,
        # so we have a unique place to store the resume state.
        tests_path = os.path.normcase(os.path.abspath(sys.modules["__main__"].__file__))
        version = sys.version

        if str is not bytes:
            tests_path = tests_path.encode("utf8")
            version = version.encode("utf8")

        case_hash = md5(tests_path)
        case_hash.update(version)

        from .Common import getTestingCacheDir

        cache_filename = os.path.join(getTestingCacheDir(), case_hash.hexdigest())

        self.cache_filename = cache_filename

        if resume and os.path.exists(cache_filename):
            self.resume_from = getFileContents(cache_filename) or None
        else:
            self.resume_from = None

    def consider(self, dirname, filename):
        if self.active and self.only:
            return False

        # Check if we become active
        if not self.active:
            if self.only and self.had_match:
                return False

            if self.start_at is None and not self.resume_from:
                self.active = True
            elif self.resume_from:
                if self._match(dirname, filename, self.resume_from):
                    self.active = True
                    if self.skip:
                        return False
            elif self.start_at:
                if self._match(dirname, filename, self.start_at):
                    self.active = True

        if self.active:
            # If active, we still filter by pattern if one was given.
            if self.start_at and not self._match(dirname, filename, self.start_at):
                return False

            # If we are active, we can save the current file as the one to resume
            # from.
            self._saveResume(dirname, filename)

            if self.only:
                self.active = False

            self.had_match = True
            self.verifications += 1
            return True

        return False

    def _saveResume(self, dirname, filename):
        parts = [dirname, filename]

        while None in parts:
            parts.remove(None)
        assert parts

        path = os.path.join(*parts)

        putTextFileContents(self.cache_filename, contents=path)

    def abortOnFinding(self, dirname, filename):
        if not self._abortOnFinding(dirname, filename):
            return False

        self.failed.append(filename)

        if self.abort_on_error:
            return True

        if self.max_failures is not None and len(self.failed) >= self.max_failures:
            self.logger.warning("Max failures reached.")
            return True

        return False

    def _abortOnFinding(self, dirname, filename):
        for candidate in self.may_fail:
            if self._match(dirname, filename, candidate):
                return False

        return True

    def onErrorDetected(self, message):
        self.finish(success=False)
        return self.exit(message)

    def finish(self, success=True):
        if not self.active and not self.had_match:
            return self.exit("Error, became never active.")

        if success and os.path.exists(self.cache_filename):
            os.unlink(self.cache_filename)

        print(
            "Ran %d test cases (%d failures)." % (self.verifications, len(self.failed))
        )

        if self.failed:
            return self.exit("Error, tests %s failed." % str(self.failed))

    def getExtraFlags(self, dirname, filename):
        # pylint: disable=unused-argument

        if self.coverage:
            return ["coverage"]
        return []

    def isCoverage(self):
        return self.coverage

    def mayFailFor(self, *names):
        self.may_fail += names

    def _match(self, dirname, filename, candidate):
        parts = [dirname, filename]

        while None in parts:
            parts.remove(None)
        assert parts

        path = os.path.join(*parts)

        candidates = (
            dirname,
            filename,
            filename.rsplit(".", 1)[0],
            filename.rsplit(".", 1)[0].replace("Test", ""),
            path,
            path.rsplit(".", 1)[0],
            path.rsplit(".", 1)[0].replace("Test", ""),
        )

        if candidate.rstrip("/") in candidates:
            return True

        if areSamePaths(os.path.join(self.start_dir, candidate), filename):
            return True

        for c in candidates:
            if c is None:
                continue

            if fnmatch(c, candidate):
                return True

        return False

    def exit(self, message):
        return self.logger.sysexit(message)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
