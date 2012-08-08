from neco.core.info import VariableProvider, TypeInfo
from neco.core.nettypes import MarkingTypeMethodGenerator
import cyast
import sys

class DeallocGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        marking_type = env.marking_type
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, "self")

        builder = cyast.Builder()
        builder.begin_FunctionDef( name = "__dealloc__",
                                   args = cyast.A("self", type="Marking") )

        for place_type in marking_type.place_types.itervalues():
            if place_type.is_packed or place_type.is_helper:
                pass
            else:
                builder.emit(place_type.delete_stmt(env = env,
                                                    marking_var = self_var))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

class InitGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, "self")

        builder = cyast.Builder()
        builder.begin_FunctionDef( name = "__cinit__",
                                   args = cyast.A("self").param("alloc", default = "False"))

        builder.begin_If( cyast.Name('alloc') )

        initialized = set()
        # packed
        if marking_type.chunk_manager.packed_bits() > 0:
            (attr_name, _, count) = marking_type.chunk_manager.packed_attribute()
            initialized.add(attr_name)
            for index in range(0, count):
                builder.emit(cyast.E("{object}.{attribute}[{index!s}] = 0".format(object=self_var.name,
                                                                                 attribute=attr_name,
                                                                                 index=index)))

        # init other places
        for place_type in marking_type.place_types.itervalues():
            attr_name = place_type.get_attribute_name()
            if attr_name in initialized:
                continue
            ################################################################################
            # assumes that packed types will always be initialized to 0 !!!
            ################################################################################
            builder.emit(place_type.new_place_stmt(env, self_var))
            builder.emit(builder.Comment("{} - 1s: {} - {}".format(place_type.info.name, place_type.one_safe(), place_type.info.type)))
        builder.end_If()
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

class CopyGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type

        builder = cyast.Builder()
        vp = VariableProvider()
        self_var = vp.new_variable(type=marking_type.type, name='self')
        marking_var = vp.new_variable(type=marking_type.type, name='m')

        builder.begin_FunctionCDef( name = "copy",
                                    args = cyast.A(self_var.name),
                                    returns = cyast.E(env.type2str( marking_type.type )),
                                    decl = [ cyast.Builder.CVar( name = 'm', type = 'Marking' ) ])


        builder.emit( cyast.E('m = Marking()') )


        copied = set()
        # copy packed
        print marking_type.chunk_manager.packed_bits()
        if marking_type.chunk_manager.packed_bits() > 0:
            attr_name, _, count = marking_type.chunk_manager.packed_attribute()
            print attr_name
            copied.add(attr_name)
            for i in range(count):
                target_expr = cyast.E('{object}.{attribute}[{index!s}]'.format(object=marking_var.name,
                                                                               attribute=attr_name,
                                                                               index=i))
                value_expr = cyast.E('{object}.{attribute}[{index!s}]'.format(object=self_var.name,
                                                                               attribute=attr_name,
                                                                               index=i))

                builder.emit( cyast.Assign(targets=[target_expr],
                                           value=value_expr) )

        # copy modified attributes
        for place_type in marking_type.place_types.itervalues():
            attr_name = place_type.get_attribute_name()
            if attr_name in copied:
                continue
            print attr_name
            target_expr = cyast.E('{object}.{attribute}'.format(object=marking_var.name,
                                                                attribute=attr_name))

            builder.emit(place_type.copy_stmt(env, marking_var, self_var))


        builder.emit_Return(cyast.E("m"))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)


class RichcmpGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        builder = cyast.Builder()
        left_marking_name  = 'self'
        right_marking_name = 'other'
        op_name = 'op'
        builder.begin_FunctionDef( name = '__richcmp__',
                                   args = (cyast.A('self', type = env.type2str(marking_type.type))
                                           .param(right_marking_name, type = env.type2str(marking_type.type))
                                           .param(op_name, type = env.type2str(TypeInfo.get('Int')))) )
        builder.emit_Return(cyast.Compare(left=cyast.Call(func=cyast.Name('neco_marking_compare'),
                                                          args=[cyast.Name(left_marking_name),
                                                                cyast.Name(right_marking_name)]
                                                          ),
                                          ops=[cyast.Eq()],
                                          comparators=[cyast.Num(0)])
                            )
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

class HashGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, 'self')

        builder = cyast.Builder()
        builder.begin_FunctionDef( name = "__hash__",
                                   args = cyast.A("self", type = "Marking"),
                                   decl = [ cyast.Builder.CVar( name = 'h', type = 'int' ) ])

        builder.emit( cyast.E("h = 0xDEADDAD") )
        mult = 0xBADBEEF
        i = 0

        hashed = set()
        if marking_type.chunk_manager.packed_bits() > 0:
            attr_name, _, count = marking_type.chunk_manager.packed_attribute()
            hashed.add(attr_name)
            attr = "{}.{}".format(self_var.name, attr_name)
            
            for index in range(0, count):
                attr_expr = cyast.E('{!s}[{!s}]'.format(attr, index))
                builder.emit( cyast.Assign(targets=[cyast.Name('h')],
                                           value=cyast.BinOp(left = cyast.BinOp(left=cyast.Name('h'),
                                                                                op=cyast.BitXor(),
                                                                                right=attr_expr ),
                                                             op = cyast.Mult(),
                                                             right = cyast.Num(mult) ) ) )
                mult = (mult + (82520L + i + i)) % sys.maxint
                i += 1

        for place_type in marking_type.place_types.itervalues():
