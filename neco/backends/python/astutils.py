""" Python abstract syntax tree helpers.
"""
import ast, sys
import neco.core.netir as coreir
from neco.backends.pythonic import *

################################################################################

class _module_extractor(ast.NodeTransformer):
    """ Helper class for extracting modules from abstract syntax trees
    """
    def visit_Module(self, node):
        return self.visit(node.body[0])


################################################################################

class _expr_extractor(_module_extractor):
    """ Helper class for extracting expressions from abstract syntax trees
    """
    def visit_Expr(self, node):
        return node.value


################################################################################

def extract_expr(node):
    return extract_python_expr(ast.AST, node)

def _extract_expr(node):
    return extract_python_expr(ast.AST, node)

class _to_ast_transformer(ast.NodeTransformer):
    def visit(self, node):
        if hasattr(node, '__ast__'):
            node = to_ast(node)
        elif hasattr(node, 'body'):
            node.body = to_ast(node.body)
        return self.generic_visit(node)

def to_ast(node):
    """ Transform a builder or a builder helper into a cython ast.
    """
    if hasattr(node, '__ast__'):
        return node.__ast__()
    elif isinstance(node, list):
        return [ to_ast(n) for n in node ]
    elif isinstance(node, tuple):
        return tuple([ to_ast(n) for n in node ])
    elif isinstance(node, ast.AST):
        return _to_ast_transformer().visit(node)
    else:
        return node

def stmt(node):
    """ Transform a builder or a builder helper into a cython statement (ast).
    """
    if hasattr(node, '__ast__'):
        node = to_ast( node )
    return ast.Expr( node )

def args_to_ast( d, keys ):
    for key in keys:
        if d.has_key(key):
            d[key] = to_ast(d[key])
    return d

################################################################################

def E(arg):
    """ Extraction helper.

    Extracts an ast from an expression or a statement.

    @param arg: object to extract from.
    @return: builder helper.
    @rtype: C{Builder.helper}
    """
    if isinstance(arg, Builder.helper):
        return arg
    return Builder.Helper(arg)


def A(param = None):
    """ Argument construction helper.

    @param param: optional first argument.
    @return: argument helper object used to build function arguments.
    @rtype: C{Builder.arguments_helper}.
    """
    args = Builder.Arguments()
    if param != None:
        return args.param(param)
    return args


################################################################################

def E(arg):
    """ Extraction helper.

    Extracts an ast from an expression or a statement.

    @param arg: object to extract from.
    @return: builder helper.
    @rtype: C{Builder.helper}
    """
    if isinstance(arg, Builder.helper):
        return arg
    return Builder.Helper(arg)

################################################################################

def _aug_assign(operator):
    def fun(self, value):
        self.node = ast.AugAssign(target = to_ast(self.node),
                                  op     = operator,
                                  value  = to_ast(value));
        return self
    return fun

def _bin_op(operator):
    def fun(self, right):
        right = to_ast(right)
        self.node = ast.BinOp(left  = to_ast(self.node),
                              op    = operator,
                              right = to_ast(right))
        return self
    return fun

def _compare2(op):
    def fun(self, other):
        self.node = ast.Compare(left  = to_ast(self.node),
                                ops   = [ op ],
                                comparators = [ to_ast(other) ])
        return self
    return fun

