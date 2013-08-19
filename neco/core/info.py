""" Petri net info structures. """
from collections import defaultdict
from abc import ABCMeta, abstractmethod
from neco.core import netir
from neco.extsnakes import Pid
from neco.utils import Enum, TypeMatch, RegDict
from snakes.nets import BlackToken, dot, Place
from snakes.plugins import status
from snakes.typing import Instance, tNatural, CrossProduct, tAll
import sys


TypeKind = Enum('AnyType', 'TupleType', 'UserType')

class TypeInfo(object):
    """ Class representing and providing types.
    """

    def __init__(self, kind = TypeKind.AnyType, subtypes = [], type_name = ""):
        """ build a new type_info.

        @param kind: type_info kind
        @type_info kind: C{TypeKind}

        @param subtypes: (available if kind is TypeKind.TupleType) list of subtypes.
        @type_info subtypes: C{list<TypeInfo>}

        @param type_name: (available if kind is TypeKind.UserType) type_info name.
        @type_info type_name: C{string}
        """
        self._kind = kind
        if self.is_UserType:
            self._type_name = type_name
        elif self.is_TupleType:
            self._subtypes = subtypes

    @classmethod
    def get(cls, type_name):
        t = getattr(cls, type_name, None)
        if not t:
            print >> sys.stderr, "[W] cannot get type {!s}, using fallback.".format(type_name)
            t = cls.AnyType
        return t

    @classmethod
    def UserType(cls, type_name):
        """ Helper class method for building user types.

        @param type_name: type name
        @type type_name: C{str}
        @return new user type.
        @rtype: C{TypeInfo}
        """
        return cls(kind = TypeKind.UserType, type_name = type_name)

    @classmethod
    def TupleType(cls, subtypes):
        """ Helper class method for building tuple types.

        @param subtypes: list of subtypes.
        @type subtypes: C{list<typeinfo>}
        @return: new tuple type
        @rtype: C{TypeInfo}
        """
        return cls(kind = TypeKind.TupleType, subtypes = subtypes)

    def __len__(self):
        """ Type length.

        @return: Type length.
        @rtype: C{int}
        """
        return (len(self._subtypes) if self.is_TupleType else 1)

    def __repr__(self):
        """ Python string representation.

        @return: Python string representation.
        @rtype: C{str}
        """
        if self.is_UserType:
            return ("TypeInfo(kind={kind}, type_name={type_name})"
                    .format(kind = repr(self._kind), type_name = repr(self._type_name)))
        else:
            return "TypeInfo(kind={kind})".format(kind = repr(self._kind))

    def __str__(self):
        """ Human readable string representation.

        @return: Human readable string.
        @rtype: C{str}
        """
        if self.is_UserType:
            return str(self._type_name)
        elif self.is_TupleType:
            return "(%s)" % ", ".join([ str(e) for e in self._subtypes ])
        elif self.is_AnyType:
            return 'AnyType'

    def __hash__(self):
        h = 0xDEADBEEF
        if self.is_UserType:
            return h ^ hash(self._type_name)
        elif self.is_TupleType:
            magic = 0xC0FFEE
            for i, subtype in enumerate(self._subtypes):
                h ^= hash(subtype) * magic
                magic = magic * (magic + i)
                return h
        else:
            return h


    def split(self):
        """ Get subtypes.

        @return: list of subtypes (empty if is not a TupleType).
        @rtype: C{list<TypeInfo>}
        """
        if not self.is_TupleType:
            raise RuntimeError('Only tuple types can be split.')
        return self._subtypes

    def __iter__(self):
        if not self.is_TupleType:
            raise RuntimeError('Only tuple types can be iterated.')
        return self._subtypes.__iter__()

    @classmethod
    def register_type(cls, type_name):
        """ Register an user type.

        Registering a type provides a new class attribute corresponding to the type,
        a test property to check types is also produced. For instance, registering a
        simple user type

        >>> TypeInfo.register_type('Foo')
        TypeInfo(kind=UserType, type_name='Foo')

        provides a new class attribute C{Foo}, and a property C{is_Foo}.

        >>> str(TypeInfo.Foo)
        'Foo'
        >>> TypeInfo.Foo.is_Foo
        True

        These properties are available for other types:

        >>> (TypeInfo(kind=TypeKind.UserType, type_name='Foo').is_Foo,
        ...  TypeInfo(kind=TypeKind.UserType, type_name='Bar').is_Foo)
        (True, False)

        When one registers a new type, older types have the new property too.

        >>> TypeInfo.register_type('Bar')
        TypeInfo(kind=UserType, type_name='Bar')
        >>> TypeInfo.Foo.is_Foo, TypeInfo.Foo.is_Bar
        (True, False)
        >>> TypeInfo.Foo == TypeInfo.Bar
        False

        >>> str(TypeInfo.Bar), TypeInfo.Bar.is_Foo, TypeInfo.Bar.is_Bar
        ('Bar', False, True)
        >>> (TypeInfo(kind=TypeKind.UserType, type_name='Foo') == TypeInfo.Foo,
        ...  TypeInfo(kind=TypeKind.UserType, type_name='Bar') == TypeInfo.Foo)
        (True, False)

        @param type_name: user type name.
        @type type_name: C{str}
        @return: registered type.
        @rtype: C{TypeInfo}
        """
        t = TypeInfo(kind = TypeKind.UserType, type_name = type_name)
        setattr(cls, type_name, t)
        # gen methods and properties
        setattr(cls, "is_{property_name}".format(property_name = type_name),
                property(lambda self : self._kind == TypeKind.UserType and self._type_name == type_name))
        return t

    @classmethod
    def from_snakes_checker(cls, checker):
        """ Build a TypeInfo from SNAKES checker.

        @param checker: SNAKES checker.
        @type checker: C{snakes.typing.Instance}
        @return: Built type
        @rtype: C{TypeInfo}
        """
        if checker == Instance(int):
            return TypeInfo.Int
        if checker == tNatural:
            return TypeInfo.Int
        elif checker == Instance(BlackToken):
            return TypeInfo.BlackToken
        elif checker == Instance(str):
            return TypeInfo.String
        elif checker == Instance(Pid):
            return TypeInfo.Pid
        elif isinstance(checker, CrossProduct):
            return TypeInfo.TupleType([ TypeInfo.from_snakes_checker(t) for t in checker._types ])
        elif checker == Instance(object) or checker == tAll:
            return TypeInfo.AnyType
        else:
            return TypeInfo.UserType(checker._class.__name__)
        raise RuntimeError('unrechable')

    @classmethod
    def from_raw(cls, raw):
        """ Build a TypeInfo from a raw python value.

        @param raw: raw value.
        @type raw: C{object}
        @return: Built type.
        @rtype: C{TypeInfo}
        """
        class matcher(TypeMatch):
            def match_BlackToken(self, raw):
                return TypeInfo.BlackToken

            def match_int(self, raw):
                return TypeInfo.Int

            def match_str(self, raw):
                return TypeInfo.String

            def match_tuple(self, raw):
                return TypeInfo.TupleType([ TypeInfo.from_raw(elt) for elt in raw ])

            def match_Pid(self, raw):
                return TypeInfo.Pid

            def default(self, raw):
                return TypeInfo.AnyType
        return matcher().match(raw)

    @classmethod
    def from_snakes(cls, obj):
        class matcher(TypeMatch):
            def match_Value(self, obj):
                return cls.from_raw(obj.value)
            def default(self, obj):
                raise NotImplementedError, repr(obj)
        return matcher().match(obj)

    def __eq__(self, other):
        """ Compare two types.

        >>> int   = TypeInfo(TypeKind.UserType, type_name = 'int')
        >>> float = TypeInfo(TypeKind.UserType, type_name = 'float')
        >>> print int == float
        False
        >>> print int == TypeInfo(TypeKind.UserType, type_name = 'int')
        True
        >>> user1 = TypeInfo(TypeKind.UserType, type_name = 'User1')
        >>> user2 = TypeInfo(TypeKind.UserType, type_name = 'User2')
        >>> print user1 == user2, user1 == int, user1 == float, user2 == int
        False False False False
        >>> print user1 == TypeInfo(TypeKind.UserType, type_name = 'User1')
        True
        >>> tuple1 = TypeInfo(TypeKind.TupleType, subtypes = [int, float])
        >>> tuple2 = TypeInfo(TypeKind.TupleType, subtypes = [int, float, int])
        >>> tuple3 = TypeInfo(TypeKind.TupleType, subtypes = [float, int])
        >>> print tuple1 == tuple2, tuple2 == tuple3, tuple1 == tuple3
        False False False
        >>>
        print tuple1 == TypeInfo(TypeKind.TupleType, subtypes = [
        ...    TypeInfo(TypeKind.UserType, type_name = 'int'),
        ...    TypeInfo(TypeKind.UserType, type_name = 'float') ])
        True
        >>> print tuple1 == int
        False
        >>> TypeInfo.TupleType([TypeInfo.Int, TypeInfo.Int]) == TypeInfo.TupleType([TypeInfo.Int, TypeInfo.Int])
        True
        

        @param other: right operand
        @type other: C{TypeInfo}
        @return: C{True} if equal, C{False} otherwise.
        @rtype: C{bool}
        """
        try:
            if self._kind == other._kind:
                if self.is_TupleType:
                    return self._subtypes == other._subtypes
                else:
                    return self._type_name == other._type_name
            else:
                return False
        except AttributeError:
            return False

    def __lt__(self, other):
        if self._kind == other._kind:
            return True
        elif self.is_AnyType:
            return True
        else:
            return False

    def __gt__(self, other):
        return other.__lt__(self)

    def __ne__(self, other):
        return not self == other

    @property
    def is_AnyType(self):
        return self._kind == TypeKind.AnyType

    @property
    def is_TupleType(self):
        return self._kind == TypeKind.TupleType

    @property
    def is_UserType(self):
        return self._kind == TypeKind.UserType

    @property
    def kind(self):
        return self._kind

    @property
    def user_type_name(self):
        assert(self.is_UserType)
        return self._type_name

    @property
    def has_pids(self):
        """
        >>> t = TypeInfo.get('Pid')
        >>> t.has_pids
        True
        >>> t = TypeInfo.get('Int')
        >>> t.has_pids
        False
        >>> t = TypeInfo.TupleType([TypeInfo.get('Int'), TypeInfo.get('Int')])
        >>> t.has_pids
        False
        >>> t = TypeInfo.TupleType([TypeInfo.get('Pid'), TypeInfo.get('Int')])
        >>> t.has_pids
        True
        >>> t = TypeInfo.TupleType([TypeInfo.get('Int'), TypeInfo.TupleType([TypeInfo.get('Pid'), TypeInfo.get('Int')])])
        >>> t.has_pids
        True
        """
        red = lambda acc, x : (acc or x.has_pids)
        return self.is_Pid or (self.is_TupleType and reduce(red, self, False))

