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
        env.add_declaration("from time import time")

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
        module_ast = ast.Module(body = compiled_nodes)
        module_ast = ast.fix_missing_locations(module_ast)

        f = open("net.py", "w")
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

        fp, pathname, description = imp.find_module("net")
        mod = imp.load_module("net", fp, pathname, description)

        if fp: fp.close() # Since we may exit via an exception, close fp explicitly.

        return mod

################################################################################
# EOF
################################################################################
