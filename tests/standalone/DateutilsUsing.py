#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-skip-unless-imports: dateutil

# nuitka-project: --mode=standalone

from datetime import *

from dateutil.parser import *
from dateutil.relativedelta import *
from dateutil.rrule import *

# test parse
# use static time to avoid time differences in output
now = parse("Thu Sep 25 10:00:00 2003")
print(now)


# test relativedelta
now += relativedelta(months=+1)
print(now)

now += relativedelta(months=+1, weeks=+1)
print(now)


# test rrule
print(list(rrule(DAILY, count=10, dtstart=parse("19970902T090000"))))

print(
    list(
        rrule(
            YEARLY,
            bymonth=1,
            byweekday=range(7),
            dtstart=parse("19980101T090000"),
            until=parse("20000131T090000"),
        )
    )
)


# test rruleset
rrset = rruleset()
rrset.rrule(rrule(WEEKLY, count=4, dtstart=parse("19970902T090000")))
rrset.rdate(datetime(1997, 9, 7, 9, 0))
rrset.exdate(datetime(1997, 9, 16, 9, 0))
print(list(rrset))


# test rrulestr
print(
    list(rrulestr("FREQ=DAILY;INTERVAL=10;COUNT=5", dtstart=parse("19970902T090000")))
)

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
