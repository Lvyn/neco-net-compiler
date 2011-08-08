""" Main compiler interface. """

import itertools
from snakes.nets import *
import neco.config as config
from neco.utils  import flatten_lists

import netir, nettypes
from info import *
from itertools import izip_longest

from glue import FactoryManager

################################################################################

class CompilingEnvironment(object):
    """ Contains data that need to be shared between components;
    """

    def __init__(self):
        """ Build a new compiling environment.
        """
        self._succ_function_names = {}
        self._process_succ_function_names = set()

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

class VariableHelper(object):
    """ Utility class that helps handling shared variables.
    """

    def __init__(self, shared, wordset):
        """ Build a new helper from a set of shared variables
        and a word set.

        @param shared: shared variables.
        @type shared: C{multidict}
        @param wordset: word set representing existing symbols.
        @type wordset: C{WordSet}
        """
        assert( isinstance(shared, multidict) )
        self._shared = shared
        self._used = multidict()
        self._wordset = wordset

    def set_used(self, name, local_name, input):
        """ Mark a variable as used, providing the variable name
        its local name and the input using the variable.

        @param name: variable name.
        @type name: C{str}
        @param local_name: local variable name.
        @type local_name: C{str}
        @param input: input using the variable.
        @type input: C{ArcInfo}
        """
        self._used.add(name, (local_name, input))

    def all_used(self, name):
        """ Check if all instances of a variable were used.

        @returns C{True} if all variables were used, C{False} otherwise.
        @rtype: C{bool}
        """
        return len(self._used[name]) == len(self._shared[name])

    def get_local_names(self, name):
        """ Get all local names of a variable.

        @return: all local names of a variable.
        @rtype: C{multidict}
        """
        return self._used[name]

    def is_shared(self, name):
        """ Check if a variable is shared.

        @return: True if the variable is shared, C{False} otherwise.
        @rtype: C{bool}
        """
        return self._shared.has_key(name)

    def get_new_name(self, variable_name):
        """ Get a name for a variable.

        @param variable_name: name of the variable needing a new name.
        @type variable_name: C{str}
        @return: a new name if the variable is shared, variable name otherwise.
        @rtype: C{str}
        """
        if self.is_shared(variable_name):
            return self._wordset.fresh( "_shared_%s_" % variable_name)
        else:
            return variable_name

    def fresh(self, *args, **kwargs):
        """ Get a fresh name.

        TODO: use WordSet params

        @return: a fresh name.
        @rtype: C{str}
        """
        return self._wordset.fresh(*args, **kwargs)

################################################################################

class ProcessSuccGenerator(object):
    """ Class that produces a succ function specific to ABCD processes
    """

    def __init__(self, env, net_info, process_info,
                 function_name, marking_type):
        """
        @param net_info: Petri net informations.
        @type net_info: C{info.NetInfo}
        @param builder: netir builder.
        @type builder: C{netir.Builder}
        @param process_info: process informations.
        @type process_info: C{info.ProcessInfo}
        @param function_name: process successor function name
        @type function_name: C{str}
        @param marking_type: marking type
        @type marking_type: C{nettypes.MarkingType}
        """
        self._env = env
        self._net_info = net_info
        self._process_info = process_info
        self._function_name = function_name
        self._marking_type = marking_type


        self._builder = netir.Builder()

        ws = WordSet( [ function_name ] )
        self._names = ws

        self._arg_marking = ws.fresh(True, base = 'a')
        self._marking_set = ws.fresh(True, base = 'ms')

        env.register_process_succ_function(function_name)

    def __call__(self):
        """ Generate function.
        """
        env = self._env
        function_name = self._function_name
        arg_marking   = self._arg_marking
        marking_set   = self._marking_set
        process_info  = self._process_info

        if not config.get('process_flow_elimination'):
            return

        builder = self._builder

        builder.begin_function_SuccP( function_name   = function_name,
                                      marking_name    = arg_marking,
                                      markingset_name = marking_set,
                                      process_info    = process_info )

        # enumerate places with not empty post
        ne_post = [ place for place in process_info.flow_places if place.post ]

        current_flow = builder.Name('flow')
        read=builder.ReadFlow(marking_name=arg_marking,
                              process_name=process_info.name)
        builder.emit_Assign(variable=current_flow, expr=read)

        for i, flow_place in enumerate(ne_post):
            if i == 0:
                builder.begin_If( condition = builder.FlowCheck(marking_name=arg_marking,
                                                                current_flow=current_flow,
                                                                place_info=flow_place))
            else:
                builder.begin_Elif(condition=builder.FlowCheck(marking_name=arg_marking,
                                                               current_flow=current_flow,
                                                               place_info=flow_place))

            #produced inside each if block:
            for transition in flow_place.post:
                name = env.get_succ_function_name( transition )
                builder.emit_ProcedureCall( function_name = name,
                                            arguments = [ netir.Name( name = marking_set ),
                                                          netir.Name( name = arg_marking ) ] )

        builder.end_all_blocks()
        builder.end_function()
        return builder.ast()
