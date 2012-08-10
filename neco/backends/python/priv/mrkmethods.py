from neco.core.info import VariableProvider
from neco.core.nettypes import MarkingTypeMethodGenerator
import pyast

class InitGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        function = pyast.FunctionDef(name='__init__',
                                   args=pyast.A('self').param('alloc', default='True').ast())

        if_block = pyast.If(test=pyast.Name(id='alloc'))

        for name, place_type in marking_type.place_types.iteritems():
            if_block.body.append( pyast.Assign(targets=[pyast.Attribute(value=pyast.Name(id='self'),
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

        function = pyast.FunctionDef(name='copy',
                                   args=pyast.A(self_var.name).param('alloc', default='True').ast())

        tmp = [ pyast.Assign(targets=[pyast.Name(id=marking_var.name)],
                           value=pyast.E('Marking(False)')) ]

        for name, place_type in marking_type.place_types.iteritems():
            tmp.append( pyast.Assign(targets=[pyast.Attribute(value=pyast.Name(id = marking_var.name),
                                                          attr=marking_type.id_provider.get(name))],
                                   value=place_type.copy_expr(env, marking_var = self_var))
                        )
        tmp.append(pyast.Return(pyast.Name(id=marking_var.name)))
        function.body = tmp
        return function
    
class EqGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        other = 'other'
        function = pyast.FunctionDef(name='__eq__',
                                   args=pyast.A('self').param(other).ast())
        return_str = "return ("
        for i, (name, _) in enumerate(marking_type.place_types.iteritems()):
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
        
        builder = pyast.Builder()
        builder.begin_FunctionDef( name = '__hash__', args = pyast.A("self").ast() )
        builder.emit( pyast.E('h = 0') )

        for (name, _) in marking_type.place_types.iteritems():
            magic = hash(name)
            builder.emit( pyast.E('h ^= hash(self.' + marking_type.id_provider.get(name) + ') ^ ' + str(magic)) )

        builder.emit_Return(pyast.E("h"))
        builder.end_FunctionDef()
        return builder.ast()

class ReprGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = pyast.Builder()
        builder.begin_FunctionDef( name = "__repr__", args = pyast.A("self").ast() )

        builder.emit( pyast.E('s = "hdict({"') )
        for (i, (place_name, _)) in enumerate(items):
            tmp = ',\n ' if i > 0 else ''
            builder.emit(pyast.AugAssign(target=pyast.Name(id='s'),
                                       op=pyast.Add(),
                                       value=pyast.BinOp(left=pyast.Str(s = tmp + "'" + place_name + "' : "),
                                                       op=pyast.Add(),
                                                       right=pyast.E('repr(self.' + marking_type.id_provider.get(place_name) + ')')
                                                       )
                                       )
                         )
        builder.emit( pyast.E('s += "})"') )
        builder.emit_Return(pyast.E('s'))

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

        builder = pyast.Builder()
        builder.begin_FunctionDef( name = "__dump__", args = pyast.A(self_var.name).ast() )

        builder.emit( pyast.E('%s = ["{"]' % list_var.name) )
        for (place_name, place_type) in items:
            if place_type.is_ProcessPlace:
                builder.emit( place_type.dump_expr(env, self_var, list_var) )
            else:
                builder.emit(pyast.stmt(pyast.Call(func=pyast.E('{}.append'.format(list_var.name)),
                                           args=[ pyast.BinOp(left = pyast.Str(s = repr(place_name) + " : "),
                                                            op = pyast.Add(),
                                                            right = pyast.BinOp(left = place_type.dump_expr(env, self_var),
                                                                              op = pyast.Add(),
                                                                              right = pyast.Str(', '))
                                                            ) ]
                                           )
                                  )
                             )

        builder.emit(pyast.stmt(pyast.E('%s.append("}")' % list_var.name)))
        builder.emit_Return(pyast.E('"\\n".join({})'.format(list_var.name)))

        builder.end_FunctionDef()
        return builder.ast()
