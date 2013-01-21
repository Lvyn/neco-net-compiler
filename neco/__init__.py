""" Neco package provides structures and functions for
compiling Snakes Petri nets
"""

from neco.utils import fatal_error
from snakes.pnml import loads
from time import time
import backends
import config
import core
import core.check
import imp
import inspect
import os.path
import random
import sys
import utils

g_logo = """
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
        @type_info backend: C{string}
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
    for (_, module) in inspect.getmembers(backends, inspect.ismodule):
        if hasattr(module, "_backend_"):
            bends[module._backend_] = module
    return bends

def compile_net(net, config):
    """ Compile Petri net C{net} into a Python module.

    The compiler and compilation options are these from C{config} module.
    The produced module is loaded and can be used for state space exploration.
    """
    backends = get_backends()
    backend = config.backend
    try:
        compiler = core.Compiler(net,
                                 backend=backends[backend].compile_impl,
                                 config=config)
    except KeyError as e:
        raise UnknownBackend(e)

    print "################################################################################"
    print "Compiling {!s} with {!s} backend".format(config.model, backend)
    print "################################################################################"
    print "optimisations:      {optimize!s:5}".format(optimize = config.optimize)
    print "Debug:              {debug!s:5}".format(debug = config.debug)
    print "flow optimisations: {pfe!s:5}".format(pfe=config.optimize_flow)
    print "search paths:       {}".format(config.search_paths)
    print "################################################################################"

    return compiler.run()


def compile_checker(formula, net, *arg, **kwargs):
    """ Produce checking functions for a compiled net.
    """

    #TODO: use trace file to store configuration options
    backends = get_backends()
    backend = config.get('backend')
    try:
        backend_instance = backends[backend]
    except KeyError as e:
        raise UnknownBackend(e)

    print "################################################################################"
    print "Compiling formula {} ".format(formula)
    print "################################################################################"
    
    compiler = core.check.CheckerCompiler(formula, net, backend_instance)
    return compiler.compile()


def produce_pnml_file(abcd_file, pnml_file=None):
    """ Compile an abcd file to pnml.
    """
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

def load_pnml_file(pnml_file, remove=False):
    """ Load a model from a pnml file.
    """
    print "loading pnml file"
    net = loads(pnml_file)
    if remove:
        print "deleting pnml file"
        os.remove(pnml_file)
    return net

def load_snakes_net(module_name, net_var_name):
    """ Load a model from a python module.
    """
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

