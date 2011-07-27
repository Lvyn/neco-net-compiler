import operator

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

# def class_name_lower(cls):
#     return str.lower(cls.__class__.__name__)

# cdef class MultiSet:

#     cdef dict _tvc

#     def __init__(self, initial_data = {}):
#         """ builds a brand new MultiSet from some initial data

#         @param initial_data: dictionary with initial data elt <-> multiplicity
#         @type initial_data: C{dict}
#         """
#         self._tvc = {}
#         self.update_from_dict(initial_data)

#     def update_from_dict(self, data):
#         for elt, count in data.iteritems():
#             t = elt.__class__
#             try:
#                 values = self._tvc[t]
#             except KeyError:
#                 values = dict()
#                 self._tvc[t] = values

#             try:
#                 values[elt] += count
#             except KeyError:
#                 values[elt] = count

#     def copy(self):
#         """ copy the MultiSet

#         >>> ms1 = MultiSet({1:2, 2:3, 'a':1})
#         >>> ms2 = ms1.copy()
#         >>> ms1
#         MultiSet({1:2, 2:3, 'a':1})
#         >>> ms2
#         MultiSet({'a':1, 1:2, 2:3})
#         >>> ms1.remove(1)
#         >>> ms1
#         MultiSet({1:1, 2:3, 'a':1})
#         >>> ms2
#         MultiSet({'a':1, 1:2, 2:3})

#         @return: a copy of the MultiSet
#         @rtype: C{MultiSet}
#         """
#         result = MultiSet()

#         for ctype, cvalues in self._tvc.iteritems():
#             values = dict()
#             result._tvc[ctype] = values

#             for value, count in cvalues.iteritems():
#                 values[value] = count

#         return result

#     def __add__(self, other):
#         new = self.copy()
#         new.update(other)
#         return new

#     def add(self, elt):
#         """ adds an element to the MultiSet

#         @param elt: element to be added
#         @type elt: C{object}
#         """
#         cls = elt.__class__
#         try:
#             values = self._tvc[cls]
#         except KeyError :
#             values = dict()
#             self._tvc[cls] = values

#         try:
#             values[elt] += 1
#         except KeyError:
#             values[elt] = 1

#     def add_items(self, items):
#         """ adds a list of items to the MultiSet

#         @param items: items to be added
#         @type items: C{iterable}
#         """
#         for item in items:
#             self.add(item)

#     def remove(self, elt):
#         """ removes an element from the MultiSet

#         @param elt: element to be removed
#         @type elt: C{object}
#         """
#         cls = elt.__class__
#         try:
#             values = self._tvc[cls]
#             values[elt] -= 1
#             if (values[elt] < 0):
#                 raise ValueError, "not enough occurrences"

#             if (values[elt] == 0):
#                 del values[elt]
#                 if len(values) == 0:
#                     del self._tvc[cls]
#         except:
#             raise ValueError, "not enough occurrences"


#     def __iter__(self):
#         """ iterator over the values (with repetitions)
#         """
#         l = []
#         for values in self._tvc.values():
#             for value, count  in values.iteritems():
#                 for i in range(0, count):
#                     l.append(value)
#         return l.__iter__()

#     def __str__(self):
#         """ return a human readable string representation

#         >>> str(MultiSet({2:1, 'a':2, 1.1:3}))
#         '[2, a, a, 1.1, 1.1, 1.1]'

#         @return: human readable string representation of the MultiSet
#         @rtype: C{str}
#         """
#         return "[%s]" % ", ".join([str(x) for x in self])

#     def __repr__(self):
#         """ return a string representation that is suitable for C{eval}

#         >>> MultiSet({2:1, 'a':2, 1.1:3})
#         MultiSet({2:1, 'a':2, 1.1:3})

#         @return: precise string representation of the MultiSet
#         @rtype: C{str}
#         """
#         l = []
#         for values in self._tvc.values():
#             l.append(', '.join([("%s:%s" % (repr(k), repr(v))) for k, v in values.iteritems()]))
#         return "MultiSet({%s})" % ', '.join(l)

#     def __len__(self):
#         """ number of elements, including repetitions
#         @rtype: C{int}
#         """
#         l = 0
#         for v in self:
#             l += 1
#         return l

#     def size(self):
#         """ number of elements, excluding repetitions

#         @rtype: C{int}
#         """
#         return len(self.domain())

#     cdef int hash(self):
        
#         cdef long x = 0x345678L
#         cdef long y
#         cdef int l = len(self)
#         cdef long mult = 1000003L

#         for i in self:
#             l -= 1
#             y = hash(i)
#             if (y == -1):
#                 return -1
#             x = (x ^ y)
#         x += 97531L
#         return x
        
#         # cdef int x = 0x345678L
#         # dom = self.domain()
#         # l = len(dom)
#         # mult = 1000003L

#         # for i in dom:
#         #     l -= 1
#         #     y = hash(i)
#         #     if (y == -1):
#         #         return -1
#         #     x = (x ^ y)
#         # x += 97531L
#         # return x

#     def __hash__ (self) :
#         return self.hash()

#     def __richcmp__(self, other, op):
#         if op == 2: # ==
#             return self.compare(other) == 0

#         elif op == 0: # <
#             return self.compare(other) < 0

#         elif op == 1: # <=
#             return self.compare(other) <= 0

#         elif op == 3: # !=
#             return self.compare(other) != 0

#         elif op == 4: # >
#             return self.compare(other) > 0

#         elif op == 5: # >=
#             return self.compare(other) >= 0

#         else:
#             assert False

#     cdef int compare(MultiSet self, MultiSet other):
#         self_types  = self._tvc.keys()
#         other_types = other._tvc.keys()

#         if self_types < other_types:
#             return -1
#         elif self_types > other_types:
#             return 1
#         else: # self_types == other_types
#             for type_name in self._tvc:
#                 self_values  = self._tvc[type_name]
#                 other_values = other._tvc[type_name]

#                 self_values_keys  = self_values.keys()
#                 other_values_keys = other_values.keys()

#                 if self_values_keys < other_values_keys:
#                     return -1
#                 elif self_values_keys > other_values_keys:
#                     return 1
#                 else: # self_values == other_values.values
#                     for val in self_values_keys:
#                         if self_values[val] < other_values[val]:
#                             return -1
#                         elif self_values[val] > other_values[val]:
#                             return 1
#                         else:
#                             continue
#             return 0

#     def update(self, other):
#         """

#         >>> ms = MultiSet({2:1, 1:1, 'a':3})
#         >>> ms.update(MultiSet({1:2, 'a':1, 'b':2, 1.1:1}))
#         >>> ms
#         MultiSet({1:3, 2:1, 'a':4, 'b':2, 1.1:1})

#         """
#         for elt in other:
#             self.add(elt)

#     def domain(self):
#         """

#         >>> MultiSet({2:2, 'a':1}).domain()
#         [2, 'a']

#         """
#         keys = []
#         for values in self._tvc.values():
#             keys.extend(values.keys())
#         return keys

