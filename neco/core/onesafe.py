"""
One Safe optimisation

This optimisations answers to two main issues:
  1. Provide base classes to represent optimized types. Backends can implement
  these types using efficient encodings.

  2. Provide base classes for token enumerators, these classes will enumerate
  optimized types in a efficient way (both are closely related).

  These should be more efficient than using a multiset and iterating over it.
"""

import ast
from neco.core import nettypes, netir

################################################################################
# Places
################################################################################


################################################################################
# Netir
################################################################################

################################################################################
# Optimisation pass
################################################################################

class OptimisationPass(object):
    """ One safe optimisation transformer.
    """

    def _update_select_type(self, select_type):
        def select(place):
            if place.one_safe:
                if place.type.is_BlackToken:
                    return "BTOneSafePlaceType"
                else:
                    return "OneSafePlaceType"
            elif place.type.is_BlackToken:
                return "BTPlaceType"
            else:
                return select_type(place)
        return select

    def transform_ast(self, net_info, node):
        class NodeTransformer(ast.NodeTransformer):
            def visit_list(self, node):
                return [ self.visit(child) for child in node ]

            def visit_TokenEnumeration(self, node):
                place_info = net_info.place_by_name(node.place_name)
                if (place_info.type.is_BlackToken):
                    if (place_info.one_safe ):
                        # bt 1s
                        new_node = BTOneSafeTokenEnumeration(node)
                        new_node.body = self.visit(node.body)
                        return new_node
                    else:
                        # bt not 1s
                        new_node = BTTokenEnumeration(node)
                        new_node.body = self.visit(node.body)
                        return new_node
                elif (place_info.one_safe ):
                    # generic 1s
                    new_node = OneSafeTokenEnumeration(node)
                    new_node.body = self.visit(node.body)
                    return new_node
                else:
                    node.body = self.visit(node.body)
                    return node
        return NodeTransformer().visit(node)

################################################################################
# EOF
################################################################################

