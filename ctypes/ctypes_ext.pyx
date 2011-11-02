cimport ctypes_ext # this line will be replaced in profiler mode !

import operator, sys, traceback

################################################################################
# Multisets
################################################################################
cpdef dump(object obj):
    if hasattr(obj, '__dump__'):
        return obj.__dump__()
    else:
        return repr(obj)

cpdef __neco_compare__(object left, object right):
    if left < right:
        return -1
    elif left > right:
        return 1
    return 0

cdef class MultiSet:
    cdef dict _data

    def __cinit__(MultiSet self, dict initial_data = {}):
        """ builds a brand new MultiSet from some initial data

        @param initial_data: list of elements (eventually with repetitions
        @type initial_data: C{dict}
        """
        self._data = {}
        self._data.update(initial_data)

    cdef MultiSet copy(MultiSet self):
        """ copy the MultiSet

        @return: a copy of the MultiSet
        @rtype: C{MultiSet}
        """
        cdef MultiSet result = MultiSet(self._data)
        return result

    def __add__(MultiSet self, MultiSet other):
        cdef MultiSet new = self.copy()
        for (e, m) in other._data.iteritems():
            try:
                new._data[e] += m
            except IndexError:
                new._data[e] = m
        return new

    cdef void add(MultiSet self, object elt):
        """ adds an element to the MultiSet

        @param elt: element to be added
        @type elt: C{object}
        """
        try :
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
        """ iterator over the values (with repetitions)
        """
        for e, m in self._data.iteritems():
            for i in range(0, m):
                yield e
        #return self._data.__iter__()

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
        #cdef long mult = 1000003L

        for i in self._data:
            l -= 1
            y = hash(i)
            if (y == -1):
                return -1
            x = (x ^ y)
        x += 97531L
        return x

    def __hash__ (MultiSet self) :
        """
        """
        cdef int x = 0x345678L
        cdef int y
        cdef int l = len(self._data)
        #cdef int mult = 1000003L

        for i in self._data:
            l -= 1
            y = hash(i)
            if (y == -1):
                return -1
            x = (x ^ y) # ^ mult
            #mult += 82520L + l + l
        x += 97531L
        return x

    cdef int compare(MultiSet self, MultiSet other):
        cdef list self_keys = self._data.keys()
        cdef list other_keys = other._data.keys()
        cdef int l1
        cdef int l2
        cdef int i = 0
        # ensure we are working on sorted domain
        self_keys.sort()
        other_keys.sort()
        l1 = len(self_keys)
        if self_keys == other_keys: # may be equal
            for 0 <= i < l1:
                key = self_keys[i]
                v1 = self._data[key]
                v2 = other._data[key]
                if v1 < v2:
                    return -1
                elif v1 > v2:
                    return 1
                continue
            return 0
        else: # definitely not equal
            l2 = len(other_keys)
            if l1 < l2: # smaller domain is smaller
                return -1
            elif l1 > l2: # bigger domain is bigger
                return 1
            else: # equal domain but different keys !
                #other_keys.sort() # ensure the domain is sorted
                assert (l1 == l2)
                for 0 <= i < l1:
                    left = self_keys[i]
                    right = other_keys[i]
                    if left.__class__ < right.__class__:
                        return -1
                    elif left.__class__ > right.__class__:
                        return 1
                    else:
                        if left < right:
                            return -1
                        elif left > right:
                            return 1
                # something get wrong here
                print >> sys.stderr, "WRONG"

                for 0 <= i < l1:
                    left = self_keys[i]
                    right = other_keys[i]
                    print >> sys.stderr  "left  : ", left
                    print >> sys.stderr  "right : ", right
                    print >> sys.stderr  "cl< : ", left.__class__ < right.__class__, " cl> : ", left.__class__ > right.__class__, " < : ", left < right, " > : ", left > right, " == ", left == right

                assert(False)

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
        cdef list elts = []

        for elt, count in self._data.iteritems():
            elts.extend( [dump(elt)] * count )

        return '[' + ', '.join(elts) + ']'

################################################################################

cpdef state_space():
    cdef set visited
    cdef set visit
    cdef set succ
    cdef int count
    #cdef int last_count = 0
    start = time()
    last_time = start
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
            if (count % 250 == 0):
                new_time = time()
                elapsed_time = new_time - start
                sys.stdout.write("\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)".format(count,
                                                                                                           elapsed_time,
                                                                                                           count / elapsed_time,
                                                                                                           100 / (new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time
    except KeyError:
        print
        return visited
    return visited


cpdef state_space_graph():
    """ State space exploration function with on the fly marking dump. """
    cdef set visit
    cdef set visited = set()
    cdef set succ
    cdef int count = 0
    cdef int next = 1
    cdef dict graph = {}
    cdef dict mrk_id_map = {}
    cdef list succ_list = []
    start = time()
    last_time = start

    cdef Marking m = init()
    cdef Marking s_mrk

    visit = set([m])
    mrk_id_map[m] = next
    next += 1

    try:
        while True:
            count += 1
            m = visit.pop()
            visited.add(m)

            # new marking, get the id
            current_node_id = mrk_id_map[m]
            succ = succs(m)
            succ_list = []

            for s_mrk in succ:
                if mrk_id_map.has_key(s_mrk):
                    node_id = mrk_id_map[s_mrk]
                    succ_list.append(node_id)
                else:
                    node_id = next
                    next += 1
                    succ_list.append(node_id)
                    mrk_id_map[s_mrk] = node_id

            graph[current_node_id] = succ_list

            visit.update(succ.difference(visited))
            if (count % 250 == 0):
                new_time = time()
                elapsed_time = new_time - start
                sys.stdout.write("\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)".format(count,
                                                                                                           elapsed_time,
                                                                                                           count / elapsed_time,
                                                                                                           250 / (new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time
    except KeyError:
        print
        return graph, mrk_id_map
    return graph, mrk_id_map
