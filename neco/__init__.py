""" Neco package provides structures and functions for
compiling Snakes Petri nets
"""

import utils, inspect
import core, backends, config

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
    for (_, module) in inspect.getmembers(backends, inspect.ismodule):
        if hasattr(module, "_backend_"):
            bends[module._backend_] = module
    return bends

def compile_net(net, *arg, **kwargs):
    """ Compile Petri net C{net} into a Python module.

    The compiler and compilation options are these from C{config} module.
    The produced module is loaded and can be used for state space exploration.
    """
    backends = get_backends()
    backend = config.get('backend')
    try:
        compiler = core.Compiler(net, backend=backends[backend].compile_impl)
    except KeyError as e:
        raise UnknownBackend(e)

    print "################################################################################"
    print "Compiling with " + backend + " backend."
    print "################################################################################"
    print "optimisations:           {optimize!s:5}".format(optimize = config.get('optimize'))
    print "Debug:                   {debug!s:5}".format(debug = config.get('debug'))
    print "flow optimisations:      {pfe!s:5}".format(pfe=config.get('optimize_flow'))
    print "Additional search paths: %s" % config.get('additional_search_paths')
    print "################################################################################"

    # compiler.set_marking_type_by_name("StaticMarkingType")
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
