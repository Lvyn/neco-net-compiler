from time import time
import sys

def normalize_marking(marking, current_set, state_space):
#    print
#    print "HANDLING ", marking.__dump__()
#    print "CURRENT : ", current_set
#    print "ST : ", state_space
    pid_tree = marking.buildPidTree()
    pid_tree.order_tree(pid_free_marking_order)
#    pid_tree.print_structure()
    
    iter_trees = pid_tree.itertrees()
    
    default_tree = iter_trees.next()
#    print "default_tree\n", default_tree.print_structure()
    bijection = default_tree.build_map()
    default_marking = marking.copy()
#    print "biection ", bijection
    default_marking.update_pids(bijection)
#    print "P MRK (default) : ", default_marking

    if default_marking in state_space:
#        print "IN"
        return None
    if default_marking in current_set:
#        print "IN"
        return None
    
    for tree in iter_trees:
#        print "tree\n", tree.print_structure()
        bijection = tree.build_map()
        tmp = marking.copy()
#        print "biection ", bijection
        tmp.update_pids(bijection)
        
#        print "P MRK : ", tmp
        if tmp in state_space:
#            print "IN"
            return None
        if tmp in current_set:
#            print "IN"
            return None

#    print "NOT IN"
    return default_marking

def state_space():
    visited = set()
    visit = set([init()])
    succ = set()
    succs2 = set()
    count = 0
    start = time()
    last_time = start

    try:
        while True:
            m = visit.pop()
            count+=1

            visited.add(m)
            succ = succs(m,visited)
            succs2 = succ.difference(visited)
            visit.update(succs2)
            succ.clear()
            succs2.clear()
            if (count % 250 == 0):
                new_time = time()
                elapsed_time = new_time - start
                sys.stdout.write('\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)'.format(count,
                                                                                                           elapsed_time,
                                                                                                           count / elapsed_time,
                                                                                                           100/(new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time

    except KeyError:
        pass
    print
    return visited


def state_space_graph():
    visited = set()
    count = 0
    next = 1
    graph = {}
    mrk_id_map = {}
    succ_list = []
    start = time()
    last_time = start

    m = init()

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
            succ = succs(m, visited)
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
                sys.stdout.write('\r{}st {:5.3f}s (global {:5.0f}st/s, since last log {:5.0f}st/s)'.format(count,
                                                                                                            elapsed_time,
                                                                                                            count / elapsed_time,
                                                                                                            250 / (new_time-last_time)))
                sys.stdout.flush()
                last_time = new_time
    except KeyError:
        print
        return graph, mrk_id_map
    print
    return graph, mrk_id_map

