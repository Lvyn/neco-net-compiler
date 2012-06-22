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
    # cdef dict _data

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
        cdef int res = self.compare(other)
        print "cmp op {}, res {}".format(op, res)
        if op == 0:
            return res < 0
        elif op == 1:
            return res <= 0
        elif op == 2:
            return res == 0
        elif op == 3:
            return res != 0
        elif op == 4:
            return res > 0
        elif op == 5:
            return res >= 0
        
    cdef void update(MultiSet self, MultiSet other):
        self._data.update(self, other._data)

    cdef list domain(MultiSet self):
        return self._data.keys()


    cpdef __dump__(MultiSet self):
        cdef list elts = []

        for elt, count in self._data.iteritems():
            elts.extend( [dump(elt)] * count )

        return '[' + ', '.join(elts) + ']'

    cdef has_key(MultiSet self, object key):
        return self._data.has_key(key)


cdef class Pid:
    
    cdef int_place_type_t* data
    
    def __cinit__(Pid self):
        self.data = int_place_type_new()
            
    cpdef copy_update(Pid self, Pid other):
        cdef int size = int_place_type_size(other.data)
        for i in range(0, size):
            int_place_type_add(self.data, int_place_type_get(other.data, i))
                               
    cpdef Pid copy(Pid self):
        cdef Pid pid = Pid()
        pid.copy_update(self)
        return pid
    
    cpdef append(Pid self, int frag):
        int_place_type_add(self.data, frag)
    
    def __len__(Pid self):
        return int_place_type_size(self.data)
    
    def __str__(Pid self):
        cdef list l = []
        cdef int val
        cdef int_place_type_t* data = self.data
        cdef int size = int_place_type_size(data)
        
        for i in range(0, size):
            val = int_place_type_get(data, i)
            l.append(val)
        
        return '.'.join([repr(e) for e in l])
    
    cpdef Pid subpid(self, begin, end):
        cdef Pid pid = Pid()
        cdef int_place_type_t* data = self.data
        cdef int_place_type_t* other_data = pid.data
        cdef int value
        for i in range(begin, end):
            value = int_place_type_get(data, i)
            int_place_type_add(other_data, value)
        return pid
        
    cpdef int at(Pid self, int i):
        return int_place_type_get(self.data, i)
    
    cpdef Pid prefix(Pid self): 
        cdef int value
        cdef int_place_type_t* data = self.data
        cdef int size = int_place_type_size(data)
        cdef Pid pid = Pid()
        for i in range(0, size-1):
            value = int_place_type_get(data, i)
            pid.append( value )
        return pid
    
    cpdef Pid suffix(Pid self):
        cdef int value
        cdef int_place_type_t* data = self.data
        cdef int size = int_place_type_size(data)
        cdef Pid pid = Pid()
        for i in range(1, size):
            value = int_place_type_get(data, i)
            pid.append( value )
        return pid
    
    cpdef int ends_with(Pid self):
        cdef int_place_type_t* data = self.data
        cdef int size = int_place_type_size(data)
        return int_place_type_get(data, size)
    
    def __hash__(Pid self):
        cdef int_place_type_t* data = self.data
        return int_place_type_hash(data)
    
    def __richcmp__(Pid self, Pid other, int op):
        cdef int cmp = int_place_type_cmp(self.data, other.data)
        if op == 0: # <
            return cmp < 0
        elif op == 1: # <=
            return cmp <= 0
        elif op == 2: # ==
            return cmp == 0
        elif op == 3: # !=
            return cmp != 0
        elif op == 4: # >
            return cmp > 0
        else: # op == 5: # >=
            return cmp >= 0
    
    cpdef Pid next(Pid self, int pid_component):
        cdef Pid p = self.copy()
        p.append(pid_component + 1)
        return p
    
    cpdef int parent(Pid self, Pid other):
        cdef int_place_type_t* self_data  = self.data
        cdef int_place_type_t* other_data = other.data
        cdef int self_size  = int_place_type_size(self_data)
        cdef int other_size = int_place_type_size(other_data)
        cdef int i
        cdef self_value
        cdef other_value
        
        if self_size >= other_size:
            return 0
        
        for i in range(0, self_size):
            self_value  = int_place_type_get(self_data, i)
            other_value = int_place_type_get(other_data, i)
            if self_value != other_value:
                return 0
        return 1

    cpdef int parent1(Pid self, Pid other):
        cdef int_place_type_t* self_data  = self.data
        cdef int_place_type_t* other_data = other.data
        cdef int self_size  = int_place_type_size(self_data)
        cdef int other_size = int_place_type_size(other_data)
        cdef int i
        cdef int self_value
        cdef int other_value
        
        if (self_size + 1) != other_size:
            return 0
        
        for i in range(0, self_size):
            self_value  = int_place_type_get(self_data, i)
            other_value = int_place_type_get(other_data, i)
            if self_value != other_value:
                return 0
        return 1

    cpdef int sibling(Pid self, Pid other):
        cdef int_place_type_t* self_data  = self.data
        cdef int_place_type_t* other_data = other.data
        cdef int self_size  = int_place_type_size(self_data)
        cdef int other_size = int_place_type_size(other_data)
        cdef int i
        cdef int self_value
        cdef int other_value
        cdef int max_i = self_size - 1
        
        # must have same size
        if self_size != other_size:
            return 0
        
        # equal prefixes
        for i in range(0, max_i):
            self_value  = int_place_type_get(self_data, i)
            other_value = int_place_type_get(other_data, i)
            if self_value != other_value:
                return 0
            
        # sibling test
        self_value  = int_place_type_get(self_data, max_i)
        other_value = int_place_type_get(other_data, max_i)
        return self_value < other_value
    
    cpdef int sibling1(Pid self, Pid other):
        cdef int_place_type_t* self_data  = self.data
        cdef int_place_type_t* other_data = other.data
        cdef int self_size  = int_place_type_size(self_data)
        cdef int other_size = int_place_type_size(other_data)
        cdef int i
        cdef int self_value
        cdef int other_value
        cdef int max_i = self_size - 1
        
        # must have same size
        if self_size != other_size:
            return 0
        
        # equal prefixes
        for i in range(0, max_i):
            self_value  = int_place_type_get(self_data, i)
            other_value = int_place_type_get(other_data, i)
            if self_value != other_value:
                return 0
            
        # sibling test
        self_value  = int_place_type_get(self_data, max_i)
        other_value = int_place_type_get(other_data, max_i)
        return (self_value + 1) == other_value
        
        
cdef MultiSet int_place_type_to_multiset(ctypes_ext.int_place_type_t* pt):
    cdef MultiSet ms = MultiSet()
    cdef int index = 0
    cdef int max = ctypes_ext.int_place_type_size(pt)
    cdef int value
    
    for 0 <= index < max:
        value = ctypes_ext.int_place_type_get(pt, index)
        ms.add(value)
        
    print ms.__dump__()
    return ms 