TypeInfo.AnyType = TypeInfo(kind = TypeKind.AnyType)
TypeInfo.register_type('Int')
TypeInfo.register_type('Bool')
TypeInfo.register_type('String')
TypeInfo.register_type('BlackToken')

TypeInfo.register_type('Pid')
TypeInfo.register_type('dict')
TypeInfo.register_type('set')

TypeInfo.register_type('NecoCtx')

################################################################################

TokenKind = Enum("Variable", "Value", "Expression", "Tuple")
class TokenInfo(object):
    """
    """

    __metaclass__ = ABCMeta

    def __init__(self, raw_token, kind = None, token_type = None):
        """
        """
        self._raw = raw_token
        self._data = RegDict()

        if kind is not None:
            assert kind in TokenKind
            self._kind = kind

        if token_type != None:
            assert isinstance(token_type, TypeInfo)
            self._type = token_type
        else:
            self._type = TypeInfo.from_raw(raw_token)

    @property
    def data(self):
        """ Get the data dict. """
        return self._data

    def __repr__(self):
        return "TokenInfo(raw_token=%s, kind=%s, type=%s)" % (repr(self._raw), repr(self._kind), repr(self._type))

    def update_type(self, token_type):
        assert(isinstance(token_type, TypeInfo))
        self._type = token_type

    @abstractmethod
    def base_names(self):
        pass


    @abstractmethod
    def variables(self):
        pass

    @property
    def is_Variable(self):
        return self._kind == TokenKind.Variable

    @property
    def is_Value(self):
        return self._kind == TokenKind.Value

    @property
    def is_Expression(self):
        return self._kind == TokenKind.Expression

    @property
    def is_Tuple(self):
        return self._kind == TokenKind.Tuple

    @property
    def raw(self):
        return self._raw

    @property
    def type(self):
        return self._type

    @classmethod
    def from_raw(cls, raw_token):
        raw_type = TypeInfo.from_raw(raw_token)
        if raw_type.is_TupleType:
            return TupleInfo([ cls.from_raw(c) for c in raw_token ] , tuple_type = raw_type)
        else:
            return ValueInfo(raw_token, value_type = raw_type)

    @classmethod
    def from_snakes(cls, snk_obj):
        class matcher(TypeMatch):
            def match_Value(self, v):
                return cls.from_raw(v.value)

            def match_Variable(self, v):
                if v.name == "dot":
                    return ValueInfo(dot, type = TypeInfo.BlackTokenType)
                return VariableInfo(v.name)

            def match_Expression(self, e):
                return ExpressionInfo(e._str)

            def match_Tuple(self, t):
                tpl = TupleInfo([])
                for c in t._components:
                    cinfo = cls.from_snakes(c)
                    tpl.components.append(cinfo)
                return tpl

            def default(self, obj):
                raise NotImplementedError, obj.__class__

        return matcher().match(snk_obj)

