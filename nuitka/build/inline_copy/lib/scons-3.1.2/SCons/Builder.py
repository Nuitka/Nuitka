"""
SCons.Builder

Builder object subsystem.

A Builder object is a callable that encapsulates information about how
to execute actions to create a target Node (file) from source Nodes
(files), and how to create those dependencies for tracking.

The main entry point here is the Builder() factory method.  This provides
a procedural interface that creates the right underlying Builder object
based on the keyword arguments supplied and the types of the arguments.

The goal is for this external interface to be simple enough that the
vast majority of users can create new Builders as necessary to support
building new types of files in their configurations, without having to
dive any deeper into this subsystem.

The base class here is BuilderBase.  This is a concrete base class which
does, in fact, represent the Builder objects that we (or users) create.

There is also a proxy that looks like a Builder:

    CompositeBuilder

        This proxies for a Builder with an action that is actually a
        dictionary that knows how to map file suffixes to a specific
        action.  This is so that we can invoke different actions
        (compilers, compile options) for different flavors of source
        files.

Builders and their proxies have the following public interface methods
used by other modules:

    - __call__()
        THE public interface.  Calling a Builder object (with the
        use of internal helper methods) sets up the target and source
        dependencies, appropriate mapping to a specific action, and the
        environment manipulation necessary for overridden construction
        variable.  This also takes care of warning about possible mistakes
        in keyword arguments.

    - add_emitter()
        Adds an emitter for a specific file suffix, used by some Tool
        modules to specify that (for example) a yacc invocation on a .y
        can create a .h *and* a .c file.

    - add_action()
        Adds an action for a specific file suffix, heavily used by
        Tool modules to add their specific action(s) for turning
        a source file into an object file to the global static
        and shared object file Builders.

There are the following methods for internal use within this module:

    - _execute()
        The internal method that handles the heavily lifting when a
        Builder is called.  This is used so that the __call__() methods
        can set up warning about possible mistakes in keyword-argument
        overrides, and *then* execute all of the steps necessary so that
        the warnings only occur once.

    - get_name()
        Returns the Builder's name within a specific Environment,
        primarily used to try to return helpful information in error
        messages.

    - adjust_suffix()
    - get_prefix()
    - get_suffix()
    - get_src_suffix()
    - set_src_suffix()
        Miscellaneous stuff for handling the prefix and suffix
        manipulation we use in turning source file names into target
        file names.

"""

#
# Copyright (c) 2001 - 2019 The SCons Foundation
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

__revision__ = "src/engine/SCons/Builder.py bee7caf9defd6e108fc2998a2520ddb36a967691 2019-12-17 02:07:09 bdeegan"

import collections

import SCons.Action
import SCons.Debug
from SCons.Debug import logInstanceCreation
from SCons.Errors import InternalError, UserError
import SCons.Executor
import SCons.Memoize
import SCons.Util
import SCons.Warnings

class _Null(object):
    pass

_null = _Null

def match_splitext(path, suffixes = []):
    if suffixes:
        matchsuf = [S for S in suffixes if path[-len(S):] == S]
        if matchsuf:
            suf = max([(len(_f),_f) for _f in matchsuf])[1]
            return [path[:-len(suf)], path[-len(suf):]]
    return SCons.Util.splitext(path)

