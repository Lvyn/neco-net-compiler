import sys, StringIO, pickle
import cyast, netir, nettypes
from neco.utils import flatten_ast, IDProvider
from neco.core.info import VariableProvider, TypeInfo
from nettypes import type2str, register_cython_type
from cyast import Builder, E, Unparser, to_ast
from neco import config
import neco.core as core
import neco.core.info as info
from snakes.nets import WordSet, dot
from neco.utils import flatten_lists
from collections import defaultdict

def operator_to_cyast(operator):
    if   operator.isLT():
        return cyast.Lt()
    elif operator.isLE():
        return cyast.LtE()
    elif operator.isEQ():
        return cyast.Eq()
    elif operator.isNE(): 
        return cyast.NotEq()
    elif operator.isGT(): 
        return cyast.Gt()
    elif operator.isGE():
        return cyast.GtE()
    else:
        raise NotImplementedError(operator.__class__)

################################################################################
#
################################################################################
class CheckerEnv(nettypes.Env):

    def __init__(self, word_set, net_info, marking_type):
        nettypes.Env.__init__(self, word_set, marking_type, None)
        self.net_info = net_info
        self.id_provider = IDProvider()
        self.check_functions = {}
        
        self.transition_id_provider = IDProvider()
        self._is_fireable_functions = {}

    def get_check_function(self, name):
        """
        @raise KeyError: if check function does not exist.
        """
        return self.check_functions[name]
    
    def place_card_expression(self, marking_var, place_name):
        place_type = self.marking_type.get_place_type_by_name(place_name)
        return place_type.card_expr(self, marking_var)
        
    def register_check_function(self, name, function):
        self.check_functions[name] = function
        
    def is_fireable_expression(self, marking_var, transition_name):
        try:
            function = self._is_fireable_functions[transition_name]            
        except KeyError:
            # function does not exist
            transition = self.net_info.transition_by_name(transition_name)
            transition_id = self.transition_id_provider.get(transition)
            function_name = "isfireable_t{}".format(transition_id)
            
            generator = IsFireableGenerator(self, transition, function_name)
            function_ir = generator()
            
            visitor = CheckerCompileVisitor(self)
            function_ast = visitor.compile( function_ir )        

            function = FunctionWrapper(function_name, function_ast)
            self._is_fireable_functions[transition_name] = function

        return function.call( [ cyast.Name(marking_var.name) ] )

    def gen_multiset_card_expression(self, marking_var, multiset):
        
        if multiset.isPlaceMarking():
            mrk_type = self.marking_type
            mrk_type.get_place_type_by_name()

    def functions(self):
        for fun in self.check_functions.itervalues():
            yield fun.ast()

    def is_fireable_functions(self):
        for fun in self._is_fireable_functions.itervalues():
            yield fun.ast()
            
class FunctionWrapper(object):
    """
    """

    def __init__(self, function_name, function_ast):
        """ Initialize the wrapper.

        @param function_name:
        @type function_name: C{str}
        @param function_ast:
        @type function_ast: C{AST}
        """
        self._function_name = function_name
        self._function_ast  = function_ast

    def ast(self):
        return self._function_ast

    def call(self, args):
        self._function_name
        return cyast.Call(func = cyast.Name(self._function_name),
                          args = args)


