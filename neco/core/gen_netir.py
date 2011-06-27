# this file has been automatically generated running:
# asdl.py --output=netir/netir.py netir/netir.asdl
# timestamp: 2011-06-27 11:32:32.141195

import ast

class _AST (ast.AST):
    def __init__ (self, **ARGS):
        ast.AST.__init__(self)
        for k, v in ARGS.iteritems():
            setattr(self, k, v)

class Node (_AST):
    pass

class FunctionDef (Node):
    _fields = ()
    _attributes = ()

class Expr (Node):
    _fields = ()
    _attributes = ()

class Stmt (Node):
    _fields = ()
    _attributes = ()

class Expr (_AST):
    pass

class PyExpr (Expr):
    _fields = ('expr',)
    _attributes = ()
    def __init__ (self, expr, **ARGS):
        Expr.__init__(self, **ARGS)
        self.expr = expr

class ReadFlow (Expr):
    _fields = ('marking_name', 'process_name')
    _attributes = ()
    def __init__ (self, marking_name, process_name, **ARGS):
        Expr.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.process_name = process_name

class FunctionCall (Expr):
    _fields = ('function_name', 'arguments')
    _attributes = ()
    def __init__ (self, function_name, arguments=[], **ARGS):
        Expr.__init__(self, **ARGS)
        self.function_name = function_name
        self.arguments = list(arguments)

class Token (Expr):
    _fields = ('value', 'place_name')
    _attributes = ()
    def __init__ (self, value, place_name, **ARGS):
        Expr.__init__(self, **ARGS)
        self.value = value
        self.place_name = place_name

class Name (Expr):
    _fields = ('name',)
    _attributes = ()
    def __init__ (self, name, **ARGS):
        Expr.__init__(self, **ARGS)
        self.name = name

class Value (Expr):
    _fields = ('value', 'place_name')
    _attributes = ()
    def __init__ (self, value, place_name, **ARGS):
        Expr.__init__(self, **ARGS)
        self.value = value
        self.place_name = place_name

class Tuple (Expr):
    _fields = ('components',)
    _attributes = ()
    def __init__ (self, components=[], **ARGS):
        Expr.__init__(self, **ARGS)
        self.components = list(components)

class Compare (Expr):
    _fields = ('left', 'ops', 'comparators')
    _attributes = ()
    def __init__ (self, left, ops=[], comparators=[], **ARGS):
        Expr.__init__(self, **ARGS)
        self.left = left
        self.ops = list(ops)
        self.comparators = list(comparators)

class Pickle (Expr):
    _fields = ('obj',)
    _attributes = ()
    def __init__ (self, obj, **ARGS):
        Expr.__init__(self, **ARGS)
        self.obj = obj

class FlowCheck (Expr):
    _fields = ('marking_name', 'current_flow', 'place_info')
    _attributes = ()
    def __init__ (self, marking_name, place_info, current_flow=None, **ARGS):
        Expr.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.current_flow = current_flow
        self.place_info = place_info

class Stmt (_AST):
    pass

