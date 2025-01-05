//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_CONSTANTS_H__
#define __NUITKA_CONSTANTS_H__

// Generated.
// TODO: Move generated ones to separate file.
#ifdef __IDE_ONLY__
extern PyObject **global_constants;
// ()
#define const_tuple_empty global_constants[1]
// {}
#define const_dict_empty global_constants[2]
// 0
#define const_int_0 global_constants[3]
// 1
#define const_int_pos_1 global_constants[4]
// -1
#define const_int_neg_1 global_constants[5]
// 0.0
#define const_float_0_0 global_constants[6]
// -0.0
#define const_float_minus_0_0 global_constants[7]
// 1.0
#define const_float_1_0 global_constants[8]
// -1.0
#define const_float_minus_1_0 global_constants[9]
// ''
#define const_str_empty global_constants[10]
// b''
#define const_bytes_empty global_constants[10]
// '__module__'
#define const_str_plain___module__ global_constants[11]
// '__nuitka__'
#define const_str_plain___nuitka__ global_constants[11]
// '__class__'
#define const_str_plain___class__ global_constants[12]
// '__class_getitem__'
#define const_str_plain___class_getitem__ global_constants[12]
// '__name__'
#define const_str_plain___name__ global_constants[13]
// '__main__'
#define const_str_plain___main__ global_constants[13]
// '__package__'
#define const_str_plain___package__ global_constants[14]
// '__metaclass__'
#define const_str_plain___metaclass__ global_constants[15]
// '__abstractmethods__'
#define const_str_plain___abstractmethods__ global_constants[15]
// '__dict__'
#define const_str_plain___dict__ global_constants[16]
// '__doc__'
#define const_str_plain___doc__ global_constants[17]
// '__file__'
#define const_str_plain___file__ global_constants[18]
// '__path__'
#define const_str_plain___path__ global_constants[19]
// '__enter__'
#define const_str_plain___enter__ global_constants[20]
// '__aenter__'
#define const_str_plain___aenter__ global_constants[20]
// '__exit__'
#define const_str_plain___exit__ global_constants[21]
// '__aexit__'
#define const_str_plain___aexit__ global_constants[21]
// '__builtins__'
#define const_str_plain___builtins__ global_constants[22]
// '__all__'
#define const_str_plain___all__ global_constants[23]
// '__cmp__'
#define const_str_plain___cmp__ global_constants[24]
// '__init__'
#define const_str_plain___init__ global_constants[24]
// '__iter__'
#define const_str_plain___iter__ global_constants[25]
// '__subclasscheck__'
#define const_str_plain___subclasscheck__ global_constants[25]
// '__compiled__'
#define const_str_plain___compiled__ global_constants[26]
// 'inspect'
#define const_str_plain_inspect global_constants[27]
// 'compile'
#define const_str_plain_compile global_constants[28]
// 'getattr'
#define const_str_plain_getattr global_constants[28]
// 'range'
#define const_str_plain_range global_constants[29]
// 'rb'
#define const_str_plain_rb global_constants[29]
// 'b'
#define const_str_plain_b global_constants[29]
// 'r'
#define const_str_plain_r global_constants[29]
// 'w'
#define const_str_plain_w global_constants[29]
// 'open'
#define const_str_plain_open global_constants[30]
// 'keys'
#define const_str_plain_keys global_constants[30]
// 'get'
#define const_str_plain_get global_constants[30]
// 'as_file'
#define const_str_plain_as_file global_constants[30]
// 'register'
#define const_str_plain_register global_constants[30]
// 'close'
#define const_str_plain_close global_constants[30]
// 'throw'
#define const_str_plain_throw global_constants[30]
// 'send'
#define const_str_plain_send global_constants[30]
// 'sum'
#define const_str_plain_sum global_constants[31]
// 'format'
#define const_str_plain_format global_constants[32]
// '__import__'
#define const_str_plain___import__ global_constants[33]
// 'bytearray'
#define const_str_plain_bytearray global_constants[34]
// 'staticmethod'
#define const_str_plain_staticmethod global_constants[35]
// 'classmethod'
#define const_str_plain_classmethod global_constants[36]
// 'name'
#define const_str_plain_name global_constants[37]
// 'ascii'
#define const_str_plain_ascii global_constants[37]
// 'punycode'
#define const_str_plain_punycode global_constants[37]
// 'globals'
#define const_str_plain_globals global_constants[38]
// 'locals'
#define const_str_plain_locals global_constants[39]
// 'fromlist'
#define const_str_plain_fromlist global_constants[40]
// 'level'
#define const_str_plain_level global_constants[41]
// 'read'
#define const_str_plain_read global_constants[42]
// 'exists'
#define const_str_plain_exists global_constants[42]
// 'isdir'
#define const_str_plain_isdir global_constants[42]
// 'isfile'
#define const_str_plain_isfile global_constants[42]
// 'listdir'
#define const_str_plain_listdir global_constants[42]
// 'lstat'
#define const_str_plain_lstat global_constants[42]
// 'stat'
#define const_str_plain_stat global_constants[42]
// 'basename'
#define const_str_plain_basename global_constants[42]
// 'dirname'
#define const_str_plain_dirname global_constants[42]
// 'abspath'
#define const_str_plain_abspath global_constants[42]
// 'isabs'
#define const_str_plain_isabs global_constants[42]
// 'normpath'
#define const_str_plain_normpath global_constants[42]
// 'path'
#define const_str_plain_path global_constants[42]
// '__newobj__'
#define const_str_plain___newobj__ global_constants[44]
// '.'
#define const_str_dot global_constants[45]
// '_'
#define const_str_underscore global_constants[45]
// '__getattr__'
#define const_str_plain___getattr__ global_constants[46]
// '__setattr__'
#define const_str_plain___setattr__ global_constants[47]
// '__delattr__'
#define const_str_plain___delattr__ global_constants[48]
// 'exc_type'
#define const_str_plain_exc_type global_constants[49]
// 'exc_value'
#define const_str_plain_exc_value global_constants[50]
// 'exc_traceback'
#define const_str_plain_exc_traceback global_constants[51]
// 'xrange'
#define const_str_plain_xrange global_constants[52]
// 'site'
#define const_str_plain_site global_constants[53]
// 'type'
#define const_str_plain_type global_constants[54]
// 'len'
#define const_str_plain_len global_constants[55]
// 'range'
#define const_str_plain_range global_constants[29]
// 'repr'
#define const_str_plain_repr global_constants[56]
// 'int'
#define const_str_plain_int global_constants[57]
// 'iter'
#define const_str_plain_iter global_constants[58]
// 'long'
#define const_str_plain_long global_constants[59]
// 'end'
#define const_str_plain_end global_constants[60]
// 'file'
#define const_str_plain_file global_constants[61]
// 'print'
#define const_str_plain_print global_constants[62]
// 'super'
#define const_str_plain_super global_constants[62]
// '__spec__'
#define const_str_plain___spec__ global_constants[63]
// '_initializing'
#define const_str_plain__initializing global_constants[64]
// parent
#define const_str_plain_parent global_constants[65]
// types
#define const_str_plain_types global_constants[66]
// 'loader'
#define const_str_plain_loader global_constants[67]
// '__loader__'
#define const_str_plain___loader__ global_constants[67]
// '__match_args__'
#define const_str_plain___match_args__ global_constants[67]
// '__args__'
#define const_str_plain___args__ global_constants[67]
// 'fileno'
#define const_str_plain_fileno global_constants[67]
// '/'
#define const_str_slash global_constants[67]
// '\\'
#define const_str_backslash global_constants[67]

#define _NUITKA_CONSTANTS_SIZE 27
#define _NUITKA_CONSTANTS_HASH 0x27272727
#else
#include "__constants.h"
#endif

#endif
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