################################################################################
#
################################################################################
def gen_InPlace_function(checker_env, function_name, place_name):
    marking_type = checker_env.marking_type
    variable_provider = VariableProvider()

    checker_env.push_cvar_env()
    checker_env.push_variable_provider(variable_provider)

    builder = cyast.Builder()
    marking_var = variable_provider.new_variable(type=marking_type.type)

    place_type = marking_type.get_place_type_by_name(place_name)
    token_var = variable_provider.new_variable(type=place_type.token_type)
    #check_var = variable_provider.new_variable(type=TypeInfo.Int)

    builder.begin_FunctionCDef(name = function_name,
                               args = (cyast.A(marking_var.name,
                                               type=type2str(marking_var.type))
                                       .param(name=token_var.name,
                                              type=type2str(token_var.type))),
                               returns = cyast.Name("int"),
                               decl = [],
                               public=False, api=False)

    main_body = []

    loop_var = variable_provider.new_variable(type=place_type.token_type)
    inner_body = cyast.If(cyast.Compare(cyast.Name(token_var.name),
                                        [cyast.Eq()],
                                        [cyast.Name(loop_var.name)]),
                          [ cyast.Return( cyast.Num(1) ) ])
    node = place_type.enumerate_tokens(checker_env,
                                       loop_var,
                                       marking_var,
                                       body=inner_body)

    main_body.append( node )
    main_body.append( cyast.Return(value=cyast.Num(0)) )

    for stmt in main_body:
        builder.emit(stmt)

    builder.end_FunctionDef()
    return FunctionWrapper(function_name, cyast.to_ast(builder))


class IsFireableGenerator(core.SuccTGenerator):
    
    def __init__(self, checker_env, transition, function_name):
        
        # DO NOT CALL BASE CLASS __init__ !
        
        self.net_info = checker_env.net_info
        self.builder = core.netir.Builder()
        self.transition = transition
        self.function_name = function_name
        self.marking_type = checker_env.marking_type
        self.ignore_flow = config.get('optimize_flow')
        self.env = checker_env

        # this helper will create new variables and take care of shared instances
        helper = info.SharedVariableHelper( transition.shared_input_variables(),
                                            WordSet(transition.variables().keys()) )
        self.variable_helper = helper

        if config.get('optimize'):
            self.transition.order_inputs()

        # function arguments
        self.arg_marking_var = helper.new_variable(type = self.marking_type.type)

        # create function
        self.builder.begin_function_IsFireable( function_name     = self.function_name,
                                                arg_marking_var   = self.arg_marking_var,
                                                transition_info   = self.transition,
                                                variable_provider = helper )
        
    def __call__(self):
        trans = self.transition
        builder = self.builder
        
        self.gen_enumerators()
        
        guard = info.ExpressionInfo(trans.trans.guard._str)
        try:
            if eval(guard.raw) != True:
                builder.begin_GuardCheck( condition = core.netir.PyExpr(guard) )
        except:
            builder.begin_GuardCheck( condition = core.netir.PyExpr(guard) )
        
        # guard valid
        success = info.ExpressionInfo("True")
        failure = info.ExpressionInfo("False")
        
        builder.emit_Return(core.netir.PyExpr(success))
        builder.end_all_blocks()
        
        builder.emit_Return(core.netir.PyExpr(failure))
        builder.end_function()
        return builder.ast()    

def build_multiset(elements):
    def zero(): return 0
    l = defaultdict(zero)
    for e in elements:
            l[eval(e)] += 1
    
    return E("ctypes_ext.MultiSet({!r})".format(dict(l)))
    
def multiset_expr_from_place_name(checker_env, marking_var, place_name):        
    place_type  = checker_env.marking_type.get_place_type_by_name(place_name)
    multiset = place_type.multiset_expr(checker_env, marking_var)
    if place_type.type != TypeInfo.MultiSet:
        print >> sys.stderr, "[W] using multiset fallback for {}, this may result in slow execution times".format(place_name)
    return multiset
    
def gen_multiset_comparison(checker_env, marking_var, cython_op, left, right):
    
    if left.isPlaceMarking():
        left_multiset = multiset_expr_from_place_name(checker_env, marking_var, left.place_name) 
        
    elif left.isMultisetConstant():
        left_multiset = build_multiset(left.elements)

    elif left.isMultisetPythonExpression():
        left_multiset = E(left.expr)
                
    else:
        raise NotImplementedError
        
    if right.isPlaceMarking():    
        right_multiset = multiset_expr_from_place_name(checker_env, marking_var, right.place_name)
        
    elif right.isMultisetConstant():
        right_multiset = build_multiset(right.elements)
        
    elif right.isMultisetPythonExpression():
        right_multiset = E(right.expr)
                
    else:
        raise NotImplementedError
    
    return cyast.Compare(left=left_multiset,
                         ops=[cython_op],
                         comparators=[right_multiset] )
        
