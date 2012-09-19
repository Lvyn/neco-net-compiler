from neco.asdl.cpp import * #@UnusedWildImport
from neco.utils import flatten_ast, OutputProviderPredicate
import sys

class CppHeaderFile(object):

    def __init__(self, name):
        self.name = name
        self.declarations = []
        self.body = []

    def write(self, env, base_dir = './'):
        module_ast = flatten_ast(body=self.body)

        f = open(base_dir + self.name, "w")
        last = self.name.rfind('/')
        guard = self.name[last:-1].replace('.', '_')
        f.write("#ifndef __{}__".format(guard))
        f.write("#define __{}__".format(guard))
        
        f.write("\n".join(self.declarations))
        CppUnparser(f).unparse(module_ast)
        
        f.write("#endif // __{}__".format(guard))
        f.close()


class IsCppHeaderFile(OutputProviderPredicate):

    def __call__(self, output):
        return isinstance(output, CppHeaderFile)


class CppUnparser(object):
    
    __native_type_map__ = { 'Void' : 'void',
                            'Bool' : 'bool',
                            'Char' : 'char',
                            'Short' : 'short',
                            'Int' : 'int',
                            'Long' : 'long',
                            'Float' : 'float',
                            'Double' : 'double', }
    
    def __init__(self, output):
        self.output = output
        self.ident = 0
        self.new_line = True
        
    def _ident_write(self, txt = ''):
        self.output.write('    ' * self.ident)
        self.output.write(txt)
        
    def _write(self, txt):
        self.output.write(txt)
        
    def _new_line(self):
        self.output.write('\n')
        
    def _start_block(self):
        self._write('{')
        self.ident += 1
        
    def _end_block(self):
        self._write('}')
        self.ident -= 1
        
    def unparse(self, node):
        cls_name = node.__class__.__name__
        if isinstance(node, list):
            for e in node:
                self.unparse(e)
                self._write('\n')

        elif node.isNative():
            self._NativeType(node, cls_name)

        else:
            attr = getattr(self, '_' + cls_name)
            attr(node)
    
    def _NativeType(self, node, cls_name):
        """	
        >>> CppUnparser(sys.stdout).unparse([ Void(), Bool() ])
        void 
        bool  
        
        >>> CppUnparser(sys.stdout).unparse([ Char(), Short(), Int(), Long() ])
        char 
        short 
        int 
        long
        
        >>> CppUnparser(sys.stdout).unparse([ Unsigned(Char()), Unsigned(Short()), Unsigned(Int()), Unsigned(Long()) ])
        unsigned char 
        unsigned short 
        unsigned int 
        unsigned long
        
        >>> CppUnparser(sys.stdout).unparse([ Float(), Double() ])
        float
        double
        """
        if (node.isUnsigned()):
            self._write('unsigned ')
            self.unparse(node.type)
            return
        self._write(self.__native_type_map__[cls_name])

    def _UserType(self, node):
        self._write(node.name)

    def _TemplateType(self, node):
        self._write(node.name)
        
    def _ClassDef(self, node):
        """
        >>> CppUnparser(sys.stdout).unparse( ClassDef(name='foo', attributes = []) )
        class foo {
        };
        """
        self._write('class {} '.format(node.name))
        self._start_block()
        self._new_line()
        
        for attr in node.attributes:
            self.unparse(attr)
        
        self._end_block()
        self._write(';')
    
    def _StructDef(self, node):
        """
        >>> CppUnparser(sys.stdout).unparse( StructDef(name='foo', attributes = []) )
        struct foo {
        };
        >>> CppUnparser(sys.stdout).unparse( StructDef(name='foo', attributes = [ AttrDecl(Int(), 'i'), AttrDecl(Bool(), 'b'),  ]) )
        struct foo {
            int i;
            bool b;
        };
        >>> CppUnparser(sys.stdout).unparse( StructDef(name='foo', attributes = [ AttrDecl(Int(), 'pack', [4]), AttrDecl(Bool(), 'b'),  ]) )
        struct foo {
            int pack[4];
            bool b;
        };
        """
        self._write('struct {} '.format(node.name))
        self._start_block()
        self._new_line()
        
        for attr in node.attributes:
            self.unparse(attr)
            self._new_line()
        
        self._end_block()
        self._write(';')
        
    def _AttrDecl(self, node):
        self._ident_write() # fix position
        self.unparse(node.type)
        if node.array:
            self._write(' {}[{}];'.format(node.name, node.array[0]))
        else:
            self._write(' {};'.format(node.name))

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
    
