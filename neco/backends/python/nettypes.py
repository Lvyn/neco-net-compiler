""" Python basic net types. """

import ast
from neco.utils import Factory, should_not_be_called, todo
import neco.utils as utils
import neco.core.nettypes as coretypes
from neco.opt import onesafe
from astutils import Builder, E, A, to_ast, stmt
from neco.core.info import *

################################################################################

def type2str(type):
    """ Type to string translation.

    @param t: type to translate
    @type t: C{TypeInfo}
    """
    if type.is_UserType:
        if type.is_BlackToken:
            return "BlackToken"
        elif type.is_Bool:
            return "bool"
        elif type.is_Int:
            return "int"
        elif type.is_String:
            return "str"
        else:
            return str(type)
    elif type.is_TupleType:
        return "tuple"
    else:
        return "object"

TypeInfo.register_type("Multiset")

################################################################################

class PythonPlaceType(object):
    def place_expr(self, env, marking_name):
        return self.marking_type.gen_get_place(env,
                                               marking_name = marking_name,
                                               place_name = self.info.name,
                                               mutable = False)

################################################################################

class ObjectPlaceType(coretypes.ObjectPlaceType, PythonPlaceType):
    """ Python implementation of the fallback place type. """

    def __init__(self, place_info, marking_type):
        coretypes.ObjectPlaceType.__init__(self,
                                           place_info = place_info,
                                           marking_type = marking_type,
                                           type = TypeInfo.MultiSet,
                                           token_type = place_info.type)

    def gen_new_place(self, env):
        return E("multiset([])")

    def gen_get_size(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E('len').call([E(place_expr)])

    def gen_iterable(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_remove_token_function_call(self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return stmt( E(place_expr).attr("remove").call([compiled_token]) )

    def gen_add_token_function_call(self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return stmt( E(place_expr).attr("add").call([compiled_token]) )

    def gen_build_token(self, env, value):
        return E(repr(value))

    def gen_copy(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).attr("copy").call()

    def gen_clear_function_call(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt( E(place_expr).assign(E("multiset([])")) )

    def gen_not_empty_function_call(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_build_token(self, env, token):
        return E(repr(token))

    def add_multiset(self, env, multiset, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt( E(place_expr).attr('update').call([multiset]) )

    def add_items(self, env, multiset, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).attr('add_items').call([multiset])

################################################################################

class StaticMarkingType(coretypes.MarkingType):
    """ Python static marking type implementation, i.e., places as class attributes. . """

    def __init__(self):
        coretypes.MarkingType.__init__(self, "Marking")
        self.id_provider = utils.NameProvider()
        self._process_place_types = {}

    def gen_types(self, select_type):
        """
        """

        for place_info in self.flow_control_places:
            print "gen : ", place_info.name
            try:
                self._process_place_types[place_info.process_name].add_place(place_info)
            except KeyError:
                #new_id = self.id_provider.new(base = place_info.process_name)
                new_id = place_info.name
                place_type = FlowPlaceType(place_info = PlaceInfo.Dummy(new_id,
                                                                        process_name = place_info.process_name),
                                           marking_type = self)
                self.place_types[place_info.process_name] = place_type
                place_type.add_place(place_info)
                self._process_place_types[place_info.process_name] = place_type

        for place_info in self.one_safe_places:
            place_name = place_info.name
            place_type = placetype_factory.new( select_type(place_info),
                                                place_info,
                                                marking_type = self )

            if self.place_types.has_key(place_name):
                raise "place exists"
            else:
                self.place_types[place_name] = place_type

        for place_info in self.places:
            place_name = place_info.name
            place_type = placetype_factory.new( select_type(place_info),
                                                place_info,
                                                marking_type = self )

            if self.place_types.has_key(place_name):
                raise "place exists"
            else:
                self.place_types[place_name] = place_type

    def gen_alloc_marking_function_call(self, env, *args):
        return E("Marking()")

    def _gen_init(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = '__init__',
                                   args = A('self').param('alloc', default = 'True') )

        builder.begin_If( test = E('alloc') )
        for name, place_type in self.place_types.iteritems():
            builder.emit( E('self').attr( self.id_provider.get(name) ).assign( place_type.gen_new_place(env) ) )
        builder.end_If()

        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_copy(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = 'copy',
                                   args = A('self').param('alloc', default = 'True') )

        builder.emit( E('m = Marking(False)') )
        for name, place_type in self.place_types.iteritems():
            builder.emit( E('m').attr(self.id_provider.get(name)).assign(place_type.gen_copy(env, marking_name = 'self')) )
        builder.emit_Return(E('m'))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_eq(self, env):
        builder = Builder()
        other = 'other'
        builder.begin_FunctionDef( name = '__eq__', args = A("self").param(other) )

        return_str = "return ("
        for i, (name, place_type) in enumerate(self.place_types.iteritems()):
            id_name = self.id_provider.get(name)
            if i > 0:
                return_str += " and "
            return_str += "(self.%s == %s.%s)" % (id_name, other, id_name)
        return_str += ")"

        builder.emit( E(return_str) )
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_hash(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = '__hash__', args = A("self") )

        builder.emit( E('h = 0') )

        for name, place_type in self.place_types.iteritems():
            magic = hash(name)
            builder.emit( E('h ^= hash(self.' + self.id_provider.get(name) + ') ^ ' + str(magic)) )

        builder.emit_Return(E("h"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_free_marking_function_call(self, env, marking_name, *args):
        pass

    def _gen_repr(self, env):
        items = list(self.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = Builder()
        builder.begin_FunctionDef( name = "__repr__", args = A("self") )

        builder.emit( E('s = "hdict({"') )
        for (i, (place_name, place_type)) in enumerate(items):
            tmp = ',\n ' if i > 0 else ''
            builder.emit( E('s').add_assign( E(ast.Str(s = tmp + "'" + place_name + "' : ")).add(E('repr(self.' + self.id_provider.get(place_name) + ')'))) )
        builder.emit( E('s += "})"') )
        builder.emit_Return(E('s'))

        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_api(self, env):
        builder = Builder.ClassDef(name  = 'Marking',
                                   bases = [ E("object") ])
        builder.add_method(self._gen_init(env))
        builder.add_method(self._gen_repr(env))
        builder.add_method(self._gen_eq(env))
        builder.add_method(self._gen_hash(env))
        builder.add_method(self._gen_copy(env))
        return to_ast(builder)

    def gen_copy_marking_function_call(self, env, marking_name, *args):
        return E(marking_name).attr('copy').call()

    def gen_get_place(self, env, marking_name, place_name, mutable):
        return E(marking_name).attr(self.id_provider.get(place_name))

    def gen_remove_token_function_call(self, env, token, marking_name, place_name, *args):
        place_type = self.get_place_type_by_name(place_name)
        return place_type.gen_remove_token_function_call(env = env,
                                                         compiled_token = token,
                                                         marking_name = marking_name,
                                                         *args)

    def gen_add_token_function_call(self, env, token, marking_name, place_name, *args):
        place_type = self.get_place_type_by_name(place_name)
        return place_type.gen_add_token_function_call(env = env,
                                                      compiled_token = token,
                                                      marking_name = marking_name,
                                                      *args)

    def gen_iterable_place(self, env, marking_name, place_name):
        return self.get_place_type_by_name(place_name).gen_iterable(env, marking_name)

    def gen_build_token(self, env, place_name, value):
        place_type = self.get_place_type_by_name(place_name)
        return place_type.gen_build_token(env, value)

    ################################################################################
    # Flow elimination
    ################################################################################

    def gen_check_flow(self, env, marking_name, place_info, current_flow):
        place_type = self.get_place_type_by_name(place_info.process_name)
        assert( isinstance(place_type, FlowPlaceType) )
        return place_type.gen_check_flow(env = env,
                                         marking_name = marking_name,
                                         place_info = place_info,
                                         current_flow = current_flow)

    def gen_update_flow(self, env, marking_name, place_info):
        place_type = self.get_place_type_by_name(place_info.process_name)
        assert( isinstance(place_type, FlowPlaceType) )
        return place_type.gen_update_flow(env = env,
                                          marking_name = marking_name,
                                          place_info = place_info)

    def gen_read_flow(self, env, marking_name, process_name):
        return self._process_place_types[process_name].gen_read_flow(env, marking_name)

################################################################################

class MarkingSetType(coretypes.MarkingSetType):
    """ Python implementation of the marking set type. """

    def __init__(self, markingtype):
        coretypes.MarkingSetType.__init__(self, markingtype)

    def gen_api(self, env):
        pass

    def gen_new_marking_set(self, env):
        return E('set').call()

    def gen_add_marking_function_call(self, env, markingset_name, marking_name):
        return stmt(E(markingset_name).attr('add').call([E(marking_name)]))

################################################################################
# opt
################################################################################

class OneSafePlaceType(onesafe.OneSafePlaceType, PythonPlaceType):
    """ Python one safe place Type implementation
    """

    def __init__(self, place_info, marking_type):
        onesafe.OneSafePlaceType.__init__(self,
                                          place_info = place_info,
                                          marking_type = marking_type,
                                          type = TypeInfo.AnyType,
                                          token_type = TypeInfo.AnyType)

    def gen_new_place(self, env):
        return E("None")

    @property
    def token_type(self):
        return self.info.type

    @should_not_be_called
    def gen_iterable(self, env, marking_name): pass

    def gen_remove_token_function_call(self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign(E('None'))

    def gen_add_token_function_call(self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign(compiled_token)

    def gen_build_token(self, env, value):
        return E(repr(value))

    def gen_copy(self, env, marking_name):
        env.add_import('copy')
        place_expr = self.place_expr(env, marking_name)
        return E('copy.deepcopy').call([place_expr])

################################################################################

class BTPlaceType(onesafe.BTPlaceType, PythonPlaceType):
    """ Python black token place type implementation.

    @attention: Using this place type without the BTTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type):
        """
        @param place_info:
        @type place_info: C{}
        @param marking_type:
        @type marking_type: C{}
        """
        onesafe.BTPlaceType.__init__(self,
                                     place_info = place_info,
                                     marking_type = marking_type,
                                     type = TypeInfo.Int,
                                     token_type = TypeInfo.Int)

    def gen_new_place(self, env):
        return E('0')

    def gen_iterable(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E('xrange').call([E('0'), place_expr])

    def gen_remove_token_function_call( self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).sub_assign(E('1'))

    def gen_add_token_function_call(self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).add_assign(E('1'))

    def gen_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_build_token(self, env, value):
        return E('dot')

################################################################################

class BTOneSafePlaceType(onesafe.BTOneSafePlaceType, PythonPlaceType):
    """ Python one safe black token place type

    Using this place type without the BTOneSafeTokenEnumerator may introduce inconsistency.
    """
    def __init__(self, place_info, marking_type):
        onesafe.BTOneSafePlaceType.__init__(self,
                                            place_info = place_info,
                                            marking_type = marking_type,
                                            type = TypeInfo.Bool,
                                            token_type = TypeInfo.BlackToken)

    def gen_new_place(self, env):
        return E('True')

    @should_not_be_called
    def gen_iterable(self, env, marking_name): pass

    def gen_remove_token_function_call( self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign(E('True'))

    def gen_add_token_function_call(self, env, compiled_token, marking_name, *args):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign(E('False'))

    def gen_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_build_token(self, env, value):
        return E('dot')

################################################################################

class FlowPlaceType(coretypes.PlaceType, PythonPlaceType):
    """ Place type to represent flow control places a specific process.
    """

    def __init__(self, place_info, marking_type):
        """ Build a new place.

        @param place_info:
        @type place_info: C{}
        @param marking_type:
        @type marking_type: C{}
        """
        self._counter = 0
        self._places = {}
        coretypes.PlaceType.__init__(self,
                                     place_info = place_info,
                                     marking_type = marking_type,
                                     type = TypeInfo.Int,
                                     token_type = TypeInfo.Int)

    @property
    def token_type(self):
        """ Get python type of the stored token

        @returns: type
        @rtype: C{TypeInfo}
        """
        return TypeInfo.Int

    def gen_new_place(self, env):
        """ Produce a new empty place.

        @returns: empty place expression
        @rtype: C{Expr}
        """
        return E("0")

    @should_not_be_called
    def gen_iterable(self, env, marking_name): pass

    @should_not_be_called
    def gen_remove_token_function_call( self, *args, **kwargs): pass

    @should_not_be_called
    def gen_add_token_function_call(self, *args, **kwargs): pass

    def gen_copy(self, env, marking_name):
        """ produce an expression corresponding to a copy of the place.

        @param env: compiling environment
        @type env: C{Env}
        @param marking_name: name of the marking storing the place
        @type marking_name: C{str}
        """
        return self.place_expr(env, marking_name)

    def add_place(self, place_info):
        """ Adds a flow control place.

        @param place_info: flow control place to be added
        @type place_info: C{PlaceInfo}
        """
        assert(place_info.flow_control)
        assert(not self._places.has_key(place_info.name))
        self._places[place_info.name] = self._counter
        self._counter += 1


    def gen_check_flow(self, env, marking_name, place_info, current_flow):
        """ Get an ast representing the flow check.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        return E(current_flow).Eq(E(self._places[place_info.name]))

    def gen_update_flow(self, env, marking_name, place_info):
        """ Get an ast representing the flow update.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign(E(self._places[place_info.name]))

    def gen_read_flow(self, env, marking_name):
        return self.place_expr(env, marking_name)

################################################################################
# factories
################################################################################
import sys, inspect

__placetype_products = []
__markingtype_products = []
__markingsettype_products = []
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    if issubclass(obj, coretypes.PlaceType):
        __placetype_products.append(obj)
    elif issubclass(obj, coretypes.MarkingType):
        __markingtype_products.append(obj)
    elif issubclass(obj, coretypes.MarkingSetType):
        __markingsettype_products.append(obj)

placetype_factory = Factory(__placetype_products)
""" python place type factory """

markingtype_factory = Factory(__markingtype_products)
""" python marking type factory """

markingsettype_factory = Factory(__markingsettype_products)
""" python marking set type factory """


################################################################################
# EOF
################################################################################
