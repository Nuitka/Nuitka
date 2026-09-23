//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_CONSTANTS_H__
#define __NUITKA_CONSTANTS_H__

#ifdef __IDE_ONLY__
#include "nuitka/cpython_api_compat.h"
#endif

// Generated.
// TODO: Move generated ones to separate file.
#ifdef __IDE_ONLY__
// The global constants are populated dynamically for each program and their
// array positions are not fixed. Only the names matter for IDE parsing, so a
// dummy index is used. The order follows 'getConstantDefaultPopulation' in
// 'nuitka/code_generation/GlobalConstants.py'.
extern PyObject **global_constants;
// ()
#define const_tuple_empty global_constants[0]
// {}
#define const_dict_empty global_constants[0]
// 0
#define const_int_0 global_constants[0]
// 1
#define const_int_pos_1 global_constants[0]
// -1
#define const_int_neg_1 global_constants[0]
// 0.0
#define const_float_0_0 global_constants[0]
// -0.0
#define const_float_minus_0_0 global_constants[0]
// 1.0
#define const_float_1_0 global_constants[0]
// -1.0
#define const_float_minus_1_0 global_constants[0]
// 0L (Python2)
#define const_long_0 global_constants[0]
// ''
#define const_str_empty global_constants[0]
// b''
#define const_bytes_empty global_constants[0]
// '<module>'
#define const_str_angle_module global_constants[0]
// '<genexpr>'
#define const_str_angle_genexpr global_constants[0]
#define const_str_plain___module__ global_constants[0]
#define const_str_plain___class__ global_constants[0]
#define const_str_plain___name__ global_constants[0]
#define const_str_plain___package__ global_constants[0]
#define const_str_plain___bases__ global_constants[0]
#define const_str_plain___metaclass__ global_constants[0]
#define const_str_plain___abstractmethods__ global_constants[0]
#define const_str_plain___closure__ global_constants[0]
#define const_str_plain___instancecheck__ global_constants[0]
#define const_str_plain___dict__ global_constants[0]
#define const_str_plain___doc__ global_constants[0]
#define const_str_plain___file__ global_constants[0]
#define const_str_plain___path__ global_constants[0]
#define const_str_plain___enter__ global_constants[0]
#define const_str_plain___exit__ global_constants[0]
#define const_str_plain___builtins__ global_constants[0]
#define const_str_plain___all__ global_constants[0]
#define const_str_plain___init__ global_constants[0]
#define const_str_plain___cmp__ global_constants[0]
#define const_str_plain___iter__ global_constants[0]
#define const_str_plain___loader__ global_constants[0]
#define const_str_plain___compiled__ global_constants[0]
#define const_str_plain___nuitka__ global_constants[0]
#define const_str_plain_inspect global_constants[0]
#define const_str_plain_compile global_constants[0]
#define const_str_plain_range global_constants[0]
#define const_str_plain_open global_constants[0]
#define const_str_plain_super global_constants[0]
#define const_str_plain_sum global_constants[0]
#define const_str_plain_format global_constants[0]
#define const_str_plain___import__ global_constants[0]
#define const_str_plain_bytearray global_constants[0]
#define const_str_plain_staticmethod global_constants[0]
#define const_str_plain_classmethod global_constants[0]
#define const_str_plain_keys global_constants[0]
#define const_str_plain_get global_constants[0]
#define const_str_plain_name global_constants[0]
#define const_str_plain_globals global_constants[0]
#define const_str_plain_locals global_constants[0]
#define const_str_plain_fromlist global_constants[0]
#define const_str_plain_level global_constants[0]
#define const_str_plain_read global_constants[0]
#define const_str_plain_rb global_constants[0]
#define const_str_plain_r global_constants[0]
#define const_str_plain_w global_constants[0]
#define const_str_plain_b global_constants[0]
#define const_str_plain_lower global_constants[0]
// '/'
#define const_str_slash global_constants[0]
// '\\'
#define const_str_backslash global_constants[0]
#define const_str_plain_path global_constants[0]
#define const_str_plain_basename global_constants[0]
#define const_str_plain_dirname global_constants[0]
#define const_str_plain_abspath global_constants[0]
#define const_str_plain_isabs global_constants[0]
#define const_str_plain_normpath global_constants[0]
#define const_str_plain_exists global_constants[0]
#define const_str_plain_isdir global_constants[0]
#define const_str_plain_isfile global_constants[0]
#define const_str_plain_listdir global_constants[0]
#define const_str_plain_stat global_constants[0]
#define const_str_plain_lstat global_constants[0]
#define const_str_plain_close global_constants[0]
#define const_str_plain___newobj__ global_constants[0]
#define const_str_plain_getattr global_constants[0]
#define const_str_plain___cached__ global_constants[0]
#define const_str_plain_print global_constants[0]
#define const_str_plain_end global_constants[0]
#define const_str_plain_file global_constants[0]
#define const_str_plain_bytes global_constants[0]
// '.'
#define const_str_dot global_constants[0]
// '_'
#define const_str_underscore global_constants[0]
#define const_str_plain___annotations__ global_constants[0]
#define const_str_plain_send global_constants[0]
#define const_str_plain_throw global_constants[0]
#define const_str_plain___getattr__ global_constants[0]
#define const_str_plain___setattr__ global_constants[0]
#define const_str_plain___delattr__ global_constants[0]
#define const_str_plain_exc_type global_constants[0]
#define const_str_plain_exc_value global_constants[0]
#define const_str_plain_exc_traceback global_constants[0]
#define const_str_plain_join global_constants[0]
#define const_str_plain_xrange global_constants[0]
#define const_str_plain_site global_constants[0]
#define const_str_plain_type global_constants[0]
#define const_str_plain_len global_constants[0]
#define const_str_plain_repr global_constants[0]
#define const_str_plain_int global_constants[0]
#define const_str_plain_iter global_constants[0]
#define const_str_plain_long global_constants[0]
#define const_str_plain___spec__ global_constants[0]
#define const_str_plain__initializing global_constants[0]
#define const_str_plain_parent global_constants[0]
#define const_str_plain_types global_constants[0]
#define const_str_plain_ascii global_constants[0]
#define const_str_plain_punycode global_constants[0]
#define const_str_plain___await__ global_constants[0]
#define const_str_plain___main__ global_constants[0]
#define const_str_plain_loader global_constants[0]
#define const_str_plain___classcell__ global_constants[0]
#define const_str_plain_as_file global_constants[0]
#define const_str_plain_register global_constants[0]
#define const_str_plain___class_getitem__ global_constants[0]
#define const_str_plain_reconfigure global_constants[0]
#define const_str_plain_encoding global_constants[0]
#define const_str_plain_line_buffering global_constants[0]
#define const_str_plain___match_args__ global_constants[0]
#define const_str_plain___args__ global_constants[0]
#define const_str_plain___aenter__ global_constants[0]
#define const_str_plain___aexit__ global_constants[0]
#define const_str_plain_derive global_constants[0]
#define const_str_plain_split global_constants[0]
#define const_str_plain___notes__ global_constants[0]
#define const_str_plain_Unpack global_constants[0]
#define const_str_plain_Mapping global_constants[0]
#define const_str_plain___qualname__ global_constants[0]
#define const_str_plain_fileno global_constants[0]
#define const_str_plain_args global_constants[0]

// Referenced by helper code, but not part of the default population on all
// versions or configurations.
#define const_str_plain___subclasscheck__ global_constants[0]
#define const_str_plain___dir__ global_constants[0]

#define _NUITKA_CONSTANTS_SIZE 27
#define _NUITKA_CONSTANTS_HASH 0x27272727
#else
#include "__constants.h"
#endif

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
