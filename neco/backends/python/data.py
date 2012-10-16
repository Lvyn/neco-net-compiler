""" data structures designed for the compiled petrinet """

from collections import Iterable
from copy import copy # a swallow copy is enough here
from neco.extsnakes import Pid
from process import PidTree
from snakes.hashables import hdict, hashable
from functools import partial
import operator

def pid_free_tuple_count_compare(ignore_set, left_pair, right_pair):
    left,  left_count  = left_pair
    right, right_count = right_pair
    
    length = len(left)
    for i in xrange(length):
        if i in ignore_set:
            continue
        li = left[i]
        ri = right[i]
        if li < ri:
            return -1
        elif li > ri:
            return 1
        d = left_count - right_count
        if d != 0:
            return d

    return 0

def build_pid_count_map(place):
    pid_count_map = {}
    for token in place:
        try:
            pid_count_map[token] += 1
        except KeyError:
            pid_count_map[token] = 0
    return pid_count_map

def pid_free_pid_count_compare(left_pair, right_pair):
    _,  left_count = left_pair
    _, right_count = right_pair
    tmp = left_count - right_count
    if tmp != 0:
        return tmp
    return 0

def dump(e):
    if hasattr(e, '__dump__'):
        return e.__dump__()

    else:
        return repr(e)

class multiset(hdict):
    """
    """

    def __hash__(self):
        return reduce(operator.xor, (hash(i) for i in self.items()), 252756382)

    def __init__(self, initial_data=[]):
        """ builds a brand new multiset from some initial data

        @param initial_data: list of elements (eventually with repetitions
        @type initial_data: C{}
        """
        hdict.__init__(self)

        for elt in initial_data:
            self.add(elt)

    def __add__(self, other):
        new = self.copy()
        new.add_items(other)
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
        return reduce(operator.add, self.values(), 0)

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
    def compare(self, other):
        if self < other:
            return -1
        elif self > other:
            return 1
        else:
            return 0

    def pid_free_tuple_compare(self, other, ignore):

        self_keys = self.keys()
        other_keys = other.keys()
        self_len = len(self_keys)
        
        tmp = len(self_keys) - len(other_keys)
        if tmp != 0:
            return tmp
        if self_len == 0:
            return 0
        
        # order items x values
        cmp_fun = partial(pid_free_tuple_count_compare, ignore)
        left  = sorted( self.iteritems(),  cmp = cmp_fun )
        right = sorted( other.iteritems(), cmp = cmp_fun )
        
        for i in xrange(self_len):
            tmp = cmp_fun(left[i], right[i])
            if tmp != 0:
                return tmp
        return 0

    def pid_free_pid_compare(self, other):
        self_keys  = self.keys()
        other_keys = other.keys()
        
        self_len  = len(self_keys)
        other_len = len(other_keys)
        
        tmp = self_len - other_len
        if tmp != 0:
            return tmp

        left_map = build_pid_count_map(self_keys)
        right_map = build_pid_count_map(other_keys)

        left  = sorted(left_map.iteritems(), cmp = pid_free_pid_count_compare )
        right = sorted(right_map.iteritems(), cmp = pid_free_pid_count_compare )
        
        for i in range(self_len):
            tmp = pid_free_pid_count_compare(left[i], right[i])
            if tmp != 0:
                return tmp
        return 0

    def pid_free_first_tuple_compare(self, other):
        self_keys = self.keys()
        other_keys = other.keys()
        l1 = len(self_keys)
        l2 = len(other_keys)
        i = 0

        if l1 < l2:
            return -1
        elif l1 > l2:
            return 1

        # ensure we are working on sorted domain
        self_keys.sort()
        other_keys.sort()

        for i in xrange(0,l1):
            lkey = self_keys[i]
            rkey = other_keys[i]

            ltuplefree = lkey[:-1]
            rtuplefree = rkey[:-1]
            if ltuplefree == rtuplefree: # equal tuples, without pids
                v1 = self[lkey]
                v2 = other[rkey]
                cmp = v1 - v2
                if cmp != 0:
                    return cmp
                continue
            elif ltuplefree < rtuplefree:
                return -1
            else:
                return 1
        return 0

    def update(self, other):
        hdict.update(self, other)

    def domain(self):
        """!
        >>> multiset(['foo', 'foo', 'bar']).domain()
        ['foo', 'bar']

        """
        return self.keys()

    def __dump__(self):
        l = ['[']
        for token in self:
            l.append(dump(token))
            l.append(', ')
        l.append(']')
        return "".join(l) 

def neco__tuple_update_pids(tup, new_pid_dict):
    """
    This function updates pids, with respect to C{new_pid_dict}, of a tuple object (C{tup}). 
    
    For example lets consider the dictionary

    >>> pid_dict = { Pid.from_str('2') : Pid.from_str('1'), Pid.from_str('2.4') : Pid.from_str('1.1') }
    
    and token 

    >>> token = (Pid.from_str('2'), Pid.from_str('2.4'), 42, Pid.from_str('2'))
    
    then this function updates the tuple in the following way

    >>> neco__tuple_update_pids(token, pid_dict)
    (Pid.from_str('1'), Pid.from_str('1.1'), 42, Pid.from_str('1'))
    
    The transformation is recursive on tuples

    >>> token = (Pid.from_str('2'), Pid.from_str('2.4'), (42, Pid.from_str('2.4'), (Pid.from_str('2'), )), Pid.from_str('2'))
    >>> neco__tuple_update_pids(token, pid_dict)
    (Pid.from_str('1'), Pid.from_str('1.1'), (42, Pid.from_str('1.1'), (Pid.from_str('1'),)), Pid.from_str('1'))
    
    """
    new_iterable = []
    for tok in tup:
        if isinstance(tok, Pid):
            new_tok = Pid.from_list(new_pid_dict[tuple(tok.data)])
        elif isinstance(tok, tuple):
            new_tok = neco__tuple_update_pids(tok, new_pid_dict)
        else:
            new_tok = tok
        new_iterable.append(new_tok)
    return tuple(new_iterable)


