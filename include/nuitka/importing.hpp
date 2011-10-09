//
//     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//
#ifndef __NUITKA_IMPORTING_H__
#define __NUITKA_IMPORTING_H__

extern PyObject *IMPORT_MODULE( PyObject *module_name, PyObject *import_name, PyObject *package, PyObject *import_items, int level );

extern void IMPORT_MODULE_STAR( PyObject *target, bool is_module, PyObject *module_name, PyObject *module );

// For the --deep mode, we need to use this variant, esp. if the modules are in packages,
// then we need to load it this way.
#ifdef _NUITKA_EXE
extern PyObject *IMPORT_EMBEDDED_MODULE( PyObject *module_name, PyObject *import_name );
#endif

#endif
