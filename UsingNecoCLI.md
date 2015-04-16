This page explains how to use Neco command line interface. Neco is still in development so if something is wrong on this page please post a bug report and refer to `--help`.

# Introduction #

Neco is a tool set (unix like philosophy) that allows to compile models into shared libraries, compute state spaces, build reachability graphs, and check LTL formulae.

# Compile a model #

Each of the following cases will produce a python module or a shared object depending on the backend, see [more options](UsingNecoCLI#More_options.md) for backend selection.

## Compile a Petri net designed with Snakes (python code) ##

To compile a petri net designed with Snakes [[1](http://pommereau.blogspot.com/2010/01/snakes.html)][[2](http://code.google.com/p/python-snakes/)], we use command `neco-compile` with option `--module` or `-m`. This option needs one argument which is the python module to compile without the `.py` extension.

`neco-compile` will look for a variable named `net` which is supposed to hod a `PetriNet` object. The name of this variable can be changed with `--netvar` option.

Example:
```
neco-compile --module model.py --netvar net
```

Additional options can be specified, see [more options](UsingNecoCLI#More_options.md).

For more information about creating models with SNAKES, refer to [the SNAKES toolkit](http://www.ibisc.univ-evry.fr/~fpommereau/SNAKES/index.html)

## Compile a Petri net specified in PNML ##

To compile a petri net model specified in PNML we simply use `neco-compile` with `--pnml` option that requires a pnml file as argument.

Example:
```
neco-compile --pnml model.pnml
```

Additional options can be specified, see [more options](UsingNecoCLI#More_options.md).

## Compile a Petri net specified in ABCD ##

To compile a petri net model specified with the ABCD formalism (see Snakes[[1](http://pommereau.blogspot.com/2010/01/snakes.html)][[2](http://code.google.com/p/python-snakes/)] for more details) we will use `neco-compile` with `--abcd` option. This option requires an abcd file as argument.

Compiling an ABCD model consists in transforming it into PNML and then compiling the PNML file. After compiling the ABCD file the PNML file is removed. This behavior can be changed by specifying a PNML file with `--pnml` option, then the intermediate PNML file will be preserved.

Example:
```
neco-compile --abcd model.abcd --pnml created_file.pnml
```

Additional options can be specified, see [more options](UsingNecoCLI#More_options.md).

## More options ##

Option `--lang` or `-l` specify target language for the compiler it accepts `-lpython` for Python backend or `-lcython` for Cython backend.

Option `--import` or `-i` is used to specify an additional python module to import for example: `neco-compile -m mymodel -i mymodule` will import module `mymodule` in compiled version of `mymodel`.

Option `--optimize` or `-O` is used to enable optimisations, this will allow the use of specific implementations for place based on information extracted from the net.

Option `--optimize-pack` or `-Op` is used to enable marking compression optimization in Cython backend, this will allow the use compact implementation for some places based on data extracted from the net. This option should be used with option `-O`

Option `--optimize-flow` or `-Of` is used to enable flow control places compression in ABCD models. This option should be used with options `-O` and `-Of`.

Option `--include` or `-I` add search paths for compilation process (Cython backend).

# Explore state spaces #

The state space exploration tool is `neco-explore` and will use a python module or shared object resulting from the invocation of `neco-compile`.
This command looks for a `net.py` or `net.so` file that represents a compiled model and then computes the number of states as default behavior.

There are two useful options that `neco-explore` provides:
  1. `--dump` or `-d` dumps all markings into a file, this is a raw dump of markings without relations between them.
  1. `--graph` or `-g` builds the state graph resulting from the exploration. This option takes two arguments
    1. MAPFILE: a map file where a map from integer to markings will be written. The syntax of this file is: `"(integer : marking EOL)*EOF"` where marking is a python representation of a marking sound with `eval`.
    1. GRAPHFILE: a graph file where the graph will be stored. The graph is presented with adjacency lists, more precisely `"(integer : integer list EOL)*EOF"`

Examples:
  1. compute the number of reachable states
```
neco-explore
```
  1. build state space and store it in file states
```
neco-explore --dump states
```
  1. build reachability graph
```
neco-explore --graph map_file graph_file
```

## Full example ##

Let us consider the following simple model, and call it `model.py`.

```
from snakes.nets import *

net = PetriNet('Net')

s1 = Place('s1', [dot], tBlackToken)
s2 = Place('s2', [],    tBlackToken)

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1',  't', Value(dot))
net.add_output('s2', 't', Value(dot))
```

This model contains two places with black token type, and one unique transition that consumes a token from place s1 and produces a black token in place s2.

  1. we compile the model
```
neco-compile -m model.py -lcython
```
  1. we build the state space and dump it to file `states`
```
neco-explore --dump states
```
  1. we can also build the reachability graphs
```
neco-explore --graph map graph
```
It outputs the reachability graph as an adjacency list, the graph is written to file `graph`, where each state is represented as an integer, and the mapping from integers to states is stored in file `map`.


# Check LTL properties using neco-spot #

To check LTL properties, we need first to compile a model using the Cython backend (so just use -lcython when compiling the model). The next step is to build a checker.

A checker is a module that checks if an atomic proposition in the LTL formula is true at a marking or not. The checker module is build based on a provided formula, atomic propositions are extracted and adequate code generated. This compilation step is needed because `neco-compile` produce a different marking structure for each model, and thus a generic checker would not work.

For LTL syntax refer to [this page](LTL_Syntax.md).


## How to compile a checker ##

To compile the checker we use `neco-check` command providing a formula. For example:

```
neco-check --formula="G (card(marking('s1')) + card(marking('s2')) = 1)"
```

This outputs two files, `checker.so` and `neco_formula`, which are respectively the checker module, and a formula where atomic propositions were replaced with identifiers. The neco\_formula file serves as an interface with `neco-spot` and may provide configuration options.

## Check the formula ##

The checker module built, we can perform the checking of the associated formula. To do so, we use `neco-spot` command providing the neco\_formula file name. This program uses the SPOT[[3](http://spot.lip6.fr/wiki/)] library to perform the LTL checking.

```
neco-spot neco_formula
```

**Remark.** `neco-spot` can also be used to compute state spaces using the `-k` option.

## Full example ##

Let us consider the following simple model, and call it `model.py`.

```
from snakes.nets import *

net = PetriNet('Net')

s1 = Place('s1', [dot], tBlackToken)
s2 = Place('s2', [], tBlackToken)

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Value(dot))
net.add_output('s2', 't', Value(dot))
```

This model contains two places with black token type, and one unique transition that consumes a token from place s1 and produces a black token in place s2.

  1. we compile the model
```
neco-compile -m model.py -lcython
```
  1. we build the checker module.
```
neco-check --formula="F (marking('s2') = [dot] and deadlock)"
```
  1. we check the formula
```
neco-spot neco_formula
```

The last step outputs
```
Formula: (F ((p0) /\ DEAD))
importing net
importing checker
negating the formula
2 unique states visited
0 strongly connected components in search stack
1 transitions explored
2 items max in DFS search stack
0 pages allocated for emptiness check
no counterexample found
```

if we had provided the formula `"F (marking('s2') = [dot] and not deadlock)"` then the result would be:

```
Formula: (F ((p0) /\ (!DEAD)))
importing net
importing checker
negating the formula
2 unique states visited
2 strongly connected components in search stack
2 transitions explored
2 items max in DFS search stack
256 pages allocated for emptiness check
a counterexample exists (use -C to print it)
```

The counter example can be printed using `-C` option when calling `neco-spot` and outputs:


```
Prefix:
  {
's1' : [dot],
's2' : [],
} * G(DEAD | !p0)
  |  !p0 & !DEAD	
Cycle:
  {
's1' : [],
's2' : [dot],
} * G(DEAD | !p0)
  |  DEAD & p0
```


---


Steps 2 and 3 can be combined in one command using the `neco-check-spot` script.

```
neco-check-spot --formula="F (marking('s2') = [dot] and not deadlock)" -ns="-C"
```