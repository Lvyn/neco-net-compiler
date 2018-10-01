import neco.asdl.properties as properties_gen
from neco.asdl.properties import *
import FAdo.yappy_parser
from FAdo.yappy_parser import Yappy, grules
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

def reduce_ast(function, formula, initial = None):
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
        return "(" + " /\\ ".join(map(formula_to_str, formula.operands)) + ")"
    elif formula.isDisjunction():
        return "(" + " \\/ ".join(map(formula_to_str, formula.operands)) + ")"
    elif formula.isExclusiveDisjunction():
        return "(" + " ^ ".join(map(formula_to_str, formula.operands)) + ")"
    # BooleanExpression
    elif (formula.isIntegerComparison() or
          formula.isMultisetComparison()):
        return "({} {} {})".format(formula_to_str(formula.left),
                                   formula_to_str(formula.operator),
                                   formula_to_str(formula.right))
    elif formula.isBool():
        return "{!s}".format(formula.value)
    elif formula.isLive():
        return "Live{!s}({!r})".format(formula.level, formula.transition_name)
    elif formula.isFireable():
        return "Fireable({!r})".format(formula.transition_name)
    elif formula.isAll():
        return "All({!r}, {!r})".format(formula.place_name, formula.function_name)
    elif formula.isAny():
        return "Any({!r}, {!r})".format(formula.place_name, formula.function_name)
    elif formula.isDeadlock():
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
        return "PlaceBound({!r})".format(formula.place_name)
    elif formula.isIntegerConstant():
        return "Int({!s})".format(formula.value)
    elif formula.isSum():
        return "(" + " + ".join(map(formula_to_str, formula.operands)) + ")"
    elif formula.isMultisetCardinality():
        return "MultisetCardinality({!s})".format(formula_to_str(formula.multiset))
    # MultisetExpression
    elif formula.isPlaceMarking():
        return "PlaceMarking({!r})".format(formula.place_name)
    elif formula.isMultisetConstant():
        ms_str = '[' + ', '.join(map(str, formula.elements)) + ']'
        return "MultisetConstant({})".format(ms_str)
    elif formula.isMultisetPythonExpression():
        return "MultisetPythonExpression({})".format(formula.expr)
    else:
        raise NotImplementedError('cannot handle {}'.format(formula.__class__))

def __update_LTLFormula_class_str():

    predicate = lambda obj : inspect.isclass(obj) and issubclass(obj, properties_gen._AST)
    for _, cls in inspect.getmembers(properties_gen, predicate):
        setattr(cls, "__str__", formula_to_str)

__update_LTLFormula_class_str()


def __match_atom(formula):
    return (formula.isIntegerComparison() or
             formula.isMultisetComparison() or
             formula.isLive() or
             formula.isFireable() or
             formula.isAll() or
             formula.isAny() or
             formula.isPlaceMarking() or
             formula.isMultisetCardinality())


def __update_atomic_proposition_identifiers(next_identifier, formula):
    if not is_AST(formula):
        return next_identifier

    if formula.isAtomicProposition():
        formula.identifier = next_identifier
        return next_identifier + 1

    else:
        next_identifier = reduce_ast(__update_atomic_proposition_identifiers, formula, next_identifier)
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
            new_left = normalize_formula(formula.right)
            new_right = normalize_formula(formula.left)
        else:
            new_left = normalize_formula(formula.left)
            new_right = normalize_formula(formula.right)

        return __new(formula, operator = new_op, left = new_left, right = new_right)

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
        return reduce(lambda acc, f2 : acc or has_bounds(f2),
                       iter_fields(formula),
                       False)