class ValueInfo(TokenInfo):
    """ values
    """

    def __init__(self, value_data, value_type = None):
        """ builds a new Value from raw data

        @param value_data: data
        @type_info value_data: C{object}
        """
        value_type = value_type if value_type else TypeInfo.AnyType
        TokenInfo.__init__(self, value_data, kind = TokenKind.Value, token_type = value_type)

    def __repr__(self):
        return "ValueInfo(value_data=%s, type=%s)" % (repr(self._raw), repr(self.type))

    def __str__(self):
        return "Value<%s>(%s)" % (str(self.type), str(self._raw))

    def base_names(self):
        return (self.name, self.local_name)

    def variables(self):
        return defaultdict(lambda : 0)

class VariableInfo(TokenInfo):
    """ variables """
    def __init__(self, name, variable_type = None):
        TokenInfo.__init__(self,
                           object(),    # dummy value
                           kind = TokenKind.Variable,
                           token_type = variable_type)
        self._name = name
        self._localname = name

    def variables(self):
        return defaultdict(lambda : 0, { self.name : 1 })

    @property
    def name(self):
        return self._name

    def base_names(self):
        return (self.name, self.local_name)

    def __repr__(self):
        return "VariableInfo(name=%s, type=%s)" % (repr(self.name), repr(self.type))

    def __str__(self):
        return "Variable<%s>(%s)" % (str(self.type), str(self.name))

