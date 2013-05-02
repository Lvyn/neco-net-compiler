import properties
import re
import sys
import xml.dom.minidom as dom

PROPERTY_SET_NAME = "property-set"
PROPERTY_NAME = "property"
ID_NAME = "id"

STRUCTURAL_ONLY = "structural-only"
LTL_ONLY = "ltl-only"
CTL_ONLY = "ctl-only"
REACHABILITY_ONLY = "reachability-only"

PROPERTY_TAG = [ STRUCTURAL_ONLY, LTL_ONLY, CTL_ONLY, REACHABILITY_ONLY ]

INVARIANT = "invariant"
IMPOSSIBILITY = "impossibility"

ALL_PATHS = "all-paths"
EXISTS_PATH = "exists-path"

CONJUNCTION = "conjunction"
DISJUNCTION = "disjunction"
EXCLUSIVE_DISJUNCTION = "exclusive-disjunction"

NEGATION = "negation"
EQUIVALENCE = "equivalence"
IMPLICATION = "implication"

GLOBALLY = "globally"
FINALLY = "finally"
NEXT = "next"
UNTIL = "until"

BEFORE = "before"
REACH = "reach"
STRENGTH = "strength"
STRONG = "strong"
WEAK = "weak"

IS_DEADLOCK = "is-deadlock"
IS_LIVE = "is-live"
IS_FIREABLE = "is-fireable"
LEVEL = "level"
LEVEL_0 = "l0"
LEVEL_1 = "l1"
LEVEL_2 = "l2"
LEVEL_3 = "l3"
LEVEL_4 = "l4"
TRANSITION_NAME = "transition-name"

SUM = "sum"
INTEGER_LE = "integer-le"
INTEGER_LT = "integer-lt"
INTEGER_EQ = "integer-eq"
INTEGER_NE = "integer-ne"
INTEGER_GT = "integer-gt"
INTEGER_GE = "integer-ge"

MULTISET_LE = "multiset-le"
MULTISET_LT = "multiset-lt"
MULTISET_EQ = "multiset-eq"
MULTISET_NE = "multiset-ne"
MULTISET_GT = "multiset-gt"
MULTISET_GE = "multiset-ge"

MULTISET_CARDINALITY = "multiset-cardinality"
MULTISET_CONSTANT = "multiset-constant"

PLACE_BOUND = "place-bound"
PLACE_NAME = "place-name"
PLACE_MARKING = "place-marking"
INTEGER_CONSTANT = "integer-constant"

TUPLE = "tuple"
BINDING = "binding"
VALUE_VARIABLE = "value-variable"
VALUE_CONSTANT = "value-constant"

#booleans
TRUE="true"
FALSE="false"

#next operator specials
IF_NO_SUCCESSOR = "if-no-successor"
STEPS = "steps"

FORMULA_HEAD = [ INVARIANT, IMPOSSIBILITY,
                 CONJUNCTION, DISJUNCTION, EXCLUSIVE_DISJUNCTION, EQUIVALENCE, IMPLICATION, NEGATION,
                 INTEGER_LE, INTEGER_LT, INTEGER_EQ, INTEGER_NE, INTEGER_GT, INTEGER_GE,
                 IS_LIVE, IS_FIREABLE,
                 ALL_PATHS, EXISTS_PATH ]
NAME_ATTRIBUTE = "name"

def tag2str(tag):
    if tag == STRUCTURAL_ONLY:
        return "struct"
    elif tag == LTL_ONLY:
        return "ltl"
    elif tag == CTL_ONLY:
        return "ctl"
    elif tag == REACHABILITY_ONLY:
        return "reach"

class ReachabilityHelper(object):

    def __init__(self, kind, formula):
        self.kind = kind
        self.formula = formula

    @classmethod
    def Invariant(cls, *args):
        return ReachabilityHelper(INVARIANT, *args)

    @classmethod
    def Impossibility(cls, *args):
        return ReachabilityHelper(IMPOSSIBILITY, *args)

    def isInvariant(self):
        return self.kind == INVARIANT

    def isImpossibility(self):
        return self.kind == IMPOSSIBILITY

    def __iter__(self):
        yield self.formula

