from mrkpidmethods import stubs
from neco.backends.python.priv import pyast
from neco.core.info import TypeInfo
from neco.utils import should_not_be_called
import neco.core.nettypes as coretypes

################################################################################

class PythonPlaceType(object):
    """ Base class for python backend place types. """

    allow_pids = False

    def place_expr(self, env, marking_var):
        return self.marking_type.gen_get_place(env,
                                               marking_var=marking_var,
                                               place_name=self.info.name,
                                               mutable=False)

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
                                           place_info=place_info,
                                           marking_type=marking_type,
                                           type_info=TypeInfo.get('MultiSet'),
                                           token_type=place_info.type)

        self.field = marking_type.create_field(self, place_info.type)

    def new_place_stmt(self, env, dst_marking_var):
        return pyast.E("{} = multiset([])".format(self.field.access_from(dst_marking_var)))

    def size_expr(self, env, marking_var):
        return pyast.E("len({})".format(self.field.access_from(marking_var)))

    def iterable_expr(self, env, marking_var):
        return pyast.E("{}".format(self.field.access_from(marking_var)))

    def remove_token_stmt(self, env, compiled_token, marking_var, *args):
        remove_expr = pyast.E("{}.remove".format(self.field.access_from(marking_var)))
        return pyast.stmt(pyast.Call(func=remove_expr, args=[compiled_token]))

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        add_expr = pyast.E("{}.add".format(self.field.access_from(marking_var)))
        return pyast.stmt(pyast.Call(func=add_expr, args=[compiled_token]))

    def token_expr(self, env, value):
        return pyast.E(repr(value))

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        return pyast.E("{} = {}.copy()".format(self.field.access_from(dst_marking_var),
                                               self.field.access_from(src_marking_var)))

    def light_copy_stmt(self, env, dst_marking_var, src_marking_var):
        return pyast.E("{} = {}".format(self.field.access_from(dst_marking_var),
                                        self.field.access_from(src_marking_var)))
        
    def clear_stmt(self, env, marking_var):
        return pyast.E("{} = multiset()".format(self.field.access_from(marking_var)))

    def assign_multiset_stmt(self, env, token_var, marking_var):
        return pyast.E('{} = {}'.format(token_var.name, self.field.access_from(marking_var)))

    def not_empty_expr(self, env, marking_var):
        return pyast.E(self.field.access_from(marking_var))


    def add_multiset_stmt(self, env, multiset, marking_var):
        update_attr_expr = pyast.E('{}.update'.format(self.field.access_from(marking_var)))
        return pyast.stmt(pyast.Call(func=update_attr_expr, args=[multiset]))

    def add_items_stmt(self, env, multiset, marking_var):
        add_items_attr_expr = pyast.E('{}.add_items'.format(self.field.access_from(marking_var)))
        return pyast.stmt(pyast.Call(func=add_items_attr_expr, args=[multiset]))

    def dump_expr(self, env, marking_var):
        return pyast.E("{}.__dump__()".format(self.field.access_from(marking_var)))
    
    def update_pids_stmt(self, env, marking_var, new_pid_dict_var):
        stub_name = stubs['object_place_type_update_pids']
        return pyast.Assign(targets=[self.place_expr(env, marking_var)],
                            value=pyast.Call(func=pyast.Name(stub_name),
                                             args=[self.place_expr(self, marking_var),
                                                   pyast.Name(new_pid_dict_var.name)]))
    
    def update_pid_tree(self, env, marking_var, pid_tree_var):
        stub_name = stubs['object_place_type_update_pid_tree']
        return pyast.stmt(pyast.Call(func=pyast.Name(stub_name),
                                     args=[self.place_expr(self, marking_var),
                                           pyast.Name(pid_tree_var.name)]))

################################################################################
# opt
################################################################################

class OneSafePlaceType(coretypes.OneSafePlaceType, PythonPlaceType):
    """ Python one safe place Type implementation
    """

    def __init__(self, place_info, marking_type):
        coretypes.OneSafePlaceType.__init__(self,
                                            place_info=place_info,
                                            marking_type=marking_type,
                                            type_info=TypeInfo.get('AnyType'),
                                            token_type=TypeInfo.get('AnyType'))
        
        self.field = marking_type.create_field(self, place_info.type)

    def new_place_stmt(self, env, marking_var):
        return pyast.E("{} = None".format(self.field.access_from(marking_var)))

    @property
    def token_type(self):
        return self.info.type

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt(self, env, compiled_token, marking_var):
        return self.new_place_stmt(env, marking_var)

    def add_token_stmt(self, env, compiled_token, marking_var):
        field_expr = pyast.E(self.field.access_from(marking_var))
        return pyast.Assign(targets=[field_expr], value=compiled_token)

    def token_expr(self, env, value):
        return pyast.E(repr(value))

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        env.add_import('copy')
        return "{} = copy.deepcopy({})".format(self.field.access_from(dst_marking_var),
                                               self.field.access_from(src_marking_var))

    def dump_expr(self, env, marking_var):
        place_expr = self.place_expr(env, marking_var)
        return pyast.IfExp(test=place_expr,
                           body=pyast.BinOp(left=pyast.Str('['),
                                            op=pyast.Add(),
                                            right=pyast.BinOp(left=pyast.Call(func=pyast.Name('dump'),
                                                                              args=[place_expr]),
                                                              op=pyast.Add(),
                                                              right=pyast.Str(']'))),
                           orelse=pyast.Str('[]'))

    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_expr = env.marking_type.gen_get_place(env=env,
                                                    marking_var=marking_var,
                                                    place_name=self.info.name,
                                                    mutable=False)
        getnode = pyast.Assign(targets=[pyast.Name(id=token_var.name)],
                               value=place_expr)
        ifnode = pyast.If(test=pyast.Compare(left=pyast.Name(id=token_var.name),
                                             ops=[pyast.NotEq()],
                                             comparators=[pyast.Name(id='None')]),
                                             body=[ compiled_body ])
        return [ getnode, ifnode ]
        
