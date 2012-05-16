""" Cython ast compiler. """

import cPickle as cPickle
import StringIO
import neco.core.netir as coreir
from neco.core.info import *
import cyast
from cyast import * # Builder, E, A, to_ast, stmt
from nettypes import is_cython_type, type2str, CVarSet, Env

################################################################################

class CompilerVisitor(coreir.CompilerVisitor):
    """ Cython ast compiler visitor class. """

    backend = "cython"

    def __init__(self, env):
        self.env = env

    def compile_Return(self, node):
        return [ cyast.Return(self.compile(node.expr)) ]

    def compile_Print(self, node):
        return [cyast.Print(values = [cyast.Str(node.message)], nl=True)]

    def compile_Comment(self, node):
        return cyast.NComment(message=node.message)

    def compile_If(self, node):
        return cyast.If( test = self.compile(node.condition),
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
                  .format(tuple_name = node.tuple_var.name, length = repr(len(tuple_info))))
        return Builder.If(test, body = self.compile(node.body))

    def compile_CheckType(self, node):
        type_info = node.type
        if type_info.is_AnyType:
            return self.compile(node.body)

        test = cyast.Call(func=cyast.Name('isinstance'),
                          args=[E(node.variable.name), E(type2str(type_info))])

        return Builder.If( test = test, body = self.compile(node.body) )

    def compile_Match(self, node):
        tuple_info = node.tuple_info
        seq = []

        component_names = [ token_info.data['local_variable'].name for token_info in tuple_info ]
        seq.append( cyast.Assign(targets = [ cyast.Tuple([ E(name) for name in component_names ])],
                                 value = cyast.Name(tuple_info.data['local_variable'].name)) )
        cur = None
        for component in tuple_info.components:
            if component.is_Value:
                #self.try_declare_cvar(component.data['local_variable'].name, component.type)
                n = Builder.If( test = Builder.Compare( left = E(component.data['local_variable'].name),
                                                        ops = [ cyast.Eq() ],
                                                        comparators = [ E(repr(component.raw)) ] ), # TO DO unify value & pickle
                                orelse = [] )
                if cur == None:
                    cur = n
                    seq.append(n)
                else:
                    cur.body = [n]
                    cur = n
            elif component.is_Variable:
                self.env.try_declare_cvar(component.data['local_variable'].name, component.type)

        if cur != None:
            cur.body = [ self.compile( node.body ) ]
        else:
            seq.append(self.compile( node.body ))

        return seq


    def compile_Assign(self, node):
        self.env.try_declare_cvar(node.variable.name, node.variable.type)

        return cyast.Assign(targets=[cyast.Name(node.variable.name)],
                            value=self.compile(node.expr))

    def compile_Value(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.token_expr(self.env, node.value.raw)

    def compile_Pickle(self, node):
        output = StringIO.StringIO()
        cPickle.dump(node.obj, output)
        pickle_str = output.getvalue()
        return E("cPickle.load(StringIO.StringIO(" + repr(pickle_str) + "))")

    def compile_FlushIn(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        return [cyast.Assign(targets=[cyast.Name(node.token_var.name)],
                             value=self.env.marking_type.gen_get_place(env = self.env,
                                                                       marking_var = node.marking,
                                                                       place_name = node.place_name)
                             ),
                destination_place.clear_stmt(env=self.env,
                                             marking_var=node.marking )
                ]

    def compile_FlushOut(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name( node.place_name )
        multiset = self.compile( node.token_expr )
        var = self.env.new_variable()
        return destination_place.add_items_stmt(env = self.env,
                                                multiset = multiset,
                                                marking_var = node.marking )

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

        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         token_expr = tuple_info,
                                         compiled_token = tuple,
                                         marking_var = node.marking)

    def compile_NotEmpty(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.not_empty_expr(env = self.env,
                                         marking_var = node.marking)

    def compile_TokenEnumeration(self, node):
        arc = node.arc
        marking_type = self.env.marking_type
        place_type = marking_type.get_place_type_by_name(node.place_name)
        if place_type.provides_by_index_access:
            index_var = arc.data['index']
            size_var = self.env.variable_provider.new_variable()

            self.env.try_declare_cvar(index_var.name, TypeInfo.Int)
            self.env.try_declare_cvar(node.token_var.name, node.token_var.type)
            self.env.try_declare_cvar(size_var.name, TypeInfo.Int)

            place_size = place_type.get_size_expr(env = self.env,
                                                  marking_var = node.marking)

            get_token = place_type.get_token_expr( env = self.env,
                                                   index_expr = index_var,
                                                   marking_var = node.marking,
                                                   compiled_index = Name(index_var.name) )


            return [ cyast.Assign(targets=[cyast.Name(size_var.name)],
                                  value=place_size),
                     Builder.CFor(start=cyast.Num(0),
                                  start_op=cyast.LtE(),
                                  target=cyast.Name(index_var.name),
                                  stop_op=cyast.Lt(),
                                  stop=cyast.Name(size_var.name),
                                  body=[ cyast.Assign(targets=[cyast.Name(node.token_var.name)],
                                                      value=get_token),
                                         self.compile(node.body) ],
                                  orelse = [] ) ]
        else:
            self.env.try_declare_cvar(node.token_var.name, node.token_var.type)
            place_type = marking_type.get_place_type_by_name(node.place_name)
            return Builder.For( target = cyast.Name(node.token_var.name),
                                iter = place_type.iterable_expr( env = self.env,
                                                                 marking_var = node.marking),
                                body = [ self.compile(node.body) ])


    def gen_different(self, indices):

        base = None
        current = None

        first_index = indices.pop()
        for index in indices:
            check = cyast.If( test = cyast.Compare( left = cyast.Name(first_index.name),
                                                    ops = [ cyast.NotEq() ],
                                                    comparators = [ cyast.Name(index.name) ]),
                              body = [],
                              orelse = [])
            if not base:
                base = check
                current = check
            else:
                current.body.append( check )
                current = check

        inner = current
        if len(indices) > 1:
            inner_base, inner = self.gen_different( indices )
            current.body.append( base )

        return base, inner

    def compile_MultiTokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)

        base = None
        current = None
        if place_type.provides_by_index_access:
            for sub_arc in node.multiarc.sub_arcs:
                variable = sub_arc.data['local_variable']
                index_var = sub_arc.data['index']

                self.env.try_declare_cvar(index_var.name, TypeInfo.Int)
                self.env.try_declare_cvar(variable.name, place_type.token_type)

                assign = cyast.Assign(targets=[cyast.Name(variable.name)],
                                      value=place_type.get_token_expr(self.env,
                                                                      index_expr = index_var,
                                                                      marking_var = node.marking,
                                                                      compiled_index = cyast.Name(index_var.name)))
                enumeration = cyast.For( target = cyast.Name(index_var.name),
                                         iter = cyast.Call(func=cyast.Name('range'),
                                                           args=[cyast.Num(0), place_type.get_size_expr(self.env,
                                                                                                        node.marking)]),
                                         body = [ assign ] )
                if base == None:
                    current = enumeration
                    base = enumeration
                else:
                    current.body.append(enumeration)
                    current = enumeration


        else: # no index access
            for sub_arc in node.multiarc.sub_arcs:
                variable = sub_arc.data['local_variable']
                index_var = sub_arc.data['index']
                init = cyast.Assign( targets =  [cyast.Name(index_var.name)],
                                     value = cyast.Num(0) )

                self.env.try_declare_cvar(index_var.name, TypeInfo.Int)
                self.env.try_declare_cvar(variable.name, place_type.token_type)

                enumeration = cyast.For( target = cyast.Name(variable.name),
                                         iter = place_type.iterable_expr( env = self.env,
                                                                          marking_var = node.marking ),
                                         body = [ cyast.AugAssign( target = cyast.Name(index_var.name),
                                                                   op = cyast.Add(),
                                                                   value = cyast.Num(1) ) ] )
                if base == None:
                    current = [ init, enumeration ]
                    base = [ init, enumeration ]
                else:
                    current[1].body.append([init, enumeration])
                    current = [init, enumeration]

        indices = [ sub_arc.data['index'] for sub_arc in node.multiarc.sub_arcs ]
        inner_base, inner = self.gen_different(indices)
        if isinstance(current, list):
            current[1].body.append(inner_base)
        else:
            current.body.append(inner_base)
        current = inner

        current.body.extend([ self.compile( node.body ) ])

        return base

    def compile_GuardCheck(self, node):
        return Builder.If( test = self.compile(node.condition),
                           body = self.compile(node.body),
                           orelse = [] )

    def compile_PyExpr(self, node):
        assert isinstance(node.expr, ExpressionInfo)
        return E(node.expr.raw)

    def compile_Name(self, node):
        return E(node.name)

    def compile_FunctionCall(self, node):
        return E(node.function_name).call([ self.compile(arg) for arg in node.arguments ])

    def compile_ProcedureCall(self, node):
        return stmt(cyast.Call(func=cyast.Name(node.function_name),
                               args=[ self.compile(arg) for arg in node.arguments ])
                    )

    def compile_MarkingCopy(self, node):
        self.env.try_declare_cvar(node.dst.name, node.dst.type)
        return self.env.marking_type.gen_copy( env = self.env,
                                               src_marking = node.src,
                                               dst_marking = node.dst,
                                               modified_places = node.mod )

    def compile_AddMarking(self, node):
        return stmt( self.env.marking_set_type.add_marking_stmt(env = self.env,
                                                                markingset_var = node.marking_set,
                                                                marking_var = node.marking) )

    def compile_AddToken(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt( env = self.env,
                                          token_expr = node.token_expr,
                                          compiled_token = self.compile(node.token_expr),
                                          marking_var = node.marking )

    def compile_RemToken(self, node):
        index = node.use_index
        marking_type = self.env.marking_type
        place_type = marking_type.get_place_type_by_name(node.place_name)
        if place_type.provides_by_index_deletion:
            return place_type.remove_by_index_stmt(env = self.env,
                                                   index_var = index,
                                                   marking_var = node.marking,
                                                   compiled_index = index)
        else:
            return place_type.remove_token_stmt(env = self.env,
                                                token_expr = node.token_expr,
                                                compiled_token = self.compile(node.token_expr),
                                                marking_var = node.marking)

    def compile_RemTuple(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.remove_token_stmt(env = self.env,
                                            token_expr = node.tuple_expr,
                                            compiled_token = self.compile(node.tuple_expr),
                                            marking_var = node.marking)

    def compile_Token(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.token_expr(env=self.env,
                                     token=node.value)

    def try_gen_type_decl(self, input):
        if input.is_Variable:
            variable = input.variable
            place_info = input.place_info
            type = self.env.marking_type.get_place_type_by_name(place_info.name).token_type
            
            if (not type.is_UserType) or (is_cython_type(type)):
                return CVarSet( [ cyast.CVar(name=variable.name, type=type2str(type)) ] )

        elif input.is_Test:
            # TO DO declare variables appearing in tests
            return CVarSet()
            # inner = input.inner
            # return CVarSet( [ self.try_gen_type_decl(input.inner) ] )

        elif input.is_MultiArc:
            varset = CVarSet()
            for arc in input.sub_arcs:
                varset.extend( self.try_gen_type_decl(arc) )
            return varset

        return CVarSet()

    def compile_SuccT(self, node):
        self.env.push_cvar_env()
        self.env.push_variable_provider(node.variable_provider)

        self.var_helper = node.transition_info.variable_helper

        stmts = [ self.compile( node.body ) ]

        decl = CVarSet()
        inputs = node.transition_info.inputs
        for input in inputs:
            decl.extend(self.try_gen_type_decl(input))

        inter_vars = node.transition_info.intermediary_variables
        for var in inter_vars:
            if (not var.type.is_UserType) or is_cython_type( var.type ):
                decl.add(cyast.CVar(name=var.name,
                                    type=type2str(var.type))
        )

        additionnal_decls = self.env.pop_cvar_env()
        for var in additionnal_decls:
            decl.add(var)

        result = to_ast( Builder.FunctionDef(name = node.function_name,
                                             args = (A(node.arg_marking_set.name, type = type2str(node.arg_marking_set.type))
                                                     .param(node.arg_marking.name, type = type2str(node.arg_marking.type))),
                                             body = stmts,
                                             lang = cyast.CDef( public = False ),
                                             returns = cyast.Name("void"),
                                             decl = decl) )
        return result


    def compile_SuccP(self, node):
        env = self.env
        env.push_cvar_env()

        stmts = [ self.compile( node.body ) ]

        decl = CVarSet()
        additionnal_decls = self.env.pop_cvar_env()
        for var in additionnal_decls:
            decl.add(var)

        return Builder.FunctionDef( name = node.function_name,
                                    args = (A(node.arg_marking_set.name, type = type2str(node.arg_marking_set.type))
                                            .param(node.arg_marking.name, type = type2str(node.arg_marking.type))),
                                    body = stmts,
                                    lang = cyast.CDef( public = False ),
                                    returns = E("void"),
                                    decl = decl )

    def compile_Succs(self, node):
        body = []
        body.extend( self.compile( node.body ) )
        body.append( E("return " + node.arg_marking_set.name) )
        f1 = Builder.FunctionCDef(name=node.function_name,
                                  args=A(node.arg_marking.name, type2str(node.arg_marking.type)),
                                  body=body,
                                  returns=cyast.Name("set"),
                                  decl=[ cyast.CVar(name=node.arg_marking_set.name,
                                                    type=type2str(node.arg_marking_set.type),
                                                    init=self.env.marking_set_type.new_marking_set_expr(self.env)) ]
                                  )

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

        f2 = Builder.FunctionCDef(name="neco_succs",
                                  args=A("m", type="Marking"),
                                  body=body,
                                  returns=cyast.Name("ctypes_ext.neco_list_t*"),
                                  decl=[cyast.CVar(name="l", type="ctypes_ext.neco_list_t*"),
                                        cyast.CVar(name="e", type="Marking")]
                                  )

        return [f1, f2]



    def compile_Init(self, node):
        new_marking = cyast.Assign(targets=[cyast.Name(node.marking.name)],
                                   value=self.env.marking_type.new_marking_expr(self.env))
        return_stmt = E( "return {}".format(node.marking.name))

        stmts = [new_marking]
        stmts.extend( self.compile(node.body) )
        stmts.append( return_stmt )

        f1 = Builder.FunctionDef( name = node.function_name,
                                  body = stmts,
                                  returns = cyast.Name("Marking"),
                                  decl = [ cyast.CVar( node.marking.name, type2str(node.marking.type) )])

        f2 = Builder.FunctionCDef( name = "neco_init",
                                   body = [ stmts ],
                                   returns = cyast.Name("Marking"),
                                   decl = [ cyast.CVar( node.marking.name, type2str(node.marking.type) )])

        return [f1, f2]

    ################################################################################
    # opts
    ################################################################################
    def compile_OneSafeTokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        getnode = cyast.Assign(targets=[cyast.Name(node.token_var.name)],
                               value=place_type.place_expr(env = self.env,
                                                           marking_var = node.marking)
                               )
        ifnode = Builder.If(test = place_type.not_empty_expr(self.env, marking_var = node.marking),
                            body = [ getnode, self.compile( node.body ) ])
        return [ to_ast(ifnode) ]

    def compile_BTTokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        ifnode = Builder.If(test = Builder.Compare(left = to_ast(place_type.place_expr(env = self.env,
                                                                                       marking_var = node.marking)),
                                                   ops = [ cyast.Gt() ],
                                                   comparators = [ cyast.Num( n = 0 ) ] ),
                            body = [ self.compile( node.body ) ])
        return [ ifnode ]

    def compile_BTOneSafeTokenEnumeration(self, node):
        body = [ self.compile( node.body ) ]
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        ifnode = Builder.If(test = place_type.place_expr(env = self.env,
                                                         marking_var = node.marking),
                            body = body )
        return [ ifnode ]

    ################################################################################
    # Flow elimination
    ################################################################################

    def compile_FlowCheck(self, node):
        return self.env.marking_type.gen_check_flow(env=self.env,
                                                    marking_var  = node.marking,
                                                    place_info   = node.place_info,
                                                    current_flow = node.current_flow)

    def compile_ReadFlow(self, node):
        return self.env.marking_type.gen_read_flow(env=self.env,
                                                   marking_var  = node.marking,
                                                   process_name = node.process_name)

    def compile_UpdateFlow(self, node):
        return self.env.marking_type.gen_update_flow(env=self.env,
                                                     marking_var = node.marking,
                                                     place_info  = node.place_info)

        
################################################################################
# EOF
################################################################################
