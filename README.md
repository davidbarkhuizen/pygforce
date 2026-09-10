# PyGForce

Force-directed graph visualisation in Python using
[NetworkX](https://networkx.org/) and GTK 3 (PyGObject).

David Barkhuizen — david.barkhuizen@gmail.com

## What it does

`demo_pygforce.py` opens a GTK window showing a small semi-random graph
(`DEMO_GRAPH_SIZE` nodes, generated with NetworkX) and runs a force-directed
layout simulation — nodes repel, edges act as springs (`SPRING_CONSTANT`,
`EQUILIBRIUM_DISPLACEMENT`, `FRICTION`, `TIME_STEP` in `constants.py`), stepped
on a GLib timer tick and drawn with cairo.

While it runs:

- **Left-click** near a node toggles its selection; the selected node and its
  adjacent edges are highlighted.
- **Drag** a node with the mouse to reposition it.
- **Tab** (in fact any key) toggles the node labels on and off.
- Every few seconds (`GENERATION_INTERVAL`) the demo adds or removes a random
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

## Layout

| File | Role |
| --- | --- |
| `demo_pygforce.py` | Entry point — builds the demo graph and starts the GTK loop |
| `force_directed_graph.py` | Layout maths, coordinate transforms, `step()` (physics) and `render(cr)` (cairo drawing) |
| `graphical_event_manager.py` | GTK 3 window and drawing area, mouse/keyboard handlers, timer tick |
| `graph_manipulator.py` | Random graph generation and add/remove-node helpers |
| `node_tag.py` | Per-node data (index, position, label, selection state) |
| `points.py` | 2D point helper |
| `constants.py` | Window size, physics constants, demo parameters |
