""" Cython AST and helper functions.

This module provides all contents from C{cyast_gen}, which is automatically generated
from C{cyast.asdl}.

"""

import neco.core.netir as coreir
import cyast_gen
from cyast_gen import *
from neco.core.netir import CurrentBlockError


################################################################################
# Node wrappers.
################################################################################

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

def FunctionDecl(name,
                 args=ast.arguments(args=[],
                                    vararg=None,
                                    kwarg=None,
                                    defaults=[]),
                 returns = None,
                 **kwargs):
    return cyast_gen.FunctionDecl(name=name,
                                  args=args,
                                  returns=returns,
                                  decorator_list=[],
                                  **kwargs)

def arguments(args=[], vararg=None, kwarg=None, defaults=[]):
    return ast.arguments(args, vararg, kwarg, defaults)

def If(test, body=[], orelse=[]):
    return ast.If(test, body, orelse)

def Tuple(elts=[]):
    return ast.Tuple(elts=elts)

def ClassDef(name, bases=[], body=[], decorator_list=[]):
    return ast.ClassDef(name, bases, body, decorator_list)

def Index(value):
    return ast.Index(value=value)

def Subscript(value, slice, ctx=ast.Load()):
    return ast.Subscript(value=value, slice=slice)

def List(elts, ctx=ast.Store()):
    return ast.List(elts=elts, ctx=ctx)

################################################################################
from neco.backends.pythonic import *

class _to_ast_transformer(ast.NodeTransformer):
    def visit(self, node):
        if isinstance(node, Builder.helper):
            node = to_ast(node)
        return self.generic_visit(node)

def to_ast(node):
    """ Transform a builder or a builder helper into a cython ast.
    """
    if node == None:
        return None
    elif hasattr(node, '__ast__'):
        return node.__ast__()
    elif isinstance(node, list):
        return [ to_ast(n) for n in node ]
    elif isinstance(node, tuple):
        return tuple([ to_ast(n) for n in node ])
    elif isinstance(node, cyast_gen._AST):
        return _to_ast_transformer().visit(node)
    else:
        return node

def args_to_ast( d, keys ):
    for key in keys:
        if d.has_key(key):
            d[key] = to_ast(d[key])
    return d

def node_from_args( ast_class ):
    """ Helper function that returns a function buildin an ast node.

    The returned function will apply C{to_ast} to each argument and
    keyword argument.

    @param ast_class: class to be built.
    """

    def fun(cls, *args, **kwargs):
        args = to_ast(args)
        kwargs = args_to_ast(kwargs, ast_class._fields)
        return ast_class(*args, **kwargs)
    return fun

def stmt(node):
    """ Transform a builder or a builder helper into a cython statement (ast).
    """
    return ast.Expr( node )

def _extract_expr(expr):
    return Python2Cythyon().visit( extract_python_expr(cyast_gen._AST, expr) )

def E(expr):
    """ Extraction helper.

    Extracts an ast from an expression or a statement.

    @param expr: expression to extract from.
    @return: ast
    """
    return _extract_expr(expr)

def A(param = None, type = None):
    """ Argument construction helper.

    @param param: optional first argument.
    @param type: optional first argument type.
    @return: argument helper object used to build function arguments.
    @rtype: C{Builder.arguments_helper}.
    """
    args = Builder.Arguments()
    if param != None:
        return args.param(param, type = type)
    return args


def _aug_assign(operator):
    def fun(self, value):
        self.node = cyast_gen.AugAssign(target = to_ast(self.node),
                                    op     = operator,
                                    value  = to_ast(value));
        return self
    return fun


