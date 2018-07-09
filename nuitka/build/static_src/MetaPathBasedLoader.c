//     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
//
// This implements the loading of C compiled modules and shared library
// extension modules bundled for standalone mode.

// This is achieved mainly by registered a "sys.meta_path" loader, that then
// gets asked for module names, and responds if knows about one. It's fed by
// a table created at compile time.

// The nature and use of these 2 loaded module kinds is very different, but
// having them as distinct loaders would only require to duplicate the search
// and registering of stuff.

#include <osdefs.h>

#ifdef _WIN32
#undef SEP
#define SEP '\\'
#endif

#include "nuitka/prelude.h"
#include "nuitka/unfreezing.h"

extern char *getDirname( char *path );

// For Python3.3, the loader is a module attribute, so we need to make it
// accessible from this variable.
#if PYTHON_VERSION < 330
static
#endif
PyObject *metapath_based_loader = NULL;

#ifdef _NUITKA_EXE
static inline bool isVerbose( void )
{
    return Py_VerboseFlag != 0;
}
#elif _NUITKA_SYSFLAG_VERBOSE
static inline bool isVerbose( void )
{
    return true;
}
#else
static inline bool isVerbose( void )
{
    return false;
}
#endif

static struct Nuitka_MetaPathBasedLoaderEntry *loader_entries = NULL;

static bool hasFrozenModule( char const *name )
{
    for ( struct _frozen const *p = PyImport_FrozenModules; ; p++ )
    {
        if ( p->name == NULL )
        {
            return false;
        }

        if ( strcmp( p->name, name ) == 0 )
        {
            break;
        }
    }

    return true;
}

static char *copyModulenameAsPath( char *buffer, char const *module_name )
{
    while( *module_name )
    {
        if ( *module_name == '.' )
        {
            *buffer++ = SEP;
            module_name++;
        }
        else
        {
            *buffer++ = *module_name++;
        }
    }

    *buffer = 0;

    return buffer;
}

extern PyObject *const_str_plain___path__;
extern PyObject *const_str_plain___file__;
extern PyObject *const_str_plain___loader__;

