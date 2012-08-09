from common import NecoTypeError, from_neco_lib
from lowlevel import Mask
from neco.core.info import TypeInfo
from neco.core.nettypes import provides_by_index_access, \
    provides_by_index_deletion
from neco.utils import should_not_be_called, todo
import cyast
import math
import neco.core.nettypes as coretypes
from neco import config

def packed_place(cls):
    """ Decorator for packed places.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_packed
    False

    >>> @packed_place
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_packed
    True


    """
    cls._packed_place_ = True
    return cls

def helper_place_type(cls):
    """ Decorator for packed     places.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_helper
    False

    >>> @helper_place_type
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_helper
    True


    """
    cls._helper_ = True
    return cls

def not_revelant(cls):
    """ Decorator for revelant place types.

    A non revelant place will not be used in a dump.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    True

    >>> @not_revelant
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    False


    """
    cls._revelant_ = False
    return cls

def checking_without_helper(cls):
    """ Decorator for place types that do not need a helper to support checking.

    A non revelant place will not be used in a dump.

    >>> class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    True

    >>> @not_revelant
    ... class MyPlaceType(CythonPlaceType):
    ...     pass
    >>>
    >>> MyPlaceType().is_revelant
    False


    """
    cls._checking_need_helper_ = False
    return cls



class CythonPlaceType(object):
    """ Base class for cython place types. """

    _packed_place_ = False
    _revelant_ = True # should be dumped
    _helper_ = False
    _checking_need_helper_ = True

    def get_attribute_name(self):
        return self.chunk.get_attribute_name()

    @property
    def is_packed(self):
        """ C{True} if place is packed, C{False} otherwise """
        return self.__class__._packed_place_

    @property
    def is_revelant(self):
        """ C{True} if place should be used in dump, C{False} otherwise """
        return getattr(self, 'revelant', self.__class__._revelant_)

    @property
    def is_helper(self):
        """ C{True} if place is a helper, C{False} otherwise """
        return self.__class__._helper_

    @property
    def checking_need_helper(self):
        return self._checking_need_helper_

################################################################################

@checking_without_helper
class ObjectPlaceType(coretypes.ObjectPlaceType, CythonPlaceType):
    """ Python implementation of fallback place type. """

    def __init__(self, place_info, marking_type):
        coretypes.ObjectPlaceType.__init__(self,
                                           place_info=place_info,
                                           marking_type=marking_type,
                                           type=TypeInfo.get('MultiSet'),
                                           token_type=place_info.type)

        self.chunk = marking_type.chunk_manager.new_chunk(marking_type.id_provider.get(self),
                                                 TypeInfo.get('MultiSet'))
        self.chunk.hint = "{} - {!s}".format(place_info.name, place_info.type)

    def new_place_stmt(self, env, marking_var):
        return cyast.Assign(targets=[self.attribute_expr(env, marking_var)],
                            value=cyast.Call(func=cyast.Name(id=env.type2str(TypeInfo.get('MultiSet')))))

    def delete_stmt(self, env, marking_var):
        return []

    def attribute_expr(self, env, marking_var):
        return cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))

    def hash_expr(self, env, marking_var):
        return cyast.E('{}.{}.hash()'.format(marking_var.name, self.chunk.get_attribute_name()))

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left, ops=[cyast.Eq()], comparators=[right])

    def iterable_expr(self, env, marking_var):
        return self.attribute_expr(env, marking_var)

    def remove_token_stmt(self, env, token_expr, compiled_token, marking_var):
        return cyast.stmt(cyast.Call(func=cyast.Attribute(value=self.attribute_expr(env, marking_var),
                                                          attr='remove'),
                                     args=[ compiled_token ]))

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        return cyast.stmt(cyast.Call(func=cyast.Attribute(value=self.attribute_expr(env, marking_var),
                                                          attr='add'),
                                     args=[ compiled_token ]))

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        attr_name = self.chunk.get_attribute_name()
        return [ cyast.E("{}.{} = {}.{}.copy()".format(dst_marking_var.name, attr_name,
                                                       src_marking_var.name, attr_name)) ]
        #return cyast.Call(func=cyast.Attribute(value=self.attribute_expr(env, marking_var),
        #                                       attr="copy"))

    def light_copy_stmt(self, env, dst_marking_var, src_marking_var):
        attr_name = self.chunk.get_attribute_name()
        return cyast.E("{}.{} = {}.{}".format(dst_marking_var.name, attr_name,
                                              src_marking_var.name, attr_name))
        #return self.attribute_expr(env, marking_var)

    def clear_stmt(self, env, marking_var):
        return cyast.Assign(targets=[self.attribute_expr(env, marking_var)],
                            value=cyast.Call(func=cyast.Name(env.type2str(TypeInfo.get('MultiSet')))))

    def not_empty_expr(self, env, marking_var):
        return self.attribute_expr(env, marking_var)

    def token_expr(self, env, token):
        return cyast.E(repr(token))

    def add_multiset_expr(self, env, multiset, marking_var):
        return cyast.stmt(cyast.Call(func=cyast.Attribute(value=self.attribute_expr(env, marking_var),
                                                          attr='update'),
                                     args=[ multiset ]))

    def dump_expr(self, env, marking_var):
        return cyast.E('dump({}.{})'.format(marking_var.name, self.chunk.get_attribute_name()))

    def add_items_stmt(self, env, multiset, marking_var):
        attribute_expr = self.attribute_expr(env, marking_var)
        return cyast.stmt(cyast.Call(func=cyast.Attribute(value=attribute_expr,
                                                          attr='add_items'),
                                     args=[multiset])
                          )

    def compare_expr(self, env, left_marking_var, right_marking_var):
        left = self.attribute_expr(env, left_marking_var)
        right = self.attribute_expr(env, right_marking_var)
        return cyast.Call(func=cyast.Attribute(value=left,
                                               attr='compare'),
                          args=[right])

