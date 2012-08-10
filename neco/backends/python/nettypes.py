""" Python basic net types. """

from neco.core.info import TypeInfo, PlaceInfo
from priv import pyast
import neco.core.nettypes as coretypes
import neco.utils as utils
import priv.mrkmethods
import priv.mrkpidmethods
import priv.placetypes

################################################################################

def type2str(type_info):
    """ Type to string translation.

    @param type: type to translate
    @type type: C{TypeInfo}
    """
    if type_info.is_UserType:
        if type_info.is_BlackToken:
            return "BlackToken"
        elif type_info.is_Bool:
            return "bool"
        elif type_info.is_Int:
            return "int"
        elif type_info.is_String:
            return "str"
        else:
            return str(type_info)
    elif type_info.is_TupleType:
        return "tuple"
    else:
        return "object"

TypeInfo.register_type("Multiset")

class Field(object):
    
    def __init__(self, name, field_type):
        self.name = name
        self.type = field_type

    def access_from(self, marking_var):
        return "{}.{}".format(marking_var.name, self.name) 
    
class StaticMarkingType(coretypes.MarkingType):
    """ Python marking type implementation, places as class attributes. """

    def __init__(self, config):
        coretypes.MarkingType.__init__(self,
                                       TypeInfo.register_type('Marking'),
                                       TypeInfo.register_type('set'))
        self.config = config
        self.id_provider = utils.NameProvider()
        self._process_place_types = {}
        
        self.fields = set()

        self.add_method_generator(priv.mrkmethods.InitGenerator())
        self.add_method_generator(priv.mrkmethods.CopyGenerator())
        self.add_method_generator(priv.mrkmethods.ReprGenerator())
        self.add_method_generator(priv.mrkmethods.DumpGenerator())
        
        if self.config.normalize_pids:
            self.add_method_generator(priv.mrkpidmethods.EqGenerator())
            self.add_method_generator(priv.mrkpidmethods.HashGenerator())
            self.add_method_generator(priv.mrkpidmethods.UpdatePidsGenerator())
            self.add_method_generator(priv.mrkpidmethods.NormalizePidsGenerator())
        else:
            self.add_method_generator(priv.mrkmethods.EqGenerator())
            self.add_method_generator(priv.mrkmethods.HashGenerator())

    def create_field(self, obj, field_type):
        name = self.id_provider.get(obj)
        field = Field(name, field_type)
        self.fields.add( field )
        return field

    def __str__(self):
        s = []
        s.append('Marking:')
        for name, place_type in self.place_types.iteritems():
            s.append('{} : {}'.format(name, place_type.__class__))
        s.append('End')
        return '\n'.join(s)

    def __add_to_process_place_type(self, place_info):
        try:
            self._process_place_types[place_info.process_name].add_place(place_info)
        except KeyError:
            new_id = place_info.process_name
            place_type = priv.placetypes.FlowPlaceType(place_info=PlaceInfo.Dummy(new_id,
                                                                                  process_name=place_info.process_name),
                                                       marking_type=self)
            self.place_types[place_info.process_name] = place_type
            place_type.add_place(place_info)
            self._process_place_types[place_info.process_name] = place_type

    def __create_one_safe_place_type(self, place_info):
        if self.optimize:
            if place_info.type.is_BlackToken:
                return priv.placetypes.BTOneSafePlaceType(place_info, marking_type=self, packed=self.bit_packing)
            else:
                return priv.placetypes.OneSafePlaceType(place_info, marking_type=self, packed=self.bit_packing)
        else:
            return priv.placetypes.ObjectPlaceType(place_info, marking_type=self)

    def gen_types(self):
        """ Build place types using C{select_type} predicate.
        """ 
        for place_info in self.flow_control_places:
            self.__add_to_process_place_type(place_info)
            
        for place_info in self.one_safe_places:
            assert(place_info.one_safe)            
            place_name = place_info.name
            place_type = self.__create_one_safe_place_type(place_info)
            if self.place_types.has_key(place_name):
                raise RuntimeError("{name} place exists".format(name=place_name))
            else:
                self.place_types[place_name] = place_type

        for place_info in self.places:
            place_name = place_info.name

            if place_info.type.is_BlackToken:
                place_type = priv.placetypes.BTPlaceType(place_info, marking_type=self)
            else:
                place_type = priv.placetypes.ObjectPlaceType(place_info, marking_type=self)

            if self.place_types.has_key(place_name):
                raise RuntimeError("{name} place exists".format(name=place_name))
            else:
                self.place_types[place_name] = place_type

    def new_marking_expr(self, env, *args):
        return pyast.E("Marking()")

    def normalize_marking_call(self, env, marking_var):
        return pyast.stmt(pyast.Call(func=pyast.Attribute(value=pyast.Name(id=marking_var.name),
                                                          attr='normalize_pids'),
                                     args=[]))

    def generate_api(self, env):
        cls = pyast.ClassDef('Marking', bases=[pyast.Name(id='object')])

        elts = []
        names = []
        for field in self.fields: # self.place_types.iteritems():
            name = field.name
            elts.append(pyast.Str(name))
            names.append(name)
        
        slots = pyast.Assign(targets=[pyast.Name('__slots__')],
                             value=pyast.Tuple(elts))

        cls.body = [slots] + self.generate_methods(env)
        return cls

    def copy_marking_expr(self, env, marking_var, *args):
        return pyast.Call(func=pyast.Attribute(value=pyast.Name(id=marking_var.name),
                                               attr='copy'))

    def gen_get_place(self, env, marking_var, place_name, mutable):
        return pyast.Attribute(value=pyast.Name(id=marking_var.name),
                               attr=self.id_provider.get(place_name))

    ################################################################################
    # Flow elimination
    ################################################################################

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        place_type = self.get_place_type_by_name(place_info.process_name)
        assert(isinstance(place_type, priv.placetypes.FlowPlaceType))
        return place_type.gen_check_flow(env=env,
                                         marking_var=marking_var,
                                         place_name=place_info.name,
                                         current_flow=current_flow)

    def gen_update_flow(self, env, marking_var, place_info):
        place_type = self.get_place_type_by_name(place_info.process_name)
        assert(isinstance(place_type, priv.placetypes.FlowPlaceType))
        return place_type.gen_update_flow(env=env,
                                          marking_var=marking_var,
                                          place_info=place_info)

    def gen_read_flow(self, env, marking_var, process_name):
        return self._process_place_types[process_name].gen_read_flow(env, marking_var)

################################################################################

class MarkingSetType(coretypes.MarkingSetType):
    """ Python implementation of the marking set type. """

    def __init__(self, markingtype):
        coretypes.MarkingSetType.__init__(self, markingtype)

    def gen_api(self, env):
        pass

    def new_marking_set_expr(self, env):
        return pyast.Call(func=pyast.Name(id='set'))

    def add_marking_stmt(self, env, markingset, marking):
        return pyast.stmt(pyast.Call(func=pyast.Attribute(value=pyast.Name(id=markingset.name),
                                                          attr='add'),
                                     args=[pyast.E(marking.name)]))


################################################################################
# EOF
################################################################################