class ExpressionInfo(TokenInfo):
    """ expressions """
    def __init__(self, s):
        TokenInfo.__init__(self, s, kind = TokenKind.Expression)

    def variables(self):
        return defaultdict(lambda : 0)    # To do

    def base_names(self):
        return (self.name, self.local_name)

    def __repr__(self):
        return "ExpressionInfo(s=%s)" % repr(self.raw)

    def __str__(self):
        return "Expression(%s)" % str(self.raw)

################################################################################

class TupleInfo(TokenInfo):
    def __init__(self, components = None, tuple_type = None):
        components = components if components else []
        tuple_type = tuple_type if tuple_type else TypeInfo.AnyType

        TokenInfo.__init__(self, components, kind = TokenKind.Tuple, token_type = tuple_type)
        self.components = components

    def variables(self):
        vardict = defaultdict(lambda : 0)
        for c in self.components:
            for name, occurences in c.variables().iteritems():
                vardict[name] += occurences
        return vardict

    def __repr__(self):
        return "TupleInfo(components=%s)" % repr([ c for c in self.components ])

    def __str__(self):
        return "TupleInfo(%s)" % (", ".join([ str(c) for c in self.components]))

    def split(self):
        return self.components

    def __len__(self):
        return len(self.components)

    def __iter__(self):
        return self.components.__iter__()

    def base_names(self):
        return [ component.base_names() for component in self.components if not isinstance(component, TupleInfo) ]

################################################################################

def build_tuple(info):
    """ Helper function to build tuples.

    @param info: info structure
    @type info: C{netir._AST}
    """
    if info.is_tuple():
        return netir.Tuple(components = [ build_tuple(component) for component in info.components ])

    elif info.is_variable():
        return netir.Name(info.name)

    elif info.is_value():
        return netir.PyExpr(info.value)

    else:
        raise NotImplementedError, info.__class__

################################################################################

