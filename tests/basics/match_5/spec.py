from snakes.nets import *

net = PetriNet('Net')
s1 = Place('s1', [])
s1.is_OneSafe = False

s2 = Place('s2', [])
s2.is_OneSafe = False

s3 = Place('s3', [])
s3.is_OneSafe = False

s4 = Place('s4', [])
s4.is_OneSafe = False

net.add_place(s1)
net.add_place(s2)
net.add_place(s3)
net.add_place(s4)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Tuple( (Variable("x"), Variable("x")) ))
net.add_input('s2', 't', Variable("z"))
net.add_input('s3', 't', Variable("z"))

net.add_output('s4', 't', Expression("x + z"))
