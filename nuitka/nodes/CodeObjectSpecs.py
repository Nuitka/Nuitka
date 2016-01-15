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
""" Code object specifications.

For code objects that will be attached to module, function, and generator
objects, as well as tracebacks. They might be shared.

"""

from nuitka.PythonVersions import python_version


class CodeObjectSpec:
    def __init__(self, code_name, code_kind, arg_names, kw_only_count, has_starlist,
                 has_stardict):
        assert type(has_starlist) is bool
        assert type(has_stardict) is bool

        self.code_name = code_name
        self.code_kind = code_kind

        self.arg_names = tuple(arg_names)

        for arg_name in arg_names:
            assert type(arg_name) is str

        self.kw_only_count = kw_only_count

        self.has_starlist = has_starlist
        self.has_stardict = has_stardict

        self.local_names = ()

    def __repr__(self):
        return """\
<CodeObjectSpec %(code_kind)s '%(code_name)s' with %(arg_names)r args, %(local_names)s locals>""" % self.getDetails()

    def getDetails(self):
        result = {
            "code_name"     : self.code_name,
            "code_kind"     : self.code_kind,
            "arg_names"     : self.arg_names,
            "local_names"   : self.local_names,
            "kw_only_count" : self.kw_only_count,
            "has_starlist"  : self.has_starlist,
            "has_stardict"  : self.has_stardict,
         }

        if python_version >= 300:
            result["kw_only_count"] = self.kw_only_count

        return result

    def getKind(self):
        return self.code_kind

    def updateLocalNames(self, local_names):
        """ Add detected local variables after closure has been decided.

        """
        self.local_names = tuple(
            local_name
            for local_name in
            local_names
            if local_name not in self.arg_names
        )

    def getVarNames(self):
        return self.arg_names + self.local_names

    def getArgumentCount(self):
        return len(self.arg_names) -           \
            (1 if self.has_stardict else 0)  - \
            (1 if self.has_starlist else 0)  - \
            self.kw_only_count

    def getKwOnlyParameterCount(self):
        return self.kw_only_count

    def getCodeObjectName(self):
        return self.code_name

    def hasStarListArg(self):
        return self.has_starlist

    def hasStarDictArg(self):
        return self.has_stardict