def _bin_op(operator):
    def fun(self, right):
        right = to_ast(right)
        self.node = cyast_gen.BinOp(left  = to_ast(self.node),
                                op    = operator,
                                right = to_ast(right))
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
            args = to_ast(args)
            self.node = cyast_gen.Call( func = to_ast(self.node), args = args, keywords = [], starargs = None, kwargs = None )
            return self

        def args(self, args):
            self.node.args = to_ast(args)
            return self

        def subscript(self, index=None):
            self.node = cyast_gen.Subscript(value = to_ast(self.node), slice = cyast_gen.Index(to_ast(E(index))))
            return self

        def attr(self, attribute):
            assert( isinstance(attribute, str) )
            self.node = cyast_gen.Attribute(value = to_ast(self.node), attr = attribute)
            return self

        def assign(self, value):
            self.node = cyast_gen.Assign(targets = [ to_ast(self.node) ], value = to_ast(E(value)));
            return self

        def type(self, value):
            self.node.type = value
            return self

        def init(self, value):
            self.node.init = to_ast(value)
            return self

        sub_assign = _aug_assign(cyast_gen.Sub())
        add_assign = _aug_assign(cyast_gen.Add())
        xor_assign = _aug_assign(cyast_gen.BitXor())
        or_assign  = _aug_assign(cyast_gen.BitOr())

        mult    = _bin_op(cyast_gen.Mult())
        add    = _bin_op(cyast_gen.Add())
        sub    = _bin_op(cyast_gen.Sub())
        bit_and = _bin_op(cyast_gen.BitAnd())
        bit_or  = _bin_op(cyast_gen.BitOr())
        bit_xor = _bin_op(cyast_gen.BitXor())
        xor = bit_xor

        def eq(self, right):
            return Builder.EqCompare(self, right)

        def lt(self, right):
            return Builder.LtCompare(self, right)

    class arguments_helper(object):
        def __init__(self):
            self.node = cyast_gen.arguments(args = [], vararg = None, kwargs = None, defaults = [])

        def param(self, name, default = None, type = None):
            annot = to_ast(E(type)) if type else None
            self.node.args.append( cyast_gen.arg( arg = name, annotation = annot) )
            if default != None:
                self.node.defaults.append( to_ast(E(default)) )
            return self

        def __ast__(self):
            return self.node

    def __init__(self):
        coreir.BuilderBase.__init__(self)

    @classmethod
    def Helper(cls, expr):
        return cls.helper(_extract_expr(expr))

    @classmethod
    def Comment(cls, str):
        return cyast_gen.Comment(str)

    @classmethod
    def EqCompare(cls, left, right):
        return E( cyast_gen.Compare( left = to_ast(left), ops = [ cyast_gen.Eq() ], comparators = [ to_ast(right) ]) )

    @classmethod
    def LtCompare(cls, left, right):
        return E( cyast_gen.Compare( left = to_ast(left), ops = [ cyast_gen.Lt() ], comparators = [ to_ast(right) ]) )

    @classmethod
    def FunctionDef(cls, **kwargs):
        args_to_ast(kwargs, cyast_gen.FunctionDef._fields)
        check_arg(kwargs, "lang", cyast_gen.Def())
        check_arg(kwargs, "args", cyast_gen.arguments( args = [], vararg = None, kwarg = None, defaults = [] ))
        return check_attrs(cyast_gen.FunctionDef( **kwargs ), body = [], decl = [])

    @classmethod
    def FunctionCpDef(cls, **kwargs):
        args_to_ast(kwargs, cyast_gen.FunctionDef._fields)
        check_arg(kwargs, "lang", cyast_gen.CpDef(public = True, api = True))
        return cls.FunctionDef(**kwargs)

    @classmethod
    def FunctionCDef(cls, **kwargs):
        args_to_ast(kwargs, cyast_gen.FunctionDef._fields)
        check_arg(kwargs, "lang", cyast_gen.CDef(public = True, api = True))
        return cls.FunctionDef(**kwargs)

    def begin_FunctionDef(self, **kwargs):
        self.begin_base_block(self.FunctionDef(**kwargs))

    def begin_FunctionCDef(self, **kwargs):
        api = False if not kwargs.has_key('api') else kwargs['api']
        public = False if not kwargs.has_key('public') else kwargs['public']
        self.begin_FunctionDef(lang = cyast_gen.CDef(public=public, api=api), **kwargs)

    def begin_FunctionCPDef(self, **kwargs):
        self.begin_FunctionDef(lang = cyast_gen.CpDef(public=True, api=True), **kwargs)

    def begin_PrivateFunctionCDef(self, **kwargs):
        self.begin_FunctionDef(lang = cyast_gen.CDef(public = False), **kwargs)

    @classmethod
    def CFor(cls, *args, **kwargs):
        args = to_ast(args)
        args_to_ast(kwargs, cyast_gen.CFor._fields)
        return check_attrs(cyast_gen.CFor(*args, **kwargs), body = [], or_else = [])

    @classmethod
    def For(cls, *args, **kwargs):
        args = to_ast(args)
        args_to_ast(kwargs, cyast_gen.For._fields)
        return check_attrs(cyast_gen.For(*args, **kwargs), body = [], or_else = [])

    @classmethod
    def If(cls, *args, **kwargs):
        args = to_ast(args)
        args_to_ast(kwargs, cyast_gen.If._fields)
        return check_attrs(cyast_gen.If(*args, **kwargs), body = [], or_else = [])

    def begin_If(self, *args, **kwargs):
        self.begin_block(to_ast(self.If(*args, **kwargs)))

    def begin_Elif(self, *args, **kwargs):
        self._current_scope = self._current.orelse
        self.begin_If(*args, **kwargs)

    def begin_Else(self, *args, **kwargs):
        self._current_scope = self._current.orelse

    def end_If(self):
        assert( isinstance(self._current, cyast_gen.If) )
        self._current = to_ast( self._current )
        self.end_block()

    def end_FunctionDef(self):
        if not isinstance(self._current, cyast_gen.FunctionDef):
            raise CurrentBlockError(expected=cyast_gen.FunctionDef, got=self._current)
        self._current.body = to_ast( flatten_lists(self._current.body) )
        if( self._current.body == []):
            self._current.body.append( cyast_gen.Pass() )
        self.end_base_block()

    def emit(self, e):
        if isinstance(e, Builder.helper):
            e = to_ast(e)
        return super(Builder, self).emit(e)

    def emit_Return(self, value):
        self.emit( cyast_gen.Return( value = to_ast(value) ) )

    @classmethod
    def Tuple(self, elts):
        return E( cyast_gen.Tuple( elts = to_ast(elts) ) )

    class class_def_helper(object):
        def __init__(self, name, bases, lang, **kwargs):
            self.node = cyast_gen.ClassDef(name  = to_ast(name),
                                       bases = to_ast(bases),
                                       lang  = to_ast(lang),
                                       **kwargs)

        def add_method(self, method):
            self.node.body.append(method)

        def add_decl(self, decl):
            self.node.decl.append(to_ast(decl))

        def __ast__(self):
            return self.node

    @classmethod
    def ClassDef(cls, name, bases = []):
        return cls.class_def_helper(name, bases, cyast_gen.Def())

    @classmethod
    def PublicClassCDef(cls, name, bases = [], **kwargs):
        return cls.class_def_helper(name, bases, cyast_gen.CDef(public = True), **kwargs)

    @classmethod
    def ClassCDef(cls, name, bases = [], **kwargs):
        return cls.class_def_helper(name, bases, cyast_gen.CDef(public = False), **kwargs)

    @classmethod
    def Compare(self, left, ops, comparators):
        return E( cyast_gen.Compare(left = to_ast(left), ops = ops, comparators = to_ast(comparators)) )

    @classmethod
    def PublicCVar( cls, name, type = None, init = None ):
        return E( cyast_gen.CVar( name = name,
                              type = type,
                              public = True,
                              init = to_ast(init) ) )

    @classmethod
    def CVar( cls, name, type = None, init = None):
        return E( cyast_gen.CVar( name = name,
                              type = type,
                              public = False,
                              init = to_ast(init) ) )

    @classmethod
    def Arguments(cls):
        return cls.arguments_helper()

    def __ast__(self):
        return super(Builder, self).ast()

