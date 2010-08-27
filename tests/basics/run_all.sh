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

for file in *.py
do
    if [ "$file" = "Referencing.py" ]
    then
        if [ -f /usr/bin/python-dbg ]
        then
            export PYTHON=python-dbg
        elif [ -f /usr/bin/python2.6-dbg ]
        then
            export PYTHON=python2.6-dbg
        else
            echo "Skip reference count test, CPython debug version not found."
            continue
        fi
    else
        unset PYTHON
    fi

    compare_with_cpython.sh $file silent

    if [ "$?" != 0 ]
    then
       echo "FAILED $file, run compare_with_cpython.sh $file"

       if [ "$1" = "search" ]
       then
           exit 1
       fi
    fi
done
