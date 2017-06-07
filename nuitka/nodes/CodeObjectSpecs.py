#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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


class CodeObjectSpec(object):
    def __init__(self, co_name, co_kind, co_varnames, co_argcount,
                 co_kwonlyargcount, co_has_starlist, co_has_stardict):

        self.co_name = co_name
        self.co_kind = co_kind

        # Strings happens from XML parsing, make sure to convert them.
        if type(co_varnames) is str:
            if co_varnames == "":
                co_varnames = ()
            else:
                co_varnames = co_varnames.split(',')

        if type(co_has_starlist) is not bool:
            co_has_starlist = co_has_starlist != "False"
        if type(co_has_stardict) is not bool:
            co_has_stardict = co_has_stardict != "False"

        self.co_varnames = tuple(co_varnames)

        self.co_argcount = int(co_argcount)
        self.co_kwonlyargcount = int(co_kwonlyargcount)

        self.co_has_starlist = co_has_starlist
        self.co_has_stardict = co_has_stardict

    def __repr__(self):
        return """\
<CodeObjectSpec %(co_kind)s '%(co_name)s' with %(co_varnames)r>""" % self.getDetails()

    def getDetails(self):
        return {
            "co_name"           : self.co_name,
            "co_kind"           : self.co_kind,
            "co_varnames"       : ','.join(self.co_varnames),
            "co_argcount"       : self.co_argcount,
            "co_kwonlyargcount" : self.co_kwonlyargcount,
            "co_has_starlist"   : self.co_has_starlist,
            "co_has_stardict"   : self.co_has_stardict,
        }

    def getCodeObjectKind(self):
        return self.co_kind

    def updateLocalNames(self, local_names):
        """ Add detected local variables after closure has been decided.

        """
        self.co_varnames += tuple(
            local_name
            for local_name in
            local_names
            if local_name not in self.co_varnames
        )

    def getVarNames(self):
        return self.co_varnames

    def getArgumentCount(self):
        return self.co_argcount

    def getKwOnlyParameterCount(self):
        return self.co_kwonlyargcount

    def getCodeObjectName(self):
        return self.co_name

    def hasStarListArg(self):
        return self.co_has_starlist

    def hasStarDictArg(self):
        return self.co_has_stardict
