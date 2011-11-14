#!/bin/bash
#
#     Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are in the public domain. It is at least Free Software
#     where it's copied from other people. In these cases, it will normally be
#     indicated.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     Please leave the whole of this copyright notice intact.
#

cd `dirname $0`

if [ "$PYTHON" = "" ]
then
    export PYTHON=python
fi

for dir_name in `find . -maxdepth 1 -mindepth 1 -type d | xargs echo`
do
    echo "Consider: $dir_name"

    cd $dir_name

    NUITKA_EXTRA_OPTIONS="$NUITKA_EXTRA_OPTIONS --deep" compare_with_cpython *Main.py silent
    EXIT_CODE=$?

    cd - 2>/dev/null

    if [ "$EXIT_CODE" != 0 ]
    then
       echo "FAILED $dir_name, run compare_with_cpython manually"

       if [ "$1" = "search" ]
       then
           exit 1
       fi
    fi
done