class ParserError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    @classmethod
    def expected(cls, expected, got):
        return ParserError("expected a {!s} got {!s}".format(expected, got))

    @classmethod
    def missing_attribute(cls, obj, attribute):
        return ParserError("{!s} does not have an attribute {!s}".format(obj, attribute))

    @classmethod
    def should_appear_only_once(cls, node, obj):
        return ParserError("{!s} should appear only once in {!s}".format(node, obj))

    @classmethod
    def cannot_be_empty(cls, node):
        return ParserError("{!s} cannot be empty".format(node))

    @classmethod
    def should_have_exaclty_n_childs(node, n):
        return ParserError("{!s} should have exaclty {!s} child{!s}".format(node, n, '' if n == 1 else 's'))

class UnsupportedNode(Exception):
    
    def __init__(self, node, msg = None):
        self.node = node
        self.msg = msg
        
    def __str__(self):
        if self.msg:
            return self.msg
        else:
            return "Unsupported node {}.".format(self.node)

class RunOnce(object):

    def __init__(self, exception):
        self._called = False
        self._exception = exception

    def __call__(self):
        if self._called:
            raise self._exception
        self._called = True

    def called(self):
        return self._called


def remove_dull_text_nodes(node):
    if node.nodeType == dom.Node.TEXT_NODE:
        if re.match(r'\s', node.data):
            return None
        else:
            return node

    remove_list = []
    for child in node.childNodes:
        keep = remove_dull_text_nodes(child)
        if not keep:
            remove_list.append(child)
    for child in remove_list:
        node.removeChild(child)
    return node


def get_property_set(dom):
    if len(dom.childNodes) > 1:
        print "property set has more than one element."

    property_set = None
    for child in dom.childNodes:
        property_set = child
        if property_set.nodeName != PROPERTY_SET_NAME:
            raise ParserError.expected(PROPERTY_SET_NAME, property_set.nodeName)

    return property_set

class Property(object):
    def __init__(self):
        self._id = None
        self._property_tag = None
        self._formula = None

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, new_formula):
        self._formula = new_formula

    @property
    def tag(self):
        return self._property_tag

    @tag.setter
    def tag(self, new_tag):
        self._property_tag = new_tag

    def __str__(self):
        return "{tag} {id!s}: {formula!s}".format(id=self._id, tag=tag2str(self._property_tag), formula=self._formula)

def parse_node_name(elt):
    if elt.nodeName == PLACE_NAME:
        return get_attribute(elt, NAME_ATTRIBUTE)
    else:
        raise ParserError.expected(PLACE_NAME, elt.nodeName)

__string_to_level_map = {
    LEVEL_0 : 0,
    LEVEL_1 : 1,
    LEVEL_2 : 2,
    LEVEL_3 : 3,
    LEVEL_4 : 4
}

def string_to_level(level):
    return __string_to_level_map[level]

def get_attribute(node, attr_name):
    try:
        return node.attributes[attr_name].value
    except KeyError:
        raise ParserError.missing_attribute(node.nodeName, attr_name)

def textual_disjunction(*elts):
    text = None
    length = len(elts)
    if length > 1:
        text = ", ".join(elts[:-1])
        text += "or " + elts[-1]
    elif length == 1:
        text = elts[0]
    return text

def parse_is_live(node):
    level = ""
    transition = ""
    level_found = RunOnce(ParserError.should_appear_only_once(LEVEL, IS_LIVE))
    transition_found = RunOnce(ParserError.should_appear_only_once(TRANSITION_NAME, IS_LIVE))
    for child in node.childNodes:
        if child.nodeName == LEVEL:
            level_found()
            level = child.childNodes[0].data

        elif child.nodeName == TRANSITION_NAME:
            transition_found()
            transition = get_attribute(child, NAME_ATTRIBUTE)

        else:
            raise ParserError.expected(textual_disjunction(LEVEL, TRANSITION_NAME), child.nodeName)

    return properties.Live(string_to_level(level), transition)

