from snakes.lang import Unparser as _Unparser
from . import asdl

class Unparser(_Unparser) :
    def _FunctionDef (self, tree) :
        self.write("\n")
        if isinstance(tree.lang, asdl.Def) :
            self.fill("def " + tree.name + "(")
            for a in tree.args.args :
                a.annotation = None
        elif isinstance(tree.lang, (asdl.CDef, asdl.CpDef)) :
            if isinstance(tree.lang, asdl.CDef) :
                self.fill("cdef ")
            else :
                self.fill("cpdef ")
            if tree.lang.public :
                self.write("public ")
            self.dispatch(tree.returns)
            self.write(" " + tree.name + "(")
        else :
            assert False
        self.dispatch(tree.args)
        self.write(")")
        self.enter()
        for d in tree.decl :
            d.public = None
            self.dispatch(d)
        self.dispatch(tree.body)
        self.leave()
    def _arg (self, tree) :
        if tree.annotation :
            self.dispatch(tree.annotation)
            self.write(" ")
        self.write(tree.arg)
    def _ClassDef (self, tree):
        self.write("\n")
        if isinstance(tree.lang, asdl.Def) :
            self.fill("class ")
            tree.decl = []
        elif isinstance(tree.lang, asdl.CDef) :
            self.fill("cdef class ")
        else :
            assert False
        self.write(tree.name)
        if tree.bases :
            self.write("(")
            for a in tree.bases:
                self.dispatch(a)
                self.write(", ")
            self.write(")")
        self.enter()
        for d in tree.decl :
            self.dispatch(d)
        self.dispatch(tree.body)
        self.leave()
    def _CFor (self, tree) :
        self.fill("for ")
        self.dispatch(tree.start)
        self.dispatch(tree.start_op)
        self.dispatch(tree.target)
        self.dispatch(tree.stop_op)
        self.dispatch(tree.stop)
        self.enter()
        self.dispatch(tree.body)
        self.leave()
    def _Eq (self, tree) :
        self.write(" == ")
    def _NotEq (self, tree) :
        self.write(" != ")
    def _Lt (self, tree) :
        self.write(" < ")
    def _LtE (self, tree) :
        self.write(" <= ")
    def _Gt (self, tree) :
        self.write(" > ")
    def _GtE (self, tree) :
        self.write(" >= ")
    def _Is (self, tree) :
        self.write(" is ")
    def _IsNot (self, tree) :
        self.write(" is not ")
    def _In (self, tree) :
        self.write(" in ")
    def _NotIn (self, tree) :
        self.write(" not in ")
    def _CImport (self, tree) :
        self.fill("cimport ")
        self.write(", ".join(tree.names))
    def _CImportFrom (self, tree) :
        self.fill("from ")
        self.write(tree.module + " import ")
        self.write(", ".join(tree.names))
    def _Extern (self, tree) :
        self.write("\n")
        self.fill("cdef extern ")
        self.write(tree.type + " ")
        self.write(tree.name)
        if tree.args is not None :
            self.write("(")
            for i, a in enumerate(tree.args) :
                if i > 0 :
                    self.write(", ")
                self.dispatch(a)
            self.write(")")
    def _ExternFrom (self, tree) :
        self.write("\n")
        self.fill('cdef extern from "%s"' % tree.hfile)
        self.enter()
        for d in tree.body :
            d.inner = True
            self.dispatch(d)
        self.leave()
    def _CVar (self, tree) :
        if tree.inner :
            self.fill("")
        else :
            self.fill("cdef ")
            if tree.public :
                self.write("public ")
        self.write(tree.type + " " + tree.name)
        if tree.init is not None :
            self.write(" = ")
            self.dispatch(tree.init)
    def _CFunction (self, tree) :
        self.fill(tree.type)
        self.write(" " + tree.name + "(")
        for i, a in enumerate(tree.args) :
            if i > 0 :
                self.write(", ")
            self.dispatch(a)
        self.write(")")
    def _CStruct (self, tree) :
        if tree.inner :
            self.fill("")
        else :
            self.fill("cdef ")
            if tree.public :
                self.write("public ")
        self.write("struct " + tree.name)
        self.enter()
        if tree.body :
            for d in tree.body :
                d.inner = True
                self.dispatch(d)
        else :
            self.fill("pass")
        self.leave()
