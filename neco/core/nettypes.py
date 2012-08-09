""" Module providing type structures.
"""

import types
from abc import abstractmethod, ABCMeta
import snakes.nets as nets
from neco import utils, config
from info import TypeInfo

################################################################################

def provides_by_index_access(cls):
    cls._by_index_access_ = True
    return cls

def provides_by_index_deletion(cls):
    cls._by_index_deletion_ = True
    return cls

class PlaceType(object):
    """ Common base class for place types.
    """

    __metaclass__ = ABCMeta

    _by_index_access_   = False
    _by_index_deletion_ = False

    def __init__(self, place_info, marking_type, type, token_type):
        """ Initialise the place type.
        """
        self.info = place_info
        self.marking_type = marking_type
        self._type = type
        self._token_type = token_type

        self._by_index_access   = self.__class__._by_index_access_
        self._by_index_deletion = self.__class__._by_index_deletion_

    def one_safe(self):
        return self.info.one_safe

    @property
    def type(self):
        return self._type

    @property
    def token_type(self):
        return self._token_type

    @property
    def process_name(self):
        return self.info.process_name

    @property
    def provides_by_index_access(self):
        return self._by_index_access

    @property
    def provides_by_index_deletion(self):
        return self._by_index_deletion

    def disable_by_index_access(self):
        self._by_index_access = False

    def disable_by_index_deletion(self):
        self._by_index_deletion = False


################################################################################

class ObjectPlaceType(PlaceType):
    """ Fallback place type.
    """

    def __init__(self, place_info, marking_type, type, token_type):
        PlaceType.__init__(self,
                           place_info = place_info,
                           marking_type = marking_type,
                           type = type,
                           token_type = token_type)

################################################################################

class MarkingTypeMethodGenerator(object):

    def generate(self, env):
        raise NotImplementedError

################################################################################

class MarkingType(object):
    """ Common base class for all marking types.
    """
    __metaclass__ = ABCMeta

    def __init__(self, type, container_type):
        """ Create a new marking type providing a type name.

        @param type_name: marking structure type name.
        @type type_name: C{str}
        """

        self._type = type
        self._contaner_type = container_type
        self._method_generators = []
        
        self.place_types = dict()

        self._places = set()
        self._flow_control_places = set()
        self._one_safe_places = set()
        
        self._optimize = False
        self._control_flow_elimination = False

    def add_method_generator(self, method_generator):
        self._method_generators.append(method_generator)

    @property
    def method_generators(self):
        return self._method_generators

    def set_control_flow_elimination(self, enabled):
        self._control_flow_elimination = enabled
        
    @property
    def control_flow_elimination(self):
        return self._control_flow_elimination

    def set_optimize(self, enabled):
        self._optimize = enabled
        
    @property
    def optimize(self):
        return self._optimize

    def generate_methods(self, env):
        api = []
        for method in self._method_generators:
            api.append( method.generate(env) )
        return api

    @property
    def type(self):
        return self._type

    @property
    def container_type(self):
        return self._contaner_type

    @property
    def places(self):
        return self._places

    @property
    def flow_control_places(self):
        return self._flow_control_places

    @property
    def one_safe_places(self):
        return self._one_safe_places

    def get_place_type_by_name(self, name):
        """ Retrieve a place by name.

        @param name: place name.
        @type name: C{str}
        @return: place type.
        @rtype: C{PlaceType}
        """
        return self.place_types[name]

    def add(self, place_info):
        """ Add a place info instance to marking type.

        The place info will be added into a set depending on its properties.
        A flow control place will be added to C{self.flow_control_places},
        a one bounded place will be added to C{self.one_safe_places}, other
        places will be addeed to C{self.places}.

        """
        if self.control_flow_elimination and place_info.flow_control:
            self._flow_control_places.add( place_info )
        elif place_info.one_safe:
            self._one_safe_places.add( place_info )
        else:
            self._places.add( place_info )


    @abstractmethod
    def gen_types(self):
        """ Create place types from place info datas.
        """
        pass

    @abstractmethod
    def generate_api(self, *args):
        """ Produce all the structures and functions needed to manage the marking.

        @return: marking structure ast (backend specific).
        @rtype: C{ast} (backend specific).
        """
        pass

    @abstractmethod
    def new_marking_expr(self, marking_name, *args):
        """ Build an expression producing a new marking.
        """
        pass

################################################################################

class MarkingSetType(object):
    """ Common base class for marking set types.
    """

    __metaclass__ = ABCMeta

    def __init__(self, marking_type):
        """ Initialise marking set structure

        @param marking_type: marking set type.
        @type marking_type: C{str}
        """
        self.marking_type = marking_type

    @abstractmethod
    def gen_api(self):
        """ Produce all functions provided by the marking set structure.
        """
        pass

    @abstractmethod
    def add_marking_stmt(self, marking_set_name, marking_name):
        """ Produce a add marking function call for the marking set structure.
        """
        pass
    
################################################################################
    
class OneSafePlaceType(PlaceType):
    """ Base class for one safe place types.
    """

    def __init__(self, place_info, marking_type, type, token_type):
        PlaceType.__init__(self,
                           place_info = place_info,
                           marking_type = marking_type,
                           type = type,
                           token_type = token_type)

################################################################################

class BTPlaceType(PlaceType):
    """ Base class for black token place types.
    """

    def __init__(self, place_info, marking_type, type, token_type):
        PlaceType.__init__(self,
                           place_info = place_info,
                           marking_type = marking_type,
                           type = type,
                           token_type = token_type)

################################################################################

class BTOneSafePlaceType(PlaceType):
    """ Base class for one safe black token place types.
    """

    def __init__(self, place_info, marking_type, type, token_type):
        PlaceType.__init__(self,
                           place_info = place_info,
                           marking_type = marking_type,
                           type = type,
                           token_type = token_type)


################################################################################
# EOF
################################################################################

