""" Facade and CLI for neco.

This module provides a CLI for neco that supports
python 2.6 and python 2.7. This module also provides a
facade function for neco C{compile_net} that will create
a python module based on its arguments and configuration
provided to C{config} module.

The loading of the module will raise a runtime error
if loaded with wrong python version.
"""

import subprocess, re, sys
if (2,6,0) <= sys.version_info < (2, 7, 0):
    import optparse as parse
    VERSION=(2,6)
elif (2, 7, 0) < sys.version_info < (3,0,0) :
    import argparse as parse
    VERSION=(2,7)
else:
    raise  RuntimeError("unsupported python version")

import imp, cProfile, pstats, os, gc, bz2, gzip, glob
from abc import ABCMeta, abstractmethod
from time import time

import backends
import core.onesafe as onesafe
import inspect
import config
import random
from snakes.pnml import loads
logo = """
  *      *
  **____** ___   ____  ____
  */ __ \\*/ _ \\ / ___// __ \\
  / / / //  __// /__ / /_/ /
 /_/ /_/ \\___/ \\___/ \\____/

"""

g_produced_files = ["net.so",
                    "net.pyx",
                    "net_api.h",
                    "net.h",
                    "net.c",
                    "net.py",
                    "net.pyc",
                    "net.pyo",
                    "ctypes.h",
                    "ctypes_ext.pxd"]


class UnknownBackend(Exception):
    """ Exception raised when an unknown backend is requested. """

    def __init__(self, backend):
        """ Initializer.

        @param backend: backend name
        @type backend: C{str}
        """
        self.backend = backend

    def __str__(self):
        return str(self.backend)

def get_backends():
    """ Get all supported backends from backends package.

    Each backend in backends package contains a function BACKEND
    returning its name. This name is used for select the backend
    we want.

    @return: backends
    @rtype: C{dict(str -> module)}
    """
    bends = {}
    for (name, module) in inspect.getmembers(backends, inspect.ismodule):
        if hasattr(module, "_backend_"):
            bends[module._backend_] = module
    return bends

def compile_net(net, *arg, **kwargs):
    """ Compile C{net} Petri net into a Python module.

    The compiler and compilation options are these from C{config} module.
    The produced module is loaded and can be used for state space exploration.
    """
    backends = get_backends()
    backend = config.get('backend')
    try:
        compiler = backends[backend].Compiler(net, *arg, **kwargs)
    except KeyError as e:
        raise UnknownBackend(e)

    print "################################################################################"
    print "Compiling with " + backend + " backend."
    print "################################################################################"
    print "Optimise: {optimise!s:5}".format(optimise = config.get('optimise'))
    print "Debug:    {debug!s:5} \tPfe:  {pfe!s:5}".format(debug = config.get('debug'), pfe = config.get('optimise_flow'))
    print "Additional search paths:  %s" % config.get('additional_search_paths')
    print "################################################################################"

    compiler.set_marking_type_by_name("StaticMarkingType")

    if config.get('optimise'):
        compiler.add_optimisation(onesafe.OptimisationPass())

    compiler.gen_netir()
    compiler.optimise_netir()
    return compiler.compile()

def fatal_error(msg, ret=-1):
    """ Helper function for handling fatal errors.

    this function will put C{msg} in C{sys.stderr} and exit the program
    with C{ret} return value.
    """
    print >> sys.stderr, 'Error: {msg}'.format(msg=msg)
    exit(ret)

