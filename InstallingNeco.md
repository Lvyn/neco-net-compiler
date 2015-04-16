# Installing Neco in local path (GNU/Linux) #

This section explains how to setup neco in local path (for example in your home directory). First we will need to retrieve the source code then setup the environment. It is essential to have dependencies installed before installing neco.

## Dependencies ##

Essential:
  * **mercurial** : needed to retrieve source;
  * **Python 2.7 including C headers** : neco is written in python;
  * **SNAKES toolkit** (http://code.google.com/p/python-snakes/) : neco uses SNAKES as a front-end. Remark: Snakes has an implicit dependency to python-tk;
  * **python yappy parser generator**;
  * **cython >= 0.17.1** : without it cython backend will not be usable; (will become an optional feature in future)
  * **gcc >= 4.6.1** : not tested with other versions, needed for cython   backend; (will be optional in future)

Optional:
  * **spot library** (see http://spot.lip6.fr/wiki/) : needed for checking LTL formulas.

## Installing SNAKES ##

Neco uses features that actually are not available in the PPA version of SNAKES, nor in the ones from the download section. Thus, you need to use the repository one. First, retrieve the source using mercurial:
```
hg clone https://code.google.com/p/python-snakes/
```
then in 'python-snakes' directory type the following
```
python setup.py install
```
This will install SNAKES on your system.

## Retrieve Neco source ##

To retrieve source you need mercurial installed (see http://doc.ubuntu-fr.org/hg_mercurial for ubuntu). To retrieve source simply refer to http://code.google.com/p/neco-net-compiler/source/checkout.

## Setup Neco without LTL model-checking ##

Before using Neco we need to install it. To do so, change current directory to `neco-net-compiler` (the downloaded repository) then run
```
python setup.py install --prefix=$HOME/.local
```
The prefix option says where to install neco, here for example into  `.local` folder in my home directory. The installation will notify to update your `.bashrc` file to setup your environment.

If you get the following error:
```
Traceback (most recent call last):
  File "setup.py", line 7, in <module>
    from snakes.lang.asdl import compile_asdl
ImportError: cannot import name compile_asdl
```
Then you're using an old version of SNAKES.

## Setup Neco with LTL model-checking ##

First you need to install SPOT library, for this step refer to http://spot.lip6.fr/wiki/.

The remaining is almost the same than installing Neco without LTL model-checking, just type
```
python setup.py install enable-neco-spot --prefix=$HOME/.local
```
The prefix option says where to install neco, here for example into  `.local` folder in my home directory, and `enable-neco-spot` says to enable LTL model-checking features. The installation will notify to update your `.bashrc` file to setup your environment.

If you get the following error:
```
Traceback (most recent call last):
  File "setup.py", line 7, in <module>
    from snakes.lang.asdl import compile_asdl
ImportError: cannot import name compile_asdl
```
Then you're using an old version of SNAKES.

## Setup the environment ##

Once you have installed Neco, you need to setup the environment by modifying your `$HOME/.bashrc` file.

To do so, you will have to modify your `$HOME/.bashrc` file : append the lines given by the invocation of `setup.py` (cf. previous step). It should be something like:

```
export PATH=$PATH:$HOME/.local/bin
export PYTHONPATH=$PYTHONPATH:$HOME/.local/lib/python2.7/site-packages
export NECO_INCLUDE=$HOME/.local/lib/python2.7/site-packages/neco/ctypes:$HOME/.local/lib/python2.7/site-packages/neco/backends/python:$HOME/.local/lib/python2.7/site-packages
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$NECO_INCLUDE
```

This will say to Neco where to locate executables and useful files. To use this new configuration restart your terminal or type

```
source $HOME/.bashrc
```

## Test your configuration ##

Move to `neco-net-compiler/tests/basics` and run `./run_tests.py PythonBackend`. You can also test cython backend by running `./run_tests.py CythonBackend`, however it takes much more time. Both backends can be tested using `./run_tests.py` command.

If you're using the LTL model-checking feature, you can also use `./run_checks.sh` to check some basic formulas.

Files created during the test procedure can be removed using `./run_test.py clean`.