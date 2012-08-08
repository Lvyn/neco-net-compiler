from snakes.nets import *

net = PetriNet('Net')
net.processes = []

s1 = Place('s1', [dot], tBlackToken)
s1.one_safe = True
s1.flow_control = False

s2 = Place('s2', [], tBlackToken)
s2.one_safe = True
s2.flow_control = False

s3 = Place('s3', [], tBlackToken)
s3.one_safe = True
s3.flow_control = False

net.add_place(s1)
net.add_place(s2)
net.add_place(s3)

transition1 = Transition('t1', Expression('True'))
net.add_transition(transition1)

transition2 = Transition('t2', Expression('True'))
net.add_transition(transition2)

net.add_input('s1', 't1',  Value(dot))
net.add_output('s2', 't1', Value(dot))


net.add_input('s2', 't2',  Value(dot))
net.add_output('s3', 't2', Value(dot))