class CLIArgumentParser(object):
    """ Base class for CLI argument parsers.

    This class contains abstract methods to retrieve configuration values, and
    class variables to provide a uniform CLI with different parsers. Used
    conventions on class variables:
        - lo: long option name
        - so: short option name
        - d: default value
        - h: help message
        - m: metavariable
    """
    __metaclass__ = ABCMeta

    lo_module,  so_module,  d_module,  h_module  = '--module',           '-m',  None,   'module containing the Petri net'
    lo_netvar,  so_netvar,  d_netvar,  h_netvar  = '--net-variable',     '-n',  None,    'variable with the Petri net object'
    lo_backend, so_backend, d_backend, h_backend = '--language',         '-l', 'python', 'select backend'
    lo_opt,     so_opt,     d_opt,     h_opt     = '--optimise',         '-o',  False,   'enable optimisations'
    lo_pfe,     so_pfe,     d_pfe,     h_pfe     = '--optimise-flow',    '-f',  False,   'enable process flow elimination'
    lo_debug,   so_debug,   d_debug,   h_debug   = '--debug',            '-d',  False,   'print debug messages'
    lo_profile, so_profile, d_profile, h_profile = '--profile',          '-p',  False,   'enable profiling support'
    lo_include, so_include, d_include, h_include = '--include',          '-I',  [],      'add additional search path'
    lo_explore, so_explore, d_explore, h_explore = '--explore',          '-e',  False,   'compute state space'
    lo_atoms,   so_atoms,   d_atoms,   h_atoms   = '--atom',             '-a',  None,    'register an atomic proposition'
    lo_dump_mk, so_dump_mk, d_dump_mk, h_dump_mk = '--dump-markings',    '-k',  None,    'dump markings to file (if the file has a .bz extension it will be compressed)'
    lo_abcd,                d_abcd,    h_abcd    = '--abcd',                    None,    'specify an abcd input file'
    lo_pnml,                d_pnml,    h_pnml    = '--pnml',                    None,    'specify a pnml input / output file'
    lo_import,  so_import,  d_import,  h_import  = '--import',           '-i',  [],      'specify additionnal file to import'
    lo_clean,   so_clean,   d_clean,   h_clean   = '--clean',            '-c',  [],      'clean all produced files'
    lo_graph,   so_graph,   d_graph,   h_graph   = '--graph',            '-g',  None,    'dump marking graph'

    m_module, m_netvar, m_backend, m_include, m_atoms, m_dump_mk, m_abcd, m_pnml, m_import = 'MODULE', 'VARIABLE', 'LANGUAGE', 'PATH', 'ATOM', 'FILE', 'FILE', 'FILE', 'FILE'
    m_map_file, m_graph_file = 'MAP_FILE', 'GRAPH_FILE'

    c_backend =  ['cython', 'python'] # backend choices

    def __init__(self):
        pass

    @abstractmethod
    def module(self):  pass

    @abstractmethod
    def backend(self): pass

    @abstractmethod
    def profile(self): pass

    @abstractmethod
    def explore(self): pass

    @abstractmethod
    def atoms(self):   pass

    @abstractmethod
    def dump_markings(self): pass

    @abstractmethod
    def net_var_name(self):  pass

    @abstractmethod
    def optimise_flow(self): pass

    @abstractmethod
    def additional_search_paths(self):  pass

    @abstractmethod
    def optimise(self): pass

    @abstractmethod
    def atoms(self):    pass

    @abstractmethod
    def abcd(self): pass

    @abstractmethod
    def pnml(self): pass

