import ast
from ast import *

def Name(id):
    return ast.Name(id=id)

def Call(func, args=[], keywords=[], starargs=None, kwargs=None):
    return ast.Call(func, args, keywords, starargs, kwargs)

def FunctionDef(name,
                args=ast.arguments(args=[],
                                   vararg=None,
                                   kwarg=None,
                                   defaults=[]),
                body=[],
                decorator_list=[]):
    return ast.FunctionDef(name, args, body, decorator_list)

def arguments(args=[], vararg=None, kwarg=None, defaults=[]):
    return ast.arguments(args, vararg, kwarg, defaults)

def If(test, body=[], orelse=[]):
    return ast.If(test, body, orelse)

def Tuple(elts=[]):
    return ast.Tuple(elts=elts)

def ClassDef(name, bases=[], body=[], decorator_list=[]):
    return ast.ClassDef(name, bases, body, decorator_list)

def List(elts):
    return ast.List(elts=elts)
