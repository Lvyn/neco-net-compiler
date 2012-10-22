
from collections import defaultdict
from neco.extsnakes import Pid
from neco.utils import flatten_lists
import itertools
import pprint

def sibling_order( left, right ):
    return left.frag - right.frag

def pid_free_marking_order( left, right ):
    if left.marking: 
        res = left.marking.pid_free_compare(right.marking) if right.marking else 1
    else:
        res = -1 if right.marking else 0
    return -res

class mydefaultdict(dict):
    def __missing__(self, key):
        l = [key]
        self[key] = l
        return l
        
class PidTree(object):

    def __init__(self, frag):
        self.frag = frag
        self.children = {} # defaultdict(lambda : PidTree())
        self.marking = None
        self.orbits  = None # will be build during orderings
        
    def add_marking(self, pid, marking):
        if len(pid) == 0:
            self.marking = marking
        else:
            frag = pid[0]
            if self.children.has_key(frag):
                self.children[frag].add_marking(pid[1:], marking)
            else:
                tree = PidTree(frag)
                self.children[frag] = tree
                tree.add_marking(pid[1:], marking)

    def order_tree(self, compare, n=0):
        #
        # Each time a child is ordered, its orbits are updated.
        # In initial state, all children have singleton orbits.
        # When compare detects an equality orbits are fused together.
        #
        # We use fragments as unique identifiers in orbits because
        # there are no clashes (cf. Pid-tree definition)
        # 

        # order children and populate orbits with singletons
        orbits = {}
        for child in self.children.itervalues():
            child.order_tree(compare, n+1)
            orbits[child.frag] = set([child])

        # the following function is used to order children, it will use order
        # to compare elements and if they are equal update respective orbits

        def comparison_function(left, right):
            # left and right are (pid-fragment x pid-tree) pairs.
            comparison_result = compare(left, right)
            # assert( comparison_result == -(compare(right, left)) )
            if comparison_result == 0:
                # fuse orbits
                left_frag, right_frag = left.frag, right.frag
                left_orbit  = orbits[left_frag]
                right_orbit = orbits[right_frag]

                left_orbit = left_orbit.union(right_orbit)

                for c in left_orbit:
                    orbits[c.frag] = left_orbit

            # return the comparison_result since it's a comparison function
            return comparison_result

        # sort children and rebuild orbits
        self.children = sorted( list(self.children.itervalues()), cmp=comparison_function )
        # don't forget to store orbits
        self.orbits = orbits

    def permutable_children(self):
        identities = set()
        permutable_children = []
        
#        f = False
#        if self.children:
#            f = True
            # print [ c.frag for c in self.children ]

        for child in self.children:
            value = self.orbits[child.frag]
            
            identity = id(value)
            if not identity in identities:
#                if f:
#                    print "adding ", [ v.frag for v in value ], identity
                identities.add(identity)
                permutable_children.append(value)

        return permutable_children

    def permutations(self):
        permutable = self.permutable_children()
        for permutation in itertools.product(*[itertools.permutations(p) for p in permutable]):
            yield itertools.chain.from_iterable(permutation)

    def itertrees(self, n=0):
        for permutation in self.permutations():
            tmp = list(permutation)
            for children in itertools.product( *(child.itertrees(n+1) for child in tmp) ): # permutation) ):

                tree = PidTree(self.frag)
                tree.marking = self.marking
                tree.children = children
                yield tree

    def build_map(self):
        """
        >>> from pprint import pprint
        >>> n = PidTree(0)
        >>> n.add_marking([2,42,7], None)
        >>> n.add_marking([2,31,8], None)
        >>> n.add_marking([2,32,8], None)
        >>> n.add_marking([22,32,9], None)
        >>> n.order_tree()
        >>> new_pid_dict = n.build_map()
        >>> n.print_structure()
        |-1-
        | |-1-
        | | |-1-
        | |-2-
        | | |-1-
        | |-3-
        |   |-1-
        |-2-
          |-1-
            |-1-
        >>> pprint(sorted(new_pid_dict.iteritems()))
        [((2,), (1,)),
         ((2, 31), (1, 1)),
         ((2, 31, 8), (1, 1, 1)),
         ((2, 32), (1, 2)),
         ((2, 32, 8), (1, 2, 1)),
         ((2, 42), (1, 3)),
         ((2, 42, 7), (1, 3, 1)),
         ((22,), (2,)),
         ((22, 32), (2, 1)),
         ((22, 32, 9), (2, 1, 1))]
        """
        
#        print
#        self.print_structure()
        old_prefix = [] 
        new_prefix = []
        bijection = {}
        self._update_map(old_prefix, new_prefix, bijection)
        return bijection
        
    def _update_map(self, old_prefix, new_prefix, bijection):
        # children are assumed ordered
        # normalize pids
        
        i = 1
        for child in self.children:
            old_prefix.append(child.frag)
            new_prefix.append(i)
            i += 1
            bijection[tuple(old_prefix)] = tuple(new_prefix)
            child._update_map(old_prefix, new_prefix, bijection)
            old_prefix.pop()
            new_prefix.pop()

    def print_structure(self, child_prefix='', prefix=''):
        """
        >>> n = PidTree(0)
        >>> n.order_tree()
        >>> n.print_structure()

        >>> n = PidTree(0)
        >>> _ = n.add_marking([1,1,1], None)
        >>> n.order_tree()
        >>> n.print_structure()
        |-1-
          |-1-
            |-1-
        >>> n = PidTree(0)
        >>> _ = n.add_marking([1,1,1], None)
        >>> _ = n.add_marking([1,2], None)
        >>> n.order_tree()
        >>> n.print_structure()
        |-1-
          |-1-
          | |-1-
          |-2-
        >>> n = PidTree(0)
        >>> _ = n.add_marking([1,1,1], None)
        >>> _ = n.add_marking([1,2], None)
        >>> _ = n.add_marking([1], None)
        >>> n.order_tree()
        >>> n.print_structure()
        |-1-
          |-1-
          | |-1-
          |-2-
        """
        if child_prefix:
            print "{}".format(child_prefix)
        length = len(self.children) - 1
        child_prefix = prefix + '|-'
        for i, child in enumerate(self.children): 
            child_prefix = prefix + '|-{}-'.format(child.frag) #, child.marking.__line_dump__())
            new_prefix = prefix + '| ' if i < length else prefix + '  ' 
            child.print_structure(child_prefix, new_prefix)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