################################################################################

class SuccTGenerator(object):
    """ Transition specific succ function generator.

    This class is used for building a transition specific succ function.
    """

    def __init__(self, env, net_info, builder, transition, function_name, marking_type, ignore_flow):
        """ Builds the transition specific succ function generator.

        @param builder: builder structure for easier ast construction
        @type builder: C{neco.core.netir.Builder}
        @param transition: considered transition
        @type transition: C{neco.core.info.TransitionInfo}
        @param function_name: function name
        @type function_name: C{str}
        @param ignore_flow: ignore flow control places ?
        @type ignore_flow: C{bool}
        """
        self.net_info = net_info
        self.builder = builder
        self.transition = transition
        self.function_name = function_name
        self.marking_type = marking_type
        self._ignore_flow = ignore_flow
        self.env = env
        self.consume = []
        self.names = WordSet( transition.variables )

        if config.get('optimise'):
            self.transition.order_inputs()

        # create
        self.arg_marking = self.names.fresh(True, base = 'a')
        self.marking_set = self.names.fresh(True, base = 'ms')

        self.builder.begin_function_SuccT( function_name   = self.function_name,
                                           marking_name    = self.arg_marking,
                                           markingset_name = self.marking_set,
                                           transition_info = self.transition)

        self.variable_helper = VariableHelper( transition.shared_input_variables(),
                                               self.names )

        env.register_succ_function(transition, function_name)

    def gen_unify_shared(self, name, local_name, var_type):
        """ Produces the unification process for shared variables.

        In the context where different names represent a unique variable,
        this function compares these names and use a witness for the final
        variable name.

        @param name: initial variable name (from the model)
        @type name: C{str}
        @param local_name: real variable name (in the produced code)
        @type local_name: C{str}
        """
        # check if all instances are used
        if self.variable_helper.is_shared( name = name ):
            if self.variable_helper.all_used( name = name ):

                # get all local names for the unification process
                locals = self.variable_helper.get_local_names(name)
                locals.pop(-1)

                # compare all values
                self.builder.begin_If( netir.Compare( left = netir.Name( name = local_name,
                                                                         place_name = var_type ),
                                                      ops =  [ netir.EQ() for i in locals ],
                                                      comparators = [ netir.Name( name = local_name,
                                                                                  place_name = var_type )
                                                                      for (local_name, origin) in locals ] ) )

                # build a variable with the initial name from a witness
                self.builder.emit_Assign( variable = VariableInfo(name = name),
                                          expr = netir.Name( name = local_name,
                                                             place_name = var_type ) )

    def modified_places(self):
        """ Return places that are modified during transition firing, ie.,
        pre(t) and post(t) that are not read arcs.

        @return: modified places.
        @rtype: C{set}
        """
        trans = self.transition
        mod = set([])
        for input in trans.inputs:
            if (input.is_Expression or input.is_Variable
                or input.is_Tuple or input.is_Value or input.is_MultiArc):
                mod.add(input.place_info)

        for output in trans.outputs:
            mod.add(output.place_info)

        return mod

    def gen_enumerators(self):
        """ Produces all the token enumeration blocs.
        """

        builder = self.builder
        trans = self.transition
        variable_helper = self.variable_helper
        trans.variable_helper = variable_helper
        consume = self.consume

        # places that provides multiple tokens, _cannot_ be used with by index acces
        multi_places = trans.input_multi_places

        if config.get('optimise'):
            trans.order_inputs()

        # loop over inputs
        for input in trans.inputs:
            if self._ignore_flow and input.place_info.flow_control:
                continue

            builder.emit_Comment("Enumerate {input} - place: {place}".format(input=input, place=input.place_name))

            # use index access if available
            place_type = self.marking_type.get_place_type_by_name(input.place_info.name)
            if place_type.provides_by_index_access and input.place_info not in multi_places:
                index = variable_helper.fresh(True, base = "i")
                trans.add_intermediary_variable( VariableInfo( name = index, type = TypeInfo.Int) ) # to do type specific keys
            else:
                index = None

            # produce the enumeration and tests according to the input's type

            # variable
            if input.is_Variable:
                variable = input.variable
                # generate a new name, if the variable is not shared the local
                # name will be the same
                local_name = variable_helper.get_new_name(variable.name)

                # notify that the variable is used
                variable_helper.set_used( name = variable.name,
                                          local_name = local_name,
                                          input = input )

                builder.begin_TokenEnumeration( token_name = local_name,
                                                marking_name = self.arg_marking,
                                                place_name = input.place_name,
                                                token_is_used = True,
                                                use_index = index )

                consume.append( (input, index) )

                self.gen_unify_shared( name = variable.name,
                                       local_name = local_name,
                                       var_type = input.place_name )

            # test
            elif input.is_Test:
                inner = input.inner

                if inner.is_Variable:
                    local_name = variable_helper.get_new_name(inner.name)
                    variable_helper.set_used( name = inner.name,
                                              local_name = local_name,
                                              input = input )

                    builder.begin_TokenEnumeration( token_name = local_name,
                                                    marking_name = self.arg_marking,
                                                    place_name = input.place_name,
                                                    token_is_used = True,
                                                    use_index = index )

                    self.gen_unify_shared( name = inner.name,
                                           local_name = local_name,
                                           var_type = input.place_name)

                elif inner.is_Value:
                    place_info = self.net_info.place_by_name(input.place_name)
                    place_type = self.marking_type.get_place_type_by_name(place_info.name)

                    token_name = variable_helper.fresh(True, base = "t")
                    trans.add_intermediary_variable( VariableInfo( name = token_name, type = place_type.token_type) )


                    # get a token
                    builder.begin_TokenEnumeration( token_name = token_name,
                                                    marking_name = self.arg_marking,
                                                    place_name = input.place_name,
                                                    token_is_used = False,
                                                    use_index = index )
                    # consume.append(input)
                    if not place_info.type.is_BlackToken:
                        # check token value
                        builder.begin_If( netir.Compare( left  = netir.Name( name = token_name ),
                                                         ops = [ netir.EQ() ],
                                                         comparators = [ netir.Value( value = input.value,
                                                                                      place_name = input.place_name ) ] ) )


                elif inner.is_Tuple:
                    # produce names for tuple components
                    inner.gen_names( self.variable_helper )

                    # by index acces not used

                    # get a tuple
                    builder.begin_TokenEnumeration( token_name = inner.name,
                                                    marking_name = self.arg_marking,
                                                    place_name = input.place_name,
                                                    token_is_used = False,
                                                    use_index = None )

                    if not (inner.type.is_TupleType and len(inner.type) == len(inner)):
                        # check its type
                        builder.begin_CheckTuple( tuple_name = inner.name,
                                                  tuple_info = inner )

                    self._gen_tuple_decomposition(input, inner)

                else:
                    raise NotImplementedError, "ArcTest : inner = %s" % inner

            # value
            elif input.is_Value:
                place_info = self.net_info.place_by_name(input.place_name)
                place_type = self.marking_type.get_place_type_by_name(place_info.name)

                token_name = variable_helper.fresh(True, base = "t")
                trans.add_intermediary_variable( VariableInfo( name = token_name, type = place_type.token_type) )

                # get a token
                builder.begin_TokenEnumeration( token_name = token_name,
                                                marking_name = self.arg_marking,
                                                place_name = input.place_name,
                                                token_is_used = False,
                                                use_index = index )
                consume.append( (input, index) )

                if not place_info.type.is_BlackToken:
                    # check token value
                    builder.begin_If( netir.Compare( left  = netir.Name( name = token_name ),
                                                     ops = [ netir.EQ() ],
                                                     comparators = [ netir.Value( value = input.value,
                                                                                  place_name = input.place_name ) ] ) )

            # flush
            elif input.is_Flush:
                inner = input.inner
                if inner.is_Variable:
                    if variable_helper.is_shared(inner.name):
                        raise NotImplementedError

                    consume.append( (input, index) )
                else:
                    raise NotImplementedError, "flush %s" % repr(inner)

            # tuple
            elif input.is_Tuple:
                # produce names for tuple components
                input.tuple.gen_names( self.variable_helper )

                # get a tuple
                builder.begin_TokenEnumeration( token_name = input.tuple.name,
                                                marking_name = self.arg_marking,
                                                place_name = input.place_name,
                                                token_is_used = False,
                                                index = None ) # no index access

                if not (input.tuple.type.is_TupleType and len(input.tuple.type) == len(input.tuple)):
                    # check its type
                    builder.begin_CheckTuple( tuple_name = input.tuple.name,
                                              tuple_info = input.tuple )


                self._gen_tuple_decomposition(input, input.tuple)
                consume.append( (input, index) )

            elif input.is_MultiArc:
                names = {} # variable -> local_name
                # sub_arcs as variables
                for sub_arc in input.sub_arcs:
                    if sub_arc.is_Variable:
                        variable = sub_arc.variable
                        local_name = variable_helper.get_new_name(variable.name)
                        names[sub_arc.variable] = local_name
                        variable_helper.set_used( name = variable.name,
                                                  local_name = local_name,
                                                  input = input )
                    else:
                        raise NotImplementedError

                offsets = [ variable_helper.fresh(True, base = "i") for _ in names ]
                builder.begin_MultiTokenEnumeration( token_names = names.values(),
                                                     offset_names = offsets,
                                                     marking_name = self.arg_marking,
                                                     place_name = input.place_name )

                consume.append( (input, None) ) # no index access allowed
                #raise NotImplementedError

            else:
                raise NotImplementedError, input.arc_annotation.__class__

    def _gen_tuple_decomposition(self, input, tuple):
        """ Produce the decomposition of a tuple (pattern matching).

        @param input: input arc
        @type input: C{neco.core.info.ArcInfo}
        @param tuple: tuple to decompose
        @type tuple: C{tuple}
        """
        builder = self.builder
        trans = self.transition
        variable_helper = self.variable_helper

        # type already checked
        # match pattern
        builder.begin_Match( tuple_info = tuple )

        for (name, local_name) in tuple.base_names():
            variable_helper.set_used( name = name,
                                      local_name = local_name,
                                      input = input )

            self.gen_unify_shared(name = name,
                                  local_name = local_name,
                                  var_type = input.place_name ) # TO DO change!

        for (inner, type) in izip_longest(tuple.split(), tuple.type.split(), fillvalue=TypeInfo.AnyType):
            if inner.is_Tuple:
                if not type.is_AnyType:
                    inner.update_type(type)

                # notify new variable introduction
                trans.add_intermediary_variable( VariableInfo( name = tuple.name, type = tuple.type) )

                if not (inner.type.is_TupleType and len(inner.type) == len(inner)):
                    # check its type
                    builder.begin_CheckTuple( tuple_name = inner.name,
                                              tuple_info = inner )

                self._gen_tuple_decomposition(input, inner)
            else:
                trans.add_intermediary_variable( VariableInfo( name = inner.local_name,
                                                               type = type ) )

    def __call__(self):
        """ Build an instance of SuccT from a TransitionInfo object.

        @param trans: transition info.
        @type trans: C{TransitionInfo}
        @return: successor function abstract representation.
        @rtype: C{SuccFunctionAR}
        """
        trans = self.transition
        names = self.names
        builder = self.builder

        if config.get('trace_calls'):
            builder.emit_Print("calling " + self.function_name)

        # for loops
        self.gen_enumerators()

        # guard
        guard = ExpressionInfo( trans.trans.guard._str )
        try:
            if eval(guard.raw) != True:
                builder.begin_GuardCheck( condition = netir.PyExpr(guard) )
        except:
            builder.begin_GuardCheck( condition = netir.PyExpr(guard) )

        if config.get('trace_calls'):
            builder.emit_Print("  guard valid in " + self.function_name)

        # eval productions and check their types
        computed_productions = {}
        for output in trans.outputs:
            if self._ignore_flow and output.place_info.flow_control:
                continue

            elif output.is_Expression:
                # new temporary variable
                var_name = self.variable_helper.fresh( True, base = 'e' )
                trans.add_intermediary_variable( VariableInfo( name = var_name,
                                                               type = output.place_info.type ) )

                # evaluate and assign the result to the variable
                builder.emit_Assign( variable = VariableInfo(var_name),
                                     expr = netir.PyExpr(output.expr) )
                check = True
                try:
                    print ">>>> BEGIN TO DO %s <<<< %s" % (__FILE__, output.expr.raw)
                    value = eval(output.expr.raw)
                    if output.place_info.type.contains(value):
                        check = False
                    print ">>>> END TO DO %s <<<< " % __FILE__
                except:
                    pass

                # check its type
                if check:
                    computed_productions[output] = netir.Name( var_name )
                else:
                    computed_productions[output] = netir.Name( var_name )

            elif output.is_Value:
                value = output.value
                var_name = self.variable_helper.fresh( True, base = 'e' )
                check = True
                try:
                    v = eval(repr(value.raw))
                    if output.place_info.type.contains(v):
                        check = False
                except:
                    pass

                # check its type
                if check:
                    builder.emit_Assign( variable = VariableInfo(var_name),
                                         expr = netir.PyExpr( ExpressionInfo( repr(output.value.raw) ) ) )

                    r = netir.Name( var_name )
                else:
                    r = netir.PyExpr( ExpressionInfo( repr(output.value.raw) ) )

                computed_productions[output] = r
            elif output.is_Variable:
                variable = output.variable
                output_impl_type = self.marking_type.get_place_type_by_name( output.place_info.name ).token_type
                if not (output_impl_type.is_AnyType or (variable.type == output_impl_type)):
                    builder.begin_CheckType( variable = variable,
                                             type = output_impl_type )
                computed_productions[output] = netir.Name( variable.name )

            elif output.is_Flush:
                # no type check, object places
                pass

            elif output.is_Tuple:
                # no type check, WARNING: may be unsound !
                pass

            else:
                raise NotImplementedError, output.arc_annotation.__class__

        # copy
        new_marking = names.fresh(True, base = "n")

        builder.emit_MarkingCopy( dst_name = new_marking,
                                  src_name = self.arg_marking,
                                  mod = self.modified_places() )


        # add intermediary variable
        trans.add_intermediary_variable( VariableInfo( name = new_marking,
                                                       type = self.marking_type.type ) )


        # consume
        for (input, index) in self.consume:
            builder.emit_Comment(message = "Consume {input} - place: {place}".format(input=input, place=input.place_name))
            if input.is_Variable:
                variable = input.variable
                builder.emit_RemToken( marking_name = new_marking,
                                       place_name = input.place_name,
                                       token_expr = netir.Name(variable.name),
                                       use_index = index )
            elif input.is_Test:
                pass # do not consume !

            elif input.is_Flush:
                inner = input.inner
                if inner.is_Variable:
                    builder.emit_FlushIn( token_name = inner.name,
                                          marking_name = new_marking,
                                          place_name = input.place_name )
                else:
                    raise NotImplementedError, "inner : %s" % repr(inner)

            elif input.is_Value:
                builder.emit_RemToken( marking_name = new_marking,
                                       place_name = input.place_name,
                                       token_expr = netir.Value( value = input.value,
                                                                 place_name = input.place_name),
                                       use_index = index )

            elif input.is_Tuple:
                builder.emit_RemTuple( marking_name = new_marking,
                                       place_name = input.place_name,
                                       tuple_expr = netir.Name(input.tuple.name))

            elif input.is_MultiArc:
                names = {}
                for sub_arc in input.sub_arcs:
                    if sub_arc.is_Variable:
                        variable = sub_arc.variable
                        builder.emit_RemToken( marking_name = new_marking,
                                               place_name = input.place_name,
                                               token_expr = netir.Name(variable.name),
                                               use_index = None )
                    else:
                        raise NotImplementedError, sub_arc.arc_annotation
            else:
                raise NotImplementedError, input.arc_annotation

        # produce
        for output in trans.outputs:
            builder.emit_Comment(message="Produce {output} - place: {place}".format(output=output, place=output.place_name))
            if self._ignore_flow and output.place_info.flow_control:
                new_flow = [ place for place in trans.post if place.flow_control ]
                assert(len(new_flow) == 1)
                builder.emit_UpdateFlow( marking_name = new_marking,
                                         place_info = new_flow[0] )


            elif output.is_Expression:
                if computed_productions.has_key(output):
                    token_expr = computed_productions[output]

                builder.emit_AddToken( marking_name = new_marking,
                                       place_name = output.place_name,
                                       token_expr = token_expr )

            elif output.is_Value:
                if computed_productions.has_key(output):
                    token_expr = computed_productions[output]
                else:
                    #
                    # TO DO TRY REPR
                    #
                    value = output.value
                    token_expr = netir.PyExpr( ExpressionInfo( repr(value.raw) ))

                builder.emit_AddToken( marking_name = new_marking,
                                       place_name = output.place_name,
                                       token_expr = token_expr )

            elif output.is_Variable:
                if computed_productions.has_key(output):
                    token_expr = computed_productions[output]
                else:
                    value = output.value
                    token_expr = netir.Name( output.name )

                builder.emit_AddToken( marking_name = new_marking,
                                       place_name = output.place_name,
                                       token_expr = token_expr )

            elif output.is_Flush:
                inner = output.inner
                if inner.is_Variable:
                    produced_token = inner.name
                    builder.emit_FlushOut( marking_name = new_marking,
                                           place_name = output.place_name,
                                           token_expr = netir.Name(produced_token) )

                elif inner.is_Expression:
                    builder.emit_FlushOut( marking_name = new_marking,
                                           place_name = output.place_name,
                                           token_expr = netir.PyExpr(inner) )
                else:
                    raise NotImplementedError, "Flush.inner : %s" % inner

            elif output.is_Tuple:
                # to do: if input then use var
                if (False):
                    pass
                # general case:
                else:
                    builder.emit_TupleOut( marking_name = new_marking,
                                           place_name = output.place_name,
                                           tuple_info = output.tuple )
            else:
                raise NotImplementedError, output.arc_annotation.__class__

        # add marking to set
        builder.emit_AddMarking( markingset_name = self.marking_set,
                                 marking_name = new_marking)
        # end function
        builder.end_all_blocks()
        builder.end_function()
        if config.get('debug'):
            print self.transition.variable_informations()

        return builder.ast()

