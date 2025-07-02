"""
tree.py
Provides functionality to visualize tree structures using Graphviz.
---------
draw_tree(tree)
  Generates a Graphviz Digraph from a nested iterable tree structure.
"""

from itertools import count
from graphviz import Digraph

def draw_tree(tree):
  """
  Args
  ----
  tree : iterable
      A nested iterable where
        • tree[0] is the node label
        • tree[1:], if present, are sub-iterables (the children)
          - a child may itself be a bare string → leaf
    
  Returns
  -------
  graphviz.Digraph
      A DOT graph with:
        • plaintext labels
        • straight branches
        • every parent-to-children set originating at one point
  """
  dot = Digraph(
    engine='dot',
    graph_attr={'rankdir':'TB', 'splines':'false'},
    node_attr={'shape':'plaintext', 'fontsize':'12'},
    edge_attr={'arrowhead':'none'}
  )

  uid = count()               # unique node IDs

  def rec(subtree, parent_id=None):
    match subtree:
      case [label, *kids]:    # non-leaf iterable
        node_id = f"n{next(uid)}"
        dot.node(node_id, str(label))
        if parent_id is not None:
          dot.edge(f'{parent_id}:s', f'{node_id}:n')

        for kid in kids:
          # A kid is a subtree iff it's a tuple or list
          is_subtree = isinstance(kid, (tuple,list))
          rec(kid if is_subtree else (kid,), node_id)

      case [leaf]:           # singleton tuple → actual leaf
        leaf_id = f"n{next(uid)}"
        dot.node(leaf_id, str(leaf))
        dot.edge(f'{parent_id}:s', f'{leaf_id}:n')

      case _:                 # safety net
        raise TypeError("Each subtree must be an iterable with at least one element")

  rec(tree)                   # kick off the recursion
  return dot
