from neco.core.info import VariableProvider
from neco.core.nettypes import MarkingTypeMethodGenerator
import pyast

class InitGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        function = pyast.FunctionDef(name = '__init__',
                                     args = pyast.A('self').param('alloc', default = 'True').ast())

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name = 'self')

        if_block = pyast.If(test = pyast.Name(id = 'alloc'))

        for place_type in marking_type.place_types.values():
            if_block.body.append(place_type.new_place_stmt(env, self_var))

        function.body = [ pyast.E('self.{} = None'.format(marking_type.get_field('_hash').name)), if_block ]
        return function

class CopyGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name = 'self')
        marking_var = vp.new_variable(marking_type.type)

        function = pyast.FunctionDef(name = 'copy',
                                     args = pyast.A(self_var.name).param('alloc', default = 'True').ast())

        tmp = [ pyast.Assign(targets = [pyast.Name(id = marking_var.name)],
                             value = pyast.E('Marking(False)')) ]

        for place_type in marking_type.place_types.values():
            tmp.append(place_type.copy_stmt(env, marking_var, self_var))

        tmp.append(pyast.Return(pyast.Name(id = marking_var.name)))
        function.body = tmp
        return function

class EqGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, 'self')
        other_var = vp.new_variable(marking_type.type, 'other')

        function = pyast.FunctionDef(name = '__eq__', args = pyast.A(self_var.name).param(other_var.name).ast())

        return_str = "return ("
        for i, place_type in enumerate(marking_type.place_types.values()):
            if i > 0:
                return_str += " and "
            field = place_type.field
            return_str += "({} == {})".format(field.access_from(self_var),
                                              field.access_from(other_var))
        return_str += ")"

        function.body = [ pyast.E(return_str) ]
        return function

class HashGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, 'self')

        builder = pyast.Builder()
        builder.begin_FunctionDef(name = '__hash__', args = pyast.A(self_var.name).ast())

        builder.begin_If(test = pyast.E('self.{} != None'.format(marking_type.get_field('_hash').name)))
        builder.emit_Return(pyast.E('self.{}'.format(marking_type.get_field('_hash').name)))
        builder.end_If()

        builder.emit(pyast.E('h = 0'))

        for (name, place_type) in marking_type.place_types.iteritems():
            magic = hash(name)
            builder.emit(pyast.E('h = (h << 1) ^ hash(' + place_type.field.access_from(self_var) + ') * ' + str(magic)))

        # builder.emit(pyast.E("print h"))
        builder.emit_Return(pyast.E("h"))
        builder.end_FunctionDef()
        return builder.ast()

class ReprGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = pyast.Builder()
        builder.begin_FunctionDef(name = "__repr__", args = pyast.A("self").ast())

        builder.emit(pyast.E('s = "hdict({"'))
        for (i, (place_name, place_type)) in enumerate(items):
            tmp = ',\n ' if i > 0 else ''
            builder.emit(pyast.AugAssign(target = pyast.Name(id = 's'),
                                       op = pyast.Add(),
                                       value = pyast.BinOp(left = pyast.Str(s = tmp + "'" + place_name + "' : "),
                                                           op = pyast.Add(),
                                                           right = pyast.E('repr(self.' + place_type.field.name + ')')
                                                           )
                                       )
                         )
        builder.emit(pyast.E('s += "})"'))
        builder.emit_Return(pyast.E('s'))

        builder.end_FunctionDef()
        return builder.ast()

class DumpGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name = 'self')
        list_var = vp.new_variable()

        builder = pyast.Builder()
        builder.begin_FunctionDef(name = "__dump__", args = pyast.A(self_var.name).ast())

        builder.emit(pyast.E('%s = ["{"]' % list_var.name))
        for (place_name, place_type) in items:
            if place_type.is_ProcessPlace:
                builder.emit(place_type.dump_expr(env, self_var, list_var))
            else:
                builder.emit(pyast.stmt(pyast.Call(func = pyast.E('{}.append'.format(list_var.name)),
                                           args = [ pyast.BinOp(left = pyast.Str(s = repr(place_name) + " : "),
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

class LineDumpGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type

        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, name = 'self')
        list_var = vp.new_variable()

        builder = pyast.Builder()
        builder.begin_FunctionDef(name = "__line_dump__", args = pyast.A(self_var.name).ast())

        builder.emit(pyast.E('%s = ["{"]' % list_var.name))
        for (place_name, place_type) in items:
            if place_type.is_ProcessPlace:
                builder.emit(place_type.dump_expr(env, self_var, list_var))
            else:
                builder.begin_If(test = place_type.place_expr(env, self_var))
                builder.emit(pyast.stmt(pyast.Call(func = pyast.E('{}.append'.format(list_var.name)),
                                           args = [ pyast.BinOp(left = pyast.Str(s = repr(place_name) + " : "),
                                                              op = pyast.Add(),
                                                              right = pyast.BinOp(left = place_type.dump_expr(env, self_var),
                                                                                  op = pyast.Add(),
                                                                                  right = pyast.Str(', '))
                                                              ) ]
                                           )
                                  )
                             )
                builder.end_If()

        builder.emit(pyast.stmt(pyast.E('%s.append("}")' % list_var.name)))
        builder.emit_Return(pyast.E('"".join({})'.format(list_var.name)))

        builder.end_FunctionDef()
        return builder.ast()

#
# class DotGenerator(MarkingTypeMethodGenerator):
#
#    def generate(self, env):
#        marking_type = env.marking_type
#
#        items = list(marking_type.place_types.iteritems())
#        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))
#
#        vp = VariableProvider()
#        self_var = vp.new_variable(marking_type.type, name='self')
#        list_var = vp.new_variable()
#
#        builder = pyast.Builder()
#        builder.begin_FunctionDef( name = "__dot__", args = pyast.A(self_var.name).ast() )
#
#        builder.emit( pyast.E('%s = ["[shape=record,label=\\\"{"]' % list_var.name) )
#        for i, (place_name, place_type) in enumerate(items):
#            if i > 0:
#                builder.emit( pyast.stmt( pyast.E('%s.append("\l|")' % list_var.name) ) )
#
#            if place_type.is_ProcessPlace:
#                builder.emit( place_type.dump_expr(env, self_var, list_var) )
#            else:
#                builder.emit(pyast.stmt(pyast.Call(func=pyast.E('{}.append'.format(list_var.name)),
#                                           args=[ pyast.BinOp(left = pyast.Str(s = repr(place_name) + " : "),
#                                                            op = pyast.Add(),
#                                                            right = pyast.BinOp(left = pyast.B('dot_protect_string').call([place_type.dump_expr(env, self_var)]).ast(),
#                                                                              op = pyast.Add(),
#                                                                              right = pyast.Str(', '))
#                                                            ) ]
#                                           )
#                                  )
#                             )
#
#        builder.emit(pyast.stmt(pyast.E('%s.append("\l}\\\"]")' % list_var.name)))
#        builder.emit_Return(pyast.E('"".join({})'.format(list_var.name)))
#
#        builder.end_FunctionDef()
#        return builder.ast()
