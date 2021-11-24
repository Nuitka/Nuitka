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

import gettext
import optparse
import re
import sys
import textwrap

import SCons.Node.FS
import SCons.Platform.virtualenv
import SCons.Warnings
from . import Main

no_hyphen_re = re.compile(r'(\s+|(?<=[\w!\"\'&.,?])-{2,}(?=\w))')
_ = gettext.gettext
OptionValueError = optparse.OptionValueError
SUPPRESS_HELP = optparse.SUPPRESS_HELP

diskcheck_all = SCons.Node.FS.diskcheck_types()

experimental_features = {'warp_speed', 'transporter', 'ninja'}


def diskcheck_convert(value):
    if value is None:
        return []
    if not SCons.Util.is_List(value):
        value = value.split(',')
    result = []
    for v in value:
        v = v.lower()
        if v == 'all':
            result = diskcheck_all
        elif v == 'none':
            result = []
        elif v in diskcheck_all:
            result.append(v)
        else:
            raise ValueError(v)
    return result


class SConsValues(optparse.Values):
    """
    Holder class for uniform access to SCons options, regardless
    of whether or not they can be set on the command line or in the
    SConscript files (using the SetOption() function).

    A SCons option value can originate three different ways:

        1)  set on the command line;
        2)  set in an SConscript file;
        3)  the default setting (from the the op.add_option()
            calls in the Parser() function, below).

    The command line always overrides a value set in a SConscript file,
    which in turn always overrides default settings.  Because we want
    to support user-specified options in the SConscript file itself,
    though, we may not know about all of the options when the command
    line is first parsed, so we can't make all the necessary precedence
    decisions at the time the option is configured.

    The solution implemented in this class is to keep these different sets
    of settings separate (command line, SConscript file, and default)
    and to override the __getattr__() method to check them in turn.
    This should allow the rest of the code to just fetch values as
    attributes of an instance of this class, without having to worry
    about where they came from.

    Note that not all command line options are settable from SConscript
    files, and the ones that are must be explicitly added to the
    "settable" list in this class, and optionally validated and coerced
    in the set_option() method.
    """

    def __init__(self, defaults):
        self.__defaults__ = defaults
        self.__SConscript_settings__ = {}

    def __getattr__(self, attr):
        """
        Fetches an options value, checking first for explicit settings
        from the command line (which are direct attributes), then the
        SConscript file settings, then the default values.
        """
        try:
            return self.__dict__[attr]
        except KeyError:
            try:
                return self.__dict__['__SConscript_settings__'][attr]
            except KeyError:
                try:
                    return getattr(self.__dict__['__defaults__'], attr)
                except KeyError:
                    # Added because with py3 this is a new class,
                    # not a classic class, and due to the way
                    # In that case it will create an object without
                    # __defaults__, and then query for __setstate__
                    # which will throw an exception of KeyError
                    # deepcopy() is expecting AttributeError if __setstate__
                    # is not available.
                    raise AttributeError(attr)

    # keep this list in sync with the SetOption doc in SCons/Script/Main.xml
    # search for UPDATE_SETOPTION_DOCS there.
    settable = [
        'clean',
        'diskcheck',
        'duplicate',
        'experimental',
        'hash_chunksize',
        'hash_format',
        'help',
        'implicit_cache',
        'implicit_deps_changed',
        'implicit_deps_unchanged',
        'max_drift',
        'md5_chunksize',
        'no_exec',
        'no_progress',
        'num_jobs',
        'random',
        'silent',
        'stack_size',
        'warn',

        # TODO: Remove these once we update the AddOption() API to allow setting
        #       added flag as setable.
        # Requested setable flag in : https://github.com/SCons/scons/issues/3983
        # From experimental ninja
        'disable_execute_ninja',
        'disable_ninja'
    ]

    def set_option(self, name, value):
        """Sets an option from an SConscript file.

        Raises:
            UserError: invalid or malformed option ("error in your script")
        """

        if name not in self.settable:
            raise SCons.Errors.UserError(
                "This option is not settable from a SConscript file: %s" % name
            )

        # the following are for options that need some extra processing
        if name == 'num_jobs':
            try:
                value = int(value)
                if value < 1:
                    raise ValueError
            except ValueError:
                raise SCons.Errors.UserError("A positive integer is required: %s" % repr(value))
        elif name == 'max_drift':
            try:
                value = int(value)
            except ValueError:
                raise SCons.Errors.UserError(
                    "An integer is required: %s" % repr(value))
        elif name == 'duplicate':
            try:
                value = str(value)
            except ValueError:
                raise SCons.Errors.UserError(
                    "A string is required: %s" % repr(value))
            if value not in SCons.Node.FS.Valid_Duplicates:
                raise SCons.Errors.UserError(
                    "Not a valid duplication style: %s" % value
                )
            # Set the duplicate style right away so it can affect linking
            # of SConscript files.
            SCons.Node.FS.set_duplicate(value)
        elif name == 'diskcheck':
            try:
                value = diskcheck_convert(value)
            except ValueError as v:
                raise SCons.Errors.UserError(
                    "Not a valid diskcheck value: %s" % v)
            if 'diskcheck' not in self.__dict__:
                # No --diskcheck= option was specified on the command line.
                # Set this right away so it can affect the rest of the
                # file/Node lookups while processing the SConscript files.
                SCons.Node.FS.set_diskcheck(value)
        elif name == 'stack_size':
            try:
                value = int(value)
            except ValueError:
                raise SCons.Errors.UserError(
                    "An integer is required: %s" % repr(value))
        elif name in ('md5_chunksize', 'hash_chunksize'):
            try:
                value = int(value)
            except ValueError:
                raise SCons.Errors.UserError(
                    "An integer is required: %s" % repr(value))
            name = 'md5_chunksize'  # for now, the old name is used
        elif name == 'warn':
            if SCons.Util.is_String(value):
                value = [value]
            value = self.__SConscript_settings__.get(name, []) + value
            SCons.Warnings.process_warn_strings(value)
        elif name == 'no_progress':
            SCons.Script.Main.progress_display.set_mode(False)
        elif name == 'experimental':
            if SCons.Util.is_String(value):
                value = [value]
            value = self.__SConscript_settings__.get(name, []) + value
        elif name in ('implicit_deps_changed', 'implicit_deps_unchanged'):
            if value:
                self.__SConscript_settings__['implicit_cache'] = True

        self.__SConscript_settings__[name] = value