class DictCmdGenerator(SCons.Util.Selector):
    """This is a callable class that can be used as a
    command generator function.  It holds on to a dictionary
    mapping file suffixes to Actions.  It uses that dictionary
    to return the proper action based on the file suffix of
    the source file."""

    def __init__(self, dict=None, source_ext_match=1):
        SCons.Util.Selector.__init__(self, dict)
        self.source_ext_match = source_ext_match

    def src_suffixes(self):
        return list(self.keys())

    def add_action(self, suffix, action):
        """Add a suffix-action pair to the mapping.
        """
        self[suffix] = action

    def __call__(self, target, source, env, for_signature):
        if not source:
            return []

        if self.source_ext_match:
            suffixes = self.src_suffixes()
            ext = None
            for src in map(str, source):
                my_ext = match_splitext(src, suffixes)[1]
                if ext and my_ext != ext:
                    raise UserError("While building `%s' from `%s': Cannot build multiple sources with different extensions: %s, %s"
                             % (repr(list(map(str, target))), src, ext, my_ext))
                ext = my_ext
        else:
            ext = match_splitext(str(source[0]), self.src_suffixes())[1]

        if not ext:
            #return ext
            raise UserError("While building `%s': "
                            "Cannot deduce file extension from source files: %s"
                 % (repr(list(map(str, target))), repr(list(map(str, source)))))

        try:
            ret = SCons.Util.Selector.__call__(self, env, source, ext)
        except KeyError as e:
            raise UserError("Ambiguous suffixes after environment substitution: %s == %s == %s" % (e.args[0], e.args[1], e.args[2]))
        if ret is None:
            raise UserError("While building `%s' from `%s': Don't know how to build from a source file with suffix `%s'.  Expected a suffix in this list: %s." % \
                            (repr(list(map(str, target))), repr(list(map(str, source))), ext, repr(list(self.keys()))))
        return ret

class CallableSelector(SCons.Util.Selector):
    """A callable dictionary that will, in turn, call the value it
    finds if it can."""
    def __call__(self, env, source):
        value = SCons.Util.Selector.__call__(self, env, source)
        if callable(value):
            value = value(env, source)
        return value

class DictEmitter(SCons.Util.Selector):
    """A callable dictionary that maps file suffixes to emitters.
    When called, it finds the right emitter in its dictionary for the
    suffix of the first source file, and calls that emitter to get the
    right lists of targets and sources to return.  If there's no emitter
    for the suffix in its dictionary, the original target and source are
    returned.
    """
    def __call__(self, target, source, env):
        emitter = SCons.Util.Selector.__call__(self, env, source)
        if emitter:
            target, source = emitter(target, source, env)
        return (target, source)

class ListEmitter(collections.UserList):
    """A callable list of emitters that calls each in sequence,
    returning the result.
    """
    def __call__(self, target, source, env):
        for e in self.data:
            target, source = e(target, source, env)
        return (target, source)

# These are a common errors when calling a Builder;
# they are similar to the 'target' and 'source' keyword args to builders,
# so we issue warnings when we see them.  The warnings can, of course,
# be disabled.
misleading_keywords = {
    'targets'   : 'target',
    'sources'   : 'source',
}

class OverrideWarner(collections.UserDict):
    """A class for warning about keyword arguments that we use as
    overrides in a Builder call.

    This class exists to handle the fact that a single Builder call
    can actually invoke multiple builders.  This class only emits the
    warnings once, no matter how many Builders are invoked.
    """
    def __init__(self, dict):
        collections.UserDict.__init__(self, dict)
        if SCons.Debug.track_instances: logInstanceCreation(self, 'Builder.OverrideWarner')
        self.already_warned = None
    def warn(self):
        if self.already_warned:
            return
        for k in list(self.keys()):
            if k in misleading_keywords:
                alt = misleading_keywords[k]
                msg = "Did you mean to use `%s' instead of `%s'?" % (alt, k)
                SCons.Warnings.warn(SCons.Warnings.MisleadingKeywordsWarning, msg)
        self.already_warned = 1

def Builder(**kw):
    """A factory for builder objects."""
    composite = None
    if 'generator' in kw:
        if 'action' in kw:
            raise UserError("You must not specify both an action and a generator.")
        kw['action'] = SCons.Action.CommandGeneratorAction(kw['generator'], {})
        del kw['generator']
    elif 'action' in kw:
        source_ext_match = kw.get('source_ext_match', 1)
        if 'source_ext_match' in kw:
            del kw['source_ext_match']
        if SCons.Util.is_Dict(kw['action']):
            composite = DictCmdGenerator(kw['action'], source_ext_match)
            kw['action'] = SCons.Action.CommandGeneratorAction(composite, {})
            kw['src_suffix'] = composite.src_suffixes()
        else:
            kw['action'] = SCons.Action.Action(kw['action'])

    if 'emitter' in kw:
        emitter = kw['emitter']
        if SCons.Util.is_String(emitter):
            # This allows users to pass in an Environment
            # variable reference (like "$FOO") as an emitter.
            # We will look in that Environment variable for
            # a callable to use as the actual emitter.
            var = SCons.Util.get_environment_var(emitter)
            if not var:
                raise UserError("Supplied emitter '%s' does not appear to refer to an Environment variable" % emitter)
            kw['emitter'] = EmitterProxy(var)
        elif SCons.Util.is_Dict(emitter):
            kw['emitter'] = DictEmitter(emitter)
        elif SCons.Util.is_List(emitter):
            kw['emitter'] = ListEmitter(emitter)

    result = BuilderBase(**kw)

    if composite is not None:
        result = CompositeBuilder(result, composite)

    return result

