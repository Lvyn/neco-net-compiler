from snakes.nets import *

net = PetriNet('Net')
net.processes = []

testplace = Place('testplace', [dot], tBlackToken)
testplace.one_safe = True
testplace.process_name = None
testplace.flow_control = False

s1 = Place('s1', [dot], tBlackToken)
s1.one_safe = True
s1.process_name = 'a'
s1.flow_control = False

s2 = Place('s2', [], tBlackToken)
s2.one_safe = True
s2.process_name = 'a'
s2.flow_control = False

net.add_place(s1)
net.add_place(s2)
net.add_place(testplace)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Value(dot))
net.add_input('testplace', 't', Test(Value(dot)))
net.add_output('s2', 't', Value(dot))
