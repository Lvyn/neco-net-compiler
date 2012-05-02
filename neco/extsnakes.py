""" Extensions for Snakes. """

from collections import defaultdict
from neco.utils import NameProvider
from snakes import ConstraintError
import snakes.plugins
import sys

snakes.plugins.load("gv", "snakes.nets", "nets")
from nets import *

#from nets import PetriNet, Place, Transition, Instance, CrossProduct, tNatural, \
#    Tuple, Variable, MultiArc, Expression, Value, ArcAnnotation

class Pid(object):
    
    def __init__(self):
        """
        
        >>> pid = Pid()
        >>> pid.data
        []
        
        """
        self.data = [] 
    
    @classmethod
    def from_str(self, str_repr = None):
        """ 
        >>> str(Pid.from_str('1.2.3'))
        '1.2.3'
        """
        pid = Pid()
        pid.data = [ int(s) for s in str_repr.split('.') ] if str_repr else []
        return pid
    
    @classmethod
    def from_list(self, frag_list = None):
        """
        >>> str(Pid.from_list([1,2,3]))
        '1.2.3'
        """
        pid = Pid()
        pid.data = frag_list if frag_list else []
        return pid
    
    def copy(self):
        """
        >>> p1 = Pid.from_str('1.1')
        >>> p2 = p1.copy()
        >>> p1.data[1] = 2
        >>> str(p1), str(p2)
        ('1.2', '1.1')
        """
        p = Pid()
        p.data = [ x for x in self.data ]
        return p
    
    def __iter__(self):
        return iter(self.data)
    
    def __bool__(self):
        return self.data # False iff empty

    def __int__(self):
        assert(len(self.data) == 1)
        return self.data[0]
        
    def __add__(self, frag):
        pid = self.copy()
        for e in frag.data:
            pid.data.append(int(e))
        return pid
    
    def __len__(self):
        return len(self.data)
    
    def __lt__(self, other):
        sl = len(self.data)
        ol = len(other.data)
        if sl < ol:
            return True
        elif ol > sl:
            return False
        else:
            for se, oe in zip(self.data, other.data):
                if se < oe:
                    continue
                else:
                    return False
            return True
    
    def at(self, i):
        return self.data[i]
    
    def subpid(self, begin = 0, end = None):
        """
        >>> pid = Pid.from_str('1.2.3.4')
        >>> pid.subpid(0)
        Pid.from_str('1.2.3.4')
        >>> pid.subpid(1)
        Pid.from_str('2.3.4')
        >>> pid.subpid(0, -1)
        Pid.from_str('1.2.3')
        >>> pid.subpid(1, -1)
        Pid.from_str('2.3')
        >>> pid.subpid(1, 3)
        Pid.from_str('2.3')
        """
        pid = self.copy()
        for _ in range(0, begin):
            pid.data.pop(0)
            
        if end:
            if end > 0:
                for _ in range(end, len(self.data)):
                    pid.data.pop(-1)
            elif end < 0: 
                max = len(self.data)
                for _ in range(max + end, max):
                    pid.data.pop(-1)
        return pid
        
    
    def prefix(self):
        """
        >>> pid = Pid.from_str('1.2.3')
        >>> pid.prefix()
        Pid.from_str('1.2')
        """
        pid = self.copy()
        pid.data.pop(-1)
        return pid

    def suffix(self):
        """
        >>> pid = Pid.from_str('1.2.3')
        >>> pid.suffix()
        Pid.from_str('2.3')
        """
        pid = self.copy()
        pid.data.pop(0)
        return pid

    def ends_with(self):
        """
        >>> pid = Pid.from_str('1.2.3')
        >>> pid.ends_with()
        3
        """
        return self.data[-1]
        
    def __hash__(self):
        """
        >>> hash(Pid.from_str('1.2')) == hash(Pid.from_str('1.2'))
        True
        >>> hash(Pid.from_str('1.2')) == hash(Pid.from_str('1.3'))
        False
        """
        h, mult, i = 0xDEADDAD, 0xDEADBEEF, 0
        for elt in self.data:
            h = (h ^ hash(elt)) * mult
            mult += 82520L + i + i
            i += 1
        return h
    
    def __eq__(self, other):
        """
        >>> Pid.from_str('1.1.1') == Pid.from_str('1.1.1')
        True
        """
        return self.data == other.data
    
    
    def __ne__(self, other):
        """
        >>> Pid.from_str('1.1.1') != Pid.from_str('1.1.2')
        True
        """
        return self.data != other.data
    
    def next(self, pid_component):
        """
        >>> Pid.from_str('1').next('0') == Pid.from_str('1.1')
        True
        >>> Pid.from_str('1.2').next('2').next(3) == Pid.from_str('1.2.3.4')
        True
        """
        p = self.copy()
        p.data.append(int(pid_component)+1)
        return p
    
    def parent(self, other):
        """
        >>> p111, p1113, p11, p11124 = Pid.from_str('1.1.1'), Pid.from_str('1.1.1.3'), Pid.from_str('1.1'), Pid.from_str('1.1.1.2.4')
        >>> p111.parent(p111)
        False
        >>> p111.parent(p1113)
        True
        >>> p111.parent(p11)
        False
        >>> p111.parent(p11124)
        True
        """
        od = other.data
        sd = self.data
        
        # child must be longer than parent
        if len(od) > len(sd):
            i = 0
            # test if parent is a prefix of the child
            for elt in sd:
                if elt != od[i]:
                    return False
            # loop passed ok
            return True
        else:
            return False

    def parent1(self, other):
        """
        >>> p111, p1113, p11, p11124 = Pid.from_str('1.1.1'), Pid.from_str('1.1.1.3'), Pid.from_str('1.1'), Pid.from_str('1.1.1.2.4')
        >>> p111.parent1(p111)
        False
        >>> p111.parent1(p1113)
        True
        >>> p111.parent1(p11)
        False
        >>> p111.parent1(p11124)
        False
        """
        od = other.data
        sd = self.data
        
        # child must be longer than parent
        if len(od) == len(sd) + 1:
            i = 0
            # test if parent is a prefix of the child
            for elt in sd:
                if elt != od[i]:
                    return False
            # loop passed ok
            return True
        else:
            return False

    def sibling(self, other):
        """
        >>> p111, p1113, p112, p115 = Pid.from_str('1.1.1'), Pid.from_str('1.1.1.3'), Pid.from_str('1.1.2'), Pid.from_str('1.1.5')
        >>> p111.sibling(p111)
        False
        >>> p111.sibling(p1113)
        False
        >>> p111.sibling(p112)
        True
        >>> p112.sibling(p111)
        False
        >>> p111.sibling(p115)
        True
        
        """
        sd = self.data
        od = other.data
        length = len(sd)
        # must have the same length 
        if length == len(od):
            i = 0
            # prefixes must be equal
            for e in sd[0:length-1]:
                if e != od[i]:
                    return False
            # prefix check passed
            return sd[length-1] < od[length-1]
        else:
            return False
    
    def sibling1(self, other):
        """
        >>> p111, p1113, p112, p115 = Pid.from_str('1.1.1'), Pid.from_str('1.1.1.3'), Pid.from_str('1.1.2'), Pid.from_str('1.1.5')
        >>> p111.sibling1(p111)
        False
        >>> p111.sibling1(p1113)
        False
        >>> p111.sibling1(p112)
        True
        >>> p112.sibling1(p111)
        False
        >>> p111.sibling1(p115)
        False
        """
        sd = self.data
        od = other.data
        length = len(sd)
        # must have the same length 
        if length == len(od):
            i = 0
            # prefixes must be equal
            for e in sd[0:length-1]:
                if e != od[i]:
                    return False
            # prefix check passed
            return sd[length-1] == od[length-1]-1
        else:
            return False

    def __repr__(self):
        """
        >>> repr(Pid.from_str('1.1.1'))
        "Pid.from_str('1.1.1')"
        >>> Pid.from_str('1.1.1') == eval(repr(Pid.from_str('1.1.1')))
        True
        """
        return 'Pid.from_str(\'' + '.'.join([repr(e) for e in self.data]) + '\')'  
    
    def __str__(self):
        """
        >>> str(Pid.from_str('1.1.1'))
        '1.1.1'
        """
        return '.'.join([repr(e) for e in self.data])