def _node_errors(builder, env, tlist, slist):
    """Validate that the lists of target and source nodes are
    legal for this builder and environment.  Raise errors or
    issue warnings as appropriate.
    """

    # First, figure out if there are any errors in the way the targets
    # were specified.
    for t in tlist:
        if t.side_effect:
            raise UserError("Multiple ways to build the same target were specified for: %s" % t)
        if t.has_explicit_builder():
            # Check for errors when the environments are different
            # No error if environments are the same Environment instance
            if (t.env is not None and t.env is not env and
                    # Check OverrideEnvironment case - no error if wrapped Environments
                    # are the same instance, and overrides lists match
                    not (getattr(t.env, '__subject', 0) is getattr(env, '__subject', 1) and
                         getattr(t.env, 'overrides', 0) == getattr(env, 'overrides', 1) and
                         not builder.multi)):
                action = t.builder.action
                t_contents = t.builder.action.get_contents(tlist, slist, t.env)
                contents = builder.action.get_contents(tlist, slist, env)

                if t_contents == contents:
                    msg = "Two different environments were specified for target %s,\n\tbut they appear to have the same action: %s" % (t, action.genstring(tlist, slist, t.env))
                    SCons.Warnings.warn(SCons.Warnings.DuplicateEnvironmentWarning, msg)
                else:
                    try:
                        msg = "Two environments with different actions were specified for the same target: %s\n(action 1: %s)\n(action 2: %s)" % (t,t_contents.decode('utf-8'),contents.decode('utf-8'))
                    except UnicodeDecodeError:
                        msg = "Two environments with different actions were specified for the same target: %s"%t
                    raise UserError(msg)
            if builder.multi:
                if t.builder != builder:
                    msg = "Two different builders (%s and %s) were specified for the same target: %s" % (t.builder.get_name(env), builder.get_name(env), t)
                    raise UserError(msg)
                # TODO(batch):  list constructed each time!
                if t.get_executor().get_all_targets() != tlist:
                    msg = "Two different target lists have a target in common: %s  (from %s and from %s)" % (t, list(map(str, t.get_executor().get_all_targets())), list(map(str, tlist)))
                    raise UserError(msg)
            elif t.sources != slist:
                msg = "Multiple ways to build the same target were specified for: %s  (from %s and from %s)" % (t, list(map(str, t.sources)), list(map(str, slist)))
                raise UserError(msg)

    if builder.single_source:
        if len(slist) > 1:
            raise UserError("More than one source given for single-source builder: targets=%s sources=%s" % (list(map(str,tlist)), list(map(str,slist))))

class EmitterProxy(object):
    """This is a callable class that can act as a
    Builder emitter.  It holds on to a string that
    is a key into an Environment dictionary, and will
    look there at actual build time to see if it holds
    a callable.  If so, we will call that as the actual
    emitter."""
    def __init__(self, var):
        self.var = SCons.Util.to_String(var)

    def __call__(self, target, source, env):
        emitter = self.var

        # Recursively substitute the variable.
        # We can't use env.subst() because it deals only
        # in strings.  Maybe we should change that?
        while SCons.Util.is_String(emitter) and emitter in env:
            emitter = env[emitter]
        if callable(emitter):
            target, source = emitter(target, source, env)
        elif SCons.Util.is_List(emitter):
            for e in emitter:
                target, source = e(target, source, env)

        return (target, source)


    def __eq__(self, other):
        return self.var == other.var

    def __lt__(self, other):
        return self.var < other.var

