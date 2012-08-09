from neco.core import CompilingEnvironment
from priv import pyast
from unparse import Unparser
import ast
import imp
import neco.config as config
import netir
import nettypes

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

    for mod in config.imports:
        env.add_declaration('from {} import *'.format(mod))

    #env.add_declaration("from dolev_yao import *")

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

    f.write("""

def state_space():
    visited = set()
    visit = set([init()])
    visit2  = set()
    succ = set()
    inter = set()
    succs2 = set()
    count = 0
    last_count = 0
    start = time()
    last_time = start

    try:
        while True:
            m = visit.pop()
            count+=1

            visited.add(m)
            succ = succs(m)
            succs2 = succ.difference(visited)
            visit.update(succs2)
            succ.clear()
            succs2.clear()
            if (count % 100 == 0):
                new_time = time()
                elapsed_time = new_time - start
                sys.stdout.write('\\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)'.format(count,
                                                                                                           elapsed_time,
                                                                                                           count / elapsed_time,
                                                                                                           100/(new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time

    except KeyError:
        pass

    return visited


def state_space_graph():
    visited = set()
    count = 0
    next = 1
    graph = {}
    mrk_id_map = {}
    succ_list = []
    start = time()
    last_time = start

    m = init()

    visit = set([m])
    mrk_id_map[m] = next
    next += 1

    try:
        while True:
            count += 1
            m = visit.pop()
            visited.add(m)

            # new marking, get the id
            current_node_id = mrk_id_map[m]
            succ = succs(m)
            succ_list = []

            for s_mrk in succ:
                if mrk_id_map.has_key(s_mrk):
                    node_id = mrk_id_map[s_mrk]
                    succ_list.append(node_id)
                else:
                    node_id = next
                    next += 1
                    succ_list.append(node_id)
                    mrk_id_map[s_mrk] = node_id

            graph[current_node_id] = succ_list

            visit.update(succ.difference(visited))
            if (count % 250 == 0):
                new_time = time()
                elapsed_time = new_time - start
                sys.stdout.write('\\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)'.format(count,
                                                                                                            elapsed_time,
                                                                                                            count / elapsed_time,
                                                                                                            250 / (new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time
    except KeyError:
        print
        return graph, mrk_id_map
    return graph, mrk_id_map

""")
    f.close()

    fp, pathname, description = imp.find_module(module_name)
    mod = imp.load_module(module_name, fp, pathname, description)

    if fp: fp.close() # Since we may exit via an exception, close fp explicitly.

    return mod

################################################################################
# EOF
################################################################################
