import inspect
import nettypes
from .. import utils

################################################################################

class FactoryManager(object):
    """ factory manager class
    """

    @classmethod
    def update(cls, instance):
        assert isinstance(instance, FactoryManager)
        cls.__instance__ = instance

    @classmethod
    def instance(cls):
        assert cls.__instance__
        return cls.__instance__

    def __init__(self):
        """ initialise the manager
        """

        placetype_products = []
        markingtype_products = []
        markingsettype_products = []
        for name, obj in inspect.getmembers(nettypes, inspect.isclass):
            if issubclass(obj, nettypes.PlaceType):
                placetype_products.append(obj)
            elif issubclass(obj, nettypes.MarkingType):
                markingtype_products.append(obj)
            elif issubclass(obj, nettypes.MarkingSetType):
                markingsettype_products.append(obj)

        self.placetype_factory = utils.Factory(placetype_products)
        """ core place type factory (abstract types)"""
        self.markingtype_factory = utils.Factory(markingtype_products)
        """ core marking type factory (abstract types)"""
        self.markingsettype_factory = utils.Factory(markingsettype_products)
        """ core marking set type factory (abstract types)"""
        fallback_placetype = "ObjectPlaceType"
        """ fallback place type name """
        self.select_type = lambda type : fallback_placetype
        """ function that selects a place type from a type. """

FactoryManager.__instance__ = None

################################################################################
# EOF
################################################################################