class CLIArgumentParserPy2_6(CLIArgumentParser):
    """ Python2.6 CLI argument parser. """

    def __init__(self, name):
        CLIArgumentParser.__init__(self)
        parser = parse.OptionParser(name)
        parser.add_option(self.lo_module,  self.so_module,  default=self.d_module,  help=self.h_module,  dest='module',  metavar=self.m_module,  type=str)
        parser.add_option(self.lo_netvar,  self.so_netvar,  default=self.d_netvar,  help=self.h_netvar,  dest='netvar',  metavar=self.m_netvar,  type=str)
        parser.add_option(self.lo_backend, self.so_backend, default=self.d_backend, help=self.h_backend, dest='backend', metavar=self.m_backend, choices=self.c_backend)
        parser.add_option(self.lo_opt,     self.so_opt,     default=self.d_opt,     help=self.h_opt,     dest='opt',     action='store_true')
        parser.add_option(self.lo_pfe,     self.so_pfe,     default=self.d_pfe,     help=self.h_pfe,     dest='pfe',     action='store_true')
        parser.add_option(self.lo_debug,   self.so_debug,   default=self.d_debug,   help=self.h_debug,   dest='debug',   action='store_true')
        parser.add_option(self.lo_profile, self.so_profile, default=self.d_profile, help=self.h_profile, dest='profile', action='store_true')
        parser.add_option(self.lo_include, self.so_include, default=self.d_include, help=self.h_include, dest='spaths',  metavar=self.m_include, action='append')
        parser.add_option(self.lo_explore, self.so_explore, default=self.d_explore, help=self.h_explore, dest='explore', action='store_true')
        parser.add_option(self.lo_dump_mk, self.so_dump_mk, default=self.d_dump_mk, help=self.h_dump_mk, dest='dump_mk', metavar=self.m_dump_mk, type=str)
        parser.add_option(self.lo_atoms,   self.so_atoms,   default=self.d_atoms,   help=self.h_atoms,   dest='atoms',   metavar=self.m_atoms, action='append')
        parser.add_option(self.lo_abcd,    default=self.d_abcd,    help=self.h_abcd,    dest='abcd',    metavar=self.m_abcd, type=str)
        parser.add_option(self.lo_pnml,    default=self.d_pnml,    help=self.h_pnml,    dest='pnml',    metavar=self.m_pnml, type=str)
        (_, args) = parser.parse_args()
        self.args = args

    def module(self):  return self.args.module
    def debug(self):   return self.args.debug
    def backend(self): return self.args.backend
    def profile(self): return self.args.profile
    def explore(self): return self.args.explore
    def atoms(self):   return self.args.atoms
    def optimise(self):     return self.args.opt
    def dump_markings(self): return self.args.dump_mk
    def net_var_name(self):  return self.args.netvar
    def optimise_flow(self): return self.args.pfe
    def additional_search_paths(self):  return self.args.spaths
    def abcd(self): return self.args.abcd
    def pnml(self): return self.args.pnml

