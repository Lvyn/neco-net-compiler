import properties_gen
from properties_gen import *
import inspect, sys, copy

def __new(obj, *args, **kwargs):
    return obj.__class__(*args, **kwargs)
    
def is_AST(formula):
    return isinstance(formula, properties_gen._AST)

def dispatch_ast(function, formula):
    for field_name in formula._fields:
        field = getattr(formula, field_name)
        if isinstance(field, list):
            for f in field:
                if is_AST(f):
                    function(f)
        elif is_AST(field):
            function(field)        

def map_ast(function, formula):
    if not is_AST(formula):
        return copy.deepcopy(formula)
    
    new_fields = {}
    for field_name in formula._fields:
        field = getattr(formula, field_name)
        if isinstance(field, list):
            new_field = []
            for elt in field:
                if not is_AST(elt):
                    new_field.append(copy.deepcopy(elt))
                else:
                    new_field.append(function(elt))
            new_fields[field_name] = new_field
        elif is_AST(field):
            new_fields[field_name] = function(field)
        else:
            new_fields[field_name] = copy.deepcopy(field)
    return __new(formula, **new_fields)

def iter_fields(formula):
    for field in formula._fields:
        yield getattr(formula, field)
    
def reduce_ast(function, formula, initial=None):
    value = initial
    for field in iter_fields(formula):
        if is_AST(field):
            value = function(value, field)
        elif isinstance(field, list):
            # " value = reduce(function, field, value) " would be incorrect because of non-AST fields
            for f in field:
                if is_AST(f):
                    value = function(value, f)
                else:
                    # nothing to do for non-AST fields
                    pass
            
    return value

def formula_to_str(formula):
    # UnaryTemporalLogicOperator
    if formula.isGlobally():
        return '(G {})'.format(formula_to_str(formula.formula))
    elif formula.isFuture():
        return '(F {})'.format(formula_to_str(formula.formula))
    elif formula.isNext():
        return '(X {})'.format(formula_to_str(formula.formula))
    # BinaryTemporalLogicOperator
    elif formula.isUntil():
        return "({} U {})".format(formula_to_str(formula.left),
                                  formula_to_str(formula.right))
    # UnaryLogicOperator
    elif formula.isNegation():
        return '(!{})'.format(formula_to_str(formula.formula))
    # BinaryLogicOperator
    elif formula.isImplication():
        return "({} => {})".format(formula_to_str(formula.left),
                                   formula_to_str(formula.right))
    elif formula.isEquivalence():
        return "({} <=> {})".format(formula_to_str(formula.left),
                                    formula_to_str(formula.right))
    # NaryLogicOperator
    elif formula.isConjunction():
        return "(" + " /\\ ".join( map(formula_to_str, formula.operands) ) + ")" 
    elif formula.isDisjunction():
        return "(" + " \\/ ".join( map(formula_to_str, formula.operands) ) + ")"
    elif formula.isExclusiveDisjunction():
        return "(" + " ^ ".join( map(formula_to_str, formula.operands) ) + ")"
    # BooleanExpression 
    elif (formula.isIntegerComparison() or
          formula.isMultisetComparison()):
        return "({} {} {})".format(formula_to_str(formula.left),
                                   formula_to_str(formula.operator),
                                   formula_to_str(formula.right))
    elif formula.isIsLive():
        return "Islive{!s}({!s})".format(formula.level, formula.transition_name)
    elif formula.isIsFireable():
        return "IsFireable({!s})".format(formula.transition_name)
    elif formula.isIsDeadlock():
        return "Deadlock"
    elif formula.isAtomicProposition():
        return "AtomicProposition<{}>".format(formula_to_str(formula.formula))
    # ComparisonOperator
    elif formula.isLT():
        return "<"
    elif formula.isLE():
        return "<="
    elif formula.isEQ():
        return "="
    elif formula.isNE():
        return "!="
    elif formula.isGE():
        return ">="
    elif formula.isGT():
        return ">"
    # IntegerExpression
    elif formula.isPlaceBound():
        return "PlaceBound({!s})".format(formula.place_name)
    elif formula.isIntegerConstant():
        return "Int({!s})".format(formula.value)
    elif formula.isPlaceBound():
        return "PlaceBound({!s})".format(formula_to_str(formula.place_name))
    elif formula.isSum():
        return "(" + " + ".join(map(formula_to_str, formula.operands)) + ")"
    elif formula.isMultisetCardinality():
        return "MultisetCardinality({!s})".format(formula_to_str(formula.multiset))
    # MultisetExpression
    elif formula.isPlaceMarking():
        return "PlaceMarking({!s})".format(formula.place_name)
    elif formula.isMultisetConstant():
        ms_str = '[' + ', '.join(map(str, formula.elements)) + ']'
        return "MultisetConstant({})".format(ms_str)
    else:
        raise NotImplementedError('cannot handle {}'.format(formula.__class__))

def __update_LTLFormula_class_str():
    
    predicate = lambda obj : inspect.isclass(obj) and issubclass(obj, properties_gen._AST)    
    for _, cls in inspect.getmembers(properties_gen, predicate):
        setattr(cls, "__str__", formula_to_str)
        
__update_LTLFormula_class_str()


def __match_atom(formula):
    return ( formula.isIntegerComparison() or
             formula.isMultisetComparison() or
             formula.isIsLive() or
             formula.isIsFireable() or 
             formula.isPlaceMarking() or
             formula.isMultisetCardinality() )


