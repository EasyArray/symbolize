"""Module for generating diagrams of relations using Graphviz."""

import itertools
import html
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from graphviz import Source

# ---------- constants -------------------------------------------------
class Colors:
  """Color constants for the diagram."""
  LEAF_BG = "#D6EAF8"
  ID_BG = "#E9EEF6"
  ID_TEXT = "#4C6A88"
  APP_BADGE_BG = "#D1F2EB"
  BADGE_BG = "#EBDEF0"
  EXT_BG = "#FFF2CC"
  NODE_BG = "#E9EEF6"
  NODE_BORDER = "#4C6A88"
  EDGE = "#17202A"
  SUBTLE_EDGE = "#D3D3D3"
  LAM_BG = "#FDEDEC"
  LAM_BORDER = "#A93226"

# ---------- id factory ------------------------------------------------
_id_counter = itertools.count()

def _new_id(prefix: str = "n") -> str:
  return f"{prefix}{next(_id_counter)}"

# ---------- HTML badge helpers ---------------------------------------
def _badge(sym: str, val: Optional[str], fill=Colors.BADGE_BG) -> str:
  inner_val = f'<TR><TD BGCOLOR="{Colors.EXT_BG}">{html.escape(val)}</TD></TR>' if val else ""
  return (
      f'<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
      f'<TR><TD BGCOLOR="{fill}"><B>{html.escape(sym)}</B></TD></TR>{inner_val}</TABLE>')

def _leaf_badge(name: str, ext: Optional[str]) -> str:
  ext_row = f'<TR><TD BGCOLOR="{Colors.EXT_BG}">{html.escape(ext)}</TD></TR>' if ext else ""
  return (
      '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
      f'<TR><TD BGCOLOR="{Colors.LEAF_BG}"><B>{html.escape(name)}</B></TD></TR>{ext_row}</TABLE>')

# ---------- core dataclass -------------------------------------------
@dataclass
class Diagram:
  """Class to generate a Graphviz diagram for a relation."""
  dot: str
  root: str
  left_anchor: str
  expr: str
  arg_ports: List[str] = field(default_factory=list)
  children: List['Diagram'] = field(default_factory=list)
  cluster_id: Optional[str] = None
  free_vars: Dict[str, List[str]] = field(default_factory=dict)

  def full_dot(self, name: str = "G"):
    """Generate the full Graphviz DOT representation of the diagram."""
    return f"""
digraph {name} {{
  rankdir=TB
  graph [margin=0.2, ranksep=0.6, nodesep=0.1]
  node  [fontname="Helvetica", fontsize=10]
  edge  [fontname="Helvetica", arrowsize=0.7, color="#17202A"]
  {self.dot}
}}
"""

  def render(self, name: str = "G"):
    """Render the diagram as a Graphviz Source object."""
    return Source(self.full_dot(name))
  
  @property
  def arity(self) -> int:
    """Return the arity of the diagram."""
    return len(self.arg_ports)


def _add_ports(n, root):
  dot = ''
  ports = []
  weight = 5 * n
  last = root
  for _ in range(n):
    port = _new_id('port')
    ports.append(port)
    dot += f'{port} [shape=point];\n'
    dot += f'{last} -> {port} [arrowhead=none, style=invis, weight=2];\n'
    last = port
    weight -= 5
  dot += '{ rank=same; ' + f'{root} ' + ' '.join(ports) + ' }\n'
  return dot, ports


# ---------- leaves ----------------------------------------------------
def id(name: str) -> Diagram:
  """Create a diagram for an identifier. """
  n = _new_id()
  dot = (
    f'{n} [label="{html.escape(name)}", shape=box, style="rounded,filled", '
          f'fillcolor="{Colors.ID_BG}", color="{Colors.ID_TEXT}"]\n'
  )
  return Diagram(dot, n, n, name, [], [], None, {})

def var(name: str) -> Diagram:
  """Create a diagram for a variable."""
  n = _new_id()
  label = f'<<I>{html.escape(name)}</I>>'
  dot = (
      f'{n} [label={label}, shape=box, style="rounded,filled,dashed", '
      f'fillcolor="#FFFFFF", color="{Colors.ID_TEXT}"]\n'
  )
  return Diagram(dot, n, n, name, [], [], None, {name: [n]})

def pred(name: str, arity: int = 1, ext: Optional[str] = None) -> Diagram:
  """Create a diagram for a predicate with the given name and arity."""
  n = _new_id()
  dot = f'{n} [shape=plain, label=<{_leaf_badge(name, ext)}>]\n'

  dot_ports, ports = _add_ports(arity, n)
  dot += dot_ports

  cid = _new_id('cluster')
  return Diagram(
    f'subgraph {cid} {{ label=""; style="solid,rounded"; margin=10;\n {dot} }}\n',
    n, n, name, ports, [], cid, {}
  )

