""" Cython basic net types. """

from cyast import Builder, A, to_ast, E, stmt, FunctionDecl, Sub, Name
from maskbitfield import MaskBitfield
from neco.backends.cython.common import NecoTypeError, from_neco_lib
from neco.core.info import TypeInfo, PlaceInfo
from neco.core.nettypes import provides_by_index_access, \
    provides_by_index_deletion
from neco.utils import should_not_be_called, todo
import cyast
import math
import neco.config as config
import neco.core.nettypes as coretypes
import neco.utils as utils

################################################################################

class CythonPlaceType(object):
    """ Base class for cython place types. """

    _packed_place_ = False
    _revelant_ = True # should be dumped
    _helper_ = False
    _checking_need_helper_ = True

    def place_expr(self, env, marking_var):
        """ Get an ast builder corresponding to place access.

        @param env: compiling environment.
        @type env: C{neco.backends.cython.utils.Env}
        @param marking_name: marking structure name.
        @type marking_name: C{str}
        @return: an ast builder.
        @rtype: C{neco.backends.cython.astutils.Builder._cyast_builder}
        """
        return env.marking_type.gen_get_place(env = env,
                                              marking_var = marking_var,
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
        return cyast.Call(func=cyast.Name(id=env.type2str(TypeInfo.MultiSet)))

    def delete_stmt(self, env, marking_var):
        return []

    def hash_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=cyast.Attribute(value=place_expr,
                                               attr="hash")
                          )

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left, ops=[cyast.Eq()], comparators=[right])

    def iterable_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def remove_token_stmt(self, env, token_expr, compiled_token, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='remove'),
                               args=[ compiled_token ])
                    )

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='add'),
                               args=[ compiled_token ])
                    )

    def copy_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=cyast.Attribute(value=place_expr,
                                               attr="copy")
                          )

    def light_copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def clear_stmt(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.Assign(targets=[place_expr],
                            value=cyast.Call(func=cyast.Name(env.type2str(TypeInfo.MultiSet))))

    def not_empty_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def token_expr(self, env, token):
        return E(repr(token))

    def add_multiset_expr(self, env, multiset, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='update'),
                               args=[ multiset ])
                    )

    def dump_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=cyast.Name("dump"),
                          args=[place_expr])

    def add_items_stmt(self, env, multiset, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=cyast.Attribute(value=place_expr,
                                                    attr='add_items'),
                               args=[multiset])
                    )

    def compare_expr(self, env, left_marking_var, right_marking_var):
        left  = self.place_expr(env, left_marking_var)
        right = self.place_expr(env, right_marking_var)
        return cyast.Call(func=cyast.Attribute(value=left,
                                               attr='compare'),
                          args=[right])

    def not_empty_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)


    def enumerate_tokens(self, checker_env, token_variable, marking_var, body):
        marking_type = checker_env.marking_type
        place_type = self
        checker_env.try_declare_cvar(token_variable.name, token_variable.type)
        return Builder.For( target = cyast.Name(token_variable.name),
                            iter = place_type.iterable_expr( env = checker_env,
                                                             marking_var = marking_var),
                            body = [ body ])
    
    def multiset_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

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


    def check_token_type(self, token_expr):
        if not token_expr.type.is_Int:
            raise NecoTypeError(expr=token_expr, type=token_expr.type, expected=TypeInfo.Int)

    def check_index_type(self, index_expr):
        if not index_expr.type.is_Int:
            raise NecoTypeError(expr=index_expr, type=index_expr.type, expected=TypeInfo.Int)

    def check_marking_type(self, marking_expr):
        if not marking_expr.type.is_Marking:
            raise NecoTypeError(expr=marking_expr, type=marking_expr.type, expected=TypeInfo.Marking)


    def new_place_expr(self, env):
        return E(from_neco_lib("int_place_type_new()"))

    def delete_stmt(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_free")),
                               args=[ place_expr ])
                    )

    def hash_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_hash")),
                          args=[ place_expr ])

    def eq_expr(self, env, left, right):
        return cyast.Call(func=E(from_neco_lib("int_place_type_eq")),
                          args=[ left, right ])

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt(self, env, token_expr, compiled_token, marking_var):
        #self.check_token_type(token_expr)
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_rem_by_value")),
                               args=[ place_expr, compiled_token ])
                    )

    def remove_by_index_stmt(self, env, index_var, compiled_index, marking_var):
        self.check_index_type(index_var)
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_rem_by_index")),
                               args=[ place_expr, E(index_var.name) ])
                    )

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        #self.check_token_type(token_expr)
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return stmt(cyast.Call(func=E(from_neco_lib("int_place_type_add")),
                               args=[ place_expr, compiled_token ])
                    )

    def copy_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_copy")),
                          args=[ place_expr ])

    def light_copy_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_light_copy")),
                          args=[ place_expr ])

    def get_size_expr(self, env, marking_var):
        self.check_marking_type(marking_var)
        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_size")),
                          args=[ place_expr ])

    def get_token_expr(self, env, index_expr, compiled_index, marking_var):
        self.check_index_type(index_expr)
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_get")),
                          args=[ place_expr, compiled_index ])

    def clear_stmt(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_clear")),
                          args=[ place_expr ])

    def token_expr(self, env, token):
        return E(repr(token))

    def dump_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_cstr")),
                          args=[ place_expr ])

    def compare_expr(self, env, left_marking_var, right_marking_var):
        self.check_marking_type(left_marking_var)
        self.check_marking_type(right_marking_var)

        left  = self.place_expr(env, left_marking_var)
        right = self.place_expr(env, right_marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_cmp")),
                          args=[ left, right ])

    def not_empty_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_not_empty")),
                          args=[place_expr])

    @todo
    def not_empty_expr(self, env, marking_type, marking_var): pass

    @todo
    def add_multiset_expr(self, env, multiset, marking_type, marking_var): pass

    @todo
    def add_items_stmt(self, env, multiset, marking_type, marking_var): pass

    def enumerate_tokens(self, env, token_var, marking_var, body):
        marking_type = env.marking_type

        index_var = env.variable_provider.new_variable(type=TypeInfo.Int)
        size_var  = env.variable_provider.new_variable(type=TypeInfo.Int)

        env.try_declare_cvar(token_var.name, token_var.type)
        env.try_declare_cvar(index_var.name, TypeInfo.Int)
        env.try_declare_cvar(size_var.name,  TypeInfo.Int)

        place_size = self.get_size_expr(env = env,
                                        marking_var = marking_var)

        get_token = self.get_token_expr(env = env,
                                        index_expr = index_var,
                                        marking_var = marking_var,
                                        compiled_index = Name(index_var.name))


        return [ cyast.Assign(targets=[cyast.Name(size_var.name)],
                              value=place_size),
                 Builder.CFor(start=cyast.Num(0),
                              start_op=cyast.LtE(),
                              target=cyast.Name(index_var.name),
                              stop_op=cyast.Lt(),
                              stop=cyast.Name(size_var.name),
                              body=[ cyast.Assign(targets=[cyast.Name(token_var.name)],
                                                  value=get_token),
                                     body ],
                              orelse = [] ) ]
    
    def multiset_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=E(from_neco_lib("int_place_type_to_multiset")),
                          args=[place_expr])
        

