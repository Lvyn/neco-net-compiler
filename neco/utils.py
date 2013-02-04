""" Utility classes and functions. """

from abc import abstractmethod, ABCMeta
from functools import wraps
from os.path import exists, abspath
from snakes.nets import WordSet
import ast
import sys
import traceback

def flatten_lists(l):
    """ Make a list of lists flat.

    >>> l = [1, 2, 3]
    >>> flatten_lists( l )
    [1, 2, 3]
    >>> l = [[1], [2], [3]]
    >>> flatten_lists( l )
    [1, 2, 3]
    >>> l = [[1, 2], 3]
    >>> flatten_lists( l )
    [1, 2, 3]
    >>> l = [[[1], [2, 3], 4, [[5]]], [6,[7]]]
    >>> flatten_lists( l )
    [1, 2, 3, 4, 5, 6, 7]

    @param l: list.
    @type l: C{list}
    @return flatten list.
    @rtype list.
    """
    new_list = []
    for elt in l:
        if isinstance(elt, list):
            elt = flatten_lists(elt)
            for e in elt:
                new_list.append(e)
        else:
            new_list.append(elt)
    return new_list

class _flatten_ast(ast.NodeTransformer):
    """ Node transformer that flattens lists in an ast.

    [[node1, [Node2], Node3], Node4] -> [node1, Node2, Node3, Node4]

    >>> from ast import *
    >>> tree = []
    >>> _flatten_ast().visit(tree)
    []
    >>> tree = [[], [[42], [[]]], []]
    >>> _flatten_ast().visit(tree)
    [42]
    >>> tree = [Name(id='')]
    >>> [ elt.__class__.__name__ for elt in _flatten_ast().visit(tree) ]
    ['Name']
    >>> tree = [[Name(id=''), [Name(id='')], Name(id='')], Name(id='')]
    >>> [ elt.__class__.__name__ for elt in _flatten_ast().visit(tree) ]
    ['Name', 'Name', 'Name', 'Name']
    >>> tree = [Name(id=''),
    ...         If(test=Name(id='True'), body=[[], []], orelse=[[]])]
    >>> res = _flatten_ast().visit(tree)
    >>> [ elt.__class__.__name__ for elt in res ]
    ['Name', 'If']
    >>> res[1].body, res[1].orelse
    ([], [])
    >>> tree = [Name(id=''),
    ...         If(test=Name(id='True'),
    ...                body=[[],
    ...                      [],
    ...                      If(test=None, body=[[], []], orelse=[]),
    ...                      []],
    ...                orelse=[])]
    >>> res = _flatten_ast().visit(tree)
    >>> [ elt.__class__.__name__ for elt in res[1].body ]
    ['If']
    >>> res[1].body[0].body
    []

    """
    def visit_list(self, node):
        # flatten lists
        new_node = flatten_lists(node)
        # flatten childs
        new_node = [ self.visit(elt) for elt in new_node ]
        return new_node

    def generic_visit(self, node):
        if isinstance(node, ast.AST):
            for field, old_value in ast.iter_fields(node):
                old_value = getattr(node, field, None)
                setattr(node, field, self.visit(old_value))
            return node
        else:
            return node

def flatten_ast(nodes):
    """ Helper function to flatten ast.

    >>> from ast import *
    >>> flatten_ast([])
    []
    >>> flatten_ast([[[], []], []])
    []
    >>> tree = [[Name(id=''), [Name(id='')], Name(id='')], Name(id='')]
    >>> [ elt.__class__.__name__ for elt in flatten_ast(tree) ]
    ['Name', 'Name', 'Name', 'Name']
    >>> tree = [Name(id=''),
    ...         If(test=Name(id='True'), body=[[], []], orelse=[[]])]
    >>> res = flatten_ast(tree)
    >>> [ elt.__class__.__name__ for elt in res ]
    ['Name', 'If']
    >>> res[1].body, res[1].orelse
    ([], [])
    >>> tree = [Name(id=''),
    ...         If(test=Name(id='True'),
    ...                body=[[],
    ...                      [],
    ...                      If(test=None, body=[[], []], orelse=[]),
    ...                      []],
    ...                orelse=[])]
    >>> res = flatten_ast(tree)
    >>> [ elt.__class__.__name__ for elt in res[1].body ]
    ['If']
    >>> res[1].body[0].body
    []
    """
    return _flatten_ast().visit(nodes)


