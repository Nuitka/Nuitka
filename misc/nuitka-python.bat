@echo off
rem
rem     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
rem
rem     Part of "Nuitka", an optimizing Python compiler that is compatible and
rem     integrates with CPython, but also works on its own.
rem
rem     If you submit Kay Hayen patches to this software in either form, you
rem     automatically grant him a copyright assignment to the code, or in the
rem     alternative a BSD license to the code, should your jurisdiction prevent
rem     this. Obviously it won't affect code that comes to him indirectly or
rem     code you don't submit to him.
rem
rem     This is to reserve my ability to re-license the code at a later time to
rem     the PSF. With this version of Nuitka, using it for a Closed Source and
rem     distributing the binary only is not allowed.
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

"%~dp0..\python" "%~dp0nuitka-python" %*

endlocal
