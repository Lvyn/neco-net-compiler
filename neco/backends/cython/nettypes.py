""" Cython basic net types. """

from neco.core.info import TypeInfo, PlaceInfo
from priv import cyast, placetypes
import neco.config as config
import neco.core.nettypes as coretypes
import neco.utils as utils

################################################################################

def place_type_from_info(place_info, marking):
    pi_type = place_info.type
    if pi_type.is_Int:
        return placetypes.IntPlaceType(place_info, marking_type=marking)
    elif pi_type.is_Bool:
        return placetypes.ObjectPlaceType(place_info, marking_type=marking)
    elif pi_type.is_String:
        return placetypes.ObjectPlaceType(place_info, marking_type=marking)
    elif pi_type.is_BlackToken:
        return placetypes.BTPlaceType(place_info, marking_type=marking)
    elif pi_type.is_UserType:
        return placetypes.ObjectPlaceType(place_info, marking_type=marking)
    else:
        return placetypes.ObjectPlaceType(place_info, marking_type=marking)

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
            name = self.id_provider.new(base="_packed")
            pack = placetypes.PackedPlaceTypes(name, self)
            self.id_provider.set(pack, name)
            pack = pack
        else:
            pack = None
        self._pack = pack
        
        import priv.mrkmethods
        self.add_method_generator(priv.mrkmethods.InitGenerator())
        self.add_method_generator(priv.mrkmethods.DeallocGenerator())
        self.add_method_generator(priv.mrkmethods.CopyGenerator())
        #self.add_method_generator( priv.mrkmethods.ReprGenerator() )
        self.add_method_generator(priv.mrkmethods.DumpExprGenerator())        
        self.add_method_generator(priv.mrkmethods.RichcmpGenerator())
        self.add_method_generator(priv.mrkmethods.HashGenerator())
        
        self._C_function_generators = []
        
        import priv.mrkfunctions
        self.add_C_function_generator(priv.mrkfunctions.CompareGenerator())
        #self.add_C_function_generator( priv.mrkfunctions.MarkedGenerator() )
        self.add_C_function_generator(priv.mrkfunctions.DumpGenerator())
        self.add_C_function_generator(priv.mrkfunctions.HashGenerator())
        self.add_C_function_generator(priv.mrkfunctions.CopyGenerator())
        
    def add_C_function_generator(self, generator):
        self._C_function_generators.append(generator)
        
    @property
    def C_function_generators(self):
        return self._C_function_generators
    
    def generate_C_functions(self, env):
        functions = []
        for generator in self._C_function_generators:
            functions.append(generator.generate(env))
        return functions

    def get_process_place_type(self, process_name):
        return self._process_place_types[process_name]

    def __gen_one_safe_place_type(self, place_info):
        if place_info.type.is_BlackToken:
            # register a new place type
            pt = placetypes.PackedBT1SPlaceType(place_info, self, pack=self._pack)
            self._pack.add_place(place_info, bits=1)
            self.place_types[place_info.name] = pt
        else: # 1s not BT
            new_id = self.id_provider.new('one_safe_')
            dummy = PlaceInfo.Dummy(new_id, one_safe=True)
            self.id_provider.set(dummy, new_id)

            pt = placetypes.PackedBT1SPlaceType(dummy, self, pack=self._pack)
            pt.revelant = False
            self._pack.add_place(dummy, bits=1)
            # remember place type
            self.place_types[new_id] = pt

            # create the place
            place_type = placetypes.OneSafePlaceType(place_info, self, pt)
            # remember place type
            self.place_types[place_info.name] = place_type


    def __gen_flow_control_place_type(self, place_info):
        process_name = place_info.process_name
        try:
            flow_place_type = self._process_place_types[process_name] # throws KeyError
        except KeyError:
            # flow place type does not exist: create new place type
            new_id = self.id_provider.new(base='flow_')
            dummy = PlaceInfo.Dummy(new_id,
                                    flow_control=True,
                                    process_name=place_info.process_name)
            self.id_provider.set(dummy, new_id)

            flow_place_type = placetypes.FlowPlaceType(dummy, self)
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
            self._pack.add_place(dummy, bits=needed_bits)
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
        cls = cyast.Builder.PublicClassCDef(name="Marking",
                                            bases=[cyast.E("object")],
                                            spec=cyast.type_name_spec(o="Marking", t="MarkingType"))

        ################################################################################
        # attributes
        ################################################################################

        if self._pack and self._pack.native_field_count() > 0: # at least one bit used
            name = '{name}[{count}]'.format(name=self.id_provider.get(self._pack),
                                            count=self._pack.native_field_count())
            cls.add_decl(cyast.CVar(name, type=env.type2str(self._pack.type)))

        for place_type in self.place_types.itervalues():
            if not place_type.is_packed and not place_type.is_helper:
                cls.add_decl(cyast.CVar(name=self.id_provider.get(place_type),
                                        type=env.type2str(place_type.type)))

        cls.add_method(cyast.FunctionDecl(name='copy',
                                          args=cyast.to_ast(cyast.A("self", cyast.Name(env.type2str(self.type)))),
                                          returns=cyast.Name(env.type2str(self.type)),
                                          lang=cyast.CDef()))

        return cyast.to_ast(cls)

    def generate_api(self, env):
        cls = cyast.Builder.ClassCDef(name="Marking",
                                      bases=[])

        ################################################################################
        # methods
        ################################################################################
        for method in self.generate_methods(env):
            cls.add_method(method)

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
                attributes.add("{attribute}[{offset}]".format(attribute=self.id_provider.get(self._pack),
                                                              offset=self._pack.get_field_native_offset(place_type)))
            else:
                attributes.add(self.id_provider.get(place_type))
        attribute_max = max(len(attr) for attr in attributes)

        comms = set([])
        for place_type in self.place_types.itervalues():
            if place_type.is_packed:
                attr = "{attribute}[{offset}]".format(attribute=self.id_provider.get(self._pack),
                                                      offset=self._pack.get_field_native_offset(place_type))
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
        return [cyast.to_ast(cls), self.generate_C_functions(env)]


    def gen_copy(self, env, src_marking, dst_marking, modified_places):
        """

        @param modified_places:
        @type modified_places: C{}
        """
        nodes = []
        nodes.append(cyast.E(dst_marking.name + " = Marking()"))

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
            nodes.append(self._pack.copy_expr(env, src_marking_var=src_marking, dst_marking_var=dst_marking))

        for place_type in copy_places:
            if place_type.is_helper or place_type.is_packed:
                pass
            else:
                place_expr = self.gen_get_place(env,
                                                place_name=place_type.info.name,
                                                marking_var=dst_marking)

                nodes.append(cyast.Assign(targets=[place_expr],
                                          value=place_type.copy_expr(env, marking_var=src_marking))
                             )


        for place_type in assign_places:
            if place_type.is_helper or place_type.is_packed:
                pass
            else:
                place_expr = self.gen_get_place(env,
                                                place_name=place_type.info.name,
                                                marking_var=dst_marking)
                nodes.append(cyast.Assign(targets=[place_expr],
                                          value=place_type.light_copy_expr(env, marking_var=src_marking))
                             )

        return cyast.to_ast(nodes)

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
        return cyast.E(marking_var.name).attr(self.id_provider.get(pack))

    ################################################################################
    # Flow elimination
    ################################################################################

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        place_type = self.get_place_type_by_name(place_info.name)
        assert(isinstance(place_type, placetypes.FlowPlaceTypeHelper))
        return place_type.gen_check_flow(env=env,
                                         marking_var=marking_var,
                                         place_info=place_info,
                                         current_flow=current_flow)

    def gen_update_flow(self, env, marking_var, place_info):
        place_type = self.get_place_type_by_name(place_info.name)
        assert(isinstance(place_type, placetypes.FlowPlaceTypeHelper))
        return place_type.gen_update_flow(env=env,
                                          marking_var=marking_var,
                                          place_info=place_info)

    def gen_read_flow(self, env, marking_var, process_name):
        witness = None
        for place in self.place_types.itervalues():
            if place.process_name == process_name and isinstance(place, placetypes.FlowPlaceTypeHelper):
                witness = place
                break

        if (witness == None):
            raise RuntimeError("no witness for process {process}".format(process=process_name))
        return witness.gen_read_flow(env, marking_var)
    
    def gen_place_comparison(self, env, marking_var, op, left_place_name, right_place_name):
        # 1 = lt
        # 2 = le
        # 3 = eq
        # 4 = ne
        left_type = self.get_place_type_by_name(left_place_name)
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
                          args=[cyast.E(marking_var.name)])

################################################################################
# EOF
################################################################################
