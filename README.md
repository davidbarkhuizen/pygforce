# PyGForce

Force-directed graph visualisation in Python using [NetworkX](https://networkx.org/)
and PyGTK.

David Barkhuizen — david.barkhuizen@gmail.com

## What it does

`demo_pygforce.py` opens a GTK window showing a small semi-random graph
(`DEMO_GRAPH_SIZE` nodes, generated with NetworkX) and runs a force-directed
layout simulation — nodes repel, edges act as springs (`SPRING_CONSTANT`,
`EQUILIBRIUM_DISPLACEMENT`, `FRICTION`, `TIME_STEP` in `constants.py`), stepped
on a GTK timer tick.

While it runs:

- **Left-click** near a node toggles its selection; the selected node and its
  adjacent edges are highlighted.
- **Drag** a node with the mouse to reposition it.
- **Tab** (in fact any key) toggles the node labels on and off.
- Every few seconds (`GENERATION_INTERVAL`) the demo adds or removes a random
  node and its edges, keeping the node count between `DEMO_GRAPH_SIZE / 2` and
  `DEMO_GRAPH_SIZE * 2`.

## Requirements

This is a **Python 2** program built on **PyGTK (GTK 2)**. PyGTK was never ported
to Python 3 and is no longer maintained, so there is no Python 3 path.

- Python 2.7
- PyGTK 2 — provides the `gtk` and `gobject` modules — plus the native GTK+ 2
  runtime libraries it binds to
- [NetworkX](https://networkx.org/)

On a Debian/Ubuntu system with Python 2 still available:

```
sudo apt install python-gtk2 python-gobject-2
pip2 install networkx
```

## Running

```
python2 demo_pygforce.py
```

## Layout

| File | Role |
| --- | --- |
| `demo_pygforce.py` | Entry point — builds the demo graph and starts the GTK loop |
| `force_directed_graph.py` | Force-directed layout maths and coordinate transforms |
| `graphical_event_manager.py` | GTK window, drawing, and mouse/keyboard/timer handlers |
| `graph_manipulator.py` | Random graph generation and add/remove-node helpers |
| `node_tag.py` | Per-node data (index, position, label, selection state) |
| `points.py` | 2D point helper |
| `constants.py` | Window size, physics constants, demo parameters |
