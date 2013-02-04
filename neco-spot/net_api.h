#ifndef __PYX_HAVE_API__net
#define __PYX_HAVE_API__net
#include "Python.h"
#include "net.h"

static struct NecoCtx *(*__pyx_f_3net_neco_ctx)(struct Marking *) = 0;
#define neco_ctx __pyx_f_3net_neco_ctx
static neco_list_t *(*__pyx_f_3net_neco_succs)(struct Marking *, struct NecoCtx *) = 0;
#define neco_succs __pyx_f_3net_neco_succs
static char *(*__pyx_f_3net_neco_marking_dump)(struct Marking *) = 0;
#define neco_marking_dump __pyx_f_3net_neco_marking_dump
static struct Marking *(*__pyx_f_3net_neco_marking_copy)(struct Marking *) = 0;
#define neco_marking_copy __pyx_f_3net_neco_marking_copy
static int (*__pyx_f_3net_neco_marking_compare)(struct Marking *, struct Marking *) = 0;
#define neco_marking_compare __pyx_f_3net_neco_marking_compare
static int (*__pyx_f_3net_neco_marking_hash)(struct Marking *) = 0;
#define neco_marking_hash __pyx_f_3net_neco_marking_hash
static PyObject *(*__pyx_f_3net_succs)(struct Marking *, struct NecoCtx *) = 0;
#define succs __pyx_f_3net_succs
static struct Marking *(*__pyx_f_3net_neco_init)(void) = 0;
#define neco_init __pyx_f_3net_neco_init


#if !defined(__Pyx_PyIdentifier_FromString)
#if PY_MAJOR_VERSION < 3
  #define __Pyx_PyIdentifier_FromString(s) PyString_FromString(s)
#else
  #define __Pyx_PyIdentifier_FromString(s) PyUnicode_FromString(s)
#endif
#endif

















#ifndef __PYX_HAVE_RT_ImportModule
#define __PYX_HAVE_RT_ImportModule
static PyObject *__Pyx_ImportModule(const char *name) {
    PyObject *py_name = 0;
    PyObject *py_module = 0;

    py_name = __Pyx_PyIdentifier_FromString(name);
    if (!py_name)
        goto bad;
    py_module = PyImport_Import(py_name);
    Py_DECREF(py_name);
    return py_module;
bad:
    Py_XDECREF(py_name);
    return 0;
}
#endif







































































































#ifndef __PYX_HAVE_RT_ImportFunction
#define __PYX_HAVE_RT_ImportFunction
static int __Pyx_ImportFunction(PyObject *module, const char *funcname, void (**f)(void), const char *sig) {
    PyObject *d = 0;
    PyObject *cobj = 0;
    union {
        void (*fp)(void);
        void *p;
    } tmp;

    d = PyObject_GetAttrString(module, (char *)"__pyx_capi__");
    if (!d)
        goto bad;
    cobj = PyDict_GetItemString(d, funcname);
    if (!cobj) {
        PyErr_Format(PyExc_ImportError,
            "%s does not export expected C function %s",
                PyModule_GetName(module), funcname);
        goto bad;
    }
#if PY_VERSION_HEX >= 0x02070000 && !(PY_MAJOR_VERSION==3 && PY_MINOR_VERSION==0)
    if (!PyCapsule_IsValid(cobj, sig)) {
        PyErr_Format(PyExc_TypeError,
            "C function %s.%s has wrong signature (expected %s, got %s)",
             PyModule_GetName(module), funcname, sig, PyCapsule_GetName(cobj));
        goto bad;
    }
    tmp.p = PyCapsule_GetPointer(cobj, sig);
#else
    {const char *desc, *s1, *s2;
    desc = (const char *)PyCObject_GetDesc(cobj);
    if (!desc)
        goto bad;
    s1 = desc; s2 = sig;
    while (*s1 != '\0' && *s1 == *s2) { s1++; s2++; }
    if (*s1 != *s2) {
        PyErr_Format(PyExc_TypeError,
            "C function %s.%s has wrong signature (expected %s, got %s)",
             PyModule_GetName(module), funcname, sig, desc);
        goto bad;
    }
    tmp.p = PyCObject_AsVoidPtr(cobj);}
#endif
    *f = tmp.fp;
    if (!(*f))
        goto bad;
    Py_DECREF(d);
    return 0;
bad:
    Py_XDECREF(d);
    return -1;
}
#endif

static int import_net(void) {
  PyObject *module = 0;
  module = __Pyx_ImportModule("net");
  if (!module) goto bad;
  if (__Pyx_ImportFunction(module, "neco_ctx", (void (**)(void))&__pyx_f_3net_neco_ctx, "struct NecoCtx *(struct Marking *)") < 0) goto bad;
  if (__Pyx_ImportFunction(module, "neco_succs", (void (**)(void))&__pyx_f_3net_neco_succs, "neco_list_t *(struct Marking *, struct NecoCtx *)") < 0) goto bad;
  if (__Pyx_ImportFunction(module, "neco_marking_dump", (void (**)(void))&__pyx_f_3net_neco_marking_dump, "char *(struct Marking *)") < 0) goto bad;
  if (__Pyx_ImportFunction(module, "neco_marking_copy", (void (**)(void))&__pyx_f_3net_neco_marking_copy, "struct Marking *(struct Marking *)") < 0) goto bad;
  if (__Pyx_ImportFunction(module, "neco_marking_compare", (void (**)(void))&__pyx_f_3net_neco_marking_compare, "int (struct Marking *, struct Marking *)") < 0) goto bad;
  if (__Pyx_ImportFunction(module, "neco_marking_hash", (void (**)(void))&__pyx_f_3net_neco_marking_hash, "int (struct Marking *)") < 0) goto bad;
  if (__Pyx_ImportFunction(module, "succs", (void (**)(void))&__pyx_f_3net_succs, "PyObject *(struct Marking *, struct NecoCtx *)") < 0) goto bad;
  if (__Pyx_ImportFunction(module, "neco_init", (void (**)(void))&__pyx_f_3net_neco_init, "struct Marking *(void)") < 0) goto bad;
  Py_DECREF(module); module = 0;
  return 0;
  bad:
  Py_XDECREF(module);
  return -1;
}

#endif /* !__PYX_HAVE_API__net */
