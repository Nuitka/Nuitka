#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tools for profiling.

Currently using perf kernel interface for native Linux are the only thing exposed,
they don't work inside of containers though, or with default security settings.

Execute that setting permanent weaker:
echo 'kernel.perf_event_paranoid = 1' | sudo tee /etc/sysctl.d/99-nuitka-perf.conf
sudo sysctl --system

Temporary:
sudo sh -c 'echo 1 > /proc/sys/kernel/perf_event_paranoid'

"""

from .Utils import isLinux

# isort: start

if not isLinux():
    # TODO: Windows and MacOS support need other solutions.

    def hasPerfProfilingSupport():
        return False

    PerfCounters = None

else:
    import ctypes
    import ctypes.util
    import fcntl  # Linux only, pylint: disable=I0021,import-error
    import os
    import platform
    import struct

    def hasPerfProfilingSupport():
        return isLinux() and getPerfFileHandle(PERF_COUNT_HW_INSTRUCTIONS) is not None

    # The syscall number for perf_event_open varies by architecture.
    ARCH_MAP = {
        "x86_64": 298,
        "i386": 336,
        "aarch64": 241,
        "armv7l": 364,
    }

    def getPerfFileHandle(config, group_fd=-1, read_format=0):
        SYS_perf_event_open = ARCH_MAP.get(platform.machine())

        if SYS_perf_event_open is None:
            # This is not a hard error, we just cannot do perf.
            return None

        # --- Load libc and define syscall function ---
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

        syscall = libc.syscall
        syscall.restype = ctypes.c_long

        attr = PerfEventAttr(
            type=PERF_TYPE_HARDWARE,
            size=ctypes.sizeof(PerfEventAttr),
            config=config,
            read_format=read_format,
            # flags for perf_event_open syscall:
            # Bit 0: disabled -> if set start in disabled state
            # Bit 17: exclude_kernel -> if set only count user space
            # Bit 18: exclude_hv -> if set exclude hypervisor
            flags=(1 << 0) | (1 << 17) | (1 << 18),
        )

        # We must explicitly cast every argument to its correct 64-bit C type to
        # satisfy the variadic nature of the syscall ABI.
        fd = syscall(
            ctypes.c_long(SYS_perf_event_open),
            ctypes.byref(attr),
            ctypes.c_long(0),  # pid
            ctypes.c_long(-1),  # cpu
            ctypes.c_long(group_fd),
            ctypes.c_long(0),  # flags
        )

        if fd < 0:
            return None

        return fd

    # See 'man perf_event_open' for details
    PERF_TYPE_HARDWARE = 0
    PERF_COUNT_HW_REF_CPU_CYCLES = 9
    PERF_COUNT_HW_INSTRUCTIONS = 1

    class _PerfEventAttrUnion(ctypes.Union):
        _fields_ = [
            ("sample_period", ctypes.c_uint64),
            ("sample_freq", ctypes.c_uint64),
        ]

    class PerfEventAttr(ctypes.Structure):
        # This structure must match the C structure, otherwise the kernel will
        # reject it with E2BIG, because the size field will not be what it
        # expects. spell-checker: ignore clockid,regs
        _fields_ = [
            ("type", ctypes.c_uint32),
            ("size", ctypes.c_uint32),
            ("config", ctypes.c_uint64),
            ("read_format", ctypes.c_uint64),
            ("_union1", _PerfEventAttrUnion),
            ("sample_type", ctypes.c_uint64),
            ("read_format", ctypes.c_uint64),
            ("flags", ctypes.c_uint64),
            # More fields for the union
            ("wakeup_events", ctypes.c_uint32),
            ("wakeup_watermark", ctypes.c_uint32),
            ("bp_type", ctypes.c_uint32),
            ("bp_addr", ctypes.c_uint64),
            ("bp_len", ctypes.c_uint64),
            ("branch_sample_type", ctypes.c_uint64),
            ("sample_regs_user", ctypes.c_uint64),
            ("sample_stack_user", ctypes.c_uint32),
            ("clockid", ctypes.c_int32),
            ("sample_regs_intr", ctypes.c_uint64),
            ("aux_watermark", ctypes.c_uint32),
            ("sample_max_stack", ctypes.c_uint16),
            ("__reserved_2", ctypes.c_uint16),
            ("aux_sample_size", ctypes.c_uint32),
            ("__reserved_3", ctypes.c_uint32),
            ("sig_data", ctypes.c_uint64),
        ]

    # --- Define ioctl magic numbers ---
    # These are from <linux/perf_event.h>
    PERF_EVENT_IOC_ENABLE = 0x2400
    PERF_EVENT_IOC_DISABLE = 0x2401
    PERF_EVENT_IOC_RESET = 0x2403

    class PerfCounter(object):
        """
        A simple in-process wrapper for a single perf counter.
        """

        def __init__(self, config, group_fd=-1, read_format=0):
            self.fd = getPerfFileHandle(
                config, group_fd=group_fd, read_format=read_format
            )

            assert self.fd is not None

        def reset(self):
            fcntl.ioctl(self.fd, PERF_EVENT_IOC_RESET, 0)

        def start(self):
            self.reset()
            fcntl.ioctl(self.fd, PERF_EVENT_IOC_ENABLE, 0)

        def stop(self):
            try:
                fcntl.ioctl(self.fd, PERF_EVENT_IOC_DISABLE, 0)
            except OSError:
                pass

        def read(self):
            # Reads the 8-byte (64-bit) counter value
            count_bytes = os.read(self.fd, 8)
            return struct.unpack("Q", count_bytes)[0]

        def close(self):
            os.close(self.fd)

    class PerfCounters(object):
        def __init__(self):
            # Create the instruction counter as the group leader.
            self.instr_counter = PerfCounter(config=PERF_COUNT_HW_INSTRUCTIONS)
            # Create the cycle counter as a member of the same group.
            self.cycle_counter = PerfCounter(
                config=PERF_COUNT_HW_REF_CPU_CYCLES, group_fd=self.instr_counter.fd
            )

        def start(self):
            # Enabling the group leader enables all counters in the group.
            self.instr_counter.start()

        def stop(self):
            # Disabling the group leader disables all counters in the group.
            self.instr_counter.stop()

        def getValues(self):
            instr_count = self.instr_counter.read()
            cycle_count = self.cycle_counter.read()

            self.instr_counter.close()
            self.cycle_counter.close()

            return instr_count, cycle_count


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
