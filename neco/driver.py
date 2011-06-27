import subprocess, re, sys, argparse
import imp, cProfile, pstats
from time import time
import os, gc

import backends
import opt.onesafe as onesafe
import inspect
import config

logo = """
  *      *
  **____** ___   ____  ____
  */ __ \\*/ _ \\ / ___// __ \\
  / / / //  __// /__ / /_/ /
 /_/ /_/ \\___/ \\___/ \\____/

"""


class UnknownBackend(Exception):
    """ Exception raised on a unknown backend """

    def __init__(self, backend):
        """

        @param backend:
        @type backend: C{}
        """
        self.backend = backend

    def __str__(self):
        return str(self.backend)

def get_backends():
    """ Get all supported backends from backends

    Each backend package contains a function BACKEND returning its name. This name
    is used for select the backent we want.

    @return: backends
    @rtype: C{dict(str -> module)}
    """
    bends = {}
    for (name, module) in inspect.getmembers(backends, inspect.ismodule):
        if hasattr(module, "_backend_"):
            bends[module._backend_] = module
    return bends

def neco_compile(net, *arg, **kwargs):
    """ Compile a petrinet into a module.

    The produced module can be used for model state space exploration.

    TODO: update doc

    @param net: a Petri net
    @type net: C{snakes.nets.PetriNet}
    @return: code object representing the module
    @rtype: C{code object}
    """
    backends = get_backends()
    backend = config.get('backend')
    try:
        compiler = backends[backend].Compiler(net, *arg, **kwargs)
    except KeyError as e:
        print e
        raise UnknownBackend(backend)

    print "################################################################################"
    print "Compiling with " + backend + " backend."
    print "################################################################################"
    print "Optimise: {optimise!s:5} \tDump: {dump!s:5}".format(optimise = config.get('optimise'),
                                                               dump = config.get('dump'))
    print "Debug:    {debug!s:5} \tPfe:  {pfe!s:5}".format(debug = config.get('debug'),
                                                           pfe = config.get('process_flow_elimination'))
    print "Additional search paths:  %s" % config.get('additional_search_paths')
    print "################################################################################"

    compiler.set_marking_type_by_name("StaticMarkingType")

    if config.get('optimise'):
        compiler.add_optimisation(onesafe.OptimisationPass())

    compiler.gen_netir()
    compiler.optimise_netir()
    return compiler.compile()


def fatal_error(msg):
    print >> sys.stderr, 'Error: {msg}'.format(msg=msg)
    exit(-1)

class Driver(object):
    """ Class for running the compiler.
    """

    _instance_ = None
    def __init__(self, name = "Driver"):
        """ Initialiser
        """

        #print logo
        assert(not self.__class__._instance_)
        self.__class__._instance_ = self
        parser = argparse.ArgumentParser(name,
                                         argument_default=argparse.SUPPRESS,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--module', '-m', type=str, dest='module', default='spec',
                            help='module containing the Petri net object')
        parser.add_argument('--netvar', '-nv', type=str, dest='netvar', default='net',
                            help='variable holding the Petri net object')
        parser.add_argument('--lang', '-l', dest='backend', choices=['cython', 'python'], default='python',
                            help='select backend')
        parser.add_argument('--opt', '-o', dest='opt', action='store_true', default=False,
                            help='enable optimisations')
        parser.add_argument('--pfe', dest='process_flow_elimination', action='store_true', default=False,
                            help='enable process flow elimination')
        parser.add_argument('--debug', dest='debug', action='store_true', default=False,
                            help='show debug messages')
        parser.add_argument('--dump', dest='dump', action='store_true', default=False,
                            help='show produced file')
        parser.add_argument('--profile', '-p', dest='profile', action='store_true', default=False,
                            help='enable profiling')
        parser.add_argument('--Include', '-I', dest='additional_search_paths', action='append', default=[],
                            help='add additional search paths')
        args = parser.parse_args()

        config.set(debug    = args.debug,
                   dump     = args.dump,
                   optimise = args.opt,
                   backend  = args.backend,
                   profile  = args.profile,
                   process_flow_elimination = args.process_flow_elimination,
                   additional_search_paths  = args.additional_search_paths,
                   trace_calls = False)

        self.lang = args.backend
        self.profile = args.profile
        self.module_name = args.module
        self.net_var_name = args.netvar

        try:
            fp, pathname, description = imp.find_module(self.module_name)
        except ImportError as e:
            fatal_error(str(e))

        self.module = imp.load_module(self.module_name, fp, pathname, description)
        fp.close()

        try:
            self.petri_net = getattr(self.module, self.net_var_name)
        except AttributeError:
            fatal_error('No variable named {varname} in module {module}'.format(varname=self.net_var_name,
                                                                                module=self.module_name))

        if self.profile:
            self.run_profile()
        else:
            self.compile()
            self.explore()

    def run_profile(self):
        print "profiling"
        self.compile()
        cProfile.run('driver.Driver._instance_.explore()', 'profile.stats')
        s = pstats.Stats("profile.stats")
        s.strip_dirs().sort_stats("time").print_stats()

    def compile(self):
        files = ["net.so", "net.pyx", "net.c", "net.py", "net.pyc", "net.pyo"]
        for f in files:
            try:
                os.remove(f)
            except OSError:
                pass

        start = time()
        self.compiled_net = neco_compile(self.petri_net)
        end = time()

        if not self.compiled_net:
            print "Error during compilation."
            exit(-1)
        print "compilation time: ", end - start
        return end - start

    def explore(self):
        net = self.compiled_net
        if self.lang == "cython":
            start = time()
            st = net.state_space()
            end = time()
            print "exploration time: ", end - start
            print "len visited = %d" % (len(st))
            return (end - start, st)
        else:
            visited = set()
            visit = set([net.init()])
            visit2  = set()
            succ = set()
            inter = set()
            succs2 = set()
            count = 0

            start = time()
            try:
                while True:
                    m = visit.pop()
                    visited.add(m)

                    succ = net.succs(m)

                    succs2 = succ.difference(visited)
                    visit.update(succs2)

                    succ.clear()
                    succs2.clear()
            except KeyError:
                end = time()
                print "exploration time: ", end - start
                print "len visited = %d" % (len(visited))
            return (end - start, visited)
