from snakes.nets import *

net = PetriNet('Net')
net.processes = []

s1 = Place('s1', [1, 1, 2, 2, 3, 3], tInteger)
s1.one_safe = False
s1.process_name = 'a'
s1.flow_control = False

s2 = Place('s2', [], tInteger)
s2.one_safe = False
s2.process_name = 'a'
s2.flow_control = False

s3 = Place('s3', [1, 3], tInteger)
s3.one_safe = False
s3.process_name = 'a'
s3.flow_control = False

net.add_place(s1)
net.add_place(s2)
net.add_place(s3)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', MultiArc([Variable('x'), Variable('x')]))
net.add_input('s3', 't', Test(Variable('x')))
net.add_output('s2', 't', Variable('x'))