class AddToken (Stmt):
    _fields = ('marking_name', 'place_name', 'token_expr')
    _attributes = ()
    def __init__ (self, marking_name, place_name, token_expr, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_name = place_name
        self.token_expr = token_expr

class RemToken (Stmt):
    _fields = ('marking_name', 'place_name', 'token_expr', 'use_index')
    _attributes = ()
    def __init__ (self, marking_name, place_name, token_expr, use_index=None, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_name = place_name
        self.token_expr = token_expr
        self.use_index = use_index

class MarkingCopy (Stmt):
    _fields = ('dst_name', 'src_name', 'mod')
    _attributes = ()
    def __init__ (self, dst_name, src_name, mod=[], **ARGS):
        Stmt.__init__(self, **ARGS)
        self.dst_name = dst_name
        self.src_name = src_name
        self.mod = list(mod)

class AddMarking (Stmt):
    _fields = ('markingset_name', 'marking_name')
    _attributes = ()
    def __init__ (self, markingset_name, marking_name, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.markingset_name = markingset_name
        self.marking_name = marking_name

class FlushIn (Stmt):
    _fields = ('token_name', 'marking_name', 'place_name')
    _attributes = ()
    def __init__ (self, token_name, marking_name, place_name, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.token_name = token_name
        self.marking_name = marking_name
        self.place_name = place_name

class FlushOut (Stmt):
    _fields = ('marking_name', 'place_name', 'token_expr')
    _attributes = ()
    def __init__ (self, marking_name, place_name, token_expr, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_name = place_name
        self.token_expr = token_expr

class RemToken (Stmt):
    _fields = ('marking_name', 'place_name', 'token_expr')
    _attributes = ()
    def __init__ (self, marking_name, place_name, token_expr, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_name = place_name
        self.token_expr = token_expr

class RemTuple (Stmt):
    _fields = ('marking_name', 'place_name', 'tuple_expr')
    _attributes = ()
    def __init__ (self, marking_name, place_name, tuple_expr, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_name = place_name
        self.tuple_expr = tuple_expr

class TupleOut (Stmt):
    _fields = ('marking_name', 'place_name', 'tuple_info')
    _attributes = ()
    def __init__ (self, marking_name, place_name, tuple_info, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_name = place_name
        self.tuple_info = tuple_info

class ProcedureCall (Stmt):
    _fields = ('function_name', 'arguments')
    _attributes = ()
    def __init__ (self, function_name, arguments=[], **ARGS):
        Stmt.__init__(self, **ARGS)
        self.function_name = function_name
        self.arguments = list(arguments)

class Assign (Stmt):
    _fields = ('variable', 'expr')
    _attributes = ()
    def __init__ (self, variable, expr, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.variable = variable
        self.expr = expr

class Print (Stmt):
    _fields = ('message',)
    _attributes = ()
    def __init__ (self, message, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.message = message

class UpdateFlow (Stmt):
    _fields = ('marking_name', 'place_info')
    _attributes = ()
    def __init__ (self, marking_name, place_info, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_info = place_info

class Comment (Stmt):
    _fields = ('message',)
    _attributes = ()
    def __init__ (self, message, **ARGS):
        Stmt.__init__(self, **ARGS)
        self.message = message

class FunctionDef (_AST):
    pass

class Init (FunctionDef):
    _fields = ('function_name', 'marking_name', 'body')
    _attributes = ()
    def __init__ (self, function_name, marking_name, body=[], **ARGS):
        FunctionDef.__init__(self, **ARGS)
        self.function_name = function_name
        self.marking_name = marking_name
        self.body = list(body)

class SuccT (FunctionDef):
    _fields = ('function_name', 'markingset_name', 'marking_name', 'body', 'transition_info')
    _attributes = ()
    def __init__ (self, function_name, markingset_name, marking_name, transition_info, body=[], **ARGS):
        FunctionDef.__init__(self, **ARGS)
        self.function_name = function_name
        self.markingset_name = markingset_name
        self.marking_name = marking_name
        self.body = list(body)
        self.transition_info = transition_info

class SuccP (FunctionDef):
    _fields = ('function_name', 'markingset_name', 'marking_name', 'body', 'process_info')
    _attributes = ()
    def __init__ (self, function_name, markingset_name, marking_name, process_info, body=[], **ARGS):
        FunctionDef.__init__(self, **ARGS)
        self.function_name = function_name
        self.markingset_name = markingset_name
        self.marking_name = marking_name
        self.body = list(body)
        self.process_info = process_info

class Succs (FunctionDef):
    _fields = ('function_name', 'marking_argument_name', 'markingset_variable_name', 'body')
    _attributes = ()
    def __init__ (self, function_name, marking_argument_name, markingset_variable_name, body=[], **ARGS):
        FunctionDef.__init__(self, **ARGS)
        self.function_name = function_name
        self.marking_argument_name = marking_argument_name
        self.markingset_variable_name = markingset_variable_name
        self.body = list(body)

class operator (_AST):
    pass

class EQ (operator):
    _fields = ()
    _attributes = ()

class Block (_AST):
    pass

class TokenEnumeration (Block):
    _fields = ('token_name', 'marking_name', 'place_name', 'token_is_used', 'use_index', 'body')
    _attributes = ()
    def __init__ (self, token_name, marking_name, place_name, token_is_used, use_index=None, body=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.token_name = token_name
        self.marking_name = marking_name
        self.place_name = place_name
        self.token_is_used = token_is_used
        self.use_index = use_index
        self.body = list(body)

class MultiTokenEnumeration (Block):
    _fields = ('token_names', 'offset_names', 'marking_name', 'place_name', 'body')
    _attributes = ()
    def __init__ (self, marking_name, place_name, token_names=[], offset_names=[], body=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.token_names = list(token_names)
        self.offset_names = list(offset_names)
        self.marking_name = marking_name
        self.place_name = place_name
        self.body = list(body)

class NotEmpty (Block):
    _fields = ('marking_name', 'place_name', 'body')
    _attributes = ()
    def __init__ (self, marking_name, place_name, body=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.marking_name = marking_name
        self.place_name = place_name
        self.body = list(body)

class GuardCheck (Block):
    _fields = ('condition', 'body')
    _attributes = ()
    def __init__ (self, condition, body=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.condition = condition
        self.body = list(body)

class If (Block):
    _fields = ('condition', 'body', 'orelse')
    _attributes = ()
    def __init__ (self, condition, body=[], orelse=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.condition = condition
        self.body = list(body)
        self.orelse = list(orelse)

class Match (Block):
    _fields = ('tuple_info', 'body')
    _attributes = ()
    def __init__ (self, tuple_info, body=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.tuple_info = tuple_info
        self.body = list(body)

class CheckTuple (Block):
    _fields = ('tuple_name', 'tuple_info', 'body')
    _attributes = ()
    def __init__ (self, tuple_name, tuple_info, body=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.tuple_name = tuple_name
        self.tuple_info = tuple_info
        self.body = list(body)

class CheckType (Block):
    _fields = ('variable', 'type', 'body')
    _attributes = ()
    def __init__ (self, variable, type, body=[], **ARGS):
        Block.__init__(self, **ARGS)
        self.variable = variable
        self.type = type
        self.body = list(body)

class PComponent (_AST):
    pass

class PVar (PComponent):
    _fields = ('name',)
    _attributes = ()
    def __init__ (self, name, **ARGS):
        PComponent.__init__(self, **ARGS)
        self.name = name

class PValue (PComponent):
    _fields = ('value',)
    _attributes = ()
    def __init__ (self, value, **ARGS):
        PComponent.__init__(self, **ARGS)
        self.value = value
