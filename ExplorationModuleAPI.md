# Exploration module API #

The compilation of the Petri net produces a python module this page details its interface.

## Python interface (python, cython backend) ##
  * A marking type `Marking` providing methods
    * `copy` : copy state
    * `__repr__` : string representation
    * `__dump__` : human readable string representation
    * `__line_dump__` : one line human readable string representation
    * `__eq__` : equality test
    * `__hash__` : hash function
  * Function `succs(marking, neco_ctx)` that computes successor states of a marking. This function returns a set of markings and its arguments are:
    * `marking` is the current marking
    * `neco_ctx` is a context used to discover new states, it takes track of previously discovered states and remaining states. It may also store optimization specific data.
  * Function `init()` that returns the initial marking of the Petri net.
  * Other functions are provided however should not be used.
  * An initial `NecoCtx` object (neco context) can be built using its constructor without arguments. Refer to file `neco/backends/python/include.py` for more details.


## C++ interface (cython backend) ##

The compilation of the Petri net using the Cython backend also produces a python module with the interface above but also a C++ api. This api is used by neco-spot and this is the main reason why LTL model-checking is not available using Python backend.

### The C++ api ###
  * an opaque structure `struct Marking` for the Petri net marking
  * an opaque structure `struct NecoCtx` which is a context used by function `succs`.
  * function `struct NecoCtx* neco_ctx(struct Marking *)` that builds a struct `NecoCtx` out of a marking (the current marking, usually the initial one)
  * `neco_list_t* neco_succs(struct Marking*, struct NecoCtx*)` successor function wrapper, it returns a list of successor states. The `neco_list_t` type is a simple STL vector.
```
typedef std::vector<void*> neco_list_t;

typedef void (*deletion_callback_t)(void *);
void neco_list_delete_elts(neco_list_t* list, deletion_callback_t del);
```

  * `char* neco_marking_dump(struct Marking *)` a wrapper for marking dump function.
  * `struct Marking* neco_marking_copy(struct Marking *)` a wrapper for marking copy function
  * `int neco_marking_compare(struct Marking *, struct Marking *)` :  a wrapper for marking compare function
  * `int neco_marking_hash(struct Marking *)` :  a wrapper for marking hash function
  * `struct Marking *neco_init(void)` : a wrapper for function init