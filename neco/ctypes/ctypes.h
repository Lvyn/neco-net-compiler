#ifndef _CTYPES_H_
#define _CTYPES_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <memory.h>
#include <stdlib.h>
#include <assert.h>

#define INT_INIT_MAX_SIZE 2
#define INT_RESIZE 4

/////////////////////////////////////////////////////
// int place type
/////////////////////////////////////////////////////

inline int int_cmp(const void* a, const void* b) {
    return *(int*)a - *(int*)b;
}

inline unsigned int int_hash(int a) {
    unsigned int hash = a;
    hash = hash ^ (hash>>4);
    hash = (hash^0xdeadbeef) + (hash<<5);
    hash = hash ^ (hash>>11);
    return hash;
}

typedef struct int_place_type {
    int refs;
    int size;
    int max_size;
    int *data;
} int_place_type_t;

char* int_place_type_cstr(int_place_type_t* pt);

int int_place_type_eq(int_place_type_t* pt1, int_place_type_t* pt2);

int int_place_type_cmp(int_place_type_t* pt1, int_place_type_t* pt2);

int int_place_type_hash(int_place_type_t* pt);

int_place_type_t* int_place_type_new(void);

void int_place_type_init(int_place_type_t* pt);

inline void int_place_type_free(int_place_type_t* pt) {
    pt->refs--;
    if (pt->refs == 0) {
	free(pt->data);
	free(pt);
    }
}

int_place_type_t* int_place_type_copy(int_place_type_t* orig);

inline int_place_type_t* int_place_type_light_copy(int_place_type_t* orig) {
    orig->refs++;
    return orig;
}

#include <assert.h>
inline void int_place_type_clean(int_place_type_t* pt) {
    assert(0);
    pt->size = 0;
}

inline int int_place_type_not_empty(int_place_type_t* pt) {
    return pt->size > 0;
}
void int_delete_place_type(int_place_type_t* pt);

void int_place_type_add(int_place_type_t* pt, int value);

inline void int_place_type_rem_by_index(int_place_type_t* pt, int index) {
    int i;
    pt->size--;
    for (i = index; i < pt->size; i++)
     	pt->data[i] = pt->data[i+1];
}

void int_place_type_rem_by_value(int_place_type_t* pt, int value);

inline int int_place_type_get(int_place_type_t* pt, int index) {
    return pt->data[index];
}

inline int int_place_type_size(int_place_type_t* pt) {
    return pt->size;
}

void int_place_type_update(int_place_type_t* left, int_place_type_t* right);

//////////////////////////////////////////////////

inline void structure_copy(void* dst, void* src, int n) {
    memcpy(dst, src, n);
}

inline int structure_cmp(void* dst, void* src, int n) {
    return strncmp((char*)dst, (char*)src, n) == 0;
}

inline int structure_to_int(void* dst, int i) {
    return ((int *)dst)[i];
}

inline int structure_to_char(void* dst, int i) {
    return ((char *)dst)[i];
}

// #define TO_ADDR(x) &(x)

//////////////////////////////////////////////////
// lists with iterators
// needed for SPOT
//////////////////////////////////////////////////

typedef struct neco_list_node {
    void *elt;
    struct neco_list_node* next;
} neco_list_node_t;

typedef struct neco_list {
    neco_list_node_t* begin;
} neco_list_t;

neco_list_t* neco_list_new(void);

int neco_list_length(neco_list_t* list);

void neco_list_push_front(neco_list_t* list, void *elt);

typedef void (*deletion_callback)(void *);

void neco_list_delete(neco_list_t* list, deletion_callback del);

// inline neco_list_node_t* neco_list_first(neco_list_t* list) {
//     return list->begin;
// }

// inline neco_list_node_t* neco_list_node_next(neco_list_node_t* node) {
//     return node->next;
// }

#ifdef __cplusplus
} // extern "C"
#endif

#endif /* _CTYPES_H_ */