def search_file(filename, paths):
    for path in paths:
        if path[-1] != '/':
            path += '/'
        path = "".join([path, filename])
        if exists(path):
            return abspath(path)

    raise IOError('{} file not found, check search paths'.format(filename))
#
#
# class Factory(object):
#    """ Generic factory class. """
#
#    class Builder(object):
#        """ Class that handles product construction. """
#
#        def __init__(self, product_cls):
#            """ initialise the builder with the product.
#
#            @param product_cls: product class
#            @type product_cls: C{class}
#            """
#            self.product_cls = product_cls
#
#        def __call__(self, factory, *args, **kw):
#            """ builder call method for intuitive use. """
#            return self.product_cls(*args, **kw)
#
#    def __init__(self, products = []):
#        """ initialise a factory from a C{list} or a C{dict} of products """
#        if isinstance(products, list):
#            new_products = {}
#            for product_cls in products:
#                new_products[product_cls] = "new_%s" % product_cls.__name__
#            products = new_products
#
#        for product_cls, method_name in products.iteritems():
#            method = types.MethodType(Factory.Builder(product_cls), self, Factory)
#            setattr(self, method_name, method)
#
#    def new(self, class_name, *args, **kwargs):
#        """ build product by name.
#
#        Calls the new_'class_name' method.
#
#        @param class_name: product class name
#        @type class_name: C{str}
#        @param args: product __init__ function arguments
#        @param kwargs: product __init__ function keyword argmuments
#        """
#        try:
#            function = getattr(self, "new_" + class_name)
#        except AttributeError:
#            raise UnsupportedTypeException(class_name)
#        return function(*args, **kwargs)
#
#    def register(self, product_cls, method_name = ""):
#        """ register a new product.
#
#        Generates a new_`product.__class__` method by default, i.e., if the method_name
#        argument is not given.
#
#        @param product_cls: product class
#        @type product_cls: C{class}
#        @param method_name: generated method name, new_`product.__class__` by default.
#        @type method_name: C{str}
#        """
#        method = types.MethodType(Factory.Builder(product_cls), self, Factory)
#        if method_name == "":
#            method_name = "new_%s" % product_cls.__name__
#        setattr(self, method_name, method)
#
#    def unregister(self, method_name):
#        """ unregister a product by deleting its method.
#
#        @param method_name: method name
#        @type method_name: C{str}
#        """
#        delattr(self, method_name)


################################################################################
# IDProvider
################################################################################

class IDProvider(object):
    """ simple class that provides unique identifiers for objects.
    """

    def __init__(self):
        """ initlalise the provider
        """
        self.next = 0;
        self.assoc = {}

    # def __call__(self, obj):
    #     """ call notation for intuitive use.

    #     returns the id of an object (see L{get} method).

    #     @param obj: object
    #     @type obj: C{object}
    #     @return: object id
    #     @rtype: C{int}
    #     """
    #     return self.get(obj)


    def to_string(self, obj):
        return "'place_" + str(self.get(obj)) + "'"


    def get(self, obj):
        """ get an identifier for an object.

        >>> provider = IDProvider()
        >>> id1 = provider.get("toto")
        >>> id2 = provider.get("tata")
        >>> id1 != id2
        True
        >>> id3 = provider.get("toto")
        >>> id1 == id3
        True

        @param obj: object
        @type obj: C{object}
        @return: object identifier
        @rtype: C{int}
        """
        if (not self.assoc.has_key(obj)):
            identifier = self.next
            self.assoc[obj] = identifier
            self.next += 1;
            return identifier

        return self.assoc[obj]

