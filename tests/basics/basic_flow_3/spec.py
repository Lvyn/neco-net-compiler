from snakes.nets import *

p1 = 'p1'
p2 = 'p2'

net = PetriNet('Net')
net.processes = [p1]

f1 = Place('f1', [dot], tBlackToken)
f1.one_safe = True
f1.process_name = p1
f1.flow_control = True

f2 = Place('f2', [], tBlackToken)
f2.one_safe = True
f2.process_name = p1
f2.flow_control = True

f3 = Place('f3', [], tBlackToken)
f3.one_safe = True
f3.process_name = p1
f3.flow_control = True

net.add_place(f1)
net.add_place(f2)
net.add_place(f3)

transition = Transition('t1', Expression('True'))
net.add_transition(transition)

net.add_input('f1', 't1', Value(dot))
net.add_output('f2', 't1', Value(dot))

transition = Transition('t2', Expression('True'))
net.add_transition(transition)

net.add_input('f2', 't2', Value(dot))
net.add_output('f3', 't2', Value(dot))

transition = Transition('t3', Expression('True'))
net.add_transition(transition)

net.add_input('f3', 't3', Value(dot))
net.add_output('f1', 't3', Value(dot))

################################################################################
# comment
################################################################################

f1 = Place("f1'", [dot], tBlackToken)
f1.one_safe = True
f1.process_name = p2
f1.flow_control = True

f2 = Place("f2'", [], tBlackToken)
f2.one_safe = True
f2.process_name = p2
f2.flow_control = True

f3 = Place("f3'", [], tBlackToken)
f3.one_safe = True
f3.process_name = p2
f3.flow_control = True

net.add_place(f1)
net.add_place(f2)
net.add_place(f3)

transition = Transition("t1'", Expression("True"))
net.add_transition(transition)

net.add_input("f1'", "t1'", Value(dot))
net.add_output("f2'", "t1'", Value(dot))

transition = Transition("t2'", Expression("True"))
net.add_transition(transition)

net.add_input("f2'", "t2'", Value(dot))
net.add_output("f3'", "t2'", Value(dot))

transition = Transition("t3'", Expression("True"))
net.add_transition(transition)

net.add_input("f3'", "t3'", Value(dot))
net.add_output("f1'", "t3'", Value(dot))