def parse_is_fireable(node):
    transition = ""
    transition_found = RunOnce(ParserError.should_appear_only_once(TRANSITION_NAME, IS_FIREABLE))
    for child in node.childNodes:
        if child.nodeName == TRANSITION_NAME:
            transition_found()
            transition = get_attribute(child, NAME_ATTRIBUTE)
        else:
            raise ParserError.expected(TRANSITION_NAME, child.nodeName)

    return properties.Fireable(transition)


__string_to_operator_map = {
    INTEGER_LE: properties.LE(),
    INTEGER_LT: properties.LT(),
    INTEGER_EQ: properties.EQ(),
    INTEGER_NE: properties.NE(),
    INTEGER_GT: properties.GT(),
    INTEGER_GE: properties.GE(),

    MULTISET_LE: properties.LE(),
    MULTISET_LT: properties.LT(),
    MULTISET_EQ: properties.EQ(),
    MULTISET_NE: properties.NE(),
    MULTISET_GT: properties.GT(),
    MULTISET_GE: properties.GE(),
}

def string_to_operator(s):
    return __string_to_operator_map[s]

def parse_subformulas(elt, count = None):
    formulas = [ parse_formula(e) for e in elt.childNodes ]
    if count != None and len(formulas) != count:
        raise ParserError.should_appear_only_once
    return formulas

def parse_binding(node):
    name, value = None, None
    got_variable = RunOnce( ParserError.should_appear_only_once(VALUE_VARIABLE, BINDING) )
    got_value    = RunOnce( ParserError.should_appear_only_once(VALUE_CONSTANT, BINDING) )
    for child in node.childNodes:
        if child.nodeName == VALUE_VARIABLE:
            got_variable()
            name = get_attribute(child, "name")
        elif child.nodeName == VALUE_CONSTANT:
            got_value()
            value = get_attribute(child, "value")
    return name, value

def parse_value(node):
    return get_attribute(node, "value")

def get_tuple(elt):
    got_binding = False
    got_value = False
    value_list = []
    value_map = {}
    for node in elt.childNodes:
        if node.nodeName == BINDING:
            got_binding = True
            name, value = parse_binding(node)
            if name in value_map:
                raise SyntaxError("{} appears twice in tuple".format(name))
            value_map[name] = value

        elif node.nodeName == VALUE_CONSTANT:
            got_value = True
            value = parse_value(node)
            value_list.append(value)
        else:
            raise ParserError("malformed tuple, {} found".format(node.nodeName))
    if got_value and got_binding:
        raise SyntaxError("mixing up values and bindings is not allowed")

    if got_binding:
        values_items = sorted( value_map.iteritems(),
                               cmp = lambda pair1, pair2 : cmp(pair1[0], pair2[0]) )
        value_list = map( lambda pair : pair[1],
                          values_items )

    #value_list = map(lambda s : eval(s),
    #                 value_list)
    return tuple(value_list)



