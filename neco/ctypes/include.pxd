cimport neco.ctypes.ctypes_ext as ctypes_ext

cdef public class NecoCtx(object)[object NecoCtx, type NecoCtxType]:
    cdef set state_space
    cdef set pid_free_hash
    cdef set remaining
 