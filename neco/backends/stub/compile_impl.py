from neco.core import CompilingEnvironment
from neco.utils import search_file
from unparse import Unparser
import netir
import nettypes

import neco.asdl.stub as stub_ast

class Env(CompilingEnvironment):
    """ Compiling environment used during AST generation. 

    This basic implementation provides a standard initializer and a
    stack based variable provider.

    New functionalities  can be added if needed.
    """

    def __init__(self, config, net_info, word_set, marking_type):
        """ Create a new Env.

        \param config        tool configuration
        \param net_info      Petri net information
        \param word_set      used names set
        \param marking_type  marking type from nettypes
        """
        CompilingEnvironment.__init__(self, config, net_info)
        
        self.marking_type = marking_type
        self.marking_set_type = nettypes.MarkingSetType(marking_type)

        self._variable_provider = []

    @property
    def variable_provider(self):
        """ Get Current variable provider. """
        return self._variable_provider[-1]

    def push_variable_provider(self, provider):
        """ push a variable provider. """
        self._variable_provider.append(provider)

    def pop_variable_provider(self):
        """ pop last variable provider. """
        self._variable_provider.pop()


def new_marking_type(name, config):
    """ Create a new marking type.

    This function simply forwards creation to nettypes.
    """
    return nettypes.MarkingType(config)

def new_compiling_environment(config, net_info, word_set, marking_type):
    """ Create a new compiling environment. """
    return Env(config, net_info, word_set, marking_type)

def compile_IR(env, config, compiler_):
    """ Compile Neco intermediate representation. """
    search_paths = config.search_paths

    ################################################################################
    # gen AST
    ################################################################################

    for mod in config.imports:
        # handle additional imports        
        pass

    for name, value  in compiler_.net.globals:
        # handle globals
        pass
        
    compiled_nodes = [] # list of top level AST nodes

    try:
        # generate marking type API
        compiled_nodes.append( env.marking_type.generate_api(env) )
    except NotImplementedError:
        print "marking_type.generate_api not implemented"
        
    try:
        # transform Neco intermediate representation
        compiler = netir.CompilerVisitor(env, config)
        
        for node in env.function_nodes():
            compiled_nodes.append(compiler.compile(node))

    except NotImplementedError:
        print "netir.CompilerVisitor not implemented"
        compiled_nodes.append(stub_ast.Stub([stub_ast.StubDef("test",
                                                              [ stub_ast.StubEntry(["e1", "e2"]),
                                                                stub_ast.StubEntry(["e3", "e4"])]
                                                              )
                                             ]))
    

    ################################################################################
    # produce output file
    ################################################################################
    
    module_name = config.out_module
    f = open(module_name + '.stub', "w")

    # write file
    Unparser(compiled_nodes, f)

    f.write('\n')
    return None

################################################################################
# EOF
################################################################################
