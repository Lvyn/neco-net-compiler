""" Python backend plugin. """

import ast, inspect, imp, sys
from neco.utils import Factory
import neco.config as config
import neco.core as core
import neco.core.nettypes as coretypes
import netir, nettypes
from neco.unparse import Unparser
from utils import Env
from neco.utils import flatten_ast

################################################################################

_backend_ = "python"

################################################################################

class FactoryManager(core.FactoryManager):
    """ A factory manager for the python implementation. """

    def __init__(self):
        core.FactoryManager.__init__(self)

        self.placetype_factory = nettypes.placetype_factory
        """ python place type factory """

        self.markingtype_factory = nettypes.markingtype_factory
        """ python marking type factory """

        self.markingsettype_factory = nettypes.markingsettype_factory
        """ python marking set type factory """

################################################################################

class Compiler(core.Compiler):
    """ Python compiler. """

    def __init__(self, net, factory_manager = FactoryManager(), *arg, **kargs):
        super(Compiler, self).__init__(net, factory_manager)

    def compile(self):
        env = Env(self.marking_type, self.markingset_type)

        for decl in self.net._declare:
            env.add_declaration(decl)

        env.add_declaration("from neco.backends.python.data import multiset, dump")
        env.add_declaration("from snakes.nets import *")
        env.add_declaration("import cPickle")
        env.add_declaration("import StringIO")

        for mod in config.get('imports'):
            env.add_declaration('from {} import *'.format(mod))

        #env.add_declaration("from dolev_yao import *")

        compiled_nodes = []

        compiled_nodes.append(self.marking_type.gen_api(env))
        compiler = netir.CompilerVisitor(env)
        for node in self.successor_function_nodes:
            compiled_nodes.append(compiler.compile(node))
        for node in self.process_successor_function_nodes:
            compiled_nodes.append(compiler.compile(node))
        compiled_nodes.append(compiler.compile(self.init_function_node))
        compiled_nodes.append(compiler.compile(self.main_successor_function_node))
        compiled_nodes = env.gen_imports() + compiled_nodes
        #module_ast = flatten_ast(ast.Module(body = compiled_nodes))
        module_ast = ast.Module(body = compiled_nodes)
        module_ast = ast.fix_missing_locations(module_ast)

        f = open("net.py", "w")
        Unparser(module_ast, f)

        fp, pathname, description = imp.find_module("net")
        mod = imp.load_module("net", fp, pathname, description)

        if fp: fp.close() # Since we may exit via an exception, close fp explicitly.

        return mod

################################################################################
# EOF
################################################################################
