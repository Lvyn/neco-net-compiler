""" Python basic net types. """

from neco.core.info import TypeInfo, PlaceInfo
from neco.utils import should_not_be_called
from priv import pyast
import neco.config as config
import neco.core.nettypes as coretypes
import neco.utils as utils

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

################################################################################

class PythonPlaceType(object):
    """ Base class for python backend place types. """
     
    allow_pids = False

    def place_expr(self, env, marking_var):
        return self.marking_type.gen_get_place(env,
                                               marking_var = marking_var,
                                               place_name = self.info.name,
                                               mutable = False)
        
    @property
    def is_ProcessPlace(self):
        return False

################################################################################

# multiple inheritance is used to allow type matching.

class ObjectPlaceType(coretypes.ObjectPlaceType, PythonPlaceType):
    """ Python implementation of the fallback place type. """
    
    allow_pids = True
    
    def __init__(self, place_info, marking_type):
        coretypes.ObjectPlaceType.__init__(self,
                                           place_info = place_info,
                                           marking_type = marking_type,
                                           type = TypeInfo.MultiSet,
                                           token_type = place_info.type)
        
    def new_place_expr(self, env):
        return pyast.E("multiset([])")

    def size_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.E('len').call([pyast.E(place_expr)])

    def iterable_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def remove_token_stmt(self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.stmt( pyast.Call(func=pyast.Attribute(value=place_expr,
                                                 attr="remove"),
                              args=[compiled_token]
                              )
                     )

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.stmt( pyast.Call(func=pyast.Attribute(value=place_expr,
                                                 attr="add"),
                              args=[compiled_token]) )

    def token_expr(self, env, value):
        return pyast.E(repr(value))

    def copy_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.Call(func=pyast.Attribute(value=place_expr,
                                           attr="copy"
                                           )
                        )

    def clear_stmt(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.stmt( pyast.Assign(targets=[place_expr],
                                        value=pyast.Call(func=pyast.Name(id="multiset")))
                     )

    def not_empty_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)


    def add_multiset_stmt(self, env, multiset, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.stmt( pyast.Call(func=pyast.Attribute(name=place_expr,
                                                 attr='update'),
                              args=[multiset])
                     )

    def add_items_stmt(self, env, multiset, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.stmt( pyast.Call(func=pyast.Attribute(value=place_expr,
                                                 attr='add_items'),
                              args=[multiset])
                     )

    def dump_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.Call(func=pyast.Attribute(value=place_expr,
                                           attr='__dump__'))

    def update_pids_stmt(self, env, marking_var, new_pid_dict_var):
        from priv.mrkpidmethods import stubs
        stub_name = stubs['object_place_type_update_pids']
        return pyast.Assign(targets=[self.place_expr(env, marking_var)],
                          value=pyast.Call(func=pyast.Name(stub_name),
                                         args=[self.place_expr(self, marking_var),
                                               pyast.Name(new_pid_dict_var.name)]))
    
    def update_pid_tree(self, env, marking_var, pid_tree_var):
        from priv.mrkpidmethods import stubs
        stub_name = stubs['object_place_type_update_pid_tree']
        return pyast.stmt(pyast.Call(func=pyast.Name(stub_name),
                             args=[self.place_expr(self, marking_var),
                                   pyast.Name(pid_tree_var.name)]))

################################################################################

class StaticMarkingType(coretypes.MarkingType):
    """ Python marking type implementation, places as class attributes. """

    def __init__(self):
        coretypes.MarkingType.__init__(self,
                                       TypeInfo.register_type('Marking'),
                                       TypeInfo.register_type('set'))
        self.id_provider = utils.NameProvider()
        self._process_place_types = {}
        
        import priv.mrkmethods
        import priv.mrkpidmethods

        self.add_method_generator( priv.mrkmethods.InitGenerator() )
        self.add_method_generator( priv.mrkmethods.CopyGenerator() )
        self.add_method_generator( priv.mrkmethods.ReprGenerator() )
        self.add_method_generator( priv.mrkmethods.DumpGenerator() )
        
        if config.get("pid_normalization"):
            self.add_method_generator( priv.mrkpidmethods.EqGenerator() )
            self.add_method_generator( priv.mrkpidmethods.HashGenerator() )
            self.add_method_generator( priv.mrkpidmethods.UpdatePidsGenerator() )
            self.add_method_generator( priv.mrkpidmethods.NormalizePidsGenerator() )
        else:
            self.add_method_generator( priv.mrkmethods.EqGenerator() )
            self.add_method_generator( priv.mrkmethods.HashGenerator() )

    def __str__(self):
        s = []
        s.append('Marking:')
        for name, place_type in self.place_types.iteritems():
            s.append('{} : {}'.format(name, place_type.__class__))
        s.append('End')
        return '\n'.join(s)

    def gen_types(self):
        """ Build place types using C{select_type} predicate.
        """
        opt = config.get('optimize')
        for place_info in self.flow_control_places:
            try:
                self._process_place_types[place_info.process_name].add_place(place_info)
            except KeyError:
                new_id = place_info.process_name
                place_type = FlowPlaceType(place_info = PlaceInfo.Dummy(new_id,
                                                                        process_name = place_info.process_name),
                                           marking_type = self)
                self.place_types[place_info.process_name] = place_type
                place_type.add_place(place_info)
                self._process_place_types[place_info.process_name] = place_type

        for place_info in self.one_safe_places:
            place_name = place_info.name

            if opt:
                if place_info.one_safe:
                    if place_info.type.is_BlackToken:
                        place_type = BTOneSafePlaceType(place_info, marking_type = self)
                    else:
                        place_type = OneSafePlaceType(place_info, marking_type = self)

                elif place_info.type.is_BlackToken:
                    place_type = BTPlaceType(place_info, marking_type = self)
                else:
                    place_type = ObjectPlaceType(place_info, marking_type = self)
            else:
                place_type = ObjectPlaceType(place_info, marking_type = self)

            if self.place_types.has_key(place_name):
                raise RuntimeError("{name} place exists".format(name=place_name))
            else:
                self.place_types[place_name] = place_type

        for place_info in self.places:
            place_name = place_info.name

            if place_info.type.is_BlackToken:
                place_type = BTPlaceType(place_info, marking_type = self)
            else:
                place_type = ObjectPlaceType(place_info, marking_type = self)

            if self.place_types.has_key(place_name):
                raise RuntimeError("{name} place exists".format(name=place_name))
            else:
                self.place_types[place_name] = place_type

    def new_marking_expr(self, env, *args):
        return pyast.E("Marking()")

    def normalize_marking_call(self, env, marking_var):
        return pyast.stmt(pyast.Call(func=pyast.Attribute(value=pyast.Name(id=marking_var.name),
                                           attr='normalize_pids'),
                             args = []))

    def generate_api(self, env):
        cls = pyast.ClassDef('Marking', bases=[pyast.Name(id='object')])

        elts = []
        for name, place_type in self.place_types.iteritems():
            elts.append( pyast.Str(self.id_provider.get(name)) )

        slots = pyast.Assign(targets = [pyast.Name('__slots__')],
                           value = pyast.Tuple(elts))

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
        assert( isinstance(place_type, FlowPlaceType) )
        return place_type.gen_check_flow(env = env,
                                         marking_var = marking_var,
                                         place_name = place_info.name,
                                         current_flow = current_flow)

    def gen_update_flow(self, env, marking_var, place_info):
        place_type = self.get_place_type_by_name(place_info.process_name)
        assert( isinstance(place_type, FlowPlaceType) )
        return place_type.gen_update_flow(env = env,
                                          marking_var = marking_var,
                                          place_info = place_info)

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
                             args=[pyast.E(marking.name)]
                             )
                    )

################################################################################
# opt
################################################################################

class OneSafePlaceType(coretypes.OneSafePlaceType, PythonPlaceType):
    """ Python one safe place Type implementation
    """

    def __init__(self, place_info, marking_type):
        coretypes.OneSafePlaceType.__init__(self,
                                          place_info = place_info,
                                          marking_type = marking_type,
                                          type = TypeInfo.AnyType,
                                          token_type = TypeInfo.AnyType)

    def new_place_expr(self, env):
        return pyast.Name(id="None")

    @property
    def token_type(self):
        return self.info.type

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt(self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.Assign(targets=[place_expr],
                          value=pyast.Name(id='None'))

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.Assign(targets=[place_expr],
                          value=compiled_token)

    def token_expr(self, env, value):
        return pyast.E(repr(value))

    def copy_expr(self, env, marking_var):
        env.add_import('copy')
        place_expr = self.place_expr(env, marking_var)
        return pyast.Call(func=pyast.Attribute(value=pyast.Name(id='copy'),
                                           attr='deepcopy'),
                        args=[place_expr])

    def dump_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.IfExp(test=place_expr,
                         body=pyast.BinOp(left = pyast.Str('['),
                                        op = pyast.Add(),
                                        right = pyast.BinOp(left = pyast.Call(func=pyast.Name('dump'),
                                                                          args=[place_expr]),
                                                          op = pyast.Add(),
                                                          right = pyast.Str(']')
                                                          )
                                        ),
                         orelse=pyast.Str('[]'))

    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_expr = env.marking_type.gen_get_place( env = env,
                                                     marking_var = marking_var,
                                                     place_name = self.info.name,
                                                     mutable = False )
        getnode = pyast.Assign(targets=[pyast.Name(id=token_var.name)],
                             value=place_expr)
        ifnode = pyast.If(test=pyast.Compare(left=pyast.Name(id=token_var.name),
                                         ops=[pyast.NotEq()],
                                         comparators=[pyast.Name(id='None')]),
                                         body=[ compiled_body ] )
        return [ getnode, ifnode ]
    
        
################################################################################

class BTPlaceType(coretypes.BTPlaceType, PythonPlaceType):
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
        coretypes.BTPlaceType.__init__(self,
                                     place_info = place_info,
                                     marking_type = marking_type,
                                     type = TypeInfo.Int,
                                     token_type = TypeInfo.Int)

    def new_place_expr(self, env):
        return pyast.Num(n=0)

    def iterable_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.Call(func=pyast.Name('xrange'),
                        args=[pyast.Num(n=0), place_expr])

    def remove_token_stmt( self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.AugAssign(target=place_expr,
                             op=pyast.Sub(),
                             value=pyast.Num(1))

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.AugAssign(target=place_expr,
                             op=pyast.Add(),
                             value=pyast.Num(1))

    def copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def token_expr(self, env, value):
        return pyast.E('dot')

    def dump_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.BinOp(left = pyast.Str('['),
                         op = pyast.Add(),
                         right = pyast.BinOp(left = pyast.Call(func=pyast.E("', '.join"),
                                                           args=[pyast.BinOp(left=pyast.List([pyast.Str('dot')]),
                                                                           op=pyast.Mult(),
                                                                           right=place_expr)]),
                                           op = pyast.Add(),
                                           right = pyast.Str(s=']')
                                           )
                         )
    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_expr = env.marking_type.gen_get_place( env = env,
                                                     marking_var = marking_var,
                                                     place_name = self.info.name,
                                                     mutable = False )
        getnode = pyast.Assign(targets=[pyast.Name(id=token_var.name)],
                             value=pyast.Name(id='dot'))
        ifnode = pyast.If(test=pyast.Compare(left=place_expr, ops=[pyast.Gt()], comparators=[pyast.Num(0)]),
                        body=[ getnode, compiled_body ] )
        return [ ifnode ]


################################################################################

class BTOneSafePlaceType(coretypes.BTOneSafePlaceType, PythonPlaceType):
    """ Python one safe black token place type

    Using this place type without the BTOneSafeTokenEnumerator may introduce inconsistency.
    """
    def __init__(self, place_info, marking_type):
        coretypes.BTOneSafePlaceType.__init__(self,
                                            place_info = place_info,
                                            marking_type = marking_type,
                                            type = TypeInfo.Bool,
                                            token_type = TypeInfo.BlackToken)

    def new_place_expr(self, env):
        return pyast.E('True')

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt( self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.Assign(targets=[place_expr],
                          value=pyast.Name(id='True'))

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        place_expr = self.place_expr(env, marking_var)
        return pyast.Assign(targets=[place_expr],
                          value=pyast.Name(id='False'))

    def copy_expr(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def token_expr(self, env, value):
        return pyast.E('dot')

    def dump_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.IfExp(test=pyast.UnaryOp(op=pyast.Not(), operand=place_expr),
                         body=pyast.Str('[ dot ]'),
                         orelse=pyast.Str('[]'))

    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_expr = env.marking_type.gen_get_place( env = env,
                                                     marking_var = marking_var,
                                                     place_name = self.info.name,
                                                     mutable = False )
        ifnode = pyast.If( test = pyast.UnaryOp(op=pyast.Not(), operand=place_expr),
                         body = compiled_body )
        return [ ifnode ]
    
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
    def is_ProcessPlace(self):
        return True

    @property
    def token_type(self):
        """ Get python type of the stored token
        """
        return TypeInfo.Int

    def new_place_expr(self, env):
        """ Produce a new empty place.

        @returns: empty place expression
        @rtype: C{Expr}
        """
        return pyast.E("0")

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    @should_not_be_called
    def remove_token_stmt( self, *args, **kwargs): pass

    @should_not_be_called
    def add_token_stmt(self, *args, **kwargs): pass

    def copy_expr(self, env, marking_var):
        """ produce an expression corresponding to a copy of the place.

        @param env: compiling environment
        @type env: C{Env}
        @param marking_var: marking storing the place
        @type marking_var: C{VariableInfo}
        """
        return self.place_expr(env, marking_var)

    def add_place(self, place_info):
        """ Adds a flow control place.

        @param place_info: flow control place to be added
        @type place_info: C{PlaceInfo}
        """
        assert(place_info.flow_control)
        assert(not self._places.has_key(place_info.name))
        self._places[place_info.name] = self._counter
        self._counter += 1

    def gen_check_flow(self, env, marking_var, place_name, current_flow):
        """ Get an pyast representing the flow check.
        """
        return pyast.Compare(left=current_flow,
                           ops=[pyast.Eq()],
                           comparators=[pyast.Num(self._places[place_name])])

    def gen_update_flow(self, env, marking_var, place_info):
        """ Get an pyast representing the flow update.
        """
        place_expr = self.place_expr(env, marking_var)
        return pyast.Assign(targets=[place_expr],
                          value=pyast.Num(self._places[place_info.name]))

    def gen_read_flow(self, env, marking_var):
        return self.place_expr(env, marking_var)

    def dump_expr(self, env, marking_var, variable):
        place_expr =  self.place_expr(env, marking_var)
        l = []
        for place in self._places:
            l.append( pyast.stmt(pyast.Call(func=pyast.E('{}.append'.format(variable.name)),
                                    args=[ pyast.BinOp(left=pyast.Str( repr(place) + ' : '),
                                                     op=pyast.Add(),
                                                     right=pyast.IfExp(test=self.gen_check_flow(env, marking_var, place, place_expr),
                                                                     body=pyast.Str('[ dot ],'),
                                                                     orelse=pyast.Str('[],'))
                                                     ) ]
                                    )
                           )
                      )
        return l

################################################################################
# EOF
################################################################################