#            if place_type.is_packed or place_type.is_helper:
#                pass
#            else:
#                if place_type.type.is_Int or place_type.type.is_Short or place_type.type.is_Char:
#                    native_place = marking_type.id_provider.get(place_type)
#                    builder.emit(cyast.E('h = (h ^ self.{place_name}) * {mult}'.format(place_name=native_place,
#                                                                                 mult=mult))
#                                 )
#                else:
            if place_type.get_attribute_name() in hashed:
                continue
            
            place_hash = place_type.hash_expr(env, marking_var = self_var)
            builder.emit(cyast.Assign(targets=[cyast.Name('h')],
                                      value=cyast.BinOp(left=cyast.BinOp(left=cyast.Name('h'),
                                                                         op=cyast.BitXor(),
                                                                         right=place_hash),
                                                        op=cyast.Mult(),
                                                        right=cyast.Num(mult))
                                      )
                         )
            mult = (mult + (82521 * i + i)) % sys.maxint
            i += 1

        builder.emit_Return(cyast.E("h"))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

def StrGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        builder = cyast.Builder()
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, "self")

        builder.begin_FunctionDef( name = "__str__",
                                   args = cyast.A(self_var.name, type=env.type2str(marking_type.type)))
        visited = set()
        builder.emit(cyast.E('s = ""'))
        first = True
        for (place_name, place_type) in items:

            place_type = marking_type.get_place_type_by_name(place_name)

            if not place_type.is_revelant:
                continue

            if not first:
                builder.emit(cyast.E('s += ", "'))
            first = False

            builder.emit(cyast.E( 's += %s' % repr(place_name + ': ')))
            builder.emit(cyast.AugAssign(target=cyast.Name('s'),
                                         op=cyast.Add(),
                                         value=cyast.Call(func=cyast.Name("str"),
                                                          args=[place_type.dump_expr(env, self_var)])
                                         )
                         )

        builder.emit_Return(cyast.E('s'))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

class ReprGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))
        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, "self")

        builder = cyast.Builder()
        builder.begin_FunctionDef( name = "__repr__",
                                   args = cyast.A(self_var.name, type=env.type2str(marking_type.type)) )
        builder.emit(cyast.E('s = "hdict({"'))

        visited = set()
        for i,(place_name, place_type) in enumerate(items):
            tmp = ',\n' if i > 0 else ''
            if place_type.is_packed:
                if place_type.pack in visited:
                    continue
                place = marking_type.gen_get_place(env, marking_var = self_var, place_name = place_name)
                str_call = cyast.E('str').call([place])
                builder.emit( cyast.E('s').add_assign( cyast.E("{tmp}'{place_name}' :".format(tmp=tmp, place_name=place_name)).add(str_call)) )
            else:
                builder.emit( cyast.E('s').add_assign( cyast.E( tmp + "'" + place_name + "' : " ).add( cyast.E( 'repr(self.{place})'.format(place = marking_type.id_provider.get(place_type))) ) ) )


        builder.emit( cyast.E('s += "})"') )
        builder.emit_Return(cyast.E("s"))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

class DumpExprGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        marking_type = env.marking_type
        
        items = list(marking_type.place_types.iteritems())
        items.sort(lambda (n1, t1), (n2, t2) : cmp(n1, n2))

        vp = VariableProvider()
        self_var = vp.new_variable(marking_type.type, 'self')
        builder = cyast.Builder()
        builder.begin_FunctionDef(name='__dump__',
                                  args=cyast.A('self'))

        builder.emit(cyast.E('s = ["{"]'))
        for (i, (place_name, place_type)) in enumerate(items):
            if place_type.is_revelant:
                builder.emit(cyast.stmt(cyast.Call(func = cyast.E('s.append'),
                                                   args = [ cyast.BinOp(left=cyast.Str(s=repr(place_name) + " : "),
                                                                op=cyast.Add(),
                                                                right=cyast.BinOp(left=place_type.dump_expr(env, self_var),
                                                                                  op=cyast.Add(),
                                                                                  right=cyast.Str(s=',')
                                                                                  ) ) ]
                                            )
                                  )
                             )
        builder.emit(cyast.stmt(cyast.E('s.append("}")')))
        builder.emit_Return(cyast.E('"\\n".join(s)'))

        builder.end_FunctionDef()
        return cyast.to_ast(builder)