ArcKind = Enum("Variable", "Value", "Test", "Flush", "Tuple", "Expression", "MultiArc", "GeneratorMultiArc")
class ArcInfo(object):

    def __init__(self, place_info, arc_annotation, is_input):
        self._is_input = is_input
        self.place_info = place_info
        self.arc_annotation = arc_annotation
        self._vars = defaultdict(lambda : 0)
        self._data = RegDict()

        arc_info = self
        class matcher(TypeMatch):
            # variables
            def match_Variable(self, arc_annotation):
                # to do, infer type_info from input_arcs
                if arc_annotation.name == "dot":
                    arc_info.value = ValueInfo(dot, value_type = TypeInfo.BlackToken)
                    arc_info.kind = ArcKind.Value
                    # no variables
                else:
                    arc_info.variable = VariableInfo(name = arc_annotation.name)
                    if arc_info.is_input:
                        arc_info.variable.update_type(arc_info.place_info.type)
                    arc_info.kind = ArcKind.Variable
                    arc_info._vars[arc_annotation.name] += 1

            # values
            def match_Value(self, arc_annotation):
                arc_info.value = ValueInfo(arc_annotation.value)
                arc_info.kind = ArcKind.Value
                arc_info._vars = {}

            # tests
            def match_Test(self, arc_annotation):
                arc_info.annotation = arc_annotation._annotation
                arc_info.kind = ArcKind.Test
                inner = TokenInfo.from_snakes(arc_info.annotation)
                arc_info.inner = inner

                if inner.is_Value:
                    arc_info.value = inner
                elif inner.is_Variable:
                    arc_info.variable = inner
                elif inner.is_Tuple:
                    arc_info.tuple = inner
                else:
                    raise NotImplementedError, inner

                if arc_info.is_input and arc_info.inner.is_Variable:
                    arc_info.inner.update_type(arc_info.place_info.type)
                arc_info._vars = arc_info.inner.variables()

            # flush
            def match_Flush(self, arc_annotation):
                arc_info.annotation = arc_annotation._annotation
                arc_info.kind = ArcKind.Flush
                arc_info.inner = TokenInfo.from_snakes(arc_info.annotation)
                arc_info._vars = arc_info.inner.variables()

            # expression
            def match_Expression(self, arc_annotation):
                arc_info.kind = ArcKind.Expression
                arc_info.expr = TokenInfo.from_snakes(arc_annotation)
                arc_info._vars = arc_info.expr.variables()    # may be bad if input

            # tuple
            def match_Tuple(self, arc_annotation):
                arc_info.kind = ArcKind.Tuple
                arc_info.tuple = TokenInfo.from_snakes(arc_annotation)
                if arc_info.is_input:
                    arc_info.tuple.update_type(arc_info.place_info.type)
                arc_info._vars = arc_info.tuple.variables()

            # multiarc
            def match_MultiArc(self, arc_annotation):
                arc_info.kind = ArcKind.MultiArc
                arc_info.sub_arcs = [ ArcInfo(place_info, annotation, is_input)
                                  for annotation in arc_annotation._components ]

                vardict = arc_info._vars
                for arc in arc_info.sub_arcs:
                    for name, occurences in arc.variables().iteritems():
                        vardict[name] += occurences
            def match_GeneratorMultiArc(self, arc_annotation):
                arc_info.kind = ArcKind.GeneratorMultiArc
                arc_info.sub_arcs = [ ArcInfo(place_info, annotation, is_input)
                                  for annotation in arc_annotation.components ]
                arc_info.pid = VariableInfo(name = arc_annotation.pid.name, variable_type = TypeInfo.Pid)
                arc_info.counter = VariableInfo(name = arc_annotation.counter.name, variable_type = TypeInfo.Int)
                arc_info.new_pids = [ VariableInfo(name = pid.name, variable_type = TypeInfo.Pid) for pid in arc_annotation.new_pids ]

            def default(self, arc_annotation):
                raise NotImplementedError, arc_annotation.__class__
        matcher().match(arc_annotation)


    @property
    def data(self):
        """ Get the data dict. """
        return self._data


    @property
    def variables_info(self):
        """
        """
        if self.is_Variable:
            return [ self.variable ]
        elif self.is_Test:
            if self.inner.is_Variable:
                return [ self.inner ]
            else:
                # TO DO tuple
                return []
        else:
            # TO DO tuple
            return []

    def type_vars(self, variables):
        """

        @param variables:
        @type variables: C{}
        """
        if self.is_Variable:
            name = self.variable.name
            other = None
            for v in variables:
                if v.name == name:
                    other = v
            if other:
                self.variable.update_type(other.type)

    def variables(self):
        return self._vars

    @property
    def is_input(self):
        return self._is_input

    @property
    def is_Variable(self):
        return self.kind == ArcKind.Variable

    @property
    def is_Value(self):
        return self.kind == ArcKind.Value

    @property
    def is_Test(self):
        return self.kind == ArcKind.Test

    @property
    def is_Flush(self):
        return self.kind == ArcKind.Flush

    @property
    def is_Tuple(self):
        return self.kind == ArcKind.Tuple

    @property
    def is_Expression(self):
        return self.kind == ArcKind.Expression

    @property
    def is_MultiArc(self):
        return self.kind == ArcKind.MultiArc

    @property
    def is_GeneratorMultiArc(self):
        return self.kind == ArcKind.GeneratorMultiArc

    @property
    def place_name(self):
        return self.place_info.name

    def __str__(self):
        if self.is_input:
            s = "input "
        else:
            s = "output "

        if self.is_Variable:
            s += "arc " + str(self.variable)
        elif self.is_Value:
            s += "arc " + str(self.value)
        elif self.is_Tuple:
            s += "arc " + str(self.tuple)
        elif self.is_Test:
            s += "arc Test inner = " + str(self.inner)
        elif self.is_Flush:
            s += "arc Flush " + str(self.inner)
        elif self.is_Expression:
            s += "arc expression " + str(self.expr)

        return s

################################################################################

