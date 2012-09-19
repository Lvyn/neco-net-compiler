#include "ctypes.h"

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
//
//neco_list_t* neco_list_new() {
//    neco_list_t* list = malloc(sizeof(neco_list_t));
//    list->begin = NULL;
//    return list;
//}
//
//int neco_list_length(neco_list_t* list) {
//    neco_list_node_t* node = list->begin;
//    int i = 0;
//    for( ; node != NULL; node = node->next) {
//	i++;
//    }
//    return i;
//}
//
//void neco_list_push_front(neco_list_t* list, void *elt) {
//    neco_list_node_t* node;
//
//    assert(list != NULL);
//
//    node = malloc(sizeof(neco_list_node_t));
//    node->elt = elt;
//    node->next = list->begin;
//    list->begin = node;
//}
//
//void neco_list_node_delete(neco_list_node_t* node, deletion_callback del) {
//    if (node == NULL)
//	return;
//
//    if (del != NULL)
//	del(node->elt);
//
//    neco_list_node_delete(node->next, del);
//    free(node);
//}
//
//void neco_list_delete(neco_list_t* list, deletion_callback del) {
//    neco_list_node_delete(list->begin, del);
//    free(list);
//}
