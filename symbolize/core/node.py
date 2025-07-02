"""
node.py
Defines the Node class for symbolic representation of AST nodes.
"""
import ast
from types import FunctionType
from .tree import draw_tree
from .ast_utils import toast, asteval, unparse

def is_concrete(node):
  """Check if the node is a concrete value (not a Node or lambda)."""
  match(node):
    case FunctionType(__name__ = '<lambda>'): return False
    case Node(): return False
  return True

class Node():
  """Node class for symbolic representation of python values"""

  def __init__(self, node, value=None):
    match node:
      case Node(ast=_ast):
        self.ast = _ast
      case FunctionType(__name__ = '<lambda>'):
        self.ast = make_lambda(node)
      case _:
        self.ast = toast(node)
    if value is not None: # ast may already have a value, don't clobber
      self.value = value

  @property
  def value(self):  return getattr(self.ast, '_value', None)
  @value.setter
  def value(self, value): self.ast._value = value

  def __eq__(self, other):
    return isinstance(other, Node) and unparse(self) == unparse(other)

  def __repr__(self) -> str:
    if isinstance(self.ast, ast.Lambda): 
      return unparse(self)
    val = self.eval() #Should we skip here, only do in as_list?
    val = '' if (val == self) or (val is None) else f' = {val}'
    return unparse(self) + val

  def are_calls_concrete(self):
    """Check if all Calls in the AST are concrete (no symbolic args)."""
    #TODO: maybe add a type hint that allows symbolic args
    match self.ast:
      case ast.Lambda():
        return True
      case ast.Call(func=func, args=args):
        func = asteval(func)
        if is_concrete(func):
          args = [asteval(arg) for arg in args]
          if any(isinstance(arg, Node) for arg in args):
            return False

    return all(child.are_calls_concrete() for child in self.children())

  def eval(self):
    """Evaluate the AST node, returning its value."""
    try:
      if not self.are_calls_concrete(): 
        return None

      val = asteval(self)
      match val:
        case FunctionType(__name__ = '<lambda>'): return Node(val)
      return val
    except NameError as e:
      print(e)
      return None

  def children(self):
    """ Return the ast node children as Node instances. """
    return [Node(c) for c in ast.iter_child_nodes(self.ast)
                    if isinstance(c, ast.expr)                ]

  def as_list(self):
    """ Convert the Node to a list representation for visualization. """
    return [repr(self), *(c.as_list() for c in self.children())]

  def _repr_svg_(self):
    tree = draw_tree(self.as_list())
    return tree._repr_svg_()

  def __call__(self, *args):
    args = [toast(arg) for arg in args]
    node = ast.Call(func=self.ast, args=args, keywords=[])
    return Node(node)

  def __and__(self, other):
    node = ast.BinOp(op=ast.BitAnd(), left=self.ast, right=toast(other))
    return Node(node)

  def __iadd__(self, other):      self.value += other; return self
  def __isub__(self, other):      self.value -= other; return self
  def __imul__(self, other):      self.value *= other; return self
  def __itruediv__(self, other):  self.value /= other; return self
  def __iand__(self, other):      self.value &= other; return self
  def __ior__(self, other):       self.value |= other; return self
  def __ixor__(self, other):      self.value ^= other; return self

  def __pos__(self):
    match self.ast:
      case ast.Call(func=ast.Name(_value=s), args=args):
        s.add(tuple(asteval(arg) for arg in args))