################################################################################
# python to cython ast translation
################################################################################

class Python2Cythyon(ast.NodeTransformer):
    # working because of a hack (same node name in unparser)
    def visit_list(self, l):
        return [ self.visit(e) for e in l ]

    def visit_FunctionDef(self, node):
        return cyast_gen.FunctionDef( name = node.name,
                                  args = self.visit( node.args ),
                                  body = self.visit( node.body ),
                                  lang = cyast_gen.Def(),
                                  decl = [] )


################################################################################
from neco import unparse
from neco.unparse import Unparser as _Unparser

class Unparser(_Unparser) :
    def _FunctionDecl (self, tree) :
        self.write("\n")
        if isinstance(tree.lang, cyast_gen.Def) :
            self.fill("def " + tree.name + "(")
        elif isinstance(tree.lang, (cyast_gen.CDef, cyast_gen.CpDef)) :
            if isinstance(tree.lang, cyast_gen.CDef) :
                self.fill("cdef ")
            else :
                self.fill("cpdef ")
            if tree.lang.public :
                self.write("public ")
            if tree.lang.api :
                self.write("api ")
            self.dispatch(tree.returns)
            self.write(" " + tree.name + "(")
        else :
            assert False
        self.dispatch(tree.args)
        self.write(")")

    def _FunctionDef (self, tree) :
        self.write("\n")
        if isinstance(tree.lang, cyast_gen.Def) :
            self.fill("def " + tree.name + "(")
        elif isinstance(tree.lang, (cyast_gen.CDef, cyast_gen.CpDef)) :
            if isinstance(tree.lang, cyast_gen.CDef) :
                self.fill("cdef ")
            else :
                self.fill("cpdef ")
            if tree.lang.public :
                self.write("public ")
            if tree.lang.api :
                self.write("api ")
            self.dispatch(tree.returns)
            self.write(" " + tree.name + "(")
        else :
            assert False
        self.dispatch(tree.args)
        self.write(")")
        self.enter()
        for d in tree.decl :
            d.public = None
            self.dispatch(d)
        self.dispatch(tree.body)
        self.leave()

    def _arg (self, tree) :
        if tree.annotation :
            self.dispatch(tree.annotation)
            self.write(" ")
        self.write(tree.arg)
    def _ClassDef (self, tree):
        self.write("\n")
        if isinstance(tree.lang, cyast_gen.Def) :
            self.fill("class ")
            tree.decl = []
        elif isinstance(tree.lang, cyast_gen.CDef) :
            if tree.lang.public:
                self.fill("cdef public class ")
            else:
                self.fill("cdef class ")
        else :
            assert False
        self.write(tree.name)
        if tree.bases :
            self.write("(")
            for i, a in enumerate(tree.bases):
                if i >= 1:
                    self.write(", ")
                self.dispatch(a)
            self.write(")")
        if tree.spec:
            self.write('[object ')
            self.write(tree.spec.o)
            self.write(', type ')
            self.write(tree.spec.t)
            self.write(']')

        self.enter()
        for d in tree.decl :
            self.dispatch(d)
        self.dispatch(tree.body)
        self.leave()
    def _CFor (self, tree) :
        self.fill("for ")
        self.dispatch(tree.start)
        self.dispatch(tree.start_op)
        self.dispatch(tree.target)
        self.dispatch(tree.stop_op)
        self.dispatch(tree.stop)
        self.enter()
        self.dispatch(tree.body)
        self.leave()
    def _Eq (self, tree) :
        self.write(" == ")
    def _NotEq (self, tree) :
        self.write(" != ")
    def _Lt (self, tree) :
        self.write(" < ")
    def _LtE (self, tree) :
        self.write(" <= ")
    def _Gt (self, tree) :
        self.write(" > ")
    def _GtE (self, tree) :
        self.write(" >= ")
    def _Is (self, tree) :
        self.write(" is ")
    def _IsNot (self, tree) :
        self.write(" is not ")
    def _In (self, tree) :
        self.write(" in ")
    def _NotIn (self, tree) :
        self.write(" not in ")
    def _CImport (self, tree) :
        self.fill("cimport ")
        self.write(", ".join(tree.names))
    def _CImportFrom (self, tree) :
        self.fill("from ")
        self.write(tree.module + " import ")
        self.write(", ".join(tree.names))
    def _Extern (self, tree) :
        self.write("\n")
        self.fill("cdef extern ")
        self.write(tree.type + " ")
        self.write(tree.name)
        if tree.args is not None :
            self.write("(")
            for i, a in enumerate(tree.args) :
                if i > 0 :
                    self.write(", ")
                self.dispatch(a)
            self.write(")")
    def _ExternFrom (self, tree) :
        self.write("\n")
        self.fill('cdef extern from "%s"' % tree.hfile)
        self.enter()
        for d in tree.body :
            d.inner = True
            self.dispatch(d)
        self.leave()
    def _CVar (self, tree) :
        if tree.inner :
            self.fill("")
        else :
            self.fill("cdef ")
            if tree.public :
                self.write("public ")
        self.write(tree.type + " " + tree.name)
        if tree.init is not None :
            self.write(" = ")
            self.dispatch(tree.init)
    def _CFunction (self, tree) :
        self.fill(tree.type)
        self.write(" " + tree.name + "(")
        for i, a in enumerate(tree.args) :
            if i > 0 :
                self.write(", ")
            self.dispatch(a)
        self.write(")")
    def _CStruct (self, tree) :
        if tree.inner :
            self.fill("")
        else :
            self.fill("cdef ")
            if tree.public :
                self.write("public ")
        self.write("struct " + tree.name)
        self.enter()
        if tree.body :
            for d in tree.body :
                d.inner = True
                self.dispatch(d)
        else :
            self.fill("pass")
        self.leave()
    def _Cast (self, tree):
        self.write("<")
        self.write(tree.target)
        self.write(">")
        self.dispatch(tree.value)

    def _Comment (self, tree):
        self.write(" \t# %s" % tree.message)

    def _NComment (self, tree):
        self.fill("")
        self.write("# %s" % tree.message)
