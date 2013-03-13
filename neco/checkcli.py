""" CLI for neco check compiler.

This module provides a CLI for neco that supports python 2.7.

The loading of the module will raise a runtime error
if loaded with wrong python version.
"""

import sys
if (2, 7, 0) <= sys.version_info < (3, 0, 0) :
    VERSION = (2, 7)
else:
    raise RuntimeError("unsupported python version")

import argparse, os
from neco.config import Config
from neco import g_logo

import cPickle as pickle

from neco import compile_checker
from yappy.parser import LRParserError
import core.xmlproperties
import compilecli

def exclusive(elts, acc = False):
    try:
        e = bool(elts.pop())
    except IndexError:
        return True

    if e and acc:
        return False
    else:
        return exclusive(elts, e ^ acc)

class Main(object):

    def __init__(self, progname = 'checkcli', logo = False, cli_args = None):
        print "{} uses python {}".format(progname, sys.version)

        if logo:
            print g_logo

        prog = os.path.basename(sys.argv[0])
        formula_meta = 'FORMULA'
        xml_formula_meta = 'XML_FILE'
        # parse arguments
        parser = argparse.ArgumentParser(progname,
                                         argument_default = argparse.SUPPRESS,
                                         formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                         usage = "{} [OPTIONS]".format(prog))

        parser.add_argument('--net', '-n', default = 'net', dest = 'net', metavar = 'COMPILED_MODEL', type = str,
                            help = 'compiled model')
        parser.add_argument('--profile', '-p', default = 'profile', dest = 'profile', action = 'store_true',
                            help = 'enable profiling.')
        parser.add_argument('--include', '-I', default = ['.'], dest = 'includes', action = 'append', metavar = 'PATH',
                            help = 'additional search paths (libs, files).')
        parser.add_argument('--formula', metavar = formula_meta, type = str, default = "false",
                            help = 'formula to check')
        parser.add_argument('--xml', metavar = xml_formula_meta, default = None, dest = 'xml', type = str,
                            help = 'xml formula file')
        parser.add_argument('--neco-spot-args', '-ns', dest = 'ns_args', action = 'append', metavar = 'ARG', default = [],
                            help = 'additional arguments for neco-spot')

        if cli_args:
            args = parser.parse_args(cli_args)
        else:
            args = parser.parse_args()

        import imp
        fp, pathname, _ = imp.find_module(args.net)
        mod = imp.load_module(args.net, fp, pathname, ('.so', 'rb', imp.C_EXTENSION))
        if fp:
            fp.close()
        else:
            print >> sys.stderr, "unable to find module {}".format(args.net)
            exit(1)
        compiled_model = mod

        profile = args.profile
        formula = args.formula
        xml_file = args.xml

        if formula and xml_file:
            raise RuntimeError

        trace = pickle.loads(compiled_model._neco_trace_)
        model_file = trace['model']
        i = model_file.rfind('.')
        ext = model_file[i + 1:]
        name = model_file[:i]

        model, abcd, pnml = (None,) * 3
        if ext == 'py':
            model = name
        elif ext == 'abcd':
            abcd = model_file
        elif ext == 'pnml':
            pnml = model_file

        assert(exclusive([model, abcd, pnml]))
        if not model:
            model = model_file
        remove_pnml = False
        if abcd and not pnml:
            remove_pnml = True
            pnml = "/tmp/__neco__tmp.{}.pnml".format(os.getpid())

        net = None
        if abcd:
            compilecli.produce_pnml_file(model, pnml)
            net = compilecli.load_pnml_file(pnml)
        elif pnml:
            net = compilecli.load_pnml_file(model)
        elif model:
            net = compilecli.load_snakes_net(model, 'net')
        assert(net)


        try:
            env_includes = os.environ['NECO_INCLUDE'].split(":")
        except KeyError:
            env_includes = []

        args.includes.extend(env_includes)

        if formula:
            try:
                formula = core.properties.PropertyParser().input(formula)
            except LRParserError as e:
                import pprint
                pprint.pprint("Syntax error in formula.")
                exit(-1)
        elif xml_file:
            properties = core.xmlproperties.parse(xml_file)
            if not properties:
                print >> sys.stderr, "no property found in {}".format(xml_file)
                exit(1)
            elif len(properties) > 1:
                print >> sys.stderr, "neco can handle only one property at a time"
                exit(1)
            formula = properties[0].formula

        # setup config
        config = Config()
        config.set_options(profile = profile,
                           backend = 'cython',    # force cython
                           formula = formula,
                           trace_calls = False,
                           search_paths = args.includes,
                           trace = trace,
                           ns_args = args.ns_args)

        compile_checker(formula, net, config)

        if remove_pnml:
            print "Removing PNML ({})".format(pnml)
            try:
                os.remove(pnml)
            except IOError:
                pass

if __name__ == '__main__':
    Main()