class CLIArgumentParserPy2_7(CLIArgumentParser):
    """ Python2.7 CLI argument parser. """

    def __init__(self, name):
        CLIArgumentParser.__init__(self)
        parser = parse.ArgumentParser(name,
                                      argument_default=parse.SUPPRESS,
                                      formatter_class=parse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(self.lo_module,  self.so_module,  default=self.d_module,  help=self.h_module,  dest='module',  metavar=self.m_module,  type=str)
        parser.add_argument(self.lo_netvar,  self.so_netvar,  default=self.d_netvar,  help=self.h_netvar,  dest='netvar',  metavar=self.m_netvar,  type=str)
        parser.add_argument(self.lo_backend, self.so_backend, default=self.d_backend, help=self.h_backend, dest='backend', metavar=self.m_backend, choices=self.c_backend)
        parser.add_argument(self.lo_opt,     self.so_opt,     default=self.d_opt,     help=self.h_opt,     dest='opt',     action='store_true')
        parser.add_argument(self.lo_pfe,     self.so_pfe,     default=self.d_pfe,     help=self.h_pfe,     dest='pfe',     action='store_true')
        parser.add_argument(self.lo_debug,   self.so_debug,   default=self.d_debug,   help=self.h_debug,   dest='debug',   action='store_true')
        parser.add_argument(self.lo_profile, self.so_profile, default=self.d_profile, help=self.h_profile, dest='profile', action='store_true')
        parser.add_argument(self.lo_include, self.so_include, default=self.d_include, help=self.h_include, dest='spaths',  metavar=self.m_include, action='append')
        parser.add_argument(self.lo_explore, self.so_explore, default=self.d_explore, help=self.h_explore, dest='explore', action='store_true')
        parser.add_argument(self.lo_dump_mk, self.so_dump_mk, default=self.d_dump_mk, help=self.h_dump_mk, dest='dump_mk', metavar=self.m_dump_mk, type=str)
        parser.add_argument(self.lo_atoms,   self.so_atoms,   default=self.d_atoms,   help=self.h_atoms,   dest='atoms',   metavar=self.m_atoms,   action='append')
        parser.add_argument(self.lo_abcd,    default=self.d_abcd,    help=self.h_abcd,    dest='abcd',    metavar=self.m_abcd, type=str)
        parser.add_argument(self.lo_pnml,    default=self.d_pnml,    help=self.h_pnml,    dest='pnml',    metavar=self.m_pnml, type=str)
        parser.add_argument(self.lo_import,  self.so_import,  default=self.d_import,  help=self.h_import,  dest='imports', metavar=self.m_import, action='append')
        parser.add_argument(self.lo_clean,   self.so_clean,   default=self.d_clean,   help=self.h_clean,   dest='clean',   action='store_true')
        parser.add_argument(self.lo_graph,   self.so_graph,   default=self.d_graph,   help=self.h_graph,   dest='graph',   nargs=2, metavar=(self.m_map_file,
                                                                                                                                             self.m_graph_file))
        self.args = parser.parse_args()

    def module(self):  return self.args.module
    def debug(self):   return self.args.debug
    def backend(self): return self.args.backend
    def profile(self): return self.args.profile
    def explore(self): return self.args.explore
    def atoms(self):   return self.args.atoms
    def optimise(self):     return self.args.opt
    def dump_markings(self): return self.args.dump_mk
    def net_var_name(self):  return self.args.netvar
    def optimise_flow(self): return self.args.pfe
    def additional_search_paths(self):  return self.args.spaths
    def abcd(self): return self.args.abcd
    def pnml(self): return self.args.pnml
    def imports(self): return self.args.imports
    def clean(self): return self.args.clean
    def graph(self): return self.args.graph


def produce_pnml_file(abcd_file, pnml_file = None):
    random.seed(time())
    out_pnml = pnml_file if pnml_file != None else "/tmp/model{}.pnml".format(random.random())
    if os.path.exists(out_pnml):
        print >> sys.stderr, "ERROR: {} file already exists".format(out_pnml)
        exit(-1)

    from snakes.utils.abcd.main import main
    if pnml_file:
        print "generating {} file from {}".format(out_pnml, abcd_file)
    else:
        print "generating pnml file from {}".format(abcd_file)

    main(['--pnml={}'.format(out_pnml), abcd_file])
    return out_pnml

def load_pnml_file(pnml_file, remove = False):
    print "loading pnml file"
    net = loads(pnml_file)
    if remove:
        print "deleting pnml file"
        os.remove(pnml_file)
    return net

def load_snakes_net(module_name, net_var_name):
    try:
        fp, pathname, description = imp.find_module(module_name)
    except ImportError as e:
        fatal_error(str(e))

    module = imp.load_module(module_name, fp, pathname, description)
    fp.close()

    try:
        # return the net from the module
        return getattr(module, net_var_name)
    except AttributeError:
        fatal_error('No variable named {varname} in module {module}'.format(varname=net_var_name,
                                                                            module=module_name))


def try_open_file(file_name):
    try:
        std_map = { 'stdout' : sys.stdout, 'stderr' : sys.stderr }
        out_file = std_map[file_name]
    except KeyError:
        basename, extension = os.path.splitext(file_name)
        if extension == '.bz2':
            print "bz2 compression enabled for file {}".format(file_name)
            out_file = bz2.BZ2File(file_name, 'w', 2048, compresslevel=6)
        elif extension == '.gz':
            print "gzip compression enabled for file {}".format(file_name)
            out_file = gzip.GzipFile(file_name, 'w', compresslevel=6)
        elif extension == '':
            print "raw text output for file {}".format(file_name)
            out_file = open(file_name, 'w')
        else:
            print >> sys.stderr, "unsupported extension: {}".format(extension)
            print >> sys.stderr, "supported extensions: .bz2 .gz"
            exit(-1)
    return out_file


class Driver(object):
    """ CLI entry point.
    """

    _instance_ = None # unique instance

    def __init__(self, name = "Driver"):
        """ Initializer.

        Runs the CLI argument parser and runs desired operation based on arguments.
        """

        #print logo
        print "{name} uses python {version}".format(name=name, version=sys.version)
        assert(not self.__class__._instance_) # assert called only once
        self.__class__._instance_ = self # setup the unique instance

        if VERSION == (2,6):
            cli_argument_parser = CLIArgumentParserPy2_6(name)
        elif VERSION == (2,7):
            cli_argument_parser = CLIArgumentParserPy2_7(name)
        else:
            raise RuntimeError("unreachable")

        config.set(debug    = cli_argument_parser.debug(),
                   optimise = cli_argument_parser.optimise(),
                   backend  = cli_argument_parser.backend(),
                   profile  = cli_argument_parser.profile(),
                   imports  = cli_argument_parser.imports(),
                   optimise_flow = cli_argument_parser.optimise_flow(),
                   additional_search_paths  = cli_argument_parser.additional_search_paths(),
                   trace_calls = False)

        self.lang          = cli_argument_parser.backend()
        self.atoms         = cli_argument_parser.atoms()
        self.profile       = cli_argument_parser.profile()
        self.do_explore    = cli_argument_parser.explore()
        self.module_name   = cli_argument_parser.module()
        self.net_var_name  = cli_argument_parser.net_var_name()
        if not self.net_var_name:
            self.net_var_name = 'net'
        self.dump_markings = cli_argument_parser.dump_markings()
        self.abcd          = cli_argument_parser.abcd()
        self.pnml          = cli_argument_parser.pnml()
        self.do_clean      = cli_argument_parser.clean()

        graph = cli_argument_parser.graph()
        if graph:
            self.map_file, self.graph_file = graph
            self.graph = True
        else:
            self.graph = False

        ################################################################################
        # check options
        ################################################################################
        if self.module_name:
            if self.abcd:
                fatal_error("A snakes module cannot be used with an abcd file.")
            elif self.pnml:
                fatal_error("A snakes module cannot be used with a pnml file.")

        if self.do_explore:
            if self.graph:
                fatal_error("explore option cannot be used with graph option.")
            if self.dump_markings:
                fatal_error("explore option cannot be used with dump markings option.")

        if self.dump_markings:
            if self.graph:
                fatal_error("dump markings option cannot be used with graph option.")



        # retrieve the Petri net from abcd file (produces a pnml file)
        remove_pnml = not self.pnml
        if self.abcd:
            self.pnml = produce_pnml_file(self.abcd, self.pnml)

        # retrieve the Petri net from pnml file
        if self.pnml:
            self.petri_net = load_pnml_file(self.pnml, remove_pnml)

        # retrieve the Petri net from module
        else:
            self.petri_net = load_snakes_net(self.module_name, self.net_var_name)

        if self.profile:
            # produce compiler trace
            import cProfile
            cProfile.run('driver.Driver._instance_.compile()', 'compile.prof')
            if self.do_explore:
                # produce exploration trace
                cProfile.run('driver.Driver._instance_.explore()', 'explore.prof')

            elif self.dump_markings:
                # produce exploration trace with marking dump
                cProfile.run('driver.Driver._instance_.dump_markings()', 'explore_dump.prof')

            elif self.graph:
                # produce exploration trace with reachability graph
                cProfile.run('driver.Driver._instance_.explore_graph()', 'explore_graph.prof')

        else: # without profiler
            self.compile()
            if self.do_explore:
                self.explore()

            elif self.dump_markings:
                self.explore_dump()

            elif self.graph:
                self.explore_graph()

        if self.do_clean:
            print "cleaning files..."
            files = g_produced_files
            files.extend(glob.glob('*.pyc'))
            for f in files:
                try:   os.remove(f)
                except OSError: pass # ignore error

    def compile(self):
        """ Compile the model. """
        for f in g_produced_files:
            try:   os.remove(f)
            except OSError: pass # ignore errors

        start = time()
        self.compiled_net = compile_net(net = self.petri_net,
                                        atoms = self.atoms)
        end = time()

        if not self.compiled_net:
            print "Error during compilation."
            exit(-1)
        print "compilation time: ", end - start
        return end - start


    def explore(self):
        """ Explore state space. """

        net = self.compiled_net
        if self.lang == "cython":
            start = time()
            ss = net.state_space()
            end = time()
            print "exploration time: ", end - start
            print "len visited = %d" % (len(ss))

        else:
            visited = set()
            visit = set([net.init()])
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
                    succ = net.succs(m)
                    succs2 = succ.difference(visited)
                    visit.update(succs2)
                    succ.clear()
                    succs2.clear()
                    if (count % 100 == 0):
                        new_time = time()
                        elapsed_time = new_time - start
                        sys.stdout.write("\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)".format(count,
                                                                                                                   elapsed_time,
                                                                                                                   count / elapsed_time,
                                                                                                                   100/(new_time-last_time)))
                        sys.stdout.flush()
                        last_time = new_time

            except KeyError:
                end = time()
                print
                print "exploration time: ", end - start
                print "len visited = %d" % (len(visited))

            return (end - start, visited)


    def explore_dump(self):
        """ Explore state space. """

        dfile = try_open_file(self.dump_markings)

        net = self.compiled_net
        if self.lang == "cython":
            start = time()
            ss = net.state_space()
            end = time()
            print "exploration time: ", end - start
            print "len visited = %d" % (len(ss))

            dfile.write('[')
            for s in ss:
                dfile.write(s.__dump__())
                dfile.write(', ')
            dfile.write(']')
            return (end - start, ss)
        else:
            visited = set()
            visit = set([net.init()])
            visit2  = set()
            succ = set()
            inter = set()
            succs2 = set()
            count = 0
            last_count = 0
            start = time()
            last_time = start
            to_print = []

            dfile.write('[')
            try:
                while True:
                    m = visit.pop()
                    to_print.append(m)
                    count+=1

                    visited.add(m)
                    succ = net.succs(m)
                    succs2 = succ.difference(visited)
                    visit.update(succs2)
                    succ.clear()
                    succs2.clear()
                    if (count % 100 == 0):
                        new_time = time()
                        elapsed_time = new_time - start
                        sys.stdout.write("\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)".format(count,
                                                                                                                   elapsed_time,
                                                                                                                   count / elapsed_time,
                                                                                                                   100/(new_time-last_time)))
                        sys.stdout.flush()
                        last_time = new_time

                        for s in to_print:
                            dfile.write(s.__dump__())
                            dfile.write(', ')
                        to_print = []
            except KeyError:
                end = time()
                print
                print "exploration time: ", end - start
                print "len visited = %d" % (len(visited))

            for s in to_print:
                dfile.write(s.__dump__())
                dfile.write(', ')
            dfile.write(']')
            dfile.close()
            return (end - start, visited)

    def explore_graph(self):
        """ Explore state space. """

        # select output stream
        map_file   = try_open_file(self.map_file)
        graph_file = try_open_file(self.graph_file)

        net = self.compiled_net
        if self.lang == "cython":
            start = time()
            graph, map = net.state_space_graph()
            end = time()
            print "exploration time: ", end - start
            print "len visited = %d" % (len(map.keys()))

            #map_file.write('{\n')
            for key, value in map.iteritems():
                map_file.write("{} : {}\n".format(repr(value), key.__dump__()))
            #map_file.write('}\n')

            #graph_file.write('{\n')
            for key, value in graph.iteritems():
                graph_file.write("{} : {}\n".format(repr(key), repr(value)))
            #graph_file.write('}\n')

            return (end - start, graph.keys())
        else:
            visited = set()
            visit = set()
            visit2  = set()
            succ = set()
            inter = set()
            succs2 = set()
            count = 0
            last_count = 0
            start = time()
            last_time = start

            graph = {}
            mrk_id_map = {}

            next = 1
            m = net.init()
            visit.add(m)
            mrk_id_map[m] = next
            next += 1

            try:
                while True:
                    count+=1
                    m = visit.pop()
                    visited.add(m)

                    current_node_id = mrk_id_map[m]
                    succ = net.succs(m)
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

                    if (count % 100 == 0):
                        new_time = time()
                        elapsed_time = new_time - start
                        sys.stdout.write("\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)".format(count,
                                                                                                                   elapsed_time,
                                                                                                                   count / elapsed_time,
                                                                                                                   100/(new_time-last_time)))
                        sys.stdout.flush()
                        last_time = new_time

            except KeyError:
                end = time()
                print
                print "exploration time: ", end - start
                print "len visited = %d" % (len(visited))

            #map_file.write('{\n')
            for key, value in mrk_id_map.iteritems():
                map_file.write("{} : {}\n".format(repr(value), key.__dump__()))
            #map_file.write('}\n')

            #graph_file.write('{\n')
            for key, value in graph.iteritems():
                graph_file.write("{} : {}\n".format(repr(key), repr(value)))
            #graph_file.write('}\n')

            return (end - start, visited)

################################################################################
# EOF
################################################################################

