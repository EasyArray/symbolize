"""
lambda_utils.py
Provides functionality to create and manipulate Python lambda functions as AST nodes.
"""

import ast
from inspect import signature, getclosurevars
from .ast_utils import toast
from .node import Node

def star_union(it):
  """Return the union of sets from an iterable of sets."""
  return set().union(*it)

def free_vars(node):
  """Return the set of free variables in an AST node."""
  node = toast(node)
  match node:
    case ast.Name(id=name, ctx=ast.Load()):
      return {name}
    case ast.Lambda(args=args, body=body):
      return free_vars(body) - {a.arg for a in args.args}
    case _:
      return star_union(free_vars(c) for c in ast.iter_child_nodes(node))

def fresh(base, taken):
  """Generate a fresh variable name based on a base name, avoiding names in taken."""
  i = 0
  candidate = base
  base = base.rstrip('0123456789')
  while candidate in taken:
    i += 1
    candidate = f"{base}{i}"
  return candidate

def make_lambda(lamb):
  """Convert a lambda function to an AST Lambda node."""
  args = list(signature(lamb).parameters.keys())
  nonlocals, globs, _, _ = getclosurevars(lamb)
  free_in_closure = star_union(free_vars(v) for v in nonlocals.values())
  taken = free_in_closure | set(globs.keys()) | set(args)
  for i, arg in enumerate(args):
    if arg in free_in_closure:
      args[i] = fresh(arg, taken)

  inputs = [Node(arg) for arg in args]
  for x in inputs: x.value = x
  body = Node(lamb(*inputs))
  return ast.Lambda(
      args=ast.arguments(posonlyargs=[],
                         args=[ast.arg(arg=arg) for arg in args],
                         kwonlyargs=[], kw_defaults=[], defaults=[]),
      body=body.ast
  )