def neco__multiset_update_pids(ms, new_pid_dict):
    """
    This function updates pids within a multiset C{ms} with resepect to C{new_pid_dict}.
    
    >>> ms = multiset()
    >>> ms.add_items([1, 2, Pid.from_str('2'), Pid.from_str('3')])
    >>> neco__multiset_update_pids(ms, {Pid.from_str('2') : Pid.from_str('1'), Pid.from_str('3') : Pid.from_str('2')})
    multiset([Pid.from_str('1'), 1, 2, Pid.from_str('2')])
    
    See L{neco__iterable_update_pids}.
    """
    new_ms = multiset()
    for tok, count in ms.iteritems():
        if isinstance(tok, Pid):
            new_tok = Pid.from_list(new_pid_dict[tuple(tok.data)])
        elif isinstance(tok, tuple):
            new_tok = neco__tuple_update_pids(tok, new_pid_dict)
        else:
            new_tok = tok
        new_ms[new_tok] = count
    return new_ms

def pid_place_type_update_pids(ms, new_pid_dict):
    new_ms = multiset()
    for tok, count in ms.iteritems():
        new_tok = Pid.from_list(new_pid_dict[tuple(tok.data)])
        new_ms[new_tok] = count
    return new_ms
    

def generator_place_update_pids(ms, new_pid_dict):
    """
    This function updated a generator place multiset C{ms} with resepect to C{new_pid_dict}.

    >>> sgen = multiset([ (Pid.from_str('1'), 6), (Pid.from_str('1.4'), 2) ])
    >>> pid_tree = neco__create_pid_tree() 
    >>> neco__generator_multiset_update_pid_tree(sgen, pid_tree)
    >>> new_pid_dict = neco__normalize_pid_tree(pid_tree)
    >>> new_pid_dict
    {Pid.from_str('1'): Pid.from_str('1'), Pid.from_str('1.7'): Pid.from_str('1.3'), Pid.from_str('1.4.3'): Pid.from_str('1.1.1'),
    Pid.from_str('1.4'): Pid.from_str('1.1')}
    >>> neco__generator_token_transformer(sgen, new_pid_dict)
    multiset([(Pid.from_str('1.1'), 0), (Pid.from_str('1'), 2)])

    """
    # print ">>> ", new_pid_dict
    new_ms = multiset()
    for pid, n in ms:
        new_pid = Pid.from_list(new_pid_dict[tuple(pid.data)])
        new_n = Pid.from_list(new_pid_dict[ tuple(pid.next(n).data) ]).ends_with() - 1
        new_ms.add((new_pid, new_n))
    return new_ms


def neco__generator_multiset_update_pid_tree(ms, pid_tree):
    """
    This function updates a pid tree (C{pid_tree}) retrieving data from a generator place multiset C{ms}.
    
    >>> sgen = multiset([ (Pid.from_str('1'), 6), (Pid.from_str('1.4'), 2) ])
    >>> pid_tree = neco__create_pid_tree() 
    >>> neco__generator_multiset_update_pid_tree(sgen, pid_tree)
    >>> pid_tree.print_structure()
    <active=F>
    |-1-<active=T>
      |-4-<active=T>
      | |-3-<active=T>
      |-7-<active=T>

    """
    for pid, n in ms:
        pid_tree.expanded_insert(pid)
        pid_tree.expanded_insert(pid.next(n))

def neco__iterable_update_pid_tree(iterable, pid_tree):
    """
    This function inserts pids to a pid tree (C{pid_tree}) from an iterable object (C{iterable}). 
    
    For example consider an empty tree and the token

    >>> tree = PidTree()
    >>> token = (Pid.from_str('1.1'), 42, Pid.from_str('1.2'), Pid.from_str('1.1'))
    
    then the call of the function modifies the tree as follows  

    >>> neco__iterable_update_pid_tree(token, tree)
    >>> tree.print_structure()
    <active=F>
    |-1-<active=F>
      |-1-<active=T>
      |-2-<active=T>
    
    Pids are also grabed from inner tuples if the iterable object is a tuple.

    >>> token = (Pid.from_str('1.1'), (42, Pid.from_str('1'), (Pid.from_str('1.1.1'),)), Pid.from_str('1.2'), Pid.from_str('1.1'))
    >>> neco__iterable_update_pid_tree(token, tree)
    >>> tree.print_structure()
    <active=F>
    |-1-<active=T>
      |-1-<active=T>
      | |-1-<active=T>
      |-2-<active=T>
    """
    for tok in iterable:
        if isinstance(tok, Pid):
            pid_tree.expanded_insert(tok)
        elif isinstance(tok, tuple):
            neco__iterable_update_pid_tree(tok, pid_tree)

def neco__create_pid_tree():
    return PidTree(0)

def neco__normalize_pid_tree(pid_tree):
    return pid_tree.reduce_sibling_offsets()

            
if __name__ == "__main__":
    import doctest
    doctest.testmod()