################################################################################


def place_type_from_info(place_info, marking):
    type = place_info.type
    if type.is_Int:
        return IntPlaceType(place_info, marking_type=marking)
    elif type.is_Bool:
        #print >> sys.stderr, "TODO add BoolPlaceType to ctypes, fallback ObjectPlaceType for place {}".format(place_info.name)
        return ObjectPlaceType(place_info, marking_type=marking)
    elif type.is_String:
        #print >> sys.stderr, "TODO add StringPlaceType to ctypes, fallback: ObjectPlaceType for place {}".format(place_info.name)
        return ObjectPlaceType(place_info, marking_type=marking)
    elif type.is_BlackToken:
        return BTPlaceType(place_info, marking_type=marking)
    elif type.is_UserType:
        #print >> sys.stderr, "TODO allow users to provide their own multiset structures, fallback: ObjectPlaceType for place {}".format(place_info.name)
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

        if config.get('optimize'):
            self.packing_enabled = True
        else:
            self.packing_enabled = False

        # pack 1SBT places ?
        if self.packing_enabled:
            name = self.id_provider.new(base = "_packed")
            pack = PackedPlaceTypes(name, self)
            self.id_provider.set(pack, name)
            pack = pack
        else:
            pack = None
        self._pack = pack
        
        import priv.mrkmethods
        self.add_method_generator( priv.mrkmethods.InitGenerator() )
        self.add_method_generator( priv.mrkmethods.DeallocGenerator() )
        self.add_method_generator( priv.mrkmethods.CopyGenerator() )
        #self.add_method_generator( priv.mrkmethods.ReprGenerator() )
        self.add_method_generator( priv.mrkmethods.DumpExprGenerator() )        
        self.add_method_generator( priv.mrkmethods.RichcmpGenerator() )
        self.add_method_generator( priv.mrkmethods.HashGenerator() )
        
        self._C_function_generators = []
        
        import priv.mrkfunctions
        self.add_C_function_generator( priv.mrkfunctions.CompareGenerator() )
        #self.add_C_function_generator( priv.mrkfunctions.MarkedGenerator() )
        self.add_C_function_generator( priv.mrkfunctions.DumpGenerator() )
        self.add_C_function_generator( priv.mrkfunctions.HashGenerator() )
        self.add_C_function_generator( priv.mrkfunctions.CopyGenerator() )
        
    def add_C_function_generator(self, generator):
        self._C_function_generators.append(generator)
        
    @property
    def C_function_generators(self):
        return self._C_function_generators
    
    def generate_C_functions(self, env):
        functions = []
        for generator in self._C_function_generators:
            functions.append( generator.generate(env) )
        return functions


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
        return cyast.Call(func=cyast.Name(env.type2str(self.type)),
                          args=[cyast.Name('alloc')],
                          keywords=[cyast.Name('True')])

    def gen_pxd(self, env):
        cls = Builder.PublicClassCDef(name="Marking",
                                      bases=[E("object")],
                                      spec=cyast.type_name_spec(o="Marking", t="MarkingType"))

        ################################################################################
        # attributes
        ################################################################################

        if self._pack and self._pack.native_field_count() > 0: # at least one bit used
            name = '{name}[{count}]'.format(name  = self.id_provider.get(self._pack),
                                            count = self._pack.native_field_count())
            cls.add_decl( cyast.CVar(name, type=env.type2str(self._pack.type)) )

        for place_type in self.place_types.itervalues():
            if not place_type.is_packed and not place_type.is_helper:
                cls.add_decl(cyast.CVar(name=self.id_provider.get(place_type),
                                        type=env.type2str(place_type.type)))

        cls.add_method( FunctionDecl(name='copy',
                                     args = to_ast(A("self", cyast.Name(env.type2str(self.type)))),
                                     returns = cyast.Name(env.type2str(self.type)),
                                     lang=cyast.CDef()) )

        return to_ast(cls)

    def generate_api(self, env):
        cls = Builder.ClassCDef(name = "Marking",
                                bases = [])

        ################################################################################
        # methods
        ################################################################################
        for method in self.generate_methods(env):
            cls.add_method( method )

        # cls.add_method( self.gen_init_method(env) )
        # cls.add_method( self.gen_dealloc_method(env) )
        # cls.add_method( self.gen_str_method(env) )
        # cls.add_method( self.gen_richcmp_method(env) )
        # cls.add_method( self.gen_hash_method(env) )
        # cls.add_method( self.gen_copy_method(env) )
        # cls.add_method( self.dump_expr_method(env) )

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
        # C api
        ################################################################################