tPid = Instance(Pid)

class GeneratorMultiArc(ArcAnnotation):

    def __init__(self, pid, counter, new_pids, components):
        if len(components) == 0:
            raise ConstraintError("missing tuple components")
        
        self.pid = pid
        self.counter = counter
        self.new_pids = new_pids
        self.components = components
          
        self.input_allowed = False
    
    def copy(self):
        return self.__class__(self.pid.copy(),
                              self.counter,
                              [ pid.copy() for pid in self.new_pids ],
                              [ x.copy() for x in self.components ])
    def __iter__(self):
        return iter(self.components)
    
    def __str__(self):
        """
        >>> cnt = Variable('c')
        >>> pid, pid1, pid2 = Variable('pid'), Variable('pid1'), Variable('pid2')
        >>> str( GeneratorMultiArc(pid, cnt, [pid1, pid2], [ Tuple([pid, Expression("c + 2")]), Tuple([pid1, Value(0)]), Tuple([pid2, Value(0)]) ]) )
        '<(pid, c + 2), pid1 := next(pid) : (pid1, 0), pid2 := next(pid) : (pid2, 0)>'
        """
        pid = self.pid
        str_list = []
        if len(self.new_pids) == len(self.components):
            components = self.components
        else:
            str_list.append(str(self.components[0]))
            components = self.components[1:]
        
        for pid_var, component in zip(self.new_pids, components):
            str_list.append('{} := next({}) : {}'.format(str(pid_var), str(pid), str(component)) )
        return '<' + ', '.join(str_list) + '>'
    
    def __eq__(self, other):
        """
        >>> cnt = Variable('c')
        >>> pid, pid1 = Variable('pid'), Variable('pid1')
        >>> arc = GeneratorMultiArc(pid, cnt, [pid1], [ Tuple([pid, Expression("c + 2")]), Tuple([pid1, Value(0)])])
        >>> arc == GeneratorMultiArc(pid, cnt, [pid1], [ Tuple([pid, Expression("c + 2")]), Tuple([pid1, Value(0)])])
        True
        >>> arc == GeneratorMultiArc(pid, cnt, [pid1], [ Tuple([pid, Expression("c + 3")]), Tuple([pid1, Value(0)])])
        False
        """
        if self.pid == other.pid:
            if self.counter == other.counter:
                if len(self.new_pids) == len(other.new_pids):
                    if len(self.components) == len(other.components):
                        # check new threads
                        for p1, p2 in zip(self.new_pids, other.new_pids):
                            if p1 != p2:
                                return False
                        # check components
                        for c1, c2 in zip(self.components, other.components):
                            if c1 != c2:
                                return False
                        return True
        # one of the conditions failed
        return False
    
    def __repr__(self):
        """
        >>> cnt = Variable('c')
        >>> pid, pid1, pid2 = Variable('pid'), Variable('pid1'), Variable('pid2')
        >>> GeneratorMultiArc(pid, cnt, [pid1, pid2], [ Tuple([pid, Expression("c + 2")]), Tuple([pid1, Value(0)]), Tuple([pid2, Value(0)]) ])
        GeneratorMultiArc(Variable('pid'), Variable('c'), [Variable('pid1'), Variable('pid2')], [Tuple((Variable('pid'), Expression('c + 2'))), Tuple((Variable('pid1'), Value(0))), Tuple((Variable('pid2'), Value(0)))])
               
        >>> cnt = Variable('c')
        >>> pid, pid1, pid2 = Variable('pid'), Variable('pid1'), Variable('pid2')
        >>> tmp = GeneratorMultiArc(pid, cnt, [pid1, pid2], [ Tuple([pid, Expression("c + 2")]), Tuple([pid1, Value(0)]), Tuple([pid2, Value(0)]) ])
        >>> eval(repr(tmp)) == tmp
        True
        
        """
        return 'GeneratorMultiArc({}, {}, {}, {})'.format(repr(self.pid),
                                                      repr(self.counter),
                                                      repr(self.new_pids),
                                                      repr(self.components))    

    def vars(self):
        l = [ self.pid, self.counter ]
        l.extend(self.new_pids)
        for component in self.components:
            l.extend(component.vars())
        return l
    
