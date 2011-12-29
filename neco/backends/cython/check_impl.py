import ast, sys
import cyast, netir, nettypes
from pprint import pprint
from neco.utils import Matcher, flatten_ast, IDProvider
from neco.core.info import VariableProvider, TypeInfo
from nettypes import type2str, register_cython_type
from cyast import Builder, E, Unparser, to_ast

################################################################################
#
################################################################################
class CheckerEnv(nettypes.Env):

    def __init__(self, word_set, marking_type):
        nettypes.Env.__init__(self, word_set, marking_type, None)

        self.id_provider = IDProvider()
        self.check_functions = {}

    def get_check_function(self, name):
        """
        @raise KeyError: if check function does not exist.
        """
        return self.check_functions[name]

    def register_check_function(self, name, function):
        self.check_functions[name] = function

    def functions(self):
        for fun in self.check_functions.itervalues():
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
                                       body = [ inner_body ])

    # main_body.append( cyast.Assign(targets=[cyast.Name(check_var.name)], value=cyast.Num(0)) )
    main_body.append( node )
    main_body.append( cyast.Return(value=cyast.Num(0)) )

    for stmt in main_body:
        builder.emit(stmt)

    builder.end_FunctionDef()
    return FunctionWrapper(function_name, cyast.to_ast(builder))


################################################################################
#
################################################################################
def gen_check_function(checker_env, id, prop):

    marking_type = checker_env.marking_type
    register_cython_type(marking_type.type, 'net.Marking')
    TypeInfo.register_type('Marking')

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


    ### begin matcher
    class matcher(Matcher):
        def case_InPlace(_, node):
            place_name = node.place.place


            calls = []
            for token_expr in node.data:
                function_name = "check_in_{}".format(checker_env.id_provider.get(place_name))

                # builder.emit( E( "print >> sys.stderr, 'checking if " + ast.dump(token_expr) + " is in " + place_name + "'" ) )

                try:
                    function = checker_env.get_check_function(function_name)
                    calls.append( function.call(args=[cyast.Name(marking_var.name),
                                                      token_expr]) )
                except KeyError:
                    function = gen_InPlace_function(checker_env, function_name, place_name)
                    checker_env.register_check_function(function_name, function)
                    calls.append( function.call(args=[cyast.Name(marking_var.name),
                                                      token_expr]) )

            builder.emit_Return(cyast.Compare(left = [cyast.Num(1)],
                                             ops = [cyast.Eq()] * len(calls),
                                             comparators = calls))
    ### end matcher
    matcher().match(prop)

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


from Cython.Distutils import build_ext
from distutils.core import setup
from distutils.extension import Extension

def produce_and_compile_pyx(checker_env, id_prop_map):
    functions = []
    for id, prop in id_prop_map.iteritems():
        gen_check_function(checker_env, id, prop) # updates env

    gen_main_check_function(checker_env, id_prop_map) # updates env

    checker_module = cyast.Module(body=functions)
    f = open("checker.pyx", "w")

    f.write("cimport net\n")
    f.write("cimport ctypes_ext\n")
    f.write("import sys\n")

    for function_ast in checker_env.functions():
        Unparser(function_ast, f)

    f.close()

    setup(name="checker.pyx",
          cmdclass={'build_ext': build_ext},
          ext_modules=[Extension("checker", ["checker.pyx"],
                                 include_dirs = ['../common'],
                                 extra_compile_args=[], # '-ggdb'],
                                 extra_link_args=['-lctypes'],
                                 library_dirs = ['../common'])],
          script_args=["build_ext", "--inplace"])

