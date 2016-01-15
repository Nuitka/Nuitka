#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

""" clockres - calculates the resolution in seconds of a given timer.

    Copyright (c) 2006, Marc-Andre Lemburg (mal@egenix.com). See the
    documentation for further information on copyrights, or contact
    the author. All Rights Reserved.

"""
import time

TEST_TIME = 1.0

def clockres(timer):
    d = {}
    wallclock = time.time
    start = wallclock()
    stop = wallclock() + TEST_TIME
    spin_loops = range(1000)
    while 1:
        now = wallclock()
        if now >= stop:
            break
        for i in spin_loops:
            d[timer()] = 1
    values = d.keys()
    values.sort()
    min_diff = TEST_TIME
    for i in range(len(values) - 1):
        diff = values[i+1] - values[i]
        if diff < min_diff:
            min_diff = diff
    return min_diff

if __name__ == '__main__':
    print 'Clock resolution of various timer implementations:'
    print 'time.clock:           %10.3fus' % (clockres(time.clock) * 1e6)
    print 'time.time:            %10.3fus' % (clockres(time.time) * 1e6)
    try:
        import systimes
        print 'systimes.processtime: %10.3fus' % (clockres(systimes.processtime) * 1e6)
    except ImportError:
        pass
