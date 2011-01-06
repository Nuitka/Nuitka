#!/bin/bash -e
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

BACKUP_PYTHONPATH=$PYTHONPATH

PACKAGE_LIST=(
    'nuitka'
    'nuitka/nodes'
    'nuitka/templates'
    'nuitka/optimizations'
)

echo "PASS 1: Compiling from compiler running from .py files."

for package in "${PACKAGE_LIST[@]}"
do
    source_dir="../../$package"
    target_dir="$package"
    mkdir -p $target_dir

    rm -f $target_dir/*.so

    for file in `ls $source_dir/*.py`
    do
        if [ `basename $file` != "__init__.py" ]
        then
            echo "Compiling $file"
            Nuitka.py $file --output-dir $target_dir $NUITKA_EXTRA_OPTIONS
        else
            cp $file $target_dir
        fi
    done
done

Nuitka.py ../../bin/Nuitka.py --output-dir . --exe $NUITKA_EXTRA_OPTIONS

compile() {
    nuitka=$1

    for package in "${PACKAGE_LIST[@]}"
    do
        source_dir="../../$package"

        for file in `ls $source_dir/*.py`
        do
            if [ `basename $file` != "__init__.py" ]
            then
                echo "Compiling $file"

                target="`basename $file .py`.build"

                rm -rf /tmp/$target

                $nuitka $file --output-dir /tmp/ $NUITKA_EXTRA_OPTIONS
                diff -rq $package/$target /tmp/$target

                rm -rf /tmp/$target
            fi
        done
    done
}

echo "PASS 2: Compiling from compiler running from .exe and many .so files."

export PYTHONPATH=.
compile ./Nuitka.exe

# Remove the .so compiler again, so it cannot confuse the later steps.
PYTHONPATH=$BACKUP_PYTHONPATH
find nuitka -name \*.so -exec rm {} \;
rm Nuitka.exe

echo "PASS 3: Compiling from compiler running from .py files to single .exe."
rm -rf /tmp/Nuitka.exe /tmp/Nuitka.build
Nuitka.py ../../bin/Nuitka.py --output-dir /tmp/ --exe --deep

echo "PASS 4: Compiling the compiler running from single exe"
# Set PYTHONPATH to local again, because nothings here right now and the single exe
# compiler shouldn't be allowed to import the .py files.
PYTHONPATH=.
compile /tmp/Nuitka.exe