class TransitionInfo(object):
    def __init__(self, trans):
        self.name = trans.name
        self.trans = trans
        self.gvars = trans.guard.vars()
        self._intermediary_variables = []
        self._post = set()
        self._pre = set()
        self._process_name = ""
        self.generator_arc = None

        input_arcs = []
        for place, arc_annotation in trans.input():
            place_info = PlaceInfo.instance[place.name]
            place_info.add_post(self)
            self.add_pre(place_info)
            input_arc = ArcInfo(place_info, arc_annotation, is_input = True)
            input_arcs.append(input_arc)
            self._process_name = place_info.process_name

        self.input_arcs = input_arcs

        outputs = []
        for place, arc_annotation in trans.output():
            place_info = PlaceInfo.instance[place.name]
            place_info.add_pre(self)
            self.add_post(place_info)
            output = ArcInfo(place_info, arc_annotation, is_input = False)
            outputs.append(output)
            if output.is_GeneratorMultiArc:
                self.generator_arc = output

        self.outputs = outputs

        vardict = defaultdict(lambda : 0)
        for var in trans.vars():
            vardict[var] = 1

        for input_arc in self.input_arcs:
            for name, occurences in input_arc.variables().iteritems():
                vardict[name] += occurences

        self._vars = vardict

        input_vars = []
        for input_arc in self.input_arcs:
            input_vars.extend(input_arc.variables_info)

        for output in self.outputs:
            output.type_vars(input_vars)

    @property
    def process_name(self):
        return self._process_name

    def variables(self):
        return self._vars

    @property
    def input_multi_places(self):
        for input_arc in self.input_arcs:
            info = input_arc.place_info
            if input_arc.is_MultiArc:
                yield info

    def variable_informations(self):
        """
        """
        l = []
        l.append("********************************************************************************")
        l.append("transition %s" % self.name)
        l.append("********************************************************************************")

        for input_arc in self.input_arcs:
            l.append(str(input_arc))

        for output in self.outputs:
            l.append(str(output))
        l.append("********************************************************************************")
        l.append("inner variables:")
        l.append("********************************************************************************")
        for var in self.intermediary_variables:
            l.append(str(var))

        return "\n" + "\n".join(l)

    @property
    def intermediary_variables(self):
        return self._intermediary_variables

    def add_intermediary_variable(self, variable):
        self._intermediary_variables.append(variable)

    def order_inputs(self):
        def transform(p):
            if p.place_info.one_safe:
                if p.place_info.type.is_BlackToken:
                    return 1
                else: return 2
            elif p.is_Value:
                return 4
            elif p.is_Test:
                return 5
            else:
                return 6
        self.input_arcs.sort(key = transform)

    def shared_input_variables(self):
        variables = self.input_variables()
        shared = { name : occurences
                   for name, occurences in variables.iteritems()
                   if occurences > 1 }
        return shared

    def input_variables(self):
        variables = defaultdict(lambda : 0)
        for input_arc in self.input_arcs:
            for var, occurences in input_arc.variables().iteritems():
                variables[var] += occurences
        return variables

    def input_variable_by_name(self, name):
        for input_arc in self.input_arcs:
            if input_arc.is_Variable:
                if input_arc.variable.name == name:
                    return input_arc.variable
        return None

    def add_pre(self, place_info):
        """ Add a place to pre set.

        @param place_info: place to be added
        @type place_info: C{PlaceInfo}
        """
        self._pre.add(place_info)

    def add_post(self, place_info):
        """ Add a place to post set.

        @param place_info: place to be added
        @type place_info: C{PlaceInfo}
        """
        self._post.add(place_info)

    @property
    def pre(self):
        """ place pre set. """
        return self._pre

    @property
    def post(self):
        """ place post set. """
        return self._post

    def modified_places(self):
        """ Return places that are modified during transition firing, ie.,
        pre(t) and post(t) that are not test arcs.

        @return: modified places.
        @rtype: C{set}
        """
        mod = set([])
        for input_arc in self.input_arcs:
            if not input_arc.is_Test:
                mod.add(input_arc.place_info)

        for output in self.outputs:
            if not output.is_Test:
                mod.add(output.place_info)

        return mod


################################################################################

class PlaceInfo(object):
    instance = {}

    def __init__(self, place, one_safe = False, bound = None, process_name = None, flow_control = False):

        self._1safe = place.one_safe if hasattr(place, 'one_safe') else one_safe
        if not self._1safe:
            try:
                capacity = place.label('capacity') if hasattr(place, 'label') else None
            except KeyError: capacity = None

            if capacity:
                (_, high) = capacity
                if high == 1:
                    self._1safe = True

        self.snk_place = place
        self._name = place.name
        self.instance[self.name] = self
        self._type = TypeInfo.from_snakes_checker(place.checker())
        self.tokens = [ token for token in place.tokens ]

        # process name
        if hasattr(place, 'label'):
            path = place.label('path')
            self._process_name = path[0] if path != [] else None
        elif hasattr(place, 'process_name'):
            self._process_name = place.process_name
        else:
            self._process_name = process_name

        # flow control
        flow_status = (status.entry, status.internal, status.exit)
        if hasattr(place, 'status'):
            if (place.status in flow_status):
                self.flow_control = True
                self._1safe = True
            else:
                self.flow_control = False
        elif hasattr(place, 'flow_control'):
            self.flow_control = place.flow_control
        else:
            self.flow_control = flow_control

        if self._process_name == None:
            self._process_name = ""

        self._pre = set()
        self._post = set()

    def __getstate__(self):
        d = self.__dict__
        d['_post'] = set()
        d['_pre'] = set()
        d['snk_place'] = None
        return d

    def __setstate__(self, state):
        for key, value in state.iteritems():
            setattr(self, key, value)

    @property
    def is_generator_place(self):
        # \todo
        return self._name == 'sgen'

    @property
    def process_name(self):
        return self._process_name

    @property
    def name(self):
        return self._name

    @property
    def one_safe(self):
        return self._1safe

    @property
    def type(self):
        return self._type

    @classmethod
    def Dummy(cls, name, one_safe = False, process_name = None, flow_control = False):
        place = Place(name)
        return PlaceInfo(place, one_safe = one_safe, flow_control = flow_control, process_name = process_name)

    def __str__(self):
        """ human readable string
        """

        name_max = max(len(name) for name in PlaceInfo.instance)
        process_name_max = max(len(place.process_name) for place in PlaceInfo.instance.values())
        type_max = max(len(str(place.type)) for place in PlaceInfo.instance.values())

        if name_max == 0: name_max = 1
        if process_name_max == 0: process_name_max = 1
        if type_max == 0: type_max = 1

        return ("place: {name:{name_max}} - one_safe: {one_safe:1} - flow: {flow_control:1} - process: {process_name:{process_name_max}} - type: {type:{type_max}}"
                .format(name = self.name,
                        one_safe = self.one_safe,
                        flow_control = self.flow_control,
                        process_name = self._process_name,
                        type = str(self.type),
                        name_max = name_max,
                        process_name_max = process_name_max,
                        type_max = type_max))


    def add_pre(self, transition_info):
        """ Add transition to pre set.

        @param transition_info: transition to be added
        @type transition_info: C{TransitionInfo}
        """
        self._pre.add(transition_info)

    def add_post(self, transition_info):
        """ Add transition to post set.

        @param transition_info: transition to be added
        @type transition_info: C{TransitionInfo}
        """
        self._post.add(transition_info)

    @property
    def pre(self):
        """ place pre set. """
        return self._pre

    @property
    def post(self):
        """ place post set. """
        return self._post

