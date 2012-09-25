from neco.core import CompilingEnvironment
from neco.utils import search_file
from priv import pyast
from unparse import Unparser
import ast
import imp
import netir
import nettypes
import re

class Env(CompilingEnvironment):
    """ Compiling environment used for co1mpiling with the python backend. """

    def __init__(self, word_set, marking_type):
        CompilingEnvironment.__init__(self)
        
        self.marking_type = marking_type
        self.marking_set_type = nettypes.MarkingSetType(marking_type)
        
        self._imports = set([])
        self._declarations = set([])
        self._variable_provider = []

    @property
    def variable_provider(self):
        return self._variable_provider[-1]

    def push_variable_provider(self, provider):
        self._variable_provider.append(provider)

    def pop_variable_provider(self):
        self._variable_provider.pop()

    def add_import(self, module):
        self._imports.add(module)

    def add_declaration(self, decl):
        self._declarations.add(decl)

    def gen_imports(self):
        nodes = []
        for decl in self._declarations:
            stmt = pyast.E(decl)
            nodes.append(stmt)

        for module in self._imports:
            nodes.append(ast.Import(names=[ ast.alias(name=module,
                                                           asname=None) ]))
        return nodes


def new_marking_type(name, config):
    return nettypes.StaticMarkingType(config)

def new_compiling_environment(word_set, marking_type):
    return Env(word_set, marking_type)

def compile_IR(env, config):
    search_paths = config.search_paths

    for decl in env.net_info.declare:
        env.add_declaration(decl)

    env.add_declaration("from neco.backends.python.data import multiset, dump")
    env.add_declaration("import neco.backends.python.data as data")
    env.add_declaration("from snakes.nets import *")
    env.add_declaration("import cPickle")
    env.add_declaration("import StringIO")
    env.add_declaration("from time import time")

    if config.normalize_pids:
        env.add_declaration("from neco.extsnakes import *")
        env.add_declaration("from neco.backends.python.process import PidTree")

    for mod in config.imports:
        env.add_declaration('from {} import *'.format(mod))

    compiled_nodes = []

    compiled_nodes.append(env.marking_type.generate_api(env))
    compiler = netir.CompilerVisitor(env)

    for node in env.function_nodes():
        compiled_nodes.append(compiler.compile(node))
    
    compiled_nodes = env.gen_imports() + compiled_nodes
    
    module_ast = ast.Module(body=compiled_nodes)
    module_ast = ast.fix_missing_locations(module_ast)

    module_name = config.out_module
    f = open(module_name + '.py', "w")
    Unparser(module_ast, f)

    include_file_path = search_file("include.py", search_paths)
    include_file = open(include_file_path, 'r')
    f.write('\n')
    for line in include_file:
        f.write(line)
    f.close()

    fp, pathname, description = imp.find_module(module_name)
    mod = imp.load_module(module_name, fp, pathname, description)

    if fp: fp.close()

    return mod

################################################################################
# EOF
################################################################################