class StringIDProvider(object):
    """ simple class that provides unique identifiers for objects.
    """

    def __init__(self):
        """ initlalise the provider
        """
        self.wordset = WordSet()
        self.assoc = {}

    def _next(self, obj):
        return self._escape(self.wordset.fresh(True, base = str(obj)))

    def _escape(self, string):
        res = ""
        d = { '.' : 'A',
              ' ' : 'B',
              '(' : 'C',
              ')' : 'D',
              ',' : 'E',
              '=' : 'G',
              '#' : 'H',
              '\'' : 'I' }
        for c in string:
            try:
                c = d[c]
            except:
                pass
            finally:
                res += c
        return res

    def to_string(self, obj):
        return "\"" + self.get(obj) + "\""

    def get(self, obj):
        """ get an identifier for an object.

        >>> provider = IDProvider()
        >>> id1 = provider.get("toto")
        >>> id2 = provider.get("tata")
        >>> id1 != id2
        True
        >>> id3 = provider.get("toto")
        >>> id1 == id3
        True

        @param obj: object
        @type obj: C{object}
        @return: object identifier
        @rtype: C{int}
        """
        try:
            return self.assoc[obj]
        except KeyError:
            new = self._next(obj)
            self.assoc[obj] = new
            return new

class NameProvider(object):
    """ simple class that provides unique identifiers for objects.
    """

    def __init__(self):
        """ initlalise the provider
        """
        self.id = 0;
        self.wordset = set()
        self.assoc = {}

    def _next(self, obj, base):
        self.id += 1
        if base != "":
            return self._escape("_n{}_{}".format(self.id, base))
        else:
            return self._escape("_n{}".format(self.id))

    def _escape(self, string):
        res = ""
        d = { '.' : 'A',
              ' ' : 'B',
              '(' : 'C',
              ')' : 'D',
              ',' : 'E',
              '=' : 'G',
              '#' : 'H',
              '\'' : 'I' }
        for c in string:
            try:
                c = d[c]
            except:
                pass
            finally:
                res += c
        return res

    def to_string(self, obj):
        return "\"" + self.get(obj) + "\""

    def new(self, base = ""):
        return self._next(None, base)

    def set(self, obj, identifier):
        self.assoc[obj] = identifier

    def get(self, obj, base = ""):
        """ get an identifier for an object.

        >>> provider = IDProvider()
        >>> id1 = provider.get("toto")
        >>> id2 = provider.get("tata")
        >>> id1 != id2
        True
        >>> id3 = provider.get("toto")
        >>> id1 == id3
        True

        @param obj: object
        @type obj: C{object}
        @return: object identifier
        @rtype: C{int}
        """
        try:
            return self.assoc[obj]
        except KeyError:
            new = self._next(obj, base)
            self.assoc[obj] = new
            return new

################################################################################
# Decorator
################################################################################

class RegDict(dict):
    """ A simple dict wrapper

    New items need to be registred, any modification on an unregistred item will
    raise a C{KeyError}.

    """
    def __init__(self):
        self._attributes = {}

    def __getitem__(self, key):
        """ Get a field.

        raise C{KeyError} if C{key} is not used.
        """
        return self._attributes[key]

    def __setitem__(self, key, item):
        """ Modify a field.

        raise C{KeyError} if C{key} is not used.
        """
        if not key in self._attributes:
            raise KeyError
        self._attributes[key] = item

    def register(self, key, value):
        """ Register a new field.

        raise C{KeyError} if C{key} is already used.
        """
        if key in self._attributes:
            raise KeyError
        self._attributes[key] = value

################################################################################
# bidict
################################################################################

class multidict(dict):
    def add(self, left, right):
        if self.has_key(left):
            self[left].append(right)
        else:
            self[left] = [ right ]

    def add_many(self, key, elts):
        if not self.has_key(key):
            self[key] = []

        for elt in elts:
            self[key].append(elt)


def _extract_dict(d, key_fun = lambda x: x, value_fun = lambda x : x):
    return [ "{key}: {value}".format(key = key_fun(key), value = value_fun(value))
             for key, value in sorted(d.iteritems()) ]

