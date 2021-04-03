#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Search modes for Nuitka's test runner.

The test runner can handle found errors, skip tests, etc. with search
modes, which are implemented here.
"""

import hashlib
import os
import sys

from nuitka.utils.FileOperations import areSamePaths


class SearchModeBase(object):
    def __init__(self):
        self.may_fail = []

    def consider(self, dirname, filename):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return True

    def finish(self):
        pass

    def abortOnFinding(self, dirname, filename):
        for candidate in self.may_fail:
            if self._match(dirname, filename, candidate):
                return False

        return True

    def getExtraFlags(self, dirname, filename):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return []

    def mayFailFor(self, *names):
        self.may_fail += names

    @classmethod
    def _match(cls, dirname, filename, candidate):
        parts = [dirname, filename]

        while None in parts:
            parts.remove(None)
        assert parts

        path = os.path.join(*parts)

        candidates = (
            dirname,
            filename,
            filename.replace(".py", ""),
            filename.split(".")[0],
            path,
            path.replace(".py", ""),
        )

        candidate2 = os.path.relpath(
            candidate, os.path.dirname(sys.modules["__main__"].__file__)
        )

        return candidate.rstrip("/") in candidates or candidate2 in candidates

    def exit(self, message):
        # Virtual method, pylint: disable=no-self-use
        sys.exit(message)

    def isCoverage(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def onErrorDetected(self, message):
        self.exit(message)


class SearchModeImmediate(SearchModeBase):
    pass


class SearchModeByPattern(SearchModeBase):
    def __init__(self, start_at):
        SearchModeBase.__init__(self)

        self.active = False
        self.start_at = start_at

    def consider(self, dirname, filename):
        if self.active:
            return True

        self.active = self._match(dirname, filename, self.start_at)
        return self.active

    def finish(self):
        if not self.active:
            sys.exit("Error, became never active.")


class SearchModeResume(SearchModeBase):
    def __init__(self, tests_path):
        SearchModeBase.__init__(self)

        tests_path = os.path.normcase(os.path.abspath(tests_path))
        version = sys.version

        if str is not bytes:
            tests_path = tests_path.encode("utf8")
            version = version.encode("utf8")

        case_hash = hashlib.md5(tests_path)
        case_hash.update(version)

        from .Common import getTestingCacheDir

        cache_filename = os.path.join(getTestingCacheDir(), case_hash.hexdigest())

        self.cache_filename = cache_filename

        if os.path.exists(cache_filename):
            with open(cache_filename, "r") as f:
                self.resume_from = f.read() or None
        else:
            self.resume_from = None

        self.active = not self.resume_from

    def consider(self, dirname, filename):
        parts = [dirname, filename]

        while None in parts:
            parts.remove(None)
        assert parts

        path = os.path.join(*parts)

        if self.active:
            with open(self.cache_filename, "w") as f:
                f.write(path)

            return True

        if areSamePaths(path, self.resume_from):
            self.active = True

        return self.active

    def finish(self):
        os.unlink(self.cache_filename)
        if not self.active:
            sys.exit("Error, became never active, restarting next time.")


class SearchModeCoverage(SearchModeBase):
    def getExtraFlags(self, dirname, filename):
        return ["coverage"]

    def isCoverage(self):
        return True


class SearchModeOnly(SearchModeByPattern):
    def __init__(self, start_at):
        SearchModeByPattern.__init__(self, start_at=start_at)

        self.done = False

    def consider(self, dirname, filename):
        if self.done:
            return False
        else:
            active = SearchModeByPattern.consider(
                self, dirname=dirname, filename=filename
            )

            if active:
                self.done = True

            return active


class SearchModeAll(SearchModeBase):
    def __init__(self):
        SearchModeBase.__init__(self)
        self.total_errors = 0

    def updateTotalErrors(self):
        self.total_errors += 1

    def onErrorDetected(self, message):
        self.updateTotalErrors()

    def finish(self):
        self.exit("Total " + str(self.total_errors) + " error(s) found.")
