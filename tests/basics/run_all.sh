#!/bin/bash
# 
#     Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Python test that I originally created or extracted from other peoples
#     work. I put my parts of it in the public domain. It is at least Free
#     Software where it's copied from other people. In these cases, I will
#     indicate it.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the new code, or in the alternative
#     a BSD license to the new code, should your jurisdiction prevent this. This
#     is to reserve my ability to re-license the code at any time.
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
done