class SConsOption(optparse.Option):
    def convert_value(self, opt, value):
        if value is not None:
            if self.nargs in (1, '?'):
                return self.check_value(opt, value)
            else:
                return tuple([self.check_value(opt, v) for v in value])

    def process(self, opt, value, values, parser):

        # First, convert the value(s) to the right type.  Howl if any
        # value(s) are bogus.
        value = self.convert_value(opt, value)

        # And then take whatever action is expected of us.
        # This is a separate method to make life easier for
        # subclasses to add new actions.
        return self.take_action(
            self.action, self.dest, opt, value, values, parser)

    def _check_nargs_optional(self):
        if self.nargs == '?' and self._short_opts:
            fmt = "option %s: nargs='?' is incompatible with short options"
            raise SCons.Errors.UserError(fmt % self._short_opts[0])

    CHECK_METHODS = optparse.Option.CHECK_METHODS
    if CHECK_METHODS is None:
        CHECK_METHODS = []
    CHECK_METHODS = CHECK_METHODS + [_check_nargs_optional]
    CONST_ACTIONS = optparse.Option.CONST_ACTIONS + optparse.Option.TYPED_ACTIONS


class SConsOptionGroup(optparse.OptionGroup):
    """
    A subclass for SCons-specific option groups.

    The only difference between this and the base class is that we print
    the group's help text flush left, underneath their own title but
    lined up with the normal "SCons Options".
    """

    def format_help(self, formatter):
        """
        Format an option group's help text, outdenting the title so it's
        flush with the "SCons Options" title we print at the top.
        """
        formatter.dedent()
        result = formatter.format_heading(self.title)
        formatter.indent()
        result = result + optparse.OptionContainer.format_help(self, formatter)
        return result