################################################################################

class Compiler(object):
    """ The main compiler class.

    This class is used to produce a library from a snake.nets.PetriNet.
    """

    def __init__(self, net, factory_manager = FactoryManager(), atoms = []):
        """ Initialise the compiler from a Petri net.

        builds the basic info structure from the snakes petri net representation

        @param net: Petri net.
        @type net: C{snakes.nets.PetriNet}
        """
        self.env = CompilingEnvironment()
        self.net = net
        self.dump_enabled = False
        self.debug = False

        self._ignore_flow = config.get('process_flow_elimination')
        FactoryManager.update( factory_manager )
        fm = FactoryManager.instance()

        self.net_info = NetInfo(net)
        self.markingtype_class = "StaticMarkingType"
        self.marking_type = fm.markingtype_factory.new(self.markingtype_class)

        self.optimisations = []
        self.rebuild_marking_type()

        self.successor_function_nodes = []
        self.process_successor_function_nodes = []
        self.main_successor_function_node = None
        self.init_function_node = None

        self.global_names = WordSet([])
        self._successor_functions = []
        # TODO hardcoded for testing
        self.atoms = [ info.AtomInfo(atom, ['s1', 's2']) for atom in atoms ]
        print "atoms : ", self.atoms

    @property
    def successor_functions(self):
        return self._successor_functions

    @property
    def marking_type(self):
        """ Marking type. """
        return self._marking_type

    @marking_type.setter
    def marking_type(self, marking_type):
        self._marking_type = marking_type
        self.markingset_type = FactoryManager.instance().markingsettype_factory.new_MarkingSetType(marking_type)

    @property
    def factory_manager(self):
        """ Factory Manager. """
        return FactoryManager.instance()

    @factory_manager.setter
    def factory_manager(self, factory_manager):
        FactoryManager.update( factory_manager )

    def set_marking_type_by_name(self, markingtype_class):
        """ Specify set marking type by name (places will be rebuild).

        @param markingtype_class: marking type name.
        @type markingtype_class: C{str}
        """
        self.markingtype_class = markingtype_class
        self.marking_type = FactoryManager.instance().markingtype_factory.new(self.markingtype_class)
        self.rebuild_marking_type()

    def available_marking_types(self):
        """ Get all available marking types.

        @return: marking types
        @rtype: C{list<str>}
        """
        return self.markingtype_factory.products()

    def rebuild_marking_type(self):
        """ Rebuild the marking type. (places will be rebuild) """
        # add place types to the marking type
        for place_info in self.net_info.places:
            self.marking_type.append( place_info )

        fm = FactoryManager.instance()
        self.marking_type.gen_types(fm.select_type)
        if self.dump_enabled:
            print self.marking_type

    def add_optimisation(self, opt):
        """ Add an optimisation.

        @param opt: optimisation pass.
        @type opt: C{neco.opt.OptimisationPass}
        """
        global g_opt
        g_opt = True
        self.optimisations.append(opt)
        # update factories and updates modules
        #self.factory_manager = opt.update_factory_manager(self.factory_manager)

        opt.update_factory_manager()
        fm = FactoryManager.instance()
        self.marking_type = fm.markingtype_factory.new(self.markingtype_class)
        self.rebuild_marking_type()

    def optimise_netir(self):
        """ Run optimisation passes on the AST. """
        for opt in self.optimisations:
            self.successor_function_nodes = [ opt.transform_ast(net_info = self.net_info, node = node)
                                              for node in self.successor_function_nodes ]
            self.process_successor_function_nodes = [ opt.transform_ast(net_info = self.net_info, node = node)
                                                      for node in self.process_successor_function_nodes ]
            self.successor_function_nodes = flatten_lists( self.successor_function_nodes )
            self.process_successor_function_nodes = flatten_lists( self.process_successor_function_nodes )


    def _gen_all_spec_succs(self):
        """ Build all needed instances of transition specific
        successor functions abstract representations.

        This method updates C{self._nodes}.
        """
        list = []
        for i,t in enumerate(self.net_info.transitions):
            function_name = "succs_%d" % i # TO DO use name + escape
            if self.dump_enabled:
                print function_name + " <=> " + t.name
            assert( function_name not in self.global_names )
            self.global_names.add(function_name)
            #self._gen_spec_succ(t, function_name)

            gen = SuccTGenerator(self.env,
                                 self.net_info,
                                 netir.Builder(), #self.builder,
                                 t,
                                 function_name,
                                 self.marking_type,
                                 ignore_flow = self._ignore_flow)
            list.append( gen() )

            self._successor_functions.append( (function_name, t.process_name) )
        return list

    def _gen_all_process_spec_succs(self):
        """ Build all needed instances of process specific successor
        function abstract representation nodes.
        """
        list = []
        if config.get('process_flow_elimination'):
            for i, process in enumerate(self.net_info.process_info):
                function_name = "succP_%d" % i # process.name
                gen = ProcessSuccGenerator(self.env,
                                           self.net_info,
                                           process,
                                           function_name,
                                           self.marking_type)
                list.append( gen() )
        return list

    def _gen_main_succ(self):
        """ Produce main successor function abstract representation node. """

        self.succs_function = 'succs'
        names = WordSet([self.succs_function])
        marking_arg = names.fresh(True, base = 'a')
        markingset = names.fresh(True, base = 'ms')

        builder = netir.Builder()
        builder.begin_function_Succs( function_name = "succs",
                                           marking_argument_name = marking_arg,
                                           markingset_variable_name = markingset )

        markingset_node  = netir.Name(markingset)
        marking_arg_node = netir.Name(marking_arg)

        if self._ignore_flow:
            for function_name in self.env.process_succ_functions:
                builder.emit_ProcedureCall( function_name = function_name,
                                                 arguments = [ markingset_node,
                                                               marking_arg_node ] )

        else:
            for function_name in self.env.succ_functions:
                builder.emit_ProcedureCall( function_name = function_name,
                                                 arguments = [ markingset_node,
                                                               marking_arg_node ] )

        builder.end_function()
        return builder.ast()

    def _gen_init(self):
        """ Produce initial marking function abstract representation node. """

        marking_name = 'marking'
        names = WordSet(['init', marking_name])

        builder = netir.Builder()

        builder.begin_function_Init(function_name = 'init',
                                    marking_name = marking_name)

        for place_info in self.net_info.places:
            if len(place_info.tokens) > 0:
                # add tokens
                if self._ignore_flow and place_info.flow_control:
                    builder.emit_UpdateFlow(marking_name = marking_name,
                                                 place_info = place_info);
                    continue

                for token in place_info.tokens:
                    info = TokenInfo.from_raw( token )
                    if info.is_Tuple:
                        builder.emit_TupleOut( marking_name = marking_name,
                                                    place_name = place_info.name,
                                                    tuple_info = info )
                    elif info.is_Value:
                        t = info.type
                        if t in [ TypeInfo.Int, TypeInfo.BlackToken ]:
                            builder.emit_AddToken( marking_name = marking_name,
                                                        place_name = place_info.name,
                                                        token_expr = netir.Token( value = token,
                                                                                  place_name = place_info.name ) )
                        elif t.is_UserType or t.is_AnyType:
                            expr = netir.Pickle( obj = info.raw )
                            builder.emit_AddToken( marking_name = marking_name,
                                                        place_name = place_info.name,
                                                        token_expr = expr )
                        else:
                            raise NotImplementedError, info.value.type()
                    else:
                        raise NotImplementedError

        builder.end_function()
        return builder.ast()

    def gen_netir(self):
        """ produce abstract representation nodes.
        """
        self.successor_function_nodes = flatten_lists( self._gen_all_spec_succs() )
        self.process_successor_function_nodes = flatten_lists( self._gen_all_process_spec_succs() )
        self.main_successor_function_node = flatten_lists( self._gen_main_succ() )
        self.init_function_node = flatten_lists( self._gen_init() )

################################################################################

if __name__ == "__main__":
    import doctest
    doctest.testmod()

################################################################################
# EOF
################################################################################
