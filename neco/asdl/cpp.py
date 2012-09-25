# this file has been automatically generated running:
# setup.py install --prefix=~/.local
# timestamp: 2012-09-24 12:06:32.836848

from snakes.lang import ast
from ast import *

class _AST (ast.AST):
    _fields = ()
    _attributes = ()
    
    def __init__ (self, **ARGS):
        ast.AST.__init__(self)
        for k, v in ARGS.items():
            setattr(self, k, v)
    
    def isAttrDecl(self):
        return False
    
    def isAttribute(self):
        return False
    
    def isBool(self):
        return False
    
    def isChar(self):
        return False
    
    def isClassDef(self):
        return False
    
    def isComponent(self):
        return False
    
    def isDouble(self):
        return False
    
    def isFile(self):
        return False
    
    def isFloat(self):
        return False
    
    def isInt(self):
        return False
    
    def isLong(self):
        return False
    
    def isNative(self):
        return False
    
    def isNativeDec(self):
        return False
    
    def isNativeInt(self):
        return False
    
    def isShort(self):
        return False
    
    def isStmt(self):
        return False
    
    def isStructDef(self):
        return False
    
    def isTemplateDef(self):
        return False
    
    def isTemplateType(self):
        return False
    
    def isType(self):
        return False
    
    def isUnsigned(self):
        return False
    
    def isUserType(self):
        return False
    
    def isVoid(self):
        return False

class Type (_AST):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        _AST.__init__(self, **ARGS)
    
    def isType(self):
        return True

class Stmt (_AST):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        _AST.__init__(self, **ARGS)
    
    def isStmt(self):
        return True

class Attribute (_AST):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        _AST.__init__(self, **ARGS)
    
    def isAttribute(self):
        return True

class File (_AST):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        _AST.__init__(self, **ARGS)
    
    def isFile(self):
        return True

class TemplateDef (Stmt):
    _fields = ('targs', 'cls', 'bind')
    _attributes = ()
    
    def __init__ (self, cls, targs=[], bind=[],  **ARGS):
        Stmt.__init__(self, **ARGS)
        self.targs = list(targs)
        self.cls = cls
        self.bind = list(bind)
    
    def isTemplateDef(self):
        return True

class Component (File):
    _fields = ('body',)
    _attributes = ()
    
    def __init__ (self, body=[],  **ARGS):
        File.__init__(self, **ARGS)
        self.body = list(body)
    
    def isComponent(self):
        return True

class UserType (Type):
    _fields = ('name',)
    _attributes = ()
    
    def __init__ (self, name,  **ARGS):
        Type.__init__(self, **ARGS)
        self.name = name
    
    def isUserType(self):
        return True

class AttrDecl (Attribute):
    _fields = ('type', 'name', 'array')
    _attributes = ()
    
    def __init__ (self, type, name, array=None,  **ARGS):
        Attribute.__init__(self, **ARGS)
        self.type = type
        self.name = name
        self.array = array
    
    def isAttrDecl(self):
        return True

class ClassDef (Stmt):
    _fields = ('name', 'attributes')
    _attributes = ()
    
    def __init__ (self, name, attributes=[],  **ARGS):
        Stmt.__init__(self, **ARGS)
        self.name = name
        self.attributes = list(attributes)
    
    def isClassDef(self):
        return True

class TemplateType (Type):
    _fields = ('name',)
    _attributes = ()
    
    def __init__ (self, name,  **ARGS):
        Type.__init__(self, **ARGS)
        self.name = name
    
    def isTemplateType(self):
        return True

class StructDef (Stmt):
    _fields = ('name', 'attributes')
    _attributes = ()
    
    def __init__ (self, name, attributes=[],  **ARGS):
        Stmt.__init__(self, **ARGS)
        self.name = name
        self.attributes = list(attributes)
    
    def isStructDef(self):
        return True

class Native (Type):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        Type.__init__(self, **ARGS)
    
    def isNative(self):
        return True

class Unsigned (Native):
    _fields = ('type',)
    _attributes = ()
    
    def __init__ (self, type,  **ARGS):
        Native.__init__(self, **ARGS)
        self.type = type
    
    def isUnsigned(self):
        return True

class Bool (Native):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        Native.__init__(self, **ARGS)
    
    def isBool(self):
        return True

class NativeInt (Native):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        Native.__init__(self, **ARGS)
    
    def isNativeInt(self):
        return True

class Void (Native):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        Native.__init__(self, **ARGS)
    
    def isVoid(self):
        return True

class NativeDec (Native):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        Native.__init__(self, **ARGS)
    
    def isNativeDec(self):
        return True

class Long (NativeInt):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        NativeInt.__init__(self, **ARGS)
    
    def isLong(self):
        return True

class Short (NativeInt):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        NativeInt.__init__(self, **ARGS)
    
    def isShort(self):
        return True

class Double (NativeDec):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        NativeDec.__init__(self, **ARGS)
    
    def isDouble(self):
        return True

class Int (NativeInt):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        NativeInt.__init__(self, **ARGS)
    
    def isInt(self):
        return True

class Float (NativeDec):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        NativeDec.__init__(self, **ARGS)
    
    def isFloat(self):
        return True

class Char (NativeInt):
    _fields = ()
    _attributes = ()
    
    def __init__ (self,  **ARGS):
        NativeInt.__init__(self, **ARGS)
    
    def isChar(self):
        return True
