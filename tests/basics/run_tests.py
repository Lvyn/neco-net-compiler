#!/usr/bin/python
import glob, re, os, argparse, subprocess
from collections import defaultdict
from snakes.nets import *

class Marking(object):
    def __init__(self, init):
        self.data = { p : sorted(ms) for p, ms in init.iteritems() }

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)

    def __eq__(self, other):
        return self.data == other.data


class MarkingSet(object):
    def __init__(self, init):
        self.data = set( [ Marking(d) for d in init ] )

    def add(self, marking):
        self.data.add(marking)

    def __contains__(self, marking):
        for m in self.data:
            if marking == m:
                return True
        return False

    def __eq__(self, other):
        if len(self.data) != len(other.data):
            return False
        for marking in other.data:
            if not marking in self:
                return False
        return True

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)

failed_list = []

def run_test(module_name, lang='python', opt=False, pfe=False):
    print "Running test %s..." % module_name
    expect = module_name + '_out'
    result = module_name + '_res'

    args = ['python', "../../neco",
            '-m', module_name,
            '-k', result,
            '-l', lang,
            '-I../common']
    if opt:
        args.append('--optimise')
    if pfe:
        args.append('--optimise-flow')

    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    r = p.wait()
    if r != 0:
        return False

    try:
        expect_file = open(expect, 'r')
        result_file = open(result, 'r')
    except IOError as e:
        print >> sys.stderr, str(e)
        return False

    try:
        expect_markings = MarkingSet(eval(expect_file.read()))
    except SyntaxError as e:
        print >> sys.stderr, "Syntax error in file {}, please check this file.".format(expect)
        print >> sys.stderr, str(e)
        return False

    try:
        result_markings = MarkingSet(eval(result_file.read()))
    except SyntaxError as e:
        print >> sys.stderr, "Syntax error in file {}, please check this file.".format(result)
        print >> sys.stderr, str(e)
        return False

    if not expect_markings == result_markings:
        print "test %s failed..." % module_name
        print "expected: "
        print expect_markings
        print "got: "
        print result_markings
        return False
    return True

common_cases = set(['basic_1',
                    'basic_2',
                    'basic_3',
                    'basic_4',
                    'basic_5',
                    'basic_flow_1',
                    'basic_flow_2',
                    'basic_flow_3',
                    'basic_flow_abcd_1',
                    'basic_flow_abcd_2',
                    'basic_flow_abcd_3',
                    'basic_flow_abcd_4',
                    'basic_flush_1',
                    'match_1',
                    'match_2',
                    'match_3',
                    'match_4',
                    'match_5',
                    'match_6',
                    'basic_one_safe_1',
                    'basic_one_safe_2',
                    'basic_multiarc_out_1',
                    'basic_multiarc_out_2',
                    'basic_multiarc_out_3',
                    'basic_multiarc_in_1',
                    'basic_multiarc_in_2',
                    'basic_multiarc_in_3',
                    'basic_multiarc_in_4',
                    'basic_multiarc_in_5',
                    'basic_test_1',
                    'basic_test_2',
                    'basic_multiarc_in_match_1',
                    'basic_multiarc_in_match_2',
                    'basic_multiarc_in_match_3',
                    'basic_tuple_match_1'])

flow_control_cases = set([ 'basic_flow_1',
                           'basic_flow_2',
                           'basic_flow_3',
                           'basic_flow_abcd_1',
                           'basic_flow_abcd_2',
                           'basic_flow_abcd_3',
                           'basic_flow_abcd_4' ])

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Tests runner",
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--clean', '-C', dest='clean', action='store_true', default=False,
                        help='remove all produced files')
    parser.add_argument('--noopts', '-n', dest='noopts', action='store_true', default=False,
                        help='run without optimisations')
    parser.add_argument('--opts', '-o', dest='opts', action='store_true', default=False,
                        help='run with optimisations')
    parser.add_argument('--pfe', '-p', dest='pfe', action='store_true', default=False,
                        help='run process flow elimination')
    parser.add_argument('--all', '-a', dest='all', action='store_true', default=False,
                        help='run all')
    parser.add_argument('--run-test', '-r', dest='run', action='append', default=[],
                        help='run a test case')
    parser.add_argument('--lang', '-l', dest='lang', action='append', default=[],
                        help='run a test case')
    args = parser.parse_args()
    langs = args.lang
    if len(langs) == 0:
        langs = ['Python']
    if args.clean:
        l = common_cases
        l.extend(flow_control_cases)
        tests = set(l)
        for test in tests:
            try:
                os.remove(test + '.res')
            except:
                pass
            try:
                os.remove(test + '.pyc')
            except:
                pass
            try:
                os.remove(test + '.pnml')
            except:
                pass
        try:
            os.remove('net.py')
        except: pass
        exit(0)

    if args.run:
        common_cases.intersection_update(args.run)
        flow_control_cases.intersection_update(args.run)
        print "common : ", common_cases
        print "flow_control_cases : ", flow_control_cases

    succeeded = 0
    failed = 0

    for lang in langs:
        llang = lang.lower()
        if args.noopts or args.all:
            print "*** {lang} without optimisations ***".format(lang=lang)
            for test in sorted(common_cases):
                if run_test(test, lang=llang):
                    succeeded += 1
                else:
                    failed += 1
                    failed_list.append(test)
            print
        if args.opts or args.all:
            print "*** {lang} with optimisations ***".format(lang=lang)
            for test in sorted(common_cases):
                if run_test(test, lang=llang, opt=True):
                    succeeded += 1
                else:
                    failed += 1
                    failed_list.append(test)
            print
        if args.pfe or args.all:
            print "*** {lang} with optimisations and flow control compression ***".format(lang=lang)
            for test in sorted(flow_control_cases):
                if run_test(test, lang=llang, opt=True, pfe=True):
                    succeeded += 1
                else:
                    failed += 1
                    failed_list.append(test)
            print
    print "{tests} tests ran".format(tests=str(succeeded + failed))
    print "{succeeded} succeeded".format(succeeded=str(succeeded))
    print "{failed} failed".format(failed=str(failed))

    if failed:
        print "failed tests: "
        for test in failed_list:
            print test
