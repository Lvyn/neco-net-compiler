import properties
import xml.dom.minidom as dom
import sys, re

PROPERTY_SET_NAME = "property-set"
PROPERTY_NAME = "property"
ID_NAME = "id"

STRUCTURAL_ONLY = "structural-only"

CONJUNCTION = "conjunction"
NEGATION = "negation"

IS_LIVE = "is-live"
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

PLACE_BOUND = "place-bound"
PLACE_NAME = "place-name"
INTEGER_CONSTANT = "integer-constant"

PROPERTY_TAG = [ STRUCTURAL_ONLY ]
FORMULA_HEAD = [ CONJUNCTION, NEGATION,
                 INTEGER_LE, INTEGER_LT, INTEGER_EQ, INTEGER_NE, INTEGER_GT, INTEGER_GE,
                 IS_LIVE]

NAME_ATTRIBUTE = "name"


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
        return ParserError("{!s} should have exaclty {!s} child{!s}".format(node, 
                                                                            n,
                                                                            '' if n == 1 else 's'))
    
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
        return "id : {!s}\ntag : {!s}\nformula : {!s}".format(self._id, 
                                                              self._property_tag,
                                                              self._formula)
        
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

    return properties.IsLive(string_to_level(level), transition)

__string_to_integer_comparigon_op_map = {
    INTEGER_LE: properties.IntegerComparison.LE,
    INTEGER_LT: properties.IntegerComparison.LT,
    INTEGER_EQ: properties.IntegerComparison.EQ,
    INTEGER_NE: properties.IntegerComparison.NE,
    INTEGER_GT: properties.IntegerComparison.GT,
    INTEGER_GE: properties.IntegerComparison.GE,
}

def string_to_integer_comparison_op(s):
    return __string_to_integer_comparigon_op_map[s]
    
def parse_formula(elt):
    if elt.nodeName == CONJUNCTION:
        formula = properties.Conjunction( [ parse_formula(child) for child in elt.childNodes ] )
        return formula
    
    elif elt.nodeName == NEGATION:
        if len(elt.childNodes) != 1:
            raise ParserError.should_have_exaclty_n_childs(elt, 1)
        
        child = elt.childNodes[0]
        return properties.Negation( parse_formula(child) )
    
    elif elt.nodeName == SUM:
        formula = properties.Sum( [ parse_formula(child) for child in elt.childNodes ] )
        if len(formula.operands) == 0:
            raise ParserError.cannot_be_empty(elt)
        return formula
    
    elif elt.nodeName in [INTEGER_LE, INTEGER_LT, INTEGER_EQ, INTEGER_NE, INTEGER_GT, INTEGER_GE ]:
        if len(elt.childNodes) != 2:
            raise ParserError.should_have_exaclty_n_childs(elt, 2)
        
        left = parse_formula(elt.childNodes[0])
        right = parse_formula(elt.childNodes[1])
        return properties.IntegerComparison(string_to_integer_comparison_op(elt.nodeName),
                                            left,
                                            right)
    
    elif elt.nodeName == PLACE_BOUND:
        if len(elt.childNodes) != 1:
            raise ParserError.should_have_exaclty_n_childs(elt, 1)
        
        name = parse_node_name(elt.childNodes[0])
        return properties.PlaceBound(name)
    
    elif elt.nodeName == INTEGER_CONSTANT:
        value = get_attribute(elt, 'value')
        return properties.IntegerConstant(value)    

    elif elt.nodeName == IS_LIVE:
        return parse_is_live(elt)
    
    else:
        raise SyntaxError
    return None

def typebased_transformation(prop):
    if prop.tag == STRUCTURAL_ONLY:
        # transform to LTL using G(formula)
        formula = prop.formula
        prop.formula = properties.Globally( formula )
    
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
                
            elif elt.nodeName in FORMULA_HEAD:
                formula_found()
                prop._formula = parse_formula(elt)

        if not formula_found.called():
            ParserError("no formula found in {!s}".format(child.nodeName))
        
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
    props = parse('../../tests/check/lamport_fmea-2.23.xml')
    for prop in props:
        print str(prop)
