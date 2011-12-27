""" CLI for neco exploration tool.

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
import imp, cProfile, pstats, os, bz2, gzip
from time import time

from snakes.pnml import loads

def try_open_file(file_name):
    """ Helper function to open files with compression support (bz2, gz).
    """
    try:
        std_map = { 'stdout' : sys.stdout, 'stderr' : sys.stderr }
        out_file = std_map[file_name]
    except KeyError:
        basename, extension = os.path.splitext(file_name)
        if extension == '.bz2':
            print "bz2 compression enabled for file {}".format(file_name)
            out_file = bz2.BZ2File(file_name, 'w', 2048, compresslevel=6)
        elif extension == '.gz':
            print "gzip compression enabled for file {}".format(file_name)
            out_file = gzip.GzipFile(file_name, 'w', compresslevel=6)
        elif extension == '':
            print "raw text output for file {}".format(file_name)
            out_file = open(file_name, 'w')
        else:
            print >> sys.stderr, "unsupported extension: {}".format(extension)
            print >> sys.stderr, "supported extensions: .bz2 .gz"
            exit(-1)
    return out_file



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
        
        parser.add_argument('--dump', '-d', default=None, dest='dump', metavar='DUMPFILE', type=str,
                            help='dump markings to file (supports bz2 and gz compression)')
                                         
        parser.add_argument('--graph', '-g', default=None, dest='graph', nargs=2, metavar=('MAPFILE',
                                                                                          'GRAPHFILE'),
                            help='produce reachability graph (supports bz2 and gz compression)')
        
        parser.add_argument('--profile', '-p', default=False, dest='profile', action='store_true',
                            help='enable profiling support')
        
        args = parser.parse_args()
                
        profile = args.profile
        dump_markings = args.dump
        graph = args.graph
        
        # setup config
        config.set(#debug    = cli_argument_parser.debug(),
                   profile  = profile,
                   trace_calls = False)

        self.dump_markings = dump_markings
        self.graph = bool(graph)        
        if graph:
            map_file, graph_file = graph
            self.map_file, self.graph_file = map_file, graph_file
        
        if dump_markings:
            if graph:
                fatal_error("dump markings option cannot be used with graph option.")
        
        # load module
        try:
            fp, pathname, description = imp.find_module("net")
            self.compiled_net = imp.load_module("net", fp, pathname, description)
        except ImportError:
            fatal_error("No net module in PYTHONPATH", -1)
        
        # explore
        if profile:
            # produce exploration trace
            import cProfile
            if not dump_markings and not graph:
                cProfile.run('explorecli.Main._instance_.explore()', 'explore.prof')

            elif self.dump_markings:
                # produce exploration trace with marking dump
                cProfile.run('explorecli.Main._instance_.dump_markings()', 'explore_dump.prof')

            elif self.graph:
                # produce exploration trace with reachability graph
                cProfile.run('explorecli.Main._instance_.dump_graph()', 'explore_graph.prof')

        else: # without profiler
            if not dump_markings and not graph:
                self.explore()

            elif dump_markings:
                self.explore_dump()

            elif graph:
                self.explore_graph()

    def explore(self):
        """ Explore state space. """

        net = self.compiled_net
        start = time()
        ss = net.state_space()
        end = time()
        print "exploration time: ", end - start
        print "len visited = %d" % (len(ss))

    def explore_dump(self):
        """ Explore state space. """

        dfile = try_open_file(self.dump_markings)

        net = self.compiled_net
        start = time()
        ss = net.state_space()
        end = time()
        print "exploration time: ", end - start
        print "len visited = %d" % (len(ss))

        dfile.write('[')
        for s in ss:
            dfile.write(s.__dump__())
            dfile.write(', ')
        dfile.write(']')
        return (end - start, ss)

    def explore_graph(self):
        """ Build reachability graph. """
        # select output stream
        map_file   = try_open_file(self.map_file)
        graph_file = try_open_file(self.graph_file)

        net = self.compiled_net
                
        start = time()
        graph, map = net.state_space_graph()
        end = time()
        print "exploration time: ", end - start
        print "len visited = %d" % (len(map.keys()))

        #map_file.write('{\n')
        for key, value in map.iteritems():
            map_file.write("{} : {}\n".format(repr(value), key.__dump__()))
        #map_file.write('}\n')

        #graph_file.write('{\n')
        for key, value in graph.iteritems():
            graph_file.write("{} : {}\n".format(repr(key), repr(value)))
        #graph_file.write('}\n')

        return (end - start, graph.keys())


if __name__ == '__main__':
    Main('explorecli')
