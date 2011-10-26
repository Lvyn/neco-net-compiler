""" Cython basic net types. """

import math
import neco.utils as utils
from neco.utils import Factory, should_not_be_called, todo
import neco.core.nettypes as coretypes
from neco.core.nettypes import provides_by_index_access, provides_by_index_deletion
from neco.core.info import *
from neco.core import onesafe
import cyast
from cyast import *
from maskbitfield import MaskBitfield

################################################################################
# Registered classes are used as cython classes (cdef)
################################################################################

def from_neco_lib(f):
    return "ctypes_ext.%s" % f

__registered_cython_types = dict()

def register_cython_type(typeinfo, id):
    """ Register a type as a cython type.

    The provided value provided to C{id} argument will be used as type name
    in produced code.

    @param typeinfo: type to be registered.
    @type typeinfo: C{neco.core.TypeInfo}
    @param id: name used as type name.
    @type id: C{str}
    """
    __registered_cython_types[typeinfo] = id

def is_cython_type(typeinfo):
    """ Check if a type is registered.

    @param typeinfo: type to be checked.
    @type typeinfo: C{neco.core.TypeInfo}
    @return: C{True} if registered, C{False} otherwise.
    @rtype bool
    """
    if __registered_cython_types.has_key(typeinfo):
        return True
    return False

################################################################################

def type2str(type):
    """ translates a type info to a string

    @param type: type info to translate
    @type type: C{TypeInfo}
    """
    if type.is_UserType:
        if is_cython_type(type):
            return __registered_cython_types[type]
        else:
            return 'object'
    elif type.is_TupleType:
        return 'tuple'
    else:
        return 'object'

################################################################################

# new types

TypeInfo.register_type("MultiSet")
TypeInfo.register_type("IntPlace")
TypeInfo.register_type("Char")
TypeInfo.register_type("Short")
TypeInfo.register_type("UnsignedInt")
TypeInfo.register_type("UnsignedChar")

# register types

register_cython_type(TypeInfo.Bool, 'bool')
register_cython_type(TypeInfo.Char, 'char')
register_cython_type(TypeInfo.Int, 'int')
register_cython_type(TypeInfo.Short, 'short')
register_cython_type(TypeInfo.IntPlace, from_neco_lib('int_place_type_t*'))
register_cython_type(TypeInfo.MultiSet, 'MultiSet')
register_cython_type(TypeInfo.UnsignedChar, 'unsigned char')
register_cython_type(TypeInfo.UnsignedInt, 'unsigned int')

################################################################################

class CythonPlaceType(object):
    """ Base class for cython place types. """

    _packed_place_ = False
    _revelant_ = True # should be dumped
    _helper_ = False
    _checking_need_helper_ = True

    def place_expr(self, env, marking_name):
        """ Get an ast builder corresponding to place access.

        @param env: compiling environment.
        @type env: C{neco.backends.cython.utils.Env}
        @param marking_name: marking structure name.
        @type marking_name: C{str}
        @return: an ast builder.
        @rtype: C{neco.backends.cython.astutils.Builder._cyast_builder}
        """
        return env.marking_type.gen_get_place(env = env,
                                              marking_name = marking_name,
                                              place_name = self.info.name)

    @property
    def is_packed(self):
        """ C{True} if place is packed, C{False} otherwise """
        return self.__class__._packed_place_

    @property
    def is_revelant(self):
        """ C{True} if place should be used in dump, C{False} otherwise """
        return getattr(self, 'revelant', self.__class__._revelant_)

    @property
    def is_helper(self):
        """ C{True} if place is a helper, C{False} otherwise """
        return self.__class__._helper_

    @property
    def checking_need_helper(self):
        return self._checking_need_helper_

################################################################################

def packed_place(cls):
    """ Decorator for packed places.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_packed
    False

    >>> @packed_place
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_packed
    True


    """
    cls._packed_place_ = True
    return cls

def helper_place_type(cls):
    """ Decorator for packed places.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_helper
    False

    >>> @helper_place_type
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_helper
    True


    """
    cls._helper_ = True
    return cls

def not_revelant(cls):
    """ Decorator for revelant place types.

    A non revelant place will not be used in a dump.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    True

    >>> @not_revelant
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    False


    """
    cls._revelant_ = False
    return cls

def checking_without_helper(cls):
    """ Decorator for place types that do not need a helper to support checking.

    A non revelant place will not be used in a dump.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    True

    >>> @not_revelant
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    False


    """
    cls._checking_need_helper_ = False
    return cls

################################################################################

@checking_without_helper
class ObjectPlaceType(coretypes.ObjectPlaceType, CythonPlaceType):
    """ Python implementation of fallback place type. """

    def __init__(self, place_info, marking_type):
        coretypes.ObjectPlaceType.__init__(self,
                                           place_info = place_info,
                                           marking_type = marking_type,
                                           type = TypeInfo.MultiSet,
                                           token_type = place_info.type)

    def new_place_expr(self, env):
        return cyast.Call(func=cyast.Name(id="MultiSet"))

    def delete_stmt(self, env, marking_name):
        return []

    def hash_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=cyast.Attribute(value=place_expr,
                                               attr="hash")
                          )

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left, ops=[cyast.Eq()], comparators=[right])

    def iterable_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def remove_token_stmt(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='remove'),
                               args=[ compiled_token ])
                    )

    def add_token_stmt(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='add'),
                               args=[ compiled_token ])
                    )
    def copy_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=cyast.Attribute(value=place_expr,
                                               attr="copy")
                          )

    def light_copy_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def clear_stmt(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Assign(targets=[place_expr],
                            value=cyast.Call(func=cyast.Name("MultiSet")))

    def not_empty_expr(self, env, marking_type, marking_name):
        return self.place_expr(env, marking_name)

    def token_expr(self, env, token):
        return E(repr(token))

    def add_multiset_expr(self, env, multiset, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='update'),
                               args=[ multiset ])
                    )

    def dump_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=cyast.Name("dump"),
                          args=[place_expr])

    def add_items_stmt(self, env, multiset, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='add_items'),
                               args=[multiset])
                    )

    def compare_expr(self, env, left_marking_name, right_marking_name):
        left  = self.place_expr(env, left_marking_name)
        right = self.place_expr(env, right_marking_name)
        return cyast.Call(func=cyast.Attribute(value=left,
                                               attr='compare'),
                          args=[right])

    def not_empty_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

