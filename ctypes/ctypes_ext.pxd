
cdef extern from "ctypes.h":
    cdef struct int_place_type:
        pass

    cdef int int_place_type_eq(int_place_type* pt1, int_place_type* pt2)
    cdef int int_place_type_cmp(int_place_type* pt1, int_place_type* pt2)
    cdef int int_place_type_hash(int_place_type* pt)
    cdef int int_place_type_not_empty(int_place_type* pt)

    cdef int_place_type* int_place_type_new()
    cdef void int_place_type_free(int_place_type* dst)
    cdef int_place_type* int_place_type_copy(int_place_type* origin)
    cdef int_place_type* int_place_type_light_copy(int_place_type* origin)
    cdef void int_place_type_clean(int_place_type *pt)

    cdef void int_place_type_add(int_place_type *pt, int value)
    cdef void int_place_type_rem_by_index(int_place_type *pt, int index)
    cdef void int_place_type_rem_by_value(int_place_type *pt, int index)

    cdef int int_place_type_get(int_place_type* pt, int index)
    cdef int int_place_type_size(int_place_type* pt)
    cdef void int_place_type_update(int_place_type* left, int_place_type* right)
    cdef char* int_place_type_cstr(int_place_type* pt)

    cdef void structure_copy(void* dst, void* src, int n)
    cdef int structure_cmp(void* dst, void* src, int n)
    cdef int  structure_to_int(void* dst, int i)
    cdef char structure_to_char(void* dst, int i)

    cdef struct neco_list_node:
        pass

    cdef struct neco_list:
        pass

    cdef neco_list* neco_list_new()
    cdef void neco_list_push_front(neco_list* list, object elt)
    # cdef void neco_list_delete(neco_list* list, deletion_callback del)
    # cdef neco_list_node* neco_list_first(neco_list* list)
    # cdef neco_list_node* neco_list_node_next(neco_list_node* node)

    cdef void __Pyx_INCREF(object o)
