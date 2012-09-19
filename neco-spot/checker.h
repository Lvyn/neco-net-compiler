#ifndef __PYX_HAVE__checker
#define __PYX_HAVE__checker


#ifndef __PYX_HAVE_API__checker

#ifndef __PYX_EXTERN_C
  #ifdef __cplusplus
    #define __PYX_EXTERN_C extern "C"
  #else
    #define __PYX_EXTERN_C extern
  #endif
#endif

__PYX_EXTERN_C DL_IMPORT(int) neco_check(struct Marking *, int);

#endif /* !__PYX_HAVE_API__checker */

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC initchecker(void);
#else
PyMODINIT_FUNC PyInit_checker(void);
#endif

#endif /* !__PYX_HAVE__checker */
