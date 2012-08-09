""" Python backend plugin. """

from Cython.Distutils import build_ext
from distutils.core import setup
from distutils.extension import Extension
from neco import config
from neco.backends.cython import netir
from neco.backends.cython.priv import common, cyast
from neco.utils import flatten_ast, search_file
import imp
import nettypes
import os
import sys
import time

_backend_ = "cython"

def new_marking_type(name, config):
    return nettypes.StaticMarkingType(config)

def new_compiling_environment(word_set, marking_type):
    env = common.CompilingEnvironment(word_set, marking_type, nettypes.MarkingSetType(marking_type))
    # register this marking type as a cython
    # class, will be used instead of object
    env.register_cython_type(marking_type.type, "Marking")
    return env


def compile_IR(env, config):
    search_paths = config.search_paths
    module_name = config.out_module

    for decl in env.net_info.declare:
        env.add_pyx_declaration(decl)

    env.add_pyx_declaration("import neco.ctypes")
    env.add_pyx_declaration("cimport neco.ctypes.ctypes_ext as ctypes_ext")
    env.add_pyx_declaration("from snakes.nets import dot")
    env.add_pyx_declaration("import cPickle, StringIO")

    for mod in config.imports:
        env.add_pyx_declaration("from {} import *".format(mod))

    compiled_nodes = []
    # gen types
    compiled_nodes.append(env.marking_type.generate_api(env))
    compiler = netir.CompilerVisitor(env)

    base_dir = "build/"
    try:
        os.mkdir(base_dir)
    except OSError:
        pass
    
    # net.pxd
    f = open(base_dir + module_name + ".pxd", "w")
    f.write("cimport neco.ctypes.ctypes_ext as ctypes_ext\n")

    cyast.Unparser(env.marking_type.generate_pxd(env), f)
    f.close()

    for node in env.function_nodes():
        compiled_nodes.append(compiler.compile(node))
    compiled_nodes = flatten_ast(compiled_nodes)

    module_ast = cyast.Module(body=compiled_nodes)

    f = open(base_dir + module_name + ".pyx", "w")
    if config.no_stats:
        file_name = "include_no_stats.pyx"
    else:
        file_name = "include.pyx"

    path = search_file(file_name, search_paths)
    include_pyx = open(path , "r")

    if config.profile:
        print "PROFILE"
        f.write("# cython: profile=True\n")

    f.write("# cython: boundscheck=False\n")
    f.write("# cython: cdivision=True\n")

    f.write("from neco.extsnakes import Pid\n")
    f.write(env.pyx_declarations)

    for line in include_pyx:
        f.write(line)

    cyast.Unparser(module_ast, f)

    f.write(env.ending_pyx_declarations)
    
    if config.debug:
        print "********************************************************************************"
        print "running cython compiler"
        print search_paths
        print "********************************************************************************"


    ctypes_source = search_file("ctypes.c", search_paths)
    setup(name=base_dir + module_name + ".pyx",
          cmdclass={'build_ext': build_ext},
          ext_modules=[Extension(config.out_module, #config.output_module,
                                 [base_dir + module_name + ".pyx", ctypes_source ],
                                 include_dirs=search_paths + [base_dir],
                                 #extra_compile_args=['-ggdb'],
                                 #extra_link_args=['-lctypes'],
                                 library_dirs=search_paths + [base_dir])],
          script_args=["build_ext", "--inplace"],
          options={ 'build': { 'build_base': 'build' } })

    if config.debug:
        print "********************************************************************************"

    
    fp, pathname, _ = imp.find_module(config.out_module)
    mod = imp.load_module(config.out_module, fp, pathname, ('.so', 'rb', imp.C_EXTENSION))
    if fp:
        fp.close()
    return mod
