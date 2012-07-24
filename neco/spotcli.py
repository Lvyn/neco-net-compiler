""" CLI for neco-spot tool.

This module provides a CLI for neco that supports python 2.7.

The loading of this module will raise a runtime error
if loaded with wrong python version.
"""

import sys
if (2, 7, 0) <= sys.version_info < (3, 0, 0) :
    VERSION = (2, 7)
else:
    raise RuntimeError("unsupported python version")
import subprocess

def read_formula(file_name):
    f = open('neco_formula', 'r')
    s = f.read()
    f.close()
    return s
    
def parse_neco_formula_file(file_name):
    options = []
    formula = None
    f = open(file_name, 'r')
    for line in f:
        if line[0] == '\n':
            continue
        elif line[0] == '#':
            line = line[1:-1] # remove # and \n
            splited = line.split(' ')
            splited = [ item for item in splited if item != '' ]
            options.extend(splited)
        else:
            if formula:
                print >> sys.stderr, "(E) l{}. : only one formula is allowed at a time"
                exit(1)
            formula = line if line[-1] != '\n' else line[0:-1]     
            
    f.close()
    return options, formula

class Main():
    
    def __init__(self, args=None):
        options, formula = parse_neco_formula_file('neco_formula')
        opts = args if args else [] 
        opts.extend(options)
        opts.extend(sys.argv[1:])

        call = ['necospotcli']
        call.extend(opts)
        call.append(formula)
        
        try:            
            subprocess.call(call, stdout=sys.stdout)
        except OSError as e:
            print ">> ", e

if __name__ == '__main__':
    Main()
