""" Stub unparser
"""
import neco.asdl.stub
import sys

def interleave(inter, f, seq):
    """Call f on each item in seq, calling inter() in between.
    """
    seq = iter(seq)
    try:
        f(seq.next())
    except StopIteration:
        pass
    else:
        for x in seq:
            inter()
            f(x)

class Unparser:
    """Methods in this class recursively traverse an AST and
    output source code for the abstract syntax; original formatting
    is disregarged. """

    def __init__(self, tree, out_file = sys.stdout):
        """Unparser(tree, file=sys.stdout) -> None.
         Print the source for tree to file."""
        self.f = out_file
        self._indent = 0
        self.dispatch(tree)
        self.f.flush()

    def fill(self, text = ""):
        "Indent a piece of text, according to the current indentation level"
        self.f.write("\n"+"    "*self._indent + text)

    def write(self, text):
        "Append a piece of text to the current line."
        self.f.write(text)

    def enter(self):
        "increase the indentation."
        self._indent += 1

    def leave(self):
        "Decrease the indentation level."
        self._indent -= 1

    def dispatch(self, tree):
        "Dispatcher function, dispatching tree type T to method _T."
        if isinstance(tree, list):
            for t in tree:
                self.dispatch(t)
            return
        meth = getattr(self, "_"+tree.__class__.__name__)
        meth(tree)

    def _str(self, s):
        self.write(s)

    ############### Unparsing methods ######################
    # There should be one method per concrete grammar type #
    # Constructors should be grouped by sum type. Ideally, #
    # this would follow the order in the grammar, but      #
    # currently doesn't.                                   #
    ########################################################

    def _Stub(self, tree):
        for stmt in tree.body:
            self.dispatch(stmt)

    # Stmt
    def _StubDef(self, tree):
        self.fill("StubDef " + tree.name + " => ")
        self.enter()
        self.dispatch(tree.body)
        self.leave()
        self.write("\n")

    def _StubEntry(self, tree):
        self.fill("entry ")
        interleave(lambda: self.write(", "), self.dispatch, tree.names)
        

def unparse(tree, output=sys.stdout):
    Unparser(tree, output)


if __name__=='__main__':
    from neco.asdl.stub import *
    tree = Stub([StubDef("test",
                        [ StubEntry(["e1", "e2"]),
                          StubEntry(["e3", "e4"])]
                        )
                ])
    unparse(tree)
