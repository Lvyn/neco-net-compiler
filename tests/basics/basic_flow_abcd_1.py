from snakes.nets import *

from snakes.utils.abcd.main import main as run
pnml_file="basic_flow_abcd_1.pnml"
run(['--pnml=%s' % pnml_file, "basic_flow_abcd_1.abcd"])

net = loads(pnml_file)
os.remove(pnml_file)
