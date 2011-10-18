""" Python plugin utilities. """

import ast, cyast
import neco.core.netir as coreir
import inspect, types

from cyast import to_ast

################################################################################

def _str_list_to_endlstr(list):
    list.append("")
    ret = "\n".join( list )
    list.pop(-1)
    return ret

class Env(object):
    """ Compiling environment used for compiling with Cython backend. """

    def __init__(self, word_set, marking_type, marking_set_type):
        self._word_set = word_set
        self._marking_type = marking_type
        self._marking_set_type = marking_set_type

        self._pyx_declarations = []
        self._ending_pyx_declarations = []
        self._pxd_declarations = []
        self._c_declarations = []

        self._successor_functions = []

        self._cvar_decl = []
        self._variable_providers = []

    def declare_cvar(self, name, type):
        self._cvar_decl[-1].add(cyast.CVar(name, type))

    def push_cvar_env(self):
        self._cvar_decl.append(set())

    def pop_cvar_env(self):
        return self._cvar_decl.pop()

    def push_variable_provider(self, variable_provider):
        self._variable_providers.append(variable_provider)

    def pop_variable_provider(self):
        return self._variable_providers.pop()

    @property
    def variable_provider(self):
        return self._variable_providers[-1]

    ################################################################################

    def new_variable(self, base=""):
        """

        @param self:
        @type self: C{}
        @param base:
        @type base: C{}
        """
        return self._word_set.fresh(base)

    @property
    def marking_type(self):
        return self._marking_type

    @property
    def marking_set_type(self):
        return self._marking_set_type

    ################################################################################

    def add_pyx_declaration(self, decl):
        self._pyx_declarations.append(decl)

    @property
    def pyx_declarations(self):
        return _str_list_to_endlstr(self._pyx_declarations)

    def add_ending_pyx_declaration(self, decl):
        self._ending_pyx_declarations.append(to_ast(decl))

    @property
    def ending_pyx_declarations(self):
        return _str_list_to_endlstr(self._ending_pyx_declarations)

    ################################################################################

    def add_pxd_declaration(self, decl, unique = False):
        if unique and decl in self._pxd_declarations:
            return
        self._pxd_declarations.append(to_ast(decl))


    @property
    def pxd_declarations(self):
        return _str_list_to_endlstr(self._pxd_declarations)

    ################################################################################

    def add_successor_function(self, function_name, process):
        self._successor_functions.append( (function_name, process) )

    @property
    def successor_functions(self):
        return self._successor_functions

################################################################################

class CVarSet(object):

    def __init__(self, iterable = []):
        """ Initialize the set.

        @param iterable: iterable object containing initial elements.
        """
        s = set()
        names = set()
        for i in iterable:
            s.add(i)
            names.add(i.name)

        self._set = s
        self._names = names

    def add(self, elt):
        """ Add an element into the set.

        @param elt: CVar to add
        """
        name = elt.name
        names = self._names
        if not (name in names):
            names.add(name)
            self._set.add(elt)

    def __iter__(self):
        return self._set.__iter__()

    def __contains__(self, elt):
        return not (elt.name in self._names)

################################################################################
# EOF
################################################################################

