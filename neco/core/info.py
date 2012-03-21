""" Petri net info structures. """

import inspect
import types
# from snakes.nets import *
# import snakes.typing as typ
from neco.extsnakes import *
from collections import defaultdict
import snakes.plugins.status as status
from abc import *
from neco.utils import multidict, TypeMatch, Enum, RegDict
import neco.config as config

TypeKind = Enum('AnyType', 'TupleType', 'UserType')

class TypeInfo(object):
    """ Class representing and providing types.
    """

    def __init__(self, kind = TypeKind.AnyType, subtypes = [], type_name = ""):
        """ build a new type.

        @param kind: type kind
        @type kind: C{TypeKind}

        @param subtypes: (available if kind is TypeKind.TupleType) list of subtypes.
        @type subtypes: C{list<TypeInfo>}

        @param type_name: (available if kind is TypeKind.UserType) type name.
        @type type_name: C{str}
        """
        self._kind = kind

        if self.is_UserType:
            self._type_name = type_name
        elif self.is_TupleType:
            self._subtypes = subtypes

    @classmethod
    def UserType(cls, type_name):
        """ Helper class method for building user types.

        @param type_name: type name
        @type type_name: C{str}
        @return new user type.
        @rtype: C{TypeInfo}
        """
        return cls(kind=TypeKind.UserType, type_name = type_name)

    @classmethod
    def TupleType(cls, subtypes):
        """ Helper class method for building tuple types.

        @param subtypes: list of subtypes.
        @type subtypes: C{list<typeinfo>}
        @return: new tuple type
        @rtype: C{TypeInfo}
        """
        return cls(kind=TypeKind.TupleType, subtypes = subtypes)

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
                    .format(kind=repr(self._kind), type_name=repr(self._type_name)))
        else:
            return "TypeInfo(kind={kind})".format(kind=repr(self._kind))

    def __str__(self):
        """ Human readable string representation.

        @return: Human readable string.
        @rtype: C{str}
        """
        if self.is_UserType:
            return str(self._type_name)
        elif self.is_TupleType:
            return "(%s)" % ", ".join( [ str(e) for e in self._subtypes ] )
        elif self.is_AnyType:
            return 'AnyType'

    def split(self):
        """ Get subtypes.

        @return: list of subtypes (empty if is not a TupleType).
        @rtype: C{list<TypeInfo>}
        """
        return (self._subtypes if self.is_TupleType else [])

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
            return TypeInfo.TupleType( [ TypeInfo.from_snakes_checker( t ) for t in checker._types ] )
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
                return TypeInfo.TupleType( [ TypeInfo.from_raw( elt ) for elt in raw ] )

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

        @param other: right operand
        @type other: C{TypeInfo}
        @return: C{True} if equal, C{False} otherwise.
        @rtype: C{bool}
        """
        if self._kind == other._kind:
            if self.is_TupleType:
                return self._subtypes == other._subtypes
            else:
                return self._type_name == other._type_name
        else:
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
        assert( self.is_UserType )
        return self._type_name

TypeInfo.AnyType = TypeInfo(kind=TypeKind.AnyType)
TypeInfo.register_type('Int')
TypeInfo.register_type('Bool')
TypeInfo.register_type('String')
TypeInfo.register_type('BlackToken')

TypeInfo.register_type('Pid')

################################################################################

TokenKind = Enum("Variable", "Value", "Expression", "Tuple")
class TokenInfo(object):
    """
    """

    __metaclass__ = ABCMeta

    def __init__(self, raw_token, kind = None, type = None):
        """
        """
        self._raw = raw_token
        self._data = RegDict()

        if kind is not None:
            assert kind in TokenKind
            self._kind = kind

        if type != None:
            assert isinstance(type, TypeInfo)
            self._type = type
        else:
            self._type = TypeInfo.from_raw(raw_token)

    @property
    def data(self):
        """ Get the data dict. """
        return self._data

    def __repr__(self):
        return "TokenInfo(raw_token=%s, kind=%s, type=%s)" % (repr(self._raw), repr(self._kind), repr(self._type))

    def update_type(self, type):
        assert(isinstance(type, TypeInfo))
        self._type = type

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
        type = TypeInfo.from_raw(raw_token)
        if type.is_TupleType:
            return TupleInfo( [ cls.from_raw(c) for c in raw_token ] , type = type )
        else:
            return ValueInfo(raw_token, type = type)

    @classmethod
    def from_snakes(cls, snk_obj):
        class matcher(TypeMatch):
            def match_Value(_, v):
                return cls.from_raw(v.value)

            def match_Variable(_, v):
                if v.name == "dot":
                    return ValueInfo( dot, type = TypeInfo.BlackTokenType )
                return VariableInfo(v.name)

            def match_Expression(_, e):
                return ExpressionInfo(e._str)

            def match_Tuple(_, t):
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

    def __init__(self, value_data, *args, **kwargs):
        """ builds a new Value from raw data

        @param value_data: data
        @type value_data: C{object}
        """
        TokenInfo.__init__(self, value_data, *args, kind = TokenKind.Value, **kwargs)

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
    def __init__(self, name, type = None):
        TokenInfo.__init__(self,
                           object(), # dummy value
                           kind = TokenKind.Variable,
                           type = type)
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
        return defaultdict(lambda : 0) # To do

    def base_names(self):
        return (self.name, self.local_name)

    def __repr__(self):
        return "ExpressionInfo(s=%s)" % repr(self.raw)

    def __str__(self):
        return "Expression(%s)" % str(self.raw)

################################################################################

class TupleInfo(TokenInfo):
    def __init__(self, components = [], *args, **kwargs):
        TokenInfo.__init__(self, components, *args, kind = TokenKind.Tuple, **kwargs)
        self.components = components

    def variables(self):
        vardict = defaultdict(lambda : 0)
        for c in self.components:
            for name, occurences in c.variables().iteritems():
                vardict[name] += occurences
        return vardict

    def __repr__(self):
        return "TupleInfo(components=%s)" % repr( [ c for c in self.components ] )

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
        return netir.Tuple( components = [ build_tuple(component) for component in info.components ])

    elif info.is_variable():
        return netir.Name( info.name )

    elif info.is_value():
        return netir.PyExpr( info.value )

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

        class matcher(TypeMatch):
            # variables
            def match_Variable(_, arc_annotation):
                # to do, infer type from inputs
                if arc_annotation.name == "dot":
                    self.value = ValueInfo( dot, type = TypeInfo.BlackToken )
                    self.kind = ArcKind.Value
                    # no variables
                else:
                    self.variable = VariableInfo( name = arc_annotation.name )
                    if self.is_input:
                        self.variable.update_type( self.place_info.type )
                    self.kind = ArcKind.Variable
                    self._vars[arc_annotation.name] += 1

            # values
            def match_Value(_, arc_annotation):
                self.value = ValueInfo( arc_annotation.value )
                self.kind = ArcKind.Value
                self._vars = {}

            # tests
            def match_Test(_, arc_annotation):
                self.annotation = arc_annotation._annotation
                self.kind = ArcKind.Test
                inner = TokenInfo.from_snakes( self.annotation )
                self.inner = inner

                if inner.is_Value:
                    self.value = inner
                elif inner.is_Variable:
                    self.variable = inner
                elif inner.is_Tuple:
                    self.tuple = inner
                else:
                    raise NotImplementedError, inner

                if self.is_input and self.inner.is_Variable:
                    self.inner.update_type(self.place_info.type)
                self._vars = self.inner.variables()

            # flush
            def match_Flush(_, arc_annotation):
                self.annotation = arc_annotation._annotation
                self.kind = ArcKind.Flush
                self.inner = TokenInfo.from_snakes(self.annotation)
                self._vars = self.inner.variables()

            # expression
            def match_Expression(_, arc_annotation):
                self.kind = ArcKind.Expression
                self.expr = TokenInfo.from_snakes( arc_annotation )
                self._vars = self.expr.variables() # may be bad if input

            # tuple
            def match_Tuple(_, arc_annotation):
                self.kind = ArcKind.Tuple
                self.tuple = TokenInfo.from_snakes( arc_annotation )
                if self.is_input:
                    self.tuple.update_type( self.place_info.type )
                self._vars = self.tuple.variables()

            # multiarc
            def match_MultiArc(_, arc_annotation):
                self.kind = ArcKind.MultiArc
                self.sub_arcs = [ ArcInfo( place_info, annotation, is_input )
                                  for annotation in arc_annotation._components ]

                vardict = self._vars
                for arc in self.sub_arcs:
                    for name, occurences in arc.variables().iteritems():
                        vardict[name] += occurences
            def match_GeneratorMultiArc(_, arc_annotation):
                self.kind = ArcKind.GeneratorMultiArc
                self.sub_arcs = [ ArcInfo( place_info, annotation, is_input )
                                  for annotation in arc_annotation.components ]
                self.pid = VariableInfo(name = arc_annotation.pid.name, type = TypeInfo.Pid)
                self.counter  = VariableInfo(name = arc_annotation.counter.name, type = TypeInfo.Int)
                self.new_pids = [ VariableInfo(name = pid.name, type = TypeInfo.Pid) for pid in arc_annotation.new_pids ]

            def default(_, arc_annotation):
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
                #TO DO tuple
                return []
        else:
            # TO DO tuple
            return []

    def type_vars(self, vars):
        """

        @param vars:
        @type vars: C{}
        """
        if self.is_Variable:
            name = self.variable.name
            other = None
            for v in vars:
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

        inputs = []
        for place, arc_annotation in trans.input():
            place_info = PlaceInfo.instance[place.name]
            place_info.add_post(self)
            self.add_pre(place_info)
            input = ArcInfo( place_info, arc_annotation, is_input = True)
            inputs.append( input )
            self._process_name = place_info.process_name

        self.inputs = inputs

        outputs = []
        for place, arc_annotation in trans.output():
            place_info = PlaceInfo.instance[place.name]
            place_info.add_pre(self)
            self.add_post(place_info)
            output = ArcInfo( place_info, arc_annotation, is_input = False)
            outputs.append( output )
            if output.is_GeneratorMultiArc:
                self.generator_arc = output

        self.outputs = outputs

        vardict = defaultdict(lambda : 0)
        for var in trans.vars():
            vardict[var] = 1

        for input in self.inputs:
            for name, occurences in input.variables().iteritems():
                vardict[name] += occurences

        self._vars = vardict

        input_vars = []
        for input in self.inputs:
            input_vars.extend(input.variables_info)

        for output in self.outputs:
            output.type_vars(input_vars)

    @property
    def process_name(self):
        return self._process_name

    def variables(self):
        return self._vars

    @property
    def input_multi_places(self):
        for input in self.inputs:
            info = input.place_info
            if input.is_MultiArc:
                yield info

    def variable_informations(self):
        """
        """
        l = []
        l.append("********************************************************************************")
        l.append("transition %s" % self.name)
        l.append("********************************************************************************")

        for input in self.inputs:
            l.append(str(input))

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
        self.inputs.sort(key = transform )

    def shared_input_variables(self):
        variables = self.input_variables()
        shared = { name : occurences
                   for name, occurences in variables.iteritems()
                   if occurences > 1 }
        return shared

    def input_variables(self):
        variables = defaultdict(lambda : 0)
        for input in self.inputs:
            for var, occurences in input.variables().iteritems():
                variables[var] += occurences
        return variables

    def input_variable_by_name(self, name):
        for input in self.inputs:
            if input.is_Variable:
                if input.variable.name == name:
                    return input.variable
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
        for input in self.inputs:
            if not input.is_Test:
                mod.add(input.place_info)

        for output in self.outputs:
            if not output.is_Test:
                mod.add(output.place_info)

        return mod


################################################################################

class PlaceInfo(object):
    instance = {}

    def __init__(self, place, one_safe=False, bound=None, process_name=None, flow_control=False):

        self._1safe = place.one_safe if hasattr(place, 'one_safe') else one_safe
        if not self._1safe:
            try:
                capacity = place.label('capacity') if hasattr(place, 'label') else None
            except KeyError as e: capacity = None

            if capacity:
                (low, high) = capacity
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
            self.flow_control= place.flow_control
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

    def update_type(self, type):
        assert(isinstance(type, TypeInfo))
        self._type = type

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
        return PlaceInfo(place, one_safe=one_safe, flow_control=flow_control, process_name=process_name)

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

    def __init__(self, net):
        self.net = net

        self.places = []
        for p in net.place():
            self.places.append( PlaceInfo(p) )

        self.transitions = []
        for t in net.transition():
            self.transitions.append( TransitionInfo(t) )

        for trans in self.transitions:
            for input in trans.inputs:
                if input.is_Flush:
                    input.place_info.update_type(TypeInfo.AnyType)
            for output in trans.outputs:
                if output.is_Flush:
                    output.place_info.update_type(TypeInfo.AnyType)

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
        assert False, 'place not found'


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

    def __init__(self, name, place_names, id=None):
        """ Create a new atom inforamtion carying object.

        @param name: name of the atom
        @param place_names: places used to compute the truth value of the atom.
        @type name: C{str}
        """
        self._name = name
        self._place_names = place_names
        self._id = self.__class__._new_id() if not id else id

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
        return '<atom: {name}({palces}) {id}>'.format(name=self.name,
                                                      places=", ".join(self.place_names),
                                                      id=self.id)

    def __repr__(self):
        return 'AtomInfo({name!r}, {place_names!r}, {id})'.format(name=self.name,
                                                                 place_names=self.place_names,
                                                                 id=self.id)


class ProcessInfo(object):
    """ Class gathering information about ABCD processes.
    """

    def __init__(self, name, net_info):
        """ Build a new ProcessInfo structure.

        @param name: process name
        @type name: C{str}
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
            for arc in transition.inputs:
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
        @type wordset: C{wordset}
        """
        self._wordset = wordset if wordset else set()
        self._next = 0

    def new_variable(self, type = None, name = None):
        var_name = self._new_name(name=name)
        var_type = type if type else TypeInfo.AnyType
        return VariableInfo(var_name, var_type)

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
                next = self._next
                while True:
                    final_name = '{}_v{}'.format(name, next)
                    next += 1
                    if not final_name in self._wordset:
                        break
                self._next = next
                self._wordset.add(final_name)
                print >> sys.stderr, "(W) cannot introduce a variable called {}, using {} instead.".format(name, final_name)
                return final_name

        next = self._next
        while True:
            name = '_v{}'.format(next)
            next += 1
            if not name in self._wordset:
                break
        self._next = next
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
        @type shared: C{dict} : VariableInfo -> int
        @param wordset: word set representing existing symbols.
        @type wordset: C{WordSet}
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

    def new_variable(self, type = None):
        new_var = VariableProvider.new_variable(self, type)
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


################################################################################
# EOF
################################################################################

