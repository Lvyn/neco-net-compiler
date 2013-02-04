import sys

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

cpdef state_space():
    cdef set visited
    cdef set visit
    cdef set succ
    cdef NecoCtx ctx = NecoCtx()
    
    
    #cdef int last_count = 0
    try:
        visited = set()
        visit = set([init()])
        succ = set()
        count = 0
        
        ctx.remaining = visit
        ctx.state_space = visited
        ctx.pid_free_hash = set()

        while True:
            m = visit.pop()
            visited.add(m)
            succ = succs(m, ctx)
            visit.update(succ.difference(visited))
    except KeyError:
        return visited
    return visited

cpdef state_space_graph():
    cdef set visit
    cdef set visited = set()
    cdef set succ
    cdef int next = 1
    cdef dict graph = {}
    cdef dict mrk_id_map = {}
    cdef list succ_list = []

    cdef NecoCtx ctx = NecoCtx()
    
    cdef Marking m = init()
    cdef Marking s_mrk

    visit = set([m])
    mrk_id_map[m] = next
    next += 1

    ctx.remaining = visit
    ctx.state_space = visited
    ctx.pid_free_hash = set()
    
    try:
        while True:
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
    except KeyError:
        return graph, mrk_id_map
    return graph, mrk_id_map