class SConsOptionParser(optparse.OptionParser):
    preserve_unknown_options = False

    def error(self, msg):
        # overridden OptionValueError exception handler
        self.print_usage(sys.stderr)
        sys.stderr.write("SCons Error: %s\n" % msg)
        sys.exit(2)

    def _process_long_opt(self, rargs, values):
        """
        SCons-specific processing of long options.

        This is copied directly from the normal
        optparse._process_long_opt() method, except that, if configured
        to do so, we catch the exception thrown when an unknown option
        is encountered and just stick it back on the "leftover" arguments
        for later (re-)processing.
        """
        arg = rargs.pop(0)

        # Value explicitly attached to arg?  Pretend it's the next argument.
        if "=" in arg:
            (opt, next_arg) = arg.split("=", 1)
            rargs.insert(0, next_arg)
            had_explicit_value = True
        else:
            opt = arg
            had_explicit_value = False

        try:
            if opt != self._match_long_opt(opt):
                raise optparse.BadOptionError(
                    "'%s'. Did you mean '%s'?"
                    % (opt, self._match_long_opt(opt))
                )
        except optparse.BadOptionError:
            if self.preserve_unknown_options:
                # SCons-specific:  if requested, add unknown options to
                # the "leftover arguments" list for later processing.
                self.largs.append(arg)
                if had_explicit_value:
                    # The unknown option will be re-processed later,
                    # so undo the insertion of the explicit value.
                    rargs.pop(0)
                return
            raise

        option = self._long_opt[opt]
        if option.takes_value():
            nargs = option.nargs
            if nargs == '?':
                if had_explicit_value:
                    value = rargs.pop(0)
                else:
                    value = option.const
            elif len(rargs) < nargs:
                if nargs == 1:
                    if not option.choices:
                        self.error(_("%s option requires an argument") % opt)
                    else:
                        msg = _("%s option requires an argument " % opt)
                        msg += _("(choose from %s)"
                                 % ', '.join(option.choices))
                        self.error(msg)
                else:
                    self.error(_("%s option requires %d arguments")
                               % (opt, nargs))
            elif nargs == 1:
                value = rargs.pop(0)
            else:
                value = tuple(rargs[0:nargs])
                del rargs[0:nargs]

        elif had_explicit_value:
            self.error(_("%s option does not take a value") % opt)

        else:
            value = None

        option.process(opt, value, values, self)

    def reparse_local_options(self):
        """ Re-parse the leftover command-line options.

        Parse options stored in `self.largs`, so that any value
        overridden on the command line is immediately available
        if the user turns around and does a :func:`GetOption` right away.

        We mimic the processing of the single args
        in the original OptionParser :func:`_process_args`, but here we
        allow exact matches for long-opts only (no partial argument names!).
        Otherwise there could be  problems in :func:`add_local_option`
        below. When called from there, we try to reparse the
        command-line arguments that

        1. haven't been processed so far (`self.largs`), but
        2. are possibly not added to the list of options yet.

        So, when we only have a value for "--myargument" so far,
        a command-line argument of "--myarg=test" would set it,
        per the behaviour of :func:`_match_long_opt`,
        which allows for partial matches of the option name,
        as long as the common prefix appears to be unique.
        This would lead to further confusion, because we might want
        to add another option "--myarg" later on (see issue #2929).

        """
        rargs = []
        largs_restore = []
        # Loop over all remaining arguments
        skip = False
        for l in self.largs:
            if skip:
                # Accept all remaining arguments as they are
                largs_restore.append(l)
            else:
                if len(l) > 2 and l[0:2] == "--":
                    # Check long option
                    lopt = (l,)
                    if "=" in l:
                        # Split into option and value
                        lopt = l.split("=", 1)

                    if lopt[0] in self._long_opt:
                        # Argument is already known
                        rargs.append('='.join(lopt))
                    else:
                        # Not known yet, so reject for now
                        largs_restore.append('='.join(lopt))
                else:
                    if l == "--" or l == "-":
                        # Stop normal processing and don't
                        # process the rest of the command-line opts
                        largs_restore.append(l)
                        skip = True
                    else:
                        rargs.append(l)

        # Parse the filtered list
        self.parse_args(rargs, self.values)
        # Restore the list of remaining arguments for the
        # next call of AddOption/add_local_option...
        self.largs = self.largs + largs_restore

    def add_local_option(self, *args, **kw):
        """
        Adds a local option to the parser.

        This is initiated by an AddOption() call to add a user-defined
        command-line option.  We add the option to a separate option
        group for the local options, creating the group if necessary.
        """
        try:
            group = self.local_option_group
        except AttributeError:
            group = SConsOptionGroup(self, 'Local Options')
            group = self.add_option_group(group)
            self.local_option_group = group

        result = group.add_option(*args, **kw)

        if result:
            # The option was added successfully.  We now have to add the
            # default value to our object that holds the default values
            # (so that an attempt to fetch the option's attribute will
            # yield the default value when not overridden) and then
            # we re-parse the leftover command-line options, so that
            # any value overridden on the command line is immediately
            # available if the user turns around and does a GetOption()
            # right away.
            setattr(self.values.__defaults__, result.dest, result.default)
            self.reparse_local_options()

        return result


