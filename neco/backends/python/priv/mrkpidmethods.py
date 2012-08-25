from neco.core.info import VariableProvider, TypeInfo
from neco.core.nettypes import MarkingTypeMethodGenerator
import pyast

GENERATOR_PLACE = 'sgen'

stubs = {
    'object_place_type_update_pids'     : 'data.neco__multiset_update_pids',
    'object_place_type_update_pid_tree' : 'data.neco__iterable_update_pid_tree',
    'create_pid_tree'    : 'data.neco__create_pid_tree',
    'normalize_pid_tree' : 'data.neco__normalize_pid_tree',
    'generator_place_update_pids'     : 'data.neco__generator_token_transformer',
    'generator_place_update_pid_tree' : 'data.neco__generator_multiset_update_pid_tree',
}

class UpdatePidsGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):        
        marking_type = env.marking_type 
        
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        new_pid_dict_var = vp.new_variable(marking_type.type, name='new_pid_dict')

        function = pyast.FunctionDef(name='update_pids',
                                   args=pyast.A(self_var.name).param(new_pid_dict_var.name).ast())
            
        body = []
        for place_type in marking_type.place_types.itervalues():
            print place_type
            if not place_type.allow_pids:
                continue
            body.append( place_type.update_pids_stmt(env, self_var, new_pid_dict_var) )
        
        if not body:
            body = [pyast.Pass()]
        
        function.body = body
        return function
    
class NormalizePidsGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):  
        marking_type = env.marking_type
        
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        tree_var = vp.new_variable(TypeInfo.get('AnyType'),  name='tree')
        pid_dict_var = vp.new_variable(TypeInfo.get('Dict'), name='pid_dict')
        
        function = pyast.FunctionDef(name='normalize_pids',
                                   args=pyast.A(self_var.name).ast())
        body = []
        body.append(pyast.Assign(targets=[pyast.Name(id=tree_var.name)],
                               value=pyast.Call(func=pyast.Name(stubs['create_pid_tree']),
                                              args=[])))
        # build the tree
        for name, place_type in marking_type.place_types.iteritems():
            if not place_type.allow_pids:
                continue
            
            if name == GENERATOR_PLACE:
                body.append(pyast.stmt(pyast.Call(func=pyast.Name(stubs['generator_place_update_pid_tree']),
                                          args=[ place_type.place_expr(env, self_var), pyast.Name(id=tree_var.name) ] )))
            else:
                body.append(place_type.update_pid_tree(env, self_var, tree_var))
        # normalize tree and get dict
        body.append(pyast.Assign(targets=[pyast.Name(id=pid_dict_var.name)],
                               value=pyast.Call(func=pyast.Name(stubs['normalize_pid_tree']),
                                              args=[pyast.Name(tree_var.name)])))
        # update tokens with new pids
        for name, place_type in marking_type.place_types.iteritems():
            if not place_type.allow_pids:
                continue
            
            if name == GENERATOR_PLACE:
                body.append( pyast.Assign(targets=[ place_type.place_expr(env, self_var) ],
                                        value=pyast.Call(func=pyast.Name(stubs['generator_place_update_pids']),
                                                       args=[place_type.place_expr(env, self_var),
                                                             pyast.Name(pid_dict_var.name)]) ) )
            else:
                body.append( place_type.update_pids_stmt(env, self_var, pid_dict_var) )
           
        if not body:
            body = [pyast.Pass()]
        
        function.body = body
        return function
    
class EqGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        config = marking_type.config
        
        other = 'other'
        function = pyast.FunctionDef(name='__eq__',
                                   args=pyast.A('self').param(other).ast())
        return_str = "return ("
        for i, (name, _) in enumerate(marking_type.place_types.iteritems()):
            if name == GENERATOR_PLACE and config.pid_normalization:
                continue
            
            id_name = marking_type.id_provider.get(name)
            if i > 0:
                return_str += " and "
            return_str += "(self.%s == %s.%s)" % (id_name, other, id_name)
        return_str += ")"

        function.body = [ pyast.E(return_str) ]
        return function

class HashGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        config = marking_type.config
        
        builder = pyast.Builder()
        builder.begin_FunctionDef( name = '__hash__', args = pyast.A("self").ast() )
        builder.emit( pyast.E('h = 0') )

        for name, _ in marking_type.place_types.iteritems():
            if name == GENERATOR_PLACE and config.pid_normalization:
                continue
            
            magic = hash(name)
            builder.emit( pyast.E('h ^= hash(self.' + marking_type.id_provider.get(name) + ') ^ ' + str(magic)) )

        builder.emit_Return(pyast.E("h"))
        builder.end_FunctionDef()
        return builder.ast()
