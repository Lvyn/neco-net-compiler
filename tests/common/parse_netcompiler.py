import re, argparse

parser = argparse.ArgumentParser(description="parse netcompiler")
parser.add_argument('-no', dest='file', metavar='<filename>', type=str, nargs=1,
                    help='input file (no opt)')
parser.add_argument('-o', dest='opt_file', metavar='<filename>', type=str, nargs=1,
                    help='input file (opt)')
args = parser.parse_args()

input_file = args.file[0]
input_opt_file = args.opt_file[0]

f = open(input_file, "r")
opt_f = open(input_opt_file, "r")

count_re  = re.compile(r"count: (?P<count>\d+)")
case_re   = re.compile(r"case: (?P<case>\d+)")
compil_re = re.compile(r"compilation time:\s*(?P<time>\d*.\d*(e?[-+]\d*)*)")
search_re = re.compile(r"exploration time:\s*(?P<time>\d*.\d*(e?[-+]\d*)*)")
states_re = re.compile(r"len visited = (?P<states>\d+(\s*\d*)*)")
count = 0
cases=[]

for line, line2 in zip(f, opt_f):
    count_match  = count_re.match(line)
    case_match   = case_re.match(line)
    compil_match = compil_re.match(line)
    search_match = search_re.match(line)
    states_match = states_re.match(line)

    count_match2  = count_re.match(line2)
    case_match2   = case_re.match(line2)
    compil_match2 = compil_re.match(line2)
    search_match2 = search_re.match(line2)
    states_match2 = states_re.match(line2)

    if count_match:
        count  = int(count_match.group('count'))
        count2 = int(count_match2.group('count'))
        assert(count == count2)
    elif case_match:
        cases.append( ((None, None, None), (None, None, None)) )
    elif compil_match:
        (a, b, c), (a2, b2, c2) = cases[-1]
        cases[-1] = ((float(compil_match.group('time')), b, c), (float(compil_match2.group('time')), b2, c2))
    elif search_match:
        (a, b, c), (a2, b2, c2) = cases[-1]
        cases[-1] = ((a, float(search_match.group('time')), c), (a2, float(search_match2.group('time')), c2))
    elif states_match:
        (a, b, c), (a2, b2, c2) = cases[-1]
        cases[-1] = ((a, b, (states_match.group('states'))), (a2, b2, (states_match2.group('states'))))

f.close()

print "count: %d" % count
print "\tcompilation \texploration \tcompil opt \texpl opt"
sum_a, sum_b, sum_a2, sum_b2 = 0, 0, 0, 0
states = None
for i, ((a, b, c), (a2, b2, c2)) in enumerate(cases):
    print "\t%10.10f \t%10.10f \t%10.10f \t%10.10f" % (a, b, a2, b2)
    sum_a += a
    sum_b += b
    sum_a2 += a2
    sum_b2 += b2
    if not states:
        states = c2

print "avg: \t%10.10f \t%10.10f \t%10.10f \t%10.10f" % (sum_a / len(cases), sum_b / len(cases), sum_a2 / len(cases), sum_b2 / len(cases))
print "states: %s" % states
print
