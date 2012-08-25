from snakes.nets import *

net = PetriNet('Net')
net.processes = []

s1 = Place('s1', [dot, dot], tBlackToken)
s1.one_safe = False
s1.process_name = 'a'
s1.flow_control = False

s2 = Place('s2', [], tBlackToken)
s2.one_safe = False
s2.process_name = 'a'
s2.flow_control = False

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', MultiArc([Value(dot), Value(dot)]))
net.add_output('s2', 't', Value(dot))
