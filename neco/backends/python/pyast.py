""" Python AST and helper functions.

This module provides all contents from C{ast} module.

"""

import ast
from ast import *

import neco.core.netir as coreir
from neco.backends.pythonic import *

def Name(id):
    return ast.Name(id=id)

def Call(func, args=[], keywords=[], starargs=None, kwargs=None):
    return ast.Call(func, args, keywords, starargs, kwargs)

def FunctionDef(name,
                args=ast.arguments(args=[],
                                   vararg=None,
                                   kwarg=None,
                                   defaults=[]),
                body=[],
                decorator_list=[]):
    return ast.FunctionDef(name, args, body, decorator_list)

def arguments(args=[], vararg=None, kwarg=None, defaults=[]):
    return ast.arguments(args, vararg, kwarg, defaults)

def If(test, body=[], orelse=[]):
    return ast.If(test, body, orelse)

def Tuple(elts=[]):
    return ast.Tuple(elts=elts)

def ClassDef(name, bases=[], body=[], decorator_list=[]):
    return ast.ClassDef(name, bases, body, decorator_list)

def List(elts):
    return ast.List(elts=elts)


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

def stmt(node):
    """ Transform a builder or a builder helper into a cython statement (ast).
    """
    return ast.Expr( node )

################################################################################

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

def E(str_expr):
    """ Extraction helper.

    Extracts an ast from an expression or a statement.

    @param arg: object to extract from.
    @return: builder helper.
    @rtype: C{Builder.helper}
    """
    return _extract_expr(str_expr)

################################################################################

def _aug_assign(operator):
    def fun(self, value):
        self.node = ast.AugAssign(target = self.node,
                                  op     = operator,
                                  value  = value);
        return self
    return fun
def _bin_op(operator):
    def fun(self, right):
        right = right
        self.node = ast.BinOp(left  = self.node,
                              op    = operator,
                              right = right)
        return self
    return fun

def _compare2(op):
    def fun(self, other):
        self.node = ast.Compare(left  = self.node,
                                ops   = [ op ],
                                comparators = [ other ])
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
            self.node.body = e

        def call(self, args = []):
            self.node = ast.Call( func = self.node,
                                  args = args,
                                  keywords = [],
                                  starargs = None,
                                  kwargs = None )
            return self

        def args(self, args):
            self.node.args = args
            return self

        def subscript(self, index=None):
            self.node = ast.Subscript(value = self.node, slice = ast.Index(index))
            return self

        def attr(self, attribute):
            assert( isinstance(attribute, str) )
            self.node = ast.Attribute(value = self.node, attr = attribute)
            return self

        def assign(self, value):
            self.node = ast.Assign(targets = [ self.node ], value = E(value));
            return self

        def init(self, value):
            self.node.init = value
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
        #args_to_ast(kwargs, ast.FunctionDef._fields)
        check_arg(kwargs, "args", ast.arguments( args = [], vararg = None, kwargs = None, defaults = [] ))
        return check_attrs(ast.FunctionDef( *args, **kwargs ), body = [], decorator_list = [])

    @classmethod
    def If(self, *args, **kwargs):
        #args_to_ast(kwargs, ast.If._fields)
        return check_attrs(ast.If( *args, **kwargs ), body = [], orelse = [])

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
        super(Builder, self).emit(e)

    def emit_Return(self, value):
        self.emit( ast.Return( value ) )

    def emit_DebugMessage(self, msg):
        self.emit( ast.DebugMessage( message = msg) )


    class arguments_helper(object):
        def __init__(self):
            self.node = ast.arguments(args = [], vararg = None, kwarg = None, defaults = [])

        def param(self, name, default = None):
            self.node.args.append( ast.Name(id=name) )
            if default != None:
                self.node.defaults.append( E(default) )
            return self

        def ast(self):
            return self.node

        def __ast__(self):
            return self.node

    @classmethod
    def Arguments(cls):
        return cls.arguments_helper()

    class class_def_helper(object):
        def __init__(self, name, bases, body = []):
            self.node = ast.ClassDef(name  = name,
                                     bases = bases,
                                     body = body)

        def add_method(self, method):
            self.node.body.append(method)

        def add_decl(self, decl):
            self.node.decl.append(decl)

        def ast(self):
            return self.node

    @classmethod
    def ClassDef(cls, name, bases = [], body = []):
        return cls.class_def_helper(name, bases, body)

    @classmethod
    def For(cls, *args, **kwargs):
        #args_to_ast(kwargs, ast.For._fields)
        return check_attrs(ast.For(*args, **kwargs), body = [], or_else = [])

    @classmethod
    def Compare(self, left, ops, comparators):
        return E( ast.Compare(left = left, ops = ops, comparators = comparators) )

    @classmethod
    def Eq(self):
        return ast.Eq()


    @classmethod
    def Not(self, node):
        return ast.UnaryOp(op = ast.Not(), operand = node)

    @classmethod
    def Tuple(self, elts):
        return ast.Tuple(elts = elts)

    def __ast__(self):
        return super(Builder, self).ast()

################################################################################
# EOF
################################################################################
