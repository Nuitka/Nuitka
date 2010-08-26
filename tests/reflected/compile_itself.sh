#!/bin/sh -e
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

echo "PASS 1: Compiling from compiler running from .py files."

if [ "$1" != "quick" ]
then
    rm -f tests/reflected/*.so

    for file in `ls src/*.py`
    do
        echo "Compiling $file"

        Nuitka.py $file --output-dir tests/reflected/
    done

    mkdir -p tests/reflected/nodes
    rm -f tests/reflected/nodes/*.so

    for file in `ls src/nodes/*.py`
    do
        if [ $file != "src/nodes/__init__.py" ]
        then
            echo "Compiling $file"

            Nuitka.py $file --output-dir tests/reflected/nodes
        fi
    done

    cp src/nodes/__init__.py tests/reflected/nodes/

    mkdir -p tests/reflected/templates
    rm -f tests/reflected/templates/*.so

    for file in `ls src/templates/*.py`
    do
        if [ $file != "src/templates/__init__.py" ]
        then
            echo "Compiling $file"

            Nuitka.py $file --output-dir tests/reflected/templates
        fi
    done

    cp src/templates/__init__.py tests/reflected/templates/

    Nuitka.py bin/Nuitka.py --output-dir tests/reflected/ --exe
else
    echo "Skipped."
fi

echo "PASS 2: Compiling from compiler running from .py files to single .exe."

Nuitka.py bin/Nuitka.py --output-dir /tmp/ --exe --deep

echo "PASS 3: Compiling from compiler running from .exe and many .so files."

for file in `ls src/*.py`
do
    echo "Compiling $file"

    rm -f /tmp/`basename $file .py`.c++

    export PYTHONPATH=tests/reflected
    ./tests/reflected/Nuitka.exe $file --output-dir /tmp/
    diff -sq ./tests/reflected/`basename $file .py`.c++ /tmp/`basename $file .py`.c++

    unset PYTHONPATH
    /tmp/Nuitka.exe $file --output-dir /tmp/
    diff -sq ./tests/reflected/`basename $file .py`.c++ /tmp/`basename $file .py`.c++
done

for file in `ls src/nodes/*.py`
do
    if [ $file != "src/nodes/__init__.py" ]
    then
        echo "Compiling $file"

        rm -f /tmp/`basename $file .py`.c++

        export PYTHONPATH=tests/reflected
        ./tests/reflected/Nuitka.exe $file --output-dir /tmp/
        diff -sq ./tests/reflected/nodes/`basename $file .py`.c++ /tmp/`basename $file .py`.c++

        unset PYTHONPATH
        /tmp/Nuitka.exe $file --output-dir /tmp/
        diff -sq ./tests/reflected/nodes/`basename $file .py`.c++ /tmp/`basename $file .py`.c++
    fi
done

for file in `ls src/templates/*.py`
do
    if [ $file != "src/templates/__init__.py" ]
    then
        echo "Compiling $file"

        rm -f /tmp/`basename $file .py`.c++

        export PYTHONPATH=tests/reflected
        ./tests/reflected/Nuitka.exe $file --output-dir /tmp/
        diff -sq ./tests/reflected/templates/`basename $file .py`.c++ /tmp/`basename $file .py`.c++

        unset PYTHONPATH
        /tmp/Nuitka.exe $file --output-dir /tmp/
        diff -sq ./tests/reflected/templates/`basename $file .py`.c++ /tmp/`basename $file .py`.c++
    fi
done
