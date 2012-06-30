#!/bin/bash -e
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

MODULE=$1

if [ "$NUITKA_BINARY" = "" ]
then
    NUITKA_BINARY=nuitka
fi

OUTPUT="/tmp/`basename $MODULE .py`.exe"
rm -f $OUTPUT

$NUITKA_BINARY --exe --output-dir=/tmp/ --unstriped $NUITKA_EXTRA_OPTIONS $1

if [ ! -f $OUTPUT ]
then
    echo "Seeming failure of Nuitka to compile."
fi

LOGFILE="/tmp/`basename $MODULE .py`.log"
VALGRIND_OPTIONS="-q --tool=callgrind --callgrind-out-file=$LOGFILE --zero-before=init__main__"

echo -n "SIZE="
du -b $OUTPUT | sed 's/\t.*//'

valgrind $VALGRIND_OPTIONS $OUTPUT

if [ "$2" = "number" ]
then
    echo -n "TICKS="
    grep $LOGFILE  -e '^summary: ' | cut -d' ' -f2
else
    kcachegrind 2>/dev/null 1>/dev/null $LOGFILE &
fi