def transform_formula(formula):
    if not is_AST(formula):
        return copy.deepcopy(formula)

    if formula.isLive():
        if formula.level != 0:
            raise NotImplementedError
        return Negation(Future(Fireable(formula.transition_name)))

    elif formula.isPlaceBound():
        return properties_gen.MultisetCardinality(PlaceMarking(formula.place_name))

    elif formula.isMultisetPythonExpression():
        return formula

    elif (formula.isIntegerComparison() or
          formula.isMultisetComparison()):
        left = formula.left
        right = formula.right
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

        left = transform_formula(left)
        right = transform_formula(right)

        return __new(formula, operator = new_op, left = left, right = right)

    elif (formula.isSum() or
          formula.isConjunction() or
          formula.isDisjunction() or
          formula.isExclusiveDisjunction()):

        operands = formula.operands
        if len(operands) == 1:
            return transform_formula(operands[0])
        else:
            return map_ast(transform_formula, formula)

    elif (formula.isDeadlock() or
          formula.isFireable() or
          formula.isAll() or
          formula.isAny() or
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
          formula.isEquivalence() or
          formula.isBool()):
        return map_ast(transform_formula, formula)

    else:
        raise NotImplementedError(formula.__class__)

def check_locations(formula, net_info):
    if formula.isPlaceBound() or formula.isPlaceMarking():
        net_info.place_by_name(formula.place_name)

    elif formula.isLive() or formula.isFireable():
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

# ## PARSER

def merge_spaces(s):
    """
    >>> merge_spaces('toto')
    'toto'
    >>> merge_spaces('  toto    ')
    'toto'
    >>> merge_spaces('   t o t o    ')
    't o t o'
    >>> merge_spaces('   t     o     t     o    ')
    't o t o'

    """
    i = 0
    new_str = ''
    p_space = True
    for i in range(0, len(s)):
        if s[i] == ' ':
            if p_space:
                continue
            else:
                new_str += s[i]
                p_space = True
        else:
            new_str += s[i]
            p_space = False
    if p_space:
        return new_str[0:-1]
    else:
        return new_str