class Builder(coreir.BuilderBase):

    class helper(object):
        def __init__(self, node):
            self.node = node

        def __ast__(self):
            return self.node

        @property
        def body(self):
            return E( self.node.body )

        @body.setter
        def body(self, e):
            self.node.body = to_ast(e)

        def call(self, args = []):
            self.node = ast.Call( func = to_ast(self.node),
                                  args = to_ast(args),
                                  keywords = [],
                                  starargs = None,
                                  kwargs = None )
            return self

        def args(self, args):
            self.node.args = to_ast(args)
            return self

        def subscript(self, index=None):
            self.node = ast.Subscript(value = to_ast(self.node), slice = ast.Index(to_ast(E(index))))
            return self

        def attr(self, attribute):
            assert( isinstance(attribute, str) )
            self.node = ast.Attribute(value = to_ast(self.node), attr = attribute)
            return self

        def assign(self, value):
            self.node = ast.Assign(targets = [ to_ast(self.node) ], value = to_ast(E(value)));
            return self

        def init(self, value):
            self.node.init = to_ast(value)
            return self

        sub_assign = _aug_assign(ast.Sub())
        add_assign = _aug_assign(ast.Add())
        xor_assign = _aug_assign(ast.BitXor())
        or_assign  = _aug_assign(ast.BitOr())
        mult    = _bin_op(ast.Mult())
        add     = _bin_op(ast.Add())
        bit_and = _bin_op(ast.BitAnd())
        bit_or  = _bin_op(ast.BitOr())
        bit_xor = _bin_op(ast.BitXor())
        xor = bit_xor

        NotEq = _compare2(ast.NotEq())
        Eq = _compare2(ast.Eq())
        Gt = _compare2(ast.Gt())
        Lt = _compare2(ast.Lt())

    def __init__(self):
        coreir.BuilderBase.__init__(self)

    @classmethod
    def Helper(cls, expr):
        return cls.helper(_extract_expr(expr))

    @classmethod
    def FunctionDef(cls, *args, **kwargs):
        args_to_ast(kwargs, ast.FunctionDef._fields)
        check_arg(kwargs, "args", ast.arguments( args = [], vararg = None, kwargs = None, defaults = [] ))
        return check_attrs(ast.FunctionDef( *(to_ast(args)), **kwargs ), body = [], decorator_list = [])

    @classmethod
    def If(self, *args, **kwargs):
        args_to_ast(kwargs, ast.If._fields)
        return check_attrs(ast.If( *(to_ast(args)), **kwargs ), body = [], orelse = [])

    def begin_FunctionDef(self, *args, **kwargs):
        node = self.FunctionDef(*args, **kwargs)
        self.begin_base_block(node)

    def begin_If(self, *args, **kwargs):
        self.begin_block(self.If(*args, **kwargs))

    def end_If(self):
        assert( isinstance(self._current, ast.If) )
        self.end_block()

    def end_FunctionDef(self):
        assert( isinstance(self._current, ast.FunctionDef) )
        self.end_base_block()

    def emit(self, e):
        super(Builder, self).emit(to_ast(e))

    def emit_Return(self, value):
        self.emit( ast.Return( to_ast(E(value)) ) )

    def emit_DebugMessage(self, msg):
        self.emit( ast.DebugMessage( message = msg) )


    class arguments_helper(object):
        def __init__(self):
            self.node = ast.arguments(args = [], vararg = None, kwargs = None, defaults = [])

        def param(self, name, default = None):
            self.node.args.append( to_ast(E(name)) )
            if default != None:
                self.node.defaults.append( to_ast(E(default)) )
            return self

        def __ast__(self):
            return self.node

    @classmethod
    def Arguments(cls):
        return cls.arguments_helper()

    class class_def_helper(object):
        def __init__(self, name, bases, body = []):
            self.node = ast.ClassDef(name  = to_ast(name),
                                     bases = to_ast(bases),
                                     body = to_ast(body))

        def add_method(self, method):
            self.node.body.append(to_ast(method))

        def add_decl(self, decl):
            self.node.decl.append(to_ast(decl))

        def __ast__(self):
            return self.node

    @classmethod
    def ClassDef(cls, name, bases = [], body = []):
        return cls.class_def_helper(name, bases, body)

    @classmethod
    def For(cls, *args, **kwargs):
        args_to_ast(kwargs, ast.For._fields)
        return check_attrs(ast.For(*args, **kwargs), body = [], or_else = [])

    @classmethod
    def Compare(self, left, ops, comparators):
        return E( ast.Compare(left = to_ast(left), ops = to_ast(ops), comparators = to_ast(comparators)) )

    @classmethod
    def Eq(self):
        return ast.Eq()


    @classmethod
    def Not(self, node):
        return ast.UnaryOp(op = ast.Not(), operand = to_ast(node))

    @classmethod
    def Tuple(self, elts):
        return E( ast.Tuple( elts = to_ast(elts) ) )

    def __ast__(self):
        return super(Builder, self).ast()



############################################################################


