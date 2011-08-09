"""
One Safe optimisation

This optimisations answers to two main issues:
  1. Provide base classes to represent optimized types. Backends can implement
  these types using efficient encodings.

  2. Provide base classes for token enumerators, these classes will enumerate
  optimized types in a efficient way (both are closely related).

  These should be more efficient than using a multiset and iterating over it.
"""

import neco.core
import ast
from snakes.nets import tBlackToken
from snakes.typing import tAll
from neco.core import nettypes, netir, info, FactoryManager

################################################################################
# Places
################################################################################

class OneSafePlaceType(nettypes.PlaceType):
    """ Base class for one safe place types.
    """

    def __init__(self, place_info, marking_type, type, token_type):
        nettypes.PlaceType.__init__(self,
                                    place_info = place_info,
                                    marking_type = marking_type,
                                    type = type,
                                    token_type = token_type)

################################################################################

class BTPlaceType(nettypes.PlaceType):
    """ Base class for black token place types.
    """

    def __init__(self, place_info, marking_type, type, token_type):
        nettypes.PlaceType.__init__(self,
                                    place_info = place_info,
                                    marking_type = marking_type,
                                    type = type,
                                    token_type = token_type)

################################################################################

class BTOneSafePlaceType(nettypes.PlaceType):
    """ Base class for one safe black token place types.
    """

    def __init__(self, place_info, marking_type, type, token_type):
        nettypes.PlaceType.__init__(self,
                                    place_info = place_info,
                                    marking_type = marking_type,
                                    type = type,
                                    token_type = token_type)

################################################################################
# Netir
################################################################################

class OneSafeTokenEnumeration(netir.TokenEnumeration):
    """ Base class for NetIR nodes that enumerate tokens in OneSafePlaceType. """

    def __init__(self, node):
        self.token_is_used = node.token_is_used
        self.token_name = node.token_name
        self.place_name = node.place_name
        self.marking_name = node.marking_name
        self.body = node.body

################################################################################

class BTTokenEnumeration(netir.TokenEnumeration):
    """ Base class for NetIR nodes that enumerate tokens in BTPlaceType. """

    def __init__(self, node):
        self.token_is_used = node.token_is_used
        self.token_name = node.token_name
        self.place_name = node.place_name
        self.marking_name = node.marking_name
        self.body = node.body

################################################################################

class BTOneSafeTokenEnumeration(netir.TokenEnumeration):
    """ Base class for NetIR nodes that enumerate tokens in BTOneSafeTokenEnumeration. """

    def __init__(self, node):
        self.token_is_used = node.token_is_used
        self.token_name = node.token_name
        self.place_name = node.place_name
        self.marking_name = node.marking_name
        self.body = node.body

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

    def update_factory_manager(self):
        fm = FactoryManager.instance()
        fm.select_type = self._update_select_type(fm.select_type)
        return fm

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