class bidict(object):
    """ Bidirectional dictionary. """

    def __init__(self, data = {}):
        """ build a bidirectional dictionary from a dictionnary

        @param data: initial elements
        @type data: C{dict}
        """
        self._left_right = {}
        self._right_left = {}

        for left, right in data.iteritems():
            self.add_left(left, right)

    def add_left(self, left, right):
        if self._left_right.has_key(left):
            self._left_right[left].append(right)
        else:
            self._left_right[left] = right

        if self._right_left.has_key(right):
            self._right_left[right].append(left)
        else:
            self._right_left[right] = left

    def add_right(self, right, left):
        self.add_left(left, right)

    def has_left(self, left):
        return self._left_right.has_key(left)

    def has_right(self, right):
        return self._right_left.has_key(right)

    def from_left(self, left):
        if self._left_right.has_key(left):
            return self._left_right[left]
        else:
            return []

    def from_right(self, right):
        if self._right_left.has_key(right):
            return self._right_left[right]
        else:
            return []

    def __str__(self):
        """ Python representation.

        >>> print(bidict({'a' : 1, 'b' : 2, 'c' : 3 }))
        (l2r: {a: 1, b: 2, c: 3}, r2l: {1: a, 2: b, 3: c})

        """

        l2r = ", ".join(_extract_dict(self._left_right))
        r2l = ", ".join(_extract_dict(self._right_left))
        return "(l2r: {%s}, r2l: {%s})" % (l2r, r2l)

    def __repr__(self):
        """ Python representation.

        >>> print(repr(bidict({'a': 1, 'b': 2, 'c': 3 })))
        bidict({'a': 1, 'b': 2, 'c': 3})

        @return: python representation.
        @rtype: C{str}
        """
        return "bidict({%s})" % ", ".join(_extract_dict(self._left_right, repr, repr))

class TypeMatch(object):
    """ Class used to implement type matching. """

    __metaclass__ = ABCMeta

    def match(self, obj):
        """ Call C{match_<obj.__class__.__name__>} method, or C{default} if
        not available.

        @param obj: matched object.
        """
        method = "match_" + obj.__class__.__name__
        try:
            attr = getattr(self, method)
        except AttributeError:
            attr = self.default
        return attr(obj)

    @abstractmethod
    def default(self, obj):
        """ Default type match case.

        @param obj: matched object.
        """
        pass

def indent(n):
    """ insert tabs

    @param n: number of tabs
    @type n: C{int}
    """
    return "\t" * n


# def Enum(*names):
#    """ Enumerations.

#    --- Days of week ---
#    >>> Days = Enum('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
#    >>> print Days
#    enum (Mo, Tu, We, Th, Fr, Sa, Su)
#    >>> print (Days.Mo, Days.Fr)
#    (Mo, Fr)
#    >>> print Days.Mo < Days.Fr
#    True
#    >>> print list(Days)
#    [Mo, Tu, We, Th, Fr, Sa, Su]

#    >>> for each in Days:
#    ...     print 'Day:', each
#    Day: Mo
#    Day: Tu
#    Day: We
#    Day: Th
#    Day: Fr
#    Day: Sa
#    Day: Su

#    --- Yes/No ---
#    >>> Confirmation = Enum('No', 'Yes')
#    >>> answer = Confirmation.No
#    >>> print 'Your answer is not', ~answer
#    Your answer is not Yes
#    """

#    assert names, "Empty enums are not supported"

#    class EnumClass(object):
#       __slots__ = names
#       def __iter__(self):        return iter(constants)
#       def __len__(self):         return len(constants)
#       def __getitem__(self, i):  return constants[i]
#       def __repr__(self):        return 'Enum' + str(names)
#       def __str__(self):         return 'enum ' + str(constants)

#    class EnumValue(object):
#       __slots__ = ('__value')
#       def __init__(self, value): self.__value = value
#       Value = property(lambda self: self.__value)
#       EnumType = property(lambda self: EnumType)
#       def __hash__(self):        return hash(self.__value)
#       def __cmp__(self, other):
#          # C fans might want to remove the following assertion
#          # to make all enums comparable by ordinal value {;))
#          assert self.EnumType is other.EnumType, "Only values from the same enum are comparable"
#          return cmp(self.__value, other.__value)
#       def __invert__(self):      return constants[maximum - self.__value]
#       def __nonzero__(self):     return bool(self.__value)
#       def __repr__(self):        return str(names[self.__value])
#       def __getstate__(self):
#           return { '__value' : self.__value }

