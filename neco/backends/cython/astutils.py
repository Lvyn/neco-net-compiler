""" Python abstract syntax tree helpers.
"""
import ast, sys
import neco.core.netir as coreir
import cyast
from neco.utils import flatten_lists
from neco import unparse
from neco.unparse import Unparser as _Unparser
from neco.backends.pythonic import *
################################################################################


################################################################################

################################################################################

# def _aug_assign(operator):
#     def fun(self, value):
#         self.node = cyast.AugAssign(target = to_ast(self.node),
#                                     op     = operator,
#                                     value  = to_ast(value));
#         return self
#     return fun


# def _bin_op(operator):
#     def fun(self, right):
#         right = to_ast(right)
#         self.node = cyast.BinOp(left  = to_ast(self.node),
#                                 op    = operator,
#                                 right = to_ast(right))
#         return self
#     return fun

################################################################################

################################################################################
# EOF
################################################################################

