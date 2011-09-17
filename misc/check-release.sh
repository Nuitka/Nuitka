#!/bin/bash -e
#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#

execute_tests()
{
    echo "Executing test case called $1 with Python $2 and flags '$3'."

    export PYTHON=$2

    export TMP_DIR=/tmp/$1
    mkdir -p $TMP_DIR

    export NUITKA_EXTRA_OPTIONS="$3 --output-dir=$TMP_DIR"

    echo "Running the basic tests with options '$3' with $PYTHON:"
    ./tests/basics/run_all.sh search

    echo "Running the program tests with options '$3' with $PYTHON:"
    ./tests/programs/run_all.sh search

    export TMP_DIR=/tmp/$1/26
    mkdir -p $TMP_DIR

    export NUITKA_EXTRA_OPTIONS="$3 --output-dir=$TMP_DIR"

    echo "Running the CPython 2.6 tests with options '$3' with $PYTHON:"
    ./tests/CPython/run_all.sh search

    # Running the Python 2.7 test suite with CPython 2.6 gives little insight, because
    # "importlib" will not be there and that's it.
    if [ "$PYTHON" != "python2.6" ]
    then
        export TMP_DIR=/tmp/$1/27
        mkdir -p $TMP_DIR

        export NUITKA_EXTRA_OPTIONS="$3 --output-dir=$TMP_DIR"

        echo "Running the CPython 2.7 tests with options '$3' with $PYTHON:"
        ./tests/CPython27/run_all.sh search
    fi

    unset NUITKA_EXTRA_OPTIONS
}

command_exists () {
    type "$1" &> /dev/null ;
}

if command_exists python3.2
then
    python3.2 bin/Nuitka.py --version 2>/dev/null
else
    echo "Cannot execute Python 3.2 tests, not installed."
fi

execute_tests "python2.6-debug" "python2.6" "--debug"
execute_tests "python2.7-debug" "python2.7" "--debug"

execute_tests "python2.6-nodebug" "python2.6" ""
execute_tests "python2.7-nodebug" "python2.7" ""

echo "Running the reflection test in debug mode with $PYTHON:"
./tests/reflected/compile_itself.sh search

echo "OK."
