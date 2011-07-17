import sys, re
sys.path.append('../../../')

from snakes.pnml import loads
from snakes.nets import *
from testrunner import TestRunner

net = loads('model.pnml')

track0 = re.compile("track\(this=0\).*")
track1 = re.compile("track\(this=1\).*")
track2 = re.compile("track\(this=2\).*")
track3 = re.compile("track\(this=3\).*")
track4 = re.compile("track\(this=4\).*")
track5 = re.compile("track\(this=5\).*")
track6 = re.compile("track\(this=6\).*")
track7 = re.compile("track\(this=7\).*")
track8 = re.compile("track\(this=8\).*")
gate   = re.compile("gate.*")
controller = re.compile("controller.*")

one_safes = re.compile(".*(green_all|state|count|down|up|crossing).*")
flow      = re.compile(".*(entry|internal|exit).*")

net.processes = ["gate" ]

for name, place in net._place.iteritems():
    place.one_safe = False
    if   track0.match(name): place.process_name = "track0"
    elif track1.match(name): place.process_name = "track1"
    elif track2.match(name): place.process_name = "track2"
    elif track3.match(name): place.process_name = "track3"
    elif track4.match(name): place.process_name = "track4"
    elif track5.match(name): place.process_name = "track5"
    elif track6.match(name): place.process_name = "track6"
    elif track7.match(name): place.process_name = "track7"
    elif track8.match(name): place.process_name = "track8"
    elif gate.match(name):   place.process_name = "gate"
    elif controller.match(name): place.process_name = "controller"
    else:
        place.process_name = None

    if flow.match(name):
        place.flow_control = True
        place.one_safe     = True
        place._check = tBlackToken
    else:
        place.flow_control = False

    place.one_safe = True if one_safes.match(name) else False

# if __name__ == '__main__':
#     TestRunner()
