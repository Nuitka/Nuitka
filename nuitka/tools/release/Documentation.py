#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Generation of Nuitka documentation."""

import os
import sys

from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.Download import getDownloadMode
from nuitka.utils.Execution import check_call, withEnvironmentVarOverridden
from nuitka.utils.FileOperations import (
    getFileContents,
    getFileList,
    openTextFile,
    putTextFileContents,
    replaceFileAtomic,
)
from nuitka.utils.PrivatePipSpace import tryDownloadPackageName


def _optimizePNGs(pngList):
    for png in pngList:
        check_call(["optipng", "-quiet", "-o2", "%s.png" % png])


def makeLogoImages():
    basePathLogo = "doc/Logo/Nuitka-Logo-%s"

    for logo in ("Vertical", "Symbol", "Horizontal"):
        cmd = "convert -background none %s.svg %s.png" % (basePathLogo, basePathLogo)
        check_call((cmd % (logo, logo)).split())

    _optimizePNGs(
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
        }.items():
            check_call((cmd % (icon, size)).split())


# spell-checker: ignore asciinema,automodule,postlist,toctree
extra_rst_keywords = (
    b"asciinema",
    b"postlist",
    b"post",
    b"youtube",
    b"grid",
    b"toctree",
    b"automodule",
    b"dropdown",
    b"rst-class",
    b"carousel",
    b"carousel-content",
    b"carousel-container",
    b"carousel-side-tab",
)
extra_rst_keywords = tuple(sorted(extra_rst_keywords, key=len, reverse=True))


def ensureRstLintInstalled(assume_yes_for_downloads):
    """Ensure that the modules for checking RST documents are available.

    Notes:
        Restructuredtext-lint is not a general Nuitka dependency, so it is
        downloaded into the private pip space when needed, rather than
        requiring a global installation for release tools.

    Args:
        assume_yes_for_downloads: bool, whether downloads may happen without
            asking.
    """
    download_mode = getDownloadMode(assume_yes_for_downloads)

    # Pygments has to be available before docutils is imported, since it
    # decides at import time whether code block analysis is supported.
    for module_name, reject_message in (
        (
            "pygments",
            "Pygments is needed for RST code block analysis.",
        ),
        (
            "restructuredtext_lint",
            "Restlint is needed for checking documentation.",
        ),
    ):
        try:
            __import__(module_name)
        except ImportError:
            site_packages_folder, download_mode = tryDownloadPackageName(
                logger=tools_logger,
                package_name=module_name,
                module_name=module_name,
                package_version=None,
                force_update=False,
                download_mode=download_mode,
                reject_message=reject_message,
            )

            if site_packages_folder is not None:
                sys.path.insert(0, site_packages_folder)

    try:
        __import__("restructuredtext_lint")
    except ImportError:
        return tools_logger.sysexit(
            "Error, failed to install 'restructuredtext_lint' into the private pip space."
        )


def checkRstLint(document):
    contents = getFileContents(document, mode="rb")

    for keyword in extra_rst_keywords:
        contents = contents.replace(b".. %s::" % keyword, b".. raw:: %s" % keyword)

    import restructuredtext_lint  # pylint: disable=I0021,import-error

    my_print("Checking '%s' for proper restructured text ..." % document, style="blue")
    lint_results = restructuredtext_lint.lint(
        contents.decode("utf8"),
        document,
    )

    lint_error = False
    for lint_result in lint_results:
        # Not an issue.
        if lint_result.message.startswith("Duplicate implicit target name:"):
            continue

        # We switched to raw, but attributes will still bne unknown.
        if lint_result.message.startswith(
            'Error in "raw" directive:\nunknown option: "hidden"'
        ):
            continue
        if lint_result.message.startswith(
            'Error in "raw" directive:\nunknown option: "excerpts"'
        ):
            continue
        if lint_result.message.startswith(
            'Error in "raw" directive:\nunknown option: "members"'
        ):
            continue

        my_print(lint_result, style="yellow")
        lint_error = True

    if lint_error:
        sys.exit("Error, no lint clean rest.")

    my_print("OK.", style="blue")


def _fixupManPageContents(manpage_filename):
    manpage_contents = getFileContents(manpage_filename).splitlines()

    for month in (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ):
        manpage_contents[1] = manpage_contents[1].replace(month + " ", "")
    manpage_contents[1] = manpage_contents[1].replace("rc0", "")

    new_contents = []
    mark = False

    for count, line in enumerate(manpage_contents):
        if line.startswith(
            (
                "Python:",
                "Commercial:",
                "Flavor:",
                "Executable:",
                "OS:",
                "Arch:",
                "Distribution:",
                "Version C compiler:",
            )
        ):
            continue

        if mark:
            line = ".SS " + line + ".BR\n"
            mark = False
        elif line == ".IP\n" and manpage_contents[count + 1].endswith(":\n"):
            mark = True
            continue

        if line == r"\fB\-\-g\fR++\-only" + "\n":
            line = r"\fB\-\-g\++\-only\fR" + "\n"

        new_contents.append(line)

    putTextFileContents(manpage_filename, contents=new_contents)


def updateManPages():
    with withEnvironmentVarOverridden("NUITKA_MANPAGE_GEN", "1"):
        if not os.path.exists("man"):
            os.mkdir("man")

        cmd = [
            "help2man",
            "-n",
            "the Python compiler",
            "--no-discard-stderr",
            "--no-info",
            "--include",
            "doc/nuitka-man-include.txt",
            "%s ./bin/nuitka --help-plugins" % sys.executable,
        ]

        with openTextFile(os.path.join("doc", "nuitka.1.tmp"), "wb") as output:
            check_call(cmd, stdout=output)
        _fixupManPageContents("doc/nuitka.1.tmp")
        replaceFileAtomic("doc/nuitka.1.tmp", "doc/nuitka.1")

        cmd[-1] = "%s ./bin/nuitka-run --help-plugins" % sys.executable
        with openTextFile(os.path.join("doc", "nuitka-run.1.tmp"), "wb") as output:
            check_call(cmd, stdout=output)
        _fixupManPageContents("doc/nuitka-run.1.tmp")
        replaceFileAtomic("doc/nuitka-run.1.tmp", "doc/nuitka-run.1")


def checkReleaseDocumentation(assume_yes_for_downloads):
    ensureRstLintInstalled(assume_yes_for_downloads=assume_yes_for_downloads)

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
