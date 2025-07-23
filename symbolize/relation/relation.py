"""
relation.py
Defines the Relation class for logical relations, allowing set-like operations on tuples.
"""
import ast
import html
from symbolize.core.node import Node


class IdNode(Node):
  """Node representing an individual identifier."""

  def diagram(self):
    from .diagram import id as id_diagram
    match self.ast:
      case ast.Name(id=name):
        return id_diagram(name)
      case _:
        return id_diagram(repr(self))

  def _repr_svg_(self):
    return self.diagram().render().pipe(format='svg').decode('utf-8')

def tuplify(x):
  """Convert input to a tuple if it is not already."""
  return x if isinstance(x, tuple) else (x,)

class Relation(set):
  """Relation class for logical relations."""

  def __init__(self, s=None, arity=None):
    if not s:
      s = set()
    else:
      s = {tuplify(e) for e in s}
    super().__init__(s)
    self.arity = arity
    if self.arity is None and s:
      self.arity = len(next(iter(s)))

  def add(self, element):
    element = tuplify(element)
    if self.arity is None:
      self.arity = len(element)
    elif len(element) != self.arity:
      raise ValueError("Arity mismatch")
    super().add(element)

  def __call__(self, *args):
    n = len(args)
    result = { t[n:] for t in self if t[:n] == args}
    ar = None
    if self.arity is not None:
      ar = max(self.arity - n, 0)
    return Relation(result, ar)

  def __invert__(self):
    return next(iter(self))[0]

  def __and__(self, other):
    return Relation(set(self) & set(other),
                    self.arity if self.arity == getattr(other, 'arity', None) else self.arity)

  def __or__(self, other):
    return Relation(set(self) | set(other),
                    self.arity if self.arity == getattr(other, 'arity', None) else self.arity)

  def __iadd__(self, other):  self.add(tuplify(other)); return self
  def __isub__(self, other):  self.remove(tuplify(other)); return self

  def __repr__(self):
    if self == set(): return '{} / False'
    if self == {()}:  return '{()} / True'
    return repr({e[0] if len(e) == 1 else e for e in self})

class RelationNode(Node):
  """Node class for Relation, allowing set-like operations on tuples."""

  def __init__(self, name, relation=None):
    super().__init__(name, relation)
    if isinstance(self.ast, ast.Name) and self.value is None:
      self.value = Relation()

  def label(self):
    label = super().label()
    if '{}' in label:
      label = html.escape(label)
      label = f'<<FONT COLOR="red">{label}</FONT>>'
    elif '{()}' in label:
      label = html.escape(label)
      label = f'<<FONT COLOR="green">{label}</FONT>>'
    return label

  def _repr_svg_(self):
    return self.diagram().render().pipe(format='svg').decode('utf-8')
  
  def diagram(self):
    """Convert to a DOT representation for graph visualization."""

    from .diagram import app, op, pred

    match(self.ast):
      case ast.Name(id=name):
        rel = self.value if isinstance(self.value, Relation) else None
        ar = rel.arity if rel else 0
        ext = repr(rel) if rel and len(rel) > 0 else None
        return pred(name, arity=ar or 0, ext=ext)
      case ast.Call(func=func, args=args):
        return app(RelationNode(func).diagram(),
                   *[IdNode(arg.id).diagram() for arg in args])
      case ast.BinOp(left=left, op=oper, right=right):
        match oper:
          case ast.BitAnd():
            oper = '&'
          case ast.BitOr():
            oper = '|'
          case ast.Add():
            oper = '+'
          case ast.Sub():
            oper = '-'
          case ast.Mult():
            oper = '*'
          case ast.Div():
            oper = '/'
          case _:
            raise ValueError(f'Unsupported operator: {oper}')
        return op(oper, RelationNode(left).diagram(), RelationNode(right).diagram())
      case _:
        return f'{self.name} [label="{self.label()}", shape=box, style=filled, fillcolor=lightgray];'


def detectors(s): 
  """Convert a string of space-separated symbols into a generator of Node Relations."""
  return (RelationNode(s, Relation()) for s in s.split())

def ids(s):
  """Convert a string of symbols characters into a generator of Nodes."""
  return (IdNode(c, c) for c in s)

