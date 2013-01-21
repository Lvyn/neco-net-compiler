""" Python AST compilser. """

from neco.core.info import ExpressionInfo
from nettypes import type2str
from priv import pyast, mrkpidmethods
import StringIO
import cPickle as cPickle
import neco.core.netir as coreir

GENERATOR_PLACE = 'sgen'

################################################################################

class CompilerVisitor(coreir.CompilerVisitor):
    """ Python pyast compiler visitor class. """

    backend = "python"

    def __init__(self, env, config):
        self.env = env
        self.config = config

    def compile_Print(self, node):
        return pyast.Print(dest = None,
                         values = [ pyast.Str( s = node.message ) ],
                         nl = True)

    def compile(self, node):
        return super(CompilerVisitor, self).compile(node)

    def compile_Comment(self, node):
        return []

    def compile_If(self, node):
        return pyast.If( test = self.compile(node.condition),
                       body = self.compile(node.body),
                       orelse = self.compile(node.orelse) )

    def compile_Compare(self, node):
        return pyast.Compare( left = self.compile(node.left),
                            ops = [ self.compile(op) for op in node.ops ],
                            comparators = [ self.compile(comparator) for comparator in node.comparators ] )

    def compile_EQ(self, node):
        return pyast.Eq()

    def compile_CheckTuple(self, node):
        tuple_info = node.tuple_info
        test = pyast.E( "isinstance(" + node.tuple_var.name +  ", tuple) and len(" + node.tuple_var.name + ") == " + repr(len(tuple_info)) )
        return pyast.If( test = test, body = self.compile(node.body) )

    def compile_CheckType(self, node):
        type_info = node.type
        if type_info.is_AnyType:
            return self.compile(node.body)

        test = pyast.E("isinstance(" + node.variable.name + ", " + type2str(node.type) + ")")
        return pyast.If( test = test, body = self.compile(node.body) )

    def compile_Match(self, node):
        tuple_info = node.tuple_info
        seq = []

        component_names = [ token_info.data['local_variable'].name for token_info in tuple_info ]
        seq.append( pyast.Assign(targets = [ pyast.Tuple([ pyast.E(name) for name in component_names ])],
                                 value = pyast.Name(tuple_info.data['local_variable'].name)) )
        cur = None
        for component in tuple_info.components:
            if component.is_Value:
                n = pyast.Builder.If( test = pyast.Builder.Compare( left = pyast.E(component.data['local_variable'].name),
                                                        ops = [ pyast.Eq() ],
                                                        comparators = [ pyast.E(repr(component.raw)) ] ), # TO DO unify value & pickle
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
        # seq.append( pyast.Assign(targets=[pyast.Tuple(elts=[ pyast.Name(id=n) for n in tuple_info.base() ])],
        #                        value=pyast.Name(id=tuple_info.name)) )
        # cur = None
        # for component in tuple_info.components:
        #     if component.is_Value:
        #         n = pyast.If(test=pyast.Compare(left=pyast.Name(id=component.name),
        #                                     ops=[pyast.Eq()],
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
        return pyast.Assign(targets=[pyast.Name(id=node.variable.name)],
                          value=self.compile(node.expr))

    def compile_Value(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.token_expr(self.env, node.value.raw)

    def compile_Pickle(self, node):
        output = StringIO.StringIO()
        cPickle.dump(node.obj, output)
        pickle_str = output.getvalue()
        return pyast.E("cPickle.load(StringIO.StringIO(" + repr(pickle_str) + "))")

    def compile_FlushIn(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        assign_expr = destination_place.assign_multiset_stmt(self.env, node.token_var, node.marking_var)
        return [assign_expr]

    def compile_RemAllTokens(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        return [destination_place.clear_stmt(self.env, node.marking_var) ]

    def compile_FlushOut(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        multiset = self.compile(node.token_expr)
        return destination_place.add_items_stmt( env = self.env,
                                                 multiset = multiset,
                                                 marking_var = node.marking_var )

    def gen_tuple(self, tuple_info):
        elts = []
        for info in tuple_info:
            if info.is_Value:
                elts.append( pyast.E(repr(info.raw)) )

            elif info.is_Variable:
                elts.append( pyast.E(info.name) )

            elif info.is_Tuple:
                elts.append( self.gen_tuple( info ) )
            elif info.is_Expression:
                elts.append( pyast.E(info.raw) )
            else:
                raise NotImplementedError, info.component.__class__

        return pyast.Tuple(elts)

    def compile_TupleOut(self, node):
        tuple_info = node.tuple_info
        compiled_tuple = self.gen_tuple(tuple_info)
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         compiled_token = compiled_tuple,
                                         marking_var = node.marking_var)

    def compile_NotEmpty(self, node):
        return self.env.marking_type.gen_not_empty_function_call( env = self.env,
                                                                  marking_var = node.marking_var,
                                                                  place_name = node.place_name )

    def compile_TokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        if hasattr(place_type, 'enumerate'):
            return place_type.enumerate(self.env, node.marking_var, node.token_var, self.compile(node.body))
        else:    
            return pyast.For(target = pyast.E(node.token_var.name),
                           iter = place_type.iterable_expr(env = self.env,
                                                           marking_var = node.marking_var),
                           body = [ self.compile(node.body) ])

    
    def gen_different(self, indices):

        base = None
        current = None

        first_index = indices.pop()
        for index in indices:
            check = pyast.If( test = pyast.Compare( left = pyast.Name(first_index),
                                                  ops = [ pyast.NotEq() ],
                                                  comparators = [ pyast.Name(index) ]),
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
            _, inner = self.gen_different( indices )
            current.body.append( base )

        return base, inner

    def compile_MultiTokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)

        base = None
        current = None
        if place_type.provides_by_index_access:
            for sub_arc in node.multiarc.sub_arcs:
                variable = sub_arc.data['local_variable']
                index = sub_arc.data['index']

                assign = pyast.Assign(targets=[pyast.Name(variable)],
                                      value=place_type.get_token_expr(self.env,
                                                                      node.marking_var,
                                                                      pyast.Name(index)))
                enumeration = pyast.For( target = pyast.Name(index),
                                         iter = pyast.Call(func=pyast.Name('range'),
                                                         args=[pyast.Num(0), place_type.get_size_expr(self.env,
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
                init = pyast.Assign( targets =  [pyast.Name(index.name)],
                                   value = pyast.Num(0) )

                enumeration = pyast.For( target = pyast.Name(variable.name),
                                       iter = place_type.iterable_expr( env = self.env,
                                                                        marking_var = node.marking_var),
                                       body = [ pyast.AugAssign( target = pyast.Name(index.name),
                                                               op = pyast.Add(),
                                                               value = pyast.Num(1) ) ] )
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
        return pyast.If( test = self.compile(node.condition),
                           body = self.compile(node.body) )

    def compile_PyExpr(self, node):
        assert isinstance(node.expr, ExpressionInfo)
        return pyast.E(node.expr.raw)

    def compile_Name(self, node):
        return pyast.E(node.name)

    def compile_FunctionCall(self, node):
        return pyast.E(node.function_name).call([ self.compile(arg) for arg in node.arguments ])

    def compile_ProcedureCall(self, node):
        return pyast.stmt( pyast.Call(func=pyast.Name(id=node.function_name),
                                      args=[ self.compile(arg) for arg in node.arguments ]) )

    def compile_MarkingCopy(self, node):
        nodes = []
        nodes.append( pyast.E( node.dst.name + " = Marking()" ) )

        names = {}
        for info in node.mod:
            names[info.name] = info

        for (place, place_type) in self.env.marking_type.place_types.iteritems():
#            dst_place_expr = place_type.place_expr(self.env, marking_var = node.dst)
#            src_place_expr = place_type.place_expr(self.env, marking_var = node.src)
            if names.has_key( place ):
                nodes.append( place_type.copy_stmt(self.env, node.dst, node.src) )
#                nodes.append( pyast.Assign(targets=[dst_place_expr],
#                                         value=place_type.copy_expr(self.env, node.src)
#                                         )
#                              )
            else:
                nodes.append( place_type.copy_stmt(self.env, node.dst, node.src) )
#                nodes.append( pyast.Assign(targets=[dst_place_expr],
#                                         value=src_place_expr
#                                         )
#                              )
        return nodes

    def compile_AddMarking(self, node):
        return self.env.marking_set_type.add_marking_stmt(env = self.env,
                                                          markingset = node.marking_set_var,
                                                          marking = node.marking_var)

    def compile_AddToken(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         compiled_token = self.compile(node.token_expr),
                                         marking_var = node.marking_var)

    def compile_RemToken(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.remove_token_stmt(env = self.env,
                                            compiled_token = self.compile(node.token_expr),
                                            marking_var = node.marking_var)

    def compile_RemTuple(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.remove_token_stmt(env = self.env,
                                            compiled_token = self.compile(node.tuple_expr),
                                            marking_var = node.marking_var)

    def compile_Token(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.token_expr(env = self.env,
                                     value = node.value)

    def compile_SuccT(self, node):
        self.env.push_variable_provider(node.variable_provider)
        stmts = [ self.compile( node.body ),
                  pyast.E('return ' + node.arg_marking_acc_var.name) ]
        result = pyast.FunctionDef(name = node.function_name,
                                 args = pyast.arguments(args=[ pyast.Name(id = node.arg_marking_var.name),
                                                               pyast.Name(id = node.arg_marking_acc_var.name), 
                                                               pyast.Name(id = node.arg_state_space_var.name),
                                                               pyast.Name(id = node.arg_pidfree_hash_set_var.name),
                                                               pyast.Name(id = node.arg_remaining_set_var.name) ]),
                                 body = stmts)
        self.env.pop_variable_provider()
        return result

    def compile_SuccP(self, node):
        stmts = [ self.compile( node.body ),
                  pyast.E('return ' + node.arg_marking_acc_var.name) ]
        return pyast.FunctionDef(name = node.function_name,
                                 args = pyast.arguments(args=[ pyast.Name(id = node.arg_marking_var.name),
                                                               pyast.Name(id = node.arg_marking_acc_var.name),
                                                               pyast.Name(id = node.arg_pidfree_hash_set_var.name),
                                                               pyast.Name(id = node.arg_remaining_set_var.name),
                                                               pyast.Name(id = node.arg_state_space_var.name)]),
                                 body = stmts)

    def compile_Succs(self, node):
        body = [ pyast.Assign(targets = [pyast.Name(id = node.arg_marking_acc_var.name)],
                              value   = self.env.marking_set_type.new_marking_set_expr(self.env)) ]

        body.extend( self.compile(node.body) )
        body.append( pyast.Return(pyast.Name(id=node.arg_marking_acc_var.name)) )
        return pyast.FunctionDef( name = node.function_name,
                                  args = pyast.arguments(args=[ pyast.Name(id = node.arg_marking_var.name),
                                                                pyast.Name(id = node.arg_state_space_var.name),
                                                                pyast.Name(id = node.arg_pidfree_hash_set_var.name),
                                                                pyast.Name(id = node.arg_remaining_set_var.name) ]),
                                  body = body )

    def compile_Init(self, node):
        new_marking = pyast.Assign(targets = [ pyast.Name(id=node.marking_var.name) ],
                                   value   = self.env.marking_type.new_marking_expr(self.env))
        return_stmt = pyast.Return(pyast.Name(id=node.marking_var.name))

        stmts = [new_marking]
        stmts.extend( self.compile(node.body) )
        stmts.append( return_stmt )

        return pyast.FunctionDef( name = node.function_name,
                                  body = stmts )

    ################################################################################
    # Flow elimination
    ################################################################################

    def compile_FlowCheck(self, node):
        return self.env.marking_type.gen_check_flow(env = self.env,
                                                    marking_var = node.marking_var,
                                                    place_info = node.place_info,
                                                    current_flow = pyast.Name(node.current_flow.name))

    def compile_ReadFlow(self, node):
        return self.env.marking_type.gen_read_flow(env=self.env,
                                                   marking_var=node.marking_var,
                                                   process_name=node.process_name)

    def compile_UpdateFlow(self, node):
        return self.env.marking_type.gen_update_flow(env = self.env,
                                                     marking_var = node.marking_var,
                                                     place_info = node.place_info)

    ################################################################################
    # Marking normalization
    ################################################################################

    def compile_InitGeneratorPlace(self, node):
        marking_type = self.env.marking_type
        generator_place = marking_type.get_place_type_by_name(GENERATOR_PLACE)
        return [ generator_place.add_token_stmt(self.env,
                                                pyast.E("( Pid.from_str('1'), 0 )"), 
                                                node.marking_var) ]

    def compile_NormalizeMarking(self, node):
        function = mrkpidmethods.select_normalization_function(self.config)
        return pyast.E("{dst} = {fun}({mrk}, {hs}, {acc}, {todo}, {ss})".format(dst  = node.normalized_marking_var.name,
                                                                                fun  = function,
                                                                                mrk  = node.marking_var.name,
                                                                                hs   = node.pidfree_hash_set_var.name,
                                                                                acc  = node.marking_acc_var.name,
                                                                                todo = node.remaining_set_var.name,
                                                                                ss   = node.state_space_var.name))
        
    def compile_AddPid(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env=self.env,
                                         compiled_token=self.compile(node.token_expr),
                                         marking_var=node.marking_var)
        
    def compile_InitialPid(self, node):
        return pyast.E("Pid.from_str('1')")
    
    def compile_UpdateHashSet(self, node):
        #return []
        return pyast.stmt(pyast.E("{}.add({}.__pid_free_hash__())".format(node.pidfree_hash_set_var.name, node.marking_var.name)))

################################################################################
# EOF
################################################################################
