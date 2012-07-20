""" Helpers for Python based languages. """

import neco.core.netir as coreir
import ast
from neco.utils import flatten_lists

class _extractor(ast.NodeTransformer):
    """ Helper class for extracting expressions from abstract syntax trees
    """
    def visit_Expr(self, node):
        return node.value

    def visit_Module(self, node):
        n = node.body[0]
        if isinstance(n, ast.Expr):
            return n.value
        else:
            return n

def extract_python_expr(ast_base, expr):
    """ Function that produces an abstract syntax representation from an expression.

    @param expr: expression
    @type expr: C{str}
    @return: abstract syntax tree
    """
    if isinstance(expr, int) or isinstance(expr, long):
        expr = str(expr)

    if isinstance(expr, ast.expr) or isinstance(expr, ast_base):
        return expr

    assert isinstance(expr, str)
    mod = compile(expr, "<string>", "exec", ast.PyCF_ONLY_AST)
    return _extractor().visit(mod)


def check_attr(obj, attr, value):
    """ Helper function that checks if an attribute exists, if not
    fills it with provided value.

    @param attr: attribute to be checked
    @param value: default value to be used.
    """
    try:    getattr(obj, attr)
    except: setattr(obj, attr, value)

def check_arg(d, arg, value):
    """ Helper function that checks if a keyword argument exists, if not
    fills it with provided value.

    @param arg: argument to be checked.
    @param value: default value to be used.
    """
    if not d.has_key(arg):
        d[arg] = value

def check_attrs(node, **kwargs):
    """ Helper function that checks if attributes exist, if not they are
    filled with provided values.

    This function calls C{check_attr} for each keyword argument.
    """
    for (arg, value) in kwargs.iteritems():
        check_attr(node, arg, value)
    return node

def check_attr_decorator(**decorator_kwargs):
    """ Check attr decorator.

    \see C{_check_attr}.

    @param decorator_kwargs: keyword arguments used as a dict (name : default value).
    """
    def wrap(function):
        if getattr(function, '_decotrated_with_check_attr_decorator', False):
            return function

        def fun(cls, *args, **kwargs):
            node = function(cls, *args, **kwargs)
            for (arg, value) in decorator_kwargs.iteritems():
                check_attr(node, arg, value)
            return node
        function._decotrated_with_check_attr_decorator = True
        return fun
    return wrap

################################################################################
# EOF
################################################################################

