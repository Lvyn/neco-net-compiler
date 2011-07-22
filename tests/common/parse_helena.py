################################################################################
# Helena output format:
################################################################################
# count: 1
# case: 1
#           7s. for net compilation
#           0s. for state space search
# case: 2
#           7s. for net compilation
#           0s. for state space search
#
################################################################################

import re, argparse

parser = argparse.ArgumentParser(description="parse helena")
parser.add_argument('-f', dest='file', metavar='<filename>', type=str, nargs=1,
                    help='input file')
args = parser.parse_args()

input_file = args.file[0]

f = open(input_file, "r")

count_re  = re.compile(r"count: (?P<count>\d+)")
case_re   = re.compile(r"case: (?P<case>\d+)")
compil_re = re.compile(r"\s*(?P<time>\d+)s. for net compilation")
search_re = re.compile(r"\s*(?P<time>\d+)s. for state space search")
states_re = re.compile(r"\s*(?P<states>\d+(\s*\d*)*) states stored \(at the end of the search\)")
count = 0
cases=[]
for line in f:
    count_match  = count_re.match(line)
    case_match   = case_re.match(line)
    compil_match = compil_re.match(line)
    search_match = search_re.match(line)
    states_match = states_re.match(line)

    if count_match:
        count = int(count_match.group('count'))
    elif case_match:
        cases.append( (None, None, None) )
    elif compil_match:
        (a, b, c) = cases[-1]
        cases[-1] = ( float(compil_match.group('time')), b, c)
    elif search_match:
        (a, b, c) = cases[-1]
        cases[-1] = (a, float(search_match.group('time')), c)
    elif states_match:
        (a, b, c) = cases[-1]
        cases[-1] = (a, b, (states_match.group('states')))

f.close()

print "count: %d" % count
print "\tcompilation \texploration"
sum_a, sum_b = 0, 0
states = None
for i, (a, b, c) in enumerate(cases):
    print "\t%10.10f \t%10.10f" % (a, b)
    sum_a += a
    sum_b += b
    if not states:
        states = c
    else:
        assert(states == c)

print "avg: \t%10.10f \t%10.10f" % (sum_a / len(cases), sum_b / len(cases))
print "states: %sEC" % states
print
