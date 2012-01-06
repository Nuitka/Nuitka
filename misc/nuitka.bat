@echo off
rem     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
rem
rem     Part of "Nuitka", an optimizing Python compiler that is compatible and
rem     integrates with CPython, but also works on its own.
rem
rem     If you submit patches or make the software available to licensors of
rem     this software in either form, you automatically them grant them a
rem     license for your part of the code under "Apache License 2.0" unless you
rem     choose to remove this notice.
rem
rem     Kay Hayen uses the right to license his code under only GPL version 3,
rem     to discourage a fork of Nuitka before it is "finished". He will later
rem     make a new "Nuitka" release fully under "Apache License 2.0".
rem
rem     This program is free software: you can redistribute it and/or modify
rem     it under the terms of the GNU General Public License as published by
rem     the Free Software Foundation, version 3 of the License.
rem
rem     This program is distributed in the hope that it will be useful,
rem     but WITHOUT ANY WARRANTY; without even the implied warranty of
rem     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
rem     GNU General Public License for more details.
rem
rem     You should have received a copy of the GNU General Public License
rem     along with this program.  If not, see <http://www.gnu.org/licenses/>.
rem
rem     Please leave the whole of this copyright notice intact.
rem

setlocal

"%~dp0..\python" "%~dp0nuitka" %*

endlocal