class SConsIndentedHelpFormatter(optparse.IndentedHelpFormatter):
    def format_usage(self, usage):
        return "usage: %s\n" % usage

    def format_heading(self, heading):
        """
        This translates any heading of "options" or "Options" into
        "SCons Options."  Unfortunately, we have to do this here,
        because those titles are hard-coded in the optparse calls.
        """
        if heading == 'Options':
            heading = "SCons Options"
        return optparse.IndentedHelpFormatter.format_heading(self, heading)

    def format_option(self, option):
        """
        A copy of the normal optparse.IndentedHelpFormatter.format_option()
        method.  This has been snarfed so we can modify text wrapping to
        out liking:

        --  add our own regular expression that doesn't break on hyphens
            (so things like --no-print-directory don't get broken);

        --  wrap the list of options themselves when it's too long
            (the wrapper.fill(opts) call below);

        --  set the subsequent_indent when wrapping the help_text.
        """
        # The help for each option consists of two parts:
        #   * the opt strings and metavars
        #     eg. ("-x", or "-fFILENAME, --file=FILENAME")
        #   * the user-supplied help string
        #     eg. ("turn on expert mode", "read data from FILENAME")
        #
        # If possible, we write both of these on the same line:
        #   -x      turn on expert mode
        #
        # But if the opt string list is too long, we put the help
        # string on a second line, indented to the same column it would
        # start in if it fit on the first line.
        #   -fFILENAME, --file=FILENAME
        #           read data from FILENAME
        result = []

        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            wrapper = textwrap.TextWrapper(width=self.width,
                                           initial_indent='  ',
                                           subsequent_indent='  ')
            wrapper.wordsep_re = no_hyphen_re
            opts = wrapper.fill(opts) + '\n'
            indent_first = self.help_position
        else:                       # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:

            help_text = self.expand_default(option)

            # SCons:  indent every line of the help text but the first.
            wrapper = textwrap.TextWrapper(width=self.help_width,
                                           subsequent_indent='  ')
            wrapper.wordsep_re = no_hyphen_re
            help_lines = wrapper.wrap(help_text)
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            for line in help_lines[1:]:
                result.append("%*s%s\n" % (self.help_position, "", line))
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result)


