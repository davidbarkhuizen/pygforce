# Force-Directed Graph Physics in PyGForce

A detailed reference for the layout simulation implemented in
[`force_directed_graph.py`](force_directed_graph.py), with the tunable values in
[`constants.py`](constants.py).

Line numbers refer to commit `5341c83`. Where the code and the intuitive reading
of a name disagree, that is called out explicitly.

---

## 1. Summary

PyGForce lays out a NetworkX graph by treating it as a small physical system:

- every **node** is a positively charged particle that repels every other node
  (all-pairs, Coulomb-like repulsion);
- every **edge** is a **spring** with a fixed natural length (Hooke's law);
- the two forces are summed, and the result is integrated as acceleration using
  **damped, semi-implicit Euler** at a fixed step size;
- the fixed step runs once per GLib timer tick (every 50 ms) and the canvas is
  repainted.

There is no energy minimisation, no cooling schedule, no gravity and no
boundary. The layout is a damped relaxation: it is not derived from an energy
functional, and it is not a physical simulation in any strict sense — the
constants are dimensionless tuning knobs that happen to be shaped like physics.

The entire model is three lines of arithmetic:

```
F_net = F_electrostatic + F_spring
v_new = v * FRICTION + F_net * TIME_STEP
x_new = x + v_new
```

---

## 2. Coordinate spaces

Two coordinate systems are in play, and mixing them up is the easiest way to get
confused when reading the code.

| Space | Extent | Constants | Origin | Used for |
| --- | --- | --- | --- | --- |
| Phase space (model) | 600 × 600 | `W_0`, `H_0` | centre | forces and integration |
| Canvas (screen) | 700 × 700 | `W_1`, `H_1` | top-left | cairo drawing |

Model coordinates therefore run roughly `[-300, +300]` on each axis. All physics
happens in model coordinates; canvas coordinates are produced only at the end of
each step, for drawing.

### `translate()` — model → canvas (`force_directed_graph.py:19`)

```python
x1 = (w1 / 2) + x0 * (w1 / w0)
y1 = (h1 / 2) - y0 * (h1 / h0)
```

Two things to note:

- the scale factor is uniform, `W_1 / W_0 = 700 / 600 ≈ 1.1667`;
- the **y axis is flipped** (`h1/2 - y0·…`), so increasing model `y` moves *up*
  the canvas, matching the usual mathematical convention while cairo's y grows
  downward.

### `reverse()` — canvas → model (`force_directed_graph.py:26`)

The exact algebraic inverse, used to convert mouse events back into model
coordinates for selection (`handle_node_select_attempt`) and dragging
(`motion_notify_event`).

### Initial positions

Nodes are seeded uniformly at random in the model square — `construct_xy_factory()`
guarantees unique coordinates across the initial graph, and `calc_xy_for_new_node()`
rejects coordinates that exactly duplicate an existing node. The starting layout
is therefore random, not derived from any graph-theoretic placement.

### No boundary handling

Integration never clamps a node to the model square, and the transform above is
affine and unbounded. A node pushed outward simply leaves the canvas and is not
pulled back, because nothing in the force model is centripetal (see §9).

---

## 3. Per-node state

Each node is a `Tag` (`node_tag.py`) carrying both the physical state and a
redundant cache of the last computed forces:

| Field | Meaning |
| --- | --- |
| `position` | model-space position (`Point2D`) |
| `translated_position` | canvas-space position, refreshed each step |
| `net_electrostatic_force` | cached `(Fx, Fy)` sum from other nodes |
| `net_spring_force` | cached `(Fx, Fy)` sum from incident edges |
| `velocity` | the damped, time-step-scaled per-step displacement |
| `displacement` | this step's position delta |
| `is_selected` | selection flag; also gates dragging |
| `idx`, `label` | identity and display text |

### Two naming traps

1. **`velocity` is not a velocity in any physical unit.** `TIME_STEP` is already
   folded in by `velocity_at_tag()`, so the value is a *displacement per step*.
   `displacement_at_node()` merely returns it (`force_directed_graph.py:189`).
2. **`TIME_STEP` is not a time in seconds.** It is a dimensionless gain factor.
   Nothing in the simulation reads a clock: one timer tick is exactly one step,
   regardless of how much wall-clock time actually elapsed. A stalled UI does
   not cause the simulation to catch up, and a fast machine does not make it run
   faster than one step per tick.

Because the fields are set by `step()` and read by `net_force_at_node()`, a
freshly constructed `Tag` has zeroed force caches — the first `step()` is what
populates them.

---

## 4. The forces

### 4.1 Electrostatic repulsion — all pairs

`net_electrostatic_force_at_node()` (`force_directed_graph.py:87-127`) sums a
Coulomb-like repulsion over **every other node in the graph**, whether or not the
two are connected:

```python
for tag_B in self.graph.nodes():
    if tag_B == tag_A:
        continue

    delta_x = tag_A.position.x - tag_B.position.x      # points B -> A
    delta_y = tag_A.position.y - tag_B.position.y

    r2 = delta_x**2 + delta_y**2
    r  = sqrt(r2)

    if r == 0.0:
        continue

    cos_theta = delta_x / r
    sin_theta = delta_y / r

    q_A = 10.0
    q_B = 10.0
    k   = 100.0

    scalar_force = k * q_A * q_B / r**1.9

    Fx = scalar_force * cos_theta
    Fy = scalar_force * sin_theta
```

In vector form, with `d = pos_A − pos_B`:

```
F = (10000 / r^1.9) · (d / r)        r = |d|
```

so the magnitude is

```
|F_repel| = 10000 / r^1.9
```

directed **away** from `B` (since `d` points from `B` to `A`). Three details
matter:

- **The exponent is 1.9, not 2.** Coulomb's law would be `1/r²`; this is very
  slightly softer. Because the magnitude is then multiplied by the unit vector
  `d/r`, each *Cartesian component* actually falls off as `r^-2.9`.
- **The constants are hardcoded** (`k = 100.0`, `q = 10.0`) in the body of the
  loop rather than living in `constants.py`, so they are easy to miss when
  tuning. They are also re-created on every inner-loop iteration — harmless, but
  the loop is `O(N²)` and this is the hot path.
- **`r == 0` is guarded, but only exactly.** The force magnitude diverges as
  `r → 0`, and there is no velocity clamp anywhere, so a near-coincident pair can
  produce a very large impulse. Random seeding makes exact coincidence unlikely,
  but nothing prevents nodes drifting close during the simulation.

### 4.2 Spring attraction along edges

`net_spring_force_at_node()` (`force_directed_graph.py:129-175`) walks the graph's
**edge list** and accumulates a Hooke's-law force for each edge incident to the
node:

```python
scalar_force = k * (r - l)            # k = SPRING_CONSTANT, l = EQUILIBRIUM_DISPLACEMENT

cos_theta = (x_other - x_tag) / r     # unit vector tag -> other
sin_theta = (y_other - y_tag) / r

Fx = scalar_force * cos_theta
Fy = scalar_force * sin_theta
```

with `SPRING_CONSTANT = 0.1` and `EQUILIBRIUM_DISPLACEMENT = 30`.

The sign convention is the natural one and the code comments say so explicitly:

| Separation | `k(r − l)` | Effect |
| --- | --- | --- |
| `r > l` (stretched) | positive | pulls the node **toward** its neighbour |
| `r = l` (rest) | zero | no force |
| `r < l` (compressed) | negative | pushes the node **away** from its neighbour |

Notable properties:

- **The rest length is the same 30 model units for every edge**, regardless of
  the graph's structure. This differs from Kamada–Kawai, where each pair has an
  ideal distance proportional to the graph-theoretic shortest path.
- **The force is not normalised by node degree.** A node with ten edges
  accumulates ten full spring forces, so high-degree nodes are pulled much
  harder than leaves. (Repulsion, by contrast, is naturally shared across all
  pairs.)
- The implementation scans **all edges for every node**, so the real cost is
  `O(N·E)` rather than the `O(E)` that accumulating edge contributions once
  would cost.

### 4.3 Net force

`net_force_at_node()` (`force_directed_graph.py:177-187`) is a plain vector sum of
the two cached contributions:

```
F_net = net_electrostatic_force + net_spring_force
```

Both caches are filled by the preceding passes of `step()`, so the sum is always
taken over one consistent snapshot of positions.

---

## 5. Integration: damped semi-implicit Euler

`velocity_at_tag()` (`force_directed_graph.py:197-216`) is the integrator:

```python
xn = (xo * FRICTION) + xf * TIME_STEP
yn = (yo * FRICTION) + yf * TIME_STEP
```

i.e.

```
v_new = v_old · FRICTION + F_net · TIME_STEP      FRICTION = 0.9, TIME_STEP = 0.1
x_new = x_old + v_new
```

Properties worth understanding:

- **The damping is a per-step velocity multiplier**, `FRICTION = 0.9`. It stands
  in for both physical drag and numerical damping, and it is what makes the
  relaxation converge instead of oscillating forever. It is not a force, does
  not depend on speed, and does not scale with `TIME_STEP`.
- **Velocity is updated before the position**, which makes this *semi-implicit*
  (symplectic) Euler rather than explicit Euler. That choice is what keeps the
  stiff spring regime stable at this step size.
- **There is no mass.** Force is treated directly as acceleration, so a node's
  inertia is fixed at 1 and cannot be tuned per node.
- **For a constant force the terminal per-step displacement is exactly `F`:**
  `v → F · TIME_STEP / (1 − FRICTION) = F · 0.1 / 0.1 = F`. This is why
  `constants.py` insists on keeping `TIME_STEP / (1 − FRICTION) ≈ 1`; the comment
  there is a real stability constraint, not a style note.
- **The relaxation timescale is `1 / (1 − FRICTION) = 10` steps**, i.e. about
  0.5 s at the 50 ms tick. Momentum from an old force decays with that time
  constant.
- **There is no cooling schedule and no speed limit.** Fruchterman–Reingold
  controls convergence with a temperature that shrinks each iteration; here the
  only mechanism is the constant `FRICTION`.

### Stability analysis

Linearising the update for a single restoring spring of effective stiffness
`k_eff` (with `a = TIME_STEP · k_eff`) gives the iteration matrix

```
[ v' ]   [ f    -a ] [ v ]
[ u' ] = [ f   1-a ] [ u ]        f = FRICTION,  u = r - l
```

Its determinant is exactly `f` **regardless of stiffness**, so in the
underdamped regime the per-step decay factor is

```
|λ| = √FRICTION = √0.9 ≈ 0.9487
```

independent of how stiff the springs are — stiffness changes the *frequency* of
the oscillation, not its decay rate. The system is underdamped for
`(1 + f − 2√f) < a < (1 + f + 2√f)`, i.e. `0.003 < a < 3.80` for `f = 0.9`, or
approximately `0.03 < k_eff < 38`; outside that band it is overdamped and decays
faster, without oscillating:

| Case | `k_eff` | Behaviour | Decay / step | Period |
| --- | --- | --- | --- | --- |
| one edge, one node free | 0.1 | underdamped | 0.9487 | ≈ 71 steps |
| one edge, both nodes free | 0.2 | underdamped | 0.9487 | ≈ 46 steps |
| ~3 collinear edges | 0.3 | underdamped | 0.9487 | ≈ 37 steps |
| ~10 collinear edges | 1.0 | underdamped | 0.9487 | ≈ 20 steps |
| ~400 collinear edges | 40.0 | overdamped | 0.6000 | — |

With `SPRING_CONSTANT = 0.1`, the demo's node degrees put the simulation firmly
in the underdamped, well-behaved column: oscillations decay by ~5% per step and
vanish within a second or so.

---

## 6. The per-step pipeline (`step()`, `force_directed_graph.py:218-260`)

Each tick performs six ordered passes:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. for all nodes: cache net_electrostatic_force    O(N²)     │
│ 2. for all nodes: cache net_spring_force           O(N·E)    │
│ 3. for all nodes: velocity = f(v, F_net)                     │
│ 4. for all nodes: displacement = velocity                    │
│ 5. for all nodes: position += displacement                   │
│      (except a selected node being dragged: pinned, v = 0)   │
│ 6. for all nodes: translated_position = translate(position)  │
└─────────────────────────────────────────────────────────────┘
```

The structure is deliberate and worth preserving:

- **Passes 1 and 2 complete before any velocity is updated**, and pass 5 runs
  only after every node's velocity is known. This is a **Jacobi-style
  synchronous update**: every node sees the same frozen snapshot of positions.
  The result is independent of node iteration order, unlike a Gauss–Seidel
  update that would use partially updated positions. The trade-off is slightly
  slower convergence and more tendency to oscillate, which the damping absorbs.
- **The force caches exist so that pass 1 need not be recomputed inside pass 2**
  and so that `velocity_at_tag()` can be a pure function of cached state.
- **Rendering is entirely separate.** `step()` does not draw; it only advances
  state and refreshes the canvas-space cache. `render(cr, …)` reads
  `translated_position` and draws. This split is why the simulation can be
  stepped headlessly.
- Pass 6 is part of `step()` rather than `render()`, so the model→canvas
  transform is recomputed on every step even when nothing is drawn.

---

## 7. Coupling to user interaction

Two interaction paths touch the physics.

**Dragging a node.** `motion_notify_event` (`graphical_event_manager.py:109`)
reverse-maps the pointer position and writes it directly into the selected node's
`position`. Then, in pass 5 of `step()`
(`force_directed_graph.py:246-255`):

```python
if tag.is_selected and self.gem.b1_down:
    tag.velocity = (0.0, 0.0)
else:
    (dx, dy) = tag.displacement
    tag.position.x += dx
    tag.position.y += dy
```

The node is pinned — its integrated position is discarded — and its velocity is
**zeroed every step**, so releasing the mouse does not fling it with the momentum
it accumulated while being pushed around. It still exerts repulsion and spring
forces on its neighbours during the drag, so the rest of the graph reacts to it.

Note the sequence: passes 1–4 still compute a force and velocity for the dragged
node; the pin happens afterwards. The cost is negligible, but it means the
dragged node's cached `velocity` is zero only as of the end of the step.

**Selection.** Selection is otherwise purely visual (colour in `render()`) and has
no effect on forces; it acts as a physics switch only through the drag gate
above.

---

## 8. Constants

From `constants.py`, plus the two hardcoded values.

| Constant | Value | Where | Meaning |
| --- | --- | --- | --- |
| `W_0`, `H_0` | 600 | `constants.py:4` | phase-space extent (model units) |
| `SPRING_CONSTANT` | 0.1 | `constants.py:8` | Hooke's `k` for every edge |
| `EQUILIBRIUM_DISPLACEMENT` | 30 | `constants.py:9` | spring rest length `l` |
| `TIME_STEP` | 0.1 | `constants.py:13` | integration gain (not seconds) |
| `FRICTION` | 0.9 | `constants.py:14` | per-step velocity retention |
| `W_1`, `H_1` | 700 | `constants.py:17` | canvas extent (pixels) |
| `TIMER_TICK_PERIOD` | 50 ms | `constants.py:24` | one simulation step per tick |
| `MINIMUM_NODE_SELECTION_RADIUS` | 15.0 | `constants.py:27` | click hit radius (model units) |
| `DEMO_GRAPH_SIZE` | 11 | `constants.py:29` | initial demo node count |
| `DEMO_GRAPH_BRANCHING_CONST` | 2 | `constants.py:30` | max new edges per node when generating |
| `GENERATION_INTERVAL` | 5.0 s | `constants.py:31` | graph mutation period |
| charge `q` | 10.0 | `force_directed_graph.py:115` | hardcoded |
| Coulomb `k` | 100.0 | `force_directed_graph.py:117` | hardcoded |
| repulsion exponent | 1.9 | `force_directed_graph.py:119` | hardcoded |

The derived scale factor is `W_1 / W_0 ≈ 1.1667` and the derived force gain is
`TIME_STEP / (1 − FRICTION) = 1`.

---

## 9. Force scales and equilibrium

With `F_repel(r) = 10000 / r^1.9` acting outward and the spring force
`F_spring(r) = 0.1(r − 30)` acting inward when stretched, the net radial force
(positive = pushing apart) for a pair joined by a single edge is
`F_repel(r) − F_spring(r)`:

| `r` (model units) | repulsion | spring | net (apart +) | tendency |
| --- | --- | --- | --- | --- |
| 10 | 125.89 | −2.00 | +127.89 | strongly apart |
| 15 | 58.27 | −1.50 | +59.77 | strongly apart |
| 30 | 15.61 | 0.00 | +15.61 | apart (rest length ≠ equilibrium) |
| 50 | 5.92 | 2.00 | +3.92 | apart |
| **65.46** | **3.55** | **3.55** | **0.00** | **equilibrium** |
| 100 | 1.58 | 7.00 | −5.42 | together |
| 200 | 0.42 | 17.00 | −16.58 | together |
| 300 | 0.20 | 27.00 | −26.80 | together |

Two conclusions fall out of this table, and they explain most of the layout's
observable behaviour:

1. **The spring rest length is not the equilibrium distance.** A pair settles at
   `r* ≈ 65.5` model units — more than twice `EQUILIBRIUM_DISPLACEMENT` — because
   repulsion keeps pushing past the nominal rest length until the spring, now
   stretched, balances it. Setting `EQUILIBRIUM_DISPLACEMENT = 30` does *not* put
   connected nodes 30 units apart.
2. **Repulsion is long-range but weak; springs dominate at graph scale.** At
   `r = 300` (half the model width) repulsion is 0.20 against a spring force of
   27 — two orders of magnitude apart. So this is a *spring-dominated* layout:
   connectivity, not charge, determines the large-scale shape, and repulsion
   mainly resolves local crowding. Consequently the graph contracts toward
   `r* ≈ 65` per edge and clusters well inside the 600-unit square.

The corollary is the most visible artefact of the model: **nodes with no edges
feel repulsion and nothing else**, so they are pushed steadily outward with no
restoring force and end up parked at the periphery. The same applies to whole
disconnected components, which drift apart from one another. This is why
"centre the graph" appears in the README's backlog.

---

## 10. Relationship to classical force-directed layouts

The model is a recognisable relative of three standard algorithms, and differs
from each in specific, checkable ways.

| Algorithm | Attraction | Repulsion | Cooling | PyGForce |
| --- | --- | --- | --- | --- |
| Eades (1984), spring embedder | logarithmic spring | inverse-square electrical | yes | linear spring; `r^-1.9`; no cooling |
| Fruchterman–Reingold (1991) | `d²/k` | `k²/d` | yes (temperature) | linear `k(r−l)`; `kq²/r^1.9`; no cooling |
| Kamada–Kawai (1989) | ideal per-pair distance | — (stress majorisation) | — | one global rest length for all edges |

Relative to Fruchterman–Reingold, the most conspicuous differences are the
**linear** (Hooke) attraction instead of the quadratic `d²/k`, **equal edge
weights with a uniform rest length**, and the **absence of a cooling schedule**
— convergence here rests entirely on `FRICTION`.

Standard references:

- P. Eades, "A heuristic for graph drawing", *Congressus Numerantium*, 1984.
- T. Fruchterman and E. Reingold, "Graph drawing by force-directed placement",
  *Software: Practice and Experience*, 1991.
- T. Kamada and S. Kawai, "An algorithm for drawing general undirected graphs",
  *Information Processing Letters*, 1989.
- J. Barnes and P. Hut, "A hierarchical O(N log N) force-calculation algorithm",
  *Nature*, 1986 — the usual remedy for the all-pairs repulsion below.

---

## 11. Complexity and numerical characteristics

**Cost per step.** Repulsion is evaluated for every ordered pair, `O(N²)`, and
the spring pass scans the full edge list once per node, `O(N·E)`. There is no
spatial subdivision (no quadtree / Barnes–Hut), no cut-off radius, and no
neighbour lists, so cost grows quadratically in node count and there is no
asymptotic relief for sparse graphs beyond the `E` factor. For the demo's 5–22
nodes this is irrelevant; it is the first thing that would need to change for a
large graph.

**Wall-clock independence.** The simulation advances one fixed step per timer
tick. It has no notion of elapsed real time, so it cannot compensate for a
dropped frame with a larger step, and `GLib.timeout_add` gives no hard real-time
guarantee. Behaviour is reproducible only up to floating-point determinism, and
the timer period is the effective integration rate (20 steps/s at 50 ms).

**Continuous perturbation.** In the demo, `time_tick_handler` adds or removes a
random node every `GENERATION_INTERVAL = 5 s`, keeping the count between
`DEMO_GRAPH_SIZE // 2` and `DEMO_GRAPH_SIZE * 2`. A settling layout is therefore
repeatedly kicked, so the demo never demonstrates the final converged state.

**Stability.** The integrator is stable (see §5) provided
`TIME_STEP / (1 − FRICTION)` is kept near 1 and the springs are not made much
stiffer. The genuinely unbounded inputs are the repulsion singularity as
`r → 0` and the absence of any velocity cap; both are latent risks rather than
observed problems at demo scale.

**Determinism.** Node identity uses a class-level counter (`Tag.last_used_idx`),
and graph mutation uses the `random` module. Layout evolution is deterministic
given the same graph, positions and iteration order.

---

## 12. Known limitations and possible improvements

Ordered roughly by how much they distort the physics:

1. **No centripetal force or re-centring.** Unconnected nodes and detached
   components drift away indefinitely (README backlog: "Centre the graph" —
   e.g. subtract the centre of mass, or add a weak force toward the origin).
2. **No cooling schedule or velocity clamp.** Adding a Fruchterman–Reingold-style
   temperature, or simply capping per-step displacement, would make convergence
   monotone and the `r → 0` case safe.
3. **Repulsion singularity.** Softening the denominator (e.g. `r² + ε`) would
   remove the exact-coincidence special case and the near-coincidence blow-up.
4. **Hardcoded force constants.** `k`, `q` and the exponent `1.9` belong in
   `constants.py` next to the other tuning values; the file currently gives a
   misleading impression of what is tunable.
5. **Degree-normalised springs.** Dividing edge contributions by node degree (or
   using per-edge weights) would stop high-degree nodes from dominating.
6. **Uniform rest length.** Using graph-theoretic distance for `l`, as
   Kamada–Kawai does, would separate clusters more meaningfully.
7. **Algorithmic cost.** Accumulating spring forces in a single `O(E)` pass, and
   spatial partitioning for repulsion, are the obvious optimisations.
8. **`velocity` / `displacement` redundancy.** `displacement_at_node()` returns
   `tag.velocity` unchanged, so the two fields are always identical; collapsing
   them would remove a stale-cache failure mode and clarify that
   `TIME_STEP` is already applied.

None of these are bugs in the current behaviour — they are the reason the
simulation behaves as §9 describes.