#    def not_empty_expr(self, env, marking_var):
#        return self.place_expr(env, marking_var)


    def enumerate_tokens(self, checker_env, token_variable, marking_var, body):
        checker_env.try_declare_cvar(token_variable.name, token_variable.type)
        return cyast.Builder.For(target=cyast.Name(token_variable.name),
                                 iter=self.iterable_expr(env=checker_env,
                                                           marking_var=marking_var),
                                 body=[ body ])

    def multiset_expr(self, env, marking_var):
        return self.attribute_expr(env, marking_var)

@provides_by_index_access
@provides_by_index_deletion
class IntPlaceType(coretypes.PlaceType, CythonPlaceType):
    """ Place type for small unbounded 'int' places. """

    def __init__(self, place_info, marking_type):
        assert(place_info.type == TypeInfo.get('Int'))
        coretypes.PlaceType.__init__(self,
                                     place_info=place_info,
                                     marking_type=marking_type,
                                     type=TypeInfo.get('IntPlace'),
                                     token_type=place_info.type)

        self.chunk = marking_type.chunk_manager.new_chunk(marking_type.id_provider.get(self),
                                                 TypeInfo.get('IntPlace'))
        self.chunk.hint = "{} - {!s}".format(place_info.name, place_info.type)

    def attribute_expr(self, env, marking_var):
        return cyast.E('{}.{}'.format(marking_var.name,
                                      self.chunk.get_attribute_name()))
        
    def check_token_type(self, token_expr):
        if not token_expr.type.is_Int:
            raise NecoTypeError(expr=token_expr, type=token_expr.type, expected=TypeInfo.get('Int'))

    def check_index_type(self, index_expr):
        if not index_expr.type.is_Int:
            raise NecoTypeError(expr=index_expr, type=index_expr.type, expected=TypeInfo.get('Int'))

    def check_marking_type(self, marking_expr):
        if not marking_expr.type.is_Marking:
            raise NecoTypeError(expr=marking_expr, type=marking_expr.type, expected=TypeInfo.get('Marking'))

    def new_place_stmt(self, env, marking_var):
        return cyast.Assign(targets=[self.attribute_expr(env, marking_var)],
                            value=cyast.E(from_neco_lib("int_place_type_new()")))

    def delete_stmt(self, env, marking_var):
        place_expr = self.attribute_expr(env, marking_var)
        return cyast.stmt(cyast.Call(func=cyast.E(from_neco_lib("int_place_type_free")),
                                     args=[ place_expr ])
                    )

    def hash_expr(self, env, marking_var):
        place_expr = self.attribute_expr(env, marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_hash")),
                          args=[ place_expr ])

    def eq_expr(self, env, left, right):
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_eq")),
                          args=[ left, right ])

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt(self, env, token_expr, compiled_token, marking_var):
        #self.check_token_type(token_expr)
        self.check_marking_type(marking_var)

        place_expr = self.attribute_expr(env, marking_var)
        return cyast.stmt(cyast.Call(func=cyast.E(from_neco_lib("int_place_type_rem_by_value")),
                               args=[ place_expr, compiled_token ])
                    )

    def remove_by_index_stmt(self, env, index_var, compiled_index, marking_var):
        self.check_index_type(index_var)
        self.check_marking_type(marking_var)

        place_expr = self.attribute_expr(env, marking_var)
        return cyast.stmt(cyast.Call(func=cyast.E(from_neco_lib("int_place_type_rem_by_index")),
                               args=[ place_expr, cyast.E(index_var.name) ])
                    )

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        #self.check_token_type(token_expr)
        self.check_marking_type(marking_var)

        place_expr = self.attribute_expr(env, marking_var)
        return cyast.stmt(cyast.Call(func=cyast.E(from_neco_lib("int_place_type_add")),
                               args=[ place_expr, compiled_token ])
                    )

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        self.check_marking_type(src_marking_var)
        self.check_marking_type(dst_marking_var)

        attr_name = self.chunk.get_attribute_name()
        return cyast.E("{}.{} = {}({}.{})".format(dst_marking_var.name, attr_name,
                                                  from_neco_lib("int_place_type_copy"),
                                                  src_marking_var.name, attr_name))
        
    def light_copy_stmt(self, env, dst_marking_var, src_marking_var):
        self.check_marking_type(dst_marking_var)
        self.check_marking_type(src_marking_var)

        attr_name = self.chunk.get_attribute_name()

        return cyast.E("{}.{} = {}({}.{})".format(dst_marking_var.name, attr_name,
                                                  from_neco_lib("int_place_type_light_copy"),
                                                  src_marking_var.name, attr_name))
    
    def get_size_expr(self, env, marking_var):
        self.check_marking_type(marking_var)
        place_expr = self.attribute_expr(env, marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_size")),
                          args=[ place_expr ])

    def get_token_expr(self, env, index_expr, compiled_index, marking_var):
        self.check_index_type(index_expr)
        self.check_marking_type(marking_var)

        place_expr = self.attribute_expr(env, marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_get")),
                          args=[ place_expr, compiled_index ])

    def clear_stmt(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.attribute_expr(env, marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_clear")),
                          args=[ place_expr ])

    def token_expr(self, env, token):
        return cyast.E(repr(token))

    def dump_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.attribute_expr(env, marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_cstr")),
                          args=[ place_expr ])

    def compare_expr(self, env, left_marking_var, right_marking_var):
        self.check_marking_type(left_marking_var)
        self.check_marking_type(right_marking_var)

        left = self.attribute_expr(env, left_marking_var)
        right = self.attribute_expr(env, right_marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_cmp")),
                          args=[ left, right ])

    def not_empty_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_not_empty")),
                          args=[place_expr])

    @todo
    def add_multiset_expr(self, env, multiset, marking_type, marking_var): pass

    @todo
    def add_items_stmt(self, env, multiset, marking_type, marking_var): pass

    def enumerate_tokens(self, env, token_var, marking_var, body):
        index_var = env.variable_provider.new_variable(type=TypeInfo.get('Int'))
        size_var = env.variable_provider.new_variable(type=TypeInfo.get('Int'))

        env.try_declare_cvar(token_var.name, token_var.type)
        env.try_declare_cvar(index_var.name, TypeInfo.get('Int'))
        env.try_declare_cvar(size_var.name, TypeInfo.get('Int'))

        place_size = self.get_size_expr(env=env,
                                        marking_var=marking_var)

        get_token = self.get_token_expr(env=env,
                                        index_expr=index_var,
                                        marking_var=marking_var,
                                        compiled_index=cyast.Name(index_var.name))


        return [ cyast.Assign(targets=[cyast.Name(size_var.name)],
                              value=place_size),
                 cyast.Builder.CFor(start=cyast.Num(0),
                                    start_op=cyast.LtE(),
                                    target=cyast.Name(index_var.name),
                                    stop_op=cyast.Lt(),
                                    stop=cyast.Name(size_var.name),
                                    body=[ cyast.Assign(targets=[cyast.Name(token_var.name)],
                                                        value=get_token),
                                           body ],
                                    orelse=[]) ]
    
    def multiset_expr(self, env, marking_var):
        self.check_marking_type(marking_var)

        place_expr = self.place_expr(env, marking_var)
        return cyast.Call(func=cyast.E(from_neco_lib("int_place_type_to_multiset")),
                          args=[place_expr])
        