def __update_atomic_proposition_identifiers(next_identifier, formula):
    if not is_AST(formula):
        return next_identifier
        
    if formula.isAtomicProposition():
        formula.identifier = next_identifier
        return next_identifier + 1
        
    else:
        next_identifier = reduce_ast( __update_atomic_proposition_identifiers, formula, next_identifier )
        return next_identifier

def __extract_atoms(formula):
    if not is_AST(formula):
        return formula
    
    elif __match_atom(formula):
        return AtomicProposition(formula) 
    
    else:
        return map_ast(__extract_atoms, formula)

def extract_atoms(formula):
    new_formula = __extract_atoms(formula)
    __update_atomic_proposition_identifiers(0, new_formula)
    return new_formula

def normalize_formula(formula):
    
    if (formula.isIntegerComparison() or
        formula.isMultisetComparison()):
        
        # reverse comparison order
        swap = False
        new_op = formula.operator
        if formula.operator.isGT():
            swap = True
            new_op = properties_gen.LT()            
        elif formula.operator.isGE():
            swap = True
            new_op = properties_gen.LE()
            
        if swap:
            new_left  = normalize_formula(formula.right)
            new_right = normalize_formula(formula.left)
        else:
            new_left  = normalize_formula(formula.left)
            new_right = normalize_formula(formula.right)
            
        return __new(formula, operator=new_op, left=new_left, right=new_right)
    
    elif (formula.isConjunction() or
          formula.isDisjunction() or
          formula.isExclusiveDisjunction()):
        new_operands = map(normalize_formula, formula.operands)
        formula.operands = new_operands
        return formula
    
    else:
        return map_ast(normalize_formula, formula)
            
def has_bounds(formula):
    """
    >>> has_bounds(PlaceBound('s1'))
    True
    >>> has_bounds(IntegerConstant(42))
    False
    >>> has_bounds(IntegerComparison(LT(), PlaceBound('s1'), 1))
    True
    
    """
    if not is_AST(formula):
        return False
    elif formula.isPlaceBound():
        return True
    else:
        return reduce( lambda acc, f2 : acc or has_bounds(f2),
                       iter_fields(formula),
                       False )

def transform_formula(formula):
    if not is_AST(formula):
        return copy.deepcopy(formula)
    
    if formula.isIsLive():
        if formula.level != 0:
            raise NotImplementedError
        return Negation(Future(IsFireable( formula.transition_name )))
    
    elif formula.isPlaceBound():
        return properties_gen.MultisetCardinality(PlaceMarking(formula.place_name))
    
    elif (formula.isIntegerComparison() or
          formula.isMultisetComparison()):
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
            if formula.operator.isEQ():
                new_op = properties_gen.LE()
            
        left  = transform_formula(left)
        right = transform_formula(right)

        return __new(formula, operator = new_op, left=left, right=right)
    
    elif (formula.isSum() or
          formula.isConjunction() or
          formula.isDisjunction() or
          formula.isExclusiveDisjunction()):
        
        operands = formula.operands
        if len(operands) == 1:
            return transform_formula(operands[0])
        else:
            return map_ast(transform_formula, formula)

    elif (formula.isIsDeadlock() or 
          formula.isIsFireable() or
          formula.isPlaceMarking() or
          formula.isMultisetConstant() or
          formula.isNext() or
          formula.isGlobally() or
          formula.isFuture() or
          formula.isNegation() or
          formula.isUntil() or 
          formula.isMultisetCardinality() or
          formula.isIntegerConstant() or
          formula.isImplication() or
          formula.isEquivalence()):
        return map_ast(transform_formula, formula)
        
    else:
        raise NotImplementedError(formula.__class__)

def check_locations(formula, net_info):
    if formula.isPlaceBound() or formula.isPlaceMarking(): 
        net_info.place_by_name(formula.place_name)
    
    elif formula.isIsLive() or formula.isIsFireable():
        net_info.transition_by_name(formula.transition_name)
    
    elif formula.isMultisetComparison():
        if   (not formula.left.isMultisetExpression()):
            raise TypeError("marking comparison left operand should be a marking")
        elif (not formula.right.isMultisetExpression()):
            raise TypeError("marking comparison right operand should be a marking")
            
        dispatch_ast(lambda subformula : check_locations(subformula, net_info),
                     formula)
    else:
        dispatch_ast(lambda subformula : check_locations(subformula, net_info),
                     formula)
       
def build_atom_map(formula, name_provider, name_atom_map):
    if formula.isAtomicProposition():
        name_atom_map[ name_provider.get(formula) ] = formula
        
    else:
        dispatch_ast(lambda f : build_atom_map(f, name_provider, name_atom_map),
                     formula)

    return name_atom_map

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
    class NameProvider(object):
        
        def __init__(self, prefix = ""):
            self._prefix = prefix
            self._begin = 0
            
        def get(self, obj):
            self._begin += 1
            return self._prefix + "_" + str(self._begin)

    from xmlproperties import parse
    props = parse('../../tests/check/lamport_fmea-2.23.xml')
    for prop in props:
        print formula_to_str(prop.formula)
        
        formula = transform_formula(prop.formula)
        print formula_to_str(formula)
        
        formula = extract_atoms(formula)
        print formula_to_str(formula)
        
        map = build_atom_map(formula, NameProvider(), {})
        for key, value in map.iteritems():
            print "{!s} : {!s}".format(key, value)