#f = open('code.py', 'w')
# _write = f.write
# self._write = sys.stdout.write
class AstPrettyPrinter(ast.NodeVisitor):
    """ Abstract syntax tree preety printer.
    """

    def __init__(self, print_ctx = False, file = None):
        self._write = sys.stdout.write if not file else file.write
        self.indent = 0;
        self.print_ctx = print_ctx
        ast.NodeVisitor.__init__(self)

    # def visit(self, node):
    #     print "visiting {cls}".format(cls=node.__class__.__name__)
    #     super(AstPrettyPrinter, self).visit(node)

    def incr_indent(self):
        self.indent += 1

    def decr_indent(self):
        self.indent -= 1

    def _write_spaces(self):
        self._write('\n' + ('    ' * self.indent))

    def visit_ListComp(self, node):
        self._write('[')
        self.visit(node.elt)
        for gen in node.generators:
            self._write(' ')
            self.visit(gen)
        self._write(']')

    def visit_comprehension(self, node):
        self._write('for ')
        self.visit(node.target)
        self._write(' in ')
        self.visit(node.iter)

        for _if in node.ifs:
            self._write(' if ')
            self.visit(_if)
        self._write('')

    def visit_Tuple(self, node):
        self._write('(')
        for i, e in enumerate(node.elts):
            if i > 0:
                self._write(', ')
            self.visit(e)
        self._write(')')

    def visit_List(self, node):
        self._write('[')
        for i, e in enumerate(node.elts):
            if i > 0:
                self._write(', ')
            self.visit(e)
        self._write(']')

    def visit_alias(self, node):
        self._write(node.name)
        if node.asname:
            self._write(" as ")
            self._write(node.asname)

    def visit_ImportFrom(self, node):
        self._write("\nfrom ")
        self._write(node.module)
        self._write(" import ")
        for i,name in enumerate(node.names):
            if i > 0:
                self._write(", ")
            self.visit(name)

    def visit_Import(self, node):
        self._write("\nimport ")
        for i, name in enumerate(node.names):
            if i > 0:
                self._write(", ")
            self.visit(name)

    def visit_Assign(self, node):
        for i,target in enumerate(node.targets):
            if i > 0:
                self._write(", ")
            self.visit(target)
        self._write(" = ")
        self.visit(node.value)

    def do_visit_body(self, nodes):
        self.incr_indent()
        for stmt in nodes:
            self._write_spaces()
            self.visit(stmt)
        self.decr_indent()

    def visit_Print(self, node):
        self._write("print ")
        for i, e in enumerate(node.values):
            if (i > 0):
                self._write(', ')
            self.visit(e)

    def visit_Sub(self, node):
        self._write("-")

    def visit_And(self, node):
        self._write(" and ")

    def visit_Add(self, node):
        self._write("+")

    def visit_BitXor(self, node):
        self._write("^")

    def visit_NotEq(self, node):
        self._write("!=")

    def visit_Gt(self, node):
        self._write(">")

    def visit_Lt(self, node):
        self._write("<")

    def visit_Eq(self, node):
        self._write("==")

    def visit_Str(self, node):
        self._write(repr(node.s))

    def visit_Pass(self, node):
        self._write_spaces()
        self._write("pass")

    def visit_BoolOp(self, node):
        for i,v in enumerate(node.values):
            if i > 0:
                self.visit(node.op)
            self._write('(')
            self.visit(v)
            self._write(')')

    def visit_Not(self, node):
        self._write("not")

    def visit_UnaryOp(self, node):
        self.visit(node.op)
        self._write(" ")
        self.visit(node.operand)

    def visit_Compare(self, node):
        self.visit(node.left)
        for op, comp in zip(node.ops, node.comparators):
            self._write(" ")
            self.visit(op)
            self._write(" ")
            self.visit(comp)

    def visit_AugAssign(self, node):
        self.visit(node.target)
        self._write(" ")
        self.visit(node.op)
        self._write("= ")
        self.visit(node.value)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self._write("[")
        self.visit(node.slice)
        self._write("]")

    def visit_For(self, node):
        self._write("for ")
        self.visit(node.target)
        self._write(" in ")
        self.visit(node.iter)
        self._write(":")
        self.do_visit_body(node.body)

    def visit_Elif(self, node):

        self._write("elif ")
        self.visit(node.test)
        self._write(" :")
        self.do_visit_body(node.body)

        if any(node.orelse):
            self._write_spaces()
            if len(node.orelse) == 1:
                head = node.orelse[0]
                self.visit_Elif(head)
            else:
                self._write('else:')
                self.do_visit_body(node.orelse)

    def visit_If(self, node):
        self._write("if ")
        self.visit(node.test)
        self._write(" :")
        self.do_visit_body(node.body)

        if any(node.orelse):
            self._write_spaces()
            if len(node.orelse) == 1:
                head = node.orelse[0]
                self.visit_Elif(head)
            else:
                self._write('else:')
                self.do_visit_body(node.orelse)

    def visit_Module(self, module):
        nodes = module.body
        for node in nodes:
            self.visit(node)

    def visit_Call(self, node):
        self.visit(node.func)
        self._write("(")
        for i,arg in enumerate(node.args):
            if (i > 0):
                self._write(", ")
            self.visit(arg)
        self._write(")")

    def visit_Attribute(self, node):
        self.visit(node.value),
        self._write(".")
        self._write(node.attr)

    def visit_Return(self, ret):
        self._write("return ")
        self.visit(ret.value)

    def visit_Load(self, node):
        if self.print_ctx:
            self._write("!l!")

    def visit_Store(self, node):
        if self.print_ctx:
            self._write("!s!")

    def visit_Param(self, node):
        if self.print_ctx:
            self._write("!p!")

    def visit_Name(self, name):
        self._write(name.id)
        self.visit(name.ctx)

    def visit_Num(self, num):
        self._write(str(num.n))

    def visit_arguments(self, arguments):
        offset = len(arguments.args) - len(arguments.defaults)
        for i,arg in enumerate(arguments.args):
            if i > 0:
                self._write(', ')
            self.visit(arg)
            if i >= offset:
                self._write(' = ')
                self.visit(arguments.defaults[i-offset])

    def visit_ClassDef(self, node):
        self._write("\nclass ")
        self._write(node.name)
        self._write("(")
        for i, base in enumerate(node.bases):
            if i > 0:
                self._write(", ")
            self.visit(base)
        self._write("):")
        self.do_visit_body(node.body)
        self._write("\n")

    def visit_FunctionDef(self, fundef):
        self._write("def ")
        self._write(fundef.name)
        self._write("(")
        self.visit(fundef.args)
        self._write("):")
        self.do_visit_body(fundef.body)
        self._write("\n\n")

################################################################################
# EOF
################################################################################