def gen_check_expression(checker_env, marking_var, formula):
    if formula.isIntegerComparison():
        operator = operator_to_cyast(formula.operator)
        left = gen_check_expression( checker_env, marking_var, formula.left )
        right = gen_check_expression( checker_env, marking_var, formula.right )
        return cyast.Compare(left=left,
                             ops=[operator],
                             comparators=[right] )
        
    elif formula.isMultisetComparison():
        operator = operator_to_cyast(formula.operator)
        return gen_multiset_comparison(checker_env, marking_var, operator, formula.left, formula.right)
        
    elif formula.isIntegerConstant():
        return cyast.Num(int(formula.value))
        
    elif formula.isMultisetCardinality():
        multiset = formula.multiset
        if multiset.isPlaceMarking():
            return checker_env.place_card_expression(marking_var, multiset.place_name)
        else:
            raise NotImplementedError
    
    elif formula.isSum():
        operands = formula.operands            
        head = operands[0]
        tail = operands[1:]
        
        left  = gen_check_expression(checker_env, marking_var, head)
        if len(tail) > 1:
            right = gen_check_expression(checker_env, marking_var, Sum(tail))
        else:
            right = gen_check_expression(checker_env, marking_var, tail[0])
        
        
        return cyast.BinOp(left = left,
                           op = cyast.Add(),
                           right = right)
    
    elif formula.isDeadlock():
        pass # nothing to do just add option -d DEAD to neco-spot
    
    elif formula.isFireable():
        return checker_env.is_fireable_expression(marking_var,                                                  
                                                  formula.transition_name)

    elif formula.isMultisetCard():
        return checker_env.gen_multiset_card_expression(marking_var,
                                                        formula.multiset)
    
    else:
        print >> sys.stderr, "Unknown atomic proposition {!s}".format(formula)
        raise NotImplementedError

################################################################################
#
################################################################################
def gen_check_function(checker_env, id, atom):

    marking_type = checker_env.marking_type
    
    variable_provider = VariableProvider()
    checker_env.push_cvar_env()
    checker_env.push_variable_provider(variable_provider)

    builder = cyast.Builder()
    marking_var = variable_provider.new_variable(type=marking_type.type)

    function_name = "check_{}".format(id)
    builder.begin_FunctionCDef(name = function_name,
                               args = cyast.A(marking_var.name, type=type2str(marking_var.type)),
                               returns = cyast.Name("int"),
                               decl = [],
                               public=False, api=False)

    formula = atom.formula
    builder.emit( cyast.Return( gen_check_expression(checker_env,
                                                     marking_var,
                                                     formula) ) )

    builder.end_FunctionDef()
    tree = cyast.to_ast(builder)
    tree = flatten_ast(tree)

    checker_env.register_check_function(function_name, FunctionWrapper(function_name, tree))
    return tree

