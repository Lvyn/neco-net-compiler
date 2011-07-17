from snakes.nets import *

net = PetriNet('Net')
s1 = Place('s1', [(1, (1, 1)),
                  (2, (1, 2)),
                  (1, (1, 10)),
                  (1, (2, 10)),
                  (1, (3, 10)) ])
s1.is_OneSafe = False

s2 = Place('s2', [])
s2.is_OneSafe = False

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Tuple( (Value(1), Tuple( (Variable("x"), Value(10))))))
net.add_output('s2', 't', Tuple( (Value(1), Tuple( (Variable("x"), Value(11))))))