# yappy.parser._DEBUG = 1
class PropertyParser(Yappy):

    def __init__(self):

        grammar = grules([(" formula -> G formula", self.globally_rule),
                          (" formula -> F formula", self.future_rule),
                          (" formula -> X formula", self.next_rule),
                          (" formula -> formula UNTIL formula", self.until_rule),
                          (" formula -> formula RELEASE formula", self.release_rule),
                          (" formula -> formula AND formula", self.and_rule),
                          (" formula -> formula OR formula", self.or_rule),
                          (" formula -> formula XOR formula", self.xor_rule),
                          (" formula -> formula EQUIV formula", self.equiv_rule),
                          (" formula -> formula IMPL formula", self.impl_rule),
                          (" formula -> NOT formula", self.not_rule),
                          (" formula -> ( formula )", self.scope_rule),
                          (" formula -> bool_expr", self.default_rule),
                          (" bool_expr -> int_expr CMP int_expr", self.integer_cmp_rule),
                          (" bool_expr -> ms_expr CMP ms_expr", self.multiset_cmp_rule),
                          (" bool_expr -> ms_py_expr CMP ms_expr", self.multiset_cmp_rule),
                          (" bool_expr -> ms_expr CMP ms_py_expr", self.multiset_cmp_rule),
                          (" bool_expr -> LIVE ( INTEGER , ID )", self.live_rule),
                          (" bool_expr -> FIREABLE ( ID )", self.fireable_rule),
                          (" bool_expr -> ALL ( ID , ID )", self.all_rule),
                          (" bool_expr -> ANY ( ID , ID )", self.any_rule),
                          (" bool_expr -> DEADLOCK", self.deadlock_rule),
                          (" bool_expr -> BOOL", self.bool_rule),
                          (" int_expr -> int_expr + int_expr", self.plus_rule),
                          (" int_expr -> BOUND ( ID )", self.bound_rule),
                          (" int_expr -> CARD ( ms_expr )", self.card_rule),
                          (" int_expr -> INTEGER", self.integer_rule),
                          (" int_expr -> ( int_expr )", self.scope_rule),
                          (" ms_expr  -> MARKING ( ID )", self.marking_rule),
                          (" ms_expr  -> [ ]", self.empty_multiset_rule),
                          (" ms_expr  -> [ ms_elts ]", self.multiset_rule),
                          (" ms_elts -> ms_elts , ms_elts", self.multiset_elts_seq_rule),
                          (" ms_elts -> INTEGER", lambda l, c : [ l[0] ]),
                          (" ms_elts -> DOT", lambda l, c : [ 'dot' ]),
                          (" ms_elts -> ID", lambda l, c : [ '"' + l[0] + '"' ]),
                          (" ms_py_expr -> PY_EXPR ", self.multiset_python_expression_rule)
                          ])

        tokenize = [(r'\$[^$]*\$', lambda x : ('PY_EXPR', x)),
                    (r'"[a-zA-Z]+([.a-zA-Z_0-9]+)*"|\'[a-zA-Z]+([()#.a-zA-Z_0-9]+)*\'', lambda x : ('ID', x[1:-1])),    # protected ids
                    (r'\s', ""),    # skip white spaces
                    (r'<=>|<->', lambda x : ('EQUIV', x), ('EQUIV', 50, 'left')),
                    (r'=>|->', lambda x : ('IMPL', x), ('IMPL', 40, 'left')),
                    (r'<=|<|=|!=|>=|>', lambda x : ('CMP', x), ('CMP', 800, 'left')),
                    (r'\+', lambda x : (x, x), ('+', 750, 'left')),
                    (r'true|false', lambda x : ('BOOL', x), ('BOOL', 700, 'noassoc')),
                    (r'live', lambda x : ('LIVE', x), ('LIVE', 700, 'noassoc')),
                    (r'fireable', lambda x : ('FIREABLE', x), ('FIREABLE', 700, 'noassoc')),
                    (r'deadlock', lambda x : ('DEADLOCK', x), ('DEADLOCK', 700, 'noassoc')),
                    (r'all', lambda x : ('ALL', x), ('ALL', 700, 'noassoc')),
                    (r'any', lambda x : ('ANY', x), ('ANY', 700, 'noassoc')),
                    (r'bound', lambda x : ('BOUND', x), ('BOUND', 700, 'noassoc')),
                    (r'card', lambda x : ('CARD', x), ('CARD', 700, 'noassoc')),
                    (r'marking', lambda x : ('MARKING', x), ('MARKING', 700, 'noassoc')),
                    (r'dot|@', lambda x : ('DOT', x), ('DOT', 700, 'noassoc')),
                    (r'not', lambda x : ('NOT', x), ('NOT', 600, 'noassoc')),
                    (r'G', lambda x : ('G', x), ('G', 500, 'noassoc')),
                    (r'F', lambda x : ('F', x), ('F', 500, 'noassoc')),
                    (r'X', lambda x : ('X', x), ('X', 500, 'noassoc')),
                    (r'R', lambda x : ('RELEASE', x), ('RELEASE', 440, 'left')),
                    (r'U', lambda x : ('UNTIL', x), ('UNTIL', 400, 'left')),
                    (r'and', lambda x : ('AND', x), ('AND', 300, 'left')),
                    (r'or', lambda x : ('OR', x), ('OR', 200, 'left')),
                    (r'xor', lambda x : ('XOR', x), ('XOR', 200, 'left')),
                    (r';', lambda x : (x, x), (';', 10, 'left')),
                    (r',', lambda x : (x, x), (',', 10, 'left')),
                    (r'\(|\)|\[|\]|\{|\}', lambda x : (x, x)),
                    (r'[a-zA-Z]+[a-zA-Z_0-9]*', lambda x : ('ID', x)),
                    (r'[0-9]+', lambda x : ('INTEGER', x)),
                    ]
        import os
        try:
            os.remove("YappyTab")
        except:
            pass
        Yappy.__init__(self, tokenize = tokenize, grammar = grammar)

    def default_rule(self, tokens, ctx):
        return tokens[0]

    def bool_rule(self, tokens, ctx):
        b = tokens[0]
        if b == 'true':
            return Bool(True)
        else:
            return Bool(False)

    def globally_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('G deadlock'))
        Globally(formula=Deadlock())
        """
        return Globally(tokens[1])

    def future_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('F deadlock'))
        Future(formula=Deadlock())
        """
        return Future(tokens[1])

    def next_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('X deadlock'))
        Next(formula=Deadlock())
        """
        return Next(tokens[1])

    def not_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('not deadlock'))
        Negation(formula=Deadlock())
        """
        return Negation(tokens[1])

    def until_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock U deadlock'))
        Until(left=Deadlock(), right=Deadlock())
        """
        return Until(tokens[0], tokens[2])

    def release_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock R deadlock'))
        Release(left=Deadlock(), right=Deadlock())
        """
        return Release(tokens[0], tokens[2])

    def and_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock and deadlock'))
        Conjunction(operands=[Deadlock(), Deadlock()])
        """
        return Conjunction([ tokens[0], tokens[2] ])

    def or_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock or deadlock'))
        Disjunction(operands=[Deadlock(), Deadlock()])
        """
        return Disjunction([ tokens[0], tokens[2] ])

    def xor_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock xor deadlock'))
        ExclusiveDisjunction(operands=[Deadlock(), Deadlock()])
        """
        return ExclusiveDisjunction([ tokens[0], tokens[2] ])

    def equiv_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock <=> deadlock'))
        Equivalence(left=Deadlock(), right=Deadlock())
        """
        return Equivalence(tokens[0], tokens[2])

    def impl_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock => deadlock'))
        Implication(left=Deadlock(), right=Deadlock())
        """
        return Implication(tokens[0], tokens[2])

    def plus_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('1 + 2 < 4'))
        IntegerComparison(operator=LT(), left=Sum(operands=[IntegerConstant(value='1'), IntegerConstant(value='2')]), right=IntegerConstant(value='4'))
        """
        return Sum([tokens[0], tokens[2]])

    def scope_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('(1 + 1) + 1 < 4'))
        IntegerComparison(operator=LT(), left=Sum(operands=[Sum(operands=[IntegerConstant(value='1'), IntegerConstant(value='1')]), IntegerConstant(value='1')]), right=IntegerConstant(value='4'))
        >>> print ast.dump(PropertyParser().input('1 + (1 + 1) < 4'))
        IntegerComparison(operator=LT(), left=Sum(operands=[IntegerConstant(value='1'), Sum(operands=[IntegerConstant(value='1'), IntegerConstant(value='1')])]), right=IntegerConstant(value='4'))
        """
        return tokens[1]

    def id_rule(self, tokens, ctx):
        return tokens[0]

    def bound_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('bound(s1) = 1'))
        IntegerComparison(operator=EQ(), left=PlaceBound(place_name='s1'), right=IntegerConstant(value='1'))
        """
        return PlaceBound(tokens[2])

    def marking_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('marking(s1) = []'))
        MultisetComparison(operator=EQ(), left=PlaceMarking(place_name='s1'), right=MultisetConstant(elements=[]))
        """
        return PlaceMarking(tokens[2])

    def live_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('live(0, t1)'))
        Live(level='0', transition_name='t1')
        """
        return Live(tokens[2], tokens[4])

    def fireable_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('fireable(t)'))
        Fireable(transition_name='t')
        """
        return Fireable(tokens[2])

    def all_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('all(p, f)'))
        All(place_name='p', function_name='f')
        """
        return All(tokens[2], tokens[4])

    def any_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('any(p, f)'))
        Any(place_name='p', function_name='f')
        """
        return Any(tokens[2], tokens[4])

    def deadlock_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('deadlock'))
        Deadlock()
        """
        return Deadlock()

    def integer_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('1 = 1'))
        IntegerComparison(operator=EQ(), left=IntegerConstant(value='1'), right=IntegerConstant(value='1'))
        """
        return IntegerConstant(tokens[0])

    def card_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('card(marking(s)) = 1'))
        IntegerComparison(operator=EQ(), left=MultisetCardinality(multiset=PlaceMarking(place_name='s')), right=IntegerConstant(value='1'))
        """
        return MultisetCardinality(tokens[2])

    __operator_map__ = { '<' : LT(), '<=' : LE(), '=' : EQ(), '!=' : NE(), '>=' :  GE(), '>' : GT() }
    def integer_cmp_rule(self, tokens, ctx):
        """
        >>> def dump(e): print ast.dump(PropertyParser().input(e))
        >>> dump('1 <= 1')
        IntegerComparison(operator=LE(), left=IntegerConstant(value='1'), right=IntegerConstant(value='1'))
        >>> dump('1 < 1')
        IntegerComparison(operator=LT(), left=IntegerConstant(value='1'), right=IntegerConstant(value='1'))
        >>> dump('1 = 1')
        IntegerComparison(operator=EQ(), left=IntegerConstant(value='1'), right=IntegerConstant(value='1'))
        >>> dump('1 != 1')
        IntegerComparison(operator=NE(), left=IntegerConstant(value='1'), right=IntegerConstant(value='1'))
        >>> dump('1 >= 1')
        IntegerComparison(operator=GE(), left=IntegerConstant(value='1'), right=IntegerConstant(value='1'))
        >>> dump('1 > 1')
        IntegerComparison(operator=GT(), left=IntegerConstant(value='1'), right=IntegerConstant(value='1'))
        """
        return IntegerComparison(self.__operator_map__[tokens[1]], tokens[0], tokens[2])

    def multiset_cmp_rule(self, tokens, ctx):
        """
        >>> def dump(e): print ast.dump(PropertyParser().input(e))
        >>> dump('[] <= []')
        MultisetComparison(operator=LE(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=[]))
        >>> dump('[] < []')
        MultisetComparison(operator=LT(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=[]))
        >>> dump('[] = []')
        MultisetComparison(operator=EQ(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=[]))
        >>> dump('[] != []')
        MultisetComparison(operator=NE(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=[]))
        >>> dump('[] >= []')
        MultisetComparison(operator=GE(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=[]))
        >>> dump('[] > []')
        MultisetComparison(operator=GT(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=[]))
        """
        return MultisetComparison(self.__operator_map__[tokens[1]], tokens[0], tokens[2])

    def empty_multiset_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('[] = []'))
        MultisetComparison(operator=EQ(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=[]))
        """
        return MultisetConstant([])

    def multiset_rule(self, tokens, ctx):
        """
        >>> print ast.dump(PropertyParser().input('[] < [1]'))
        MultisetComparison(operator=LT(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=['1']))
        >>> print ast.dump(PropertyParser().input('[] < [1, 1, 1]'))
        MultisetComparison(operator=LT(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=['1', '1', '1']))
        >>> print ast.dump(PropertyParser().input('[] < [dot, 1, dot]'))
        MultisetComparison(operator=LT(), left=MultisetConstant(elements=[]), right=MultisetConstant(elements=['dot', '1', 'dot']))
        """
        return MultisetConstant(tokens[1])

    def multiset_elts_seq_rule(self, tokens, ctx):
        return tokens[0] + tokens[2]

    def multiset_python_expression_rule(self, tokens, ctx):
        return MultisetPythonExpression(merge_spaces(tokens[0][2:-2]))

# p = PropertyParser()
# print "out: ", p.input("F [dot] < marking( place52 ) \\/ G card( marking( 'long place name' )) + 1 + 1 + 1 <= 5 U bound( p3 ) <= 4")
# f = "G bound( place2 ) <= 1 \\/ G ( card(marking('long place name')) = card(marking(shortname)) => [1,1,1] <= marking(place3) )"
# formula = p.input(f)
# print formula
#
# print ast.dump(formula)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
