from neco.core.info import VariableProvider, TypeInfo
from neco.core.nettypes import MarkingTypeMethodGenerator
from neco.utils import todo
import pyast

GENERATOR_PLACE = 'sgen'

stubs = {
    'object_place_type_update_pids'     : 'data.neco__multiset_update_pids',
    'object_place_type_update_pid_tree' : 'data.neco__iterable_update_pid_tree',
    'iterable_extract_pids' : 'data.neco__iterable_extract_pids',
    'normalize_pid_tree' : 'data.neco__normalize_pid_tree',
    'generator_place_update_pids'     : 'data.generator_place_update_pids',
    'generator_place_update_pid_tree' : 'data.neco__generator_multiset_update_pid_tree',
    'pid_place_type_update_pids' : 'data.pid_place_type_update_pids'
}

def select_normalization_function(config):
    if config.pid_first or config.normalize_only:
        return 'normalize_marking'
    else:
        return 'full_normalize_marking'

class UpdatePidsGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type 
        
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        new_pid_dict_var = vp.new_variable(marking_type.type, name='new_pid_dict')

        function = pyast.FunctionDef(name='update_pids',
                                   args=pyast.A(self_var.name).param(new_pid_dict_var.name).ast())
            
        body = []
        for name, place_type in marking_type.place_types.iteritems():
            print place_type
            if not place_type.allow_pids:
                continue
            if name == GENERATOR_PLACE:
                body.append( pyast.Assign(targets=[ place_type.place_expr(env, self_var) ],
                                          value=pyast.Call(func=pyast.Name(stubs['generator_place_update_pids']),
                                                           args=[place_type.place_expr(env, self_var),
                                                                pyast.Name(new_pid_dict_var.name)]) ) )
            else:
                body.append( place_type.update_pids_stmt(env, self_var, new_pid_dict_var) )
        
        if not body:
            body = [pyast.Pass()]
        
        function.body = body
        return function
#
#class NormalizePidsGenerator(MarkingTypeMethodGenerator):
#    
#    def generate(self, env):  
#        marking_type = env.marking_type
#
#        vp = VariableProvider()
#        self_var = vp.new_variable(marking_type.type, name='self')
#        tree_var = vp.new_variable(TypeInfo.get('AnyType'),  name='tree')
#        token_var = vp.new_variable(TypeInfo.get('AnyType'),  name='token')
#        pid_dict_var = vp.new_variable(TypeInfo.get('Dict'), name='pid_dict')
#        pid_map_var  = vp.new_variable(TypeInfo.get('Dict'), name='pid_map')
#        state_space_var = vp.new_variable(TypeInfo.get('Set'), name='ss')
#        
#        tmp_pid_var = vp.new_variable(TypeInfo.get('Pid'), name='tpid')
#        tmp_marking_var = vp.new_variable(TypeInfo.get('Marking'), name='tmkr')
#
#        function = pyast.FunctionDef(name='normalize_pids',
#                                   args=pyast.A(self_var.name).param(state_space_var.name).ast())
#        body = []
#        body.append( pyast.E("{} = {{}}".format(pid_dict_var.name)) )
#        body.append( pyast.E("{} = PidTree(0)".format(tree_var.name)) )
#        # build the tree
#        for name, place_type in marking_type.place_types.iteritems():
#            if not place_type.allow_pids:
#                continue
#
#            if name == GENERATOR_PLACE:
#                enum_body = [ pyast.If(test=pyast.E('not {}.has_key({}[0])'.format(pid_dict_var.name, token_var.name)),
#                                       body=[pyast.E("{}[ {}[0] ] = Marking(True)".format(pid_dict_var.name, token_var.name))]),
#                              pyast.E("{}[ Pid.from_list({}[0].data + [{}[1] + 1]) ] = Marking(True)".format(pid_dict_var.name, token_var.name, token_var.name)) ]
#
#                body.append( place_type.enumerate( env, self_var, token_var, enum_body ) )
#            else:
#                body.append( place_type.extract_pids(env, self_var, pid_dict_var) )
#
#        # body.append(pyast.E("print {}".format(pid_dict_var.name)))
#        body.append(pyast.For(target=pyast.E('{}, {}'.format(tmp_pid_var.name, tmp_marking_var.name)),
#                              iter=pyast.E(('{}.iteritems()'.format(pid_dict_var.name))),
#                              body=[pyast.stmt(pyast.E('{}.add_marking({}, {})'.format(tree_var.name,
#                                                                                       tmp_pid_var.name,
#                                                                                       tmp_marking_var.name)))]))
#        
#        body.append(pyast.stmt(pyast.E("{}.order_tree(pid_free_marking_order)".format(tree_var.name))))
#        body.append(pyast.E("{} = {}.build_map()".format(pid_map_var.name, tree_var.name)))
#        
#        # update tokens with new pids
#        for name, place_type in marking_type.place_types.iteritems():
#            if not place_type.allow_pids:
#                continue
#
#            if name == GENERATOR_PLACE:
#                body.append( pyast.Assign(targets=[ place_type.place_expr(env, self_var) ],
#                                        value=pyast.Call(func=pyast.Name(stubs['generator_place_update_pids']),
#                                                         args=[place_type.place_expr(env, self_var),
#                                                               pyast.Name(pid_map_var.name)]) ) )
#            else:
#                body.append( place_type.update_pids_stmt(env, self_var, pid_map_var) )
#
#        if not body:
#            body = [pyast.Pass()]
#
#        function.body = body
#        return function


class BuildPidTreeGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):  
        marking_type = env.marking_type

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        tree_var = vp.new_variable(TypeInfo.get('AnyType'),  name='tree')
        token_var = vp.new_variable(TypeInfo.get('AnyType'),  name='token')
        pid_dict_var = vp.new_variable(TypeInfo.get('Dict'), name='pid_dict')

        tmp_pid_var = vp.new_variable(TypeInfo.get('Pid'), name='tpid')
        tmp_marking_var = vp.new_variable(TypeInfo.get('Marking'), name='tmkr')

        function = pyast.FunctionDef(name='buildPidTree',
                                   args=pyast.A(self_var.name).ast())
        body = []
        body.append( pyast.E("{} = defaultdict(Marking)".format(pid_dict_var.name)) )
        body.append( pyast.E("{} = PidTree(0)".format(tree_var.name)) )
        # build the tree
        for name, place_type in marking_type.place_types.iteritems():
            if not place_type.allow_pids:
                continue

            if name == GENERATOR_PLACE:
                enum_body = [ pyast.If(test=pyast.E('not {}.has_key({}[0])'.format(pid_dict_var.name, token_var.name)),
                                       body=[pyast.E("{}[ {}[0] ] = Marking(True)".format(pid_dict_var.name, token_var.name))]),
                              pyast.E("{}[ Pid.from_list({}[0].data + [{}[1] + 1]) ] = Marking(True)".format(pid_dict_var.name, token_var.name, token_var.name)) ]

                body.append( place_type.enumerate( env, self_var, token_var, enum_body ) )
            else:
                body.append( place_type.extract_pids(env, self_var, pid_dict_var) )

        # body.append(pyast.E("print {}".format(pid_dict_var.name)))
        body.append(pyast.For(target=pyast.E('{}, {}'.format(tmp_pid_var.name, tmp_marking_var.name)),
                              iter=pyast.E(('{}.iteritems()'.format(pid_dict_var.name))),
                              body=[pyast.stmt(pyast.E('{}.add_marking({}, {})'.format(tree_var.name,
                                                                                       tmp_pid_var.name,
                                                                                       tmp_marking_var.name)))]))
        body.append(pyast.E("return {}".format(tree_var.name)))
        function.body = body
        return function
    
class EqGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        config = marking_type.config
        
        vp = VariableProvider()
        self_var  = vp.new_variable(env.marking_type.type, 'self')
        other_var = vp.new_variable(env.marking_type.type, 'other')
        
        function = pyast.FunctionDef(name='__eq__',
                                     args=pyast.A(self_var.name).param(other_var.name).ast())
        return_str = "return ("
        for i, (name, place_type) in enumerate(marking_type.place_types.iteritems()):
            if name == GENERATOR_PLACE and config.normalize_pids:
                continue
            
            id_name = place_type.field
            if i > 0:
                return_str += " and "
            return_str += "(%s == %s)" % (id_name.access_from(self_var), id_name.access_from(other_var))
        return_str += ")"

        function.body = [ pyast.E(return_str) ]
        return function

class HashGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        config = marking_type.config
        
        vp = VariableProvider()
        self_var  = vp.new_variable(env.marking_type.type, 'self')
        
        builder = pyast.Builder()
        
        builder.begin_FunctionDef( name = '__hash__', args = pyast.A(self_var.name).ast() )

        builder.begin_If(test=pyast.E('self.{} != None'.format(marking_type.get_field('_hash').name)))
        builder.emit_Return(pyast.E('self.{}'.format(marking_type.get_field('_hash').name)))
        builder.end_If()
        
        builder.emit( pyast.E('h = 0') )


        for name, place_type in marking_type.place_types.iteritems():
            if name == GENERATOR_PLACE and config.normalize_pids:
                continue
            
            magic = hash(name)
            builder.emit( pyast.E('h ^= hash(' + place_type.field.access_from(self_var) + ') * ' + str(magic) ) )

        builder.emit(pyast.E("self.{} = h".format(marking_type.get_field('_hash').name)))
        # builder.emit(pyast.E("print h"))
        builder.emit_Return(pyast.E("h"))
        builder.end_FunctionDef()
        return builder.ast()

class PidFreeHashGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type
        config = marking_type.config
        
        vp = VariableProvider()
        self_var  = vp.new_variable(env.marking_type.type, 'self')
        
        builder = pyast.Builder()
        
        builder.begin_FunctionDef( name = '__pid_free_hash__', args = pyast.A(self_var.name).ast() )
       
        builder.emit( pyast.E('h = 0') )
        
        
        for (name, place_type) in marking_type.place_types.iteritems():
            magic = hash(name)
            type_info = place_type.token_type

            if type_info.is_Pid:
                
                # builder.emit( pyast.E('h ^= hash(' +  place_type.field.access_from(self_var) + ') * ' + str(magic)) )
                
                right_operand = pyast.BinOp( left=place_type.pid_free_hash_expr(env, self_var, [0]),
                                             op=pyast.Mult(),
                                             right=pyast.E(str(magic)) )
                
                builder.emit( pyast.AugAssign(target = [pyast.E("h")],
                                              op=pyast.BitXor(),
                                              value = right_operand ) )

            elif type_info.has_pids:
                # must be tuple
                assert( type_info.is_TupleType )
                
                ignore = [ i for i, subtype in enumerate(type_info) if subtype.is_Pid ]
                # builder.emit("{!s} = {!r}".format(ig_var.name, ig))
                
                right_operand = pyast.BinOp( left=place_type.pid_free_hash_expr(env, self_var, ignore),
                                             op=pyast.Mult(),
                                             right=pyast.E(str(magic)) )
                
                builder.emit( pyast.AugAssign(target = [pyast.E("h")],
                                              op=pyast.BitXor(),
                                              value = right_operand ) )

            else:
                builder.emit( pyast.E('h ^= hash(' +  place_type.field.access_from(self_var) + ') * ' + str(magic)) )

        builder.emit_Return(pyast.E("h"))
        builder.end_FunctionDef()
        return builder.ast()


class PidFreeCmpGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, 'self')
        other_var = vp.new_variable(marking_type.type, 'other')
        cmp_var = vp.new_variable(marking_type.type, 'tmp')
        # ig_var = vp.new_variable(marking_type.type, 'ignore')

        builder = pyast.Builder()
        builder.begin_FunctionDef(name='pid_free_compare',
                                  args=pyast.A(self_var.name).param(other_var.name).ast())

        for place_type in marking_type.place_types.values():
            type_info = place_type.token_type
            print type_info, place_type
            if type_info.is_Pid:
                builder.emit( pyast.Assign(targets = [pyast.E(cmp_var.name)],
                                           value = place_type.pid_free_compare_expr(env, self_var, other_var, [0]) ) )
                builder.begin_If(test=pyast.E('{} != 0'.format(cmp_var.name)))
                builder.emit_Return( pyast.E(cmp_var.name) )
                builder.end_If()
            
            elif type_info.has_pids:
                # must be tuple
                assert( type_info.is_TupleType )
                
                ignore = [ i for i, subtype in enumerate(type_info) if subtype.is_Pid ]
                # builder.emit("{!s} = {!r}".format(ig_var.name, ig))

                builder.emit( pyast.Assign(targets = [pyast.E(cmp_var.name)],
                                           value = place_type.pid_free_compare_expr(env, self_var, other_var, ignore) ) )
                builder.begin_If(test=pyast.E('{} != 0'.format(cmp_var.name)))
                builder.emit_Return( pyast.E(cmp_var.name) )
                builder.end_If()

            else:
                builder.emit( pyast.Assign(targets = [pyast.E(cmp_var.name)],
                                           value = place_type.compare_expr(env, self_var, other_var) ) )
                builder.begin_If(test=pyast.E('{} != 0'.format(cmp_var.name)))
                builder.emit_Return( pyast.E(cmp_var.name) )
                builder.end_If()

        builder.emit_Return(pyast.Num(0))
        builder.end_FunctionDef()

        return builder.ast()


