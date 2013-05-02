import pickle, sys
from neco import config
import properties
from neco.utils import IDProvider, reverse_map
import neco.core.info as info
# from neco.utils import Matcher
# import netir
# from netir import Builder
# from info import VariableProvider

def has_deadlocks(formula):
    if formula.isDeadlock():
        return True
    return properties.reduce_ast(lambda acc, node: acc or has_deadlocks(node),
                                  formula,
                                  False)

def spot_formula(formula):
    
    # Neco-Spot prints True if there is no counter example, so it assumes that
    # all formulas are prefixed by "A" operator.

    if formula.isAtomicProposition():
        return '(p' + str(formula.identifier) + ')'
    elif formula.isDeadlock():
        return 'DEAD'
    elif formula.isConjunction():
        return '(' + ' /\\ '.join(map(spot_formula, formula.operands)) + ')'
    elif formula.isDisjunction():
        return '(' + ' \\/ '.join(map(spot_formula, formula.operands)) + ')'
    elif formula.isExclusiveDisjunction():
        return '(' + ' ^ '.join(map(spot_formula, formula.operands)) + ')'
    elif formula.isImplication():
        return '(' + spot_formula(formula.left) + ' => ' + spot_formula(formula.right) + ')'
    elif formula.isEquivalence():
        return '(' + spot_formula(formula.left) + ' <=> ' + spot_formula(formula.right) + ')'
    elif formula.isNegation():
        return '(!' + spot_formula(formula.formula) + ')'
    elif formula.isNext():
        return "(X {})".format(spot_formula(formula.formula))
    elif formula.isGlobally():
        return '(G ' + spot_formula(formula.formula) + ')'
    elif formula.isFuture():
        return '(F ' + spot_formula(formula.formula) + ')'
    elif formula.isUntil():
        return '(' + spot_formula(formula.left) + ' U ' + spot_formula(formula.right) + ')'
    elif formula.isWeakUntil():
        return '(' + spot_formula(formula.left) + ' W ' + spot_formula(formula.right) + ')'
    elif formula.isBool():
        return 'true' if formula.value else 'false'
    elif formula.isAllPaths():
        return spot_formula(formula.formula)
    elif formula.isExistsPath():
        return '(!' + spot_formula(formula.formula) + ')'
    else:
        raise NotImplementedError

class CheckerCompiler(object):
    """ Class responsible of compiling atomic propositions and provide id-prop maps.
    """

    def __init__(self, formula, net, config, backend):
        trace = config.trace
        self.marking_type = trace['marking_type']
        self.config = config

        config.set_options(optimize = trace['optimize'],
                           model = trace['model'])

        self.net_info = info.NetInfo(net)    # trace.get_marking_type()

        # normalize and decompose formula
        formula = properties.normalize_formula(formula)
        try:
            properties.check_locations(formula, self.net_info)
        except (LookupError, TypeError) as e:
            print >> sys.stderr, e.message
            exit(1)

        formula = properties.transform_formula(formula)
        formula = properties.extract_atoms(formula)
        self.formula = formula
        self.id_prop_map = properties.build_atom_map(formula, IDProvider(), {})
        self.expected = not formula.isExistsPath()

        print "compiled formula: {!s}".format(self.formula)
        spot_str = spot_formula(self.formula)
        print "spot formula:     {!s}".format(spot_str)
        print "atomic propositions:"
        for i, (key, value) in enumerate(self.id_prop_map.iteritems(), start = 1):
            print "{!s:>3}. p{!s:<3} = {!s}".format(i, key, value)
        print "end atomic propositions"
        print

        # write formula to file
        formula_file = open('neco_formula', 'w')
        args = []
        if has_deadlocks(formula):
            args.append("-d DEAD")
            args.append("--expected {}".format("TRUE" if self.expected else "FALSE"))
        for arg in config.ns_args:
            args.append(arg)
        if args:
            for arg in args:            
                formula_file.write("# " + arg + "\n")

        formula_file.write(spot_str)
        formula_file.write("\n")
        formula_file.close()

        self.backend = backend
        self.checker_env = backend.check_impl.CheckerEnv(config, self.net_info, set(), self.marking_type)

    def compile(self):
        """ Produce compiled checker.
        """
        self.backend.check_impl.produce_and_compile_pyx(self.checker_env, self.id_prop_map)

