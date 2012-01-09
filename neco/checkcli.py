""" CLI for neco check compiler.

This module provides a CLI for neco that supports python 2.7.

The loading of the module will raise a runtime error
if loaded with wrong python version.
"""

import subprocess, re, sys
if (2, 7, 0) <= sys.version_info < (3,0,0) :
    VERSION=(2,7)
else:
    raise RuntimeError("unsupported python version")

import argparse
import neco.config as config
from neco.utils import fatal_error
from neco import compile_net, g_logo

import backends

import backends
import core.check
import core.onesafe as onesafe

import imp, cProfile, pstats, os, bz2, gzip
from time import time

from neco import compile_checker

class Main(object):

    _instance_ = None

    def __init__(self, progname, logo=False):

        print "{} uses python {}".format(progname, sys.version)
        assert(not self.__class__._instance_) # assert called only once
        self.__class__._instance_ = self # setup the unique instance

        if logo:
            print g_logo

        # parse arguments
        parser = argparse.ArgumentParser(progname,
                                         argument_default=argparse.SUPPRESS,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument('--trace', '-t', default='trace', dest='trace', metavar='TRACEFILE', type=str,
                            help='compilation trace file')

        parser.add_argument('--profile', '-p', default='profile', dest='profile', action='store_true',
                            help='enable profiling.')

        parser.add_argument('formula', metavar='FORMULA', type=str, help='formula')

        args = parser.parse_args()

        trace = args.trace
        profile = args.profile
        formula = args.formula

        # setup config
        config.set(#debug = cli_argument_parser.debug(),
                   profile = profile,
                   backend = 'cython', # force cython
                   formula = formula,
                   trace_calls = False,
                   trace_file = trace)

        compile_checker(formula)

if __name__ == '__main__':
    Main('ckeckcli')
