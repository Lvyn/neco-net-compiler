""" Stub basic marking types. 

This file contains classes used to represent markings and marking sets.

"""

from neco.core.info import TypeInfo, PlaceInfo # information database functions
import neco.core.nettypes as coretypes         # base types to extend
import neco.utils as utils                     # utilities
import priv.placetypes
   
################################################################################

class MarkingType(coretypes.MarkingType):
    """ Marking type implementation.

    This class is responsible of creating adequate place types based on place type information.
    """

    def __init__(self, config):
        coretypes.MarkingType.__init__(self,
                                       TypeInfo.register_type('Marking'), # register marking type
                                       TypeInfo.register_type('set'),     # register making set type
                                       config)
        

        self.id_provider = utils.NameProvider() # helper for new name generation

        # the representation of the marking itself is implementation detail
        # at this level some optimizations may be implemented at place selection level (gen_types)        
    
    def __str__(self):
        """ marking structure as string, helper for debugging. """
        s = []
        s.append('Marking:')
        for name, place_type in self.place_types.iteritems():
            s.append('{} : {}'.format(name, place_type.__class__))
        s.append('End')
        return '\n'.join(s)
    
    def gen_types(self):
        """ Build place types using C{select_type} predicate.

        This function creates all place metatypes that are used for place related AST generation.
        """ 
        
        ################################################################################
        # one safe places optimizations
        ################################################################################
        for place_info in self.one_safe_places:
            # create one safe place type
            place_name = place_info.name

            # \TODO USER CODE
            place_type = priv.placetypes.ObjectPlaceType(place_info, marking_type=self)

            if self.place_types.has_key(place_name):
                raise RuntimeError("{name} place exists".format(name=place_name))
            else:
                self.place_types[place_name] = place_type

        ################################################################################
                
        for place_info in self.places:
            place_name = place_info.name

            if place_info.type.is_BlackToken:                
                place_type = priv.placetypes.BTPlaceType(place_info, marking_type=self)
            elif place_info.type.is_Pid:
                place_type = priv.placetypes.PidPlaceType(place_info, marking_type=self)
            else:
                place_type = priv.placetypes.ObjectPlaceType(place_info, marking_type=self)

            if self.place_types.has_key(place_name):
                raise RuntimeError("{name} place exists".format(name=place_name))
            else:
                self.place_types[place_name] = place_type

    def generate_api(self, env):
        """ AST for API code. 
        
        Expose data structures and functions.
        """
        raise NotImplementedError

    def new_marking_expr(self, env, *args):
        """ AST that creates a new Marking. (may be omitted if netir is enough)
        """
        raise NotImplementedError

    def copy_marking_expr(self, env, marking_var, *args):
        """ AST that copies a marking. (may be omitted if netir is enough)

        marking: marking_var
        """
        raise NotImplementedError

    ################################################################################
    # Flow elimination
    ################################################################################

    def gen_check_flow(self, env, marking_var, place_info, current_flow):
        """ Flow specific. """
        raise NotImplementedError

    def gen_update_flow(self, env, marking_var, place_info):
        """ Flow specific. """
        raise NotImplementedError

    def gen_read_flow(self, env, marking_var, process_name):
        """ Flow specific. """
        raise NotImplementedError

################################################################################

class MarkingSetType(coretypes.MarkingSetType):
    """ implementation of the marking set type. """

    def __init__(self, markingtype):
        coretypes.MarkingSetType.__init__(self, markingtype)

    def gen_api(self, env):
        pass

    def new_marking_set_expr(self, env):
        """ AST that create new marking set. """
        raise NotImplementedError

    def add_marking_stmt(self, env, marking_set, marking):
        """ AST that adds a marking to a marking set. 
        """
        raise NotImplementedError

################################################################################
# EOF
################################################################################
