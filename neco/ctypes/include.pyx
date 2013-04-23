import sys
from time import time

cdef class NecoCtx:
    def __cinit__(self):
        self.state_space = set()
        self.pid_free_hash = set()
        self.remaining = set() 

cdef public api NecoCtx neco_ctx(Marking mrk):
    cdef NecoCtx ctx = NecoCtx()
    ctx.remaining = set([mrk])
    return ctx

cpdef dump(object obj):
    if hasattr(obj, '__dump__'):
        return obj.__dump__()
    else:
        return repr(obj)
    
cdef public api ctypes_ext.neco_list_t* neco_succs(Marking m, NecoCtx ctx):
    cdef ctypes_ext.neco_list_t* l = new ctypes_ext.neco_list_t()
    cdef Marking e

    for e in succs(m, ctx):
        ctypes_ext.__Pyx_INCREF(e)
        l.push_back( <void*>e )
    return l

cpdef state_space():
    cdef set visited
    cdef set visit
    cdef set succ
    cdef int count
    cdef NecoCtx ctx = NecoCtx()
    #cdef int last_count = 0
    start = time()
    last_time = start
    try:
        visited = set()
        visit = set([init()])
        succ = set()
        count = 0
        start = time()
        while True:
            count += 1
            m = visit.pop()
            visited.add(m)
            succ = succs(m, ctx)
            visit.update(succ.difference(visited))
            if (count % 250 == 0):
                new_time = time()
                elapsed_time = new_time - start
                sys.stdout.write("\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)".format(count,
                                                                                                           elapsed_time,
                                                                                                           count / elapsed_time,
                                                                                                           100 / (new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time
    except KeyError:
        print
        return visited
    return visited

cpdef state_space_graph():
    """ State space exploration function with on the fly marking dump. """
    cdef NecoCtx ctx = NecoCtx() 
    cdef set visit
    cdef set visited = set()
    cdef set succ
    cdef int count = 0
    cdef int next = 1
    cdef dict graph = {}
    cdef dict mrk_id_map = {}
    cdef list succ_list = []
    start = time()
    last_time = start

    cdef Marking m = init()
    cdef Marking s_mrk

    visit = set([m])
    mrk_id_map[m] = next
    next += 1

    try:
        while True:
            count += 1
            m = visit.pop()
            visited.add(m)

            # new marking, get the id
            current_node_id = mrk_id_map[m]
            succ = succs(m, ctx)
            succ_list = []

            for s_mrk in succ:
                if mrk_id_map.has_key(s_mrk):
                    node_id = mrk_id_map[s_mrk]
                    succ_list.append(node_id)
                else:
                    node_id = next
                    next += 1
                    succ_list.append(node_id)
                    mrk_id_map[s_mrk] = node_id

            graph[current_node_id] = succ_list

            visit.update(succ.difference(visited))
            if (count % 250 == 0):
                new_time = time()
                elapsed_time = new_time - start
                sys.stdout.write("\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)".format(count,
                                                                                                           elapsed_time,
                                                                                                           count / elapsed_time,
                                                                                                           250 / (new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time
    except KeyError:
        print
        return graph, mrk_id_map
    return graph, mrk_id_map

cpdef state_space_mcc():
    cdef set visited
    cdef set visit
    cdef set succ
    cdef int count
    cdef NecoCtx ctx = NecoCtx()
    try:
        visited = set()
        visit = set([init()])
        succ = set()
        count = 0
        while True:
            count += 1
            m = visit.pop()
            visited.add(m)
            succ = succs(m, ctx)
            visit.update(succ.difference(visited))
    except KeyError:
        return visited
    return visited
