import sys
from neco.utils import Enum

class FormulaTrait(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def __call__(self, cls):
        def trait(obj):
            return self.value
        setattr(cls, "is" + self.name, trait)
        return cls
    
def FormulaTraits(*args, **kwargs):
    return lambda cls : _FormulaTraits(cls, *args, **kwargs)
    
def _FormulaTraits(cls, *args, **kwargs):
    def trait(obj):
        return True
    
    setattr(cls, "is" + cls.__name__, trait)
    
    for arg in args:
        trait = FormulaTrait(arg)
        cls = trait(cls)
        
    for arg, value in kwargs.iteritems():
        trait = FormulaTrait(arg, value)
        cls = trait(cls)
    
    return cls
    

@FormulaTraits(UnaryOperator=False,
               LogicUnaryOperator=False,
               Negation=False,
               
               NaryOperator=False,
               LogicNaryOperator=False,
               Conjunction=False,
               
               BinaryOperator=False,
               ArithmeticNaryOperator=False,
               IntegerComparison=False,
               ArithmeticExpression=False,
               IntegerConstant=False,
               PlaceBound=False,
               AtomicProposition=False,
               Sum=False,
               IsLive=False,
               IsFireable=False,
               Globally=False,
               Future=False,
               Card=False)
class Formula(object):
    __traits__ = {}

@FormulaTraits()
class NaryOperator(Formula):
    
    def __init__(self, operands):
        self._operands = operands
        
    @property
    def operands(self):
        return self._operands
    
    @operands.setter
    def operands(self, new_operands):
        self._operands = new_operands
        
    def __iter__(self):
        return self._operands.__iter__()

@FormulaTraits()
class UnaryOperator(Formula):

    def __init__(self, formula):
        self._formula = formula

    @property
    def formula(self):
        return self._formula
    
    @formula.setter
    def formula(self, new_formula):
        self._formula = new_formula

    def __iter__(self):
        yield self._formula

@FormulaTraits()
class BinaryOperator(Formula):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __iter__(self):
        yield self.left
        yield self.right
        
@FormulaTraits()
class LogicUnaryOperator(UnaryOperator):
    def __init__(self, formula):
        UnaryOperator.__init__(self, formula)
    
@FormulaTraits()
class LogicNaryOperator(NaryOperator):
    def __init__(self, operands):
        NaryOperator.__init__(self, operands = operands)

@FormulaTraits()
class ArithmeticBinaryOperator(BinaryOperator):
    def __init__(self, left, right):
        BinaryOperator.__init__(self, left, right)
        
@FormulaTraits()
class ArithmeticNaryOperator(NaryOperator):
    def __init__(self, operands):
        NaryOperator.__init__(self, operands = operands)
        
@FormulaTraits()
class ArithmeticExpression(Formula):
    pass
        
@FormulaTraits()
class Conjunction(LogicNaryOperator):
    
    def __init__(self, operands):
        LogicNaryOperator.__init__(self, operands)
        
    def __str__(self):
        return "(" + " /\\ ".join([ str(operand) for operand in self.operands ]) + ")"

@FormulaTraits()
class Sum(ArithmeticNaryOperator):
    
    def __init__(self, operands):
        ArithmeticNaryOperator.__init__(self, operands)

    def __str__(self):
        return "(" + " + ".join([ str(operand) for operand in self.operands ]) + ")"
    
@FormulaTraits()
class Negation(LogicUnaryOperator):

    def __str__(self):
        return "(not {!s})".format(self._formula)
    
    def __iter__(self):
        yield self._formula

@FormulaTraits()
class Globally(LogicUnaryOperator):
    def __init__(self, formula):
        LogicUnaryOperator.__init__(self, formula)

    def __str__(self):
        return "(G " + str(self.formula) + " )"


@FormulaTraits()
class Future(LogicUnaryOperator):
    def __init__(self, formula):
        LogicUnaryOperator.__init__(self, formula)

    def __str__(self):
        return "(F " + str(self.formula) + " )"

@FormulaTraits()
class PlaceBound(Formula):
    def __init__(self, name):
        self._place_name = name
        
    @property
    def place_name(self):
        return self._place_name
    
    def __str__(self):
        return "Bound({!s})".format(self._place_name)

@FormulaTraits()
class Card(ArithmeticExpression):
    def __init__(self, name):
        self._place_name = name
        
    @property
    def place_name(self):
        return self._place_name
    
    def __str__(self):
        return "Card({!s})".format(self._place_name)


@FormulaTraits()
class IntegerComparison(ArithmeticBinaryOperator):

    LT = 0x1
    LE = 0x2
    EQ = 0x3
    NE = 0x4
    GT = 0x5
    GE = 0x6
    
    def __init__(self, operator, left = None, right = None):
        self._operator = operator
        self._left = left
        self._right = right

    @property
    def left(self):
        return self._left
    
    @property
    def right(self):
        return self._right

    def __str__(self):
        return "({!s} {!s} {!s})".format(self._left,
                                         operator_to_string(self._operator),                   
                                         self._right)

    @property
    def operator(self):
        return self._operator
    
__operator_to_string_map = { IntegerComparison.LT : "<",
                             IntegerComparison.LE : "<=",
                             IntegerComparison.EQ : "=",
                             IntegerComparison.NE : "!=",
                             IntegerComparison.GT : ">",
                             IntegerComparison.GE : ">=" }
    
def operator_to_string(operator):
    return __operator_to_string_map[operator]

@FormulaTraits()
class IntegerConstant(ArithmeticExpression):
    
    def __init__(self, value):
        self._value = value
        
    @property
    def value(self):
        return self._value
        
    def __str__(self):
        return "(int {})".format(self._value)
    
    def __iter__(self):
        return iter([])

@FormulaTraits()
class IsLive(Formula):
    def __init__(self, level, transition_name):
        self.level = level
        self.transition_name = transition_name
    
    def __str__(self):
        return "IsLive({!s}, {!s})".format(self.level,
                                           self.transition_name)

@FormulaTraits()
class IsFireable(Formula):
    def __init__(self, transition_name):
        self.transition_name = transition_name
    
    def __str__(self):
        return "IsFireable({!s})".format(self.transition_name)

@FormulaTraits()
class AtomicProposition(Formula):
    
    __identifier__ = -1
    
    @classmethod
    def __new_identifier(cls):
        cls.__identifier__ += 1
        return cls.__identifier__
    
    
    def __init__(self, formula):
        self._identifier = AtomicProposition.__new_identifier()
        self._formula = formula
    
    @property
    def formula(self):
        return self._formula
    
    @property
    def identifier(self):
        return self._identifier
    
    def __str__(self):
        return "(Atomic<{!s}>)".format(self._formula)

def match_atom(formula):
    if ( formula.isIntegerComparison() or
         formula.isIsLive() or
         formula.isIsFireable()):
        return AtomicProposition(formula)
    
    raise NotImplementedError
    
def __new(obj, *args, **kwargs):
    return obj.__class__(*args, **kwargs)
    
def extract_atoms(formula):
    
    if formula.isLogicNaryOperator():
        new_operands = [ extract_atoms(operand) for operand in formula.operands ]
        return __new(formula, operands = new_operands)
    
    elif formula.isLogicUnaryOperator():
        return __new(formula, extract_atoms( formula.formula ))
    else:
        atom = match_atom(formula)
        if atom:
            formula = atom
        else:
            print >> sys.stderr, "cannot extract atoms from {!s}".format(formula)
            import pprint
            pprint.pprint(formula.__traits__)
            raise SyntaxError
    
    return formula

def normalize_formula(formula):
    
    if formula.isIsLive():
        return formula
    
    elif formula.isPlaceBound():
        return formula
    
    elif formula.isCard():
        return formula
    
    elif formula.isIntegerComparison():
        # reverse comparison order
        swap = False
        new_op = formula.operator
        if formula.operator == IntegerComparison.GT:
            swap = True
            new_op = IntegerComparison.LT            
        elif formula.operator == IntegerComparison.GE:
            swap = True
            new_op = IntegerComparison.LE
            
        if swap:
            new_left  = normalize_formula(formula.right)
            new_right = normalize_formula(formula.left)
        else:
            new_left  = normalize_formula(formula.left)
            new_right = normalize_formula(formula.right)
            
        return __new(formula, new_op, new_left, new_right)
    
    elif formula.isUnaryOperator():
        return __new(formula, normalize_formula(formula.formula))
    
    elif formula.isBinaryOperator():
        new_left  = normalize_formula(formula.left)
        new_right = normalize_formula(formula.right)
        return __new(formula, new_op, new_left, new_right)
    
    elif formula.isNaryOperator():
        operands = [ normalize_formula(operand) for operand in formula.operands ]
        return __new(formula, operands)
    
    elif formula.isArithmeticExpression():
        return formula
    
    else:
        print >> sys.stderr, str(formula)
        raise NotImplementedError

def has_bounds(formula):
    """
    >>> has_bounds(PlaceBound('s1'))
    True
    >>> has_bounds(IntegerConstant(42))
    False
    >>> has_bounds(IntegerComparison(IntegerComparison.LT, PlaceBound('s1'), 1))
    True
    
    """
    if formula.isPlaceBound():
        return True
    else:
        return reduce( lambda acc, f2 : acc or has_bounds(f2),
                       formula,
                       False )            

def transform_formula(formula):
    
    if formula.isIsLive():
        if formula.level != 0:
            raise NotImplementedError
        return Negation(Future(IsFireable( formula.transition_name )))
    
    elif formula.isIntegerComparison():
        left   = formula.left
        right  = formula.right
        new_op = formula.operator
        
        left_has_bounds = has_bounds(left)
        right_has_bounds = has_bounds(right)
        
        if  left_has_bounds and right_has_bounds:
            print >> sys.stderr, "cannot compare two expressions with bounds"
            raise NotImplementedError
        
        # transform "bound = k" into "card <= k"
        if left_has_bounds or right_has_bounds:    
            if formula.operator == IntegerComparison.EQ:
                new_op = IntegerComparison.LE
            
        left  = transform_formula(left)
        right = transform_formula(right)
        
        return __new(formula, new_op, left=left, right=right)
    
    elif formula.isSum():
        operands = formula.operands
        # clean up sums of length one
        if len(operands) == 1:
            return transform_formula(operands[0])
        else:
            new_operands = [ transform_formula(operand) for operand in operands ]
            return __new(formula, new_operands)
    
    elif formula.isPlaceBound():
        return Card(formula.place_name)
    
    elif formula.isUnaryOperator():
        return __new(formula, transform_formula(formula.formula))   
    
    elif formula.isBinaryOperator():
        left  = transform_formula(formula.left)
        right = transform_formula(formula.right)
        return __new(formula, left=left, right=right)
    
    elif formula.isNaryOperator():
        operands = [ transform_formula(sub) for sub in formula ]
        return __new(formula, operands)
    
    elif formula.isArithmeticExpression():
        return formula
    
    else:
        print str(formula)
        raise NotImplementedError
       
def build_atom_map(formula, name_provider, name_atom_map):
    if isinstance(formula, AtomicProposition):
        name_atom_map[ name_provider.get(formula) ] = formula
    else:
        for subformula in formula:
            build_atom_map(subformula, name_provider, name_atom_map)
    return name_atom_map

if __name__ == "__main__":
    import doctest
    doctest.testmod()
#    class NameProvider(object):
#        
#        def __init__(self, prefix = ""):
#            self._prefix = prefix
#            self._begin = 0
#            
#        def get(self, obj):
#            self._begin += 1
#            return self._prefix + "_" + str(self._begin)
#
#    from xmlproperties import parse
#    props = parse('../../tests/check/lamport_fmea-2.23.xml')
#    for prop in props:
#        print prop.formula
#        new_formula = extract_atoms(prop.formula)
#        map = build_atom_map(new_formula, NameProvider(), {})
#        for key, value in map.iteritems():
#            print "{!s} : {!s}".format(key, value)
