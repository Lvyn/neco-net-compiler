cimport neco.ctypes.ctypes_ext as ctypes_ext

cdef public class NecoCtx(object)[object NecoCtx, type NecoCtxType]:
    cdef public set state_space
    cdef public set pid_free_hash
    cdef public set remaining
 