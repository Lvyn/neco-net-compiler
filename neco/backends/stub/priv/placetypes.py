from neco.core.info import TypeInfo, VariableProvider
from neco.utils import should_not_be_called
import neco.core.nettypes as coretypes

################################################################################

class ObjectPlaceType(coretypes.ObjectPlaceType):
    """ Stub implementation of the fallback place type. """

    allow_pids = False

    def __init__(self, place_info, marking_type):
        coretypes.ObjectPlaceType.__init__(self,
                                           place_info=place_info,
                                           marking_type=marking_type,
                                           type_info=TypeInfo.get('MultiSet'),
                                           token_type=place_info.type)
        # self.field = marking_type.create_field(self, place_info.type)

    def new_place_stmt(self, env, dst_marking_var):
        """ AST of a new place expression (initialization assignment) 
        
        destination place: dst_marking_var
        """
        raise NotImplementedError

    def size_expr(self, env, marking_var):
        """ AST of place size expression.

        marking: marking_var
        """
        raise NotImplementedError

    def iterable_expr(self, env, marking_var):
        """ AST of an iterable expression.

        (may not be required, depends on netir.TokenEnumeration implementation)

        marking: marking_var
        """
        raise NotImplementedError

    def remove_token_stmt(self, env, compiled_token, marking_var, *args):
        """ AST of token removal from a place.

        token:   compiled_token
        marking: marking_var
        """
        raise NotImplementedError

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        """ AST of token addition to a place

        token:   compiled_token
        marking: marking_var
        """
        raise NotImplementedError

    def token_expr(self, env, value):
        """ AST expression of a token of value 'value' that is consistent with this type. 
        """
        raise NotImplementedError

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        """ AST expression of a copy of the place.

        destination marking: dst_marking_var
        source marking:      src_marking_var
        """
        raise NotImplementedError

    def light_copy_stmt(self, env, dst_marking_var, src_marking_var):
        """ AST expression of a light copy of the place (data sharing).

        destination marking: dst_marking_var
        source marking:      src_marking_var
        """
        raise NotImplementedError

    def clear_stmt(self, env, marking_var):
        """ AST expression that removes all tokens form a place. 

        marking: marking_var
        """
        raise NotImplementedError

    def assign_multiset_stmt(self, env, token_var, marking_var):
        """ AST expression that replaces place content with a multiset of tokens.

        multiset expression: token_var
        marking:             marking_var
        """
        raise NotImplementedError

    def not_empty_expr(self, env, marking_var):
        """ AST expression that check if a place is empty. 

        marking: marking_var
        """
        raise NotImplementedError

    def add_items_stmt(self, env, multiset, marking_var):
        """ AST expression that adds tokens form a multiset to a place.

        multiset expression: multiset
        marking:             marking_var
        """
        raise NotImplementedError

    def dump_expr(self, env, marking_var):
        """ AST expression that returns a string representation of a place.

        marking: marking_var
        """
        raise NotImplementedError
        
    def enumerate(self, env, marking_var, token_var, compiled_body):
        """ AST expression that enumerated tokens from a place. 

        token variable: token_var
        marking:        marking_var
        body:           compiled_body
        """
        raise NotImplementedError
    
    
    def update_pids_stmt(self, env, marking_var, new_pid_dict_var):
        """ PID specific.
        """
        raise NotImplementedError

    def pid_free_compare_expr(self, env, left_marking_var, right_marking_var, ignore):
        """ PID specific 
        """
        raise NotImplementedError
    
    def pid_free_hash_expr(self, env, marking_var, ignore):
        """ PID specific 
        """
        raise NotImplementedError
    
    def extract_pids(self, env, marking_var, dict_var):
        """ PID specific 
        """
        raise NotImplementedError
       
################################################################################

class BTPlaceType(coretypes.BTPlaceType):
    """ black token place type implementation stub.
    
    \see ObjectPlaceType for documentation.
    """

    def __init__(self, place_info, marking_type):  
        coretypes.BTPlaceType.__init__(self,
                                       place_info=place_info,
                                       marking_type=marking_type,
                                       type_info=TypeInfo.get('Int'),
                                       token_type=TypeInfo.get('Int'))

        # assume that there is a create_field method in marking that
        # reserves space in the marking strucutre
        self.field = marking_type.create_field(self, TypeInfo.get('Int'))

    def new_place_stmt(self, env, marking_var):
        # return AST expression for "{} = 0".format(self.field.access_from(marking_var))
        raise NotImplementedError

    def iterable_expr(self, env, marking_var): 
        # all black tokens are equal so use just one token
        raise NotImplementedError

    def remove_token_stmt(self, env, compiled_token, marking_var, *args):
        # "{} -= 1".format(self.field.access_from(marking_var))
        raise NotImplementedError

    def add_token_stmt(self, env, compiled_token, marking_var, *args):
        # "{} += 1".format(self.field.access_from(marking_var))
        raise NotImplementedError

    def copy_stmt(self, env, dst_marking_var, src_marking_var):
        # just copy the value from one place to the other
        # "{} = {}".format(self.field.access_from(dst_marking_var),
        #                  self.field.access_from(src_marking_var))
        raise NotImplementedError

    def token_expr(self, env, value):
        # token expression for a black token is always black token so return 1
        raise NotImplementedError
        

    def dump_expr(self, env, marking_var):
        # just return a string of dots
        raise NotImplementedError

    def enumerate(self, env, marking_var, token_var, compiled_body):
        # all black tokens are the same so just test that the place is
        # not empty an execute the body
        raise NotImplementedError

################################################################################
# EOF
################################################################################