class OneSafePlaceType(coretypes.OneSafePlaceType, CythonPlaceType):
    """ Cython one safe place Type implementation.

    Somehow peculiar because encoded using two place types, one packed for
    the emptiness test and one for the contained data.
    """

    def __init__(self, place_info, marking_type, bit_packing):
        coretypes.OneSafePlaceType.__init__(self,
                                          place_info,
                                          marking_type,
                                          place_info.type,
                                          place_info.type)
        self.helper_chunk = marking_type.chunk_manager.new_chunk(marking_type.id_provider.new(),
                                                                 TypeInfo.get('Bool'),
                                                                 packed=bit_packing)
        self.chunk = marking_type.chunk_manager.new_chunk(marking_type.id_provider.get(self),
                                                          place_info.type)
        
        self.info = place_info
        self.marking_type = marking_type
        
        self.helper_chunk.hint = "{} - {!s} <helper>".format(place_info.name, place_info.type)
        self.chunk.hint = "{} - {!s}".format(place_info.name, place_info.type)
        
    def new_place_stmt(self, env, marking_var):
        helper = self.helper_chunk
        if helper.packed:
            return []
        else:
            # set helper to false and return ast
            return cyast.E("{}.{} = 0".format(marking_var.name, helper.get_attribute_name()))

    def delete_stmt(self, env, marking_var):
        return []

    def hash_expr(self, env, marking_var):
        hash = "hash({}.{})".format(marking_var.name, self.chunk.get_attribute_name())
        if self.helper_chunk.packed:
            mask = int(self.helper_chunk.mask())
            bytes_offset, _ = self.helper_chunk.offset()
            test = "{}.{}[{}] & {}".format(marking_var.name,
                                           self.helper_chunk.get_attribute_name(),
                                           bytes_offset,
                                           mask)
        else:
            test = "{}.{}".format(marking_var.name, self.helper_chunk.get_attribute_name())
 
        return cyast.E("{hash} if {test} else 1".format(hash=hash, test=test))

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left,
                             ops=[cyast.Eq()],
                             comparators=[right])

    def compare_expr(self, env, left_marking_var, right_marking_var):
        if self.helper_chunk.packed:
            bytes_offset, _ = self.helper_chunk.offset()
            left_helper = "{}.{}[{}]".format(left_marking_var.name, self.helper_chunk.get_attribute_name(), bytes_offset)
            right_helper = "{}.{}[{}]".format(right_marking_var.name, self.helper_chunk.get_attribute_name(), bytes_offset)
        else:
            left_helper = "{}.{}".format(left_marking_var.name, self.helper_chunk.get_attribute_name())
            right_helper = "{}.{}".format(right_marking_var.name, self.helper_chunk.get_attribute_name())
        left = "{}.{}".format(left_marking_var.name, self.chunk.get_attribute_name())
        right = "{}.{}".format(right_marking_var.name, self.chunk.get_attribute_name())
        typ = self.info.type
        
        if typ.is_Int:
            token_compare = "{} - {}".format(left, right)
        elif typ.is_UserType or typ.is_AnyType:
            token_compare = "{}({}, {})".format(from_neco_lib("__neco_compare__"), left, right)
        else:
            raise NotImplementedError


        if self.helper_chunk.packed:
            mask = int(self.helper_chunk.mask())
            expr = "{tc} if {lh} & {mask} and {rh} & {mask} else (1 if {lh} & {mask} else -1)".format(tc=token_compare,
                                                                                                      lh=left_helper,
                                                                                                      rh=right_helper,
                                                                                                      mask=mask)
        else:
            expr = "{tc} if {lh} > 0 and {rh} > 0 else (1 if {lh} > 0 else -1)".format(tc=token_compare,
                                                                                       lh=left_helper,
                                                                                       rh=right_helper)
        return cyast.E(expr)

    def not_empty_expr(self, env, marking_var):
        if self.helper_chunk.packed:
            mask = int(self.helper_chunk.mask())
            attr = self.helper_chunk.get_attribute_name()
            byte_offset, _ = self.helper_chunk.offset()
            return cyast.E('{object}.{attribute}[{byte_offset}] & {mask}'.format(object=marking_var.name,
                                                                                  attribute=attr,
                                                                                  byte_offset=byte_offset,
                                                                                  mask=mask))
        else:
            return cyast.E("{}.{} > 0".format(marking_var.name, self.helper_chunk.get_attribute_name()))

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    def remove_token_stmt(self, env, token_expr, compiled_token, marking_var):
        # one safe place, if we remove something it cannot be empty
        if self.helper_chunk.packed:
            # must be full before remove
            mask = int(self.helper_chunk.mask())
            attr = self.helper_chunk.get_attribute_name()
            byte_offset, _ = self.helper_chunk.offset()
            return cyast.E('{object}.{attribute}[{byte_offset}] ^= {mask}'.format(object=marking_var.name,
                                                                                  attribute=attr,
                                                                                  byte_offset=byte_offset,
                                                                                  mask=mask))

        return [ cyast.E("{}.{} = 0".format(marking_var.name, self.helper_chunk.get_attribute_name())),
                 cyast.Comment('remove : ' + self.helper_chunk.hint) ]

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        if self.helper_chunk.packed:
            # must be empty before add
            mask = int(self.helper_chunk.mask())
            attr = self.helper_chunk.get_attribute_name()
            byte_offset, _ = self.helper_chunk.offset()
            helper_expr = cyast.E('{object}.{attribute}[{byte_offset}] |= {mask}'.format(object=marking_var.name,
                                                                                         attribute=attr,
                                                                                         byte_offset=byte_offset,
                                                                                         mask=mask))
        else:
            helper_expr = cyast.E("{}.{} = 1".format(marking_var.name, self.helper_chunk.get_attribute_name()))

        assign = cyast.Assign(targets=[cyast.E("{}.{}".format(marking_var.name, 
                                                              self.chunk.get_attribute_name()))],
                              value=compiled_token)
        return [helper_expr,
                cyast.Comment(self.helper_chunk.hint), 
                assign,
                cyast.Comment(self.chunk.hint)]


    def token_expr(self, env, token):
        return cyast.E(repr(token))

    def light_copy_stmt(self, env, dst_marking_var, src_marking_var):
        helper_attr = self.helper_chunk.get_attribute_name()
        attr = self.chunk.get_attribute_name()

        dst = dst_marking_var.name
        src = src_marking_var.name

        # do not assign helper if packed
        if self.helper_chunk.packed:
            assign_helper = []
            comment_helper = []
        else:
            assign_helper = cyast.E("{}.{} = {}.{}".format(dst, helper_attr, src, helper_attr))
            comment_helper = cyast.Comment(self.helper_chunk.hint)

        copy_data = cyast.E("{}.{} = {}.{}".format(dst, attr, src, attr))
        comment_data = cyast.Comment(self.chunk.hint)
        return [ assign_helper, comment_helper, copy_data, comment_data ]
 
    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        helper_attr = self.helper_chunk.get_attribute_name()
        attr = self.chunk.get_attribute_name()

        dst = dst_marking_var.name
        src = src_marking_var.name
        
        if self.helper_chunk.packed:
            assign_helper = []
            comment_helper = []
        else:
            assign_helper = cyast.E("{}.{} = {}.{}".format(dst, helper_attr, src, helper_attr))
            comment_helper = cyast.Comment(self.helper_chunk.hint)

        if self.info.type in [ TypeInfo.get('BlackToken'),
                               TypeInfo.get('Int') ]:
            copy_data = cyast.E("{}.{} = {}.{}".format(dst, attr, dst, attr))
        else:
            copy_data = cyast.E("{}.{} = {}.{}.copy()".format(dst, attr, dst, attr))
        comment_data = cyast.Comment(self.chunk.hint)

        return [ assign_helper, comment_helper, copy_data, comment_data ]

    def dump_expr(self, env, marking_var):
        place_expr = "{}.{}".format(marking_var.name, self.chunk.get_attribute_name())

        if self.helper_chunk.packed:
            mask = int(self.helper_chunk.mask())
            bytes_offset, _ = self.helper_chunk.offset()
            helper_expr = "{}.{}[{}] & {}".format(marking_var.name,
                                              self.helper_chunk.get_attribute_name(),
                                              bytes_offset,
                                              mask)
        else:
            helper_expr = "{}.{}".format(marking_var.name, self.helper_chunk.get_attribute_name())
        
        return cyast.E("'[' + dump({}) + ']' if {} else '[]'".format(place_expr, helper_expr))

    def enumerate(self, env, marking_var, token_var, compiled_body):
        getnode = cyast.E("{} = {}.{}".format(token_var.name, marking_var.name, self.chunk.get_attribute_name()))
        ifnode = cyast.Builder.If(test=self.not_empty_expr(env, marking_var=marking_var),
                                  body=[ getnode, compiled_body ])
        return [ cyast.to_ast(ifnode) ]

