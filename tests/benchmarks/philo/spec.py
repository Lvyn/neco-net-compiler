import sys, re
sys.path.append('../../../')

from snakes.pnml import loads
from snakes.nets import *

net = loads('model.pnml')
net.processes = []

for p in net.place():
    p.one_safe = True
    p.process_name = None
    p.flow_control = False

if __name__ == '__main__':
    from neco.driver import Driver
    Driver()

