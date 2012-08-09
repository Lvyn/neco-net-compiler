from snakes.nets import *

net = PetriNet('Net')
net.processes = []

s1 = Place('s1', [3, 5], tInteger)
s1.flow_control = False
s1.one_safe = False
s1.process_name = None

s2 = Place('s2', [], tInteger)
s2.flow_control = False
s2.one_safe = False
s2.process_name = None


net.add_place(s1)
net.add_place(s2)

transition = Transition('t1', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't1', Variable('x'))
net.add_output('s2', 't1', Expression('2*x + 1'))
