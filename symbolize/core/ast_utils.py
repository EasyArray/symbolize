"""
ast_utils.py
Provides functionality to manipulate and evaluate Python AST nodes.
---------
toast(s)
  Converts various types of input into an AST node.
build_env(node, env=None)
  Builds an environment dictionary from AST nodes.
evast(node, env=None)
  Evaluates an AST node in a given environment.
unparse(node, env={})
  Converts an AST node back to source code.
print_env(env)
  Prints the environment dictionary with AST nodes.
"""

import ast
from itertools import count

def toast(s, _counter=count()):
  """Convert various types of input into an AST node."""
  match s:
    case ast.AST():         return s
    case object(ast=node):  return node
    case str():             return ast.parse(s, mode='eval').body
    case int():             return ast.Constant(value=s)
    case _:                 #return ast.parse(repr(s), mode='eval').body
      return ast.Name(id=f'_{next(_counter)}', ctx=ast.Load(), _value=s)


def build_env(node, env=None):
  """Build an environment dictionary from _value attributes of AST Names."""
  if env is None:
    env = {}
  for n in ast.walk(node):
    match n:
      case ast.Name(id=name, _value=value):
        env[name] = value
  return env


# There is interesting (ha!) behavior when evaluating a
# Node storing a Lambda. Even if ast for a Name inside the Lambda
# has a _value, that value is not used (locals are ignored when eval'ing
# lambdas apparently); any global value for that Name *is* used, though
def asteval(node, env=None):
  """Evaluate (something convertible to) an AST node in a given environment."""
  if env is None:
    env = {}
  # Toast node
  node = toast(node)
  if not isinstance(node, ast.Expression):
    node = ast.Expression(body=node)
  ast.fix_missing_locations(node)

  # Grab values from ast nodes in node
  build_env(node, env)

  # Eval
  code = compile(node, filename='', mode='eval')
  return eval(code, None, env)

def unparse(node):
  """Convert (something convertible to) an AST node back to source code."""
  return ast.unparse(toast(node))

def print_env(env):
  """Print the environment dictionary with AST nodes."""
  print([(k, v, type(v)) for k,v in env.items()])