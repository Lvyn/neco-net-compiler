import snakes.plugins
snakes.plugins.load("gv", "snakes.nets", "nets")
from nets import *

net = PetriNet('Net')
s1 = Place('s1', [(1,2)])
s1.is_OneSafe = False

s2 = Place('s2', [1], tInteger)
s2.is_OneSafe = False

s3 = Place('s3', [2])
s3.is_OneSafe = False

s4 = Place('s4', [], tInteger)
s4.is_OneSafe = False

net.add_place(s1)
net.add_place(s2)
net.add_place(s3)
net.add_place(s4)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Tuple( (Variable("x"), Variable("y")) ))
net.add_input('s2', 't', Variable("x"))
net.add_input('s3', 't', Variable("y"))

net.add_output('s4', 't', Expression("x + y"))

if __name__ == '__main__':
    print 'writing net.ps'
    net.draw("net.ps")
