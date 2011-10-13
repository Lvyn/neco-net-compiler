#!/usr/bin/python
import glob, re, os
import argparse

class Marking(object):
    def __init__(self):
        self.data = {}

    def add_token(self, place, token):
        try:
            place = self.data[place]
        except KeyError:
            self.data[place] = {}
            place = self.data[place]
        try:
            place[token] += 1
        except KeyError:
            place[token] = 1

    def create_place(self, place):
        try:
            self.data[place]
        except KeyError:
            self.data[place] = {}

    def __repr__(self):
        return str(self.data)

    def __str__(self):
        return str(self.data)

    def __eq__(self, other):
        return self.data == other.data

class MarkingSet(object):
    def __init__(self):
        self.data = set()

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

class FormatError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class FileReader(object):

    def __init__(self, filename):
        self.filename = filename
        self.line = 0
        self.file = open(filename, 'r')

    def readline(self):
        s = self.file.readline()
        if s == '':
            raise EOFError
        self.line += 1
        if s == '\n':
            return self.readline()
        return s

class SpecReader(FileReader):

    def __init__(self, filename):
        FileReader.__init__(self, filename)
        self.markings = MarkingSet()

    def read(self):
        check = self.readcheck()
        if check == 'markings':
            self.readmarkings()
        else:
            raise FormatError("unknown checking specification (%s) at line %d" % (check, self.line))

    def readcheck(self):
        s = self.readline()
        if self.line != 1:
            raise FormatError("check should be the first line")
        m = re.match(r"check\s*-\s*(?P<check>\w+)", s)
        if not m:
            raise FormatError("%s: syntax error at line %s" % (self.filename, self.line))
        check = m.group('check')
        return check

    def readmarkings(self):
        while True:
            try:
                self.readmarking()
            except EOFError:
                break

    def readmarking(self):
        marking = Marking()
        s = self.readline()
        m = re.match(r"begin marking", s)
        if not m:
            print s
            raise FormatError("%s: syntax error at line %s" % (self.filename, self.line))
        s = self.readline()
        while not re.match(r"end marking", s):
            m = re.match(r'(?P<place>[a-z0-9().#\'`]+)\s*-\s*(?P<tokens>(\'?\w*\'?\s)*)', s)
            if not m:
                raise FormatError("%s: syntax error at line %d" % (self.filename, self.line))
            place = m.group('place')
            tokens = re.split(r'\W+', m.group('tokens'))
            for token in tokens:
                if token == '':
                    marking.create_place(place)
                    continue
                marking.add_token(place, token)
            s = self.readline()
        self.markings.add(marking)

import subprocess

failed_list = []

def run_test(module_name, lang='python', opt=False, pfe=False):
    print "Running test %s..." % module_name
    expected = module_name + '.out'
    got = module_name + '_res'

    args = ['python', "../../neco",
            '-m', module_name,
            '-k', got,
            '-l', lang,
            '-I../common']
    if opt:
        args.append('--optimise')
    if pfe:
        args.append('--flow-elimination')

    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    r = p.wait()
    if r != 0:
        return False
    e_reader = SpecReader(expected)
    g_reader = SpecReader(got)
    e_reader.read()
    g_reader.read()
    if not e_reader.markings == g_reader.markings:
        print "test %s failed..." % module_name
        print "expected: "
        print e_reader.markings
        print "got: "
        print g_reader.markings
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
                    'basic_test_1',
                    'basic_test_2'])

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