#        capi = []
#        capi.append( self._gen_C_hash(env) )
#        capi.append( self._gen_C_copy(env) )
#        capi.append( self._gen_C_compare(env) )
#        capi.append( self._gen_C_dump(env) )
        return [to_ast(cls), self.generate_C_functions(env)]


    def gen_copy(self, env, src_marking, dst_marking, modified_places):
        """

        @param modified_places:
        @type modified_places: C{}
        """
        nodes = []
        nodes.append( E( dst_marking.name + " = Marking()" ) )

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


        if self._pack and self._pack.native_field_count() > 0:
            nodes.append( self._pack.copy_expr(env, src_marking_var = src_marking, dst_marking_var = dst_marking) )

        for place_type in copy_places:
            if place_type.is_helper or place_type.is_packed:
                pass
            else:
                place_expr = self.gen_get_place(env,
                                                place_name = place_type.info.name,
                                                marking_var = dst_marking)

                nodes.append(cyast.Assign(targets=[place_expr],
                                          value=place_type.copy_expr(env, marking_var = src_marking))
                             )


        for place_type in assign_places:
            if place_type.is_helper or place_type.is_packed:
                pass
            else:
                place_expr = self.gen_get_place(env,
                                                place_name = place_type.info.name,
                                                marking_var = dst_marking)
                nodes.append(cyast.Assign(targets=[place_expr],
                                          value=place_type.light_copy_expr(env, marking_var = src_marking))
                             )

        return to_ast(nodes)

    def copy_marking_expr(self, env, marking_var):
        return cyast.Call(func=cyast.Attribute(name=marking_var.name,
                                               attr='copy')
                          )

    def gen_get_place(self, env, marking_var, place_name):
        place_type = self.get_place_type_by_name(place_name)

        if place_type.is_packed:
            return place_type.pack.gen_get_place(env, marking_var, place_type)
        else:
            return cyast.Attribute(value=cyast.Name(marking_var.name),
                                   attr=self.id_provider.get(place_type))

    def gen_get_pack(self, env, marking_var, pack):
        return E(marking_var.name).attr(self.id_provider.get(pack))

    ################################################################################
    # Flow elimination
    ################################################################################

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        place_type = self.get_place_type_by_name(place_info.name)
        assert( isinstance(place_type, FlowPlaceTypeHelper))
        return place_type.gen_check_flow(env=env,
                                         marking_var=marking_var,
                                         place_info=place_info,
                                         current_flow=current_flow)

    def gen_update_flow(self, env, marking_var, place_info):
        place_type = self.get_place_type_by_name(place_info.name)
        assert( isinstance(place_type, FlowPlaceTypeHelper))
        return place_type.gen_update_flow(env=env,
                                          marking_var=marking_var,
                                          place_info=place_info)

    def gen_read_flow(self, env, marking_var, process_name):
        witness = None
        for place in self.place_types.itervalues():
            if place.process_name == process_name and isinstance(place, FlowPlaceTypeHelper):
                witness = place
                break

        if (witness == None):
            raise RuntimeError("no witness for process {process}".format(process = process_name))
        return witness.gen_read_flow(env, marking_var)
    
    def gen_place_comparison(self, env, marking_var, op, left_place_name, right_place_name):
        # 1 = lt
        # 2 = le
        # 3 = eq
        # 4 = ne
        left_type  = self.get_place_type_by_name(left_place_name)
        right_type = self.get_place_type_by_name(right_place_name)
        
        if left_type.__class__ == right_type.__class__:
            return left_type.gen_place_compraison(env, marking_var, op, right_type)
        else:
            raise NotImplementedError
        

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

    def add_marking_stmt(self, env, markingset_var, marking_var):
        return cyast.Call(func=cyast.Attribute(value=cyast.Name(markingset_var.name),
                                               attr=self.add_attribute_name),
                          args=[E(marking_var.name)])