################################################################################

class BTPlaceType(coretypes.BTPlaceType, CythonPlaceType):
    """ Python black token place type implementation.

    @attention: Using this place type without the BTTokenEnumerator may introduce inconsistency.
    """

    def __init__(self, place_info, marking_type, packed):
        coretypes.BTPlaceType.__init__(self,
                                       place_info=place_info,
                                       marking_type=marking_type,
                                       type=TypeInfo.get('Short'),
                                       token_type=TypeInfo.get('Short'))

        if packed:
            cython_type = TypeInfo.get('Bool')
            packed=True
        else:
            cython_type = TypeInfo.get('Short')
            packed=False

        self.chunk = marking_type.chunk_manager.new_chunk(marking_type.id_provider.get(self),
                                                          cython_type,
                                                          packed=packed)

        self.chunk.hint = "{} - {!s}".format(place_info.name, place_info.type)
        self.info = place_info
        self.marking_type = marking_type

    def delete_stmt(self, env, marking_var):
        return []

    def attribute_expr(self, env, marking_var):
        return cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))

    def hash_expr(self, env, marking_var):
        return cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))

    def eq_expr(self, env, left, right):
        return cyast.Compare(left=left,
                             ops=[cyast.Eq()],
                             comparators=[right])

    def compare_expr(self, env, left_marking_var, right_marking_var):
        attribute = self.chunk.get_attribute_name()
        left = cyast.E('{}.{}'.format(left_marking_var.name, attribute))
        right = cyast.E('{}.{}'.format(right_marking_var.name, attribute))
        return cyast.BinOp(left=left,
                           op=cyast.Sub(),
                           right=right)

    def new_place_stmt(self, env, marking_var):
        return cyast.Assign(targets=[self.attribute_expr(env, marking_var)],
                            value=cyast.Num(0))

    def not_empty_expr(self, env, marking_var):
        if self.chunk.packed:
            attr_name = self.chunk.get_attribute_name()
            bytes_offset, _ = self.chunk.offset()
            mask = int(self.chunk.mask())
            return cyast.E('{object}.{attribute}[{index}] & {mask}'.format(object=marking_var.name,
                                                                           attribute=attr_name,
                                                                           index=bytes_offset,
                                                                           mask=mask))
        else:
            return cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))

    def dump_expr(self, env, marking_var):
        if self.chunk.packed:
            return cyast.IfExp(test=self.not_empty_expr(env, marking_var),
                               body=cyast.Str('[dot]'),
                               orelse=cyast.Str('[]'))
        else:
            place_expr = cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))
            return cyast.BinOp(left=cyast.Str('['),
                               op=cyast.Add(),
                               right=cyast.BinOp(left=cyast.Call(func=cyast.E("', '.join"),
                                                                 args=[cyast.BinOp(left=cyast.List([cyast.Str('dot')]),
                                                                                   op=cyast.Mult(),
                                                                                   right=place_expr)]),
                                                 op=cyast.Add(),
                                                 right=cyast.Str(']')))

    def iterable_expr(self, env, marking_var):
        if self.chunk.packed:
            raise NotImplementedError
        else:
            place_expr = cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))
            return cyast.Call(func=cyast.Name('range'),
                              args=[ cyast.Num(0), place_expr ])

    def remove_token_stmt(self, env, token_expr, compiled_token, marking_var):
        if self.chunk.packed:
            # 1 bit only, should be 1, just reset it
            mask = int(self.chunk.mask())
            attr = self.chunk.get_attribute_name()
            byte_offset, _ = self.chunk.offset()
            return cyast.E('{object}.{attribute}[{byte_offset}] ^= {mask}'.format(object=marking_var.name,
                                                                                  attribute=attr,
                                                                                  byte_offset=byte_offset,
                                                                                  mask=mask))

        else:
            place_expr = cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))
            return cyast.AugAssign(target=place_expr,
                                   op=cyast.Sub(),
                                   value=cyast.Num(1))

    def add_token_stmt(self, env, token_expr, compiled_token, marking_var):
        if self.chunk.packed:
            # 1 bit only, should be 1, just reset it
            mask = int(self.chunk.mask())
            attr = self.chunk.get_attribute_name()
            byte_offset, _ = self.chunk.offset()
            return cyast.E('{object}.{attribute}[{byte_offset}] ^= {mask}'.format(object=marking_var.name,
                                                                                  attribute=attr,
                                                                                  byte_offset=byte_offset,
                                                                                  mask=mask))
        else:
            place_expr = cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))
            return cyast.AugAssign(target=place_expr,
                                   op=cyast.Add(),
                                   value=cyast.Num(1))

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        if self.chunk.packed:
            raise NotImplementedError
        else:
            attr_name = self.chunk.get_attribute_name()
            return cyast.E('{}.{} = {}.{}'.format(dst_marking_var.name, attr_name,
                                                  src_marking_var.name, attr_name))

    def light_copy_stmt(self, env, dst_marking_var, src_marking_var):
        if self.chunk.packed:
            raise NotImplementedError
        else:
            return self.copy_stmt(env, dst_marking_var, src_marking_var)

    def token_expr(self, env, token):
        return cyast.E("dot")

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body):
        return cyast.If(test=self.not_empty_expr(checker_env, marking_var),
                        body=[cyast.Assign(targets=[cyast.Name(loop_var.name)],
                                           value=cyast.E("dot")),
                              body],
                        orelse=[])

    def card_expr(self, env, marking_var):
        return cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))

    def multiset_expr(self, env, marking_var):
        return cyast.Call(func=cyast.E(env.type2str(TypeInfo.get('MultiSet'))),
                          args=[ cyast.Dict([cyast.E('dot')], [cyast.E('{}.{}'.format(marking_var.name,
                                                                                      self.chunk.get_attribute_name()))])])    

    def enumerate(self, env, marking_var, token_var, compiled_body):
        if self.chunk.packed:
            ifnode = cyast.Builder.If(test=self.not_empty_expr(env=env, marking_var=marking_var),
                                      body=[ compiled_body ])
            return [ ifnode ]
        else:
            place_expr = cyast.E('{}.{}'.format(marking_var.name, self.chunk.get_attribute_name()))
            ifnode = cyast.Builder.If(test=cyast.Builder.Compare(left=place_expr,
                                                                 ops=[ cyast.Gt() ],
                                                                 comparators=[ cyast.Num(n=0) ]),
                                      body=[ compiled_body ])
            return [ ifnode ]

