""" Main compiler interface. """

import itertools, pickle
from collections import defaultdict
from snakes.nets import *
import neco.config as config
from neco.utils import flatten_lists
import netir, nettypes
from info import *
from itertools import izip_longest

from netir import PyExpr
import StringIO

################################################################################

class CompilingEnvironment(object):
    """ Contains data that need to be shared between components;
    """

    def __init__(self, config, net_info):
        """ Build a new compiling environment.
        """
        self.config = config
        self.net_info = net_info

        self.successor_function_nodes = []
        self.process_successor_function_nodes = []
        self.main_successor_function_node = None
        self.init_function_node = None
        self.global_names = WordSet([])
        self.successor_functions = []

        self._succ_function_names = {}
        self._process_succ_function_names = set()

    def function_nodes(self):
        for node in self.successor_function_nodes:
            yield node
        for node in self.process_successor_function_nodes:
            yield node
        yield self.main_successor_function_node
        yield self.init_function_node

    @property
    def succ_functions(self):
        """ transition specific successor function names. """
        return self._succ_function_names.values()

    def get_succ_function_name(self, transition_info):
        """ Returns the name of a successor function.

        @param transition_info:
        @type transition_info: C{}
        """
        return self._succ_function_names[transition_info.name]

    def register_succ_function(self, transition_info, function_name):
        """ Registers a function name as a successor function.

        @param transition_info: transition that produced the function.
        @type transition_info: C{TransitionInfo}
        @param function_name: successor function name
        @type function_name: C{str}
        """
        self._succ_function_names[transition_info.name] = function_name

    @property
    def process_succ_functions(self):
        """ process successor function names. """
        return self._process_succ_function_names

    def register_process_succ_function(self, function_name):
        """ Registers a function name as a process successor function.

        @param function_name: successor function name
        @type function_name: C{str}
        """
        self._process_succ_function_names.add(function_name)

################################################################################

class ProcessSuccGenerator(object):
    """ Class that produces a succ function specific to ABCD processes
    """

    def __init__(self, env, process_info, function_name, marking_type):
        """
        Function that handles the production of processor specific successor
        functions.

        @param env: compiling environment.
        @param net_info: Petri net info structure.
        @param process_info: ProcessInfo of the process.
        @param function_name: name of produced function.
        @param marking_type: used marking type_info
        """
        self.env = env
        self.config = env.config
        self.net_info = env.net_info
        self.process_info = process_info
        self.function_name = function_name
        self.marking_type = marking_type

        variable_provider = VariableProvider(set([function_name]))
        self.variable_provider = variable_provider
        self.flow_variable = variable_provider.new_variable(variable_type = TypeInfo.Int)

        self.builder = netir.Builder()

        self.arg_marking_var = variable_provider.new_variable(variable_type = marking_type.type)
        self.arg_marking_acc_var = variable_provider.new_variable(variable_type = marking_type.container_type)
        self.arg_ctx_var = variable_provider.new_variable(variable_type = TypeInfo.get('NecoCtx'))

        env.register_process_succ_function(function_name)

    def __call__(self):
        """ Generate function.
        """
        env = self.env
        function_name = self.function_name
        arg_marking_var = self.arg_marking_var
        arg_marking_acc_var = self.arg_marking_acc_var
        process_info = self.process_info
        arg_ctx_var = self.arg_ctx_var

        if not self.env.config.optimize_flow:
            return

        builder = self.builder

        builder.begin_function_SuccP(function_name = function_name,
                                      arg_marking_var = arg_marking_var,
                                      arg_marking_acc_var = arg_marking_acc_var,
                                      arg_ctx_var = arg_ctx_var,
                                      process_info = process_info,
                                      flow_variable = self.flow_variable,
                                      variable_provider = self.variable_provider)

        # enumerate places with not empty post
        ne_post = filter(lambda place : place.post, process_info.flow_places)

        current_flow = self.flow_variable

        read = builder.ReadFlow(marking_var = arg_marking_var,
                                process_name = process_info.name)
        builder.emit_Assign(variable = current_flow,
                            expr = read)

        for i, flow_place in enumerate(ne_post):
            if i == 0:
                builder.begin_If(condition = builder.FlowCheck(marking_var = arg_marking_var,
                                                                current_flow = current_flow,
                                                                place_info = flow_place))
            else:
                builder.begin_Elif(condition = builder.FlowCheck(marking_var = arg_marking_var,
                                                                  current_flow = current_flow,
                                                                  place_info = flow_place))

            # produced inside each if block:
            for transition in flow_place.post:
                name = env.get_succ_function_name(transition)
                builder.emit_ProcedureCall(function_name = name,
                                            arguments = [ netir.Name(name = arg_marking_var.name),
                                                          netir.Name(name = arg_marking_acc_var.name),
                                                          netir.Name(name = arg_ctx_var.name) ])

        builder.end_all_blocks()
        builder.end_function()
        return builder.ast()

