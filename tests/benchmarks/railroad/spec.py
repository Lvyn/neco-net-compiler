import sys, re
sys.path.append('../../../')

from snakes.pnml import loads
from snakes.nets import *

net = loads('model.pnml')
net.processes = []

for p in net.place():
    p.one_safe = False
    p.process_name = None

flow = re.compile(".*(entry|internal|exit).*")
one_safes = re.compile(".*(green_all|state|count|down|up|crossing).*")

for name, place in net._place.iteritems():
    if flow.match(name):
        place.one_safe = True
        place._check = tBlackToken
    elif one_safes.match(name):
        place.one_safe = True
    else:
        place.one_safe = False

if __name__ == '__main__':
    from netcompiler.driver import Driver
    Driver()
