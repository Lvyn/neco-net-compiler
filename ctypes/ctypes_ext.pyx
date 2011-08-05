from snakes.nets import dot
from time import time
import operator
cimport ctypes_ext

################################################################################
# Multisets
################################################################################

cpdef dump(object obj):
    if hasattr(obj, '__dump__'):
        return obj.__dump__()
    else:
        return str(obj)

cpdef _compare(object left, object right):
    if hasattr(left, 'compare'):
        return left.compare(right)
    else:
        if left == right:
            return 0
        elif left < right:
            return -1
        else:
            return 1

cdef class MultiSet:
    cdef dict _data

    def __cinit__(MultiSet self, dict initial_data = {}):
        """ builds a brand new MultiSet from some initial data

        @param initial_data: list of elements (eventually with repetitions
        @type initial_data: C{dict}
        """
        cdef int i
        cdef object e

        self._data = {}
        for e, count in initial_data.iteritems():
            for 0 <= i < count:
                self.add(e)

    cdef MultiSet copy(MultiSet self):
        """ copy the MultiSet

        @return: a copy of the MultiSet
        @rtype: C{MultiSet}
        """
        cdef MultiSet result = MultiSet(self._data)
        return result

    def __add__(MultiSet self, MultiSet other):
        cdef MultiSet new = self.copy()
        new.add_items(other)
        return new

    cdef void add(MultiSet self, object elt):
        """ adds an element to the MultiSet

        @param elt: element to be added
        @type elt: C{object}
        """
        try:
            self._data[elt] += 1
        except KeyError :
            self._data[elt] = 1

    cdef add_items(self, items):
        """ adds a list of items to the MultiSet

        @param items: items to be added
        @type items: C{iterable}
        """
        for item in items:
            self.add(item)

    cdef void remove(MultiSet self, elt):
        """ removes an element from the MultiSet

        @param elt: element to be removed
        @type elt: C{object}
        """
        if self._data.get(elt, 0) <= 0:
            raise ValueError, "not enough occurrences"
        self._data[elt] -= 1
        if self._data[elt] == 0:
            del self._data[elt]

    def __iter__(MultiSet self):
        """ iterator over the values (without repetitions)
        """
        cdef list l = []
        cdef int i
        for e, c in self._data.iteritems():
            for 0 <= i < c:
                l.append(e)
        return l.__iter__()

    def __str__(MultiSet self):
        """ return a human readable string representation

        @return: human readable string representation of the MultiSet
        @rtype: C{str}
        """
        l = []
        for elt, count in self._data.iteritems():
            for 0 <= i < count:
                l.append(elt)

        return "{%s}" % ", ".join([str(x) for x in l])

    def __repr__(MultiSet self):
        """ return a string representation that is suitable for C{eval}

        @return: precise string representation of the MultiSet
        @rtype: C{str}
        """
        l = []
        for elt, count in self._data.iteritems():
            for 0 <= i < count:
                l.append(elt)

        return "MultiSet([%s])" % ", ".join([repr(x) for x in l])

    def __len__(MultiSet self):
        """ number of elements, including repetitions
        @rtype: C{int}
        """
        return len(self._data)

    cdef size(MultiSet self):
        """ number of elements, excluding repetitions

        @rtype: C{int}
        """
        return dict.__len__(self)

    cdef int hash(MultiSet self):
        cdef long x = 0x345678L
        cdef long y
        cdef int l = len(self._data)
        cdef long mult = 1000003L

        for i in self._data:
            l -= 1
            y = hash(i)
            if (y == -1):
                return -1
            x = (x ^ y)
        x += 97531L
        return x

        # 252756382 = hash("snakes.hashables.hlist")
        cdef int h = 252756382
        for i in self._data.items():
            h ^= hash(i)
        return h

    def __hash__ (MultiSet self) :
        """
        """
        cdef int x = 0x345678L
        cdef int y
        cdef int l = len(self._data)
        cdef int mult = 1000003L

        for i in self._data:
            l -= 1
            y = hash(i)
            if (y == -1):
                return -1
            x = (x ^ y) # ^ mult
            #mult += 82520L + l + l
        x += 97531L
        return x


        # 252756382 = hash("snakes.hashables.hlist")
        cdef int h = 252756382
        for i in self._data.items():
            h ^= hash(i)
        return h
        #return reduce(operator.xor, ( [hash(i) for i in self._data.items()] ), 252756382)

    cdef int compare(MultiSet self, MultiSet other):
        cdef int l1 = len(self)
        cdef int l2 = len(other)
        cdef list self_keys
        cdef list other_keys
        cdef object v1
        cdef object v2

        if l1 < l2:
            return -1
        elif l1 > l2:
            return 1
        else:
            self_keys = sorted(self._data.keys())
            other_keys = sorted(other._data.keys())

            if self_keys < other_keys:
                return -1
            elif self_keys > other_keys:
                return 1
            else:
                for val in self_keys:
                    v1 = self._data[val]
                    v2 = other._data[val]

                    if v1 < v2:
                        return -1
                    elif v1 > v2:
                        return 1
                    else:
                        continue
                return 0

    def __richcmp__(MultiSet self, MultiSet other, int op):
        if op == 2: # ==
            if len(self) != len(other):
                return False
            else:
                for val in self._data:
                    try :
                        if self._data[val] != other._data[val] :
                            return False
                    except (KeyError, TypeError) :
                        return False
            return True

        elif op == 0: # <
            assert(False)
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

        elif op == 1: # <=
            assert(False)
            if not set(self.keys()) <= set(other.keys()):
                return False
            for value, times in dict.items(self):
                count = other.get(value, 0)
                if times > count:
                    return False
            return True

        elif op == 3: # !=
            assert(False)
            return not (self == other)

        elif op == 4: # >
            assert(False)
            return (other < self)

        elif op == 5: # >=
            assert(False)
            return (other <= self)

        else:
            raise ValueError()

    cdef void update(MultiSet self, MultiSet other):
        self._data.update(self, other._data)

    cdef list domain(MultiSet self):
        return self._data.keys()

    cpdef __dump__(MultiSet self):
        cdef list l = []
        cdef int i
        cdef str s
        for elt, count in self._data.iteritems():
            for 0 <= i < count:
                l.append(elt)
        s = ''
        for e in l:
            s += dump(e) + ' '
        return s