#    maximum = len(names) - 1
#    constants = [None] * len(names)
#    for i, each in enumerate(names):
#       val = EnumValue(i)
#       setattr(EnumClass, each, val)
#       constants[i] = val
#    constants = tuple(constants)
#    EnumType = EnumClass()
#    return EnumType


class EnumValue(object):
    # __slots__ = ('__value')
    def __init__(self, name, value):
        self.__name = name
        self.__value = value
    Value = property(lambda self: self.__value)
    # EnumType = property(lambda self: EnumType)
    def __hash__(self):        return hash(self.__value)
    def __cmp__(self, other):
        return cmp(self.__value, other.__value)
    def __nonzero__(self):     return bool(self.__value)
    def __repr__(self):        return str(self.__name)

class EnumClass(object):
    # __slots__ = ('names', 'constants')
    def __init__(self, names):
        self.names = names
        constants = [None] * len(names)
        for i, name in enumerate(names):
            val = EnumValue(name, i)
            setattr(self, name, val)
            constants[i] = val
        self.constants = tuple(constants)

    def __iter__(self):        return iter(self.constants)
    def __len__(self):         return len(self.names)
    def __getitem__(self, i):  return self.names[i]
    def __repr__(self):        return 'Enum' + str(self.names)
    def __str__(self):         return 'enum ' + str(self.constants)

def Enum(*names):
    """ Enumerations.

    --- Days of week ---
    >>> Days = Enum('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
    >>> print Days
    enum (Mo, Tu, We, Th, Fr, Sa, Su)
    >>> print (Days.Mo, Days.Fr)
    (Mo, Fr)
    >>> print Days.Mo < Days.Fr
    True
    >>> print list(Days)
    [Mo, Tu, We, Th, Fr, Sa, Su]

    >>> for each in Days:
    ...     print 'Day:', each
    Day: Mo
    Day: Tu
    Day: We
    Day: Th
    Day: Fr
    Day: Sa
    Day: Su
    """
    return EnumClass(names)

################################################################################

def should_not_be_called(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        msg = ("{function_name} Should not be called, supports by index access"
               .format(function_name = function.__name__))
        raise RuntimeError(msg)
    return wrapper

################################################################################

def todo(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        msg = ("TODO: {function_name}"
               .format(function_name = function.__name__))
        raise RuntimeError(msg)
    return wrapper

################################################################################

class Matcher(object):

    def match(self, node):
        """ Match a node. """
        method = 'case_' + node.__class__.__name__
        matcher = getattr(self, method, self.no_match_found)
        return matcher(node)

    def no_match_found(self, node):
        """Called if no explicit match function exists."""
        class NoMatchFound(Exception):
            def __init__(self, string):
                self._str = string
            def __str__(self):
                return self._str
        raise NoMatchFound("No match found for {}".format(node.__class__.__name__))

################################################################################

def fatal_error(msg, ret = -1):
    """ Helper function for handling fatal errors.

    this function will put C{msg} in C{sys.stderr} and exit the program
    with C{ret} return value.
    """
    print >> sys.stderr, 'Error: {msg}'.format(msg = msg)
    exit(ret)

def reverse_map(a_b_map):
    b_a_map = {}
    for a, b in a_b_map.iteritems():
        b_a_map[b] = a
    return b_a_map

################################################################################
# EOF
################################################################################

class OutputProviderPredicate(object):

    def __call__(self, ouput):
        return True

class OutputProvider(object):

    def __init__(self):
        self.providers = {}

    def register(self, output):
        if self.providers.has_key(output.name):
            print >> sys.stderr, "{!s} output already exists. Please use another output.".format(output.name)
            traceback.print_stack()
            exit(-1)

        self.providers[output.name] = output

    def get(self, output_name, predicate = OutputProviderPredicate()):
        try:
            output = self.providers[output_name]
            if predicate(output):
                return output
            else:
                print >> sys.stderr, "{!s} do not satisfy {!s}".format(output_name, predicate)
                traceback.print_stack()
                exit(-1)
        except KeyError:
            print >> sys.stderr, "{!s} in not a valid output name. Please register an output before using it.".format(output_name)
            traceback.print_stack()
            exit(-1)

    def __iter__(self):
        return self.providers.itervalues()
