#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os
import subprocess
import sys

# Not really re-creating the images ever, cannot make sure they are binary
# identical, so made this optional.

if "logo" in sys.argv:
    assert 0 == os.system("convert -background none doc/Logo/Nuitka-Logo-Vertical.svg doc/images/Nuitka-Logo-Vertical.png")
    assert 0 == os.system("convert -background none doc/Logo/Nuitka-Logo-Symbol.svg doc/images/Nuitka-Logo-Symbol.png")
    assert 0 == os.system("convert -background none doc/Logo/Nuitka-Logo-Horizontal.svg doc/images/Nuitka-Logo-Horizontal.png")

    assert 0 == os.system("optipng -o2 doc/images/Nuitka-Logo-Vertical.png")
    assert 0 == os.system("optipng -o2 doc/images/Nuitka-Logo-Symbol.png")
    assert 0 == os.system("optipng -o2 doc/images/Nuitka-Logo-Horizontal.png")

    if os.path.exists("../nikola-site"):
        assert 0 == os.system("convert -resize 32x32 doc/Logo/Nuitka-Logo-Symbol.svg ../nikola-site/files/favicon.ico")
        assert 0 == os.system("convert -resize 32x32 doc/Logo/Nuitka-Logo-Symbol.svg ../nikola-site/files/favicon.png")

        assert 0 == os.system("convert -resize 72x72 doc/Logo/Nuitka-Logo-Symbol.svg ../nikola-site/files/apple-touch-icon-ipad.png")
        assert 0 == os.system("convert -resize 144x144 doc/Logo/Nuitka-Logo-Symbol.svg ../nikola-site/files/apple-touch-icon-ipad3.png")
        assert 0 == os.system("convert -resize 57x57 doc/Logo/Nuitka-Logo-Symbol.svg ../nikola-site/files/apple-touch-icon-iphone.png")
        assert 0 == os.system("convert -resize 114x114 doc/Logo/Nuitka-Logo-Symbol.svg ../nikola-site/files/apple-touch-icon-iphone4.png")


for document in ("README.rst", "Developer_Manual.rst", "Changelog.rst"):
    args = []

    if document != "Changelog.rst":
        args.append("-s doc/page-styles.txt")

        args.append('--header="###Title### - ###Section###"')
        args.append('--footer="###Title### - page ###Page### - ###Section###"')

    assert 0 == subprocess.call(
        "%(rst2pdf)s %(args)s  %(document)s" %
        {
            "rst2pdf"  : (
                "rst2pdf"
                    if os.name != "nt" else
                r"C:\Python27_32\Scripts\rst2pdf.exe"
            ),
            "args"     : ' '.join(args),
            "document" : document
        },
        shell = True
    ), document


if os.name != "nt":
    if not os.path.exists("man"):
        os.mkdir("man")

    assert 0 == subprocess.call("help2man -n 'the Python compiler' --no-discard-stderr --no-info --include doc/nuitka-man-include.txt ./bin/nuitka >doc/nuitka.1", shell = True)
    assert 0 == subprocess.call("help2man -n 'the Python compiler' --no-discard-stderr --no-info ./bin/nuitka-run >doc/nuitka-run.1", shell = True)

    for manpage in ("doc/nuitka.1", "doc/nuitka-run.1"):
        manpage_contents = open(manpage).readlines()
        new_contents = []
        mark = False

        for count, line in enumerate(manpage_contents):
            if mark:
                line = ".SS " + line + ".BR\n"
                mark = False
            elif line == ".IP\n" and manpage_contents[ count + 1 ].endswith(":\n"):
                mark = True
                continue

            if line == r"\fB\-\-g\fR++\-only" + '\n':
                line = r"\fB\-\-g\++\-only\fR" + '\n'

            new_contents.append(line)

        open(manpage, 'w').writelines(new_contents)