def state_space():
    cdef set visited
    cdef set visit
    cdef set succ
    cdef int count
    cdef int start
    try:
        visited = set()
        visit = set([init()])
        succ = set()
        count = 0
        start = time()
        while True:
            count += 1
            m = visit.pop()
            visited.add(m)
            succ = succs(m)
            visit.update(succ.difference(visited))
    except KeyError:
        return visited
    return visited


# LTL debuging functions :)
import sys

do_print = False
def f1(p1, p2):
    if do_print: sys.stderr.write('call f1\n')
    for t in p1:
        if t == dot:
            if do_print: sys.stderr.write('f1 True\n')
            return True
    if do_print: sys.stderr.write('f1 False\n')
    return False

def f2(p1, p2):
    if do_print: sys.stderr.write('call f2\n')
    for t in p2:
        if t == dot:
            if do_print: sys.stderr.write('f2 True\n')
            return True
    if do_print: sys.stderr.write('f2 False\n')
    return False

# ... ... ... ... ... ...

### Place helpers

### int place types

cdef class IntPlaceTypeHelperIterator(object):
    cdef int m_index
    cdef int m_max
    cdef ctypes_ext.int_place_type *m_place

    def __cinit__(IntPlaceTypeHelperIterator self):
        self.m_index = -1

    def __iter__(IntPlaceTypeHelperIterator self):
        return self

    def next(IntPlaceTypeHelperIterator self):
        self.m_index += 1
        if (self.m_index >= self.m_size):
            raise StopIteration
        return ctypes_ext.int_place_type_get(self.m_place, self.m_index)

cdef class IntPlaceTypeHelper(object):
    cdef ctypes_ext.int_place_type* m_place

    def __init__(IntPlaceTypeHelper self):
        pass

    def __iter__(IntPlaceTypeHelper self):
        cdef IntPlaceTypeHelper iterator = IntPlaceTypeHelperIterator(self)
        iterator.m_place = self.m_place
        iterator.m_max = ctypes_ext.int_place_type_size(self.m_place)
        return

    def __contains__(IntPlaceTypeHelper self, int value):
        cdef int current
        cdef int i = 0
        cdef int size = ctypes_ext.int_place_type_size(self.m_place)
        for 0 <= i < size:
            current = ctypes_ext.int_place_type_get(self.m_place, i)
            if current == value:
                return 1
        return 0

    def __len__(IntPlaceTypeHelper self):
        return ctypes_ext.int_place_type_size(self.m_place)

    def is_empty(IntPlaceTypeHelper self):
        return ctypes_ext.int_place_type_size(self.m_place) == 0

###

cdef class BtPlaceTypeHelperIterator(object):
    cdef int m_index
    cdef int m_count

    def __init__(BtPlaceTypeHelperIterator self, int c):
        self.m_index = -1
        self.m_count = c

    def __iter__(BtPlaceTypeHelperIterator self):
        return self

    def __next__(BtPlaceTypeHelperIterator self):
        self.m_index += 1
        if self.m_index >= self.m_count:
            raise StopIteration
        return dot

cdef class BtPlaceTypeHelper(object):
    cdef int m_count

    def __cinit__(BtPlaceTypeHelper self, int c):
        self.m_count = c

    def __iter__(BtPlaceTypeHelper self):
        return BtPlaceTypeHelperIterator(self.m_count)

    def __contains__(BtPlaceTypeHelper self, dot):
        if self.m_count > 0:
            return True
        return False

    def __len__(BtPlaceTypeHelper self):
        return self.m_count

    cdef is_empty(BtPlaceTypeHelper self):
        return self.m_count > 0

###

cdef class OneSafePlaceTypeHelperIterator(object):
    cdef int m_index
    cdef int m_full
    cdef object m_object

    def __cinit__(OneSafePlaceTypeHelperIterator self, int full, object obj):
        self.m_index = 0
        self.m_full = full
        self.m_object = obj

    def __iter__(OneSafePlaceTypeHelperIterator self):
        return self

    def next(OneSafePlaceTypeHelperIterator self):
        if self.m_index < self.m_full:
            raise StopIteration
        self.m_index += 1
        return self.m_object

cdef class OneSafePlaceTypeHelper(object):
    cdef int m_full
    cdef object m_object

    def __cinit__(OneSafePlaceTypeHelper self, int full, object obj):
        self.m_full = full
        self.m_object = obj

    def __iter__(OneSafePlaceTypeHelper self):
        cdef OneSafePlaceTypeHelperIterator it = OneSafePlaceTypeHelperIterator(self.m_full, self.m_object)
        return it

    def __contains__(OneSafePlaceTypeHelper self, value):
        if self.m_full > 0 and value == self.m_object:
            return 1
        return 0

    def __len__(OneSafePlaceTypeHelper self):
        if self.m_full:
            return 1
        return 0

    def is_empty(OneSafePlaceTypeHelper self):
        return self.m_full == 0

