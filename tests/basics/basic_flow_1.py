from snakes.nets import *

p1 = 'p1'
net = PetriNet('Net')
net.processes = [p1]

f1 = Place('f1', [dot], tBlackToken)
f1.one_safe = True
f1.process_name = p1
f1.flow_control = True

f2 = Place('f2', [], tBlackToken)
f2.one_safe = True
f2.process_name = p1
f2.flow_control = True

net.add_place(f1)
net.add_place(f2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('f1', 't', Value(dot))
net.add_output('f2', 't', Value(dot))