################################################################################

class SuccTGenerator(object):
    """ Transition specific succ function generator.

    This class is used for building a transition specific succ function.
    """

    def __init__(self, env, net_info, builder, transition, function_name, marking_type, config):
        """ Builds the transition specific succ function generator.

        @param builder: builder structure for easier ast construction
        @type_info builder: C{neco.core.netir.Builder}
        @param transition: considered transition
        @type_info transition: C{neco.core.info.TransitionInfo}
        @param function_name: function name
        @type_info function_name: C{string}
        @param ignore_flow: ignore flow control places ?
        @type_info ignore_flow: C{bool}
        """
        self.env = env
        self.config = config
        self.net_info = net_info
        self.builder = builder
        self.transition = transition
        self.function_name = function_name
        self.marking_type = marking_type

        # this helper will create new variables and take care of shared instances
        helper = SharedVariableHelper(transition.shared_input_variables(),
                                       WordSet(transition.variables().keys()))
        self.variable_helper = helper

        if self.config.optimize:
            self.transition.order_inputs()

        # create new variables for function arguments
        self.arg_marking_var = helper.new_variable(variable_type = marking_type.type)
        self.marking_acc_var = helper.new_variable(variable_type = marking_type.container_type)
        self.ctx_var = helper.new_variable(variable_type = TypeInfo.get('NecoCtx'))

        # create function

        self.builder.begin_function_SuccT(function_name = self.function_name,
                                           arg_marking_var = self.arg_marking_var,
                                           arg_marking_acc_var = self.marking_acc_var,
                                           arg_ctx_var = self.ctx_var,
                                           transition_info = self.transition,
                                           variable_provider = helper)

        # remember this succ function
        env.register_succ_function(transition, function_name)

    def try_unify_shared_variable(self, variable):
        """ Produces the unification process for shared variables if all occurences have been used.

        In the context where different names represent a unique variable,
        this function compares these names and use a witness for the final
        variable name.

        @param variable: initial variable (appearing in the model)
        @type variable: C{str}
        """
        assert(isinstance(variable, VariableInfo))
        if self.variable_helper.is_shared(variable):
            if self.variable_helper.all_used(variable):
                if not self.variable_helper.unified(variable):
                    local_variables = self.variable_helper.get_local_variables(variable)
                    first_local = local_variables.pop(-1)

                    # compare values
                    operators = [ netir.EQ() ] * len(local_variables)
                    comparators = [ netir.Name(loc_var.name) for loc_var in local_variables ]
                    self.builder.begin_If(netir.Compare(left = netir.Name(first_local.name),
                                                         ops = operators,
                                                         comparators = comparators))

                    # build a witness with the initial variable name
                    self.builder.emit_Assign(variable = variable,
                                              expr = netir.Name(first_local.name))
                    self.variable_helper.set_unified(variable)
                    return True
            return False

    def gen_enumerators(self):
        """ Produces all the token enumeration blocs.
        """

        builder = self.builder
        trans = self.transition
        variable_helper = self.variable_helper

        trans.variable_helper = variable_helper

        # places that provides multiple tokens, _cannot_ be used with by index access
        multi_places = trans.input_multi_places
        for place in multi_places:
            place_type = self.marking_type.get_place_type_by_name(place.name)
            place_type.disable_by_index_deletion()

        if self.config.optimize:
            trans.order_inputs()

        # loop over input_arcs
        for input_arc in trans.input_arcs:
            if self.config.optimize_flow and input_arc.place_info.flow_control:
                continue

            builder.emit_Comment("Enumerate {input_arc} - place: {place}".format(input_arc = input_arc,
                                                                                 place = input_arc.place_name))

            # use index access if available
            place_type = self.marking_type.get_place_type_by_name(input_arc.place_info.name)
            if (place_type.provides_by_index_access and
                 input_arc.place_info not in multi_places):
                index = variable_helper.new_variable(variable_type = TypeInfo.Int)
            else:
                index = None

            # produce the enumeration and tests according to the input_arc's type

            # variable
            if input_arc.is_Variable:
                variable = input_arc.variable

                # if the variable is shared a new variable is produced, the variable is used otherwise
                local_variable = variable_helper.new_variable_occurence(variable)

                # notify that the variable is used
                variable_helper.mark_as_used(variable, local_variable)

                builder.begin_TokenEnumeration(arc = input_arc,
                                                token_var = local_variable,
                                                marking_var = self.arg_marking_var,
                                                place_name = input_arc.place_name)

                input_arc.data.register('local_variable', local_variable)
                input_arc.data.register('index', index)

                self.try_unify_shared_variable(variable)

            # test
            elif input_arc.is_Test:
                inner = input_arc.inner

                if inner.is_Variable:
                    variable = inner

                    local_variable = variable_helper.new_variable_occurence(variable)
                    variable_helper.mark_as_used(variable, local_variable)

                    builder.begin_TokenEnumeration(arc = input_arc,
                                                    token_var = local_variable,
                                                    marking_var = self.arg_marking_var,
                                                    place_name = input_arc.place_name)

                    self.try_unify_shared_variable(variable)
                    input_arc.data.register('local_variable', local_variable)
                    input_arc.data.register('index', index)

                elif inner.is_Value:
                    place_info = self.net_info.place_by_name(input_arc.place_name)
                    place_type = self.marking_type.get_place_type_by_name(place_info.name)

                    local_variable = variable_helper.new_variable(variable_type = place_type.token_type)

                    # get a token
                    builder.begin_TokenEnumeration(arc = input_arc,
                                                    token_var = local_variable,
                                                    marking_var = self.arg_marking_var,
                                                    place_name = input_arc.place_name)

                    if not place_info.type.is_BlackToken:
                        # check token value
                        builder.begin_If(netir.Compare(left = netir.Name(name = local_variable.name),
                                                         ops = [ netir.EQ() ],
                                                         comparators = [ netir.Value(value = input_arc.value,
                                                                                      place_name = input_arc.place_name) ]
                                                        )
                                         )
                    # end if

                    input_arc.data.register('local_variable', local_variable)
                    input_arc.data.register('index', index)

                elif inner.is_Tuple:
                    # produce names for tuple components
                    self._gen_names(inner)

                    place_info = self.net_info.place_by_name(input_arc.place_name)
                    place_type = self.marking_type.get_place_type_by_name(place_info.name)
                    token_var = inner.data['local_variable']
                    # get a tuple
                    builder.begin_TokenEnumeration(arc = input_arc,
                                                    token_var = token_var,
                                                    marking_var = self.arg_marking_var,
                                                    place_name = input_arc.place_name)

                    if not (inner.type.is_TupleType and len(inner.type) == len(inner)):
                        # check its type
                        builder.begin_CheckTuple(tuple_var = token_var,
                                                  tuple_info = inner)

                    self._gen_tuple_decomposition(input_arc, inner)

                else:
                    raise NotImplementedError, "ArcTest : inner = %s" % inner

            # value
            elif input_arc.is_Value:
                place_info = self.net_info.place_by_name(input_arc.place_name)
                place_type = self.marking_type.get_place_type_by_name(place_info.name)

                local_variable = variable_helper.new_variable(place_type.token_type)

                # get a token
                builder.begin_TokenEnumeration(arc = input_arc,
                                                token_var = local_variable,
                                                marking_var = self.arg_marking_var,
                                                place_name = input_arc.place_name)

                input_arc.data.register('local_variable', local_variable)
                input_arc.data.register('index', index)

                if not place_info.type.is_BlackToken:
                    # check token value
                    builder.begin_If(netir.Compare(left = netir.Name(name = local_variable.name),
                                                     ops = [ netir.EQ() ],
                                                     comparators = [ netir.Value(value = input_arc.value,
                                                                                  place_name = input_arc.place_name) ]))


            # flush
            elif input_arc.is_Flush:
                inner = input_arc.inner
                if inner.is_Variable:
                    if variable_helper.is_shared(inner):
                        raise NotImplementedError

                    input_arc.data.register('local_variable', inner)
                    builder.emit_FlushIn(token_var = input_arc.data['local_variable'],
                                          marking_var = self.arg_marking_var,
                                          place_name = input_arc.place_name)
                else:
                    raise NotImplementedError, "flush %s" % repr(inner)

            # tuple
            elif input_arc.is_Tuple:
                # produce names for tuple components
                self._gen_names(input_arc.tuple)

                place_info = self.net_info.place_by_name(input_arc.place_name)
                place_type = self.marking_type.get_place_type_by_name(place_info.name)
                token_variable = input_arc.tuple.data['local_variable']
                token_variable.update_type(place_type.token_type)

                # get a tuple
                builder.begin_TokenEnumeration(arc = input_arc,
                                                token_var = token_variable,
                                                marking_var = self.arg_marking_var,
                                                place_name = input_arc.place_name)    # no index access

                if not (input_arc.tuple.type.is_TupleType and len(input_arc.tuple.type) == len(input_arc.tuple)):
                    # check its type
                    builder.begin_CheckTuple(tuple_var = token_variable,
                                              tuple_info = input_arc.tuple)


                self._gen_tuple_decomposition(input_arc, input_arc.tuple)
                input_arc.data.register('index', index)

            elif input_arc.is_MultiArc:
                variables = set()
                values = {}    # variable -> value
                # sub_arcs as variables
                for sub_arc in input_arc.sub_arcs:
                    if sub_arc.is_Variable:
                        variable = sub_arc.variable
                        local_variable = variable_helper.new_variable_occurence(variable)
                        variable_helper.mark_as_used(variable, local_variable)

                        variables.add(variable)
                        sub_arc.data.register('local_variable', local_variable)
                        sub_arc.data.register('index', variable_helper.new_variable(TypeInfo.Int))

                    elif sub_arc.is_Value:
                        variable = variable_helper.new_variable(variable_type = place_type.token_type)

                        variables.add(variable)
                        sub_arc.data.register('local_variable', variable)
                        sub_arc.data.register('index', variable_helper.new_variable(TypeInfo.Int))

                        if sub_arc.value.raw != dot and not place_type.token_type.is_BlackToken:
                            values[variable] = sub_arc.value

                    else:
                        raise NotImplementedError, sub_arc


                builder.begin_MultiTokenEnumeration(multiarc = input_arc,
                                                     marking_var = self.arg_marking_var,
                                                     place_name = input_arc.place_name)

                for variable, value in values.iteritems():
                    builder.begin_If(netir.Compare(left = netir.Name(name = variable.name),
                                                     ops = [ netir.EQ() ],
                                                     comparators = [ netir.Value(value = value,
                                                                                  place_name = input_arc.place_name) ]
                                                    )
                                     )
                # end for

                for variable in variables:
                    self.try_unify_shared_variable(variable)

            else:
                raise NotImplementedError, input_arc.arc_annotation.__class__

    def _gen_names(self, token_info):
        """ Produce names for intermediary variables when handling tuples.

        @param token_info: tuple or component.
        """
        if token_info.is_Tuple:
            token_info.data.register('local_variable',
                                     self.variable_helper.new_variable())
            for component in token_info:
                self._gen_names(component)

        elif token_info.is_Variable:
            variable_occurence = self.variable_helper.new_variable_occurence(token_info)
            token_info.data.register('local_variable', variable_occurence)

        elif token_info.is_Value:
            new_variable = self.variable_helper.new_variable()
            token_info.data.register('local_variable', new_variable)

        else:
            raise NotImplementedError, token_info

    def _gen_tuple_decomposition(self, input_arc, tuple_info):
        """ Produce the decomposition of a tuple_info (pattern matching).

        @param input_arc: input_arc arc
        @inner_type input_arc: C{neco.core.info.ArcInfo}
        @param tuple_info: tuple_info to decompose
        @inner_type tuple_info: C{tuple_info}
        """
        builder = self.builder
        variable_helper = self.variable_helper

        builder.begin_Match(tuple_info = tuple_info)

        def base_names(token_info):
            if token_info.is_Tuple:
                local_variable = token_info.data['local_variable']
                local_names = set([ (local_variable, local_variable) ])
                for component in token_info:
                    local_names.union(base_names(component))
                return local_names

            elif token_info.is_Variable:
                return set([ (token_info, token_info.data['local_variable']) ])

            elif token_info.is_Value:
                local_variable = token_info.data['local_variable']
                return set([ (local_variable, local_variable) ])

            else:
                raise NotImplementedError, token_info

        if not tuple_info.type.is_TupleType:
            sub_types = []
        else:
            sub_types = tuple_info.type.split()

        for (inner, inner_type) in izip_longest(tuple_info.split(), sub_types, fillvalue = TypeInfo.AnyType):
            if not inner_type.is_AnyType:
                inner.update_type(inner_type)

            if inner.is_Tuple:
                tuple_var = inner.data['local_variable']

                if not (inner.type.is_TupleType and len(inner.type) == len(inner)):
                    # check its type
                    builder.begin_CheckTuple(tuple_var = tuple_var,
                                              tuple_info = inner)

                self._gen_tuple_decomposition(input_arc, inner)

            elif inner.is_Variable:
                variable_helper.mark_as_used(inner, inner.data['local_variable'])
                self.try_unify_shared_variable(inner)

    def gen_computed_production(self, output, computed_productions):
        """ Compute an expression on an output arc and store the
        result in a dict.

        This allows an expression to be computed as soon as
        possible. It means that when all tokens involved in the
        expression are available, we will compute the expression and
        store the result.

        @param output output to be used
        @param computed_productions output -> productions list
        @type computed_productions defaultdict(list)

        """
        builder = self.builder

        if self.config.optimize_flow and output.place_info.flow_control:
            return

        output_place = self.marking_type.get_place_type_by_name(output.place_info.name)
        output_impl_type = output_place.token_type

        if output.is_Expression:
            # new temporary variable
            variable = self.variable_helper.new_variable(output_impl_type)

            # evaluate and assign the result to the variable
            builder.emit_Assign(variable = variable,
                                 expr = netir.PyExpr(output.expr))
            check = True
            try:
                print ">>>> BEGIN TO DO %s <<<< " % (output.expr.raw)
                value = eval(output.expr.raw)
                if output.place_info.type.contains(value):
                    check = False
                print ">>>> END TO DO <<<< "
            except:
                print "type of '{}' will be checked".format(output.expr.raw)

            if (not output_impl_type.is_AnyType) and check:
                builder.begin_CheckType(variable = variable,
                                         type = output_impl_type)


            computed_productions[output].append(netir.Name(variable.name))
            # TO DO rafine tuples

        elif output.is_Value:
            value = output.value
            variable = self.variable_helper.new_variable(output_impl_type)
            check = True

            v = eval(repr(value.raw))
            if v == dot and output.place_info.type.is_BlackToken:
                check = False

            # check its type
            if check:
                builder.emit_Assign(variable = variable,
                                     expr = netir.PyExpr(ExpressionInfo(repr(output.value.raw))))

                r = netir.Name(variable.name)
            else:
                r = netir.PyExpr(ExpressionInfo(repr(output.value.raw)))

            computed_productions[output].append(r)

        elif output.is_Variable:
            variable = output.variable
            if not (output_impl_type.is_AnyType or (variable.type == output_impl_type)):
                builder.begin_CheckType(variable = variable,
                                         type = output_impl_type)

            computed_productions[output].append(netir.Name(variable.name))

        elif output.is_Flush:
            # no type check, object places
            pass

        elif output.is_Tuple:
            # no type check, WARNING: may be unsound !
            pass

        elif output.is_MultiArc:
            for subarc in output.sub_arcs:
                # produce code for the computation and variable assignation
                self.gen_computed_production(subarc, computed_productions)

        elif output.is_GeneratorMultiArc:
            for subarc in output.sub_arcs:
                # produce code for the computation and variable assignation
                self.gen_computed_production(subarc, computed_productions)

        else:
            raise NotImplementedError, output.arc_annotation.__class__


    def gen_produce(self, output_arc):
        computed_productions = self.computed_productions
        new_marking_var = self.new_marking_var
        trans = self.transition
        builder = self.builder

        builder.emit_Comment(message = "Produce {output_arc} - place: {place}".format(output_arc = output_arc,
                                                                                    place = output_arc.place_name))
        if self.config.optimize_flow and output_arc.place_info.flow_control:
            new_flow = [ place for place in trans.post if place.flow_control ]
            assert(len(new_flow) == 1)
            builder.emit_UpdateFlow(marking_var = new_marking_var,
                                     place_info = new_flow[0])


        elif output_arc.is_Expression:
            if computed_productions.has_key(output_arc):
                token_expr = computed_productions[output_arc]

            builder.emit_AddToken(marking_var = new_marking_var,
                                   place_name = output_arc.place_name,
                                   token_expr = token_expr)

        elif output_arc.is_Value:
            if computed_productions.has_key(output_arc):
                token_expr = computed_productions[output_arc]
            else:
                #
                # TO DO TRY REPR
                #
                value = output_arc.value
                token_expr = netir.PyExpr(ExpressionInfo(repr(value.raw)))

            builder.emit_AddToken(marking_var = new_marking_var,
                                   place_name = output_arc.place_name,
                                   token_expr = token_expr)

        elif output_arc.is_Variable:
            if computed_productions.has_key(output_arc):
                token_expr = computed_productions[output_arc]
            else:
                value = output_arc.value
                token_expr = netir.Name(output_arc.name)

            builder.emit_AddToken(marking_var = new_marking_var,
                                   place_name = output_arc.place_name,
                                   token_expr = token_expr)

        elif output_arc.is_Flush:
            inner = output_arc.inner
            if inner.is_Variable:
                produced_token = inner.name
                builder.emit_FlushOut(marking_var = new_marking_var,
                                       place_name = output_arc.place_name,
                                       token_expr = netir.Name(produced_token))

            elif inner.is_Expression:
                builder.emit_FlushOut(marking_var = new_marking_var,
                                       place_name = output_arc.place_name,
                                       token_expr = netir.PyExpr(inner))
            else:
                raise NotImplementedError, "Flush.inner : %s" % inner

        elif output_arc.is_Tuple:
            # to do: if arc then use var
            if (False):
                pass
            # general case:
            else:
                builder.emit_TupleOut(marking_var = new_marking_var,
                                       place_name = output_arc.place_name,
                                       tuple_info = output_arc.tuple)
        elif output_arc.is_MultiArc:

            for subarc in output_arc.sub_arcs:
                if subarc in computed_productions:
                    builder.emit_AddToken(marking_var = new_marking_var,
                                           place_name = output_arc.place_name,
                                           token_expr = computed_productions[subarc])
                else:
                    self.gen_produce(subarc)

        elif output_arc.is_GeneratorMultiArc:

            for subarc in output_arc.sub_arcs:
                if subarc in computed_productions:
                    builder.emit_AddToken(marking_var = new_marking_var,
                                           place_name = output_arc.place_name,
                                           token_expr = computed_productions[subarc])
                else:
                    self.gen_produce(subarc)


        else:
            raise NotImplementedError, output_arc.arc_annotation.__class__



    def __call__(self):
        """ Build an instance of SuccT from a TransitionInfo object.

        @return: successor function abstract representation.
        """
        trans = self.transition
        helper = self.variable_helper
        builder = self.builder

