#     Copyright 2019, Tommy Li, mailto:tommyli3318@gmail.com
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


# nuitka-skip-unless-imports: pytz

from datetime import datetime, timedelta
from pytz import timezone
import pytz

utc = pytz.utc
print(utc.zone)

eastern = timezone('US/Eastern')
print(eastern.zone)

amsterdam = timezone('Europe/Amsterdam')
fmt = '%Y-%m-%d %H:%M:%S %Z%z'
loc_dt = eastern.localize(datetime(2002, 10, 27, 6, 0, 0))
print(loc_dt.strftime(fmt))

ams_dt = loc_dt.astimezone(amsterdam)
print(ams_dt.strftime(fmt))

utc_dt = datetime(2002, 10, 27, 6, 0, 0, tzinfo=utc)
loc_dt = utc_dt.astimezone(eastern)
print(loc_dt.strftime(fmt))

before = loc_dt - timedelta(minutes=10)
print(before.strftime(fmt))

print(eastern.normalize(before).strftime(fmt))

after = eastern.normalize(before + timedelta(minutes=20))
print(after.strftime(fmt))

utc_dt = utc.localize(datetime.utcfromtimestamp(1143408899))
print(utc_dt.strftime(fmt))

au_tz = timezone('Australia/Sydney')
au_dt = utc_dt.astimezone(au_tz)
print(au_dt.strftime(fmt))

utc_dt2 = au_dt.astimezone(utc)
print(utc_dt2.strftime(fmt))

print(utc_dt == utc_dt2)
