""" data structures designed for the compiled petrinet """

from snakes.hashables import hdict
import operator

def dump(e):
    if hasattr(e, '__dump__'):
        return e.__dump__()
    else:
        return str(e)

class multiset(hdict):
    """
    """

    def __init__(self, initial_data = []):
        """ builds a brand new multiset from some initial data

        @param initial_data: list of elements (eventually with repetitions
        @type initial_data: C{}
        """
        for elt in initial_data:
            self.add(elt)

    def __add__(self, other):
        new = self.copy()
        new.update(other)
        return new

    def copy(self):
        """ copy the multiset

        @return: a copy of the multiset
        @rtype: C{multiset}
        """
        result = multiset()
        result.update(self)
        return result

    def add(self, elt):
        """ adds an element to the multiset

        >>> m = multiset()
        >>> m
        multiset([])
        >>> m.add('foo')
        >>> m
        multiset(['foo'])
        >>> m.add('foo')
        >>> m
        multiset(['foo', 'foo'])
        >>> m.add('bar')
        >>> m
        multiset(['foo', 'foo', 'bar'])

        @param elt: element to be added
        @type elt: C{object}
        """
        try :
            self[elt] += 1
        except KeyError :
            self[elt] = 1

    def add_items(self, items):
        """ adds a list of items to the multiset

        >>> m = multiset()
        >>> m.add_items(['foo', 'foo', 'bar'])
        >>> m
        multiset(['foo', 'foo', 'bar'])

        @param items: items to be added
        @type items: C{iterable}
        """
        for item in items:
            self.add(item)

    def remove(self, elt):
        """ removes an element from the multiset

        >>> m = multiset(['foo'])
        >>> m
        multiset(['foo'])
        >>> m.remove('foo')
        >>> m
        multiset([])
        >>> m = multiset(['foo', 'foo'])
        >>> m
        multiset(['foo', 'foo'])
        >>> m.remove('foo')
        >>> m
        multiset(['foo'])

        @param elt: element to be removed
        @type elt: C{object}
        """
        if self.get(elt, 0) <= 0:
            raise ValueError, "not enough occurrences"
        self[elt] -= 1
        if self[elt] == 0:
            del self[elt]

    def __iter__(self):
        """ iterator over the values (with repetitions)

        >>> m = multiset(['foo', 'foo', 'bar'])
        >>> for e in m:
        ...     e
        'foo'
        'foo'
        'bar'

        """
        for value in dict.__iter__(self):
            for count in range(self[value]):
                yield value

    def __str__(self):
        """ return a human readable string representation

        @return: human readable string representation of the multiset
        @rtype: C{str}
        """
        return "{%s}" % ", ".join(str(x) for x in self)

    def __repr__(self):
        """ return a string representation that is suitable for C{eval}

        @return: precise string representation of the multiset
        @rtype: C{str}
        """
        return "multiset([%s])" % ", ".join(repr(x) for x in self)

    def __len__(self):
        """ number of elements, including repetitions

        >>> len( multiset() )
        0
        >>> len( multiset(['foo']) )
        1
        >>> len( multiset(['foo', 'foo']) )
        2
        >>> len( multiset(['foo', 'bar', 'foo']) )
        3

        @rtype: C{int}
        """
        if self.size() == 0:
            return 0
        else:
            return reduce(operator.add, self.values())

    def size(self):
        """ number of elements, excluding repetitions

        >>> multiset().size()
        0
        >>> multiset(['foo']).size()
        1
        >>> multiset(['foo', 'foo']).size()
        1
        >>> multiset(['foo', 'bar', 'foo']).size()
        2

        @rtype: C{int}
        """
        return dict.__len__(self)

    def __eq__(self, other):
        """ test for equality

        >>> multiset([1, 2, 3]*2) == multiset([1, 2, 3]*2)
        True
        >>> multiset([1, 2, 3]) == multiset([1, 2, 3, 3])
        False

        @param other: multiset to compare with
        @type other: C{multiset}
        @rtype{bool}
        """
        if len(self) != len(other):
            return False
        else:
            for val in self:
                try :
                    if self[val] != other[val] :
                        return False
                except (KeyError, TypeError) :
                    return False
        return True

    def __ne__(self, other):
        """ test for difference

        >>> multiset([1, 2, 3]*2) != multiset([1, 2, 3]*2)
        False
        >>> multiset([1, 2, 3]) != multiset([1, 2, 3, 3])
        True

        @param other: multiset to compare with
        @type other: C{multiset}
        """
        return not (self == other)

    def __lt__(self, other):
        """ test for strict inclusion

        >>> multiset([1, 2, 3]) < multiset([1, 2, 3, 4])
        True
        >>> multiset([1, 2, 3]) < multiset([1, 2, 3, 3])
        True
        >>> multiset([1, 2, 3]) < multiset([1, 2, 3])
        False
        >>> multiset([1, 2, 3]) < multiset([1, 2])
        False
        >>> multiset([1, 2, 2]) < multiset([1, 2, 3, 4])
        False


        @param other: multiset to compare with
        @type other: C{multiset}
        """
        if not set(self.keys()) <= set(other.keys()):
            return False
        result = False
        for value, times in dict.items(self):
            count = other.get(value, 0)
            if times > count:
                return False
            elif times < count:
                result = True
        return result or (dict.__len__(self) < dict.__len__(other))


    def __le__ (self, other) :
        """Test for inclusion inclusion

        >>> multiset([1, 2, 3]) <= multiset([1, 2, 3, 4])
        True
        >>> multiset([1, 2, 3]) <= multiset([1, 2, 3, 3])
        True
        >>> multiset([1, 2, 3]) <= multiset([1, 2, 3])
        True
        >>> multiset([1, 2, 3]) <= multiset([1, 2])
        False
        >>> multiset([1, 2, 2]) <= multiset([1, 2, 3, 4])
        False

        @param other: the multiset to compare with
        @type other: C{multiset}
        @rtype: C{bool}
        """
        if not set(self.keys()) <= set(other.keys()):
            return False
        for value, times in dict.items(self):
            count = other.get(value, 0)
            if times > count:
                return False
        return True

    def __gt__ (self, other) :
        """Test for strict inclusion

        >>> multiset([1, 2, 3, 4]) > multiset([1, 2, 3])
        True
        >>> multiset([1, 2, 3, 3]) > multiset([1, 2, 3])
        True
        >>> multiset([1, 2, 3]) > multiset([1, 2, 3])
        False
        >>> multiset([1, 2]) > multiset([1, 2, 3])
        False
        >>> multiset([1, 2, 3, 4]) > multiset([1, 2, 2])
        False

        @param other: the multiset to compare with
        @type other: C{multiset}
        @rtype: C{bool}
        """
        return other.__lt__(self)

    def __ge__ (self, other) :
        """Test for inclusion

        >>> multiset([1, 2, 3, 4]) >= multiset([1, 2, 3])
        True
        >>> multiset([1, 2, 3, 3]) >= multiset([1, 2, 3])
        True
        >>> multiset([1, 2, 3]) >= multiset([1, 2, 3])
        True
        >>> multiset([1, 2]) >= multiset([1, 2, 3])
        False
        >>> multiset([1, 2, 3, 4]) >= multiset([1, 2, 2])
        False

        @param other: the multiset to compare with
        @type other: C{multiset}
        @rtype: C{bool}
        """
        return other.__le__(self)

    def update(self, other):
        hdict.update(self, other)

    def domain(self):
        """
        >>> multiset(['foo', 'foo', 'bar']).domain()
        ['foo', 'bar']

        """
        return self.keys()

    def __dump__(self):
        l = []
        for token in self:
            l.append(repr(token))
        return " ".join(l)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
