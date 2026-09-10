# PyGForce

Force-directed graph visualisation in Python using
[NetworkX](https://networkx.org/) and GTK 3 (PyGObject).

David Barkhuizen

## What it does

`demo_pygforce.py` opens a GTK window showing a small semi-random graph
(`DEMO_GRAPH_SIZE` = 11 nodes, generated with NetworkX) and runs a force-directed
layout simulation — nodes repel, edges act as springs — stepped on a GLib timer
tick and drawn with cairo. Each step updates every node's velocity as
`v = v * FRICTION + force * TIME_STEP` and then moves it by `v`, so an
undisturbed layout settles rather than drifting. The tunable constants
(`SPRING_CONSTANT`, `EQUILIBRIUM_DISPLACEMENT`, `FRICTION`, `TIME_STEP`, ...)
live in `constants.py`.

While it runs:

- **Left-click** within `MINIMUM_NODE_SELECTION_RADIUS` of a node toggles its
  selection; the selected node and its adjacent edges are drawn in blue.
- **Drag** a node with the mouse to reposition it (its velocity is held at zero
  while dragged).
- **Tab** — in fact any key — toggles the node labels on and off.
- Every `GENERATION_INTERVAL` seconds (5 s) the demo adds or removes a random
  node and its edges, keeping the node count between `DEMO_GRAPH_SIZE // 2` and
  `DEMO_GRAPH_SIZE * 2`.

## Requirements

- Python 3
- GTK 3 with GObject Introspection (PyGObject) and pycairo
- [NetworkX](https://networkx.org/) — 2.x or 3.x

On Debian/Ubuntu the runtime pieces are easiest from apt:

```
sudo apt install python3-gi gir1.2-gtk-3.0 python3-gi-cairo
pip install -r requirements.txt   # networkx
```

`pip install pygobject pycairo` also works if the GTK 3 / cairo development
headers are present.

## Running

```
python3 demo_pygforce.py
```

It needs an X11 or Wayland display; on a headless machine wrap it with
`xvfb-run`.

## Layout

| File | Role |
| --- | --- |
| `demo_pygforce.py` | Entry point — builds the demo graph and starts the GTK loop |
| `force_directed_graph.py` | Layout maths, coordinate transforms, `step()` (physics) and `render(cr)` (cairo drawing) |
| `graphical_event_manager.py` | GTK 3 window and drawing area, mouse/keyboard handlers, timer tick |
| `graph_manipulator.py` | Random graph generation and add/remove-node helpers |
| `node_tag.py` | Per-node data — index, position, label, per-step force/velocity/displacement, selection state |
| `points.py` | 2D point helper |
| `constants.py` | Window size, physics constants, demo parameters |

## Status

### Implemented

- Generate a semi-random test graph
- Per-node physics each step — net force, velocity update, displacement
- Draw the graph
- Event-based time simulation, periodically adding / removing a random node
  (with its edges) while keeping the node count within bounds
- Select a node with the mouse — single node, left-click to toggle; the selected
  node and its adjacent edges are drawn in the selection colour
- Drag the selected node — its position follows the pointer
- Toggle node labels — press Tab (any key)

### Backlog

- **Selected-node info** — show the selected node's full tag info, degree and
  neighbours (console first, later a panel / widgets)
- **Multiple selection**
- **Adding edges** — select two nodes, add an edge
- **Centre the graph** — compute and use the centre of mass
