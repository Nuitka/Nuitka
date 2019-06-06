"""SCons.Tool.cyglink

Customization of gnulink for Cygwin (http://www.cygwin.com/)

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

import SCons.Action
import SCons.Util

import gnulink

def shlib_generator(target, source, env, for_signature):
    cmd = SCons.Util.CLVar(['$SHLINK'])

    dll = env.FindIxes(target, 'SHLIBPREFIX', 'SHLIBSUFFIX')
    if dll: cmd.extend(['-o', dll])

    cmd.extend(['$SHLINKFLAGS', '$__RPATH'])

    implib = env.FindIxes(target, 'IMPLIBPREFIX', 'IMPLIBSUFFIX')
    if implib:
        cmd.extend([
            '-Wl,--out-implib='+implib.get_string(for_signature),
            '-Wl,--export-all-symbols',
            '-Wl,--enable-auto-import',
            '-Wl,--whole-archive', '$SOURCES',
            '-Wl,--no-whole-archive', '$_LIBDIRFLAGS', '$_LIBFLAGS'
            ])
    else:
        cmd.extend(['$SOURCES', '$_LIBDIRFLAGS', '$_LIBFLAGS'])

    return [cmd]

def shlib_emitter(target, source, env):
    dll = env.FindIxes(target, 'SHLIBPREFIX', 'SHLIBSUFFIX')
    no_import_lib = env.get('no_import_lib', 0)

    if not dll or len(target) > 1:
        raise SCons.Errors.UserError("A shared library should have exactly one target with the suffix: %s" % env.subst("$SHLIBSUFFIX"))

    # Remove any "lib" after the prefix
    pre = env.subst('$SHLIBPREFIX')
    if dll.name[len(pre):len(pre)+3] == 'lib':
        dll.name = pre + dll.name[len(pre)+3:]

    orig_target = target
    target = [env.fs.File(dll)]
    target[0].attributes.shared = 1

    # Append an import lib target
    if not no_import_lib:
        # Create list of target libraries as strings
        target_strings = env.ReplaceIxes(orig_target[0],
                                         'SHLIBPREFIX', 'SHLIBSUFFIX',
                                         'IMPLIBPREFIX', 'IMPLIBSUFFIX')

        implib_target = env.fs.File(target_strings)
        implib_target.attributes.shared = 1
        target.append(implib_target)

    return (target, source)


shlib_action = SCons.Action.Action(shlib_generator, generator=1)

def generate(env):
    """Add Builders and construction variables for cyglink to an Environment."""
    gnulink.generate(env)

    env['LINKFLAGS']   = SCons.Util.CLVar('-Wl,-no-undefined')

    env['SHLINKCOM'] = shlib_action
    env['LDMODULECOM'] = shlib_action
    env.Append(SHLIBEMITTER = [shlib_emitter])

    env['SHLIBPREFIX']         = 'cyg'
    env['SHLIBSUFFIX']         = '.dll'

    env['IMPLIBPREFIX']        = 'lib'
    env['IMPLIBSUFFIX']        = '.dll.a'

def exists(env):
    return gnulink.exists(env)


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
