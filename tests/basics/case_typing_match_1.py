from snakes.nets import *

net = PetriNet('Net')
s1 = Place('s1', [ (1, (2, (3, 4, 5))) ], CrossProduct(tInteger, CrossProduct(tInteger, CrossProduct(tInteger, tInteger, tInteger))))
s1.is_OneSafe = False
s2 = Place('s2', [], CrossProduct(tInteger, tInteger))
s2.is_OneSafe = False

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Tuple( (Variable('x'), Tuple( (Variable('y'), Tuple( (Variable('y1'), Variable('x1'), Variable('z1'))) )))))
net.add_output('s2', 't', (Expression('(x+1, (y, (y,z1)))')))
