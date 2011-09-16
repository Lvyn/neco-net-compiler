import operator

################################################################################
# Multisets
################################################################################

def class_name_lower(cls):
    return str.lower(cls.__class__.__name__)

class MultiSet:
    cdef dict _tvc

    def __cinit__(MultiSet self, dict initial_data = {}):
        """ builds a brand new MultiSet from some initial data

        @param initial_data: list of elements (eventually with repetitions
        @type initial_data: C{dict}
        """
        self._tvc = {}
        self.update_from_dict(initial_data)

    cdef update_from_dict(MultiSet self, dict data):
        cdef object elt
        cdef object t
        cdef dict values

        for elt in data:
            t = elt.__class__
            try:
                values = self._tvc[t]
            except IndexError:
                values = dict()
                self._tvc[t] = values

            try:
                values[elt] += 1
            except IndexError:
                values[elt] = 0

    cdef copy(MultiSet self):
        """ copy the MultiSet

        @return: a copy of the MultiSet
        @rtype: C{MultiSet}
        """
        cdef MultiSet result
        cdef object ctype
        cdef dict cvalues
        cdef object value
        cdef int count

        result = MultiSet()
        for ctype, cvalues in self._tvc.iteritems():
            values = dict()
            result._tvc[ctype] = values

            for value, count in cvalues.iteritems():
                values[value] = count

        return result

    def __add__(MultiSet self, MultiSet other):
        cdef MultiSet new
        new = self.copy()
        new.update(other)
        return new

    cdef add(MultiSet self, object elt):
        """ adds an element to the MultiSet

        @param elt: element to be added
        @type elt: C{object}
        """
        cdef object cls
        cdef dict values

        cls = elt.__class__
        try:
            values = self._tvc[cls]
        except KeyError :
            values = dict()
            self._tvc[cls] = values

        try:
            values[elt] += 1
        except KeyError:
            values[elt] = 1

    cdef add_items(MultiSet self, object items):
        """ adds a list of items to the MultiSet

        @param items: items to be added
        @type items: C{iterable}
        """
        cdef object item
        for item in items:
            self.add(item)

    cdef remove(MultiSet self, object elt):
        """ removes an element from the MultiSet

        @param elt: element to be removed
        @type elt: C{object}
        """
        cdef object cls
        cdef dict values
        cls = elt.__class__
        try:
            values = self._tvc[cls]
            values[elt] -= 1
            if (values[elt] < 0):
                raise ValueError, "not enough occurrences"

            if (values[elt] == 0):
                del values[elt]
        except:
            raise ValueError, "not enough occurrences"


    def __iter__(MultiSet self):
        """ iterator over the values (with repetitions)
        """
        cdef list l = []
        cdef dict values
        cdef object value
        cdef int count
        for values in self._tvc.values():
            for value, count  in values.iteritems():
                for i in range(0, count):
                    l.append(value)
        return l.__iter__()

    def __str__(MultiSet self):
        """ return a human readable string representation

        @return: human readable string representation of the MultiSet
        @rtype: C{str}
        """
        return "{%s}" % ", ".join([str(x) for x in self])

    def __repr__(MultiSet self):
        """ return a string representation that is suitable for C{eval}

        @return: precise string representation of the MultiSet
        @rtype: C{str}
        """
        return "MultiSet([%s])" % ", ".join([repr(x) for x in self])

    def __len__(MultiSet self):
        """ number of elements, including repetitions
        @rtype: C{int}
        """
        cdef int l
        cdef object v
        l = 0
        for v in self:
            l += 1
        return l

    cdef size(MultiSet self):
        """ number of elements, excluding repetitions

        @rtype: C{int}
        """
        return len(self.domain())

    cdef int hash(MultiSet self):
        # update this function
        cdef long x = 0x345678L
        cdef long y
        dom = self.domain()
        cdef int l = len(dom)
        cdef long mult = 1000003L

        for i in dom:
            l -= 1
            y = hash(i)
            if (y == -1):
                return -1
            x = (x ^ y)
        x += 97531L
        return x

        # # 252756382 = hash("snakes.hashables.hlist")
        # cdef int h = 252756382
        # for i in self._data.items():
        #     h ^= hash(i)
        # return h

    def __hash__(Multiset self) :
        """
        """
        return self.hash()
        # cdef int x = 0x345678L
        # cdef int y
        # cdef int l = len(self._data)
        # cdef int mult = 1000003L

        # for i in self._data:
        #     l -= 1
        #     y = hash(i)
        #     if (y == -1):
        #         return -1
        #     x = (x ^ y) # ^ mult
        #     #mult += 82520L + l + l
        # x += 97531L
        # return x


        # # 252756382 = hash("snakes.hashables.hlist")
        # cdef int h = 252756382
        # for i in self._data.items():
        #     h ^= hash(i)
        # return h
        # #return reduce(operator.xor, ( [hash(i) for i in self._data.items()] ), 252756382)

    def __richcmp__(Multiset self, Multiset other, int op):
        print "richcmp !!!"
        if op == 2: # ==
            assert False

        elif op == 0: # <
            assert False

        elif op == 1: # <=
            assert False

        elif op == 3: # !=
            assert False

        elif op == 4: # >
            assert False

        elif op == 5: # >=
            assert False

        else:
            assert False

    cdef int compare(Multiset self, Multiset other):
        cdef list self_types  = self._tvc.keys()
        cdef list other_types = other._tvc.keys()
        cdef list self_values_keys
        cdef list other_values_keys
        cdef dict self_values
        cdef dict other_values
        cdef object type_name
        cdef object val
        try:
            if self_types < other_types:
                return -1
            elif self_types > other_types:
                return 1
            else: # self_types == other_types
                for type_name in self._tvc:
                    self_values  = self._tvc[type_name]
                    other_values = other._tvc[type_name]

                    self_values_keys  = self_values.keys()
                    other_values_keys = other_values.keys()

                    if self_values_keys < other_values_keys:
                        return -1
                    elif self_values_keys > other_values_keys:
                        return 1
                    else: # self_values == other_values.values
                        for val in self_values_keys:
                            if self_values[val] < other_values[val]:
                                return -1
                            elif self_values[val] > other_values[val]:
                                return 1
                            else:
                                continue
                        #endif                    
                    #endif
                return 0
        #endif
        except KeyError as e:
            print e
            print

    cdef update(Multiset self, Multiset other):
        for elt in other:
            self.add(elt)

    cdef list domain(Multiset self):
        cdef list keys = []
        cdef dict values
        for values in self._tvc:
            keys.extend(values.keys)
        return keys


if __name__ == '__main__':
    import doctest
    doctest.testmod()