#        if self._trace_calls:
#            builder.emit_Print("calling " + self.function_name)

        # for loops
        self.gen_enumerators()

        # produce new pids if process Petri net.

        if trans.generator_arc:
            # ok, that looks like a process Petri net... you quack, you're a duck...
            generator_arc = trans.generator_arc
            pid = generator_arc.pid
            new_pids = generator_arc.new_pids
            counter_var = generator_arc.counter
            i = 0
            for new_pid in new_pids:
                if i > 0:
                    expr = ExpressionInfo('{}.next({} + {})'.format(pid.name, counter_var.name, i))
                else:
                    expr = ExpressionInfo('{}.next({})'.format(pid.name, counter_var.name))

                builder.emit_Assign(variable = new_pid, expr = PyExpr(expr))
                i += 1

        # guard
        guard = ExpressionInfo(trans.trans.guard._str)
        try:
            if eval(guard.raw) != True:
                builder.begin_GuardCheck(condition = netir.PyExpr(guard))
        except:
            builder.begin_GuardCheck(condition = netir.PyExpr(guard))

        computed_productions = defaultdict(list)
        for output in trans.outputs:
            self.gen_computed_production(output, computed_productions)
        self.computed_productions = computed_productions

        new_marking_var = helper.new_variable(self.marking_type.type)

        if self.config.normalize_pids:
            normalized_marking_var = helper.new_variable(self.marking_type.type)

        self.new_marking_var = new_marking_var
        builder.emit_MarkingCopy(dst = new_marking_var,
                                  src = self.arg_marking_var,
                                  mod = trans.modified_places())

        # consume
        for arc in trans.input_arcs:
            builder.emit_Comment(message = "Consume {arc} - place: {place}".format(arc = arc, place = arc.place_name))

            if self.config.optimize_flow and arc.place_info.flow_control:
                continue
            elif arc.is_Variable:
                builder.emit_RemToken(marking_var = new_marking_var,
                                       place_name = arc.place_name,
                                       token_expr = netir.Name(arc.data['local_variable'].name),
                                       use_index = arc.data['index'])
            elif arc.is_Test:
                pass    # do not consume !

            elif arc.is_Flush:
                inner = arc.inner
                if inner.is_Variable:
                    builder.emit_RemAllTokens(token_var = arc.data['local_variable'],
                                               marking_var = new_marking_var,
                                               place_name = arc.place_name)
                else:
                    raise NotImplementedError, "inner : %s" % repr(inner)

            elif arc.is_Value:
                builder.emit_RemToken(marking_var = new_marking_var,
                                       place_name = arc.place_name,
                                       token_expr = netir.Value(value = arc.value,
                                                                  place_name = arc.place_name),
                                       use_index = arc.data['index'])

            elif arc.is_Tuple:
                builder.emit_RemTuple(marking_var = new_marking_var,
                                       place_name = arc.place_name,
                                       tuple_expr = netir.Name(arc.tuple.data['local_variable'].name))

            elif arc.is_MultiArc:
                for sub_arc in arc.sub_arcs:
                    if sub_arc.is_Variable:
                        builder.emit_RemToken(marking_var = new_marking_var,
                                               place_name = arc.place_name,
                                               token_expr = netir.Name(sub_arc.data['local_variable'].name),
                                               use_index = None)
                    elif sub_arc.is_Value:
                        builder.emit_RemToken(marking_var = new_marking_var,
                                               place_name = arc.place_name,
                                               token_expr = netir.Value(value = sub_arc.value,
                                                                          place_name = arc.place_name),
                                               use_index = None)

                    else:
                        raise NotImplementedError, sub_arc.arc_annotation
            else:
                raise NotImplementedError, arc.arc_annotation


        # produce
        for output_arc in trans.outputs:
            self.gen_produce(output_arc)

        # add pid normalization step if needed
        if self.config.normalize_pids:
            builder.emit_NormalizeMarking(normalized_marking_var = normalized_marking_var,
                                          marking_var = new_marking_var,
                                          marking_acc_var = self.marking_acc_var,
                                          arg_ctx_var = self.ctx_var)

            builder.emit_AddMarking(marking_set_var = self.marking_acc_var,
                                    marking_var = normalized_marking_var)
            builder.emit_UpdateHashSet(ctx_var = self.ctx_var,
                                       marking_var = normalized_marking_var)
        else:
            # add marking to set
            builder.emit_AddMarking(marking_set_var = self.marking_acc_var,
                                     marking_var = new_marking_var)
        # end function
        builder.end_all_blocks()
        builder.end_function()

        return builder.ast()

