from snakes.nets import *

MAX = 30

net = PetriNet("Sieves of Erathostenes")
net.add_place(Place("numbers", range(2, MAX+1), tInteger))
net.add_transition(Transition("filter", Expression("x%y == 0")))
net.add_input("numbers", "filter", MultiArc([Variable("x"), Variable("y")]))
net.add_output("numbers", "filter", Variable("y"))
