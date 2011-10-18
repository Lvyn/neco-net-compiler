from snakes.plugins import load
load("gv", "snakes.nets", "snk")
from snk import *

MAX = 10

n = PetriNet("Sieves of Erathostenes")
n.add_place(Place("numbers", range(2, MAX+1), tInteger))
n.add_transition(Transition("filter", Expression("x%y == 0")))
n.add_input("numbers", "filter", MultiArc([Variable("x"), Variable("y")]))
n.add_output("numbers", "filter", Variable("y"))

# test

n.draw("sieve.png")

g = StateGraph(n)
for state in g :
    print state, "=", g.net.get_marking()["numbers"]
if len(g) < 50 :
    g.draw("primes.png")
