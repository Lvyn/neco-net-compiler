from snakes.nets import *

net = PetriNet('Net')
s1 = Place('s1', [ (1, 2, (3, 4, 5)) ])
s1.is_OneSafe = False
s2 = Place('s2', [ 5, 6])
s2.is_OneSafe = False
s3 = Place('s3', [])
s2.is_OneSafe = False

net.add_place(s1)
net.add_place(s2)
net.add_place(s3)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Tuple( (Variable('x'),
                                 Variable('y'),
                                 Tuple( (Variable('z1'),
                                         Variable('z2'),
                                         Variable('z3')
                                         )
                                        )
                                 )
                                )
              )
net.add_input('s2', 't', Variable('x'))
net.add_output('s3', 't', (Expression('(x+1, (y, (y, z1)))')))