################################################################################
#
################################################################################

@not_revelant
@packed_place
class FlowPlaceType(coretypes.PlaceType, CythonPlaceType):

    def __init__(self, place_info, marking_type):
        self._counter = 0
        self._places = {}
        self._helpers = {}
        coretypes.PlaceType.__init__(self,
                                     place_info=place_info,
                                     marking_type=marking_type,
                                     type=TypeInfo.get('UnsignedInt'),
                                     token_type=TypeInfo.get('UnsignedInt'))

        # this chunk will be updated when adding places
        self.chunk = marking_type.chunk_manager.new_chunk(marking_type.id_provider.get(self),
                                                 TypeInfo.get('Bool'),
                                                 packed=True)
    @property
    def max(self):
        assert(self._counter != 0)
        return self._counter - 1

    @property
    def needed_bits(self):
        return int(math.ceil(math.log(self._counter, 2)))

    @should_not_be_called
    def new_place_expr(self, env): pass

    @should_not_be_called
    def delete_stmt(self, env, marking_var): pass

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    @should_not_be_called
    def remove_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def add_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def copy_expr(self, env, marking_var): pass

    @should_not_be_called
    def light_copy_expr(self, env, marking_var): pass

    def add_place(self, place_info):
        """ Adds a flow control place.

        @param place_info: flow control place to be added
        @type place_info: C{PlaceInfo}
        """
        assert(place_info.flow_control)
        try:
            return self._places[place_info.name]
        except KeyError: 
            helper = FlowPlaceTypeHelper(place_info, self.marking_type, self)
            self._helpers[place_info.name] = helper
            self._counter += 1
            self._places[place_info.name] = self._counter

            bits = int(math.ceil(math.log(self._counter, 2)))
            self.chunk.bits = bits if bits > 0 else 1

            return helper

    def get_helper(self, place_info):
        return self._helpers[place_info.name]

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        value = self._places[place_info.name]
        byte_offset, bit_offset = self.chunk.offset()
        mask = int(Mask.from_int(value, self.chunk.bits) << bit_offset)
        attr_name = self.chunk.get_attribute_name()

        if current_flow:
            return cyast.E("{} == {}".format(current_flow.name,
                                             mask))
        else:
            return cyast.E("{}.{}[{}] == {}".format(marking_var.name,
                                                attr_name,
                                                byte_offset,
                                                mask))
        

    def gen_update_flow(self, env, marking_var, place_info):
        """ Get an ast representing the flow update.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        
        value = self._places[place_info.name]
        byte_offset, bit_offset = self.chunk.offset()
        chunk_mask = int(~self.chunk.mask())
        value_mask = int(Mask.from_int(value, self.chunk.bits) << bit_offset)        
        attr_name = self.chunk.get_attribute_name()
        
        comment = cyast.Builder.Comment("mask: {mask:#0{anw}b} vmask:{vmask:#0{anw}b} - place:{place}"
                                        .format(mask=chunk_mask, vmask=value_mask, anw=10, place=place_info.name))
        
        return [ cyast.E("{obj}.{attr}[{i}] = ({obj}.{attr}[{i}] & {chunk_mask}) | {value}".format(obj=marking_var.name,
                                                  attr=attr_name,
                                                  i=byte_offset,
                                                  value=value_mask,
                                                  chunk_mask=chunk_mask)),
                comment ]
#        
#        return [ self.pack.gen_set(env = env,
#                                   marking_var = marking_var,
#                                   place_type = self,
#                                   integer = self._places[place_info.name]) ]

    def gen_read_flow(self, env, marking_var, place_info):
        
        value = self._places[place_info.name]
        byte_offset, bit_offset = self.chunk.offset()
        mask = int(self.chunk.mask())
        attr_name = self.chunk.get_attribute_name()
        return cyast.E("{}.{}[{}] & {}".format(marking_var.name,
                                                 attr_name,
                                                 byte_offset,
                                                 mask))
        
#        return self.pack.gen_get_place(env = env,
#                                       marking_var = marking_var,
#                                       place_type = self)

    def dump_expr(self, env, marking_var, place_info):                
        byte_offset, bit_offset = self.chunk.offset()
        mask = int(self.chunk.mask())
        for (place_name, next_flow) in self._places.iteritems():
            if place_name == place_info.name:
                next_flow_value = Mask.from_int(next_flow, self.chunk.bits) # todo offset !
                next_flow_value = int(next_flow_value << bit_offset)
                print "next flow mask ", bin(next_flow_value) 
                attr_name = self.chunk.get_attribute_name()
                print "{}.{}[{}] & {} == {}  ie. {} {}".format(marking_var.name,
                                                               attr_name,
                                                               byte_offset,
                                                               int(mask),
                                                               int(next_flow_value),
                                                               bin(mask),
                                                               bin(next_flow_value))
                
                check = cyast.E("{}.{}[{}] & {} == {}".format(marking_var.name,
                                                              attr_name,
                                                              byte_offset,
                                                              int(mask),
                                                              int(next_flow_value)))
                
                return cyast.IfExp(test=check,
                                   body=cyast.Str('[dot]'),
                                   orelse=cyast.Str('[]'))
        assert(False)

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body, place_info):
        for (place_name, next_flow) in self._places.iteritems():
            if place_name == place_info.name:
                mask = int(self.pack.field_compatible_mask(self.info, next_flow))
                check = cyast.Builder.EqCompare(self.place_expr(checker_env, marking_var), cyast.E(mask))
                return cyast.If(test=check,
                                body=[ cyast.Assign(targets=[cyast.Name(loop_var.name)],
                                                    values=cyast.E('dot')),
                                       body ],
                                orelse=[])
        assert(False)

@helper_place_type
class FlowPlaceTypeHelper(coretypes.PlaceType, CythonPlaceType):

    def __init__(self, place_info, marking_type, flow_place_type):
        self.flow_place_type = flow_place_type
        coretypes.PlaceType.__init__(self,
                                     place_info=place_info,
                                     marking_type=marking_type,
                                     type=TypeInfo.UnsignedInt,
                                     token_type=TypeInfo.UnsignedInt)

    def get_attribute_name(self):
        return self.flow_place_type.chunk.get_attribute_name()
    
    @should_not_be_called
    def new_place_expr (self, env): pass

    @should_not_be_called
    def delete_stmt(self, env, marking_var): pass

    @should_not_be_called
    def iterable_expr(self, env, marking_var): pass

    @should_not_be_called
    def remove_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def add_token_stmt(self, *args, **kwargs): pass

    @should_not_be_called
    def copy_expr(self, env, marking_var): pass

    @should_not_be_called
    def light_copy_expr(self, env, marking_var): pass

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        return self.flow_place_type.gen_check_flow(env, marking_var, place_info, current_flow)

        mask = int(self.pack.field_compatible_mask(self.info, next_flow))
        return cyast.Builder.EqCompare(current_flow, cyast.E(mask))

    def gen_update_flow(self, env, marking_var, place_info):
        """ Get an ast representing the flow update.

        @param place_info: place requesting flow control.
        @type place_info: C{PlaceInfo}
        """
        return self.flow_place_type.gen_update_flow(env, marking_var, place_info)

    def gen_read_flow(self, env, marking_var):
        return self.flow_place_type.gen_read_flow(env=env,
                                                  marking_var=marking_var,
                                                  place_info=self.info)

    def dump_expr(self, env, marking_var):
        return self.flow_place_type.dump_expr(env, marking_var, self.info)

    def enumerate_tokens(self, checker_env, loop_var, marking_var, body):
        return self.flow_place_type.enumerate_tokens(checker_env, loop_var, marking_var, body, self.info)

################################################################################

@not_revelant
class PackedPlaceTypes(object):
    def __init__(self, name, marking_type):
        self.name = name
        self.marking_type = marking_type
        self._bitfield = MaskBitfield(native_width=8)

    @property
    def type(self):
        return TypeInfo.UnsignedChar

    def _id_from_place_info(self, place_info):
        if place_info.flow_control:
            return self.marking_type.id_provider.get(place_info) + "_f"
        elif place_info.one_safe:
            return self.marking_type.id_provider.get(place_info) + "_1s"
        else:
            return self.marking_type.id_provider.get(place_info)

    def native_field_count(self):
        return self._bitfield.native_field_count()

    def get_native_field(self, marking_var, index):
        return cyast.Subscript(cyast.Attribute(cyast.Name(marking_var.name),
                                               attr=self.name),
                               slice=cyast.Index(cyast.Num(index)))


    def get_field_native_offset(self, place_type):
        return self._bitfield.get_field_native_offset(self._id_from_place_info(place_type.info))

    def add_place(self, place_info, bits):
        self._bitfield.add_field(self._id_from_place_info(place_info), bits)

    def get_fields(self):
        for field in self._bitfield.get_fields():
            yield field

    def field_compatible_mask(self, place_info, integer):
        return self._bitfield.get_field_compatible_mask(self._id_from_place_info(place_info), integer)


    def gen_initialise(self, env, marking_var):
        l = []
        for index in range(0, self.native_field_count()):
            l.append(cyast.Assign(targets=[cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                                  attr=self.name),
                                                            slice=cyast.Index(cyast.Num(index)))],
                                   value=cyast.Num(0)))
        return cyast.to_ast(l)

    def gen_get_place(self, env, marking_var, place_type):
        place_info = place_type.info
        offset = self._bitfield.get_field_native_offset(self._id_from_place_info(place_info))
        mask = int(~self._bitfield.get_field_mask(self._id_from_place_info(place_info)))
        return cyast.BinOp(left=cyast.Subscript(cyast.Attribute(cyast.Name(marking_var.name),
                                                                attr=self.name),
                                                slice=cyast.Index(cyast.Num(offset))),
                           op=cyast.BitAnd(),
                           right=cyast.E(mask))

    def gen_remove_bit(self, env, marking_var, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = cyast.AugAssign(target=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                         attr=self.name),
                                                   slice=cyast.Index(cyast.Num(offset))),
                            op=cyast.BitXor(),
                            value=cyast.Num(value))
        # e = E(marking_name).attr(self.name).subscript(index=offset).xor_assign(E(value))
        comment = cyast.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value,
                                                                                anw=(self._bitfield.native_width + 2),
                                                                                place=place_type.info.name))
        return [ e, comment ]

    def gen_set_bit(self, env, marking_var, place_type):
        field_name = self._id_from_place_info(place_type.info)
        value = int(self._bitfield.get_field_compatible_mask(field_name, 1))
        offset = self._bitfield.get_field_native_offset(field_name)
        e = cyast.AugAssign(target=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                         attr=self.name),
                                                   slice=cyast.Index(cyast.Num(offset))),
                            op=cyast.BitOr(),
                            value=cyast.Num(value))
        #e = E(marking_name).attr(self.name).subscript(index=str(offset)).or_assign(E(value))
        comment = cyast.Builder.Comment("vmask:{vmask:#0{anw}b} - place:{place}".format(vmask=value, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def gen_set(self, env, marking_var, place_type, integer):
        field = self._id_from_place_info(place_type.info)
        mask = int(self._bitfield.get_field_mask(field))
        vmask = int(self._bitfield.get_field_compatible_mask(field, integer))
        offset = self._bitfield.get_field_native_offset(field)
        #right  = E(marking_name).attr(self.name).subscript(index=str(offset)).bit_and(E(mask)).bit_or(E(vmask))
        right = cyast.BinOp(left=cyast.BinOp(left=cyast.Subscript(value=cyast.Attribute(value=cyast.Name(marking_var.name),
                                                                                         attr=self.name),
                                                                   slice=cyast.Index(cyast.Num(offset))),
                                              op=cyast.BitAnd(),
                                              right=cyast.E(mask)),
                             op=cyast.BitOr(),
                             right=cyast.E(vmask))

        #e = E(marking_name).attr(self.name).subscript(index=str(offset)).assign(right)
        e = cyast.Assign(targets=[cyast.Subscript(value=cyast.Attribute(cyast.Name(marking_var.name),
                                                                        attr=self.name),
                                                  slice=cyast.Index(cyast.Num(offset)))],
                         value=right)
        comment = cyast.Builder.Comment("mask: {mask:#0{anw}b} vmask:{vmask:#0{anw}b} - place:{place}"
                                        .format(mask=mask, vmask=vmask, anw=(self._bitfield.native_width + 2), place=place_type.info.name))
        return [ e, comment ]

    def copy_expr(self, env, src_marking_var, dst_marking_var):
        l = []
        for index in range(0, self.native_field_count()):
            right = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(src_marking_var.name),
                                                          attr=self.name),
                                    slice=cyast.Index(cyast.Num(index)))
            left = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(dst_marking_var.name),
                                                         attr=self.name),
                                   slice=cyast.Index(cyast.Num(index)))
            l.append(cyast.Assign(targets=[left],
                                   value=right))
        return l


    def gen_tests(self, left_marking_var, right_marking_var):
        """
        """
        tests = []
        for index in range(0, self.native_field_count()):
            left = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(left_marking_var.name),
                                                         attr=self.name),
                                   slice=cyast.Index(cyast.Num(index)))
            right = cyast.Subscript(value=cyast.Attribute(value=cyast.Name(right_marking_var.name),
                                                          attr=self.name),
                                    slice=cyast.Index(cyast.Num(index)))
            tests.append((left, right,))
        return tests
