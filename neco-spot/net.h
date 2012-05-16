#ifndef __PYX_HAVE__net
#define __PYX_HAVE__net

struct Marking;

#ifndef __PYX_HAVE_API__net

#ifndef __PYX_EXTERN_C
  #ifdef __cplusplus
    #define __PYX_EXTERN_C extern "C"
  #else
    #define __PYX_EXTERN_C extern
  #endif
#endif

__PYX_EXTERN_C DL_IMPORT(PyTypeObject) MarkingType;

__PYX_EXTERN_C DL_IMPORT(int) neco_marking_hash(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(struct Marking) *neco_marking_copy(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(int) neco_marking_compare(struct Marking *, struct Marking *);
__PYX_EXTERN_C DL_IMPORT(char) *neco_marking_dump(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(struct Marking) *neco_init(void);
__PYX_EXTERN_C DL_IMPORT(PyObject) *succs(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(neco_list_t) *neco_succs(struct Marking *);

#endif /* !__PYX_HAVE_API__net */

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC initnet(void);
#else
PyMODINIT_FUNC PyInit_net(void);
#endif

#endif /* !__PYX_HAVE__net */