################################################################################
# opt
################################################################################

class OneSafePlaceType(coretypes.OneSafePlaceType, CythonPlaceType):
    """ Cython one safe place Type implementation.

    Somehow peculiar because encoded using two place types, one packed for
    the emptiness test and one for the contained data.
    """

    def __init__(self, place_info, marking_type, helper):
        coretypes.OneSafePlaceType.__init__(self,
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
            return E( env.type2str(type) + '()' )
        elif type.is_AnyType:
            return E("None")
        else:
            assert(False and "TO DO")

    def delete_stmt(self, env, marking_var):
        return []

    def hash_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=cyast.Name("hash"),
                          args=[place_expr])

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left,
                             ops=[cyast.Eq()],
                             comparators=[right])

    def compare_expr(self, env, left_marking_var, right_marking_var):
        left_helper_expr  = self.existence_helper_place_type.place_expr(env, left_marking_var)
        right_helper_expr = self.existence_helper_place_type.place_expr(env, right_marking_var)
        left  = self.place_expr(env, left_marking_var)
        right = self.place_expr(env, right_marking_var)

        type = self.info.type
        if type.is_Int:
            token_compare_expr=cyast.BinOp(left=left,
                                           op=Sub(),
                                           right=right)
        elif type.is_UserType or type.is_AnyType:
            token_compare_expr=cyast.Call(func=cyast.Name(from_neco_lib("__neco_compare__")),
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


    def not_empty_expr(self, env, marking_var):
        return self.existence_helper_place_type.gen_get_place(env, marking_var = marking_var)

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt(self, env, token_expr, compiled_token, marking_var):
        return self.existence_helper_place_type.remove_token_stmt(env,
                                                                  token_expr = token_expr,
                                                                  compiled_token = compiled_token,
                                                                  marking_var = marking_var )

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        place_expr = self.place_expr(env, marking_var) #self.existence_helper_place_type.place_expr(env, marking_name)
        return [ cyast.Assign(targets=[place_expr],
                              value=compiled_token),
                 self.existence_helper_place_type.add_token_stmt(env,
                                                                 token_expr = token_expr,
                                                                 compiled_token = compiled_token,
                                                                 marking_var = marking_var) ]

    def token_expr(self, env, token):
        return E(repr(token))

    def light_copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def dump_expr(self, env, marking_var):
        helper_expr = self.existence_helper_place_type.place_expr(env, marking_var)
        place_expr = self.place_expr(env, marking_var)
        return cyast.IfExp(test=helper_expr,
                           body=cyast.BinOp(left = cyast.Str('['),
                                            op = cyast.Add(),
                                            right = cyast.BinOp(left = cyast.Call(func=cyast.Name('dump'),
                                                                                  args=[place_expr]),
                                                                op = cyast.Add(),
                                                                right = cyast.Str(']')
                                                                )
                                            ),
                           orelse=cyast.Str('[]'))

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body):
        helper_expr = self.existence_helper_place_type.place_expr(checker_env, marking_var)
        place_expr = self.place_expr(checker_env, marking_var)
        return cyast.If(test=helper_expr,
                        body=[cyast.Assign(targets=[cyast.Name(loop_var.name)],
                                           value=place_expr),
                              body],
                        orelse=[])
        
    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_type = env.marking_type.get_place_type_by_name(self.info.name)
        getnode = cyast.Assign(targets=[cyast.Name(token_var.name)],
                               value=place_type.place_expr(env = env,
                                                           marking_var = marking_var)
                               )
        ifnode = Builder.If(test = place_type.not_empty_expr(env, marking_var = marking_var),
                            body = [ getnode, compiled_body ])
        return [ to_ast(ifnode) ]

