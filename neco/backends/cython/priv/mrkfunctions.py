from neco.core.info import VariableProvider, TypeInfo
from neco.core.nettypes import MarkingTypeMethodGenerator
import cyast

def _gen_C_compare_aux(builder, tests):
    while tests:
        test = tests.pop()
        # l - r == 0 ?:
        builder.emit(cyast.Assign(targets=[cyast.Name("tmp")],
                                  value=test))
        builder.begin_If(cyast.Compare(left=cyast.Name("tmp"),
                                       ops=[cyast.Lt()],
                                       comparators=[cyast.Num(0)])
                         )
        builder.emit_Return(cyast.Num(-1))
        # l - r < 0 ?:
        builder.begin_Elif(cyast.Compare(left=cyast.Name("tmp"),
                                         ops=[cyast.Gt()],
                                         comparators=[cyast.Num(0)])
                           )
        builder.emit_Return(cyast.Num(1))
        builder.end_If()
        builder.end_If()

    builder.emit_Return(cyast.Num(0))

class CompareGenerator(MarkingTypeMethodGenerator):
    def generate(self, env):
        marking_type = env.marking_type

        vp = VariableProvider()
        builder = cyast.Builder()
        left_marking_var  = vp.new_variable(marking_type.type, "self")
        right_marking_var = vp.new_variable(marking_type.type, "other")

        builder.begin_FunctionCDef( name = "neco_marking_compare",
                                    args = (cyast.A("self", type = env.type2str(marking_type.type))
                                            .param(right_marking_var.name, type = env.type2str(marking_type.type))),
                                    returns = cyast.E("int"),
                                    public=True, api=True,
                                    decl = [ cyast.Builder.CVar( name = 'tmp', type = env.type2str(TypeInfo.get('Int'))) ] )

        compared = set()
        tests = []
        if marking_type.chunk_manager.packed_bits() > 0:
            attr, _, count = marking_type.chunk_manager.packed_attribute()
            compared.add(attr)
            for index in range(0, count):
                left = cyast.E("{object}.{attribute}[{index}]".format(object=left_marking_var.name,
                                                                      attribute=attr,
                                                                      index=index)) 
                right = cyast.E("{object}.{attribute}[{index}]".format(object=right_marking_var.name,
                                                                       attribute=attr,
                                                                       index=index))
                tests.append(cyast.BinOp(left=left,
                                         op=cyast.Sub(),
                                         right=right))

        for place_type in marking_type.place_types.itervalues():
            if place_type.get_attribute_name() in compared:
                continue
            tests.append(place_type.compare_expr(env,
                                                 left_marking_var=left_marking_var,
                                                 right_marking_var=right_marking_var)
                         )

        tests.reverse()
        _gen_C_compare_aux(builder, tests)
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

#
#def _gen_C_marked_aux(self, builder, tests, rs):
#    try:
#        test = tests.pop()
#        r = rs.pop()
#        # l - r == 0 ?:
#        builder.begin_If(test)
#        builder.emit_Return(r)
#        # else l - r > 0:
#        builder.begin_Else()
#        self._gen_C_marked_aux(builder, tests, rs)
#        builder.end_If()
#    except IndexError:
#        builder.emit_Return(cyast.Num(0))
#
#class MarkedGenerator(MarkingTypeMethodGenerator):
#    
#    def generate(self, env):
#        marking_type = env.marking_type
#
#        builder = cyast.Builder()
#        left_marking_name  = 'self'
#        right_marking_name = 'other'
#        builder.begin_FunctionCDef( name = 'neco_marked',
#                                    args = (cyast.A('self', type = env.type2str(marking_type.type))
#                                            .param('place_name', type='object')),
#                                    returns = cyast.Name('int'),
#                                    public=True, api=True)
#
#        i = 0
#        tests = []
#        rs = []
#        for name, place_type in marking_type.place_types.iteritems():
#            id = marking_type.id_provider.get(place_type)
#            tests.append(cyast.Compare(left=cyast.E(repr(name)),
#                                       ops=[cyast.Eq()],
#                                       comparators=[cyast.Name('place_name')])
#                         )
#            rs.append( place_type.not_empty_expr(env, 'self') )
#
#        env._gen_C_marked_aux(builder, tests, rs)
#        builder.end_FunctionDef()
#        return cyast.to_ast(builder)

class DumpGenerator(MarkingTypeMethodGenerator):

    def generate(self, env):
        builder = cyast.Builder()
        builder.begin_FunctionCDef(name = "neco_marking_dump",
                                   args = cyast.A("self", type="Marking"),
                                   returns = cyast.Name("char*"),
                                   decl = [ cyast.Builder.CVar( "c_string", type = "char*" ) ],
                                   public=True, api=True)
        builder.emit(cyast.E("py_unicode_string = str(self)"))
        builder.emit(cyast.E("py_byte_string = py_unicode_string.encode('UTF-8')"))
        builder.emit(cyast.E("c_string = py_byte_string"))
        builder.emit_Return(cyast.E("c_string"))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

class HashGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        builder = cyast.Builder()
        builder.begin_FunctionCDef( name = "neco_marking_hash",
                                    args = cyast.A("self", type = "Marking"),
                                    returns = cyast.E("int"),
                                    public=True, api=True)
        builder.emit_Return(cyast.E('self.__hash__()'))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)

class CopyGenerator(MarkingTypeMethodGenerator):
    
    def generate(self, env):
        builder = cyast.Builder()
        builder.begin_FunctionCDef( name = "neco_marking_copy",
                                    args = cyast.A("self", type = "Marking"),
                                    returns = cyast.E("Marking"),
                                    public=True, api=True)
        builder.emit_Return(cyast.E('self.copy()'))
        builder.end_FunctionDef()
        return cyast.to_ast(builder)
