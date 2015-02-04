""" Stub AST compilser. 

This visitor class compiles Neco AST to target language AST.

\see neco/asdl/netir.asdl for full AST definition.
\see neco/backends/python/netir.py for an example.

"""

from neco.core.info import ExpressionInfo
import neco.core.netir as coreir

################################################################################

class CompilerVisitor(coreir.CompilerVisitor):
    """ Stub AST compiler visitor class. 
    
    Each compile_{AST_NODE} function returns an AST in target language that 
    corresponds to the node {AST_NODE} in Neco AST (neco.core.netir).

    Each time you want the AST of a sub expression you should use
       self.compile(sub_node)

    This will dispatch the call to adequate function.
    """
    
    backend = "stub-backend" # backend name

    ################################################################################

    def __init__(self, env, config):
        self.env = env
        self.config = config

    def compile(self, node):
        """ Dispatch compile based on object type. """
        return super(CompilerVisitor, self).compile(node)

    ################################################################################
    # User Code
    ################################################################################    

    def compile_Print(self, node):
        """ AST that prints 'node.message' """
        raise NotImplementedError

    def compile_Comment(self, node):
        """ AST of a comment, can be empty """
        return []

    def compile_If(self, node):
        """ AST of an 'If', 

         condition:       'self.compile(node.condition)'
        body:             'self.compile(node.body)'
        else clause body: 'self.compile(node.orelse)' 
        """
        raise NotImplementedError

    def compile_Compare(self, node): 
        """ AST of a comparison, there may be multiple ops and multiple comparators. 

        left operand: self.compile(node.left),
        operators:    [ self.compile(op) for op in node.ops ]
        comparators:  [ self.compile(comparator) for comparator in node.comparators ]
        """
        raise NotImplementedError

    def compile_EQ(self, node):
        """ AST of Eq operator in target AST """
        raise NotImplementedError

    def compile_CheckTuple(self, node):
        """ AST of a tuple type check.

        It checks if variable 'node.tuple_var.name' is a tuple of adequate length based on 'node.tuple_info'. 
        This usually returns an if expression which body is 'self.compile(node.body)'  
        \see neco/backends/python/netir.py
        """
        raise NotImplementedError

    def compile_CheckType(self, node):
        """ AST of a type chack.

        It checks that 'node.variable.name' is of type 'node.type', the test can be omitted if 'node.type.is_AnyType' is true """
        type_info = node.type
        if type_info.is_AnyType:
            return self.compile(node.body)

        return NotImplementedError

    def compile_Match(self, node):
        """ This is the most complicated AST part, it returns an AST that matches and decomposes tuples. 
        
        \see neco/backends/python/netir.py
        """

    def compile_Assign(self, node):
        """ AST that assigns the result of an expression ('self.compile(node.expr)') to a variable ('node.variable.name'). """
        raise NotImplementedError

    def compile_Value(self, node):
        """ AST representing value "node.value.raw". 
        
        Depending on optimizations if a value have different representations a conversion may be needed.
        """
        raise NotImplementedError

    def compile_Pickle(self, node):
        """ Pythonic specific.
        
        pickle representation, this is Pythonic language specific for some complex types. """
        raise NotImplementedError

    def compile_FlushIn(self, node):
        """ AST of flush input arc (removes tokens from place). 

        place:   node.place_name
        marking: node.marking_var        
        """
        raise NotImplementedError

    def compile_RemAllTokens(self, node):
        """ AST that removes all tokens from place 'node.place_name' of marking 'node.marking_var' """
        raise NotImplementedError

    def compile_FlushOut(self, node):
        """ AST corresponding to output flush arc (adds tokens to place). 
        
        destination place: node.place_name
        multiset:          self.compile(node.token_expr)
        marking:           node.marking_var
        """
        raise NotImplementedError

    def compile_TupleOut(self, node):
        """ returns an AST that adds a tuple to a place. 
        
        build tuple based on node.tuple_info

        place:   node.place_name
        marking: node.marking_var        
        """
        raise NotImplementedError

    def compile_NotEmpty(self, node):
        """ returns an AST that checks if place 'node.place_name' of marking 'node.marking_var' is empty. """
        raise NotImplementedError

    def compile_TokenEnumeration(self, node):
        """ returns an AST that enumerates all tokens of place.

        place:   'node.place_name'
        marking: 'node.marking_var'
        body:    'self.compile(node.body)' 
        """
        raise NotImplementedError

    def compile_MultiTokenEnumeration(self, node):
        """ returns an AST that enumerates multiple tokens of place 'node.place_name' of marking 'node.marking_var', and for each of them executes 'self.compile(node.body)' 

        This is for example when you want to get all couples (x, y, ...) such that (x, y, ...) are in P, so this means to
        1. nest multiple TokenEnumeration
        2. check that x, y, ... have different indices.

        multiarc: 'node.multiarc' 
                   use sub_arc.data['local_variable'] for value variable and sub_arc.data['index'] for index variable.
        place:    'node.place_name'
        marking:  'node.marking_var'
        body:     'self.compile(node.body)' 
                
        """
        raise NotImplementedError

    def compile_GuardCheck(self, node):
        """ returns an AST that checks if guard 'node.condition' is true, then executes 'self.compile(node.body)'. """
        raise NotImplementedError

    def compile_PyExpr(self, node):
        """ Pythonic feature.
        
        AST of a Python expression. """
        raise NotImplementedError

    def compile_Name(self, node):
        """ AST of a name, (Not sure this is still used.) """
        raise NotImplementedError

    def compile_FunctionCall(self, node):
        """ AST of a function call ('node.function_name') with arguments '[ self.compile(arg) for arg in node.arguments ]' """
        raise NotImplementedError

    def compile_ProcedureCall(self, node):
        """ AST of a procedure call ('node.function_name') with arguments '[ self.compile(arg) for arg in node.arguments ]' """
        raise NotImplementedError

    def compile_MarkingCopy(self, node):
        """ AST of a copy of marking 'node.src' that will be stored in 'node.dst'. """
        raise NotImplementedError

    def compile_AddMarking(self, node):
        """ AST that adds marking 'node.marking_var' to marking set 'node.marking_set_var'. """
        raise NotImplementedError

    def compile_AddToken(self, node):
        """ AST that adds a token 'self.compile(node.token_expr)' to place 'node.place_name'. """
        raise NotImplementedError

    def compile_RemToken(self, node):
        """ AST that removes a token 'self.compile(node.token_expr)' from place 'node.place_name'. """
        raise NotImplementedError

    def compile_RemTuple(self, node):
        """ AST that removes a tuple  'self.compile(node.tuple_expr)' from place 'node.place_name'. """
        raise NotImplementedError

    def compile_Token(self, node):
        """ AST that corresponds to token 'node.value' that will be stored in a place of the same type as place 'node.place_name'. """
        raise NotImplementedError

    def compile_SuccT(self, node):
        """ AST of the transition specific firing function. 

        function name : node.function_name

        arguments :     node.arg_marking_var,     # current marking
                        node.arg_marking_acc_var, # marking set
                        node.arg_ctx_var          # context

        body;           self.compile(node.body)
        """
        raise NotImplementedError

    def compile_SuccP(self, node):
        """ Pids specific. """
        raise NotImplementedError

    def compile_Succs(self, node):
        """ AST of the main successor function.

        This function should create a marking set and store it in
        variable 'node.arg_marking_acc_var' and return it after the
        execution of the body.
        
        function name: node.function_name
        arguments: node.arg_marking_var, # 
                   node.arg_ctx_var
        returns; a set of markings                         
        """
        raise NotImplementedError

    def compile_Init(self, node):
        """ AST of initial marking function.

        this function should create a marking and store it in variable
        'node.marking_var.name', execute the body, and finally return
        this marking.

        function name: node.function_name
        returns: initial marking
        """
        raise NotImplementedError

    ################################################################################
    # Flow elimination
    ################################################################################

    def compile_FlowCheck(self, node):
        """ flow specific """
        raise NotImplementedError

    def compile_ReadFlow(self, node):
        """ flow specific """
        raise NotImplementedError

    def compile_UpdateFlow(self, node):
        """ flow specific """
        raise NotImplementedError

    ################################################################################
    # Marking normalization
    ################################################################################

    def compile_InitGeneratorPlace(self, node):
        """ Pid specific """
        raise NotImplementedError

    def compile_NormalizeMarking(self, node):
        """ Pid specific """
        raise NotImplementedError

    def compile_AddPid(self, node):
        """ Pid specific """
        raise NotImplementedError

    def compile_InitialPid(self, node):
        """ Pid specific """
        raise NotImplementedError

    def compile_UpdateHashSet(self, node):
        """ Pid specific """
        raise NotImplementedError

################################################################################
# EOF
################################################################################