def parse_formula(elt):
    if elt.nodeName in [ INVARIANT, IMPOSSIBILITY ]:
        subformulas = parse_subformulas(elt, 1)
        return ReachabilityHelper( elt.nodeName, subformulas[0] )

    elif elt.nodeName == NEXT:
        subformulas = parse_subformulas(elt)
        if len(subformulas) == 1:
            return properties.Next( subformulas[0] )
        else:
            steps = 1
            body = None
            for subformula in subformulas:
                if subformula.isIfNoSuccessor():
                    if not subformula.value:
                        raise UnsupportedNode(subformula, "False if-no-successor nodes are not supported")
                elif subformula.isSteps():
                    steps = subformula.value
                else:               
                    if (body):
                        raise SyntaxError("Multiple formulae in Next node")
                    body = subformula
                    
            def rec(steps, body):
                if steps == 0:
                    return body
                else:
                    return properties.Next( rec(steps-1, body) )
            return rec(steps, body)
            
            
    elif elt.nodeName == IF_NO_SUCCESSOR:
        result = [ e.data for e in elt.childNodes ]
        result_str = "".join(result)
        return properties.IfNoSuccessor(result_str == 'true')
    
    elif elt.nodeName == STEPS:
        result = [ e.data for e in elt.childNodes ]
        result_int = int("".join(result))
        return properties.Steps(result_int)
        
    elif elt.nodeName == GLOBALLY:
        subformulas = parse_subformulas(elt, 1)
        return properties.Globally( subformulas[0] )

    elif elt.nodeName == FINALLY:
        subformulas = parse_subformulas(elt, 1)
        return properties.Future( subformulas[0] )

    elif elt.nodeName == UNTIL:
        subformulas = parse_subformulas(elt)
        before, reach, strength = None, None, None
        for subformula in subformulas:
            if subformula.isBefore():
                before = subformula.formula
            elif subformula.isReach():
                reach = subformula.formula
            elif subformula.isStrength():
                strength = subformula.value
            else:
                raise SyntaxError("illformed until node.")
        if before and reach and strength:
            if strength == STRONG:
                return properties.Until( before, reach )
            elif strength == WEAK:
                return properties.WeakUntil( before, reach )
            else:
                 raise SyntaxError("illformed until::strength node.")
        else:
            raise SyntaxError("illformed until node.")
    
    elif elt.nodeName == BEFORE:
        subformulas = parse_subformulas(elt, 1)
        return properties.Before( subformulas[0] )
    
    elif elt.nodeName == REACH:
        subformulas = parse_subformulas(elt, 1)
        return properties.Reach( subformulas[0] )
    
    elif elt.nodeName == STRENGTH:
        result = [ e.data for e in elt.childNodes ]
        result_str = "".join(result)
        return properties.Strength( result_str )
    
    elif elt.nodeName == TRUE:
        return properties.Bool(True)
    
    elif elt.nodeName == FALSE:
        return properties.Bool(False)
    
    elif elt.nodeName == IS_DEADLOCK:
        return properties.Deadlock()

    elif elt.nodeName == ALL_PATHS:
        subformulas = parse_subformulas(elt, 1)
        return properties.AllPaths( subformulas[0] )
    
    elif elt.nodeName == EXISTS_PATH:
        subformulas = parse_subformulas(elt, 1)
        return properties.ExistsPath( subformulas[0] )
        
    elif elt.nodeName == CONJUNCTION:
        return properties.Conjunction( parse_subformulas(elt) )

    elif elt.nodeName == EQUIVALENCE:
        subformulas = parse_subformulas(elt, 2)
        return properties.Equivalence(subformulas[0], subformulas[1])

    elif elt.nodeName == IMPLICATION:
        subformulas = parse_subformulas(elt, 2)
        return properties.Implication(subformulas[0], subformulas[1])

    elif elt.nodeName == DISJUNCTION:
        return properties.Disjunction( parse_subformulas(elt) )

    elif elt.nodeName == EXCLUSIVE_DISJUNCTION:
        return properties.ExclusiveDisjunction( parse_subformulas(elt) )

    elif elt.nodeName == NEGATION:
        subformulas = parse_subformulas(elt, 1)
        return properties.Negation( formula=subformulas[0] )

    elif elt.nodeName == SUM:
        subformulas = parse_subformulas(elt)
        formula = properties.Sum( operands=subformulas )
        if len(formula.operands) == 0:
            raise ParserError.cannot_be_empty(elt)
        return formula

    elif elt.nodeName in [INTEGER_LE, INTEGER_LT, INTEGER_EQ, INTEGER_NE, INTEGER_GT, INTEGER_GE ]:
        subformulas = parse_subformulas(elt, 2)
        operator = string_to_operator(elt.nodeName)
        return properties.IntegerComparison(operator, subformulas[0], subformulas[1])

    elif elt.nodeName in [MULTISET_LE, MULTISET_LT, MULTISET_EQ, MULTISET_NE, MULTISET_GT, MULTISET_GE ]:
        subformulas = parse_subformulas(elt, 2)
        operator = string_to_operator(elt.nodeName)
        return properties.MultisetComparison(operator, subformulas[0], subformulas[1])

    elif elt.nodeName == PLACE_BOUND:
        if len(elt.childNodes) != 1:
            raise ParserError.should_have_exaclty_n_childs(elt, 1)

        name = parse_node_name(elt.childNodes[0])
        return properties.PlaceBound(name)

    elif elt.nodeName == MULTISET_CARDINALITY:
        subformulas = parse_subformulas(elt, 1)
        return properties.MultisetCardinality( subformulas[0] )

    elif elt.nodeName == PLACE_MARKING:
        if len(elt.childNodes) != 1:
            raise ParserError.should_have_exaclty_n_childs(elt, 1)

        name = parse_node_name(elt.childNodes[0])
        return properties.PlaceMarking(name)

    elif elt.nodeName == INTEGER_CONSTANT:
        value = get_attribute(elt, 'value')
        return properties.IntegerConstant(value)

    elif elt.nodeName == MULTISET_CONSTANT:
        sub_formulas = parse_subformulas(elt, 1)
        return properties.MultisetConstant(sub_formulas)

    elif elt.nodeName == IS_LIVE:
        return parse_is_live(elt)

    elif elt.nodeName == IS_FIREABLE:
        return parse_is_fireable(elt)

    elif elt.nodeName == TUPLE:
        return get_tuple(elt)

    else:
        raise SyntaxError("{} nodes are not supported".format(elt.nodeName))

    return None