@provides_by_index_access
@provides_by_index_deletion
class IntPlaceType(coretypes.PlaceType, CythonPlaceType):
    """ Place type for small unbounded 'int' places. """

    def __init__(self, place_info, marking_type):
        assert( place_info.type == TypeInfo.Int )
        coretypes.PlaceType.__init__(self,
                                     place_info = place_info,
                                     marking_type = marking_type,
                                     type = TypeInfo.IntPlace,
                                     token_type = place_info.type)

    def new_place_expr(self, env):
        return E(from_neco_lib("int_place_type_new()"))

    def delete_stmt(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_free")),
                               args=[ place_expr ])
                    )

    def hash_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_hash")),
                          args=[ place_expr ])

    def eq_expr(self, env, left, right):
        return cyast.Call(func=E(from_neco_lib("int_place_type_eq")),
                          args=[ left, right ])

    @should_not_be_called
    def iterable_expr(self, env, marking_type, marking_name): pass

    def remove_token_stmt(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_rem_by_value")),
                               args=[ place_expr, compiled_token ])
                    )

    def remove_by_index_stmt(self, env, index, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_rem_by_index")),
                               args=[ place_expr, E(index) ])
                    )

    def add_token_stmt(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_add")),
                               args=[ place_expr, compiled_token ])
                    )

    def copy_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_copy")),
                          args=[ place_expr ])

    def light_copy_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_light_copy")),
                          args=[ place_expr ])

    def get_size_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_size")),
                          args=[ place_expr ])

    def get_token_expr(self, env, marking_name, index):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_get")),
                          args=[ place_expr, E(index) ])

    def clear_stmt(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_clear")),
                          args=[ place_expr ])

    def token_expr(self, env, token):
        return E(repr(token))

    def dump_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_cstr")),
                          args=[ place_expr ])

    def compare_expr(self, env, left_marking_name, right_marking_name):
        left  = self.place_expr(env, left_marking_name)
        right = self.place_expr(env, right_marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_cmp")),
                          args=[ left, right ])

    def not_empty_expr(self, env,marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E(from_neco_lib("int_place_type_not_empty")),
                          args=[place_expr])

    @todo
    def not_empty_expr(self, env, marking_type, marking_name): pass

    @todo
    def add_multiset_expr(self, env, multiset, marking_type, marking_name): pass

    @todo
    def add_items_stmt(self, env, multiset, marking_type, marking_name): pass


################################################################################


def place_type_from_info(place_info, marking):
    type = place_info.type
    if type.is_Int:
        return IntPlaceType(place_info, marking_type=marking)
    elif type.is_Bool:
        print >> sys.stderr, "TODO add BoolPlaceType to ctypes, fallback ObjectPlaceType for place {}".format(place_info.name)
        return ObjectPlaceType(place_info, marking_type=marking)
    elif type.is_String:
        print >> sys.stderr, "TODO add StringPlaceType to ctypes, fallback: ObjectPlaceType for place {}".format(place_info.name)
        return ObjectPlaceType(place_info, marking_type=marking)
    elif type.is_BlackToken:
        return BTPlaceType(place_info, marking_type=marking)
    elif type.is_UserType:
        print >> sys.stderr, "TODO allow users to provide their own multiset structures, fallback: ObjectPlaceType for place {}".format(place_info.name)
        return ObjectPlaceType(place_info, marking_type=marking)
    else:
        return ObjectPlaceType(place_info, marking_type=marking)


