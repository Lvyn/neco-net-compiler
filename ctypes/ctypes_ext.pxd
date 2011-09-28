
cdef extern from "ctypes.h":
    ctypedef struct int_place_type_t:
        pass

    int int_place_type_eq(int_place_type_t* pt1, int_place_type_t* pt2)
    int int_place_type_cmp(int_place_type_t* pt1, int_place_type_t* pt2)
    int int_place_type_hash(int_place_type_t* pt)
    int int_place_type_not_empty(int_place_type_t* pt)

    int_place_type_t* int_place_type_new()
    void int_place_type_free(int_place_type_t* dst)
    int_place_type_t* int_place_type_copy(int_place_type_t* origin)
    int_place_type_t* int_place_type_light_copy(int_place_type_t* origin)
    void int_place_type_clean(int_place_type_t *pt)

    void int_place_type_add(int_place_type_t *pt, int value)
    void int_place_type_rem_by_index(int_place_type_t *pt, int index)
    void int_place_type_rem_by_value(int_place_type_t *pt, int index)

    int int_place_type_get(int_place_type_t* pt, int index)
    int int_place_type_size(int_place_type_t* pt)
    void int_place_type_update(int_place_type_t* left, int_place_type_t* right)
    char* int_place_type_cstr(int_place_type_t* pt)

    void structure_copy(void* dst, void* src, int n)
    int structure_cmp(void* dst, void* src, int n)
    int  structure_to_int(void* dst, int i)
    char structure_to_char(void* dst, int i)

    ctypedef struct neco_list_node_t:
        pass

    ctypedef struct neco_list_t:
        pass

    neco_list_t* neco_list_new()
    void neco_list_push_front(neco_list_t* list, object elt)
    # void neco_list_delete(neco_list_t* list, deletion_callback del)
    # neco_list_node_t* neco_list_first(neco_list_t* list)
    # neco_list_node_t* neco_list_node_next(neco_list_node_t* node)

    void __Pyx_INCREF(object o)
