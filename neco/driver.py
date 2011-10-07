""" Facade and CLI for neco.

This module provides a CLI for neco that supports
python 2.6 and python 2.7. This module also provides a
facade function for neco C{neco_compile} that will create
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

import imp, cProfile, pstats, os, gc
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

def neco_compile(net, *arg, **kwargs):
    """ Compile C{net} Petri net into a Python module.

    The compiler and compilation options are these from C{config} module.
    The produced module is loaded and can be used for state space exploration.
    """
    backends = get_backends()
    backend = config.get('backend')
    try:
        compiler = backends[backend].Compiler(net, *arg, **kwargs)
    except KeyError as e:
        raise UnknownBackend(backend)

    print "################################################################################"
    print "Compiling with " + backend + " backend."
    print "################################################################################"
    print "Optimise: {optimise!s:5}".format(optimise = config.get('optimise'))
    print "Debug:    {debug!s:5} \tPfe:  {pfe!s:5}".format(debug = config.get('debug'), pfe = config.get('process_flow_elimination'))
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

    lo_module,  so_module,  d_module,  h_module  = '--module',           '-m', 'spec',   'module containing the Petri net'
    lo_netvar,  so_netvar,  d_netvar,  h_netvar  = '--net-variable',     '-n', 'net',    'variable with the Petri net object'
    lo_backend, so_backend, d_backend, h_backend = '--language',         '-l', 'python', 'select backend'
    lo_opt,     so_opt,     d_opt,     h_opt     = '--optimise',         '-o',  False,   'enable optimisations'
    lo_pfe,     so_pfe,     d_pfe,     h_pfe     = '--flow-elimination', '-f',  False,   'enable process flow elimination'
    lo_debug,   so_debug,   d_debug,   h_debug   = '--debug',            '-g',  False,   'print debug messages'
    lo_profile, so_profile, d_profile, h_profile = '--profile',          '-p',  False,   'enable profiling support'
    lo_include, so_include, d_include, h_include = '--include',          '-I',  [],      'add additional search path'
    lo_explore, so_explore, d_explore, h_explore = '--explore',          '-e',  False,   'compute state space'
    lo_atoms,   so_atoms,   d_atoms,   h_atoms   = '--atom',             '-a',  None,    'register an atomic proposition'
    lo_dump_mk, so_dump_mk, d_dump_mk, h_dump_mk = '--dump-markings',    '-k',  None,    'dump markings to file'
    lo_abcd,                d_abcd,    h_abcd    = '--abcd',                    None,    'specify an abcd input file'
    lo_pnml,                d_pnml,    h_pnml    = '--pnml',                    None,    'specify a pnml input / output file'
    lo_import,  so_import,  d_import,  h_import  = '--import',           '-i',  [],      'specify additionnal file to import'

    m_module, m_netvar, m_backend, m_include, m_atoms, m_dump_mk, m_abcd, m_pnml, m_import = 'MODULE', 'VARIABLE', 'LANGUAGE', 'PATH', 'ATOM', 'FILE', 'FILE', 'FILE', 'FILE'

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
    def process_flow_elimination(self): pass

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
    def process_flow_elimination(self): return self.args.pfe
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
    def process_flow_elimination(self): return self.args.pfe
    def additional_search_paths(self):  return self.args.spaths
    def abcd(self): return self.args.abcd
    def pnml(self): return self.args.pnml
    def imports(self): return self.args.imports

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
                   process_flow_elimination = cli_argument_parser.process_flow_elimination(),
                   additional_search_paths  = cli_argument_parser.additional_search_paths(),
                   trace_calls = False)

        self.lang          = cli_argument_parser.backend()
        self.atoms         = cli_argument_parser.atoms()
        self.profile       = cli_argument_parser.profile()
        self.do_explore    = cli_argument_parser.explore()
        self.module_name   = cli_argument_parser.module()
        self.net_var_name  = cli_argument_parser.net_var_name()
        self.dump_markings = cli_argument_parser.dump_markings()
        self.abcd          = cli_argument_parser.abcd()
        self.pnml          = cli_argument_parser.pnml()


        # retrieve the Petri net from abcd file (produces a pnml file)
        if self.abcd:
            random.seed(time())
            out_pnml = self.pnml if self.pnml != None else "/tmp/model{}.pnml".format(random.random())
            if self.pnml and os.path.exists(out_pnml):
                print >> sys.stderr, "ERROR: {} file already exists".format(out_pnml)
                exit(-1)

            from snakes.utils.abcd.main import main
            if self.pnml:
                print "generating {} file from {}".format(out_pnml, self.abcd)
            else:
                print "generating pnml file from {}".format(self.abcd)
            main(['--pnml={}'.format(out_pnml), self.abcd])
            print "loading pnml file"
            self.petri_net = loads(out_pnml)
            if not self.pnml:
                print "deleting pnml file"
                os.remove(out_pnml)

        # retrieve the Petri net from pnml file
        elif self.pnml:
            print "loading pnml file"
            self.petri_net = loads(self.pnml)

        # retrieve the Petri net from module
        else:
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
            # profile compilation
            import cProfile
            cProfile.run('driver.Driver._instance_.compile()', 'compile.prof')
            # profile exploration
            if self.do_explore:
                cProfile.run('driver.Driver._instance_.explore()', 'explore.prof')
        else:
            self.compile()
            if self.do_explore or self.dump_markings:
                t, visited = self.explore()
                if self.dump_markings:
                    # select output stream
                    try:
                        std_map = { 'stdout' : sys.stdout, 'stderr' : sys.stderr }
                        dfile = std_map[self.dump_markings]
                    except KeyError:
                        dfile = open(self.dump_markings, 'w')

                    # write data
                    dfile.write("check - markings\n")
                    dfile.write("count - %d\n" % len(visited))
                    for s in visited:
                        dfile.write(s.__dump__())
                    # close stream
                    dfile.close()

    def compile(self):
        """ Compile the model. """
        files = ["net.so", "net.pyx", "net.c", "net.py", "net.pyc", "net.pyo"]
        for f in files:
            try:   os.remove(f)
            except OSError: pass # ignore errors

        start = time()
        self.compiled_net = neco_compile(net = self.petri_net,
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
            return (end - start, ss)
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
                    count+=1
                    visited.add(m)
                    succ = net.succs(m)
                    succs2 = succ.difference(visited)
                    visit.update(succs2)
                    succ.clear()
                    succs2.clear()
                    if (count % 100 == 0):
                        sys.stdout.write("\r{} ({:.3f}s)".format(count, (time() - start)))
                        sys.stdout.flush()
            except KeyError:
                end = time()
                print "exploration time: ", end - start
                print "len visited = %d" % (len(visited))
            return (end - start, visited)

################################################################################
# EOF
################################################################################

