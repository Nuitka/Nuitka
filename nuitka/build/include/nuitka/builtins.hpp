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
#ifndef __NUITKA_BUILTINS_H__
#define __NUITKA_BUILTINS_H__

extern PyModuleObject *_module_builtin;

class PythonBuiltin
{
    public:
        explicit PythonBuiltin( PyObject **name )
        {
            this->name = (Nuitka_StringObject **)name;
            this->value = NULL;
        }

        PyObject *asObject()
        {
            if ( this->value == NULL )
            {
                PyDictEntry *entry = GET_PYDICT_ENTRY(
                    _module_builtin,
                    *this->name
                );

                this->value = entry->me_value;
            }

            assertObject( this->value );

            return this->value;
        }

        void refresh( void )
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY(
                _module_builtin,
                *this->name
            );

            this->value = entry->me_value;
        }

        template<typename... P>
        PyObject *call( P...eles )
        {
            return CALL_FUNCTION(
                this->asObject(),
                PyObjectTemporary( MAKE_TUPLE( eles... ) ).asObject(),
                NULL
            );
        }

    private:

        PythonBuiltin( PythonBuiltin const &  ) = delete;

        Nuitka_StringObject **name;
        PyObject *value;
};

#endif
