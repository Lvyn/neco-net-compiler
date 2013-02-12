cdef extern from "ctypes.h":
        void __Pyx_INCREF(object o)
        cdef cppclass TGenericPlaceType[T]:
                TGenericPlaceType()
                TGenericPlaceType(TGenericPlaceType[T]&)

                void decrement_ref()
                void increment_ref()

                int equals(TGenericPlaceType[T]&)
                int compare(TGenericPlaceType[T]&)
                int hash()
                int not_empty()

                clean()

                void add(T& value)
                void remove_by_value(T&)
                void remove_by_index(int)

                T& get(int)
                int size()
                void update(TGenericPlaceType[T]&)
                char* cstr()

        cdef cppclass TPid[T]:
                TPid()
                TPid(int i)
                TPid(TPid[T]& pid)
                TPid(TPid[T]& pid, int next)
                bint operator == (TPid[T]& right)
                int compare(TPid[T]& right)

        cdef cppclass Pair[T1, T2]:
                T1 get_first()
                T2 get_second()

        cdef cppclass TGeneratorPlaceType[PidType, CounterType]:
                TGeneratorPlaceType()
                TGeneratorPlaceType(TGeneratorPlaceType[PidType, CounterType]&)

                void increment_ref()
                void decrement_ref()

                void update_pid_counter(PidType&, CounterType&)
                void remove_pid(PidType&)
                char* cstr()
                Pair[PidType, CounterType] get(int)

                int size()
                int hash()
                int compare(TGeneratorPlaceType[PidType, CounterType]&)

        cdef cppclass neco_list_t:
                neco_list_t()
                void push_back(void*)
                int size()

    # ctypedef struct neco_list_node_t:
    #     pass

    # ctypedef struct neco_list_t:
    #     pass

    # neco_list_t* neco_list_new()
    # void neco_list_push_front(neco_list_t* list, object elt)
    # void neco_list_delete(neco_list_t* list, deletion_callback del)
    # neco_list_node_t* neco_list_first(neco_list_t* list)
    # neco_list_node_t* neco_list_node_next(neco_list_node_t* node)


cdef class MultiSet:
        cdef dict _data

        cdef MultiSet copy(MultiSet self)
        cdef void add(MultiSet self, object elt)
        cdef add_items(self, items)
        cdef void remove(MultiSet self, elt)
        cdef int size(MultiSet self)
        cdef int hash(MultiSet self)
        cdef int compare(MultiSet self, MultiSet other)
        cdef void update(MultiSet self, MultiSet other)
        cdef list domain(MultiSet self)
        cpdef __dump__(MultiSet self)
        cdef has_key(MultiSet self, object key)

cdef api class Pid[object Pid, type Pid]:
        cdef TPid[int]* mPid

# cdef class Pid:
#       cdef list data

#       cpdef copy_update(Pid self, Pid other)
#       cpdef Pid copy(Pid self)
#       cpdef append(Pid self, int frag)
#       cpdef Pid subpid(Pid self, int begin, int end)
#       cpdef int at(Pid self, int i)
#       cpdef Pid prefix(Pid self)
#       cpdef Pid suffix(Pid self)
#       cpdef int ends_with(Pid self)
#       cdef int cmp(Pid self, Pid other)
#       cpdef Pid next(Pid self, int pid_component)
#       cpdef int parent(Pid self, Pid other)
#       cpdef int parent1(Pid self, Pid other)
#       cpdef int sibling(Pid self, Pid other)
#       cpdef int sibling1(Pid self, Pid other)
#       cdef int hash(Pid self)

# cdef Pid initial_pid()

# cdef list pid_place_type_copy(list origin)
# cdef int pid_place_type_hash(list place)
# cdef int pid_place_type_cmp(list l, list r)

# cdef MultiSet int_place_type_to_multiset(int_place_type_t* pt)

# cdef int list_hash(list l)
# cdef int generator_place_type_hash(dict generator)
# cdef dict generator_place_type_copy(dict generator)
# cdef generator_place_type_cstr(dict generator)
# cdef int generator_place_type_cmp(dict left, dict right)
# cdef pid_place_type_cstr(list pid)

cdef MultiSet int_place_type_to_multiset(TGenericPlaceType[int]* place_type)

