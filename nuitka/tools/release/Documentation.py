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
""" Generation of Nuitka documentation.

"""

import os
import sys

from nuitka.Tracing import my_print
from nuitka.utils.Execution import check_call
from nuitka.utils.FileOperations import (
    getFileContents,
    getFileList,
    openTextFile,
    putTextFileContents,
)
from nuitka.utils.Rest import createPDF


def optimize_pngs(pngList):
    for png in pngList:
        check_call(["optipng", "-o2", "%s.png" % png])


def makeLogoImages():
    basePathLogo = "doc/Logo/Nuitka-Logo-%s"

    for logo in ("Vertical", "Symbol", "Horizontal"):
        cmd = "convert -background none %s.svg %s.png" % (basePathLogo, basePathLogo)
        check_call((cmd % (logo, logo)).split())

    optimize_pngs(
        [basePathLogo % item for item in ("Vertical", "Symbol", "Horizontal")]
    )

    if os.path.exists("../Nuitka-website"):
        cmd = "convert -resize %s doc/Logo/Nuitka-Logo-Symbol.svg %s"
        for icon, size in {
            "../Nuitka-website/files/favicon.ico": "32x32",
            "../Nuitka-website/files/favicon.png": "32x32",
            "../Nuitka-website/doc/_static/favicon.ico": "32x32",
            "../Nuitka-website/doc/_static/favicon.png": "32x32",
            "../Nuitka-website/doc/_static/apple-touch-icon-ipad.png": "72x72",
            "../Nuitka-website/doc/_static/apple-touch-icon-ipad3.png": "144x144",
            "../Nuitka-website/doc/_static/apple-touch-icon-iphone.png": "57x57",
            "../Nuitka-website/doc/_static/apple-touch-icon-iphone4.png": "114x114",
            "../Nuitka-website/doc/_static/apple-touch-icon-180x180.png": "180x180",
        }:
            check_call((cmd % (icon, size)).split())


def checkRstLint(document):
    import restructuredtext_lint  # pylint: disable=I0021,import-error

    my_print("Checking %r for proper restructed text ..." % document, style="blue")
    lint_results = restructuredtext_lint.lint_file(document, encoding="utf8")

    lint_error = False
    for lint_result in lint_results:
        # Not an issue.
        if lint_result.message.startswith("Duplicate implicit target name:"):
            continue

        my_print(lint_result, style="yellow")
        lint_error = True

    if lint_error:
        sys.exit("Error, no lint clean rest.")

    my_print("OK.", style="blue")


def makeManpages():
    if not os.path.exists("man"):
        os.mkdir("man")

    def makeManpage(python, suffix):
        cmd = [
            "help2man",
            "-n",
            "the Python compiler",
            "--no-discard-stderr",
            "--no-info",
            "--include",
            "doc/nuitka-man-include.txt",
            "%s ./bin/nuitka" % python,
        ]

        with openTextFile("doc/nuitka%s.1" % suffix, "wb") as output:
            check_call(cmd, stdout=output)
        cmd[-1] += "-run"
        with openTextFile("doc/nuitka%s-run.1" % suffix, "wb") as output:
            check_call(cmd, stdout=output)

        for manpage in ("doc/nuitka%s.1" % suffix, "doc/nuitka%s-run.1" % suffix):
            manpage_contents = getFileContents(manpage).splitlines()

            new_contents = []
            mark = False

            for count, line in enumerate(manpage_contents):
                if mark:
                    line = ".SS " + line + ".BR\n"
                    mark = False
                elif line == ".IP\n" and manpage_contents[count + 1].endswith(":\n"):
                    mark = True
                    continue

                if line == r"\fB\-\-g\fR++\-only" + "\n":
                    line = r"\fB\-\-g\++\-only\fR" + "\n"

                new_contents.append(line)

            putTextFileContents(manpage, contents=new_contents)

    makeManpage("python2", "2")
    makeManpage("python3", "3")


def createReleaseDocumentation():
    checkReleaseDocumentation()

    for document in ("README.rst", "Developer_Manual.rst", "Changelog.rst"):
        createPDF(document)

    if os.name != "nt":
        makeManpages()


def checkReleaseDocumentation():
    documents = [
        entry
        for entry in getFileList(".")
        if entry.endswith(".rst") and not entry.startswith("web" + os.path.sep)
        if "inline_copy" not in entry
    ]

    for document in ("README.rst", "Developer_Manual.rst", "Changelog.rst"):
        assert document in documents, documents

    for document in documents:
        checkRstLint(document)
