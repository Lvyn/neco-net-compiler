import pickle
from neco import config
import properties
from neco.utils import IDProvider, reverse_map
from neco.core.properties import operator_to_string
import neco.core.info as info
# from neco.utils import Matcher
# import netir
# from netir import Builder
# from info import VariableProvider

def spot_formula(formula):
    
    if formula.isAtomicProposition():
        return '(p' + str(formula.identifier) + ')'
    elif formula.isConjunction():
        subformulas = [ spot_formula(subformula) for subformula in formula ]
        return '(' + ' /\\ '.join( subformulas ) + ')'
    elif formula.isNegation():
        return '(!' + spot_formula(formula.formula) + ')'
    elif formula.isGlobally():
        return '(G ' + spot_formula(formula.formula) + ')'
    elif formula.isFuture():
        return '(F ' + spot_formula(formula.formula) + ')' 
    else:
        raise NotImplementedError

class CheckerCompiler(object):
    """ Class responsible of compiling atomic propositions and provide id-prop maps.
    """

    def __init__(self, formula, net, backend):
        trace_file = open(config.get('trace_file'), 'rb')

        trace = pickle.load(trace_file)
        self.marking_type = trace['marking_type']
        config.set(optimise=trace['optimise'])
        
        self.net_info = info.NetInfo(net) #trace.get_marking_type()

        # normalize and decompose formula
        formula = properties.normalize_formula(formula)
        formula = properties.transform_formula(formula)
        formula = properties.extract_atoms(formula)
        self.formula = formula
        self.id_prop_map = properties.build_atom_map(formula, IDProvider(), {})
        # self.prop_id_map = reverse_map(self.id_prop_map)
        # fd = FormulaDecomposer()
        # self.formula = fd.decompose(formula)
        # self.id_prop_map = fd.get_id_prop_map()
        # self.prop_id_map = fd.get_prop_id_map()

        print "compiled formula: {!s}".format(self.formula)
        spot_str = spot_formula(self.formula)
        print "spot formula:     {!s}".format(spot_str)
        print "atomic propositions:"
        for i, (key, value) in enumerate(self.id_prop_map.iteritems(), start=1):
            print "{!s:>3}. p{!s:<3} = {!s}".format(i, key, value)
        print "end atomic propositions"
        print
        
        # write formula to file
        formula_file = open('neco_formula', 'w')
        formula_file.write(spot_str)
        formula_file.close()

        self.backend = backend
        self.checker_env = backend.CheckerEnv(set(), self.net_info, self.marking_type)

    def compile(self):
        """ Produce compiled checker.
        """
        self.backend.produce_and_compile_pyx(self.checker_env, self.id_prop_map)

