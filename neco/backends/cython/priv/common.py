
from cyast import CVar, to_ast
import cyast
from neco.core.info import TypeInfo
from neco.utils import flatten_ast, OutputProviderPredicate
import neco.core as core

def _str_list_to_endlstr(lst):
    lst.append("")
    ret = "\n".join(lst)
    lst.pop(-1)
    return ret

################################################################################
# Registered classes are used as cython classes (cdef)
################################################################################

class NecoTypeError(Exception):
    def __init__(self, expr, got, expected):
        self.expr = expr
        self.type = got
        self.expected = expected

    def __str__(self):
        return str(self.expr) + " is of type " + self.type + " but type " + self.expected + " was expected."

def from_neco_lib(f):
    return "ctypes_ext.%s" % f


################################################################################

# new types

TypeInfo.register_type("MultiSet")
TypeInfo.register_type("IntPlace")
TypeInfo.register_type("Char")
TypeInfo.register_type("Short")
TypeInfo.register_type("UnsignedInt")
TypeInfo.register_type("UnsignedChar")

TypeInfo.register_type("PidPlace")
TypeInfo.register_type("GeneratorPlace")

################################################################################

class CVars(object):

    def __init__(self, env, initial=None):
        self.env = env
        self._cvars = initial if initial else set([])


    def type(self, name):
        for n, t in self._cvars:
            if n == name:
                return t
        raise IndexError

    def update_type(self, name, typ):
        tmp = None
        for t in self._cvars:
            if t[0] == name:
                tmp = t
                break
        if tmp:
            self._cvars.remove(tmp)
            self._cvars.add((name, typ))

    def declare(self, name, typ):
        self._cvars.add((name, typ))

    def __iter__(self):
        for n, t in self._cvars:
            yield CVar(name=n, type=self.env.type2str(t))
        raise StopIteration

    def __str__(self):
        return str(self._cvars)

################################################################################

class CompilingEnvironment(core.CompilingEnvironment):
    """ Compiling environment used for compiling with Cython backend. """

    def __init__(self, word_set, marking_type, marking_set_type):
        core.CompilingEnvironment.__init__(self)
        
        self._word_set = word_set
        self._marking_type = marking_type
        self._marking_set_type = marking_set_type

        self._pyx_declarations = []
        self._ending_pyx_declarations = []
        self._pxd_declarations = []
        self._c_declarations = []

        
        self._cvar_decl = []
        self._variable_providers = []

        self._registered_cython_types = dict()

        # register types
        self.register_cython_type(TypeInfo.get('Bool'), 'short')
        self.register_cython_type(TypeInfo.get('Char'), 'char')
        self.register_cython_type(TypeInfo.get('Int'), 'int')
        self.register_cython_type(TypeInfo.get('Short'), 'short')
        self.register_cython_type(TypeInfo.get('IntPlace'), from_neco_lib('TGenericPlaceType[int]*'))
        self.register_cython_type(TypeInfo.get('MultiSet'), 'ctypes_ext.MultiSet')
        self.register_cython_type(TypeInfo.get('UnsignedChar'), 'unsigned char')
        self.register_cython_type(TypeInfo.get('UnsignedInt'), 'unsigned int')
        if marking_type.config.normalize_pids:
            self.register_cython_type(TypeInfo.get('Pid'), from_neco_lib('Pid'))
        else:
            self.register_cython_type(TypeInfo.get('Pid'), 'object')
        self.register_cython_type(TypeInfo.get('PidPlace'), from_neco_lib('TGenericPlaceType[' + from_neco_lib('Pid') + ']*'))
        self.register_cython_type(TypeInfo.get('GeneratorPlace'), from_neco_lib('TGeneratorPlaceType[' + from_neco_lib('Pid') + ', int]*'))

    @property
    def cvars(self):
        return self._cvar_decl[-1]

    def push_cvar_env(self):
        self._cvar_decl.append(CVars(self))

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

    def add_pxd_declaration(self, decl, unique=False):
        if unique and decl in self._pxd_declarations:
            return
        self._pxd_declarations.append(to_ast(decl))


    @property
    def pxd_declarations(self):
        return _str_list_to_endlstr(self._pxd_declarations)

    ################################################################################

    def add_successor_function(self, function_name, process):
        self._successor_functions.append((function_name, process))

    def try_declare_cvar(self, variable_name, new_type):
        """

        @param variable_name:
        @type variable_name: C{}
        @param new_type:
        @type new_type: C{}
        """
        cvars = self.cvars
        try:
            old_type = cvars.type(variable_name)
            if old_type < new_type:
                cvars.update_type(variable_name, new_type)
        except IndexError:
            self.cvars.declare(variable_name, new_type)

    def register_cython_type(self, typeinfo, identifier):
        """ Register a type as a cython type.
    
        The provided value provided to C{id} argument will be used as type name
        in produced code.
    
        @param typeinfo: type to be registered.
        @type typeinfo: C{neco.core.TypeInfo}
        @param id: name used as type name.
        @type id: C{str}
        """
        self._registered_cython_types[str(typeinfo)] = identifier
    
    def is_cython_type(self, typeinfo):
        """ Check if a type is registered.
    
        @param typeinfo: type to be checked.
        @type typeinfo: C{neco.core.TypeInfo}
        @return: C{True} if registered, C{False} otherwise.
        @rtype bool
        """
        return self._registered_cython_types.has_key(str(typeinfo))
            
    ################################################################################
    
    def type2str(self, typ):
        """ translates a type info to a string
    
        @param type: type info to translate
        @type type: C{TypeInfo}
        """
        if typ.is_UserType:
            if self.is_cython_type(typ):
                return self._registered_cython_types[str(typ)]
            else:
                return 'object'
        elif typ.is_TupleType:
            return 'tuple'
        else:
            return 'object'

################################################################################

class CVarSet(object):

    def __init__(self, iterable=[]):
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

    def extend(self, iterable):
        for elt in iterable:
            self.add(elt)

    def __iter__(self):
        return self._set.__iter__()

    def __contains__(self, elt):
        return not (elt.name in self._names)

    def __str__(self):
        return str(self._set)



class CythonPyxFile(object):

    def __init__(self, name):
        self.name = name
        self.declarations = []
        self.body = []

    def write(self, env, base_dir = './'):
        module_ast = flatten_ast(cyast.Module(body=self.body))

        f = open(base_dir + self.name, "w")
        f.write("\n".join(self.declarations))
        cyast.Unparser(module_ast, f)
        f.close()

class CythonPxdFile(object):

    def __init__(self, name):
        self.name = name
        self.declarations = []
        self.body = []

    def write(self, env, base_dir = './'):
        module_ast = flatten_ast(cyast.Module(body=self.body))

        f = open(base_dir + self.name, "w")
        f.write("\n".join(self.declarations))
        cyast.Unparser(module_ast, f)
        f.close()
        

class IsCythonPyxFile(OutputProviderPredicate):

    def __call__(self, output):
        return isinstance(output, CythonPyxFile)

class IsCythonPxdFile(OutputProviderPredicate):

    def __call__(self, output):
        return isinstance(output, CythonPxdFile)