def Parser(version):
    """
    Returns an options parser object initialized with the standard
    SCons options.
    """

    formatter = SConsIndentedHelpFormatter(max_help_position=30)

    op = SConsOptionParser(option_class=SConsOption,
                           add_help_option=False,
                           formatter=formatter,
                           usage="usage: scons [OPTION] [TARGET] ...",)

    op.preserve_unknown_options = True
    op.version = version

    # Add the options to the parser we just created.
    #
    # These are in the order we want them to show up in the -H help
    # text, basically alphabetical.  Each op.add_option() call below
    # should have a consistent format:
    #
    #   op.add_option("-L", "--long-option-name",
    #                 nargs=1, type="string",
    #                 dest="long_option_name", default='foo',
    #                 action="callback", callback=opt_long_option,
    #                 help="help text goes here",
    #                 metavar="VAR")
    #
    # Even though the optparse module constructs reasonable default
    # destination names from the long option names, we're going to be
    # explicit about each one for easier readability and so this code
    # will at least show up when grepping the source for option attribute
    # names, or otherwise browsing the source code.

    # options ignored for compatibility
    def opt_ignore(option, opt, value, parser):
        sys.stderr.write("Warning:  ignoring %s option\n" % opt)
    op.add_option("-b", "-d", "-e", "-m", "-S", "-t", "-w",
                  "--environment-overrides",
                  "--no-keep-going",
                  "--no-print-directory",
                  "--print-directory",
                  "--stop",
                  "--touch",
                  action="callback", callback=opt_ignore,
                  help="Ignored for compatibility.")

    op.add_option('-c', '--clean', '--remove',
                  dest="clean", default=False,
                  action="store_true",
                  help="Remove specified targets and dependencies.")

    op.add_option('-C', '--directory',
                  nargs=1, type="string",
                  dest="directory", default=[],
                  action="append",
                  help="Change to DIR before doing anything.",
                  metavar="DIR")

    op.add_option('--cache-debug',
                  nargs=1,
                  dest="cache_debug", default=None,
                  action="store",
                  help="Print CacheDir debug info to FILE.",
                  metavar="FILE")

    op.add_option('--cache-disable', '--no-cache',
                  dest='cache_disable', default=False,
                  action="store_true",
                  help="Do not retrieve built targets from CacheDir.")

    op.add_option('--cache-force', '--cache-populate',
                  dest='cache_force', default=False,
                  action="store_true",
                  help="Copy already-built targets into the CacheDir.")

    op.add_option('--cache-readonly',
                  dest='cache_readonly', default=False,
                  action="store_true",
                  help="Do not update CacheDir with built targets.")

    op.add_option('--cache-show',
                  dest='cache_show', default=False,
                  action="store_true",
                  help="Print build actions for files from CacheDir.")

    def opt_invalid(group, value, options):
        """report an invalid option from a group"""
        errmsg = "`%s' is not a valid %s option type, try:\n" % (value, group)
        return errmsg + "    %s" % ", ".join(options)

    def opt_invalid_rm(group, value, msg):
        """report an invalid option from a group: recognized but removed"""
        errmsg = "`%s' is not a valid %s option type " % (value, group)
        return errmsg + msg

    config_options = ["auto", "force", "cache"]

    opt_config_help = "Controls Configure subsystem: %s." \
                      % ", ".join(config_options)

    op.add_option('--config',
                  nargs=1, choices=config_options,
                  dest="config", default="auto",
                  help=opt_config_help,
                  metavar="MODE")

    op.add_option('-D',
                  dest="climb_up", default=None,
                  action="store_const", const=2,
                  help="Search up directory tree for SConstruct,       "
                       "build all Default() targets.")

    deprecated_debug_options = {}

    removed_debug_options = {
        "dtree": '; please use --tree=derived instead',
        "nomemoizer": '; there is no replacement',
        "stree": '; please use --tree=all,status instead',
        "tree": '; please use --tree=all instead',
    }

    debug_options = ["count", "duplicate", "explain", "findlibs",
                     "includes", "memoizer", "memory", "objects",
                     "pdb", "prepare", "presub", "stacktrace",
                     "time", "action-timestamps"]

    def opt_debug(option, opt, value__, parser,
                  debug_options=debug_options,
                  deprecated_debug_options=deprecated_debug_options,
                  removed_debug_options=removed_debug_options):
        for value in value__.split(','):
            if value in debug_options:
                parser.values.debug.append(value)
            elif value in deprecated_debug_options:
                parser.values.debug.append(value)
                try:
                    parser.values.delayed_warnings
                except AttributeError:
                    parser.values.delayed_warnings = []
                msg = deprecated_debug_options[value]
                w = "The --debug=%s option is deprecated%s." % (value, msg)
                t = (SCons.Warnings.DeprecatedDebugOptionsWarning, w)
                parser.values.delayed_warnings.append(t)
            elif value in removed_debug_options:
                msg = removed_debug_options[value]
                raise OptionValueError(opt_invalid_rm('debug', value, msg))
            else:
                raise OptionValueError(opt_invalid(
                    'debug', value, debug_options))

    opt_debug_help = "Print various types of debugging information: %s." \
                     % ", ".join(debug_options)
    op.add_option('--debug',
                  nargs=1, type="string",
                  dest="debug", default=[],
                  action="callback", callback=opt_debug,
                  help=opt_debug_help,
                  metavar="TYPE")

    def opt_diskcheck(option, opt, value, parser):
        try:
            diskcheck_value = diskcheck_convert(value)
        except ValueError as e:
            raise OptionValueError("`%s' is not a valid diskcheck type" % e)
        setattr(parser.values, option.dest, diskcheck_value)

    op.add_option('--diskcheck',
                  nargs=1, type="string",
                  dest='diskcheck', default=None,
                  action="callback", callback=opt_diskcheck,
                  help="Enable specific on-disk checks.",
                  metavar="TYPE")

    def opt_duplicate(option, opt, value, parser):
        if value not in SCons.Node.FS.Valid_Duplicates:
            raise OptionValueError(opt_invalid('duplication', value,
                                               SCons.Node.FS.Valid_Duplicates))
        setattr(parser.values, option.dest, value)
        # Set the duplicate style right away so it can affect linking
        # of SConscript files.
        SCons.Node.FS.set_duplicate(value)

    opt_duplicate_help = "Set the preferred duplication methods. Must be one of " \
                         + ", ".join(SCons.Node.FS.Valid_Duplicates)

    op.add_option('--duplicate',
                  nargs=1, type="string",
                  dest="duplicate", default='hard-soft-copy',
                  action="callback", callback=opt_duplicate,
                  help=opt_duplicate_help)

    if not SCons.Platform.virtualenv.virtualenv_enabled_by_default:
        op.add_option('--enable-virtualenv',
                      dest="enable_virtualenv",
                      action="store_true",
                      help="Import certain virtualenv variables to SCons")

    def experimental_callback(option, opt, value, parser):
        experimental = getattr(parser.values, option.dest)

        if ',' in value:
            value = value.split(',')
        else:
            value = [value]

        for v in value:
            if v == 'none':
                experimental = set()
            elif v == 'all':
                experimental = experimental_features
            elif v not in experimental_features:
                raise OptionValueError(
                    "option --experimental: invalid choice: '%s' "
                    "(choose from 'all','none',%s)"
                    % (v, ','.join(["'%s'" % e for e in sorted(experimental_features)]))
                )
            else:
                experimental |= {v}

        setattr(parser.values, option.dest, experimental)

    op.add_option('--experimental',
                  dest='experimental',
                  action='callback',
                  default=set(),  # empty set
                  type='str',
                  # choices=experimental_options+experimental_features,
                  callback=experimental_callback,
                  help='Enable experimental features')

    op.add_option('-f', '--file', '--makefile', '--sconstruct',
                  nargs=1, type="string",
                  dest="file", default=[],
                  action="append",
                  help="Read FILE as the top-level SConstruct file.")

    op.add_option('-h', '--help',
                  dest="help", default=False,
                  action="store_true",
                  help="Print defined help message, or this one.")

    op.add_option("-H", "--help-options",
                  action="help",
                  help="Print this message and exit.")

    def warn_md5_chunksize_deprecated(option, opt, value, parser):
        if opt == '--md5-chunksize':
            SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                                "Parameter %s is deprecated. Use "
                                "--hash-chunksize instead." % opt)

        setattr(parser.values, option.dest, value)

    op.add_option('--hash-chunksize', '--md5-chunksize',
                  nargs=1, type="int",
                  dest='md5_chunksize', default=SCons.Node.FS.File.hash_chunksize,
                  action="callback",
                  help="Set chunk-size for hash signature computation to N kilobytes.",
                  callback=warn_md5_chunksize_deprecated,
                  metavar="N")

    op.add_option('--hash-format',
                  dest='hash_format',
                  action='store',
                  help='Hash format (e.g. md5, sha1, or sha256).')

    op.add_option('-i', '--ignore-errors',
                  dest='ignore_errors', default=False,
                  action="store_true",
                  help="Ignore errors from build actions.")

    op.add_option('-I', '--include-dir',
                  nargs=1,
                  dest='include_dir', default=[],
                  action="append",
                  help="Search DIR for imported Python modules.",
                  metavar="DIR")

    op.add_option('--ignore-virtualenv',
                  dest="ignore_virtualenv",
                  action="store_true",
                  help="Do not import virtualenv variables to SCons")

    op.add_option('--implicit-cache',
                  dest='implicit_cache', default=False,
                  action="store_true",
                  help="Cache implicit dependencies")

    def opt_implicit_deps(option, opt, value, parser):
        setattr(parser.values, 'implicit_cache', True)
        setattr(parser.values, option.dest, True)

    op.add_option('--implicit-deps-changed',
                  dest="implicit_deps_changed", default=False,
                  action="callback", callback=opt_implicit_deps,
                  help="Ignore cached implicit dependencies.")

    op.add_option('--implicit-deps-unchanged',
                  dest="implicit_deps_unchanged", default=False,
                  action="callback", callback=opt_implicit_deps,
                  help="Ignore changes in implicit dependencies.")

    op.add_option('--interact', '--interactive',
                  dest='interactive', default=False,
                  action="store_true",
                  help="Run in interactive mode.")

    op.add_option('-j', '--jobs',
                  nargs=1, type="int",
                  dest="num_jobs", default=1,
                  action="store",
                  help="Allow N jobs at once.",
                  metavar="N")

    op.add_option('-k', '--keep-going',
                  dest='keep_going', default=False,
                  action="store_true",
                  help="Keep going when a target can't be made.")

    op.add_option('--max-drift',
                  nargs=1, type="int",
                  dest='max_drift', default=SCons.Node.FS.default_max_drift,
                  action="store",
                  help="Set maximum system clock drift to N seconds.",
                  metavar="N")

    op.add_option('-n', '--no-exec', '--just-print', '--dry-run', '--recon',
                  dest='no_exec', default=False,
                  action="store_true",
                  help="Don't build; just print commands.")

    op.add_option('--no-site-dir',
                  dest='site_dir',
                  action="store_false",
                  help="Don't search or use the usual site_scons dir.")

    op.add_option('--profile',
                  nargs=1,
                  dest="profile_file", default=None,
                  action="store",
                  help="Profile SCons and put results in FILE.",
                  metavar="FILE")

    op.add_option('-q', '--question',
                  dest="question", default=False,
                  action="store_true",
                  help="Don't build; exit status says if up to date.")

    op.add_option('-Q',
                  dest='no_progress', default=False,
                  action="store_true",
                  help="Suppress \"Reading/Building\" progress messages.")

    op.add_option('--random',
                  dest="random", default=False,
                  action="store_true",
                  help="Build dependencies in random order.")

    op.add_option('-s', '--silent', '--quiet',
                  dest="silent", default=False,
                  action="store_true",
                  help="Don't print commands.")

    op.add_option('--site-dir',
                  nargs=1,
                  dest='site_dir', default=None,
                  action="store",
                  help="Use DIR instead of the usual site_scons dir.",
                  metavar="DIR")

    op.add_option('--stack-size',
                  nargs=1, type="int",
                  dest='stack_size',
                  action="store",
                  help="Set the stack size of the threads used to run jobs to N kilobytes.",
                  metavar="N")

    op.add_option('--taskmastertrace',
                  nargs=1,
                  dest="taskmastertrace_file", default=None,
                  action="store",
                  help="Trace Node evaluation to FILE.",
                  metavar="FILE")

    tree_options = ["all", "derived", "prune", "status", "linedraw"]

    def opt_tree(option, opt, value, parser, tree_options=tree_options):
        tp = Main.TreePrinter()
        for o in value.split(','):
            if o == 'all':
                tp.derived = False
            elif o == 'derived':
                tp.derived = True
            elif o == 'prune':
                tp.prune = True
            elif o == 'status':
                tp.status = True
            elif o == 'linedraw':
                tp.sLineDraw = True
            else:
                raise OptionValueError(opt_invalid('--tree', o, tree_options))
        parser.values.tree_printers.append(tp)

    opt_tree_help = "Print a dependency tree in various formats: %s." \
                    % ", ".join(tree_options)

    op.add_option('--tree',
                  nargs=1, type="string",
                  dest="tree_printers", default=[],
                  action="callback", callback=opt_tree,
                  help=opt_tree_help,
                  metavar="OPTIONS")

    op.add_option('-u', '--up', '--search-up',
                  dest="climb_up", default=0,
                  action="store_const", const=1,
                  help="Search up directory tree for SConstruct,       "
                       "build targets at or below current directory.")

    op.add_option('-U',
                  dest="climb_up", default=0,
                  action="store_const", const=3,
                  help="Search up directory tree for SConstruct,       "
                       "build Default() targets from local SConscript.")

    def opt_version(option, opt, value, parser):
        sys.stdout.write(parser.version + '\n')
        sys.exit(0)
    op.add_option("-v", "--version",
                  action="callback", callback=opt_version,
                  help="Print the SCons version number and exit.")

    def opt_warn(option, opt, value, parser, tree_options=tree_options):
        if SCons.Util.is_String(value):
            value = value.split(',')
        parser.values.warn.extend(value)

    op.add_option('--warn', '--warning',
                  nargs=1, type="string",
                  dest="warn", default=[],
                  action="callback", callback=opt_warn,
                  help="Enable or disable warnings.",
                  metavar="WARNING-SPEC")

    op.add_option('-Y', '--repository', '--srcdir',
                  nargs=1,
                  dest="repository", default=[],
                  action="append",
                  help="Search REPOSITORY for source and target files.")

    # Options from Make and Cons classic that we do not yet support,
    # but which we may support someday and whose (potential) meanings
    # we don't want to change.  These all get a "the -X option is not
    # yet implemented" message and don't show up in the help output.

    def opt_not_yet(option, opt, value, parser):
        msg = "Warning:  the %s option is not yet implemented\n" % opt
        sys.stderr.write(msg)

    op.add_option('-l', '--load-average', '--max-load',
                  nargs=1, type="float",
                  dest="load_average", default=0,
                  action="callback", callback=opt_not_yet,
                  # action="store",
                  # help="Don't start multiple jobs unless load is below "
                  #      "LOAD-AVERAGE."
                  help=SUPPRESS_HELP)
    op.add_option('--list-actions',
                  dest="list_actions",
                  action="callback", callback=opt_not_yet,
                  # help="Don't build; list files and build actions."
                  help=SUPPRESS_HELP)
    op.add_option('--list-derived',
                  dest="list_derived",
                  action="callback", callback=opt_not_yet,
                  # help="Don't build; list files that would be built."
                  help=SUPPRESS_HELP)
    op.add_option('--list-where',
                  dest="list_where",
                  action="callback", callback=opt_not_yet,
                  # help="Don't build; list files and where defined."
                  help=SUPPRESS_HELP)
    op.add_option('-o', '--old-file', '--assume-old',
                  nargs=1, type="string",
                  dest="old_file", default=[],
                  action="callback", callback=opt_not_yet,
                  # action="append",
                  # help = "Consider FILE to be old; don't rebuild it."
                  help=SUPPRESS_HELP)
    op.add_option('--override',
                  nargs=1, type="string",
                  action="callback", callback=opt_not_yet,
                  dest="override",
                  # help="Override variables as specified in FILE."
                  help=SUPPRESS_HELP)
    op.add_option('-p',
                  action="callback", callback=opt_not_yet,
                  dest="p",
                  # help="Print internal environments/objects."
                  help=SUPPRESS_HELP)
    op.add_option('-r', '-R', '--no-builtin-rules', '--no-builtin-variables',
                  action="callback", callback=opt_not_yet,
                  dest="no_builtin_rules",
                  # help="Clear default environments and variables."
                  help=SUPPRESS_HELP)
    op.add_option('--write-filenames',
                  nargs=1, type="string",
                  dest="write_filenames",
                  action="callback", callback=opt_not_yet,
                  # help="Write all filenames examined into FILE."
                  help=SUPPRESS_HELP)
    op.add_option('-W', '--new-file', '--assume-new', '--what-if',
                  nargs=1, type="string",
                  dest="new_file",
                  action="callback", callback=opt_not_yet,
                  # help="Consider FILE to be changed."
                  help=SUPPRESS_HELP)
    op.add_option('--warn-undefined-variables',
                  dest="warn_undefined_variables",
                  action="callback", callback=opt_not_yet,
                  # help="Warn when an undefined variable is referenced."
                  help=SUPPRESS_HELP)
    return op

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
