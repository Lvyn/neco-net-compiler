#include "ctypes.h"
#include <assert.h>
#include <stdlib.h>

/////////////////////////////////////////////////////
// int place type
/////////////////////////////////////////////////////
int* g_tab1 = NULL; // [256];// = NULL;
int* g_tab2 = NULL; // [256]; // = NULL;
int  g_tab_size = 0;

#define MAX(a, b) (a) > (b) ? (a) : (b)

int int_place_type_eq(int_place_type_t* pt1, int_place_type_t* pt2) {
    int i;
    int tmp;
    int size;

    if (pt1 == pt2)
     	return 1;

    size = pt1->size;
    tmp = size - pt2->size;
    if (tmp != 0)
	return 0; // tmp;

    //////////////////////////////////////////////////
    // ENSURE ORDERED !!!
    //////////////////////////////////////////////////

    for (i = size-1; i >= 0; i--) {
	tmp = pt1->data[i] - pt2->data[i];
	if (tmp != 0)
	    return 0;
    }
    return 1;
}


int int_place_type_hash(int_place_type_t* pt) {
    int i;
    int hash = 0; // int_hash(pt->size);
    for (i = pt->size-1; i >= 0; i--) {
	hash ^= hash << 5;
    	hash = (hash ^ pt->data[i]);
    }
    return hash;
}

int_place_type_t* int_place_type_new(void) {
    int_place_type_t* tmp = malloc(sizeof(struct int_place_type));
    int *data = malloc(INT_INIT_MAX_SIZE * sizeof(int));

    tmp->refs = 1;
    tmp->size = 0;
    tmp->max_size = INT_INIT_MAX_SIZE;
    tmp->data = data;

    return tmp;
}

int_place_type_t* int_place_type_copy(int_place_type_t* src) {
    int_place_type_t* dst = malloc(sizeof(int_place_type_t));
    int *data = malloc(src->max_size * sizeof(int));

    dst->refs = 1;
    dst->size = src->size;
    dst->max_size = src->max_size;
    dst->data = data;

    memcpy(dst->data, src->data, src->size * sizeof(int));

    return dst;
}

void int_place_type_add(int_place_type_t* pt, int value) {
    int i, j;
    if (pt->size >= pt->max_size) {
	pt->max_size += INT_RESIZE;
	int *data = realloc(pt->data, pt->max_size * sizeof(int));
	pt->data = data;
    }
    // find suitable index
    for (i = 0; i < pt->size; i++) {
	if (pt->data[i] < value)
	    continue;
	else
	    break;
    }

    // shift values
    for (j = pt->size+1; j > i; j--) {
	pt->data[j] = pt->data[j-1];
    }

    // store new value
    pt->data[i] = value;

    pt->size++;
}

void int_place_type_rem_by_value(int_place_type_t* pt, int value) {
    int index = 0;
    for (; index < pt->size; index++) {
	if (pt->data[index] == value) {
	    pt->size--;
	    pt->data[index] = pt->data[pt->size];
	    break;
	}
    }
    qsort(pt->data, pt->size, sizeof(int), int_cmp);
}

void int_place_type_update(int_place_type_t* left, int_place_type_t* right) {
    assert(0);
}

// /////////////////////////////////////////////////////
// // bool token place type
// /////////////////////////////////////////////////////

// typedef struct {
//     unsigned int positives; // true
//     unsigned int negatives; // false
// } bool_place_type;

// inline unsigned long
// bool_place_type_hash(bool_place_type *pt)
// {
//     unsigned long hash = 5381;

//     hash = ((hash << 5) ^ hash ) ^ (unsigned long)pt->positives;
//     hash = ((hash << 5) ^ hash ) ^ (unsigned long)pt->negatives;

//     return hash;
// }

// inline int
// bool_place_type_eq(bool_place_type *pt1,
// 		   bool_place_type *pt2)
// {
//     int tmp = pt1->positives - pt2->positives;
//     if (tmp != 0)
// 	return tmp;

//     return pt1->negatives - pt2->negatives;
// }

// inline int
// bool_place_type_not_empty(bool_place_type *pt)
// {
//     return (pt->positives > 0) || (pt->negatives > 0);
// }

// inline void
// bool_place_type_init(bool_place_type *pt)
// {
//     pt->positives = 0;
//     pt->negatives = 0;
// }

// inline void
// bool_place_type_add(bool_place_type *pt,
// 		    int value)
// {
//     if (value != 0)
// 	pt->positives++;
//     else
// 	pt->negatives++;
// }

// inline void
// bool_place_type_rem(bool_place_type *pt,
// 		    int index)
// {
//     if ((index == 0) && (pt->positives > 0)) {
// 	pt->positives--;
//     } else {
// 	pt->negatives--;
//     }
// }

// inline int
// bool_place_type_size(bool_place_type *pt)
// {
//     return (pt->positives > 0 ? 1 : 0)
// 	 + (pt->negatives > 0 ? 1 : 0);
// }

// inline int
// bool_place_type_retrieve(bool_place_type *pt,
// 			 int index)
// {
//     if ((index == 0) && (pt->positives > 0))
// 	return 1;
//     else
// 	return 0;
// }

// inline void
// bool_place_type_copy_init(bool_place_type *src,
// 			  bool_place_type *dst)
// {
//     dst->positives = src->positives;
//     dst->negatives = src->negatives;
// }

// inline void
// bool_place_type_dump(bool_place_type *pt)
// {
//     printf("true: %d \tfalse: %d \n", pt->positives, pt->negatives);
// }



//////////////////////////////////////////////////
// lists with iterators
// needed for SPOT
//////////////////////////////////////////////////

neco_list_t* neco_list_new() {
    neco_list_t* list = malloc(sizeof(neco_list_t));
    list->begin = NULL;
    return list;
}

int neco_list_length(neco_list_t* list) {
    neco_list_node_t* node = list->begin;
    int i = 0;
    for( ; node != NULL; node = node->next) {
	i++;
    }
    return i;
}

void neco_list_push_front(neco_list_t* list, void *elt) {
    neco_list_node_t* node;

    assert(list != NULL);

    node = malloc(sizeof(neco_list_node_t));
    node->elt = elt;
    node->next = list->begin;
    list->begin = node;
}

void neco_list_node_delete(neco_list_node_t* node, deletion_callback del) {
    if (node == NULL)
	return;

    if (del != NULL)
	del(node->elt);

    neco_list_node_delete(node->next, del);
    free(node);
}

void neco_list_delete(neco_list_t* list, deletion_callback del) {
    neco_list_node_delete(list->begin, del);
    free(list);
}
