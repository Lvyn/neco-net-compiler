from time import time
import pprint
import sys
import pdb

perm_log = open('perm_log', 'w')
calls = 0
def full_normalize_marking(marking, hash_set, current_set, todo_set, state_space):
    pid_tree = marking.buildPidTree()
    pid_tree.order_tree(pid_free_marking_order)
    iter_trees = pid_tree.itertrees()
    
    default_tree = iter_trees.next()
    bijection = default_tree.build_map()
    default_marking = marking.copy()
    default_marking.update_pids(bijection)

    # return default_marking
    perm_log.write(".")

    if not default_marking.__pid_free_hash__() in hash_set:
        perm_log.write("h")
        return default_marking

    if ((default_marking in state_space) or
        (default_marking in todo_set) or
        (default_marking in current_set)):
        return default_marking

    perm_log.write("+")
    c = 0
    # print "begin permutations !"
    global calls
#    calls += 1
#    print calls
    for tree in iter_trees:
        c+=1
        perm_log.write("*")
        # print "tree ", c
        # tree.print_structure()
        bijection = tree.build_map()
        tmp = marking.copy()
        tmp.update_pids(bijection)

        if tmp in state_space:
            return tmp
        if tmp in current_set:
            return tmp
        if tmp in todo_set:
            return tmp
        
    perm_log.write("{}%".format(c))

    return default_marking

def normalize_marking(marking, hash_set, current_set, todo_set, state_space):
    pid_tree = marking.buildPidTree()
    pid_tree.order_tree_without_orbits(pid_free_marking_order)
    bijection = pid_tree.build_map()
    marking.update_pids(bijection)
    perm_log.write(".")
    return marking

def state_space():
    done = set()
    todo = set([init()])
    succ = set()
    succs2 = set()
    count = 0
    start = time()
    last_time = start

    hash_set = set()

    try:
        while True:
            m = todo.pop()
            count+=1

            done.add(m)
            succ = succs(m, hash_set, done, todo)
            succs2 = succ.difference(done)
            todo.update(succs2)
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
    return done


def state_space_graph():
    visited = set()
    count = 0
    next = 1
    graph = {}
    mrk_id_map = {}
    succ_list = []
    start = time()
    last_time = start
    hash_set = set()

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
            succ = succs(m, hash_set, visit, visited)
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