################################################################################

class Compiler(object):
    """ The main compiler class.

    This class is used to produce a library from a snake.nets.PetriNet.
    """

    def __init__(self, net, backend, config):
        """ Initialise the compiler from a Petri net.

        builds the basic info structure from the snakes petri net representation

        @param net: Petri net.
        @type_info net: C{snakes.nets.PetriNet}
        """

        self.config = config
        self.backend = backend
        self.net_info = NetInfo(net)

        if self.config.normalize_pids:
            if self.config.pid_first and not self.check_first_pid():
                exit(-1)

            if not self.check_typed():
                print >> sys.stderr, "pid normalization require fully typed nets."
                exit(-1)

        self.markingtype_class = "StaticMarkingType"
        self.marking_type = backend.new_marking_type(self.markingtype_class, self.config)
        self.optimisations = []

        self.env = backend.new_compiling_environment(self.config, self.net_info, WordSet(), self.marking_type)
        self.rebuild_marking_type()

    def check_typed(self):
        for place in self.net_info.places:
            if place.type.is_AnyType:
                print >> sys.stderr, "[W] place {} is assumed as pid-free".format(place.name)
            elif place.type.has_pids:
                if place.type.is_Pid:
                    continue
                elif place.type.is_TupleType:
                    for subtype in place.type:
                        if subtype.is_TupleType and subtype.has_pids:
                            print >> sys.stderr, "[E] nested tuples cannot contain pids. (this may be implemented in future)".format(place.name)
                            return False
        return True

    def check_first_pid(self):
        for place in self.net_info.places:
            if place.type.is_AnyType:
                print >> sys.stderr, "[W] place {} is assumed as pid-free".format(place.name)
            elif place.type.has_pids:
                if place.type.is_Pid:
                    continue
                elif place.type.is_TupleType:
                    for i, subtype in enumerate(place.type):
                        if i > 0 and subtype.has_pids:
                            print >> sys.stderr, "[E] place {} accepts pids at position {}".format(place.name, i)
                            return False
        return True


    def rebuild_marking_type(self):
        """ Rebuild the marking type. (places will be rebuild) """
        if self.config.dump_enabled:
            print self.marking_type

        # add place types to the marking type
        for place_info in self.net_info.places:
            self.marking_type.add(place_info)    # will not create duplicates

        self.marking_type.gen_types()
        if self.config.dump_enabled:
            print self.marking_type

    def add_optimisation(self, opt):
        """ Add an optimization.

        @param opt: optimization pass.
        @type opt: C{neco.opt.OptimisationPass}
        """
        self.optimisations.append(opt)
        self.marking_type = self.backend.new_marking_type(self.markingtype_class)
        self.rebuild_marking_type()

    def optimize_netir(self):
        """ Run optimization passes on AST. """
        env = self.env
        for opt in self.optimisations:
            env.successor_function_nodes = [ opt.transform_ast(net_info = self.net_info, node = node)
                                             for node in env.successor_function_nodes ]
            env.process_successor_function_nodes = [ opt.transform_ast(net_info = self.net_info, node = node)
                                                     for node in env.process_successor_function_nodes ]
            env.successor_function_nodes = flatten_lists(env.successor_function_nodes)
            env.process_successor_function_nodes = flatten_lists(env.process_successor_function_nodes)

    def _gen_all_spec_succs(self):
        """ Build all needed instances of transition specific
        successor functions abstract representations.

        This method updates C{self._nodes}.
        """
        env = self.env
        acc = []
        for i, transition in enumerate(self.net_info.transitions):
            function_name = "succs_{}".format(i)
            if self.config.dump_enabled:
                print function_name + " <=> " + transition.name
            assert(function_name not in env.global_names)
            env.global_names.add(function_name)

            gen = SuccTGenerator(env = self.env,
                                 net_info = self.net_info,
                                 builder = netir.Builder(),
                                 transition = transition,
                                 function_name = function_name,
                                 marking_type = self.marking_type,
                                 config = self.config)
            acc.append(gen())

        return acc

    def _gen_all_process_spec_succs(self):
        """ Build all needed instances of process specific successor
        function abstract representation nodes.
        """
        acc = []
        if self.config.optimize_flow:
            for i, process in enumerate(self.net_info.process_info):
                function_name = "succP_{}".format(i)
                gen = ProcessSuccGenerator(env = self.env,
                                           process_info = process,
                                           function_name = function_name,
                                           marking_type = self.marking_type)
                acc.append(gen())
        return acc

    def _gen_main_succ(self):
        """ Produce main successor function abstract representation node. """

        self.succs_function = 'succs'
        vp = VariableProvider(set([self.succs_function]))
        arg_marking_var = vp.new_variable(variable_type = self.marking_type.type)
        arg_marking_acc_var = vp.new_variable(variable_type = self.marking_type.container_type)
        arg_ctx_var = vp.new_variable(variable_type = TypeInfo.get('NecoCtx'))

        builder = netir.Builder()
        builder.begin_function_Succs(function_name = "succs",
                                      arg_marking_var = arg_marking_var,
                                      arg_marking_acc_var = arg_marking_acc_var,
                                      arg_ctx_var = arg_ctx_var,
                                      variable_provider = vp)

        marking_acc_node = netir.Name(arg_marking_acc_var.name)
        marking_arg_node = netir.Name(arg_marking_var.name)
        ctx_node = netir.Name(arg_ctx_var.name)

        if self.config.optimize_flow:
            for function_name in self.env.process_succ_functions:
                builder.emit_ProcedureCall(function_name = function_name,
                                           arguments = [ marking_arg_node,
                                                         marking_acc_node,
                                                         ctx_node ])

        else:
            for function_name in self.env.succ_functions:
                builder.emit_ProcedureCall(function_name = function_name,
                                           arguments = [ marking_arg_node,
                                                         marking_acc_node,
                                                         ctx_node ])

        builder.end_function()
        return builder.ast()

    def _gen_init(self):
        """ Produce initial marking function abstract representation node. """

        marking_var = VariableInfo('marking', variable_type = self.marking_type.type)
        variable_provider = VariableProvider(set(['init', marking_var.name]))

        builder = netir.Builder()
        builder.begin_function_Init(function_name = 'init',
                                    marking_var = marking_var,
                                    variable_provider = variable_provider)

        for place_info in self.net_info.places:
            if len(place_info.tokens) > 0:
                if self.config.optimize_flow and place_info.flow_control:
                    builder.emit_UpdateFlow(marking_var = marking_var,
                                            place_info = place_info);
                    continue

                # handle other places

                for token in place_info.tokens:
                    info = TokenInfo.from_raw(token)
                    if info.is_Tuple:
                        builder.emit_TupleOut(marking_var = marking_var,
                                               place_name = place_info.name,
                                               tuple_info = info)
                    elif info.is_Value:
                        t = info.type
                        if self.config.normalize_pids and t.is_Pid:
                            builder.emit_AddPid(marking_var = marking_var,
                                                 place_name = place_info.name,
                                                 token_expr = netir.Token(value = token,
                                                                          place_name = place_info.name))

                        elif t in [ TypeInfo.Int, TypeInfo.BlackToken ]:
                            builder.emit_AddToken(marking_var = marking_var,
                                                   place_name = place_info.name,
                                                   token_expr = netir.Token(value = token,
                                                                             place_name = place_info.name))
                        elif t.is_UserType or t.is_AnyType:
                            expr = netir.Pickle(obj = info.raw)
                            builder.emit_AddToken(marking_var = marking_var,
                                                   place_name = place_info.name,
                                                   token_expr = expr)
                        else:
                            raise NotImplementedError, info.value.type()
                    else:
                        raise NotImplementedError

        builder.end_function()
        return builder.ast()

    def gen_netir(self):
        """ produce abstract representation nodes.
        """
        env = self.env

        env.successor_function_nodes = flatten_lists(self._gen_all_spec_succs())
        env.process_successor_function_nodes = flatten_lists(self._gen_all_process_spec_succs())
        env.main_successor_function_node = flatten_lists(self._gen_main_succ())
        env.init_function_node = flatten_lists(self._gen_init())

    def produce_compilation_trace(self):
        trace_object = { "marking_type" : self.marking_type,
                         "optimize"     : self.config.optimize,
                         "model"        : self.config.model }

        io = StringIO.StringIO()
        pickle.dump(trace_object, io, -1)
        v = io.getvalue()
        io.close()
        return v

    def run(self):
        self.gen_netir()
        self.optimize_netir()
        net = self.backend.compile_IR(self.env, self.config, self)
        return net

################################################################################

if __name__ == "__main__":
    doctest.testmod()

################################################################################
# EOF
################################################################################
