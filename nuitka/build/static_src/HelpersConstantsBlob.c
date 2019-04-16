//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
//
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
//

/** Providing access to the constants binary blob.
 *
 * There are multiple ways, the constants binary is accessed, and its
 * definition depends on how that is done.
 *
 * This deals with loading the resource from a DLL under Windows.
 *
 */

#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)

#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
unsigned char const *constant_bin = NULL;
#endif

void loadConstantsResource() {

#ifdef _NUITKA_EXE
    // Using NULL as this indicates running program.
    HMODULE handle = NULL;
#else
    HMODULE handle = getDllModuleHandle();
#endif

    constant_bin =
        (const unsigned char *)LockResource(LoadResource(handle, FindResource(handle, MAKEINTRESOURCE(3), RT_RCDATA)));

    assert(constant_bin);
}
#endif
