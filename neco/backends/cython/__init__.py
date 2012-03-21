""" Python backend plugin. """

import ast, inspect, sys, shutil, imp
from os.path import exists, abspath
from string import join

from Cython.Distutils import build_ext
from distutils.core import setup
from distutils.extension import Extension

from neco.utils import Factory, flatten_ast
import neco.core as core
import neco.core.nettypes as coretypes
import netir, nettypes
import neco.config as config
from nettypes import register_cython_type, is_cython_type, Env
from cyast import Builder, E, Unparser, to_ast

_backend_ = "cython"

from check_impl import *

################################################################################

class FactoryManager(core.FactoryManager):
    """ A factory manager for the python implementation. """

    def __init__(self):
        core.FactoryManager.__init__(self)

        placetype_products = []
        markingtype_products = []
        markingsettype_products = []
        for _, obj in inspect.getmembers(nettypes, inspect.isclass):
            if issubclass(obj, coretypes.PlaceType):
                placetype_products.append(obj)
            elif issubclass(obj, coretypes.MarkingType):
                markingtype_products.append(obj)
            elif issubclass(obj, coretypes.MarkingSetType):
                markingsettype_products.append(obj)

        #print placetype_products
        self.placetype_factory = Factory(placetype_products)
        """ python place type factory """

        self.markingtype_factory = Factory(markingtype_products)
        """ python marking type factory """

        self.markingsettype_factory = Factory(markingsettype_products)
        """ python marking set type factory """

        # add IntPlaceType to select
        select_type = self.select_type
        def select_type_new(info):
            # if info.type.is_Int: # and not info.is_OneSafe:
            #     return "IntPlaceType"
            # elif info.type.is_BlackToken: # and not info.is_OneSafe:
            #     return "BTPlaceType"
            # else:
            return select_type(info)
        self.select_type = select_type_new

################################################################################

def search_file(filename, paths):
    for path in paths:
        if path[-1] != '/':
            path += '/'
        path = "".join([path, filename])
        if exists(path):
            return abspath(path)

    raise IOError('{} file not found, check additional search paths'.format(filename))

class Compiler(core.Compiler):
    """ Cython compiler. """

    def __init__(self, net, factory_manager = FactoryManager(), *args, **kwargs):
        super(Compiler, self).__init__(net, factory_manager, *args, **kwargs)
        self.additional_search_paths = config.get('additional_search_paths')
        self.additional_search_paths.append(".")

    def compile(self):
        env = Env(self.global_names, self.marking_type, self.markingset_type)

        for (function_name, process_name) in self.successor_functions:
            env.add_successor_function( function_name, process_name )

        for decl in self.net._declare:
            env.add_pyx_declaration(decl)

        env.add_pyx_declaration("cimport ctypes_ext")
        env.add_pyx_declaration("from snakes.nets import dot")
        env.add_pyx_declaration("import ctypes_ext, cPickle, StringIO")

        for mod in config.get('imports'):
            env.add_pyx_declaration("from {} import *".format(mod))

        compiled_nodes = []
        # gen types
        self.marking_type.atoms = self.atoms
        compiled_nodes.append(self.marking_type.gen_api(env))
        compiler = netir.CompilerVisitor(env)

        # net.pxd
        f = open("net.pxd", "w")
        f.write("cimport ctypes_ext\n")

        Unparser(self.marking_type.gen_pxd(env), f)
        f.close()

        for node in self.successor_function_nodes:
            compiled_nodes.append( compiler.compile(node) )

        for node in self.process_successor_function_nodes:
            compiled_nodes.append( compiler.compile(node) )

        compiled_nodes.append( compiler.compile(self.init_function_node) )
        compiled_nodes.append( compiler.compile(self.main_successor_function_node) )

        compiled_nodes = flatten_ast( compiled_nodes )

        module_ast = ast.fix_missing_locations(ast.Module(body = compiled_nodes))

        f = open("net.pyx", "w")
        file_name = "include.pyx"

        path = search_file(file_name, self.additional_search_paths)
        include_pyx = open(path , "r")

        if config.get('profile'):
            print "PROFILE"
            f.write("# cython: profile=True\n")

        f.write("from neco.extsnakes import Pid\n")
        f.write(env.pyx_declarations)

        for line in include_pyx:
            f.write(line)

        Unparser(module_ast, f)

        f.write(env.ending_pyx_declarations)

        path = search_file("ctypes_ext.pxd", self.additional_search_paths)
        shutil.copyfile(path, "ctypes_ext.pxd")

        path = search_file("ctypes.h", self.additional_search_paths)
        shutil.copyfile(path, "ctypes.h")

        f = open("ctypes_ext.pxd", "a")
        f.write( env.pxd_declarations )
        f.close()

        if config.get('debug'):
            print "********************************************************************************"
            print "running cython compiler"
            print self.additional_search_paths
            print "********************************************************************************"

        setup(name="net.pyx",
              cmdclass={'build_ext': build_ext},
              ext_modules=[Extension("net", ["net.pyx"],
                                     include_dirs = self.additional_search_paths,
                                     extra_compile_args=[], # '-ggdb'],
                                     extra_link_args=['-lctypes'],
                                     library_dirs = self.additional_search_paths)],
              script_args=["build_ext", "--inplace"])

        if config.get('debug'):
            print "********************************************************************************"

        fp, pathname, description = imp.find_module("net")
        self.produce_compilation_trace(config.get('trace_file'))

        print "net"
        try:
            return imp.load_dynamic("net", pathname, fp)
        finally:
            if fp:
                fp.close()

        return None

################################################################################
# EOF
################################################################################
