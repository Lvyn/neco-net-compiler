#!/usr/bin/python
import sys, argparse
from snakes.nets import *

def gen_pnml():
    sup_count = count + 1

    forks = [ Place('fork_' + str(i) , [dot], tBlackToken) for i in range(1, sup_count) ]
    philos = [ Place('philo_' + str(i), [], tBlackToken) for i in range(1, sup_count) ]

    net = PetriNet('Net')

    for fork in forks:
        fork.is_OneSafe = True
        net.add_place(fork)
    for philo in philos:
        philo.is_OneSafe = True
        net.add_place(philo)

    for i in range(1, sup_count):
        # mange
        t_name = 'b_' + str(i)
        in_1 = 'fork_' + str(i)
        in_2 = 'fork_' + str( (i%count) + 1 )
        out_b  = 'philo_' + str(i)

        transition = Transition(t_name, Expression('True'))
        net.add_transition(transition)

        net.add_input(in_1, t_name, Value(dot))
        net.add_input(in_2, t_name, Value(dot))

        net.add_output(out_b, t_name, Value(dot))

        # fini
        t_name = 'e_' + str(i)
        in_e = out_b
        out_1 = in_1
        out_2 = in_2

        transition = Transition(t_name, Expression('True'))
        net.add_transition(transition)

        net.add_input(in_e, t_name, Value(dot))

        net.add_output(out_1, t_name, Value(dot) )
        net.add_output(out_2, t_name, Value(dot) )

    print repr(net.__pnmldump__())

def gen_lna():

    print "philo {"
    print "\ttype dot : enum (DOT);"

    #forks
    for i in range(1, count+1):
        print "\tplace fork_%d { dom : dot; init : <( DOT )>; }" % i

    #philos
    for i in range(1, count+1):
        print "\tplace philo_%d { dom : dot; }" % i

    # transitions
    for i in range (1, count+1):
        print
        print "\ttransition grab_%d {" % i

        print "\t\tin { fork_%d : <( DOT )>; fork_%d : <( DOT )>; }" % (i, (i%count)+1)
        print "\t\tout { philo_%d : <( DOT )>; }" % i

        print "\t}"
        print

        print "\ttransition release_%d {" % i

        print "\t\tin { philo_%d : <( DOT )>; }" % i
        print "\t\tout { fork_%d : <( DOT )>; fork_%d : <( DOT )>; }" % (i, (i%count)+1)

        print "\t}"

    print "}"


parser = argparse.ArgumentParser(description="mkphilo")
parser.add_argument('-t', dest='target', choices=['lna', 'pnml'], default='pnml',
                    help='select the target language')
parser.add_argument('-c', dest='count', metavar='<count>', type=int, nargs=1, default=[2],
                    help='philosopher count (must be greater than 1)')
args = parser.parse_args()

count = args.count[0]
assert((count > 1))


if args.target == 'pnml':
    gen_pnml()
elif args.target == 'lna':
    gen_lna()
else:
    assert(False)
