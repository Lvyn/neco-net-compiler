""" Python AST compiler. """

import cPickle as cPickle
import StringIO
import neco.config as config
import neco.core.netir as coreir
from neco.core.info import *
from nettypes import type2str
from pyast import *
import pyast as ast

################################################################################

class CompilerVisitor(coreir.CompilerVisitor):
    """ Python ast compiler visitor class. """

    backend = "python"

    def __init__(self, env):
        self.env = env

    def compile_Print(self, node):
        return ast.Print(dest = None,
                         values = [ ast.Str( s = node.message ) ],
                         nl = True)

    def compile(self, node):
        return super(CompilerVisitor, self).compile(node)

    def compile_Comment(self, node):
        return []

    def compile_If(self, node):
        return ast.If( test = self.compile(node.condition),
                       body = self.compile(node.body),
                       orelse = self.compile(node.orelse) )

    def compile_Compare(self, node):
        return ast.Compare( left = self.compile(node.left),
                            ops = [ self.compile(op) for op in node.ops ],
                            comparators = [ self.compile(comparator) for comparator in node.comparators ] )

    def compile_EQ(self, node):
        return ast.Eq()

    def compile_CheckTuple(self, node):
        tuple_info = node.tuple_info
        test = E( "isinstance(" + node.tuple_var.name +  ", tuple) and len(" + node.tuple_var.name + ") == " + repr(len(tuple_info)) )
        return ast.If( test = test, body = self.compile(node.body) )

    def compile_CheckType(self, node):
        type_info = node.type
        if type_info.is_AnyType:
            return self.compile(node.body)

        test = E("isinstance(" + node.variable.name + ", " + type2str(node.type) + ")")
        return ast.If( test = test, body = self.compile(node.body) )

    def compile_Match(self, node):
        tuple_info = node.tuple_info
        seq = []

        component_names = [ token_info.data['local_variable'].name for token_info in tuple_info ]
        seq.append( ast.Assign(targets = [ ast.Tuple([ E(name) for name in component_names ])],
                                 value = ast.Name(tuple_info.data['local_variable'].name)) )
        cur = None
        for component in tuple_info.components:
            if component.is_Value:
                n = Builder.If( test = Builder.Compare( left = E(component.data['local_variable'].name),
                                                        ops = [ ast.Eq() ],
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

        # tuple_info = node.tuple_info
        # seq = []
        # seq.append( ast.Assign(targets=[ast.Tuple(elts=[ ast.Name(id=n) for n in tuple_info.base() ])],
        #                        value=ast.Name(id=tuple_info.name)) )
        # cur = None
        # for component in tuple_info.components:
        #     if component.is_Value:
        #         n = ast.If(test=ast.Compare(left=ast.Name(id=component.name),
        #                                     ops=[ast.Eq()],
        #                                     comparators=[E(repr(component.raw))]
        #                                     )
        #                    )
        #         if cur == None:
        #             cur = n
        #             seq.append(n)
        #         else:
        #             cur.body = [n]
        #             cur = n

        # if cur != None:
        #     cur.body = [ self.compile( node.body ) ]
        # else:
        #     seq.append(self.compile( node.body ))

        # return seq

    def compile_Assign(self, node):
        return ast.Assign(targets=[ast.Name(id=node.variable.name)],
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
        place_expr = destination_place.place_expr(self.env, node.marking)
        return [ ast.Assign(targets=[ast.Name(id=node.token_var.name)],
                            value=place_expr),
                 destination_place.clear_stmt(self.env, node.marking) ]

    def compile_FlushOut(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        multiset = self.compile(node.token_expr)
        return destination_place.add_items_stmt( env = self.env,
                                                 multiset = multiset,
                                                 marking_var = node.marking )

    def gen_tuple(self, tuple_info):
        elts = []
        for info in tuple_info:
            if info.is_Value:
                elts.append( E(repr(info.raw)) )

            elif info.is_Variable:
                elts.append( E(info.name) )

            elif info.is_Tuple:
                elts.append( self.gen_tuple( info ) )
            elif info.is_Expression:
                elts.append( E(info.raw) )
            else:
                raise NotImplementedError, info.component.__class__

        return ast.Tuple(elts)

    def compile_TupleOut(self, node):
        tuple_info = node.tuple_info
        tuple = self.gen_tuple(tuple_info)
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         compiled_token = tuple,
                                         marking_var = node.marking)

    def compile_NotEmpty(self, node):
        return self.env.marking_type.gen_not_empty_function_call( env = self.env,
                                                                  marking_var = node.marking_var,
                                                                  place_name = node.place_name )

    def compile_TokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return ast.For(target = E(node.token_var.name),
                       iter = place_type.iterable_expr(env = self.env,
                                                       marking_var = node.marking),
                       body = [ self.compile(node.body) ])


    def gen_different(self, indices):

        base = None
        current = None

        first_index = indices.pop()
        for index in indices:
            check = ast.If( test = ast.Compare( left = ast.Name(first_index),
                                                  ops = [ ast.NotEq() ],
                                                  comparators = [ ast.Name(index) ]),
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
            current.body.append( first )

        return base, inner

    def compile_MultiTokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)

        base = None
        current = None
        if place_type.provides_by_index_access:
            for sub_arc in node.multiarc.sub_arcs:
                variable = sub_arc.data['local_variable']
                index = sub_arc.data['index']

                assign = ast.Assign(targets=[ast.Name(variable)],
                                      value=place_type.get_token_expr(self.env,
                                                                      node.marking_var,
                                                                      ast.Name(index)))
                enumeration = ast.For( target = ast.Name(index),
                                         iter = ast.Call(func=ast.Name('range'),
                                                         args=[ast.Num(0), place_type.get_size_expr(self.env,
                                                                                                    node.marking_var)]),
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
                index = sub_arc.data['index']
                init = ast.Assign( targets =  [ast.Name(index.name)],
                                   value = ast.Num(0) )

                enumeration = ast.For( target = ast.Name(variable.name),
                                       iter = place_type.iterable_expr( env = self.env,
                                                                        marking_var = node.marking),
                                       body = [ ast.AugAssign( target = ast.Name(index.name),
                                                               op = ast.Add(),
                                                               value = ast.Num(1) ) ] )
                if base == None:
                    current = [ init, enumeration ]
                    base = [ init, enumeration ]
                else:
                    current[1].body.append([init, enumeration])
                    current = [init, enumeration]

        indices = [ sub_arc.data['index'].name for sub_arc in node.multiarc.sub_arcs ]
        inner_base, inner = self.gen_different(indices)
        if isinstance(current, list):
            current[1].body.append(inner_base)
        else:
            current.body.append(inner_base)
        current = inner

        current.body.extend([ self.compile( node.body ) ])

        return base


    def compile_GuardCheck(self, node):
        return ast.If( test = self.compile(node.condition),
                           body = self.compile(node.body) )

    def compile_PyExpr(self, node):
        assert isinstance(node.expr, ExpressionInfo)
        return E(node.expr.raw)

    def compile_Name(self, node):
        return E(node.name)

    def compile_FunctionCall(self, node):
        return E(node.function_name).call([ self.compile(arg) for arg in node.arguments ])

    def compile_ProcedureCall(self, node):
        return stmt( ast.Call(func=ast.Name(id=node.function_name),
                              args=[ self.compile(arg) for arg in node.arguments ]) )

    def compile_MarkingCopy(self, node):
        nodes = []
        nodes.append( E( node.dst.name + " = Marking()" ) )

        names = {}
        for info in node.mod:
            names[info.name] = info

        for (place, place_type) in self.env.marking_type.place_types.iteritems():
            dst_place_expr = place_type.place_expr(self.env, marking_var = node.dst)
            src_place_expr = place_type.place_expr(self.env, marking_var = node.src)
            if names.has_key( place ):
                nodes.append( ast.Assign(targets=[dst_place_expr],
                                         value=place_type.copy_expr(self.env, node.src)
                                         )
                              )
            else:
                nodes.append( ast.Assign(targets=[dst_place_expr],
                                         value=src_place_expr
                                         )
                              )
        return nodes

    def compile_AddMarking(self, node):
        return self.env.marking_set_type.add_marking_stmt(env = self.env,
                                                          markingset = node.marking_set,
                                                          marking = node.marking)

    def compile_AddToken(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         compiled_token = self.compile(node.token_expr),
                                         marking_var = node.marking)

    def compile_RemToken(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.remove_token_stmt(env = self.env,
                                            compiled_token = self.compile(node.token_expr),
                                            marking_var = node.marking)

    def compile_RemTuple(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.remove_token_stmt(env = self.env,
                                            compiled_token = self.compile(node.tuple_expr),
                                            marking_var = node.marking)

    def compile_Token(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.token_expr(env = self.env,
                                     value = node.value)

    def compile_SuccT(self, node):
        self.env.push_variable_provider(node.variable_provider)
        stmts = [ self.compile( node.body ),
                  E('return ' + node.arg_marking_set.name) ]
        result = ast.FunctionDef(name = node.function_name,
                                 args = ast.arguments(args=[ast.Name(id=node.arg_marking_set.name),
                                                            ast.Name(id=node.arg_marking.name)]),
                                 body = stmts)
        self.env.pop_variable_provider()
        return result

    def compile_SuccP(self, node):
        stmts = [ self.compile( node.body ),
                  E('return ' + node.arg_marking_set.name) ]
        return ast.FunctionDef(name = node.function_name,
                               args = ast.arguments(args=[ast.Name(id=node.arg_marking_set.name),
                                                          ast.Name(id=node.arg_marking.name)]),
                               body = stmts)

    def compile_Succs(self, node):
        body = [ ast.Assign(targets=[ast.Name(id=node.arg_marking_set.name)],
                            value=self.env.marking_set_type.new_marking_set_expr(self.env)) ]

        body.extend( self.compile(node.body) )
        body.append( ast.Return(ast.Name(id=node.arg_marking_set.name)) )
        return ast.FunctionDef( name = node.function_name,
                                args = ast.arguments(args=[ast.Name(id=node.arg_marking.name)]),
                                body = body )

    def compile_Init(self, node):
        new_marking = ast.Assign(targets=[ast.Name(id=node.marking.name)],
                                 value=self.env.marking_type.new_marking_expr(self.env))
        return_stmt = ast.Return(ast.Name(id=node.marking.name))

        stmts = [new_marking]
        stmts.extend( self.compile(node.body) )
        stmts.append( return_stmt )

        return ast.FunctionDef( name = node.function_name,
                                body = stmts )

    ################################################################################
    # opts
    ################################################################################
    def compile_OneSafeTokenEnumeration(self, node):
        place_expr = self.env.marking_type.gen_get_place( env = self.env,
                                                          marking_var = node.marking,
                                                          place_name = node.place_name,
                                                          mutable = False )
        getnode = ast.Assign(targets=[ast.Name(id=node.token_var.name)],
                             value=place_expr)
        ifnode = ast.If(test=ast.Compare(left=ast.Name(id=node.token_var.name),
                                         ops=[ast.NotEq()],
                                         comparators=[ast.Name(id='None')]),
                        body=[ self.compile( node.body ) ] )
        return [ getnode, ifnode ]

    def compile_BTTokenEnumeration(self, node):
        place_expr = self.env.marking_type.gen_get_place( env = self.env,
                                                          marking_var = node.marking_var,
                                                          place_name = node.place_name,
                                                          mutable = False )
        getnode = ast.Assign(targets=[ast.Name(id=node.token_name)],
                             value=ast.Name(id='dot'))
        ifnode = ast.If(test=ast.Compare(left=place_expr, ops=[ast.Gt()], comparators=[ast.Num(0)]),
                        body=[ getnode, self.compile( node.body ) ] )
        return [ ifnode ]

    def compile_BTOneSafeTokenEnumeration(self, node):
        body = [ self.compile( node.body ) ]
        place_expr = self.env.marking_type.gen_get_place( env = self.env,
                                                          marking_var = node.marking,
                                                          place_name = node.place_name,
                                                          mutable = False )
        ifnode = ast.If( test = ast.UnaryOp(op=ast.Not(), operand=place_expr),
                         body = body )
        return [ ifnode ]

    ################################################################################
    # Flow elimination
    ################################################################################

    def compile_FlowCheck(self, node):
        return self.env.marking_type.gen_check_flow(env = self.env,
                                                    marking_var = node.marking,
                                                    place_info = node.place_info,
                                                    current_flow = ast.Name(node.current_flow.name))

    def compile_ReadFlow(self, node):
        return self.env.marking_type.gen_read_flow(env=self.env,
                                                   marking_var=node.marking,
                                                   process_name=node.process_name)

    def compile_UpdateFlow(self, node):
        return self.env.marking_type.gen_update_flow(env = self.env,
                                                     marking_var = node.marking,
                                                     place_info = node.place_info)

    def compile_NormalizeMarking(self, node):
        return self.env.marking_type.normalize_marking_call(env = self.env,
                                                            marking_var = node.marking)
        
################################################################################
# EOF
################################################################################
