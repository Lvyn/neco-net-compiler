""" Python backend plugin. """

from Cython.Build import cythonize
from Cython.Distutils import build_ext
from distutils.core import setup
from distutils.extension import Extension
from neco.backends.cython import netir
from neco.backends.cython.priv import common, cyast
from neco.backends.cython.priv.common import CythonPyxFile, CythonPxdFile
from neco.utils import flatten_ast, search_file, OutputProvider, \
    OutputProviderPredicate
import imp
import nettypes
import os

_backend_ = "cython"

def new_marking_type(name, config):
    return nettypes.StaticMarkingType(config)

def new_compiling_environment(config, net_info, word_set, marking_type):
    env = common.CompilingEnvironment(config, net_info, word_set, marking_type, nettypes.MarkingSetType(marking_type))
    # register this marking type as a cython
    # class, will be used instead of object
    env.register_cython_type(marking_type.type, "Marking")
    return env

def compile_IR(env, config):
    search_paths = config.search_paths
    module_name = config.out_module

    env.module_name = module_name
    env.output_provider = OutputProvider()

    module_pyx_file = CythonPyxFile(module_name + '.pyx')
    module_pxd_file = CythonPxdFile(module_name + '.pxd')
    env.output_provider.register(module_pyx_file)
    env.output_provider.register(module_pxd_file)

    base_dir = "build/"
    try:
        os.mkdir(base_dir)
    except OSError:
        pass

    ################################################################################
    # produce pyx module file
    ################################################################################

    if config.profile:
        print "[ Profiling enabled ]"
        module_pyx_file.declarations.append("# cython: profile=True")

    module_pyx_file.declarations.append("# distutils: language = c++\n")
    module_pyx_file.declarations.append("# cython: boundscheck=False\n")
    module_pyx_file.declarations.append("# cython: cdivision=True\n")
    module_pyx_file.declarations.append("from cython.operator cimport dereference as deref\n")
    module_pyx_file.declarations.append("import neco.ctypes")
    module_pyx_file.declarations.append("cimport neco.ctypes.ctypes_ext as ctypes_ext")
    module_pyx_file.declarations.append("from snakes.nets import dot")
    module_pyx_file.declarations.append("import cPickle, StringIO")
    module_pyx_file.declarations.append("from neco.extsnakes import Pid\n")

    # command line imports
    for mod in config.imports:
        module_pyx_file.declarations.append("from {} import *".format(mod))

    # model imports
    module_pyx_file.declarations.extend(env.net_info.declare)

    ################################################################################
    # inline hand written code into pyx
    ################################################################################

    if config.no_stats: include_file_name = "include_no_stats.pyx"
    else:               include_file_name = "include.pyx"

    path = search_file(include_file_name, search_paths)
    include_pyx = open(path , "r")

    for line in include_pyx:
        module_pyx_file.declarations.append(line)

    ################################################################################
    # handle pxd file declarations
    ################################################################################
    module_pxd_file.declarations.append("cimport neco.ctypes.ctypes_ext as ctypes_ext\n")

    ################################################################################
    # populate bodies
    ################################################################################

    # produce marking type and related functions
    # this will populate body parts of some outputs
    env.marking_type.generate_code(env)

    # add functions to pyx file
    compiler = netir.CompilerVisitor(env)
    for node in env.function_nodes():
        module_pyx_file.body.append(compiler.compile(node))

    ################################################################################
    # produce code
    ################################################################################

    for output in env.output_provider:
        output.write(env, base_dir)

    ################################################################################
    # compile module
    ################################################################################

    if config.debug:
        print "********************************************************************************"
        print "running cython compiler"
        print "search paths: ", search_paths
        print "********************************************************************************"

    ctypes_source = search_file("ctypes.cpp", search_paths)
    sources = [base_dir + module_name + ".pyx", ctypes_source]

    macros = []
    if config.normalize_pids:
        macros.append(('USE_PIDS', '1',))

    setup(name = base_dir + module_name + ".pyx",
          cmdclass = {'build_ext': build_ext},
#          ext_modules=cythonize([ base_dir + module_name + '.pyx', ctypes_source ],
#                                includes=search_paths + [base_dir],
#                                library_dirs=search_paths + [base_dir]),
                    ext_modules = [Extension(config.out_module,    # config.output_module,
                                 sources,
                                 include_dirs = search_paths + [base_dir],
                                 define_macros = macros,
                                 # extra_compile_args=['-ggdb'],
                                 # extra_link_args=['-lctypes'],
                                 library_dirs = search_paths + [base_dir],
                                 language = 'c++')],
          script_args = ["build_ext", "--inplace"],
          options = { 'build': { 'build_base': 'build' } })

    if config.debug:
        print "********************************************************************************"

    fp, pathname, _ = imp.find_module(config.out_module)
    mod = imp.load_module(config.out_module, fp, pathname, ('.so', 'rb', imp.C_EXTENSION))
    if fp:
        fp.close()
    return mod
