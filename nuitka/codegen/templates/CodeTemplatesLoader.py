#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Templates for the loading of embedded modules.

"""


template_metapath_loader_compiled_module_entry = """\
{ (char *)"%(module_name)s", MOD_INIT_NAME( %(module_identifier)s ), NULL, 0, NUITKA_COMPILED_MODULE },"""

template_metapath_loader_compiled_package_entry = """\
{ (char *)"%(module_name)s", MOD_INIT_NAME( %(module_identifier)s ), NULL, 0, NUITKA_PACKAGE_FLAG },"""

template_metapath_loader_shlib_module_entry = """\
{ (char *)"%(module_name)s", NULL, NULL, 0, NUITKA_SHLIB_FLAG },"""

template_metapath_loader_bytecode_module_entry = """\
{ (char *)"%(module_name)s", NULL, %(bytecode)s, %(size)d, %(flags)s },"""


template_metapath_loader_body = """\
/* Code to register embedded modules for meta path based loading if any. */

#include "nuitka/unfreezing.hpp"

/* Table for lookup to find compiled or bytecode modules included in this
 * binary or module, or put along this binary as extension modules. We do
 * our own loading for each of these.
 */
%(metapath_module_decls)s
static struct Nuitka_MetaPathBasedLoaderEntry meta_path_loader_entries[] =
{
%(metapath_loader_inittab)s
    { NULL, NULL, 0 }
};

void setupMetaPathBasedLoader( void )
{
    static bool init_done = false;

    if ( init_done == false )
    {
        registerMetaPathBasedUnfreezer( meta_path_loader_entries );
        init_done = true;
    }
}
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
