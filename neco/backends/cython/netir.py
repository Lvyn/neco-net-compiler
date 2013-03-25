""" Cython ast compiler. """

from neco.core.info import TypeInfo, ExpressionInfo
from priv.common import CVarSet, from_neco_lib
from priv.mrkpidfunctions import GENERATOR_PLACE
import StringIO
import cPickle as cPickle
import neco.core.netir as coreir
import priv.cyast as cyast

################################################################################

class CompilerVisitor(coreir.CompilerVisitor):
    """ Cython ast compiler visitor class. """

    backend = "cython"

    def __init__(self, env):
        self.env = env

    def compile_Return(self, node):
        return [ cyast.Return(self.compile(node.expr)) ]

    def compile_Print(self, node):
        return [cyast.Print(values = [cyast.Str(node.message)], nl = True)]

    def compile_Comment(self, node):
        return cyast.NComment(message = node.message)

    def compile_If(self, node):
        return cyast.If(test = self.compile(node.condition),
                        body = [ self.compile(node.body) ],
                        orelse = [ self.compile(node.orelse) ])

    def compile_Compare(self, node):
        return cyast.Builder.Compare(left = self.compile(node.left),
                                     ops = [ self.compile(op) for op in node.ops ],
                                     comparators = [ self.compile(comparator) for comparator in node.comparators ])

    def compile_EQ(self, node):
        return cyast.Eq()

    def compile_CheckTuple(self, node):
        tuple_info = node.tuple_info
        expr = "isinstance({tuple_name}, tuple) and len({tuple_name}) == {length}"
        test = cyast.E(expr.format(tuple_name = node.tuple_var.name,
                                   length = repr(len(tuple_info))))
        return cyast.Builder.If(test, body = self.compile(node.body))

    def compile_CheckType(self, node):
        type_info = node.type
        if type_info.is_AnyType:
            return self.compile(node.body)

        test = cyast.Call(func = cyast.Name('isinstance'),
                          args = [cyast.E(node.variable.name), cyast.E(self.env.type2str(type_info))])

        return cyast.Builder.If(test = test, body = self.compile(node.body))

    def compile_Match(self, node):
        tuple_info = node.tuple_info
        seq = []

        component_names = [ token_info.data['local_variable'].name for token_info in tuple_info ]
        seq.append(cyast.Assign(targets = [ cyast.Tuple([ cyast.E(name) for name in component_names ])],
                                value = cyast.Name(tuple_info.data['local_variable'].name)))
        cur = None
        for component in tuple_info.components:
            if component.is_Value:
                # self.try_declare_cvar(component.data['local_variable'].name, component.type)
                n = cyast.Builder.If(test = cyast.Builder.Compare(left = cyast.E(component.data['local_variable'].name),
                                                                  ops = [ cyast.Eq() ],
                                                                  comparators = [ cyast.E(repr(component.raw)) ]),    # TO DO unify value & pickle
                                     orelse = [])
                if cur == None:
                    cur = n
                    seq.append(n)
                else:
                    cur.body = [n]
                    cur = n
            elif component.is_Variable:
                self.env.try_declare_cvar(component.data['local_variable'].name, component.type)

        if cur != None:
            cur.body = [ self.compile(node.body) ]
        else:
            seq.append(self.compile(node.body))

        return seq


    def compile_Assign(self, node):
        self.env.try_declare_cvar(node.variable.name, node.variable.type)

        return cyast.Assign(targets = [cyast.Name(node.variable.name)],
                            value = self.compile(node.expr))

    def compile_Value(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.token_expr(self.env, node.value.raw)

    def compile_Pickle(self, node):
        output = StringIO.StringIO()
        cPickle.dump(node.obj, output)
        pickle_str = output.getvalue()
        return cyast.E("cPickle.load(StringIO.StringIO(" + repr(pickle_str) + "))")

    def compile_FlushIn(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        return [cyast.Assign(targets = [cyast.Name(node.token_var.name)],
                             value = destination_place.attribute_expr(self.env, node.marking_var))]

    def compile_RemAllTokens(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        return [destination_place.clear_stmt(env = self.env,
                                             marking_var = node.marking_var)]

    def compile_FlushOut(self, node):
        destination_place = self.env.marking_type.get_place_type_by_name(node.place_name)
        multiset = self.compile(node.token_expr)
        return destination_place.add_items_stmt(env = self.env,
                                                multiset = multiset,
                                                marking_var = node.marking_var)

    def gen_tuple(self, tuple_info):
        elts = []
        for info in tuple_info:
            if info.is_Value:
                elts.append(cyast.E(repr(info.raw)))
            elif info.is_Variable:
                elts.append(cyast.Name(id = info.name))
            elif info.is_Tuple:
                elts.append(self.gen_tuple(info))
            elif info.is_Expression:
                elts.append(cyast.E(info.raw))
            else:
                raise NotImplementedError, info.component.__class__

        return cyast.Builder.Tuple(elts = elts)

    def compile_TupleOut(self, node):
        tuple_info = node.tuple_info
        generated_tuple = self.gen_tuple(tuple_info)

        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         token_expr = tuple_info,
                                         compiled_token = generated_tuple,
                                         marking_var = node.marking_var)

    def compile_NotEmpty(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.not_empty_expr(env = self.env,
                                         marking_var = node.marking_var)

    def compile_TokenEnumeration(self, node):
        marking_type = self.env.marking_type
        place_type = marking_type.get_place_type_by_name(node.place_name)

        if hasattr(place_type, 'enumerate'):
            return place_type.enumerate(self.env, node.marking_var, node.token_var, self.compile(node.body))

        arc = node.arc

        if place_type.provides_by_index_access:
            index_var = arc.data['index']
            size_var = self.env.variable_provider.new_variable()

            self.env.try_declare_cvar(index_var.name, TypeInfo.get('Int'))
            self.env.try_declare_cvar(node.token_var.name, node.token_var.type)
            self.env.try_declare_cvar(size_var.name, TypeInfo.get('Int'))

            place_size = place_type.get_size_expr(env = self.env,
                                                  marking_var = node.marking_var)

            get_token = place_type.get_token_expr(env = self.env,
                                                  index_expr = index_var,
                                                  marking_var = node.marking_var,
                                                  compiled_index = cyast.Name(index_var.name))


            return [ cyast.Assign(targets = [cyast.Name(size_var.name)],
                                  value = place_size),
                     cyast.Builder.CFor(start = cyast.Num(0),
                                        start_op = cyast.LtE(),
                                        target = cyast.Name(index_var.name),
                                        stop_op = cyast.Lt(),
                                        stop = cyast.Name(size_var.name),
                                        body = [ cyast.Assign(targets = [cyast.Name(node.token_var.name)],
                                                            value = get_token),
                                              self.compile(node.body) ],
                                        orelse = []) ]
        else:
            self.env.try_declare_cvar(node.token_var.name, node.token_var.type)
            place_type = marking_type.get_place_type_by_name(node.place_name)
            return cyast.Builder.For(target = cyast.Name(node.token_var.name),
                                     iter = place_type.iterable_expr(env = self.env,
                                                                   marking_var = node.marking_var),
                                     body = [ self.compile(node.body) ])


    def gen_different(self, indices):

        base = None
        current = None

        first_index = indices.pop()
        for index in indices:
            check = cyast.If(test = cyast.Compare(left = cyast.Name(first_index.name),
                                                ops = [ cyast.NotEq() ],
                                                comparators = [ cyast.Name(index.name) ]),
                              body = [],
                              orelse = [])
            if not base:
                base = check
                current = check
            else:
                current.body.append(check)
                current = check

        inner = current
        if len(indices) > 1:
            _, inner = self.gen_different(indices)
            current.body.append(base)

        return base, inner

    def compile_MultiTokenEnumeration(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)

        base = None
        current = None
        if place_type.provides_by_index_access:
            for sub_arc in node.multiarc.sub_arcs:
                variable = sub_arc.data['local_variable']
                index_var = sub_arc.data['index']

                self.env.try_declare_cvar(index_var.name, TypeInfo.get('Int'))
                self.env.try_declare_cvar(variable.name, place_type.token_type)

                assign = cyast.Assign(targets = [cyast.Name(variable.name)],
                                      value = place_type.get_token_expr(self.env,
                                                                      index_expr = index_var,
                                                                      marking_var = node.marking_var,
                                                                      compiled_index = cyast.Name(index_var.name)))
                enumeration = cyast.For(target = cyast.Name(index_var.name),
                                         iter = cyast.Call(func = cyast.Name('range'),
                                                         args = [cyast.Num(0), place_type.get_size_expr(self.env,
                                                                                                      node.marking_var)]),
                                         body = [ assign ])
                if base == None:
                    current = enumeration
                    base = enumeration
                else:
                    current.body.append(enumeration)
                    current = enumeration


        else:    # no index access
            for sub_arc in node.multiarc.sub_arcs:
                variable = sub_arc.data['local_variable']
                index_var = sub_arc.data['index']
                init = cyast.Assign(targets = [cyast.Name(index_var.name)],
                                     value = cyast.Num(0))

                self.env.try_declare_cvar(index_var.name, TypeInfo.get('Int'))
                self.env.try_declare_cvar(variable.name, place_type.token_type)

                enumeration = cyast.For(target = cyast.Name(variable.name),
                                        iter = place_type.iterable_expr(env = self.env,
                                                                      marking_var = node.marking_var),
                                        body = [ cyast.AugAssign(target = cyast.Name(index_var.name),
                                                               op = cyast.Add(),
                                                               value = cyast.Num(1)) ])
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

        current.body.extend([ self.compile(node.body) ])

        return base

    def compile_GuardCheck(self, node):
        return cyast.Builder.If(test = self.compile(node.condition),
                                body = self.compile(node.body),
                                orelse = [])

    def compile_PyExpr(self, node):
        assert isinstance(node.expr, ExpressionInfo)
        return cyast.E(node.expr.raw)

    def compile_Name(self, node):
        return cyast.E(node.name)

    def compile_FunctionCall(self, node):
        return cyast.E(node.function_name).call([ self.compile(arg) for arg in node.arguments ])

    def compile_ProcedureCall(self, node):
        return cyast.stmt(cyast.Call(func = cyast.Name(node.function_name),
                                     args = [ self.compile(arg) for arg in node.arguments ])
                    )

    def compile_MarkingCopy(self, node):
        self.env.try_declare_cvar(node.dst.name, node.dst.type)
        return self.env.marking_type.gen_copy(env = self.env,
                                              src_marking = node.src,
                                              dst_marking = node.dst,
                                              modified_places = node.mod)

    def compile_AddMarking(self, node):
        return cyast.stmt(self.env.marking_set_type.add_marking_stmt(env = self.env,
                                                                     markingset_var = node.marking_set_var,
                                                                     marking_var = node.marking_var))

    def compile_AddToken(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         token_expr = node.token_expr,
                                         compiled_token = self.compile(node.token_expr),
                                         marking_var = node.marking_var)

    def compile_RemToken(self, node):
        index = node.use_index
        marking_type = self.env.marking_type
        place_type = marking_type.get_place_type_by_name(node.place_name)
        if place_type.provides_by_index_deletion and index:
            return place_type.remove_by_index_stmt(env = self.env,
                                                   index_var = index,
                                                   marking_var = node.marking_var,
                                                   compiled_index = index)
        else:
            return place_type.remove_token_stmt(env = self.env,
                                                token_expr = node.token_expr,
                                                compiled_token = self.compile(node.token_expr),
                                                marking_var = node.marking_var)

    def compile_RemTuple(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.remove_token_stmt(env = self.env,
                                            token_expr = node.tuple_expr,
                                            compiled_token = self.compile(node.tuple_expr),
                                            marking_var = node.marking_var)

    def compile_Token(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.token_expr(env = self.env,
                                     token = node.value)

    def try_gen_type_decl(self, input_arc):
        if input_arc.is_Variable:
            variable = input_arc.variable
            place_info = input_arc.place_info
            pi_type = self.env.marking_type.get_place_type_by_name(place_info.name).token_type

            if (not pi_type.is_UserType) or (self.env.is_cython_type(pi_type)):
                return CVarSet([ cyast.CVar(name = variable.name, type = self.env.type2str(pi_type)) ])

        elif input_arc.is_Test:
            # TO DO declare variables appearing in tests
            return CVarSet()
            # inner = input_arc.inner
            # return CVarSet( [ self.try_gen_type_decl(input_arc.inner) ] )

        elif input_arc.is_MultiArc:
            varset = CVarSet()
            for arc in input_arc.sub_arcs:
                varset.extend(self.try_gen_type_decl(arc))
            return varset

        return CVarSet()


    def succ_function_args(self, node):
        return  (cyast.A(node.arg_marking_var.name, type = self.env.type2str(node.arg_marking_var.type))
                 .param(node.arg_marking_acc_var.name, type = self.env.type2str(node.arg_marking_acc_var.type))
                 .param(node.arg_ctx_var.name, type = self.env.type2str(node.arg_ctx_var.type)))

    def main_succ_function_args(self, node):
        return  (cyast.A(node.arg_marking_var.name, type = self.env.type2str(node.arg_marking_var.type))
                 .param(node.arg_ctx_var.name, type = self.env.type2str(node.arg_ctx_var.type)))

    def compile_SuccT(self, node):
        self.env.push_cvar_env()
        self.env.push_variable_provider(node.variable_provider)

        self.var_helper = node.transition_info.variable_helper

        stmts = [ self.compile(node.body) ]

        decl = CVarSet()
        input_arcs = node.transition_info.input_arcs
        for input_arc in input_arcs:
            decl.extend(self.try_gen_type_decl(input_arc))

        inter_vars = node.transition_info.intermediary_variables
        for var in inter_vars:
            if (not var.type.is_UserType) or self.env.is_cython_type(var.type):
                decl.add(cyast.CVar(name = var.name,
                                    type = self.env.type2str(var.type))
        )

        additionnal_decls = self.env.pop_cvar_env()
        for var in additionnal_decls:
            decl.add(var)

        result = cyast.to_ast(cyast.Builder.FunctionDef(name = node.function_name,
                                                        args = self.succ_function_args(node),
                                                        body = stmts,
                                                        lang = cyast.CDef(public = True),
                                                        returns = cyast.Name(""),
                                                        decl = decl))
        return result


    def compile_SuccP(self, node):
        env = self.env
        env.push_cvar_env()

        stmts = [ self.compile(node.body) ]

        decl = CVarSet()
        additionnal_decls = self.env.pop_cvar_env()
        for var in additionnal_decls:
            decl.add(var)

        return cyast.Builder.FunctionDef(name = node.function_name,
                                         args = self.succ_function_args(node),
                                         body = stmts,
                                         lang = cyast.CDef(public = False),
                                         returns = cyast.E("void"),
                                         decl = decl)

    def compile_Succs(self, node):
        body = []
        body.extend(self.compile(node.body))
        body.append(cyast.E("return " + node.arg_marking_acc_var.name))
        f1 = cyast.Builder.FunctionCpDef(name = node.function_name,
                                         args = self.main_succ_function_args(node),
                                         body = body,
                                         lang = cyast.CpDef(public = True),
                                         returns = cyast.Name("set"),
                                         decl = [ cyast.CVar(name = node.arg_marking_acc_var.name,
                                                             type = self.env.type2str(node.arg_marking_acc_var.type),
                                                             init = self.env.marking_set_type.new_marking_set_expr(self.env)) ]
                                         )

        body = [ cyast.E("l = ctypes_ext.neco_list_new()") ]

        body.append(cyast.For(target = cyast.to_ast(cyast.E("e")),
                               iter = cyast.to_ast(cyast.E("succs(m, ctx)")),
                               body = [ cyast.to_ast(cyast.stmt(cyast.E("ctypes_ext.__Pyx_INCREF(e)"))),
                                        cyast.Expr(cyast.Call(func = cyast.to_ast(cyast.E("ctypes_ext.neco_list_push_front")),
                                                              args = [cyast.to_ast(cyast.E("l")), cyast.Name("e")],
                                                              keywords = [],
                                                              starargs = None,
                                                              kwargs = None)) ]))

        body.append(cyast.E("return l"))
        f2 = cyast.Builder.FunctionCDef(name = "neco_succs",
                                        args = (cyast.A("m", type = self.env.type2str(node.arg_marking_var.type))
                                                .param("ctx", type = self.env.type2str(node.arg_ctx_var.type))),
                                        body = body,
                                        returns = cyast.Name("ctypes_ext.neco_list_t*"),
                                        decl = [cyast.CVar(name = "l", type = "ctypes_ext.neco_list_t*"),
                                                cyast.CVar(name = "e", type = "Marking")]
                                        )

        return [f1]

    def compile_Init(self, node):
        env = self.env
        env.push_cvar_env()

        new_marking = cyast.Assign(targets = [cyast.Name(node.marking_var.name)],
                                   value = self.env.marking_type.new_marking_expr(self.env))
        return_stmt = cyast.E("return {}".format(node.marking_var.name))

        stmts = [new_marking]
        stmts.extend(self.compile(node.body))
        stmts.append(return_stmt)

        decl = CVarSet()
        decl.extend([cyast.CVar(node.marking_var.name, self.env.type2str(node.marking_var.type))])

        additionnal_decls = self.env.pop_cvar_env()
        decl.extend(additionnal_decls)

        f1 = cyast.Builder.FunctionDef(name = node.function_name,
                                       body = stmts,
                                       returns = cyast.Name("Marking"),
                                       decl = decl)

        f2 = cyast.Builder.FunctionCDef(name = "neco_init",
                                        body = stmts,
                                        returns = cyast.Name("Marking"),
                                        decl = decl)

        return [f1, f2]

    ################################################################################
    # Flow elimination
    ################################################################################

    def compile_FlowCheck(self, node):
        return self.env.marking_type.gen_check_flow(env = self.env,
                                                    marking_var = node.marking_var,
                                                    place_info = node.place_info,
                                                    current_flow = node.current_flow)

    def compile_ReadFlow(self, node):
        return self.env.marking_type.gen_read_flow(env = self.env,
                                                   marking_var = node.marking_var,
                                                   process_name = node.process_name)

    def compile_UpdateFlow(self, node):
        return self.env.marking_type.gen_update_flow(env = self.env,
                                                     marking_var = node.marking_var,
                                                     place_info = node.place_info)

    ################################################################################
    # MarkingNormalization
    ################################################################################

    def compile_InitGeneratorPlace(self, node):
        marking_type = self.env.marking_type
        generator_place = marking_type.get_place_type_by_name(GENERATOR_PLACE)
        initial_pid_var = self.env.variable_provider.new_variable(variable_type = TypeInfo.get('Pid'))
        self.env.try_declare_cvar(initial_pid_var.name, initial_pid_var.type)
        assign = cyast.Assign(targets = [cyast.E(initial_pid_var.name)],
                              value = self.compile_InitialPid(None))
        return [ assign, generator_place.add_pid_stmt(self.env, initial_pid_var, node.marking_var) ]

    def compile_NormalizeMarking(self, node):
        return cyast.stmt(cyast.Call(func = cyast.E('normalize_pids'),
                                     args = [cyast.E(node.marking_var.name)]))

    def compile_AddPid(self, node):
        place_type = self.env.marking_type.get_place_type_by_name(node.place_name)
        return place_type.add_token_stmt(env = self.env,
                                         token_expr = node.token_expr,
                                         compiled_token = self.compile(node.token_expr),
                                         marking_var = node.marking_var)

    def compile_InitialPid(self, node):
        return cyast.E(self.env.type2str(TypeInfo.get('Pid')) + '(1)')

################################################################################
# EOF
################################################################################