def gen_main_check_function(checker_env, id_prop_map):

    function_name = "neco_check"
    builder = cyast.Builder()
    variable_provider = VariableProvider()

    checker_env.push_cvar_env()
    checker_env.push_variable_provider(variable_provider)

    marking_var = variable_provider.new_variable(type=checker_env.marking_type.type)
    atom_var    = variable_provider.new_variable(type=TypeInfo.Int)

    builder.begin_FunctionCDef(name = function_name,
                               args = (cyast.A(marking_var.name, type=type2str(marking_var.type))
                                       .param(atom_var.name, type=type2str(TypeInfo.Int))),
                               returns = cyast.Name("int"),
                               decl = [],
                               public=True, api=True)

    for (i, (ident, prop)) in enumerate(id_prop_map.iteritems()):
        if i == 0:
            builder.begin_If( test = cyast.Compare( left = cyast.Name(atom_var.name),
                                                    ops = [ cyast.Eq() ],
                                                    comparators = [ cyast.Num(ident) ] ) )
        else:
            builder.begin_Elif( test = cyast.Compare( left = cyast.Name(atom_var.name),
                                                    ops = [ cyast.Eq() ],
                                                    comparators = [ cyast.Num(ident) ] ) )

        builder.emit_Return(checker_env.get_check_function("check_{}".format(ident)).call([cyast.Name(marking_var.name)]))

    for _ in id_prop_map:
        builder.end_If()

    builder.emit(cyast.Print(dest=E('sys.stderr'),
                             values=[cyast.Str(s='!W! invalid proposition identifier'),
                                     cyast.Name(atom_var.name)],
                             nl=True))
    builder.emit_Return(cyast.Num(n=0))

    builder.end_FunctionDef()
    tree = to_ast(builder)
    checker_env.register_check_function(function_name, FunctionWrapper(function_name, tree))
    return tree


class CheckerCompileVisitor(netir.CompilerVisitor):
    
    def __init__(self, env):
        netir.CompilerVisitor.__init__(self, env)
    
    def compile_IsFireable(self, node):
        self.env.push_cvar_env()
        self.env.push_variable_provider(node.variable_provider)

        self.var_helper = node.transition_info.variable_helper

        stmts = [ self.compile( node.body ) ]

        decl = netir.CVarSet()
        inputs = node.transition_info.inputs
        for input in inputs:
            decl.extend(self.try_gen_type_decl(input))

        inter_vars = node.transition_info.intermediary_variables
        for var in inter_vars:
            if (not var.type.is_UserType) or netir.is_cython_type( var.type ):
                decl.add(cyast.CVar(name=var.name,
                                    type=type2str(var.type))
        )

        additionnal_decls = self.env.pop_cvar_env()
        for var in additionnal_decls:
            decl.add(var)

        result = to_ast( Builder.FunctionDef(name = node.function_name,
                                             args = (netir.A(node.arg_marking_var.name, type = type2str(node.arg_marking_var.type))),
                                             body = stmts,
                                             lang = cyast.CDef( public = False ),
                                             returns = cyast.Name("int"),
                                             decl = decl) )
        return result

from Cython.Distutils import build_ext
from distutils.core import setup
from distutils.extension import Extension
import os

def produce_and_compile_pyx(checker_env, id_prop_map):
    marking_type = checker_env.marking_type
    register_cython_type(marking_type.type, 'net.Marking')
    TypeInfo.register_type('Marking')

    functions = []
    for id, prop in id_prop_map.iteritems():
        gen_check_function(checker_env, id, prop) # updates env

    gen_main_check_function(checker_env, id_prop_map) # updates env

    checker_module = cyast.Module(body=functions)
    
    base_dir = "build/"
    try:
        os.mkdir(base_dir)
    except OSError:
        pass
    
    f = open(base_dir + "checker.pyx", "w")

    f.write("cimport net\n")
    f.write("cimport ctypes_ext\n")
    f.write("import sys, StringIO\n")
    f.write("import cPickle as pickle\n")
    f.write("from snakes.nets import *\n")
    
    for function_ast in checker_env.is_fireable_functions():
        Unparser(function_ast, f)
    for function_ast in checker_env.functions():
        Unparser(function_ast, f)
    f.close()

    includes = config.get('additional_search_paths')
    include_dirs = includes
    library_dirs = includes

    include_dirs.append('.')
    library_dirs.append('.')

    setup(name=base_dir + "checker.pyx",
          cmdclass={'build_ext': build_ext},
          ext_modules=[Extension("checker", [base_dir + "checker.pyx"],
                                 include_dirs = include_dirs + [base_dir],
                                 extra_compile_args = [],
                                 extra_link_args = ['-lctypes'],
                                 library_dirs = library_dirs + [base_dir])],
          script_args=["build_ext", "--inplace"],
          options = { 'build': { 'build_base': 'build' } })