class StaticMarkingType(coretypes.MarkingType):
    """ Python static marking type implementation, i.e., places as class attributes. . """

    def __init__(self):
        coretypes.MarkingType.__init__(self,
                                       TypeInfo.register_type("Marking"),
                                       TypeInfo.register_type("MarkingSet"))

        # id provider for class attributes
        self.id_provider = utils.NameProvider() # used to produce attribute names
        self._process_place_types = {}

        if config.get('optimise'):
            self.packing_enabled = True
        else:
            self.packing_enabled = False

        # register this marking type as a cython
        # class, will be used instead of object
        register_cython_type(self.type, "Marking")

        # pack 1SBT places ?
        if self.packing_enabled:
            name = self.id_provider.new(base = "_packed")
            pack = PackedPlaceTypes(name, self)
            self.id_provider.set(pack, name)
            pack = pack
        else:
            pack = None
        self._pack = pack


    def get_process_place_type(self, process_name):
        return self._process_place_types[process_name]

    def __gen_one_safe_place_type(self, place_info):
        if place_info.type.is_BlackToken:
            # register a new place type
            pt = PackedBT1SPlaceType( place_info, self, pack = self._pack )
            self._pack.add_place( place_info, bits = 1 )
            self.place_types[place_info.name] = pt
        else: # 1s not BT
            new_id = self.id_provider.new('one_safe_')
            dummy = PlaceInfo.Dummy( new_id, one_safe = True )
            self.id_provider.set(dummy, new_id)

            pt = PackedBT1SPlaceType( dummy, self, pack = self._pack )
            pt.revelant = False
            self._pack.add_place( dummy, bits = 1 )
            # remember place type
            self.place_types[new_id] = pt

            # create the place
            place_type = OneSafePlaceType(place_info, self, pt)
            # remember place type
            self.place_types[place_info.name] = place_type


    def __gen_flow_control_place_type(self, place_info):
        process_name = place_info.process_name
        try:
            flow_place_type = self._process_place_types[process_name] # throws KeyError
        except KeyError:
            # flow place type does not exist: create new place type
            new_id = self.id_provider.new(base = 'flow_')
            dummy = PlaceInfo.Dummy(new_id,
                                    flow_control = True,
                                    process_name = place_info.process_name)
            self.id_provider.set(dummy, new_id)

            flow_place_type = FlowPlaceType(dummy, self)
            self.place_types[new_id] = flow_place_type
            self._process_place_types[process_name] = flow_place_type

            # add all flow control places to flow place and create helpers
            # this is needed to allocate place in self._pack
            flow_place_type.add_helper(place_info)
            for info in self.flow_control_places:
                if info.process_name == process_name:
                   flow_place_type.add_helper(info)
            # get size to allocate
            needed_bits = flow_place_type.needed_bits

            # pack flow place
            self._pack.add_place(dummy, bits = needed_bits)
            flow_place_type.pack = self._pack

        # flow_place_type and helpers exist
        self.place_types[place_info.name] = flow_place_type.get_helper(place_info)


        # place_name = place_info.name
        # place_type = placetype_factory.new(select_type(place_info),
        #                                    place_info,
        #                                    marking_type = self)
        # if self.place_types.has_key(place_name):
        #     raise "place exists"
        # else:
        #     self.place_types[place_name] = place_type

    def gen_types(self):
        if self.packing_enabled:
            for place_info in self.flow_control_places:
                self.__gen_flow_control_place_type(place_info)
            for place_info in self.one_safe_places:
                self.__gen_one_safe_place_type(place_info)

        else:
            for place_info in self.flow_control_places:
                self.place_types[place_info.name] = place_type_from_info(place_info, self)
            for place_info in self.one_safe_places:
                self.place_types[place_info.name] = place_type_from_info(place_info, self)

        for place_info in self.places:
            self.place_types[place_info.name] = place_type_from_info(place_info, self)
        
        # for place_info in self.flow_control_places:
        #     if self.packing_enabled:
        #         self.__gen_flow_control_place_type(place_info)
        #     else:
        #         self.__gen_place_type(place_info, select_type)

        # for place_info in self.one_safe_places:
        #     if self.packing_enabled and place_info.one_safe:
        #         self.__gen_one_safe_place_type(place_info)
        #     else:
        #         self.__gen_place_type(place_info, select_type)

        # for place_info in self.places:
        #     self.__gen_place_type(place_info, select_type)

    def __str__(self):
        """ Dump the marking structure. """
        l = ["MARKING DUMP BEGIN\n"]
        for place_name, place_type in self.place_types.items():
            l.append(place_name)
            l.append(" \t")
            l.append(str(place_type.info.type))
            l.append(" \tonesafe") if place_type.info.one_safe else l.append("")
            l.append("\n")
        l.append("MARKING DUMP END\n")
        return "".join(l)

    def new_marking_expr(self, env):
        return cyast.Call(func=cyast.Name(type2str(self.type)),
                          args=[cyast.Name('alloc')],
                          keywords=[cyast.Name('True')])

    def gen_dealloc_method(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = "__dealloc__",
                                   args = A("self", type="Marking") )

        for place_type in self.place_types.itervalues():
            if place_type.is_packed or place_type.is_helper:
                pass
            else:
                builder.emit(place_type.delete_stmt(env = env,
                                                   marking_name = "self"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_init_method(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = "__cinit__",
                                   args = A("self").param("alloc", default = "False"))

        builder.begin_If( cyast.Name('alloc') )

        if self._pack:
            builder.emit( self._pack.gen_initialise(env, "self") )

        # init places
        for place_type in self.place_types.itervalues():
            if place_type.is_packed or place_type.is_helper:
                pass
            else:
                attr = self.id_provider.get(place_type)
                builder.emit(cyast.Assign(targets=[cyast.Attribute(cyast.Name('self'),
                                                                   attr=attr)],
                                          value=place_type.new_place_expr(env) )
                             )
        builder.end_If()
        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_copy_method(self, env):
        builder = Builder()
        builder.begin_FunctionCDef( name = "copy",
                                    args = A("self"),
                                    returns = E(type2str( self.type )),
                                    decl = [ Builder.CVar( name = 'm', type = 'Marking' ) ])



        builder.emit( E('m = Marking()') )

        # copy packs
        if self._pack:
            builder.emit( self._pack.copy_expr(env, src_marking_name = "self", dst_marking_name = "m") )

        # copy places
        for place_type in self.place_types.itervalues():
            if place_type.is_packed or place_type.is_helper:
                pass
            else:
                builder.emit(cyast.Assign(targets=[E('m.{place}'.format(place=self.id_provider.get(place_type)))],
                                          value=place_type.copy_expr(env=env, marking_name='self'))
                             )
        builder.emit_Return(E("m"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_compare_aux(self, builder, tests):
        try:
            test = tests.pop()
            # l - r == 0 ?:
            builder.emit(cyast.Assign(targets=[cyast.Name("tmp")],
                                      value=test))
            builder.begin_If(cyast.Compare(left=cyast.Name("tmp"),
                                           ops=[cyast.Lt()],
                                           comparators=[cyast.Num(0)])
                             )
            builder.emit_Return(cyast.Num(-1))
            # l - r < 0 ?:
            builder.begin_Elif(cyast.Compare(left=cyast.Name("tmp"),
                                             ops=[cyast.Gt()],
                                             comparators=[cyast.Num(0)])
                               )
            builder.emit_Return(cyast.Num(1))
            builder.end_If()
            builder.end_If()

            self._gen_C_compare_aux(builder, tests)

        except IndexError:
            builder.emit_Return(cyast.Num(0))

    def _gen_C_compare(self, env):

        builder = Builder()
        left_marking_name  = "self"
        right_marking_name = "other"
        builder.begin_FunctionCDef( name = "neco_marking_compare",
                                    args = (A("self", type = type2str(self.type))
                                            .param(right_marking_name, type = type2str(self.type))),
                                    returns = E("int"),
                                    public=True, api=True,
                                    decl = [ Builder.CVar( name = 'tmp', type = type2str(TypeInfo.Int)) ] )

        # TODO: Order places

        i = 0
        tests = []
        if self._pack:
            if self.packing_enabled:
                gen = self._pack.gen_tests(left_marking_name=left_marking_name,
                                           right_marking_name=right_marking_name)
                for l, r in gen:
                    tests.append(cyast.BinOp(left=l,
                                             op=cyast.Sub(),
                                             right=r))

        for place_type in self.place_types.itervalues():
            if place_type.is_packed or place_type.is_helper:
                continue
            else:
                id = self.id_provider.get(place_type)
                tests.append(place_type.compare_expr(env,
                                                    left_marking_name='self',
                                                    right_marking_name='other')
                             )

        tests.reverse()
        self._gen_C_compare_aux(builder, tests)
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_marked_aux(self, builder, tests, rs):
        try:
            test = tests.pop()
            r = rs.pop()
            # l - r == 0 ?:
            builder.begin_If(test)
            builder.emit_Return(r)
            # else l - r > 0:
            builder.begin_Else()
            self._gen_C_marked_aux(builder, tests, rs)
            builder.end_If()
        except IndexError:
            builder.emit_Return(cyast.Num(0))

    def _gen_C_marked(self, env):

        builder = Builder()
        left_marking_name  = 'self'
        right_marking_name = 'other'
        builder.begin_FunctionCDef( name = 'neco_marked',
                                    args = (A('self', type = self.type_name)
                                            .param('place_name', type='object')),
                                    returns = cyast.Name('int'),
                                    public=True, api=True)

        i = 0
        tests = []
        rs = []
        for name, place_type in self.place_types.iteritems():
            id = self.id_provider.get(place_type)
            tests.append(cyast.Compare(left=E(repr(name)),
                                       ops=[cyast.Eq()],
                                       comparators=[cyast.Name('place_name')])
                         )
            rs.append( place_type.not_empty_expr(env, 'self') )

        self._gen_C_marked_aux(builder, tests, rs)
        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_richcmp_method(self, env):
        builder = Builder()
        left_marking_name  = 'self'
        right_marking_name = 'other'
        op_name = 'op'
        builder.begin_FunctionDef( name = '__richcmp__',
                                   args = (A('self', type = type2str(self.type))
                                           .param(right_marking_name, type = type2str(self.type))
                                           .param(op_name, type = type2str(TypeInfo.Int))) )
        builder.emit_Return(cyast.Compare(left=cyast.Call(func=cyast.Name('neco_marking_compare'),
                                                          args=[cyast.Name(left_marking_name),
                                                                cyast.Name(right_marking_name)]
                                                          ),
                                          ops=[cyast.Eq()],
                                          comparators=[cyast.Num(0)])
                            )
        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_hash_method(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = "__hash__",
                                   args = A("self", type = "Marking"),
                                   decl = [ Builder.CVar( name = 'h', type = 'int' ) ])

        builder.emit( E("h = 0xDEADDAD") )
        mult = 0xBADBEEF
        i = 0

        maximum = 2**32-1
        offset = 2**31-1

        if self._pack:
            for index in range(0, self._pack.native_field_count()):
                native_field = self._pack.get_native_field('self', index)
                builder.emit( cyast.Assign(targets=[cyast.Name('h')],
                                           value=cyast.BinOp(left = cyast.BinOp(left=cyast.Name('h'),
                                                                                op=cyast.BitXor(),
                                                                                right=native_field),
                                                             op = cyast.Mult(),
                                                             right = cyast.Num((mult % maximum) - offset) ) ) )
                #E('h').assign(E('h').xor(native_field).mult(E(mult))) )
                mult += (82520L + i + i)
                i += 1

        for place_type in self.place_types.itervalues():
            if place_type.is_packed or place_type.is_helper:
                pass
            else:
                if place_type.type.is_Int or place_type.type.is_Short or place_type.type.is_Char:
                    native_place = self.id_provider.get(place_type)
                    builder.emit(E('h = (h ^ self.{place_name}) * {mult}'.format(place_name=native_place,
                                                                                 mult=(mult % maximum) - offset))
                                 )
                                 #builder.emit( E('h').assign(E('h').xor(E('self').attr(native_place)).mult(E(mult))) )
                else:
                    place_hash = place_type.hash_expr(env, marking_name = "self")
                    builder.emit(cyast.Assign(targets=[cyast.Name('h')],
                                              value=cyast.BinOp(left=cyast.BinOp(left=cyast.Name('h'),
                                                                                 op=cyast.BitXor(),
                                                                                 right=place_hash),
                                                                op=cyast.Mult(),
                                                                right=cyast.Num((mult % maximum) - offset))
                                              )
                                 )
                mult += (82521L * i + i)
                i += 1

        builder.emit_Return(E("h"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_dump(self, env):
        builder = Builder()
        builder.begin_FunctionCDef(name = "neco_marking_dump",
                                   args = A("self", type="Marking"),
                                   returns = cyast.Name("char*"),
                                   decl = [ Builder.CVar( "c_string", type = "char*" ) ],
                                   public=True, api=True)
        builder.emit(E("py_unicode_string = str(self)"))
        builder.emit(E("py_byte_string = py_unicode_string.encode('UTF-8')"))
        builder.emit(E("c_string = py_byte_string"))
        builder.emit_Return(E("c_string"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_hash(self, env):
        builder = Builder()
        builder.begin_FunctionCDef( name = "neco_marking_hash",
                                    args = A("self", type = "Marking"),
                                    returns = E("int"),
                                    public=True, api=True)
        builder.emit_Return(E('self.__hash__()'))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_copy(self, env):
        builder = Builder()
        builder.begin_FunctionCDef( name = "neco_marking_copy",
                                    args = A("self", type = "Marking"),
                                    returns = E("Marking"),
                                    public=True, api=True)
        builder.emit_Return(E('self.copy()'))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_check(self, env):
        builder = Builder()
        builder.begin_FunctionCDef(name="neco_check",
                                   args=(A("self", type=type2str(self.type))
                                         .param("atom", type=type2str(TypeInfo.Int))),
                                   returns=E(type2str(TypeInfo.Int)),
                                   public=True, api=True)
        builder.emit_Return(E("self.check(atom)"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def free_marking_stmt(self, env, marking_name):
        pass


    def gen_str_method(self, env):
        items = list(self.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = Builder()
        builder.begin_FunctionDef( name = "__str__",
                                   args = A("self") )
        visited = set()
        builder.emit(E('s = ""'))
        for i, (place_name, place_type) in enumerate(items):
            if i > 0:
                builder.emit(E('s += ", "'))
            # if place_type.is_packed:
            #     if place_type.pack in visited:
            #         continue

            #     assert(False and "TO DO")

            #     place_type = self.get_place_type_by_name(place_name)
            #     builder.emit( E('s').add_assign( place_type.dump_expr(env, 'self') ) )
            # else:
            place_type = self.get_place_type_by_name(place_name)
            builder.emit( E( 's += %s' % repr(place_name + ': ')) )

            builder.emit(cyast.AugAssign(target=cyast.Name('s'),
                                         op=cyast.Add(),
                                         value=cyast.Call(func=cyast.Name("str"),
                                                          args=[place_type.dump_expr(env, 'self')])
                                         )
                         )

        builder.emit_Return(E('s'))
        builder.end_FunctionDef()
        return to_ast(builder)

    @todo
    def _gen_repr(self, env):
        items = list(self.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = Builder()
        builder.begin_FunctionDef( name = "__repr__",
                                   args = A("self") )
        builder.emit( E('s = "hdict({"') )

        visited = set()
        for i,(place_name, place_type) in enumerate(items):
            tmp = ',\n' if i > 0 else ''
            if place_type.is_packed:
                if place_type.pack in visited:
                    continue
                place = self.gen_get_place(env, marking_name = 'self', place_name = place_name)
                str_call = E('str').call([place])
                builder.emit( E('s').add_assign( E("{tmp}'{place_name}' :".format(tmp=tmp, place_name=place_name)).add(str_call)) )
            else:
                builder.emit( E('s').add_assign( E( tmp + "'" + place_name + "' : " ).add( E( 'repr(self.{place})'.format(place = self.id_provider.get(place_type))) ) ) )


        builder.emit( E('s += "})"') )
        builder.emit_Return(E("s"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def dump_expr_method(self, env):
        items = list(self.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = Builder()
        builder.begin_FunctionDef(name='__dump__',
                                  args=A('self'))

        builder.emit(E('s = "begin marking"'))
        for (i, (place_name, place_type)) in enumerate(items):
            if place_type.is_revelant:

                if isinstance(place_type, FlowPlaceTypeHelper):
                    builder.emit(cyast.AugAssign(target=ast.Name(id='s'),
                                                 op=ast.Add(),
                                                 value=place_type.dump_expr(env, 'self')))
                else:
                    builder.emit(cyast.AugAssign(target=ast.Name(id='s'),
                                                 op=ast.Add(),
                                                 value=ast.BinOp(left=cyast.Str(s='\n' + place_name + " - "),
                                                                 op=cyast.Add(),
                                                                 right=place_type.dump_expr(env, 'self'))
                                                 )
                                 )
        builder.emit(E('s += "\\nend marking\\n"'))
        builder.emit_Return(E('s'))

        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_atom_case(self, env, builder, atom, checked_id, first=False):
        """ Produce a if/elif case in ckeck functions.

        @param builder:
        @type builder: C{}
        @param atom:
        @type atom: C{}
        @param first:
        @type first: C{}
        """
        if first:
            builder.begin_If(test=cyast.Compare(left=cyast.Name(checked_id),
                                                ops=[cyast.Eq()],
                                                comparators=[cyast.Num(atom.id)]))
        else:
            builder.begin_Elif(test=cyast.Compare(left=cyast.Name(checked_id),
                                                  ops=[cyast.Eq()],
                                                  comparators=[cyast.Num(atom.id)]))
        builder.emit(cyast.Comment("atom: {name}".format(name=atom.name)))

        for place_name in atom.place_names:
            place_type = self.get_place_type_by_name(place_name)
            if place_type.checking_need_helper:
                builder.emit(cyast.Assign(targets=[cyast.Name(place_name)],
                                          value=place_type.check_helper_expr(env, 'self'))
                             )
            else:
                builder.emit(cyast.Assign(targets=[cyast.Name(place_name)],
                                          value=self.gen_get_place(env,
                                                                   place_name = place_name,
                                                                   marking_name = 'self')
                                          )
                             )
        builder.emit_Return(cyast.Call(func=cyast.Name(atom.name),
                                       args=[ cyast.Name(place_name) for place_name in atom.place_names ]))
        return

    def gen_check_method(self, env):
        """ Produce simple checking method.

        The method has the following signature:
        C{cdef int check(Marking self, int atom)}

        @param env: compiling environment.
        """
        checked_id = 'atom'
        builder = Builder()
        builder.begin_FunctionCDef(name='check',
                                   args=(A('self', type = type2str(self.type))
                                         .param(checked_id, type='int')),
                                   returns = cyast.Name('int'))

        for atom in self.atoms[0:1]:
            self.gen_atom_case(env, builder, atom, checked_id, True)
        for atom in self.atoms[1:]:
            self.gen_atom_case(env, builder, atom, checked_id)
        for atom in self.atoms:
            builder.end_If()

        # should not be rachable in produced code, so we inform about an invalid ID
        builder.emit(stmt(E('sys.stderr.write("net: invalid atom ID\\n")')))
        builder.emit_Return(cyast.Num('0'))

        builder.end_FunctionDef()
        return to_ast(builder)


    def _gen_C_get_prop_name(self, env):
        """ Produce a method that returns atomic properties names by ids.

        The method has the following signature:
        C{cdef char* get_prop_name(Marking self, int atom)}

        @param env: compiling environment.
        """
        checked_id = 'atom'
        builder = Builder()
        builder.begin_FunctionCDef(name='neco_get_prop_name',
                                   args=(A(checked_id, type='int')),
                                   returns = cyast.Name('char*'),
                                   public=True, api=True)

        for atom in self.atoms[0:1]:
            self.gen_get_prop_name_case(env, builder, atom, checked_id, True)
        for atom in self.atoms[1:]:
            self.gen_get_prop_name_case(env, builder, atom, checked_id)
        for atom in self.atoms:
            builder.end_If()

        # should not be rachable in produced code, so we inform about an invalid ID
        builder.emit(E('return \'\''))

        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_get_prop_name_case(self, env, builder, atom, checked_id, first=False):
        """ Produce a if/elif case in get_prop_name method.
        """
        if first:
            builder.begin_If(test=cyast.Compare(left=cyast.Name(checked_id),
                                                ops=[cyast.Eq()],
                                                comparators=[cyast.Num(atom.id)]))
        else:
            builder.begin_Elif(test=cyast.Compare(left=cyast.Name(checked_id),
                                                  ops=[cyast.Eq()],
                                                  comparators=[cyast.Num(atom.id)]))
        builder.emit(cyast.Comment("atom: {name}".format(name=atom.name)))

        builder.emit_Return(E(repr(atom.name)))
        return


    def gen_api(self, env):
        cls = Builder.PublicClassCDef(name = "Marking",
                                      bases = [ E("object") ],
                                      spec = cyast.type_name_spec(o="Marking", t="MarkingType"))

        ################################################################################
        # methods
        ################################################################################

        cls.add_method( self.gen_init_method(env) )
        cls.add_method( self.gen_dealloc_method(env) )
        #cls.add_method( self.gen_str_method(env) )
        cls.add_method( self.gen_richcmp_method(env) )
        cls.add_method( self.gen_hash_method(env) )
        cls.add_method( self.gen_copy_method(env) )
        cls.add_method( self.dump_expr_method(env) )
        cls.add_method( self.gen_check_method(env) )

        ################################################################################
        # comments
        ################################################################################

        attributes = set()
        for place_type in self.place_types.itervalues():
            if place_type.is_packed:
                attributes.add("{attribute}[{offset}]".format(attribute = self.id_provider.get(self._pack),
                                                              offset = self._pack.get_field_native_offset(place_type)))
            else:
                attributes.add(self.id_provider.get(place_type))
        attribute_max = max( len(attr) for attr in attributes)

        comms = set([])
        for place_type in self.place_types.itervalues():
            if place_type.is_packed:
                attr = "{attribute}[{offset}]".format(attribute = self.id_provider.get(self._pack),
                                                      offset = self._pack.get_field_native_offset(place_type))
            else:
                attr = self.id_provider.get(place_type)
            comms.add("{info} - packed: {packed:1} - attribute: {attribute:{attribute_max}} #"
                         .format(info=place_type.info,
                                 packed=place_type.is_packed,
                                 attribute=attr,
                                 attribute_max=attribute_max))
        max_length = max(len(x) - 2 for x in comms)
        comms = list(comms)
        comms.insert(0, "{text:*^{max_length}} #".format(text=' Marking Structure ', max_length=max_length))
        comms.append("{text:*^{max_length}} #".format(text='*', max_length=max_length))

        comms_ast = [ cyast.NComment(comm) for comm in comms ]
        cls.add_decl(comms_ast)

        ################################################################################
        # attributes
        ################################################################################

        if self._pack:
            name = '{name}[{count}]'.format(name  = self.id_provider.get(self._pack),
                                            count = self._pack.native_field_count())
            cls.add_decl( cyast.CVar(name, type=type2str(self._pack.type)) )

        for place_type in self.place_types.itervalues():
            if not place_type.is_packed and not place_type.is_helper:
                cls.add_decl(cyast.CVar(name=self.id_provider.get(place_type),
                                        type=type2str(place_type.type)))

        ################################################################################
        # C api
        ################################################################################

        capi = []
        capi.append( self._gen_C_hash(env) )
        capi.append( self._gen_C_copy(env) )
        capi.append( self._gen_C_compare(env) )
        capi.append( self._gen_C_dump(env) )
        capi.append( self._gen_C_check(env) )
        capi.append( self._gen_C_get_prop_name(env) )
        return [to_ast(cls), capi]


    def gen_copy(self, env, src_marking_name, dst_marking_name, modified_places):
        """

        @param modified_places:
        @type modified_places: C{}
        """
        nodes = []
        nodes.append( E( dst_marking_name + " = Marking()" ) )

        copy_packs = set()
        copy_places = set()
        assign_packs = set()
        assign_places = set()

        for place_type in self.place_types.itervalues():
            if place_type.info in modified_places:
                if place_type.is_packed:
                    copy_packs.add(place_type.pack)
                else:
                    copy_places.add(place_type)
            else:
                if place_type.is_packed:
                    assign_packs.add(place_type.pack)
                else:
                    assign_places.add(place_type)

        # a place in copy from a pack forces the copy of the whole pack
        assign_packs = assign_packs - copy_packs


        if self._pack:
            nodes.append( self._pack.copy_expr(env, src_marking_name = src_marking_name, dst_marking_name = dst_marking_name) )

        for place_type in copy_places:
            if place_type.is_helper or place_type.is_packed:
                pass
            else:
                place_expr = self.gen_get_place(env,
                                                place_name = place_type.info.name,
                                                marking_name = dst_marking_name)
                nodes.append(cyast.Assign(targets=[place_expr],
                                          value=place_type.copy_expr(env, marking_name = src_marking_name))
                             )


        for place_type in assign_places:
            if place_type.is_helper or place_type.is_packed:
                pass
            else:
                place_expr = self.gen_get_place(env,
                                                place_name = place_type.info.name,
                                                marking_name = dst_marking_name)
                nodes.append(cyast.Assign(targets=[place_expr],
                                          value=place_type.light_copy_expr(env, marking_name = src_marking_name))
                             )

        return to_ast(nodes)

    def copy_marking_expr(self, env, marking_name):
        return cyast.Call(func=cyast.Attribute(name=marking_name,
                                               attr='copy')
                          )

    def gen_get_place(self, env, marking_name, place_name):
        place_type = self.get_place_type_by_name(place_name)

        if place_type.is_packed:
            return place_type.pack.gen_get_place(env, marking_name, place_type)
        else:
            return cyast.Attribute(value=cyast.Name(marking_name),
                                   attr=self.id_provider.get(place_type))

    # def gen_get_place_size(self, env, marking_name, place_name):
    #     place_type = self.get_place_type_by_name(place_name)

    #     assert (not place_type.is_packed)
    #     return place_type.get_size_expr(env = env, marking_name = marking_name)

    # def gen_get_token(self, env, marking_name, place_name, index):
    #     place_type = self.get_place_type_by_name(place_name)

    #     assert (not place_type.is_packed)
    #     return place_type.get_token_expr(env = env,
    #                                      marking_name = marking_name,
    #                                      index = index)

    def gen_get_pack(self, env, marking_name, pack):
        return E(marking_name).attr(self.id_provider.get(pack))

    # def remove_token_stmt(self, env, token, marking_name, place_name):
    #     place_type = self.get_place_type_by_name(place_name)
    #     return place_type.remove_token_stmt(env = env,
    #                                                      compiled_token = token,
    #                                                      marking_name = marking_name)

    # def remove_by_index_stmt(self, env, token, marking_name, place_name, index):
    #     place_type = self.get_place_type_by_name(place_name)
    #     return place_type.remove_by_index_stmt(env = env,
    #                                                         index = index,
    #                                                         marking_name = marking_name)

    # def add_token_stmt(self, env, token, marking_name, place_name):
    #     place_type = self.get_place_type_by_name(place_name)
    #     return place_type.add_token_stmt(env = env,
    #                                                   compiled_token = token,
    #                                                   marking_name = marking_name)

    # def token_expr(self, env, place_name, value):
    #     place_type = self.get_place_type_by_name(place_name)
    #     return place_type.token_expr(env, value)

    ################################################################################
    # Flow elimination
    ################################################################################

    def gen_check_flow(self, env, marking_name, place_info, current_flow):
        place_type = self.get_place_type_by_name(place_info.name)
        assert( isinstance(place_type, FlowPlaceTypeHelper))
        return place_type.gen_check_flow(env=env,
                                         marking_name=marking_name,
                                         place_info=place_info,
                                         current_flow=current_flow)

    def gen_update_flow(self, env, marking_name, place_info):
        place_type = self.get_place_type_by_name(place_info.name)
        assert( isinstance(place_type, FlowPlaceTypeHelper))
        return place_type.gen_update_flow(env=env,
                                          marking_name=marking_name,
                                          place_info=place_info)

    def gen_read_flow(self, env, marking_name, process_name):
        witness = None
        for place in self.place_types.itervalues():
            if place.process_name == process_name and isinstance(place, FlowPlaceTypeHelper):
                witness = place
                break

        if (witness == None):
            raise RuntimeError("no witness for process {process}".format(process = process_name))
        return witness.gen_read_flow(env, marking_name)

################################################################################

class MarkingSetType(coretypes.MarkingSetType):
    """ Python implementation of the marking set type. """

    def __init__(self, markingtype):
        coretypes.MarkingSetType.__init__(self, markingtype)
        self.add_attribute_name = "add"

    def gen_api(self, env):
        pass

    def new_marking_set_expr(self, env):
        return cyast.Call(func=cyast.Name("set"))

    def add_marking_stmt(self, env, markingset_name, marking_name):
        return cyast.Call(func=cyast.Attribute(value=cyast.Name(markingset_name),
                                               attr=self.add_attribute_name),
                          args=[E(marking_name)])

################################################################################
# opt
################################################################################

class OneSafePlaceType(onesafe.OneSafePlaceType, CythonPlaceType):
    """ Cython one safe place Type implementation.

    Somehow peculiar because encoded using two place types, one packed for
    the emptiness test and one for the contained data.
    """

    def __init__(self, place_info, marking_type, helper):
        onesafe.OneSafePlaceType.__init__(self,
                                          place_info,
                                          marking_type,
                                          place_info.type,
                                          place_info.type)
        self.existence_helper_place_type = helper
        self.info = place_info
        self.marking_type = marking_type

    def new_place_expr(self, env):
        type = self.info.type
        if type.is_BlackToken or type.is_Int:
            return E(0)
        elif type.is_Char or type.is_String:
            return E("''")
        elif type.is_UserType:
            return E( type2str(type) + '()' )
        elif type.is_AnyType:
            return E("None")
        else:
            assert(False and "TO DO")

    def delete_stmt(self, env, marking_name):
        return []

    def hash_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=cyast.Name("hash"),
                          args=[place_expr])

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left,
                             ops=[cyast.Eq()],
                             comparators=[right])

    def compare_expr(self, env, left_marking_name, right_marking_name):
        left_helper_expr  = self.existence_helper_place_type.place_expr(env, left_marking_name)
        right_helper_expr = self.existence_helper_place_type.place_expr(env, right_marking_name)
        left  = self.place_expr(env, left_marking_name)
        right = self.place_expr(env, right_marking_name)

        type = self.info.type
        if type.is_Int:
            token_compare_expr=cyast.BinOp(left=left,
                                           op=Sub(),
                                           right=right)
        elif type.is_UserType or type.is_AnyType:
            token_compare_expr=cyast.Call(func=cyast.Name("__neco_compare__"),
                                          args=[left, right])
        else:
            raise NotImplemented

        helper_compare_expr=cyast.IfExp(test=cyast.UnaryOp(operand=cyast.BinOp(left=left_helper_expr,
                                                                       op=cyast.BitAnd(),
                                                                       right=right_helper_expr),
                                                           op=cyast.Not()),
                                        body=cyast.Num(0),
                                        orelse=cyast.IfExp(cyast.BinOp(left=cyast.UnaryOp(operand=left_helper_expr,
                                                                                          op=cyast.Not()),
                                                                       op=cyast.BitAnd(),
                                                                       right=right_helper_expr),
                                                           body=cyast.Num(-1),
                                                           orelse=cyast.Num(1))
                                        )

        return cyast.IfExp(test=cyast.BinOp(left=left_helper_expr,
                                            op=cyast.BitAnd(),
                                            right=right_helper_expr),
                           body=token_compare_expr,
                           orelse=helper_compare_expr)


    def not_empty_expr(self, env, marking_name):
        return self.existence_helper_place_type.gen_get_place(env, marking_name = marking_name)

    @should_not_be_called
    def iterable_expr(self, env, marking_type, marking_name): pass

    def remove_token_stmt(self, env, compiled_token, marking_name):
        return self.existence_helper_place_type.remove_token_stmt(env, None, marking_name )

    def add_token_stmt(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name) #self.existence_helper_place_type.place_expr(env, marking_name)
        return [ cyast.Assign(targets=[place_expr],
                              value=compiled_token),
                 self.existence_helper_place_type.add_token_stmt(env, None, marking_name) ]

    def token_expr(self, env, token):
        return E(repr(token))

    def light_copy_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def copy_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def dump_expr(self, env, marking_name):
        helper_expr = self.existence_helper_place_type.place_expr(env, marking_name)
        place_expr = self.place_expr(env, marking_name)
        return cyast.IfExp(test=helper_expr,
                           body=cyast.Call(func=cyast.Name('dump'),
                                           args=[place_expr]),
                           orelse=cyast.Str(''))


################################################################################

class BTPlaceType(onesafe.BTPlaceType, CythonPlaceType):
    """ Python black token place type implementation.

    @attention: Using this place type without the BTTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type):
        onesafe.BTPlaceType.__init__(self,
                                     place_info=place_info,
                                     marking_type=marking_type,
                                     type=TypeInfo.Short,
                                     token_type=TypeInfo.Short)
        self.info = place_info
        self.marking_type = marking_type

    def delete_stmt(self, env, marking_name):
        return []

    def hash_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left,
                             ops=[cyast.Eq()],
                             comparators=[right])

    def compare_expr(self, env, left_marking_name, right_marking_name):
        left  = self.place_expr(env, left_marking_name)
        right = self.place_expr(env, right_marking_name)
        return cyast.BinOp(left=left,
                           op=cyast.Sub(),
                           right=right)

    def new_place_expr(self, env):
        return cyast.Num(0)

    def not_empty_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def dump_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=E("' '.join"),
                          args=[cyast.BinOp(left=cyast.List([cyast.Str('dot')]),
                                            op=cyast.Mult(),
                                            right=place_expr)])

    def iterable_expr(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.Call(func=cyast.Name('range'),
                          args=[ cyast.Num(0), place_expr ])

    def remove_token_stmt( self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.AugAssign(target=place_expr,
                               op=cyast.Sub(),
                               value=cyast.Num(1))

    def add_token_stmt(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return cyast.AugAssign(target=place_expr,
                               op=cyast.Add(),
                               value=cyast.Num(1))

    def copy_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def light_copy_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def token_expr(self, env, token):
        return E("dot")

################################################################################

class BTOneSafePlaceType(onesafe.BTOneSafePlaceType, CythonPlaceType):
    """ Python one safe black token place type.

    Using this place type without the BTOneSafeTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type):
        self.info = place_info
        self.marking_type = marking_type

    def new_place_expr(self, env):
        return E("0")

    @should_not_be_called
    def iterable_expr(self, env, marking_type, marking_name): pass

    def remove_token_stmt( self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign("0")

    def add_token_stmt(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return Builder.LValut(place_expr).assign("1")

    def copy_expr(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def token_expr(self, env, token):
        return E("dot")

################################################################################

class BT1SPack(object):
    """ Class used to pack BlackToken one bound places. """

    MAX_LENGTH = 8

    def __init__(self, marking_type):
        """
        """
        self.marking_type = marking_type
        self.packed = []

    @property
    def is_full(self):
        return len(self.packed) >= BT1SPack.MAX_LENGTH

    @property
    def type(self):
        return TypeInfo.Char

    @property
    def token_type(self):
        return TypeInfo.Char

    def pack_expr(self, env, marking_name):
        return env.marking_type.gen_get_pack(env = env,
                                             marking_name = marking_name,
                                             pack = self)

    def gen_init_value(self, env):
        return E("0x0")

    def gen_get_place(self, env, marking_name, place_type):
        offset = self._offset_of( place_type )
        return E(self.marking_type.gen_get_pack(env, marking_name, self)).add(E(repr(offset)))

    def push(self, place_type):
        """ Add a place type to the pack

        Added places will be encoded within a unique class attribute.

        @param place_type: type to be pushed
        @type place_type: C{PackedBT1SPlaceType}
        """
        assert isinstance(place_type, PackedBT1SPlaceType)
        assert len(self.packed) <= BT1SPack.MAX_LENGTH

        self.packed.append( place_type )
        place_type.pack = self

    def _offset_of(self, place_type):
        return 1 << self.packed.index(place_type)

    def remove(self, env, place_type, marking_name):
        offset = self._offset_of(place_type)
        mask = (offset) # forces to 8 bits

        pack_expr = self.pack_expr(env, marking_name)
        return E(pack_expr).xor_assign(E(mask))


    def add(self, env, place_type, marking_name):
        offset = self._offset_of(place_type)

        mask = offset
        pack_expr = self.pack_expr(env, marking_name)
        return E(pack_expr).or_assign(E(mask))

    def copy_expr(self, env, marking_name):
        return marking_type.gen_get_pack(env = env,
                                         marking_name = marking_name,
                                         pack = self)

#@not_revelant
@packed_place
class PackedBT1SPlaceType(coretypes.PlaceType, CythonPlaceType):
    """ BlackToken place types that have been packed.
    """

    def __init__(self, place_info, marking_type, pack):
        """ new place type

        @param place_info: place info structure
        @type place_info: C{PlaceInfo}
        """
        self.pack = pack
        self.info = place_info
        self.marking_type = marking_type
        coretypes.PlaceType.__init__(self,
                                     place_info = place_info,
                                     marking_type = marking_type,
                                     type = self.pack.type,
                                     token_type = TypeInfo.UnsignedInt)

    @should_not_be_called
    def new_place_expr(self, env): pass

    @should_not_be_called
    def iterable_expr(self, env, marking_type, marking_name): pass

    def gen_get_place(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def remove_token_stmt( self, env, compiled_token, marking_name):
        return self.pack.gen_remove_bit(env, marking_name, self)

    def add_token_stmt(self, env, compiled_token, marking_name):
        return self.pack.gen_set_bit(env, marking_name, self)

    def copy_expr(self, env, marking_name):
        return self.pack.copy_expr(env, marking_name)

    def token_expr(self, env, token):
        return E(1)

    def dump_expr(self, env, marking_name):
        return cyast.IfExp(test=self.gen_get_place(env, marking_name),
                           body=cyast.Str('dot'),
                           orelse=cyast.Str(''))

    def not_empty_expr(self, env, marking_name):
        return self.gen_get_place(env, marking_name)

    def check_helper_expr(self, env, marking_name):
        return cyast.Call(func=E("BtPlaceTypeHelper"),
                          args=[IfExp(test=self.gen_get_place(env, marking_name),
                                      body=cyast.Num(1),
                                      orelse=cyast.Num(0))])

################################################################################
#
################################################################################

@not_revelant
@packed_place
class FlowPlaceType(coretypes.PlaceType, CythonPlaceType):

    def __init__(self, place_info, marking_type):
        self.pack = None
        self._counter = 0
        self._places = {}
        self._helpers = {}
        coretypes.PlaceType.__init__(self,
                                     place_info=place_info,
                                     marking_type=marking_type,
                                     type=TypeInfo.UnsignedInt,
                                     token_type=TypeInfo.UnsignedInt)

    @property
    def max(self):
        assert( self._counter != 0 )
        return self._counter - 1

    @property
    def needed_bits(self):
        return int(math.ceil(math.log(self._counter, 2)))

    @should_not_be_called
    def new_place_expr(self, env): pass

    @should_not_be_called
    def delete_stmt(self, env, marking_name): pass

    @should_not_be_called
    def iterable_expr(self, env, marking_name): pass

    @should_not_be_called
    def remove_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def add_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def copy_expr(self, env, marking_name): pass

    @should_not_be_called
    def light_copy_expr(self, env, marking_name): pass

    def add_helper(self, place_info):
        """ Adds a flow control place.

        @param place_info: flow control place to be added
        @type place_info: C{PlaceInfo}
        """
        assert(place_info.flow_control)
        if self._places.has_key(place_info.name):
            return
        self._helpers[place_info.name] = FlowPlaceTypeHelper(place_info, self.marking_type, self)
        self._places[place_info.name] = self._counter
        self._counter += 1

    def get_helper(self, place_info):
        return self._helpers[place_info.name]

    def gen_check_flow(self, env, marking_name, place_info, current_flow):
        next_flow = self._places[place_info.name]
        if not current_flow:
            current_flow = self.place_expr(env, marking_name)
        else:
            current_flow = E(current_flow.name)

        mask = int(self.pack.field_compatible_mask(self.info, next_flow))
        return Builder.EqCompare(current_flow, E(mask))

    def gen_update_flow(self, env, marking_name, place_info):
        """ Get an ast representing the flow update.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        return [ self.pack.gen_set(env = env,
                                   marking_name = marking_name,
                                   place_type = self,
                                   integer = self._places[place_info.name]) ]

    def gen_read_flow(self, env, marking_name, place_type):
        return self.pack.gen_get_place(env = env,
                                       marking_name = marking_name,
                                       place_type = self)

    def dump_expr(self, env, marking_name, place_info):
        for (place_name, next_flow) in self._places.iteritems():
            if place_name == place_info.name:
                mask = int(self.pack.field_compatible_mask(self.info, next_flow))
                check =  Builder.EqCompare(self.place_expr(env, marking_name), E(mask))
                return cyast.BinOp(left=cyast.Str('\n' + place_name + ' - '),
                                   op=cyast.Add(),
                                   right=cyast.IfExp(test=check,
                                                     body=cyast.Str('dot'),
                                                     orelse=cyast.Str(''))
                                   )
        assert(False)

@helper_place_type
class FlowPlaceTypeHelper(coretypes.PlaceType, CythonPlaceType):

    def __init__(self, place_info, marking_type, flow_place_type):
        self.flow_place_type = flow_place_type
        coretypes.PlaceType.__init__(self,
                                     place_info = place_info,
                                     marking_type = marking_type,
                                     type = TypeInfo.UnsignedInt,
                                     token_type = TypeInfo.UnsignedInt)

    @should_not_be_called
    def new_place_expr (self, env): pass

    @should_not_be_called
    def delete_stmt(self, env, marking_name): pass

    @should_not_be_called
    def iterable_expr(self, env, marking_name): pass

    @should_not_be_called
    def remove_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def add_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def copy_expr(self, env, marking_name): pass

    @should_not_be_called
    def light_copy_expr(self, env, marking_name): pass

    def gen_check_flow(self, env, marking_name, place_info, current_flow):
        return self.flow_place_type.gen_check_flow(env, marking_name, place_info, current_flow)

        mask = int(self.pack.field_compatible_mask(self.info, next_flow))
        return Builder.EqCompare(current_flow, E(mask))

    def gen_update_flow(self, env, marking_name, place_info):
        """ Get an ast representing the flow update.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        return self.flow_place_type.gen_update_flow(env, marking_name, place_info)

    def gen_read_flow(self, env, marking_name):
        return self.flow_place_type.gen_read_flow(env=env,
                                                  marking_name=marking_name,
                                                  place_type=self)

    def dump_expr(self, env, marking_name):
        return self.flow_place_type.dump_expr(env, marking_name, self.info)

################################################################################

@not_revelant
class PackedPlaceTypes(object):
    def __init__(self, name, marking_type):
        self.name = name
        self.marking_type = marking_type
        self._bitfield = MaskBitfield(native_width=8)

    @property
    def type(self):
        return TypeInfo.UnsignedChar

    def _id_from_place_info(self, place_info):
        if place_info.flow_control:
            return self.marking_type.id_provider.get(place_info) + "_f"
        elif place_info.one_safe:
            return self.marking_type.id_provider.get(place_info) + "_1s"
        else:
            return self.marking_type.id_provider.get(place_info)

    def native_field_count(self):
        return self._bitfield.native_field_count()

    def get_native_field(self, marking_name, index):
        return cyast.Subscript(cyast.Attribute(cyast.Name(marking_name),
                                               attr=self.name),
                               slice=cyast.Index(cyast.Num(index)))


    def get_field_native_offset(self, place_type):
        return self._bitfield.get_field_native_offset(self._id_from_place_info(place_type.info))

    def add_place(self, place_info, bits):
        self._bitfield.add_field( self._id_from_place_info(place_info), bits )

    def get_fields(self):
        for field in self._bitfield.get_fields():
            yield field

    def field_compatible_mask(self, place_info, integer):
        return self._bitfield.get_field_compatible_mask(self._id_from_place_info(place_info), integer)


    def gen_initialise(self, env, marking_name):
        l = []
        for index in range(0, self.native_field_count()):
            l.append( cyast.Assign(targets=[cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_name),
                                                                                  attr=self.name),
                                                            slice=cyast.Index(cyast.Num(index)))],
                                   value=cyast.Num(0)) )
        return to_ast(l)

    def gen_get_place(self, env, marking_name, place_type):
        place_info = place_type.info
        offset = self._bitfield.get_field_native_offset(self._id_from_place_info(place_info))
        mask = int(~self._bitfield.get_field_mask(self._id_from_place_info(place_info)))
        return cyast.BinOp(left=cyast.Subscript(cyast.Attribute(cyast.Name(marking_name),
                                                                attr=self.name),
                                                slice=cyast.Index(cyast.Num(offset))),
                           op=cyast.BitAnd(),
                           right=E(mask))

    def gen_remove_bit(self, env, marking_name, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = cyast.AugAssign(target=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_name),
                                                                         attr=self.name),
                                                   slice=cyast.Index(cyast.Num(offset))),
                            op=cyast.BitXor(),
                            value=cyast.Num(value))
        # e = E(marking_name).attr(self.name).subscript(index=offset).xor_assign(E(value))
        comment = cyast.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value,
                                                                                anw=(self._bitfield.native_width + 2),
                                                                                place=place_type.info.name))
        return [ e, comment ]

    def gen_set_bit(self, env, marking_name, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = cyast.AugAssign(target=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_name),
                                                                         attr=self.name),
                                                   slice=cyast.Index(cyast.Num(offset))),
                            op=cyast.BitOr(),
                            value=cyast.Num(value))
        #e = E(marking_name).attr(self.name).subscript(index=str(offset)).or_assign(E(value))
        comment = Builder.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def gen_set(self, env, marking_name, place_type, integer):
        field  = self._id_from_place_info(place_type.info)
        mask   = int(self._bitfield.get_field_mask(field))
        vmask  = int(self._bitfield.get_field_compatible_mask(field, integer))
        offset = self._bitfield.get_field_native_offset(field)
        #right  = E(marking_name).attr(self.name).subscript(index=str(offset)).bit_and(E(mask)).bit_or(E(vmask))
        right  = cyast.BinOp(left=cyast.BinOp(left=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_name),
                                                                                         attr=self.name),
                                                                   slice=cyast.Index(cyast.Num(offset))),
                                              op=cyast.BitAnd(),
                                              right=E(mask)),
                             op=cyast.BitOr(),
                             right=E(vmask))

        #e = E(marking_name).attr(self.name).subscript(index=str(offset)).assign(right)
        e = cyast.Assign(targets=[cyast.Subscript(value=cyast.Attribute(cyast.Name(marking_name),
                                                                        attr=self.name),
                                                  slice=cyast.Index(cyast.Num(offset)))],
                         value=right)
        comment = Builder.Comment("mask: {mask:#0{anw}b} vmask:{vmask:#0{anw}b} - place:{place}"
                                  .format(mask=mask, vmask=vmask, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def copy_expr(self, env, src_marking_name, dst_marking_name):
        l = []
        for index in range(0, self.native_field_count()):
            right = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(src_marking_name),
                                                          attr=self.name),
                                    slice=cyast.Index(cyast.Num(index)))
            left = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(dst_marking_name),
                                                         attr=self.name),
                                   slice=cyast.Index(cyast.Num(index)))
            l.append( cyast.Assign(targets=[left],
                                   value=right) )
        return l


    def gen_tests(self, left_marking_name, right_marking_name):
        """
        """
        tests = []
        for index in range(0, self.native_field_count()):
            left = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(left_marking_name),
                                                         attr=self.name),
                                   slice=cyast.Index(cyast.Num(index)))
            right = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(right_marking_name),
                                                          attr=self.name),
                                    slice=cyast.Index(cyast.Num(index)))
            tests.append( (left, right, ) )
        return tests


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
