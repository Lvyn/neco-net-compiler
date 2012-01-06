import sys, re, os
sys.path.append('../../../')

from snakes.pnml import loads
from snakes.nets import *

from snakes.utils.abcd.main import main as run
pnml_file="basic_flow_abcd_2.pnml"
run(['--pnml=%s' % pnml_file, "basic_flow_abcd_2.abcd"])

net = loads(pnml_file)
os.remove(pnml_file)

one_safes = re.compile(".*(green_all|state|count|down|up|crossing).*")
flow      = re.compile(".*(entry|internal|exit).*")

net.processes = ["gate" ]

for name, place in net._place.iteritems():
    place.one_safe = False

    if flow.match(name):
        place.flow_control = True
        place.one_safe     = True
        place._check = tBlackToken
    else:
        place.flow_control = False

    place.one_safe = True if one_safes.match(name) else False
