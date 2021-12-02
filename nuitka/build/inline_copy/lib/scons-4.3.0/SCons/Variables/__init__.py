# MIT License
#
# Copyright The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Add user-friendly customizable variables to an SCons build. """

import os.path
import sys
from functools import cmp_to_key

import SCons.Environment
import SCons.Errors
import SCons.Util
import SCons.Warnings

from .BoolVariable import BoolVariable  # okay
from .EnumVariable import EnumVariable  # okay
from .ListVariable import ListVariable  # naja
from .PackageVariable import PackageVariable # naja
from .PathVariable import PathVariable # okay


class Variables:
    """
    Holds all the options, updates the environment with the variables,
    and renders the help text.

    If *is_global* is true, this is a singleton, create only once.

    Args:
      files (optional): List of option configuration files to load
        (backward compatibility). If a single string is passed it is
        automatically placed in a file list (Default value = None)
      args (optional): dictionary to override values set from *files*.
        (Default value = None)
      is_global (optional): global instance? (Default value = True)

    """
    instance = None

    def __init__(self, files=None, args=None, is_global=True):
        if args is None:
            args = {}
        self.options = []
        self.args = args
        if not SCons.Util.is_List(files):
            if files:
                files = [files,]
            else:
                files = []
        self.files = files
        self.unknown = {}

        # create the singleton instance
        if is_global:
            self = Variables.instance

            if not Variables.instance:
                Variables.instance=self

    def _do_add(self, key, help="", default=None, validator=None, converter=None, **kwargs) -> None:
        class Variable:
            pass

        option = Variable()

        # If we get a list or a tuple, we take the first element as the
        # option key and store the remaining in aliases.
        if SCons.Util.is_List(key) or SCons.Util.is_Tuple(key):
            option.key = key[0]
            option.aliases = list(key[1:])
        else:
            option.key = key
            # TODO: normalize to not include key in aliases. Currently breaks tests.
            option.aliases = [key,]
        if not SCons.Environment.is_valid_construction_var(option.key):
            raise SCons.Errors.UserError("Illegal Variables key `%s'" % str(option.key))
        option.help = help
        option.default = default
        option.validator = validator
        option.converter = converter

        self.options.append(option)

        # options might be added after the 'unknown' dict has been set up,
        # so we remove the key and all its aliases from that dict
        for alias in option.aliases + [option.key,]:
            if alias in self.unknown:
                del self.unknown[alias]

    def keys(self) -> list:
        """Returns the keywords for the options."""
        return [o.key for o in self.options]

    def Add(self, key, *args, **kwargs) -> None:
        r""" Add an option.

        Args:
          key: the name of the variable, or a 5-tuple (or list).
            If a tuple, and there are no additional arguments,
            the tuple is unpacked into help, default, validator, converter.
            If there are additional arguments, the first word of the tuple
            is taken as the key, and the remainder as aliases.
          \*args: optional positional arguments
            help: optional help text for the options (Default value = "")
            default: optional default value for option (Default value = None)
            validator: optional function called to validate the option's value
              (Default value = None)
            converter: optional function to be called to convert the option's
              value before putting it in the environment. (Default value = None)
          \*\*kwargs: keyword args, can be the arguments from \*args or
            arbitrary kwargs used by a variable itself

        """
        if SCons.Util.is_List(key) or SCons.Util.is_Tuple(key):
            if not (len(args) or len(kwargs)):
                return self._do_add(*key)

        return self._do_add(key, *args, **kwargs)

    def AddVariables(self, *optlist) -> None:
        """ Add a list of options.

        Each list element is a tuple/list of arguments to be passed on
        to the underlying method for adding options.

        Example::

            opt.AddVariables(
                ('debug', '', 0),
                ('CC', 'The C compiler'),
                ('VALIDATE', 'An option for testing validation', 'notset', validator, None),
            )

        """

        for o in optlist:
            self._do_add(*o)

    def Update(self, env, args=None) -> None:
        """ Update an environment with the option variables.

        Args:
            env: the environment to update.
            args: [optional] a dictionary of keys and values to update
                in *env*. If omitted, uses the variables from the commandline.
        """

        values = {}

        # first set the defaults:
        for option in self.options:
            if option.default is not None:
                values[option.key] = option.default

        # next set the value specified in the options file
        for filename in self.files:
            if os.path.exists(filename):
                dir = os.path.split(os.path.abspath(filename))[0]
                if dir:
                    sys.path.insert(0, dir)
                try:
                    values['__name__'] = filename
                    with open(filename, 'r') as f:
                        contents = f.read()
                    exec(contents, {}, values)
                finally:
                    if dir:
                        del sys.path[0]
                    del values['__name__']

        # set the values specified on the command line
        if args is None:
            args = self.args

        for arg, value in args.items():
            added = False
            for option in self.options:
                if arg in option.aliases + [option.key,]:
                    values[option.key] = value
                    added = True
            if not added:
                self.unknown[arg] = value

        # put the variables in the environment:
        # (don't copy over variables that are not declared as options)
        for option in self.options:
            try:
                env[option.key] = values[option.key]
            except KeyError:
                pass

        # apply converters
        for option in self.options:
            if option.converter and option.key in values:
                value = env.subst('${%s}'%option.key)
                try:
                    try:
                        env[option.key] = option.converter(value)
                    except TypeError:
                        env[option.key] = option.converter(value, env)
                except ValueError as x:
                    raise SCons.Errors.UserError('Error converting option: %s\n%s'%(option.key, x))


        # apply validators
        for option in self.options:
            if option.validator and option.key in values:
                option.validator(option.key, env.subst('${%s}'%option.key), env)

    def UnknownVariables(self) -> dict:
        """ Returns unknown variables.

        Identifies options that were not known, declared options in this object.
        """
        return self.unknown

    def Save(self, filename, env) -> None:
        """ Save the options to a file.

        Saves all the options which have non-default settings
        to the given file as Python expressions.  This file can
        then be used to load the options for a subsequent run.
        This can be used to create an option cache file.

        Args:
            filename: Name of the file to save into
            env: the environment get the option values from
        """

        # Create the file and write out the header
        try:
            with open(filename, 'w') as fh:
                # Make an assignment in the file for each option
                # within the environment that was assigned a value
                # other than the default. We don't want to save the
                # ones set to default: in case the SConscript settings
                # change you would then pick up old defaults.
                for option in self.options:
                    try:
                        value = env[option.key]
                        try:
                            prepare = value.prepare_to_store
                        except AttributeError:
                            try:
                                eval(repr(value))
                            except KeyboardInterrupt:
                                raise
                            except:
                                # Convert stuff that has a repr() that
                                # cannot be evaluated into a string
                                value = SCons.Util.to_String(value)
                        else:
                            value = prepare()

                        defaultVal = env.subst(SCons.Util.to_String(option.default))
                        if option.converter:
                            try:
                                defaultVal = option.converter(defaultVal)
                            except TypeError:
                                defaultVal = option.converter(defaultVal, env)

                        if str(env.subst('${%s}' % option.key)) != str(defaultVal):
                            fh.write('%s = %s\n' % (option.key, repr(value)))
                    except KeyError:
                        pass
        except IOError as x:
            raise SCons.Errors.UserError('Error writing options to file: %s\n%s' % (filename, x))

    def GenerateHelpText(self, env, sort=None) -> str:
        """ Generate the help text for the options.

        Args:
            env: an environment that is used to get the current values
                of the options.
            cmp: Either a comparison function used for sorting
                (must take two arguments and return -1, 0 or 1)
                or a boolean to indicate if it should be sorted.
        """

        if callable(sort):
            options = sorted(self.options, key=cmp_to_key(lambda x, y: sort(x.key, y.key)))
        elif sort is True:
            options = sorted(self.options, key=lambda x: x.key)
        else:
            options = self.options

        def format_opt(opt, self=self, env=env) -> str:
            if opt.key in env:
                actual = env.subst('${%s}' % opt.key)
            else:
                actual = None
            return self.FormatVariableHelpText(env, opt.key, opt.help, opt.default, actual, opt.aliases)

        lines = [_f for _f in map(format_opt, options) if _f]
        return ''.join(lines)

    fmt = '\n%s: %s\n    default: %s\n    actual: %s\n'
    aliasfmt = '\n%s: %s\n    default: %s\n    actual: %s\n    aliases: %s\n'

    def FormatVariableHelpText(self, env, key, help, default, actual, aliases=None) -> str:
        if aliases is None:
            aliases = []
        # Don't display the key name itself as an alias.
        aliases = [a for a in aliases if a != key]
        if aliases:
            return self.aliasfmt % (key, help, default, actual, aliases)
        else:
            return self.fmt % (key, help, default, actual)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
