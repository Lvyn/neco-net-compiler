""" Abstract syntax tree for representing functions and algorithms.

The file gen_netir was automatically generated.
"""

import inspect, types
from ast import NodeVisitor, NodeTransformer
import gen_netir
from gen_netir import *
from neco.debug import *

class CompilerVisitor(object):
    """ Base class implementing the visitor pattern for compiling an ast. """

    def __init__(self):
        self.backend = "Core"

    def compile_list(self, node):
        return [ self.compile(child) for child in node ]

    def compile(self, node):
        """compile a node."""
        method = 'compile_' + node.__class__.__name__
        debug_print("compiling: " + node.__class__.__name__)
        compiler = getattr(self, method, self.cannot_compile)
        return compiler(node)

    def cannot_compile(self, node):
        """Called if no explicit compile function exists for a node."""
        class CannotCompile(Exception):
            def __init__(self, str):
                self._str = str
            def __str__(self):
                return self._str
        raise CannotCompile(self.backend + " backend cannot compile %s" % node.__class__.__name__)


class BuilderBase(object):
    """ Utility class for building AST
    """

    class ast_builder(object):
        """
        """
        def __init__(self, node):
            """

            @param node:
            @type node: C{}
            """
            self._node = node

        @property
        def ast(self):
            return self._node

    class __Caller__(object):
        def __init__(self, cls, builder, method):
            self.cls = cls
            self.builder = builder
            self.method = method

        def __call__(self, factory, *args, **kw):
            return self.method(self.builder, self.cls(*args, **kw) )

    def __init__(self):
        """ Build a builder. """
        self._parents = []
        self._nodes = []
        self._current = None
        self._current_scope = None

    def register_block_node(self, cls):
        """ registers a new block node.

        Adds a new begin_<C{cls}> method to builder.

        @param cls: ast block class
        @type cls: C{Block}
        """
        method = types.MethodType(self.__Caller__(cls, self, BuilderBase.begin_block),
                                  self,
                                  BuilderBase)
        method_name = "begin_%s" % cls.__name__
        setattr(self, method_name, method)

    def register_emit_node(self, cls):
        """ registers a new statatement node.

        Adds a new begin_<C{cls}> method to builder.

        @param cls: ast stmt class
        @type cls: C{Stmt}
        """
        method = types.MethodType(self.__Caller__(cls, self, BuilderBase.emit),
                                  self,
                                  BuilderBase)
        method_name = "emit_%s" % cls.__name__
        setattr(self, method_name, method)

    def register_expr_node(self, cls):
        """ registers a new expression node.

        Adds a new <cls> method to builder.
        @param cls: ast stmt class
        @type cls: C{Expr}
        """
        method = types.MethodType(self.__Caller__(cls, self, BuilderBase.expr),
                                  self,
                                  BuilderBase)
        method_name = "%s" % cls.__name__
        setattr(self, method_name, method)

    def ast(self):
        """ Retrive the built ast.

        @return nodes
        @rtype C{list<Node>}
        """
        assert (self._current == None)
        return self._nodes

    def begin_base_block(self, node):
        """ Begin a base block.

        Begins a base block, a function for instance.

        @param node: ast node class
        @type node: C{Node}
        """
        self._current = node
        self._current_scope = node.body

    def begin_block(self, node):
        """ Begin a new block.

        @param: ast block node
        @type: C{Node}
        """
        self._current_scope.append(node)
        self._parents.append( (self._current, self._current_scope) )
        self._current = node
        self._current_scope = node.body

    def end_block(self):
        """ End a block. """
        node, current_scope = self._parents.pop(-1)
        self._current = node
        self._current_scope = current_scope

    def end_base_block(self):
        """ End a base block.

        Ends a base block, a function for instance.
        """
        assert (not self._parents)
        self._nodes.append(self._current)
        self._current = None
        self._current_scope = None

    def end_all_blocks(self):
        """ End all blocks. """
        l = len(self._parents)
        for _ in range(0, len(self._parents)):
            (node, current_scope) = self._parents.pop(-1)
            self._current = node
            self._current_scope = current_scope

    def emit(self, stmt_node):
        """ Add a statement.

        Adds a statements to current node.

        @param stmt_node: ast statement node
        @type stmt_node: C{Stmt}
        """
        # assert (isinstance(self._current, Block) or
        #         isinstance(self._current, FunctionDef))
        self._current_scope.append(stmt_node)

    def expr(self, expr_node):
        """ Get an expression.
        """
        return expr_node


class Builder(BuilderBase):
    """ utility class for building the AST
    """
    def __init__(self):
        BuilderBase.__init__(self)

        for name, cls in inspect.getmembers(gen_netir, inspect.isclass):
            if issubclass(cls, FunctionDef) and cls != FunctionDef:
                self.register_function_node(cls)

        for name, cls in inspect.getmembers(gen_netir, inspect.isclass):
            if issubclass(cls, Stmt) and cls != Stmt:
                self.register_emit_node(cls)

        for name, cls in inspect.getmembers(gen_netir, inspect.isclass):
            if issubclass(cls, Block) and cls != Block:
                self.register_block_node(cls)

        for name, cls in inspect.getmembers(gen_netir, inspect.isclass):
            if issubclass(cls, Expr) and cls != Block:
                self.register_expr_node(cls)

    def register_function_node(self, cls):
        """ Register a new function node class.

        Registers a new function node, allowing calls like begin_function_<C{cls}>.

        @param cls: ast function node class
        @type cls: C{FunctionDef}
        """
        method = types.MethodType(self.__Caller__(cls, self, Builder.begin_function),
                                  self,
                                  Builder)
        method_name = "begin_function_%s" % cls.__name__
        setattr(self, method_name, method)

    def begin_function(self, node):
        assert (self._current == None)
        assert (isinstance(node, FunctionDef))
        if getattr(node, "body", None) == None:
            node.body = []

        self._current_function = node
        self._current = node
        self._current_scope = node.body

    def end_function(self):
        assert (isinstance(self._current, FunctionDef))
        self._current = None
        self._current_scope = None
        self._nodes.append(self._current_function)


    def begin_Elif(self, *args, **kwargs):
        self._current_scope = self._current.orelse
        self.begin_If(*args, **kwargs)

    def begin_Else(self, *args, **kwargs):
        self._current_scope = self._current.orelse
