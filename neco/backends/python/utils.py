""" Python plugin utilities. """

import ast
import astutils
import neco.core.netir as coreir
import inspect, types
from astutils import to_ast, E

################################################################################

class Env(object):
    """ Compiling environment used for co1mpiling with the python backend. """

    def __init__(self, marking_type, marking_set_type):
        self._marking_type = marking_type
        self._marking_set_type = marking_set_type
        self._imports = set([])
        self._declarations = set([])

    @property
    def marking_type(self):
        return self._marking_type

    @property
    def marking_set_type(self):
        return self._marking_set_type

    @property
    def succs(self):
        return self._succs

    def add_import(self, module):
        self._imports.add(module)

    def add_declaration(self, decl):
        self._declarations.add(decl)

    def gen_imports(self):
        nodes = []
        for decl in self._declarations:
            stmt = to_ast(E(decl))
            nodes.append( stmt )

        for module in self._imports:
            nodes.append( ast.Import( names = [ ast.alias( name = module,
                                                           asname = None ) ] ) )
        return nodes

################################################################################
# EOF
################################################################################

