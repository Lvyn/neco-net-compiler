#!/usr/bin/python
import argparse, shutil
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-prof', dest='prof', action='store_true', default=False,
                        help='enable profiling support')
    args = parser.parse_args()


    if args.prof: # profiler enabled
        # copy pxd file
        shutil.copyfile("ctypes_ext.pxd", "ctypes_extd.pxd")

        # produce pyx file
        ext_pyx  = open("ctypes_ext.pyx", "r")
        extd_pyx = open("ctypes_extd.pyx", "w")

        # add profiler and import pxd file
        extd_pyx.write("# cython: profile=True\n")
        extd_pyx.write("cimport ctypes_extd as ctypes_ext\n\n")

        # copy the rest of file ctypes_ext.pyx except first line
        for i,line in enumerate(ext_pyx):
            if i > 0:
                extd_pyx.write(line)

        # finalize
        ext_pyx.close()
        extd_pyx.close()

        # # build extension
        # setup(name="ctypes_extd",
        #       cmdclass={'build_ext': build_ext},
        #       ext_modules=[Extension("ctypes_extd", ["ctypes_extd.pyx"],
        #                              extra_link_args=["-lctypesd", "-L."])],
        #       script_args=["build_ext", "--inplace"])

    else: # profiler disabled
        # build extension
        # setup(name="ctypes_ext",
        #       cmdclass={'build_ext': build_ext},
        #       ext_modules=[Extension("ctypes_ext", ["ctypes_ext.pyx"],
        #                              extra_link_args=["-lctypes", "-L."])],
        #       script_args=["build_ext", "--inplace"])
        pass