def typebased_transformation(prop):
    if prop.tag == STRUCTURAL_ONLY:
        # transform to LTL using G(formula)
        formula = prop.formula
        prop.formula = properties.Globally( formula )

    elif prop.tag == LTL_ONLY:
        pass # nothing to do

    elif prop.tag == CTL_ONLY:
        # CTL properties are not supported
        print >> sys.stderr, "CTL formulae are not supported"
        exit(1)

    elif prop.tag == REACHABILITY_ONLY:
        helper = prop.formula
        if helper.isInvariant():
            prop.formula = properties.Globally( helper.formula )
        if helper.isImpossibility():
            prop.formula = properties.Negation( properties.Future( helper.formula ) )

    else:
        raise NotImplementedError

    return prop

def get_properties(property_set):
    props = []
    for child in property_set.childNodes:
        if child.nodeName != PROPERTY_NAME:
            continue

        prop = Property()

        id_found = RunOnce(ParserError.should_appear_only_once(ID_NAME, child.nodeName))
        formula_found = RunOnce(ParserError("multiple formulae found for {!s}".format(child.nodeName)))
        tag_found = RunOnce(ParserError.should_appear_only_once(PROPERTY_NAME, child.nodeName))
        for elt in child.childNodes:
            if elt.nodeName == ID_NAME:
                id_found()
                id_str_list = [ e.data for e in elt.childNodes ]
                id_str = "\n".join(id_str_list)
                prop._id = id_str

            elif elt.nodeName in PROPERTY_TAG:
                tag_found()
                prop.tag = elt.nodeName
                if prop.tag == CTL_ONLY:
                    print >> sys.stderr, "CTL Formulae are not supported"
                    exit(1)

            else: # elif elt.nodeName in FORMULA_HEAD:
                try:
                    formula_found()
                    prop._formula = parse_formula(elt)
                except UnsupportedNode as e:
                    prop._formula = properties.Unsupported(e)

        if not formula_found.called():
            raise ParserError("no formula found in {!s}".format(child.nodeName))

        prop = typebased_transformation(prop)
        props.append(prop)

    return props

def parse(filename):
    document = dom.parse(filename)
    document = remove_dull_text_nodes(document)
    pset = get_property_set(document)
    props = get_properties(pset)
    return props

if __name__ == "__main__":
    props = parse('/home/lukasz/mcc/BenchKit/INPUTS/Railroad-PT-010/LTLMix2.xml')
    for prop in props:
        print str(prop)