################################################################################

class BTPlaceType(coretypes.BTPlaceType, PythonPlaceType):
    """ Python black token place type implementation.

    @attention: Using this place type without the BTTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type):
        """
        @param p)lace_info:
        @type_info place_info: C{}
        @param marking_type:
        @type_info marking_type: C{}
        """
        coretypes.BTPlaceType.__init__(self,
                                       place_info=place_info,
                                       marking_type=marking_type,
                                       type_info=TypeInfo.get('Int'),
                                       token_type=TypeInfo.get('Int'))
        
        self.field = marking_type.create_field(self, TypeInfo.get('Int'))

    def new_place_stmt(self, env, marking_var):
        return pyast.E("{} = 0".format(self.field.access_from(marking_var)))

    def iterable_expr(self, env, marking_var):
        return pyast.E("xrange(0, {})".format(self.field.access_from(marking_var)))
#        place_expr = self.place_expr(env, marking_var)
#        return pyast.Call(func=pyast.Name('xrange'),
#                          args=[pyast.Num(n=0), place_expr])

    def remove_token_stmt(self, env, compiled_token, marking_var, *args):
        return pyast.E("{} -= 1".format(self.field.access_from(marking_var)))

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        return pyast.E("{} += 1".format(self.field.access_from(marking_var)))

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        return pyast.E("{} = {}".format(self.field.access_from(dst_marking_var),
                                        self.field.access_from(src_marking_var))) 

    def token_expr(self, env, value):
        return pyast.E('dot')

    def dump_expr(self, env, marking_var):
        return pyast.E("'[' + ','.join(['dot'] * {}) + ']'".format(self.field.access_from(marking_var)))
#        
#        place_expr = self.place_expr(env, marking_var)
#        return pyast.BinOp(left=pyast.Str('['),
#                           op=pyast.Add(),
#                           right=pyast.BinOp(left=pyast.Call(func=pyast.E("', '.join"),
#                                                             args=[pyast.BinOp(left=pyast.List([pyast.Str('dot')]),
#                                                                               op=pyast.Mult(),
#                                                                               right=place_expr)]),
#                                             op=pyast.Add(),
#                                             right=pyast.Str(s=']')))

    def enumerate(self, env, marking_var, token_var, compiled_body):
        place_expr = env.marking_type.gen_get_place(env=env,
                                                    marking_var=marking_var,
                                                    place_name=self.info.name,
                                                    mutable=False)
        getnode = pyast.Assign(targets=[pyast.Name(id=token_var.name)],
                               value=pyast.Name(id='dot'))
        ifnode = pyast.If(test=pyast.Compare(left=place_expr,
                                             ops=[pyast.Gt()],
                                             comparators=[pyast.Num(0)]),
                          body=[ getnode, compiled_body ])
        return [ ifnode ]


################################################################################

class BTOneSafePlaceType(coretypes.BTOneSafePlaceType, PythonPlaceType):
    """ Python one safe black token place type

    Using this place type without the BTOneSafeTokenEnumerator may introduce inconsistency.
    """
    def __init__(self, place_info, marking_type):
        coretypes.BTOneSafePlaceType.__init__(self,
                                              place_info=place_info,
                                              marking_type=marking_type,
                                              type_info=TypeInfo.get('Bool'),
                                              token_type=TypeInfo.get('BlackToken'))

    def new_place_expr(self, env):
        return pyast.E('True')

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt(self, env, compiled_token, marking_var, *args):
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
        place_expr = env.marking_type.gen_get_place(env=env,
                                                    marking_var=marking_var,
                                                    place_name=self.info.name,
                                                    mutable=False)
        ifnode = pyast.If(test=pyast.UnaryOp(op=pyast.Not(), operand=place_expr),
                          body=compiled_body)
        return [ ifnode ]
    
################################################################################

class FlowPlaceType(coretypes.PlaceType, PythonPlaceType):
    """ Place type to represent flow control places a specific process.
    """

    def __init__(self, place_info, marking_type):
        """ Build a new place.

        @param place_info:
        @type_info place_info: C{}
        @param marking_type:
        @type_info marking_type: C{}
        """
        self._counter = 0
        self._places = {}
        coretypes.PlaceType.__init__(self,
                                     place_info=place_info,
                                     marking_type=marking_type,
                                     type_info=TypeInfo.get('Int'),
                                     token_type=TypeInfo.get('Int'))

    @property
    def is_ProcessPlace(self):
        return True

    @property
    def token_type(self):
        """ Get python type of the stored token
        """
        return TypeInfo.get('Int')

    def new_place_expr(self, env):
        """ Produce a new empty place.

        @returns: empty place expression
        @rtype: C{Expr}
        """
        return pyast.E("0")

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    @should_not_be_called
    def remove_token_stmt(self, *args, **kwargs): pass

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
        place_expr = self.place_expr(env, marking_var)
        l = []
        for place in self._places:
            l.append(pyast.stmt(pyast.Call(func=pyast.E('{}.append'.format(variable.name)),
                                           args=[ pyast.BinOp(left=pyast.Str(repr(place) + ' : '),
                                                              op=pyast.Add(),
                                                              right=pyast.IfExp(test=self.gen_check_flow(env, marking_var, place, place_expr),
                                                                                body=pyast.Str('[ dot ],'),
                                                                                orelse=pyast.Str('[],')))
                                                 ])))
        return l
