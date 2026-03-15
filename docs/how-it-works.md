# How 4D-Tesseractinator Works

This project shows the same 4D object in two different ways:

- a **projection view**, which maps the 4D tesseract into 3D space
- a **slice view**, which shows the 3D shape created by intersecting the tesseract with a hyperplane

## 1. The Tesseract

A tesseract is the 4D analogue of a cube.

- A line segment has `2` endpoints.
- A square has `4` vertices.
- A cube has `8` vertices.
- A tesseract has `16` vertices.

In this codebase, the tesseract is centered at the origin and its vertices are all combinations of:

```text
(\pm 0.5, \pm 0.5, \pm 0.5, \pm 0.5)
```

Two vertices are connected by an edge when they differ in exactly one coordinate. That gives the tesseract `32` edges.

## 2. Rotating in 4D

In 3D, we usually think about rotating around the `x`, `y`, or `z` axis. In 4D, rotations happen in coordinate **planes** instead.

The six rotation planes used here are:

- `xy`
- `xz`
- `yz`
- `xw`
- `yw`
- `zw`

Each slider controls one planar rotation. The code builds a `4 x 4` rotation matrix for each plane and multiplies them together in the order given by the controls. Rotation order matters because 4D rotations are not commutative.

## 3. Projection View

The projection view answers the question:

> If a 4D object could cast a 3D "shadow", what would it look like?

After rotating the tesseract in 4D, the code projects each point from `R^4` into `R^3` using a perspective-style formula based on the `w` coordinate:

```text
factor = viewer_distance / (viewer_distance - w)
```

The displayed 3D point is then:

```text
(x, y, z) * factor
```

So points with different `w` values appear scaled differently in 3D, which helps give a sense of depth from the fourth dimension.

## 4. Slice View

The slice view answers a different question:

> What 3D shape do we get if we cut the 4D tesseract at a fixed value of `w`?

That means intersecting the rotated tesseract with the hyperplane:

```text
w = w_fixed
```

The code checks every 4D edge:

- If the edge crosses the hyperplane, it computes the intersection point by linear interpolation.
- If a vertex lies directly on the hyperplane, that point is included too.

Those intersection points form a 3D point cloud. The code then uses a convex hull to recover the boundary faces and edges of the sliced solid.

## 5. Why the Two Views Look Different

The two views are showing different mathematical ideas:

- The **projection** view shows the whole 4D object compressed into 3D.
- The **slice** view shows only the 3D cross-section at one chosen `w` value.

That is why the two panels can look dramatically different even when they use the same rotation settings.

## 6. Why Matplotlib Still Shows a 3D Plot on a 2D Screen

Even the 3D output is still being drawn on a 2D screen. Matplotlib uses a 3D camera model to draw the scene from a chosen viewpoint, which is why you can rotate the plot visually and why hidden faces and edges matter for the slice renderer.

## Code Map

If you want to connect the math to the implementation:

- [`tesseractinator/geometry.py`](../tesseractinator/geometry.py) contains the tesseract construction, rotation math, projection, and slicing logic.
- [`tesseractinator/rendering.py`](../tesseractinator/rendering.py) turns that geometry into the projection and slice plots.
- [`tesseractinator/notebook.py`](../tesseractinator/notebook.py) wires the controls into the notebook dashboard.