class BuilderBase(object):
    """Base class for Builders, objects that create output
    nodes (files) from input nodes (files).
    """

    def __init__(self,  action = None,
                        prefix = '',
                        suffix = '',
                        src_suffix = '',
                        target_factory = None,
                        source_factory = None,
                        target_scanner = None,
                        source_scanner = None,
                        emitter = None,
                        multi = 0,
                        env = None,
                        single_source = 0,
                        name = None,
                        chdir = _null,
                        is_explicit = 1,
                        src_builder = None,
                        ensure_suffix = False,
                        **overrides):
        if SCons.Debug.track_instances: logInstanceCreation(self, 'Builder.BuilderBase')
        self._memo = {}
        self.action = action
        self.multi = multi
        if SCons.Util.is_Dict(prefix):
            prefix = CallableSelector(prefix)
        self.prefix = prefix
        if SCons.Util.is_Dict(suffix):
            suffix = CallableSelector(suffix)
        self.env = env
        self.single_source = single_source
        if 'overrides' in overrides:
            msg =  "The \"overrides\" keyword to Builder() creation has been removed;\n" +\
                "\tspecify the items as keyword arguments to the Builder() call instead."
            raise TypeError(msg)
        if 'scanner' in overrides:
            msg = "The \"scanner\" keyword to Builder() creation has been removed;\n" +\
                "\tuse: source_scanner or target_scanner as appropriate."
            raise TypeError(msg)
        self.overrides = overrides

        self.set_suffix(suffix)
        self.set_src_suffix(src_suffix)
        self.ensure_suffix = ensure_suffix

        self.target_factory = target_factory
        self.source_factory = source_factory
        self.target_scanner = target_scanner
        self.source_scanner = source_scanner

        self.emitter = emitter

        # Optional Builder name should only be used for Builders
        # that don't get attached to construction environments.
        if name:
            self.name = name
        self.executor_kw = {}
        if chdir is not _null:
            self.executor_kw['chdir'] = chdir
        self.is_explicit = is_explicit

        if src_builder is None:
            src_builder = []
        elif not SCons.Util.is_List(src_builder):
            src_builder = [ src_builder ]
        self.src_builder = src_builder

    def __nonzero__(self):
        raise InternalError("Do not test for the Node.builder attribute directly; use Node.has_builder() instead")

    def __bool__(self):
        return self.__nonzero__()

    def get_name(self, env):
        """Attempts to get the name of the Builder.

        Look at the BUILDERS variable of env, expecting it to be a
        dictionary containing this Builder, and return the key of the
        dictionary.  If there's no key, then return a directly-configured
        name (if there is one) or the name of the class (by default)."""

        try:
            index = list(env['BUILDERS'].values()).index(self)
            return list(env['BUILDERS'].keys())[index]
        except (AttributeError, KeyError, TypeError, ValueError):
            try:
                return self.name
            except AttributeError:
                return str(self.__class__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def splitext(self, path, env=None):
        if not env:
            env = self.env
        if env:
            suffixes = self.src_suffixes(env)
        else:
            suffixes = []
        return match_splitext(path, suffixes)

    def _adjustixes(self, files, pre, suf, ensure_suffix=False):
        if not files:
            return []
        result = []
        if not SCons.Util.is_List(files):
            files = [files]

        for f in files:
            if SCons.Util.is_String(f):
                f = SCons.Util.adjustixes(f, pre, suf, ensure_suffix)
            result.append(f)
        return result

    def _create_nodes(self, env, target = None, source = None):
        """Create and return lists of target and source nodes.
        """
        src_suf = self.get_src_suffix(env)

        target_factory = env.get_factory(self.target_factory)
        source_factory = env.get_factory(self.source_factory)

        source = self._adjustixes(source, None, src_suf)
        slist = env.arg2nodes(source, source_factory)

        pre = self.get_prefix(env, slist)
        suf = self.get_suffix(env, slist)

        if target is None:
            try:
                t_from_s = slist[0].target_from_source
            except AttributeError:
                raise UserError("Do not know how to create a target from source `%s'" % slist[0])
            except IndexError:
                tlist = []
            else:
                splitext = lambda S: self.splitext(S,env)
                tlist = [ t_from_s(pre, suf, splitext) ]
        else:
            target = self._adjustixes(target, pre, suf, self.ensure_suffix)
            tlist = env.arg2nodes(target, target_factory, target=target, source=source)

        if self.emitter:
            # The emitter is going to do str(node), but because we're
            # being called *from* a builder invocation, the new targets
            # don't yet have a builder set on them and will look like
            # source files.  Fool the emitter's str() calls by setting
            # up a temporary builder on the new targets.
            new_targets = []
            for t in tlist:
                if not t.is_derived():
                    t.builder_set(self)
                    new_targets.append(t)

            orig_tlist = tlist[:]
            orig_slist = slist[:]

            target, source = self.emitter(target=tlist, source=slist, env=env)

            # Now delete the temporary builders that we attached to any
            # new targets, so that _node_errors() doesn't do weird stuff
            # to them because it thinks they already have builders.
            for t in new_targets:
                if t.builder is self:
                    # Only delete the temporary builder if the emitter
                    # didn't change it on us.
                    t.builder_set(None)

            # Have to call arg2nodes yet again, since it is legal for
            # emitters to spit out strings as well as Node instances.
            tlist = env.arg2nodes(target, target_factory,
                                  target=orig_tlist, source=orig_slist)
            slist = env.arg2nodes(source, source_factory,
                                  target=orig_tlist, source=orig_slist)

        return tlist, slist

    def _execute(self, env, target, source, overwarn={}, executor_kw={}):
        # We now assume that target and source are lists or None.
        if self.src_builder:
            source = self.src_builder_sources(env, source, overwarn)

        if self.single_source and len(source) > 1 and target is None:
            result = []
            if target is None: target = [None]*len(source)
            for tgt, src in zip(target, source):
                if tgt is not None:
                    tgt = [tgt]
                if src is not None:
                    src = [src]
                result.extend(self._execute(env, tgt, src, overwarn))
            return SCons.Node.NodeList(result)

        overwarn.warn()

        tlist, slist = self._create_nodes(env, target, source)

        # If there is more than one target ensure that if we need to reset
        # the implicit list to new scan of dependency all targets implicit lists
        # are cleared. (SCons GH Issue #2811 and MongoDB SERVER-33111)
        if len(tlist) > 1:
            for t in tlist:
                t.target_peers = tlist

        # Check for errors with the specified target/source lists.
        _node_errors(self, env, tlist, slist)

        # The targets are fine, so find or make the appropriate Executor to
        # build this particular list of targets from this particular list of
        # sources.

        executor = None
        key = None

        if self.multi:
            try:
                executor = tlist[0].get_executor(create = 0)
            except (AttributeError, IndexError):
                pass
            else:
                executor.add_sources(slist)

        if executor is None:
            if not self.action:
                fmt = "Builder %s must have an action to build %s."
                raise UserError(fmt % (self.get_name(env or self.env),
                                        list(map(str,tlist))))
            key = self.action.batch_key(env or self.env, tlist, slist)
            if key:
                try:
                    executor = SCons.Executor.GetBatchExecutor(key)
                except KeyError:
                    pass
                else:
                    executor.add_batch(tlist, slist)

        if executor is None:
            executor = SCons.Executor.Executor(self.action, env, [],
                                               tlist, slist, executor_kw)
            if key:
                SCons.Executor.AddBatchExecutor(key, executor)

        # Now set up the relevant information in the target Nodes themselves.
        for t in tlist:
            t.cwd = env.fs.getcwd()
            t.builder_set(self)
            t.env_set(env)
            t.add_source(slist)
            t.set_executor(executor)
            t.set_explicit(self.is_explicit)

        return SCons.Node.NodeList(tlist)

    def __call__(self, env, target=None, source=None, chdir=_null, **kw):
        # We now assume that target and source are lists or None.
        # The caller (typically Environment.BuilderWrapper) is
        # responsible for converting any scalar values to lists.
        if chdir is _null:
            ekw = self.executor_kw
        else:
            ekw = self.executor_kw.copy()
            ekw['chdir'] = chdir
        if 'chdir' in ekw and SCons.Util.is_String(ekw['chdir']):
            ekw['chdir'] = env.subst(ekw['chdir'])
        if kw:
            if 'srcdir' in kw:
                def prependDirIfRelative(f, srcdir=kw['srcdir']):
                    import os.path
                    if SCons.Util.is_String(f) and not os.path.isabs(f):
                        f = os.path.join(srcdir, f)
                    return f
                if not SCons.Util.is_List(source):
                    source = [source]
                source = list(map(prependDirIfRelative, source))
                del kw['srcdir']
            if self.overrides:
                env_kw = self.overrides.copy()
                env_kw.update(kw)
            else:
                env_kw = kw
        else:
            env_kw = self.overrides
        env = env.Override(env_kw)
        return self._execute(env, target, source, OverrideWarner(kw), ekw)

    def adjust_suffix(self, suff):
        if suff and not suff[0] in [ '.', '_', '$' ]:
            return '.' + suff
        return suff

    def get_prefix(self, env, sources=[]):
        prefix = self.prefix
        if callable(prefix):
            prefix = prefix(env, sources)
        return env.subst(prefix)

    def set_suffix(self, suffix):
        if not callable(suffix):
            suffix = self.adjust_suffix(suffix)
        self.suffix = suffix

    def get_suffix(self, env, sources=[]):
        suffix = self.suffix
        if callable(suffix):
            suffix = suffix(env, sources)
        return env.subst(suffix)

    def set_src_suffix(self, src_suffix):
        if not src_suffix:
            src_suffix = []
        elif not SCons.Util.is_List(src_suffix):
            src_suffix = [ src_suffix ]
        self.src_suffix = [callable(suf) and suf or self.adjust_suffix(suf) for suf in src_suffix]

    def get_src_suffix(self, env):
        """Get the first src_suffix in the list of src_suffixes."""
        ret = self.src_suffixes(env)
        if not ret:
            return ''
        return ret[0]

    def add_emitter(self, suffix, emitter):
        """Add a suffix-emitter mapping to this Builder.

        This assumes that emitter has been initialized with an
        appropriate dictionary type, and will throw a TypeError if
        not, so the caller is responsible for knowing that this is an
        appropriate method to call for the Builder in question.
        """
        self.emitter[suffix] = emitter

    def add_src_builder(self, builder):
        """
        Add a new Builder to the list of src_builders.

        This requires wiping out cached values so that the computed
        lists of source suffixes get re-calculated.
        """
        self._memo = {}
        self.src_builder.append(builder)

    def _get_sdict(self, env):
        """
        Returns a dictionary mapping all of the source suffixes of all
        src_builders of this Builder to the underlying Builder that
        should be called first.

        This dictionary is used for each target specified, so we save a
        lot of extra computation by memoizing it for each construction
        environment.

        Note that this is re-computed each time, not cached, because there
        might be changes to one of our source Builders (or one of their
        source Builders, and so on, and so on...) that we can't "see."

        The underlying methods we call cache their computed values,
        though, so we hope repeatedly aggregating them into a dictionary
        like this won't be too big a hit.  We may need to look for a
        better way to do this if performance data show this has turned
        into a significant bottleneck.
        """
        sdict = {}
        for bld in self.get_src_builders(env):
            for suf in bld.src_suffixes(env):
                sdict[suf] = bld
        return sdict

    def src_builder_sources(self, env, source, overwarn={}):
        sdict = self._get_sdict(env)

        src_suffixes = self.src_suffixes(env)

        lengths = list(set(map(len, src_suffixes)))

        def match_src_suffix(name, src_suffixes=src_suffixes, lengths=lengths):
            node_suffixes = [name[-l:] for l in lengths]
            for suf in src_suffixes:
                if suf in node_suffixes:
                    return suf
            return None

        result = []
        for s in SCons.Util.flatten(source):
            if SCons.Util.is_String(s):
                match_suffix = match_src_suffix(env.subst(s))
                if not match_suffix and '.' not in s:
                    src_suf = self.get_src_suffix(env)
                    s = self._adjustixes(s, None, src_suf)[0]
            else:
                match_suffix = match_src_suffix(s.name)
            if match_suffix:
                try:
                    bld = sdict[match_suffix]
                except KeyError:
                    result.append(s)
                else:
                    tlist = bld._execute(env, None, [s], overwarn)
                    # If the subsidiary Builder returned more than one
                    # target, then filter out any sources that this
                    # Builder isn't capable of building.
                    if len(tlist) > 1:
                        tlist = [t for t in tlist if match_src_suffix(t.name)]
                    result.extend(tlist)
            else:
                result.append(s)

        source_factory = env.get_factory(self.source_factory)

        return env.arg2nodes(result, source_factory)

    def _get_src_builders_key(self, env):
        return id(env)

    @SCons.Memoize.CountDictCall(_get_src_builders_key)
    def get_src_builders(self, env):
        """
        Returns the list of source Builders for this Builder.

        This exists mainly to look up Builders referenced as
        strings in the 'BUILDER' variable of the construction
        environment and cache the result.
        """
        memo_key = id(env)
        try:
            memo_dict = self._memo['get_src_builders']
        except KeyError:
            memo_dict = {}
            self._memo['get_src_builders'] = memo_dict
        else:
            try:
                return memo_dict[memo_key]
            except KeyError:
                pass

        builders = []
        for bld in self.src_builder:
            if SCons.Util.is_String(bld):
                try:
                    bld = env['BUILDERS'][bld]
                except KeyError:
                    continue
            builders.append(bld)

        memo_dict[memo_key] = builders
        return builders

    def _subst_src_suffixes_key(self, env):
        return id(env)

    @SCons.Memoize.CountDictCall(_subst_src_suffixes_key)
    def subst_src_suffixes(self, env):
        """
        The suffix list may contain construction variable expansions,
        so we have to evaluate the individual strings.  To avoid doing
        this over and over, we memoize the results for each construction
        environment.
        """
        memo_key = id(env)
        try:
            memo_dict = self._memo['subst_src_suffixes']
        except KeyError:
            memo_dict = {}
            self._memo['subst_src_suffixes'] = memo_dict
        else:
            try:
                return memo_dict[memo_key]
            except KeyError:
                pass
        suffixes = [env.subst(x) for x in self.src_suffix]
        memo_dict[memo_key] = suffixes
        return suffixes

    def src_suffixes(self, env):
        """
        Returns the list of source suffixes for all src_builders of this
        Builder.

        This is essentially a recursive descent of the src_builder "tree."
        (This value isn't cached because there may be changes in a
        src_builder many levels deep that we can't see.)
        """
        sdict = {}
        suffixes = self.subst_src_suffixes(env)
        for s in suffixes:
            sdict[s] = 1
        for builder in self.get_src_builders(env):
            for s in builder.src_suffixes(env):
                if s not in sdict:
                    sdict[s] = 1
                    suffixes.append(s)
        return suffixes

class CompositeBuilder(SCons.Util.Proxy):
    """A Builder Proxy whose main purpose is to always have
    a DictCmdGenerator as its action, and to provide access
    to the DictCmdGenerator's add_action() method.
    """

    def __init__(self, builder, cmdgen):
        if SCons.Debug.track_instances: logInstanceCreation(self, 'Builder.CompositeBuilder')
        SCons.Util.Proxy.__init__(self, builder)

        # cmdgen should always be an instance of DictCmdGenerator.
        self.cmdgen = cmdgen
        self.builder = builder

    __call__ = SCons.Util.Delegate('__call__')

    def add_action(self, suffix, action):
        self.cmdgen.add_action(suffix, action)
        self.set_src_suffix(self.cmdgen.src_suffixes())

def is_a_Builder(obj):
    """"Returns True if the specified obj is one of our Builder classes.

    The test is complicated a bit by the fact that CompositeBuilder
    is a proxy, not a subclass of BuilderBase.
    """
    return (isinstance(obj, BuilderBase)
            or isinstance(obj, CompositeBuilder)
            or callable(obj))

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
