""" Python basic net types. """

import cyast, math
import neco.utils as utils
from neco.utils import Factory, should_not_be_called, todo
import neco.core.nettypes as coretypes
from neco.core.nettypes import provides_by_index_access, provides_by_index_deletion
from neco.core.info import *
from neco.opt import onesafe
from astutils import Builder, E, A, to_ast, stmt
from maskbitfield import MaskBitfield

################################################################################
# Registered classes are used as cython classes (cdef)
################################################################################

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

    @param t: type info to translate
    @type t: C{TypeInfo}
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
register_cython_type(TypeInfo.IntPlace, 'net.int_place_type*')
register_cython_type(TypeInfo.MultiSet, 'MultiSet')
register_cython_type(TypeInfo.UnsignedChar, 'unsigned char')
register_cython_type(TypeInfo.UnsignedInt, 'unsigned int')

################################################################################



class CythonPlaceType(object):
    """ Base class for cython place types. """

    _packed_place_ = False

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
        """ C{True} is place is packed, C{False} otherwise """
        return self.__class__._packed_place_

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

################################################################################

class ObjectPlaceType(coretypes.ObjectPlaceType, CythonPlaceType):
    """ Python implementation of fallback place type. """

    def __init__(self, place_info, marking_type):
        coretypes.ObjectPlaceType.__init__(self,
                                           place_info = place_info,
                                           marking_type = marking_type,
                                           type = TypeInfo.MultiSet,
                                           token_type = place_info.type)

    def gen_new_place(self, env):
        return E("MultiSet()")

    def gen_delete(self, env, marking_name):
        return []

    def gen_hash(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).attr("hash").call()

    def gen_eq(self, env, left, right):
        return Builder.EqCompare(left, right)

    def gen_iterable(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_remove_token_function_call(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E(place_expr).attr('remove').call([ compiled_token ]))

    def gen_add_token_function_call(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E(place_expr).attr('add').call([ compiled_token ]))

    def gen_build_token(self, env, value):
        return E(repr(value))

    def gen_copy(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).attr("copy").call()

    def gen_light_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_clear_function_call(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign("MultiSet()")

    def gen_not_empty_function_call(self, env, marking_type, marking_name):
        return self.place_expr(env, marking_name)

    def gen_build_token(self, env, token):
        return E(repr(token))

    def add_multiset(self, env, multiset, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E(place_expr).attr('update').call([ multiset ]))

    def add_items(self, env, multiset, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E(place_expr).attr('add_items').call([multiset]))

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

    def gen_new_place(self, env):
        return E("net.int_place_type_new()")

    def gen_delete(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E("net.int_place_type_free").call([ place_expr ]))

    def gen_hash(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E("net.int_place_type_hash").call([ place_expr ])

    def gen_eq(self, env, left, right):
        return E("net.int_place_type_eq").call([ left, right ])

    @should_not_be_called
    def gen_iterable(self, env, marking_type, marking_name): pass

    def gen_remove_token_function_call(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E("net.int_place_type_rem_by_index").call([ place_expr, compiled_token ]))

    def gen_remove_by_index_function_call(self, env, index, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E("net.int_place_type_rem_by_index").call([ place_expr, E(index) ]))

    def gen_add_token_function_call(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return stmt(E("net.int_place_type_add").call([ place_expr, compiled_token ]))

    def gen_build_token(self, env, value):
        return E(repr(value))

    def gen_copy(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E("net.int_place_type_copy").call([ place_expr ])

    def gen_light_copy(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E("net.int_place_type_light_copy").call([ place_expr ])

    def gen_get_size_function_call(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E("net.int_place_type_size").call([ place_expr ])

    def gen_get_token_function_call(self, env, marking_name, index):
        place_expr = self.place_expr(env, marking_name)
        return E("net.int_place_type_get").call([ place_expr, E(index) ])

    def gen_clear_function_call(self, env, marking_type, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E("net.int_place_type_clear").call([ place_expr ])

    def gen_build_token(self, env, token):
        return E(repr(token))

    @todo
    def gen_not_empty_function_call(self, env, marking_type, marking_name): pass

    @todo
    def add_multiset(self, env, multiset, marking_type, marking_name): pass

    @todo
    def add_items(self, env, multiset, marking_type, marking_name): pass


################################################################################

class StaticMarkingType(coretypes.MarkingType):
    """ Python static marking type implementation, i.e., places as class attributes. . """

    def __init__(self):
        coretypes.MarkingType.__init__(self, "Marking")

        # id provider for class attributes
        self.id_provider = utils.NameProvider()
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
            name = self.id_provider.new(base = "packed")
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
            helper = PackedBT1SPlaceTypeHelper( place_info, self, pack = self._pack )
            self._pack.add_place( place_info, bits = 1 )
            # use helper as place type
            self.place_types[place_info.name] = helper
        else: # 1s not BT
            # create a helper
            new_id = self.id_provider.new('one_safe_')
            dummy = PlaceInfo.Dummy( new_id, one_safe = True )
            self.id_provider.set(dummy, new_id)

            helper = PackedBT1SPlaceTypeHelper( dummy, self, pack = self._pack )
            self._pack.add_place( dummy, bits = 1 )
            # remember helper
            self.place_types[new_id] = helper

            # create the place
            place_type = OneSafePlaceType(place_info, self, helper)
            # remember place type
            self.place_types[place_info.name] = place_type


    def __gen_flow_control_place_type(self, place_info):
        process_name = place_info.process_name
        try:
            # place type already exists
            place_type = self._process_place_types[process_name]
            self.place_types[place_info.name] = place_type
        except KeyError:
            # place type does not exist: create new place type

            new_id = self.id_provider.new(base = 'flow_')
            dummy = PlaceInfo.Dummy(new_id,
                                    flow_control = True,
                                    process_name = place_info.process_name)
            self.id_provider.set(dummy, new_id)

            helper = FlowPlaceTypeHelper(dummy, self)
            helper.add_place(place_info)
            for pi in self.flow_control_places:
                if pi.process_name == process_name:
                   helper.add_place(pi)
            needed_bits = helper.needed_bits

            self._pack.add_place(dummy, bits = needed_bits)
            helper.pack = self._pack
            self.place_types[place_info.name] = helper
            self._process_place_types[process_name] = helper

    def __gen_place_type(self, place_info, select_type):
        place_name = place_info.name
        place_type = placetype_factory.new(select_type(place_info),
                                           place_info,
                                           marking_type = self)

        if self.place_types.has_key(place_name):
            raise "place exists"
        else:
            self.place_types[place_name] = place_type

    def gen_types(self, select_type):
        for place_info in self.flow_control_places:
            if self.packing_enabled:
                self.__gen_flow_control_place_type(place_info)
            else:
                self.__gen_place_type(place_info, select_type)

        for place_info in self.one_safe_places:
            if self.packing_enabled and place_info.one_safe:
                self.__gen_one_safe_place_type(place_info)
            else:
                self.__gen_place_type(place_info, select_type)

        for place_info in self.places:
            self.__gen_place_type(place_info, select_type)

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

    def gen_alloc_marking_function_call(self, env):
        return E( self.type_name + "(alloc=True)")

    def _gen_dealloc(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = "__dealloc__",
                                   args = A("self", type="Marking") )

        for place_type in self.place_types.itervalues():
            if not place_type.is_packed:
                builder.emit(place_type.gen_delete(env = env,
                                                   marking_name = "self"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_init(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = "__cinit__",
                                   args = A("self").param("alloc", default = "False"))

        builder.begin_If( E('alloc') )

        if self._pack:
            builder.emit( self._pack.gen_initialise(env, "self") )

        # init places
        for place_type in self.place_types.itervalues():
            if place_type.is_packed:
                pass
            else:
                attr = self.id_provider.get(place_type)
                builder.emit( E('self').attr(attr).assign( place_type.gen_new_place(env) ) )
        builder.end_If()
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_copy(self, env):
        builder = Builder()
        builder.begin_FunctionCDef( name = "copy",
                                    args = A("self"),
                                    returns = E(type2str( self.type )),
                                    decl = [ Builder.CVar( name = 'm', type = 'Marking' ) ])



        builder.emit( E('m = Marking()') )

        # copy packs
        if self._pack:
            builder.emit( self._pack.gen_copy(env, src_marking_name = "self", dst_marking_name = "m") )

        # copy places
        for place_type in self.place_types.itervalues():
            if not place_type.is_packed:
                builder.emit( E('m').attr(self.id_provider.get(place_type)).assign( place_type.gen_copy(env = env, marking_name = 'self') ) )
        builder.emit_Return(E("m"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_compare_aux(self, builder, tests):
        try:
            test = tests.pop()
            # l - r == 0 ?:
            builder.begin_If(test.eq(E('0')))
            self._gen_C_compare_aux(builder, tests)
            # l - r < 0 ?:
            builder.begin_Elif(test.lt(E('0')))
            builder.emit_Return(E('-1'))
            builder.end_If()
            # else l - r > 0:
            builder.begin_Else()
            builder.emit_Return(E('1'))
            builder.end_If()
        except IndexError:
            builder.emit_Return(E('0'))

    def _gen_C_compare(self, env):

        builder = Builder()
        left_marking_name  = "self"
        right_marking_name = "other"
        builder.begin_FunctionCDef( name = "neco_marking_compare",
                                    args = (A("self", type = self.type_name)
                                            .param(right_marking_name, type = self.type_name)),
                                    returns = E("int"))

        # TODO: Order places

        i = 0
        tests = []
        if self._pack:
            if self.packing_enabled:
                gen = self._pack.gen_tests(left_marking_name=left_marking_name,
                                           right_marking_name=right_marking_name)
                for l, r in gen:
                    tests.append(E(l).sub(E(r)))

        for place_type in self.place_types.itervalues():
            if place_type.is_packed:
                continue
            else:
                id = self.id_provider.get(place_type)
                tests.append(place_type.gen_compare(env, left=E(left_marking_name + '.' + id), right=E(right_marking_name + '.' + id)))

        tests.reverse()
        self._gen_C_compare_aux(builder, tests)
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_richcmp(self, env):
        builder = Builder()
        left_marking_name = "self"
        right_marking_name = "other"
        op_name = "op"
        builder.begin_FunctionDef( name = "__richcmp__",
                                   args = (A("self", type = self.type_name)
                                           .param(right_marking_name, type = self.type_name)
                                           .param(op_name, type = "int")) )
        builder.emit_Return(E("neco_marking_compare").call([E(left_marking_name), E(right_marking_name)]).eq(E("0")))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_hash(self, env):
        builder = Builder()
        builder.begin_FunctionDef( name = "__hash__",
                                   args = A("self", type = "Marking"),
                                   decl = [ Builder.CVar( name = 'h', type = 'int' ) ])

        builder.emit( E("h = 0xDEADDAD") )
        mult = 0xBADBEEF
        i = 0

        if self._pack:
            for index in range(0, self._pack.native_field_count()):
                native_field = self._pack.get_native_field('self', index)
                builder.emit( E('h').assign(E('h').xor(native_field).mult(E(mult))) )
                mult += (82520L + i + i)
                i += 1

        for place_type in self.place_types.itervalues():
            if not place_type.is_packed:
                if place_type.type.is_Int or place_type.type.is_Short or place_type.type.is_Char:
                    native_place = self.id_provider.get(place_type)
                    builder.emit( E('h').assign(E('h').xor(E('self').attr(native_place)).mult(E(mult))) )
                else:
                    place_hash = place_type.gen_hash(env, marking_name = "self")
                    builder.emit( E('h').assign(E('h').xor( place_hash ).mult(E(mult))) )
                mult += (82521L * i + i)
                i += 1

        builder.emit_Return(E("h"))
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_hash(self, env):
        builder = Builder()
        builder.begin_FunctionCDef( name = "neco_marking_hash",
                                    args = A("self", type = "Marking"),
                                    returns = E("int"))
        builder.emit_Return(E("self").attr('__hash__').call())
        builder.end_FunctionDef()
        return to_ast(builder)

    def _gen_C_copy(self, env):
        builder = Builder()
        builder.begin_FunctionCDef( name = "neco_marking_copy",
                                    args = A("self", type = "Marking"),
                                    returns = E("Marking"))
        builder.emit_Return(E("self").attr('copy').call())
        builder.end_FunctionDef()
        return to_ast(builder)

    def gen_free_marking_function_call(self, env, marking_name):
        pass

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
            tmp = ',\n       ' if i > 0 else ''
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

    def gen_api(self, env):
        cls = Builder.PublicClassCDef(name = "Marking",
                                      bases = [ E("object") ],
                                      spec = cyast.type_name_spec(o="Marking", t="MarkingType"))

        ################################################################################
        # methods
        ################################################################################

        cls.add_method( self._gen_init(env) )
        cls.add_method( self._gen_dealloc(env) )
        # cls.add_method( self._gen_repr(env) )
        cls.add_method( self._gen_richcmp(env) )
        cls.add_method( self._gen_hash(env) )
        cls.add_method( self._gen_copy(env) )

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
            cls.add_decl( Builder.CVar(name).type(type2str(self._pack.type)) )

        for place_type in self.place_types.itervalues():
            if not place_type.is_packed:
                cls.add_decl( Builder.CVar(self.id_provider.get(place_type)).type(type2str(place_type.type)) )

        capi = []
        capi.append( self._gen_C_hash(env) )
        capi.append( self._gen_C_copy(env) )
        capi.append( self._gen_C_compare(env) )

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
            nodes.append( self._pack.gen_copy(env, src_marking_name = src_marking_name, dst_marking_name = dst_marking_name) )

        for place_type in copy_places:
            place_expr = self.gen_get_place(env,
                                            place_name = place_type.info.name,
                                            marking_name = dst_marking_name)
            nodes.append( E(place_expr).assign(place_type.gen_copy(env, marking_name = src_marking_name)) )


        for place_type in assign_places:
            place_expr = self.gen_get_place(env,
                                            place_name = place_type.info.name,
                                            marking_name = dst_marking_name)
            nodes.append( E(place_expr).assign(place_type.gen_light_copy(env, marking_name = src_marking_name)) )

        return to_ast(nodes)

    def gen_copy_marking_function_call(self, env, marking_name):
        return E(marking_name).attr('copy').call()

    def gen_get_place(self, env, marking_name, place_name):
        place_type = self.get_place_type_by_name(place_name)

        if place_type.is_packed:
            return place_type.pack.gen_get_place(env, marking_name, place_type)
        else:
            return E(marking_name).attr(self.id_provider.get(place_type))

    def gen_get_place_size(self, env, marking_name, place_name):
        place_type = self.get_place_type_by_name(place_name)

        assert (not place_type.is_packed)
        return place_type.gen_get_size_function_call(env = env, marking_name = marking_name)

    def gen_get_token(self, env, marking_name, place_name, index):
        place_type = self.get_place_type_by_name(place_name)

        assert (not place_type.is_packed)
        return place_type.gen_get_token_function_call(env = env,
                                                      marking_name = marking_name,
                                                      index = index)

    def gen_get_pack(self, env, marking_name, pack):
        return E(marking_name).attr(self.id_provider.get(pack))

    def gen_remove_token_function_call(self, env, token, marking_name, place_name):
        place_type = self.get_place_type_by_name(place_name)
        return place_type.gen_remove_token_function_call(env = env,
                                                         compiled_token = token,
                                                         marking_name = marking_name)

    def gen_remove_by_index_function_call(self, env, token, marking_name, place_name, index):
        place_type = self.get_place_type_by_name(place_name)
        return place_type.gen_remove_by_index_function_call(env = env,
                                                            index = index,
                                                            marking_name = marking_name)

    def gen_add_token_function_call(self, env, token, marking_name, place_name):
        place_type = self.get_place_type_by_name(place_name)
        return place_type.gen_add_token_function_call(env = env,
                                                      compiled_token = token,
                                                      marking_name = marking_name)

    def gen_iterable_place(self, env, marking_name, place_name):
        return self.get_place_type_by_name(place_name).gen_iterable(env, marking_name)

    def gen_build_token(self, env, place_name, value):
        place_type = self.get_place_type_by_name(place_name)
        return place_type.gen_build_token(env, value)

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

    def gen_new_marking_set(self, env):
        return E("set").call()

    def gen_add_marking_function_call(self, env, markingset_name, marking_name):
        return E(markingset_name).attr(self.add_attribute_name).call([E(marking_name)])

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

    def gen_new_place(self, env):
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

    def gen_delete(self, env, marking_name):
        return []

    def gen_hash(self, env, marking_type, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E("hash").call([place_expr])

    def gen_eq(self, env, left, right):
        return Builder.EqCompare(left, right)

    def gen_not_empty_function_call(self, env, marking_name):
        return self.existence_helper_place_type.gen_get_place(env, marking_name = marking_name)

    @should_not_be_called
    def gen_iterable(self, env, marking_type, marking_name): pass

    def gen_remove_token_function_call(self, env, compiled_token, marking_name):
        return self.existence_helper_place_type.gen_remove_token_function_call(env, None, marking_name )

    def gen_add_token_function_call(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return [ E(place_expr).assign(compiled_token),
                 self.existence_helper_place_type.gen_add_token_function_call(env, None, marking_name) ]

    def gen_build_token(self, env, value):
        return E(repr(value))

    def gen_light_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

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

    def gen_delete(self, env, marking_name):
        return []

    def gen_hash(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_eq(self, env, left, right):
        return Builder.EqCompare(left, right)

    def gen_compare(self, env, left, right):
        return E(left).sub(E(right))

    def gen_new_place(self, env):
        return E("0")

    def gen_iterable(self, env, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E("range").call([ E(0), place_expr ])

    def gen_remove_token_function_call( self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).sub_assign(E(1))

    def gen_add_token_function_call(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).add_assign(E(1))

    def gen_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_light_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_build_token(self, env, value):
        return E("dot")

################################################################################

class BTOneSafePlaceType(onesafe.BTOneSafePlaceType, CythonPlaceType):
    """ Python one safe black token place type.

    Using this place type without the BTOneSafeTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type):
        self.info = place_info
        self.marking_type = marking_type

    def gen_new_place(self, env):
        return E("0")

    @should_not_be_called
    def gen_iterable(self, env, marking_type, marking_name): pass

    def gen_remove_token_function_call( self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return E(place_expr).assign("0")

    def gen_add_token_function_call(self, env, compiled_token, marking_name):
        place_expr = self.place_expr(env, marking_name)
        return Builder.LValut(place_expr).assign("1")

    def gen_copy(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_build_token(self, env, value):
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
        return E("0x00")

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

    def gen_copy(self, env, marking_name):
        return marking_type.gen_get_pack(env = env,
                                         marking_name = marking_name,
                                         pack = self)

@packed_place
class PackedBT1SPlaceTypeHelper(coretypes.PlaceType, CythonPlaceType):
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
    def gen_new_place(self, env): pass

    @should_not_be_called
    def gen_iterable(self, env, marking_type, marking_name): pass

    def gen_get_place(self, env, marking_name):
        return self.place_expr(env, marking_name)

    def gen_remove_token_function_call( self, env, compiled_token, marking_name):
        return self.pack.gen_remove_bit(env, marking_name, self)

    def gen_add_token_function_call(self, env, compiled_token, marking_name):
        return self.pack.gen_set_bit(env, marking_name, self)

    def gen_copy(self, env, marking_name):
        return self.pack.gen_copy(env, marking_name)

    def gen_build_token(self, env, value):
        return E(1)

################################################################################
#
################################################################################

@packed_place
class FlowPlaceTypeHelper(coretypes.PlaceType, CythonPlaceType):

    def __init__(self, place_info, marking_type):
        self.pack = None
        self._counter = 0
        self._places = {}
        coretypes.PlaceType.__init__(self,
                                     place_info = place_info,
                                     marking_type = marking_type,
                                     type = TypeInfo.UnsignedInt,
                                     token_type = TypeInfo.UnsignedInt)

    @property
    def max(self):
        assert( self._counter != 0 )
        return self._counter - 1

    @property
    def needed_bits(self):
        return int(math.ceil(math.log(self._counter, 2)))

    @should_not_be_called
    def gen_new_place(self, env): pass

    @should_not_be_called
    def gen_delete(self, env, marking_name): pass

    @should_not_be_called
    def gen_iterable(self, env, marking_name): pass

    @should_not_be_called
    def gen_remove_token_function_call(self, *args, **kwargs): pass

    @should_not_be_called
    def gen_add_token_function_call(self, *args, **kwargs): pass

    @should_not_be_called
    def gen_copy(self, env, marking_name): pass

    @should_not_be_called
    def gen_light_copy(self, env, marking_name): pass

    def add_place(self, place_info):
        """ Adds a flow control place.

        @param place_info: flow control place to be added
        @type place_info: C{PlaceInfo}
        """
        assert(place_info.flow_control)
        if self._places.has_key(place_info.name):
            return
        self._places[place_info.name] = self._counter
        self._counter += 1

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

    def gen_read_flow(self, env, marking_name):
        return self.pack.gen_get_place(env = env,
                                       marking_name = marking_name,
                                       place_type = self)

################################################################################

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
        return E(marking_name).attr(self.name).subscript(index=index)


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
            l.append(E(marking_name).attr(self.name).subscript(index = str(index)).assign(0))
        return to_ast(l)

    def gen_get_place(self, env, marking_name, place_type):
        place_info = place_type.info
        offset = self._bitfield.get_field_native_offset(self._id_from_place_info(place_info))
        mask = int(~self._bitfield.get_field_mask(self._id_from_place_info(place_info)))
        return E(marking_name).attr(self.name).subscript(index=str(offset)).bit_and(E(mask))

    def gen_remove_bit(self, env, marking_name, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = E(marking_name).attr(self.name).subscript(index=offset).xor_assign(E(value))
        comment = Builder.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value,
                                                                                  anw=(self._bitfield.native_width + 2),
                                                                                  place=place_type.info.name))
        return [ e, comment ]

    def gen_set_bit(self, env, marking_name, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = E(marking_name).attr(self.name).subscript(index=str(offset)).or_assign(E(value))
        comment = Builder.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def gen_set(self, env, marking_name, place_type, integer):
        field  = self._id_from_place_info(place_type.info)
        mask   = int(self._bitfield.get_field_mask(field))
        vmask  = int(self._bitfield.get_field_compatible_mask(field, integer))
        offset = self._bitfield.get_field_native_offset(field)
        right  = E(marking_name).attr(self.name).subscript(index=str(offset)).bit_and(E(mask)).bit_or(E(vmask))
        e = E(marking_name).attr(self.name).subscript(index=str(offset)).assign(right)
        comment = Builder.Comment("mask: {mask:#0{anw}b} vmask:{vmask:#0{anw}b} - place:{place}"
                                  .format(mask=mask, vmask=vmask, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def gen_copy(self, env, src_marking_name, dst_marking_name):
        l = []
        for index in range(0, self.native_field_count()):
            right = E(src_marking_name).attr(self.name).subscript(index=str(index))
            e = E(dst_marking_name).attr(self.name).subscript(index=str(index)).assign(right)
            l.append( e )

        return l


    def gen_tests(self, left_marking_name, right_marking_name):
        """
        """
        tests = []
        for index in range(0, self.native_field_count()):
            left = E(left_marking_name).attr(self.name).subscript(index=str(index))
            right = E(right_marking_name).attr(self.name).subscript(index=str(index))
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