class ProcessPetriNet(PetriNet):
    
    strict = True
    
    def __init__(self, name):
        """
        >>> ProcessPetriNet('net').place()
        [Place('sgen', MultiSet([(Pid.from_str('1'), 0)]), CrossProduct(Instance(Pid), (Instance(int) & GreaterOrEqual(0))))]
        
        """
        PetriNet.__init__(self, name)
        # add generator place
        initial_pid = Pid.from_str('1')
        generator_place = Place("sgen", [(initial_pid, 0)], CrossProduct(tPid, tNatural))
        
        self._initial_pid = initial_pid
        self.name_provider = NameProvider()
        self._generator_place = generator_place
        self.add_place(self._generator_place)
        self.spawn_operations     = defaultdict(lambda : defaultdict(list))
        self.get_operations       = defaultdict(list)
        self.terminate_operations = defaultdict(set)
   
    def initial_pid(self):
        return self._initial_pid
    
    def add_get_pid(self, trans, count = 1):
        pid_var, count_var = Variable('x'), Variable('x')
        # override names, begins with _ which is usually illegal
        pid_var.name   = self.name_provider.new()
        count_var.name = self.name_provider.new()
        # remember variables to use
        self.get_operations[trans].append( (pid_var, count_var) )
        self.spawn_operations[trans][pid_var] # force output arc creation
        # return variables
        return pid_var, count_var
        
    def add_spawn(self, trans, pid_variable, thread_count = 1):
        # create pids
        pid_vars = []
        for _ in range(thread_count):
            # hack that allows names beginning with _
            var = Variable('tmp')
            var.name = self.name_provider.new()
            pid_vars.append( var )
            
        # remember pids to create
        self.spawn_operations[trans][pid_variable].extend( pid_vars )
        return pid_vars
    
    def add_terminate(self, trans, pid_var):
        self.terminate_operations[trans].add(pid_var)
        
    def _get_counter_var(self, trans, pid_var):
        for p, c in self.get_operations[trans]:
            if p == pid_var:
                return c
        print >> sys.stderr, ("counter for {} not found, user should specify a get"
                              " operation and use the returned variable to create new threads.")
        raise RuntimeError
        
    def finalize_net(self):
        # add arcs
        for trans in self._trans:
            # from generator place to transition.
            pc_pairs = self.get_operations[trans]
            if pc_pairs:
                tuple_list = [Tuple([p, c]) for p, c in pc_pairs]
                if len(tuple_list) > 1:
                    self.add_input(self._generator_place.name, trans, MultiArc(tuple_list))
                else:
                    self.add_input(self._generator_place.name, trans, tuple_list[0])
            
            # from transition to generator place.
            spawn_ops = self.spawn_operations[trans]
            for pid_var, new_pids in spawn_ops.iteritems():
                counter_var = self._get_counter_var(trans, pid_var)
                # update thread counter
                if pid_var in self.terminate_operations[trans]:
                    tuple_list = []
                else:
                    if len(new_pids) == 0:
                        expr = Expression(str(counter_var))
                    else:
                        expr = Expression("{} + {}".format(str(counter_var), str(len(new_pids))))
                    tuple_list = [ Tuple( [ pid_var, expr ]) ]
                # add new thread coutners
                tuple_list.extend([ Tuple([new_pid_var, Value(0)]) for new_pid_var in new_pids ])
                
                if not tuple_list:
                    continue
                # add generator arc
                generator_arc = GeneratorMultiArc(pid_var, counter_var, new_pids, tuple_list)
                self.add_output(self._generator_place.name, trans, generator_arc)
                self.transition(trans).generator_arc = generator_arc


if __name__ == "__main__":
    import doctest
    doctest.testmod()
