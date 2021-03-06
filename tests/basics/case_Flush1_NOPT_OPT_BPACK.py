from snakes.nets import *

net = PetriNet('Net')
s1 = Place('s1', [1, 2, 3]) # tInteger) # do not support flush in cython
s1.is_OneSafe = True
s2 = Place('s2', []) # tInteger) # do not support flush in cython
s2.is_OneSafe = True

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Flush('x'))
net.add_output('s2', 't', Flush('x + x'))
