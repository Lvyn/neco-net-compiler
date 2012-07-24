import neco.config as config
from neco.core.info import VariableProvider
from neco.core.nettypes import MarkingTypeMethodGenerator
import neco.backends.python.pyast as ast
from neco.backends.python.pyast import Builder, E, A, stmt

class InitGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        function = ast.FunctionDef(name='__init__',
                                   args=A('self').param('alloc', default='True').ast())

        if_block = ast.If(test=ast.Name(id='alloc'))

        for name, place_type in marking_type.place_types.iteritems():
            if_block.body.append( ast.Assign(targets=[ast.Attribute(value=ast.Name(id='self'),
                                                                    attr=marking_type.id_provider.get(name))],
                                             value=place_type.new_place_expr(env)) )
        function.body = if_block
        return function

class CopyGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type
        
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        marking_var = vp.new_variable(marking_type.type)

        function = ast.FunctionDef(name='copy',
                                   args=A(self_var.name).param('alloc', default='True').ast())

        tmp = [ ast.Assign(targets=[ast.Name(id=marking_var.name)],
                           value=E('Marking(False)')) ]

        for name, place_type in marking_type.place_types.iteritems():
            tmp.append( ast.Assign(targets=[ast.Attribute(value=ast.Name(id = marking_var.name),
                                                          attr=marking_type.id_provider.get(name))],
                                   value=place_type.copy_expr(env, marking_var = self_var))
                        )
        tmp.append(ast.Return(ast.Name(id=marking_var.name)))
        function.body = tmp
        return function
    
class EqGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        other = 'other'
        function = ast.FunctionDef(name='__eq__',
                                   args=A('self').param(other).ast())
        return_str = "return ("
        for i, (name, place_type) in enumerate(marking_type.place_types.iteritems()):
            id_name = marking_type.id_provider.get(name)
            if i > 0:
                return_str += " and "
            return_str += "(self.%s == %s.%s)" % (id_name, other, id_name)
        return_str += ")"

        function.body = [ E(return_str) ]
        return function

class HashGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        builder = Builder()
        builder.begin_FunctionDef( name = '__hash__', args = A("self").ast() )
        builder.emit( E('h = 0') )

        for name, place_type in marking_type.place_types.iteritems():
            magic = hash(name)
            builder.emit( E('h ^= hash(self.' + marking_type.id_provider.get(name) + ') ^ ' + str(magic)) )

        builder.emit_Return(E("h"))
        builder.end_FunctionDef()
        return builder.ast()

class ReprGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = Builder()
        builder.begin_FunctionDef( name = "__repr__", args = A("self").ast() )

        builder.emit( E('s = "hdict({"') )
        for (i, (place_name, place_type)) in enumerate(items):
            tmp = ',\n ' if i > 0 else ''
            builder.emit(ast.AugAssign(target=ast.Name(id='s'),
                                       op=ast.Add(),
                                       value=ast.BinOp(left=ast.Str(s = tmp + "'" + place_name + "' : "),
                                                       op=ast.Add(),
                                                       right=E('repr(self.' + marking_type.id_provider.get(place_name) + ')')
                                                       )
                                       )
                         )
        builder.emit( E('s += "})"') )
        builder.emit_Return(E('s'))

        builder.end_FunctionDef()
        return builder.ast()

class DumpGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name='self')
        list_var = vp.new_variable()

        builder = Builder()
        builder.begin_FunctionDef( name = "__dump__", args = A(self_var.name).ast() )

        builder.emit( E('%s = ["{"]' % list_var.name) )
        for (i, (place_name, place_type)) in enumerate(items):
            if place_type.is_ProcessPlace:
                builder.emit( place_type.dump_expr(env, self_var, list_var) )
            else:
                builder.emit(stmt(ast.Call(func=E('{}.append'.format(list_var.name)),
                                           args=[ ast.BinOp(left = ast.Str(s = repr(place_name) + " : "),
                                                            op = ast.Add(),
                                                            right = ast.BinOp(left = place_type.dump_expr(env, self_var),
                                                                              op = ast.Add(),
                                                                              right = ast.Str(', '))
                                                            ) ]
                                           )
                                  )
                             )

        builder.emit(stmt(E('%s.append("}")' % list_var.name)))
        builder.emit_Return(E('"\\n".join({})'.format(list_var.name)))

        builder.end_FunctionDef()
        return builder.ast()
