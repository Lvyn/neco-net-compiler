from neco.core.info import VariableProvider, TypeInfo
from neco.core.nettypes import MarkingTypeMethodGenerator
import cyast

GENERATOR_PLACE = 'sgen'

stubs = {
    'object_place_type_update_pids'     : 'ctypes_ext.neco__multiset_update_pids',
    'object_place_type_update_pid_tree' : 'ctypes_ext.neco__iterable_update_pid_tree',
    'create_pid_tree'    : 'ctypes_ext.neco__create_pid_tree',
    'normalize_pid_tree' : 'ctypes_ext.neco__normalize_pid_tree',
    'generator_place_update_pids'     : 'ctypes_ext.neco__generator_token_transformer',
    'generator_place_update_pid_tree' : 'ctypes_ext.neco__generator_multiset_update_pid_tree',
}

class UpdatePidsGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):        
        marking_type = env.marking_type 
        
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        new_pid_dict_var = vp.new_variable(marking_type.type, name='new_pid_dict')

        builder = cyast.Builder()
        
        args = (cyast.A(self_var.name, type=env.type2str(self_var.type))
                .param(new_pid_dict_var.name, type=env.type2str(new_pid_dict_var.type)))
        
        function = builder.FunctionCDef(name='update_pids', args=args, returns=cyast.E("void"))
            
        body = []
        for place_type in marking_type.place_types.itervalues():
            print place_type
            if not place_type.allows_pids:
                continue
            #body.append( update_pids_stmt(env, place_type, self_var, new_pid_dict_var) )
        
        if not body:
            body = [cyast.Pass()]
        
        function.body = body
        import pprint, ast
        pprint.pprint(ast.dump(function))
        return function



def add_pids_to_tree(env, place_type, marking_var, new_pid_dict_var):
    
    if place_type.type.is_Pid:
        body = []
        token_var = env.variable_provider.new_variable()
        return place_type.enumerate_tokens(env, token_var, marking_var, body)
    else:
        raise NotImplementedError
    
    
class NormalizePidsGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):  
        marking_type = env.marking_type

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        tree_var = vp.new_variable(TypeInfo.get('AnyType'),  name='tree')
        pid_dict_var = vp.new_variable(TypeInfo.get('Dict'), name='pid_dict')

  
        function = cyast.Builder.FunctionCDef(name='normalize_pids',
                                              args=cyast.A(self_var.name, type=env.type2str(self_var.type)),
                                              returns=cyast.E('void'))
        body = []
        body.append(cyast.Assign(targets=[cyast.Name(id=tree_var.name)],
                               value=cyast.Call(func=cyast.Name(stubs['create_pid_tree']),
                                              args=[])))
        # build the tree
        for name, place_type in marking_type.place_types.iteritems():
            if not place_type.allows_pids:
                continue

            if name == GENERATOR_PLACE:
                body.append(cyast.stmt(cyast.Call(func=cyast.Name(stubs['generator_place_update_pid_tree']),
                                          args=[ place_type.place_expr(env, self_var), cyast.Name(id=tree_var.name) ] )))
            else:
                body.append( add_pids_to_tree(env, place_type, self_var, tree_var))

        # normalize tree and get dict
        body.append(cyast.Assign(targets=[cyast.Name(id=pid_dict_var.name)],
                                 value=cyast.Call(func=cyast.Name(stubs['normalize_pid_tree']),
                                                  args=[cyast.Name(tree_var.name)])))
        # update tokens with new pids
        for name, place_type in marking_type.place_types.iteritems():
            if not place_type.allows_pids:
                continue

            if name == GENERATOR_PLACE:
                body.append( cyast.Assign(targets=[ place_type.place_expr(env, self_var) ],
                                        value=cyast.Call(func=cyast.Name(stubs['generator_place_update_pids']),
                                                       args=[place_type.place_expr(env, self_var),
                                                             cyast.Name(pid_dict_var.name)]) ) )
            else:
                body.append( place_type.update_pids_stmt(env, self_var, pid_dict_var) )

        if not body:
            body = [cyast.Pass()]

        function.body = body
        
        function.body = [cyast.Pass()]
        return function

#class CompareGenerator(MarkingTypeMethodGenerator):
#    
#    def generate(self, env):
#        marking_type = env.marking_type
#        config = marking_type.config
#        
#        vp = VariableProvider()
#        self_var  = vp.new_variable(env.marking_type.type, 'self')
#        other_var = vp.new_variable(env.marking_type.type, 'other')
#        
#        args = (cyast.A(self_var.name, type=env.type2str(self_var.type))
#                .param(other_var.name, type=env.type2str(other_var.type)))
#        
#        function = cyast.Builder.FunctionDef(name='__eq__', args=args)
#        
#        return_str = "return ("
#        for i, (name, place_type) in enumerate(marking_type.place_types.iteritems()):
#            if name == GENERATOR_PLACE and config.normalize_pids:
#                continue
#            
#            id_name = place_type.chunk.get_attribute_name()
#            if i > 0:
#                return_str += " and "
#            return_str += "({left}.{attr} == {right}.{attr})".format(left=self_var.name, 
#                                                                     right=other_var.name,
#                                                                     attr=id_name)
#        return_str += ")"
#
#        function.body = [ cyast.E(return_str) ]
#        return function