# ── operators ────────────────────────────────────────────────────────
def op(sym, *kids, value=None):
  """Create a diagram for an operator with the given symbol and children."""
  if not kids:
    raise ValueError

  arity = kids[0].arity
  if any(kid.arity != arity for kid in kids):
    raise ValueError

  expr= (f"{sym}({kids[0].expr})"
          if len(kids)==1
          else '(' + f" {sym} ".join(k.expr for k in kids) + ')'
        )
  b = _new_id()
  body = (
      f'{b} [shape=plain, label=<{_badge(sym,value)}>];\n'
      + "".join(k.dot for k in kids)
  )

  for i, k in enumerate(kids):
    weight = 1 if i==0 else 0
    constraint = True
    body += f'{b} -> {k.root} [weight={weight}, constraint={constraint}];\n'


  dot_ports, ports = _add_ports(arity, b)
  body += dot_ports

  for kid in kids:
    for port, kid_port in zip(ports, kid.arg_ports):
      body += f'{port} -> {kid_port} [weight=0, dir=none, style=dashed, color="{Colors.SUBTLE_EDGE}"];\n'

  cid = _new_id('cluster')
  free: Dict[str, List[str]] = {}
  for k in kids:
    for name, nodes in k.free_vars.items():
      free.setdefault(name, []).extend(nodes)

  return Diagram(
    f'subgraph {cid} {{ label="{html.escape(expr)}"; style=dotted; margin=10;\n{body}}}\n',
    b, kids[0].left_anchor, expr, ports, list(kids), cid, free
  )

# ---------- application  ----------------------
def app(func: Diagram, *args: List[Diagram], value: Optional[str] = None) -> Diagram:
  """Create a diagram for an application of a function to arguments."""
  arg_exprs = ", ".join(a.expr for a in args)
  expr = f"({func.expr})({arg_exprs})"
  badge = _new_id()

  # base body: () badge + function subtree + args subtrees
  body = (
      f'{badge} [shape=plain, label=<{_badge("()", value, Colors.APP_BADGE_BG)}>]\n' 
      + func.dot + "".join(a.dot for a in args)
  )

  for p, arg in zip(func.arg_ports, args):
    body += f'{p} -> {arg.root} [weight=1, style=dashed, arrowhead=empty];\n'

  body += f'{badge} -> {func.root} [style=invis, weight=5];\n'

#  for i, k in enumerate(args):
#    body += f'{badge} -> {k.root} [style=invis, arrowhead=none, weight=0, constraint=false];\n'

  cid = _new_id('cluster_app')
  cluster = f'subgraph {cid} {{ label="{html.escape(expr)}"; style=dotted; margin=10;\n{body}}}\n'
  free: Dict[str, List[str]] = {}
  for part in (func, *args):
    for name, nodes in part.free_vars.items():
      free.setdefault(name, []).extend(nodes)

  return Diagram(cluster, badge, func.left_anchor, expr, [func], [], cid, free)


# ---------- lambda  ----------------------
def lam(var: str, body: Diagram, value: Optional[str] = None) -> Diagram:
  """Create a diagram for a lambda abstraction."""
  expr = f"λ{var}.{body.expr}"
  badge = _new_id()

  dot = (
      f'{badge} [label="λ{html.escape(var)}", shape=parallelogram, style="filled", '
      f'fillcolor="{Colors.LAM_BG}", color="{Colors.LAM_BORDER}", fontname="monospace"]\n'
      + body.dot
  )

  dot += f'{badge} -> {body.root} [weight=1, constraint=true];\n'

  dot_ports, ports = _add_ports(1, badge)
  dot += dot_ports

  for target in body.free_vars.get(var, []):
    dot += (
        f'{ports[0]} -> {target} [style=dotted, color="{Colors.LAM_BORDER}", '
        f'arrowhead=onormal, penwidth=0.8];\n'
    )

  cid = _new_id('cluster_lam')
  cluster = (
      f'subgraph {cid} {{ label="{html.escape(expr)}"; style=dashed; color="{Colors.LAM_BORDER}"; margin=10;\n{dot}}}\n'
  )
  free = {k: list(v) for k, v in body.free_vars.items() if k != var}
  return Diagram(cluster, badge, body.left_anchor, expr, ports, [body], cid, free)



#Tests
if __name__ == "__main__":
  leaf1 = pred("over", 2, "ext1")
  leaf2 = pred("under", 2, "ext1")

  id1, id2 = id("A"), id("B")

  conj = op("&", leaf1, leaf2, value="True")

  dia = app(conj, id1, id2, value="True")

  print(dia.full_dot())
  dia.render().render(filename='diagram', format='png', cleanup=True)



