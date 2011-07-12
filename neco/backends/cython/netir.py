""" Cython ast compiler. """

import cyast
import cPickle as cPickle
import StringIO
import neco.core.netir as coreir
from neco.core.info import *
from astutils import Builder, E, A, to_ast, stmt
from nettypes import is_cython_type, type2str
################################################################################

class CompilerVisitor(coreir.CompilerVisitor):
    """ Cython ast compiler visitor class. """

    backend = "cython"

    def __init__(self, env):
        self.env = env

    def compile_Print(self, node):
        return [] # cyast.Print(values = [cyast.Str(node.message)], nl=True)

    def compile_Comment(self, node):
        return cyast.NComment(message=node.message)

    def compile_If(self, node):
        return Builder.If( test = self.compile(node.condition),
                           body = [ self.compile(node.body) ],
                           orelse = [ self.compile(node.orelse) ] )

    def compile_Compare(self, node):
        return Builder.Compare(left = self.compile(node.left),
                               ops = [ self.compile(op) for op in node.ops ],
                               comparators = [ self.compile(comparator) for comparator in node.comparators ])

    def compile_EQ(self, node):
        return cyast.Eq()

    def compile_CheckTuple(self, node):
        tuple_info = node.tuple_info
        test = E( "isinstance({tuple_name}, tuple) and len({tuple_name}) == {length}"
                  .format(tuple_name = node.tuple_name, length = repr(len(tuple_info))))
        return Builder.If(test, body = self.compile(node.body))

    def compile_CheckType(self, node):
        type_info = node.type
        if type_info.is_AnyType:
            return self.compile(node.body)

        test = E("isinstance").call([E(node.variable.name), E(type2str(type_info))])
        return Builder.If( test = test, body = self.compile(node.body) )

    def compile_Match(self, node):
        tuple_info = node.tuple_info
        seq = []
        seq.append( Builder.Tuple([ E(name) for name in tuple_info.base() ]).assign(tuple_info.name) )
        cur = None
        for component in tuple_info.components:
            if component.is_Value:
                n = Builder.If( test = Builder.Compare( left = E(component.name),
                                                        ops = [ cyast.Eq() ],
                                                        comparators = [ E(repr(component.raw)) ] ), # TO DO unify value & pickle
                                orelse = [] )
                if cur == None:
                    cur = n
                    seq.append(n)
                else:
                    cur.body = [n]
                    cur = n

        if cur != None:
            cur.body = [ self.compile( node.body ) ]
        else:
            seq.append(self.compile( node.body ))

        return seq


    def compile_Assign(self, node):
        return E(node.variable.name).assign(self.compile(node.expr))

    def compile_Value(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.gen_build_token(self.env, node.value.raw)

    def compile_Pickle(self, node):
        output = StringIO.StringIO()
        cPickle.dump(node.obj, output)
        pickle_str = output.getvalue()
        return E("cPickle.load(StringIO.StringIO(" + repr(pickle_str) + "))")

    def compile_FlushIn(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        return [ E(node.token_name).assign( self.env.marking_type.gen_get_place( env = self.env,
                                                                                 marking_name = node.marking_name,
                                                                                 place_name = node.place_name) ),
                 destination_place.gen_clear_function_call( env = self.env, marking_name = node.marking_name ) ]

    def compile_FlushOut(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        multiset = self.compile(node.token_expr)
        return destination_place.add_items( env = self.env,
                                            multiset = multiset,
                                            marking_name = node.marking_name )

    def gen_tuple(self, tuple_info):
        elts = []
        for info in tuple_info:
            if info.is_Value:
                elts.append( E(repr(info.raw)) )
            elif info.is_Variable:
                elts.append( cyast.Name( id = info.name ) )
            elif info.is_Tuple:
                elts.append( self.gen_tuple( info ) )
            elif info.is_Expression:
                elts.append( E(info.raw) )
            else:
                raise NotImplementedError, info.component.__class__

        return Builder.Tuple( elts = elts )

    def compile_TupleOut(self, node):
        tuple_info = node.tuple_info
        tuple = self.gen_tuple(tuple_info)
        return self.env.marking_type.gen_add_token_function_call(env = self.env,
                                                                 token = tuple,
                                                                 marking_name = node.marking_name,
                                                                 place_name = node.place_name)

    def compile_NotEmpty(self, node):
        return self.env.marking_type.gen_not_empty_function_call( env = self.env,
                                                                  marking_name = node.marking_name,
                                                                  place_name = node.place_name )

    def compile_TokenEnumeration(self, node):
        index = node.use_index
        if index:
            size_var = self.var_helper.fresh( True, base = 'tmp' )
            place_size = self.env.marking_type.gen_get_place_size( env = self.env,
                                                                   marking_name = node.marking_name,
                                                                   place_name = node.place_name )

            get_token = self.env.marking_type.gen_get_token( env = self.env,
                                                             marking_name = node.marking_name,
                                                             place_name = node.place_name,
                                                             index = index )
            return [ E( size_var ).assign( place_size ),
                     Builder.CFor(start = E( 0 ),
                                  start_op = cyast.LtE(),
                                  target = E( index ),
                                  stop_op = cyast.Lt(),
                                  stop = E( size_var ),
                                  body = [ E( node.token_name ).assign( get_token ),
                                           self.compile(node.body) ],
                                  orelse = [] ) ]
        else:
            return Builder.For( target = E(node.token_name),
                                iter = self.env.marking_type.gen_iterable_place( env = self.env,
                                                                                 marking_name = node.marking_name,
                                                                                 place_name = node.place_name),
                                body = [ self.compile(node.body) ])

    def compile_GuardCheck(self, node):
        return Builder.If( test = self.compile(node.condition),
                           body = self.compile(node.body),
                           orelse = [] )

    def compile_PyExpr(self, node):
        assert isinstance(node.expr, ExpressionInfo)
        return E(node.expr.raw)

    def compile_Name(self, node ):
        return E(node.name)

    def compile_FunctionCall(self, node):
        return E(node.function_name).call([ self.compile(arg) for arg in node.arguments ])

    def compile_ProcedureCall(self, node):
        return stmt(E(node.function_name).call([ self.compile(arg) for arg in node.arguments ]))

    def compile_MarkingCopy(self, node):
        return self.env.marking_type.gen_copy( env = self.env,
                                               src_marking_name = node.src_name,
                                               dst_marking_name = node.dst_name,
                                               modified_places = node.mod )

    def compile_AddMarking(self, node):
        return stmt( self.env.marking_set_type.gen_add_marking_function_call(env = self.env,
                                                                             markingset_name = node.markingset_name,
                                                                             marking_name = node.marking_name) )

    def compile_AddToken(self, node):
        return self.env.marking_type.gen_add_token_function_call(env = self.env,
                                                                 token = self.compile(node.token_expr),
                                                                 marking_name = node.marking_name,
                                                                 place_name = node.place_name)

    def compile_RemToken(self, node):
        index = node.use_index
        if index:
            return self.env.marking_type.gen_remove_by_index_function_call(env = self.env,
                                                                           token = self.compile(node.token_expr),
                                                                           marking_name = node.marking_name,
                                                                           place_name = node.place_name,
                                                                           index = index)
        else:
            return self.env.marking_type.gen_remove_token_function_call(env = self.env,
                                                                        token = self.compile(node.token_expr),
                                                                        marking_name = node.marking_name,
                                                                        place_name = node.place_name)

    def compile_RemTuple(self, node):
        return self.env.marking_type.gen_remove_token_function_call(env = self.env,
                                                                    token = self.compile(node.tuple_expr),
                                                                    marking_name = node.marking_name,
                                                                    place_name = node.place_name)

    def compile_Token(self, node):
        return self.env.marking_type.gen_build_token(env = self.env,
                                                     place_name = node.place_name,
                                                     value = node.value)

    def compile_SuccT(self, node):
        self.var_helper = node.transition_info.variable_helper

        stmts = [ self.compile( node.body ) ]

        decl = []
        inputs = node.transition_info.inputs
        for input in inputs:
            if input.is_Variable:
                variable = input.variable
                place_info = input.place_info

                type = self.env.marking_type.get_place_type_by_name(place_info.name).token_type

                if (not type.is_UserType) or (is_cython_type(type)):
                    decl.append( Builder.CVar( variable.name ).type( type2str(type) ) )
            elif input.is_Test:
                inner = input.inner
                if inner.is_Variable:
                    if (not inner.type.is_UserType) or (is_cython_type(inner.type)):
                        decl.append( Builder.CVar( name = inner.name ).type( type2str(inner.type) ) )
        inter_vars = node.transition_info.intermediary_variables
        for var in inter_vars:
            if (not var.type.is_UserType) or is_cython_type( var.type ):
                decl.append( Builder.CVar( name = var.name ).type( type2str(var.type) ) )

        return to_ast( Builder.FunctionDef(name = node.function_name,
                                           args = (A(node.markingset_name, type = "set")
                                                   .param(node.marking_name, type = "Marking")),
                                           body = stmts,
                                           lang = cyast.CDef( public = False ),
                                           returns = cyast.Name("void"),
                                           decl = decl) )


    def compile_SuccP(self, node):
        env = self.env
        stmts = [ self.compile( node.body ) ]
        return Builder.FunctionDef(name = node.function_name,
                                   args = (A(node.markingset_name, type = "set")
                                           .param(node.marking_name, type = "Marking")),
                                   body = stmts,
                                   lang = cyast.CDef( public = False ),
                                   returns = E("void"))

    def compile_Succs(self, node):
        body = []
        body.extend( self.compile( node.body ) )
        body.append( E("return " + node.markingset_variable_name) )
        f1 = Builder.FunctionCpDef( name = node.function_name,
                                    args = A(node.marking_argument_name, type = "Marking"),
                                    body = body,
                                    returns = cyast.Name("set"),
                                    decl = [ (Builder.CVar(node.markingset_variable_name)
                                              .type('set')
                                              .init(self.env.marking_set_type.gen_new_marking_set(self.env))) ])


        body = [ E("l = ctypes_ext.neco_list_new()") ]

        body.append( cyast.For(target=to_ast(E("e")),
                               iter=to_ast(E("succs(m)")),
                               body=[ to_ast(stmt(E("ctypes_ext.__Pyx_INCREF(e)"))),
                                      cyast.Expr( cyast.Call(func=to_ast(E("ctypes_ext.neco_list_push_front")),
                                                             args=[to_ast(E("l")), cyast.Name("e")],
                                                             keywords=[],
                                                             starargs=None,
                                                             kwargs=None) ) ] ) )

        body.append( E("return l") )

        f2 = Builder.FunctionCDef( name = "neco_succs",
                                   args = A("m", type = "Marking"),
                                   body = body,
                                   returns = cyast.Name("ctypes_ext.neco_list*"),
                                   decl = [ Builder.CVar("l").type("ctypes_ext.neco_list*"),
                                            Builder.CVar("e").type("Marking")])

        return [f1, f2]



    def compile_Init(self, node):
        new_marking = E( node.marking_name ).assign( self.env.marking_type.gen_alloc_marking_function_call(self.env) )
        return_stmt = E( "return {mn}".format(mn = node.marking_name))

        stmts = [new_marking]
        stmts.extend( self.compile(node.body) )
        stmts.append( return_stmt )

        f1 = Builder.FunctionCpDef( name = node.function_name,
                                  body = stmts,
                                  returns = cyast.Name("Marking"),
                                  decl = [ cyast.CVar( node.marking_name, type = "Marking" )])

        f2 = Builder.FunctionCDef( name = "neco_init",
                                   body = [ stmts ],
                                   returns = cyast.Name("Marking"),
                                   decl = [ cyast.CVar( node.marking_name, type = "Marking" )])

        return [f1, f2]

    ################################################################################
    # opts
    ################################################################################
    def compile_OneSafeTokenEnumeration(self, node):
        getnode = E( node.token_name ).assign( self.env.marking_type.gen_get_place( env = self.env,
                                                                                    marking_name = node.marking_name,
                                                                                    place_name = node.place_name) )

        place_type = self.env.marking_type.get_place_type_by_name( node.place_name )

        ifnode = Builder.If( test = place_type.gen_not_empty_function_call(self.env, marking_name = node.marking_name),
                             body = [ getnode, self.compile( node.body ) ] )
        return [ to_ast(ifnode) ]

    def compile_BTTokenEnumeration(self, node):
        ifnode = Builder.If(test = Builder.Compare( left = to_ast(self.env.marking_type.gen_get_place( env = self.env,
                                                                                                       marking_name = node.marking_name,
                                                                                                       place_name = node.place_name)),
                                                    ops = [ cyast.Gt() ],
                                                    comparators = [ cyast.Num( n = 0 ) ] ),
                            body = [ self.compile( node.body ) ])
        return [ ifnode ]

    def compile_BTOneSafeTokenEnumeration(self, node):
        body = [ self.compile( node.body ) ]
        ifnode = Builder.If(test = self.env.marking_type.gen_get_place( env = self.env,
                                                                        marking_name = node.marking_name,
                                                                        place_name = node.place_name ),
                            body = body )
        return [ ifnode ]

    ################################################################################
    # Flow elimination
    ################################################################################

    def compile_FlowCheck(self, node):
        return self.env.marking_type.gen_check_flow(env=self.env,
                                                    marking_name=node.marking_name,
                                                    place_info=node.place_info,
                                                    current_flow=node.current_flow)

    def compile_ReadFlow(self, node):
        return self.env.marking_type.gen_read_flow(env=self.env,
                                                   marking_name=node.marking_name,
                                                   process_name=node.process_name)

    def compile_UpdateFlow(self, node):
        return self.env.marking_type.gen_update_flow(env=self.env,
                                                     marking_name=node.marking_name,
                                                     place_info=node.place_info)

################################################################################
# EOF
################################################################################
