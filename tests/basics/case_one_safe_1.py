from snakes.nets import *

net = PetriNet('Net')
s1 = Place('s1', [4], tInteger)
s1.one_safe = True
s2 = Place('s2', [], tInteger)
s2.one_safe = True

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Variable('x'))
net.add_output('s2', 't', Variable('x'))
