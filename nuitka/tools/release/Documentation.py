#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import os
import subprocess
import sys

from nuitka.utils.FileOperations import getFileList


def optimize_pngs(pngList):
    for png in pngList:
        subprocess.check_call(['optipng', '-o2', '%s.png' % png])


def makeLogoImages():
    basePathLogo = "doc/Logo/Nuitka-Logo-%s"

    try:
        for logo in ("Vertical", "Symbol", "Horizontal"):
            cmd = "convert -background none %s.svg %s.png" % (basePathLogo,
                                                              basePathLogo)
            subprocess.check_call((cmd % (logo, logo)).split())
    except OSError:
        sys.exit("Could not execute convert. Is it installed?")

    try:
        optimize_pngs([basePathLogo % item for item in
                      ("Vertical", "Symbol", "Horizontal")])
    except OSError:
        sys.exit("Could not execute optipng. Is it installed?")

    if os.path.exists("../nikola-site"):
        cmd = "convert -resize %s doc/Logo/Nuitka-Logo-Symbol.svg %s"
        for icon, size in {
                "../nikola-site/files/favicon.ico": "32x32",
                "../nikola-site/files/favicon.png": "32x32",
                "../nikola-site/files/apple-touch-icon-ipad.png": "72x72",
                "../nikola-site/files/apple-touch-icon-ipad3.png": "144x144",
                "../nikola-site/files/apple-touch-icon-iphone.png": "57x57",
                "../nikola-site/files/apple-touch-icon-iphone4.png": "114x114",
                }:
            subprocess.check_call((cmd % (icon, size)).split())


def checkRstLint(document):
    import restructuredtext_lint  # pylint: disable=I0021,import-error

    print("Checking %r for proper restructed text ..." % document)
    lint_results = restructuredtext_lint.lint_file(document, encoding="utf8")

    lint_error = False
    for lint_result in lint_results:
        # Not an issue.
        if lint_result.message.startswith("Duplicate implicit target name:"):
            continue

        print(lint_result)
        lint_error = True

    if lint_error:
        sys.exit("Error, no lint clean rest.")

    print("OK.")


def makeManpages():
    if not os.path.exists("man"):
        os.mkdir("man")

    def makeManpage(python, suffix):
        cmd = ["help2man", "-n", "'the Python compiler'",
               "--no-discard-stderr",
               "--no-info", "--include doc/nuitka-man-include.txt",
               "'%s ./bin/nuitka'" % python, ">doc/nuitka%s.1" % suffix]
        subprocess.check_call(cmd)

        cmd[-1] = ">doc/nuitka%s-run.1" % suffix
        subprocess.check_call(cmd)

        for manpage in ("doc/nuitka%s.1" % suffix,
                        "doc/nuitka%s-run.1" % suffix):
            with open(manpage) as f:
                manpage_contents = f.readlines()
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

            with open(manpage, "w") as f:
                f.writelines(new_contents)

    try:
        makeManpage("python2", "")
        makeManpage("python3", "3")
    except OSError:
        sys.exit("Could not execute help2man. Is it installed?")


def createRstPDF(document, args):
    try:
        subprocess.check_call(
            "rst2pdf %s  %s" % (" ".join(args), document), shell=True)
    except OSError:
        sys.exit("Could not execute rst2pdf. Is it installed?")


def createReleaseDocumentation():
    checkReleaseDocumentation()

    for document in ("README.rst", "Developer_Manual.rst", "Changelog.rst"):
        args = []

        if document != "Changelog.rst":
            args.append("-s doc/page-styles.txt")

            args.append('--header="###Title### - ###Section###"')
            args.append('--footer="###Title### - page ###Page### - ###Section###"')

        createRstPDF(document, args)

    if os.name != "nt":
        makeManpages()


def checkReleaseDocumentation():
    documents = [
        entry
        for entry in getFileList(".")
        if entry.endswith(".rst") and not entry.startswith("web" + os.path.sep)
    ]

    for document in ("README.rst", "Developer_Manual.rst", "Changelog.rst"):
        assert document in documents, documents

    for document in documents:
        checkRstLint(document)