################################################################################

class NetInfo(object):

    def __init__(self, net, config):
        # self.net = net

        self.declare = getattr(net, '_declare', [])
        self.places = []

        for p in net.place():
            self.places.append(PlaceInfo(p, one_safe=config.safe_net))

        self.transitions = []
        for t in net.transition():
            self.transitions.append(TransitionInfo(t))

#        for trans in self.transitions:
#            for input_arc in trans.input_arcs:
#                if input_arc.is_Flush:
#                    input_arc.place_info.update_type(TypeInfo.AnyType)
#            for output in trans.outputs:
#                if output.is_Flush:
#                    output.place_info.update_type(TypeInfo.AnyType)

        process_names = set()
        for p in net.node():
            process_name = None
            if hasattr(p, 'label') and p.label("path"):
                process_name = p.label("path")[0]
            elif hasattr(p, 'process_name'):
                process_name = p.process_name

            if process_name != None:
                process_names.add(process_name)
            
        self.process_info = []
        for process_name in process_names:
            self.process_info.append(ProcessInfo(name = process_name,
                                                 net_info = self))


    def place_by_name(self, name):
        for p in self.places:
            if p.name == name:
                return p
        raise LookupError("place of ID {} does not exist".format(name))

    def transition_by_name(self, name):
        for t in self.transitions:
            if t.name == name:
                return t
        raise LookupError("transition of ID {} does not exist".format(name))

class AtomInfo(object):
    """ Atomic proposition related informations.
    """

    __next_id__ = 0

    @classmethod
    def _new_id(cls):
        """ Produce new atom id.

        @return: a fresh atom id.
        @rtype: C{int}
        """
        new_id = cls.__next_id__
        cls.__next_id__ += 1
        return new_id

    def __init__(self, name, place_names, identifier = None):
        """ Create a new atom inforamtion carying object.

        @param name: name of the atom
        @param place_names: places used to compute the truth value of the atom.
        @type_info name: C{string}
        """
        self._name = name
        self._place_names = place_names
        self._id = self.__class__._new_id() if not identifier else identifier

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def place_names(self):
        return self._place_names

    def __str__(self):
        return '<atom: {name}({palces}) {id}>'.format(name = self.name,
                                                      places = ", ".join(self.place_names),
                                                      id = self.id)

    def __repr__(self):
        return 'AtomInfo({name!r}, {place_names!r}, {id})'.format(name = self.name,
                                                                 place_names = self.place_names,
                                                                 id = self.id)


class ProcessInfo(object):
    """ Class gathering information about ABCD processes.
    """

    def __init__(self, name, net_info):
        """ Build a new ProcessInfo structure.

        @param name: process name
        @type_info name: C{string}
        """
        self._name = name
        # retrieve places

        self._places = []
        self._flow_places = []
        self._local_places = []
        for place in net_info.places:
            if place.process_name == name:
                self._places.append(place)
                if place.flow_control:
                    self._flow_places.append(place)
                else:
                    self._local_places.append(place)

        self.transitions = []
        for transition in net_info.transitions:
            for arc in transition.input_arcs:
                place = arc.place_info
                if place.process_name == self.name:
                    self.transitions.append(transition)

    @property
    def name(self):
        """ process name property
        """
        return self._name

    @property
    def flow_places(self):
        """ process flow control places
        """
        return self._flow_places

    @property
    def local_places(self):
        """ process local places
        """
        return self._local_places

    def __str__(self):
        """
        """
        s = "".join(["process %s" % self.name,
                     "\n  flow places:\n      ",
                     "\n      ".join([ str(place) for place in self._flow_places ]),
                     "\n  local places:\n      ",
                     "\n      ".join([ str(place) for place in self._local_places ]),
                     "\n  all places:\n      ",
                     "\n      ".join([ str(place) for place in self._places ]),
                     "\n  transitions:\n      ",
                     "\n      ".join([ transition.name for transition in self.transitions ]),
                     "\nend process %s" % self.name ])
        return s

################################################################################
# VariableProvider
################################################################################

