"""
relation.py
Defines the Relation class for logical relations, allowing set-like operations on tuples.
"""
from symbolize.core.node import Node

def tuplify(x):
  """Convert input to a tuple if it is not already."""
  return x if isinstance(x, tuple) else (x,)

def detectors(s): 
  """Convert a string of space-separated symbols into a generator of Node Relations."""
  return (Node(s, Relation()) for s in s.split())

def ids(s):
  """Convert a string of symbols into a list of characters."""
  return list(s)


class Relation(set):
  """Relation class for logical relations. """

  def __init__(self, s=None):
    if not s:
      s = set()
    else:
      s = {tuplify(e) for e in s}
    super().__init__(s)

  def __call__(self, *args):
    n = len(args)
    return Relation({ t[n:] for t in self if t[:n] == args})

  def __invert__(self):
    return next(iter(self))[0]

  def __and__(self, other): return Relation(set(self) & set(other))
  def __or__(self, other):  return Relation(set(self) | set(other))

  def __iadd__(self, other):  self.add(tuplify(other)); return self
  def __isub__(self, other):  self.remove(tuplify(other)); return self

  def __repr__(self):
    if self == set(): return '{} / False'
    if self == {()}:  return '{()} / True'
    return repr({e[0] if len(e) == 1 else e for e in self})
