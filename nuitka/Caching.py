import hashlib
import marshal
import os
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import getFileContents, makePath

def _getCacheFilename(module_name, hash, extension):
    module_cache_dir = os.path.join(getCacheDir(), "module-cache")
    makePath(module_cache_dir)
    return os.path.join(
        module_cache_dir, "%s-%s.%s" % (module_name, hash, extension)
    )


def getSourceCodeHash(path):
    return hashlib.md5(getFileContents(path, "rb")).hexdigest()


def isAlreadyCached(path):
    return os.path.exists(path)


def loadBytecodeFromCache(path):
    return getFileContents(path, "rb")


def filenameToBytecode(path, module_name):
    cache_file_name = _getCacheFilename(module_name, getSourceCodeHash(path), "dat")
    if isAlreadyCached(cache_file_name):
        bytecode = loadBytecodeFromCache(cache_file_name)
        return bytecode
        
    else:
        bytecode = compile(getFileContents(path), path, "exec", dont_inherit=True)
        writeBytecodeToCache(cache_file_name, bytecode)
        return marshal.dumps(bytecode)


#def writeModulesNamesToCache(path, hash, used_modules):
#    with open(_getCacheFilename(path, hash, "txt"), "w") as modules_cache_file:
#        for module_name, _filename in used_modules:
#            modules_cache_file.write(module_name.asString() + "\n")


def writeBytecodeToCache(path, bytecode):
    with open(path, "wb") as bytecode_cache_file:
        bytecode_cache_file.write(marshal.dumps(bytecode))