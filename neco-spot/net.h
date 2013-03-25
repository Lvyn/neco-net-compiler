#ifndef __PYX_HAVE__net
#define __PYX_HAVE__net

struct NecoCtx;
struct Marking;

/* "net.pxd":3
 * cimport neco.ctypes.ctypes_ext as ctypes_ext
 * 
 * cdef public class NecoCtx(object)[object NecoCtx, type NecoCtxType]:             # <<<<<<<<<<<<<<
 *     cdef public set state_space
 *     cdef public set pid_free_hash
 */
struct NecoCtx {
  PyObject_HEAD
  PyObject *state_space;
  PyObject *pid_free_hash;
  PyObject *remaining;
};

/* "net.pxd":9
 * 
 * 
 * cdef public class Marking(object)[object Marking, type MarkingType]:             # <<<<<<<<<<<<<<
 *     cdef short _n2 	# s2 - BlackToken
 *     cdef short _n3 	# s1 - BlackToken
 */
struct Marking {
  PyObject_HEAD
  struct __pyx_vtabstruct_3net_Marking *__pyx_vtab;
  short _n2;
  short _n3;
};

#ifndef __PYX_HAVE_API__net

#ifndef __PYX_EXTERN_C
  #ifdef __cplusplus
    #define __PYX_EXTERN_C extern "C"
  #else
    #define __PYX_EXTERN_C extern
  #endif
#endif

__PYX_EXTERN_C DL_IMPORT(PyTypeObject) NecoCtxType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) MarkingType;

__PYX_EXTERN_C DL_IMPORT(struct NecoCtx) *neco_ctx(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(neco_list_t) *neco_succs(struct Marking *, struct NecoCtx *);
__PYX_EXTERN_C DL_IMPORT(char) *neco_marking_dump(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(struct Marking) *neco_marking_copy(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(int) neco_marking_compare(struct Marking *, struct Marking *);
__PYX_EXTERN_C DL_IMPORT(int) neco_marking_hash(struct Marking *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *succs_0(struct Marking *, PyObject *, struct NecoCtx *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *succs(struct Marking *, struct NecoCtx *, int __pyx_skip_dispatch);
__PYX_EXTERN_C DL_IMPORT(struct Marking) *neco_init(void);

#endif /* !__PYX_HAVE_API__net */

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC initnet(void);
#else
PyMODINIT_FUNC PyInit_net(void);
#endif

#endif /* !__PYX_HAVE__net */
