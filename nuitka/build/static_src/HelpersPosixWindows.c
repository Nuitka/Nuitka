//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if defined(__CYGWIN__) || defined(__MSYS__)
#include <sys/cygwin.h>
#include <sys/mount.h>

static void ensurePosixWindowsMounts(void) {
    // Without a host Cygwin/MSYS2 installation, cygwin1.dll and msys-2.0.dll
    // derive '/' relative to the bundled DLL, so '/dev/shm' (required by
    // sem_open / multiprocessing) and '/tmp' do not exist. Mount them in
    // memory onto Windows temp storage; the mount table is inherited by
    // forked and spawned children.
    bool need_dev_shm = !isExistingDirectory("/dev/shm");
    bool need_tmp = !isExistingDirectory("/tmp");

    if (!need_dev_shm && !need_tmp) {
        return;
    }

    char const *temp_candidates[] = {
        getenv("TEMP"),
        getenv("TMP"),
        getenv("TMPDIR"),
    };

    char const *temp_posix = NULL;
    for (size_t i = 0; i < sizeof(temp_candidates) / sizeof(temp_candidates[0]); i++) {
        if (temp_candidates[i] != NULL && temp_candidates[i][0] != 0 && isExistingDirectory(temp_candidates[i])) {
            temp_posix = temp_candidates[i];
            break;
        }
    }

    char win_temp[MAXPATHLEN + 1];
    bool has_win_temp = false;

    if (temp_posix != NULL) {
        has_win_temp = cygwin_conv_path(CCP_POSIX_TO_WIN_A | CCP_ABSOLUTE, temp_posix, win_temp, sizeof(win_temp)) == 0;
    }

    if (!has_win_temp) {
        char const *windir = getenv("WINDIR");
        if (windir == NULL || windir[0] == 0) {
            windir = getenv("SYSTEMROOT");
        }

        if (windir != NULL && windir[0] != 0) {
            if (windir[0] == '/') {
                has_win_temp =
                    cygwin_conv_path(CCP_POSIX_TO_WIN_A | CCP_ABSOLUTE, windir, win_temp, sizeof(win_temp)) == 0;
            } else {
                copyStringSafe(win_temp, windir, sizeof(win_temp));
                has_win_temp = true;
            }

            if (has_win_temp) {
                appendStringSafe(win_temp, "\\Temp", sizeof(win_temp));
            }
        }

        if (!has_win_temp) {
            copyStringSafe(win_temp, "C:\\Windows\\Temp", sizeof(win_temp));
        }
    }

    if (need_dev_shm) {
        mount(win_temp, "/dev/shm", MOUNT_NOACL);
    }

    if (need_tmp) {
        mount(win_temp, "/tmp", MOUNT_NOACL);
    }
}
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