################################################################################

class BTPlaceType(coretypes.BTPlaceType, CythonPlaceType):
    """ Python black token place type implementation.

    @attention: Using this place type without the BTTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type):
        coretypes.BTPlaceType.__init__(self,
                                     place_info=place_info,
                                     marking_type=marking_type,
                                     type=TypeInfo.Short,
                                     token_type=TypeInfo.Short)
        self.info = place_info
        self.marking_type = marking_type

    def delete_stmt(self, env, marking_var):
        return []

    def hash_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left,
                             ops=[cyast.Eq()],
                             comparators=[right])

    def compare_expr(self, env, left_marking_var, right_marking_var):
        left  = self.place_expr(env, left_marking_var)
        right = self.place_expr(env, right_marking_var)
        return cyast.BinOp(left=left,
                           op=cyast.Sub(),
                           right=right)

    def new_place_expr(self, env):
        return cyast.Num(0)

    def not_empty_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def dump_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)

        return cyast.BinOp(left = cyast.Str('['),
                           op = cyast.Add(),
                           right = cyast.BinOp(left = cyast.Call(func=E("', '.join"),
                                                                 args=[cyast.BinOp(left=cyast.List([cyast.Str('dot')]),
                                                                                   op=cyast.Mult(),
                                                                                   right=place_expr)]),
                                               op = cyast.Add(),
                                               right = cyast.Str(']')
                                               )
                           )

    def iterable_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=cyast.Name('range'),
                          args=[ cyast.Num(0), place_expr ])

    def remove_token_stmt( self, env, token_expr, compiled_token, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.AugAssign(target=place_expr,
                               op=cyast.Sub(),
                               value=cyast.Num(1))

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return cyast.AugAssign(target=place_expr,
                               op=cyast.Add(),
                               value=cyast.Num(1))

    def copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def light_copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def token_expr(self, env, token):
        return E("dot")

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body):
        return cyast.If(test=self.not_empty_expr(checker_env, marking_var),
                        body=[cyast.Assign(targets=[cyast.Name(loop_var.name)],
                                           value=E("dot")),
                              body],
                        orelse=[])
        
    def card_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)
    
    def multiset_expr(self, env, marking_var):
        return cyast.Call(func=E(env.type2str(TypeInfo.MultiSet)),
                          args=[ cyast.Dict([E('dot')], [self.place_expr(env, marking_var)])])    

    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_type = env.marking_type.get_place_type_by_name(self.info.name)
        ifnode = Builder.If(test = Builder.Compare(left = to_ast(place_type.place_expr(env = env,
                                                                                       marking_var = marking_var)),
                                                   ops = [ cyast.Gt() ],
                                                   comparators = [ cyast.Num( n = 0 ) ] ),
                            body = [ compiled_body ])
        return [ ifnode ]

################################################################################

class BTOneSafePlaceType(coretypes.BTOneSafePlaceType, CythonPlaceType):
    """ Python one safe black token place type.

    Using this place type without the BTOneSafeTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type):
        self.info = place_info
        self.marking_type = marking_type

    def new_place_expr(self, env):
        return E("0")

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt( self, env, token_expr, compiled_token, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return E(place_expr).assign("0")

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return Builder.LValue(place_expr).assign("1")

    def copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def token_expr(self, env, token):
        return E("dot")

    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_type = env.marking_type.get_place_type_by_name(self.info.name)
        ifnode = Builder.If(test = place_type.place_expr(env = env,
                                                         marking_var = marking_var),
                            body = compiled_body )
        return [ ifnode ]

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

    def pack_expr(self, env, marking_var):
        return env.marking_type.gen_get_pack(env = env,
                                             marking_var = marking_var,
                                             pack = self)

    def gen_init_value(self, env):
        return E("0x0")

    def gen_get_place(self, env, marking_var, place_type):
        offset = self._offset_of( place_type )
        return E(self.marking_type.gen_get_pack(env, marking_var, self)).add(E(repr(offset)))

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

    def remove(self, env, place_type, marking_var):
        offset = self._offset_of(place_type)
        mask = (offset) # forces to 8 bits

        pack_expr = self.pack_expr(env, marking_var)
        return E(pack_expr).xor_assign(E(mask))


    def add(self, env, place_type, marking_var):
        offset = self._offset_of(place_type)

        mask = offset
        pack_expr = self.pack_expr(env, marking_var)
        return E(pack_expr).or_assign(E(mask))

    def copy_expr(self, env, marking_var):
        return env.marking_type.gen_get_pack(env = env,
                                             marking_var = marking_var,
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
    def iterable_expr(self, env, marking_var): pass

    def gen_get_place(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def remove_token_stmt( self, env, token_expr, compiled_token, marking_var):
        return self.pack.gen_remove_bit(env, marking_var, self)

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        return self.pack.gen_set_bit(env, marking_var, self)

    def copy_expr(self, env, marking_var):
        return self.pack.copy_expr(env, marking_var)

    def token_expr(self, env, token):
        return E(1)

    def dump_expr(self, env, marking_var):
        return cyast.IfExp(test=self.gen_get_place(env, marking_var),
                           body=cyast.Str('[dot]'),
                           orelse=cyast.Str('[]'))

    def not_empty_expr(self, env, marking_var):
        return self.gen_get_place(env, marking_var)

    def check_helper_expr(self, env, marking_var):
        return cyast.Call(func=E("BtPlaceTypeHelper"),
                          args=[cyast.IfExp(test=self.gen_get_place(env, marking_var),
                                            body=cyast.Num(1),
                                            orelse=cyast.Num(0))])

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body):
        return [ cyast.Assign(targets = [cyast.Name(loop_var.name)],
                              value = cyast.IfExp(test=self.gen_get_place(checker_env, marking_var),
                                                  body=E('dot'),
                                                  orelse=E('None'))),
                 body ]

    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_type = env.marking_type.get_place_type_by_name(self.info.name)
        ifnode = Builder.If(test = Builder.Compare(left = to_ast(place_type.place_expr(env = env,
                                                                                       marking_var = marking_var)),
                                                   ops = [ cyast.Gt() ],
                                                   comparators = [ cyast.Num( n = 0 ) ] ),
                            body = [ compiled_body ])
        return [ ifnode ]


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
    def delete_stmt(self, env, marking_var): pass

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    @should_not_be_called
    def remove_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def add_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def copy_expr(self, env, marking_var): pass

    @should_not_be_called
    def light_copy_expr(self, env, marking_var): pass

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

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        next_flow = self._places[place_info.name]
        if not current_flow:
            current_flow = self.place_expr(env, marking_var)
        else:
            current_flow = E(current_flow.name)

        mask = int(self.pack.field_compatible_mask(self.info, next_flow))
        return Builder.EqCompare(current_flow, E(mask))

    def gen_update_flow(self, env, marking_var, place_info):
        """ Get an ast representing the flow update.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        return [ self.pack.gen_set(env = env,
                                   marking_var = marking_var,
                                   place_type = self,
                                   integer = self._places[place_info.name]) ]

    def gen_read_flow(self, env, marking_var, place_type):
        return self.pack.gen_get_place(env = env,
                                       marking_var = marking_var,
                                       place_type = self)

    def dump_expr(self, env, marking_var, place_info):
        for (place_name, next_flow) in self._places.iteritems():
            if place_name == place_info.name:
                mask = int(self.pack.field_compatible_mask(self.info, next_flow))
                check =  Builder.EqCompare(self.place_expr(env, marking_var), E(mask))
                return cyast.IfExp(test=check,
                                   body=cyast.Str('[dot]'),
                                   orelse=cyast.Str('[]'))
        assert(False)

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body, place_info):
        for (place_name, next_flow) in self._places.iteritems():
            if place_name == place_info.name:
                mask = int(self.pack.field_compatible_mask(self.info, next_flow))
                check =  Builder.EqCompare(self.place_expr(checker_env, marking_var), E(mask))
                return cyast.If(test=check,
                                body=[ cyast.Assign(targets=[cyast.Name(loop_var.name)],
                                                    values=E('dot')),
                                       body ],
                                orelse=[])
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
    def delete_stmt(self, env, marking_var): pass

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    @should_not_be_called
    def remove_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def add_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def copy_expr(self, env, marking_var): pass

    @should_not_be_called
    def light_copy_expr(self, env, marking_var): pass

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        return self.flow_place_type.gen_check_flow(env, marking_var, place_info, current_flow)

        mask = int(self.pack.field_compatible_mask(self.info, next_flow))
        return Builder.EqCompare(current_flow, E(mask))

    def gen_update_flow(self, env, marking_var, place_info):
        """ Get an ast representing the flow update.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        return self.flow_place_type.gen_update_flow(env, marking_var, place_info)

    def gen_read_flow(self, env, marking_var):
        return self.flow_place_type.gen_read_flow(env=env,
                                                  marking_var=marking_var,
                                                  place_type=self)

    def dump_expr(self, env, marking_var):
        return self.flow_place_type.dump_expr(env, marking_var, self.info)

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body):
        return self.flow_place_type.enumerate_tokens(checker_env, loop_var, marking_var, body, self.info)

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

    def get_native_field(self, marking_var, index):
        return cyast.Subscript(cyast.Attribute(cyast.Name(marking_var.name),
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


    def gen_initialise(self, env, marking_var):
        l = []
        for index in range(0, self.native_field_count()):
            l.append( cyast.Assign(targets=[cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                                  attr=self.name),
                                                            slice=cyast.Index(cyast.Num(index)))],
                                   value=cyast.Num(0)) )
        return to_ast(l)

    def gen_get_place(self, env, marking_var, place_type):
        place_info = place_type.info
        offset = self._bitfield.get_field_native_offset(self._id_from_place_info(place_info))
        mask = int(~self._bitfield.get_field_mask(self._id_from_place_info(place_info)))
        return cyast.BinOp(left=cyast.Subscript(cyast.Attribute(cyast.Name(marking_var.name),
                                                                attr=self.name),
                                                slice=cyast.Index(cyast.Num(offset))),
                           op=cyast.BitAnd(),
                           right=E(mask))

    def gen_remove_bit(self, env, marking_var, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = cyast.AugAssign(target=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                         attr=self.name),
                                                   slice=cyast.Index(cyast.Num(offset))),
                            op=cyast.BitXor(),
                            value=cyast.Num(value))
        # e = E(marking_name).attr(self.name).subscript(index=offset).xor_assign(E(value))
        comment = cyast.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value,
                                                                                anw=(self._bitfield.native_width + 2),
                                                                                place=place_type.info.name))
        return [ e, comment ]

    def gen_set_bit(self, env, marking_var, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = cyast.AugAssign(target=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                         attr=self.name),
                                                   slice=cyast.Index(cyast.Num(offset))),
                            op=cyast.BitOr(),
                            value=cyast.Num(value))
        #e = E(marking_name).attr(self.name).subscript(index=str(offset)).or_assign(E(value))
        comment = Builder.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def gen_set(self, env, marking_var, place_type, integer):
        field  = self._id_from_place_info(place_type.info)
        mask   = int(self._bitfield.get_field_mask(field))
        vmask  = int(self._bitfield.get_field_compatible_mask(field, integer))
        offset = self._bitfield.get_field_native_offset(field)
        #right  = E(marking_name).attr(self.name).subscript(index=str(offset)).bit_and(E(mask)).bit_or(E(vmask))
        right  = cyast.BinOp(left=cyast.BinOp(left=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                                         attr=self.name),
                                                                   slice=cyast.Index(cyast.Num(offset))),
                                              op=cyast.BitAnd(),
                                              right=E(mask)),
                             op=cyast.BitOr(),
                             right=E(vmask))

        #e = E(marking_name).attr(self.name).subscript(index=str(offset)).assign(right)
        e = cyast.Assign(targets=[cyast.Subscript(value=cyast.Attribute(cyast.Name(marking_var.name),
                                                                        attr=self.name),
                                                  slice=cyast.Index(cyast.Num(offset)))],
                         value=right)
        comment = Builder.Comment("mask: {mask:#0{anw}b} vmask:{vmask:#0{anw}b} - place:{place}"
                                  .format(mask=mask, vmask=vmask, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def copy_expr(self, env, src_marking_var, dst_marking_var):
        l = []
        for index in range(0, self.native_field_count()):
            right = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(src_marking_var.name),
                                                          attr=self.name),
                                    slice=cyast.Index(cyast.Num(index)))
            left = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(dst_marking_var.name),
                                                         attr=self.name),
                                   slice=cyast.Index(cyast.Num(index)))
            l.append( cyast.Assign(targets=[left],
                                   value=right) )
        return l


    def gen_tests(self, left_marking_var, right_marking_var):
        """
        """
        tests = []
        for index in range(0, self.native_field_count()):
            left = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(left_marking_var.name),
                                                         attr=self.name),
                                   slice=cyast.Index(cyast.Num(index)))
            right = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(right_marking_var.name),
                                                          attr=self.name),
                                    slice=cyast.Index(cyast.Num(index)))
            tests.append( (left, right, ) )
        return tests

################################################################################
# EOF
################################################################################