class VariableProvider(object):
    """ Simple class that produces new variable names.

    >>> v = VariableProvider()
    >>> v.new_variable().name
    '_v0'
    >>> v.new_variable().name
    '_v1'
    >>> v.new_variable().name
    '_v2'
    >>> ws = set(['_v1', 'a', 'b'])
    >>> v = VariableProvider(ws)
    >>> v.new_variable().name
    '_v0'
    >>> v.new_variable().name
    '_v2'
    >>> sorted(ws)
    ['_v0', '_v1', '_v2', 'a', 'b']

    """
    __slots__ = ('_wordset', '_next', '_variables')

    def __init__(self, wordset = None):
        """ Initialise provider.

        The provider will produce new names and ensures that they do
        not appear in \C{wordset}. The wordset will be updated when
        new variables appear.

        @param wordset: names to ignore.
        @type_info wordset: C{wordset}
        """
        self._wordset = wordset if wordset else set()
        self._next = 0

    def new_variable(self, variable_type = None, name = None):
        variable_name = self._new_name(name = name)
        variable_type = variable_type if variable_type else TypeInfo.AnyType
        return VariableInfo(variable_name, variable_type)

    def _new_name(self, name = None):
        """ Produce a new variable name.

        @return new variable name
        @rtype C{str}
        """
        if name:
            if not name in self._wordset:
                self._wordset.add(name)
                return name
            else:
                next_elt = self._next
                while True:
                    final_name = '{}_v{}'.format(name, next_elt)
                    next_elt += 1
                    if not final_name in self._wordset:
                        break
                self._next = next_elt
                self._wordset.add(final_name)
                print >> sys.stderr, "(W) cannot introduce a variable called {}, using {} instead.".format(name, final_name)
                return final_name

        next_elt = self._next
        while True:
            name = '_v{}'.format(next_elt)
            next_elt += 1
            if not name in self._wordset:
                break
        self._next = next_elt
        self._wordset.add(name)
        return name

################################################################################

class SharedVariableHelper(VariableProvider):
    """ Utility class that helps handling shared variables.
    """

    __slots__ = ('_shared', '_used', '_local_variables', '_unified', '_variables')

    def __init__(self, shared, wordset):
        """ Build a new helper from a set of shared variables
        and a word set.

        @param shared: shared variables with occurences.
        @type_info shared: C{dict} : VariableInfo -> int
        @param wordset: word set representing existing symbols.
        @type_info wordset: C{WordSet}
        """
        VariableProvider.__init__(self, wordset)
        self._shared = shared
        self._used = defaultdict(lambda : 0)
        self._local_variables = defaultdict(list)
        self._unified = defaultdict(lambda : False)

        self._variables = defaultdict(set)

    def mark_as_used(self, variable, local_variable):
        """ Mark a variable as used.

        The local variable is important since it will be used when performing
        an unification step.

        @param variable: variable.
        @type name: C{str}
        @param local_variable: local variable used for the variable.
        @type name: C{str}
        """
        self._used[variable.name] += 1
        self._local_variables[variable.name].append(local_variable)

    def all_used(self, variable):
        """ Check if all instances of a variable are used.

        @param variable: variable to check.
        @returns: C{True} if all variables were used, C{False} otherwise.
        @rtype: C{bool}
        """
        return self._used[variable.name] == self._shared[variable.name]

    def get_local_names(self, variable):
        """ Get all local names of a variable.

        @return: all local names of a variable.
        @rtype: C{list}
        """
        return [ var.name for var in self.get_local_variables(variable) ]

    def get_local_variables(self, variable):
        return self._local_variables[variable.name]


    def is_shared(self, variable):
        """ Check if a variable is shared.

        @return: True if the variable is shared, C{False} otherwise.
        @rtype: C{bool}
        """
        return variable.name in self._shared


    def new_variable_occurence(self, variable):
        if self.is_shared(variable):
            new_var = self.new_variable()
            self._variables[variable.name].add(variable)
            self._variables[variable.name].add(new_var)
            return new_var
        else:
            self._variables[variable.name] = [ variable ]
            return variable

    def new_variable(self, variable_type = None):
        new_var = VariableProvider.new_variable(self, variable_type)
        self._variables[new_var.name] = [ new_var ]
        return new_var

    def unified(self, variable):
        return self._unified[variable.name]

    def set_unified(self, variable):
        self._unified[variable.name] = True


################################################################################
# formula related info structures
################################################################################






################################################################################

if __name__ == '__main__':
    import doctest
    doctest.testmod()
#    from snakes.nets import *
#
#    net = PetriNet('Net')
#    s1 = Place('s1', [ dot ], tBlackToken)
#    s1.is_OneSafe = False
#
#    s2 = Place('s2', [ dot ], tBlackToken)
#    s2.is_OneSafe = False
#
#    net.add_place(s1)
#    net.add_place(s2)
#
#    transition = Transition('t', Expression('True'))
#    net.add_transition(transition)
#
#    net.add_input('s1', 't', Variable("x"))
#    net.add_output('s2', 't', Variable("x"))
#
#    info = NetInfo(net)
#
#    import pickle, StringIO
#    pickle.dump(info, StringIO.StringIO(), -1)


################################################################################
# EOF
################################################################################

