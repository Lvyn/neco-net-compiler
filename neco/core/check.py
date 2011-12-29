import pickle, ast, sys
from StringIO import StringIO
from abc import abstractmethod, ABCMeta
from snakes.utils.ctlstar.build import build, parse
import snakes.lang.ctlstar.asdl as asdl
from neco.utils import Matcher
import netir
from netir import Builder
from info import VariableProvider

class FormulaDecomposer(object):
    """ Class responsible of formula decomposition.

    It handles two maps:
    - id_prop_map that associates an unique integer identifier with an unique atomic proposition;
    - prop_id_map that associates an unique atomic proposition identifier with an unique integer.

    Each time a formula is decomposed and an atomic proposition is found the maps are updated.

    """

    def __init__(self):
        """ initialize the decomposer.
        """
        self.last_id = -1
        self.id_prop_map = {}
        self.prop_id_map = {}

    def get_formula_id(self, formula):
        """ Returns an unique identifier for a formula.

        @param formula: formula to identify.
        @return: Unique integer identifier.
        """
        if formula in self.prop_id_map:
            return self.prop_id_map[formula]
        else:
            self.last_id += 1
            self.id_prop_map[self.last_id] = formula
            self.prop_id_map[formula] = self.last_id
            return self.last_id

    def __call__(self, formula):
        """ Function style operator for calling decompose. """
        return self.decompose(formula)

    def decompose(self, formula):
        """ Decompose a formula.

        @param formula: formula to decompose
        @return: updated formula where atomic propositions were replaced with NAME instances.
        """
        for field_name in formula._fields:
            field = getattr(formula, field_name)
            if isinstance(field, asdl._AST):
                if isinstance(field, asdl.atom):
                    identifier = "p " + str(self.get_formula_id(field))
                    setattr(formula, field_name, asdl.Instance(name=str(identifier), args=[]))
                else:
                    # recursive call on sub-formula
                    formula.field = self.decompose(field)
        return formula

    def get_id_prop_map(self):
        """ Get the id-prop map.
        @return: id-prop map.
        """
        return self.id_prop_map

    def get_prop_id_map(self):
        """ Get the prop-id map.
        @return: prop-id map.
        """
        return self.id_prop_map


class CheckerCompiler(object):
    """ Class responsible of compiling atomic propositions and provide id-prop maps.
    """

    __metaclass__ = ABCMeta

    def __init__(self, compilation_trace_name, formula, backend):
        trace_file = open(compilation_trace_name, 'rb')

        trace = pickle.load(trace_file)
        self.marking_type = trace #trace.get_marking_type()

        # decompose formula
        fd = FormulaDecomposer()
        self.formula = fd.decompose(formula)
        self.id_prop_map = fd.get_id_prop_map()
        self.prop_id_map = fd.get_prop_id_map()

        # write formula to buf, replace all ' by "
        buf = StringIO()
        FormulaPrinter(buf).dispatch(self.formula)
        neco_formula = buf.getvalue().replace("'", '"')

        # write formula to file
        formula_file = open('neco_formula', 'w')
        formula_file.write(neco_formula)
        formula_file.close()

        self.backend = backend
        self.checker_env = backend.CheckerEnv(set(), self.marking_type)

    def compile(self):
        """ Produce compiled checker.
        """

        self.backend.produce_and_compile_pyx(self.checker_env, self.id_prop_map)


################################################################################
# tiny formula printer
################################################################################

class FormulaPrinter(object):

    def __init__(self, output = sys.stdout):
        self.output = output

    def separator(self):
        self.output.write(' ')

    def _Spec(self, tree):
        self.dispatch(tree.main)
        self.output.write('\n')

    def _CtlUnary(self, tree):
        self.dispatch(tree.op)
        self.separator()
        self.dispatch(tree.child)

    def _CtlBinary(self, tree):
        self.dispatch(tree.left)
        self.separator()
        self.dispatch(tree.op)
        self.separator()
        self.dispatch(tree.right)

    def _Not(self, tree):
        self.output.write("!")

    def _And(self, tree):
        self.output.write('/\\')

    def _Or(self, tree):
        self.output.write('\\/')

    def _Imply(self, tree):
        self.output.wrtie("=>")


    def _Iff(self, tree):
        self.output.wrtie("<=>")

    def _Until(self, tree):
        self.output.wrtie("U")

    def _All(self, tree):
        self.output.write("A")

    def _Globally(self, tree):
        self.output.write("G")

    def _Future(self, tree):
        self.output.write("F")

    def _Next(self, tree):
        self.output.write("X")

    def _Instance(self, tree):
        self.output.write(repr(tree.name))

    def dispatch(self, tree):

        attr_name = '_' + tree.__class__.__name__
        method = getattr(self, attr_name)
        method(tree)