// TODO: This updates the wrong absolute path. We ought to change it to
// the "module_path_name" at the time of writing it, then we save a few
// bytes in the blob, and don't have to create that string here.
#ifdef _NUITKA_STANDALONE
static void patchCodeObjectPaths( PyCodeObject *code_object, PyObject *module_path )
{
    code_object->co_filename = module_path;
    Py_INCREF( module_path );

    Py_ssize_t nconsts = PyTuple_GET_SIZE( code_object->co_consts );

    for ( int i = 0; i < nconsts; i++ )
    {
        PyObject *constant = PyTuple_GET_ITEM( code_object->co_consts, i );

        if ( PyCode_Check( constant ) )
        {
            patchCodeObjectPaths( (PyCodeObject *)constant, module_path );
        }
    }
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_RELATIVE_PATH_FROM_NAME( char const *name, bool is_package )
{
    char buffer[ MAXPATHLEN+1 ];

    copyModulenameAsPath( buffer, name );

    if ( is_package )
    {
        char const sep_str[2] = { SEP, 0 };
        strncat( buffer, sep_str, sizeof(buffer)-1 );
        strncat( buffer, "__init__.py", sizeof(buffer)-1 );
    }
    else
    {
        strncat( buffer, ".py", sizeof(buffer)-1 );
    }

#if PYTHON_VERSION < 300
    PyObject *module_path_entry_base = PyString_FromString( buffer );
#else
    PyObject *module_path_entry_base = PyUnicode_FromString( buffer );
#endif

    PyObject *result = MAKE_RELATIVE_PATH( module_path_entry_base );

    Py_DECREF( module_path_entry_base );

    return result;
}

static PyObject *loadModuleFromCodeObject( PyCodeObject *code_object, char const *name, bool is_package )
{
    assert( code_object != NULL );

    PyObject *modules = PyImport_GetModuleDict();
    PyObject *module;

    assert( PyDict_GetItemString( modules, name ) == NULL );

    module = PyModule_New( name );
    assert( module != NULL );

    int res = PyDict_SetItemString( modules, name, module );
    assert( res == 0 );

    char buffer[ MAXPATHLEN+1 ];

    PyObject *module_path_entry = NULL;

    if ( is_package )
    {
        copyModulenameAsPath( buffer, name );
#if PYTHON_VERSION < 300
        PyObject *module_path_entry_base = PyString_FromString( buffer );
#else
        PyObject *module_path_entry_base = PyUnicode_FromString( buffer );
#endif
        module_path_entry = MAKE_RELATIVE_PATH( module_path_entry_base );
        Py_DECREF( module_path_entry_base );

        char const sep_str[2] = { SEP, 0 };
        strncat( buffer, sep_str, sizeof(buffer)-1 );
        strncat( buffer, "__init__.py", sizeof(buffer)-1 );
    }
    else
    {
        copyModulenameAsPath( buffer, name );
        strncat( buffer, ".py", sizeof(buffer)-1 );
    }

#if PYTHON_VERSION < 300
    PyObject *module_path_name = PyString_FromString( buffer );
#else
    PyObject *module_path_name = PyUnicode_FromString( buffer );
#endif

    PyObject *module_path = MAKE_RELATIVE_PATH( module_path_name );
    Py_DECREF( module_path_name );

    if ( is_package )
    {
        /* Set __path__ properly, unlike frozen module importer does. */
        PyObject *path_list = PyList_New(1);
        if (unlikely( path_list == NULL )) return NULL;

        res = PyList_SetItem( path_list, 0, module_path_entry );
        if (unlikely( res != 0 )) return NULL;
        Py_INCREF( module_path_entry );

        res = PyObject_SetAttr( module, const_str_plain___path__, path_list );
        if (unlikely( res != 0 )) return NULL;

        Py_DECREF( path_list );
    }

#ifdef _NUITKA_STANDALONE
    patchCodeObjectPaths( code_object, module_path );
#endif

    module = PyImport_ExecCodeModuleEx(
        (char *)name,
        (PyObject *)code_object,
        Nuitka_String_AsString( module_path )
    );

    Py_DECREF( module_path );

    return module;
}

static struct Nuitka_MetaPathBasedLoaderEntry *findEntry( char const *name )
{
    struct Nuitka_MetaPathBasedLoaderEntry *current = loader_entries;
    assert( current );

    while ( current->name != NULL )
    {
        if ( strcmp( name, current->name ) == 0 )
        {
            return current;
        }

        current++;
    }

    return NULL;
}

static char *_kwlist[] = {
    (char *)"fullname",
    (char *)"unused",
    NULL
};

static PyObject *_path_unfreezer_find_module( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O|O:find_module",
        _kwlist,
        &module_name,
        &unused
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

    char const *name = Nuitka_String_AsString( module_name );

    if ( isVerbose() )
    {
        PySys_WriteStderr( "import %s # considering responsibility\n", name );
    }

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry( name );

    if ( entry )
    {
        if ( isVerbose() )
        {
            PySys_WriteStderr(
                "import %s # claimed responsibility (compiled)\n",
                name
            );
        }

        Py_INCREF( metapath_based_loader );
        return metapath_based_loader;
    }

    if ( hasFrozenModule( name ) )
    {
        if ( isVerbose() )
        {
            PySys_WriteStderr( "import %s # claimed responsibility (frozen)\n", name );
        }

        Py_INCREF( metapath_based_loader );
        return metapath_based_loader;
    }

    if ( isVerbose() )
    {
        PySys_WriteStderr( "import %s # denied responsibility\n", name );
    }

    Py_INCREF( Py_None );
    return Py_None;
}

static char *_kwlist_get_data[] = {
    (char *)"filename",
    NULL
};

extern PyObject *const_str_plain_read, *const_str_plain_rb;

static PyObject *_path_unfreezer_get_data( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *filename;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O:get_data",
        _kwlist_get_data,
        &filename
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

#if PYTHON_VERSION < 300
    PyObject *data_file = BUILTIN_OPEN( filename, const_str_plain_rb, NULL );
#else
    PyObject *data_file = BUILTIN_OPEN( filename, const_str_plain_rb, NULL, NULL, NULL, NULL, NULL, NULL );
#endif
    if (unlikely( data_file == NULL ))
    {
        // TODO: Issue a runtime warning maybe.
        return NULL;
    }

    PyObject *read_method = PyObject_GetAttr( data_file, const_str_plain_read );
    Py_DECREF( data_file );

    if (unlikely( read_method == NULL ))
    {
        return NULL;
    }

    PyObject *result = CALL_FUNCTION_NO_ARGS( read_method );
    Py_DECREF( read_method );
    return result;
}


#ifdef _NUITKA_STANDALONE

#if PYTHON_VERSION < 300
typedef void (*entrypoint_t)( void );
#else
typedef PyObject * (*entrypoint_t)( void );
#endif

#ifndef _WIN32
// Shared libraries loading.
#include <dlfcn.h>
#endif

#if PYTHON_VERSION >= 350
static PyObject *createModuleSpec( PyObject *module_name );
#endif

PyObject *callIntoShlibModule( const char *full_name, const char *filename )
{
    // Determine the package name and basename of the module to load.
    char const *dot = strrchr( full_name, '.' );
    char const *name;
    char const *package;

    if ( dot == NULL )
    {
        package = NULL;
        name = full_name;
    }
    else {
        package = (char *)full_name;
        name = dot+1;
    }

    char entry_function_name[1024];
    snprintf(
        entry_function_name, sizeof( entry_function_name ),
#if PYTHON_VERSION < 300
        "init%s",
#else
        "PyInit_%s",
#endif
        name
    );

#ifdef _WIN32
    unsigned int old_mode = SetErrorMode( SEM_FAILCRITICALERRORS );

    if ( isVerbose() )
    {
        PySys_WriteStderr(
            "import %s # LoadLibraryEx(\"%s\");\n",
            full_name,
            filename
        );
    }

    HINSTANCE hDLL = LoadLibraryEx( filename, NULL, LOAD_WITH_ALTERED_SEARCH_PATH );

    if (unlikely( hDLL == NULL ))
    {
        PyErr_Format( PyExc_ImportError, "LoadLibraryEx '%s' failed", filename );
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)GetProcAddress( hDLL, entry_function_name );

    SetErrorMode( old_mode );
#else
    int dlopenflags = PyThreadState_GET()->interp->dlopenflags;

    if ( isVerbose() )
    {
        PySys_WriteStderr(
            "import %s # dlopen(\"%s\", %x);\n",
            full_name,
            filename,
            dlopenflags
        );
    }

    void *handle = dlopen( filename, dlopenflags );

    if (unlikely( handle == NULL ))
    {
        const char *error = dlerror();

        if (unlikely( error == NULL ))
        {
            error = "unknown dlopen() error";
        }

        PyErr_SetString( PyExc_ImportError, error );
        return NULL;
    }

    entrypoint_t entrypoint = (entrypoint_t)dlsym(
        handle,
        entry_function_name
    );

#endif
    assert( entrypoint );

    char *old_context = _Py_PackageContext;
    _Py_PackageContext = (char *)package;

    // Finally call into the DLL.
#if PYTHON_VERSION < 300
    (*entrypoint)();
#else
    PyObject *module = (*entrypoint)();
#endif

    _Py_PackageContext = old_context;

#if PYTHON_VERSION < 300
    PyObject *module = PyDict_GetItemString(
        PyImport_GetModuleDict(),
        full_name
    );
#endif

    if (unlikely( module == NULL ))
    {
        if ( !ERROR_OCCURRED() )
        {
            PyErr_Format(
                PyExc_SystemError,
                "dynamic module '%s' not initialized properly",
                full_name
            );
        }

        return NULL;
    }

#if PYTHON_VERSION >= 300
#if PYTHON_VERSION >= 350
    PyModuleDef *def;

    if ( Py_TYPE( module ) == &PyModuleDef_Type )
    {
        def = (PyModuleDef *)module;

        PyObject *spec = createModuleSpec( PyUnicode_FromString( full_name ) );
        module = PyModule_FromDefAndSpec( def, spec );
        Py_DECREF( spec );

        if (unlikely( module == NULL ))
        {
            PyErr_Format(
                PyExc_SystemError,
                "dynamic module '%s' not initialized properly from def",
                full_name
            );

            return NULL;
        }

        assert( PyModule_Check( module ));

        int res = PyModule_ExecDef( module, def );

        if (unlikely( res == -1 ))
        {
            return NULL;
        }

        PyDict_SetItemString(
            PyImport_GetModuleDict(),
            full_name,
            module
        );

        return module;
    }
    else
    {
        def = PyModule_GetDef( module );
    }

    if (likely( def != NULL ))
    {
        def->m_base.m_init = entrypoint;
    }
#else
    PyModuleDef *def = PyModule_GetDef( module );

    if (unlikely( def == NULL ))
    {
        PyErr_Format(
            PyExc_SystemError,
            "initialization of %s did not return an extension module",
            filename
        );

        return NULL;
    }

    def->m_base.m_init = entrypoint;
#endif

#endif

    // Set filename attribute
    int res = PyModule_AddStringConstant( module, "__file__", filename );
    if (unlikely( res < 0 ))
    {
        // Might be refuted, which wouldn't be harmful.
        CLEAR_ERROR_OCCURRED();
    }

    // Call the standard import fix-ups for extension modules. Their interface
    // changed over releases.
#if PYTHON_VERSION < 300
    PyObject *res2 = _PyImport_FixupExtension( (char *)full_name, (char *)filename );

    if (unlikely( res2 == NULL ))
    {
        return NULL;
    }
#elif PYTHON_VERSION < 330
    PyObject *filename_obj = PyUnicode_DecodeFSDefault( filename );
    CHECK_OBJECT( filename_obj );

    res = _PyImport_FixupExtensionUnicode( module, (char *)full_name, filename_obj );

    Py_DECREF( filename_obj );

    if (unlikely( res == -1 ))
    {
        return NULL;
    }
#else
    PyObject *full_name_obj = PyUnicode_FromString( full_name );
    CHECK_OBJECT( full_name_obj );
    PyObject *filename_obj = PyUnicode_DecodeFSDefault( filename );
    CHECK_OBJECT( filename_obj );

    res = _PyImport_FixupExtensionObject( module, full_name_obj, filename_obj );

    Py_DECREF( full_name_obj );
    Py_DECREF( filename_obj );

    if (unlikely( res == -1 ))
    {
        return NULL;
    }
#endif

    return module;
}

#endif



static void loadTriggeredModule( char const *name, char const *trigger_name )
{
    char trigger_module_name[2048];

    strncpy( trigger_module_name, name, sizeof(trigger_module_name)-1 );
    strncat( trigger_module_name, trigger_name, sizeof(trigger_module_name)-1 );

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry( trigger_module_name );

    if ( entry != NULL )
    {
        if ( isVerbose() )
        {
            PySys_WriteStderr( "Loading %s\n", trigger_module_name );
        }

        entry->python_initfunc();

        if (unlikely( ERROR_OCCURRED() ))
        {
            PyErr_Print();
            abort();
        }
    }
}


static PyObject *loadModule( PyObject *module_name, struct Nuitka_MetaPathBasedLoaderEntry *entry )
{
#ifdef _NUITKA_STANDALONE
    if ( ( entry->flags & NUITKA_SHLIB_FLAG ) != 0 )
    {
        // Append the the entry name from full path module name with dots,
        // and translate these into directory separators.
        char filename[ MAXPATHLEN + 1 ];

        strcpy( filename, getBinaryDirectoryHostEncoded() );

        char *d = filename;
        d += strlen( filename );
        assert( *d == 0 );

        *d++ = SEP;

        d = copyModulenameAsPath( d, entry->name );

#ifdef _WIN32
        strcat( d, ".pyd" );
#else
        strcat( d, ".so" );
#endif

        callIntoShlibModule(
            entry->name,
            filename
        );
    }
    else
#endif
    if ( ( entry->flags & NUITKA_BYTECODE_FLAG ) != 0 )
    {
        PyCodeObject *code_object = (PyCodeObject *)PyMarshal_ReadObjectFromString(
            (char *)&constant_bin[ entry->bytecode_start ],
            entry->bytecode_size
        );

        // TODO: Probably a bit harsh reaction.
        if (unlikely( code_object == NULL ))
        {
            PyErr_Print();
            abort();
        }

        return loadModuleFromCodeObject(
            code_object,
            entry->name,
            ( entry->flags & NUITKA_PACKAGE_FLAG ) != 0
        );
    }
    else
    {
        assert( ( entry->flags & NUITKA_SHLIB_FLAG ) == 0 );
        assert( entry->python_initfunc );
        entry->python_initfunc();
    }

    if (unlikely( ERROR_OCCURRED() ))
    {
        return NULL;
    }

    if ( isVerbose() )
    {
        PySys_WriteStderr( "Loaded %s\n", entry->name );
    }

    return LOOKUP_SUBSCRIPT( PyImport_GetModuleDict(), module_name );
}

// Note: This may become an entry point for hard coded imports of compiled
// stuff.
PyObject *IMPORT_EMBEDDED_MODULE( PyObject *module_name, char const *name )
{
    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry( name );
    bool frozen_import = entry == NULL && hasFrozenModule( name );

    if ( entry != NULL || frozen_import )
    {
        // Execute the "preLoad" code produced for the module potentially. This
        // is from plug-ins typically, that want to modify things for the the
        // module before loading, to e.g. set a plug-in path, or do some monkey
        // patching in order to make things compatible.
        loadTriggeredModule( name, "-preLoad" );
    }

    PyObject *result = NULL;

    if ( entry != NULL )
    {
        result = loadModule( module_name, entry );

        if ( result == NULL )
        {
            return NULL;
        }
    }

    if ( frozen_import )
    {
        int res = PyImport_ImportFrozenModule( (char *)name );

        if (unlikely( res == -1 ))
        {
            return NULL;
        }

        if ( res == 1 )
        {
            result = LOOKUP_SUBSCRIPT( PyImport_GetModuleDict(), module_name );
        }
    }

    if ( result != NULL )
    {
        // Execute the "postLoad" code produced for the module potentially. This
        // is from plug-ins typically, that want to modify the module immediately
        // after loading, to e.g. set a plug-in path, or do some monkey patching
        // in order to make things compatible.
        loadTriggeredModule( name, "-postLoad" );

        return result;
    }

    Py_INCREF( Py_None );
    return Py_None;
}

static PyObject *_path_unfreezer_load_module( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O|O:load_module",
        _kwlist,
        &module_name,
        &unused
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

    assert( module_name );
    assert( Nuitka_String_Check( module_name ) );

    char const *name = Nuitka_String_AsString( module_name );

    if ( isVerbose() )
    {
        PySys_WriteStderr( "Loading %s\n", name );
    }

    return IMPORT_EMBEDDED_MODULE( module_name, name );
}

static PyObject *_path_unfreezer_is_package( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *module_name;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O:is_package",
        _kwlist,
        &module_name
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

    assert( module_name );
    assert( Nuitka_String_Check( module_name ) );

    char const *name = Nuitka_String_AsString( module_name );

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry( name );

    PyObject *result;

    if ( entry )
    {
        result = BOOL_FROM( ( entry->flags & NUITKA_PACKAGE_FLAG ) != 0 );
    }
    else
    {
        // TODO: Maybe needs to be an exception.
        result = Py_None;
    }

    Py_INCREF( result );
    return result;
}

#if PYTHON_VERSION >= 340
static PyObject *_path_unfreezer_repr_module( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *module;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O|O:module_repr",
        _kwlist,
        &module,
        &unused
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

    return PyUnicode_FromFormat(
        "<module '%s' from %R>",
        PyModule_GetName( module ),
        PyModule_GetFilenameObject( module )
    );

}

static char *_kwlist2[] = {
    (char *)"fullname",
    (char *)"is_package",
    (char *)"path",
    NULL
};

static PyObject *createModuleSpec( PyObject *module_name )
{
    assert( module_name );
    assert( Nuitka_String_Check( module_name ) );

    char const *name = Nuitka_String_AsString( module_name );

    struct Nuitka_MetaPathBasedLoaderEntry *entry = findEntry( name );

    if ( entry == NULL )
    {
        Py_INCREF( Py_None );
        return Py_None;
    }

    static PyObject *importlib = NULL;
    if ( importlib == NULL )
    {
        importlib = PyImport_ImportModule( "importlib._bootstrap" );
    }

    if (unlikely( importlib == NULL ))
    {
        return NULL;
    }

    static PyObject *module_spec_class = NULL;
    if ( module_spec_class == NULL )
    {
        module_spec_class = PyObject_GetAttrString( importlib, "ModuleSpec" );
    }

    if (unlikely( module_spec_class == NULL ))
    {
        return NULL;
    }

    PyObject *result = PyObject_CallFunctionObjArgs(
        module_spec_class,
        module_name,
        metapath_based_loader,
        NULL
    );

    return result;
}

static PyObject *_path_unfreezer_find_spec( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *module_name;
    PyObject *unused1;
    PyObject *unused2;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "OO|O:find_spec",
        _kwlist2,
        &module_name,
        &unused1,
        &unused2
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

    return createModuleSpec( module_name );
}

#endif

static PyMethodDef _method_def_loader_get_data =
{
    "get_data",
    (PyCFunction)_path_unfreezer_get_data,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_loader_find_module =
{
    "find_module",
    (PyCFunction)_path_unfreezer_find_module,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_loader_load_module =
{
    "load_module",
    (PyCFunction)_path_unfreezer_load_module,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_loader_is_package =
{
    "is_package",
    (PyCFunction)_path_unfreezer_is_package,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

#if PYTHON_VERSION >= 340
static PyMethodDef _method_def_loader_repr_module =
{
    "module_repr",
    (PyCFunction)_path_unfreezer_repr_module,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_loader_find_spec =
{
    "module_repr",
    (PyCFunction)_path_unfreezer_find_spec,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};
#endif

void registerMetaPathBasedUnfreezer( struct Nuitka_MetaPathBasedLoaderEntry *_loader_entries )
{
    // Do it only once.
    if ( loader_entries )
    {
        assert( _loader_entries == loader_entries );

        return;
    }

    loader_entries = _loader_entries;

    // Build the dictionary of the "loader" object, which needs to have two
    // methods "find_module" where we acknowledge that we are capable of loading
    // the module, and "load_module" that does the actual thing.
    PyObject *method_dict = PyDict_New();
    CHECK_OBJECT( method_dict );

    PyObject *loader_get_data = PyCFunction_New(
        &_method_def_loader_get_data,
        NULL
    );
    CHECK_OBJECT( loader_get_data );
    PyDict_SetItemString( method_dict, "get_data", loader_get_data );

    PyObject *loader_find_module = PyCFunction_New(
        &_method_def_loader_find_module,
        NULL
    );
    CHECK_OBJECT( loader_find_module );
    PyDict_SetItemString( method_dict, "find_module", loader_find_module );

    PyObject *loader_load_module = PyCFunction_New(
        &_method_def_loader_load_module,
        NULL
    );
    CHECK_OBJECT( loader_load_module );
    PyDict_SetItemString( method_dict, "load_module", loader_load_module );

    PyObject *loader_is_package = PyCFunction_New(
        &_method_def_loader_is_package,
        NULL
    );
    CHECK_OBJECT( loader_is_package );
    PyDict_SetItemString( method_dict, "is_package", loader_is_package );

#if PYTHON_VERSION >= 330
    PyDict_SetItemString( method_dict, "__module__", Py_None );
#endif

#if PYTHON_VERSION >= 340
    PyObject *loader_repr_module = PyCFunction_New(
        &_method_def_loader_repr_module,
        NULL
    );
    CHECK_OBJECT( loader_repr_module );
    PyDict_SetItemString( method_dict, "module_repr", loader_repr_module );

    PyObject *loader_find_spec = PyCFunction_New(
        &_method_def_loader_find_spec,
        NULL
    );
    CHECK_OBJECT( loader_find_spec );
    PyDict_SetItemString( method_dict, "find_spec", loader_find_spec );
#endif

    // Build the actual class.
    metapath_based_loader = PyObject_CallFunctionObjArgs(
        (PyObject *)&PyType_Type,
#if PYTHON_VERSION < 300
        PyString_FromString( "_nuitka_compiled_modules_loader" ),
#else
        PyUnicode_FromString( "_nuitka_compiled_modules_loader" ),
#endif
        const_tuple_empty,
        method_dict,
        NULL
    );

    CHECK_OBJECT( metapath_based_loader );

    if ( isVerbose() )
    {
        PySys_WriteStderr( "Setup nuitka compiled module/bytecode/shlib importer.\n" );
    }

    // Register it as a meta path loader.
    int res = PyList_Insert(
        PySys_GetObject( ( char *)"meta_path" ),
#if PYTHON_VERSION < 330
        0,
#else
        2,
#endif
        metapath_based_loader
    );
    assert( res == 0 );
}


#if defined(_NUITKA_STANDALONE) || _NUITKA_FROZEN > 0

extern PyObject *const_str_plain___file__;

// This is called for each module imported early on.
void setEarlyFrozenModulesFileAttribute( void )
{
    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while( PyDict_Next( PyImport_GetModuleDict(), &ppos, &key, &value ) )
    {
        if ( key != NULL && value != NULL && PyModule_Check( value ) )
        {
            if ( PyObject_HasAttr( value, const_str_plain___file__ ) )
            {
                bool is_package = PyObject_HasAttr( value, const_str_plain___path__ ) == 1;

                PyObject *file_value = MAKE_RELATIVE_PATH_FROM_NAME(
                    Nuitka_String_AsString( key ),
                    is_package
                );
                PyObject_SetAttr( value, const_str_plain___file__, file_value );
                Py_DECREF( file_value );
            }
        }
    }

    assert( !ERROR_OCCURRED() );
}

#endif
