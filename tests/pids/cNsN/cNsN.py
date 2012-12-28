from neco.extsnakes import DPCPetriNet, Place, Transition, tBlackToken, dot, Value, Expression, Variable, tPid, tInteger, MultiArc, CrossProduct, Tuple, Pid

net = DPCPetriNet('net')

clients = {{{CLIENTS}}}
clients_range = range(1, clients+1)

steps = {{{STEPS}}}

# server
net.add_place(Place('s1', [Pid.from_str('1')], tPid))
net.add_place(Place('s_in', [], tPid))
# threads
net.add_place(Place('s_thread', [], tPid))
net.add_place(Place('s_thread_data', [], CrossProduct(tPid, tPid)))

# clients
client_pids = [ Pid.from_str('1.{}'.format(i)) for i in clients_range ]
net.add_place(Place('c1', client_pids, tPid))
net.add_place(Place('c2', [], tPid))
net.add_place(Place('c3', [], tPid))
net.add_place(Place('c_in', [], tPid))

# client transitions
net.add_transition(Transition('tc_1', Expression('True')))
net.add_input('c1', 'tc_1', Variable('p'))
net.add_output('c2', 'tc_1', Variable('p'))
net.add_output('s_in', 'tc_1', Variable('p'))


net.add_transition(Transition('tc_2', Expression('True')))
net.add_input('c2', 'tc_2', Variable('p'))
net.add_input('c_in', 'tc_2', Variable('p'))
net.add_output('c3', 'tc_2', Variable('p'))

# server transitions

# ts_1
server_pid, _ = net.add_get_pid('ts_1')
net.add_transition(Transition('ts_1', Expression('{} == p'.format(server_pid))))

net.add_input('s1', 'ts_1', Variable('p'))
net.add_output('s1', 'ts_1', Variable('p'))
net.add_input('s_in', 'ts_1', Variable('p_c'))

(thread_pid,) = net.add_spawn('ts_1', server_pid, 1)

net.add_output('s_thread', 'ts_1', Expression(str(thread_pid)))
net.add_output('s_thread_data', 'ts_1', Expression('({}, p_c)'.format(thread_pid)))

# transitions between ts_1 and ts_2, ie, steps

prev_place = "s_thread"
for step in range(steps):
    place_name = "step_{}".format(step)
    transition_name = "t_step_{}".format(step)

    net.add_place( Place(place_name, [], tPid) )
    net.add_transition( Transition(transition_name, Expression('True')) )
    net.add_input(prev_place, transition_name, Variable('p'))
    net.add_output(place_name, transition_name, Variable('p'))
    prev_place = place_name

# ts_2

thread_pid, _ = net.add_get_pid('ts_2')
net.add_transition(Transition('ts_2', Expression('p == {}'.format(thread_pid))))

net.add_input(prev_place, 'ts_2', Variable('p'))
net.add_input('s_thread_data', 'ts_2', Tuple( [Variable('p'), Variable('d')] ))
net.add_output('c_in', 'ts_2', Expression('d'))

net.add_terminate('ts_2', thread_pid)

net.setup_initial_hierarchy( { '{}'.format(i) : {} for i in clients_range } )

net.finalize_net()


if __name__ == '__main__':
    if __file__[-3:] == '.py':
        filename = __file__[0:-3] + '.ps'
    else:
        filename = __file__ + '.ps'
    print 'writing ' + filename
    net.draw(filename)
